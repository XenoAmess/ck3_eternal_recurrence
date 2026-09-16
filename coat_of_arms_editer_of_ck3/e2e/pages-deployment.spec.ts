import { expect, test } from '@playwright/test'

const pagesUrl = 'https://xenoamess.github.io/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/'
const expectedHash = process.env.COA_EXPECTED_PAGES_HASH?.slice(0, 8)

test('published nested Pages route exposes the immutable build version', async ({ page }) => {
  test.skip(!expectedHash, 'Set COA_EXPECTED_PAGES_HASH to verify a deployed revision')
  test.setTimeout(60_000)
  const response = await page.goto(pagesUrl, { waitUntil: 'networkidle' })
  expect(response?.status()).toBe(200)
  expect(new URL(page.url()).pathname).toBe('/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/')
  await expect(page.getByTestId('page-version')).toContainText(expectedHash!)
  await expect(page.getByTestId('page-version')).toContainText(
    /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z/,
  )
  await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })
})
