export type BrowserStorageFailureKind =
  | 'quota'
  | 'blocked'
  | 'unavailable'
  | 'aborted'
  | 'unknown'

export class BrowserStorageError extends Error {
  readonly kind: BrowserStorageFailureKind
  readonly operation: string

  constructor(kind: BrowserStorageFailureKind, operation: string, cause?: unknown) {
    const causeMessage = cause instanceof Error && cause.message ? `：${cause.message}` : ''
    super(`浏览器存储${operation}失败（${kind}）${causeMessage}`, { cause })
    this.name = 'BrowserStorageError'
    this.kind = kind
    this.operation = operation
  }
}

export interface BrowserStorageEstimate {
  status: 'available' | 'unavailable' | 'error'
  usageBytes: number | null
  quotaBytes: number | null
  remainingBytes: number | null
}

function errorName(error: unknown): string {
  if (error instanceof DOMException) return error.name
  if (error instanceof Error) return error.name
  if (typeof error === 'object' && error !== null && 'name' in error) {
    return String((error as { name: unknown }).name)
  }
  return ''
}

export function classifyBrowserStorageFailure(error: unknown): BrowserStorageFailureKind {
  if (error instanceof BrowserStorageError) return error.kind
  const name = errorName(error)
  if (name === 'QuotaExceededError' || name === 'NS_ERROR_DOM_QUOTA_REACHED') return 'quota'
  if (name === 'AbortError' || name === 'TransactionInactiveError') return 'aborted'
  if (
    name === 'InvalidStateError'
    || name === 'NotSupportedError'
    || name === 'SecurityError'
  ) return 'unavailable'
  return 'unknown'
}

export function asBrowserStorageError(
  error: unknown,
  operation: string,
  fallbackKind: BrowserStorageFailureKind = 'unknown',
): BrowserStorageError {
  if (error instanceof BrowserStorageError) return error
  const classified = classifyBrowserStorageFailure(error)
  return new BrowserStorageError(classified === 'unknown' ? fallbackKind : classified, operation, error)
}

export async function inspectBrowserStorage(
  storage: Pick<StorageManager, 'estimate'> | undefined = globalThis.navigator?.storage,
): Promise<BrowserStorageEstimate> {
  if (!storage?.estimate) {
    return { status: 'unavailable', usageBytes: null, quotaBytes: null, remainingBytes: null }
  }
  try {
    const estimate = await storage.estimate()
    const usageBytes = typeof estimate.usage === 'number' && Number.isFinite(estimate.usage)
      ? Math.max(0, estimate.usage)
      : null
    const quotaBytes = typeof estimate.quota === 'number' && Number.isFinite(estimate.quota)
      ? Math.max(0, estimate.quota)
      : null
    return {
      status: 'available',
      usageBytes,
      quotaBytes,
      remainingBytes: usageBytes === null || quotaBytes === null
        ? null
        : Math.max(0, quotaBytes - usageBytes),
    }
  } catch {
    return { status: 'error', usageBytes: null, quotaBytes: null, remainingBytes: null }
  }
}
