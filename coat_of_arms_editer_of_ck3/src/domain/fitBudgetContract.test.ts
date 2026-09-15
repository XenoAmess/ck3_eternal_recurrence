import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import { FIT_BUDGET_STRESS_CONTRACT } from './fitBudgetContract'
import { fitImageToCoatOfArms, type FitImage, type FitTextureCandidate } from './imageFitter'

const opaqueRedChannel = (): DecodedDds => {
  const size = 4
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let offset = 0; offset < pixels.length; offset += 4) {
    pixels[offset] = 255
    pixels[offset + 3] = 255
  }
  return { width: size, height: size, fourCC: 'BGRA8', pixels }
}

const candidate = (name: string): FitTextureCandidate => ({
  name,
  assetSha256: name.padEnd(64, '0').slice(0, 64).toUpperCase(),
  texture: opaqueRedChannel(),
})

const stressTarget = (size: number): FitImage => {
  const colors = [
    [13, 27, 41], [221, 37, 53], [29, 199, 113], [237, 211, 61],
  ] as const
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const offset = (y * size + x) * 4
      const color = colors[(x + y * 3) % colors.length]
      pixels.set([...color, 255], offset)
    }
  }
  return { width: size, height: size, pixels }
}

describe('real 10,000 fit-budget contract', () => {
  it('executes the uncapped budget and records natural resolution convergence', () => {
    const contract = FIT_BUDGET_STRESS_CONTRACT
    const progress: { layerBudget: number, evaluatedCandidates: number }[] = []
    const started = performance.now()
    const result = fitImageToCoatOfArms(
      stressTarget(contract.searchResolution),
      [candidate('pattern_solid.dds')],
      [candidate('ce_block_02.dds')],
      {
        resolution: contract.searchResolution,
        maxLayers: 10_000,
        maxPatterns: 1,
        maxEmblemCandidates: 1,
        refinementCandidates: 8,
        beamWidth: 1,
        onProgress: (update) => progress.push({
          layerBudget: update.layerBudget,
          evaluatedCandidates: update.evaluatedCandidates,
        }),
      },
    )
    const durationMs = performance.now() - started

    expect(result.provenance.layerBudget).toBe(10_000)
    expect(result.provenance.nativeTileSearch.userBudgetAppliedWithoutClamp).toBe(10_000)
    expect(result.provenance.nativeTileSearch.maximumDepth).toBe(7)
    expect(result.provenance.nativeTileSearch.pixelLeafCapacity).toBe(9_216)
    expect(result.provenance.drawnInstances).toBeGreaterThan(1_024)
    expect(result.provenance.drawnInstances).toBeLessThanOrEqual(10_000)
    expect(result.provenance.evaluatedCandidates).toBeGreaterThan(result.provenance.drawnInstances)
    expect(['exact_match', 'no_improvement']).toContain(result.provenance.terminationReason)
    expect(progress.length).toBeGreaterThan(10)
    expect(progress.every((update) => update.layerBudget === 10_000)).toBe(true)
    expect(durationMs).toBeLessThan(contract.maximumDurationMs[10000])
    console.info(JSON.stringify({
      contract: contract.contract,
      budget: 10_000,
      durationMs,
      actualDrawnInstances: result.provenance.drawnInstances,
      evaluatedCandidates: result.provenance.evaluatedCandidates,
      terminationReason: result.provenance.terminationReason,
      nativeTileSearch: result.provenance.nativeTileSearch,
      totalLoss: result.metrics.totalLoss,
      edgeLoss: result.metrics.edgeLoss,
    }))
  }, 190_000)
})
