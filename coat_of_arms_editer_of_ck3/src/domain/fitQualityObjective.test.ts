import { describe, expect, it, vi } from 'vitest'
import {
  compareFitQualityCandidate,
  createFitQualityObjective,
  FIT_QUALITY_OBJECTIVE_CONTRACT,
  FIT_QUALITY_SCALE_WEIGHTS,
  fitQualityHasNoScaleRegression,
} from './fitQualityObjective'

describe('Epsilon-Q E0 multi-resolution quality objective', () => {
  it('freezes the initial 96/230/512 weights and publishes every absolute loss', () => {
    const quality = createFitQualityObjective({ 96: 0.10, 230: 0.20, 512: 0.30 })
    expect(FIT_QUALITY_SCALE_WEIGHTS).toEqual({ 96: 0.20, 230: 0.45, 512: 0.35 })
    expect(Object.isFrozen(FIT_QUALITY_SCALE_WEIGHTS)).toBe(true)
    expect(quality).toMatchObject({
      contract: FIT_QUALITY_OBJECTIVE_CONTRACT,
      lossByScale: { 96: 0.10, 230: 0.20, 512: 0.30 },
    })
    expect(quality.weightedLoss).toBeCloseTo(0.215, 15)
    expect(Object.isFrozen(quality)).toBe(true)
    expect(Object.isFrozen(quality.lossByScale)).toBe(true)
  })

  it('rejects a weighted improvement when any scale regresses', () => {
    const incumbent = createFitQualityObjective({ 96: 0.20, 230: 0.20, 512: 0.20 })
    const candidate = createFitQualityObjective({ 96: 0.01, 230: 0.01, 512: 0.21 })
    expect(candidate.weightedLoss).toBeLessThan(incumbent.weightedLoss)
    expect(fitQualityHasNoScaleRegression(candidate, incumbent)).toBe(false)
    expect(compareFitQualityCandidate(candidate, incumbent)).toBe(1)
  })

  it('selects a lower weighted loss after all scales pass the no-regression gate', () => {
    const incumbent = createFitQualityObjective({ 96: 0.20, 230: 0.20, 512: 0.20 })
    const candidate = createFitQualityObjective({ 96: 0.20, 230: 0.18, 512: 0.19 })
    expect(fitQualityHasNoScaleRegression(candidate, incumbent)).toBe(true)
    expect(compareFitQualityCandidate(candidate, incumbent)).toBe(-1)
  })

  it('uses lower-priority criteria only for a numeric quality tie', () => {
    const incumbent = createFitQualityObjective({ 96: 0.20, 230: 0.20, 512: 0.20 })
    const better = createFitQualityObjective({ 96: 0.19, 230: 0.20, 512: 0.20 })
    const tie = createFitQualityObjective({ 96: 0.20, 230: 0.20, 512: 0.20 })
    const compareComplexity = vi.fn(() => -1)

    expect(compareFitQualityCandidate(better, incumbent, compareComplexity)).toBe(-1)
    expect(compareComplexity).not.toHaveBeenCalled()
    expect(compareFitQualityCandidate(tie, incumbent, compareComplexity)).toBe(-1)
    expect(compareComplexity).toHaveBeenCalledOnce()
  })

  it('rejects invalid loss vectors and tolerances', () => {
    expect(() => createFitQualityObjective({ 96: 0, 230: -1, 512: 0 })).toThrow(/230px/)
    const quality = createFitQualityObjective({ 96: 0, 230: 0, 512: 0 })
    expect(() => fitQualityHasNoScaleRegression(quality, quality, Number.NaN)).toThrow(/容差/)
  })
})
