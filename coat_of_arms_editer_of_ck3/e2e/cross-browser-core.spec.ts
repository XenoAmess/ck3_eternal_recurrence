import { expect, test } from '@playwright/test'

test('imports, previews, localizes, and decodes a local image without uploading user content', async ({ page }) => {
  const nonGetRequests: string[] = []
  page.on('request', (request) => {
    if (request.method() !== 'GET') nonGetRequests.push(request.url())
  })

  await page.goto('/')
  await expect(page.getByRole('heading', { name: '家徽工坊' })).toBeVisible()

  const source = `coa = {
    pattern = "pattern_solid.dds"
    color1 = rgb { 24 48 96 }
    color2 = white
    color3 = red
  }`
  await page.locator('.code-input textarea').fill(source)
  await page.getByRole('button', { name: '解析并载入' }).click()
  await expect(page.getByText('没有解析诊断', { exact: true })).toBeVisible()
  await expect(page.locator('.shield img')).toBeVisible()

  await page.getByTestId('locale-select').click()
  await page.getByRole('option', { name: 'English', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Coat of Arms Workshop' })).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')

  await page.locator('.image-drop input').setInputFiles({
    name: 'local-cross-browser.svg',
    mimeType: 'image/svg+xml',
    buffer: Buffer.from(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <rect width="64" height="64" fill="#173060"/>
        <circle cx="32" cy="32" r="18" fill="#f4ead2"/>
      </svg>
    `, 'utf8'),
  })
  await expect(page.getByText(/local-cross-browser\.svg · 64×64/)).toBeVisible()
  await expect(page.locator('.image-drop img')).toBeVisible()
  expect(nonGetRequests).toEqual([])
})
