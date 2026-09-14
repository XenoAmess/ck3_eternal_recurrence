<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createCk3CompanionClient,
  type CoatOfArmsConfiguredResourceItem,
  type CoatOfArmsResourceItem,
} from './api/ck3Companion'
import { decodeDdsBase64, decodedDdsToDataUrl, type DecodedDds } from './domain/dds'
import { syntaxCapabilityRows } from './domain/capabilityMatrix'
import { parseCoatOfArms } from './domain/parser'
import {
  renderCoatOfArms,
  renderedCoatOfArmsToDataUrl,
  resolveColor,
  type NamedColorMap,
} from './domain/renderer'
import { serializeCoatOfArms } from './domain/serializer'
import { validateCoatOfArms } from './domain/validation'
import {
  createCoatOfArms,
  createColoredEmblem,
  createInstance,
  createTexturedEmblem,
  type CoatOfArms,
  type Diagnostic,
} from './domain/types'

const sample = `coa = {
    pattern = "pattern_solid.dds"
    color1 = rgb { 32 64 160 }
    color2 = white
    color3 = red

    colored_emblem = {
        texture = "ce_martlet.dds"
        color1 = yellow
        color2 = red
        color3 = white
        mask = { 1 }

        instance = {
            position = { 0.30 0.50 }
            scale = { 0.35 0.35 }
            rotation = -20
            depth = 1.01
        }
        instance = {
            position = { 0.70 0.50 }
            scale = { -0.35 0.35 }
            rotation = 20
            depth = 2.01
        }
    }
}`

const source = ref(sample)
const coatOfArms = ref<CoatOfArms>(createCoatOfArms())
const diagnostics = ref<Diagnostic[]>([])
const selectedEmblem = ref(0)
const companion = createCk3CompanionClient()
const mcpBusy = ref(false)
const catalogBusy = ref(false)
const textureBusy = ref(false)
const clipboardBusy = ref(false)
const mcpStatus = ref('未连接')
const patternResources = ref<CoatOfArmsResourceItem[]>([])
const emblemResources = ref<CoatOfArmsResourceItem[]>([])
const emblemSearch = ref('')
const patternPreviewUrl = ref('')
const emblemPreviewUrls = ref<Record<string, string>>({})
const patternTexture = ref<DecodedDds>()
const emblemTextures = ref<Record<string, DecodedDds>>({})
const surfaceMask = ref<DecodedDds>()
const texturedDefaultPreviewUrl = ref('')
const shaderNamedColors = ref<NamedColorMap>({})
const shaderSourceCount = ref(0)
const configuredModCount = ref<number | null>(null)
const installedDlcDescriptorCount = ref<number | null>(null)
const dlcCoaSourceCount = ref<number | null>(null)
const runtimeFeatureBusy = ref(false)
const runtimeFeatureStatus = ref('未读取')
const runtimeEnabledFeatureCount = ref<number | null>(null)
const runtimeFeatureCount = ref<number | null>(null)
const runtimeDlcKeys = ref<string[] | null>(null)
const configuredPatternCount = ref<number | null>(null)
const configuredEmblemCount = ref<number | null>(null)
const configuredArchiveCount = ref(0)
const configuredPatternResources = ref<CoatOfArmsConfiguredResourceItem[]>([])
const configuredEmblemResources = ref<CoatOfArmsConfiguredResourceItem[]>([])

const output = computed(() => serializeCoatOfArms(coatOfArms.value))
const activeEmblem = computed(() => coatOfArms.value.coloredEmblems[selectedEmblem.value])
const visibleDiagnostics = computed<Diagnostic[]>(() => {
  const items = [...diagnostics.value, ...validateCoatOfArms(coatOfArms.value)]
  if (new TextEncoder().encode(output.value).length > 128 * 1024) {
    items.push({ severity: 'error', message: '确定性导出超过原生 MCP 的 128 KiB 输入上限' })
  }
  return items.filter((item, index) => items.findIndex((candidate) => (
    candidate.severity === item.severity && candidate.message === item.message
  )) === index)
})
const errorCount = computed(() => visibleDiagnostics.value.filter((item) => item.severity === 'error').length)
const renderedPreviewUrl = computed(() => {
  const rendered = renderCoatOfArms(
    coatOfArms.value,
    {
      pattern: patternTexture.value,
      coloredEmblems: emblemTextures.value,
      surfaceMask: surfaceMask.value,
    },
    shaderNamedColors.value,
  )
  return rendered ? renderedCoatOfArmsToDataUrl(rendered) : ''
})

const fallbackNamedColors: Record<string, string> = {
  black: '#22201e', blue: '#315b9a', green: '#497554', red: '#9b3c35',
  white: '#eee7d8', yellow: '#d2a84b', orange: '#bb6b38', purple: '#6b4b7e',
}

function cssColor(value: string): string {
  const normalized = value.trim().replaceAll('"', '').toLowerCase()
  const resolved = resolveColor(value, shaderNamedColors.value)
  if (resolved) return `rgb(${resolved.map((channel) => Math.round(channel * 255)).join(' ')})`
  if (fallbackNamedColors[normalized]) return fallbackNamedColors[normalized]
  const rgb = normalized.match(/^rgb\s*\{\s*(\d+)\s+(\d+)\s+(\d+)\s*}$/)
  if (rgb) return `rgb(${rgb[1]} ${rgb[2]} ${rgb[3]})`
  return '#6f6254'
}

function importSource() {
  const result = parseCoatOfArms(source.value)
  coatOfArms.value = result.coatOfArms
  diagnostics.value = result.diagnostics
  selectedEmblem.value = 0
  patternPreviewUrl.value = ''
  emblemPreviewUrls.value = {}
  patternTexture.value = undefined
  emblemTextures.value = {}
  if (result.diagnostics.some((item) => item.severity === 'error')) {
    ElMessage.error('已解析，但存在阻止确定性导出的诊断')
  } else {
    ElMessage.success('已导入为结构化纹章')
  }
}

async function copyOutput() {
  if (errorCount.value > 0) {
    ElMessage.error('请先修复确定性导出诊断')
    return
  }
  try {
    await navigator.clipboard.writeText(output.value)
    ElMessage.success('CK3 纹章代码已复制；多行换行使用 CRLF')
  } catch (error) {
    ElMessage.error(`剪贴板写入失败：${errorMessage(error)}`)
  }
}

async function pasteSource() {
  clipboardBusy.value = true
  try {
    if (!navigator.clipboard?.readText) {
      throw new Error('当前浏览器或页面上下文不允许读取剪贴板')
    }
    const pasted = await navigator.clipboard.readText()
    if (!pasted.trim()) throw new Error('剪贴板中没有可导入的文本')
    source.value = pasted
    importSource()
  } catch (error) {
    ElMessage.error(`剪贴板读取失败：${errorMessage(error)}`)
  } finally {
    clipboardBusy.value = false
  }
}

function loadSample() {
  source.value = sample
  importSource()
}

function reset() {
  coatOfArms.value = createCoatOfArms()
  diagnostics.value = []
  selectedEmblem.value = 0
  patternPreviewUrl.value = ''
  emblemPreviewUrls.value = {}
  patternTexture.value = undefined
  emblemTextures.value = {}
}

function addEmblem() {
  coatOfArms.value.coloredEmblems.push(createColoredEmblem())
  selectedEmblem.value = coatOfArms.value.coloredEmblems.length - 1
}

function removeEmblem(index: number) {
  coatOfArms.value.coloredEmblems.splice(index, 1)
  selectedEmblem.value = Math.max(0, Math.min(selectedEmblem.value, coatOfArms.value.coloredEmblems.length - 1))
}

function parseMask(value: string) {
  if (!activeEmblem.value) return
  activeEmblem.value.mask = value.trim()
    ? value.trim().split(/[\s,]+/).map(Number)
    : []
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

async function getCurrentCoaRevision(): Promise<number> {
  const binding = await companion.sourceBinding()
  if (
    binding.schema !== 'coat-of-arms-source-binding-v1'
    || binding.status !== 'bound'
    || !Number.isSafeInteger(binding.revision)
    || binding.revision < 0
    || (binding.revision_source === 'frontend' && binding.revision !== 0)
    || (binding.revision_source === 'snapshot' && binding.revision < 1)
  ) {
    throw new Error('MCP 没有返回有效的家徽源码绑定')
  }
  mcpStatus.value = `已连接 · ${binding.revision_source} revision ${binding.revision}`
  return binding.revision
}

async function getCurrentGameplayRevision(): Promise<number> {
  const snapshot = await companion.session()
  if (!Number.isSafeInteger(snapshot.revision) || snapshot.revision < 1) {
    throw new Error('MCP snapshot 没有有效的正 revision')
  }
  return snapshot.revision
}

async function refreshSession() {
  mcpBusy.value = true
  try {
    await getCurrentCoaRevision()
    ElMessage.success('已连接本机 CK3 MCP')
  } catch (error) {
    mcpStatus.value = '不可用'
    ElMessage.error(`MCP 连接失败：${errorMessage(error)}`)
  } finally {
    mcpBusy.value = false
  }
}

async function openNativeDesigner() {
  mcpBusy.value = true
  try {
    const result = await companion.openNativeDesigner()
    if (
      result.status !== 'verified'
      || result.action !== 'open_coat_of_arms_designer'
      || result.postcondition_verified !== true
      || result.after?.route !== 'coat_of_arms_designer'
    ) {
      throw new Error('MCP 未证明 CK3 已进入家徽设计页')
    }
    mcpStatus.value = '家徽设计页已打开'
    ElMessage.success('CK3 已通过原生语义 MCP 打开王朝家徽设计页')
  } catch (error) {
    mcpStatus.value = '打开家徽页失败'
    ElMessage.error(`原生家徽页打开失败：${errorMessage(error)}`)
  } finally {
    mcpBusy.value = false
  }
}

async function enterNativeCustomMode() {
  mcpBusy.value = true
  try {
    const result = await companion.enterNativeCustomMode()
    if (
      result.status !== 'verified'
      || result.action !== 'enter_coat_of_arms_custom_mode'
      || result.postcondition_verified !== true
      || result.after?.route !== 'coat_of_arms_designer'
      || result.after_inspection?.scope_root_name !== 'coat_of_arms_page'
      || result.after_inspection?.root_available !== true
    ) {
      throw new Error('MCP 未证明 CK3 自定义家徽背景页已经物化')
    }
    mcpStatus.value = `原生自定义背景已就绪 · ${result.after_inspection.widget_count} widgets`
    ElMessage.success('CK3 已通过固定原生动作进入自定义模式')
  } catch (error) {
    mcpStatus.value = '进入自定义模式失败'
    ElMessage.error(`原生自定义模式失败：${errorMessage(error)}`)
  } finally {
    mcpBusy.value = false
  }
}

async function commitNativeDesign() {
  mcpBusy.value = true
  try {
    const result = await companion.commitNativeDesign()
    if (
      result.status !== 'verified'
      || result.action !== 'commit_dynasty_coat_of_arms'
      || result.postcondition_verified !== true
      || result.after?.route !== 'ruler_designer'
    ) {
      throw new Error('MCP 未证明家徽已提交回角色设计器')
    }
    mcpStatus.value = '家徽已提交回角色设计器'
    ElMessage.success('CK3 已通过原生 Finish 提交王朝家徽')
  } catch (error) {
    mcpStatus.value = '提交失败'
    ElMessage.error(`MCP 提交失败：${errorMessage(error)}`)
  } finally {
    mcpBusy.value = false
  }
}

async function loadRuntimeFeatures() {
  runtimeFeatureBusy.value = true
  runtimeEnabledFeatureCount.value = null
  runtimeFeatureCount.value = null
  runtimeDlcKeys.value = null
  try {
    const revision = await getCurrentGameplayRevision()
    const result = await companion.runtimeFeatures(revision)
    if (result.status !== 'available') {
      runtimeFeatureStatus.value = `不可用 · ${result.unavailable_reason ?? 'unknown'}`
      ElMessage.warning(`CK3 运行态 feature 不可用：${result.unavailable_reason ?? 'unknown'}`)
      return
    }
    const features = result.effective_feature_flags.items ?? []
    runtimeEnabledFeatureCount.value = features.filter((item) => item.enabled).length
    runtimeFeatureCount.value = result.effective_feature_flags.native_count
    runtimeDlcKeys.value = result.script_dlc_keys.keys
    runtimeFeatureStatus.value = `可用 · revision ${revision}`
    ElMessage.success('已读取 CK3 当前进程的 feature 与 script DLC truth')
  } catch (error) {
    runtimeFeatureStatus.value = '请求失败'
    ElMessage.error(`运行态 feature 读取失败：${errorMessage(error)}`)
  } finally {
    runtimeFeatureBusy.value = false
  }
}

async function probeInCk3(apply: boolean) {
  if (errorCount.value > 0) {
    ElMessage.error('请先修复解析错误，再发送确定性导出')
    return
  }
  mcpBusy.value = true
  try {
    const revision = await getCurrentCoaRevision()
    const result = await companion.probe(output.value, revision, apply)
    mcpStatus.value = `${result.status} · revision ${revision}`
    if (result.status === 'detected' || result.status === 'applied') {
      ElMessage.success(apply ? 'CK3 原生设计器已应用候选纹章' : 'CK3 原生 reader 已识别此纹章')
    } else {
      ElMessage.warning(`CK3 返回 ${result.status}${result.reason ? `：${result.reason}` : ''}`)
    }
  } catch (error) {
    mcpStatus.value = '请求失败'
    ElMessage.error(`MCP 请求失败：${errorMessage(error)}`)
  } finally {
    mcpBusy.value = false
  }
}

async function exportFromCk3() {
  mcpBusy.value = true
  try {
    const revision = await getCurrentCoaRevision()
    const result = await companion.exportSource(revision)
    mcpStatus.value = `${result.status} · revision ${revision}`
    if (result.status !== 'exported' || !result.source) {
      ElMessage.warning(`CK3 导出不可用${result.reason ? `：${result.reason}` : ''}`)
      return
    }
    source.value = result.source
    importSource()
    ElMessage.success('已从 CK3 原生 Copy 结果载入编辑器')
  } catch (error) {
    mcpStatus.value = '请求失败'
    ElMessage.error(`CK3 导出失败：${errorMessage(error)}`)
  } finally {
    mcpBusy.value = false
  }
}

async function loadResourceCatalog() {
  catalogBusy.value = true
  try {
    const [
      patterns,
      emblems,
      renderSupport,
      loadConfiguration,
      installedDlcSources,
      configuredPatterns,
      configuredEmblems,
    ] = await Promise.all([
      companion.resources({ kind: 'pattern', limit: 200 }),
      companion.resources({
        kind: 'colored_emblem',
        query: emblemSearch.value.trim() || undefined,
        limit: 200,
      }),
      companion.renderSupport(),
      companion.loadConfiguration().catch(() => null),
      companion.installedDlcSources().catch(() => null),
      companion.configuredResources({ kind: 'pattern', limit: 200 }).catch(() => null),
      companion.configuredResources({
        kind: 'colored_emblem',
        query: emblemSearch.value.trim() || undefined,
        limit: 200,
      }).catch(() => null),
    ])
    patternResources.value = patterns.items
    emblemResources.value = emblems.items
    configuredModCount.value = loadConfiguration?.enabled_mod_count ?? null
    installedDlcDescriptorCount.value = installedDlcSources?.installed_descriptor_count ?? null
    dlcCoaSourceCount.value = installedDlcSources?.dlc_with_coa_candidates ?? null
    configuredPatternCount.value = configuredPatterns?.total ?? null
    configuredEmblemCount.value = configuredEmblems?.total ?? null
    configuredPatternResources.value = configuredPatterns?.items ?? []
    configuredEmblemResources.value = configuredEmblems?.items ?? []
    configuredArchiveCount.value = Math.max(
      configuredPatterns?.provenance.archive_mods_enumerated ?? 0,
      configuredEmblems?.provenance.archive_mods_enumerated ?? 0,
    )
    const decodedSurfaceMask = decodeDdsBase64(renderSupport.surface_mask.asset_base64)
    if (
      decodedSurfaceMask.width !== renderSupport.surface_mask.dds.width
      || decodedSurfaceMask.height !== renderSupport.surface_mask.dds.height
      || decodedSurfaceMask.fourCC !== renderSupport.surface_mask.dds.format
    ) throw new Error('CoA surface mask 元数据与解码结果不一致')
    surfaceMask.value = decodedSurfaceMask
    const decodedTexturedDefault = decodeDdsBase64(
      renderSupport.textured_emblem_default.asset_base64,
    )
    if (
      decodedTexturedDefault.width !== renderSupport.textured_emblem_default.dds.width
      || decodedTexturedDefault.height !== renderSupport.textured_emblem_default.dds.height
      || decodedTexturedDefault.fourCC !== renderSupport.textured_emblem_default.dds.format
    ) throw new Error('Textured emblem 默认 DDS 元数据与解码结果不一致')
    texturedDefaultPreviewUrl.value = decodedDdsToDataUrl(decodedTexturedDefault)
    shaderNamedColors.value = Object.fromEntries(
      renderSupport.named_colors.map((item) => [item.name, item.rgb]),
    )
    const sources = renderSupport.provenance.shader_sources
    shaderSourceCount.value = Array.isArray(sources) ? sources.length : 0
    ElMessage.success(`已索引 ${patterns.returned} 个 pattern、${emblems.returned} 个 emblem，并绑定原版 shader`)
    await loadCurrentTexturePreviews()
  } catch (error) {
    ElMessage.error(`资源目录读取失败：${errorMessage(error)}`)
  } finally {
    catalogBusy.value = false
  }
}

async function readTexturePreview(
  kind: 'pattern' | 'colored_emblem',
  name: string,
): Promise<{ decoded: DecodedDds, preview: string }> {
  const asset = await companion.asset(kind, name)
  const decoded = decodeDdsBase64(asset.asset_base64)
  if (
    decoded.width !== asset.dds.width
    || decoded.height !== asset.dds.height
    || decoded.fourCC !== asset.dds.format
  ) {
    throw new Error(`DDS 元数据与解码结果不一致：${name}`)
  }
  return { decoded, preview: decodedDdsToDataUrl(decoded) }
}

async function readConfiguredTexturePreview(
  item: CoatOfArmsConfiguredResourceItem,
): Promise<{ decoded: DecodedDds, preview: string }> {
  if (item.kind !== 'pattern' && item.kind !== 'colored_emblem') {
    throw new Error(`不支持的 configured DDS 类型：${item.kind}`)
  }
  const asset = await companion.configuredAsset(item.kind, item.candidate_id)
  const decoded = decodeDdsBase64(asset.asset_base64)
  if (
    decoded.width !== asset.dds.width
    || decoded.height !== asset.dds.height
    || decoded.fourCC !== asset.dds.format
  ) {
    throw new Error(`Configured DDS 元数据与解码结果不一致：${item.name}`)
  }
  return { decoded, preview: decodedDdsToDataUrl(decoded) }
}

async function useConfiguredPattern(item: CoatOfArmsConfiguredResourceItem) {
  textureBusy.value = true
  try {
    const { decoded, preview } = await readConfiguredTexturePreview(item)
    coatOfArms.value.pattern = item.name
    patternTexture.value = decoded
    patternPreviewUrl.value = preview
    ElMessage.success(`已使用 ${item.mod_name ?? item.registry_path} 的 pattern 候选`)
  } catch (error) {
    ElMessage.error(`Configured pattern 读取失败：${errorMessage(error)}`)
  } finally {
    textureBusy.value = false
  }
}

async function useConfiguredEmblem(item: CoatOfArmsConfiguredResourceItem) {
  if (!activeEmblem.value) {
    ElMessage.warning('请先添加或选择一个 colored emblem 图层')
    return
  }
  textureBusy.value = true
  try {
    const { decoded, preview } = await readConfiguredTexturePreview(item)
    activeEmblem.value.texture = item.name
    emblemTextures.value = { ...emblemTextures.value, [item.name]: decoded }
    emblemPreviewUrls.value = { ...emblemPreviewUrls.value, [item.name]: preview }
    ElMessage.success(`已使用 ${item.mod_name ?? item.registry_path} 的 emblem 候选`)
  } catch (error) {
    ElMessage.error(`Configured emblem 读取失败：${errorMessage(error)}`)
  } finally {
    textureBusy.value = false
  }
}

async function loadPatternTexture(name: string) {
  if (!name) return
  textureBusy.value = true
  try {
    const { decoded, preview } = await readTexturePreview('pattern', name)
    if (coatOfArms.value.pattern === name) {
      patternTexture.value = decoded
      patternPreviewUrl.value = preview
    }
  } catch (error) {
    patternPreviewUrl.value = ''
    ElMessage.warning(`Pattern 预览读取失败：${errorMessage(error)}`)
  } finally {
    textureBusy.value = false
  }
}

async function loadEmblemTexture(name: string) {
  if (!name) return
  textureBusy.value = true
  try {
    const { decoded, preview } = await readTexturePreview('colored_emblem', name)
    emblemTextures.value = { ...emblemTextures.value, [name]: decoded }
    emblemPreviewUrls.value = { ...emblemPreviewUrls.value, [name]: preview }
  } catch (error) {
    ElMessage.warning(`Emblem 预览读取失败：${errorMessage(error)}`)
  } finally {
    textureBusy.value = false
  }
}

async function loadCurrentTexturePreviews() {
  textureBusy.value = true
  const names = [...new Set(coatOfArms.value.coloredEmblems
    .map((emblem) => emblem.texture)
    .filter(Boolean))]
  try {
    const requests: Promise<void>[] = []
    if (coatOfArms.value.pattern) {
      requests.push(readTexturePreview('pattern', coatOfArms.value.pattern).then(({ decoded, preview }) => {
        patternTexture.value = decoded
        patternPreviewUrl.value = preview
      }))
    }
    for (const name of names) {
      requests.push(readTexturePreview('colored_emblem', name).then(({ decoded, preview }) => {
        emblemTextures.value = { ...emblemTextures.value, [name]: decoded }
        emblemPreviewUrls.value = { ...emblemPreviewUrls.value, [name]: preview }
      }))
    }
    const results = await Promise.allSettled(requests)
    const failed = results.filter((result) => result.status === 'rejected').length
    if (failed) ElMessage.warning(`${failed} 个纹理没有生成浏览器预览`)
  } finally {
    textureBusy.value = false
  }
}

importSource()
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Crusader Kings III · MCP-first</p>
        <h1>家徽工坊</h1>
        <p class="subtitle">结构化编辑原版可导入的静态纹章数据，不执行任意 CK3 脚本。</p>
      </div>
      <div class="top-actions">
        <el-tag :type="mcpStatus.startsWith('已连接') ? 'success' : 'info'" effect="plain">
          {{ mcpStatus }}
        </el-tag>
        <el-button @click="reset">重置</el-button>
        <el-button type="primary" :disabled="errorCount > 0" @click="copyOutput">复制 CK3 代码</el-button>
      </div>
    </header>

    <main class="workspace">
      <section class="source-pane panel">
        <div class="panel-title">
          <div>
            <span class="step">01</span>
            <h2>导入代码</h2>
          </div>
          <div class="source-actions">
            <el-button :loading="clipboardBusy" @click="pasteSource">从剪贴板粘贴</el-button>
            <el-button text link type="primary" @click="loadSample">载入实机样例</el-button>
          </div>
        </div>
        <el-input v-model="source" type="textarea" :rows="21" resize="none" spellcheck="false" class="code-input" />
        <el-button class="import-button" type="primary" @click="importSource">解析并载入</el-button>

        <div class="mcp-panel">
          <div class="section-heading">
            <div>
              <h3>CK3 原生 MCP</h3>
              <small>只调用 typed MCP，不使用 OCR 或屏幕自动化</small>
            </div>
            <el-button size="small" :loading="mcpBusy" @click="refreshSession">连接</el-button>
          </div>
          <div class="mcp-actions">
            <el-button :loading="mcpBusy" @click="openNativeDesigner">打开原生家徽页</el-button>
            <el-button :loading="mcpBusy" @click="enterNativeCustomMode">进入原生自定义模式</el-button>
            <el-button :loading="mcpBusy" :disabled="errorCount > 0" @click="probeInCk3(false)">原生检测</el-button>
            <el-button type="primary" plain :loading="mcpBusy" :disabled="errorCount > 0" @click="probeInCk3(true)">应用到设计器</el-button>
            <el-button :loading="mcpBusy" @click="exportFromCk3">从 CK3 读取</el-button>
            <el-button type="success" plain :loading="mcpBusy" @click="commitNativeDesign">提交回角色设计器</el-button>
          </div>
          <p>“打开”要求 CK3 已停在角色设计器；“进入自定义模式”只允许原版两个固定按钮，并以背景图案网格可见作为后置条件。检测和应用要求已进入家徽页。“应用”只改变家徽页 working state；“提交”调用原生王朝 Finish 并验证返回角色设计器，但仍不等于完成整个角色创建。</p>
        </div>

        <div v-if="visibleDiagnostics.length" class="diagnostics">
          <div v-for="(item, index) in visibleDiagnostics" :key="index" :class="['diagnostic', item.severity]">
            <span>{{ item.severity.toUpperCase() }}</span>
            <p>{{ item.message }}<small v-if="item.line">（{{ item.line }}:{{ item.column }}）</small></p>
          </div>
        </div>
        <el-empty v-else description="没有解析诊断" :image-size="46" />

        <el-collapse class="syntax-capabilities">
          <el-collapse-item title="CK3 1.19.0.6 剪贴板语法能力矩阵" name="syntax-capabilities">
            <p class="capability-note">
              这里只列 MCP 实机矩阵已有证据的语法；“detected”仅表示 reader 产生预览，不等于脚本执行或资源存在。
            </p>
            <el-table :data="syntaxCapabilityRows" size="small" max-height="420">
              <el-table-column label="分类" width="112">
                <template #default="{ row }">
                  <el-tag
                    size="small"
                    effect="plain"
                    :type="row.classification === 'supported' ? 'success' : row.classification === 'ambiguous' ? 'warning' : 'danger'"
                  >
                    {{ row.classification === 'supported' ? '可导入' : row.classification === 'ambiguous' ? '有歧义' : '不可执行' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="syntax" label="语法" min-width="190" show-overflow-tooltip />
              <el-table-column label="例子" min-width="250">
                <template #default="{ row }"><code>{{ row.example }}</code></template>
              </el-table-column>
              <el-table-column prop="engineOutcome" label="原生结果" min-width="170" show-overflow-tooltip />
              <el-table-column prop="editorPolicy" label="编辑器策略" width="105" />
              <el-table-column prop="note" label="边界" min-width="250" show-overflow-tooltip />
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </section>

      <section class="preview-pane panel">
        <div class="panel-title">
          <div><span class="step">02</span><h2>构图预览</h2></div>
          <el-tag effect="plain" :type="renderedPreviewUrl ? 'success' : 'warning'">
            {{ renderedPreviewUrl ? `原版 shader 源码模型 · ${shaderSourceCount} 源文件` : '浏览器几何近似' }}
          </el-tag>
        </div>
        <div class="preview-stage">
          <div :class="['shield', { 'shader-bound': renderedPreviewUrl }]" :style="{ '--shield-color': cssColor(coatOfArms.colors[0]) }">
            <img v-if="renderedPreviewUrl" class="shader-preview" :src="renderedPreviewUrl" alt="原版 shader 源码模型预览" />
            <template v-else>
              <img v-if="patternPreviewUrl" class="pattern-texture" :src="patternPreviewUrl" alt="原版 pattern DDS 通道图" />
              <div class="shield-light" :style="{ background: cssColor(coatOfArms.colors[1]) }" />
              <div
                v-for="(emblem, emblemIndex) in coatOfArms.coloredEmblems"
                :key="`${emblem.texture}-${emblemIndex}`"
                class="emblem-group"
              >
                <template v-for="(instance, instanceIndex) in emblem.instances" :key="instanceIndex">
                  <img
                    v-if="emblemPreviewUrls[emblem.texture]"
                    class="emblem-texture"
                    :src="emblemPreviewUrls[emblem.texture]"
                    :alt="emblem.texture"
                    :style="{
                      left: `${instance.position[0] * 100}%`,
                      top: `${instance.position[1] * 100}%`,
                      transform: `translate(-50%, -50%) rotate(${instance.rotation}deg) scale(${instance.scale[0]}, ${instance.scale[1]})`,
                      zIndex: Math.round(instance.depth * 10),
                    }"
                    :title="emblem.texture"
                  />
                  <div
                    v-else
                    class="emblem-glyph"
                    :style="{
                      left: `${instance.position[0] * 100}%`,
                      top: `${instance.position[1] * 100}%`,
                      color: cssColor(emblem.colors[0]),
                      transform: `translate(-50%, -50%) rotate(${instance.rotation}deg) scale(${instance.scale[0]}, ${instance.scale[1]})`,
                      zIndex: Math.round(instance.depth * 10),
                    }"
                    :title="emblem.texture"
                  >✦</div>
                </template>
              </div>
            </template>
          </div>
        </div>
        <div class="preview-caption">
          <strong>{{ coatOfArms.pattern || '未指定 pattern' }}</strong>
          <span>{{ coatOfArms.coloredEmblems.length }} 个彩色图层 · {{ coatOfArms.coloredEmblems.reduce((sum, item) => sum + item.instances.length, 0) }} 个实例 · {{ coatOfArms.texturedEmblems.length }} 个受限纹理层</span>
        </div>
        <el-button class="preview-load" :loading="textureBusy" @click="loadCurrentTexturePreviews">加载当前原版 DDS</el-button>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>预览翻译 exact 1.19.0.6 随附 shader 的通道、mask、transform、surface detail 与 blend；FallbackColor 绑定、GPU 采样/色彩空间仍待以后原生像素对照。</template>
        </el-alert>
      </section>

      <section class="editor-pane panel">
        <div class="panel-title">
          <div><span class="step">03</span><h2>结构化编辑</h2></div>
          <el-space>
            <el-button size="small" :loading="runtimeFeatureBusy" @click="loadRuntimeFeatures">读取运行态</el-button>
            <el-button size="small" :loading="catalogBusy" @click="loadResourceCatalog">读取资源</el-button>
          </el-space>
        </div>
        <el-scrollbar height="690px">
          <div class="resource-search">
            <el-input v-model="emblemSearch" clearable placeholder="筛选 emblem 名；留空取前 200 项" @keyup.enter="loadResourceCatalog" />
            <el-button :loading="catalogBusy" @click="loadResourceCatalog">刷新目录</el-button>
          </div>
          <p class="resource-note">
            目录只证明 exact 1.19.0.6 基础游戏磁盘资源；
            <template v-if="installedDlcDescriptorCount !== null && dlcCoaSourceCount !== null">
              安装树含 {{ installedDlcDescriptorCount }} 份 DLC 描述符，其中 {{ dlcCoaSourceCount }} 份有直接 CoA 候选；
              该数字不证明商店授权或引擎 mount。
            </template>
            <template v-if="configuredModCount !== null">
              `dlc_load.json` 当前配置 {{ configuredModCount }} 个 mod；
              <template v-if="configuredPatternCount !== null && configuredEmblemCount !== null">
                已枚举 {{ configuredPatternCount }} 个 pattern、{{ configuredEmblemCount }} 个 emblem 资源候选，
                其中读取 {{ configuredArchiveCount }} 个 archive mod。
              </template>
              仍未应用资源 precedence/merge，也不冒充引擎 mount 状态。
            </template>
            <template v-else>
              启动配置未读取，暂不包含 DLC/mod 覆盖，也不冒充运行时注册状态。
            </template>
            <br>
            CK3 运行态：{{ runtimeFeatureStatus }}。
            <template v-if="runtimeEnabledFeatureCount !== null && runtimeFeatureCount !== null && runtimeDlcKeys !== null">
              原生同帧读到 {{ runtimeEnabledFeatureCount }}/{{ runtimeFeatureCount }} 个 effective feature 为真，
              `has_dlc` 可见 {{ runtimeDlcKeys.length }} 个 key。
              这证明当前进程的 gameplay gate，不证明商店授权，也不决定同名家徽资源的最终胜者。
            </template>
          </p>
          <el-collapse
            v-if="configuredPatternResources.length || configuredEmblemResources.length"
            class="configured-candidates"
          >
            <el-collapse-item
              v-if="configuredPatternResources.length"
              :title="`Configured pattern 候选（当前页 ${configuredPatternResources.length}）`"
              name="configured-patterns"
            >
              <p class="candidate-warning">
                显式选择只决定本编辑器使用哪份 DDS 做预览；导出的 CK3 代码仍只包含资源名，不声明引擎最终胜者。
              </p>
              <el-table :data="configuredPatternResources" size="small" max-height="220">
                <el-table-column prop="name" label="资源名" min-width="180" show-overflow-tooltip />
                <el-table-column prop="mod_name" label="来源 mod" min-width="150" show-overflow-tooltip />
                <el-table-column label="冲突" width="82">
                  <template #default="{ row }">
                    <el-tag v-if="row.potential_configured_name_conflict" type="warning" size="small">
                      {{ row.same_name_configured_candidate_count }} 项
                    </el-tag>
                    <span v-else>—</span>
                  </template>
                </el-table-column>
                <el-table-column label="" width="82" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" text type="primary" @click="useConfiguredPattern(row)">使用</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
            <el-collapse-item
              v-if="configuredEmblemResources.length"
              :title="`Configured emblem 候选（当前页 ${configuredEmblemResources.length}）`"
              name="configured-emblems"
            >
              <p class="candidate-warning">
                选择后写入当前 emblem 图层，并按该 opaque candidate ID 读取目录/ZIP 内的精确 DDS。
              </p>
              <el-table :data="configuredEmblemResources" size="small" max-height="260">
                <el-table-column prop="name" label="资源名" min-width="180" show-overflow-tooltip />
                <el-table-column prop="mod_name" label="来源 mod" min-width="150" show-overflow-tooltip />
                <el-table-column label="冲突" width="82">
                  <template #default="{ row }">
                    <el-tag v-if="row.potential_configured_name_conflict" type="warning" size="small">
                      {{ row.same_name_configured_candidate_count }} 项
                    </el-tag>
                    <span v-else>—</span>
                  </template>
                </el-table-column>
                <el-table-column label="" width="82" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" text type="primary" @click="useConfiguredEmblem(row)">使用</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
          <el-form label-position="top">
            <div class="form-grid">
              <el-form-item label="Parent 引用（可选）">
                <el-input v-model="coatOfArms.parent" placeholder="c_england" />
              </el-form-item>
              <el-form-item label="Pattern 资源名">
                <el-select v-model="coatOfArms.pattern" filterable allow-create default-first-option @change="loadPatternTexture">
                  <el-option
                    v-for="item in patternResources"
                    :key="item.name"
                    :label="`${item.name} · ${item.colors ?? '?'} 色`"
                    :value="item.name"
                  />
                </el-select>
              </el-form-item>
              <el-form-item v-for="index in 3" :key="index" :label="`底色 ${index}`">
                <el-input v-model="coatOfArms.colors[index - 1]" />
              </el-form-item>
            </div>

            <div class="section-heading">
              <h3>Colored emblems</h3>
              <el-button size="small" type="primary" plain @click="addEmblem">添加图层</el-button>
            </div>
            <el-tabs v-if="coatOfArms.coloredEmblems.length" v-model="selectedEmblem" type="card">
              <el-tab-pane v-for="(emblem, index) in coatOfArms.coloredEmblems" :key="index" :label="`图层 ${index + 1}`" :name="index" />
            </el-tabs>

            <template v-if="activeEmblem">
              <div class="form-grid">
                <el-form-item label="Texture 资源名" class="wide">
                  <el-select v-model="activeEmblem.texture" filterable allow-create default-first-option @change="loadEmblemTexture">
                    <el-option
                      v-for="item in emblemResources"
                      :key="item.name"
                      :label="`${item.name} · ${item.colors ?? '?'} 色`"
                      :value="item.name"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item v-for="index in 3" :key="index" :label="`图案颜色 ${index}`">
                  <el-input v-model="activeEmblem.colors[index - 1]" />
                </el-form-item>
                <el-form-item label="Mask（空格分隔）">
                  <el-input :model-value="activeEmblem.mask.join(' ')" @update:model-value="parseMask" />
                </el-form-item>
              </div>

              <div class="instance-list">
                <div v-for="(instance, index) in activeEmblem.instances" :key="index" class="instance-card">
                  <div class="instance-title">
                    <strong>实例 {{ index + 1 }}</strong>
                    <el-button link type="danger" @click="activeEmblem.instances.splice(index, 1)">删除</el-button>
                  </div>
                  <div class="number-grid">
                    <el-form-item label="X"><el-input-number v-model="instance.position[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Y"><el-input-number v-model="instance.position[1]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale X"><el-input-number v-model="instance.scale[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale Y"><el-input-number v-model="instance.scale[1]" :step="0.05" /></el-form-item>
                    <el-form-item label="Rotation"><el-input-number v-model="instance.rotation" :step="5" /></el-form-item>
                    <el-form-item label="Depth"><el-input-number v-model="instance.depth" :step="0.01" /></el-form-item>
                  </div>
                </div>
              </div>
              <div class="row-actions">
                <el-button @click="activeEmblem.instances.push(createInstance())">添加实例</el-button>
                <el-button type="danger" plain @click="removeEmblem(selectedEmblem)">删除当前图层</el-button>
              </div>
            </template>

            <div class="section-heading textured-heading">
              <h3>Textured emblems（受限）</h3>
              <el-button size="small" plain @click="coatOfArms.texturedEmblems.push(createTexturedEmblem())">
                添加受限层
              </el-button>
            </div>
            <el-alert type="warning" :closable="false" show-icon>
              <template #title>
                当前实机已证明 `textured_emblem = { texture = "_default.dds" }` 可应用且由原生 Copy 保留；本区只保真解析/导出 texture，
                不为未验证字段生成 UI；行内只显示 exact 原始 DDS，不冒充最终合成预览。
              </template>
            </el-alert>
            <div v-if="coatOfArms.texturedEmblems.length" class="textured-list">
              <div
                v-for="(emblem, index) in coatOfArms.texturedEmblems"
                :key="index"
                class="textured-row"
              >
                <img
                  v-if="emblem.texture === '_default.dds' && texturedDefaultPreviewUrl"
                  :src="texturedDefaultPreviewUrl"
                  alt="_default.dds 原始纹理"
                  class="textured-raw-preview"
                />
                <div v-else class="textured-preview-placeholder">?</div>
                <el-input v-model="emblem.texture" placeholder="_default.dds" />
                <el-button
                  type="danger"
                  plain
                  @click="coatOfArms.texturedEmblems.splice(index, 1)"
                >删除</el-button>
              </div>
            </div>
          </el-form>

          <div class="output-block">
            <div class="section-heading"><h3>确定性导出</h3><el-tag>CRLF</el-tag></div>
            <pre>{{ output }}</pre>
          </div>
        </el-scrollbar>
      </section>
    </main>
  </div>
</template>
