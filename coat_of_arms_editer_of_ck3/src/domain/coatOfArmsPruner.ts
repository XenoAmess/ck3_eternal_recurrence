import type { DecodedDds } from './dds'
import {
  measureImageFitLosses,
  resizeFitImage,
  type FitImage,
  type ImageFitMetrics,
} from './imageFitter'
import { structurallyCompressCoatOfArms } from './coatOfArmsOptimizer'
import { renderCoatOfArms, type NamedColorMap, type RenderedCoatOfArms } from './renderer'
import type { CoatOfArms, CoatOfArmsInstance, ColoredEmblem } from './types'

export interface InstancePruneOptions {
  mode?: 'pixel-exact' | 'metric-pareto'
  searchResolution?: number
  validationResolutions?: number[]
  numericLossTolerance?: number
  allowedVisualDifferenceBytes?: number
  allowedCumulativeTotalLossIncrease?: number
  allowedCumulativeEdgeLossIncrease?: number
  onProgress?: (progress: InstancePruneProgress) => void
}

export interface InstancePruneProgress {
  pass: number
  completedInPass: number
  totalInPass: number
  evaluatedCandidates: number
  percent: number
}

export interface InstanceRemovalMeasurement {
  resolution: number
  differingBytes: number
  maximumByteDifference: number
  colorLossDelta: number
  edgeLossDelta: number
  totalLossDelta: number
}

export interface InstanceNecessityEvidence {
  instanceId: number
  sourceBlockIndex: number
  sourceInstanceIndex: number
  depth: number
  pass: number
  removed: boolean
  reason:
    | 'pixel-exact-redundant'
    | 'metric-pareto-redundant'
    | 'changes-search-pixels'
    | 'changes-validation-pixels'
    | 'would-worsen-search-metric'
    | 'would-worsen-validation-metric'
  measurements: InstanceRemovalMeasurement[]
}

export interface InstancePruneReceipt {
  contract: 'exact-leave-one-out-fixed-point-v1' | 'metric-pareto-leave-one-out-fixed-point-v1'
  mode: 'pixel-exact' | 'metric-pareto'
  numericLossTolerance: number
  allowedVisualDifferenceBytes: number
  allowedCumulativeTotalLossIncrease: number
  allowedCumulativeEdgeLossIncrease: number
  searchResolution: number
  validationResolutions: number[]
  drawnInstancesBefore: number
  drawnInstancesAfter: number
  removedInstances: number
  fixedPointPasses: number
  evaluatedCandidates: number
  initialMetrics: ImageFitMetrics
  finalMetrics: ImageFitMetrics
  resolutionMetrics: Array<{
    resolution: number
    initial: Pick<ImageFitMetrics, 'colorLoss' | 'edgeLoss' | 'totalLoss'>
    final: Pick<ImageFitMetrics, 'colorLoss' | 'edgeLoss' | 'totalLoss'>
  }>
  removedEvidence: InstanceNecessityEvidence[]
  finalNecessityEvidence: InstanceNecessityEvidence[]
}

export interface InstancePruneResult {
  coatOfArms: CoatOfArms
  receipt: InstancePruneReceipt
}

interface FlatInstance {
  id: number
  sourceBlockIndex: number
  sourceInstanceIndex: number
  style: Omit<ColoredEmblem, 'instances'>
  instance: CoatOfArmsInstance
}

interface ResolutionState {
  target: FitImage
  rendered: RenderedCoatOfArms
  metrics: Pick<ImageFitMetrics, 'colorLoss' | 'edgeLoss' | 'totalLoss'>
}

const cloneInstance = (instance: CoatOfArmsInstance): CoatOfArmsInstance => ({
  position: [...instance.position],
  scale: [...instance.scale],
  rotation: instance.rotation,
  depth: instance.depth,
})

function flatten(coatOfArms: CoatOfArms): FlatInstance[] {
  let id = 0
  return coatOfArms.coloredEmblems.flatMap((emblem, sourceBlockIndex) => (
    emblem.instances.map((instance, sourceInstanceIndex) => ({
      id: id++,
      sourceBlockIndex,
      sourceInstanceIndex,
      style: {
        texture: emblem.texture,
        colors: [...emblem.colors],
        mask: [...emblem.mask],
      },
      instance: cloneInstance(instance),
    }))
  ))
}

function modelFromItems(source: CoatOfArms, items: FlatInstance[]): CoatOfArms {
  return {
    outerKey: source.outerKey,
    parent: source.parent,
    pattern: source.pattern,
    colors: [...source.colors],
    coloredEmblems: items.map((item) => ({
      texture: item.style.texture,
      colors: [...item.style.colors],
      mask: [...item.style.mask],
      instances: [cloneInstance(item.instance)],
    })),
    texturedEmblems: source.texturedEmblems.map((emblem) => ({ ...emblem })),
    rootPresence: source.rootPresence ? {
      pattern: source.rootPresence.pattern,
      colors: [...source.rootPresence.colors],
    } : undefined,
  }
}

function pixelDifference(
  left: RenderedCoatOfArms,
  right: RenderedCoatOfArms,
): { differingBytes: number, maximumByteDifference: number } {
  if (
    left.width !== right.width
    || left.height !== right.height
    || left.pixels.length !== right.pixels.length
  ) throw new Error('剪枝像素比较尺寸不一致')
  let differingBytes = 0
  let maximumByteDifference = 0
  for (let index = 0; index < left.pixels.length; index += 1) {
    const difference = Math.abs(left.pixels[index] - right.pixels[index])
    if (difference > 0) differingBytes += 1
    maximumByteDifference = Math.max(maximumByteDifference, difference)
  }
  return { differingBytes, maximumByteDifference }
}

function renderState(
  coatOfArms: CoatOfArms,
  target: FitImage,
  pattern: DecodedDds,
  coloredEmblems: Record<string, DecodedDds>,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
): ResolutionState {
  const rendered = renderCoatOfArms(
    coatOfArms,
    { pattern, coloredEmblems, surfaceMask },
    namedColors,
    target.width,
  )
  if (!rendered) throw new Error('剪枝候选无法渲染')
  return { target, rendered, metrics: measureImageFitLosses(target, rendered) }
}

/**
 * Exact fixed-point leave-one-out. A removal is accepted only when its complete
 * RGBA render is byte-identical at the search resolution and every declared
 * validation resolution. The loss deltas are still recorded for every final
 * retained instance, but the zero-pixel-difference gate is intentionally
 * stricter than a visual loss allowance.
 */
export function pruneRedundantInstances(
  coatOfArms: CoatOfArms,
  inputTarget: FitImage,
  pattern: DecodedDds,
  coloredEmblems: Record<string, DecodedDds>,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap = {},
  options: InstancePruneOptions = {},
): InstancePruneResult {
  const mode = options.mode ?? 'pixel-exact'
  const searchResolution = options.searchResolution ?? 96
  const validationResolutions = [...new Set(options.validationResolutions ?? [230, 512])]
    .filter((resolution) => resolution !== searchResolution)
  const numericLossTolerance = options.numericLossTolerance ?? 1e-12
  const allowedVisualDifferenceBytes = options.allowedVisualDifferenceBytes ?? 0
  const allowedCumulativeTotalLossIncrease = options.allowedCumulativeTotalLossIncrease ?? 0
  const allowedCumulativeEdgeLossIncrease = options.allowedCumulativeEdgeLossIncrease ?? 0
  if (
    !['pixel-exact', 'metric-pareto'].includes(mode)
    || !Number.isSafeInteger(searchResolution)
    || searchResolution < 1
    || validationResolutions.some((value) => !Number.isSafeInteger(value) || value < 1)
    || numericLossTolerance < 0
    || allowedVisualDifferenceBytes !== 0
    || allowedCumulativeTotalLossIncrease < 0
    || allowedCumulativeEdgeLossIncrease < 0
  ) throw new Error('剪枝门禁参数不合法；v1 只允许零像素差且损失预算不能为负')

  const items = flatten(coatOfArms)
  const drawnInstancesBefore = items.length
  for (const item of items) {
    if (!coloredEmblems[item.style.texture]) {
      throw new Error(`剪枝缺少纹章素材：${item.style.texture}`)
    }
  }
  const resolutions = [searchResolution, ...validationResolutions]
  const targets = new Map(resolutions.map((resolution) => (
    [resolution, resizeFitImage(inputTarget, resolution)]
  )))
  let currentModel = modelFromItems(coatOfArms, items)
  const states = new Map(resolutions.map((resolution) => (
    [resolution, renderState(
      currentModel,
      targets.get(resolution)!,
      pattern,
      coloredEmblems,
      surfaceMask,
      namedColors,
    )]
  )))
  const initialStates = new Map(states)
  const initialMetrics = { ...states.get(searchResolution)!.metrics, relativeImprovement: 0 }
  const removedEvidence: InstanceNecessityEvidence[] = []
  let finalNecessityEvidence: InstanceNecessityEvidence[] = []
  let fixedPointPasses = 0
  let evaluatedCandidates = 0

  while (true) {
    fixedPointPasses += 1
    let removedThisPass = 0
    const retainedThisPass: InstanceNecessityEvidence[] = []
    const totalInPass = items.length
    let completedInPass = 0
    for (let index = items.length - 1; index >= 0; index -= 1) {
      const item = items[index]
      const candidateItems = items.filter((_, itemIndex) => itemIndex !== index)
      const candidateModel = modelFromItems(coatOfArms, candidateItems)
      const measurements: InstanceRemovalMeasurement[] = []
      const candidateStates = new Map<number, ResolutionState>()
      let removable = true
      let reason: InstanceNecessityEvidence['reason'] = mode === 'pixel-exact'
        ? 'pixel-exact-redundant'
        : 'metric-pareto-redundant'
      for (const resolution of resolutions) {
        const current = states.get(resolution)!
        const candidate = renderState(
          candidateModel,
          targets.get(resolution)!,
          pattern,
          coloredEmblems,
          surfaceMask,
          namedColors,
        )
        candidateStates.set(resolution, candidate)
        const difference = pixelDifference(current.rendered, candidate.rendered)
        measurements.push({
          resolution,
          ...difference,
          colorLossDelta: candidate.metrics.colorLoss - current.metrics.colorLoss,
          edgeLossDelta: candidate.metrics.edgeLoss - current.metrics.edgeLoss,
          totalLossDelta: candidate.metrics.totalLoss - current.metrics.totalLoss,
        })
        if (mode === 'pixel-exact' && difference.differingBytes > allowedVisualDifferenceBytes) {
          removable = false
          reason = resolution === searchResolution ? 'changes-search-pixels' : 'changes-validation-pixels'
          break
        }
        if (mode === 'metric-pareto') {
          const initial = initialStates.get(resolution)!
          const exceedsCurrent = candidate.metrics.totalLoss > current.metrics.totalLoss + numericLossTolerance
            || candidate.metrics.edgeLoss > current.metrics.edgeLoss + numericLossTolerance
          const exceedsCumulative = candidate.metrics.totalLoss
              > initial.metrics.totalLoss + allowedCumulativeTotalLossIncrease + numericLossTolerance
            || candidate.metrics.edgeLoss
              > initial.metrics.edgeLoss + allowedCumulativeEdgeLossIncrease + numericLossTolerance
          if (removable && (exceedsCurrent || exceedsCumulative)) {
            removable = false
            reason = resolution === searchResolution
              ? 'would-worsen-search-metric'
              : 'would-worsen-validation-metric'
            // One failed member of the fixed resolution gate is sufficient to
            // prove this instance must stay. Avoid rendering the remaining
            // high-resolution members merely to collect redundant failures.
            break
          }
        }
      }
      evaluatedCandidates += 1
      completedInPass += 1
      options.onProgress?.({
        pass: fixedPointPasses,
        completedInPass,
        totalInPass,
        evaluatedCandidates,
        percent: Math.round(completedInPass / Math.max(1, totalInPass) * 100),
      })
      const evidence: InstanceNecessityEvidence = {
        instanceId: item.id,
        sourceBlockIndex: item.sourceBlockIndex,
        sourceInstanceIndex: item.sourceInstanceIndex,
        depth: item.instance.depth,
        pass: fixedPointPasses,
        removed: removable,
        reason,
        measurements,
      }
      if (evidence.removed) {
        items.splice(index, 1)
        currentModel = candidateModel
        for (const resolution of resolutions) {
          states.set(resolution, candidateStates.get(resolution)!)
        }
        removedEvidence.push(evidence)
        removedThisPass += 1
      } else {
        retainedThisPass.push(evidence)
      }
    }
    if (removedThisPass === 0) {
      finalNecessityEvidence = retainedThisPass.sort((left, right) => left.instanceId - right.instanceId)
      break
    }
  }

  const compressed = structurallyCompressCoatOfArms(currentModel).coatOfArms
  const finalMetrics = {
    ...states.get(searchResolution)!.metrics,
    relativeImprovement: 0,
  }
  for (const resolution of resolutions) {
    const initial = initialStates.get(resolution)!
    const final = states.get(resolution)!
    if (mode === 'pixel-exact') {
      for (const key of ['colorLoss', 'edgeLoss', 'totalLoss'] as const) {
        if (Math.abs(final.metrics[key] - initial.metrics[key]) > numericLossTolerance) {
          throw new Error(`精确剪枝固定点改变了 ${resolution}px ${key}`)
        }
      }
    } else if (
      final.metrics.totalLoss
        > initial.metrics.totalLoss + allowedCumulativeTotalLossIncrease + numericLossTolerance
      || final.metrics.edgeLoss
        > initial.metrics.edgeLoss + allowedCumulativeEdgeLossIncrease + numericLossTolerance
    ) {
      throw new Error(`Pareto 剪枝超过 ${resolution}px 累计损失预算`)
    }
  }
  return {
    coatOfArms: compressed,
    receipt: {
      contract: mode === 'pixel-exact'
        ? 'exact-leave-one-out-fixed-point-v1'
        : 'metric-pareto-leave-one-out-fixed-point-v1',
      mode,
      numericLossTolerance,
      allowedVisualDifferenceBytes,
      allowedCumulativeTotalLossIncrease,
      allowedCumulativeEdgeLossIncrease,
      searchResolution,
      validationResolutions,
      drawnInstancesBefore,
      drawnInstancesAfter: items.length,
      removedInstances: drawnInstancesBefore - items.length,
      fixedPointPasses,
      evaluatedCandidates,
      initialMetrics,
      finalMetrics,
      resolutionMetrics: resolutions.map((resolution) => ({
        resolution,
        initial: { ...initialStates.get(resolution)!.metrics },
        final: { ...states.get(resolution)!.metrics },
      })),
      removedEvidence,
      finalNecessityEvidence,
    },
  }
}
