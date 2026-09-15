import { decodeDds, type DecodedDds } from './dds'
import type { NamedColorMap } from './renderer'

export type WebAssetKind = 'pattern' | 'colored_emblem' | 'surface_mask'

export interface WebAssetPackEntry {
  kind: WebAssetKind
  name: string
  colors: number
  visible: boolean
  category: string | null
  url: string
  asset_bytes: number
  asset_sha256: string
  dds: {
    width: number
    height: number
    format: 'DXT1' | 'DXT5' | 'BGRA8'
  }
}

export interface WebAssetPack {
  schema: 'ck3-coa-web-asset-pack-v1'
  schema_version: 1
  pack_id: string
  ck3_build: string
  source_manifest_sha256: string
  named_colors: NamedColorMap
  assets: WebAssetPackEntry[]
}

export interface LoadedWebAssetPack {
  pack: WebAssetPack
  manifestUrl: string
  manifestSha256: string
}

const SHA256 = /^[0-9A-F]{64}$/
const SAFE_NAME = /^[\x20-\x7e]{1,128}$/
const SAFE_ASSET_URL = /^assets\/[0-9a-f]{64}\.dds$/
const MAX_ASSETS = 4096
const MAX_ASSET_BYTES = 16 * 1024 * 1024

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} 必须是 object`)
  }
  return value as Record<string, unknown>
}

function integer(value: unknown, label: string, minimum: number, maximum: number): number {
  if (!Number.isSafeInteger(value) || (value as number) < minimum || (value as number) > maximum) {
    throw new Error(`${label} 超出允许范围`)
  }
  return value as number
}

function text(value: unknown, label: string, pattern = SAFE_NAME): string {
  if (typeof value !== 'string' || !pattern.test(value)) throw new Error(`${label} 不合法`)
  return value
}

function parseEntry(value: unknown, index: number): WebAssetPackEntry {
  const item = record(value, `assets[${index}]`)
  if (!['pattern', 'colored_emblem', 'surface_mask'].includes(String(item.kind))) {
    throw new Error(`assets[${index}].kind 不支持`)
  }
  const dds = record(item.dds, `assets[${index}].dds`)
  if (!['DXT1', 'DXT5', 'BGRA8'].includes(String(dds.format))) {
    throw new Error(`assets[${index}].dds.format 不支持`)
  }
  if (typeof item.visible !== 'boolean') throw new Error(`assets[${index}].visible 必须是 boolean`)
  if (item.category !== null && typeof item.category !== 'string') {
    throw new Error(`assets[${index}].category 必须是 string 或 null`)
  }
  return {
    kind: item.kind as WebAssetKind,
    name: text(item.name, `assets[${index}].name`),
    colors: integer(item.colors, `assets[${index}].colors`, 0, 3),
    visible: item.visible,
    category: item.category as string | null,
    url: text(item.url, `assets[${index}].url`, SAFE_ASSET_URL),
    asset_bytes: integer(item.asset_bytes, `assets[${index}].asset_bytes`, 128, MAX_ASSET_BYTES),
    asset_sha256: text(item.asset_sha256, `assets[${index}].asset_sha256`, SHA256),
    dds: {
      width: integer(dds.width, `assets[${index}].dds.width`, 1, 4096),
      height: integer(dds.height, `assets[${index}].dds.height`, 1, 4096),
      format: dds.format as 'DXT1' | 'DXT5' | 'BGRA8',
    },
  }
}

export function parseWebAssetPack(value: unknown): WebAssetPack {
  const source = record(value, 'asset pack')
  if (source.schema !== 'ck3-coa-web-asset-pack-v1' || source.schema_version !== 1) {
    throw new Error('asset pack schema/version 不支持')
  }
  if (!Array.isArray(source.assets) || source.assets.length < 1 || source.assets.length > MAX_ASSETS) {
    throw new Error(`asset pack assets 数量必须在 1..${MAX_ASSETS}`)
  }
  const colors = record(source.named_colors, 'named_colors')
  const namedColors: NamedColorMap = {}
  for (const [name, components] of Object.entries(colors)) {
    if (!SAFE_NAME.test(name) || !Array.isArray(components) || components.length !== 3) {
      throw new Error(`named_colors.${name} 不合法`)
    }
    const parsed = components.map((component) => {
      if (typeof component !== 'number' || !Number.isFinite(component) || component < 0 || component > 1) {
        throw new Error(`named_colors.${name} 分量超出 0..1`)
      }
      return component
    })
    namedColors[name] = parsed as [number, number, number]
  }
  const assets = source.assets.map(parseEntry)
  const keys = new Set<string>()
  let surfaceMasks = 0
  for (const entry of assets) {
    const key = `${entry.kind}\0${entry.name}`
    if (keys.has(key)) throw new Error(`asset pack 存在重复资源：${entry.kind}/${entry.name}`)
    keys.add(key)
    if (entry.kind === 'surface_mask') surfaceMasks += 1
  }
  if (surfaceMasks !== 1) throw new Error('asset pack 必须包含且只包含一个 surface_mask')
  return {
    schema: 'ck3-coa-web-asset-pack-v1',
    schema_version: 1,
    pack_id: text(source.pack_id, 'pack_id'),
    ck3_build: text(source.ck3_build, 'ck3_build'),
    source_manifest_sha256: text(source.source_manifest_sha256, 'source_manifest_sha256', SHA256),
    named_colors: namedColors,
    assets,
  }
}

async function sha256Hex(data: ArrayBuffer | Uint8Array): Promise<string> {
  const bytes = Uint8Array.from(data instanceof Uint8Array ? data : new Uint8Array(data))
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0'))
    .join('').toUpperCase()
}

export async function loadWebAssetPack(
  manifestUrl: string,
  fetcher: typeof fetch = fetch,
): Promise<LoadedWebAssetPack> {
  const response = await fetcher(manifestUrl, { cache: 'no-cache' })
  if (!response.ok) throw new Error(`asset pack manifest HTTP ${response.status}`)
  const bytes = new Uint8Array(await response.arrayBuffer())
  if (bytes.byteLength < 2 || bytes.byteLength > 4 * 1024 * 1024) {
    throw new Error('asset pack manifest 大小超出 2 B..4 MiB')
  }
  let parsed: unknown
  try {
    parsed = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes))
  } catch (error) {
    throw new Error(`asset pack manifest 不是合法 UTF-8 JSON：${String(error)}`)
  }
  return {
    pack: parseWebAssetPack(parsed),
    manifestUrl: new URL(manifestUrl, window.location.href).href,
    manifestSha256: await sha256Hex(bytes),
  }
}

export async function readWebAsset(
  loaded: LoadedWebAssetPack,
  entry: WebAssetPackEntry,
  fetcher: typeof fetch = fetch,
): Promise<DecodedDds> {
  if (!loaded.pack.assets.includes(entry)) throw new Error('asset entry 不属于当前 pack')
  const assetUrl = new URL(entry.url, loaded.manifestUrl)
  const manifestDirectory = new URL('.', loaded.manifestUrl)
  if (!assetUrl.href.startsWith(manifestDirectory.href)) throw new Error('asset URL 逃逸 manifest 目录')
  const response = await fetcher(assetUrl.href, { cache: 'force-cache' })
  if (!response.ok) throw new Error(`asset pack DDS HTTP ${response.status}`)
  const bytes = new Uint8Array(await response.arrayBuffer())
  if (bytes.byteLength !== entry.asset_bytes) throw new Error(`${entry.name} DDS 字节数不匹配`)
  if (await sha256Hex(bytes) !== entry.asset_sha256) throw new Error(`${entry.name} DDS SHA-256 不匹配`)
  const decoded = decodeDds(bytes)
  if (
    decoded.width !== entry.dds.width
    || decoded.height !== entry.dds.height
    || decoded.fourCC !== entry.dds.format
  ) throw new Error(`${entry.name} DDS 元数据不匹配`)
  return decoded
}
