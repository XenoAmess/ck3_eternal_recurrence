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
  english: {
    syntax: string
    engineOutcome: string
    note: string
  }
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
    english: {
      syntax: 'name = { ... }', engineOutcome: 'detected',
      note: 'Plain identifiers, coa, and numeric outer keys are accepted; export consistently writes coa.',
    },
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
    english: {
      syntax: 'pattern / color1..3 / colored_emblem / instance', engineOutcome: 'applied to designer working state',
      note: 'Position, scale, rotation, depth, repeated instances, masks, and negative scale were applied in a combined payload.',
    },
  },
  {
    id: 'hsv-and-comments',
    classification: 'supported',
    syntax: '# comment / hsv { h s v }',
    example: 'coa = { # comment\r\n color1 = hsv { 0.5 0.8 0.9 } }',
    engineOutcome: 'applied; Copy drops comments and emits RGB',
    evidence: 'mcp-applied',
    editorPolicy: 'accept',
    note: 'hsv { 0.60 0.75 0.80 } 的原生 Copy 结果为 rgb { 51 112 204 }，注释不保留。',
    english: {
      syntax: '# comment / hsv { h s v }', engineOutcome: 'applied; Copy drops comments and emits RGB',
      note: 'Native Copy converts hsv { 0.60 0.75 0.80 } to rgb { 51 112 204 }; comments are not preserved.',
    },
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
    english: {
      syntax: '@name = literal / field = @name', engineOutcome: 'applied',
      note: 'Only statically resolvable references are supported. The editor exports literals rather than variable syntax.',
    },
  },
  {
    id: 'textured-default',
    classification: 'supported',
    syntax: 'textured_emblem = { texture = "_default.dds" }',
    example: 'coa = { textured_emblem = { texture = "_default.dds" } }',
    engineOutcome: 'applied; texture preserved by Copy',
    evidence: 'mcp-applied',
    editorPolicy: 'warn',
    note: '已证明 _default.dds 进入 designer working state；未证明最终像素或完整字段集。',
    english: {
      syntax: 'textured_emblem = { texture = "_default.dds" }', engineOutcome: 'applied; texture preserved by Copy',
      note: '_default.dds is proven to enter designer working state; final pixels and a broader field set are not proven.',
    },
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
    english: {
      syntax: 'missing pattern/emblem resource name', engineOutcome: 'detected, resource unresolved',
      note: 'Syntax acceptance and resource existence are separate; inspect the exact manifest or configured candidates.',
    },
  },
  {
    id: 'empty-or-defaulted',
    classification: 'supported',
    syntax: '空块或缺少 pattern',
    example: 'coa = {}',
    engineOutcome: 'applied; Copy emits an empty body',
    evidence: 'mcp-applied',
    editorPolicy: 'warn',
    note: '引擎允许空 working state；编辑器会载入可编辑默认值并警告，不声称字节保真。',
    english: {
      syntax: 'empty body or missing pattern', engineOutcome: 'applied; Copy emits an empty body',
      note: 'The engine allows an empty working state. The editor loads editable defaults with a warning and does not claim byte preservation.',
    },
  },
  {
    id: 'parent',
    classification: 'supported',
    syntax: 'parent = c_england',
    example: 'coa = { parent = c_england color1 = blue }',
    engineOutcome: 'applied; parent reference preserved by Copy',
    evidence: 'mcp-applied',
    editorPolicy: 'warn',
    note: '与 color1 共存和 parent-only 都可应用；编辑器保留引用，但继承后最终像素仍需 CK3 确认。',
    english: {
      syntax: 'parent = c_england', engineOutcome: 'applied; parent reference preserved by Copy',
      note: 'Both parent-only and parent with color1 apply. The editor preserves the reference; inherited final pixels still need CK3 confirmation.',
    },
  },
  {
    id: 'duplicate-scalar',
    classification: 'supported',
    syntax: '同一块内重复普通标量',
    example: 'coa = { color1 = blue color1 = red }',
    engineOutcome: 'applied; last scalar wins',
    evidence: 'mcp-applied',
    editorPolicy: 'warn',
    note: '原生 Copy 输出 color1=red；编辑器采用同样规则并显示非阻断警告。',
    english: {
      syntax: 'repeated scalar in one block', engineOutcome: 'applied; last scalar wins',
      note: 'Native Copy emits color1=red. The editor follows the same rule and shows a non-blocking warning.',
    },
  },
  {
    id: 'multiple-root',
    classification: 'supported',
    syntax: '多个顶层纹章对象',
    example: 'first = { color1 = blue } second = { color1 = red }',
    engineOutcome: 'applied; first outer object wins',
    evidence: 'mcp-applied',
    editorPolicy: 'reject',
    note: '原生 Copy 输出第一个对象的 blue；编辑器仍拒绝默认丢弃后续对象。',
    english: {
      syntax: 'multiple top-level coat-of-arms objects', engineOutcome: 'applied; first outer object wins',
      note: 'Native Copy emits blue from the first object. The editor refuses to silently discard later objects.',
    },
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
    english: {
      syntax: 'fields without an outer wrapper', engineOutcome: 'not_detected',
      note: 'The clipboard reader requires one top-level name = { ... } object.',
    },
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
    english: {
      syntax: 'effect / trigger / event / decision / GUI expression', engineOutcome: 'not_detected; no evaluator call path',
      note: 'This entry point has no scope, effect VM, trigger evaluator, event queue, or console dispatcher.',
    },
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
    english: {
      syntax: 'list / weighted list / template trigger', engineOutcome: 'not_detected',
      note: 'This is random-template-stage DSL, not a materialized render description.',
    },
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
    english: {
      syntax: 'unknown key or color4', engineOutcome: 'not_detected',
      note: 'Fields outside the editor allowlist are not treated as executable extensions.',
    },
  },
]
