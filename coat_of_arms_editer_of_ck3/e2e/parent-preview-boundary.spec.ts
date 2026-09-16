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
  await expect(warning).toContainText('CK3 1.19.0.6')
  await expect(warning).toContainText('不会把继承图案物化进预览')

  await expect(page.locator('.output-block pre')).toContainText('parent = c_england')

  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: 'English', exact: true }).click()
  await expect(warning).toContainText('also preserves this reference without materializing')
  await expect(warning).toContainText('parent = c_england')
})
