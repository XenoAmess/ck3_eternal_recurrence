import type { DecodedDds } from './dds'
import {
  measureImageFitLosses,
  repairImageFitCandidateWithExactAssets,
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
import { structurallyCompressCoatOfArms, type StructuralCompressionReceipt } from './coatOfArmsOptimizer'

export interface FullAssetFitAssets {
  patterns: Record<string, DecodedDds>
  coloredEmblems: Record<string, DecodedDds>
  surfaceMask?: DecodedDds
  patternAssetSha256?: Record<string, string>
  emblemAssetSha256?: Record<string, string>
}

export interface FullAssetCandidateReceipt {
  originalIndex: number
  recolorBlend: number
  searchMetrics: ImageFitMetrics
  finalMetrics: ImageFitMetrics
  perceptualLossV2: number
  drawnInstances: number
}

export interface FullAssetFitFinalizationReceipt {
  contract: 'full-dds-rescore-repair-pareto-v3'
  searchAssetContract: 'fit-index-rgba32-v2'
  finalAssetContract: 'decoded-exact-dds-mip-v1'
  candidates: FullAssetCandidateReceipt[]
  selectedOriginalIndexes: number[]
  sourceWinnerPreserved: boolean
  maximumAbsoluteTotalLossDelta: number
  maximumAbsoluteEdgeLossDelta: number
  exactResidualRepair: {
    contract: 'exact-dds-residual-tile-perceptual-v2'
    attemptedCandidates: number
    repairedCandidates: number
    acceptedLayers: number
    perceptualAcceptedLayers: number
    evaluatedCandidates: number
    maximumAdditionalLayersPerCandidate: 144
  }
  perceptualColorRefinement: {
    contract: 'linear-light-native-tile-recolor-v1'
    evaluatedVariants: number
    selectedBlend: number
    selectionPolicy: 'perceptual-v2-first-output-size-on-exact-tie'
    variants: Array<{
      originalIndex: number
      blend: number
      totalLoss: number
      edgeLoss: number
      perceptualLossV2: number
    }>
  }
  structuralCompression: StructuralCompressionReceipt
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

function srgbToLinear(value: number): number {
  const normalized = value / 255
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4
}

function linearToSrgb(value: number): number {
  const bounded = Math.max(0, Math.min(1, value))
  const normalized = bounded <= 0.0031308
    ? bounded * 12.92
    : 1.055 * bounded ** (1 / 2.4) - 0.055
  return Math.round(normalized * 255)
}

function nativeTileTargetColors(
  target: FitImage,
  instance: CoatOfArms['coloredEmblems'][number]['instances'][number],
): { srgb: [number, number, number], linear: [number, number, number] } | null {
  if (Math.abs(instance.rotation % 360) > 1e-9) return null
  const halfWidth = Math.abs(instance.scale[0]) / 2
  const halfHeight = Math.abs(instance.scale[1]) / 2
  const minimumX = Math.max(0, Math.floor((instance.position[0] - halfWidth) * target.width))
  const maximumX = Math.min(target.width, Math.ceil((instance.position[0] + halfWidth) * target.width))
  const minimumY = Math.max(0, Math.floor((instance.position[1] - halfHeight) * target.height))
  const maximumY = Math.min(target.height, Math.ceil((instance.position[1] + halfHeight) * target.height))
  const srgbSums = [0, 0, 0]
  const linearSums = [0, 0, 0]
  let weight = 0
  for (let y = minimumY; y < maximumY; y += 1) {
    const v = (y + 0.5) / target.height
    if (v < instance.position[1] - halfHeight || v > instance.position[1] + halfHeight) continue
    for (let x = minimumX; x < maximumX; x += 1) {
      const u = (x + 0.5) / target.width
      if (u < instance.position[0] - halfWidth || u > instance.position[0] + halfWidth) continue
      const offset = (y * target.width + x) * 4
      const alpha = target.pixels[offset + 3] / 255
      if (alpha <= 0) continue
      weight += alpha
      for (let channel = 0; channel < 3; channel += 1) {
        const value = target.pixels[offset + channel]
        srgbSums[channel] += value * alpha
        linearSums[channel] += srgbToLinear(value) * alpha
      }
    }
  }
  if (weight <= 1e-12) return null
  return {
    srgb: srgbSums.map((sum) => Math.round(sum / weight)) as [number, number, number],
    linear: linearSums.map((sum) => linearToSrgb(sum / weight)) as [number, number, number],
  }
}

function recolorNativePaintTiles(
  candidate: ImageFitParetoCandidate,
  target: FitImage,
  blend: number,
): ImageFitParetoCandidate | null {
  let changed = false
  const coloredEmblems = candidate.coatOfArms.coloredEmblems.map((emblem) => {
    if (emblem.texture !== 'ce_block_02.dds' || emblem.instances.length !== 1) return emblem
    const colors = nativeTileTargetColors(target, emblem.instances[0])
    if (!colors) return emblem
    const blended = colors.srgb.map((value, channel) => Math.round(
      value * (1 - blend) + colors.linear[channel] * blend,
    )) as [number, number, number]
    const expression = `rgb { ${blended[0]} ${blended[1]} ${blended[2]} }`
    if (emblem.colors.every((value) => value === expression)) return emblem
    changed = true
    return { ...emblem, colors: [expression, expression, expression] as [string, string, string] }
  })
  if (!changed) return null
  return {
    ...candidate,
    coatOfArms: { ...candidate.coatOfArms, coloredEmblems },
  }
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
  const primaryTarget = targets.get(searchResult.provenance.resolution)!
  const repairReceipts: Array<ReturnType<typeof repairImageFitCandidateWithExactAssets>['receipt']> = []
  const repairOriginalIndexes = new Set(searchResult.paretoCandidates
    .map((candidate, originalIndex) => ({ candidate, originalIndex }))
    .filter(({ candidate }) => (
      candidate.reconstructionMode === 'hybrid-native-paint'
      || candidate.reconstructionMode === 'native-high-resolution-edge-refined'
    ))
    .map(({ originalIndex }) => originalIndex))
  const repairedCandidates = searchResult.paretoCandidates.map((candidate, originalIndex) => {
    const pattern = assets.patterns[candidate.coatOfArms.pattern]
    if (!pattern) throw new Error(`完整 DDS 复评缺少 pattern：${candidate.coatOfArms.pattern}`)
    for (const emblem of candidate.coatOfArms.coloredEmblems) {
      if (!assets.coloredEmblems[emblem.texture]) {
        throw new Error(`完整 DDS 复评缺少 colored_emblem：${emblem.texture}`)
      }
    }
    if (!repairOriginalIndexes.has(originalIndex)) {
      repairReceipts.push({
        attempted: false,
        acceptedLayers: 0,
        evaluatedCandidates: 0,
        perceptualAcceptedLayers: 0,
      })
      return candidate
    }
    const repaired = repairImageFitCandidateWithExactAssets(
      candidate,
      primaryTarget,
      {
        pattern,
        coloredEmblems: assets.coloredEmblems,
        surfaceMask: assets.surfaceMask,
      },
      searchResult.provenance.layerBudget,
      namedColors,
    )
    repairReceipts.push(repaired.receipt)
    return repaired.candidate
  })
  const candidateEntries = repairedCandidates.flatMap((candidate, originalIndex) => {
    if (!repairOriginalIndexes.has(originalIndex)) return [{ candidate, originalIndex, recolorBlend: 0 }]
    const variants = [0.25, 0.5, 0.75, 1]
      .map((blend) => ({ candidate: recolorNativePaintTiles(candidate, primaryTarget, blend), blend }))
      .filter((item): item is { candidate: ImageFitParetoCandidate, blend: number } => Boolean(item.candidate))
      .map((item) => ({ candidate: item.candidate, originalIndex, recolorBlend: item.blend }))
    return [{ candidate, originalIndex, recolorBlend: 0 }, ...variants]
  })
  const rescored = candidateEntries.map(({ candidate, originalIndex, recolorBlend }) => {
    const pattern = assets.patterns[candidate.coatOfArms.pattern]
    if (!pattern) throw new Error(`完整 DDS 复评缺少 pattern：${candidate.coatOfArms.pattern}`)
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
      searchMetrics: searchResult.paretoCandidates[originalIndex].metrics,
      drawnInstances: drawnInstances(candidate),
      recolorBlend,
    }
  })
  const legacyParetoIndexes = selectParetoFitCandidateIndexes(rescored.map((item) => ({
    totalLoss: item.candidate.metrics.totalLoss,
    edgeLoss: item.candidate.metrics.edgeLoss,
    drawnInstances: item.drawnInstances,
    stableKey: `${String(item.originalIndex).padStart(4, '0')}:${item.candidate.reconstructionMode}:recolor-${item.recolorBlend}`,
  })))
  if (!legacyParetoIndexes.length) throw new Error('完整 DDS 复评没有可交付候选')
  const perceptualEligible = rescored
    .map((item, index) => ({ item, index }))
    .sort((left, right) => (
      left.item.candidate.perceptualMetricsV2.totalLoss - right.item.candidate.perceptualMetricsV2.totalLoss
      || left.item.drawnInstances - right.item.drawnInstances
      || left.item.recolorBlend - right.item.recolorBlend
      || left.index - right.index
    ))
  const qualityWinnerIndex = perceptualEligible[0]?.index ?? legacyParetoIndexes[0]
  const selectedIndexes = [qualityWinnerIndex, ...legacyParetoIndexes]
    .filter((index, position, indexes) => indexes.indexOf(index) === position)
    .slice(0, 3)
  const selected = selectedIndexes.map((index) => rescored[index])
  const winner = selected[0]
  const structuralCompression = structurallyCompressCoatOfArms(winner.candidate.coatOfArms)
  const winnerCoat = structuralCompression.coatOfArms
  const selectedAssetSha256 = assets.patternAssetSha256 && assets.emblemAssetSha256
    ? [
        assets.patternAssetSha256[winnerCoat.pattern],
        ...winnerCoat.coloredEmblems.flatMap((emblem) => (
          emblem.instances.map(() => assets.emblemAssetSha256![emblem.texture])
        )),
      ].filter((value): value is string => Boolean(value))
    : searchResult.provenance.selectedAssetSha256
  const receipt: FullAssetFitFinalizationReceipt = {
    contract: 'full-dds-rescore-repair-pareto-v3',
    searchAssetContract: 'fit-index-rgba32-v2',
    finalAssetContract: 'decoded-exact-dds-mip-v1',
    candidates: rescored.map((item) => ({
      originalIndex: item.originalIndex,
      recolorBlend: item.recolorBlend,
      searchMetrics: { ...item.searchMetrics },
      finalMetrics: { ...item.candidate.metrics },
      perceptualLossV2: item.candidate.perceptualMetricsV2.totalLoss,
      drawnInstances: item.drawnInstances,
    })),
    selectedOriginalIndexes: selected.map((item) => item.originalIndex),
    sourceWinnerPreserved: winner.originalIndex === 0 && winner.recolorBlend === 0,
    maximumAbsoluteTotalLossDelta: Math.max(...rescored.map((item) => (
      Math.abs(item.candidate.metrics.totalLoss - item.searchMetrics.totalLoss)
    ))),
    maximumAbsoluteEdgeLossDelta: Math.max(...rescored.map((item) => (
      Math.abs(item.candidate.metrics.edgeLoss - item.searchMetrics.edgeLoss)
    ))),
    exactResidualRepair: {
      contract: 'exact-dds-residual-tile-perceptual-v2',
      attemptedCandidates: repairReceipts.filter((item) => item.attempted).length,
      repairedCandidates: repairReceipts.filter((item) => item.acceptedLayers > 0).length,
      acceptedLayers: repairReceipts.reduce((sum, item) => sum + item.acceptedLayers, 0),
      perceptualAcceptedLayers: repairReceipts.reduce(
        (sum, item) => sum + item.perceptualAcceptedLayers,
        0,
      ),
      evaluatedCandidates: repairReceipts.reduce((sum, item) => sum + item.evaluatedCandidates, 0),
      maximumAdditionalLayersPerCandidate: 144,
    },
    perceptualColorRefinement: {
      contract: 'linear-light-native-tile-recolor-v1',
      evaluatedVariants: candidateEntries.filter((item) => item.recolorBlend > 0).length,
      selectedBlend: winner.recolorBlend,
      selectionPolicy: 'perceptual-v2-first-output-size-on-exact-tie',
      variants: rescored
        .filter((item) => repairOriginalIndexes.has(item.originalIndex))
        .map((item) => ({
          originalIndex: item.originalIndex,
          blend: item.recolorBlend,
          totalLoss: item.candidate.metrics.totalLoss,
          edgeLoss: item.candidate.metrics.edgeLoss,
          perceptualLossV2: item.candidate.perceptualMetricsV2.totalLoss,
        })),
    },
    structuralCompression: structuralCompression.receipt,
  }
  return {
    result: {
      ...searchResult,
      coatOfArms: winnerCoat,
      metrics: winner.candidate.metrics,
      paretoCandidates: selected.map((item, index) => index === 0
        ? { ...item.candidate, coatOfArms: winnerCoat }
        : item.candidate),
      provenance: {
        ...searchResult.provenance,
        logicalLayers: winnerCoat.coloredEmblems.length + winnerCoat.texturedEmblems.length,
        coloredEmblemBlocks: winnerCoat.coloredEmblems.length,
        drawnInstances: winner.drawnInstances,
        selectedLayers: winner.drawnInstances,
        reconstructionMode: winner.candidate.reconstructionMode,
        perceptualScoringShadow: {
          ...searchResult.provenance.perceptualScoringShadow,
          status: 'full-dds-bounded-selection',
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
          exactResidualRepair: receipt.exactResidualRepair,
          perceptualColorRefinement: receipt.perceptualColorRefinement,
          structuralCompression: receipt.structuralCompression,
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
