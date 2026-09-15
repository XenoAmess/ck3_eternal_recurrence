import type { DecodedFitImage } from './imageInput'
import type { FitImage, ImageFitCheckpoint } from './imageFitter'

const DATABASE_NAME = 'ck3-coa-fit-checkpoint'
const DATABASE_VERSION = 1
const STORE_NAME = 'fit-state'
const CHECKPOINT_KEY = 'latest'
const SHA256 = /^[A-F0-9]{64}$/

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
    checkpoint.contract !== 'ck3-coa-fit-checkpoint-v1'
    || checkpoint.algorithm !== 'ck3-coa-browser-fit-v6-budget-exhaustive-edge'
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
    request.onerror = () => reject(request.error ?? new Error('IndexedDB 拟合 checkpoint 请求失败'))
  })
}

function openDatabase(): Promise<IDBDatabase> {
  if (!globalThis.indexedDB) return Promise.reject(new Error('当前浏览器不支持 IndexedDB'))
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION)
    request.onupgradeneeded = () => {
      const database = request.result
      if (!database.objectStoreNames.contains(STORE_NAME)) database.createObjectStore(STORE_NAME)
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('无法打开拟合 checkpoint IndexedDB'))
    request.onblocked = () => reject(new Error('拟合 checkpoint IndexedDB 被其他页面阻止'))
  })
}

async function withStore<T>(
  mode: IDBTransactionMode,
  action: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const database = await openDatabase()
  try {
    const transaction = database.transaction(STORE_NAME, mode)
    const result = await requestResult(action(transaction.objectStore(STORE_NAME)))
    await new Promise<void>((resolve, reject) => {
      transaction.oncomplete = () => resolve()
      transaction.onabort = () => reject(transaction.error ?? new Error('拟合 checkpoint IndexedDB 事务中止'))
      transaction.onerror = () => reject(transaction.error ?? new Error('拟合 checkpoint IndexedDB 事务失败'))
    })
    return result
  } finally {
    database.close()
  }
}

export async function savePersistedFitCheckpoint(record: PersistedFitCheckpoint): Promise<void> {
  await withStore('readwrite', (store) => store.put(validatePersistedFitCheckpoint(record), CHECKPOINT_KEY))
}

export async function loadPersistedFitCheckpoint(): Promise<PersistedFitCheckpoint | null> {
  const value = await withStore('readonly', (store) => store.get(CHECKPOINT_KEY))
  return value === undefined ? null : validatePersistedFitCheckpoint(value)
}

export async function clearPersistedFitCheckpoint(): Promise<void> {
  await withStore('readwrite', (store) => store.delete(CHECKPOINT_KEY))
}
