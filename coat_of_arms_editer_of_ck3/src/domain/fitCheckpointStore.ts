import type { DecodedFitImage } from './imageInput'
import type { FitImage, ImageFitCheckpoint } from './imageFitter'
import { asBrowserStorageError, BrowserStorageError } from './browserStorage'

const DATABASE_NAME = 'ck3-coa-fit-checkpoint'
const DATABASE_VERSION = 1
const STORE_NAME = 'fit-state'
const CHECKPOINT_KEY = 'latest'
const SHA256 = /^[A-F0-9]{64}$/

export const PORTABLE_FIT_CHECKPOINT_SCHEMA = 'ck3-coa-portable-fit-checkpoint-v1'
export const PORTABLE_FIT_CHECKPOINT_MAX_BYTES = 24 * 1024 * 1024

export interface PersistedFitCheckpoint {
  schema: 'ck3-coa-persisted-fit-checkpoint-v1'
  savedAt: string
  input: {
    name: string
    image: FitImage
    pyramid: FitImage[]
    originalWidth: number
    originalHeight: number
    workingResolution: number
    mimeType: string
    bytes: number
    sha256: string
    previewUrl: string
  }
  assetPack: {
    packId: string
    manifestSha256: string
  }
  layerBudget: number
  checkpoint: ImageFitCheckpoint
}

interface PortableFitImage {
  width: number
  height: number
  pixelsBase64: string
}

interface PortableFitCheckpointEnvelope {
  schema: typeof PORTABLE_FIT_CHECKPOINT_SCHEMA
  payloadSha256: string
  payload: Omit<PersistedFitCheckpoint, 'input'> & {
    input: Omit<PersistedFitCheckpoint['input'], 'image' | 'pyramid'> & {
      image: PortableFitImage
      pyramid: PortableFitImage[]
    }
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function assertImage(value: unknown, label: string): asserts value is FitImage {
  if (!isObject(value)) throw new Error(`${label} 不是对象`)
  const { width, height, pixels } = value
  if (
    !Number.isSafeInteger(width) || !Number.isSafeInteger(height)
    || (width as number) < 1 || (height as number) < 1
    || (width as number) > 256 || (height as number) > 256
    || !(pixels instanceof Uint8ClampedArray)
    || pixels.length !== (width as number) * (height as number) * 4
  ) throw new Error(`${label} 的尺寸或 RGBA 数据无效`)
}

export function validatePersistedFitCheckpoint(value: unknown): PersistedFitCheckpoint {
  if (!isObject(value) || value.schema !== 'ck3-coa-persisted-fit-checkpoint-v1') {
    throw new Error('持久拟合 checkpoint 版本不兼容')
  }
  if (typeof value.savedAt !== 'string' || Number.isNaN(Date.parse(value.savedAt))) {
    throw new Error('持久拟合 checkpoint 的时间无效')
  }
  const input = value.input
  const assetPack = value.assetPack
  const checkpoint = value.checkpoint
  if (!isObject(input) || !isObject(assetPack) || !isObject(checkpoint)) {
    throw new Error('持久拟合 checkpoint 缺少输入、素材包或搜索状态')
  }
  assertImage(input.image, 'checkpoint input.image')
  if (!Array.isArray(input.pyramid) || input.pyramid.length < 1 || input.pyramid.length > 4) {
    throw new Error('持久拟合 checkpoint 的输入金字塔无效')
  }
  input.pyramid.forEach((image, index) => assertImage(image, `checkpoint input.pyramid[${index}]`))
  if (
    typeof input.name !== 'string' || input.name.length > 512
    || typeof input.mimeType !== 'string'
    || typeof input.previewUrl !== 'string' || !input.previewUrl.startsWith('data:image/')
    || input.previewUrl.length > 4 * 1024 * 1024
    || typeof input.sha256 !== 'string' || !SHA256.test(input.sha256)
    || !Number.isSafeInteger(input.originalWidth) || !Number.isSafeInteger(input.originalHeight)
    || (input.originalWidth as number) < 1 || (input.originalWidth as number) > 4096
    || (input.originalHeight as number) < 1 || (input.originalHeight as number) > 4096
    || !Number.isSafeInteger(input.workingResolution)
    || !Number.isSafeInteger(input.bytes) || (input.bytes as number) < 1 || (input.bytes as number) > 16 * 1024 * 1024
  ) throw new Error('持久拟合 checkpoint 的输入元数据无效')
  if (
    typeof assetPack.packId !== 'string' || !assetPack.packId
    || typeof assetPack.manifestSha256 !== 'string' || !SHA256.test(assetPack.manifestSha256)
    || !Number.isSafeInteger(value.layerBudget) || (value.layerBudget as number) < 1
  ) throw new Error('持久拟合 checkpoint 的素材包或预算元数据无效')
  if (
    checkpoint.contract !== 'ck3-coa-fit-checkpoint-v8'
    || checkpoint.algorithm !== 'ck3-coa-browser-fit-v13-epsilon-direct-multiscale'
  ) throw new Error('持久拟合 checkpoint 内的搜索状态版本不兼容')
  if (
    checkpoint.inputSha256 !== input.sha256
    || checkpoint.assetPackManifestSha256 !== assetPack.manifestSha256
    || checkpoint.layerBudget !== value.layerBudget
    || checkpoint.sourceWidth !== input.originalWidth
    || checkpoint.sourceHeight !== input.originalHeight
    || !Array.isArray(checkpoint.tiles)
    || typeof checkpoint.tileCount !== 'number'
    || typeof checkpoint.layerBudget !== 'number'
    || !Number.isSafeInteger(checkpoint.refinementCandidates)
    || (checkpoint.refinementCandidates as number) < 8
    || (checkpoint.refinementCandidates as number) > 128
    || !Number.isSafeInteger(checkpoint.beamWidth)
    || (checkpoint.beamWidth as number) < 1
    || (checkpoint.beamWidth as number) > 4
    || typeof checkpoint.nextTileIndex !== 'number'
    || checkpoint.tileCount !== checkpoint.tiles.length
    || checkpoint.tileCount > checkpoint.layerBudget
    || !Number.isSafeInteger(checkpoint.nextTileIndex)
    || checkpoint.nextTileIndex < 0
    || checkpoint.nextTileIndex > checkpoint.tileCount
  ) throw new Error('持久拟合 checkpoint 的身份、预算或搜索游标不一致')
  return value as unknown as PersistedFitCheckpoint
}

function cloneImage(image: FitImage): FitImage {
  return { width: image.width, height: image.height, pixels: new Uint8ClampedArray(image.pixels) }
}

function encodeBase64(bytes: Uint8ClampedArray): string {
  let binary = ''
  const chunkSize = 0x8000
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize))
  }
  return btoa(binary)
}

function portableImage(image: FitImage): PortableFitImage {
  return { width: image.width, height: image.height, pixelsBase64: encodeBase64(image.pixels) }
}

function decodePortableImage(value: unknown, label: string): FitImage {
  if (!isObject(value)) throw new Error(`${label} 不是对象`)
  const width = value.width
  const height = value.height
  const pixelsBase64 = value.pixelsBase64
  if (
    !Number.isSafeInteger(width) || !Number.isSafeInteger(height)
    || (width as number) < 1 || (height as number) < 1
    || (width as number) > 256 || (height as number) > 256
    || typeof pixelsBase64 !== 'string'
  ) throw new Error(`${label} 的尺寸或 RGBA 编码无效`)
  const expectedBytes = (width as number) * (height as number) * 4
  const expectedBase64Length = Math.ceil(expectedBytes / 3) * 4
  if (
    pixelsBase64.length !== expectedBase64Length
    || !/^[A-Za-z0-9+/]*={0,2}$/.test(pixelsBase64)
  ) throw new Error(`${label} 的 RGBA 编码长度无效`)
  let binary: string
  try {
    binary = atob(pixelsBase64)
  } catch {
    throw new Error(`${label} 的 RGBA Base64 无效`)
  }
  if (binary.length !== expectedBytes) throw new Error(`${label} 的 RGBA 数据长度无效`)
  const pixels = new Uint8ClampedArray(expectedBytes)
  for (let index = 0; index < binary.length; index += 1) pixels[index] = binary.charCodeAt(index)
  if (encodeBase64(pixels) !== pixelsBase64) throw new Error(`${label} 的 RGBA Base64 不是规范编码`)
  return { width: width as number, height: height as number, pixels }
}

async function sha256Utf8(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()
}

function portablePayload(record: PersistedFitCheckpoint): PortableFitCheckpointEnvelope['payload'] {
  return {
    ...record,
    input: {
      ...record.input,
      image: portableImage(record.input.image),
      pyramid: record.input.pyramid.map(portableImage),
    },
  }
}

export async function serializePortableFitCheckpoint(record: PersistedFitCheckpoint): Promise<string> {
  const validated = validatePersistedFitCheckpoint(record)
  const payload = portablePayload(validated)
  const payloadText = JSON.stringify(payload)
  const envelope: PortableFitCheckpointEnvelope = {
    schema: PORTABLE_FIT_CHECKPOINT_SCHEMA,
    payloadSha256: await sha256Utf8(payloadText),
    payload,
  }
  const result = `${JSON.stringify(envelope, null, 2)}\n`
  if (new TextEncoder().encode(result).length > PORTABLE_FIT_CHECKPOINT_MAX_BYTES) {
    throw new Error('便携拟合 checkpoint 超过 24 MiB 安全上限')
  }
  return result
}

export async function parsePortableFitCheckpoint(text: string): Promise<PersistedFitCheckpoint> {
  if (new TextEncoder().encode(text).length > PORTABLE_FIT_CHECKPOINT_MAX_BYTES) {
    throw new Error('便携拟合 checkpoint 超过 24 MiB 安全上限')
  }
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    throw new Error('便携拟合 checkpoint 不是合法 JSON')
  }
  if (!isObject(parsed) || parsed.schema !== PORTABLE_FIT_CHECKPOINT_SCHEMA) {
    throw new Error('便携拟合 checkpoint 版本不兼容')
  }
  if (typeof parsed.payloadSha256 !== 'string' || !SHA256.test(parsed.payloadSha256)) {
    throw new Error('便携拟合 checkpoint 缺少合法的 payload SHA-256')
  }
  const payload = parsed.payload
  if (!isObject(payload)) throw new Error('便携拟合 checkpoint 缺少 payload')
  const actualSha256 = await sha256Utf8(JSON.stringify(payload))
  if (actualSha256 !== parsed.payloadSha256) {
    throw new Error('便携拟合 checkpoint payload SHA-256 不一致')
  }
  const input = payload.input
  if (!isObject(input) || !Array.isArray(input.pyramid)) {
    throw new Error('便携拟合 checkpoint 缺少输入金字塔')
  }
  return validatePersistedFitCheckpoint({
    ...payload,
    input: {
      ...input,
      image: decodePortableImage(input.image, 'portable checkpoint input.image'),
      pyramid: input.pyramid.map((image, index) => (
        decodePortableImage(image, `portable checkpoint input.pyramid[${index}]`)
      )),
    },
  })
}

export function estimatePersistedFitCheckpointBytes(record: PersistedFitCheckpoint): number {
  const validated = validatePersistedFitCheckpoint(record)
  const pixelBytes = validated.input.image.pixels.byteLength
    + validated.input.pyramid.reduce((sum, image) => sum + image.pixels.byteLength, 0)
  const metadata = {
    ...validated,
    input: {
      ...validated.input,
      image: {
        width: validated.input.image.width,
        height: validated.input.image.height,
        pixelsBytes: validated.input.image.pixels.byteLength,
      },
      pyramid: validated.input.pyramid.map((image) => ({
        width: image.width,
        height: image.height,
        pixelsBytes: image.pixels.byteLength,
      })),
    },
  }
  return pixelBytes + new TextEncoder().encode(JSON.stringify(metadata)).length
}

export function createPersistedFitCheckpoint(
  checkpoint: ImageFitCheckpoint,
  input: DecodedFitImage,
  assetPack: PersistedFitCheckpoint['assetPack'],
  savedAt = new Date().toISOString(),
): PersistedFitCheckpoint {
  return validatePersistedFitCheckpoint({
    schema: 'ck3-coa-persisted-fit-checkpoint-v1',
    savedAt,
    input: {
      name: input.originalFile?.name ?? 'recovered-image',
      image: cloneImage(input.image),
      pyramid: input.pyramid.map(cloneImage),
      originalWidth: input.originalWidth,
      originalHeight: input.originalHeight,
      workingResolution: input.workingResolution,
      mimeType: input.mimeType,
      bytes: input.bytes,
      sha256: input.sha256,
      previewUrl: input.previewUrl,
    },
    assetPack: { ...assetPack },
    layerBudget: checkpoint.layerBudget,
    checkpoint,
  })
}

export function restorePersistedFitInput(record: PersistedFitCheckpoint): DecodedFitImage {
  const validated = validatePersistedFitCheckpoint(record)
  return {
    image: cloneImage(validated.input.image),
    pyramid: validated.input.pyramid.map(cloneImage),
    originalWidth: validated.input.originalWidth,
    originalHeight: validated.input.originalHeight,
    workingResolution: validated.input.workingResolution,
    mimeType: validated.input.mimeType,
    bytes: validated.input.bytes,
    sha256: validated.input.sha256,
    previewUrl: validated.input.previewUrl,
  }
}

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(asBrowserStorageError(
      request.error ?? new Error('IndexedDB 拟合 checkpoint 请求失败'),
      '请求',
    ))
  })
}

function openDatabase(): Promise<IDBDatabase> {
  if (!globalThis.indexedDB) {
    return Promise.reject(new BrowserStorageError('unavailable', '打开拟合 checkpoint IndexedDB'))
  }
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION)
    request.onupgradeneeded = () => {
      const database = request.result
      if (!database.objectStoreNames.contains(STORE_NAME)) database.createObjectStore(STORE_NAME)
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(asBrowserStorageError(
      request.error ?? new Error('无法打开拟合 checkpoint IndexedDB'),
      '打开拟合 checkpoint IndexedDB',
      'unavailable',
    ))
    request.onblocked = () => reject(new BrowserStorageError('blocked', '打开拟合 checkpoint IndexedDB'))
  })
}

async function withStore<T>(
  mode: IDBTransactionMode,
  operation: string,
  action: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const database = await openDatabase()
  try {
    const transaction = database.transaction(STORE_NAME, mode)
    const transactionResult = new Promise<void>((resolve, reject) => {
      transaction.oncomplete = () => resolve()
      transaction.onabort = () => reject(asBrowserStorageError(
        transaction.error ?? new DOMException('拟合 checkpoint IndexedDB 事务中止', 'AbortError'),
        operation,
        'aborted',
      ))
      transaction.onerror = () => reject(asBrowserStorageError(
        transaction.error ?? new Error('拟合 checkpoint IndexedDB 事务失败'),
        operation,
      ))
    })
    let request: IDBRequest<T>
    try {
      request = action(transaction.objectStore(STORE_NAME))
    } catch (error) {
      try { transaction.abort() } catch { /* The transaction may already be inactive. */ }
      await transactionResult.catch(() => undefined)
      throw error
    }
    const result = await requestResult(request).catch(async (error) => {
      try { transaction.abort() } catch { /* The request may already have aborted it. */ }
      await transactionResult.catch(() => undefined)
      throw error
    })
    await transactionResult
    return result
  } catch (error) {
    throw asBrowserStorageError(error, operation)
  } finally {
    database.close()
  }
}

export async function savePersistedFitCheckpoint(record: PersistedFitCheckpoint): Promise<void> {
  await withStore('readwrite', '写入拟合 checkpoint', (store) => (
    store.put(validatePersistedFitCheckpoint(record), CHECKPOINT_KEY)
  ))
}

export async function loadPersistedFitCheckpoint(): Promise<PersistedFitCheckpoint | null> {
  const value = await withStore('readonly', '读取拟合 checkpoint', (store) => store.get(CHECKPOINT_KEY))
  return value === undefined ? null : validatePersistedFitCheckpoint(value)
}

export async function clearPersistedFitCheckpoint(): Promise<void> {
  await withStore('readwrite', '删除拟合 checkpoint', (store) => store.delete(CHECKPOINT_KEY))
}
