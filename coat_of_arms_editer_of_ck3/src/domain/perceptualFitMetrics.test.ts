import { describe, expect, it } from 'vitest'
import {
  measurePerceptualFitMetricsV2,
  measurePerceptualFitMetricsV3,
  PERCEPTUAL_FIT_SCORING_CONTRACT,
  PERCEPTUAL_FIT_SCORING_CONTRACT_V3,
  type PerceptualImage,
} from './perceptualFitMetrics'

function picture(
  width: number,
  height: number,
  sample: (x: number, y: number) => [number, number, number, number],
): PerceptualImage {
  const pixels = new Uint8ClampedArray(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) pixels.set(sample(x, y), (y * width + x) * 4)
  }
  return { width, height, pixels }
}

describe('perceptual fit metrics v2 shadow contract', () => {
  it('is exactly zero and deterministic for identical pixels', () => {
    const image = picture(32, 32, (x, y) => [x * 7, y * 7, (x + y) * 3, 255])
    const first = measurePerceptualFitMetricsV2(image, image)
    const second = measurePerceptualFitMetricsV2(image, image)
    expect(first).toEqual(second)
    expect(first.totalLoss).toBe(0)
    expect(first.structureLoss).toBe(0)
  })

  it('orders mild color and position perturbations before severe ones', () => {
    const target = picture(40, 40, (x, y) => (
      x >= 10 && x < 30 && y >= 12 && y < 28 ? [220, 40, 30, 255] : [18, 30, 48, 255]
    ))
    const mildColor = picture(40, 40, (x, y) => (
      x >= 10 && x < 30 && y >= 12 && y < 28 ? [212, 48, 38, 255] : [18, 30, 48, 255]
    ))
    const severeColor = picture(40, 40, (x, y) => (
      x >= 10 && x < 30 && y >= 12 && y < 28 ? [90, 180, 210, 255] : [18, 30, 48, 255]
    ))
    const mildShift = picture(40, 40, (x, y) => (
      x >= 11 && x < 31 && y >= 12 && y < 28 ? [220, 40, 30, 255] : [18, 30, 48, 255]
    ))
    const severeShift = picture(40, 40, (x, y) => (
      x >= 20 && x < 40 && y >= 12 && y < 28 ? [220, 40, 30, 255] : [18, 30, 48, 255]
    ))
    expect(measurePerceptualFitMetricsV2(target, mildColor).totalLoss)
      .toBeLessThan(measurePerceptualFitMetricsV2(target, severeColor).totalLoss)
    expect(measurePerceptualFitMetricsV2(target, mildShift).totalLoss)
      .toBeLessThan(measurePerceptualFitMetricsV2(target, severeShift).totalLoss)
  })

  it('reports topology differences separately from pixel color', () => {
    const ring = picture(40, 40, (x, y) => {
      const outer = x >= 8 && x < 32 && y >= 8 && y < 32
      const inner = x >= 14 && x < 26 && y >= 14 && y < 26
      return outer && !inner ? [240, 240, 240, 255] : [15, 15, 15, 255]
    })
    const filled = picture(40, 40, (x, y) => (
      x >= 8 && x < 32 && y >= 8 && y < 32 ? [240, 240, 240, 255] : [15, 15, 15, 255]
    ))
    const metrics = measurePerceptualFitMetricsV2(ring, filled)
    expect(metrics.structureLoss).toBeGreaterThan(0)
    expect(metrics.structure.targetEnclosedRegions).not.toBe(metrics.structure.renderedEnclosedRegions)
  })
})

describe('perceptual fit metrics v3 enclosed-region contract', () => {
  it('keeps v2 versioned while removing its false hole across split border regions', () => {
    const splitBoundary = picture(32, 32, (x) => (
      x < 16 ? [10, 10, 10, 255] : [245, 245, 245, 255]
    ))
    expect(PERCEPTUAL_FIT_SCORING_CONTRACT).toMatch(/-v2$/)
    expect(PERCEPTUAL_FIT_SCORING_CONTRACT_V3).toMatch(/-v3$/)
    expect(measurePerceptualFitMetricsV2(splitBoundary, splitBoundary).structure.targetEnclosedRegions)
      .toBe(1)
    expect(measurePerceptualFitMetricsV3(splitBoundary, splitBoundary).structure.targetEnclosedRegions)
      .toBe(0)
  })

  it('distinguishes a closed hole from an edge boundary open to the canvas', () => {
    const closed = picture(40, 40, (x, y) => (
      x >= 9 && x < 31 && y >= 9 && y < 31
        ? [245, 245, 245, 255]
        : [10, 10, 10, 255]
    ))
    const open = picture(40, 40, (x, y) => (
      x >= 9 && y >= 9 && y < 31
        ? [245, 245, 245, 255]
        : [10, 10, 10, 255]
    ))
    expect(measurePerceptualFitMetricsV3(closed, closed).structure.targetEnclosedRegions).toBe(1)
    expect(measurePerceptualFitMetricsV3(open, open).structure.targetEnclosedRegions).toBe(0)
  })

  it('is deterministic for a fine diagonal immediately around the frozen edge threshold', () => {
    const diagonal = (level: number) => picture(40, 40, (x, y) => (
      x > y ? [level, level, level, 255] : [0, 0, 0, 255]
    ))
    const below = diagonal(60)
    const above = diagonal(64)
    const first = measurePerceptualFitMetricsV3(above, above)
    const second = measurePerceptualFitMetricsV3(above, above)
    expect(first).toEqual(second)
    const belowMetrics = measurePerceptualFitMetricsV3(below, below)
    expect(belowMetrics.structure.targetComponents).toBe(2)
    expect(belowMetrics.structure.targetEnclosedRegions).toBe(0)
    expect(first.structure.targetComponents).toBe(1)
    expect(first.structure.targetEnclosedRegions).toBe(0)
  })
})
