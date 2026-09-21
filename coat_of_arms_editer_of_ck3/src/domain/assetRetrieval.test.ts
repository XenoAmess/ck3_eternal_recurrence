import { describe, expect, it } from 'vitest'
import {
  ASSET_RETRIEVAL_CONTRACT,
  computeAssetRetrievalDescriptorV2,
  rankAssetRetrievalV2,
  transformAssetRetrievalGrid,
} from './assetRetrieval'
import { FIT_SHAPE_DESCRIPTOR_SIZE } from './shapeFeatures'

const size = FIT_SHAPE_DESCRIPTOR_SIZE
const grid = (predicate: (x: number, y: number) => boolean) => Float32Array.from(
  { length: size * size },
  (_, index) => predicate(index % size, Math.floor(index / size)) ? 1 : 0,
)

describe('asset retrieval v2', () => {
  it('extracts distance, moment, histogram, symmetry and topology features deterministically', () => {
    const ring = grid((x, y) => {
      const radius = Math.hypot(x - 8.5, y - 8.5)
      return radius >= 4 && radius <= 7
    })
    const first = computeAssetRetrievalDescriptorV2(ring)
    const repeated = computeAssetRetrievalDescriptorV2(ring)
    expect(ASSET_RETRIEVAL_CONTRACT).toContain('sdf-hu-radial-orientation-topology')
    expect([...first.signedDistanceField]).toEqual([...repeated.signedDistanceField])
    expect([...first.huMoments]).toEqual([...repeated.huMoments])
    expect(first.topology.components).toBe(1)
    expect(first.topology.enclosedRegions).toBe(1)
    expect(first.topology.fillRatio).toBeGreaterThan(0)
  })

  it('recovers a rotated and mirrored asymmetric identity ahead of distractors', () => {
    const hook = grid((x, y) => (x >= 3 && x <= 6 && y >= 2 && y <= 15) || (x >= 6 && x <= 13 && y >= 12 && y <= 15))
    const ring = grid((x, y) => {
      const radius = Math.hypot(x - 8.5, y - 8.5)
      return radius >= 4 && radius <= 7
    })
    const cross = grid((x, y) => (x >= 7 && x <= 10) || (y >= 7 && y <= 10))
    const query = computeAssetRetrievalDescriptorV2(transformAssetRetrievalGrid(hook, 90, -1))
    const ranked = rankAssetRetrievalV2(query, [
      { item: 'ring', name: 'ring', descriptor: computeAssetRetrievalDescriptorV2(ring) },
      { item: 'hook', name: 'hook', descriptor: computeAssetRetrievalDescriptorV2(hook) },
      { item: 'cross', name: 'cross', descriptor: computeAssetRetrievalDescriptorV2(cross) },
    ])
    expect(ranked[0].item).toBe('hook')
    expect(ranked[0].loss).toBeLessThan(ranked[1].loss)
    expect(ranked[0].rotation % 90).toBe(0)
  })

  it('uses stable names to break exact duplicate ties', () => {
    const square = computeAssetRetrievalDescriptorV2(grid((x, y) => x >= 4 && x <= 13 && y >= 4 && y <= 13))
    const ranked = rankAssetRetrievalV2(square, [
      { item: 2, name: 'z.dds', descriptor: square },
      { item: 1, name: 'a.dds', descriptor: square },
    ])
    expect(ranked.map((item) => item.name)).toEqual(['a.dds', 'z.dds'])
  })
})
