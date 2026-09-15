const DATABASE_NAME = 'ck3-coa-browser-editor'
const DATABASE_VERSION = 1
const STORE_NAME = 'project-state'
const AUTOSAVE_KEY = 'latest-autosave'

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('IndexedDB 请求失败'))
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
    request.onerror = () => reject(request.error ?? new Error('无法打开 IndexedDB'))
    request.onblocked = () => reject(new Error('IndexedDB 升级被其他页面阻止'))
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
      transaction.onabort = () => reject(transaction.error ?? new Error('IndexedDB 事务中止'))
      transaction.onerror = () => reject(transaction.error ?? new Error('IndexedDB 事务失败'))
    })
    return result
  } finally {
    database.close()
  }
}

export async function saveAutosaveProject(text: string): Promise<void> {
  await withStore('readwrite', (store) => store.put(text, AUTOSAVE_KEY))
}

export async function loadAutosaveProject(): Promise<string | null> {
  const value = await withStore('readonly', (store) => store.get(AUTOSAVE_KEY))
  if (value === undefined) return null
  if (typeof value !== 'string') throw new Error('自动保存槽内容类型无效')
  return value
}

export async function clearAutosaveProject(): Promise<void> {
  await withStore('readwrite', (store) => store.delete(AUTOSAVE_KEY))
}
