import { describe, expect, it } from 'vitest'
import { createCoatOfArms } from './types'
import { isDeterministicColorExpression, validateCoatOfArms } from './validation'

describe('CK3 coat of arms structured-model validation', () => {
  it('accepts the color literal families proven by the capability report', () => {
    expect(isDeterministicColorExpression('blue')).toBe(true)
    expect(isDeterministicColorExpression('rgb { 32 64 160 }')).toBe(true)
    expect(isDeterministicColorExpression('hsv { 0.5 0.75 1 }')).toBe(true)
  })

  it('rejects executable-looking blocks and unresolved variables', () => {
    expect(isDeterministicColorExpression('effect { add_gold = 1000 }')).toBe(false)
    expect(isDeterministicColorExpression('@unknown')).toBe(false)

    const coatOfArms = createCoatOfArms()
    coatOfArms.colors[0] = 'trigger { always = yes }'
    expect(validateCoatOfArms(coatOfArms)).toContainEqual(expect.objectContaining({
      severity: 'error',
      message: expect.stringContaining('命名颜色或 rgb/hsv'),
    }))
  })

  it('rejects fractional or out-of-range RGB in root and emblem colors', () => {
    for (const expression of [
      'rgb { 0.802549 0.772549 0.772549 }',
      'rgb { 0.8 197 197 }',
      'rgb { 197.0 197 197 }',
      'rgb { 1e2 197 197 }',
      'rgb { -1 197 197 }',
      'rgb { 256 197 197 }',
    ]) {
      expect(isDeterministicColorExpression(expression)).toBe(false)
      const coatOfArms = createCoatOfArms()
      coatOfArms.colors[0] = expression
      coatOfArms.coloredEmblems[0].colors[2] = expression
      expect(validateCoatOfArms(coatOfArms).filter(({ severity }) => severity === 'error')).toHaveLength(2)
    }
    expect(isDeterministicColorExpression('rgb { 0 1 255 }')).toBe(true)
  })

  it('guards finite instance data and marks unproven textured resources', () => {
    const coatOfArms = createCoatOfArms()
    coatOfArms.coloredEmblems[0].instances[0].depth = Number.NaN
    coatOfArms.texturedEmblems.push({ texture: 'custom_texture.dds' })

    const diagnostics = validateCoatOfArms(coatOfArms)
    expect(diagnostics.some((item) => item.severity === 'error' && item.message.includes('depth'))).toBe(true)
    expect(diagnostics.some((item) => item.severity === 'warning' && item.message.includes('_default.dds'))).toBe(true)
  })

  it('accepts only the three integer mask channels proven by the engine model', () => {
    const accepted = createCoatOfArms()
    accepted.coloredEmblems[0].mask = [1, 2, 3]
    expect(validateCoatOfArms(accepted).some((item) => item.message.includes('mask')))
      .toBe(false)

    for (const mask of [[0], [4], [1.5], [Number.NaN]]) {
      const rejected = createCoatOfArms()
      rejected.coloredEmblems[0].mask = mask
      expect(validateCoatOfArms(rejected)).toContainEqual(expect.objectContaining({
        severity: 'error',
        message: expect.stringContaining('分区索引 1、2、3'),
      }))
    }
  })
})
