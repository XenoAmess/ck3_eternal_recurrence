import { createHash } from 'node:crypto'
import { expect, test } from '@playwright/test'

function solidBgraDds(red: number, green: number, blue: number, alpha = 255): Buffer {
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
    result[offset + 3] = alpha
  }
  return result
}

test('composites the registered raw textured emblem through the standalone shader model', async ({ page }) => {
  const nonGetRequests: string[] = []
  page.on('request', (request) => {
    if (request.method() !== 'GET') nonGetRequests.push(request.url())
  })
  const assets = new Map<string, Buffer>()
  const entry = (kind: string, name: string, data: Buffer, registration = 'render_support') => {
    const digest = createHash('sha256').update(data).digest('hex')
    assets.set(digest, data)
    return {
      kind, name, colors: kind === 'surface_mask' ? 0 : 1, visible: kind !== 'surface_mask',
      category: 'textured-preview-e2e', registration,
      url: `assets/${digest}.dds`, asset_bytes: data.length,
      asset_sha256: digest.toUpperCase(), dds: { width: 4, height: 4, format: 'BGRA8' },
    }
  }
  const manifest = {
    schema: 'ck3-coa-web-asset-pack-v1', schema_version: 1,
    pack_id: 'textured-preview-e2e', ck3_build: '1.19.0.6-test',
    source_manifest_sha256: 'E'.repeat(64),
    named_colors: { black: [0, 0, 0], white: [1, 1, 1] },
    assets: [
      entry('pattern', 'pattern_solid.dds', solidBgraDds(255, 0, 0), 'designer_manifest'),
      entry('colored_emblem', 'ce_block_02.dds', solidBgraDds(255, 255, 255), 'designer_manifest'),
      entry('textured_emblem', '_default.dds', solidBgraDds(0, 255, 0, 128)),
      entry('surface_mask', 'coa_mask_texture.dds', solidBgraDds(128, 128, 128)),
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
  await expect(page.getByText(/textured-preview-e2e/)).toBeVisible()
  await page.locator('.code-input textarea').fill(`coa = {
    pattern = "pattern_solid.dds"
    color1 = rgb { 64 128 192 }
    color2 = white
    color3 = black
    textured_emblem = { texture = "_default.dds" }
  }`)
  await page.getByRole('button', { name: '解析并载入' }).click()
  await expect(page.locator('.preview-caption')).toContainText('1 个受限纹理层')
  await expect(page.locator('.shader-preview')).toBeVisible()
  const pixel = await page.locator('.shader-preview').evaluate(async (element) => {
    const image = element as HTMLImageElement
    await image.decode()
    const canvas = document.createElement('canvas')
    canvas.width = image.naturalWidth
    canvas.height = image.naturalHeight
    const context = canvas.getContext('2d')!
    context.drawImage(image, 0, 0)
    return [...context.getImageData(Math.floor(canvas.width / 2), Math.floor(canvas.height / 2), 1, 1).data]
  })
  expect(pixel).toEqual([32, 192, 95, 255])
  const supportNotice = page.locator('.editor-pane .el-alert').filter({ hasText: '浏览器按随附' })
  await expect(supportNotice).toContainText('_default.dds')
  expect(nonGetRequests).toEqual([])
})
