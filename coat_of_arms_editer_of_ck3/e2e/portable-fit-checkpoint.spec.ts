import { createHash } from 'node:crypto'
import { expect, test } from '@playwright/test'

function portableCheckpoint(tamper = false): string {
  const image = {
    width: 1,
    height: 1,
    pixelsBase64: Buffer.from([12, 34, 56, 255]).toString('base64'),
  }
  const payload = {
    schema: 'ck3-coa-persisted-fit-checkpoint-v1',
    savedAt: '2026-09-21T00:00:00.000Z',
    input: {
      name: 'portable-checkpoint.png',
      image,
      pyramid: [image],
      originalWidth: 1,
      originalHeight: 1,
      workingResolution: 1,
      mimeType: 'image/png',
      bytes: 4,
      sha256: 'A'.repeat(64),
      previewUrl: 'data:image/png;base64,AA==',
    },
    assetPack: { packId: 'portable-e2e-pack', manifestSha256: 'B'.repeat(64) },
    layerBudget: 1,
    checkpoint: {
      contract: 'ck3-coa-fit-checkpoint-v9',
      algorithm: 'ck3-coa-browser-fit-v14-epsilon-delta-safety-lane',
      lane: 'baseline',
      inputSha256: 'A'.repeat(64),
      assetPackManifestSha256: 'B'.repeat(64),
      resolution: 1,
      sourceWidth: 1,
      sourceHeight: 1,
      layerBudget: 1,
      refinementCandidates: 48,
      beamWidth: 2,
      randomSeed: null,
      nextTileIndex: 0,
      tileCount: 0,
      evaluatedCandidates: 0,
      tiles: [],
      state: {
        coatOfArms: {
          outerKey: 'coa',
          parent: '',
          pattern: 'pattern_solid.dds',
          colors: ['black', 'black', 'black'],
          coloredEmblems: [],
          texturedEmblems: [],
        },
        candidateKey: 'portable-e2e',
        patternName: 'pattern_solid.dds',
        selectedAssetNames: [],
        layerLosses: [],
        reconstructionMode: 'native-tile-paint',
        paintPlacements: [],
      },
    },
  }
  const payloadSha256 = createHash('sha256').update(JSON.stringify(payload)).digest('hex').toUpperCase()
  if (tamper) payload.layerBudget = 2
  return JSON.stringify({
    schema: 'ck3-coa-portable-fit-checkpoint-v1',
    payloadSha256,
    payload,
  })
}

test('imports a SHA-bound portable fit checkpoint and persists the recovery slot', async ({ page }) => {
  await page.route('**/asset-packs/ck3-1.19.0.6/manifest.json', (route) => route.fulfill({
    status: 503,
    contentType: 'text/plain',
    body: 'asset pack intentionally unavailable for portable checkpoint isolation',
  }))
  await page.goto('/')
  await page.getByTestId('fit-checkpoint-file-input').setInputFiles({
    name: 'valid.coa-fit-checkpoint.json',
    mimeType: 'application/json',
    buffer: Buffer.from(portableCheckpoint()),
  })
  const recovery = page.getByTestId('fit-checkpoint-recovery')
  await expect(recovery).toBeVisible()
  await expect(recovery).toContainText('portable-checkpoint.png')
  await expect(recovery).toContainText('预算 1')
  await expect(recovery.getByRole('button', { name: '恢复拟合' })).toBeDisabled()

  await page.reload()
  await expect(page.getByTestId('fit-checkpoint-recovery')).toContainText('portable-checkpoint.png')
})

test('rejects a portable checkpoint whose payload changed after hashing', async ({ page }) => {
  await page.route('**/asset-packs/ck3-1.19.0.6/manifest.json', (route) => route.fulfill({
    status: 503,
    contentType: 'text/plain',
    body: 'asset pack intentionally unavailable for portable checkpoint isolation',
  }))
  await page.goto('/')
  await page.getByTestId('fit-checkpoint-file-input').setInputFiles({
    name: 'tampered.coa-fit-checkpoint.json',
    mimeType: 'application/json',
    buffer: Buffer.from(portableCheckpoint(true)),
  })
  await expect(page.getByText(/payload SHA-256 不一致/)).toBeVisible()
  await expect(page.getByTestId('fit-checkpoint-recovery')).toHaveCount(0)
})

test('keeps an imported checkpoint recoverable when IndexedDB quota is exhausted', async ({ page }) => {
  await page.addInitScript(() => {
    const originalPut = IDBObjectStore.prototype.put
    IDBObjectStore.prototype.put = function (value, key) {
      if ((value as { schema?: string } | null)?.schema === 'ck3-coa-persisted-fit-checkpoint-v1') {
        throw new DOMException('injected quota exhaustion', 'QuotaExceededError')
      }
      return key === undefined
        ? originalPut.call(this, value)
        : originalPut.call(this, value, key)
    }
  })
  await page.route('**/asset-packs/ck3-1.19.0.6/manifest.json', (route) => route.fulfill({
    status: 503,
    contentType: 'text/plain',
    body: 'asset pack intentionally unavailable for portable checkpoint isolation',
  }))
  await page.goto('/')
  await page.getByTestId('fit-checkpoint-file-input').setInputFiles({
    name: 'quota-fallback.coa-fit-checkpoint.json',
    mimeType: 'application/json',
    buffer: Buffer.from(portableCheckpoint()),
  })

  await expect(page.getByTestId('fit-checkpoint-recovery')).toContainText('portable-checkpoint.png')
  await expect(page.getByTestId('fit-report')).toHaveAttribute('data-fit-storage-failure', 'quota')
  await expect(page.getByTestId('fit-report')).toHaveAttribute('data-fit-checkpoint-persistence', 'failed')
  await expect(page.getByTestId('fit-report')).toContainText(/浏览器存储空间不足/)
})

test('reports a blocked recovery slot without discarding the imported checkpoint', async ({ page }) => {
  await page.addInitScript(() => {
    IDBFactory.prototype.open = function () {
      const request = {} as IDBOpenDBRequest
      window.setTimeout(() => {
        request.onblocked?.call(request, new Event('blocked') as IDBVersionChangeEvent)
      }, 0)
      return request
    }
  })
  await page.route('**/asset-packs/ck3-1.19.0.6/manifest.json', (route) => route.fulfill({
    status: 503,
    contentType: 'text/plain',
    body: 'asset pack intentionally unavailable for portable checkpoint isolation',
  }))
  await page.goto('/')
  await page.getByTestId('fit-checkpoint-file-input').setInputFiles({
    name: 'blocked-fallback.coa-fit-checkpoint.json',
    mimeType: 'application/json',
    buffer: Buffer.from(portableCheckpoint()),
  })

  await expect(page.getByTestId('fit-checkpoint-recovery')).toContainText('portable-checkpoint.png')
  await expect(page.getByTestId('fit-report')).toHaveAttribute('data-fit-storage-failure', 'blocked')
  await expect(page.getByTestId('fit-report')).toHaveAttribute('data-fit-checkpoint-persistence', 'failed')
  await expect(page.getByTestId('fit-report')).toContainText(/浏览器存储被另一个标签页或旧连接阻止/)
})
