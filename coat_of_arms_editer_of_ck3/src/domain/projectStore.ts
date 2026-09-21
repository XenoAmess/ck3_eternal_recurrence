import { asBrowserStorageError, BrowserStorageError } from './browserStorage'

const DATABASE_NAME = 'ck3-coa-browser-editor'
const DATABASE_VERSION = 1
const STORE_NAME = 'project-state'
const AUTOSAVE_KEY = 'latest-autosave'

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(asBrowserStorageError(
      request.error ?? new Error('IndexedDB 请求失败'),
      '项目存储请求',
    ))
  })
}

function openDatabase(): Promise<IDBDatabase> {
  if (!globalThis.indexedDB) return Promise.reject(new BrowserStorageError('unavailable', '打开项目 IndexedDB'))
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION)
    request.onupgradeneeded = () => {
      const database = request.result
      if (!database.objectStoreNames.contains(STORE_NAME)) database.createObjectStore(STORE_NAME)
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(asBrowserStorageError(
      request.error ?? new Error('无法打开 IndexedDB'),
      '打开项目 IndexedDB',
      'unavailable',
    ))
    request.onblocked = () => reject(new BrowserStorageError('blocked', '打开项目 IndexedDB'))
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
        transaction.error ?? new DOMException('项目 IndexedDB 事务中止', 'AbortError'),
        operation,
        'aborted',
      ))
      transaction.onerror = () => reject(asBrowserStorageError(
        transaction.error ?? new Error('项目 IndexedDB 事务失败'),
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

export async function saveAutosaveProject(text: string): Promise<void> {
  await withStore('readwrite', '写入项目自动保存', (store) => store.put(text, AUTOSAVE_KEY))
}

export async function loadAutosaveProject(): Promise<string | null> {
  const value = await withStore('readonly', '读取项目自动保存', (store) => store.get(AUTOSAVE_KEY))
  if (value === undefined) return null
  if (typeof value !== 'string') throw new Error('自动保存槽内容类型无效')
  return value
}

export async function clearAutosaveProject(): Promise<void> {
  await withStore('readwrite', '删除项目自动保存', (store) => store.delete(AUTOSAVE_KEY))
}
