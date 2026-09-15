import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import { fitImageToCoatOfArms, type FitImage, type FitTextureCandidate } from './imageFitter'
import { renderCoatOfArms } from './renderer'

const texture = (name: 'solid' | 'split' | 'square'): DecodedDds => {
  const size = 16
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const offset = (y * size + x) * 4
      if (name === 'split') pixels[offset + (x < size / 2 ? 0 : 1)] = 255
      else if (name === 'solid') pixels[offset] = 255
      else if (x >= 4 && x < 12 && y >= 4 && y < 12) pixels[offset] = 255
      pixels[offset + 3] = name === 'square' && !(x >= 4 && x < 12 && y >= 4 && y < 12) ? 0 : 255
    }
  }
  return { width: size, height: size, fourCC: 'DXT5', pixels }
}

const candidate = (name: string, value: DecodedDds): FitTextureCandidate => ({
  name, assetSha256: name.padEnd(64, '0').slice(0, 64).toUpperCase(), texture: value,
})

const asImage = (pixels: Uint8ClampedArray, size: number): FitImage => ({ width: size, height: size, pixels })

describe('browser image fitter', () => {
  it('recovers a known two-color pattern deterministically', () => {
    const size = 32
    const split = texture('split')
    const target = renderCoatOfArms({
      outerKey: 'coa', parent: '', pattern: 'split.dds',
      colors: ['rgb { 220 30 30 }', 'rgb { 30 50 220 }', 'rgb { 220 30 30 }'],
      coloredEmblems: [], texturedEmblems: [],
    }, { pattern: split, coloredEmblems: {} }, {}, size)
    expect(target).not.toBeNull()
    const patterns = [candidate('solid.dds', texture('solid')), candidate('split.dds', split)]
    const first = fitImageToCoatOfArms(asImage(target!.pixels, size), patterns, [], { resolution: 32 })
    const second = fitImageToCoatOfArms(asImage(target!.pixels, size), patterns, [], { resolution: 32 })
    expect(first.coatOfArms.pattern).toBe('split.dds')
    expect(second.coatOfArms).toEqual(first.coatOfArms)
    expect(second.metrics).toEqual(first.metrics)
  })

  it('adds a fitting emblem only when it materially improves the target', () => {
    const size = 32
    const solid = texture('solid')
    const square = texture('square')
    const target = renderCoatOfArms({
      outerKey: 'coa', parent: '', pattern: 'solid.dds',
      colors: ['rgb { 245 245 245 }', 'rgb { 245 245 245 }', 'rgb { 245 245 245 }'],
      coloredEmblems: [{
        texture: 'square.dds', colors: ['black', 'black', 'rgb { 20 20 20 }'], mask: [],
        instances: [{ position: [0.5, 0.5], scale: [0.7, 0.7], rotation: 0, depth: 1 }],
      }], texturedEmblems: [],
    }, { pattern: solid, coloredEmblems: { 'square.dds': square } }, { black: [0, 0, 0] }, size)
    expect(target).not.toBeNull()
    const result = fitImageToCoatOfArms(
      asImage(target!.pixels, size),
      [candidate('solid.dds', solid)],
      [candidate('square.dds', square)],
      { resolution: 32 },
    )
    expect(result.coatOfArms.coloredEmblems[0]?.texture).toBe('square.dds')
    expect(result.metrics.relativeImprovement).toBeGreaterThan(0.01)
    expect(result.provenance.searchBackend).toBe('cpu-reference')
  })
})

