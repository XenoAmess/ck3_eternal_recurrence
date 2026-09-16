import type { CoatOfArmsDocumentStats } from './documentStats'
import type { ImageFitMetrics } from './imageFitter'

export const MAX_COMPARISON_CANDIDATES = 3

export interface CoatOfArmsComparisonCandidate {
  id: string
  name: string
  source: string
  stats: CoatOfArmsDocumentStats
  metrics?: ImageFitMetrics
  metricContract?: string
  previewUrl?: string
  automaticFitIndex?: number
}

export type CandidateDominance = 'non-dominated' | 'dominated' | 'unmeasured'

export function candidateDominance(
  candidate: CoatOfArmsComparisonCandidate,
  candidates: readonly CoatOfArmsComparisonCandidate[],
): CandidateDominance {
  if (!candidate.metrics || !candidate.metricContract) return 'unmeasured'
  const dominated = candidates.some((other) => {
    if (
      other.id === candidate.id
      || !other.metrics
      || other.metricContract !== candidate.metricContract
    ) return false
    const noWorse = other.metrics.totalLoss <= candidate.metrics!.totalLoss
      && other.metrics.edgeLoss <= candidate.metrics!.edgeLoss
      && other.stats.drawnInstances <= candidate.stats.drawnInstances
    const strictlyBetter = other.metrics.totalLoss < candidate.metrics!.totalLoss
      || other.metrics.edgeLoss < candidate.metrics!.edgeLoss
      || other.stats.drawnInstances < candidate.stats.drawnInstances
    return noWorse && strictlyBetter
  })
  return dominated ? 'dominated' : 'non-dominated'
}
