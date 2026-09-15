<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createCk3CompanionClient,
  type CoatOfArmsConfiguredResourceItem,
  type CoatOfArmsResourceItem,
} from './api/ck3Companion'
import { decodeDdsBase64, decodedDdsToDataUrl, type DecodedDds } from './domain/dds'
import {
  loadWebAssetPack,
  readWebAsset,
  readWebFitIndex,
  type LoadedWebAssetPack,
  type WebAssetPackEntry,
} from './domain/assetPack'
import { syntaxCapabilityRows } from './domain/capabilityMatrix'
import {
  structurallyCompressCoatOfArms,
  type StructuralCompressionReceipt,
} from './domain/coatOfArmsOptimizer'
import type {
  InstancePruneProgress,
  InstancePruneReceipt,
  InstancePruneResult,
} from './domain/coatOfArmsPruner'
import { decodeFitImageFile, type DecodedFitImage } from './domain/imageInput'
import {
  resizeFitImage,
  type FitImage,
  type FitTextureCandidate,
  type ImageFitProgress,
  type ImageFitResult,
} from './domain/imageFitter'
import { parseCoatOfArms } from './domain/parser'
import {
  createCoatOfArmsProject,
  parseCoatOfArmsProject,
  serializeCoatOfArmsProject,
} from './domain/projectDocument'
import {
  renderCoatOfArms,
  renderedCoatOfArmsToDataUrl,
  resolveColor,
  type NamedColorMap,
} from './domain/renderer'
import { COAT_OF_ARMS_MCP_MAX_BYTES, serializeCoatOfArms } from './domain/serializer'
import { validateCoatOfArms } from './domain/validation'
import { scoreWithWebGl2, type WebGlScore } from './domain/webglScorer'
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
const projectFileBusy = ref(false)
const projectFileInput = ref<HTMLInputElement>()
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
const developmentCompanionEnabled = import.meta.env.VITE_ENABLE_CK3_COMPANION === 'true'
const defaultAssetPackUrl = import.meta.env.VITE_COA_ASSET_PACK_URL
  || `${import.meta.env.BASE_URL}asset-packs/ck3-1.19.0.6/manifest.json`
const loadedAssetPack = ref<LoadedWebAssetPack>()
const assetPackBusy = ref(false)
const assetPackStatus = ref('尚未载入独立素材包')
const webAssetCache = new Map<string, DecodedDds>()
const targetImage = ref<DecodedFitImage>()
const fitBusy = ref(false)
const fitStatus = ref('请选择一张图片')
const fitResult = ref<ImageFitResult>()
const fitWebGlScore = ref<WebGlScore | null>(null)
const fitPreviewUrl = ref('')
const fitLayerBudget = ref(6)
const fitProgressPercent = ref(0)
const fitProgressLabel = ref('等待开始')
const fitCompressionEvidence = ref<{
  receipt: StructuralCompressionReceipt
  pixelExactResolutions: number[]
}>()
const fitCompressionSource = ref('')
const fitPruneBusy = ref(false)
const fitPruneProgress = ref<InstancePruneProgress>()
const fitPruneEvidence = ref<InstancePruneReceipt>()
const fitPruneSource = ref('')
let fitWorker: Worker | null = null
let fitRunId = 0
let fitPruneWorker: Worker | null = null
let fitPruneRunId = 0
const INSTANCE_EDITOR_WINDOW_SIZE = 32
const OUTPUT_PREVIEW_CHARACTER_LIMIT = 64 * 1024
const instanceWindowStart = ref(0)

const fitTerminationLabels: Record<ImageFitResult['provenance']['terminationReason'], string> = {
  layer_budget: '达到用户搜索预算',
  exact_match: '残差已归零',
  no_emblems: '素材包没有可用徽记',
  no_improvement: '没有继续改善的构图',
  minimum_improvement: '改善低于阈值',
}

const output = computed(() => serializeCoatOfArms(coatOfArms.value))
const outputBytes = computed(() => new TextEncoder().encode(output.value).length)
const outputLines = computed(() => output.value ? (output.value.match(/\n/g)?.length ?? 0) + 1 : 0)
const outputPreviewTruncated = computed(() => output.value.length > OUTPUT_PREVIEW_CHARACTER_LIMIT)
const outputPreview = computed(() => outputPreviewTruncated.value
  ? `${output.value.slice(0, OUTPUT_PREVIEW_CHARACTER_LIMIT)}\r\n… UI 仅显示前 ${OUTPUT_PREVIEW_CHARACTER_LIMIT.toLocaleString()} 字符；复制和项目保存仍读取完整模型 …`
  : output.value)
const activeFitCompression = computed(() => (
  fitCompressionSource.value === output.value ? fitCompressionEvidence.value : undefined
))
const activeFitPrune = computed(() => (
  fitPruneSource.value === output.value ? fitPruneEvidence.value : undefined
))
const fitEvidenceJson = computed(() => {
  if (!fitResult.value) return ''
  const { layerLosses, selectedAssetSha256, ...provenance } = fitResult.value.provenance
  return JSON.stringify({
    metrics: fitResult.value.metrics,
    provenance,
    layerLossSummary: {
      count: layerLosses.length,
      first: layerLosses[0],
      last: layerLosses.at(-1),
      strictlyDecreasing: layerLosses.every((loss, index) => index === 0 || loss < layerLosses[index - 1]),
    },
    selectedAssetSha256: [...new Set(selectedAssetSha256)],
    structuralCompression: activeFitCompression.value ?? null,
    exactInstancePrune: activeFitPrune.value
      ? {
          contract: activeFitPrune.value.contract,
          drawnInstancesBefore: activeFitPrune.value.drawnInstancesBefore,
          drawnInstancesAfter: activeFitPrune.value.drawnInstancesAfter,
          removedInstances: activeFitPrune.value.removedInstances,
          fixedPointPasses: activeFitPrune.value.fixedPointPasses,
          evaluatedCandidates: activeFitPrune.value.evaluatedCandidates,
          finalNecessityEvidenceCount: activeFitPrune.value.finalNecessityEvidence.length,
        }
      : null,
  })
})
const activeEmblem = computed(() => coatOfArms.value.coloredEmblems[selectedEmblem.value])
const boundedInstanceWindowStart = computed(() => {
  const length = activeEmblem.value?.instances.length ?? 0
  const maximum = Math.max(0, length - INSTANCE_EDITOR_WINDOW_SIZE)
  return Math.min(Math.max(0, Math.floor(instanceWindowStart.value)), maximum)
})
const visibleInstanceItems = computed(() => (activeEmblem.value?.instances ?? [])
  .slice(boundedInstanceWindowStart.value, boundedInstanceWindowStart.value + INSTANCE_EDITOR_WINDOW_SIZE)
  .map((instance, offset) => ({ instance, index: boundedInstanceWindowStart.value + offset })))
const instanceWindowEnd = computed(() => (
  boundedInstanceWindowStart.value + visibleInstanceItems.value.length
))
const fallbackPreviewEmblems = computed(() => {
  let remaining = 512
  return coatOfArms.value.coloredEmblems.flatMap((emblem, emblemIndex) => {
    if (remaining <= 0) return []
    const instances = emblem.instances.slice(0, remaining)
    remaining -= instances.length
    return instances.length ? [{ emblem, emblemIndex, instances }] : []
  })
})
const visibleDiagnostics = computed<Diagnostic[]>(() => {
  const items = [...diagnostics.value, ...validateCoatOfArms(coatOfArms.value)]
  if (outputBytes.value > COAT_OF_ARMS_MCP_MAX_BYTES) {
    items.push({
      severity: 'warning',
      message: '代码超过旧版单请求 MCP v1 的 128 KiB 合同；网页仍允许完整复制，且 380,862-byte hunter 已通过分块 MCP v2 的 CK3 Apply/Copy 实测',
    })
  }
  return items.filter((item, index) => items.findIndex((candidate) => (
    candidate.severity === item.severity && candidate.message === item.message
  )) === index)
})
const errorCount = computed(() => visibleDiagnostics.value.filter((item) => item.severity === 'error').length)
const drawnInstanceCount = computed(() => coatOfArms.value.coloredEmblems.reduce(
  (sum, item) => sum + item.instances.length, 0,
))
const largeDocumentPreviewDeferred = computed(() => drawnInstanceCount.value > 2_048)
const renderedPreviewUrl = computed(() => {
  // A synchronous 10,000-instance canvas redraw on every numeric keystroke
  // blocks the editor for seconds. Large documents therefore keep editing,
  // copying and project persistence live while preview is explicitly deferred.
  if (largeDocumentPreviewDeferred.value) return ''
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

function openProjectFilePicker() {
  projectFileInput.value?.click()
}

function downloadTextFile(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = name
  anchor.click()
  URL.revokeObjectURL(url)
}

async function exportProject() {
  projectFileBusy.value = true
  try {
    const loaded = loadedAssetPack.value
    const project = await createCoatOfArmsProject(coatOfArms.value, {
      selectedEmblem: selectedEmblem.value,
      assetPack: loaded ? {
        packId: loaded.pack.pack_id,
        manifestSha256: loaded.manifestSha256,
        ck3Build: loaded.pack.ck3_build,
      } : undefined,
    })
    downloadTextFile(
      `ck3-coat-of-arms-${new Date().toISOString().replaceAll(':', '-')}.coa-project.json`,
      serializeCoatOfArmsProject(project),
      'application/json;charset=utf-8',
    )
    ElMessage.success(`项目已保存：${project.ck3Source.stats.drawnInstances} 个完整实例`)
  } catch (error) {
    ElMessage.error(`项目保存失败：${errorMessage(error)}`)
  } finally {
    projectFileBusy.value = false
  }
}

async function importProject(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  projectFileBusy.value = true
  try {
    const project = await parseCoatOfArmsProject(await file.text())
    cancelImageFit(false)
    cancelInstancePrune(false)
    coatOfArms.value = project.coatOfArms
    source.value = serializeCoatOfArms(project.coatOfArms)
    diagnostics.value = []
    selectedEmblem.value = project.selectedEmblem
    instanceWindowStart.value = 0
    fitResult.value = undefined
    fitCompressionEvidence.value = undefined
    fitCompressionSource.value = ''
    fitPruneEvidence.value = undefined
    fitPruneSource.value = ''
    fitPreviewUrl.value = ''
    await loadCurrentTexturePreviews()
    ElMessage.success(`项目已恢复：${project.ck3Source.stats.drawnInstances} 个实例，SHA-256 已验证`)
  } catch (error) {
    ElMessage.error(`项目导入失败：${errorMessage(error)}`)
  } finally {
    projectFileBusy.value = false
    input.value = ''
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
  instanceWindowStart.value = 0
}

function addEmblem() {
  coatOfArms.value.coloredEmblems.push(createColoredEmblem())
  selectedEmblem.value = coatOfArms.value.coloredEmblems.length - 1
}

function removeEmblem(index: number) {
  coatOfArms.value.coloredEmblems.splice(index, 1)
  selectedEmblem.value = Math.max(0, Math.min(selectedEmblem.value, coatOfArms.value.coloredEmblems.length - 1))
}

function selectEmblemIndex(index: number) {
  selectedEmblem.value = Math.min(
    Math.max(0, Math.floor(index)),
    Math.max(0, coatOfArms.value.coloredEmblems.length - 1),
  )
}

function moveInstanceWindow(start: number) {
  const length = activeEmblem.value?.instances.length ?? 0
  instanceWindowStart.value = Math.min(
    Math.max(0, Math.floor(start)),
    Math.max(0, length - INSTANCE_EDITOR_WINDOW_SIZE),
  )
}

function addInstanceToActiveEmblem() {
  if (!activeEmblem.value) return
  activeEmblem.value.instances.push(createInstance())
  moveInstanceWindow(activeEmblem.value.instances.length - INSTANCE_EDITOR_WINDOW_SIZE)
}

function removeActiveInstance(index: number) {
  if (!activeEmblem.value) return
  activeEmblem.value.instances.splice(index, 1)
  moveInstanceWindow(boundedInstanceWindowStart.value)
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

function packEntry(kind: 'pattern' | 'colored_emblem', name: string): WebAssetPackEntry | undefined {
  return loadedAssetPack.value?.pack.assets.find((item) => item.kind === kind && item.name === name)
}

function asResourceItem(item: WebAssetPackEntry, index: number): CoatOfArmsResourceItem {
  return {
    index,
    name: item.name,
    colors: item.colors,
    visible: item.visible,
    category: item.category,
    relative_path: item.url,
    asset_exists: true,
    asset_bytes: item.asset_bytes,
    asset_sha256: item.asset_sha256,
  }
}

async function readPackTexture(item: WebAssetPackEntry): Promise<DecodedDds> {
  const cached = webAssetCache.get(item.asset_sha256)
  if (cached) return cached
  if (!loadedAssetPack.value) throw new Error('独立素材包尚未载入')
  const decoded = await readWebAsset(loadedAssetPack.value, item)
  webAssetCache.set(item.asset_sha256, decoded)
  return decoded
}

async function loadStandaloneAssetPack(notify = true) {
  assetPackBusy.value = true
  try {
    const loaded = await loadWebAssetPack(defaultAssetPackUrl)
    const patterns = loaded.pack.assets.filter(
      (item) => item.kind === 'pattern' && item.registration === 'designer_manifest',
    )
    const emblems = loaded.pack.assets.filter(
      (item) => item.kind === 'colored_emblem' && item.registration === 'designer_manifest',
    )
    const mask = loaded.pack.assets.find((item) => item.kind === 'surface_mask')
    if (!patterns.length || !emblems.length || !mask) throw new Error('素材包缺少已注册 pattern、emblem 或 surface mask')
    loadedAssetPack.value = loaded
    webAssetCache.clear()
    patternResources.value = patterns.map(asResourceItem)
    emblemResources.value = emblems.map(asResourceItem)
    shaderNamedColors.value = loaded.pack.named_colors
    surfaceMask.value = await readPackTexture(mask)
    shaderSourceCount.value = 5
    const inventory = loaded.pack.inventory
    assetPackStatus.value = `${loaded.pack.pack_id} · ${patterns.length} 注册 pattern · ${emblems.length} 注册 emblem${inventory ? ` · ${inventory.source_dds_total} DDS 全盘清单` : ''} · ${loaded.manifestSha256.slice(0, 12)}`
    if (notify) ElMessage.success('独立静态素材包已载入；运行时不需要 CK3、MCP 或 Java')
    await loadCurrentTexturePreviews()
  } catch (error) {
    loadedAssetPack.value = undefined
    assetPackStatus.value = `素材包不可用：${errorMessage(error)}`
    if (notify) ElMessage.error(assetPackStatus.value)
  } finally {
    assetPackBusy.value = false
  }
}

async function selectTargetImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  cancelInstancePrune(false)
  cancelImageFit(false)
  fitProgressPercent.value = 0
  fitProgressLabel.value = '等待开始'
  try {
    targetImage.value = await decodeFitImageFile(file)
    fitResult.value = undefined
    fitCompressionEvidence.value = undefined
    fitCompressionSource.value = ''
    fitPruneEvidence.value = undefined
    fitPruneSource.value = ''
    fitWebGlScore.value = null
    fitPreviewUrl.value = ''
    fitStatus.value = `${file.name} · ${targetImage.value.originalWidth}×${targetImage.value.originalHeight} · ${(file.size / 1024).toFixed(1)} KiB · 只在浏览器内处理`
  } catch (error) {
    targetImage.value = undefined
    fitStatus.value = `图片拒绝：${errorMessage(error)}`
    ElMessage.error(fitStatus.value)
  } finally {
    input.value = ''
  }
}

function cancelImageFit(notify = true) {
  fitRunId += 1
  fitWorker?.terminate()
  fitWorker = null
  if (fitBusy.value && notify) ElMessage.info('已取消图片拟合')
  if (fitBusy.value) {
    fitProgressPercent.value = 0
    fitProgressLabel.value = notify ? '已取消' : '等待开始'
  }
  fitBusy.value = false
}

function cancelInstancePrune(notify = true) {
  fitPruneRunId += 1
  fitPruneWorker?.terminate()
  fitPruneWorker = null
  if (fitPruneBusy.value && notify) ElMessage.info('已取消精确剪枝；当前编辑结果保持不变')
  fitPruneBusy.value = false
  fitPruneProgress.value = undefined
}

function cloneDecodedDdsForWorker(texture: DecodedDds): DecodedDds {
  return {
    width: texture.width,
    height: texture.height,
    fourCC: texture.fourCC,
    pixels: new Uint8ClampedArray(texture.pixels),
  }
}

function cloneCoatOfArmsForWorker(value: CoatOfArms): CoatOfArms {
  return {
    outerKey: value.outerKey,
    parent: value.parent,
    pattern: value.pattern,
    colors: [...value.colors],
    coloredEmblems: value.coloredEmblems.map((emblem) => ({
      texture: emblem.texture,
      colors: [...emblem.colors],
      mask: [...emblem.mask],
      instances: emblem.instances.map((instance) => ({
        position: [...instance.position],
        scale: [...instance.scale],
        rotation: instance.rotation,
        depth: instance.depth,
      })),
    })),
    texturedEmblems: value.texturedEmblems.map((emblem) => ({ ...emblem })),
  }
}

function pruneFitDocument() {
  if (!fitResult.value || !targetImage.value || !patternTexture.value) {
    ElMessage.warning('请先完成一次图片拟合并载入结果素材')
    return
  }
  const missing = [...new Set(coatOfArms.value.coloredEmblems.map((item) => item.texture))]
    .filter((name) => !emblemTextures.value[name])
  if (missing.length) {
    ElMessage.error(`无法执行精确剪枝，缺少 ${missing.length} 个结果 DDS`)
    return
  }
  cancelInstancePrune(false)
  const runId = ++fitPruneRunId
  fitPruneBusy.value = true
  fitPruneEvidence.value = undefined
  fitPruneSource.value = ''
  fitPruneProgress.value = {
    pass: 1, completedInPass: 0,
    totalInPass: fitResult.value.provenance.drawnInstances,
    evaluatedCandidates: 0, percent: 0,
  }
  const worker = new Worker(new URL('./domain/coatOfArmsPruner.worker.ts', import.meta.url), { type: 'module' })
  fitPruneWorker = worker
  const fail = (message: string) => {
    if (runId !== fitPruneRunId) return
    worker.terminate()
    fitPruneWorker = null
    fitPruneBusy.value = false
    fitPruneProgress.value = undefined
    ElMessage.error(`精确剪枝 Worker 失败：${message}`)
  }
  worker.onmessage = (event: MessageEvent<
    | { kind: 'progress', progress: InstancePruneProgress }
    | { kind: 'result', ok: boolean, result?: InstancePruneResult, error?: string }
  >) => {
    if (runId !== fitPruneRunId) return
    if (event.data.kind === 'progress') {
      fitPruneProgress.value = event.data.progress
      return
    }
    worker.terminate()
    fitPruneWorker = null
    fitPruneBusy.value = false
    if (!event.data.ok || !event.data.result) {
      fitPruneProgress.value = undefined
      ElMessage.error(`精确剪枝失败：${event.data.error ?? 'unknown'}`)
      return
    }
    const pruned = event.data.result
    const removedIds = new Set(pruned.receipt.removedEvidence.map((item) => item.instanceId))
    const [patternAssetSha256, ...instanceAssetSha256] = fitResult.value!.provenance.selectedAssetSha256
    const retainedAssetSha256 = instanceAssetSha256.length === pruned.receipt.drawnInstancesBefore
      ? instanceAssetSha256.filter((_, index) => !removedIds.has(index))
      : instanceAssetSha256
    coatOfArms.value = pruned.coatOfArms
    source.value = serializeCoatOfArms(pruned.coatOfArms)
    fitResult.value = {
      ...fitResult.value!,
      coatOfArms: pruned.coatOfArms,
      provenance: {
        ...fitResult.value!.provenance,
        logicalLayers: pruned.coatOfArms.coloredEmblems.length + pruned.coatOfArms.texturedEmblems.length,
        coloredEmblemBlocks: pruned.coatOfArms.coloredEmblems.length,
        drawnInstances: pruned.receipt.drawnInstancesAfter,
        selectedLayers: pruned.receipt.drawnInstancesAfter,
        selectedAssetSha256: [patternAssetSha256, ...retainedAssetSha256].filter(Boolean),
      },
    }
    fitPruneEvidence.value = pruned.receipt
    fitPruneSource.value = source.value
    if (pruned.receipt.removedInstances > 0) {
      fitCompressionEvidence.value = undefined
      fitCompressionSource.value = ''
    }
    fitPruneProgress.value = {
      pass: pruned.receipt.fixedPointPasses,
      completedInPass: pruned.receipt.finalNecessityEvidence.length,
      totalInPass: pruned.receipt.finalNecessityEvidence.length,
      evaluatedCandidates: pruned.receipt.evaluatedCandidates,
      percent: 100,
    }
    ElMessage.success(`精确剪枝达到固定点：移除 ${pruned.receipt.removedInstances}，保留 ${pruned.receipt.drawnInstancesAfter}`)
  }
  worker.onerror = (event) => {
    fail(event.message)
  }
  worker.onmessageerror = () => {
    fail('结果消息无法反序列化')
  }
  const usedTextureNames = [...new Set(coatOfArms.value.coloredEmblems.map((item) => item.texture))]
  const workerEmblems = Object.fromEntries(usedTextureNames.map((name) => (
    [name, cloneDecodedDdsForWorker(emblemTextures.value[name])]
  )))
  try {
    worker.postMessage([
      cloneCoatOfArmsForWorker(coatOfArms.value),
      {
        width: targetImage.value.image.width,
        height: targetImage.value.image.height,
        pixels: new Uint8ClampedArray(targetImage.value.image.pixels),
      },
      cloneDecodedDdsForWorker(patternTexture.value),
      workerEmblems,
      undefined,
      Object.fromEntries(Object.entries(shaderNamedColors.value).map(([name, color]) => (
        [name, [...color]]
      ))),
      {
        searchResolution: 96,
        validationResolutions: [230, 512],
        numericLossTolerance: 1e-12,
        allowedVisualDifferenceBytes: 0,
      },
    ])
  } catch (error) {
    fail(errorMessage(error))
  }
}

function compressFitDocument() {
  if (!fitResult.value || !patternTexture.value) {
    ElMessage.warning('请先完成一次图片拟合并载入结果素材')
    return
  }
  const original = coatOfArms.value
  const missing = [...new Set(original.coloredEmblems.map((item) => item.texture))]
    .filter((name) => !emblemTextures.value[name])
  if (missing.length) {
    ElMessage.error(`无法验证安全压缩，缺少 ${missing.length} 个结果 DDS`)
    return
  }
  const compressed = structurallyCompressCoatOfArms(original)
  const pixelExactResolutions = [96, 230, 512]
  for (const size of pixelExactResolutions) {
    const assets = {
      pattern: patternTexture.value,
      coloredEmblems: emblemTextures.value,
      surfaceMask: surfaceMask.value,
    }
    const before = renderCoatOfArms(original, assets, shaderNamedColors.value, size)
    const after = renderCoatOfArms(compressed.coatOfArms, assets, shaderNamedColors.value, size)
    if (!before || !after || before.pixels.length !== after.pixels.length) {
      ElMessage.error(`安全压缩 ${size}px 渲染验证不可用`)
      return
    }
    for (let index = 0; index < before.pixels.length; index += 1) {
      if (before.pixels[index] !== after.pixels[index]) {
        ElMessage.error(`安全压缩在 ${size}px 改变了像素，已拒绝应用`)
        return
      }
    }
  }
  coatOfArms.value = compressed.coatOfArms
  source.value = serializeCoatOfArms(compressed.coatOfArms)
  fitResult.value = {
    ...fitResult.value,
    coatOfArms: compressed.coatOfArms,
    provenance: {
      ...fitResult.value.provenance,
      logicalLayers: compressed.coatOfArms.coloredEmblems.length
        + compressed.coatOfArms.texturedEmblems.length,
      coloredEmblemBlocks: compressed.coatOfArms.coloredEmblems.length,
      drawnInstances: compressed.receipt.drawnInstancesAfter,
      selectedLayers: compressed.receipt.drawnInstancesAfter,
    },
  }
  fitCompressionEvidence.value = { receipt: compressed.receipt, pixelExactResolutions }
  fitCompressionSource.value = source.value
  const saved = compressed.receipt.utf8BytesBefore - compressed.receipt.utf8BytesAfter
  ElMessage.success(`安全压缩完成：合并 ${compressed.receipt.mergedBlocks} 个块，减少 ${saved} bytes`)
}

async function fitTargetImage() {
  if (!targetImage.value) {
    ElMessage.warning('请先选择目标图片')
    return
  }
  if (!loadedAssetPack.value) {
    ElMessage.warning('请先载入独立静态素材包')
    return
  }
  const layerBudget = Math.floor(fitLayerBudget.value)
  if (!Number.isSafeInteger(layerBudget) || layerBudget < 1) {
    ElMessage.warning('图层搜索预算必须是至少为 1 的安全整数')
    return
  }
  fitLayerBudget.value = layerBudget
  cancelInstancePrune(false)
  cancelImageFit(false)
  const runId = ++fitRunId
  fitBusy.value = true
  fitResult.value = undefined
  fitCompressionEvidence.value = undefined
  fitCompressionSource.value = ''
  fitPruneEvidence.value = undefined
  fitPruneSource.value = ''
  fitWebGlScore.value = null
  fitPreviewUrl.value = ''
  fitProgressPercent.value = 0
  fitProgressLabel.value = '正在准备完整素材索引'
  try {
    const patterns = loadedAssetPack.value.pack.assets
      .filter((item) => item.kind === 'pattern' && item.registration === 'designer_manifest')
      .sort((left, right) => left.name.localeCompare(right.name))
    const emblems = loadedAssetPack.value.pack.assets
      .filter((item) => item.kind === 'colored_emblem' && item.registration === 'designer_manifest')
      .sort((left, right) => left.name.localeCompare(right.name))
    fitStatus.value = loadedAssetPack.value.pack.fit_index
      ? `正在校验并读取完整 ${loadedAssetPack.value.pack.fit_index.asset_indices.length} 项可粘贴 RGBA 搜索索引…`
      : `旧素材包没有搜索索引，正在读取 ${patterns.length + emblems.length} 个 DDS…`
    const toCandidate = async (item: WebAssetPackEntry): Promise<FitTextureCandidate> => ({
      name: item.name,
      assetSha256: item.asset_sha256,
      texture: await readPackTexture(item),
    })
    let patternCandidates: FitTextureCandidate[]
    let emblemCandidates: FitTextureCandidate[]
    if (loadedAssetPack.value.pack.fit_index) {
      const indexed = await readWebFitIndex(loadedAssetPack.value)
      patternCandidates = indexed
        .filter((item) => item.entry.kind === 'pattern')
        .map((item) => ({ name: item.entry.name, assetSha256: item.entry.asset_sha256, texture: item.texture }))
      emblemCandidates = indexed
        .filter((item) => item.entry.kind === 'colored_emblem')
        .map((item) => ({ name: item.entry.name, assetSha256: item.entry.asset_sha256, texture: item.texture }))
    } else {
      [patternCandidates, emblemCandidates] = await Promise.all([
        Promise.all(patterns.map(toCandidate)),
        Promise.all(emblems.map(toCandidate)),
      ])
    }
    if (runId !== fitRunId) return
    fitStatus.value = `浏览器 Worker 正在执行透明度加权、轮廓粗筛和双路径残差重建；最多 ${layerBudget} 层，只保留严格改善层…`
    const worker = new Worker(new URL('./domain/imageFitter.worker.ts', import.meta.url), { type: 'module' })
    fitWorker = worker
    const target = targetImage.value.image
    worker.onmessage = async (event: MessageEvent<
      | { kind: 'progress', progress: ImageFitProgress }
      | { kind: 'result', ok: boolean, result?: ImageFitResult, error?: string }
    >) => {
      if (runId !== fitRunId) return
      if (event.data.kind === 'progress') {
        const progress = event.data.progress
        fitProgressPercent.value = progress.percent
        const phase = progress.phase === 'background'
          ? '背景匹配'
          : progress.phase === 'coarse'
            ? `第 ${progress.layer}/${progress.layerBudget} 层 · 全库轮廓粗筛`
            : progress.phase === 'refine'
              ? `第 ${progress.layer}/${progress.layerBudget} 层 · 全角度与 0.1° 级精筛`
              : `原生矩形块残差细化 · 最多 ${progress.layerBudget} 层`
        fitProgressLabel.value = `${phase} · ${progress.completed}/${progress.total} · 已评估 ${progress.evaluatedCandidates}`
        return
      }
      worker.terminate()
      fitWorker = null
      if (!event.data.ok || !event.data.result) {
        fitBusy.value = false
        fitProgressPercent.value = 0
        fitProgressLabel.value = '拟合失败'
        fitStatus.value = `拟合失败：${event.data.error ?? 'unknown'}`
        ElMessage.error(fitStatus.value)
        return
      }
      const result = event.data.result
      fitResult.value = result
      coatOfArms.value = result.coatOfArms
      source.value = serializeCoatOfArms(result.coatOfArms)
      diagnostics.value = []
      selectedEmblem.value = 0
      const selectedPatternEntry = patterns.find((item) => item.name === result.coatOfArms.pattern)
      const selectedEmblemNames = new Set(result.coatOfArms.coloredEmblems.map((item) => item.texture))
      const selectedEmblemEntries = emblems.filter((item) => selectedEmblemNames.has(item.name))
      let selectedPatternTexture: DecodedDds | undefined
      let selectedFullEmblems: (readonly [string, DecodedDds])[]
      try {
        [selectedPatternTexture, selectedFullEmblems] = await Promise.all([
          selectedPatternEntry ? readPackTexture(selectedPatternEntry) : Promise.resolve(undefined),
          Promise.all(selectedEmblemEntries.map(async (item) => [item.name, await readPackTexture(item)] as const)),
        ])
      } catch (error) {
        if (runId !== fitRunId) return
        fitBusy.value = false
        fitProgressPercent.value = 0
        fitProgressLabel.value = '结果素材校验失败'
        fitStatus.value = `拟合已完成，但完整 DDS 校验失败：${errorMessage(error)}`
        ElMessage.error(fitStatus.value)
        return
      }
      if (runId !== fitRunId) return
      fitBusy.value = false
      fitProgressPercent.value = 100
      fitProgressLabel.value = `完成 · 选中 ${result.provenance.selectedLayers} 层`
      patternTexture.value = selectedPatternTexture
      patternPreviewUrl.value = selectedPatternTexture ? decodedDdsToDataUrl(selectedPatternTexture) : ''
      emblemTextures.value = Object.fromEntries(selectedFullEmblems)
      emblemPreviewUrls.value = Object.fromEntries(
        Object.entries(emblemTextures.value).map(([name, decoded]) => [name, decodedDdsToDataUrl(decoded)]),
      )
      const normalizedTarget = resizeFitImage(target, result.provenance.resolution)
      const rendered = renderCoatOfArms(
        result.coatOfArms,
        { pattern: selectedPatternTexture, coloredEmblems: emblemTextures.value },
        {},
        result.provenance.resolution,
      )
      fitPreviewUrl.value = rendered ? renderedCoatOfArmsToDataUrl(rendered) : ''
      try {
        fitWebGlScore.value = rendered
          ? scoreWithWebGl2(normalizedTarget, { width: rendered.width, height: rendered.height, pixels: rendered.pixels })
          : null
      } catch {
        fitWebGlScore.value = null
      }
      const reconstructionMode = result.provenance.reconstructionMode === 'native-tile-paint'
        ? '原生块多层重建'
        : result.provenance.reconstructionMode === 'native-edge-refined'
          ? '原生块局部边缘细化'
        : result.provenance.reconstructionMode === 'hybrid-native-paint'
          ? '语义元素 + 原生块混合重建'
          : '语义元素搜索'
      fitStatus.value = `完成 · ${reconstructionMode} · 从完整库评估 ${result.provenance.evaluatedCandidates} 个构图 · 选中 ${result.provenance.selectedLayers}/${result.provenance.layerBudget} 层 · 停止：${fitTerminationLabels[result.provenance.terminationReason]} · CPU reference${fitWebGlScore.value ? ' + WebGL2 RGBA8 交叉评分' : ' · WebGL2 不可用'}`
      ElMessage.success('多层原生元素构图已载入结构化编辑器，可继续调整并复制代码')
    }
    worker.onerror = (event) => {
      if (runId !== fitRunId) return
      worker.terminate()
      fitWorker = null
      fitBusy.value = false
      fitProgressPercent.value = 0
      fitProgressLabel.value = 'Worker 失败'
      fitStatus.value = `Worker 失败：${event.message}`
      ElMessage.error(fitStatus.value)
    }
    const workerImage: FitImage = {
      width: target.width,
      height: target.height,
      pixels: new Uint8ClampedArray(target.pixels),
    }
    const workerCandidates = (items: FitTextureCandidate[]): FitTextureCandidate[] => items.map((item) => ({
      name: item.name,
      assetSha256: item.assetSha256,
      texture: {
        width: item.texture.width,
        height: item.texture.height,
        fourCC: item.texture.fourCC,
        pixels: new Uint8ClampedArray(item.texture.pixels),
      },
    }))
    worker.postMessage([workerImage, workerCandidates(patternCandidates), workerCandidates(emblemCandidates), {
      resolution: layerBudget >= 128 ? 96 : 56,
      maxPatterns: patterns.length,
      maxEmblemCandidates: emblemCandidates.length,
      maxLayers: layerBudget,
      sourceWidth: targetImage.value.originalWidth,
      sourceHeight: targetImage.value.originalHeight,
      pyramidImages: targetImage.value.pyramid.map((image) => ({
        width: image.width,
        height: image.height,
        pixels: new Uint8ClampedArray(image.pixels),
      })),
      refinementCandidates: 48,
      beamWidth: 2,
    }])
  } catch (error) {
    if (runId !== fitRunId) return
    fitBusy.value = false
    fitProgressPercent.value = 0
    fitProgressLabel.value = '拟合失败'
    fitStatus.value = `拟合失败：${errorMessage(error)}`
    ElMessage.error(fitStatus.value)
  }
}

onMounted(() => {
  void loadStandaloneAssetPack(false)
})

watch(selectedEmblem, () => {
  instanceWindowStart.value = 0
})

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
  if (outputBytes.value > COAT_OF_ARMS_MCP_MAX_BYTES) {
    ElMessage.error('代码超过当前开发期 MCP 的 128 KiB 安全合同；这不是已证明的 CK3 原生上限')
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
  const staticEntry = packEntry(kind, name)
  if (staticEntry) {
    const decoded = await readPackTexture(staticEntry)
    return { decoded, preview: decodedDdsToDataUrl(decoded) }
  }
  if (!developmentCompanionEnabled) {
    throw new Error(`独立素材包中没有 ${kind}/${name}`)
  }
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
        <p class="eyebrow">Crusader Kings III code · standalone browser Alpha</p>
        <h1>家徽工坊</h1>
        <p class="subtitle">独立生成与编辑可粘贴的静态纹章代码；正式平台不连接或启动游戏。</p>
      </div>
      <div class="top-actions">
        <el-tag :type="loadedAssetPack ? 'success' : 'warning'" effect="plain">
          {{ loadedAssetPack ? '独立素材包已绑定' : '等待独立素材包' }}
        </el-tag>
        <input ref="projectFileInput" class="hidden-file-input" type="file" accept="application/json,.json" @change="importProject">
        <el-button :loading="projectFileBusy" @click="openProjectFilePicker">打开项目</el-button>
        <el-button :loading="projectFileBusy" @click="exportProject">保存项目</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button type="primary" :disabled="errorCount > 0" @click="copyOutput">复制 CK3 代码</el-button>
      </div>
    </header>

    <section class="image-fit-panel panel">
      <div class="panel-title">
        <div><span class="step">00</span><h2>图片拟合原生元素</h2></div>
        <el-tag effect="plain" type="success">纯浏览器 · 图片不上传</el-tag>
      </div>
      <div class="image-fit-grid">
        <label class="image-drop">
          <input type="file" accept="image/png,image/jpeg,image/webp" @change="selectTargetImage">
          <img v-if="targetImage" :src="targetImage.previewUrl" alt="待拟合目标图片">
          <span v-else>选择 PNG / JPEG / WebP<br><small>最大 16 MiB、4096×4096</small></span>
        </label>
        <div class="fit-controls">
          <strong>独立素材包</strong>
          <p>{{ assetPackStatus }}</p>
          <el-button :loading="assetPackBusy" @click="loadStandaloneAssetPack()">重新载入静态素材包</el-button>
          <div class="fit-budget">
            <span>最大改善图层数</span>
            <el-input-number v-model="fitLayerBudget" :min="1" :step="1" />
          </div>
          <small class="fit-budget-note">例如 1024 表示最多搜索并保留 1024 层，不保证输出恰好 1024 层。每一层必须严格降低实际渲染损失；无改善或用户取消时提前停止。输入支持 10000 及更大安全整数。</small>
          <small class="fit-budget-note">当前原生块细化平面为 96×96；它按分辨率和预算扩展四叉树深度，预算不会被改写，但像素粒度、无改善或精确匹配可能令实际实例提前收敛。</small>
          <div class="fit-actions">
            <el-button type="primary" :loading="fitBusy" :disabled="fitPruneBusy || !targetImage || !loadedAssetPack" @click="fitTargetImage">
              开始本地拟合
            </el-button>
            <el-button :disabled="!fitBusy" @click="cancelImageFit()">取消</el-button>
            <el-button :disabled="fitBusy || fitPruneBusy || !fitResult" @click="compressFitDocument">安全压缩相邻同样式块</el-button>
            <el-button :loading="fitPruneBusy" :disabled="fitBusy || fitPruneBusy || !fitResult" @click="pruneFitDocument">精确固定点剪枝</el-button>
            <el-button v-if="fitPruneBusy" @click="cancelInstancePrune()">取消剪枝</el-button>
          </div>
        </div>
        <div class="fit-report" :data-fit-evidence="fitEvidenceJson">
          <strong>运行状态</strong>
          <p>{{ fitStatus }}</p>
          <div class="fit-progress">
            <el-progress
              :percentage="fitProgressPercent"
              :status="fitResult && !fitBusy ? 'success' : undefined"
              :stroke-width="10"
            />
            <small>{{ fitProgressLabel }}（进度表示当前搜索阶段）</small>
          </div>
          <template v-if="fitResult">
            <div v-if="fitPruneProgress" class="fit-progress">
              <el-progress :percentage="fitPruneProgress.percent" :status="activeFitPrune ? 'success' : undefined" :stroke-width="8" />
              <small>剪枝第 {{ fitPruneProgress.pass }} 轮 · {{ fitPruneProgress.completedInPass }}/{{ fitPruneProgress.totalInPass }} · 累计 {{ fitPruneProgress.evaluatedCandidates }} 候选</small>
            </div>
            <div v-if="fitPreviewUrl" class="fit-result-image">
              <span>拟合平面（不叠加盾面材质）</span>
              <img :src="fitPreviewUrl" alt="图片拟合结果预览">
            </div>
            <dl>
              <div><dt>总损失</dt><dd>{{ fitResult.metrics.totalLoss.toFixed(5) }}</dd></div>
              <div><dt>颜色</dt><dd>{{ fitResult.metrics.colorLoss.toFixed(5) }}</dd></div>
              <div><dt>边缘</dt><dd>{{ fitResult.metrics.edgeLoss.toFixed(5) }}</dd></div>
              <div><dt>候选数</dt><dd>{{ fitResult.provenance.evaluatedCandidates }}</dd></div>
              <div><dt>用户预算</dt><dd>{{ fitResult.provenance.layerBudget }} 个绘制实例</dd></div>
              <div><dt>实际绘制实例</dt><dd>{{ fitResult.provenance.drawnInstances }}</dd></div>
              <div><dt>逻辑图层</dt><dd>{{ fitResult.provenance.logicalLayers }}</dd></div>
              <div><dt>colored_emblem 块</dt><dd>{{ fitResult.provenance.coloredEmblemBlocks }}</dd></div>
              <div><dt>instance 数</dt><dd>{{ fitResult.provenance.drawnInstances }}</dd></div>
              <div><dt>代码体积</dt><dd>{{ outputBytes }} UTF-8 bytes / {{ outputLines }} 行</dd></div>
              <template v-if="activeFitCompression">
                <div><dt>安全压缩块</dt><dd>{{ activeFitCompression.receipt.coloredEmblemBlocksBefore }} → {{ activeFitCompression.receipt.coloredEmblemBlocksAfter }}</dd></div>
                <div><dt>安全压缩实例</dt><dd>{{ activeFitCompression.receipt.drawnInstancesBefore }} → {{ activeFitCompression.receipt.drawnInstancesAfter }}</dd></div>
                <div><dt>安全压缩体积</dt><dd>{{ activeFitCompression.receipt.utf8BytesBefore }} → {{ activeFitCompression.receipt.utf8BytesAfter }} bytes</dd></div>
                <div><dt>压缩像素门禁</dt><dd>{{ activeFitCompression.pixelExactResolutions.join(' / ') }} 全部逐字节一致</dd></div>
              </template>
              <template v-if="activeFitPrune">
                <div><dt>固定点剪枝</dt><dd>{{ activeFitPrune.drawnInstancesBefore }} → {{ activeFitPrune.drawnInstancesAfter }} 实例</dd></div>
                <div><dt>必要性证据</dt><dd>{{ activeFitPrune.finalNecessityEvidence.length }} / {{ activeFitPrune.drawnInstancesAfter }} 完整</dd></div>
                <div><dt>剪枝合同</dt><dd>96 / 230 / 512 零像素差；损失容差 1e-12</dd></div>
              </template>
              <div><dt>高分辨率接缝门禁</dt><dd>{{ fitResult.provenance.nativeTileSeamValidation.status === 'passed' ? '96 / 230 / 512 全部通过' : '不适用' }}</dd></div>
              <div><dt>接缝指标</dt><dd>{{ fitResult.provenance.nativeTileSeamValidation.metrics.map((metric) => `${metric.resolution}px leak=${metric.backgroundLeakPixels} peak=${Math.max(metric.peakRowLeakPixels, metric.peakColumnLeakPixels)}`).join('；') || '不适用' }}</dd></div>
              <div><dt>块搜索空间</dt><dd>{{ fitResult.provenance.nativeTileSearch.searchWidth }}×{{ fitResult.provenance.nativeTileSearch.searchHeight }} · depth {{ fitResult.provenance.nativeTileSearch.maximumDepth }} · 像素叶容量 {{ fitResult.provenance.nativeTileSearch.pixelLeafCapacity }} · 预算原值 {{ fitResult.provenance.nativeTileSearch.userBudgetAppliedWithoutClamp }}</dd></div>
              <div><dt>算法合同</dt><dd>{{ fitResult.provenance.algorithm }}</dd></div>
              <div><dt>相对改善</dt><dd>{{ (fitResult.metrics.relativeImprovement * 100).toFixed(2) }}%</dd></div>
              <div><dt>GPU 交叉分</dt><dd>{{ fitWebGlScore ? fitWebGlScore.meanSquaredRgbError.toFixed(5) : '不可用' }}</dd></div>
              <div><dt>输入/金字塔</dt><dd>{{ fitResult.provenance.sourceWidth }}×{{ fitResult.provenance.sourceHeight }} → {{ fitResult.provenance.pyramidResolutions.join(' / ') }}px</dd></div>
              <div><dt>候选路径</dt><dd>{{ fitResult.provenance.candidateLosses.map((item) => `${item.mode === 'native-tile-paint' ? '原生块' : item.mode === 'native-edge-refined' ? '边缘细化' : item.mode === 'hybrid-native-paint' ? '混合' : '语义'} ${item.layers}层=${item.totalLoss.toFixed(4)} [${item.textureNames.join(', ') || '无纹章'}]`).join('；') }}</dd></div>
            </dl>
            <small>分数只用于同一算法和目标之间比较，不代表 CK3 像素一致率。结果已进入下方结构化编辑器。</small>
          </template>
        </div>
      </div>
      <el-alert
        class="mcp-limit-note"
        type="warning"
        :closable="false"
        show-icon
        title="128 KiB 只是旧版单请求 MCP v1 合同，不是 CK3 上限"
        description="380,862-byte、1000-instance hunter 已通过分块 MCP v2 的真实 CK3 Apply → Copy。网页复制不设此上限；当前页面内置的旧开发 companion 按钮仍使用 v1，正式 Pages 不包含该开发入口。512 KiB 也只是当前 v2 传输资源上限，不代表引擎上限。"
      />
    </section>

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

        <div v-if="developmentCompanionEnabled" class="mcp-panel">
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
            <el-button :loading="mcpBusy" :disabled="errorCount > 0 || outputBytes > COAT_OF_ARMS_MCP_MAX_BYTES" @click="probeInCk3(false)">原生检测</el-button>
            <el-button type="primary" plain :loading="mcpBusy" :disabled="errorCount > 0 || outputBytes > COAT_OF_ARMS_MCP_MAX_BYTES" @click="probeInCk3(true)">应用到设计器</el-button>
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
                v-for="item in fallbackPreviewEmblems"
                :key="`${item.emblem.texture}-${item.emblemIndex}`"
                class="emblem-group"
              >
                <template v-for="(instance, instanceIndex) in item.instances" :key="instanceIndex">
                  <img
                    v-if="emblemPreviewUrls[item.emblem.texture]"
                    class="emblem-texture"
                    :src="emblemPreviewUrls[item.emblem.texture]"
                    :alt="item.emblem.texture"
                    :style="{
                      left: `${instance.position[0] * 100}%`,
                      top: `${instance.position[1] * 100}%`,
                      transform: `translate(-50%, -50%) rotate(${instance.rotation}deg) scale(${instance.scale[0]}, ${instance.scale[1]})`,
                      zIndex: Math.round(instance.depth * 10),
                    }"
                    :title="item.emblem.texture"
                  />
                  <div
                    v-else
                    class="emblem-glyph"
                    :style="{
                      left: `${instance.position[0] * 100}%`,
                      top: `${instance.position[1] * 100}%`,
                      color: cssColor(item.emblem.colors[0]),
                      transform: `translate(-50%, -50%) rotate(${instance.rotation}deg) scale(${instance.scale[0]}, ${instance.scale[1]})`,
                      zIndex: Math.round(instance.depth * 10),
                    }"
                    :title="item.emblem.texture"
                  >✦</div>
                </template>
              </div>
            </template>
          </div>
        </div>
        <div class="preview-caption">
          <strong>{{ coatOfArms.pattern || '未指定 pattern' }}</strong>
          <span>{{ coatOfArms.coloredEmblems.length }} 个彩色图层 · {{ drawnInstanceCount }} 个实例 · {{ coatOfArms.texturedEmblems.length }} 个受限纹理层</span>
        </div>
        <el-alert v-if="largeDocumentPreviewDeferred" type="warning" :closable="false" show-icon>
          <template #title>当前文档超过 2,048 个实例；为保证编辑响应，实时整幅预览已延后。完整模型、复制和项目保存不受影响。</template>
        </el-alert>
        <el-button class="preview-load" :loading="textureBusy" @click="loadCurrentTexturePreviews">从独立素材包加载当前 DDS</el-button>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>预览翻译 exact 1.19.0.6 随附 shader 的通道、mask、transform、surface detail 与 blend；FallbackColor 绑定、GPU 采样/色彩空间仍待以后原生像素对照。</template>
        </el-alert>
      </section>

      <section class="editor-pane panel">
        <div class="panel-title">
          <div><span class="step">03</span><h2>结构化编辑</h2></div>
          <el-space>
            <el-button v-if="developmentCompanionEnabled" size="small" :loading="runtimeFeatureBusy" @click="loadRuntimeFeatures">开发期运行态</el-button>
            <el-button v-if="developmentCompanionEnabled" size="small" :loading="catalogBusy" @click="loadResourceCatalog">开发期 MCP 资源</el-button>
            <el-button v-else size="small" :loading="assetPackBusy" @click="loadStandaloneAssetPack()">刷新静态资源</el-button>
          </el-space>
        </div>
        <el-scrollbar height="690px">
          <div v-if="developmentCompanionEnabled" class="resource-search">
            <el-input v-model="emblemSearch" clearable placeholder="筛选 emblem 名；留空取前 200 项" @keyup.enter="loadResourceCatalog" />
            <el-button :loading="catalogBusy" @click="loadResourceCatalog">刷新目录</el-button>
          </div>
          <p class="resource-note">
            正式平台只读取部署时冻结、逐项 SHA-256 绑定的静态 asset pack，不访问本机游戏。
            <template v-if="developmentCompanionEnabled && installedDlcDescriptorCount !== null && dlcCoaSourceCount !== null">
              安装树含 {{ installedDlcDescriptorCount }} 份 DLC 描述符，其中 {{ dlcCoaSourceCount }} 份有直接 CoA 候选；
              该数字不证明商店授权或引擎 mount。
            </template>
            <template v-if="developmentCompanionEnabled && configuredModCount !== null">
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
            <template v-if="developmentCompanionEnabled">开发期 CK3 运行态：{{ runtimeFeatureStatus }}。</template>
            <template v-if="developmentCompanionEnabled && runtimeEnabledFeatureCount !== null && runtimeFeatureCount !== null && runtimeDlcKeys !== null">
              原生同帧读到 {{ runtimeEnabledFeatureCount }}/{{ runtimeFeatureCount }} 个 effective feature 为真，
              `has_dlc` 可见 {{ runtimeDlcKeys.length }} 个 key。
              这证明当前进程的 gameplay gate，不证明商店授权，也不决定同名家徽资源的最终胜者。
            </template>
          </p>
          <el-collapse
            v-if="developmentCompanionEnabled && (configuredPatternResources.length || configuredEmblemResources.length)"
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
            <el-tabs v-if="coatOfArms.coloredEmblems.length && coatOfArms.coloredEmblems.length <= 128" v-model="selectedEmblem" type="card">
              <el-tab-pane v-for="(emblem, index) in coatOfArms.coloredEmblems" :key="index" :label="`图层 ${index + 1}`" :name="index" />
            </el-tabs>
            <div v-else-if="coatOfArms.coloredEmblems.length" class="emblem-window-toolbar">
              <span>图层 {{ selectedEmblem + 1 }} / {{ coatOfArms.coloredEmblems.length }}（大文档按索引编辑）</span>
              <el-button size="small" :disabled="selectedEmblem === 0" @click="selectEmblemIndex(selectedEmblem - 1)">上一层</el-button>
              <el-input-number
                :model-value="selectedEmblem + 1"
                :min="1"
                :max="coatOfArms.coloredEmblems.length"
                controls-position="right"
                @update:model-value="selectEmblemIndex(Number($event) - 1)"
              />
              <el-button size="small" :disabled="selectedEmblem + 1 >= coatOfArms.coloredEmblems.length" @click="selectEmblemIndex(selectedEmblem + 1)">下一层</el-button>
            </div>

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

              <div v-if="activeEmblem.instances.length > INSTANCE_EDITOR_WINDOW_SIZE" class="instance-window-toolbar">
                <span>实例窗口 {{ boundedInstanceWindowStart + 1 }}–{{ instanceWindowEnd }} / {{ activeEmblem.instances.length }}</span>
                <el-button size="small" :disabled="boundedInstanceWindowStart === 0" @click="moveInstanceWindow(boundedInstanceWindowStart - INSTANCE_EDITOR_WINDOW_SIZE)">上一页</el-button>
                <el-input-number
                  :model-value="boundedInstanceWindowStart + 1"
                  :min="1"
                  :max="activeEmblem.instances.length"
                  :step="INSTANCE_EDITOR_WINDOW_SIZE"
                  controls-position="right"
                  @update:model-value="moveInstanceWindow(Number($event) - 1)"
                />
                <el-button size="small" :disabled="instanceWindowEnd >= activeEmblem.instances.length" @click="moveInstanceWindow(instanceWindowEnd)">下一页</el-button>
              </div>
              <div class="instance-list" data-testid="instance-editor-window">
                <div v-for="item in visibleInstanceItems" :key="item.index" class="instance-card" :data-instance-index="item.index">
                  <div class="instance-title">
                    <strong>实例 {{ item.index + 1 }}</strong>
                    <el-button link type="danger" @click="removeActiveInstance(item.index)">删除</el-button>
                  </div>
                  <div class="number-grid">
                    <el-form-item label="X"><el-input-number v-model="item.instance.position[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Y"><el-input-number v-model="item.instance.position[1]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale X"><el-input-number v-model="item.instance.scale[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale Y"><el-input-number v-model="item.instance.scale[1]" :step="0.05" /></el-form-item>
                    <el-form-item label="Rotation"><el-input-number v-model="item.instance.rotation" :step="5" /></el-form-item>
                    <el-form-item label="Depth"><el-input-number v-model="item.instance.depth" :step="0.01" /></el-form-item>
                  </div>
                </div>
              </div>
              <div class="row-actions">
                <el-button @click="addInstanceToActiveEmblem">添加实例</el-button>
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
            <div class="section-heading">
              <h3>确定性导出</h3>
              <el-space>
                <el-tag>{{ outputBytes.toLocaleString() }} bytes · {{ outputLines.toLocaleString() }} 行</el-tag>
                <el-tag v-if="outputPreviewTruncated" type="warning">UI 摘要；复制仍为完整文档</el-tag>
                <el-tag>CRLF</el-tag>
              </el-space>
            </div>
            <pre>{{ outputPreview }}</pre>
          </div>
        </el-scrollbar>
      </section>
    </main>
  </div>
</template>
