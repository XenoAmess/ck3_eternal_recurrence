import { describe, expect, it } from 'vitest'
import {
  candidateDominance,
  MAX_COMPARISON_CANDIDATES,
  type CoatOfArmsComparisonCandidate,
} from './comparisonCandidates'

function candidate(
  id: string,
  totalLoss: number | undefined,
  edgeLoss: number | undefined,
  drawnInstances: number,
): CoatOfArmsComparisonCandidate {
  return {
    id,
    name: id,
    source: `coa = { parent = ${id} }`,
    stats: {
      logicalLayers: 1,
      coloredEmblemBlocks: 1,
      texturedEmblemBlocks: 0,
      drawnInstances,
      utf8Bytes: 10,
      lines: 1,
    },
    metrics: totalLoss === undefined || edgeLoss === undefined ? undefined : {
      colorLoss: totalLoss,
      edgeLoss,
      totalLoss,
      relativeImprovement: 0,
    },
    metricContract: totalLoss === undefined ? undefined : 'input-sha:scorer:renderer:96',
  }
}

describe('comparison candidate contract', () => {
  it('uses the requested one-to-three comparison slots', () => {
    expect(MAX_COMPARISON_CANDIDATES).toBe(3)
  })

  it('requires one candidate to be no worse on both losses and complexity before calling another dominated', () => {
    const simpler = candidate('simpler', 0.02, 0.04, 900)
    const dominated = candidate('dominated', 0.03, 0.05, 1_000)
    const edgeTradeoff = candidate('edge-tradeoff', 0.019, 0.06, 850)
    const candidates = [simpler, dominated, edgeTradeoff]
    expect(candidateDominance(simpler, candidates)).toBe('non-dominated')
    expect(candidateDominance(dominated, candidates)).toBe('dominated')
    expect(candidateDominance(edgeTradeoff, candidates)).toBe('non-dominated')
  })

  it('does not invent Pareto status when comparable fit metrics are absent', () => {
    const manual = candidate('manual', undefined, undefined, 2)
    expect(candidateDominance(manual, [manual])).toBe('unmeasured')
  })

  it('does not compare metrics produced under different input or renderer contracts', () => {
    const left = candidate('left', 0.02, 0.02, 500)
    const right = candidate('right', 0.03, 0.03, 600)
    right.metricContract = 'different-input:scorer:renderer:96'
    expect(candidateDominance(right, [left, right])).toBe('non-dominated')
  })
})
