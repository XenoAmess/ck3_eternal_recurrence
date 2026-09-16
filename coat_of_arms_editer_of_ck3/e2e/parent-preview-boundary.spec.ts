import { expect, test } from '@playwright/test'

const parentSource = `coa = {
    parent = c_england
    pattern = "pattern_solid.dds"
    color1 = red
}`

test('parent inheritance is preserved but never silently presented as a complete browser preview', async ({ page }) => {
  await page.goto('./')

  const source = page.locator('textarea').first()
  await source.fill(parentSource)
  await page.getByRole('button', { name: '解析并载入' }).click()

  const warning = page.getByTestId('parent-preview-boundary')
  await expect(warning).toContainText('parent = c_england')
  await expect(warning).toContainText('预览不包含 parent 继承')

  await expect(page.locator('.output-block pre')).toContainText('parent = c_england')

  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: 'English', exact: true }).click()
  await expect(warning).toContainText('browser does not yet resolve')
  await expect(warning).toContainText('parent = c_england')
})
