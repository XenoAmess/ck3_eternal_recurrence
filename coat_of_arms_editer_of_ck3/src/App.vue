<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { ElMessage as ElementMessage } from 'element-plus'
import elementEn from 'element-plus/es/locale/lang/en'
import elementZhCn from 'element-plus/es/locale/lang/zh-cn'
import { decodedDdsToDataUrl, type DecodedDds } from './domain/dds'
import {
  candidateDominance,
  MAX_COMPARISON_CANDIDATES,
  type CoatOfArmsComparisonCandidate,
} from './domain/comparisonCandidates'
import { coatOfArmsDocumentStats } from './domain/documentStats'
import {
  loadWebAssetPack,
  loadWebAssetPackFiles,
  readWebAsset,
  readWebFitIndex,
  type LoadedWebAssetPack,
  type WebAssetPackEntry,
} from './domain/assetPack'
import { syntaxCapabilityRows, type CapabilityStage } from './domain/capabilityMatrix'
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
import { finalizeImageFitWithFullAssets } from './domain/fitFinalizer'
import {
  resizeFitImage,
  type FitImage,
  type FitTextureCandidate,
  type ImageFitCheckpoint,
  type ImageFitMetrics,
  type ImageFitProgress,
  type ImageFitResult,
} from './domain/imageFitter'
import {
  FIT_WORKER_PROTOCOL,
  isCurrentFitWorkerMessage,
  type FitTaskState,
  type FitWorkerResponse,
  type FitWorkerStartRequest,
} from './domain/fitWorkerProtocol'
import {
  clearPersistedFitCheckpoint,
  createPersistedFitCheckpoint,
  estimatePersistedFitCheckpointBytes,
  loadPersistedFitCheckpoint,
  parsePortableFitCheckpoint,
  PORTABLE_FIT_CHECKPOINT_MAX_BYTES,
  restorePersistedFitInput,
  savePersistedFitCheckpoint,
  serializePortableFitCheckpoint,
  type PersistedFitCheckpoint,
} from './domain/fitCheckpointStore'
import {
  classifyBrowserStorageFailure,
  inspectBrowserStorage,
  type BrowserStorageEstimate,
  type BrowserStorageFailureKind,
} from './domain/browserStorage'
import { parseCoatOfArms } from './domain/parser'
import {
  createCoatOfArmsProject,
  parseCoatOfArmsProject,
  serializeCoatOfArmsProject,
  type CoatOfArmsProjectDocument,
} from './domain/projectDocument'
import { clearAutosaveProject, loadAutosaveProject, saveAutosaveProject } from './domain/projectStore'
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
import { translateRuntimeText, useUiI18n, type UiLocale } from './i18n'

const { locale, setLocale, t } = useUiI18n()
const elementPlusLocale = computed(() => locale.value === 'en' ? elementEn : elementZhCn)
const buildVersion = `${__COA_BUILD_TIMESTAMP__} · ${__COA_GIT_HASH__}`

function chooseLocale(value: string | number | boolean | undefined) {
  if (value === 'zh-CN' || value === 'en') setLocale(value as UiLocale)
}

function uiText(value: string): string {
  return translateRuntimeText(value, locale.value)
}

function capabilityStageLabel(stage: CapabilityStage): string {
  if (stage === 'full') return t('coverageFull')
  if (stage === 'normalized') return t('coverageNormalized')
  if (stage === 'limited') return t('coverageLimited')
  if (stage === 'missing') return t('coverageMissing')
  if (stage === 'rejected') return t('coverageRejected')
  return t('coverageNotApplicable')
}

const ElMessage = {
  success: (message: string) => ElementMessage.success(uiText(message)),
  info: (message: string) => ElementMessage.info(uiText(message)),
  warning: (message: string) => ElementMessage.warning(uiText(message)),
  error: (message: string) => ElementMessage.error(uiText(message)),
}

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
const textureBusy = ref(false)
const clipboardBusy = ref(false)
const projectFileBusy = ref(false)
const projectFileInput = ref<HTMLInputElement>()
const fitCheckpointFileInput = ref<HTMLInputElement>()
const assetPackDirectoryInput = ref<HTMLInputElement>()
const undoHistory = ref<{ source: string, utf8Bytes: number }[]>([])
const redoHistory = ref<{ source: string, utf8Bytes: number }[]>([])
const historyPending = ref(false)
const historyNotice = ref('尚无可撤销修改')
const autosaveStatus = ref('正在检查自动保存')
const recoverableAutosave = ref<CoatOfArmsProjectDocument>()
const comparisonCandidates = ref<CoatOfArmsComparisonCandidate[]>([])
let comparisonCandidateSequence = 0
const patternResources = ref<WebAssetPackEntry[]>([])
const emblemResources = ref<WebAssetPackEntry[]>([])
const patternPreviewUrl = ref('')
const emblemPreviewUrls = ref<Record<string, string>>({})
const patternTexture = ref<DecodedDds>()
const emblemTextures = ref<Record<string, DecodedDds>>({})
const texturedEmblemTextures = ref<Record<string, DecodedDds>>({})
const surfaceMask = ref<DecodedDds>()
const texturedDefaultPreviewUrl = ref('')
const shaderNamedColors = ref<NamedColorMap>({})
const shaderSourceCount = ref(0)
const defaultAssetPackUrl = import.meta.env.VITE_COA_ASSET_PACK_URL
  || `${import.meta.env.BASE_URL}asset-packs/ck3-1.19.0.6/manifest.json`
const loadedAssetPack = ref<LoadedWebAssetPack>()
const assetPackBusy = ref(false)
const assetPackStatus = ref('尚未载入独立素材包')
const assetPackVfsStatus = computed(() => {
  const receipt = loadedAssetPack.value?.pack.vfs_receipt
  if (!receipt) return t('vfsReceiptUnavailable')
  const scope = receipt.scope === 'base_game_only' ? t('vfsScopeBase') : t('vfsScopeOverlay')
  const evidence = receipt.native_precedence_evidence.status === 'scoped_passed'
    ? t('vfsNativeScoped')
    : receipt.native_precedence_evidence.status === 'unverified'
      ? t('vfsNativeUnverified')
      : t('notApplicable')
  return t('vfsReceiptSummary', {
    scope,
    sources: receipt.sources.length,
    conflicts: receipt.conflict_count,
    hash: receipt.winner_set_sha256.slice(0, 12),
    evidence,
  })
})
const assetPackRuntimeBoundary = computed(() => (
  loadedAssetPack.value?.pack.vfs_receipt.scope === 'resolved_overlay'
    ? t('resolvedOverlayBoundary')
    : t('noLoadConfiguration')
))
const webAssetCache = new Map<string, DecodedDds>()
let webFitIndexCache: {
  pack: LoadedWebAssetPack
  promise: ReturnType<typeof readWebFitIndex>
} | undefined
const targetImage = ref<DecodedFitImage>()
const fitBusy = ref(false)
const fitStatus = ref('请选择一张图片')
const fitResult = ref<ImageFitResult>()
const fitWebGlScore = ref<WebGlScore | null>(null)
// Six layers was an early smoke-test default and produces visibly unrelated
// portraits. Start at the already supported 1024-instance quality point; the
// field remains freely editable and is never clamped to this value.
const fitLayerBudget = ref(1_024)
const fitProgressPercent = ref(0)
const fitProgressLabel = ref('等待开始')
const fitTaskState = ref<FitTaskState>('idle')
// Worker checkpoints contain large typed arrays and must remain structured-
// cloneable; deep Vue proxies cannot be sent back through postMessage.
const fitCheckpoint = shallowRef<ImageFitCheckpoint>()
const recoverableFitCheckpoint = shallowRef<PersistedFitCheckpoint>()
const fitCheckpointPersistenceStatus = ref<'empty' | 'pending' | 'saved' | 'failed'>('empty')
const fitCheckpointEstimatedBytes = ref(0)
const fitStorageEstimate = ref<BrowserStorageEstimate>()
const fitStorageFailureKind = ref<BrowserStorageFailureKind | ''>('')
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
let fitRevision = 0
let fitCheckpointSaveTimer: number | undefined
let pendingFitCheckpoint: ImageFitCheckpoint | undefined
let fitCheckpointStorageQueue = Promise.resolve()
let fitPruneWorker: Worker | null = null
let fitPruneRunId = 0
const INSTANCE_EDITOR_WINDOW_SIZE = 32
const OUTPUT_PREVIEW_CHARACTER_LIMIT = 64 * 1024
const HISTORY_MAX_BYTES = 16 * 1024 * 1024
const HISTORY_MAX_ENTRIES = 32
const HISTORY_DEBOUNCE_MS = 450
const AUTOSAVE_DEBOUNCE_MS = 1_000
const instanceWindowStart = ref(0)
const selectedInstanceIndex = ref(0)
const visualGuidesVisible = ref(false)
const visualTransformMode = ref<'move' | 'scale' | 'rotate' | null>(null)
const shieldElement = ref<HTMLElement>()
let historyApplying = false
let pendingHistorySource = ''
let historyTimer: number | undefined
let autosaveTimer: number | undefined
let autosaveReady = false
let autosaveGeneration = 0
let autosaveRevision = 0
let autosaveQueue = Promise.resolve()

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
const undoHistoryBytes = computed(() => undoHistory.value.reduce((sum, item) => sum + item.utf8Bytes, 0))
const redoHistoryBytes = computed(() => redoHistory.value.reduce((sum, item) => sum + item.utf8Bytes, 0))
const activeFitCompression = computed(() => (
  fitCompressionSource.value === output.value ? fitCompressionEvidence.value : undefined
))
const activeFitPrune = computed(() => (
  fitPruneSource.value === output.value ? fitPruneEvidence.value : undefined
))
const fitEvidenceJson = computed(() => {
  if (!fitResult.value) return ''
  const { layerLosses, selectedAssetSha256, ...provenance } = fitResult.value.provenance
  const paretoCandidates = fitResult.value.paretoCandidates.map((candidate) => {
    const candidateSource = serializeCoatOfArms(candidate.coatOfArms)
    return {
      metrics: candidate.metrics,
      reconstructionMode: candidate.reconstructionMode,
      textureNames: candidate.textureNames,
      multiscaleMetrics: candidate.multiscaleMetrics,
      stats: coatOfArmsDocumentStats(candidate.coatOfArms, candidateSource),
    }
  })
  return JSON.stringify({
    metrics: fitResult.value.metrics,
    paretoCandidates,
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
const selectedInstance = computed(() => activeEmblem.value?.instances[selectedInstanceIndex.value])
const visualTransformStyle = computed(() => {
  const instance = selectedInstance.value
  if (!instance) return {}
  return {
    left: `${instance.position[0] * 100}%`,
    top: `${instance.position[1] * 100}%`,
    width: `${Math.max(18, Math.abs(instance.scale[0]) * 260)}px`,
    height: `${Math.max(18, Math.abs(instance.scale[1]) * 260)}px`,
    transform: `translate(-50%, -50%) rotate(${instance.rotation}deg)`,
  }
})
const comparisonRows = computed(() => comparisonCandidates.value.map((candidate) => ({
  ...candidate,
  current: candidate.source === output.value,
  dominance: candidateDominance(candidate, comparisonCandidates.value),
})))
const localizedSyntaxCapabilityRows = computed(() => syntaxCapabilityRows.map((row) => (
  locale.value === 'en' ? { ...row, ...row.english } : row
)))
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
      texturedEmblems: texturedEmblemTextures.value,
      surfaceMask: surfaceMask.value,
    },
    shaderNamedColors.value,
  )
  return rendered ? renderedCoatOfArmsToDataUrl(rendered) : ''
})
// Large documents deliberately avoid a synchronous full redraw on every
// numeric edit. A completed fit, however, already represents an immutable
// comparison candidate. Keep its one-time canonical render and reuse the
// exact same pixels in both the main preview and the comparison card. The
// source equality check makes the snapshot disappear as soon as the user
// edits the model, so a stale candidate can never masquerade as the current
// composition.
const currentCandidatePreviewUrl = computed(() => (
  comparisonRows.value.find((candidate) => candidate.current)?.previewUrl ?? ''
))
const canonicalPreviewUrl = computed(() => renderedPreviewUrl.value || currentCandidatePreviewUrl.value)
const canonicalPreviewIsCandidateSnapshot = computed(() => (
  !renderedPreviewUrl.value && Boolean(currentCandidatePreviewUrl.value)
))
// The fit report and editor must never maintain independent render products.
// Both surfaces display the same canonical shader-model frame so their pixels,
// resolution, surface mask and named-color interpretation cannot drift.
const fitPreviewUrl = computed(() => fitResult.value ? canonicalPreviewUrl.value : '')

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

function fitMetricContract(result: ImageFitResult): string | undefined {
  if (!targetImage.value) return undefined
  return [
    targetImage.value.sha256,
    result.provenance.scoringContract,
    result.provenance.rendererContract,
    result.provenance.resolution,
    result.provenance.surfaceMaskApplied ? 'surface-mask:on' : 'surface-mask:off',
  ].join(':')
}

function currentFitMetrics(): { metrics: ImageFitMetrics, metricContract: string } | undefined {
  const result = fitResult.value
  if (
    !result
    || activeFitCompression.value
    || activeFitPrune.value
    || serializeCoatOfArms(result.coatOfArms) !== output.value
  ) return undefined
  const metricContract = fitMetricContract(result)
  return metricContract ? { metrics: { ...result.metrics }, metricContract } : undefined
}

function candidateDisplayName(candidate: CoatOfArmsComparisonCandidate): string {
  return candidate.automaticFitIndex === undefined
    ? uiText(candidate.name)
    : t('fitCandidateName', { index: candidate.automaticFitIndex + 1 })
}

function captureComparisonCandidate(
  name?: string,
  fitEvidence = currentFitMetrics(),
  notify = true,
) {
  const existingIndex = comparisonCandidates.value.findIndex((candidate) => candidate.source === output.value)
  const candidate: CoatOfArmsComparisonCandidate = {
    id: existingIndex >= 0
      ? comparisonCandidates.value[existingIndex].id
      : `candidate-${++comparisonCandidateSequence}`,
    name: name ?? (existingIndex >= 0
      ? comparisonCandidates.value[existingIndex].name
      : `候选 ${comparisonCandidates.value.length + 1}`),
    source: output.value,
    stats: coatOfArmsDocumentStats(coatOfArms.value, output.value),
    metrics: fitEvidence ? { ...fitEvidence.metrics } : undefined,
    metricContract: fitEvidence?.metricContract,
    previewUrl: largeDocumentPreviewDeferred.value ? undefined : renderedPreviewUrl.value,
  }
  if (existingIndex >= 0) {
    comparisonCandidates.value.splice(existingIndex, 1, candidate)
    if (notify) ElMessage.info('当前构图已在候选区，已刷新快照和可比指标')
    return
  }
  if (comparisonCandidates.value.length >= MAX_COMPARISON_CANDIDATES) {
    if (notify) ElMessage.warning('候选对比区按 Beta 合同保留 1–3 项；请先删除一个候选')
    return
  }
  comparisonCandidates.value.push(candidate)
  if (notify) ElMessage.success(`已保存${candidate.name}；候选源码与当前完整模型一致`)
}

async function activateComparisonCandidate(candidate: CoatOfArmsComparisonCandidate) {
  const parsed = parseCoatOfArms(candidate.source)
  if (parsed.diagnostics.some((item) => item.severity === 'error')) {
    ElMessage.error('候选源码重新解析失败，未改动当前构图')
    return
  }
  coatOfArms.value = parsed.coatOfArms
  source.value = candidate.source
  diagnostics.value = parsed.diagnostics
  selectedEmblem.value = 0
  selectedInstanceIndex.value = 0
  instanceWindowStart.value = 0
  fitResult.value = undefined
  fitCompressionEvidence.value = undefined
  fitCompressionSource.value = ''
  fitPruneEvidence.value = undefined
  fitPruneSource.value = ''
  await loadCurrentTexturePreviews()
  ElMessage.success(`已载入${candidate.name}；完整源码进入当前编辑模型`)
}

async function copyComparisonCandidate(candidate: CoatOfArmsComparisonCandidate) {
  try {
    await navigator.clipboard.writeText(candidate.source)
    ElMessage.success(`已复制${candidateDisplayName(candidate)}的完整 CK3 代码`)
  } catch (error) {
    ElMessage.error(`剪贴板写入失败：${errorMessage(error)}`)
  }
}

function removeComparisonCandidate(candidateId: string) {
  comparisonCandidates.value = comparisonCandidates.value.filter((candidate) => candidate.id !== candidateId)
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
    if (loadedAssetPack.value) void loadCurrentTexturePreviews()
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

function openFitCheckpointFilePicker() {
  fitCheckpointFileInput.value?.click()
}

async function exportFitCheckpointFile() {
  const checkpoint = fitCheckpoint.value
  if (!checkpoint) {
    ElMessage.warning('当前还没有可导出的安全 checkpoint')
    return
  }
  try {
    const record = checkpointRecord(checkpoint)
    const text = await serializePortableFitCheckpoint(record)
    downloadTextFile(
      `ck3-coat-of-arms-fit-${record.savedAt.replaceAll(':', '-')}.coa-fit-checkpoint.json`,
      text,
      'application/json;charset=utf-8',
    )
    ElMessage.success('便携拟合 checkpoint 已导出；文件包含 SHA-256 完整性绑定')
  } catch (error) {
    ElMessage.error(`便携拟合 checkpoint 导出失败：${errorMessage(error)}`)
  }
}

async function importFitCheckpointFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    if (fitBusy.value || fitTaskState.value === 'paused') {
      throw new Error('请先取消当前拟合，再导入另一个 checkpoint')
    }
    if (file.size > PORTABLE_FIT_CHECKPOINT_MAX_BYTES) {
      throw new Error('便携拟合 checkpoint 超过 24 MiB 安全上限')
    }
    const record = await parsePortableFitCheckpoint(await file.text())
    await refreshFitStorageEstimate(record)
    recoverableFitCheckpoint.value = record
    fitCheckpointPersistenceStatus.value = 'pending'
    try {
      await enqueueFitCheckpointStorage(() => savePersistedFitCheckpoint(record))
      fitCheckpointPersistenceStatus.value = 'saved'
      fitStorageFailureKind.value = ''
      ElMessage.success('便携拟合 checkpoint 已校验并写入浏览器恢复槽')
    } catch (error) {
      fitCheckpointPersistenceStatus.value = 'failed'
      fitStorageFailureKind.value = classifyBrowserStorageFailure(error)
      ElMessage.warning(`checkpoint 已在当前标签页校验，可直接恢复；${storageFailureGuidance(error)}`)
    }
  } catch (error) {
    ElMessage.error(`便携拟合 checkpoint 导入失败：${errorMessage(error)}`)
  } finally {
    input.value = ''
  }
}

function sourceEntry(value: string) {
  return { source: value, utf8Bytes: new TextEncoder().encode(value).length }
}

function pushBoundedHistory(stack: { source: string, utf8Bytes: number }[], sourceValue: string) {
  const entry = sourceEntry(sourceValue)
  if (entry.utf8Bytes > HISTORY_MAX_BYTES) {
    historyNotice.value = `单个历史快照超过 ${(HISTORY_MAX_BYTES / 1024 / 1024).toFixed(0)} MiB，未加入撤销栈；当前文档仍保留`
    return
  }
  if (stack.at(-1)?.source === entry.source) return
  stack.push(entry)
  let bytes = stack.reduce((sum, item) => sum + item.utf8Bytes, 0)
  while (stack.length > HISTORY_MAX_ENTRIES || bytes > HISTORY_MAX_BYTES) {
    bytes -= stack.shift()!.utf8Bytes
  }
}

function flushPendingHistory() {
  if (!pendingHistorySource) return
  pushBoundedHistory(undoHistory.value, pendingHistorySource)
  pendingHistorySource = ''
  historyPending.value = false
  if (historyTimer !== undefined) window.clearTimeout(historyTimer)
  historyTimer = undefined
  historyNotice.value = `${undoHistory.value.length} 个撤销点 · ${(undoHistoryBytes.value / 1024 / 1024).toFixed(1)} MiB / 16 MiB`
}

function applyHistorySource(value: string) {
  const parsed = parseCoatOfArms(value)
  if (parsed.diagnostics.some((item) => item.severity === 'error')) {
    throw new Error('历史快照无法重新解析')
  }
  historyApplying = true
  try {
    coatOfArms.value = parsed.coatOfArms
    source.value = value
    diagnostics.value = parsed.diagnostics
    selectedEmblem.value = Math.min(selectedEmblem.value, Math.max(0, parsed.coatOfArms.coloredEmblems.length - 1))
    instanceWindowStart.value = 0
  } finally {
    historyApplying = false
  }
  scheduleAutosave()
}

function undoEdit() {
  flushPendingHistory()
  const previous = undoHistory.value.pop()
  if (!previous) return
  pushBoundedHistory(redoHistory.value, output.value)
  try {
    applyHistorySource(previous.source)
    historyNotice.value = `已撤销 · ${undoHistory.value.length} 个撤销点 / ${redoHistory.value.length} 个重做点`
  } catch (error) {
    pushBoundedHistory(undoHistory.value, previous.source)
    ElMessage.error(`撤销失败：${errorMessage(error)}`)
  }
}

function redoEdit() {
  const next = redoHistory.value.pop()
  if (!next) return
  pushBoundedHistory(undoHistory.value, output.value)
  try {
    applyHistorySource(next.source)
    historyNotice.value = `已重做 · ${undoHistory.value.length} 个撤销点 / ${redoHistory.value.length} 个重做点`
  } catch (error) {
    pushBoundedHistory(redoHistory.value, next.source)
    ElMessage.error(`重做失败：${errorMessage(error)}`)
  }
}

function currentAssetPackReceipt() {
  const loaded = loadedAssetPack.value
  return loaded ? {
    packId: loaded.pack.pack_id,
    manifestSha256: loaded.manifestSha256,
    ck3Build: loaded.pack.ck3_build,
    vfsScope: loaded.pack.vfs_receipt.scope,
    vfsWinnerSetSha256: loaded.pack.vfs_receipt.winner_set_sha256,
  } : undefined
}

function scheduleAutosave() {
  if (!autosaveReady) return
  const generation = ++autosaveGeneration
  autosaveStatus.value = '等待自动保存'
  if (autosaveTimer !== undefined) window.clearTimeout(autosaveTimer)
  autosaveTimer = window.setTimeout(() => {
    autosaveTimer = undefined
    autosaveQueue = autosaveQueue.then(async () => {
      if (generation !== autosaveGeneration) return
      const project = await createCoatOfArmsProject(coatOfArms.value, {
        revision: ++autosaveRevision,
        selectedEmblem: selectedEmblem.value,
        assetPack: currentAssetPackReceipt(),
      })
      if (generation !== autosaveGeneration) return
      const text = serializeCoatOfArmsProject(project)
      await saveAutosaveProject(text)
      if (generation === autosaveGeneration) {
        autosaveStatus.value = `已自动保存 ${project.ck3Source.stats.drawnInstances.toLocaleString()} 实例 · 单槽覆盖`
      }
    }).catch((error) => {
      if (generation === autosaveGeneration) autosaveStatus.value = `自动保存失败：${errorMessage(error)}`
    })
  }, AUTOSAVE_DEBOUNCE_MS)
}

async function discoverAutosave() {
  try {
    const text = await loadAutosaveProject()
    if (!text) {
      autosaveStatus.value = '没有可恢复的自动保存'
      return
    }
    recoverableAutosave.value = await parseCoatOfArmsProject(text)
    autosaveRevision = recoverableAutosave.value.revision
    autosaveStatus.value = `发现 ${recoverableAutosave.value.ck3Source.stats.drawnInstances.toLocaleString()} 实例的自动保存`
  } catch (error) {
    autosaveStatus.value = `自动保存不可读：${errorMessage(error)}`
  } finally {
    autosaveReady = true
  }
}

async function restoreAutosave() {
  const project = recoverableAutosave.value
  if (!project) return
  historyApplying = true
  try {
    coatOfArms.value = project.coatOfArms
    source.value = serializeCoatOfArms(project.coatOfArms)
    diagnostics.value = []
    selectedEmblem.value = project.selectedEmblem
    instanceWindowStart.value = 0
  } finally {
    historyApplying = false
  }
  recoverableAutosave.value = undefined
  await loadCurrentTexturePreviews()
  scheduleAutosave()
  ElMessage.success(`已恢复自动保存：${project.ck3Source.stats.drawnInstances.toLocaleString()} 个实例`)
}

async function discardAutosave() {
  try {
    await clearAutosaveProject()
    recoverableAutosave.value = undefined
    autosaveGeneration += 1
    autosaveStatus.value = '已丢弃自动保存'
  } catch (error) {
    ElMessage.error(`无法丢弃自动保存：${errorMessage(error)}`)
  }
}

async function exportProject() {
  projectFileBusy.value = true
  try {
    const loaded = loadedAssetPack.value
    const project = await createCoatOfArmsProject(coatOfArms.value, {
      selectedEmblem: selectedEmblem.value,
      assetPack: loaded ? currentAssetPackReceipt() : undefined,
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
  selectedInstanceIndex.value = 0
}

function selectEmblemIndex(index: number) {
  selectedEmblem.value = Math.min(
    Math.max(0, Math.floor(index)),
    Math.max(0, coatOfArms.value.coloredEmblems.length - 1),
  )
  selectedInstanceIndex.value = 0
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
  selectedInstanceIndex.value = activeEmblem.value.instances.length - 1
  moveInstanceWindow(activeEmblem.value.instances.length - INSTANCE_EDITOR_WINDOW_SIZE)
}

function removeActiveInstance(index: number) {
  if (!activeEmblem.value) return
  activeEmblem.value.instances.splice(index, 1)
  selectedInstanceIndex.value = Math.min(
    selectedInstanceIndex.value,
    Math.max(0, activeEmblem.value.instances.length - 1),
  )
  moveInstanceWindow(boundedInstanceWindowStart.value)
}

function selectInstanceForVisualEdit(index: number) {
  selectedInstanceIndex.value = Math.min(
    Math.max(0, Math.floor(index)),
    Math.max(0, (activeEmblem.value?.instances.length ?? 1) - 1),
  )
  visualGuidesVisible.value = true
}

interface VisualTransformGesture {
  mode: 'move' | 'scale' | 'rotate'
  pointerId: number
  element: HTMLElement
  width: number
  height: number
  centerX: number
  centerY: number
  startClientX: number
  startClientY: number
  startPosition: [number, number]
  startScale: [number, number]
  startRotation: number
  startDistance: number
  startAngle: number
  historySource: string
}

let visualTransformGesture: VisualTransformGesture | undefined

function roundedTransformValue(value: number, precision = 6) {
  return Number(value.toFixed(precision))
}

function beginVisualTransform(mode: VisualTransformGesture['mode'], event: PointerEvent) {
  const instance = selectedInstance.value
  const shield = shieldElement.value
  if (!instance || !shield) return
  event.preventDefault()
  const rect = shield.getBoundingClientRect()
  const width = shield.clientWidth
  const height = shield.clientHeight
  if (width <= 0 || height <= 0) return
  flushPendingHistory()
  const contentLeft = rect.left + shield.clientLeft
  const contentTop = rect.top + shield.clientTop
  const centerX = contentLeft + instance.position[0] * width
  const centerY = contentTop + instance.position[1] * height
  const dx = event.clientX - centerX
  const dy = event.clientY - centerY
  const element = event.currentTarget as HTMLElement
  element.setPointerCapture?.(event.pointerId)
  visualTransformGesture = {
    mode,
    pointerId: event.pointerId,
    element,
    width,
    height,
    centerX,
    centerY,
    startClientX: event.clientX,
    startClientY: event.clientY,
    startPosition: [...instance.position],
    startScale: [...instance.scale],
    startRotation: instance.rotation,
    startDistance: Math.max(1, Math.hypot(dx, dy)),
    startAngle: Math.atan2(dy, dx),
    historySource: output.value,
  }
  visualTransformMode.value = mode
}

function updateVisualTransform(event: PointerEvent) {
  const gesture = visualTransformGesture
  const instance = selectedInstance.value
  if (!gesture || !instance || gesture.pointerId !== event.pointerId) return
  event.preventDefault()
  if (gesture.mode === 'move') {
    instance.position = [
      roundedTransformValue(Math.min(1, Math.max(0,
        gesture.startPosition[0] + (event.clientX - gesture.startClientX) / gesture.width,
      ))),
      roundedTransformValue(Math.min(1, Math.max(0,
        gesture.startPosition[1] + (event.clientY - gesture.startClientY) / gesture.height,
      ))),
    ]
    return
  }
  const dx = event.clientX - gesture.centerX
  const dy = event.clientY - gesture.centerY
  if (gesture.mode === 'scale') {
    const factor = Math.max(0.001, Math.hypot(dx, dy) / gesture.startDistance)
    instance.scale = [
      roundedTransformValue((gesture.startScale[0] || 0.001) * factor),
      roundedTransformValue((gesture.startScale[1] || 0.001) * factor),
    ]
    return
  }
  let delta = (Math.atan2(dy, dx) - gesture.startAngle) * 180 / Math.PI
  if (delta > 180) delta -= 360
  if (delta < -180) delta += 360
  instance.rotation = roundedTransformValue(gesture.startRotation + delta, 3)
}

function finishVisualTransform(event: PointerEvent) {
  const gesture = visualTransformGesture
  if (!gesture || gesture.pointerId !== event.pointerId) return
  updateVisualTransform(event)
  if (gesture.element.hasPointerCapture?.(event.pointerId)) {
    gesture.element.releasePointerCapture(event.pointerId)
  }
  visualTransformGesture = undefined
  visualTransformMode.value = null
  flushPendingHistory()
}

function parseMask(value: string) {
  if (!activeEmblem.value) return
  activeEmblem.value.mask = value.trim()
    ? value.trim().split(/[\s,]+/).map(Number)
    : []
}

function markRootColorExplicit(index: number) {
  if (coatOfArms.value.rootPresence) coatOfArms.value.rootPresence.colors[index] = true
}

function errorMessage(error: unknown): string {
  return uiText(error instanceof Error ? error.message : String(error))
}

function readCachedWebFitIndex(loaded: LoadedWebAssetPack) {
  if (webFitIndexCache?.pack === loaded) return webFitIndexCache.promise
  const cache = {
    pack: loaded,
    promise: readWebFitIndex(loaded),
  }
  webFitIndexCache = cache
  cache.promise.catch(() => {
    if (webFitIndexCache === cache) webFitIndexCache = undefined
  })
  return cache.promise
}

function packEntry(kind: 'pattern' | 'colored_emblem' | 'textured_emblem', name: string): WebAssetPackEntry | undefined {
  return loadedAssetPack.value?.pack.assets.find((item) => item.kind === kind && item.name === name)
}

async function readPackTexture(item: WebAssetPackEntry): Promise<DecodedDds> {
  const cached = webAssetCache.get(item.asset_sha256)
  if (cached) return cached
  if (!loadedAssetPack.value) throw new Error('独立素材包尚未载入')
  const decoded = await readWebAsset(loadedAssetPack.value, item)
  webAssetCache.set(item.asset_sha256, decoded)
  return decoded
}

async function activateStandaloneAssetPack(
  loaded: LoadedWebAssetPack,
  notify = true,
  local = false,
) {
    const patterns = loaded.pack.assets.filter(
      (item) => item.kind === 'pattern' && item.registration === 'designer_manifest',
    )
    const emblems = loaded.pack.assets.filter(
      (item) => item.kind === 'colored_emblem' && item.registration === 'designer_manifest',
    )
    const texturedDefault = loaded.pack.assets.find(
      (item) => item.kind === 'textured_emblem' && item.name === '_default.dds',
    )
    const mask = loaded.pack.assets.find((item) => item.kind === 'surface_mask')
    if (!patterns.length || !emblems.length || !texturedDefault || !mask) {
      throw new Error('素材包缺少已注册 pattern、emblem、textured emblem 或 surface mask')
    }
    loadedAssetPack.value = loaded
    webFitIndexCache = undefined
    webAssetCache.clear()
    patternResources.value = patterns
    emblemResources.value = emblems
    shaderNamedColors.value = loaded.pack.named_colors
    const [decodedSurfaceMask, decodedTexturedDefault] = await Promise.all([
      readPackTexture(mask),
      readPackTexture(texturedDefault),
    ])
    surfaceMask.value = decodedSurfaceMask
    texturedEmblemTextures.value = { '_default.dds': decodedTexturedDefault }
    texturedDefaultPreviewUrl.value = decodedDdsToDataUrl(decodedTexturedDefault)
    // The complete 1,577-entry RGBA fit index is intentionally lazy. Loading it
    // during application startup competes with editing, autosave and safe image
    // decode on constrained devices. fitTargetImage() reads and verifies the
    // same index before starting a fit, where its cost belongs.
    shaderSourceCount.value = 5
    const inventory = loaded.pack.inventory
    assetPackStatus.value = `${loaded.pack.pack_id} · ${patterns.length} 注册 pattern · ${emblems.length} 注册 emblem${inventory ? ` · ${inventory.source_dds_total} DDS 全盘清单` : ''} · ${loaded.manifestSha256.slice(0, 12)}`
    if (notify) ElMessage.success(local ? t('localPackLoaded') : t('staticPackLoaded'))
    await loadCurrentTexturePreviews()
}

async function loadStandaloneAssetPack(notify = true) {
  assetPackBusy.value = true
  try {
    await activateStandaloneAssetPack(await loadWebAssetPack(defaultAssetPackUrl), notify)
  } catch (error) {
    loadedAssetPack.value = undefined
    webFitIndexCache = undefined
    assetPackStatus.value = `素材包不可用：${errorMessage(error)}`
    if (notify) ElMessage.error(assetPackStatus.value)
  } finally {
    assetPackBusy.value = false
  }
}

function openAssetPackDirectoryPicker() {
  assetPackDirectoryInput.value?.click()
}

async function importAssetPackDirectory(event: Event) {
  const input = event.target as HTMLInputElement
  const files = [...(input.files ?? [])]
  input.value = ''
  if (!files.length) return
  assetPackBusy.value = true
  try {
    const loaded = await loadWebAssetPackFiles(files)
    await activateStandaloneAssetPack(loaded, true, true)
  } catch (error) {
    assetPackStatus.value = `素材包不可用：${errorMessage(error)}`
    ElMessage.error(assetPackStatus.value)
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
    fitStatus.value = `${file.name} · ${targetImage.value.originalWidth}×${targetImage.value.originalHeight} · ${(file.size / 1024).toFixed(1)} KiB · 只在浏览器内处理`
  } catch (error) {
    targetImage.value = undefined
    fitStatus.value = `图片拒绝：${errorMessage(error)}`
    ElMessage.error(fitStatus.value)
  } finally {
    input.value = ''
  }
}

function enqueueFitCheckpointStorage(operation: () => Promise<void>): Promise<void> {
  fitCheckpointStorageQueue = fitCheckpointStorageQueue
    .catch(() => undefined)
    .then(operation)
  return fitCheckpointStorageQueue
}

function checkpointRecord(checkpoint: ImageFitCheckpoint): PersistedFitCheckpoint {
  const input = targetImage.value
  const pack = loadedAssetPack.value
  if (!input || !pack) throw new Error('拟合 checkpoint 缺少当前输入或素材包')
  return createPersistedFitCheckpoint(checkpoint, input, {
    packId: pack.pack.pack_id,
    manifestSha256: pack.manifestSha256,
  })
}

function formatStorageBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return 'unknown'
  if (bytes < 1024) return `${bytes.toFixed(0)} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MiB`
}

function storageFailureGuidance(error: unknown): string {
  const kind = classifyBrowserStorageFailure(error)
  if (kind === 'quota') return t('storageFailureQuota')
  if (kind === 'blocked') return t('storageFailureBlocked')
  if (kind === 'unavailable') return t('storageFailureUnavailable')
  if (kind === 'aborted') return t('storageFailureAborted')
  return t('storageFailureUnknown', { detail: errorMessage(error) })
}

const fitStorageSummary = computed(() => {
  if (!fitCheckpointEstimatedBytes.value) return ''
  const checkpoint = formatStorageBytes(fitCheckpointEstimatedBytes.value)
  const estimate = fitStorageEstimate.value
  if (estimate?.status === 'available' && estimate.remainingBytes !== null) {
    return t('checkpointStorageEstimate', {
      checkpoint,
      remaining: formatStorageBytes(estimate.remainingBytes),
    })
  }
  return t('checkpointStorageEstimateUnavailable', { checkpoint })
})

const fitStorageFailureSummary = computed(() => {
  if (fitStorageFailureKind.value === 'quota') return t('storageFailureQuota')
  if (fitStorageFailureKind.value === 'blocked') return t('storageFailureBlocked')
  if (fitStorageFailureKind.value === 'unavailable') return t('storageFailureUnavailable')
  if (fitStorageFailureKind.value === 'aborted') return t('storageFailureAborted')
  if (fitStorageFailureKind.value === 'unknown') {
    return t('storageFailureUnknown', { detail: t('unavailable') })
  }
  return ''
})

async function refreshFitStorageEstimate(record: PersistedFitCheckpoint): Promise<void> {
  fitCheckpointEstimatedBytes.value = estimatePersistedFitCheckpointBytes(record)
  fitStorageEstimate.value = await inspectBrowserStorage()
}

function updateFitCheckpointSize(record: PersistedFitCheckpoint): void {
  fitCheckpointEstimatedBytes.value = estimatePersistedFitCheckpointBytes(record)
}

function scheduleStoredFitCheckpoint(checkpoint: ImageFitCheckpoint) {
  pendingFitCheckpoint = checkpoint
  fitCheckpointPersistenceStatus.value = 'pending'
  if (fitCheckpointSaveTimer !== undefined) window.clearTimeout(fitCheckpointSaveTimer)
  fitCheckpointSaveTimer = window.setTimeout(() => {
    fitCheckpointSaveTimer = undefined
    const pending = pendingFitCheckpoint
    if (!pending) return
    let record: PersistedFitCheckpoint
    try {
      record = checkpointRecord(pending)
      updateFitCheckpointSize(record)
    } catch {
      fitCheckpointPersistenceStatus.value = 'failed'
      return
    }
    void enqueueFitCheckpointStorage(async () => {
      await savePersistedFitCheckpoint(record)
      if (pendingFitCheckpoint === pending) {
        fitCheckpointPersistenceStatus.value = 'saved'
        fitStorageFailureKind.value = ''
      }
    }).catch((error) => {
      if (pendingFitCheckpoint === pending) {
        fitCheckpointPersistenceStatus.value = 'failed'
        fitStorageFailureKind.value = classifyBrowserStorageFailure(error)
      }
    })
  }, 500)
}

async function persistStoredFitCheckpointNow(): Promise<void> {
  if (fitCheckpointSaveTimer !== undefined) window.clearTimeout(fitCheckpointSaveTimer)
  fitCheckpointSaveTimer = undefined
  const checkpoint = pendingFitCheckpoint ?? fitCheckpoint.value
  if (!checkpoint) return
  fitCheckpointPersistenceStatus.value = 'pending'
  const record = checkpointRecord(checkpoint)
  await refreshFitStorageEstimate(record)
  await enqueueFitCheckpointStorage(() => savePersistedFitCheckpoint(record))
  if (pendingFitCheckpoint === checkpoint || fitCheckpoint.value === checkpoint) {
    fitCheckpointPersistenceStatus.value = 'saved'
    fitStorageFailureKind.value = ''
  }
}

function clearStoredFitCheckpoint(): Promise<void> {
  if (fitCheckpointSaveTimer !== undefined) window.clearTimeout(fitCheckpointSaveTimer)
  fitCheckpointSaveTimer = undefined
  pendingFitCheckpoint = undefined
  fitCheckpointPersistenceStatus.value = 'empty'
  fitCheckpointEstimatedBytes.value = 0
  fitStorageEstimate.value = undefined
  recoverableFitCheckpoint.value = undefined
  return enqueueFitCheckpointStorage(clearPersistedFitCheckpoint)
}

async function discoverFitCheckpoint() {
  try {
    const record = await loadPersistedFitCheckpoint()
    if (record) {
      await refreshFitStorageEstimate(record)
      recoverableFitCheckpoint.value = record
      fitCheckpointPersistenceStatus.value = 'saved'
      fitStorageFailureKind.value = ''
    }
  } catch (error) {
    fitCheckpointPersistenceStatus.value = 'failed'
    fitStorageFailureKind.value = classifyBrowserStorageFailure(error)
    fitStatus.value = `持久拟合 checkpoint 不可读：${storageFailureGuidance(error)}`
  }
}

async function restoreFitCheckpoint() {
  const record = recoverableFitCheckpoint.value
  const pack = loadedAssetPack.value
  if (!record || !pack) return
  if (
    record.assetPack.packId !== pack.pack.pack_id
    || record.assetPack.manifestSha256 !== pack.manifestSha256
  ) {
    ElMessage.error('持久拟合 checkpoint 所需的素材包版本未载入')
    return
  }
  fitRunId += 1
  fitRevision = 0
  targetImage.value = restorePersistedFitInput(record)
  fitLayerBudget.value = record.layerBudget
  fitCheckpoint.value = record.checkpoint
  pendingFitCheckpoint = record.checkpoint
  fitTaskState.value = 'paused'
  fitBusy.value = false
  coatOfArms.value = cloneCoatOfArmsForWorker(record.checkpoint.state.coatOfArms)
  source.value = serializeCoatOfArms(coatOfArms.value)
  diagnostics.value = []
  fitProgressPercent.value = Math.round(
    record.checkpoint.nextTileIndex / Math.max(1, record.checkpoint.tileCount) * 100,
  )
  fitProgressLabel.value = `已恢复持久 checkpoint · ${record.checkpoint.lane} ${record.checkpoint.nextTileIndex}/${record.checkpoint.tileCount}`
  fitStatus.value = '持久拟合 checkpoint 已恢复；继续前已校验输入、素材包、预算和搜索游标'
  recoverableFitCheckpoint.value = undefined
  await loadCurrentTexturePreviews()
}

async function discardFitCheckpoint() {
  try {
    await clearStoredFitCheckpoint()
    fitStorageFailureKind.value = ''
    ElMessage.info('已丢弃持久拟合 checkpoint')
  } catch (error) {
    fitStorageFailureKind.value = classifyBrowserStorageFailure(error)
    ElMessage.error(`无法丢弃持久拟合 checkpoint：${storageFailureGuidance(error)}`)
  }
}

function cancelImageFit(notify = true) {
  fitRunId += 1
  fitRevision += 1
  fitWorker?.terminate()
  fitWorker = null
  const wasActive = fitBusy.value || fitTaskState.value === 'paused'
  if (wasActive && notify) ElMessage.info('已取消图片拟合')
  if (wasActive) {
    fitProgressPercent.value = 0
    fitProgressLabel.value = notify ? '已取消' : '等待开始'
  }
  fitBusy.value = false
  fitCheckpoint.value = undefined
  void clearStoredFitCheckpoint().catch((error) => {
    fitStorageFailureKind.value = classifyBrowserStorageFailure(error)
    fitStatus.value = `拟合已取消，但旧 checkpoint 删除失败：${storageFailureGuidance(error)}`
  })
  fitTaskState.value = notify && wasActive ? 'cancelled' : 'idle'
}

async function pauseImageFit() {
  if (!fitBusy.value || !fitWorker || !fitCheckpoint.value) {
    ElMessage.warning('当前阶段还没有可恢复的安全 checkpoint')
    return
  }
  fitRevision += 1
  fitWorker.terminate()
  fitWorker = null
  fitBusy.value = false
  fitTaskState.value = 'paused'
  fitProgressPercent.value = Math.round(
    fitCheckpoint.value.nextTileIndex / Math.max(1, fitCheckpoint.value.tileCount) * 100,
  )
  fitProgressLabel.value = `已暂停 · ${fitCheckpoint.value.lane} ${fitCheckpoint.value.nextTileIndex}/${fitCheckpoint.value.tileCount}`
  fitStatus.value = '拟合已暂停；输入、素材包、配置、模型与原生块游标已保留在当前浏览器标签页'
  try {
    await persistStoredFitCheckpointNow()
    fitStatus.value = '拟合已暂停；checkpoint 已写入浏览器 IndexedDB，可在刷新后恢复'
    ElMessage.info('图片拟合已在安全 checkpoint 暂停并持久保存')
  } catch (error) {
    fitCheckpointPersistenceStatus.value = 'failed'
    fitStorageFailureKind.value = classifyBrowserStorageFailure(error)
    fitStatus.value = `拟合已暂停；内存 checkpoint 仍可继续，${storageFailureGuidance(error)}`
    ElMessage.warning(fitStatus.value)
  }
}

function resumeImageFit() {
  if (fitTaskState.value !== 'paused' || !fitCheckpoint.value) {
    ElMessage.warning('没有可恢复的拟合 checkpoint')
    return
  }
  void runImageFit(fitCheckpoint.value)
}

function cancelInstancePrune(notify = true) {
  fitPruneRunId += 1
  fitPruneWorker?.terminate()
  fitPruneWorker = null
  if (fitPruneBusy.value && notify) ElMessage.info('已取消零退化剪枝；当前编辑结果保持不变')
  fitPruneBusy.value = false
  fitPruneProgress.value = undefined
}

function cloneDecodedDdsForWorker(texture: DecodedDds): DecodedDds {
  return {
    width: texture.width,
    height: texture.height,
    fourCC: texture.fourCC,
    pixels: new Uint8ClampedArray(texture.pixels),
    mipmaps: texture.mipmaps?.map((mipmap) => ({
      width: mipmap.width,
      height: mipmap.height,
      pixels: new Uint8ClampedArray(mipmap.pixels),
    })),
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
    rootPresence: value.rootPresence ? {
      pattern: value.rootPresence.pattern,
      colors: [...value.rootPresence.colors],
    } : undefined,
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
    ElMessage.error(`无法执行零退化剪枝，缺少 ${missing.length} 个结果 DDS`)
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
    ElMessage.error(`零退化剪枝 Worker 失败：${message}`)
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
      ElMessage.error(`零退化剪枝失败：${event.data.error ?? 'unknown'}`)
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
    ElMessage.success(`零退化剪枝达到固定点：移除 ${pruned.receipt.removedInstances}，保留 ${pruned.receipt.drawnInstancesAfter}`)
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
      surfaceMask.value ? cloneDecodedDdsForWorker(surfaceMask.value) : undefined,
      Object.fromEntries(Object.entries(shaderNamedColors.value).map(([name, color]) => (
        [name, [...color]]
      ))),
      {
        mode: 'metric-pareto',
        searchResolution: 96,
        validationResolutions: [230, 512],
        numericLossTolerance: 1e-12,
        allowedVisualDifferenceBytes: 0,
        allowedCumulativeTotalLossIncrease: 0,
        allowedCumulativeEdgeLossIncrease: 0,
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

function fitTargetImage() {
  void runImageFit()
}

async function runImageFit(resumeCheckpoint?: ImageFitCheckpoint) {
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
  let runId: number
  let revision: number
  if (resumeCheckpoint) {
    runId = fitRunId
    revision = fitRevision + 1
  } else {
    cancelImageFit(false)
    runId = ++fitRunId
    revision = 1
    fitCheckpoint.value = undefined
  }
  fitRevision = revision
  fitBusy.value = true
  fitTaskState.value = 'preparing'
  if (!resumeCheckpoint) {
    fitResult.value = undefined
    fitCompressionEvidence.value = undefined
    fitCompressionSource.value = ''
    fitPruneEvidence.value = undefined
    fitPruneSource.value = ''
    fitWebGlScore.value = null
    fitProgressPercent.value = 0
  }
  fitProgressLabel.value = resumeCheckpoint ? '正在恢复安全 checkpoint' : '正在准备完整素材索引'
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
      const indexed = await readCachedWebFitIndex(loadedAssetPack.value)
      patternCandidates = indexed
        .filter((item) => item.entry.kind === 'pattern')
        .map((item) => ({
          name: item.entry.name,
          assetSha256: item.entry.asset_sha256,
          texture: item.texture,
          shapeFeatures: item.shapeFeatures,
        }))
      emblemCandidates = indexed
        .filter((item) => item.entry.kind === 'colored_emblem')
        .map((item) => ({
          name: item.entry.name,
          assetSha256: item.entry.asset_sha256,
          texture: item.texture,
          shapeFeatures: item.shapeFeatures,
        }))
    } else {
      [patternCandidates, emblemCandidates] = await Promise.all([
        Promise.all(patterns.map(toCandidate)),
        Promise.all(emblems.map(toCandidate)),
      ])
    }
    if (runId !== fitRunId || revision !== fitRevision) return
    fitStatus.value = `浏览器 Worker 正在执行透明度加权、轮廓粗筛和双路径残差重建；最多 ${layerBudget} 层，只保留严格改善层…`
    fitTaskState.value = 'running'
    const worker = new Worker(new URL('./domain/imageFitter.worker.ts', import.meta.url), { type: 'module' })
    fitWorker = worker
    const target = targetImage.value.image
    worker.onmessage = async (event: MessageEvent<FitWorkerResponse>) => {
      if (
        runId !== fitRunId
        || revision !== fitRevision
        || !isCurrentFitWorkerMessage(event.data, runId, revision)
      ) return
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
      if (event.data.kind === 'checkpoint') {
        fitCheckpoint.value = event.data.checkpoint
        scheduleStoredFitCheckpoint(event.data.checkpoint)
        return
      }
      worker.terminate()
      fitWorker = null
      if (!event.data.ok) {
        fitBusy.value = false
        fitTaskState.value = 'failed'
        fitProgressPercent.value = 0
        fitProgressLabel.value = '拟合失败'
        fitStatus.value = `拟合失败：${event.data.error}`
        ElMessage.error(fitStatus.value)
        return
      }
      let result = event.data.result
      const selectedPatternNames = new Set(result.paretoCandidates.map((item) => item.coatOfArms.pattern))
      const selectedPatternEntries = patterns.filter((item) => selectedPatternNames.has(item.name))
      const selectedEmblemNames = new Set(result.paretoCandidates.flatMap((candidate) => (
        candidate.coatOfArms.coloredEmblems.map((item) => item.texture)
      )))
      const selectedEmblemEntries = emblems.filter((item) => selectedEmblemNames.has(item.name))
      let selectedFullPatterns: (readonly [string, DecodedDds])[]
      let selectedFullEmblems: (readonly [string, DecodedDds])[]
      try {
        [selectedFullPatterns, selectedFullEmblems] = await Promise.all([
          Promise.all(selectedPatternEntries.map(async (item) => [item.name, await readPackTexture(item)] as const)),
          Promise.all(selectedEmblemEntries.map(async (item) => [item.name, await readPackTexture(item)] as const)),
        ])
      } catch (error) {
        if (runId !== fitRunId || revision !== fitRevision) return
        fitBusy.value = false
        fitTaskState.value = 'failed'
        fitProgressPercent.value = 0
        fitProgressLabel.value = '结果素材校验失败'
        fitStatus.value = `拟合已完成，但完整 DDS 校验失败：${errorMessage(error)}`
        ElMessage.error(fitStatus.value)
        return
      }
      if (runId !== fitRunId || revision !== fitRevision) return
      fitBusy.value = false
      fitTaskState.value = 'completed'
      fitCheckpoint.value = undefined
      void clearStoredFitCheckpoint().catch((error) => {
        fitStorageFailureKind.value = classifyBrowserStorageFailure(error)
        fitStatus.value = `拟合已完成，但旧 checkpoint 删除失败：${storageFailureGuidance(error)}`
      })
      fitProgressPercent.value = 100
      fitProgressLabel.value = `完成 · 选中 ${result.provenance.selectedLayers} 层`
      const selectedPatternTextures = Object.fromEntries(selectedFullPatterns)
      emblemTextures.value = Object.fromEntries(selectedFullEmblems)
      emblemPreviewUrls.value = Object.fromEntries(
        Object.entries(emblemTextures.value).map(([name, decoded]) => [name, decodedDdsToDataUrl(decoded)]),
      )
      try {
        result = finalizeImageFitWithFullAssets(
          result,
          target,
          {
            patterns: selectedPatternTextures,
            coloredEmblems: emblemTextures.value,
            surfaceMask: surfaceMask.value,
            patternAssetSha256: Object.fromEntries(selectedPatternEntries.map((item) => (
              [item.name, item.asset_sha256]
            ))),
            emblemAssetSha256: Object.fromEntries(selectedEmblemEntries.map((item) => (
              [item.name, item.asset_sha256]
            ))),
          },
          shaderNamedColors.value,
        ).result
      } catch (error) {
        fitBusy.value = false
        fitTaskState.value = 'failed'
        fitProgressPercent.value = 0
        fitProgressLabel.value = '完整 DDS 复评失败'
        fitStatus.value = `拟合搜索已完成，但导出素材复评失败：${errorMessage(error)}`
        ElMessage.error(fitStatus.value)
        return
      }
      fitResult.value = result
      coatOfArms.value = result.coatOfArms
      source.value = serializeCoatOfArms(result.coatOfArms)
      diagnostics.value = []
      selectedEmblem.value = 0
      const selectedPatternTexture = selectedPatternTextures[result.coatOfArms.pattern]
      patternTexture.value = selectedPatternTexture
      patternPreviewUrl.value = selectedPatternTexture ? decodedDdsToDataUrl(selectedPatternTexture) : ''
      const metricContract = fitMetricContract(result)
      if (metricContract) {
        const currentSource = serializeCoatOfArms(result.coatOfArms)
        comparisonCandidates.value = result.paretoCandidates.map((candidate, index) => {
          const candidateSource = serializeCoatOfArms(candidate.coatOfArms)
          const stats = coatOfArmsDocumentStats(candidate.coatOfArms, candidateSource)
          // The current fit result must always receive one canonical snapshot,
          // even when live redraw is deferred for a large document. Other large
          // alternatives may remain deferred until loaded; this keeps one fit
          // completion from synchronously rendering several 10,000-instance
          // documents while preserving exact top/card parity for the result
          // the user is actually viewing.
          const candidateRendered = stats.drawnInstances > 2_048 && candidateSource !== currentSource
            ? null
            : renderCoatOfArms(
                candidate.coatOfArms,
                {
                  pattern: selectedPatternTextures[candidate.coatOfArms.pattern],
                  coloredEmblems: emblemTextures.value,
                  surfaceMask: surfaceMask.value,
                },
                shaderNamedColors.value,
              )
          return {
            id: `candidate-${++comparisonCandidateSequence}`,
            name: `拟合候选 ${index + 1}`,
            automaticFitIndex: index,
            source: candidateSource,
            stats,
            metrics: { ...candidate.metrics },
            metricContract,
            previewUrl: candidateRendered ? renderedCoatOfArmsToDataUrl(candidateRendered) : undefined,
          }
        })
      }
      const normalizedTarget = resizeFitImage(target, result.provenance.resolution)
      const rendered = renderCoatOfArms(
        result.coatOfArms,
        {
          pattern: selectedPatternTexture,
          coloredEmblems: emblemTextures.value,
          surfaceMask: surfaceMask.value,
        },
        shaderNamedColors.value,
        result.provenance.resolution,
      )
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
      const batchStatus = result.provenance.batchSearch.status === 'active'
        ? `WebGL2 批量搜索 ${result.provenance.batchSearch.candidates} 候选 + CPU reference`
        : `CPU reference · WebGL2 批量搜索 ${result.provenance.batchSearch.status}`
      fitStatus.value = `完成 · ${reconstructionMode} · 从完整库评估 ${result.provenance.evaluatedCandidates} 个构图 · 选中 ${result.provenance.selectedLayers}/${result.provenance.layerBudget} 层 · 停止：${fitTerminationLabels[result.provenance.terminationReason]} · ${batchStatus}${fitWebGlScore.value ? ' · 最终 RGBA8 交叉评分' : ''}`
      ElMessage.success('多层原生元素构图已载入结构化编辑器，可继续调整并复制代码')
    }
    worker.onerror = (event) => {
      if (runId !== fitRunId || revision !== fitRevision) return
      worker.terminate()
      fitWorker = null
      fitBusy.value = false
      fitTaskState.value = 'failed'
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
      shapeFeatures: item.shapeFeatures ? {
        ...item.shapeFeatures,
        contentBounds: [...item.shapeFeatures.contentBounds],
        contentCenter: [...item.shapeFeatures.contentCenter],
        contentSpan: [...item.shapeFeatures.contentSpan],
        channelEnergy: [...item.shapeFeatures.channelEnergy],
        descriptor: new Float32Array(item.shapeFeatures.descriptor),
      } : undefined,
    }))
    const request: FitWorkerStartRequest = {
      protocol: FIT_WORKER_PROTOCOL,
      kind: 'start',
      runId,
      revision,
      args: [workerImage, workerCandidates(patternCandidates), workerCandidates(emblemCandidates), {
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
        inputSha256: targetImage.value.sha256,
        assetPackManifestSha256: loadedAssetPack.value.manifestSha256,
        surfaceMask: surfaceMask.value ? cloneDecodedDdsForWorker(surfaceMask.value) : undefined,
        namedColors: Object.fromEntries(Object.entries(shaderNamedColors.value).map(([name, color]) => (
          [name, [...color]]
        ))),
        resumeCheckpoint,
      }],
    }
    worker.postMessage(request)
  } catch (error) {
    if (runId !== fitRunId || revision !== fitRevision) return
    fitBusy.value = false
    fitTaskState.value = 'failed'
    fitProgressPercent.value = 0
    fitProgressLabel.value = '拟合失败'
    fitStatus.value = `拟合失败：${errorMessage(error)}`
    ElMessage.error(fitStatus.value)
  }
}

onMounted(() => {
  setLocale(locale.value)
  void loadStandaloneAssetPack(false)
  void discoverAutosave()
  void discoverFitCheckpoint()
})

watch(selectedEmblem, () => {
  instanceWindowStart.value = 0
})

async function readTexturePreview(
  kind: 'pattern' | 'colored_emblem' | 'textured_emblem',
  name: string,
): Promise<{ decoded: DecodedDds, preview: string }> {
  const staticEntry = packEntry(kind, name)
  if (!staticEntry) throw new Error(`独立素材包中没有 ${kind}/${name}`)
  const decoded = await readPackTexture(staticEntry)
  return { decoded, preview: decodedDdsToDataUrl(decoded) }
}

async function loadPatternTexture(name: string) {
  if (!name) return
  if (coatOfArms.value.rootPresence) coatOfArms.value.rootPresence.pattern = true
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
  const texturedNames = [...new Set(coatOfArms.value.texturedEmblems
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
    for (const name of texturedNames) {
      requests.push(readTexturePreview('textured_emblem', name).then(({ decoded, preview }) => {
        texturedEmblemTextures.value = { ...texturedEmblemTextures.value, [name]: decoded }
        if (name === '_default.dds') texturedDefaultPreviewUrl.value = preview
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
watch(output, (next, previous) => {
  if (historyApplying || next === previous) return
  if (!pendingHistorySource) pendingHistorySource = visualTransformGesture?.historySource ?? previous
  historyPending.value = true
  redoHistory.value = []
  if (historyTimer !== undefined) window.clearTimeout(historyTimer)
  historyTimer = visualTransformGesture
    ? undefined
    : window.setTimeout(flushPendingHistory, HISTORY_DEBOUNCE_MS)
  scheduleAutosave()
}, { flush: 'sync' })

watch(selectedEmblem, () => {
  selectedInstanceIndex.value = 0
})

watch(() => activeEmblem.value?.instances.length ?? 0, (length) => {
  selectedInstanceIndex.value = Math.min(selectedInstanceIndex.value, Math.max(0, length - 1))
})
</script>

<template>
  <el-config-provider :locale="elementPlusLocale">
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">{{ t('appEyebrow') }}</p>
        <h1>{{ t('appTitle') }}</h1>
        <p class="subtitle">{{ t('appSubtitle') }}</p>
      </div>
      <div class="top-actions">
        <el-tag effect="plain" data-testid="page-version">{{ t('pageVersion', { version: buildVersion }) }}</el-tag>
        <el-tag :type="loadedAssetPack ? 'success' : 'warning'" effect="plain">
          {{ loadedAssetPack ? t('standaloneBound') : t('standaloneWaiting') }}
        </el-tag>
        <el-select class="locale-select" :model-value="locale" :aria-label="t('language')" data-testid="locale-select" @update:model-value="chooseLocale">
          <el-option value="zh-CN" :label="t('chinese')" />
          <el-option value="en" :label="t('english')" />
        </el-select>
        <input
          ref="projectFileInput"
          class="hidden-file-input"
          data-testid="project-file-input"
          type="file"
          accept="application/json,.json"
          @change="importProject"
        >
        <el-button :loading="projectFileBusy" @click="openProjectFilePicker">{{ t('openProject') }}</el-button>
        <el-button :loading="projectFileBusy" @click="exportProject">{{ t('saveProject') }}</el-button>
        <el-button :disabled="!historyPending && !undoHistory.length" @click="undoEdit">{{ t('undo') }}</el-button>
        <el-button :disabled="!redoHistory.length" @click="redoEdit">{{ t('redo') }}</el-button>
        <el-tag effect="plain">{{ uiText(autosaveStatus) }}</el-tag>
        <el-button @click="reset">{{ t('reset') }}</el-button>
        <el-button type="primary" :disabled="errorCount > 0" @click="copyOutput">{{ t('copyCk3Code') }}</el-button>
      </div>
    </header>

    <section v-if="recoverableAutosave" class="autosave-recovery panel">
      <div>
        <strong>{{ t('recoverableProject') }}</strong>
        <span>{{ t('recoverableSummary', { savedAt: recoverableAutosave.savedAt, instances: recoverableAutosave.ck3Source.stats.drawnInstances.toLocaleString() }) }}</span>
      </div>
      <el-space>
        <el-button type="primary" @click="restoreAutosave">{{ t('restore') }}</el-button>
        <el-button @click="discardAutosave">{{ t('discard') }}</el-button>
      </el-space>
    </section>

    <section class="image-fit-panel panel">
      <div class="panel-title">
        <div><span class="step">00</span><h2>{{ t('imageFitTitle') }}</h2></div>
        <el-tag effect="plain" type="success">{{ t('localOnly') }}</el-tag>
      </div>
      <section v-if="recoverableFitCheckpoint" class="autosave-recovery" data-testid="fit-checkpoint-recovery">
        <div>
          <strong>{{ t('recoverableFitCheckpoint') }}</strong>
          <span>{{ t('recoverableFitCheckpointSummary', {
            savedAt: recoverableFitCheckpoint.savedAt,
            name: recoverableFitCheckpoint.input.name,
            budget: recoverableFitCheckpoint.layerBudget,
            completed: recoverableFitCheckpoint.checkpoint.nextTileIndex,
            total: recoverableFitCheckpoint.checkpoint.tileCount,
          }) }}</span>
        </div>
        <el-space>
          <el-button type="primary" :disabled="!loadedAssetPack" @click="restoreFitCheckpoint">{{ t('restoreFitCheckpoint') }}</el-button>
          <el-button @click="discardFitCheckpoint">{{ t('discardFitCheckpoint') }}</el-button>
        </el-space>
      </section>
      <div class="image-fit-grid">
        <label class="image-drop">
          <input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" @change="selectTargetImage">
          <img v-if="targetImage" :src="targetImage.previewUrl" :alt="t('imageAlt')">
          <span v-else>{{ t('chooseImage') }}<br><small>{{ t('imageLimits') }}</small></span>
        </label>
        <div class="fit-controls">
          <strong>{{ t('standalonePack') }}</strong>
          <p>{{ uiText(assetPackStatus) }}</p>
          <p data-testid="asset-pack-vfs-receipt">{{ assetPackVfsStatus }}</p>
          <input
            ref="assetPackDirectoryInput"
            class="hidden-file-input"
            data-testid="asset-pack-directory-input"
            type="file"
            webkitdirectory
            multiple
            @change="importAssetPackDirectory"
          >
          <input
            ref="fitCheckpointFileInput"
            class="hidden-file-input"
            data-testid="fit-checkpoint-file-input"
            type="file"
            accept="application/json,.json"
            @change="importFitCheckpointFile"
          >
          <div class="fit-actions">
            <el-button :loading="assetPackBusy" @click="loadStandaloneAssetPack()">{{ t('reloadPack') }}</el-button>
            <el-button :loading="assetPackBusy" @click="openAssetPackDirectoryPicker">{{ t('importPackDirectory') }}</el-button>
          </div>
          <small class="fit-budget-note">{{ t('importPackBoundary') }}</small>
          <div class="fit-budget">
            <span>{{ t('maxImprovingLayers') }}</span>
            <el-input-number v-model="fitLayerBudget" :min="1" :step="1" />
          </div>
          <small class="fit-budget-note">{{ t('budgetHelp') }}</small>
          <small class="fit-budget-note">{{ t('budgetPlaneHelp') }}</small>
          <div class="fit-actions">
            <el-button type="primary" :loading="fitBusy" :disabled="assetPackBusy || fitPruneBusy || !targetImage || !loadedAssetPack" @click="fitTargetImage">
              {{ t('startLocalFit') }}
            </el-button>
            <el-button :disabled="!fitBusy || !fitCheckpoint" @click="pauseImageFit">{{ t('pauseFit') }}</el-button>
            <el-button v-if="fitTaskState === 'paused'" type="primary" plain @click="resumeImageFit">{{ t('resumeFit') }}</el-button>
            <el-button :disabled="!fitBusy && fitTaskState !== 'paused'" @click="cancelImageFit()">{{ t('cancel') }}</el-button>
            <el-button :disabled="fitBusy || fitTaskState === 'paused'" @click="openFitCheckpointFilePicker">{{ t('importFitCheckpointFile') }}</el-button>
            <el-button :disabled="!fitCheckpoint" @click="exportFitCheckpointFile">{{ t('exportFitCheckpointFile') }}</el-button>
            <el-button :disabled="fitBusy || fitPruneBusy || !fitResult" @click="compressFitDocument">{{ t('compressBlocks') }}</el-button>
            <el-button :loading="fitPruneBusy" :disabled="fitBusy || fitPruneBusy || !fitResult" @click="pruneFitDocument">{{ t('exactPrune') }}</el-button>
            <el-button v-if="fitPruneBusy" @click="cancelInstancePrune()">{{ t('cancelPrune') }}</el-button>
          </div>
          <small class="fit-budget-note">{{ t('portableCheckpointHelp') }}</small>
        </div>
        <div
          class="fit-report"
          data-testid="fit-report"
          :data-fit-evidence="fitEvidenceJson"
          :data-fit-task-state="fitTaskState"
          :data-fit-checkpoint-persistence="fitCheckpointPersistenceStatus"
          :data-fit-storage-failure="fitStorageFailureKind"
          :data-fit-checkpoint-estimated-bytes="fitCheckpointEstimatedBytes"
        >
          <strong>{{ t('runStatus') }}</strong>
          <p>{{ uiText(fitStatus) }}</p>
          <div class="fit-progress">
            <el-progress
              :percentage="fitProgressPercent"
              :status="fitResult && !fitBusy ? 'success' : undefined"
              :stroke-width="10"
            />
            <small>{{ uiText(fitProgressLabel) }}{{ t('progressStageNote') }}</small>
            <small v-if="fitCheckpoint">
              {{ t('checkpointReady', { lane: fitCheckpoint.lane, completed: fitCheckpoint.nextTileIndex, total: fitCheckpoint.tileCount }) }} ·
              {{ fitCheckpointPersistenceStatus === 'saved' ? t('checkpointSaved') : fitCheckpointPersistenceStatus === 'failed' ? t('checkpointFailed') : t('checkpointPending') }}
            </small>
            <small v-if="fitStorageSummary">{{ fitStorageSummary }}</small>
            <small v-if="fitStorageFailureSummary" class="warning-text">{{ fitStorageFailureSummary }}</small>
          </div>
          <template v-if="fitResult">
            <div v-if="fitPruneProgress" class="fit-progress">
              <el-progress :percentage="fitPruneProgress.percent" :status="activeFitPrune ? 'success' : undefined" :stroke-width="8" />
              <small>{{ t('pruneProgress', { pass: fitPruneProgress.pass, completed: fitPruneProgress.completedInPass, total: fitPruneProgress.totalInPass, candidates: fitPruneProgress.evaluatedCandidates }) }}</small>
            </div>
            <div v-if="fitPreviewUrl" class="fit-result-image">
              <span>{{ t('fitPlane') }}</span>
              <img data-testid="fit-preview" :src="fitPreviewUrl" :alt="t('fitResultAlt')">
            </div>
            <dl>
              <div><dt>{{ t('totalLoss') }}</dt><dd>{{ fitResult.metrics.totalLoss.toFixed(5) }}</dd></div>
              <div><dt>{{ t('colorLoss') }}</dt><dd>{{ fitResult.metrics.colorLoss.toFixed(5) }}</dd></div>
              <div><dt>{{ t('edgeLoss') }}</dt><dd>{{ fitResult.metrics.edgeLoss.toFixed(5) }}</dd></div>
              <div><dt>{{ t('candidates') }}</dt><dd>{{ fitResult.provenance.evaluatedCandidates }}</dd></div>
              <div><dt>{{ t('shapeFeatureIndex') }}</dt><dd>{{ fitResult.provenance.shapeFeatureIndex.indexedAssets }} / {{ fitResult.provenance.shapeFeatureIndex.indexedAssets + fitResult.provenance.shapeFeatureIndex.fallbackAssets }}</dd></div>
              <div><dt>{{ t('userBudget') }}</dt><dd>{{ t('drawingInstances', { count: fitResult.provenance.layerBudget }) }}</dd></div>
              <div><dt>{{ t('actualInstances') }}</dt><dd>{{ fitResult.provenance.drawnInstances }}</dd></div>
              <div><dt>{{ t('logicalLayers') }}</dt><dd>{{ fitResult.provenance.logicalLayers }}</dd></div>
              <div><dt>{{ t('emblemBlocks') }}</dt><dd>{{ fitResult.provenance.coloredEmblemBlocks }}</dd></div>
              <div><dt>{{ t('instanceCount') }}</dt><dd>{{ fitResult.provenance.drawnInstances }}</dd></div>
              <div><dt>{{ t('codeSize') }}</dt><dd>{{ outputBytes }} UTF-8 bytes / {{ outputLines }} {{ t('lines') }}</dd></div>
              <template v-if="activeFitCompression">
                <div><dt>{{ t('safeCompressedBlocks') }}</dt><dd>{{ activeFitCompression.receipt.coloredEmblemBlocksBefore }} → {{ activeFitCompression.receipt.coloredEmblemBlocksAfter }}</dd></div>
                <div><dt>{{ t('safeCompressedInstances') }}</dt><dd>{{ activeFitCompression.receipt.drawnInstancesBefore }} → {{ activeFitCompression.receipt.drawnInstancesAfter }}</dd></div>
                <div><dt>{{ t('safeCompressedSize') }}</dt><dd>{{ activeFitCompression.receipt.utf8BytesBefore }} → {{ activeFitCompression.receipt.utf8BytesAfter }} bytes</dd></div>
                <div><dt>{{ t('compressionPixelGate') }}</dt><dd>{{ t('allByteExact', { resolutions: activeFitCompression.pixelExactResolutions.join(' / ') }) }}</dd></div>
              </template>
              <template v-if="activeFitPrune">
                <div><dt>{{ t('fixedPointPrune') }}</dt><dd>{{ activeFitPrune.drawnInstancesBefore }} → {{ activeFitPrune.drawnInstancesAfter }} {{ t('actualInstances') }}</dd></div>
                <div><dt>{{ t('necessityEvidence') }}</dt><dd>{{ activeFitPrune.finalNecessityEvidence.length }} / {{ activeFitPrune.drawnInstancesAfter }} {{ t('complete') }}</dd></div>
                <div><dt>{{ t('pruneContract') }}</dt><dd>{{ t('pruneContractValue') }}</dd></div>
              </template>
              <div><dt>{{ t('seamGate') }}</dt><dd>{{ fitResult.provenance.nativeTileSeamValidation.status === 'passed' ? t('allPassed') : t('notApplicable') }}</dd></div>
              <div><dt>{{ t('seamMetrics') }}</dt><dd>{{ fitResult.provenance.nativeTileSeamValidation.metrics.map((metric) => `${metric.resolution}px leak=${metric.backgroundLeakPixels} peak=${Math.max(metric.peakRowLeakPixels, metric.peakColumnLeakPixels)}`).join(' · ') || t('notApplicable') }}</dd></div>
              <div><dt>{{ t('tileSearchSpace') }}</dt><dd>{{ fitResult.provenance.nativeTileSearch.searchWidth }}×{{ fitResult.provenance.nativeTileSearch.searchHeight }} · depth {{ fitResult.provenance.nativeTileSearch.maximumDepth }} · {{ t('pixelLeafCapacity') }} {{ fitResult.provenance.nativeTileSearch.pixelLeafCapacity }} · {{ t('originalBudget') }} {{ fitResult.provenance.nativeTileSearch.userBudgetAppliedWithoutClamp }}</dd></div>
              <div><dt>{{ t('algorithmContract') }}</dt><dd>{{ fitResult.provenance.algorithm }}</dd></div>
              <div><dt>{{ t('relativeImprovement') }}</dt><dd>{{ (fitResult.metrics.relativeImprovement * 100).toFixed(2) }}%</dd></div>
              <div><dt>{{ t('gpuBatchSearch') }}</dt><dd>{{ fitResult.provenance.batchSearch.backend ?? 'CPU' }} · {{ fitResult.provenance.batchSearch.status }} · {{ fitResult.provenance.batchSearch.batches }} batch / {{ fitResult.provenance.batchSearch.candidates }} candidates · Δ {{ fitResult.provenance.batchSearch.maximumMetricDelta.toExponential(2) }}</dd></div>
              <div><dt>{{ t('gpuCrossScore') }}</dt><dd>{{ fitWebGlScore ? fitWebGlScore.meanSquaredRgbError.toFixed(5) : t('unavailable') }}</dd></div>
              <div><dt>{{ t('inputPyramid') }}</dt><dd>{{ fitResult.provenance.sourceWidth }}×{{ fitResult.provenance.sourceHeight }} → {{ fitResult.provenance.pyramidResolutions.join(' / ') }}px</dd></div>
              <div><dt>{{ t('candidatePaths') }}</dt><dd>{{ fitResult.provenance.candidateLosses.map((item) => `${item.mode === 'native-tile-paint' ? t('nativeBlock') : item.mode === 'native-edge-refined' ? t('edgeRefined') : item.mode === 'native-high-resolution-edge-refined' ? t('highResolutionRefined') : item.mode === 'hybrid-native-paint' ? t('hybrid') : t('semantic')} ${item.layers} ${t('layersShort')}=${item.totalLoss.toFixed(4)} [${item.textureNames.join(', ') || t('noEmblem')}]`).join(' · ') }}</dd></div>
            </dl>
            <small>{{ t('scoreBoundary') }}</small>
          </template>
        </div>
      </div>
      <el-alert
        class="mcp-limit-note"
        type="warning"
        :closable="false"
        show-icon
        :title="t('mcpLimitTitle')"
        :description="t('mcpLimitDescription')"
      />
    </section>

    <main class="workspace">
      <section class="source-pane panel">
        <div class="panel-title">
          <div>
            <span class="step">01</span>
            <h2>{{ t('importCode') }}</h2>
          </div>
          <div class="source-actions">
            <el-button :loading="clipboardBusy" @click="pasteSource">{{ t('pasteClipboard') }}</el-button>
            <el-button text link type="primary" @click="loadSample">{{ t('loadNativeSample') }}</el-button>
          </div>
        </div>
        <el-input v-model="source" type="textarea" :rows="21" resize="none" spellcheck="false" class="code-input" />
        <el-button class="import-button" type="primary" @click="importSource">{{ t('parseAndLoad') }}</el-button>

        <div v-if="visibleDiagnostics.length" class="diagnostics">
          <div v-for="(item, index) in visibleDiagnostics" :key="index" :class="['diagnostic', item.severity]">
            <span>{{ item.severity.toUpperCase() }}</span>
            <p>{{ uiText(item.message) }}<small v-if="item.line"> ({{ item.line }}:{{ item.column }})</small></p>
          </div>
        </div>
        <el-empty v-else :description="t('noDiagnostics')" :image-size="46" />

        <el-collapse class="syntax-capabilities">
          <el-collapse-item :title="t('syntaxMatrix')" name="syntax-capabilities">
            <p class="capability-note">
              {{ t('syntaxMatrixBoundary') }}
            </p>
            <el-table :data="localizedSyntaxCapabilityRows" size="small" max-height="420">
              <el-table-column :label="t('classification')" width="112">
                <template #default="{ row }">
                  <el-tag
                    size="small"
                    effect="plain"
                    :type="row.classification === 'supported' ? 'success' : row.classification === 'ambiguous' ? 'warning' : 'danger'"
                  >
                    {{ row.classification === 'supported' ? t('supported') : row.classification === 'ambiguous' ? t('ambiguous') : t('notExecutable') }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="syntax" :label="t('syntax')" min-width="190" show-overflow-tooltip />
              <el-table-column :label="t('example')" min-width="250">
                <template #default="{ row }"><code>{{ row.example }}</code></template>
              </el-table-column>
              <el-table-column :label="t('parserCoverage')" width="100">
                <template #default="{ row }">{{ capabilityStageLabel(row.coverage.parser) }}</template>
              </el-table-column>
              <el-table-column :label="t('previewCoverage')" width="100">
                <template #default="{ row }">{{ capabilityStageLabel(row.coverage.preview) }}</template>
              </el-table-column>
              <el-table-column :label="t('editorCoverage')" width="100">
                <template #default="{ row }">{{ capabilityStageLabel(row.coverage.editor) }}</template>
              </el-table-column>
              <el-table-column :label="t('serializerCoverage')" width="100">
                <template #default="{ row }">{{ capabilityStageLabel(row.coverage.serializer) }}</template>
              </el-table-column>
              <el-table-column prop="engineOutcome" :label="t('nativeResult')" min-width="170" show-overflow-tooltip />
              <el-table-column prop="nativeEvidence" :label="t('nativeEvidence')" min-width="190" show-overflow-tooltip />
              <el-table-column prop="editorPolicy" :label="t('editorPolicy')" width="105" />
              <el-table-column prop="note" :label="t('boundary')" min-width="250" show-overflow-tooltip />
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </section>

      <section class="preview-pane panel">
        <div class="panel-title">
          <div><span class="step">02</span><h2>{{ t('previewTitle') }}</h2></div>
          <el-space>
            <el-button
              v-if="selectedInstance"
              size="small"
              data-testid="toggle-visual-guides"
              @click="visualGuidesVisible = !visualGuidesVisible"
            >{{ visualGuidesVisible ? t('hideVisualGuides') : t('showVisualGuides') }}</el-button>
            <el-tag effect="plain" :type="canonicalPreviewUrl ? 'success' : 'warning'">
              {{ canonicalPreviewIsCandidateSnapshot
                ? t('canonicalCandidateSnapshot')
                : canonicalPreviewUrl
                  ? t('shaderModel', { count: shaderSourceCount })
                  : t('browserApproximation') }}
            </el-tag>
          </el-space>
        </div>
        <div class="preview-stage">
          <div ref="shieldElement" :class="['shield', { 'shader-bound': canonicalPreviewUrl }]" :style="{ '--shield-color': cssColor(coatOfArms.colors[0]) }">
            <img v-if="canonicalPreviewUrl" data-testid="editor-preview" class="shader-preview" :src="canonicalPreviewUrl" :alt="t('shaderPreviewAlt')" />
            <template v-else>
              <img v-if="patternPreviewUrl" class="pattern-texture" :src="patternPreviewUrl" :alt="t('patternPreviewAlt')" />
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
            <div v-if="selectedInstance && visualGuidesVisible" class="visual-transform-layer">
              <div
                class="visual-transform-box"
                :class="{ active: visualTransformMode !== null }"
                :style="visualTransformStyle"
                data-testid="visual-transform-box"
              >
                <button
                  type="button"
                  class="visual-handle move-handle"
                  :aria-label="t('dragPosition')"
                  data-testid="visual-move-handle"
                  @pointerdown.stop="beginVisualTransform('move', $event)"
                  @pointermove.stop="updateVisualTransform"
                  @pointerup.stop="finishVisualTransform"
                  @pointercancel.stop="finishVisualTransform"
                />
                <button
                  type="button"
                  class="visual-handle scale-handle"
                  :aria-label="t('uniformScale')"
                  data-testid="visual-scale-handle"
                  @pointerdown.stop="beginVisualTransform('scale', $event)"
                  @pointermove.stop="updateVisualTransform"
                  @pointerup.stop="finishVisualTransform"
                  @pointercancel.stop="finishVisualTransform"
                />
                <button
                  type="button"
                  class="visual-handle rotate-handle"
                  :aria-label="t('rotateInstance')"
                  data-testid="visual-rotate-handle"
                  @pointerdown.stop="beginVisualTransform('rotate', $event)"
                  @pointermove.stop="updateVisualTransform"
                  @pointerup.stop="finishVisualTransform"
                  @pointercancel.stop="finishVisualTransform"
                />
              </div>
            </div>
          </div>
        </div>
        <p v-if="selectedInstance && visualGuidesVisible" class="visual-editor-help">
          {{ t('visualEditorHelp', { layer: selectedEmblem + 1, instance: selectedInstanceIndex + 1 }) }}
        </p>
        <section class="candidate-comparison" data-testid="candidate-comparison">
          <div class="section-heading">
            <h3>{{ t('candidateComparison', { count: comparisonCandidates.length, maximum: MAX_COMPARISON_CANDIDATES }) }}</h3>
            <el-button size="small" :disabled="comparisonCandidates.length >= MAX_COMPARISON_CANDIDATES && !comparisonCandidates.some((item) => item.source === output)" @click="captureComparisonCandidate()">
              {{ t('saveCurrentCandidate') }}
            </el-button>
          </div>
          <p>{{ t('candidateBoundary') }}</p>
          <div v-if="comparisonRows.length" class="candidate-grid">
            <article v-for="candidate in comparisonRows" :key="candidate.id" class="candidate-card" :data-candidate-id="candidate.id">
              <div v-if="candidate.previewUrl" class="candidate-preview-frame">
                <img
                  :src="candidate.previewUrl"
                  :alt="candidateDisplayName(candidate)"
                  class="candidate-shield-preview"
                  :data-testid="candidate.current ? 'current-candidate-preview' : undefined"
                />
              </div>
              <div v-else class="candidate-preview-placeholder">{{ t('previewDeferred') }}</div>
              <strong>{{ candidateDisplayName(candidate) }}</strong>
              <span>{{ t('candidateStats', { instances: candidate.stats.drawnInstances.toLocaleString(), blocks: candidate.stats.coloredEmblemBlocks.toLocaleString(), bytes: candidate.stats.utf8Bytes.toLocaleString() }) }}</span>
              <template v-if="candidate.metrics">
                <span>{{ t('candidateLosses', { total: candidate.metrics.totalLoss.toFixed(5), edge: candidate.metrics.edgeLoss.toFixed(5) }) }}</span>
                <el-tag size="small" :type="candidate.dominance === 'dominated' ? 'warning' : 'success'">
                  {{ candidate.dominance === 'dominated' ? t('dominated') : t('nonDominated') }}
                </el-tag>
              </template>
              <el-tag v-else size="small" type="info">{{ t('metricsUnbound') }}</el-tag>
              <el-tag v-if="candidate.current" size="small" type="primary">{{ t('currentComposition') }}</el-tag>
              <div class="candidate-actions">
                <el-button size="small" @click="activateComparisonCandidate(candidate)">{{ t('load') }}</el-button>
                <el-button size="small" @click="copyComparisonCandidate(candidate)">{{ t('copyCandidate') }}</el-button>
                <el-button size="small" type="danger" plain @click="removeComparisonCandidate(candidate.id)">{{ t('delete') }}</el-button>
              </div>
            </article>
          </div>
          <el-empty v-else :image-size="54" :description="t('noCandidates')" />
        </section>
        <div class="preview-caption">
          <strong>{{ coatOfArms.pattern || t('unspecifiedPattern') }}</strong>
          <span>{{ t('previewStats', { layers: coatOfArms.coloredEmblems.length, instances: drawnInstanceCount, textured: coatOfArms.texturedEmblems.length }) }}</span>
        </div>
        <el-alert v-if="largeDocumentPreviewDeferred && !canonicalPreviewUrl" type="warning" :closable="false" show-icon>
          <template #title>{{ t('largePreviewDeferred') }}</template>
        </el-alert>
        <el-button class="preview-load" :loading="textureBusy" @click="loadCurrentTexturePreviews">{{ t('loadCurrentDds') }}</el-button>
        <el-alert
          v-if="coatOfArms.parent.trim()"
          data-testid="parent-preview-boundary"
          type="warning"
          :closable="false"
          show-icon
        >
          <template #title>{{ t('parentPreviewBoundary', { parent: coatOfArms.parent.trim() }) }}</template>
        </el-alert>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>{{ t('previewEvidenceBoundary') }}</template>
        </el-alert>
      </section>

      <section class="editor-pane panel">
        <div class="panel-title">
          <div><span class="step">03</span><h2>{{ t('structuredEditor') }}</h2></div>
          <el-space>
            <el-button size="small" :loading="assetPackBusy" @click="loadStandaloneAssetPack()">{{ t('refreshStaticAssets') }}</el-button>
          </el-space>
        </div>
        <p class="history-status">{{ t('historyStatus', { notice: uiText(historyNotice), redo: redoHistory.length, memory: ((undoHistoryBytes + redoHistoryBytes) / 1024 / 1024).toFixed(1) }) }}</p>
        <el-scrollbar height="690px">
          <p class="resource-note">
            {{ t('staticAssetBoundary') }}
            {{ assetPackRuntimeBoundary }}
          </p>
          <el-form label-position="top">
            <div class="form-grid">
              <el-form-item :label="t('parentReference')">
                <el-input v-model="coatOfArms.parent" placeholder="c_england" />
              </el-form-item>
              <el-form-item :label="t('patternResource')">
                <el-select v-model="coatOfArms.pattern" filterable allow-create default-first-option @change="loadPatternTexture">
                  <el-option
                    v-for="item in patternResources"
                    :key="item.name"
                    :label="t('resourceColors', { name: item.name, colors: item.colors ?? '?' })"
                    :value="item.name"
                  />
                </el-select>
              </el-form-item>
              <el-form-item v-for="index in 3" :key="index" :label="t('baseColor', { index })">
                <el-input v-model="coatOfArms.colors[index - 1]" @input="markRootColorExplicit(index - 1)" />
              </el-form-item>
            </div>

            <div class="section-heading">
              <h3>{{ t('coloredEmblems') }}</h3>
              <el-button size="small" type="primary" plain @click="addEmblem">{{ t('addLayer') }}</el-button>
            </div>
            <el-tabs v-if="coatOfArms.coloredEmblems.length && coatOfArms.coloredEmblems.length <= 128" v-model="selectedEmblem" type="card">
              <el-tab-pane v-for="(emblem, index) in coatOfArms.coloredEmblems" :key="index" :label="t('layer', { index: index + 1 })" :name="index" />
            </el-tabs>
            <div v-else-if="coatOfArms.coloredEmblems.length" class="emblem-window-toolbar">
              <span>{{ t('layerWindow', { current: selectedEmblem + 1, total: coatOfArms.coloredEmblems.length }) }}</span>
              <el-button size="small" :disabled="selectedEmblem === 0" @click="selectEmblemIndex(selectedEmblem - 1)">{{ t('previousLayer') }}</el-button>
              <el-input-number
                :model-value="selectedEmblem + 1"
                :min="1"
                :max="coatOfArms.coloredEmblems.length"
                controls-position="right"
                @update:model-value="selectEmblemIndex(Number($event) - 1)"
              />
              <el-button size="small" :disabled="selectedEmblem + 1 >= coatOfArms.coloredEmblems.length" @click="selectEmblemIndex(selectedEmblem + 1)">{{ t('nextLayer') }}</el-button>
            </div>

            <template v-if="activeEmblem">
              <div class="form-grid">
                <el-form-item :label="t('textureResource')" class="wide">
                  <el-select v-model="activeEmblem.texture" filterable allow-create default-first-option @change="loadEmblemTexture">
                    <el-option
                      v-for="item in emblemResources"
                      :key="item.name"
                      :label="t('resourceColors', { name: item.name, colors: item.colors ?? '?' })"
                      :value="item.name"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item v-for="index in 3" :key="index" :label="t('emblemColor', { index })">
                  <el-input v-model="activeEmblem.colors[index - 1]" />
                </el-form-item>
                <el-form-item :label="t('maskSeparated')">
                  <el-input :model-value="activeEmblem.mask.join(' ')" @update:model-value="parseMask" />
                </el-form-item>
              </div>

              <div v-if="activeEmblem.instances.length > INSTANCE_EDITOR_WINDOW_SIZE" class="instance-window-toolbar">
                <span>{{ t('instanceWindow', { start: boundedInstanceWindowStart + 1, end: instanceWindowEnd, total: activeEmblem.instances.length }) }}</span>
                <el-button size="small" :disabled="boundedInstanceWindowStart === 0" @click="moveInstanceWindow(boundedInstanceWindowStart - INSTANCE_EDITOR_WINDOW_SIZE)">{{ t('previousPage') }}</el-button>
                <el-input-number
                  :model-value="boundedInstanceWindowStart + 1"
                  :min="1"
                  :max="activeEmblem.instances.length"
                  :step="INSTANCE_EDITOR_WINDOW_SIZE"
                  controls-position="right"
                  @update:model-value="moveInstanceWindow(Number($event) - 1)"
                />
                <el-button size="small" :disabled="instanceWindowEnd >= activeEmblem.instances.length" @click="moveInstanceWindow(instanceWindowEnd)">{{ t('nextPage') }}</el-button>
              </div>
              <div class="instance-list" data-testid="instance-editor-window">
                <div
                  v-for="item in visibleInstanceItems"
                  :key="item.index"
                  :class="['instance-card', { selected: item.index === selectedInstanceIndex }]"
                  :data-instance-index="item.index"
                >
                  <div class="instance-title">
                    <strong>{{ t('instance', { index: item.index + 1 }) }}</strong>
                    <el-space>
                      <el-button link type="primary" @click="selectInstanceForVisualEdit(item.index)">
                        {{ item.index === selectedInstanceIndex ? t('previewEditing') : t('editInPreview') }}
                      </el-button>
                      <el-button link type="danger" @click="removeActiveInstance(item.index)">{{ t('delete') }}</el-button>
                    </el-space>
                  </div>
                  <div class="number-grid">
                    <el-form-item label="X"><el-input-number v-model="item.instance.position[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Y"><el-input-number v-model="item.instance.position[1]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale X"><el-input-number v-model="item.instance.scale[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale Y"><el-input-number v-model="item.instance.scale[1]" :step="0.05" /></el-form-item>
                    <el-form-item :label="t('rotation')"><el-input-number v-model="item.instance.rotation" :step="5" /></el-form-item>
                    <el-form-item :label="t('depth')"><el-input-number v-model="item.instance.depth" :step="0.01" /></el-form-item>
                  </div>
                </div>
              </div>
              <div class="row-actions">
                <el-button @click="addInstanceToActiveEmblem">{{ t('addInstance') }}</el-button>
                <el-button type="danger" plain @click="removeEmblem(selectedEmblem)">{{ t('deleteCurrentLayer') }}</el-button>
              </div>
            </template>

            <div class="section-heading textured-heading">
              <h3>{{ t('texturedEmblems') }}</h3>
              <el-button size="small" plain @click="coatOfArms.texturedEmblems.push(createTexturedEmblem())">
                {{ t('addRestrictedLayer') }}
              </el-button>
            </div>
            <el-alert type="warning" :closable="false" show-icon>
              <template #title>
                {{ t('texturedBoundary') }}
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
                  :alt="t('rawTexturedAlt')"
                  class="textured-raw-preview"
                />
                <div v-else class="textured-preview-placeholder">?</div>
                <el-input v-model="emblem.texture" placeholder="_default.dds" />
                <el-button
                  type="danger"
                  plain
                  @click="coatOfArms.texturedEmblems.splice(index, 1)"
                >{{ t('delete') }}</el-button>
              </div>
            </div>
          </el-form>

          <div class="output-block">
            <div class="section-heading">
              <h3>{{ t('deterministicExport') }}</h3>
              <el-space>
                <el-tag>{{ t('outputSummary', { bytes: outputBytes.toLocaleString(), lines: outputLines.toLocaleString() }) }}</el-tag>
                <el-tag v-if="outputPreviewTruncated" type="warning">{{ t('uiSummaryOnly') }}</el-tag>
                <el-tag>CRLF</el-tag>
              </el-space>
            </div>
            <pre>{{ outputPreview }}</pre>
          </div>
        </el-scrollbar>
      </section>
    </main>
  </div>
  </el-config-provider>
</template>
