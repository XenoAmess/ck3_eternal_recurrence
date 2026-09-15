import { describe, expect, it } from 'vitest'
import {
  FIT_WORKER_PROTOCOL,
  isCurrentFitWorkerMessage,
  type FitWorkerResponse,
} from './fitWorkerProtocol'

describe('fit worker protocol', () => {
  const progress = {
    phase: 'paint' as const,
    completed: 8,
    total: 16,
    percent: 50,
    layer: 4,
    layerBudget: 128,
    evaluatedCandidates: 20,
  }

  it('accepts only the current run and revision', () => {
    const message: FitWorkerResponse = {
      protocol: FIT_WORKER_PROTOCOL,
      kind: 'progress',
      runId: 7,
      revision: 3,
      progress,
    }
    expect(isCurrentFitWorkerMessage(message, 7, 3)).toBe(true)
    expect(isCurrentFitWorkerMessage(message, 6, 3)).toBe(false)
    expect(isCurrentFitWorkerMessage(message, 7, 2)).toBe(false)
  })
})
