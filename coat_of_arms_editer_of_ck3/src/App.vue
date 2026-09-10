<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createCk3CompanionClient,
  type CoatOfArmsResourceItem,
} from './api/ck3Companion'
import { decodeDdsBase64, decodedDdsToDataUrl, type DecodedDds } from './domain/dds'
import { parseCoatOfArms } from './domain/parser'
import {
  renderCoatOfArms,
  renderedCoatOfArmsToDataUrl,
  resolveColor,
  type NamedColorMap,
} from './domain/renderer'
import { serializeCoatOfArms } from './domain/serializer'
import {
  createCoatOfArms,
  createColoredEmblem,
  createInstance,
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
const mcpStatus = ref('未连接')
const patternResources = ref<CoatOfArmsResourceItem[]>([])
const emblemResources = ref<CoatOfArmsResourceItem[]>([])
const emblemSearch = ref('')
const patternPreviewUrl = ref('')
const emblemPreviewUrls = ref<Record<string, string>>({})
const patternTexture = ref<DecodedDds>()
const emblemTextures = ref<Record<string, DecodedDds>>({})
const surfaceMask = ref<DecodedDds>()
const shaderNamedColors = ref<NamedColorMap>({})
const shaderSourceCount = ref(0)

const output = computed(() => serializeCoatOfArms(coatOfArms.value))
const activeEmblem = computed(() => coatOfArms.value.coloredEmblems[selectedEmblem.value])
const errorCount = computed(() => diagnostics.value.filter((item) => item.severity === 'error').length)
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
  await navigator.clipboard.writeText(output.value)
  ElMessage.success('CK3 纹章代码已复制；多行换行使用 CRLF')
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
  activeEmblem.value.mask = value.split(/[\s,]+/).map(Number).filter(Number.isFinite)
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

async function getCurrentRevision(): Promise<number> {
  const snapshot = await companion.session()
  if (!Number.isSafeInteger(snapshot.revision) || snapshot.revision < 0) {
    throw new Error('MCP snapshot 没有有效 revision')
  }
  mcpStatus.value = `已连接 · revision ${snapshot.revision}`
  return snapshot.revision
}

async function refreshSession() {
  mcpBusy.value = true
  try {
    await getCurrentRevision()
    ElMessage.success('已连接本机 CK3 MCP')
  } catch (error) {
    mcpStatus.value = '不可用'
    ElMessage.error(`MCP 连接失败：${errorMessage(error)}`)
  } finally {
    mcpBusy.value = false
  }
}

async function probeInCk3(apply: boolean) {
  if (errorCount.value > 0) {
    ElMessage.error('请先修复解析错误，再发送确定性导出')
    return
  }
  mcpBusy.value = true
  try {
    const revision = await getCurrentRevision()
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
    const revision = await getCurrentRevision()
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
    const [patterns, emblems, renderSupport] = await Promise.all([
      companion.resources({ kind: 'pattern', limit: 200 }),
      companion.resources({
        kind: 'colored_emblem',
        query: emblemSearch.value.trim() || undefined,
        limit: 200,
      }),
      companion.renderSupport(),
    ])
    patternResources.value = patterns.items
    emblemResources.value = emblems.items
    const decodedSurfaceMask = decodeDdsBase64(renderSupport.surface_mask.asset_base64)
    if (
      decodedSurfaceMask.width !== renderSupport.surface_mask.dds.width
      || decodedSurfaceMask.height !== renderSupport.surface_mask.dds.height
      || decodedSurfaceMask.fourCC !== renderSupport.surface_mask.dds.four_cc
    ) throw new Error('CoA surface mask 元数据与解码结果不一致')
    surfaceMask.value = decodedSurfaceMask
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
    || decoded.fourCC !== asset.dds.four_cc
  ) {
    throw new Error(`DDS 元数据与解码结果不一致：${name}`)
  }
  return { decoded, preview: decodedDdsToDataUrl(decoded) }
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
          <el-button text link type="primary" @click="loadSample">载入实机样例</el-button>
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
            <el-button :loading="mcpBusy" :disabled="errorCount > 0" @click="probeInCk3(false)">原生检测</el-button>
            <el-button type="primary" plain :loading="mcpBusy" :disabled="errorCount > 0" @click="probeInCk3(true)">应用到设计器</el-button>
            <el-button :loading="mcpBusy" @click="exportFromCk3">从 CK3 读取</el-button>
          </div>
          <p>检测和应用需要 CK3 已停在纹章设计器；“应用”只改变 working state，不等于上层保存。</p>
        </div>

        <div v-if="diagnostics.length" class="diagnostics">
          <div v-for="(item, index) in diagnostics" :key="index" :class="['diagnostic', item.severity]">
            <span>{{ item.severity.toUpperCase() }}</span>
            <p>{{ item.message }}<small v-if="item.line">（{{ item.line }}:{{ item.column }}）</small></p>
          </div>
        </div>
        <el-empty v-else description="没有解析诊断" :image-size="46" />
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
          <span>{{ coatOfArms.coloredEmblems.length }} 个彩色图层 · {{ coatOfArms.coloredEmblems.reduce((sum, item) => sum + item.instances.length, 0) }} 个实例</span>
        </div>
        <el-button class="preview-load" :loading="textureBusy" @click="loadCurrentTexturePreviews">加载当前原版 DDS</el-button>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>预览翻译 exact 1.19.0.6 随附 shader 的通道、mask、transform、surface detail 与 blend；FallbackColor 绑定、GPU 采样/色彩空间仍待以后原生像素对照。</template>
        </el-alert>
      </section>

      <section class="editor-pane panel">
        <div class="panel-title">
          <div><span class="step">03</span><h2>结构化编辑</h2></div>
          <el-button size="small" :loading="catalogBusy" @click="loadResourceCatalog">读取原版资源</el-button>
        </div>
        <el-scrollbar height="690px">
          <div class="resource-search">
            <el-input v-model="emblemSearch" clearable placeholder="筛选 emblem 名；留空取前 200 项" @keyup.enter="loadResourceCatalog" />
            <el-button :loading="catalogBusy" @click="loadResourceCatalog">刷新目录</el-button>
          </div>
          <p class="resource-note">
            目录只证明 exact 1.19.0.6 基础游戏磁盘资源；暂不包含 DLC/mod 覆盖，也不冒充运行时注册状态。
          </p>
          <el-form label-position="top">
            <div class="form-grid">
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
