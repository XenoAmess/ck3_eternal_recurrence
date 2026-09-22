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
import {
  measurePerceptualFitMetricsV2,
  measurePerceptualFitMetricsV3,
  type PerceptualFitMetricsV2,
  type PerceptualFitMetricsV3,
} from './perceptualFitMetrics'
import {
  createFitQualityObjective,
  fitQualityHasNoScaleRegression,
  FIT_QUALITY_OBJECTIVE_CONTRACT,
  FIT_QUALITY_SCALES,
  type FitQualityObjective,
  type FitQualityScale,
} from './fitQualityObjective'
import {
  proposeContourCandidates,
  type ContourPrimitiveAsset,
  type ContourProposalResult,
} from './fitContourProposals'
import {
  refineCoatOfArmsJointly,
  type JointRefinementReceipt,
} from './fitJointRefinement'
import { renderCoatOfArms, type NamedColorMap, type RenderedCoatOfArms } from './renderer'
import type { CoatOfArms, ColoredEmblem } from './types'
import { structurallyCompressCoatOfArms, type StructuralCompressionReceipt } from './coatOfArmsOptimizer'
import { pruneRedundantInstances, type InstancePruneReceipt } from './coatOfArmsPruner'

export interface FullAssetFitAssets {
  patterns: Record<string, DecodedDds>
  coloredEmblems: Record<string, DecodedDds>
  surfaceMask?: DecodedDds
  patternAssetSha256?: Record<string, string>
  emblemAssetSha256?: Record<string, string>
}

export interface FullAssetFitFinalizationOptions {
  /** Source-derived targets take precedence over resizing the search plane. */
  targetPyramid?: FitImage[]
  /** Bounded exact-DDS coordinate/replacement evaluations; zero disables E2. */
  jointRefinementEvaluations?: number
  /** Second exact 230px refinement budget; zero disables the medium cascade. */
  mediumJointRefinementEvaluations?: number
  /** Final exact 512px small-step refinement budget; zero disables the high cascade. */
  highJointRefinementEvaluations?: number
  /** Bounded full-budget contour replacements; zero disables E3/E4. */
  contourReplacementEvaluations?: number
  /** Exact 96/230/512 leave-one-out runs only at or below this draw count. */
  pruneDrawnInstanceLimit?: number
}

export interface MultiscalePerceptualReceipt {
  resolution: FitQualityScale
  v2: PerceptualFitMetricsV2
  v3: PerceptualFitMetricsV3
}

export interface FullAssetCandidateReceipt {
  originalIndex: number
  recolorBlend: number
  variant: 'search-incumbent' | 'exact-repair' | 'recolor' | 'contour-replacement' | 'joint-refinement'
  searchMetrics: ImageFitMetrics
  finalMetrics: ImageFitMetrics
  perceptualLossV2: number
  multiscalePerceptual: MultiscalePerceptualReceipt[]
  qualityObjective: FitQualityObjective
  passesIncumbentScaleGate: boolean
  drawnInstances: number
}

export interface FullAssetFitFinalizationReceipt {
  contract: 'full-dds-epsilon-multiscale-delta-gated-v6'
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
    selectionPolicy: 'multiscale-v2-no-regression-then-output-size-on-exact-tie'
    variants: Array<{
      originalIndex: number
      blend: number
      totalLoss: number
      edgeLoss: number
      perceptualLossV2: number
    }>
  }
  multiscaleSelection: {
    contract: typeof FIT_QUALITY_OBJECTIVE_CONTRACT
    scales: readonly [96, 230, 512]
    incumbentLoss: number
    selectedLoss: number
    incumbentPerScale: MultiscalePerceptualReceipt[]
    selectedPerScale: MultiscalePerceptualReceipt[]
    incumbentSource: 'search-winner' | 'delta-q-v9-compatibility'
    incumbentOriginalIndex: number
    compatibilityOriginalIndexes: number[]
    eligibleCandidates: number
    rejectedForScaleRegression: number
    selectedVariant: FullAssetCandidateReceipt['variant']
  }
  jointRefinement: JointRefinementReceipt
  jointRefinementMedium: JointRefinementReceipt
  jointRefinementHigh: JointRefinementReceipt
  contourRefinement: {
    contract: 'epsilon-q-contour-fixed-budget-replacement-v1'
    attempted: boolean
    emittedProposals: number
    evaluatedCandidates: number
    fullBudgetReplacements: number
    acceptedCandidateAdded: boolean
    analysis: ContourProposalResult<string>['analysis'] | null
  }
  qualityEquivalentPruning: {
    contract: 'epsilon-q-quality-equivalent-prune-v1'
    attempted: boolean
    skippedReason: 'disabled' | 'draw-count-limit' | null
    receipt: InstancePruneReceipt | null
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

type CandidateVariant = FullAssetCandidateReceipt['variant']

interface FinalizerCandidateEntry {
  candidate: ImageFitParetoCandidate
  originalIndex: number
  recolorBlend: number
  variant: CandidateVariant
}

interface RescoredFinalizerCandidate extends FinalizerCandidateEntry {
  searchMetrics: ImageFitMetrics
  drawnInstances: number
  qualityObjective: FitQualityObjective
  multiscalePerceptual: MultiscalePerceptualReceipt[]
  passesIncumbentScaleGate: boolean
}

function cloneCoatOfArms(coatOfArms: CoatOfArms): CoatOfArms {
  return {
    ...coatOfArms,
    colors: [...coatOfArms.colors],
    coloredEmblems: coatOfArms.coloredEmblems.map((emblem) => ({
      ...emblem,
      colors: [...emblem.colors],
      mask: [...emblem.mask],
      instances: emblem.instances.map((instance) => ({
        ...instance,
        position: [...instance.position],
        scale: [...instance.scale],
      })),
    })),
    texturedEmblems: coatOfArms.texturedEmblems.map((emblem) => ({ ...emblem })),
    rootPresence: coatOfArms.rootPresence ? {
      pattern: coatOfArms.rootPresence.pattern,
      colors: [...coatOfArms.rootPresence.colors],
    } : undefined,
  }
}

function primitiveFamily(texture: string): ContourPrimitiveAsset<string>['family'] | null {
  if (texture === 'ce_block_02.dds' || texture === 'ce_billet.dds') return 'block'
  if (texture === 'ce_circle.dds') return 'circle'
  if (texture === 'ce_lozenge.dds') return 'diamond'
  if (texture === 'ce_triangle_mask.dds') return 'wedge'
  return null
}

function contourPrimitiveAssets(assets: FullAssetFitAssets): ContourPrimitiveAsset<string>[] {
  return Object.keys(assets.coloredEmblems)
    .flatMap((texture): ContourPrimitiveAsset<string>[] => {
      const family = primitiveFamily(texture)
      if (!family) return []
      return [{
        id: texture,
        identity: assets.emblemAssetSha256?.[texture] ?? texture,
        texture,
        family,
        mask: [1],
      }]
    })
}

function replaceInstancesWithContour(
  source: CoatOfArms,
  flatInstanceIndexes: readonly number[],
  proposal: ContourProposalResult<string>['proposals'][number],
): CoatOfArms {
  const coatOfArms = cloneCoatOfArms(source)
  const victims = new Set(flatInstanceIndexes)
  let cursor = 0
  let victimDepth = proposal.instance.depth
  const victimDepths: number[] = []
  coatOfArms.coloredEmblems = coatOfArms.coloredEmblems
    .map((block) => {
      const instances = block.instances.filter((instance) => {
        const remove = victims.has(cursor)
        cursor += 1
        if (remove) victimDepths.push(instance.depth)
        return !remove
      })
      return { ...block, instances }
    })
    .filter((block) => block.instances.length > 0)
  if (victimDepths.length) victimDepth = Math.min(...victimDepths)
  const expression = `rgb { ${proposal.targetColor.join(' ')} }`
  const replacement: ColoredEmblem = {
    texture: proposal.texture,
    colors: [expression, expression, expression],
    mask: [...proposal.mask],
    instances: [{
      ...proposal.instance,
      position: [...proposal.instance.position],
      scale: [...proposal.instance.scale],
      depth: victimDepth,
    }],
  }
  coatOfArms.coloredEmblems.push(replacement)
  return coatOfArms
}

function appendContour(
  source: CoatOfArms,
  proposal: ContourProposalResult<string>['proposals'][number],
): CoatOfArms {
  const coatOfArms = cloneCoatOfArms(source)
  const expression = `rgb { ${proposal.targetColor.join(' ')} }`
  coatOfArms.coloredEmblems.push({
    texture: proposal.texture,
    colors: [expression, expression, expression],
    mask: [...proposal.mask],
    instances: [{
      ...proposal.instance,
      position: [...proposal.instance.position],
      scale: [...proposal.instance.scale],
    }],
  })
  return coatOfArms
}

function smallestAreaInstanceIndexes(coatOfArms: CoatOfArms, maximum: number): number[] {
  let flatIndex = 0
  return coatOfArms.coloredEmblems.flatMap((emblem) => emblem.instances.map((instance) => ({
    index: flatIndex++,
    area: Math.abs(instance.scale[0] * instance.scale[1]),
    depth: instance.depth,
  })))
    .sort((left, right) => left.area - right.area || right.depth - left.depth || left.index - right.index)
    .slice(0, maximum)
    .map((item) => item.index)
}

function nearestInstanceIndexes(
  coatOfArms: CoatOfArms,
  position: readonly [number, number],
  maximum: number,
): number[] {
  let flatIndex = 0
  return coatOfArms.coloredEmblems.flatMap((emblem) => emblem.instances.map((instance) => ({
    index: flatIndex++,
    distance: Math.hypot(instance.position[0] - position[0], instance.position[1] - position[1]),
    area: Math.abs(instance.scale[0] * instance.scale[1]),
  })))
    .sort((left, right) => left.distance - right.distance || left.area - right.area || left.index - right.index)
    .slice(0, maximum)
    .map((item) => item.index)
}

function detailInstanceIndexes(
  coatOfArms: CoatOfArms,
  analysis: ContourProposalResult<string>['analysis'] | null,
  maximum: number,
): number[] {
  let flatIndex = 0
  const instances = coatOfArms.coloredEmblems.flatMap((emblem) => emblem.instances.map((instance) => ({
    index: flatIndex++,
    position: instance.position,
    area: Math.abs(instance.scale[0] * instance.scale[1]),
  })))
  if (!analysis?.regions.length) return smallestAreaInstanceIndexes(coatOfArms, maximum)
  const selected: number[] = []
  for (const region of analysis.regions) {
    const nearest = instances
      .filter((item) => !selected.includes(item.index))
      .sort((left, right) => (
        Math.hypot(left.position[0] - region.center[0], left.position[1] - region.center[1])
          - Math.hypot(right.position[0] - region.center[0], right.position[1] - region.center[1])
        || left.area - right.area
        || left.index - right.index
      ))[0]
    if (nearest) selected.push(nearest.index)
    if (selected.length >= maximum) break
  }
  for (const index of smallestAreaInstanceIndexes(coatOfArms, maximum)) {
    if (!selected.includes(index)) selected.push(index)
    if (selected.length >= maximum) break
  }
  return selected
}

function disabledJointReceipt(coatOfArms: CoatOfArms, loss: number): JointRefinementReceipt {
  const instances = coatOfArms.coloredEmblems.reduce((sum, emblem) => sum + emblem.instances.length, 0)
  return {
    contract: 'exact-dds-fixed-budget-coordinate-replacement-v1',
    deterministic: true,
    renderer: 'complete-decoded-dds',
    evaluationBudget: 0,
    objectiveEvaluations: 0,
    evaluatedMoves: 0,
    acceptedMoves: [],
    acceptedArchiveCount: 0,
    lossBefore: loss,
    lossAfter: loss,
    drawnInstancesBefore: instances,
    drawnInstancesAfter: instances,
    keptIncumbent: true,
    stages: [],
    terminationReason: 'no-improvement',
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
  options: FullAssetFitFinalizationOptions = {},
): { result: ImageFitResult, receipt: FullAssetFitFinalizationReceipt } {
  if (!searchResult.paretoCandidates.length) throw new Error('完整 DDS 复评没有输入候选')
  const resolutions = [...new Set([
    searchResult.provenance.resolution,
    ...FIT_QUALITY_SCALES,
  ])].sort((left, right) => left - right)
  const sourceTargets = [inputTarget, ...(options.targetPyramid ?? [])]
    .filter((target) => target.width === target.height)
    .sort((left, right) => right.width - left.width)
  const targets = new Map(resolutions.map((resolution) => {
    const exact = sourceTargets.find((target) => target.width === resolution)
    const source = exact ?? sourceTargets[0] ?? inputTarget
    return [resolution, exact ?? resizeFitImage(source, resolution)]
  }))
  const primaryTarget = targets.get(searchResult.provenance.resolution)!
  const repairReceipts: Array<ReturnType<typeof repairImageFitCandidateWithExactAssets>['receipt']> = []
  const compatibilityLane = searchResult.provenance.qualityCompatibilityLane ?? {
    enabled: false,
    candidateStartIndex: null,
    candidateCount: 0,
  }
  const compatibilityOriginalIndexes = new Set<number>()
  if (compatibilityLane.enabled && compatibilityLane.candidateStartIndex !== null) {
    for (
      let index = compatibilityLane.candidateStartIndex;
      index < compatibilityLane.candidateStartIndex + compatibilityLane.candidateCount;
      index += 1
    ) compatibilityOriginalIndexes.add(index)
  }
  const repairEligibleIndexes = searchResult.paretoCandidates
    .map((candidate, originalIndex) => ({ candidate, originalIndex }))
    .filter(({ candidate }) => (
      candidate.reconstructionMode === 'hybrid-native-paint'
      || candidate.reconstructionMode === 'native-high-resolution-edge-refined'
    ))
    .map(({ originalIndex }) => originalIndex)
  const repairOriginalIndexes = new Set([
    ...repairEligibleIndexes.filter((index) => compatibilityOriginalIndexes.has(index)),
    ...repairEligibleIndexes.filter((index) => !compatibilityOriginalIndexes.has(index)).slice(0, 3),
  ])
  const recolorOriginalIndex = repairEligibleIndexes.find(
    (index) => !compatibilityOriginalIndexes.has(index),
  )
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
  const candidateEntries: FinalizerCandidateEntry[] = repairedCandidates.flatMap((candidate, originalIndex) => {
    if (!repairOriginalIndexes.has(originalIndex)) {
      return [{ candidate, originalIndex, recolorBlend: 0, variant: 'exact-repair' as const }]
    }
    if (
      originalIndex !== recolorOriginalIndex
      && !compatibilityOriginalIndexes.has(originalIndex)
    ) {
      return [{ candidate, originalIndex, recolorBlend: 0, variant: 'exact-repair' as const }]
    }
    const variants = [0.25, 0.5, 0.75, 1]
      .map((blend) => ({ candidate: recolorNativePaintTiles(candidate, primaryTarget, blend), blend }))
      .filter((item): item is { candidate: ImageFitParetoCandidate, blend: number } => Boolean(item.candidate))
      .map((item) => ({
        candidate: item.candidate,
        originalIndex,
        recolorBlend: item.blend,
        variant: 'recolor' as const,
      }))
    return [{
      candidate,
      originalIndex,
      recolorBlend: 0,
      variant: 'exact-repair' as const,
    }, ...variants]
  })
  // Keep the current search winner available even when it is not repairable.
  // For large budgets the immutable quality baseline is selected below by
  // replaying Delta-Q v9's exact-repair + primary-perceptual selection over the
  // dedicated compatibility frontier.
  candidateEntries.unshift({
    candidate: searchResult.paretoCandidates[0],
    originalIndex: 0,
    recolorBlend: 0,
    variant: 'search-incumbent',
  })
  const seenCandidateModels = new Set<CoatOfArms>()
  for (let index = 0; index < candidateEntries.length;) {
    const model = candidateEntries[index].candidate.coatOfArms
    if (seenCandidateModels.has(model)) candidateEntries.splice(index, 1)
    else {
      seenCandidateModels.add(model)
      index += 1
    }
  }

  const rescore = ({
    candidate,
    originalIndex,
    recolorBlend,
    variant,
  }: FinalizerCandidateEntry): Omit<RescoredFinalizerCandidate, 'passesIncumbentScaleGate'> => {
    const pattern = assets.patterns[candidate.coatOfArms.pattern]
    if (!pattern) throw new Error(`完整 DDS 复评缺少 pattern：${candidate.coatOfArms.pattern}`)
    const renderedByResolution = new Map<number, RenderedCoatOfArms>()
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
      renderedByResolution.set(resolution, rendered)
      return { resolution, ...measureImageFitLosses(target, rendered) }
    })
    const primary = multiscaleMetrics.find(
      (metric) => metric.resolution === searchResult.provenance.resolution,
    )!
    const primaryRendered = renderedByResolution.get(searchResult.provenance.resolution)
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
    const multiscalePerceptual = FIT_QUALITY_SCALES.map((resolution) => {
      const rendered = renderedByResolution.get(resolution)
      if (!rendered) throw new Error(`完整 DDS 候选缺少 ${resolution}px 固定质量渲染`)
      const target = targets.get(resolution)!
      return {
        resolution,
        v2: measurePerceptualFitMetricsV2(target, rendered),
        v3: measurePerceptualFitMetricsV3(target, rendered),
      }
    })
    const qualityObjective = createFitQualityObjective(Object.fromEntries(
      multiscalePerceptual.map((item) => [item.resolution, item.v2.totalLoss]),
    ) as Record<FitQualityScale, number>)
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
      variant,
      qualityObjective,
      multiscalePerceptual,
    }
  }

  const rescoredWithoutGate = candidateEntries.map(rescore)
  const compatibilityIncumbent = compatibilityOriginalIndexes.size > 0
    ? rescoredWithoutGate
        .filter((item) => compatibilityOriginalIndexes.has(item.originalIndex))
        .sort((left, right) => (
          left.candidate.perceptualMetricsV2.totalLoss - right.candidate.perceptualMetricsV2.totalLoss
          || left.drawnInstances - right.drawnInstances
          || left.recolorBlend - right.recolorBlend
          || left.originalIndex - right.originalIndex
        ))[0]
    : undefined
  const incumbent = compatibilityIncumbent ?? rescoredWithoutGate[0]
  if (!incumbent) throw new Error('完整 DDS 复评没有可用于非回退门禁的基线')
  let rescored: RescoredFinalizerCandidate[] = rescoredWithoutGate.map((item) => ({
    ...item,
    passesIncumbentScaleGate: fitQualityHasNoScaleRegression(
      item.qualityObjective,
      incumbent.qualityObjective,
    ),
  }))
  const compareQuality = (left: RescoredFinalizerCandidate, right: RescoredFinalizerCandidate) => (
    left.qualityObjective.weightedLoss - right.qualityObjective.weightedLoss
    || left.drawnInstances - right.drawnInstances
    || left.candidate.coatOfArms.coloredEmblems.length - right.candidate.coatOfArms.coloredEmblems.length
    || left.variant.localeCompare(right.variant)
    || left.originalIndex - right.originalIndex
    || left.recolorBlend - right.recolorBlend
  )
  const initialEligible = rescored.filter((item) => item.passesIncumbentScaleGate).sort(compareQuality)
  let refinementSeed = initialEligible[0] ?? rescored[0]

  const primitiveAssets = contourPrimitiveAssets(assets)
  const contourEvaluationBudget = Math.max(0, Math.floor(
    options.contourReplacementEvaluations ?? 32,
  ))
  let contourAnalysis: ContourProposalResult<string>['analysis'] | null = null
  let contourEmittedProposals = 0
  let contourEvaluatedCandidates = 0
  let fullBudgetReplacements = 0
  let acceptedContourCandidateAdded = false
  if (contourEvaluationBudget > 0 && primitiveAssets.some((item) => item.family === 'block')) {
    const contourResolution: FitQualityScale = 230
    const pattern = assets.patterns[refinementSeed.candidate.coatOfArms.pattern]
    const baselineRendered = pattern ? renderCoatOfArms(
      refinementSeed.candidate.coatOfArms,
      { pattern, coloredEmblems: assets.coloredEmblems, surfaceMask: assets.surfaceMask },
      namedColors,
      contourResolution,
    ) : null
    if (baselineRendered) {
      const proposals = proposeContourCandidates(
        targets.get(contourResolution)!,
        baselineRendered,
        primitiveAssets,
        { maximumRegions: 12, maximumCandidates: 24, maximumCandidatesPerRegion: 4 },
      )
      contourAnalysis = proposals.analysis
      contourEmittedProposals = proposals.proposals.length
      const instanceCount = drawnInstances(refinementSeed.candidate)
      const availableSlots = Math.max(0, searchResult.provenance.layerBudget - instanceCount)
      const candidates: Array<{ coatOfArms: CoatOfArms, loss: number, key: string }> = []
      const detailProposals = proposals.proposals.filter((proposal) => {
        const region = proposals.analysis.regions.find((item) => item.id === proposal.regionId)
        if (!region) return false
        const area = (region.bounds[2] - region.bounds[0]) * (region.bounds[3] - region.bounds[1])
        return area <= 0.12 && (region.kind !== 'curved' || area <= 0.05)
      })
      outer: for (const proposal of detailProposals) {
        const nearest = nearestInstanceIndexes(refinementSeed.candidate.coatOfArms, proposal.instance.position, 4)
        const victimGroups = availableSlots > 0
          ? [[]]
          : [1, 2, 4].filter((size) => size <= nearest.length).map((size) => nearest.slice(0, size))
        for (const victimIndexes of victimGroups) {
          if (contourEvaluatedCandidates >= contourEvaluationBudget) break outer
          const coatOfArms = victimIndexes.length === 0
            ? appendContour(refinementSeed.candidate.coatOfArms, proposal)
            : replaceInstancesWithContour(refinementSeed.candidate.coatOfArms, victimIndexes, proposal)
          const rendered = renderCoatOfArms(
            coatOfArms,
            { pattern, coloredEmblems: assets.coloredEmblems, surfaceMask: assets.surfaceMask },
            namedColors,
            contourResolution,
          )
          contourEvaluatedCandidates += 1
          if (victimIndexes.length > 0) fullBudgetReplacements += 1
          if (!rendered) continue
          const loss = measurePerceptualFitMetricsV2(targets.get(contourResolution)!, rendered).totalLoss
          candidates.push({ coatOfArms, loss, key: `${proposal.stableKey}|victims-${victimIndexes.join(',')}` })
        }
      }
      const promising = candidates
        .filter((item) => item.loss < refinementSeed.qualityObjective.lossByScale[230] - 1e-12)
        .sort((left, right) => left.loss - right.loss || left.key.localeCompare(right.key))
        .slice(0, 4)
      for (const item of promising) {
        const entry = rescore({
          candidate: {
            ...refinementSeed.candidate,
            coatOfArms: item.coatOfArms,
            textureNames: [...new Set(item.coatOfArms.coloredEmblems.map((emblem) => emblem.texture))],
          },
          originalIndex: refinementSeed.originalIndex,
          recolorBlend: refinementSeed.recolorBlend,
          variant: 'contour-replacement',
        })
        rescored.push({
          ...entry,
          passesIncumbentScaleGate: fitQualityHasNoScaleRegression(
            entry.qualityObjective,
            incumbent.qualityObjective,
          ),
        })
        acceptedContourCandidateAdded = true
      }
      refinementSeed = rescored.filter((item) => item.passesIncumbentScaleGate).sort(compareQuality)[0]
        ?? refinementSeed
    }
  }

  const jointEvaluationBudget = Math.max(0, Math.floor(
    options.jointRefinementEvaluations
      ?? (refinementSeed.drawnInstances <= 128 ? 2_048 : 512),
  ))
  let jointRefinement = disabledJointReceipt(
    refinementSeed.candidate.coatOfArms,
    refinementSeed.qualityObjective.lossByScale[96],
  )
  if (jointEvaluationBudget > 0) {
    const jointTarget = targets.get(96)!
    const joint = refineCoatOfArmsJointly(refinementSeed.candidate.coatOfArms, {
      assets: {
        pattern: assets.patterns[refinementSeed.candidate.coatOfArms.pattern],
        coloredEmblems: assets.coloredEmblems,
        surfaceMask: assets.surfaceMask,
      },
      namedColors,
      renderSize: 96,
      maxEvaluations: jointEvaluationBudget,
      eligibleFlatInstanceIndexes: detailInstanceIndexes(
        refinementSeed.candidate.coatOfArms,
        contourAnalysis,
        refinementSeed.drawnInstances <= 128 ? 24 : 16,
      ),
      eligibleTextures: primitiveAssets.map((item) => item.texture),
      maxReplacementCandidates: primitiveAssets.length,
      stages: [{
        id: 'epsilon-residual-focus',
        passes: refinementSeed.drawnInstances <= 128 ? 16 : 4,
        positionSteps: [0.03, 0.01],
        scaleSteps: [0.04, 0.015],
        rotationSteps: [8, 2],
        colorSteps: [0.05, 0.015],
        tryTextureReplacements: true,
      }],
      objective: ({ rendered }) => measurePerceptualFitMetricsV2(jointTarget, rendered).totalLoss,
    })
    jointRefinement = joint.receipt
    for (const archivedCoatOfArms of joint.acceptedArchive) {
      const entry = rescore({
        candidate: {
          ...refinementSeed.candidate,
          coatOfArms: archivedCoatOfArms,
          textureNames: [...new Set(archivedCoatOfArms.coloredEmblems.map((emblem) => emblem.texture))],
        },
        originalIndex: refinementSeed.originalIndex,
        recolorBlend: refinementSeed.recolorBlend,
        variant: 'joint-refinement',
      })
      rescored.push({
        ...entry,
        passesIncumbentScaleGate: fitQualityHasNoScaleRegression(
          entry.qualityObjective,
          incumbent.qualityObjective,
        ),
      })
    }
  }

  const mediumRefinementSeed = rescored
    .filter((item) => item.passesIncumbentScaleGate)
    .sort(compareQuality)[0] ?? refinementSeed
  const mediumJointEvaluationBudget = Math.max(0, Math.floor(
    options.mediumJointRefinementEvaluations
      ?? (mediumRefinementSeed.drawnInstances <= 128 ? 512 : 128),
  ))
  let jointRefinementMedium = disabledJointReceipt(
    mediumRefinementSeed.candidate.coatOfArms,
    mediumRefinementSeed.qualityObjective.lossByScale[230],
  )
  if (mediumJointEvaluationBudget > 0) {
    const mediumTarget = targets.get(230)!
    const mediumJoint = refineCoatOfArmsJointly(mediumRefinementSeed.candidate.coatOfArms, {
      assets: {
        pattern: assets.patterns[mediumRefinementSeed.candidate.coatOfArms.pattern],
        coloredEmblems: assets.coloredEmblems,
        surfaceMask: assets.surfaceMask,
      },
      namedColors,
      renderSize: 230,
      maxEvaluations: mediumJointEvaluationBudget,
      eligibleFlatInstanceIndexes: detailInstanceIndexes(
        mediumRefinementSeed.candidate.coatOfArms,
        contourAnalysis,
        mediumRefinementSeed.drawnInstances <= 128 ? 24 : 12,
      ),
      eligibleTextures: primitiveAssets.map((item) => item.texture),
      maxReplacementCandidates: primitiveAssets.length,
      stages: [{
        id: 'epsilon-medium-residual-focus',
        passes: mediumRefinementSeed.drawnInstances <= 128 ? 4 : 2,
        positionSteps: [0.015, 0.005],
        scaleSteps: [0.02, 0.0075],
        rotationSteps: [4, 1],
        colorSteps: [0.025, 0.0075],
        tryTextureReplacements: true,
      }],
      objective: ({ rendered }) => measurePerceptualFitMetricsV2(mediumTarget, rendered).totalLoss,
    })
    jointRefinementMedium = mediumJoint.receipt
    for (const archivedCoatOfArms of mediumJoint.acceptedArchive) {
      const entry = rescore({
        candidate: {
          ...mediumRefinementSeed.candidate,
          coatOfArms: archivedCoatOfArms,
          textureNames: [...new Set(archivedCoatOfArms.coloredEmblems.map((emblem) => emblem.texture))],
        },
        originalIndex: mediumRefinementSeed.originalIndex,
        recolorBlend: mediumRefinementSeed.recolorBlend,
        variant: 'joint-refinement',
      })
      rescored.push({
        ...entry,
        passesIncumbentScaleGate: fitQualityHasNoScaleRegression(
          entry.qualityObjective,
          incumbent.qualityObjective,
        ),
      })
    }
  }

  const highRefinementSeed = rescored
    .filter((item) => item.passesIncumbentScaleGate)
    .sort(compareQuality)[0] ?? mediumRefinementSeed
  const highJointEvaluationBudget = Math.max(0, Math.floor(
    options.highJointRefinementEvaluations
      ?? (highRefinementSeed.drawnInstances <= 128 ? 512 : 64),
  ))
  let jointRefinementHigh = disabledJointReceipt(
    highRefinementSeed.candidate.coatOfArms,
    highRefinementSeed.qualityObjective.lossByScale[512],
  )
  if (highJointEvaluationBudget > 0) {
    const highAssets = {
      pattern: assets.patterns[highRefinementSeed.candidate.coatOfArms.pattern],
      coloredEmblems: assets.coloredEmblems,
      surfaceMask: assets.surfaceMask,
    }
    const highJoint = refineCoatOfArmsJointly(highRefinementSeed.candidate.coatOfArms, {
      assets: highAssets,
      namedColors,
      renderSize: 512,
      maxEvaluations: highJointEvaluationBudget,
      eligibleFlatInstanceIndexes: detailInstanceIndexes(
        highRefinementSeed.candidate.coatOfArms,
        contourAnalysis,
        highRefinementSeed.drawnInstances <= 128 ? 24 : 8,
      ),
      eligibleTextures: primitiveAssets.map((item) => item.texture),
      maxReplacementCandidates: primitiveAssets.length,
      stages: [{
        id: 'epsilon-direct-multiscale-focus',
        passes: highRefinementSeed.drawnInstances <= 128 ? 4 : 1,
        positionSteps: [0.02, 0.0075],
        scaleSteps: [0.025, 0.01],
        rotationSteps: [5, 1.5],
        colorSteps: [0.03, 0.01],
        tryTextureReplacements: true,
      }],
      objective: ({ coatOfArms, rendered }) => {
        const lossByScale = {
          512: measurePerceptualFitMetricsV2(targets.get(512)!, rendered).totalLoss,
          96: 0,
          230: 0,
        } as Record<FitQualityScale, number>
        for (const scale of [96, 230] as const) {
          const scaleRendered = renderCoatOfArms(coatOfArms, highAssets, namedColors, scale)
          if (!scaleRendered) return Number.MAX_VALUE
          lossByScale[scale] = measurePerceptualFitMetricsV2(targets.get(scale)!, scaleRendered).totalLoss
        }
        const objective = createFitQualityObjective(lossByScale)
        return fitQualityHasNoScaleRegression(objective, incumbent.qualityObjective)
          ? objective.weightedLoss
          : Number.MAX_VALUE
      },
    })
    jointRefinementHigh = highJoint.receipt
    for (const archivedCoatOfArms of highJoint.acceptedArchive) {
      const entry = rescore({
        candidate: {
          ...highRefinementSeed.candidate,
          coatOfArms: archivedCoatOfArms,
          textureNames: [...new Set(archivedCoatOfArms.coloredEmblems.map((emblem) => emblem.texture))],
        },
        originalIndex: highRefinementSeed.originalIndex,
        recolorBlend: highRefinementSeed.recolorBlend,
        variant: 'joint-refinement',
      })
      rescored.push({
        ...entry,
        passesIncumbentScaleGate: fitQualityHasNoScaleRegression(
          entry.qualityObjective,
          incumbent.qualityObjective,
        ),
      })
    }
  }

  const legacyParetoIndexes = selectParetoFitCandidateIndexes(rescored.map((item) => ({
    totalLoss: item.candidate.metrics.totalLoss,
    edgeLoss: item.candidate.metrics.edgeLoss,
    drawnInstances: item.drawnInstances,
    stableKey: `${String(item.originalIndex).padStart(4, '0')}:${item.candidate.reconstructionMode}:${item.variant}:recolor-${item.recolorBlend}`,
  })))
  if (!legacyParetoIndexes.length) throw new Error('完整 DDS 复评没有可交付候选')
  const qualityPool = rescored.filter((item) => item.passesIncumbentScaleGate)
  const qualityFront = qualityPool.filter((item) => !qualityPool.some((other) => {
    if (other === item) return false
    const noWorse = FIT_QUALITY_SCALES.every((scale) => (
      other.qualityObjective.lossByScale[scale] <= item.qualityObjective.lossByScale[scale] + 1e-12
    )) && other.drawnInstances <= item.drawnInstances
    const strictlyBetter = FIT_QUALITY_SCALES.some((scale) => (
      other.qualityObjective.lossByScale[scale] < item.qualityObjective.lossByScale[scale] - 1e-12
    )) || other.drawnInstances < item.drawnInstances
    return noWorse && strictlyBetter
  }))
  const qualityIndexes = rescored
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => qualityFront.includes(item))
    .sort((left, right) => compareQuality(left.item, right.item) || left.index - right.index)
    .map(({ index }) => index)
  const qualityWinnerIndex = qualityIndexes[0] ?? 0
  const dominatesDeliveredCandidate = (
    left: RescoredFinalizerCandidate,
    right: RescoredFinalizerCandidate,
  ): boolean => {
    const leftPerceptualLoss = left.candidate.perceptualMetricsV2?.totalLoss ?? Number.POSITIVE_INFINITY
    const rightPerceptualLoss = right.candidate.perceptualMetricsV2?.totalLoss ?? Number.POSITIVE_INFINITY
    const noWorse = leftPerceptualLoss <= rightPerceptualLoss
      && left.candidate.metrics.totalLoss <= right.candidate.metrics.totalLoss
      && left.candidate.metrics.edgeLoss <= right.candidate.metrics.edgeLoss
      && left.drawnInstances <= right.drawnInstances
    const strictlyBetter = leftPerceptualLoss < rightPerceptualLoss
      || left.candidate.metrics.totalLoss < right.candidate.metrics.totalLoss
      || left.candidate.metrics.edgeLoss < right.candidate.metrics.edgeLoss
      || left.drawnInstances < right.drawnInstances
    return noWorse && strictlyBetter
  }
  const selectedIndexes: number[] = []
  const deliveryOrder = [qualityWinnerIndex, ...qualityIndexes, ...legacyParetoIndexes]
    .filter((index, position, indexes) => indexes.indexOf(index) === position)
  for (const index of deliveryOrder) {
    const candidate = rescored[index]
    // Quality winner always stays first. Additional cards are useful only when
    // they are genuinely incomparable with every already-delivered card under
    // the exact metrics shown in the UI; never surface a dominated alternative.
    if (selectedIndexes.some((selectedIndex) => (
      dominatesDeliveredCandidate(rescored[selectedIndex], candidate)
      || dominatesDeliveredCandidate(candidate, rescored[selectedIndex])
    ))) continue
    selectedIndexes.push(index)
    if (selectedIndexes.length >= 3) break
  }
  const selected = selectedIndexes.map((index) => rescored[index])
  let winner = selected[0]
  const pruneDrawnInstanceLimit = Math.max(0, Math.floor(options.pruneDrawnInstanceLimit ?? 32))
  let pruneReceipt: InstancePruneReceipt | null = null
  let pruneSkippedReason: 'disabled' | 'draw-count-limit' | null = null
  if (pruneDrawnInstanceLimit === 0) {
    pruneSkippedReason = 'disabled'
  } else if (winner.drawnInstances > pruneDrawnInstanceLimit) {
    pruneSkippedReason = 'draw-count-limit'
  } else {
    const pattern = assets.patterns[winner.candidate.coatOfArms.pattern]
    const pruned = pruneRedundantInstances(
      winner.candidate.coatOfArms,
      targets.get(512)!,
      pattern,
      assets.coloredEmblems,
      assets.surfaceMask,
      namedColors,
      {
        mode: 'pixel-exact',
        searchResolution: 96,
        validationResolutions: [230, 512],
      },
    )
    pruneReceipt = pruned.receipt
    if (pruned.receipt.removedInstances > 0) {
      const entry = rescore({
        candidate: { ...winner.candidate, coatOfArms: pruned.coatOfArms },
        originalIndex: winner.originalIndex,
        recolorBlend: winner.recolorBlend,
        variant: winner.variant,
      })
      if (!fitQualityHasNoScaleRegression(entry.qualityObjective, winner.qualityObjective)) {
        throw new Error('像素等价剪枝改变了 Epsilon-Q 多尺度质量')
      }
      winner = {
        ...entry,
        passesIncumbentScaleGate: true,
      }
      selected[0] = winner
    }
  }
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
    contract: 'full-dds-epsilon-multiscale-delta-gated-v6',
    searchAssetContract: 'fit-index-rgba32-v2',
    finalAssetContract: 'decoded-exact-dds-mip-v1',
    candidates: rescored.map((item) => ({
      originalIndex: item.originalIndex,
      recolorBlend: item.recolorBlend,
      variant: item.variant,
      searchMetrics: { ...item.searchMetrics },
      finalMetrics: { ...item.candidate.metrics },
      perceptualLossV2: item.candidate.perceptualMetricsV2.totalLoss,
      multiscalePerceptual: item.multiscalePerceptual,
      qualityObjective: item.qualityObjective,
      passesIncumbentScaleGate: item.passesIncumbentScaleGate,
      drawnInstances: item.drawnInstances,
    })),
    selectedOriginalIndexes: selected.map((item) => item.originalIndex),
    sourceWinnerPreserved: winner.variant === 'search-incumbent',
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
      selectionPolicy: 'multiscale-v2-no-regression-then-output-size-on-exact-tie',
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
    multiscaleSelection: {
      contract: FIT_QUALITY_OBJECTIVE_CONTRACT,
      scales: FIT_QUALITY_SCALES,
      incumbentLoss: incumbent.qualityObjective.weightedLoss,
      selectedLoss: winner.qualityObjective.weightedLoss,
      incumbentPerScale: incumbent.multiscalePerceptual,
      selectedPerScale: winner.multiscalePerceptual,
      incumbentSource: compatibilityIncumbent
        ? 'delta-q-v9-compatibility'
        : 'search-winner',
      incumbentOriginalIndex: incumbent.originalIndex,
      compatibilityOriginalIndexes: [...compatibilityOriginalIndexes],
      eligibleCandidates: rescored.filter((item) => item.passesIncumbentScaleGate).length,
      rejectedForScaleRegression: rescored.filter((item) => !item.passesIncumbentScaleGate).length,
      selectedVariant: winner.variant,
    },
    jointRefinement,
    jointRefinementMedium,
    jointRefinementHigh,
    contourRefinement: {
      contract: 'epsilon-q-contour-fixed-budget-replacement-v1',
      attempted: contourEvaluationBudget > 0,
      emittedProposals: contourEmittedProposals,
      evaluatedCandidates: contourEvaluatedCandidates,
      fullBudgetReplacements,
      acceptedCandidateAdded: acceptedContourCandidateAdded,
      analysis: contourAnalysis,
    },
    qualityEquivalentPruning: {
      contract: 'epsilon-q-quality-equivalent-prune-v1',
      attempted: pruneReceipt !== null,
      skippedReason: pruneSkippedReason,
      receipt: pruneReceipt,
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
          multiscaleSelection: receipt.multiscaleSelection,
          jointRefinement: receipt.jointRefinement,
          jointRefinementMedium: receipt.jointRefinementMedium,
          jointRefinementHigh: receipt.jointRefinementHigh,
          contourRefinement: receipt.contourRefinement,
          qualityEquivalentPruning: receipt.qualityEquivalentPruning,
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
