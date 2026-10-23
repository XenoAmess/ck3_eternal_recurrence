import { expect, test } from '@playwright/test'

test('blocks fractional RGB export and copies corrected byte colors', async ({ page }) => {
  await page.addInitScript(() => {
    let text = ''
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        readText: async (): Promise<string> => text,
        writeText: async (value: string): Promise<void> => { text = value },
      },
    })
  })
  await page.goto('/')
  const copy = page.getByRole('button', { name: '复制 CK3 代码', exact: true })
  const color = page.locator('.el-form-item').filter({ hasText: '图案颜色 1' }).locator('input')
  await color.fill('rgb { 0.802549 0.772549 0.772549 }')
  await expect(copy).toBeDisabled()
  await expect(page.getByText('colored_emblem 1 color1 只能是命名颜色或 rgb/hsv 三分量字面量；rgb 分量必须为 0–255 整数', { exact: true })).toBeVisible()

  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: 'English', exact: true }).click()
  await expect(page.getByText('colored_emblem 1 color1 must be a named color or an rgb/hsv triplet; rgb channels must be integers from 0 to 255', { exact: true })).toBeVisible()
  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: '简体中文', exact: true }).click()
  await color.fill('rgb { 205 197 197 }')
  await expect(copy).toBeEnabled()
  await copy.click()
  const source = await page.evaluate(() => navigator.clipboard.readText())
  await test.info().attach('integer-rgb-source.txt', { body: source, contentType: 'text/plain' })
  expect(source).toContain('color1 = rgb { 205 197 197 }')
  for (const match of source.matchAll(/\brgb\s*\{([^}]+)\}/g)) {
    const components = match[1].trim().split(/\s+/)
    expect(components).toHaveLength(3)
    expect(components.every((component) => /^\d+$/.test(component) && Number(component) <= 255)).toBe(true)
  }
})
