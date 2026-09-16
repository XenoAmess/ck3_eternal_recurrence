import { expect, test, type Page } from '@playwright/test'

async function readFitShardReceipts(page: Page) {
  return page.evaluate(async () => {
    const manifestUrl = new URL('asset-packs/ck3-1.19.0.6/manifest.json', document.baseURI)
    const manifest = await fetch(manifestUrl).then((response) => response.json()) as {
      fit_index: { url: string, features?: { url: string } }
    }
    const urls = [manifest.fit_index.url, manifest.fit_index.features?.url]
      .filter((value): value is string => Boolean(value))
    return Promise.all(urls.map(async (relativeUrl) => {
      const response = await fetch(new URL(relativeUrl, manifestUrl))
      const bytes = await response.arrayBuffer()
      const digest = await crypto.subtle.digest('SHA-256', bytes)
      return {
        relativeUrl,
        bytes: bytes.byteLength,
        sha256: Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, '0'))
          .join('').toUpperCase(),
      }
    }))
  })
}

test.skip(process.env.COA_E2E_USE_PREVIEW !== 'true', 'service worker is registered only by production builds')

test('restores the editor and on-demand asset shards offline from a versioned same-origin cache', async ({ context, page }) => {
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
  const onlineFitShards = await readFitShardReceipts(page)
  expect(onlineFitShards).toHaveLength(2)
  expect(onlineFitShards.every((item) => item.bytes > 0)).toBe(true)
  await context.setOffline(true)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: '家徽工坊' })).toBeVisible()
  await expect(page.getByText(/ck3-1\.19\.0\.6/)).toBeVisible({ timeout: 30_000 })
  expect(await readFitShardReceipts(page)).toEqual(onlineFitShards)
  expect(nonGetRequests).toEqual([])
})
