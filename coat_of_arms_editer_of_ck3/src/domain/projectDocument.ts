import { coatOfArmsDocumentStats, type CoatOfArmsDocumentStats } from './documentStats'
import { serializeCoatOfArms } from './serializer'
import type { CoatOfArms, CoatOfArmsInstance, ColoredEmblem, TexturedEmblem } from './types'

export const COAT_OF_ARMS_PROJECT_SCHEMA = 'ck3-coa-browser-project-v1'
export const COAT_OF_ARMS_PROJECT_SCHEMA_VERSION = 1

export interface CoatOfArmsProjectAssetPack {
  packId: string
  manifestSha256: string
  ck3Build: string
}

export interface CoatOfArmsProjectDocument {
  schema: typeof COAT_OF_ARMS_PROJECT_SCHEMA
  schemaVersion: typeof COAT_OF_ARMS_PROJECT_SCHEMA_VERSION
  revision: number
  savedAt: string
  selectedEmblem: number
  assetPack?: CoatOfArmsProjectAssetPack
  coatOfArms: CoatOfArms
  ck3Source: {
    sha256: string
    stats: CoatOfArmsDocumentStats
  }
}

const isRecord = (value: unknown): value is Record<string, unknown> => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
)

function expectRecord(value: unknown, path: string): Record<string, unknown> {
  if (!isRecord(value)) throw new Error(`${path} 必须是对象`)
  return value
}

function expectString(value: unknown, path: string): string {
  if (typeof value !== 'string') throw new Error(`${path} 必须是字符串`)
  return value
}

function expectFiniteNumber(value: unknown, path: string): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`${path} 必须是有限数值`)
  return value
}

function expectNonNegativeSafeInteger(value: unknown, path: string): number {
  if (!Number.isSafeInteger(value) || (value as number) < 0) throw new Error(`${path} 必须是非负安全整数`)
  return value as number
}

function expectTuple2(value: unknown, path: string): [number, number] {
  if (!Array.isArray(value) || value.length !== 2) throw new Error(`${path} 必须恰有两个数值`)
  return [expectFiniteNumber(value[0], `${path}[0]`), expectFiniteNumber(value[1], `${path}[1]`)]
}

function expectStringTuple3(value: unknown, path: string): [string, string, string] {
  if (!Array.isArray(value) || value.length !== 3) throw new Error(`${path} 必须恰有三个字符串`)
  return [
    expectString(value[0], `${path}[0]`),
    expectString(value[1], `${path}[1]`),
    expectString(value[2], `${path}[2]`),
  ]
}

function parseInstance(value: unknown, path: string): CoatOfArmsInstance {
  const source = expectRecord(value, path)
  return {
    position: expectTuple2(source.position, `${path}.position`),
    scale: expectTuple2(source.scale, `${path}.scale`),
    rotation: expectFiniteNumber(source.rotation, `${path}.rotation`),
    depth: expectFiniteNumber(source.depth, `${path}.depth`),
  }
}

function parseColoredEmblem(value: unknown, path: string): ColoredEmblem {
  const source = expectRecord(value, path)
  if (!Array.isArray(source.mask)) throw new Error(`${path}.mask 必须是数组`)
  if (!Array.isArray(source.instances)) throw new Error(`${path}.instances 必须是数组`)
  return {
    texture: expectString(source.texture, `${path}.texture`),
    colors: expectStringTuple3(source.colors, `${path}.colors`),
    mask: source.mask.map((item, index) => expectFiniteNumber(item, `${path}.mask[${index}]`)),
    instances: source.instances.map((item, index) => parseInstance(item, `${path}.instances[${index}]`)),
  }
}

function parseTexturedEmblem(value: unknown, path: string): TexturedEmblem {
  const source = expectRecord(value, path)
  return { texture: expectString(source.texture, `${path}.texture`) }
}

function parseCoatOfArmsModel(value: unknown): CoatOfArms {
  const source = expectRecord(value, 'coatOfArms')
  if (!Array.isArray(source.coloredEmblems)) throw new Error('coatOfArms.coloredEmblems 必须是数组')
  if (!Array.isArray(source.texturedEmblems)) throw new Error('coatOfArms.texturedEmblems 必须是数组')
  return {
    outerKey: expectString(source.outerKey, 'coatOfArms.outerKey'),
    parent: expectString(source.parent, 'coatOfArms.parent'),
    pattern: expectString(source.pattern, 'coatOfArms.pattern'),
    colors: expectStringTuple3(source.colors, 'coatOfArms.colors'),
    coloredEmblems: source.coloredEmblems.map((item, index) => (
      parseColoredEmblem(item, `coatOfArms.coloredEmblems[${index}]`)
    )),
    texturedEmblems: source.texturedEmblems.map((item, index) => (
      parseTexturedEmblem(item, `coatOfArms.texturedEmblems[${index}]`)
    )),
  }
}

async function sha256Utf8(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('').toUpperCase()
}

export async function createCoatOfArmsProject(
  coatOfArms: CoatOfArms,
  options: {
    revision?: number
    savedAt?: string
    selectedEmblem?: number
    assetPack?: CoatOfArmsProjectAssetPack
  } = {},
): Promise<CoatOfArmsProjectDocument> {
  const cloned = parseCoatOfArmsModel(coatOfArms)
  const source = serializeCoatOfArms(cloned)
  return {
    schema: COAT_OF_ARMS_PROJECT_SCHEMA,
    schemaVersion: COAT_OF_ARMS_PROJECT_SCHEMA_VERSION,
    revision: options.revision ?? 1,
    savedAt: options.savedAt ?? new Date().toISOString(),
    selectedEmblem: Math.min(
      Math.max(0, options.selectedEmblem ?? 0),
      Math.max(0, cloned.coloredEmblems.length - 1),
    ),
    ...(options.assetPack ? { assetPack: { ...options.assetPack } } : {}),
    coatOfArms: cloned,
    ck3Source: {
      sha256: await sha256Utf8(source),
      stats: coatOfArmsDocumentStats(cloned, source),
    },
  }
}

export function serializeCoatOfArmsProject(project: CoatOfArmsProjectDocument): string {
  return `${JSON.stringify(project, null, 2)}\n`
}

function sameStats(left: CoatOfArmsDocumentStats, right: CoatOfArmsDocumentStats): boolean {
  return Object.keys(left).every((key) => (
    left[key as keyof CoatOfArmsDocumentStats] === right[key as keyof CoatOfArmsDocumentStats]
  ))
}

export async function parseCoatOfArmsProject(text: string): Promise<CoatOfArmsProjectDocument> {
  let raw: unknown
  try {
    raw = JSON.parse(text)
  } catch (error) {
    throw new Error(`项目 JSON 无效：${error instanceof Error ? error.message : String(error)}`)
  }
  const root = expectRecord(raw, 'project')
  if (root.schema !== COAT_OF_ARMS_PROJECT_SCHEMA) throw new Error(`不支持的项目 schema：${String(root.schema)}`)
  if (root.schemaVersion !== COAT_OF_ARMS_PROJECT_SCHEMA_VERSION) {
    throw new Error(`不支持的项目 schemaVersion：${String(root.schemaVersion)}`)
  }
  const revision = expectNonNegativeSafeInteger(root.revision, 'project.revision')
  const selectedEmblem = expectNonNegativeSafeInteger(root.selectedEmblem, 'project.selectedEmblem')
  const savedAt = expectString(root.savedAt, 'project.savedAt')
  if (Number.isNaN(Date.parse(savedAt))) throw new Error('project.savedAt 不是有效 ISO 时间')
  const coatOfArms = parseCoatOfArmsModel(root.coatOfArms)
  const source = serializeCoatOfArms(coatOfArms)
  const actualStats = coatOfArmsDocumentStats(coatOfArms, source)
  const sourceReceipt = expectRecord(root.ck3Source, 'project.ck3Source')
  const expectedHash = expectString(sourceReceipt.sha256, 'project.ck3Source.sha256').toUpperCase()
  const actualHash = await sha256Utf8(source)
  if (actualHash !== expectedHash) throw new Error('项目 CK3 源码 SHA-256 与模型不一致')
  const expectedStats = expectRecord(sourceReceipt.stats, 'project.ck3Source.stats')
  const parsedStats = Object.fromEntries(Object.keys(actualStats).map((key) => [
    key,
    expectNonNegativeSafeInteger(expectedStats[key], `project.ck3Source.stats.${key}`),
  ])) as unknown as CoatOfArmsDocumentStats
  if (!sameStats(actualStats, parsedStats)) throw new Error('项目 CK3 源码计数与模型不一致')
  if (selectedEmblem >= Math.max(1, coatOfArms.coloredEmblems.length)) {
    throw new Error('project.selectedEmblem 超出图层范围')
  }
  let assetPack: CoatOfArmsProjectAssetPack | undefined
  if (root.assetPack !== undefined) {
    const value = expectRecord(root.assetPack, 'project.assetPack')
    assetPack = {
      packId: expectString(value.packId, 'project.assetPack.packId'),
      manifestSha256: expectString(value.manifestSha256, 'project.assetPack.manifestSha256'),
      ck3Build: expectString(value.ck3Build, 'project.assetPack.ck3Build'),
    }
  }
  return {
    schema: COAT_OF_ARMS_PROJECT_SCHEMA,
    schemaVersion: COAT_OF_ARMS_PROJECT_SCHEMA_VERSION,
    revision,
    savedAt,
    selectedEmblem,
    ...(assetPack ? { assetPack } : {}),
    coatOfArms,
    ck3Source: { sha256: actualHash, stats: actualStats },
  }
}
