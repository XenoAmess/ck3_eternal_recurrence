import { decodeDds, type DecodedDds } from './dds'
import type { NamedColorMap } from './renderer'

export type WebAssetKind =
  | 'pattern'
  | 'colored_emblem'
  | 'auxiliary_colored_emblem'
  | 'textured_emblem'
  | 'surface_mask'

export type WebAssetRegistration = 'designer_manifest' | 'unregistered_file' | 'render_support'

export interface WebAssetPackEntry {
  kind: WebAssetKind
  name: string
  colors: number
  visible: boolean
  category: string | null
  url: string
  asset_bytes: number
  asset_sha256: string
  source_relative_path: string
  registration: WebAssetRegistration
  fit_eligible: boolean
  dds: {
    width: number
    height: number
    format: 'DXT1' | 'DXT5' | 'BGRA8'
  }
}

export interface WebFitIndex {
  schema: 'ck3-coa-fit-index-v1'
  format: 'RGBA8'
  resolution: number
  asset_indices: number[]
  url: string
  asset_bytes: number
  asset_sha256: string
}

export interface WebAssetInventory {
  complete_raw_tree: boolean
  source_dds_total: number
  registered_patterns: number
  registered_colored_emblems: number
  auxiliary_colored_emblems: number
  textured_emblems: number
  surface_masks: number
  fit_eligible_registered: number
}

export interface WebAssetPack {
  schema: 'ck3-coa-web-asset-pack-v1'
  schema_version: 1
  pack_id: string
  ck3_build: string
  source_manifest_sha256: string
  named_colors: NamedColorMap
  assets: WebAssetPackEntry[]
  fit_index?: WebFitIndex
  inventory?: WebAssetInventory
}

export interface LoadedWebAssetPack {
  pack: WebAssetPack
  manifestUrl: string
  manifestSha256: string
  /** Browser-selected pack files, keyed relative to manifest.json. */
  localFiles?: ReadonlyMap<string, File>
}

const SHA256 = /^[0-9A-F]{64}$/
// The exact manifest contains long names and one U+FFFD name inherited from the
// source bytes; reject path/control characters without rewriting engine identity.
const SAFE_NAME = /^[^\u0000-\u001f\u007f/\\]{1,512}$/u
const SAFE_ASSET_URL = /^assets\/[0-9a-f]{64}\.dds$/
const SAFE_INDEX_URL = /^assets\/[0-9a-f]{64}\.rgba$/
const SAFE_SOURCE_PATH = /^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))[^\0]{1,512}$/
const MAX_ASSETS = 4096
const MAX_ASSET_BYTES = 16 * 1024 * 1024
const MAX_SELECTED_PACK_FILES = MAX_ASSETS + 8

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
  if (![
    'pattern', 'colored_emblem', 'auxiliary_colored_emblem', 'textured_emblem', 'surface_mask',
  ].includes(String(item.kind))) {
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
  const kind = item.kind as WebAssetKind
  const defaultRegistration: WebAssetRegistration = ['pattern', 'colored_emblem'].includes(kind)
    ? 'designer_manifest'
    : 'render_support'
  const registration = item.registration === undefined ? defaultRegistration : String(item.registration)
  if (!['designer_manifest', 'unregistered_file', 'render_support'].includes(registration)) {
    throw new Error(`assets[${index}].registration 不支持`)
  }
  const fitEligible = item.fit_eligible === undefined
    ? ['pattern', 'colored_emblem'].includes(kind)
    : item.fit_eligible
  if (typeof fitEligible !== 'boolean') throw new Error(`assets[${index}].fit_eligible 必须是 boolean`)
  return {
    kind,
    name: text(item.name, `assets[${index}].name`),
    colors: integer(item.colors, `assets[${index}].colors`, 0, 3),
    visible: item.visible,
    category: item.category as string | null,
    url: text(item.url, `assets[${index}].url`, SAFE_ASSET_URL),
    asset_bytes: integer(item.asset_bytes, `assets[${index}].asset_bytes`, 128, MAX_ASSET_BYTES),
    asset_sha256: text(item.asset_sha256, `assets[${index}].asset_sha256`, SHA256),
    source_relative_path: text(
      item.source_relative_path ?? `legacy/${String(item.name)}`,
      `assets[${index}].source_relative_path`,
      SAFE_SOURCE_PATH,
    ),
    registration: registration as WebAssetRegistration,
    fit_eligible: fitEligible,
    dds: {
      width: integer(dds.width, `assets[${index}].dds.width`, 1, 4096),
      height: integer(dds.height, `assets[${index}].dds.height`, 1, 4096),
      format: dds.format as 'DXT1' | 'DXT5' | 'BGRA8',
    },
  }
}

function parseFitIndex(value: unknown, assets: WebAssetPackEntry[]): WebFitIndex {
  const item = record(value, 'fit_index')
  if (item.schema !== 'ck3-coa-fit-index-v1' || item.format !== 'RGBA8') {
    throw new Error('fit_index schema/format 不支持')
  }
  if (!Array.isArray(item.asset_indices) || item.asset_indices.length < 1 || item.asset_indices.length > MAX_ASSETS) {
    throw new Error('fit_index.asset_indices 数量不合法')
  }
  const indices = item.asset_indices.map((value, index) => integer(
    value, `fit_index.asset_indices[${index}]`, 0, assets.length - 1,
  ))
  if (new Set(indices).size !== indices.length) throw new Error('fit_index.asset_indices 不得重复')
  for (const index of indices) {
    if (!assets[index].fit_eligible || !['pattern', 'colored_emblem'].includes(assets[index].kind)) {
      throw new Error(`fit_index 引用了不可拟合资源 assets[${index}]`)
    }
  }
  const resolution = integer(item.resolution, 'fit_index.resolution', 8, 128)
  const expectedBytes = indices.length * resolution * resolution * 4
  return {
    schema: 'ck3-coa-fit-index-v1',
    format: 'RGBA8',
    resolution,
    asset_indices: indices,
    url: text(item.url, 'fit_index.url', SAFE_INDEX_URL),
    asset_bytes: integer(item.asset_bytes, 'fit_index.asset_bytes', expectedBytes, expectedBytes),
    asset_sha256: text(item.asset_sha256, 'fit_index.asset_sha256', SHA256),
  }
}

function parseInventory(value: unknown): WebAssetInventory {
  const item = record(value, 'inventory')
  if (typeof item.complete_raw_tree !== 'boolean') throw new Error('inventory.complete_raw_tree 必须是 boolean')
  const count = (name: keyof Omit<WebAssetInventory, 'complete_raw_tree'>) =>
    integer(item[name], `inventory.${name}`, 0, MAX_ASSETS)
  return {
    complete_raw_tree: item.complete_raw_tree,
    source_dds_total: count('source_dds_total'),
    registered_patterns: count('registered_patterns'),
    registered_colored_emblems: count('registered_colored_emblems'),
    auxiliary_colored_emblems: count('auxiliary_colored_emblems'),
    textured_emblems: count('textured_emblems'),
    surface_masks: count('surface_masks'),
    fit_eligible_registered: count('fit_eligible_registered'),
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
  const fitIndex = source.fit_index === undefined ? undefined : parseFitIndex(source.fit_index, assets)
  const inventory = source.inventory === undefined ? undefined : parseInventory(source.inventory)
  if (inventory) {
    const observed = {
      registered_patterns: assets.filter((item) => item.kind === 'pattern' && item.registration === 'designer_manifest').length,
      registered_colored_emblems: assets.filter((item) => item.kind === 'colored_emblem' && item.registration === 'designer_manifest').length,
      auxiliary_colored_emblems: assets.filter((item) => item.kind === 'auxiliary_colored_emblem').length,
      textured_emblems: assets.filter((item) => item.kind === 'textured_emblem').length,
      surface_masks: surfaceMasks,
    }
    for (const [name, count] of Object.entries(observed)) {
      if (inventory[name as keyof typeof observed] !== count) throw new Error(`inventory.${name} 与 assets 不一致`)
    }
    const fitEligibleRegistered = assets.filter(
      (item) => item.registration === 'designer_manifest' && item.fit_eligible,
    ).length
    if (inventory.fit_eligible_registered !== fitEligibleRegistered) {
      throw new Error('inventory.fit_eligible_registered 与 assets 不一致')
    }
    if (inventory.complete_raw_tree && inventory.source_dds_total !== assets.length) {
      throw new Error('完整素材包的 source_dds_total 与 assets 数量不一致')
    }
  }
  return {
    schema: 'ck3-coa-web-asset-pack-v1',
    schema_version: 1,
    pack_id: text(source.pack_id, 'pack_id'),
    ck3_build: text(source.ck3_build, 'ck3_build'),
    source_manifest_sha256: text(source.source_manifest_sha256, 'source_manifest_sha256', SHA256),
    named_colors: namedColors,
    assets,
    fit_index: fitIndex,
    inventory,
  }
}

export interface WebFitTexture {
  entry: WebAssetPackEntry
  texture: DecodedDds
}

export async function readWebFitIndex(
  loaded: LoadedWebAssetPack,
  fetcher: typeof fetch = fetch,
): Promise<WebFitTexture[]> {
  const index = loaded.pack.fit_index
  if (!index) throw new Error('asset pack 没有完整搜索索引')
  const assetUrl = new URL(index.url, loaded.manifestUrl)
  const manifestDirectory = new URL('.', loaded.manifestUrl)
  if (!assetUrl.href.startsWith(manifestDirectory.href)) throw new Error('fit index URL 逃逸 manifest 目录')
  const localFile = loaded.localFiles?.get(index.url)
  const bytes = localFile
    ? new Uint8Array(await localFile.arrayBuffer())
    : await (async () => {
        const response = await fetcher(assetUrl.href, { cache: 'force-cache' })
        if (!response.ok) throw new Error(`asset pack fit index HTTP ${response.status}`)
        return new Uint8Array(await response.arrayBuffer())
      })()
  if (bytes.byteLength !== index.asset_bytes) throw new Error('fit index 字节数不匹配')
  if (await sha256Hex(bytes) !== index.asset_sha256) throw new Error('fit index SHA-256 不匹配')
  const recordBytes = index.resolution * index.resolution * 4
  return index.asset_indices.map((assetIndex, recordIndex) => ({
    entry: loaded.pack.assets[assetIndex],
    texture: {
      width: index.resolution,
      height: index.resolution,
      fourCC: 'BGRA8',
      pixels: new Uint8ClampedArray(bytes.slice(recordIndex * recordBytes, (recordIndex + 1) * recordBytes)),
    },
  }))
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

/**
 * Loads a generated asset-pack directory selected by the user. Files stay local:
 * only an individual DDS (or the fit index) is read when the editor needs it.
 */
export async function loadWebAssetPackFiles(files: readonly File[]): Promise<LoadedWebAssetPack> {
  if (files.length < 2 || files.length > MAX_SELECTED_PACK_FILES) {
    throw new Error(`本地素材包文件数量必须在 2..${MAX_SELECTED_PACK_FILES}`)
  }
  const pathOf = (file: File) => {
    const relative = file.webkitRelativePath || file.name
    return relative.replaceAll('\\', '/').replace(/^\/+/, '')
  }
  const manifests = files.filter((file) => pathOf(file).split('/').at(-1) === 'manifest.json')
  if (manifests.length !== 1) throw new Error('本地素材包必须包含且只包含一个 manifest.json')
  const manifest = manifests[0]
  if (manifest.size < 2 || manifest.size > 4 * 1024 * 1024) {
    throw new Error('asset pack manifest 大小超出 2 B..4 MiB')
  }
  const manifestPath = pathOf(manifest)
  const slash = manifestPath.lastIndexOf('/')
  const root = slash < 0 ? '' : manifestPath.slice(0, slash + 1)
  const localFiles = new Map<string, File>()
  for (const file of files) {
    const path = pathOf(file)
    if (!path.startsWith(root)) throw new Error('本地素材包文件不在 manifest 目录内')
    const relative = path.slice(root.length)
    if (!relative || relative.startsWith('/') || relative.split('/').includes('..')) {
      throw new Error('本地素材包包含不安全相对路径')
    }
    if (localFiles.has(relative)) throw new Error(`本地素材包包含重复路径：${relative}`)
    localFiles.set(relative, file)
  }
  const manifestBytes = new Uint8Array(await manifest.arrayBuffer())
  let parsed: unknown
  try {
    parsed = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(manifestBytes))
  } catch (error) {
    throw new Error(`asset pack manifest 不是合法 UTF-8 JSON：${String(error)}`)
  }
  const pack = parseWebAssetPack(parsed)
  const required = [
    ...pack.assets.map((entry) => ({ path: entry.url, bytes: entry.asset_bytes })),
    ...(pack.fit_index ? [{ path: pack.fit_index.url, bytes: pack.fit_index.asset_bytes }] : []),
  ]
  for (const item of required) {
    const file = localFiles.get(item.path)
    if (!file) throw new Error(`本地素材包缺少 ${item.path}`)
    if (file.size !== item.bytes) throw new Error(`本地素材包 ${item.path} 字节数不匹配`)
  }
  const manifestSha256 = await sha256Hex(manifestBytes)
  return {
    pack,
    manifestUrl: `https://local-pack.invalid/${manifestSha256}/manifest.json`,
    manifestSha256,
    localFiles,
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
  const localFile = loaded.localFiles?.get(entry.url)
  const bytes = localFile
    ? new Uint8Array(await localFile.arrayBuffer())
    : await (async () => {
        const response = await fetcher(assetUrl.href, { cache: 'force-cache' })
        if (!response.ok) throw new Error(`asset pack DDS HTTP ${response.status}`)
        return new Uint8Array(await response.arrayBuffer())
      })()
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
