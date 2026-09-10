import type { CoatOfArms } from './types'

const indent = (level: number) => '    '.repeat(level)

const quoted = (value: string) => {
  if (/^(?:[A-Za-z0-9_@.:-]+|rgb\s*\{[^}]+\}|hsv\s*\{[^}]+\})$/.test(value)) return value
  return `"${value.replaceAll('\\', '\\\\').replaceAll('"', '\\"')}"`
}

const texture = (value: string) => `"${value.replaceAll('\\', '\\\\').replaceAll('"', '\\"')}"`

export function serializeCoatOfArms(coatOfArms: CoatOfArms): string {
  const lines = ['coa = {']
  if (coatOfArms.pattern.trim()) lines.push(`${indent(1)}pattern = ${texture(coatOfArms.pattern.trim())}`)
  coatOfArms.colors.forEach((color, index) => {
    if (color.trim()) lines.push(`${indent(1)}color${index + 1} = ${quoted(color.trim())}`)
  })

  coatOfArms.coloredEmblems.forEach((emblem) => {
    lines.push('', `${indent(1)}colored_emblem = {`)
    lines.push(`${indent(2)}texture = ${texture(emblem.texture.trim())}`)
    emblem.colors.forEach((color, index) => {
      if (color.trim()) lines.push(`${indent(2)}color${index + 1} = ${quoted(color.trim())}`)
    })
    if (emblem.mask.length) lines.push(`${indent(2)}mask = { ${emblem.mask.join(' ')} }`)
    emblem.instances.forEach((instance) => {
      lines.push('', `${indent(2)}instance = {`)
      lines.push(`${indent(3)}position = { ${instance.position.join(' ')} }`)
      lines.push(`${indent(3)}scale = { ${instance.scale.join(' ')} }`)
      lines.push(`${indent(3)}rotation = ${instance.rotation}`)
      lines.push(`${indent(3)}depth = ${instance.depth}`)
      lines.push(`${indent(2)}}`)
    })
    lines.push(`${indent(1)}}`)
  })

  coatOfArms.texturedEmblems.forEach((emblem) => {
    lines.push('', `${indent(1)}textured_emblem = {`)
    lines.push(`${indent(2)}texture = ${texture(emblem.texture.trim())}`)
    lines.push(`${indent(1)}}`)
  })
  lines.push('}', '')
  return lines.join('\r\n')
}
