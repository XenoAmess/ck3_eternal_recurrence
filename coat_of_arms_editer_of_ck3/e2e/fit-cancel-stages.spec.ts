import { createHash } from 'node:crypto'
import { expect, test, type Page } from '@playwright/test'
import { FIT_BUDGET_STRESS_CONTRACT } from '../src/domain/fitBudgetContract'
import { syntheticBaseVfsReceipt } from './syntheticAssetPack'

function opaqueBgraDds(red: number, green: number, blue: number): Buffer {
  const width = 8
  const height = 8
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

async function cancelWhenPhase(page: Page, phaseText: string): Promise<number> {
  const armed = page.evaluate(({ expected, timeoutMs }) => new Promise<number>((resolve, reject) => {
    const cancel = () => Array.from(document.querySelectorAll('button'))
      .find((button) => button.textContent?.trim() === '取消') as HTMLButtonElement | undefined
    const tryCancel = () => {
      const progress = document.querySelector('.fit-progress small')
      const button = cancel()
      if (!progress?.textContent?.includes(expected) || !button || button.disabled) return false
      const started = performance.now()
      button.click()
      window.clearTimeout(timer)
      resolve(started)
      return true
    }
    const observer = new MutationObserver(() => {
      if (!tryCancel()) return
      observer.disconnect()
    })
    observer.observe(document.body, { attributes: true, childList: true, subtree: true })
    const timer = window.setTimeout(() => {
      observer.disconnect()
      reject(new Error(`fit phase was not observed within ${timeoutMs}ms: ${expected}`))
    }, timeoutMs)
    tryCancel()
  }), { expected: phaseText, timeoutMs: 180_000 })
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  const started = await armed
  await expect(page.locator('.fit-report')).toHaveAttribute('data-fit-task-state', 'cancelled')
  await expect(page.locator('.fit-progress small').first()).toContainText('已取消')
  return page.evaluate((value) => performance.now() - value, started)
}

test('cancels and restarts cleanly from background, semantic refinement, and native paint', async ({ page }) => {
  test.setTimeout(480_000)
  const asset = opaqueBgraDds(255, 255, 255)
  const surface = opaqueBgraDds(0, 128, 128)
  const assets = new Map<string, Buffer>()
  const entry = (kind: string, name: string, data: Buffer, visible = true) => {
    const digest = createHash('sha256').update(data).digest('hex')
    assets.set(digest, data)
    return {
      kind,
      name,
      colors: kind === 'surface_mask' || kind === 'textured_emblem' ? 0 : 3,
      visible,
      category: 'cancel-stage-e2e',
      url: `assets/${digest}.dds`,
      asset_bytes: data.length,
      asset_sha256: digest.toUpperCase(),
      dds: { width: 8, height: 8, format: 'BGRA8' },
    }
  }
  const patterns = Array.from({ length: 12 }, (_, index) => entry(
    'pattern',
    index === 0 ? 'pattern_solid.dds' : `pattern_cancel_${index}.dds`,
    asset,
  ))
  const emblems = Array.from({ length: 64 }, (_, index) => entry(
    'colored_emblem',
    index === 0 ? 'ce_block_02.dds' : `ce_cancel_${String(index).padStart(2, '0')}.dds`,
    asset,
  ))
  const manifestAssets = [
    ...patterns,
    ...emblems,
    entry('textured_emblem', '_default.dds', asset),
    entry('surface_mask', 'coa_mask_texture.dds', surface, false),
  ]
  const manifest = {
    schema: 'ck3-coa-web-asset-pack-v1',
    schema_version: 1,
    pack_id: 'cancel-stage-e2e',
    ck3_build: '1.19.0.6-test',
    source_manifest_sha256: 'C'.repeat(64),
    named_colors: {},
    assets: manifestAssets,
    vfs_receipt: syntheticBaseVfsReceipt(manifestAssets, 'C'.repeat(64)),
  }
  await page.route('**/asset-packs/ck3-1.19.0.6/manifest.json', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(manifest),
  }))
  await page.route('**/asset-packs/ck3-1.19.0.6/assets/*.dds', (route) => {
    const digest = route.request().url().match(/\/([0-9a-f]{64})\.dds$/)?.[1]
    const body = digest ? assets.get(digest) : undefined
    return body
      ? route.fulfill({ status: 200, contentType: 'application/octet-stream', body })
      : route.fulfill({ status: 404, body: 'missing synthetic asset' })
  })
  await page.goto('/')
  await expect(page.getByText(/cancel-stage-e2e/)).toBeVisible({ timeout: 30_000 })
  const pngBase64 = await page.evaluate(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 96
    canvas.height = 96
    const context = canvas.getContext('2d')!
    for (let y = 0; y < 96; y += 1) {
      for (let x = 0; x < 96; x += 1) {
        context.fillStyle = `rgb(${(x * 13 + y * 7) % 256} ${(x * 3 + y * 17) % 256} ${(x * 19 + y * 5) % 256})`
        context.fillRect(x, y, 1, 1)
      }
    }
    return canvas.toDataURL('image/png').split(',')[1]
  })
  await page.locator('.image-drop input').setInputFiles({
    name: 'cancel-stages.png',
    mimeType: 'image/png',
    buffer: Buffer.from(pngBase64, 'base64'),
  })
  await page.locator('.fit-budget input').fill('10000')

  const phases = [
    '背景匹配',
    '全库轮廓粗筛',
    '全角度与 0.1° 级精筛',
    '原生矩形块残差细化',
  ]
  const latencies: Record<string, number> = {}
  for (const phase of phases) {
    latencies[phase] = await cancelWhenPhase(page, phase)
    expect(latencies[phase]).toBeLessThan(FIT_BUDGET_STRESS_CONTRACT.maximumCancellationLatencyMs)
    await page.waitForTimeout(50)
    await expect(page.locator('.fit-report')).toHaveAttribute('data-fit-evidence', '')
  }

  await page.locator('.fit-budget input').fill('1')
  const restarted = Date.now()
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.locator('.fit-progress small').first()).toContainText(/背景匹配|全库轮廓粗筛|全角度与|残差细化/, {
    timeout: FIT_BUDGET_STRESS_CONTRACT.maximumRestartProgressLatencyMs,
  })
  expect(Date.now() - restarted).toBeLessThan(FIT_BUDGET_STRESS_CONTRACT.maximumRestartProgressLatencyMs)
  await page.getByRole('button', { name: '取消', exact: true }).click()
  await expect(page.locator('.fit-report')).toHaveAttribute('data-fit-task-state', 'cancelled')
  console.info(JSON.stringify({ contract: 'ck3-coa-fit-multi-stage-cancel-v1', latencies }))
})
