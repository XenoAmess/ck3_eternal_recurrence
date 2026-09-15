import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import {
  dominantColors,
  fitImageToCoatOfArms,
  resizeFitImage,
  type FitImage,
  type FitTextureCandidate,
  type ImageFitProgress,
} from './imageFitter'
import { renderCoatOfArms } from './renderer'

const texture = (name: 'solid' | 'split' | 'square' | 'neutralBlock'): DecodedDds => {
  const size = 16
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const offset = (y * size + x) * 4
      if (name === 'neutralBlock') pixels[offset + 2] = 128
      else if (name === 'split') pixels[offset + (x < size / 2 ? 0 : 1)] = 255
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
    const progress: ImageFitProgress[] = []
    const result = fitImageToCoatOfArms(
      asImage(target!.pixels, size),
      [candidate('solid.dds', solid)],
      [candidate('square.dds', square)],
      { resolution: 32, onProgress: (update) => progress.push(update) },
    )
    expect(result.coatOfArms.coloredEmblems[0]?.texture).toBe('square.dds')
    expect(result.metrics.relativeImprovement).toBeGreaterThan(0.01)
    expect(result.provenance.searchBackend).toBe('cpu-reference')
    expect(new Set(progress.map((update) => update.phase))).toEqual(new Set(['background', 'coarse', 'refine']))
    for (const phase of ['background', 'coarse', 'refine'] as const) {
      expect(progress.some((update) => update.phase === phase && update.percent === 100)).toBe(true)
    }
    expect(progress.every((update) => (
      update.total > 0
      && update.completed >= 0
      && update.completed <= update.total
      && update.percent >= 0
      && update.percent <= 100
    ))).toBe(true)
  })

  it('accepts a 10000-layer search budget without applying a product cap', () => {
    const size = 16
    const solid = texture('solid')
    const target = renderCoatOfArms({
      outerKey: 'coa', parent: '', pattern: 'solid.dds',
      colors: ['rgb { 80 80 80 }', 'rgb { 80 80 80 }', 'rgb { 80 80 80 }'],
      coloredEmblems: [], texturedEmblems: [],
    }, { pattern: solid, coloredEmblems: {} }, {}, size)
    expect(target).not.toBeNull()
    const result = fitImageToCoatOfArms(
      asImage(target!.pixels, size),
      [candidate('solid.dds', solid)],
      [candidate('square.dds', texture('square'))],
      { resolution: size, maxLayers: 10_000 },
    )
    expect(result.provenance.layerBudget).toBe(10_000)
    expect(result.provenance.selectedLayers).toBe(0)
    expect(result.provenance.terminationReason).toBe('exact_match')
  })

  it('ignores transparent padding instead of turning it into a white target', () => {
    const pixels = new Uint8ClampedArray(16 * 16 * 4)
    for (let offset = 0; offset < pixels.length; offset += 4) {
      pixels[offset] = 255
      pixels[offset + 1] = 0
      pixels[offset + 2] = 255
      pixels[offset + 3] = 0
    }
    for (let y = 6; y < 10; y += 1) {
      for (let x = 6; x < 10; x += 1) {
        const offset = (y * 16 + x) * 4
        pixels[offset] = 12
        pixels[offset + 1] = 34
        pixels[offset + 2] = 56
        pixels[offset + 3] = 255
      }
    }
    const resized = resizeFitImage(asImage(pixels, 16), 8)
    expect(Math.max(...dominantColors(resized, 1)[0])).toBeLessThan(80)
    expect(resized.pixels[3]).toBe(0)
  })

  it('recovers an off-center anisotropic emblem with sub-degree rotation refinement', () => {
    const size = 56
    const solid = texture('solid')
    const square = texture('square')
    const targetRotation = 17.3
    const target = renderCoatOfArms({
      outerKey: 'coa', parent: '', pattern: 'solid.dds',
      colors: ['rgb { 245 245 245 }', 'rgb { 245 245 245 }', 'rgb { 245 245 245 }'],
      coloredEmblems: [{
        texture: 'square.dds', colors: ['black', 'black', 'black'], mask: [],
        instances: [{ position: [0.63, 0.38], scale: [0.72, 0.34], rotation: targetRotation, depth: 1 }],
      }], texturedEmblems: [],
    }, { pattern: solid, coloredEmblems: { 'square.dds': square } }, { black: [0, 0, 0] }, size)
    expect(target).not.toBeNull()
    const result = fitImageToCoatOfArms(
      asImage(target!.pixels, size),
      [candidate('solid.dds', solid)],
      [candidate('square.dds', square)],
      { resolution: size, maxLayers: 1 },
    )
    const instance = result.coatOfArms.coloredEmblems[0]?.instances[0]
    expect(instance).toBeDefined()
    const rotationalError = Math.min(...Array.from({ length: 9 }, (_, index) => (index - 4) * 90)
      .map((symmetry) => Math.abs(instance!.rotation - targetRotation - symmetry)))
    expect(rotationalError).toBeLessThanOrEqual(0.2)
    expect(instance!.position[0]).toBeCloseTo(0.63, 1)
    expect(instance!.position[1]).toBeCloseTo(0.38, 1)
    expect(result.metrics.relativeImprovement).toBeGreaterThan(0.6)
  })

  it('reconstructs separated details by stacking repeated native DDS layers', () => {
    const size = 32
    const solid = texture('solid')
    const square = texture('square')
    const target = renderCoatOfArms({
      outerKey: 'coa', parent: '', pattern: 'solid.dds',
      colors: ['rgb { 245 245 245 }', 'rgb { 245 245 245 }', 'rgb { 245 245 245 }'],
      coloredEmblems: [
        {
          texture: 'square.dds', colors: ['black', 'black', 'rgb { 20 20 20 }'], mask: [],
          instances: [{ position: [0.28, 0.5], scale: [0.34, 0.34], rotation: 0, depth: 1 }],
        },
        {
          texture: 'square.dds', colors: ['rgb { 180 25 30 }', 'black', 'black'], mask: [],
          instances: [{ position: [0.72, 0.5], scale: [0.34, 0.34], rotation: 0, depth: 2 }],
        },
      ],
      texturedEmblems: [],
    }, { pattern: solid, coloredEmblems: { 'square.dds': square } }, { black: [0, 0, 0] }, size)
    expect(target).not.toBeNull()
    const result = fitImageToCoatOfArms(
      asImage(target!.pixels, size),
      [candidate('solid.dds', solid)],
      [candidate('square.dds', square)],
      { resolution: size, maxLayers: 3, minRelativeLayerImprovement: 0.0001 },
    )
    expect(result.provenance.algorithm).toBe('ck3-coa-browser-fit-v3-shape-beam')
    expect(result.provenance.selectedLayers).toBeGreaterThanOrEqual(2)
    expect(result.coatOfArms.coloredEmblems).toHaveLength(result.provenance.selectedLayers)
    expect(result.provenance.layerLosses).toHaveLength(result.provenance.selectedLayers + 1)
    for (let index = 1; index < result.provenance.layerLosses.length; index += 1) {
      expect(result.provenance.layerLosses[index]).toBeLessThan(result.provenance.layerLosses[index - 1])
    }
    expect(new Set(result.coatOfArms.coloredEmblems.map((item) => item.texture))).toEqual(new Set(['square.dds']))
    expect(result.coatOfArms.coloredEmblems.map((item) => item.instances[0].position[0]).sort())
      .toEqual(expect.arrayContaining([expect.closeTo(0.28, 1), expect.closeTo(0.72, 1)]))
  })

  it('uses a large budget as a ceiling and keeps every accepted native paint tile strictly improving', () => {
    const size = 32
    const solid = texture('solid')
    const pixels = new Uint8ClampedArray(size * size * 4)
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const offset = (y * size + x) * 4
        const color = x >= 5 && x < 15 && y >= 7 && y < 25
          ? [230, 20, 20]
          : x >= 18 && x < 27 && y >= 10 && y < 22
            ? [10, 10, 10]
            : [250, 250, 250]
        pixels.set([...color, 255], offset)
      }
    }
    const result = fitImageToCoatOfArms(
      asImage(pixels, size),
      [candidate('pattern_solid.dds', solid)],
      [candidate('ce_block_02.dds', texture('neutralBlock'))],
      { resolution: size, maxLayers: 128 },
    )
    expect(result.provenance.reconstructionMode).toBe('native-tile-paint')
    expect(result.provenance.selectedLayers).toBeGreaterThan(1)
    expect(result.provenance.selectedLayers).toBeLessThanOrEqual(128)
    expect(result.provenance.layerLosses).toHaveLength(result.provenance.selectedLayers + 1)
    for (let index = 1; index < result.provenance.layerLosses.length; index += 1) {
      expect(result.provenance.layerLosses[index]).toBeLessThan(result.provenance.layerLosses[index - 1])
    }
    expect(result.metrics.relativeImprovement).toBeGreaterThan(0.5)
  })
})
