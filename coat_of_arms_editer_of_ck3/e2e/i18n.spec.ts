import { expect, test } from '@playwright/test'

test('switches the production UI between Simplified Chinese and English and persists the choice', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '家徽工坊' })).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN')

  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: 'English', exact: true }).click()

  await expect(page.getByRole('heading', { name: 'Coat of Arms Workshop' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Fit image with native elements' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Import code' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Composition preview' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Structured editor' })).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  await expect(page).toHaveTitle('Coat of Arms Workshop')
  expect(await page.evaluate(() => localStorage.getItem('ck3-coa-ui-locale-v1'))).toBe('en')

  await page.getByText('CK3 1.19.0.6 clipboard syntax capability matrix', { exact: true }).click()
  const visibleText = (await page.locator('body').innerText()).replace('简体中文', '')
  expect(visibleText).not.toMatch(/[\u3400-\u9fff]/)

  await page.reload()
  await expect(page.getByRole('heading', { name: 'Coat of Arms Workshop' })).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')

  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: '简体中文', exact: true }).click()
  await expect(page.getByRole('heading', { name: '家徽工坊' })).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN')
  await expect(page).toHaveTitle('家徽工坊')
})
