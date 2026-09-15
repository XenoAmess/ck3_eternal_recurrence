import { copyFile, mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const layerBudget = '1024'
const fixture = resolve('test-fixtures/xenoamess_hunter_1024_no_shade.png')
const artifactDirectory = resolve('test-results/reference-hunter-fit')

test('fits the user-provided hunter reference with a 1024-layer ceiling', async ({ page }) => {
  test.setTimeout(5 * 60 * 1000)
  await page.goto('/')
  await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })
  await page.locator('.fit-budget input').fill(layerBudget)
  await page.locator('.image-drop input').setInputFiles(fixture)
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.getByText(/完成 · .*从完整库评估 \d+ 个构图/)).toBeVisible({ timeout: 4 * 60 * 1000 })
  await expect(page.locator('.fit-report')).toContainText(new RegExp(`实际图层\\s*[1-9]\\d* / ${layerBudget}`))

  await mkdir(artifactDirectory, { recursive: true })
  await copyFile(fixture, resolve(artifactDirectory, 'target.png'))
  const source = await page.locator('.output-block pre').textContent()
  const reportText = await page.locator('.fit-report').innerText()
  const selectedLayers = Number(reportText.match(/实际图层\s+(\d+) \/ 1024/)?.[1])
  const totalLoss = Number(reportText.match(/总损失\s+(\d+\.\d+)/)?.[1])
  const relativeImprovement = Number(reportText.match(/相对改善\s+(\d+\.\d+)%/)?.[1])
  expect(selectedLayers).toBeGreaterThanOrEqual(900)
  expect(selectedLayers).toBeLessThanOrEqual(1024)
  expect(source?.match(/colored_emblem\s*=/g)).toHaveLength(selectedLayers)
  expect(totalLoss).toBeLessThan(0.04)
  expect(relativeImprovement).toBeGreaterThan(80)
  await writeFile(resolve(artifactDirectory, 'coat_of_arms.txt'), source ?? '', 'utf8')
  const preview = await page.getByAltText('图片拟合结果预览').getAttribute('src')
  if (!preview?.startsWith('data:image/png;base64,')) throw new Error('missing flat fitted PNG preview')
  await writeFile(
    resolve(artifactDirectory, 'fitted-render.png'),
    Buffer.from(preview.slice('data:image/png;base64,'.length), 'base64'),
  )
  const shaderPreview = await page.locator('img.shader-preview').getAttribute('src')
  if (!shaderPreview?.startsWith('data:image/png;base64,')) throw new Error('missing shader PNG preview')
  await writeFile(
    resolve(artifactDirectory, 'fitted-shader-preview.png'),
    Buffer.from(shaderPreview.slice('data:image/png;base64,'.length), 'base64'),
  )
  const report = {
    status: reportText,
    generatedAt: new Date().toISOString(),
  }
  await writeFile(resolve(artifactDirectory, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  await page.locator('.image-fit-grid').screenshot({ path: resolve(artifactDirectory, 'fit-report.png') })
  await page.locator('.preview-pane').screenshot({ path: resolve(artifactDirectory, 'preview-panel.png') })
})
