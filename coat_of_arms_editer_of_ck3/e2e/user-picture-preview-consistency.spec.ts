import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

interface PictureCase {
  id: string
  file: string
  mimeType: string
  bytes: number
  width: number
  height: number
  sha256: string
}

const fixtureRoot = resolve('e2e/fixtures/pictures')
const corpus = JSON.parse(readFileSync(resolve(fixtureRoot, 'cases.json'), 'utf8')) as {
  cases: PictureCase[]
}

test.describe.serial('user picture preview consistency corpus', () => {
  for (const picture of corpus.cases) {
    test(`${picture.id}: ${picture.file}`, async ({ page }) => {
      test.setTimeout(180_000)
      const path = resolve(fixtureRoot, picture.file)
      const bytes = readFileSync(path)
      expect(bytes.length).toBe(picture.bytes)
      expect(createHash('sha256').update(bytes).digest('hex').toUpperCase()).toBe(picture.sha256)

      await page.goto('/')
      await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })
      if (picture.id === 'picture-01') await expect(page.locator('.fit-budget input')).toHaveValue('1024')
      await page.locator('.fit-budget input').fill('1')
      await page.locator('.image-drop input').setInputFiles({
        name: picture.file,
        mimeType: picture.mimeType,
        buffer: bytes,
      })
      await expect(page.getByText(new RegExp(`${picture.width}×${picture.height}`))).toBeVisible()
      await page.getByRole('button', { name: '开始本地拟合' }).click()
      await expect(page.getByText(/完成 · .*从完整库评估 \d+ 个构图/)).toBeVisible({ timeout: 120_000 })

      const fitPreview = page.getByTestId('fit-preview')
      const editorPreview = page.getByTestId('editor-preview')
      await expect(fitPreview).toBeVisible()
      await expect(editorPreview).toBeVisible()
      expect(await fitPreview.getAttribute('src')).toBe(await editorPreview.getAttribute('src'))
      const evidence = JSON.parse((await page.locator('.fit-report').getAttribute('data-fit-evidence'))!)
      expect(evidence.provenance.surfaceMaskApplied).toBe(true)
      expect(await fitPreview.evaluate((element) => getComputedStyle(element).objectFit)).toBe('fill')
      expect(await fitPreview.evaluate((element) => getComputedStyle(element).clipPath)).toBe(
        await editorPreview.evaluate((element) => getComputedStyle(element.parentElement!).clipPath),
      )
    })
  }
})
