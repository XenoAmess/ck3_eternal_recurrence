import { describe, expect, it } from 'vitest'
import { parseCoatOfArms } from './parser'
import { serializeCoatOfArms } from './serializer'

describe('CK3 coat of arms parser', () => {
  it('imports the live-applied core shape and preserves repeated instances', () => {
    const source = 'coa={pattern="pattern_solid.dds" color1=rgb { 32 64 160 } colored_emblem={texture="ce_martlet.dds" mask={1 2 3} instance={position={0.3 0.5} scale={0.35 0.35} rotation=-20 depth=1.01} instance={position={0.7 0.5} scale={-0.35 0.35} rotation=20 depth=2.01}}}'
    const result = parseCoatOfArms(source)

    expect(result.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
    expect(result.coatOfArms.colors[0]).toBe('rgb { 32 64 160 }')
    expect(result.coatOfArms.coloredEmblems[0].mask).toEqual([1, 2, 3])
    expect(result.coatOfArms.coloredEmblems[0].instances).toHaveLength(2)
    expect(result.coatOfArms.coloredEmblems[0].instances[1].scale[0]).toBe(-0.35)
  })

  it('expands static variables and diagnoses engine-ambiguous input', () => {
    const result = parseCoatOfArms('@chosen=blue first={color1=@chosen parent=c_england} second={color1=red}')

    expect(result.coatOfArms.colors[0]).toBe('blue')
    expect(result.diagnostics.map((item) => item.severity)).toContain('error')
    expect(result.diagnostics.map((item) => item.message).join(' ')).toContain('parent')
  })

  it('serializes deterministic CRLF source with a coa wrapper', () => {
    const result = parseCoatOfArms('79={pattern="pattern_solid.dds" color1=blue}')
    const output = serializeCoatOfArms(result.coatOfArms)

    expect(output.startsWith('coa = {\r\n')).toBe(true)
    expect(output).toContain('pattern = "pattern_solid.dds"')
    expect(output).not.toMatch(/(?<!\r)\n/)
  })

  it('rejects body-only syntax', () => {
    const result = parseCoatOfArms('pattern="pattern_solid.dds" color1=blue')
    expect(result.diagnostics.some((item) => item.severity === 'error')).toBe(true)
  })

  it('blocks template DSL and duplicate scalar ambiguity', () => {
    const template = parseCoatOfArms('coa={pattern="pattern_solid.dds" color1=list "normal_colors"}')
    const duplicate = parseCoatOfArms('coa={color1=blue color1=red}')

    expect(template.diagnostics.some((item) => item.severity === 'error')).toBe(true)
    expect(duplicate.diagnostics.some((item) => item.severity === 'error')).toBe(true)
  })
})
