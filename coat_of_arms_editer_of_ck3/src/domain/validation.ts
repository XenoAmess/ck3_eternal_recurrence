import type { CoatOfArms, Diagnostic } from './types'

const ATOM = /^[A-Za-z0-9_.:-]+$/
const NUMBER = '[-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?'
const COLOR_BLOCK = new RegExp(
  `^(?:rgb|hsv)\\s*\\{\\s*${NUMBER}\\s+${NUMBER}\\s+${NUMBER}\\s*\\}$`,
  'i',
)

function isPrintableAscii(value: string): boolean {
  return [...value].every((character) => {
    const code = character.charCodeAt(0)
    return code >= 0x20 && code <= 0x7e
  })
}

export function isDeterministicColorExpression(value: string): boolean {
  const normalized = value.trim()
  return isPrintableAscii(normalized)
    && (ATOM.test(normalized) || COLOR_BLOCK.test(normalized))
}

function validateResourceName(
  value: string,
  field: string,
  diagnostics: Diagnostic[],
  emptySeverity: 'error' | 'warning' = 'error',
) {
  if (!value.trim()) {
    diagnostics.push({
      severity: emptySeverity,
      message: emptySeverity === 'warning'
        ? `${field} 为空；CK3 reader 可能接受，但结果依赖默认值`
        : `${field} 不能为空`,
    })
  } else if (!isPrintableAscii(value.trim())) {
    diagnostics.push({
      severity: 'error',
      message: `${field} 必须是可打印 ASCII；原生 MCP 不接受高位 UTF-8`,
    })
  }
}

function validateColors(
  colors: [string, string, string],
  context: string,
  diagnostics: Diagnostic[],
) {
  colors.forEach((color, index) => {
    if (!isDeterministicColorExpression(color)) {
      diagnostics.push({
        severity: 'error',
        message: `${context} color${index + 1} 只能是命名颜色或 rgb/hsv 三分量字面量`,
      })
    }
  })
}

export function validateCoatOfArms(coatOfArms: CoatOfArms): Diagnostic[] {
  const diagnostics: Diagnostic[] = []
  if (coatOfArms.parent.trim() && !ATOM.test(coatOfArms.parent.trim())) {
    diagnostics.push({
      severity: 'error',
      message: 'parent 只能是已实机验证形态的可打印 ASCII 数据库标识符',
    })
  }
  validateResourceName(coatOfArms.pattern, 'pattern', diagnostics, 'warning')
  validateColors(coatOfArms.colors, '根级', diagnostics)

  coatOfArms.coloredEmblems.forEach((emblem, emblemIndex) => {
    const context = `colored_emblem ${emblemIndex + 1}`
    validateResourceName(emblem.texture, `${context} texture`, diagnostics)
    validateColors(emblem.colors, context, diagnostics)
    if (!emblem.mask.every((value) => (
      Number.isInteger(value) && value >= 1 && value <= 3
    ))) {
      diagnostics.push({
        severity: 'error',
        message: `${context} mask 只能包含分区索引 1、2、3`,
      })
    }
    emblem.instances.forEach((instance, instanceIndex) => {
      const instanceContext = `${context} instance ${instanceIndex + 1}`
      if (
        instance.position.length !== 2
        || !instance.position.every(Number.isFinite)
      ) {
        diagnostics.push({
          severity: 'error',
          message: `${instanceContext} position 必须恰好包含两个有限数值`,
        })
      }
      if (instance.scale.length !== 2 || !instance.scale.every(Number.isFinite)) {
        diagnostics.push({
          severity: 'error',
          message: `${instanceContext} scale 必须恰好包含两个有限数值`,
        })
      }
      if (!Number.isFinite(instance.rotation)) {
        diagnostics.push({ severity: 'error', message: `${instanceContext} rotation 必须是有限数值` })
      }
      if (!Number.isFinite(instance.depth)) {
        diagnostics.push({ severity: 'error', message: `${instanceContext} depth 必须是有限数值` })
      }
    })
  })

  coatOfArms.texturedEmblems.forEach((emblem, index) => {
    const field = `textured_emblem ${index + 1} texture`
    validateResourceName(emblem.texture, field, diagnostics)
    if (emblem.texture.trim() && emblem.texture.trim() !== '_default.dds') {
      diagnostics.push({
        severity: 'warning',
        message: `${field} 尚无本构建原生实机检测证据；当前只验证了 _default.dds`,
      })
    }
  })
  return diagnostics
}
