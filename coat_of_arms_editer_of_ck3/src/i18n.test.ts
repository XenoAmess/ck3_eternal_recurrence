import { describe, expect, it } from 'vitest'
import { interpolate, resolveUiLocale } from './i18n'

describe('UI locale contract', () => {
  it('prefers an explicit stored locale and otherwise follows browser languages', () => {
    expect(resolveUiLocale(['en-US', 'zh-CN'], 'zh-CN')).toBe('zh-CN')
    expect(resolveUiLocale(['zh-Hans-CN', 'en-US'])).toBe('zh-CN')
    expect(resolveUiLocale(['en-US', 'fr-FR'])).toBe('en')
  })

  it('interpolates only declared named placeholders', () => {
    expect(interpolate('{count} instances · {missing}', { count: 12 })).toBe('12 instances · {missing}')
  })
})
