import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import { computeFitTextureShapeFeatures, FIT_SHAPE_DESCRIPTOR_SIZE } from './shapeFeatures'

function squareTexture(): DecodedDds {
  const size = 8
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const offset = (y * size + x) * 4
      if (x >= 2 && x < 6 && y >= 1 && y < 7) {
        pixels[offset] = 255
        pixels[offset + 3] = 255
      }
    }
  }
  return { width: size, height: size, fourCC: 'BGRA8', pixels }
}

describe('fit shape features', () => {
  it('precomputes bounds, channel energy, contour energy and descriptor', () => {
    const features = computeFitTextureShapeFeatures(squareTexture())
    expect(features.contentBounds).toEqual([0.25, 0.125, 0.75, 0.875])
    expect(features.contentCenter).toEqual([0.5, 0.5])
    expect(features.contentSpan).toEqual([0.5, 0.75])
    expect(features.alphaEnergy).toBeCloseTo(24 / 64)
    expect(features.channelEnergy).toEqual([24 / 64, 0, 0])
    expect(features.contourEnergy).toBeGreaterThan(0)
    expect(features.descriptor).toHaveLength(FIT_SHAPE_DESCRIPTOR_SIZE ** 2)
    expect(Math.max(...features.descriptor)).toBe(1)
  })

  it('uses alpha as the shape signal for black opaque emblems', () => {
    const pixels = new Uint8ClampedArray(4 * 4 * 4)
    for (let index = 0; index < 16; index += 1) pixels[index * 4 + 3] = 255
    const features = computeFitTextureShapeFeatures({ width: 4, height: 4, fourCC: 'BGRA8', pixels })
    expect(features.alphaEnergy).toBe(1)
    expect(features.channelEnergy).toEqual([0, 0, 0])
    expect(features.contentBounds).toEqual([0, 0, 1, 1])
    expect(Math.min(...features.descriptor)).toBe(1)
  })
})
