import { describe, expect, it } from 'vitest'
import { loadWebAssetPackFiles, parseWebAssetPack } from './assetPack'

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
})

describe('web asset pack contract', () => {
  it('accepts a bounded content-addressed pack', () => {
    const parsed = parseWebAssetPack(pack())
    expect(parsed.ck3_build).toBe('1.19.0.6')
    expect(parsed.assets).toHaveLength(2)
    expect(parsed.named_colors.red).toEqual([0.8, 0.1, 0.1])
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

  it('loads a browser-selected directory without network access', async () => {
    const localPack = pack()
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
    const manifest = new File([JSON.stringify(pack())], 'manifest.json')
    await expect(loadWebAssetPackFiles([
      manifest,
      new File([new Uint8Array(128)], entry.url),
    ])).rejects.toThrow(/缺少/)
  })
})
