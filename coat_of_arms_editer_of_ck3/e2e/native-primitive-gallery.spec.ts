import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const enabled = process.env.RUN_COA_PRIMITIVE_GALLERY === '1'
const names = [
  'ce_billet.dds',
  'ce_circle.dds',
  'ce_circle_mask.dds',
  'ce_block_01.dds',
  'ce_block_02.dds',
  'ce_block_03.dds',
  'ce_block_04.dds',
  'ce_block_05.dds',
  'ce_gotland_spiral.dds',
  'ce_norse_spirals.dds',
  'ce_pagan_spiral_03.dds',
  'ce_pagan_spiral_04.dds',
  'ce_pagan_spiral_06.dds',
  'ce_spirals_03_rotated.dds',
  'ce_triskel.dds',
  'ce_triskelion.dds',
  'ce_triskel_02.dds',
]

test('renders native primitive and spiral candidates', async ({ page }) => {
  test.skip(!enabled, 'manual DDS gallery; set RUN_COA_PRIMITIVE_GALLERY=1')
  test.setTimeout(5 * 60 * 1000)
  const directory = resolve('test-results/native-primitive-gallery')
  await mkdir(directory, { recursive: true })
  await page.goto('/')
  await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })
  for (const name of names) {
    const source = `coa = {
      pattern = "pattern_solid.dds"
      color1 = rgb { 255 255 255 }
      color2 = rgb { 255 255 255 }
      color3 = rgb { 255 255 255 }
      colored_emblem = {
        texture = "${name}"
        color1 = rgb { 255 0 0 }
        color2 = rgb { 255 0 0 }
        color3 = rgb { 255 0 0 }
        instance = { position = { 0.5 0.5 } scale = { 0.9 0.9 } rotation = 0 depth = 1 }
      }
    }`
    await page.locator('.code-input textarea').fill(source)
    await page.getByRole('button', { name: '解析并载入' }).click()
    await page.getByRole('button', { name: '从独立素材包加载当前 DDS' }).click()
    await expect(page.locator('img.shader-preview')).toBeVisible()
    const preview = await page.locator('img.shader-preview').getAttribute('src')
    if (!preview?.startsWith('data:image/png;base64,')) throw new Error(`missing preview for ${name}`)
    await writeFile(
      resolve(directory, `${name}.png`),
      Buffer.from(preview.slice('data:image/png;base64,'.length), 'base64'),
    )
  }
})
