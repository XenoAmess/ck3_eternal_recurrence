import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import { finalizeImageFitWithFullAssets } from './fitFinalizer'
import type { FitImage, ImageFitMetrics, ImageFitResult } from './imageFitter'
import { createCoatOfArms, type CoatOfArms } from './types'

const metric = (totalLoss: number): ImageFitMetrics => ({
  colorLoss: totalLoss,
  edgeLoss: totalLoss,
  totalLoss,
  relativeImprovement: 0,
})

function candidate(color: string): CoatOfArms {
  const coat = createCoatOfArms()
  coat.pattern = 'solid.dds'
  coat.colors = ['rgb { 0 0 0 }', 'rgb { 0 0 0 }', 'rgb { 0 0 0 }']
  coat.coloredEmblems = [{
    texture: 'opaque.dds',
    colors: [color, color, color],
    mask: [],
    instances: [{ position: [0.5, 0.5], scale: [1, 1], rotation: 0, depth: 1 }],
  }]
  return coat
}

describe('full DDS image-fit finalization', () => {
  it('re-scores exported candidates and replaces a fit-index false winner', () => {
    const green = candidate('rgb { 0 255 0 }')
    const red = candidate('rgb { 255 0 0 }')
    const searchResult = {
      coatOfArms: green,
      metrics: metric(0.01),
      paretoCandidates: [
        {
          coatOfArms: green,
          metrics: metric(0.01),
          reconstructionMode: 'semantic-search',
          textureNames: ['opaque.dds'],
          multiscaleMetrics: [],
        },
        {
          coatOfArms: red,
          metrics: metric(0.02),
          reconstructionMode: 'semantic-search',
          textureNames: ['opaque.dds'],
          multiscaleMetrics: [],
        },
      ],
      provenance: {
        resolution: 8,
        pyramidResolutions: [8],
        selectedAssetSha256: [],
        nativeTileSeamValidation: {
          status: 'passed',
          samplingContract: 'pixel-center-hard-geometry-v1',
          metrics: [],
        },
      },
    } as unknown as ImageFitResult
    const targetPixels = new Uint8ClampedArray(8 * 8 * 4)
    for (let offset = 0; offset < targetPixels.length; offset += 4) {
      targetPixels.set([255, 0, 0, 255], offset)
    }
    const target: FitImage = { width: 8, height: 8, pixels: targetPixels }
    const pattern: DecodedDds = {
      width: 1,
      height: 1,
      fourCC: 'BGRA8',
      pixels: new Uint8ClampedArray([255, 0, 0, 255]),
    }
    const opaque: DecodedDds = {
      width: 1,
      height: 1,
      fourCC: 'BGRA8',
      pixels: new Uint8ClampedArray([0, 255, 128, 255]),
    }

    const finalized = finalizeImageFitWithFullAssets(searchResult, target, {
      patterns: { 'solid.dds': pattern },
      coloredEmblems: { 'opaque.dds': opaque },
    })

    expect(finalized.receipt.selectedOriginalIndexes).toEqual([1])
    expect(finalized.receipt.sourceWinnerPreserved).toBe(false)
    expect(finalized.result.coatOfArms).toBe(red)
    expect(finalized.result.metrics.totalLoss).toBeLessThan(0.00001)
    expect(finalized.receipt.candidates[0].finalMetrics.totalLoss)
      .toBeGreaterThan(finalized.result.metrics.totalLoss)
    expect(finalized.result.provenance.fullAssetFinalization).toMatchObject({
      contract: 'full-dds-rescore-pareto-v1',
      finalAssetContract: 'decoded-exact-dds-mip-v1',
      selectedOriginalIndexes: [1],
    })
    expect(finalized.result.provenance.nativeTileSeamValidation.status).toBe('not-applicable')
  })
})
