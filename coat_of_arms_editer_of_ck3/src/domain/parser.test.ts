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

  it('expands static variables, preserves parent, and rejects lossy multiple roots', () => {
    const result = parseCoatOfArms('@chosen=blue first={color1=@chosen parent=c_england} second={color1=red}')

    expect(result.coatOfArms.colors[0]).toBe('blue')
    expect(result.coatOfArms.parent).toBe('c_england')
    expect(result.diagnostics.map((item) => item.severity)).toContain('error')
    expect(result.diagnostics.map((item) => item.message).join(' ')).toContain('parent')
    expect(serializeCoatOfArms(result.coatOfArms)).toContain('parent = c_england')
  })

  it('does not invent inheritable root fields around a parent reference', () => {
    const parentOnly = parseCoatOfArms('coa={parent=c_england}')
    const oneOverride = parseCoatOfArms('coa={parent=c_england color1=blue}')

    expect(serializeCoatOfArms(parentOnly.coatOfArms)).toBe([
      'coa = {',
      '    parent = c_england',
      '}',
      '',
    ].join('\r\n'))
    const overrideOutput = serializeCoatOfArms(oneOverride.coatOfArms)
    expect(overrideOutput).toContain('color1 = blue')
    expect(overrideOutput).not.toContain('color2 =')
    expect(overrideOutput).not.toContain('color3 =')
  })

  it('rejects unresolved, cyclic and duplicate static variables', () => {
    const unresolved = parseCoatOfArms('coa={color1=@missing}')
    const cyclic = parseCoatOfArms('@a=@b @b=@a coa={color1=@a}')
    const duplicate = parseCoatOfArms('@a=blue @a=red coa={color1=@a}')

    expect(unresolved.diagnostics.some((item) => item.message.includes('未声明'))).toBe(true)
    expect(cyclic.diagnostics.some((item) => item.message.includes('循环'))).toBe(true)
    expect(duplicate.diagnostics.some((item) => item.message.includes('重复声明'))).toBe(true)
  })

  it('rejects loose values and scalar assignments outside the wrapper', () => {
    const loose = parseCoatOfArms('garbage coa={pattern="pattern_solid.dds"}')
    const scalar = parseCoatOfArms('unexpected=yes coa={pattern="pattern_solid.dds"}')

    expect(loose.diagnostics.some((item) => item.message.includes('顶层游离值'))).toBe(true)
    expect(scalar.diagnostics.some((item) => item.message.includes('顶层标量'))).toBe(true)
  })

  it('serializes deterministic CRLF source with a coa wrapper', () => {
    const result = parseCoatOfArms('79={pattern="pattern_solid.dds" color1=blue}')
    const output = serializeCoatOfArms(result.coatOfArms)

    expect(output.startsWith('coa = {\r\n')).toBe(true)
    expect(output).toContain('pattern = "pattern_solid.dds"')
    expect(output).not.toMatch(/(?<!\r)\n/)
  })

  it('imports native Copy output and drops engine-owned wrapper metadata', () => {
    const source = 'coa_rd_dynasty_4127510289={\r\n\tcustom=yes\r\n\tpattern="pattern_solid.dds"\r\n\tcolor1=black\r\n\tcolor2=white\r\n\tcolor3=black\r\n\tcolored_emblem={\r\n\t\tcolor1=white\r\n\t\ttexture="ce_fleur.dds"\r\n\t\tinstance={\r\n\t\t\tscale={ 0.700000 0.700000 }\r\n\t\t}\r\n\r\n\t}\r\n\r\n}\r\n'
    const result = parseCoatOfArms(source)

    expect(result.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
    expect(result.coatOfArms.outerKey).toBe('coa_rd_dynasty_4127510289')
    result.coatOfArms.colors[0] = 'red'

    const output = serializeCoatOfArms(result.coatOfArms)
    expect(output.startsWith('coa = {\r\n')).toBe(true)
    expect(output).not.toContain('custom =')
    expect(output).toContain('color1 = red')
    expect(output).toContain('texture = "ce_fleur.dds"')
    expect(result.coatOfArms.coloredEmblems[0].mask).toEqual([])
    expect(output).not.toContain('mask =')
  })

  it('round-trips an explicitly unmasked generated emblem without inventing a mask', () => {
    const source = [
      'coa = {',
      '    pattern = "pattern_solid.dds"',
      '    color1 = black',
      '    color2 = white',
      '    color3 = red',
      '',
      '    colored_emblem = {',
      '        texture = "ce_block_02.dds"',
      '        color1 = black',
      '        color2 = black',
      '        color3 = black',
      '',
      '        instance = {',
      '            position = { 0.5 0.5 }',
      '            scale = { 1 1 }',
      '            rotation = 0',
      '            depth = 1',
      '        }',
      '    }',
      '}',
      '',
    ].join('\r\n')
    const result = parseCoatOfArms(source)

    expect(result.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
    expect(result.coatOfArms.coloredEmblems[0].mask).toEqual([])
    expect(serializeCoatOfArms(result.coatOfArms)).toBe(source)
  })

  it('rejects body-only syntax', () => {
    const result = parseCoatOfArms('pattern="pattern_solid.dds" color1=blue')
    expect(result.diagnostics.some((item) => item.severity === 'error')).toBe(true)
  })

  it('blocks template DSL and follows the native last-wins duplicate scalar rule', () => {
    const template = parseCoatOfArms('coa={pattern="pattern_solid.dds" color1=list "normal_colors"}')
    const duplicate = parseCoatOfArms('coa={color1=blue color1=red}')

    expect(template.diagnostics.some((item) => item.severity === 'error')).toBe(true)
    expect(duplicate.diagnostics.some((item) => item.severity === 'error')).toBe(false)
    expect(duplicate.diagnostics.some((item) => item.severity === 'warning')).toBe(true)
    expect(duplicate.coatOfArms.colors[0]).toBe('red')
    expect(serializeCoatOfArms(duplicate.coatOfArms)).toContain('color1 = red')
  })

  it('rejects color expressions outside the proven deterministic subset', () => {
    const tagged = parseCoatOfArms(
      'coa={pattern="pattern_solid.dds" color1=effect { add_gold=1000 }}',
    )
    const unicode = parseCoatOfArms(
      'coa={pattern="pattern_solid.dds" color1="蓝色"}',
    )

    expect(tagged.diagnostics.some((item) => item.message.includes('rgb/hsv'))).toBe(true)
    expect(unicode.diagnostics.some((item) => item.message.includes('rgb/hsv'))).toBe(true)
  })

  it('does not silently replace malformed numeric blocks with defaults', () => {
    const result = parseCoatOfArms(
      'coa={pattern="pattern_solid.dds" colored_emblem={texture="ce_martlet.dds" mask={one} instance={position={x=1} scale=wide rotation=nope depth=nan}}}',
    )

    expect(result.diagnostics.filter((item) => item.severity === 'error').length).toBeGreaterThanOrEqual(3)
    expect(result.diagnostics.map((item) => item.message).join(' ')).toContain('position')
    expect(result.diagnostics.map((item) => item.message).join(' ')).toContain('mask')
  })

  it('round-trips the only live-detected textured emblem shape', () => {
    const result = parseCoatOfArms(
      'coa={pattern="pattern_solid.dds" textured_emblem={texture="_default.dds"}}',
    )
    const output = serializeCoatOfArms(result.coatOfArms)

    expect(result.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
    expect(result.coatOfArms.texturedEmblems).toEqual([{ texture: '_default.dds' }])
    expect(output).toContain('textured_emblem = {\r\n')
    expect(output).toContain('texture = "_default.dds"')
  })
})
