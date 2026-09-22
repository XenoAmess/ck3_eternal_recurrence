import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const exactPack = resolve('public/asset-packs/ck3-1.19.0.6/manifest.json')
const qualityFitCompletionTimeoutMs = 15 * 60_000
const qualityFitTestTimeoutMs = 20 * 60_000

test('production workflow uses only same-origin static GET requests', async ({ page }) => {
  // Epsilon-Q deliberately spends minutes on complete-pack exact-DDS quality
  // refinement. This gate proves the network boundary, not generation speed.
  test.setTimeout(qualityFitTestTimeoutMs)
  test.skip(!existsSync(exactPack), 'the tracked exact-build static asset pack is required')

  const requests: Array<{ method: string, url: string }> = []
  page.on('request', (request) => requests.push({
    method: request.method(),
    url: request.url(),
  }))
  await page.addInitScript(() => {
    let clipboardText = ''
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        readText: async () => clipboardText,
        writeText: async (value: string) => { clipboardText = value },
      },
    })
  })

  await page.goto('/')
  await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })

  const pngBase64 = await page.evaluate(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 64
    canvas.height = 64
    const context = canvas.getContext('2d')!
    context.fillStyle = '#ba2028'
    context.fillRect(0, 0, 32, 64)
    context.fillStyle = '#eee7d8'
    context.fillRect(32, 0, 32, 64)
    return canvas.toDataURL('image/png').split(',')[1]
  })
  await page.locator('.fit-budget input').fill('1')
  await page.locator('.image-drop input').setInputFiles({
    name: 'private-target.png',
    mimeType: 'image/png',
    buffer: Buffer.from(pngBase64, 'base64'),
  })
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.getByText(/完成 · .*从完整库评估 \d+ 个构图/)).toBeVisible({
    timeout: qualityFitCompletionTimeoutMs,
  })

  await page.getByRole('button', { name: '复制 CK3 代码' }).click()
  const copied = await page.evaluate(() => navigator.clipboard.readText())
  expect(copied).toContain('pattern =')

  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: '保存项目' }).click()
  const download = await downloadPromise
  const projectPath = await download.path()
  expect(projectPath).toBeTruthy()
  await page.getByRole('button', { name: '重置' }).click()
  await page.getByTestId('project-file-input').setInputFiles(projectPath!)
  await expect(page.locator('.output-block pre')).toContainText('pattern =')

  const httpRequests = requests.filter(({ url }) => /^https?:/i.test(url))
  expect(httpRequests.length).toBeGreaterThan(0)
  for (const request of httpRequests) {
    const url = new URL(request.url)
    expect(url.origin).toBe('http://127.0.0.1:4173')
    expect(request.method).toBe('GET')
    expect(url.pathname).not.toContain('/api/')
    expect(url.href).not.toContain('private-target.png')
  }
  expect(JSON.stringify(requests)).not.toMatch(/localhost:8080|127\.0\.0\.1:8080|ck3\/coat-of-arms/i)
  console.log(JSON.stringify({
    httpRequests: httpRequests.length,
    methods: [...new Set(httpRequests.map((request) => request.method))],
    origins: [...new Set(httpRequests.map((request) => new URL(request.url).origin))],
    backendRequests: 0,
    userContentRequests: 0,
  }))
})
