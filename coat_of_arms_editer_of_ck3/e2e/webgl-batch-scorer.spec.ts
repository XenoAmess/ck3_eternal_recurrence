import { expect, test } from '@playwright/test'

test('WebGL2 texture-array batch scorer matches CPU and fails closed after context loss', async ({ page }) => {
  await page.goto('/')
  const evidence = await page.evaluate(async () => {
    const { measureImageFitLosses } = await import('../src/domain/imageFitter')
    const { createWebGl2BatchScorer } = await import('../src/domain/webglBatchScorer')
    const width = 16
    const height = 12
    const pixels = (variant: number) => {
      const result = new Uint8ClampedArray(width * height * 4)
      for (let y = 0; y < height; y += 1) {
        for (let x = 0; x < width; x += 1) {
          const offset = (y * width + x) * 4
          result[offset] = (x * 17 + variant * 13) % 256
          result[offset + 1] = (y * 23 + variant * 29) % 256
          result[offset + 2] = ((x + y) * 11 + variant * 7) % 256
          result[offset + 3] = (x + y) % 5 === 0 ? 128 : 255
        }
      }
      return result
    }
    const target = { width, height, pixels: pixels(0) }
    const candidates = [0, 1, 2, 3].map((variant) => ({ width, height, pixels: pixels(variant) }))
    const scorer = createWebGl2BatchScorer(target)
    if (!scorer) return { available: false }
    const gpu = scorer.score(candidates)
    const cpu = candidates.map((candidate) => measureImageFitLosses(target, candidate))
    const deltas = gpu?.map((metric, index) => Math.max(
      Math.abs(metric.colorLoss - cpu[index].colorLoss),
      Math.abs(metric.edgeLoss - cpu[index].edgeLoss),
      Math.abs(metric.totalLoss - cpu[index].totalLoss),
    )) ?? []
    const lost = scorer.loseContextForTest()
    const afterLoss = scorer.score(candidates)
    const status = scorer.status()
    scorer.dispose()
    return {
      available: true,
      backend: scorer.backend,
      maximumBatchSize: scorer.maximumBatchSize,
      candidateCount: gpu?.length ?? 0,
      maximumMetricDelta: Math.max(...deltas),
      lost,
      afterLoss,
      status,
    }
  })

  expect(evidence).toMatchObject({
    available: true,
    backend: 'webgl2-texture-array-reduction-float-v1',
    candidateCount: 4,
    lost: true,
    afterLoss: null,
    status: 'context_lost',
  })
  expect(evidence.maximumBatchSize).toBeGreaterThanOrEqual(4)
  expect(evidence.maximumMetricDelta).toBeLessThan(2e-6)
})
