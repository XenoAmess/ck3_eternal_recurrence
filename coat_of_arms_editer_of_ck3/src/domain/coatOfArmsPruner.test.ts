import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import { pruneRedundantInstances } from './coatOfArmsPruner'
import { renderCoatOfArms, type NamedColorMap } from './renderer'
import type { CoatOfArms } from './types'

const texture = (alpha = 255): DecodedDds => ({
  width: 1,
  height: 1,
  fourCC: 'DXT5',
  pixels: new Uint8ClampedArray([255, 0, 0, alpha]),
})

describe('coat of arms instance pruner', () => {
  it('removes a fully covered instance and proves the remaining fixed point', () => {
    const coatOfArms: CoatOfArms = {
      outerKey: 'coa', parent: '', pattern: 'pattern.dds', colors: ['white', 'white', 'white'],
      coloredEmblems: [
        {
          texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [],
          instances: [{ position: [0.5, 0.5], scale: [0.5, 0.5], rotation: 0, depth: 1 }],
        },
        {
          texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [],
          instances: [{ position: [0.5, 0.5], scale: [0.5, 0.5], rotation: 0, depth: 2 }],
        },
        {
          texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [],
          instances: [{ position: [0.15, 0.15], scale: [0.2, 0.2], rotation: 0, depth: 3 }],
        },
      ],
      texturedEmblems: [],
    }
    const colors: NamedColorMap = { white: [1, 1, 1], red: [1, 0, 0], blue: [0, 0, 1] }
    const pattern = texture()
    const block = texture()
    const targetRender = renderCoatOfArms(
      coatOfArms,
      { pattern, coloredEmblems: { 'block.dds': block } },
      colors,
      32,
    )!
    const result = pruneRedundantInstances(
      coatOfArms,
      { width: 32, height: 32, pixels: targetRender.pixels },
      pattern,
      { 'block.dds': block },
      undefined,
      colors,
      { searchResolution: 32, validationResolutions: [48, 64] },
    )

    expect(result.receipt).toMatchObject({
      contract: 'exact-leave-one-out-fixed-point-v1',
      drawnInstancesBefore: 3,
      drawnInstancesAfter: 2,
      removedInstances: 1,
      fixedPointPasses: 2,
    })
    expect(result.receipt.removedEvidence.map((item) => item.instanceId)).toEqual([1])
    expect(result.receipt.removedEvidence[0].measurements).toHaveLength(3)
    expect(result.receipt.removedEvidence[0].measurements.every(
      (item) => item.differingBytes === 0 && item.maximumByteDifference === 0,
    )).toBe(true)
    expect(result.receipt.finalNecessityEvidence.map((item) => item.instanceId)).toEqual([0, 2])
    expect(result.receipt.finalNecessityEvidence.every((item) => item.removed === false)).toBe(true)
    expect(result.receipt.finalNecessityEvidence.every(
      (item) => item.reason === 'changes-search-pixels',
    )).toBe(true)
    expect(result.receipt.finalMetrics).toEqual(result.receipt.initialMetrics)
  })

  it('rejects incomplete assets and any non-zero visual allowance', () => {
    const coatOfArms: CoatOfArms = {
      outerKey: 'coa', parent: '', pattern: 'pattern.dds', colors: ['white', 'white', 'white'],
      coloredEmblems: [{
        texture: 'missing.dds', colors: ['white', 'white', 'white'], mask: [],
        instances: [{ position: [0.5, 0.5], scale: [1, 1], rotation: 0, depth: 1 }],
      }],
      texturedEmblems: [],
    }
    const target = { width: 1, height: 1, pixels: new Uint8ClampedArray([255, 255, 255, 255]) }
    expect(() => pruneRedundantInstances(
      coatOfArms, target, texture(), {}, undefined,
    )).toThrow(/缺少纹章素材/)
    expect(() => pruneRedundantInstances(
      coatOfArms, target, texture(), { 'missing.dds': texture() }, undefined, {},
      { allowedVisualDifferenceBytes: 1 },
    )).toThrow(/只允许零像素差/)
  })
})
