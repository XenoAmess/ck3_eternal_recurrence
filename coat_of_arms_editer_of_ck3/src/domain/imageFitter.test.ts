import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import {
  dominantColors,
  fitImageToCoatOfArms,
  measureImageFitLosses,
  passesNativeShapeMaterialImprovementGate,
  resizeFitImage,
  selectMixedNativeShapeCandidateNames,
  selectParetoFitCandidateIndexes,
  type FitImage,
  type FitTextureCandidate,
  type ImageFitCheckpoint,
  type ImageFitProgress,
} from './imageFitter'
import { renderCoatOfArms } from './renderer'
import { computeFitTextureShapeFeatures } from './shapeFeatures'
import type { CoatOfArms } from './types'

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

type MosaicCell = {
  minimumX: number
  minimumY: number
  maximumX: number
  maximumY: number
  color: [number, number, number]
}

const seamMosaicCells: MosaicCell[] = [
  { minimumX: 0, minimumY: 0, maximumX: 0.25, maximumY: 0.25, color: [240, 20, 20] },
  { minimumX: 0.25, minimumY: 0, maximumX: 0.5, maximumY: 0.25, color: [20, 220, 40] },
  { minimumX: 0, minimumY: 0.25, maximumX: 0.25, maximumY: 0.5, color: [20, 40, 230] },
  { minimumX: 0.25, minimumY: 0.25, maximumX: 0.5, maximumY: 0.5, color: [235, 210, 20] },
  { minimumX: 0.5, minimumY: 0, maximumX: 1, maximumY: 0.5, color: [10, 10, 10] },
  { minimumX: 0, minimumY: 0.5, maximumX: 0.5, maximumY: 1, color: [245, 245, 245] },
  { minimumX: 0.5, minimumY: 0.5, maximumX: 1, maximumY: 1, color: [20, 220, 220] },
]

const mosaicCellAt = (u: number, v: number) => seamMosaicCells.find((cell) => (
  u >= cell.minimumX && u < cell.maximumX && v >= cell.minimumY && v < cell.maximumY
))!

const seamMosaic = (size: number): FitImage => {
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const offset = (y * size + x) * 4
      pixels.set([...mosaicCellAt((x + 0.5) / size, (y + 0.5) / size).color, 255], offset)
    }
  }
  return asImage(pixels, size)
}

const seamSurfaceMask = (): DecodedDds => {
  const size = 8
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const offset = (y * size + x) * 4
      pixels.set([0, 128, 96 + ((x + y) % 5) * 16, 255], offset)
    }
  }
  return { width: size, height: size, fourCC: 'DXT1', pixels }
}

const nominalTileReference = (coatOfArms: CoatOfArms): CoatOfArms => ({
  ...coatOfArms,
  colors: [...coatOfArms.colors],
  coloredEmblems: coatOfArms.coloredEmblems.map((emblem) => ({
    ...emblem,
    colors: [...emblem.colors],
    mask: [...emblem.mask],
    instances: emblem.instances.map((instance) => {
      const cell = seamMosaicCells.find((candidate) => (
        Math.abs(instance.position[0] - (candidate.minimumX + candidate.maximumX) / 2) <= 1e-12
        && Math.abs(instance.position[1] - (candidate.minimumY + candidate.maximumY) / 2) <= 1e-12
      ))
      if (!cell) throw new Error(`找不到实例 ${instance.position.join(',')} 的 nominal tile`)
      return {
        ...instance,
        position: [...instance.position],
        scale: [cell.maximumX - cell.minimumX, cell.maximumY - cell.minimumY],
      }
    }),
  })),
  texturedEmblems: coatOfArms.texturedEmblems.map((emblem) => ({ ...emblem })),
})

const renderedPixel = (pixels: Uint8ClampedArray, offset: number) => (
  [pixels[offset], pixels[offset + 1], pixels[offset + 2]] as [number, number, number]
)

const squaredDistance = (left: number[], right: number[]) => left.reduce(
  (sum, value, index) => sum + (value - right[index]) ** 2,
  0,
)

const seamLeakMetrics = (
  actual: Uint8ClampedArray,
  reference: Uint8ClampedArray,
  background: Uint8ClampedArray,
  size: number,
) => {
  const boundaryBand = 2 / size
  const verticalBoundaries = [0.25, 0.5]
  const horizontalBoundaries = [0.25, 0.5]
  let backgroundLeakPixels = 0
  let maximumLeakAmount = 0
  const rowLeaks = new Uint32Array(size)
  const columnLeaks = new Uint32Array(size)
  for (let y = 1; y < size - 1; y += 1) {
    const v = (y + 0.5) / size
    for (let x = 1; x < size - 1; x += 1) {
      const u = (x + 0.5) / size
      const onInternalBoundary = verticalBoundaries.some((boundary) => Math.abs(u - boundary) <= boundaryBand)
        || horizontalBoundaries.some((boundary) => Math.abs(v - boundary) <= boundaryBand)
      if (!onInternalBoundary) continue
      const offset = (y * size + x) * 4
      const actualColor = renderedPixel(actual, offset)
      const referenceColor = renderedPixel(reference, offset)
      const backgroundColor = renderedPixel(background, offset)
      const actualDistance = squaredDistance(actualColor, backgroundColor)
      const referenceDistance = squaredDistance(referenceColor, backgroundColor)
      const maximumChannelDelta = Math.max(...actualColor.map(
        (value, channel) => Math.abs(value - referenceColor[channel]),
      ))
      if (maximumChannelDelta <= 2 || actualDistance + 4 >= referenceDistance) continue
      backgroundLeakPixels += 1
      maximumLeakAmount = Math.max(maximumLeakAmount, maximumChannelDelta)
      rowLeaks[y] += 1
      columnLeaks[x] += 1
    }
  }
  return {
    backgroundLeakPixels,
    maximumLeakAmount,
    peakRowLeakPixels: Math.max(...rowLeaks),
    peakColumnLeakPixels: Math.max(...columnLeaks),
  }
}

describe('browser image fitter', () => {
  it('returns at most three real non-dominated quality/complexity points', () => {
    const points = [
      { stableKey: 'best-quality', totalLoss: 0.08, edgeLoss: 0.09, drawnInstances: 24 },
      { stableKey: 'best-complexity', totalLoss: 0.12, edgeLoss: 0.11, drawnInstances: 4 },
      { stableKey: 'best-edge', totalLoss: 0.10, edgeLoss: 0.06, drawnInstances: 18 },
      { stableKey: 'dominated', totalLoss: 0.13, edgeLoss: 0.12, drawnInstances: 25 },
      { stableKey: 'best-quality', totalLoss: 0.08, edgeLoss: 0.09, drawnInstances: 24 },
    ]
    const selected = selectParetoFitCandidateIndexes(points)
    expect(selected.map((index) => points[index].stableKey)).toEqual([
      'best-quality', 'best-complexity', 'best-edge',
    ])
    expect(selected).toHaveLength(3)
    expect(selected).not.toContain(3)
    expect(selected).not.toContain(4)
  })

  it('rejects the measured browser-only shape gain and accepts a material mip-aware gain', () => {
    expect(passesNativeShapeMaterialImprovementGate(
      { totalLoss: 0.052995, edgeLoss: 0.095896 },
      { totalLoss: 0.052549, edgeLoss: 0.094820 },
    )).toBe(false)
    expect(passesNativeShapeMaterialImprovementGate(
      { totalLoss: 0.052810569499734915, edgeLoss: 0.08679505759266391 },
      { totalLoss: 0.05118391010135082, edgeLoss: 0.08446813456742323 },
    )).toBe(true)
  })

  it('keeps descriptor leaders and every available primitive family in the mixed shortlist', () => {
    const ranked = [
      'semantic-a.dds', 'semantic-b.dds', 'semantic-c.dds', 'semantic-d.dds',
      'ce_triangle_mask.dds', 'ce_lozenge.dds', 'ce_circle.dds',
      'ce_billet.dds', 'ce_block_02.dds', 'semantic-e.dds',
    ]
    const selected = selectMixedNativeShapeCandidateNames(ranked, 8)
    expect(selected).toHaveLength(8)
    expect(selected).toEqual(expect.arrayContaining([
      'semantic-a.dds', 'semantic-b.dds', 'semantic-c.dds',
      'ce_block_02.dds', 'ce_billet.dds', 'ce_circle.dds',
      'ce_lozenge.dds', 'ce_triangle_mask.dds',
    ]))
    expect(selected).toEqual(ranked.filter((name) => selected.includes(name)))
  })

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
    patterns[0].shapeFeatures = computeFitTextureShapeFeatures(patterns[0].texture)
    const first = fitImageToCoatOfArms(asImage(target!.pixels, size), patterns, [], { resolution: 32 })
    const second = fitImageToCoatOfArms(asImage(target!.pixels, size), patterns, [], { resolution: 32 })
    expect(first.coatOfArms.pattern).toBe('split.dds')
    expect(second.coatOfArms).toEqual(first.coatOfArms)
    expect(second.metrics).toEqual(first.metrics)
    expect(first.provenance.shapeFeatureIndex).toEqual({
      contract: 'ck3-coa-shape-features-v1',
      indexedAssets: 1,
      fallbackAssets: 1,
    })
  })

  it('uses a batch scorer for background selection only after CPU-reference agreement', () => {
    const size = 32
    const split = texture('split')
    const target = renderCoatOfArms({
      outerKey: 'coa', parent: '', pattern: 'split.dds',
      colors: ['rgb { 220 30 30 }', 'rgb { 30 50 220 }', 'rgb { 220 30 30 }'],
      coloredEmblems: [], texturedEmblems: [],
    }, { pattern: split, coloredEmblems: {} }, {}, size)!
    const image = asImage(target.pixels, size)
    const patterns = [candidate('solid.dds', texture('solid')), candidate('split.dds', split)]
    const exactScorer = {
      backend: 'test-exact-batch',
      maximumBatchSize: 128,
      status: () => 'available' as const,
      score: (candidates: readonly FitImage[]) => candidates.map((item) => ({
        ...measureImageFitLosses(image, item),
        relativeImprovement: 0,
      })),
    }
    const accelerated = fitImageToCoatOfArms(image, patterns, [], {
      resolution: size,
      batchSearchRequested: true,
      batchScorer: exactScorer,
    })
    expect(accelerated.coatOfArms.pattern).toBe('split.dds')
    expect(accelerated.provenance.searchBackend).toBe('webgl2-batch+cpu-reference')
    expect(accelerated.provenance.batchSearch).toMatchObject({
      backend: 'test-exact-batch',
      status: 'active',
      candidates: 12,
      cpuReferenceAgreement: true,
    })

    const rejected = fitImageToCoatOfArms(image, patterns, [], {
      resolution: size,
      batchSearchRequested: true,
      batchScorer: {
        ...exactScorer,
        backend: 'test-invalid-batch',
        score: (candidates) => candidates.map(() => ({
          colorLoss: 0, edgeLoss: 0, totalLoss: 0, relativeImprovement: 0,
        })),
      },
    })
    expect(rejected.coatOfArms.pattern).toBe('split.dds')
    expect(rejected.provenance.searchBackend).toBe('cpu-reference')
    expect(rejected.provenance.batchSearch.status).toBe('reference_mismatch_fallback')

    const contextLost = fitImageToCoatOfArms(image, patterns, [], {
      resolution: size,
      batchSearchRequested: true,
      batchScorer: {
        ...exactScorer,
        backend: 'test-context-lost-batch',
        status: () => 'context_lost' as const,
        score: () => null,
      },
    })
    expect(contextLost.coatOfArms.pattern).toBe('split.dds')
    expect(contextLost.provenance.searchBackend).toBe('cpu-reference')
    expect(contextLost.provenance.batchSearch.status).toBe('context_lost_fallback')
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
    expect(new Set(progress.map((update) => update.phase))).toEqual(new Set(['background', 'coarse', 'refine', 'finalize']))
    for (const phase of ['background', 'coarse', 'refine', 'finalize'] as const) {
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
    expect(result.provenance.algorithm).toBe('ck3-coa-browser-fit-v13-epsilon-direct-multiscale')
    expect(result.provenance.selectedLayers).toBeGreaterThanOrEqual(2)
    expect(result.coatOfArms.coloredEmblems).toHaveLength(result.provenance.selectedLayers)
    expect(result.provenance.drawnInstances).toBe(result.provenance.selectedLayers)
    expect(result.provenance.logicalLayers).toBe(result.coatOfArms.coloredEmblems.length)
    expect(result.provenance.coloredEmblemBlocks).toBe(result.coatOfArms.coloredEmblems.length)
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
    expect(result.provenance.candidateLosses.map((item) => item.mode)).toEqual(
      expect.arrayContaining(['native-tile-paint', 'native-edge-refined']),
    )
    expect(result.provenance.baselineEdgeRepair.acceptedLayers).toBeGreaterThan(8)
    expect(result.provenance.baselineEdgeRepair.terminationReason).toBe('layer_budget')
    expect(result.provenance.selectedLayers).toBeGreaterThan(1)
    expect(result.provenance.selectedLayers).toBeLessThanOrEqual(128)
    expect(result.provenance.layerLosses).toHaveLength(result.provenance.selectedLayers + 1)
    for (let index = 1; index < result.provenance.layerLosses.length; index += 1) {
      expect(result.provenance.layerLosses[index]).toBeLessThan(result.provenance.layerLosses[index - 1])
    }
    expect(result.metrics.relativeImprovement).toBeGreaterThan(0.5)
    expect(result.paretoCandidates.length).toBeGreaterThanOrEqual(1)
    expect(result.paretoCandidates.length).toBeLessThanOrEqual(3)
    expect(result.paretoCandidates[0].coatOfArms).toEqual(result.coatOfArms)
    expect(result.paretoCandidates[0].metrics).toEqual(result.metrics)
    for (const candidate of result.paretoCandidates) {
      const candidateInstances = candidate.coatOfArms.coloredEmblems.reduce(
        (total, emblem) => total + emblem.instances.length,
        0,
      )
      expect(candidateInstances).toBeLessThanOrEqual(128)
      expect(result.paretoCandidates.some((other) => (
        other !== candidate
        && other.metrics.totalLoss <= candidate.metrics.totalLoss
        && other.metrics.edgeLoss <= candidate.metrics.edgeLoss
        && other.coatOfArms.coloredEmblems.reduce(
          (total, emblem) => total + emblem.instances.length,
          0,
        ) <= candidateInstances
        && (
          other.metrics.totalLoss < candidate.metrics.totalLoss
          || other.metrics.edgeLoss < candidate.metrics.edgeLoss
          || other.coatOfArms.coloredEmblems.reduce(
            (total, emblem) => total + emblem.instances.length,
            0,
          ) < candidateInstances
        )
      ))).toBe(false)
    }
  })

  it('uses the highest supplied pyramid level for non-regressing local detail repair', () => {
    const size = 64
    const solid = texture('solid')
    const block = texture('neutralBlock')
    const pixels = new Uint8ClampedArray(size * size * 4)
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const offset = (y * size + x) * 4
        const onDetail = (x === 31 || x === 32) && y >= 7 && y < 57
        pixels.set(onDetail ? [15, 15, 15, 255] : [245, 245, 245, 255], offset)
      }
    }
    const target = asImage(pixels, size)
    const result = fitImageToCoatOfArms(
      target,
      [candidate('pattern_solid.dds', solid)],
      [candidate('ce_block_02.dds', block)],
      {
        resolution: 16,
        pyramidImages: [target],
        maxLayers: 1024,
      },
    )
    const baseline = result.provenance.candidateLosses.find(
      (item) => item.mode === 'native-edge-refined',
    ) ?? result.provenance.candidateLosses.find((item) => item.mode === 'native-tile-paint')
    const highResolution = result.provenance.candidateLosses.find(
      (item) => item.mode === 'native-high-resolution-edge-refined',
    )
    expect(result.provenance.highResolutionEdgeRepair).toMatchObject({
      resolution: 64,
      terminationReason: expect.stringMatching(/layer_budget|no_improvement/),
    })
    expect(result.provenance.highResolutionEdgeRepair.evaluatedCandidates).toBeGreaterThan(0)
    expect(result.provenance.highResolutionEdgeRepair.acceptedLayers).toBeGreaterThan(0)
    expect(baseline).toBeDefined()
    expect(highResolution).toBeDefined()
    expect(highResolution!.totalLoss).toBeLessThanOrEqual(baseline!.totalLoss)
    expect(highResolution!.edgeLoss).toBeLessThanOrEqual(baseline!.edgeLoss)
    expect(highResolution!.multiscaleMetrics).toHaveLength(1)
    expect(highResolution!.multiscaleMetrics[0].resolution).toBe(result.provenance.resolution)
  })

  it('resumes native paint from a versioned checkpoint without changing the result', () => {
    const size = 32
    const solid = texture('solid')
    const block = texture('neutralBlock')
    const checkpoints: ImageFitCheckpoint[] = []
    const options = {
      resolution: size,
      maxLayers: 128,
      inputSha256: 'A'.repeat(64),
      assetPackManifestSha256: 'B'.repeat(64),
    }
    const uninterrupted = fitImageToCoatOfArms(
      seamMosaic(size),
      [candidate('pattern_solid.dds', solid)],
      [candidate('ce_block_02.dds', block)],
      { ...options, onCheckpoint: (checkpoint) => checkpoints.push(checkpoint) },
    )
    const checkpoint = checkpoints.find((item) => (
      item.lane === 'baseline'
      && item.nextTileIndex > 0
      && item.nextTileIndex < item.tileCount
    ))
    expect(checkpoint).toBeDefined()
    expect(checkpoint).toMatchObject({
      contract: 'ck3-coa-fit-checkpoint-v8',
      algorithm: 'ck3-coa-browser-fit-v13-epsilon-direct-multiscale',
      inputSha256: options.inputSha256,
      assetPackManifestSha256: options.assetPackManifestSha256,
      resolution: size,
      layerBudget: 128,
      refinementCandidates: 48,
      beamWidth: 2,
      randomSeed: null,
    })
    const resumed = fitImageToCoatOfArms(
      seamMosaic(size),
      [candidate('pattern_solid.dds', solid)],
      [candidate('ce_block_02.dds', block)],
      { ...options, resumeCheckpoint: checkpoint },
    )
    expect(resumed.coatOfArms).toEqual(uninterrupted.coatOfArms)
    expect(resumed.metrics).toEqual(uninterrupted.metrics)
    expect(resumed.provenance.layerLosses).toEqual(uninterrupted.provenance.layerLosses)
    expect(resumed.provenance.nativeTileSeamValidation).toEqual(
      uninterrupted.provenance.nativeTileSeamValidation,
    )

    expect(() => fitImageToCoatOfArms(
      seamMosaic(size),
      [candidate('pattern_solid.dds', solid)],
      [candidate('ce_block_02.dds', block)],
      { ...options, inputSha256: 'C'.repeat(64), resumeCheckpoint: checkpoint },
    )).toThrow('输入图片或素材包标识不匹配')
  })

  it('enters a mixed semantic plus native paint path for a large budget', () => {
    const size = 48
    const solid = texture('solid')
    const square = texture('square')
    const block = texture('neutralBlock')
    const target = renderCoatOfArms({
      outerKey: 'coa', parent: '', pattern: 'pattern_solid.dds',
      colors: ['rgb { 245 245 245 }', 'rgb { 245 245 245 }', 'rgb { 245 245 245 }'],
      coloredEmblems: [
        {
          texture: 'semantic-square.dds', colors: ['black', 'black', 'black'], mask: [],
          instances: [{ position: [0.5, 0.5], scale: [1.2, 0.72], rotation: 17.3, depth: 1 }],
        },
        {
          texture: 'ce_block_02.dds',
          colors: ['rgb { 210 25 30 }', 'rgb { 210 25 30 }', 'rgb { 210 25 30 }'], mask: [],
          instances: [{ position: [0.82, 0.2], scale: [0.18, 0.14], rotation: 0, depth: 2 }],
        },
      ],
      texturedEmblems: [],
    }, {
      pattern: solid,
      coloredEmblems: { 'semantic-square.dds': square, 'ce_block_02.dds': block },
    }, { black: [0, 0, 0] }, size)!
    const result = fitImageToCoatOfArms(
      asImage(target.pixels, size),
      [candidate('pattern_solid.dds', solid)],
      [candidate('semantic-square.dds', square), candidate('ce_block_02.dds', block)],
      { resolution: size, maxLayers: 128 },
    )
    const purePaint = result.provenance.candidateLosses.find((item) => item.mode === 'native-tile-paint')
    const hybrid = result.provenance.candidateLosses.find((item) => (
      (item.mode === 'hybrid-native-paint' || item.mode === 'semantic-search')
      && item.textureNames.includes('semantic-square.dds')
      && item.textureNames.includes('ce_block_02.dds')
    ))
    expect(purePaint).toBeDefined()
    expect(hybrid).toBeDefined()
    expect(hybrid!.textureNames).toEqual(expect.arrayContaining(['semantic-square.dds', 'ce_block_02.dds']))
    expect(hybrid!.totalLoss).toBeLessThan(purePaint!.totalLoss)
    expect(result.provenance.pyramidResolutions).toEqual([48])
    expect(result.provenance.nativeShapeRefinement).toMatchObject({
      requestedPasses: 0,
      completedPasses: expect.any(Number),
      evaluatedCandidates: expect.any(Number),
    })
    expect(result.provenance.nativeShapeRefinement.completedPasses).toBe(0)
    expect(result.provenance.nativeShapeRefinement.evaluatedCandidates).toBe(0)
  })

  it('keeps mixed-size native paint tiles seamless above the 96px search plane', () => {
    const solid = texture('solid')
    const block = texture('neutralBlock')
    const blockCandidate = candidate('ce_block_02.dds', block)
    const blockFeatures = computeFitTextureShapeFeatures(block)
    // A paint brush can have a skewed energy centroid despite full occupied
    // bounds. Exact-pack v2 also stores the fully opaque vanilla block at
    // 0.49999999999999634 rather than exactly 0.5 after summing 256x256
    // samples. Coverage must use bounds, never the energy centroid.
    blockCandidate.shapeFeatures = {
      ...blockFeatures,
      contentCenter: [0.45, 0.55],
    }
    const result = fitImageToCoatOfArms(
      seamMosaic(32),
      [candidate('pattern_solid.dds', solid)],
      [blockCandidate],
      { resolution: 32, maxLayers: 128 },
    )
    expect(result.provenance.reconstructionMode).toBe('native-tile-paint')
    expect(result.provenance.selectedLayers).toBeGreaterThanOrEqual(5)
    expect(result.provenance.nativeTileSeamValidation).toEqual({
      status: 'passed',
      samplingContract: 'pixel-center-hard-geometry-v1',
      metrics: [96, 230, 512].map((resolution) => ({
        resolution,
        backgroundLeakPixels: 0,
        maximumLeakAmount: 0,
        peakRowLeakPixels: 0,
        peakColumnLeakPixels: 0,
      })),
    })
    const reference = nominalTileReference(result.coatOfArms)

    const observations = []
    for (const surfaceMask of [undefined, seamSurfaceMask()]) {
      for (const size of [96, 230, 512]) {
        const assets = {
          pattern: solid,
          coloredEmblems: { 'ce_block_02.dds': block },
          surfaceMask,
        }
        const actual = renderCoatOfArms(result.coatOfArms, assets, {}, size)!
        const expected = renderCoatOfArms(reference, assets, {}, size)!
        const background = renderCoatOfArms(
          { ...result.coatOfArms, coloredEmblems: [] },
          assets,
          {},
          size,
        )!
        observations.push({
          surfaceMask: surfaceMask ? 'on' : 'off',
          size,
          ...seamLeakMetrics(actual.pixels, expected.pixels, background.pixels, size),
        })
      }
    }
    expect(observations).toEqual(['off', 'on'].flatMap((surfaceMask) => [96, 230, 512].map((size) => ({
      surfaceMask,
      size,
      backgroundLeakPixels: 0,
      maximumLeakAmount: 0,
      peakRowLeakPixels: 0,
      peakColumnLeakPixels: 0,
    }))))
  })
})
