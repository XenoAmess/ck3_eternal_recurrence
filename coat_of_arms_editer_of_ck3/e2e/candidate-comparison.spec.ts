import { expect, test } from '@playwright/test'

const parentInput = (page: import('@playwright/test').Page) => (
  page.locator('.editor-pane .form-grid').first().locator('input').first()
)

test('keeps three exact comparison snapshots and reloads one into the complete model', async ({ page }) => {
  const nonGetRequests: { method: string, url: string }[] = []
  page.on('request', (request) => {
    if (request.method() !== 'GET') nonGetRequests.push({ method: request.method(), url: request.url() })
  })
  await page.goto('/')
  const comparison = page.getByTestId('candidate-comparison')
  const save = comparison.getByRole('button', { name: '保存当前候选' })

  await save.click()
  await expect(comparison.locator('.candidate-card')).toHaveCount(1)
  await expect(comparison.getByText('未绑定可比拟合指标')).toHaveCount(1)
  await expect(comparison.getByText('当前构图')).toHaveCount(1)

  await parentInput(page).fill('c_candidate_2')
  await save.click()
  await parentInput(page).fill('c_candidate_3')
  await save.click()
  await expect(comparison.locator('.candidate-card')).toHaveCount(3)

  await parentInput(page).fill('c_not_saved_fourth')
  await expect(save).toBeDisabled()
  await comparison.locator('[data-candidate-id="candidate-1"]').getByRole('button', { name: '载入' }).click()
  await expect(parentInput(page)).toHaveValue('')
  await expect(comparison.getByText('当前构图')).toHaveCount(1)
  await expect(save).toBeEnabled()
  await save.click()
  await expect(comparison.locator('.candidate-card')).toHaveCount(3)

  await comparison.locator('[data-candidate-id="candidate-2"]').getByRole('button', { name: '删除' }).click()
  await expect(comparison.locator('.candidate-card')).toHaveCount(2)
  expect(nonGetRequests).toEqual([])
})
