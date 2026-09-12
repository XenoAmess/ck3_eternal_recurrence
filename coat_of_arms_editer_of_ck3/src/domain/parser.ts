import type {
  CoatOfArms,
  CoatOfArmsInstance,
  ColoredEmblem,
  Diagnostic,
  ImportResult,
  TexturedEmblem,
} from './types'
import { createCoatOfArms, createInstance } from './types'

type TokenKind = 'atom' | 'string' | 'equals' | 'open' | 'close' | 'eof'

interface Token {
  kind: TokenKind
  text: string
  line: number
  column: number
}

interface AstAtom {
  kind: 'atom'
  text: string
}

interface AstBlock {
  kind: 'block'
  items: AstItem[]
}

interface AstTaggedBlock {
  kind: 'tagged-block'
  tag: string
  block: AstBlock
}

type AstValue = AstAtom | AstBlock | AstTaggedBlock

interface AstAssignment {
  kind: 'assignment'
  key: string
  value: AstValue
  token: Token
}

type AstItem = AstAssignment | AstValue

class ParseFailure extends Error {
  constructor(
    message: string,
    readonly token: Token,
  ) {
    super(message)
  }
}

function tokenize(source: string): Token[] {
  const tokens: Token[] = []
  let index = 0
  let line = 1
  let column = 1

  const advance = () => {
    const char = source[index++]
    if (char === '\n') {
      line += 1
      column = 1
    } else {
      column += 1
    }
    return char
  }

  while (index < source.length) {
    const char = source[index]
    if (/\s/.test(char)) {
      advance()
      continue
    }
    if (char === '#') {
      while (index < source.length && source[index] !== '\n') advance()
      continue
    }
    const startLine = line
    const startColumn = column
    if (char === '=' || char === '{' || char === '}') {
      const kind = char === '=' ? 'equals' : char === '{' ? 'open' : 'close'
      tokens.push({ kind, text: advance(), line: startLine, column: startColumn })
      continue
    }
    if (char === '"') {
      advance()
      let value = ''
      let closed = false
      while (index < source.length) {
        const current = advance()
        if (current === '"') {
          closed = true
          break
        }
        if (current === '\\' && index < source.length) {
          value += advance()
        } else {
          value += current
        }
      }
      if (!closed) {
        throw new ParseFailure('字符串缺少结束引号', {
          kind: 'string', text: value, line: startLine, column: startColumn,
        })
      }
      tokens.push({ kind: 'string', text: value, line: startLine, column: startColumn })
      continue
    }
    let value = ''
    while (index < source.length && !/[\s={}#"]/.test(source[index])) {
      value += advance()
    }
    if (!value) {
      throw new ParseFailure(`无法识别字符 ${JSON.stringify(char)}`, {
        kind: 'atom', text: char, line: startLine, column: startColumn,
      })
    }
    tokens.push({ kind: 'atom', text: value, line: startLine, column: startColumn })
  }
  tokens.push({ kind: 'eof', text: '', line, column })
  return tokens
}

class Parser {
  private index = 0

  constructor(private readonly tokens: Token[]) {}

  parseDocument(): AstItem[] {
    const items: AstItem[] = []
    while (this.peek().kind !== 'eof') items.push(this.parseItem())
    return items
  }

  private parseItem(): AstItem {
    const token = this.peek()
    const next = this.tokens[this.index + 1]
    if ((token.kind === 'atom' || token.kind === 'string') && next?.kind === 'equals') {
      this.index += 2
      return { kind: 'assignment', key: token.text, value: this.parseValue(), token }
    }
    return this.parseValue()
  }

  private parseValue(): AstValue {
    const token = this.peek()
    if (token.kind === 'open') return this.parseBlock()
    if (token.kind !== 'atom' && token.kind !== 'string') {
      throw new ParseFailure('这里需要一个值', token)
    }
    this.index += 1
    if (this.peek().kind === 'open') {
      return { kind: 'tagged-block', tag: token.text, block: this.parseBlock() }
    }
    return { kind: 'atom', text: token.text }
  }

  private parseBlock(): AstBlock {
    this.expect('open')
    const items: AstItem[] = []
    while (this.peek().kind !== 'close') {
      if (this.peek().kind === 'eof') throw new ParseFailure('块缺少结束花括号', this.peek())
      items.push(this.parseItem())
    }
    this.expect('close')
    return { kind: 'block', items }
  }

  private peek(): Token {
    return this.tokens[this.index]
  }

  private expect(kind: TokenKind): Token {
    const token = this.peek()
    if (token.kind !== kind) throw new ParseFailure(`需要 ${kind}`, token)
    this.index += 1
    return token
  }
}

const isAssignment = (item: AstItem): item is AstAssignment => item.kind === 'assignment'

function valueText(value: AstValue): string {
  if (value.kind === 'atom') return value.text
  const block = value.kind === 'tagged-block' ? value.block : value
  const body = block.items.map((item) => {
    if (isAssignment(item)) return `${item.key} = ${valueText(item.value)}`
    return valueText(item)
  }).join(' ')
  return value.kind === 'tagged-block' ? `${value.tag} { ${body} }` : `{ ${body} }`
}

function assignments(block: AstBlock): AstAssignment[] {
  return block.items.filter(isAssignment)
}

function diagnoseLooseValues(block: AstBlock, context: string, diagnostics: Diagnostic[]) {
  for (const item of block.items.filter((candidate) => !isAssignment(candidate))) {
    diagnostics.push({
      severity: 'error',
      message: `${context} 中存在不能解释为 key = value 的游离值：${valueText(item)}`,
    })
  }
}

function findLastAssignment(entries: AstAssignment[], key: string): AstAssignment | undefined {
  for (let index = entries.length - 1; index >= 0; index -= 1) {
    if (entries[index].key === key) return entries[index]
  }
  return undefined
}

function scalar(
  entries: AstAssignment[],
  key: string,
  fallback: string,
  diagnostics: Diagnostic[],
  variables: Map<string, string>,
): string {
  const matches = entries.filter((entry) => entry.key === key)
  if (!matches.length) return fallback
  if (matches.length > 1) diagnostics.push({
    severity: 'error',
    message: `${key} 重复 ${matches.length} 次；编辑器采用最后一个值，导出前应人工确认`,
    line: matches[1].token.line,
    column: matches[1].token.column,
  })
  let result = valueText(matches.at(-1)!.value)
  const seen = new Set<string>()
  while (result.startsWith('@') && variables.has(result) && !seen.has(result)) {
    seen.add(result)
    result = variables.get(result)!
  }
  return result
}

function numberList(value: AstValue | undefined, fallback: number[]): number[] {
  if (!value || value.kind !== 'block') return [...fallback]
  const parsed = value.items
    .filter((item): item is AstAtom => item.kind === 'atom')
    .map((item) => Number(item.text))
  return parsed.length && parsed.every(Number.isFinite) ? parsed : [...fallback]
}

function parseInstance(block: AstBlock, diagnostics: Diagnostic[]): CoatOfArmsInstance {
  const fallback = createInstance()
  diagnoseLooseValues(block, 'instance', diagnostics)
  const entries = assignments(block)
  const position = numberList(entries.find((entry) => entry.key === 'position')?.value, fallback.position)
  const scale = numberList(entries.find((entry) => entry.key === 'scale')?.value, fallback.scale)
  if (position.length !== 2) diagnostics.push({ severity: 'warning', message: 'position 应有两个数值' })
  if (scale.length !== 2) diagnostics.push({ severity: 'warning', message: 'scale 应有两个数值' })
  const readNumber = (key: string, value: number) => {
    const text = findLastAssignment(entries, key)
    if (!text) return value
    const parsed = Number(valueText(text.value))
    if (!Number.isFinite(parsed)) {
      diagnostics.push({ severity: 'warning', message: `${key} 不是有效数值` })
      return value
    }
    return parsed
  }
  return {
    position: [position[0] ?? 0.5, position[1] ?? 0.5],
    scale: [scale[0] ?? 0.7, scale[1] ?? 0.7],
    rotation: readNumber('rotation', fallback.rotation),
    depth: readNumber('depth', fallback.depth),
  }
}

const KNOWN_ROOT = new Set(['custom', 'pattern', 'color1', 'color2', 'color3', 'colored_emblem', 'textured_emblem'])
const KNOWN_EMBLEM = new Set(['texture', 'color1', 'color2', 'color3', 'mask', 'instance'])
const KNOWN_TEXTURED_EMBLEM = new Set(['texture'])

export function parseCoatOfArms(source: string): ImportResult {
  const diagnostics: Diagnostic[] = []
  const fallback = createCoatOfArms()
  try {
    const document = new Parser(tokenize(source)).parseDocument()
    const topLevel = document.filter(isAssignment)
    const variables = new Map<string, string>()
    for (const entry of topLevel.filter((entry) => entry.key.startsWith('@'))) {
      variables.set(entry.key, valueText(entry.value))
    }
    const outer = topLevel.filter((entry) => !entry.key.startsWith('@') && entry.value.kind === 'block')
    if (!outer.length) throw new ParseFailure('需要 name = { ... } 外层对象', topLevel[0]?.token ?? { kind: 'eof', text: '', line: 1, column: 1 })
    if (outer.length > 1) diagnostics.push({ severity: 'error', message: '存在多个顶层纹章对象；CK3 的采用规则不明确' })

    const selected = outer[0]
    const block = selected.value as AstBlock
    diagnoseLooseValues(block, '纹章根块', diagnostics)
    const entries = assignments(block)
    for (const entry of entries.filter((entry) => !KNOWN_ROOT.has(entry.key))) {
      diagnostics.push({
        severity: entry.key === 'parent' ? 'warning' : 'error',
        message: entry.key === 'parent'
          ? 'parent 可被 CK3 reader 接受，但继承结果尚未验证；确定性导出会移除它'
          : `不支持的根字段：${entry.key}`,
        line: entry.token.line,
        column: entry.token.column,
      })
    }

    const coloredEmblems: ColoredEmblem[] = []
    const texturedEmblems: TexturedEmblem[] = []
    for (const entry of entries) {
      if (entry.key === 'colored_emblem' && entry.value.kind === 'block') {
        diagnoseLooseValues(entry.value, 'colored_emblem', diagnostics)
        const emblemEntries = assignments(entry.value)
        for (const unknown of emblemEntries.filter((item) => !KNOWN_EMBLEM.has(item.key))) {
          diagnostics.push({ severity: 'error', message: `不支持的 colored_emblem 字段：${unknown.key}`, line: unknown.token.line, column: unknown.token.column })
        }
        coloredEmblems.push({
          texture: scalar(emblemEntries, 'texture', 'ce_martlet.dds', diagnostics, variables),
          colors: [1, 2, 3].map((index) => scalar(emblemEntries, `color${index}`, index === 1 ? 'yellow' : 'white', diagnostics, variables)) as [string, string, string],
          mask: numberList(findLastAssignment(emblemEntries, 'mask')?.value, [1]),
          instances: emblemEntries
            .filter((item) => item.key === 'instance' && item.value.kind === 'block')
            .map((item) => parseInstance(item.value as AstBlock, diagnostics)),
        })
      }
      if (entry.key === 'textured_emblem' && entry.value.kind === 'block') {
        diagnoseLooseValues(entry.value, 'textured_emblem', diagnostics)
        const texturedEntries = assignments(entry.value)
        for (const unknown of texturedEntries.filter((item) => !KNOWN_TEXTURED_EMBLEM.has(item.key))) {
          diagnostics.push({ severity: 'error', message: `不支持的 textured_emblem 字段：${unknown.key}`, line: unknown.token.line, column: unknown.token.column })
        }
        texturedEmblems.push({
          texture: scalar(texturedEntries, 'texture', '_default.dds', diagnostics, variables),
        })
      }
    }

    const coatOfArms: CoatOfArms = {
      outerKey: selected.key,
      pattern: scalar(entries, 'pattern', '', diagnostics, variables),
      colors: [1, 2, 3].map((index) => scalar(entries, `color${index}`, index === 1 ? 'blue' : 'white', diagnostics, variables)) as [string, string, string],
      coloredEmblems,
      texturedEmblems,
    }
    if (!coatOfArms.pattern) diagnostics.push({ severity: 'warning', message: '缺少 pattern；CK3 虽可能接受，但结果依赖默认值' })
    if (variables.size) diagnostics.push({ severity: 'info', message: `已展开 ${variables.size} 个静态 @变量；导出使用确定字面量` })
    return { coatOfArms, diagnostics }
  } catch (error) {
    if (error instanceof ParseFailure) {
      diagnostics.push({ severity: 'error', message: error.message, line: error.token.line, column: error.token.column })
    } else {
      diagnostics.push({ severity: 'error', message: error instanceof Error ? error.message : '未知解析错误' })
    }
    return { coatOfArms: fallback, diagnostics }
  }
}
