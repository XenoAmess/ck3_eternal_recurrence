import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import {
  getOverlay,
  patternMaskAlpha,
  renderCoatOfArms,
  resolveColor,
  shadeColoredEmblem,
  shadePattern,
} from './renderer'
import { createCoatOfArms } from './types'

const closeRgb = (actual: number[], expected: number[]) => {
  expected.forEach((value, index) => expect(actual[index]).toBeCloseTo(value, 6))
}

describe('shader-grounded coat-of-arms renderer', () => {
  it('implements Clausewitz GetOverlay with its legacy parameter flip', () => {
    closeRgb(
      getOverlay([0.8, 0.2, 0.4], [0.25, 0.75, 0.5], 1),
      [0.4, 0.6, 0.4],
    )
    closeRgb(
      getOverlay([0.8, 0.2, 0.4], [0.25, 0.75, 0.5], 0.5),
      [0.6, 0.4, 0.4],
    )
  })

  it('resolves named, RGB, HSV, and HSV360 color expressions', () => {
    const named = { red: [0.45, 0.1332, 0.09] as [number, number, number] }
    closeRgb(resolveColor('red', named)!, [0.45, 0.1332, 0.09])
    closeRgb(resolveColor('rgb { 255 128 0 }', named)!, [1, 128 / 255, 0])
    closeRgb(resolveColor('hsv { 0 1 1 }', named)!, [1, 0, 0])
    closeRgb(resolveColor('hsv360 { 120 100 100 }', named)!, [0, 1, 0])
    expect(resolveColor('missing', named)).toBeNull()
  })

  it('follows the shipped pattern and colored-emblem channel order', () => {
    const colors: [[number, number, number], [number, number, number], [number, number, number]] = [
      [1, 0, 0], [0, 1, 0], [0, 0, 1],
    ]
    closeRgb(shadePattern([1, 0, 0], colors), colors[0])
    closeRgb(shadePattern([0, 1, 0], colors), colors[1])
    closeRgb(shadePattern([0, 0, 1], colors), colors[2])
    closeRgb(shadeColoredEmblem([0, 1, 0.5], colors), [0, 1, 0])
  })

  it('isolates cumulative pattern channels before applying mask indices', () => {
    expect(patternMaskAlpha([1, 0, 0], [1])).toBe(1)
    expect(patternMaskAlpha([1, 1, 0], [1])).toBe(0)
    expect(patternMaskAlpha([1, 1, 0], [2])).toBe(1)
    expect(patternMaskAlpha([1, 1, 1], [3])).toBe(1)
    expect(patternMaskAlpha([1, 1, 1], [])).toBe(1)
  })

  it('renders a deterministic pattern without DOM or CK3', () => {
    const texture: DecodedDds = {
      width: 1,
      height: 1,
      fourCC: 'DXT1',
      pixels: new Uint8ClampedArray([255, 0, 0, 255]),
    }
    const coatOfArms = createCoatOfArms()
    coatOfArms.colors = ['rgb { 64 128 192 }', 'white', 'black']
    coatOfArms.coloredEmblems = []

    const result = renderCoatOfArms(
      coatOfArms,
      { pattern: texture, coloredEmblems: {} },
      {},
      2,
    )

    expect(result?.pixels).toEqual(new Uint8ClampedArray([
      64, 128, 192, 255, 64, 128, 192, 255,
      64, 128, 192, 255, 64, 128, 192, 255,
    ]))
  })

  it('uses the decoded DDS mip chain for minified full-surface textures', () => {
    const pixels = (size: number, rgba: [number, number, number, number]) => {
      const result = new Uint8ClampedArray(size * size * 4)
      for (let offset = 0; offset < result.length; offset += 4) result.set(rgba, offset)
      return result
    }
    const pattern: DecodedDds = {
      width: 4,
      height: 4,
      fourCC: 'BGRA8',
      pixels: pixels(4, [255, 0, 0, 255]),
      mipmaps: [
        { width: 2, height: 2, pixels: pixels(2, [0, 255, 0, 255]) },
        { width: 1, height: 1, pixels: pixels(1, [0, 0, 255, 255]) },
      ],
    }
    const coatOfArms = createCoatOfArms()
    coatOfArms.colors = ['rgb { 255 0 0 }', 'rgb { 0 255 0 }', 'rgb { 0 0 255 }']
    coatOfArms.coloredEmblems = []

    const result = renderCoatOfArms(
      coatOfArms,
      { pattern, coloredEmblems: {} },
      {},
      1,
    )

    expect(result?.pixels).toEqual(new Uint8ClampedArray([0, 0, 255, 255]))
  })

  it('uses transform-derived mip LOD for minified colored emblems', () => {
    const solid = (
      width: number,
      height: number,
      rgba: [number, number, number, number],
    ) => {
      const result = new Uint8ClampedArray(width * height * 4)
      for (let offset = 0; offset < result.length; offset += 4) result.set(rgba, offset)
      return result
    }
    const pattern: DecodedDds = {
      width: 1,
      height: 1,
      fourCC: 'DXT1',
      pixels: new Uint8ClampedArray([255, 0, 0, 255]),
    }
    const emblem: DecodedDds = {
      width: 4,
      height: 4,
      fourCC: 'BGRA8',
      pixels: solid(4, 4, [0, 0, 128, 255]),
      mipmaps: [
        { width: 2, height: 2, pixels: solid(2, 2, [0, 0, 128, 0]) },
        { width: 1, height: 1, pixels: solid(1, 1, [0, 0, 128, 0]) },
      ],
    }
    const coatOfArms = createCoatOfArms()
    coatOfArms.colors = ['rgb { 0 0 0 }', 'rgb { 0 0 0 }', 'rgb { 0 0 0 }']
    coatOfArms.coloredEmblems = [{
      texture: 'minified.dds',
      colors: ['rgb { 255 255 255 }', 'rgb { 255 255 255 }', 'rgb { 255 255 255 }'],
      mask: [],
      instances: [{ position: [0.5, 0.5], scale: [0.125, 0.125], rotation: 0, depth: 1 }],
    }]

    const result = renderCoatOfArms(
      coatOfArms,
      { pattern, coloredEmblems: { 'minified.dds': emblem } },
      {},
      8,
    )

    expect(result?.pixels.every((value, index) => index % 4 === 3 ? value === 255 : value === 0)).toBe(true)
  })

  it('alpha-blends a raw textured emblem before colored emblems', () => {
    const pattern: DecodedDds = {
      width: 1, height: 1, fourCC: 'DXT1',
      pixels: new Uint8ClampedArray([255, 0, 0, 255]),
    }
    const textured: DecodedDds = {
      width: 1, height: 1, fourCC: 'BGRA8',
      pixels: new Uint8ClampedArray([0, 255, 0, 128]),
    }
    const coatOfArms = createCoatOfArms()
    coatOfArms.colors = ['rgb { 64 128 192 }', 'white', 'black']
    coatOfArms.coloredEmblems = []
    coatOfArms.texturedEmblems = [{ texture: '_default.dds' }]

    const result = renderCoatOfArms(
      coatOfArms,
      { pattern, coloredEmblems: {}, texturedEmblems: { '_default.dds': textured } },
      {},
      1,
    )
    expect(result?.pixels).toEqual(new Uint8ClampedArray([32, 192, 96, 255]))
  })

  it('uses CK3 native clockwise screen-space rotation by default', () => {
    const pattern: DecodedDds = {
      width: 1, height: 1, fourCC: 'DXT1',
      pixels: new Uint8ClampedArray([255, 0, 0, 255]),
    }
    const emblemPixels = new Uint8ClampedArray(5 * 5 * 4)
    const marker = (0 * 5 + 2) * 4
    emblemPixels.set([0, 255, 128, 255], marker)
    const emblem: DecodedDds = {
      width: 5, height: 5, fourCC: 'BGRA8', pixels: emblemPixels,
    }
    const coatOfArms = createCoatOfArms()
    coatOfArms.colors = ['black', 'black', 'black']
    coatOfArms.coloredEmblems = [{
      texture: 'marker.dds',
      colors: ['white', 'white', 'white'],
      mask: [],
      instances: [{ position: [0.5, 0.5], scale: [0.8, 0.5], rotation: 90, depth: 1 }],
    }]
    const assets = { pattern, coloredEmblems: { 'marker.dds': emblem } }
    const nativeDefault = renderCoatOfArms(coatOfArms, assets, {}, 21)
    const explicitNative = renderCoatOfArms(
      coatOfArms,
      assets,
      {},
      21,
      { emblemRotationSign: -1 },
    )
    const opposite = renderCoatOfArms(
      coatOfArms,
      assets,
      {},
      21,
      { emblemRotationSign: 1 },
    )
    expect(nativeDefault?.pixels).toEqual(explicitNative?.pixels)
    expect(nativeDefault?.pixels).not.toEqual(opposite?.pixels)
  })

  it('uses CK3 native descending depth order with smaller depth on top', () => {
    const pattern: DecodedDds = {
      width: 1, height: 1, fourCC: 'DXT1',
      pixels: new Uint8ClampedArray([255, 0, 0, 255]),
    }
    const opaque: DecodedDds = {
      width: 1, height: 1, fourCC: 'BGRA8',
      pixels: new Uint8ClampedArray([0, 255, 128, 255]),
    }
    const coatOfArms = createCoatOfArms()
    coatOfArms.colors = ['black', 'black', 'black']
    coatOfArms.coloredEmblems = [
      {
        texture: 'opaque.dds',
        colors: ['rgb { 255 0 0 }', 'rgb { 255 0 0 }', 'rgb { 255 0 0 }'],
        mask: [],
        instances: [{ position: [0.5, 0.5], scale: [1, 1], rotation: 0, depth: 1 }],
      },
      {
        texture: 'opaque.dds',
        colors: ['rgb { 0 255 0 }', 'rgb { 0 255 0 }', 'rgb { 0 255 0 }'],
        mask: [],
        instances: [{ position: [0.5, 0.5], scale: [1, 1], rotation: 0, depth: 2 }],
      },
    ]
    const assets = { pattern, coloredEmblems: { 'opaque.dds': opaque } }
    const nativeDefault = renderCoatOfArms(coatOfArms, assets, {}, 1)
    const explicitNative = renderCoatOfArms(
      coatOfArms,
      assets,
      {},
      1,
      { emblemDepthOrder: 'descending' },
    )
    const opposite = renderCoatOfArms(
      coatOfArms,
      assets,
      {},
      1,
      { emblemDepthOrder: 'ascending' },
    )
    expect(nativeDefault?.pixels).toEqual(explicitNative?.pixels)
    expect(nativeDefault?.pixels[0]).toBeGreaterThan(250)
    expect(nativeDefault?.pixels[1]).toBeLessThan(2)
    expect(opposite?.pixels[0]).toBeLessThan(2)
    expect(opposite?.pixels[1]).toBeGreaterThan(250)
  })
})
