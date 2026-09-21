import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import {
  JOINT_REFINEMENT_CONTRACT,
  refineCoatOfArmsJointly,
  type JointRefinementObjective,
  type JointRefinementRenderAssets,
} from './fitJointRefinement'
import { renderCoatOfArms, type NamedColorMap, type RenderedCoatOfArms } from './renderer'
import type { CoatOfArms, CoatOfArmsInstance } from './types'

const texture = (
  width: number,
  height: number,
  pixel: (x: number, y: number) => [number, number, number, number],
): DecodedDds => {
  const pixels = new Uint8ClampedArray(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) pixels.set(pixel(x, y), (y * width + x) * 4)
  }
  return { width, height, fourCC: 'BGRA8', pixels }
}

const solid = (value: [number, number, number, number]): DecodedDds =>
  texture(4, 4, () => value)

const instance = (overrides: Partial<CoatOfArmsInstance> = {}): CoatOfArmsInstance => ({
  position: [0.5, 0.5],
  scale: [0.5, 0.5],
  rotation: 0,
  depth: 1,
  ...overrides,
})

const coat = (instances: CoatOfArmsInstance[] = [instance()]): CoatOfArms => ({
  outerKey: 'coa',
  parent: '',
  pattern: 'pattern.dds',
  colors: ['white', 'white', 'white'],
  coloredEmblems: [{
    texture: 'asymmetric.dds',
    colors: ['red', 'red', 'red'],
    mask: [],
    instances,
  }],
  texturedEmblems: [],
})

const colors: NamedColorMap = {
  black: [0, 0, 0],
  blue: [0, 0, 1],
  green: [0, 1, 0],
  red: [1, 0, 0],
  white: [1, 1, 1],
}

const assets: JointRefinementRenderAssets = {
  pattern: solid([128, 0, 0, 255]),
  coloredEmblems: {
    'asymmetric.dds': texture(8, 8, (x, y) => [0, 0, 128, x < 2 || y > x ? 255 : 0]),
    'other.dds': texture(8, 8, (x, y) => [0, 0, 128, x > 4 && y < 5 ? 255 : 0]),
  },
}

const pixelLoss = (target: RenderedCoatOfArms): JointRefinementObjective => ({ rendered }) => {
  let sum = 0
  for (let index = 0; index < target.pixels.length; index += 1) {
    const delta = target.pixels[index] - rendered.pixels[index]
    sum += delta * delta
  }
  return sum / target.pixels.length / (255 * 255)
}

const rendered = (value: CoatOfArms): RenderedCoatOfArms => {
  const result = renderCoatOfArms(value, assets, colors, 48)
  if (!result) throw new Error('test render failed')
  return result
}

describe('exact DDS joint refinement', () => {
  it('improves existing geometry under a fixed instance budget', () => {
    const source = coat([instance({ position: [0.4, 0.5], scale: [0.4, 0.5], rotation: 0 })])
    const target = coat([instance({ position: [0.5, 0.5], scale: [0.5, 0.5], rotation: 15 })])
    const original = JSON.stringify(source)
    const result = refineCoatOfArmsJointly(source, {
      assets,
      namedColors: colors,
      objective: pixelLoss(rendered(target)),
      renderSize: 48,
      maxEvaluations: 80,
      stages: [{
        id: 'exact-steps',
        passes: 4,
        positionSteps: [0.1],
        scaleSteps: [0.1],
        rotationSteps: [15],
      }],
    })

    expect(result.receipt.contract).toBe(JOINT_REFINEMENT_CONTRACT)
    expect(result.receipt.lossAfter).toBeLessThan(result.receipt.lossBefore)
    expect(result.receipt.drawnInstancesBefore).toBe(1)
    expect(result.receipt.drawnInstancesAfter).toBe(1)
    expect(result.receipt.acceptedMoves.length).toBeGreaterThan(0)
    expect(result.receipt.objectiveEvaluations).toBeLessThanOrEqual(80)
    expect(JSON.stringify(source)).toBe(original)
  })

  it('can recolor one shared-block instance and perform a one-for-one exact asset replacement', () => {
    const source = coat([
      instance({ position: [0.3, 0.5] }),
      instance({ position: [0.7, 0.5] }),
    ])
    const target: CoatOfArms = {
      ...coat(),
      coloredEmblems: [
        {
          texture: 'asymmetric.dds', colors: ['red', 'red', 'red'], mask: [],
          instances: [instance({ position: [0.3, 0.5] })],
        },
        {
          texture: 'other.dds', colors: ['green', 'green', 'green'], mask: [],
          instances: [instance({ position: [0.7, 0.5] })],
        },
      ],
    }
    const result = refineCoatOfArmsJointly(source, {
      assets,
      namedColors: colors,
      objective: pixelLoss(rendered(target)),
      renderSize: 48,
      maxEvaluations: 120,
      eligibleTextures: ['other.dds'],
      colorCandidates: ['green'],
      stages: [{
        id: 'style',
        passes: 4,
        tryColorCandidates: true,
        tryTextureReplacements: true,
      }],
    })

    expect(result.receipt.lossAfter).toBeLessThan(result.receipt.lossBefore)
    expect(result.receipt.drawnInstancesAfter).toBe(2)
    expect(result.coatOfArms.coloredEmblems.length).toBeGreaterThan(1)
    expect(result.receipt.acceptedMoves.some(({ move }) => move.kind === 'color')).toBe(true)
    expect(result.receipt.acceptedMoves.some(({ move }) => move.kind === 'texture-replacement')).toBe(true)
  })

  it('keeps the incumbent on exact ties with deterministic receipts', () => {
    const source = coat()
    const run = () => refineCoatOfArmsJointly(source, {
      assets,
      namedColors: colors,
      objective: () => 1,
      maxEvaluations: 9,
      eligibleTextures: ['other.dds'],
      colorCandidates: ['green'],
      stages: [{
        id: 'tie',
        passes: 2,
        positionSteps: [0.1],
        scaleSteps: [0.1],
        rotationSteps: [10],
        colorSteps: [0.1],
        tryColorCandidates: true,
        tryTextureReplacements: true,
      }],
    })
    const first = run()
    const second = run()

    expect(first.coatOfArms).toEqual(source)
    expect(first.coatOfArms).not.toBe(source)
    expect(first.receipt).toEqual(second.receipt)
    expect(first.receipt).toMatchObject({
      evaluationBudget: 9,
      objectiveEvaluations: 5,
      evaluatedMoves: 4,
      acceptedMoves: [],
      lossBefore: 1,
      lossAfter: 1,
      keptIncumbent: true,
      terminationReason: 'no-improvement',
    })
  })

  it('hard-stops at the total evaluation budget', () => {
    const result = refineCoatOfArmsJointly(coat(), {
      assets,
      namedColors: colors,
      objective: ({ coatOfArms }) => -coatOfArms.coloredEmblems[0].instances[0].position[0],
      maxEvaluations: 2,
      stages: [{ id: 'budget', passes: 5, positionSteps: [0.1] }],
    })

    expect(result.receipt.objectiveEvaluations).toBe(2)
    expect(result.receipt.evaluatedMoves).toBe(1)
    expect(result.receipt.terminationReason).toBe('evaluation-budget')
    expect(result.receipt.drawnInstancesAfter).toBe(1)
  })
})
