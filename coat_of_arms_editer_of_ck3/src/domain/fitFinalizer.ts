import type { DecodedDds } from './dds'
import {
  measureImageFitLosses,
  resizeFitImage,
  selectParetoFitCandidateIndexes,
  type FitImage,
  type ImageFitMetrics,
  type ImageFitParetoCandidate,
  type ImageFitResult,
} from './imageFitter'
import { measurePerceptualFitMetricsV2 } from './perceptualFitMetrics'
import { renderCoatOfArms, type NamedColorMap } from './renderer'
import type { CoatOfArms } from './types'

export interface FullAssetFitAssets {
  patterns: Record<string, DecodedDds>
  coloredEmblems: Record<string, DecodedDds>
  surfaceMask?: DecodedDds
  patternAssetSha256?: Record<string, string>
  emblemAssetSha256?: Record<string, string>
}

export interface FullAssetCandidateReceipt {
  originalIndex: number
  searchMetrics: ImageFitMetrics
  finalMetrics: ImageFitMetrics
  drawnInstances: number
}

export interface FullAssetFitFinalizationReceipt {
  contract: 'full-dds-rescore-pareto-v1'
  searchAssetContract: 'fit-index-rgba32-v2'
  finalAssetContract: 'decoded-exact-dds-mip-v1'
  candidates: FullAssetCandidateReceipt[]
  selectedOriginalIndexes: number[]
  sourceWinnerPreserved: boolean
  maximumAbsoluteTotalLossDelta: number
  maximumAbsoluteEdgeLossDelta: number
}

function withoutEmblems(coatOfArms: CoatOfArms): CoatOfArms {
  return {
    ...coatOfArms,
    colors: [...coatOfArms.colors],
    coloredEmblems: [],
    texturedEmblems: [],
    rootPresence: coatOfArms.rootPresence ? {
      pattern: coatOfArms.rootPresence.pattern,
      colors: [...coatOfArms.rootPresence.colors],
    } : undefined,
  }
}

function drawnInstances(candidate: ImageFitParetoCandidate): number {
  return candidate.coatOfArms.coloredEmblems.reduce(
    (total, emblem) => total + emblem.instances.length,
    0,
  )
}

/**
 * The fit index deliberately uses 32px RGBA projections for fast search.
 * Export, editor preview and CK3 use the exact decoded DDS and mip chain.
 * Re-score and re-select the final Pareto front on those exact assets so the
 * metrics shown beside exported code describe the pixels users actually see.
 */
export function finalizeImageFitWithFullAssets(
  searchResult: ImageFitResult,
  inputTarget: FitImage,
  assets: FullAssetFitAssets,
  namedColors: NamedColorMap = {},
): { result: ImageFitResult, receipt: FullAssetFitFinalizationReceipt } {
  if (!searchResult.paretoCandidates.length) throw new Error('完整 DDS 复评没有输入候选')
  const resolutions = [...new Set([
    searchResult.provenance.resolution,
    ...searchResult.provenance.pyramidResolutions,
  ])]
  const targets = new Map(resolutions.map((resolution) => (
    [resolution, resizeFitImage(inputTarget, resolution)]
  )))
  const rescored = searchResult.paretoCandidates.map((candidate, originalIndex) => {
    const pattern = assets.patterns[candidate.coatOfArms.pattern]
    if (!pattern) throw new Error(`完整 DDS 复评缺少 pattern：${candidate.coatOfArms.pattern}`)
    for (const emblem of candidate.coatOfArms.coloredEmblems) {
      if (!assets.coloredEmblems[emblem.texture]) {
        throw new Error(`完整 DDS 复评缺少 colored_emblem：${emblem.texture}`)
      }
    }
    const multiscaleMetrics = resolutions.map((resolution) => {
      const target = targets.get(resolution)!
      const rendered = renderCoatOfArms(
        candidate.coatOfArms,
        {
          pattern,
          coloredEmblems: assets.coloredEmblems,
          surfaceMask: assets.surfaceMask,
        },
        namedColors,
        resolution,
      )
      if (!rendered) throw new Error(`完整 DDS 候选无法在 ${resolution}px 渲染`)
      return { resolution, ...measureImageFitLosses(target, rendered) }
    })
    const primary = multiscaleMetrics.find(
      (metric) => metric.resolution === searchResult.provenance.resolution,
    )!
    const primaryTarget = targets.get(searchResult.provenance.resolution)!
    const primaryRendered = renderCoatOfArms(
      candidate.coatOfArms,
      { pattern, coloredEmblems: assets.coloredEmblems, surfaceMask: assets.surfaceMask },
      namedColors,
      searchResult.provenance.resolution,
    )
    if (!primaryRendered) throw new Error('完整 DDS 候选无法在主分辨率渲染')
    const baselineRendered = renderCoatOfArms(
      withoutEmblems(candidate.coatOfArms),
      { pattern, coloredEmblems: {}, surfaceMask: assets.surfaceMask },
      namedColors,
      searchResult.provenance.resolution,
    )
    if (!baselineRendered) throw new Error('完整 DDS 背景基线无法渲染')
    const baseline = measureImageFitLosses(primaryTarget, baselineRendered)
    const metrics: ImageFitMetrics = {
      colorLoss: primary.colorLoss,
      edgeLoss: primary.edgeLoss,
      totalLoss: primary.totalLoss,
      relativeImprovement: baseline.totalLoss <= 1e-12
        ? 0
        : Math.max(0, (baseline.totalLoss - primary.totalLoss) / baseline.totalLoss),
    }
    return {
      originalIndex,
      candidate: {
        ...candidate,
        metrics,
        perceptualMetricsV2: measurePerceptualFitMetricsV2(primaryTarget, primaryRendered),
        multiscaleMetrics,
      },
      searchMetrics: candidate.metrics,
      drawnInstances: drawnInstances(candidate),
    }
  })
  const selectedOriginalIndexes = selectParetoFitCandidateIndexes(rescored.map((item) => ({
    totalLoss: item.candidate.metrics.totalLoss,
    edgeLoss: item.candidate.metrics.edgeLoss,
    drawnInstances: item.drawnInstances,
    stableKey: `${String(item.originalIndex).padStart(4, '0')}:${item.candidate.reconstructionMode}`,
  })))
  if (!selectedOriginalIndexes.length) throw new Error('完整 DDS 复评没有可交付候选')
  const selected = selectedOriginalIndexes.map((index) => rescored[index])
  const winner = selected[0]
  const winnerCoat = winner.candidate.coatOfArms
  const selectedAssetSha256 = assets.patternAssetSha256 && assets.emblemAssetSha256
    ? [
        assets.patternAssetSha256[winnerCoat.pattern],
        ...winnerCoat.coloredEmblems.flatMap((emblem) => (
          emblem.instances.map(() => assets.emblemAssetSha256![emblem.texture])
        )),
      ].filter((value): value is string => Boolean(value))
    : searchResult.provenance.selectedAssetSha256
  const receipt: FullAssetFitFinalizationReceipt = {
    contract: 'full-dds-rescore-pareto-v1',
    searchAssetContract: 'fit-index-rgba32-v2',
    finalAssetContract: 'decoded-exact-dds-mip-v1',
    candidates: rescored.map((item) => ({
      originalIndex: item.originalIndex,
      searchMetrics: { ...item.searchMetrics },
      finalMetrics: { ...item.candidate.metrics },
      drawnInstances: item.drawnInstances,
    })),
    selectedOriginalIndexes: selected.map((item) => item.originalIndex),
    sourceWinnerPreserved: winner.originalIndex === 0,
    maximumAbsoluteTotalLossDelta: Math.max(...rescored.map((item) => (
      Math.abs(item.candidate.metrics.totalLoss - item.searchMetrics.totalLoss)
    ))),
    maximumAbsoluteEdgeLossDelta: Math.max(...rescored.map((item) => (
      Math.abs(item.candidate.metrics.edgeLoss - item.searchMetrics.edgeLoss)
    ))),
  }
  return {
    result: {
      ...searchResult,
      coatOfArms: winnerCoat,
      metrics: winner.candidate.metrics,
      paretoCandidates: selected.map((item) => item.candidate),
      provenance: {
        ...searchResult.provenance,
        logicalLayers: winnerCoat.coloredEmblems.length + winnerCoat.texturedEmblems.length,
        coloredEmblemBlocks: winnerCoat.coloredEmblems.length,
        drawnInstances: winner.drawnInstances,
        selectedLayers: winner.drawnInstances,
        reconstructionMode: winner.candidate.reconstructionMode,
        perceptualScoringShadow: {
          ...searchResult.provenance.perceptualScoringShadow,
          selected: winner.candidate.perceptualMetricsV2,
        },
        selectedMultiscaleMetrics: winner.candidate.multiscaleMetrics,
        selectedAssetSha256,
        fullAssetFinalization: {
          contract: receipt.contract,
          searchAssetContract: receipt.searchAssetContract,
          finalAssetContract: receipt.finalAssetContract,
          rescoredCandidates: receipt.candidates.length,
          selectedOriginalIndexes: receipt.selectedOriginalIndexes,
          sourceWinnerPreserved: receipt.sourceWinnerPreserved,
          maximumAbsoluteTotalLossDelta: receipt.maximumAbsoluteTotalLossDelta,
          maximumAbsoluteEdgeLossDelta: receipt.maximumAbsoluteEdgeLossDelta,
        },
        nativeTileSeamValidation: receipt.sourceWinnerPreserved
          ? searchResult.provenance.nativeTileSeamValidation
          : {
              status: 'not-applicable',
              samplingContract: 'pixel-center-hard-geometry-v1',
              metrics: [],
            },
      },
    },
    receipt,
  }
}
