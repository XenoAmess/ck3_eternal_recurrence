import { expect, test } from '@playwright/test'

test.skip(process.env.COA_E2E_USE_PREVIEW !== 'true', 'service worker is registered only by production builds')

test('restores the editor and exact asset pack offline from a versioned same-origin cache', async ({ context, page }) => {
  const nonGetRequests: string[] = []
  page.on('request', (request) => {
    if (request.method() !== 'GET') nonGetRequests.push(request.url())
  })

  await page.goto('/')
  await expect(page.getByText(/ck3-1\.19\.0\.6/)).toBeVisible({ timeout: 30_000 })
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready
    if (!navigator.serviceWorker.controller) {
      await new Promise<void>((resolve) => {
        navigator.serviceWorker.addEventListener('controllerchange', () => resolve(), { once: true })
      })
    }
  })

  // The controlled reload stores the manifest and the exact assets actually
  // consumed by the initial editor. User-provided blob/data URLs never enter
  // the service worker's same-origin HTTP request path.
  await page.reload()
  await expect(page.getByText(/ck3-1\.19\.0\.6/)).toBeVisible({ timeout: 30_000 })
  await context.setOffline(true)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: '家徽工坊' })).toBeVisible()
  await expect(page.getByText(/ck3-1\.19\.0\.6/)).toBeVisible({ timeout: 30_000 })
  expect(nonGetRequests).toEqual([])
})
