import { createHash } from 'node:crypto'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'
import { syntheticBaseVfsReceipt } from './syntheticAssetPack'

function bgraDds(
  width: number,
  height: number,
  pixel: (x: number, y: number) => [number, number, number, number],
): Buffer {
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
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const [red, green, blue, alpha] = pixel(x, y)
      const offset = 128 + (y * width + x) * 4
      result[offset] = blue
      result[offset + 1] = green
      result[offset + 2] = red
      result[offset + 3] = alpha
    }
  }
  return result
}

test('fits an uploaded image without CK3, MCP, or Java', async ({ page }) => {
  const completionTimeout = process.env.GITHUB_PAGES === 'true' ? 180_000 : 30_000
  test.setTimeout(process.env.GITHUB_PAGES === 'true' ? 300_000 : 180_000)
  const apiRequests: string[] = []
  page.on('request', (request) => {
    if (new URL(request.url()).pathname.startsWith('/api/')) apiRequests.push(request.url())
  })
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: async (text: string) => {
          Object.assign(window, { __copiedCoa: text })
        },
      },
    })
  })
  const pattern = bgraDds(16, 16, () => [255, 0, 0, 255])
  const emblem = bgraDds(16, 16, (x, y) => (
    x >= 4 && x < 12 && y >= 4 && y < 12 ? [255, 0, 0, 255] : [0, 0, 0, 0]
  ))
  const surface = bgraDds(16, 16, () => [0, 128, 128, 255])
  const assets = new Map<string, Buffer>()
  const entry = (kind: string, name: string, colors: number, data: Buffer, visible = true) => {
    const digest = createHash('sha256').update(data).digest('hex')
    assets.set(digest, data)
    return {
      kind, name, colors, visible, category: 'synthetic-e2e',
      url: `assets/${digest}.dds`, asset_bytes: data.length,
      asset_sha256: digest.toUpperCase(),
      dds: { width: 16, height: 16, format: 'BGRA8' },
    }
  }
  const manifestAssets = [
    entry('pattern', 'pattern_solid.dds', 1, pattern),
    entry('colored_emblem', 'ce_square.dds', 1, emblem),
    entry('textured_emblem', '_default.dds', 0, emblem),
    entry('surface_mask', 'coa_mask_texture.dds', 0, surface, false),
  ]
  const manifest = {
    schema: 'ck3-coa-web-asset-pack-v1', schema_version: 1,
    pack_id: 'synthetic-browser-e2e', ck3_build: '1.19.0.6-test',
    source_manifest_sha256: 'D'.repeat(64),
    named_colors: { black: [0, 0, 0], white: [1, 1, 1] },
    assets: manifestAssets,
    vfs_receipt: syntheticBaseVfsReceipt(manifestAssets, 'D'.repeat(64)),
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
  await expect(page.getByText(/synthetic-browser-e2e/)).toBeVisible()
  await expect(page.getByText('CK3 原生 MCP')).toHaveCount(0)
  const layerBudget = page.locator('.fit-budget input')
  await layerBudget.fill('10000')
  await expect(layerBudget).toHaveValue('10000')
  await layerBudget.fill('6')

  const pngBase64 = await page.evaluate(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 300
    canvas.height = 300
    const context = canvas.getContext('2d')!
    context.fillStyle = 'white'
    context.fillRect(0, 0, 300, 300)
    context.fillStyle = 'black'
    context.fillRect(33, 94, 84, 112)
    context.fillStyle = '#b41924'
    context.fillRect(183, 94, 84, 112)
    return canvas.toDataURL('image/png').split(',')[1]
  })
  await page.locator('.image-drop input').setInputFiles({
    name: 'target.png', mimeType: 'image/png', buffer: Buffer.from(pngBase64, 'base64'),
  })
  await expect(page.getByText(/target\.png/)).toBeVisible()
  await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.getByText(/完成 · .*从完整库评估 \d+ 个构图 · 选中 [2-6]\/6 层/)).toBeVisible({ timeout: completionTimeout })
  await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100')
  await expect(page.locator('.fit-report')).toContainText('300×300 → 56 / 96 / 192 / 230 / 256px')
  await expect(page.getByText(/完成 · 选中 [2-6] 层（进度表示当前搜索阶段）/)).toBeVisible()
  const comparison = page.getByTestId('candidate-comparison')
  const candidateCount = await comparison.locator('.candidate-card').count()
  expect(candidateCount).toBeGreaterThanOrEqual(1)
  expect(candidateCount).toBeLessThanOrEqual(3)
  await expect(comparison.getByText('同合同下非支配')).toHaveCount(candidateCount)
  await expect(comparison.locator('.candidate-shield-preview')).toHaveCount(candidateCount)
  const candidateSources: string[] = []
  for (const card of await comparison.locator('.candidate-card').all()) {
    await card.getByRole('button', { name: '复制候选代码' }).click()
    candidateSources.push(await page.evaluate(() => (
      (window as unknown as { __copiedCoa?: string }).__copiedCoa ?? ''
    )))
  }
  expect(candidateSources.every((item) => item.includes('coa = {'))).toBe(true)
  expect(new Set(candidateSources).size).toBe(candidateCount)
  await expect(comparison).toContainText(/总损失 \d+\.\d+ · 边缘 \d+\.\d+/)
  await expect(comparison).toContainText('当前构图')
  await expect(page.locator('.output-block pre')).toContainText('pattern_solid.dds')
  await expect(page.locator('.output-block pre')).toContainText('colored_emblem')
  const output = await page.locator('.output-block pre').textContent()
  expect(output?.match(/colored_emblem\s*=/g)?.length).toBeGreaterThanOrEqual(2)
  await page.getByRole('button', { name: '安全压缩相邻同样式块' }).click()
  await expect(page.locator('.fit-report')).toContainText('安全压缩块')
  await expect(page.locator('.fit-report')).toContainText('96 / 230 / 512 全部逐字节一致')
  await page.getByRole('button', { name: '零退化固定点剪枝' }).click()
  await expect(page.locator('.fit-report')).toContainText('必要性证据', { timeout: 30_000 })
  await expect(page.locator('.fit-report')).toContainText('96 / 230 / 512 总损失与边缘损失零累计退化')
  await expect(page.getByText(/结果已进入下方结构化编辑器/)).toBeVisible()
  await expect(page.locator('.fit-report dl div').filter({ hasText: 'GPU 交叉分' }).locator('dd'))
    .toHaveText(/^\d+\.\d+$/)
  expect(apiRequests).toEqual([])
})

const localPack = resolve('public/asset-packs/ck3-1.19.0.6/manifest.json')
test('runs against the locally generated exact-build asset pack', async ({ page }) => {
  const completionTimeout = process.env.GITHUB_PAGES === 'true' ? 180_000 : 90_000
  test.setTimeout(process.env.GITHUB_PAGES === 'true' ? 300_000 : 120_000)
  test.skip(!existsSync(localPack), 'the exact-build static asset pack is missing from this checkout')
  const apiRequests: string[] = []
  const assetRequests: string[] = []
  const localManifest = JSON.parse(readFileSync(localPack, 'utf8')) as {
    assets: { url: string }[]
    fit_index: { url: string, features?: { url: string } }
  }
  const fitShardUrls = [localManifest.fit_index.url, localManifest.fit_index.features?.url]
    .filter((value): value is string => Boolean(value))
  page.on('request', (request) => {
    const pathname = new URL(request.url()).pathname
    if (pathname.startsWith('/api/')) apiRequests.push(request.url())
    if (pathname.includes('/asset-packs/ck3-1.19.0.6/assets/')) assetRequests.push(pathname)
  })
  await page.goto('/')
  await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })
  expect(assetRequests.some((path) => fitShardUrls.some((url) => path.endsWith(url)))).toBe(false)
  const initialDdsRequests = new Set(assetRequests.filter((path) => path.endsWith('.dds')))
  expect(initialDdsRequests.size).toBeGreaterThan(0)
  expect(initialDdsRequests.size).toBeLessThan(localManifest.assets.length)
  const pngBase64 = await page.evaluate(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 64
    canvas.height = 64
    const context = canvas.getContext('2d')!
    context.fillStyle = '#b92626'
    context.fillRect(0, 0, 32, 64)
    context.fillStyle = '#e9e1cf'
    context.fillRect(32, 0, 32, 64)
    return canvas.toDataURL('image/png').split(',')[1]
  })
  await page.locator('.fit-budget input').fill('1')
  await page.locator('.image-drop input').setInputFiles({
    name: 'split-target.png', mimeType: 'image/png', buffer: Buffer.from(pngBase64, 'base64'),
  })
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.getByText(/完成 · .*从完整库评估 \d+ 个构图/)).toBeVisible({ timeout: completionTimeout })
  await expect(page.locator('.fit-report dl div').filter({ hasText: '预计算形状特征' }).locator('dd'))
    .toHaveText('1619 / 1619')
  await expect(page.locator('.output-block pre')).toContainText('pattern =')
  for (const shardUrl of fitShardUrls) {
    expect(assetRequests.some((path) => path.endsWith(shardUrl))).toBe(true)
  }
  const requestedDds = new Set(assetRequests.filter((path) => path.endsWith('.dds')))
  expect(requestedDds.size).toBeLessThan(localManifest.assets.length)
  console.log(JSON.stringify({
    contract: 'ck3-coa-asset-pack-on-demand-v1',
    manifestAssets: localManifest.assets.length,
    initialDdsRequests: initialDdsRequests.size,
    fitShardRequests: fitShardUrls.length,
    totalDdsRequests: requestedDds.size,
  }))
  expect(apiRequests).toEqual([])
})
