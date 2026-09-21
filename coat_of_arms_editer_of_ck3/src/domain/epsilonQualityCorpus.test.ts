import { describe, expect, it } from 'vitest'
import {
  EPSILON_QUALITY_CORPUS_CONTRACT,
  EPSILON_QUALITY_SCENARIOS,
  renderEpsilonQualityScenario,
} from './epsilonQualityCorpus'

describe('Epsilon-Q frozen programmatic corpus', () => {
  it('freezes 32 independent scenes across four balanced categories and two splits', () => {
    expect(EPSILON_QUALITY_SCENARIOS).toHaveLength(32)
    expect(new Set(EPSILON_QUALITY_SCENARIOS.map((item) => item.id)).size).toBe(32)
    expect(new Set(EPSILON_QUALITY_SCENARIOS.map((item) => item.family)).size).toBe(32)
    expect(EPSILON_QUALITY_SCENARIOS.filter((item) => item.split === 'development')).toHaveLength(16)
    expect(EPSILON_QUALITY_SCENARIOS.filter((item) => item.split === 'sealed-holdout')).toHaveLength(16)
    for (const category of ['flat-contour', 'fine-detail', 'color-overlap', 'texture-gradient']) {
      const cases = EPSILON_QUALITY_SCENARIOS.filter((item) => item.category === category)
      expect(cases).toHaveLength(8)
      expect(cases.filter((item) => item.split === 'development')).toHaveLength(4)
      expect(cases.filter((item) => item.split === 'sealed-holdout')).toHaveLength(4)
    }
    expect(EPSILON_QUALITY_SCENARIOS.every(
      (item) => item.generatorRevision === EPSILON_QUALITY_CORPUS_CONTRACT,
    )).toBe(true)
  })

  it('renders deterministically without mutating the frozen registry', () => {
    const signatures = EPSILON_QUALITY_SCENARIOS.map((scenario) => {
      const first = renderEpsilonQualityScenario(scenario, 48)
      const repeated = renderEpsilonQualityScenario(scenario, 48)
      expect(repeated).toEqual(first)
      return first.pixels.reduce(
        (hash, value, index) => (Math.imul(hash ^ value ^ index, 16_777_619) >>> 0),
        2_166_136_261,
      )
    })
    expect(new Set(signatures).size).toBe(32)
  })

  it('rejects non-frozen revisions and unsafe render sizes', () => {
    const scenario = EPSILON_QUALITY_SCENARIOS[0]
    expect(() => renderEpsilonQualityScenario({ ...scenario, id: 'unknown' }, 48)).toThrow(/revision/)
    expect(() => renderEpsilonQualityScenario(scenario, 8)).toThrow(/16\.\.1024/)
  })
})
