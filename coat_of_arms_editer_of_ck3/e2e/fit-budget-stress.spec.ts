import { createHash } from 'node:crypto'
import { expect, test } from '@playwright/test'
import { FIT_BUDGET_STRESS_CONTRACT } from '../src/domain/fitBudgetContract'
import { parseCoatOfArms } from '../src/domain/parser'

function redChannelDds(): Buffer {
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
    result[offset + 2] = 255
    result[offset + 3] = 255
  }
  return result
}

function surfaceDds(): Buffer {
  const data = redChannelDds()
  for (let offset = 128; offset < data.length; offset += 4) {
    data[offset] = 128
    data[offset + 1] = 128
    data[offset + 2] = 0
  }
  return data
}

test('runs real 128/1024/10000 browser fits without clamping and cancels a paint phase', async ({ page }) => {
  const contract = FIT_BUDGET_STRESS_CONTRACT
  const performanceGateEnforced = process.env.COA_E2E_PERFORMANCE_GATE !== 'report-only'
  const resumeCompletionTimeoutMs = performanceGateEnforced
    ? contract.maximumResumeDurationMs
    : contract.reportOnlyMaximumDurationMs
  // Hosted Pages runners are intentionally report-only performance probes and
  // can spend ~250 seconds in the three real fits before pause/resume and
  // cancellation gates begin. Keep workstation thresholds strict while giving
  // the slower hosted environment enough suite-level time to reach those gates.
  test.setTimeout(performanceGateEnforced ? 300_000 : 600_000)
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
  const pattern = redChannelDds()
  const emblem = redChannelDds()
  const surface = surfaceDds()
  const assets = new Map<string, Buffer>()
  const entry = (kind: string, name: string, data: Buffer, visible = true) => {
    const digest = createHash('sha256').update(data).digest('hex')
    assets.set(digest, data)
    return {
      kind, name, colors: kind === 'surface_mask' ? 0 : 1, visible,
      category: 'fit-budget-e2e', url: `assets/${digest}.dds`,
      asset_bytes: data.length, asset_sha256: digest.toUpperCase(),
      dds: { width: 4, height: 4, format: 'BGRA8' },
    }
  }
  const manifest = {
    schema: 'ck3-coa-web-asset-pack-v1', schema_version: 1,
    pack_id: 'fit-budget-e2e', ck3_build: '1.19.0.6-test',
    source_manifest_sha256: 'E'.repeat(64), named_colors: {},
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
  await page.goto('/')
  await expect(page.getByText(/fit-budget-e2e/)).toBeVisible({ timeout: 30_000 })
  const pngBase64 = await page.evaluate(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 96
    canvas.height = 96
    const context = canvas.getContext('2d')!
    const colors = ['rgb(13 27 41)', 'rgb(221 37 53)', 'rgb(29 199 113)', 'rgb(237 211 61)']
    for (let y = 0; y < 96; y += 1) {
      for (let x = 0; x < 96; x += 1) {
        context.fillStyle = colors[(x + y * 3) % colors.length]
        context.fillRect(x, y, 1, 1)
      }
    }
    return canvas.toDataURL('image/png').split(',')[1]
  })
  await page.locator('.image-drop input').setInputFiles({
    name: 'fit-budget-stress.png', mimeType: 'image/png', buffer: Buffer.from(pngBase64, 'base64'),
  })
  const heapBefore = await page.evaluate(() => (
    (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? null
  ))
  const report = page.locator('.fit-report')
  const observations: Record<string, unknown>[] = []
  let baseline128Evidence: Record<string, unknown> | undefined

  for (const budget of contract.budgets) {
    await page.locator('.fit-budget input').fill(String(budget))
    const started = Date.now()
    await page.getByRole('button', { name: '开始本地拟合' }).click()
    await expect(report.locator('p')).toContainText(`/${budget} 层`, {
      timeout: performanceGateEnforced
        ? contract.maximumDurationMs[budget]
        : contract.reportOnlyMaximumDurationMs,
    })
    const durationMs = Date.now() - started
    if (performanceGateEnforced) {
      expect(durationMs).toBeLessThan(contract.maximumDurationMs[budget])
    }
    const rawEvidence = await report.getAttribute('data-fit-evidence')
    expect(rawEvidence).toBeTruthy()
    const evidence = JSON.parse(rawEvidence!) as {
      metrics: Record<string, unknown>
      provenance: {
        searchBackend: string
        batchSearch: {
          status: string
          batches: number
          candidates: number
          cpuReferenceAgreement: boolean
        }
        layerBudget: number
        drawnInstances: number
        coloredEmblemBlocks: number
        evaluatedCandidates: number
        terminationReason: string
        nativeTileSearch: {
          userBudgetAppliedWithoutClamp: number
          maximumDepth: number
          pixelLeafCapacity: number
        }
      }
    }
    if (budget === 128) baseline128Evidence = evidence
    expect(evidence.provenance.layerBudget).toBe(budget)
    expect(evidence.provenance.searchBackend).toBe('webgl2-batch+cpu-reference')
    expect(evidence.provenance.batchSearch).toMatchObject({
      status: 'active',
      batches: 1,
      candidates: 6,
      cpuReferenceAgreement: true,
    })
    expect(evidence.provenance.nativeTileSearch.userBudgetAppliedWithoutClamp).toBe(budget)
    expect(evidence.provenance.drawnInstances).toBeLessThanOrEqual(budget)
    expect(evidence.provenance.evaluatedCandidates).toBeGreaterThan(evidence.provenance.drawnInstances)
    const observation = { budget, durationMs, ...evidence.provenance }
    observations.push(observation)
    console.info(JSON.stringify({
      contract: contract.contract,
      performanceReference: contract.performanceReference,
      performanceGateEnforced,
      observation,
    }))
  }

  const finalEvidence = observations.at(-1)! as {
    drawnInstances: number
    coloredEmblemBlocks: number
    terminationReason: string
    nativeTileSearch: { maximumDepth: number, pixelLeafCapacity: number }
  }
  expect(finalEvidence.drawnInstances).toBeGreaterThan(1_024)
  expect(finalEvidence.nativeTileSearch).toMatchObject({ maximumDepth: 7, pixelLeafCapacity: 9_216 })
  expect(['exact_match', 'no_improvement']).toContain(finalEvidence.terminationReason)
  await page.getByRole('button', { name: '复制 CK3 代码' }).click()
  const copied = await page.evaluate(() => (window as unknown as { __copiedCoa: string }).__copiedCoa)
  const parsed = parseCoatOfArms(copied)
  const copiedUtf8Bytes = Buffer.byteLength(copied, 'utf8')
  const copiedLines = copied ? (copied.match(/\n/g)?.length ?? 0) + 1 : 0
  expect(parsed.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
  expect(parsed.coatOfArms.coloredEmblems).toHaveLength(finalEvidence.coloredEmblemBlocks)
  expect(parsed.coatOfArms.coloredEmblems.reduce((sum, item) => sum + item.instances.length, 0))
    .toBe(finalEvidence.drawnInstances)

  // Pause at a real native-paint checkpoint, resume the same run revision,
  // and require the completed model and metrics to match an uninterrupted
  // 128-budget run. This is distinct from cancellation/restart below.
  await page.locator('.fit-budget input').fill('128')
  const pauseArmed = page.evaluate(() => new Promise<number>((resolve) => {
    const findPauseButton = () => Array.from(document.querySelectorAll('button'))
      .find((button) => button.textContent?.trim() === '暂停') as HTMLButtonElement | undefined
    const clickAtFirstSafeCheckpoint = () => {
      const button = findPauseButton()
      if (!button || button.disabled) return false
      const clickedAt = performance.now()
      button.click()
      resolve(clickedAt)
      return true
    }
    if (clickAtFirstSafeCheckpoint()) return
    const observer = new MutationObserver(() => {
      if (!clickAtFirstSafeCheckpoint()) return
      observer.disconnect()
    })
    observer.observe(document.body, { attributes: true, childList: true, subtree: true })
  }))
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  const pauseClickedAt = await pauseArmed
  await expect(report).toHaveAttribute('data-fit-task-state', 'paused')
  const pauseLatencyMs = await page.evaluate((clickedAt) => performance.now() - clickedAt, pauseClickedAt)
  expect(pauseLatencyMs).toBeLessThan(contract.maximumPauseLatencyMs)
  await expect(report).toHaveAttribute('data-fit-checkpoint-persistence', 'saved')
  const reloadStarted = Date.now()
  await page.reload()
  await expect(page.getByText(/fit-budget-e2e/)).toBeVisible({ timeout: 30_000 })
  const recovery = page.getByTestId('fit-checkpoint-recovery')
  await expect(recovery).toBeVisible()
  await expect(recovery).toContainText('fit-budget-stress.png')
  await recovery.getByRole('button', { name: '恢复拟合' }).click()
  await expect(report).toHaveAttribute('data-fit-task-state', 'paused')
  const persistentRestoreDurationMs = Date.now() - reloadStarted
  if (performanceGateEnforced) {
    expect(persistentRestoreDurationMs).toBeLessThan(contract.maximumResumeDurationMs)
  }
  const resumeStarted = Date.now()
  await page.getByRole('button', { name: '继续', exact: true }).click()
  await expect(report).toHaveAttribute('data-fit-task-state', 'running')
  await expect(report.locator('p')).toContainText('/128 层', { timeout: resumeCompletionTimeoutMs })
  await expect(report).toHaveAttribute('data-fit-task-state', 'completed')
  const resumeDurationMs = Date.now() - resumeStarted
  if (performanceGateEnforced) {
    expect(resumeDurationMs).toBeLessThan(contract.maximumResumeDurationMs)
  }
  const resumedRawEvidence = await report.getAttribute('data-fit-evidence')
  expect(resumedRawEvidence).toBeTruthy()
  const resumedEvidence = JSON.parse(resumedRawEvidence!) as {
    metrics: Record<string, unknown>
    provenance: Record<string, unknown>
  }
  expect(resumedEvidence.metrics).toEqual(baseline128Evidence!.metrics)
  expect(resumedEvidence.provenance).toMatchObject({
    layerBudget: 128,
    drawnInstances: (baseline128Evidence!.provenance as Record<string, unknown>).drawnInstances,
    coloredEmblemBlocks: (baseline128Evidence!.provenance as Record<string, unknown>).coloredEmblemBlocks,
    terminationReason: (baseline128Evidence!.provenance as Record<string, unknown>).terminationReason,
  })

  // Cancel during the expensive paint phase, then use the contract's minimal
  // recovery probe to isolate worker-slot reuse from the already-measured
  // 128-layer performance gate and prove there is no stale-result pollution.
  await page.locator('.fit-budget input').fill('10000')
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.locator('.fit-progress small').first()).toContainText('原生矩形块残差细化', { timeout: 15_000 })
  const cancelStarted = Date.now()
  await page.getByRole('button', { name: '取消', exact: true }).click()
  await expect(page.locator('.fit-progress small').first()).toContainText('已取消')
  const cancellationLatencyMs = Date.now() - cancelStarted
  expect(cancellationLatencyMs).toBeLessThan(contract.maximumCancellationLatencyMs)
  await page.locator('.fit-budget input').fill(String(contract.restartProbeBudget))
  const restartStarted = Date.now()
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.locator('.fit-progress small').first()).toContainText(/背景匹配|全库轮廓粗筛|全角度与|残差细化/, {
    timeout: contract.maximumRestartProgressLatencyMs,
  })
  const restartProgressLatencyMs = Date.now() - restartStarted
  expect(restartProgressLatencyMs).toBeLessThan(contract.maximumRestartProgressLatencyMs)
  await page.getByRole('button', { name: '取消', exact: true }).click()
  await expect(page.locator('.fit-progress small').first()).toContainText('已取消')
  await page.waitForTimeout(250)
  await expect(report).toHaveAttribute('data-fit-evidence', '')

  const heapAfter = await page.evaluate(() => (
    (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? null
  ))
  const measuredJsHeapDeltaBytes = heapBefore === null || heapAfter === null
    ? null
    : Math.max(0, heapAfter - heapBefore)
  if (measuredJsHeapDeltaBytes !== null) {
    expect(measuredJsHeapDeltaBytes).toBeLessThan(contract.maximumMeasuredJsHeapDeltaBytes)
  }
  expect(nonGetRequests).toEqual([])
  console.info(JSON.stringify({
    contract: contract.contract,
    performanceReference: contract.performanceReference,
    performanceGateEnforced,
    observations,
    pauseLatencyMs,
    persistentRestoreDurationMs,
    resumeDurationMs,
    pauseResumeContract: 'ck3-coa-fit-checkpoint-v1',
    cancellationLatencyMs,
    restartProgressLatencyMs,
    restartBudget: contract.restartProbeBudget,
    copiedUtf8Bytes,
    copiedLines,
    copiedBlocks: parsed.coatOfArms.coloredEmblems.length,
    copiedInstances: parsed.coatOfArms.coloredEmblems.reduce((sum, item) => sum + item.instances.length, 0),
    measuredJsHeapDeltaBytes,
    memoryEvidenceScope: contract.memoryEvidenceScope,
    nonGetRequests,
  }))
})
