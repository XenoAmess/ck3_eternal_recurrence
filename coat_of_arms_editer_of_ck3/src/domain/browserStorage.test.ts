import { describe, expect, it } from 'vitest'
import {
  asBrowserStorageError,
  BrowserStorageError,
  classifyBrowserStorageFailure,
  inspectBrowserStorage,
} from './browserStorage'

describe('browser storage diagnostics', () => {
  it('classifies quota, abort, unavailable, blocked and unknown failures', () => {
    expect(classifyBrowserStorageFailure(new DOMException('full', 'QuotaExceededError'))).toBe('quota')
    expect(classifyBrowserStorageFailure(new DOMException('abort', 'AbortError'))).toBe('aborted')
    expect(classifyBrowserStorageFailure(new DOMException('denied', 'SecurityError'))).toBe('unavailable')
    expect(classifyBrowserStorageFailure(new BrowserStorageError('blocked', 'open'))).toBe('blocked')
    expect(classifyBrowserStorageFailure(new Error('other'))).toBe('unknown')
  })

  it('keeps the original operation and upgrades fallback-only failures', () => {
    const result = asBrowserStorageError(new Error('blocked by another tab'), 'open', 'blocked')
    expect(result).toMatchObject({ kind: 'blocked', operation: 'open' })
    expect(result.cause).toBeInstanceOf(Error)
  })

  it('reports bounded remaining bytes without treating estimates as write results', async () => {
    await expect(inspectBrowserStorage({
      estimate: async () => ({ usage: 600, quota: 1_000 }),
    })).resolves.toEqual({
      status: 'available', usageBytes: 600, quotaBytes: 1_000, remainingBytes: 400,
    })
    await expect(inspectBrowserStorage(undefined)).resolves.toEqual({
      status: 'unavailable', usageBytes: null, quotaBytes: null, remainingBytes: null,
    })
    await expect(inspectBrowserStorage({
      estimate: async () => { throw new Error('estimate denied') },
    })).resolves.toEqual({
      status: 'error', usageBytes: null, quotaBytes: null, remainingBytes: null,
    })
  })
})
