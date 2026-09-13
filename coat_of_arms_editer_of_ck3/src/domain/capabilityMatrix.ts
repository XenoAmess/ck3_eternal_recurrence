export type SyntaxClassification = 'supported' | 'not-executable' | 'ambiguous'
export type EditorPolicy = 'accept' | 'warn' | 'sanitize' | 'reject'

export interface SyntaxCapabilityRow {
  id: string
  classification: SyntaxClassification
  syntax: string
  example: string
  engineOutcome: string
  evidence: 'mcp-applied' | 'mcp-detected' | 'mcp-not-detected'
  editorPolicy: EditorPolicy
  note: string
}

/**
 * Product-facing projection of the exact-build matrix in
 * docs/ck3-coat-of-arms-clipboard-import-capability.md §5–§7.
 * Keep this list conservative: syntax not present here is not advertised.
 */
export const syntaxCapabilityRows: readonly SyntaxCapabilityRow[] = [
  {
    id: 'wrapper',
    classification: 'supported',
    syntax: 'name = { ... }',
    example: 'coa = { pattern = "pattern_solid.dds" }',
    engineOutcome: 'detected',
    evidence: 'mcp-detected',
    editorPolicy: 'accept',
    note: '普通标识符、coa 与数字 outer key 都被 reader 接受；导出统一写 coa。',
  },
  {
    id: 'core-render-description',
    classification: 'supported',
    syntax: 'pattern / color1..3 / colored_emblem / instance',
    example: 'coa = { pattern = "pattern_solid.dds" color1 = rgb { 32 64 160 } colored_emblem = { texture = "ce_martlet.dds" mask = { 1 } instance = { position = { 0.5 0.5 } scale = { -0.7 0.7 } rotation = -20 depth = 1.01 } } }',
    engineOutcome: 'applied to designer working state',
    evidence: 'mcp-applied',
    editorPolicy: 'accept',
    note: 'position、scale、rotation、depth、多实例、mask 与负 scale 已在组合载荷中应用。',
  },
  {
    id: 'hsv-and-comments',
    classification: 'supported',
    syntax: '# comment / hsv { h s v }',
    example: 'coa = { # comment\r\n color1 = hsv { 0.5 0.8 0.9 } }',
    engineOutcome: 'detected',
    evidence: 'mcp-detected',
    editorPolicy: 'accept',
    note: '注释与 HSV 的 canonical copy-back 规则尚未用当前 export round-trip 闭合。',
  },
  {
    id: 'static-variable',
    classification: 'supported',
    syntax: '@name = literal / field = @name',
    example: '@chosen = blue coa = { color1 = @chosen }',
    engineOutcome: 'applied',
    evidence: 'mcp-applied',
    editorPolicy: 'sanitize',
    note: '只支持可静态展开的引用；编辑器导出字面量，不保留变量语法。',
  },
  {
    id: 'textured-default',
    classification: 'supported',
    syntax: 'textured_emblem = { texture = "_default.dds" }',
    example: 'coa = { textured_emblem = { texture = "_default.dds" } }',
    engineOutcome: 'detected',
    evidence: 'mcp-detected',
    editorPolicy: 'warn',
    note: '只验证 reader/preview handle；未证明最终像素或完整字段集。',
  },
  {
    id: 'missing-resource',
    classification: 'ambiguous',
    syntax: '不存在的 pattern/emblem 资源名',
    example: 'coa = { pattern = "does_not_exist.dds" }',
    engineOutcome: 'detected, resource unresolved',
    evidence: 'mcp-detected',
    editorPolicy: 'warn',
    note: '语法接受与资源存在是两层；应另查 exact manifest/配置候选。',
  },
  {
    id: 'empty-or-defaulted',
    classification: 'ambiguous',
    syntax: '空块或缺少 pattern',
    example: 'coa = { color1 = blue }',
    engineOutcome: 'detected',
    evidence: 'mcp-detected',
    editorPolicy: 'warn',
    note: '结果可能依赖引擎默认值，编辑器保留警告。',
  },
  {
    id: 'parent',
    classification: 'ambiguous',
    syntax: 'parent = c_england',
    example: 'coa = { parent = c_england color1 = blue }',
    engineOutcome: 'detected, inheritance unresolved',
    evidence: 'mcp-detected',
    editorPolicy: 'sanitize',
    note: 'reader 接受不等于继承结果已证明；确定性导出移除 parent。',
  },
  {
    id: 'duplicate-or-multiple-root',
    classification: 'ambiguous',
    syntax: '重复标量或多个顶层对象',
    example: 'first = { color1 = blue } second = { color1 = red }',
    engineOutcome: 'detected, precedence unresolved',
    evidence: 'mcp-detected',
    editorPolicy: 'reject',
    note: '引擎采用规则未由 canonical copy-back 证明，编辑器拒绝猜测。',
  },
  {
    id: 'body-only',
    classification: 'not-executable',
    syntax: '无 outer wrapper 的字段',
    example: 'pattern = "pattern_solid.dds" color1 = blue',
    engineOutcome: 'not_detected',
    evidence: 'mcp-not-detected',
    editorPolicy: 'reject',
    note: '剪贴板 reader 要求一个顶层 name = { ... } 对象。',
  },
  {
    id: 'script-vm-families',
    classification: 'not-executable',
    syntax: 'effect / trigger / event / decision / GUI expression',
    example: 'coa = { effect = { add_gold = 1000 } }',
    engineOutcome: 'not_detected; no evaluator call path',
    evidence: 'mcp-not-detected',
    editorPolicy: 'reject',
    note: '此入口没有 scope、effect VM、trigger evaluator、event queue 或控制台 dispatcher。',
  },
  {
    id: 'template-dsl',
    classification: 'not-executable',
    syntax: 'list / weighted list / template trigger',
    example: 'coa = { color1 = list "normal_colors" }',
    engineOutcome: 'not_detected',
    evidence: 'mcp-not-detected',
    editorPolicy: 'reject',
    note: '这是随机模板阶段 DSL，不是已经物化的 render description。',
  },
  {
    id: 'unknown-field',
    classification: 'not-executable',
    syntax: '未知键或 color4',
    example: 'coa = { color4 = red }',
    engineOutcome: 'not_detected',
    evidence: 'mcp-not-detected',
    editorPolicy: 'reject',
    note: '编辑器白名单之外的字段不会被当作可执行扩展。',
  },
]
