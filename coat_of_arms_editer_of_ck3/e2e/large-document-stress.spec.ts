import { createHash } from 'node:crypto'
import { expect, test } from '@playwright/test'
import { buildLargeDocumentFixture, LARGE_DOCUMENT_CONTRACT } from '../src/domain/largeDocumentContract'
import {
  createCoatOfArmsProject,
  parseCoatOfArmsProject,
  serializeCoatOfArmsProject,
} from '../src/domain/projectDocument'
import { parseCoatOfArms } from '../src/domain/parser'

function solidBgraDds(red: number, green: number, blue: number): Buffer {
  const width = 4
  const height = 4
  const result = Buffer.alloc(128 + width * height * 4)
  result.write('DDS ', 0, 'ascii')
  result.writeUInt32LE(124, 4)
  result.writeUInt32LE(0x0002100f, 8)
  result.writeUInt32LE(height, 12)
  result.writeUInt32LE(width, 16)
  result.writeUInt32LE(width * 4, 20)
  result.writeUInt32LE(1, 28)
  result.writeUInt32LE(32, 76)
  result.writeUInt32LE(0x41, 80)
  result.writeUInt32LE(32, 88)
  result.writeUInt32LE(0x00ff0000, 92)
  result.writeUInt32LE(0x0000ff00, 96)
  result.writeUInt32LE(0x000000ff, 100)
  result.writeUInt32LE(0xff000000, 104)
  result.writeUInt32LE(0x1000, 108)
  for (let offset = 128; offset < result.length; offset += 4) {
    result[offset] = blue
    result[offset + 1] = green
    result[offset + 2] = red
    result[offset + 3] = 255
  }
  return result
}

test('edits and exports an exact 10,000-instance project through a bounded DOM window', async ({ page }) => {
  test.setTimeout(120_000)
  const contract = LARGE_DOCUMENT_CONTRACT
  const nonGetRequests: { method: string, url: string }[] = []
  page.on('request', (request) => {
    if (request.method() !== 'GET') nonGetRequests.push({ method: request.method(), url: request.url() })
  })
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: async (text: string) => { (window as unknown as { __copiedCoa: string }).__copiedCoa = text },
        readText: async () => (window as unknown as { __copiedCoa?: string }).__copiedCoa ?? '',
      },
    })
  })

  const pattern = solidBgraDds(18, 24, 31)
  const emblem = solidBgraDds(215, 34, 47)
  const surface = solidBgraDds(128, 128, 0)
  const assets = new Map<string, Buffer>()
  const entry = (kind: string, name: string, data: Buffer, visible = true) => {
    const digest = createHash('sha256').update(data).digest('hex')
    assets.set(digest, data)
    return {
      kind, name, colors: kind === 'surface_mask' ? 0 : 1, visible,
      category: 'large-document-e2e', url: `assets/${digest}.dds`,
      asset_bytes: data.length, asset_sha256: digest.toUpperCase(),
      dds: { width: 4, height: 4, format: 'BGRA8' },
    }
  }
  const manifest = {
    schema: 'ck3-coa-web-asset-pack-v1', schema_version: 1,
    pack_id: 'large-document-e2e', ck3_build: '1.19.0.6-test',
    source_manifest_sha256: 'D'.repeat(64),
    named_colors: { black: [0, 0, 0], white: [1, 1, 1] },
    assets: [
      entry('pattern', 'pattern_solid.dds', pattern),
      entry('colored_emblem', 'ce_block_02.dds', emblem),
      entry('textured_emblem', '_default.dds', emblem),
      entry('surface_mask', 'coa_mask_texture.dds', surface, false),
    ],
  }
  await page.route('**/asset-packs/ck3-1.19.0.6/manifest.json', (route) => route.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(manifest),
  }))
  await page.route('**/asset-packs/ck3-1.19.0.6/assets/*.dds', (route) => {
    const digest = route.request().url().match(/\/([0-9a-f]{64})\.dds$/)?.[1]
    const body = digest ? assets.get(digest) : undefined
    return body
      ? route.fulfill({ status: 200, contentType: 'application/octet-stream', body })
      : route.fulfill({ status: 404, body: 'missing synthetic asset' })
  })

  const project = await createCoatOfArmsProject(buildLargeDocumentFixture(), {
    savedAt: '2026-09-15T00:00:00.000Z',
    assetPack: {
      packId: 'large-document-e2e', manifestSha256: 'D'.repeat(64), ck3Build: '1.19.0.6-test',
    },
  })
  const projectText = serializeCoatOfArmsProject(project)
  await page.goto('/')
  await expect(page.getByText(/large-document-e2e/)).toBeVisible()
  const heapBefore = await page.evaluate(() => (
    (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? null
  ))

  const importStart = Date.now()
  await page.locator('input.hidden-file-input').setInputFiles({
    name: 'large-10000.coa-project.json',
    mimeType: 'application/json',
    buffer: Buffer.from(projectText, 'utf8'),
  })
  await expect(page.getByText(/项目已恢复：10000 个实例/)).toBeVisible({
    timeout: contract.maximumBrowserProjectImportMs,
  })
  const importMs = Date.now() - importStart
  expect(importMs).toBeLessThan(contract.maximumBrowserProjectImportMs)
  await expect(page.locator('[data-testid="instance-editor-window"] .instance-card')).toHaveCount(32)
  await expect(page.getByText(/实例窗口 1–32 \/ 10000/)).toBeVisible()
  await expect(page.locator('.output-block')).toContainText('1,653,890 bytes · 70,014 行')
  await expect(page.locator('.output-block')).toContainText('UI 摘要；复制仍为完整文档')

  const editStart = Date.now()
  await page.locator('.instance-window-toolbar input').fill('10000')
  await expect(page.getByText(/实例窗口 9969–10000 \/ 10000/)).toBeVisible()
  const tail = page.locator('[data-instance-index="9999"]')
  await expect(tail).toBeVisible()
  await tail.locator('.el-input-number input').nth(4).fill('123.4')
  await tail.locator('.el-input-number input').nth(4).press('Enter')
  const editMs = Date.now() - editStart
  expect(editMs).toBeLessThan(contract.maximumBrowserWindowJumpAndEditMs)

  const autosaveStart = Date.now()
  await expect(page.getByText(/已自动保存 10,000 实例 · 单槽覆盖/)).toBeVisible({
    timeout: contract.maximumBrowserAutosaveMs,
  })
  const autosaveMs = Date.now() - autosaveStart
  expect(autosaveMs).toBeLessThan(contract.maximumBrowserAutosaveMs)

  const copyStart = Date.now()
  await page.getByRole('button', { name: '复制 CK3 代码' }).click()
  await expect(page.getByText(/CK3 纹章代码已复制/)).toBeVisible()
  const copied = await page.evaluate(() => (
    (window as unknown as { __copiedCoa: string }).__copiedCoa
  ))
  const copyMs = Date.now() - copyStart
  expect(copyMs).toBeLessThan(contract.maximumBrowserClipboardCopyMs)
  expect((copied.match(/instance\s*=\s*\{/g) ?? [])).toHaveLength(contract.drawnInstances)
  const copiedModel = parseCoatOfArms(copied)
  expect(copiedModel.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
  expect(copiedModel.coatOfArms.coloredEmblems[0].instances.at(-1)?.rotation).toBe(123.4)

  const downloadStart = Date.now()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: '保存项目' }).click()
  const download = await downloadPromise
  const downloadStream = await download.createReadStream()
  const chunks: Buffer[] = []
  for await (const chunk of downloadStream) chunks.push(Buffer.from(chunk))
  const downloadedText = Buffer.concat(chunks).toString('utf8')
  const downloadMs = Date.now() - downloadStart
  expect(downloadMs).toBeLessThan(contract.maximumBrowserProjectDownloadMs)
  const downloadedProject = await parseCoatOfArmsProject(downloadedText)
  expect(downloadedProject.ck3Source.stats.drawnInstances).toBe(contract.drawnInstances)
  expect(downloadedProject.coatOfArms.coloredEmblems[0].instances.at(-1)?.rotation).toBe(123.4)

  const heapAfter = await page.evaluate(() => (
    (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? null
  ))
  const measuredJsHeapDeltaBytes = heapBefore === null || heapAfter === null
    ? null
    : Math.max(0, heapAfter - heapBefore)
  if (measuredJsHeapDeltaBytes !== null) {
    expect(measuredJsHeapDeltaBytes).toBeLessThan(contract.maximumMeasuredJsHeapDeltaBytes)
  }

  const recoveryStart = Date.now()
  await page.reload()
  const recovery = page.locator('.autosave-recovery')
  await expect(recovery).toContainText('10,000 个实例 · SHA-256 已验证', {
    timeout: contract.maximumBrowserAutosaveRecoveryMs,
  })
  await recovery.getByRole('button', { name: '恢复' }).click()
  await expect(page.getByText(/已恢复自动保存：10,000 个实例/)).toBeVisible()
  await page.locator('.instance-window-toolbar input').fill('10000')
  await expect(page.locator('[data-instance-index="9999"] .el-input-number input').nth(4)).toHaveValue('123.4')
  const recoveryMs = Date.now() - recoveryStart
  expect(recoveryMs).toBeLessThan(contract.maximumBrowserAutosaveRecoveryMs)
  // A post-reload heap sample is observational only: Chromium may retain the old
  // document until a later GC, so it cannot be subtracted from heapBefore.
  const heapAfterRecoveryNavigation = await page.evaluate(() => (
    (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? null
  ))
  expect(nonGetRequests).toEqual([])
  console.info(JSON.stringify({
    contract: contract.contract,
    drawnInstances: contract.drawnInstances,
    timingsMs: { importMs, editMs, copyMs, downloadMs, autosaveMs, recoveryMs },
    measuredJsHeapDeltaBytes,
    heapAfterRecoveryNavigation,
    memoryEvidenceScope: contract.memoryEvidenceScope,
    renderedInstanceCards: 32,
    copiedInstanceCount: (copied.match(/instance\s*=\s*\{/g) ?? []).length,
    nonGetRequests,
  }))
})
