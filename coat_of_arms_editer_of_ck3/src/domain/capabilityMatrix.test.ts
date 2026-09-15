import { describe, expect, it } from 'vitest'
import { syntaxCapabilityRows } from './capabilityMatrix'
import { parseCoatOfArms } from './parser'
import { serializeCoatOfArms } from './serializer'

describe('CK3 clipboard syntax capability matrix', () => {
  it('has unique stable identities and evidence on every row', () => {
    const identities = syntaxCapabilityRows.map((row) => row.id)
    expect(new Set(identities).size).toBe(identities.length)
    expect(syntaxCapabilityRows.every((row) => row.evidence.startsWith('mcp-'))).toBe(true)
    expect(syntaxCapabilityRows.every((row) => (
      ['parser', 'preview', 'editor', 'serializer'].every((stage) => (
        Boolean(row.coverage[stage as keyof typeof row.coverage])
      ))
    ))).toBe(true)
  })

  it('keeps accepted and warning examples inside the deterministic parser', () => {
    const rows = syntaxCapabilityRows.filter(
      (row) => row.editorPolicy === 'accept' || row.editorPolicy === 'warn',
    )
    for (const row of rows) {
      const errors = parseCoatOfArms(row.example).diagnostics.filter(
        (diagnostic) => diagnostic.severity === 'error',
      )
      expect(errors, row.id).toEqual([])
    }
  })

  it('rejects every advertised reject example', () => {
    const rows = syntaxCapabilityRows.filter((row) => row.editorPolicy === 'reject')
    for (const row of rows) {
      expect(
        parseCoatOfArms(row.example).diagnostics.some(
          (diagnostic) => diagnostic.severity === 'error',
        ),
        row.id,
      ).toBe(true)
    }
  })

  it('sanitizes static variables instead of exporting unresolved DSL', () => {
    for (const row of syntaxCapabilityRows.filter(
      (candidate) => candidate.editorPolicy === 'sanitize',
    )) {
      const parsed = parseCoatOfArms(row.example)
      const output = serializeCoatOfArms(parsed.coatOfArms)
      expect(parsed.diagnostics.some((diagnostic) => diagnostic.severity === 'error'), row.id).toBe(false)
      expect(output, row.id).not.toContain('@chosen')
    }
  })
})
