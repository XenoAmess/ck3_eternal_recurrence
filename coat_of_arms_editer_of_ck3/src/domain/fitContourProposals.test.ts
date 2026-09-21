import { describe, expect, it } from 'vitest'
import {
  FIT_CONTOUR_PROPOSAL_CONTRACT,
  analyzeContourResidual,
  proposeContourCandidates,
  type ContourImagePlane,
  type ContourPrimitiveAsset,
} from './fitContourProposals'

const image = (width = 48, height = 48, value = 255): ContourImagePlane => {
  const pixels = new Uint8ClampedArray(width * height * 4)
  for (let index = 0; index < width * height; index += 1) {
    const offset = index * 4
    pixels[offset] = value
    pixels[offset + 1] = value
    pixels[offset + 2] = value
    pixels[offset + 3] = 255
  }
  return { width, height, pixels }
}

const paint = (source: ContourImagePlane, x: number, y: number, value = 0) => {
  if (x < 0 || y < 0 || x >= source.width || y >= source.height) return
  const offset = (y * source.width + x) * 4
  ;(source.pixels as Uint8ClampedArray)[offset] = value
  ;(source.pixels as Uint8ClampedArray)[offset + 1] = value
  ;(source.pixels as Uint8ClampedArray)[offset + 2] = value
}

const assets = (): ContourPrimitiveAsset<string>[] => [
  {
    id: 'ce_block_02.dds',
    identity: 'block-sha',
    texture: 'ce_block_02.dds',
    family: 'block',
    mask: [1],
    shapeFeatures: { contentSpan: [1, 1], alphaEnergy: 1, contourEnergy: 0.06 },
  },
  {
    id: 'ce_circle.dds',
    identity: 'circle-sha',
    texture: 'ce_circle.dds',
    family: 'circle',
    shapeFeatures: { contentSpan: [0.92, 0.92], alphaEnergy: 0.76, contourEnergy: 0.08 },
  },
  {
    id: 'ce_lozenge.dds',
    identity: 'diamond-sha',
    texture: 'ce_lozenge.dds',
    family: 'diamond',
    shapeFeatures: { contentSpan: [0.88, 0.88], alphaEnergy: 0.52, contourEnergy: 0.10 },
  },
  {
    id: 'ce_triangle_mask.dds',
    identity: 'wedge-sha',
    texture: 'ce_triangle_mask.dds',
    family: 'wedge',
    shapeFeatures: { contentSpan: [0.9, 0.82], alphaEnergy: 0.48, contourEnergy: 0.13 },
  },
]

function expectAngleNear(actual: number, expected: number, tolerance = 3) {
  const delta = Math.abs(actual - expected)
  expect(Math.min(delta, 180 - delta)).toBeLessThanOrEqual(tolerance)
}

describe('contour proposal generation', () => {
  it('finds horizontal, vertical and diagonal fine lines and emits oriented block geometry', () => {
    const cases: Array<{
      draw: (target: ContourImagePlane) => void
      angle: number
    }> = [
      {
        draw: (target) => {
          for (let x = 7; x <= 40; x += 1) paint(target, x, 23)
        },
        angle: 0,
      },
      {
        draw: (target) => {
          for (let y = 7; y <= 40; y += 1) paint(target, 23, y)
        },
        angle: 90,
      },
      {
        draw: (target) => {
          for (let offset = 0; offset <= 31; offset += 1) paint(target, 8 + offset, 8 + offset)
        },
        angle: 45,
      },
    ]

    for (const fixture of cases) {
      const target = image()
      const rendered = image()
      fixture.draw(target)
      const result = proposeContourCandidates(target, rendered, assets())
      expect(result.contract).toBe(FIT_CONTOUR_PROPOSAL_CONTRACT)
      expect(result.analysis.regions).toHaveLength(1)
      expect(result.analysis.regions[0].kind).toBe('fine-line')
      expectAngleNear(result.analysis.regions[0].dominantAngleDegrees, fixture.angle)
      const block = result.proposals.find((proposal) => proposal.family === 'block')
      expect(block).toBeDefined()
      expectAngleNear(block!.instance.rotation, fixture.angle)
      expect(block!.instance.scale[0]).toBeGreaterThan(block!.instance.scale[1] * 8)
      expect(block!.instance.position[0]).toBeGreaterThan(0)
      expect(block!.instance.position[0]).toBeLessThan(1)
      expect(block!.instance.position[1]).toBeGreaterThan(0)
      expect(block!.instance.position[1]).toBeLessThan(1)
    }
  })

  it('adds circle and diamond fallbacks for compact blobs and wedge alternatives for curved residuals', () => {
    const rendered = image()
    const disk = image()
    for (let y = 0; y < disk.height; y += 1) {
      for (let x = 0; x < disk.width; x += 1) {
        if (Math.hypot(x - 24, y - 24) <= 7) paint(disk, x, y)
      }
    }
    const diskResult = proposeContourCandidates(disk, rendered, assets())
    expect(diskResult.analysis.regions[0].kind).toBe('compact')
    expect(diskResult.proposals.map((proposal) => proposal.family)).toEqual([
      'block', 'circle', 'diamond', 'wedge',
    ])

    const arc = image()
    for (let degrees = 18; degrees <= 162; degrees += 2) {
      const radians = degrees * Math.PI / 180
      const x = Math.round(24 + Math.cos(radians) * 13)
      const y = Math.round(27 - Math.sin(radians) * 13)
      paint(arc, x, y)
      paint(arc, x, y + 1)
    }
    const arcResult = proposeContourCandidates(arc, rendered, assets())
    expect(arcResult.analysis.regions[0].kind).toBe('curved')
    expect(arcResult.proposals[0].family).toBe('block')
    expect(arcResult.proposals.some((proposal) => proposal.family === 'wedge')).toBe(true)
    expect(arcResult.analysis.regions[0].curvature).toBeGreaterThan(0.34)
  })

  it('keeps diagnostics, limits and ordering deterministic across repeated and reordered inputs', () => {
    const target = image()
    const rendered = image()
    for (let x = 4; x <= 19; x += 1) paint(target, x, 8)
    for (let y = 25; y <= 42; y += 1) paint(target, 36, y)

    const options = {
      maximumRegions: 2,
      maximumCandidates: 5,
      maximumCandidatesPerRegion: 4,
    }
    const first = proposeContourCandidates(target, rendered, assets(), options)
    const repeated = proposeContourCandidates(target, rendered, [...assets()].reverse(), options)
    expect(repeated).toEqual(first)
    expect(first.proposals).toHaveLength(5)
    expect(new Set(first.proposals.map((proposal) => proposal.stableKey)).size).toBe(5)
    expect(first.proposals.slice(0, 2).every((proposal) => proposal.family === 'block')).toBe(true)
    expect(new Set(first.proposals.slice(0, 2).map((proposal) => proposal.regionId)).size).toBe(2)
    expect(first.diagnostics.truncatedCandidates).toBe(3)
    expect(first.analysis.activePixels).toBe(34)

    const analysis = analyzeContourResidual(target, rendered, { maximumRegions: 1 })
    expect(analysis.regions).toHaveLength(1)
    expect(analysis.truncatedRegions).toBe(1)
  })

  it('returns no regions for an exact render and rejects a missing block brush', () => {
    const exact = image()
    expect(analyzeContourResidual(exact, exact).regions).toEqual([])
    expect(() => proposeContourCandidates(exact, exact, assets().filter((asset) => asset.family !== 'block')))
      .toThrow(/block brush/)
  })
})
