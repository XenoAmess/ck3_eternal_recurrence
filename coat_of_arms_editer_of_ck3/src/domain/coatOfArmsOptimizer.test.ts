import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import { structurallyCompressCoatOfArms } from './coatOfArmsOptimizer'
import { parseCoatOfArms } from './parser'
import { renderCoatOfArms, type NamedColorMap } from './renderer'
import { serializeCoatOfArms } from './serializer'
import type { CoatOfArms } from './types'

const opaqueTexture = (red: number, green: number, blue: number): DecodedDds => ({
  width: 1,
  height: 1,
  fourCC: 'DXT5',
  pixels: new Uint8ClampedArray([red, green, blue, 255]),
})

const instance = (depth: number, x: number) => ({
  position: [x, 0.5] as [number, number],
  scale: [0.4, 0.4] as [number, number],
  rotation: 0,
  depth,
})

describe('coat of arms structural optimizer', () => {
  it('merges only adjacent equal-style blocks without changing pixels or parse semantics', () => {
    const coatOfArms: CoatOfArms = {
      outerKey: 'coa',
      parent: '',
      pattern: 'pattern.dds',
      colors: ['white', 'white', 'white'],
      coloredEmblems: [
        { texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [], instances: [instance(1, 0.2)] },
        { texture: 'block.dds', colors: ['blue', 'blue', 'blue'], mask: [], instances: [instance(2, 0.4)] },
        { texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [], instances: [instance(3, 0.6)] },
        { texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [], instances: [instance(4, 0.8)] },
      ],
      texturedEmblems: [],
    }
    const result = structurallyCompressCoatOfArms(coatOfArms)

    expect(result.receipt).toMatchObject({
      strategy: 'adjacent-equal-style-v1',
      exactStructureOnly: true,
      coloredEmblemBlocksBefore: 4,
      coloredEmblemBlocksAfter: 3,
      mergedBlocks: 1,
      drawnInstancesBefore: 4,
      drawnInstancesAfter: 4,
    })
    expect(result.receipt.utf8BytesAfter).toBeLessThan(result.receipt.utf8BytesBefore)
    expect(result.receipt.linesAfter).toBeLessThan(result.receipt.linesBefore)
    expect(result.coatOfArms.coloredEmblems.map((block) => block.colors[0]))
      .toEqual(['red', 'blue', 'red'])
    expect(result.coatOfArms.coloredEmblems[2].instances.map((item) => item.depth))
      .toEqual([3, 4])

    const assets = {
      pattern: opaqueTexture(255, 0, 0),
      coloredEmblems: { 'block.dds': opaqueTexture(0, 0, 128) },
    }
    const colors: NamedColorMap = { white: [1, 1, 1], red: [1, 0, 0], blue: [0, 0, 1] }
    const before = renderCoatOfArms(coatOfArms, assets, colors, 64)
    const after = renderCoatOfArms(result.coatOfArms, assets, colors, 64)
    expect(after?.pixels).toEqual(before?.pixels)

    const reparsed = parseCoatOfArms(serializeCoatOfArms(result.coatOfArms))
    expect(reparsed.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
    expect(reparsed.coatOfArms).toEqual(result.coatOfArms)
  })

  it('does not mutate the source document', () => {
    const source: CoatOfArms = {
      outerKey: 'coa', parent: '', pattern: 'pattern.dds', colors: ['white', 'white', 'white'],
      coloredEmblems: [
        { texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [1], instances: [instance(1, 0.3)] },
        { texture: 'block.dds', colors: ['red', 'red', 'red'], mask: [1], instances: [instance(2, 0.7)] },
      ],
      texturedEmblems: [{ texture: '_default.dds' }],
    }
    const frozen = JSON.stringify(source)
    const result = structurallyCompressCoatOfArms(source)

    result.coatOfArms.coloredEmblems[0].instances[0].position[0] = 0.9
    expect(JSON.stringify(source)).toBe(frozen)
  })
})
