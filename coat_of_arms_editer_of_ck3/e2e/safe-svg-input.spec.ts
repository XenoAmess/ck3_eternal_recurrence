import { expect, test } from '@playwright/test'

const upload = (page: import('@playwright/test').Page, name: string, source: string) => (
  page.locator('.image-drop input').setInputFiles({
    name,
    mimeType: 'image/svg+xml',
    buffer: Buffer.from(source, 'utf8'),
  })
)

test('rasterizes bounded local SVG geometry and rejects executable or external content before decode', async ({ page }) => {
  const externalRequests: string[] = []
  const nonGetRequests: string[] = []
  page.on('request', (request) => {
    if (request.url().includes('evil.invalid')) externalRequests.push(request.url())
    if (request.method() !== 'GET') nonGetRequests.push(request.url())
  })
  await page.goto('/')

  await upload(page, 'safe-vector.svg', `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240">
      <defs><clipPath id="safeClip"><circle cx="160" cy="120" r="105"/></clipPath></defs>
      <rect width="320" height="240" fill="#f4ead2"/>
      <g clip-path="url(#safeClip)">
        <path d="M20 220 L160 20 L300 220 Z" fill="#a31f2b"/>
        <circle cx="160" cy="130" r="54" fill="#171515" stroke="#fff" stroke-width="8"/>
      </g>
    </svg>
  `)
  await expect(page.getByText(/safe-vector\.svg · 320×240/)).toBeVisible()
  await expect(page.locator('.image-drop img')).toBeVisible()
  await expect(page.getByRole('button', { name: '开始本地拟合' })).toBeEnabled()

  await upload(page, 'external.svg', `
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
      <image href="https://evil.invalid/tracker.png" width="200" height="200"/>
    </svg>
  `)
  await expect(page.locator('.fit-report > p')).toContainText('图片拒绝：SVG 包含不允许的元素 <image>')
  await expect(page.locator('.image-drop img')).toHaveCount(0)

  await upload(page, 'external-use.svg', `
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
      <use href="https://evil.invalid/external.svg#shape"/>
    </svg>
  `)
  await expect(page.locator('.fit-report > p')).toContainText('不允许外部或可执行 URI')

  await upload(page, 'script.svg', `
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
      <script>fetch('https://evil.invalid/script')</script>
      <rect width="200" height="200" fill="red"/>
    </svg>
  `)
  await expect(page.locator('.fit-report > p')).toContainText('图片拒绝：SVG 包含不允许的元素 <script>')

  await upload(page, 'event.svg', `
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" onload="fetch('https://evil.invalid/run')">
      <rect width="200" height="200" fill="red"/>
    </svg>
  `)
  await expect(page.locator('.fit-report > p')).toContainText('图片拒绝：SVG 不允许属性 onload')
  expect(externalRequests).toEqual([])
  expect(nonGetRequests).toEqual([])
})
