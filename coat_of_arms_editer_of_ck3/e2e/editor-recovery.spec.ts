import { expect, test } from '@playwright/test'

const parentInput = (page: import('@playwright/test').Page) => (
  page.locator('.editor-pane .form-grid').first().locator('input').first()
)

test('groups edits into bounded undo/redo and restores one SHA-bound IndexedDB autosave', async ({ page }) => {
  // Autosave is a standalone project-model contract. Keep this test independent
  // from the exact-pack fit-index load so a constrained CI runner cannot starve
  // the IndexedDB observation behind unrelated asset hashing. Exact-pack loading
  // is covered by standalone-image-fit.spec.ts and service-worker-offline.spec.ts.
  await page.route('**/asset-packs/ck3-1.19.0.6/manifest.json', (route) => route.fulfill({
    status: 503,
    contentType: 'text/plain',
    body: 'asset pack intentionally unavailable for autosave isolation',
  }))
  const nonGetRequests: { method: string, url: string }[] = []
  page.on('request', (request) => {
    if (request.method() !== 'GET') nonGetRequests.push({ method: request.method(), url: request.url() })
  })
  await page.goto('/')
  await expect(page.getByText(/没有可恢复的自动保存/)).toBeVisible()
  await parentInput(page).fill('c_autosave_recovery')
  await expect(page.getByRole('button', { name: '撤销' })).toBeEnabled()
  await expect(page.getByText(/已自动保存 2 实例 · 单槽覆盖/)).toBeVisible({ timeout: 10_000 })

  await page.getByRole('button', { name: '撤销' }).click()
  await expect(parentInput(page)).toHaveValue('')
  await expect(page.getByRole('button', { name: '重做' })).toBeEnabled()
  await page.getByRole('button', { name: '重做' }).click()
  await expect(parentInput(page)).toHaveValue('c_autosave_recovery')
  await expect(page.getByText(/已自动保存 2 实例 · 单槽覆盖/)).toBeVisible({ timeout: 10_000 })

  await page.reload()
  const recovery = page.locator('.autosave-recovery')
  await expect(recovery).toContainText('2 个实例 · SHA-256 已验证')
  await recovery.getByRole('button', { name: '恢复' }).click()
  await expect(parentInput(page)).toHaveValue('c_autosave_recovery')
  await expect(recovery).toHaveCount(0)
  await expect(page.getByText(/已自动保存 2 实例 · 单槽覆盖/)).toBeVisible({ timeout: 10_000 })

  await page.reload()
  await expect(page.locator('.autosave-recovery')).toBeVisible()
  await page.locator('.autosave-recovery').getByRole('button', { name: '丢弃' }).click()
  await expect(page.locator('.autosave-recovery')).toHaveCount(0)
  await page.reload()
  await expect(page.getByText(/没有可恢复的自动保存/)).toBeVisible()
  expect(nonGetRequests).toEqual([])
})
