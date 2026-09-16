import { expect, test, type Locator, type Page } from '@playwright/test'

function instanceInputs(page: Page, index = 0): Locator {
  return page.locator(`[data-instance-index="${index}"] .el-input-number input`)
}

async function center(locator: Locator) {
  await locator.scrollIntoViewIfNeeded()
  const box = await locator.boundingBox()
  if (!box) throw new Error('visual transform handle has no bounding box')
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 }
}

test('directly moves, scales, rotates and undoes the selected CK3 instance', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('visual-transform-box')).toHaveCount(0)
  await page.getByTestId('toggle-visual-guides').click()
  await expect(page.getByTestId('visual-transform-box')).toBeVisible()
  await expect(page.locator('[data-instance-index="0"]')).toHaveClass(/selected/)

  const moveStart = await center(page.getByTestId('visual-move-handle'))
  await page.mouse.move(moveStart.x, moveStart.y)
  await page.mouse.down()
  await expect(page.getByTestId('visual-transform-box')).toHaveClass(/active/)
  await page.mouse.move(moveStart.x + 32, moveStart.y + 30, { steps: 4 })
  await page.mouse.up()
  const movedX = Number(await instanceInputs(page).nth(0).inputValue())
  const movedY = Number(await instanceInputs(page).nth(1).inputValue())
  expect(movedX).toBeGreaterThan(0.4)
  expect(movedY).toBeGreaterThan(0.58)
  await expect(page.getByRole('button', { name: '撤销' })).toBeEnabled()
  await page.getByRole('button', { name: '撤销' }).click()
  await expect(page.getByText(/已撤销/)).toBeVisible()
  await expect(instanceInputs(page).nth(0)).toHaveValue('0.3')
  await expect(instanceInputs(page).nth(1)).toHaveValue('0.5')

  const scaleStart = await center(page.getByTestId('visual-scale-handle'))
  const moveCenter = await center(page.getByTestId('visual-move-handle'))
  const scaleVector = { x: scaleStart.x - moveCenter.x, y: scaleStart.y - moveCenter.y }
  await page.mouse.move(scaleStart.x, scaleStart.y)
  await page.mouse.down()
  await page.mouse.move(
    moveCenter.x + scaleVector.x * 1.45,
    moveCenter.y + scaleVector.y * 1.45,
    { steps: 4 },
  )
  await page.mouse.up()
  const scaledX = Number(await instanceInputs(page).nth(2).inputValue())
  const scaledY = Number(await instanceInputs(page).nth(3).inputValue())
  expect(scaledX).toBeGreaterThan(0.45)
  expect(scaledY).toBeGreaterThan(0.45)
  await page.getByRole('button', { name: '撤销' }).click()
  await expect(instanceInputs(page).nth(2)).toHaveValue('0.35')
  await expect(instanceInputs(page).nth(3)).toHaveValue('0.35')

  const rotateStart = await center(page.getByTestId('visual-rotate-handle'))
  const rotateCenter = await center(page.getByTestId('visual-move-handle'))
  const rotateVector = { x: rotateStart.x - rotateCenter.x, y: rotateStart.y - rotateCenter.y }
  await page.mouse.move(rotateStart.x, rotateStart.y)
  await page.mouse.down()
  await page.mouse.move(
    rotateCenter.x - rotateVector.y,
    rotateCenter.y + rotateVector.x,
    { steps: 4 },
  )
  await page.mouse.up()
  expect(Number(await instanceInputs(page).nth(4).inputValue())).toBeCloseTo(70, 0)
  await page.getByRole('button', { name: '撤销' }).click()
  await expect(instanceInputs(page).nth(4)).toHaveValue('-20')

  await page.locator('[data-instance-index="1"]').getByRole('button', { name: '在预览中编辑' }).click()
  await expect(page.getByText(/正在编辑图层 1 · 实例 2/)).toBeVisible()
  await expect(page.locator('[data-instance-index="1"]')).toHaveClass(/selected/)
})
