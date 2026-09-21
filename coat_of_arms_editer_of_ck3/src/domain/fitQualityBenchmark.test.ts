import { describe, expect, it } from 'vitest'
import corpus from '../data/fit-quality-synthetic-corpus-v1.json'

describe('Delta-Q synthetic quality corpus', () => {
  it('freezes the exact-build identity and 192/64 split', () => {
    expect(corpus.schema).toBe('ck3-coa-fit-quality-synthetic-corpus-v1')
    expect(corpus.generator.contract).toBe('sha256-counter-no-prng-v1')
    expect(corpus.assetPack.id).toBe('ck3-1.19.0.6-base-complete')
    expect(corpus.assetPack.manifestSha256).toMatch(/^[A-F0-9]{64}$/)
    expect(corpus.counts).toEqual({ total: 256, dev: 192, holdout: 64 })
    expect(corpus.samples).toHaveLength(256)
    expect(corpus.samples.filter((sample) => sample.split === 'dev')).toHaveLength(192)
    expect(corpus.samples.filter((sample) => sample.split === 'holdout')).toHaveLength(64)
  })

  it('contains unique, complete and exact-asset-bound truth records', () => {
    expect(new Set(corpus.samples.map((sample) => sample.id)).size).toBe(256)
    expect(corpus.samplesPayloadSha256).toMatch(/^[A-F0-9]{64}$/)
    for (const sample of corpus.samples) {
      expect(sample.truth.pattern).toMatch(/pattern.*\.dds$/)
      expect(sample.truth.patternSha256).toMatch(/^[A-F0-9]{64}$/)
      expect(sample.truth.colors).toHaveLength(3)
      expect(sample.truth.coloredEmblems.length).toBeGreaterThanOrEqual(1)
      expect(sample.truth.coloredEmblems.length).toBeLessThanOrEqual(3)
      expect(sample.wrongEmblem.textureSha256).toMatch(/^[A-F0-9]{64}$/)
      const selected = new Set(sample.truth.coloredEmblems.map((emblem) => emblem.texture))
      expect(selected.has(sample.wrongEmblem.texture)).toBe(false)
      for (const [index, emblem] of sample.truth.coloredEmblems.entries()) {
        expect(emblem.texture).toMatch(/^ce_.*\.dds$/)
        expect(emblem.textureSha256).toMatch(/^[A-F0-9]{64}$/)
        expect(emblem.colors).toHaveLength(3)
        expect(emblem.instances).toHaveLength(1)
        expect(emblem.instances[0].depth).toBe(index + 1)
      }
    }
  })

  it('freezes strictly increasing perturbation ladders', () => {
    for (const ladder of [
      corpus.perturbationLadders.colorChannelDelta,
      corpus.perturbationLadders.positionDelta,
      corpus.perturbationLadders.scaleMultiplier,
      corpus.perturbationLadders.rotationDegrees,
    ]) {
      expect(ladder).toHaveLength(3)
      expect(ladder[0]).toBeLessThan(ladder[1])
      expect(ladder[1]).toBeLessThan(ladder[2])
    }
  })
})
