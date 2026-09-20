import { describe, expect, it } from 'vitest'
import {
  createPersistedFitCheckpoint,
  parsePortableFitCheckpoint,
  restorePersistedFitInput,
  serializePortableFitCheckpoint,
  validatePersistedFitCheckpoint,
} from './fitCheckpointStore'
import type { DecodedFitImage } from './imageInput'
import type { ImageFitCheckpoint } from './imageFitter'

const image = () => ({
  width: 8,
  height: 8,
  pixels: new Uint8ClampedArray(8 * 8 * 4).fill(127),
})

const checkpoint = (): ImageFitCheckpoint => ({
  contract: 'ck3-coa-fit-checkpoint-v1',
  algorithm: 'ck3-coa-browser-fit-v6-budget-exhaustive-edge',
  lane: 'baseline',
  inputSha256: 'A'.repeat(64),
  assetPackManifestSha256: 'B'.repeat(64),
  resolution: 8,
  sourceWidth: 32,
  sourceHeight: 32,
  layerBudget: 16,
  randomSeed: null,
  nextTileIndex: 1,
  tileCount: 1,
  evaluatedCandidates: 12,
  tiles: [{
    minimumX: 0, minimumY: 0, maximumX: 8, maximumY: 8,
    color: [127, 127, 127], variance: 0, residual: 1,
  }],
  state: {
    coatOfArms: {
      outerKey: 'coa', parent: '', pattern: 'pattern_solid.dds',
      colors: ['black', 'black', 'black'], coloredEmblems: [], texturedEmblems: [],
    },
    candidateKey: 'candidate',
    patternName: 'pattern_solid.dds',
    selectedAssetNames: [],
    layerLosses: [1],
    reconstructionMode: 'native-tile-paint',
    paintPlacements: [],
  },
})

const input = (): DecodedFitImage => ({
  image: image(),
  pyramid: [image()],
  originalWidth: 32,
  originalHeight: 32,
  workingResolution: 8,
  mimeType: 'image/png',
  bytes: 128,
  sha256: 'A'.repeat(64),
  previewUrl: 'data:image/png;base64,AA==',
})

describe('persisted fit checkpoint', () => {
  it('round-trips a bounded input and exact search-state receipt', () => {
    const record = createPersistedFitCheckpoint(
      checkpoint(),
      input(),
      { packId: 'test-pack', manifestSha256: 'B'.repeat(64) },
      '2026-09-16T00:00:00.000Z',
    )
    expect(validatePersistedFitCheckpoint(record)).toBe(record)
    const restored = restorePersistedFitInput(record)
    expect(restored).toMatchObject({
      originalWidth: 32,
      originalHeight: 32,
      sha256: 'A'.repeat(64),
      bytes: 128,
    })
    expect(restored.image.pixels).toEqual(input().image.pixels)
    expect(restored.image.pixels).not.toBe(record.input.image.pixels)
  })

  it('fails closed on version and identity mismatches', () => {
    const record = createPersistedFitCheckpoint(
      checkpoint(), input(), { packId: 'test-pack', manifestSha256: 'B'.repeat(64) },
    )
    expect(() => validatePersistedFitCheckpoint({ ...record, schema: 'future-v2' }))
      .toThrow('版本不兼容')
    expect(() => validatePersistedFitCheckpoint({
      ...record,
      input: { ...record.input, sha256: 'C'.repeat(64) },
    })).toThrow('身份、预算或搜索游标不一致')
  })

  it('exports and imports a SHA-bound portable checkpoint with typed RGBA restored', async () => {
    const record = createPersistedFitCheckpoint(
      checkpoint(), input(), { packId: 'test-pack', manifestSha256: 'B'.repeat(64) },
      '2026-09-21T00:00:00.000Z',
    )
    const text = await serializePortableFitCheckpoint(record)
    const restored = await parsePortableFitCheckpoint(text)
    expect(restored).toEqual(record)
    expect(restored.input.image.pixels).toBeInstanceOf(Uint8ClampedArray)
    expect(restored.input.image.pixels).not.toBe(record.input.image.pixels)
    expect(text).toContain('ck3-coa-portable-fit-checkpoint-v1')
  })

  it('rejects tampered portable payloads before restoring search state', async () => {
    const record = createPersistedFitCheckpoint(
      checkpoint(), input(), { packId: 'test-pack', manifestSha256: 'B'.repeat(64) },
    )
    const envelope = JSON.parse(await serializePortableFitCheckpoint(record))
    envelope.payload.layerBudget = 99
    await expect(parsePortableFitCheckpoint(JSON.stringify(envelope)))
      .rejects.toThrow('payload SHA-256 不一致')
  })
})
