import { expect, test } from '@playwright/test'

test('keeps the editor usable without page-level horizontal overflow on a narrow phone viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '家徽工坊' })).toBeVisible()

  const layout = await page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    pageWidth: document.documentElement.scrollWidth,
    workspaceColumns: getComputedStyle(document.querySelector('.workspace')!).gridTemplateColumns,
    fitColumns: getComputedStyle(document.querySelector('.image-fit-grid')!).gridTemplateColumns,
  }))
  expect(layout.pageWidth).toBeLessThanOrEqual(layout.viewportWidth)
  expect(layout.workspaceColumns.split(' ')).toHaveLength(1)
  expect(layout.fitColumns.split(' ')).toHaveLength(1)

  await page.locator('.code-input textarea').fill('coa={pattern="pattern_solid.dds" color1=blue}')
  await page.getByRole('button', { name: '解析并载入' }).click()
  await expect(page.getByText('没有解析诊断', { exact: true })).toBeVisible()
  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: 'English', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Coat of Arms Workshop' })).toBeVisible()
})
