import { describe, expect, it } from 'vitest'
import { parseWebAssetPack } from './assetPack'

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
})
