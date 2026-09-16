import { describe, expect, it } from 'vitest'
import {
  calculateWebAssetWinnerSetSha256,
  loadWebAssetPackFiles,
  parseWebAssetPack,
  readWebFitIndex,
  verifyWebAssetPackVfsReceipt,
} from './assetPack'
import { FIT_SHAPE_DESCRIPTOR_SIZE, FIT_SHAPE_SCALAR_FIELDS } from './shapeFeatures'

const entry = {
  kind: 'pattern',
  name: 'pattern_solid.dds',
  colors: 1,
  visible: true,
  category: 'basic',
  url: `assets/${'a'.repeat(64)}.dds`,
  asset_bytes: 128,
  asset_sha256: 'A'.repeat(64),
  dds: { width: 16, height: 16, format: 'DXT1' },
}

const pack = () => ({
  schema: 'ck3-coa-web-asset-pack-v1',
  schema_version: 1,
  pack_id: 'ck3-1.19.0.6-alpha',
  ck3_build: '1.19.0.6',
  source_manifest_sha256: 'B'.repeat(64),
  named_colors: { red: [0.8, 0.1, 0.1] },
  assets: [
    entry,
    {
      ...entry,
      kind: 'surface_mask',
      name: 'coa_mask_texture.dds',
      url: `assets/${'c'.repeat(64)}.dds`,
      asset_sha256: 'C'.repeat(64),
    },
  ],
  vfs_receipt: {
    schema: 'ck3-coa-vfs-receipt-v1',
    scope: 'base_game_only',
    resolution_policy: 'single_source_no_conflicts',
    load_configuration_sha256: null,
    winner_set_sha256: 'D'.repeat(64),
    resolved_asset_count: 2,
    conflict_count: 0,
    sources: [{
      source_id: 'ck3-base-1.19.0.6',
      source_kind: 'base_game',
      precedence_order: 0,
      source_identity_sha256: 'B'.repeat(64),
    }],
    native_precedence_evidence: {
      status: 'scoped_passed',
      evidence_id: 'vfs-winner-native-r22',
      direct_path_winner_rule: 'later_enabled_source_wins',
      scope: 'two enabled directory mods with one conflicting registered direct DDS path',
      uncovered: ['DLC mount precedence', 'archive mod precedence'],
    },
  },
})

describe('web asset pack contract', () => {
  it('accepts a bounded content-addressed pack', () => {
    const parsed = parseWebAssetPack(pack())
    expect(parsed.ck3_build).toBe('1.19.0.6')
    expect(parsed.assets).toHaveLength(2)
    expect(parsed.named_colors.red).toEqual([0.8, 0.1, 0.1])
    expect(parsed.vfs_receipt.scope).toBe('base_game_only')
  })

  it('fails closed when the VFS winner-set receipt does not bind the parsed inventory', async () => {
    const parsed = parseWebAssetPack(pack())
    await expect(verifyWebAssetPackVfsReceipt(parsed)).rejects.toThrow(/winner_set_sha256/)
    parsed.vfs_receipt.winner_set_sha256 = await calculateWebAssetWinnerSetSha256(parsed)
    await expect(verifyWebAssetPackVfsReceipt(parsed)).resolves.toBeUndefined()
  })

  it('requires load identity and a non-base source for resolved overlay receipts', () => {
    const invalid = pack()
    invalid.vfs_receipt = {
      ...invalid.vfs_receipt,
      scope: 'resolved_overlay',
      resolution_policy: 'later_enabled_source_wins_direct_path',
    }
    expect(() => parseWebAssetPack(invalid)).toThrow(/resolved_overlay/)
  })

  it('binds every resolved-overlay winner to a declared source', async () => {
    const overlay: any = pack()
    overlay.assets = overlay.assets.map((item: Record<string, unknown>, index: number) => ({
      ...item,
      source_id: index === 0 ? 'ck3-base-1.19.0.6' : 'later-directory-mod',
    }))
    overlay.vfs_receipt = {
      ...overlay.vfs_receipt,
      scope: 'resolved_overlay',
      resolution_policy: 'later_enabled_source_wins_direct_path',
      load_configuration_sha256: 'E'.repeat(64),
      conflict_count: 1,
      sources: [
        overlay.vfs_receipt.sources[0],
        {
          source_id: 'later-directory-mod',
          source_kind: 'directory_mod',
          precedence_order: 1,
          source_identity_sha256: 'F'.repeat(64),
        },
      ],
    }
    const parsed = parseWebAssetPack(overlay)
    overlay.vfs_receipt.winner_set_sha256 = await calculateWebAssetWinnerSetSha256(parsed)
    const verified = parseWebAssetPack(overlay)

    await expect(verifyWebAssetPackVfsReceipt(verified)).resolves.toBeUndefined()
    expect(verified.assets.map((item) => item.source_id)).toEqual([
      'ck3-base-1.19.0.6',
      'later-directory-mod',
    ])
  })

  it('rejects a resolved-overlay winner without source provenance', () => {
    const overlay: any = pack()
    overlay.vfs_receipt = {
      ...overlay.vfs_receipt,
      scope: 'resolved_overlay',
      resolution_policy: 'later_enabled_source_wins_direct_path',
      load_configuration_sha256: 'E'.repeat(64),
      sources: [
        overlay.vfs_receipt.sources[0],
        {
          source_id: 'later-directory-mod',
          source_kind: 'directory_mod',
          precedence_order: 1,
          source_identity_sha256: 'F'.repeat(64),
        },
      ],
    }
    expect(() => parseWebAssetPack(overlay)).toThrow(/缺少 source_id/)
  })

  it('rejects duplicate logical resources', () => {
    const duplicate = pack()
    duplicate.assets.push({ ...entry })
    expect(() => parseWebAssetPack(duplicate)).toThrow(/重复资源/)
  })

  it('rejects URLs that can escape the pack directory', () => {
    const unsafe = pack()
    unsafe.assets[0] = { ...entry, url: '../pattern.dds' }
    expect(() => parseWebAssetPack(unsafe)).toThrow(/url 不合法/)
  })

  it('requires exactly one surface mask', () => {
    const missing = pack()
    missing.assets = [entry]
    expect(() => parseWebAssetPack(missing)).toThrow(/一个 surface_mask/)
  })

  it('binds a compact fit index to eligible registered resources', () => {
    const indexed = pack() as ReturnType<typeof pack> & { fit_index: object, inventory: object }
    indexed.fit_index = {
      schema: 'ck3-coa-fit-index-v1', format: 'RGBA8', resolution: 16,
      asset_indices: [0], url: `assets/${'d'.repeat(64)}.rgba`,
      asset_bytes: 16 * 16 * 4, asset_sha256: 'D'.repeat(64),
    }
    indexed.inventory = {
      complete_raw_tree: true, source_dds_total: 2,
      registered_patterns: 1, registered_colored_emblems: 0,
      auxiliary_colored_emblems: 0, textured_emblems: 0, surface_masks: 1,
      fit_eligible_registered: 1,
    }
    const parsed = parseWebAssetPack(indexed)
    expect(parsed.fit_index?.asset_indices).toEqual([0])
    expect(parsed.inventory?.complete_raw_tree).toBe(true)
  })

  it('rejects fit-index references to render-only resources', () => {
    const indexed = pack() as ReturnType<typeof pack> & { fit_index: object }
    indexed.fit_index = {
      schema: 'ck3-coa-fit-index-v1', format: 'RGBA8', resolution: 16,
      asset_indices: [1], url: `assets/${'d'.repeat(64)}.rgba`,
      asset_bytes: 16 * 16 * 4, asset_sha256: 'D'.repeat(64),
    }
    expect(() => parseWebAssetPack(indexed)).toThrow(/不可拟合资源/)
  })

  it('loads a hash-bound v2 shape-feature sidecar', async () => {
    const resolution = 8
    const rgba = new Uint8Array(resolution * resolution * 4).fill(127)
    const recordBytes = FIT_SHAPE_SCALAR_FIELDS.length * 8
      + FIT_SHAPE_DESCRIPTOR_SIZE * FIT_SHAPE_DESCRIPTOR_SIZE * 4
    const featureBytes = new Uint8Array(32 + recordBytes)
    featureBytes.set(new TextEncoder().encode('CK3FIT2\0'), 0)
    const view = new DataView(featureBytes.buffer)
    ;[2, 1, resolution, FIT_SHAPE_DESCRIPTOR_SIZE, FIT_SHAPE_SCALAR_FIELDS.length, recordBytes]
      .forEach((value, index) => view.setUint32(8 + index * 4, value, true))
    const scalars = [0, 0, 1, 1, 0.5, 0.5, 1, 1, 0.5, 0.1, 0.2, 0.3, 0.4]
    scalars.forEach((value, index) => view.setFloat64(32 + index * 8, value, true))
    const descriptorOffset = 32 + FIT_SHAPE_SCALAR_FIELDS.length * 8
    for (let index = 0; index < FIT_SHAPE_DESCRIPTOR_SIZE ** 2; index += 1) {
      view.setFloat32(descriptorOffset + index * 4, 0.25, true)
    }
    const digest = async (bytes: Uint8Array) => Array.from(
      new Uint8Array(await crypto.subtle.digest('SHA-256', Uint8Array.from(bytes).buffer)),
      (byte) => byte.toString(16).padStart(2, '0'),
    ).join('').toUpperCase()
    const rgbaSha = await digest(rgba)
    const featureSha = await digest(featureBytes)
    const indexed = pack() as ReturnType<typeof pack> & { fit_index: object }
    indexed.fit_index = {
      schema: 'ck3-coa-fit-index-v2', format: 'RGBA8', resolution,
      asset_indices: [0], url: `assets/${rgbaSha.toLowerCase()}.rgba`,
      asset_bytes: rgba.byteLength, asset_sha256: rgbaSha,
      features: {
        schema: 'ck3-coa-shape-features-v1',
        format: 'F64LE_SCALARS_F32LE_DESCRIPTOR',
        scalar_fields: [...FIT_SHAPE_SCALAR_FIELDS],
        descriptor_size: FIT_SHAPE_DESCRIPTOR_SIZE,
        header_bytes: 32,
        record_bytes: recordBytes,
        url: `assets/${featureSha.toLowerCase()}.fit`,
        asset_bytes: featureBytes.byteLength,
        asset_sha256: featureSha,
      },
    }
    const parsed = parseWebAssetPack(indexed)
    const fetcher = (async (input: string | URL | Request) => {
      const url = String(input)
      return new Response(url.endsWith('.fit') ? featureBytes : rgba)
    }) as typeof fetch
    const loaded = await readWebFitIndex({
      pack: parsed,
      manifestUrl: 'https://example.test/pack/manifest.json',
      manifestSha256: 'E'.repeat(64),
    }, fetcher)

    expect(loaded).toHaveLength(1)
    expect(loaded[0].shapeFeatures?.contentBounds).toEqual([0, 0, 1, 1])
    expect(loaded[0].shapeFeatures?.channelEnergy[2]).toBeCloseTo(0.3)
    expect(loaded[0].shapeFeatures?.contourEnergy).toBeCloseTo(0.4)
    expect(loaded[0].shapeFeatures?.descriptor).toHaveLength(FIT_SHAPE_DESCRIPTOR_SIZE ** 2)
    expect(loaded[0].shapeFeatures?.descriptor[0]).toBeCloseTo(0.25)
  })

  it('rejects a v2 feature sidecar with a mismatched scalar contract', () => {
    const indexed = pack() as ReturnType<typeof pack> & { fit_index: object }
    indexed.fit_index = {
      schema: 'ck3-coa-fit-index-v2', format: 'RGBA8', resolution: 16,
      asset_indices: [0], url: `assets/${'d'.repeat(64)}.rgba`,
      asset_bytes: 16 * 16 * 4, asset_sha256: 'D'.repeat(64),
      features: {
        schema: 'ck3-coa-shape-features-v1',
        format: 'F64LE_SCALARS_F32LE_DESCRIPTOR',
        scalar_fields: ['wrong'], descriptor_size: FIT_SHAPE_DESCRIPTOR_SIZE,
        header_bytes: 32, record_bytes: 1400,
        url: `assets/${'e'.repeat(64)}.fit`, asset_bytes: 1432, asset_sha256: 'E'.repeat(64),
      },
    }
    expect(() => parseWebAssetPack(indexed)).toThrow(/scalar_fields/)
  })

  it('loads a browser-selected directory without network access', async () => {
    const localPack = pack()
    const parsed = parseWebAssetPack(localPack)
    localPack.vfs_receipt.winner_set_sha256 = await calculateWebAssetWinnerSetSha256(parsed)
    const withPath = (file: File, path: string) => {
      Object.defineProperty(file, 'webkitRelativePath', { value: path })
      return file
    }
    const files = [
      withPath(new File([JSON.stringify(localPack)], 'manifest.json'), 'custom/manifest.json'),
      withPath(new File([new Uint8Array(128)], entry.url), `custom/${entry.url}`),
      withPath(
        new File([new Uint8Array(128)], localPack.assets[1].url),
        `custom/${localPack.assets[1].url}`,
      ),
    ]

    const loaded = await loadWebAssetPackFiles(files)

    expect(loaded.pack.pack_id).toBe('ck3-1.19.0.6-alpha')
    expect(loaded.localFiles?.get(entry.url)?.size).toBe(128)
    expect(loaded.manifestUrl).toMatch(/^https:\/\/local-pack\.invalid\/[0-9A-F]{64}\/manifest\.json$/)
  })

  it('rejects an incomplete browser-selected directory', async () => {
    const incompletePack = pack()
    incompletePack.vfs_receipt.winner_set_sha256 = await calculateWebAssetWinnerSetSha256(
      parseWebAssetPack(incompletePack),
    )
    const manifest = new File([JSON.stringify(incompletePack)], 'manifest.json')
    await expect(loadWebAssetPackFiles([
      manifest,
      new File([new Uint8Array(128)], entry.url),
    ])).rejects.toThrow(/缺少/)
  })
})
