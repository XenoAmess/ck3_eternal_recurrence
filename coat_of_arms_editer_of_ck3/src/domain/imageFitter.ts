import type { DecodedDds } from './dds'
import {
  renderCoatOfArms,
  renderColoredEmblemLayer,
  type NamedColorMap,
  type RenderedCoatOfArms,
} from './renderer'
import type { CoatOfArms, CoatOfArmsInstance, ColoredEmblem } from './types'

export interface FitImage {
  width: number
  height: number
  pixels: Uint8ClampedArray
}

export interface FitTextureCandidate {
  name: string
  assetSha256: string
  texture: DecodedDds
}

export interface ImageFitOptions {
  resolution?: number
  sourceWidth?: number
  sourceHeight?: number
  pyramidImages?: FitImage[]
  maxPatterns?: number
  maxEmblemCandidates?: number
  maxLayers?: number
  refinementCandidates?: number
  minRelativeLayerImprovement?: number
  surfaceMask?: DecodedDds
  namedColors?: NamedColorMap
  beamWidth?: number
  onProgress?: (progress: ImageFitProgress) => void
  inputSha256?: string
  assetPackManifestSha256?: string
  resumeCheckpoint?: ImageFitCheckpoint
  onCheckpoint?: (checkpoint: ImageFitCheckpoint) => void
  batchSearchRequested?: boolean
  batchScorer?: ImageFitBatchScorer
}

export interface ImageFitBatchScorer {
  readonly backend: string
  readonly maximumBatchSize: number
  score(candidates: readonly FitImage[]): ImageFitMetrics[] | null
  status(): 'available' | 'unavailable' | 'context_lost' | 'runtime_error'
}

export interface ImageFitBatchSearchReceipt {
  requested: boolean
  backend: string | null
  status: 'active' | 'unavailable_fallback' | 'context_lost_fallback' | 'runtime_error_fallback' | 'reference_mismatch_fallback'
  batches: number
  candidates: number
  maximumBatchSize: number
  cpuReferenceTolerance: number
  maximumMetricDelta: number
  cpuReferenceAgreement: boolean
}

export interface ImageFitProgress {
  phase: 'background' | 'coarse' | 'refine' | 'paint'
  completed: number
  total: number
  percent: number
  layer: number
  layerBudget: number
  evaluatedCandidates: number
}

export interface ImageFitCheckpoint {
  contract: 'ck3-coa-fit-checkpoint-v1'
  algorithm: 'ck3-coa-browser-fit-v6-budget-exhaustive-edge'
  lane: 'baseline' | 'hybrid'
  inputSha256: string
  assetPackManifestSha256: string
  resolution: number
  sourceWidth: number
  sourceHeight: number
  layerBudget: number
  randomSeed: null
  nextTileIndex: number
  tileCount: number
  evaluatedCandidates: number
  tiles: PaintTile[]
  state: {
    coatOfArms: CoatOfArms
    candidateKey: string
    patternName: string
    selectedAssetNames: string[]
    layerLosses: number[]
    reconstructionMode: ImageFitReconstructionMode
    paintPlacements: NativePaintPlacement[]
  }
}

export interface ImageFitMetrics {
  colorLoss: number
  edgeLoss: number
  totalLoss: number
  relativeImprovement: number
}

export type ImageFitReconstructionMode =
  | 'semantic-search'
  | 'native-tile-paint'
  | 'native-edge-refined'
  | 'native-high-resolution-edge-refined'
  | 'hybrid-native-paint'

export interface MultiscaleFitMetric {
  resolution: number
  colorLoss: number
  edgeLoss: number
  totalLoss: number
}

export interface NativeTileSeamMetric {
  resolution: number
  backgroundLeakPixels: number
  maximumLeakAmount: number
  peakRowLeakPixels: number
  peakColumnLeakPixels: number
}

export interface NativeTileSeamValidation {
  status: 'passed' | 'failed' | 'not-applicable'
  samplingContract: 'pixel-center-hard-geometry-v1'
  metrics: NativeTileSeamMetric[]
}

export interface ImageFitResult {
  coatOfArms: CoatOfArms
  metrics: ImageFitMetrics
  provenance: {
    algorithm: 'ck3-coa-browser-fit-v6-budget-exhaustive-edge'
    searchBackend: 'cpu-reference' | 'webgl2-batch+cpu-reference'
    batchSearch: ImageFitBatchSearchReceipt
    scoringContract: 'alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1'
    rendererContract: 'cpu-rgba8-bilinear-clamp-pixel-center-native-clockwise-depth-descending-v3'
    randomSeed: null
    surfaceMaskApplied: boolean
    sourceWidth: number
    sourceHeight: number
    resolution: number
    pyramidResolutions: number[]
    evaluatedCandidates: number
    patternAssets: number
    emblemAssets: number
    layerBudget: number
    logicalLayers: number
    coloredEmblemBlocks: number
    drawnInstances: number
    selectedLayers: number
    layerLosses: number[]
    reconstructionMode: ImageFitReconstructionMode
    candidateLosses: {
      mode: ImageFitReconstructionMode
      layers: number
      totalLoss: number
      edgeLoss: number
      textureNames: string[]
      multiscaleMetrics: MultiscaleFitMetric[]
      passesPrimaryNonRegression: boolean
    }[]
    selectedMultiscaleMetrics: MultiscaleFitMetric[]
    baselineEdgeRepair: {
      availableSlots: number
      acceptedLayers: number
      evaluatedCandidates: number
      terminationReason: 'not_applicable' | 'layer_budget' | 'no_improvement'
    }
    highResolutionEdgeRepair: {
      resolution: number | null
      availableSlots: number
      acceptedLayers: number
      evaluatedCandidates: number
      terminationReason: 'not_applicable' | 'layer_budget' | 'no_improvement'
    }
    nativeShapeRefinement: {
      requestedPasses: number
      completedPasses: number
      acceptedLayers: number
      evaluatedCandidates: number
      primitiveTextureNames: string[]
      acceptedTextureNames: string[]
      terminationReason: 'not_applicable' | 'layer_budget' | 'no_improvement' | 'pass_budget'
    }
    terminationReason: 'layer_budget' | 'exact_match' | 'no_emblems' | 'no_improvement' | 'minimum_improvement'
    selectedAssetSha256: string[]
    nativeTileSeamValidation: NativeTileSeamValidation
    nativeTileSearch: {
      contract: 'resolution-bounded-quadtree-v2'
      searchWidth: number
      searchHeight: number
      maximumDepth: number
      pixelLeafCapacity: number
      userBudgetAppliedWithoutClamp: number
    }
  }
}

interface ScoredCandidate {
  coatOfArms: CoatOfArms
  rendered: RenderedCoatOfArms
  colorLoss: number
  edgeLoss: number
  totalLoss: number
  key: string
}

interface SearchState {
  candidate: ScoredCandidate
  patternAsset: FitTextureCandidate
  selectedAssets: FitTextureCandidate[]
  layerLosses: number[]
  reconstructionMode: ImageFitResult['provenance']['reconstructionMode']
  paintPlacements: NativePaintPlacement[]
}

type ByteRgb = [number, number, number]

const DEFAULT_RESOLUTION = 40

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value))
}

function normalizeLayerBudget(value: number | undefined): number {
  const normalized = Math.floor(value ?? 6)
  if (!Number.isSafeInteger(normalized) || normalized < 0) {
    throw new Error('图层搜索预算必须是非负安全整数')
  }
  return normalized
}

function reportProgress(
  callback: ImageFitOptions['onProgress'],
  phase: ImageFitProgress['phase'],
  completed: number,
  total: number,
  layer: number,
  layerBudget: number,
  evaluatedCandidates: number,
): void {
  if (!callback) return
  const boundedTotal = Math.max(1, total)
  const boundedCompleted = clamp(completed, 0, boundedTotal)
  callback({
    phase,
    completed: boundedCompleted,
    total: boundedTotal,
    percent: Math.round(boundedCompleted / boundedTotal * 100),
    layer,
    layerBudget,
    evaluatedCandidates,
  })
}

function shouldReportProgress(completed: number, total: number): boolean {
  const interval = Math.max(1, Math.floor(total / 20))
  return completed === total || completed % interval === 0
}

function validateImage(image: FitImage): void {
  if (
    !Number.isSafeInteger(image.width)
    || !Number.isSafeInteger(image.height)
    || image.width < 1
    || image.height < 1
    || image.width > 4096
    || image.height > 4096
    || image.pixels.length !== image.width * image.height * 4
  ) throw new Error('目标图片尺寸或 RGBA 数据不合法')
}

export function resizeFitImage(image: FitImage, size: number): FitImage {
  validateImage(image)
  if (!Number.isSafeInteger(size) || size < 8 || size > 4096) throw new Error('重采样分辨率必须在 8..4096')
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    const sourceY = clamp((y + 0.5) * image.height / size - 0.5, 0, image.height - 1)
    const y0 = Math.floor(sourceY)
    const y1 = Math.min(image.height - 1, y0 + 1)
    const ty = sourceY - y0
    for (let x = 0; x < size; x += 1) {
      const sourceX = clamp((x + 0.5) * image.width / size - 0.5, 0, image.width - 1)
      const x0 = Math.floor(sourceX)
      const x1 = Math.min(image.width - 1, x0 + 1)
      const tx = sourceX - x0
      const target = (y * size + x) * 4
      const sources = [
        [(y0 * image.width + x0) * 4, (1 - tx) * (1 - ty)],
        [(y0 * image.width + x1) * 4, tx * (1 - ty)],
        [(y1 * image.width + x0) * 4, (1 - tx) * ty],
        [(y1 * image.width + x1) * 4, tx * ty],
      ] as const
      let alpha = 0
      const premultiplied = [0, 0, 0]
      for (const [source, weight] of sources) {
        const sourceAlpha = image.pixels[source + 3] / 255
        alpha += sourceAlpha * weight
        for (let channel = 0; channel < 3; channel += 1) {
          premultiplied[channel] += image.pixels[source + channel] * sourceAlpha * weight
        }
      }
      for (let channel = 0; channel < 3; channel += 1) {
        pixels[target + channel] = alpha > 1e-8 ? Math.round(premultiplied[channel] / alpha) : 0
      }
      pixels[target + 3] = Math.round(alpha * 255)
    }
  }
  return { width: size, height: size, pixels }
}

export function dominantColors(image: FitImage, count = 3): ByteRgb[] {
  validateImage(image)
  const buckets = new Map<number, { weight: number, sums: [number, number, number] }>()
  for (let offset = 0; offset < image.pixels.length; offset += 4) {
    const alpha = image.pixels[offset + 3] / 255
    if (alpha <= 1 / 255) continue
    const values = [0, 1, 2].map((channel) => image.pixels[offset + channel]) as ByteRgb
    const key = ((values[0] >> 4) << 8) | ((values[1] >> 4) << 4) | (values[2] >> 4)
    const bucket = buckets.get(key) ?? { weight: 0, sums: [0, 0, 0] }
    bucket.weight += alpha
    for (let channel = 0; channel < 3; channel += 1) bucket.sums[channel] += values[channel] * alpha
    buckets.set(key, bucket)
  }
  const result = [...buckets.entries()]
    .sort((left, right) => right[1].weight - left[1].weight || left[0] - right[0])
    .slice(0, count)
    .map(([, bucket]) => bucket.sums.map((sum) => Math.round(sum / bucket.weight)) as ByteRgb)
  while (result.length < count) result.push(result[result.length - 1] ?? [128, 128, 128])
  return result
}

function permutations(values: ByteRgb[]): ByteRgb[][] {
  if (values.length !== 3) return [values]
  return [
    [values[0], values[1], values[2]], [values[0], values[2], values[1]],
    [values[1], values[0], values[2]], [values[1], values[2], values[0]],
    [values[2], values[0], values[1]], [values[2], values[1], values[0]],
  ]
}

function expression(color: ByteRgb): string {
  return `rgb { ${color[0]} ${color[1]} ${color[2]} }`
}

function luminance(pixels: Uint8ClampedArray, offset: number): number {
  return (pixels[offset] * 54 + pixels[offset + 1] * 183 + pixels[offset + 2] * 19) / 256
}

export function measureImageFitLosses(
  target: FitImage,
  rendered: RenderedCoatOfArms,
): Pick<ScoredCandidate, 'colorLoss' | 'edgeLoss' | 'totalLoss'> {
  validateImage(target)
  if (
    rendered.width !== target.width
    || rendered.height !== target.height
    || rendered.pixels.length !== target.pixels.length
  ) throw new Error('评分目标与渲染结果尺寸不一致')
  let color = 0
  let edge = 0
  let colorWeight = 0
  let edgeWeight = 0
  for (let y = 0; y < target.height; y += 1) {
    for (let x = 0; x < target.width; x += 1) {
      const offset = (y * target.width + x) * 4
      const weight = target.pixels[offset + 3] / 255
      if (weight <= 0) continue
      for (let channel = 0; channel < 3; channel += 1) {
        const delta = (target.pixels[offset + channel] - rendered.pixels[offset + channel]) / 255
        color += delta * delta * weight
      }
      colorWeight += weight
      if (x > 0) {
        const previous = offset - 4
        const pairWeight = Math.min(weight, target.pixels[previous + 3] / 255)
        edge += pairWeight * Math.abs(
          (luminance(target.pixels, offset) - luminance(target.pixels, previous))
          - (luminance(rendered.pixels, offset) - luminance(rendered.pixels, previous)),
        ) / 255
        edgeWeight += pairWeight
      }
      if (y > 0) {
        const previous = offset - target.width * 4
        const pairWeight = Math.min(weight, target.pixels[previous + 3] / 255)
        edge += pairWeight * Math.abs(
          (luminance(target.pixels, offset) - luminance(target.pixels, previous))
          - (luminance(rendered.pixels, offset) - luminance(rendered.pixels, previous)),
        ) / 255
        edgeWeight += pairWeight
      }
    }
  }
  if (colorWeight <= 0) throw new Error('目标图片没有可拟合的不透明像素')
  const colorLoss = color / (colorWeight * 3)
  const edgeLoss = edgeWeight > 0 ? edge / edgeWeight : 0
  return { colorLoss, edgeLoss, totalLoss: colorLoss * 0.62 + edgeLoss * 0.38 }
}

function score(
  coatOfArms: CoatOfArms,
  pattern: DecodedDds,
  emblems: Record<string, DecodedDds>,
  target: FitImage,
  key: string,
  surfaceMask?: DecodedDds,
  namedColors: NamedColorMap = {},
): ScoredCandidate {
  const rendered = renderCoatOfArms(
    coatOfArms,
    { pattern, coloredEmblems: emblems, surfaceMask },
    namedColors,
    target.width,
    // Search states append a new foreground layer incrementally. Keep that
    // insertion-order optimization internally, then reverse the numeric depth
    // domain once for CK3's smaller-depth-on-top contract at export.
    { emblemDepthOrder: 'ascending' },
  )
  if (!rendered) throw new Error('候选渲染失败')
  return { coatOfArms, rendered, ...measureImageFitLosses(target, rendered), key }
}

function better(candidate: ScoredCandidate, current: ScoredCandidate | null): boolean {
  return !current
    || candidate.totalLoss < current.totalLoss - 1e-12
    || (Math.abs(candidate.totalLoss - current.totalLoss) <= 1e-12 && candidate.key < current.key)
}

function residualWeights(target: FitImage, rendered: RenderedCoatOfArms): Float64Array {
  const result = new Float64Array(target.width * target.height)
  for (let index = 0; index < result.length; index += 1) {
    const offset = index * 4
    const alpha = target.pixels[offset + 3] / 255
    result[index] = alpha * Math.sqrt([0, 1, 2].reduce((sum, channel) => {
      const delta = target.pixels[offset + channel] - rendered.pixels[offset + channel]
      return sum + delta * delta
    }, 0))
  }
  return result
}

interface ResidualFocus {
  position: [number, number]
  scale: [number, number]
  descriptor: Float32Array
}

const SHAPE_DESCRIPTOR_SIZE = 18

const MIXED_NATIVE_PRIMITIVE_TEXTURES: readonly string[] = [
  'ce_block_02.dds',
  'ce_billet.dds',
  'ce_circle.dds',
  'ce_lozenge.dds',
  'ce_triangle_mask.dds',
]

/**
 * Keeps the strongest descriptor matches while reserving real-render slots for
 * the shipped rectangle, circle, lozenge and wedge-like primitive families.
 * The returned order remains the descriptor order, so candidate enumeration
 * never becomes a hidden tie-break.
 */
export function selectMixedNativeShapeCandidateNames(
  rankedNames: readonly string[],
  maximum: number,
): string[] {
  const rankedUnique = [...new Set(rankedNames)]
  const requested = Number.isFinite(maximum) ? Math.floor(maximum) : 0
  const limit = Math.max(0, Math.min(requested, rankedUnique.length))
  if (limit === 0) return []
  const reserved = MIXED_NATIVE_PRIMITIVE_TEXTURES
    .filter((name) => rankedUnique.includes(name))
    .slice(0, limit)
  const selected = new Set<string>(reserved)
  for (const name of rankedUnique) {
    if (selected.size >= limit) break
    selected.add(name)
  }
  return rankedUnique.filter((name) => selected.has(name))
}

function residualGeometry(
  target: FitImage,
  rendered: RenderedCoatOfArms,
): ResidualFocus {
  const weights = residualWeights(target, rendered)
  const maximumWeight = Math.max(...weights)
  if (maximumWeight < 1) return {
    position: [0.5, 0.5],
    scale: [0.5, 0.5],
    descriptor: new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE),
  }
  const threshold = Math.max(18, maximumWeight * 0.22)
  const visited = new Uint8Array(weights.length)
  let selected: number[] = []
  let selectedWeight = -1
  for (let seed = 0; seed < weights.length; seed += 1) {
    if (visited[seed] || weights[seed] < threshold) continue
    const component: number[] = []
    const queue = [seed]
    visited[seed] = 1
    let componentWeight = 0
    for (let cursor = 0; cursor < queue.length; cursor += 1) {
      const index = queue[cursor]
      component.push(index)
      componentWeight += weights[index]
      const x = index % target.width
      const y = Math.floor(index / target.width)
      const neighbors = [
        x > 0 ? index - 1 : -1,
        x + 1 < target.width ? index + 1 : -1,
        y > 0 ? index - target.width : -1,
        y + 1 < target.height ? index + target.width : -1,
      ]
      for (const neighbor of neighbors) {
        if (neighbor >= 0 && !visited[neighbor] && weights[neighbor] >= threshold) {
          visited[neighbor] = 1
          queue.push(neighbor)
        }
      }
    }
    if (componentWeight > selectedWeight) {
      selected = component
      selectedWeight = componentWeight
    }
  }
  if (!selected.length) selected = [...weights.keys()]
  let minimumX = target.width
  let minimumY = target.height
  let maximumX = -1
  let maximumY = -1
  let weightedX = 0
  let weightedY = 0
  let totalWeight = 0
  for (const index of selected) {
    const x = index % target.width
    const y = Math.floor(index / target.width)
    const weight = weights[index]
    minimumX = Math.min(minimumX, x)
    maximumX = Math.max(maximumX, x)
    minimumY = Math.min(minimumY, y)
    maximumY = Math.max(maximumY, y)
    weightedX += (x + 0.5) * weight
    weightedY += (y + 0.5) * weight
    totalWeight += weight
  }
  if (totalWeight === 0) return {
    position: [0.5, 0.5],
    scale: [0.5, 0.5],
    descriptor: new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE),
  }
  const descriptor = new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE)
  const spanX = Math.max(1, maximumX - minimumX + 1)
  const spanY = Math.max(1, maximumY - minimumY + 1)
  for (let descriptorY = 0; descriptorY < SHAPE_DESCRIPTOR_SIZE; descriptorY += 1) {
    const sourceY = clamp(
      Math.floor(minimumY + (descriptorY + 0.5) * spanY / SHAPE_DESCRIPTOR_SIZE),
      minimumY,
      maximumY,
    )
    for (let descriptorX = 0; descriptorX < SHAPE_DESCRIPTOR_SIZE; descriptorX += 1) {
      const sourceX = clamp(
        Math.floor(minimumX + (descriptorX + 0.5) * spanX / SHAPE_DESCRIPTOR_SIZE),
        minimumX,
        maximumX,
      )
      descriptor[descriptorY * SHAPE_DESCRIPTOR_SIZE + descriptorX]
        = weights[sourceY * target.width + sourceX] / maximumWeight
    }
  }
  return {
    position: [weightedX / totalWeight / target.width, weightedY / totalWeight / target.height],
    scale: [
      clamp(spanX / target.width, 0.04, 1.8),
      clamp(spanY / target.height, 0.04, 1.8),
    ],
    descriptor,
  }
}

function sampleDescriptor(descriptor: Float32Array, x: number, y: number): number {
  if (x < 0 || y < 0 || x > 1 || y > 1) return 0
  const sourceX = x * (SHAPE_DESCRIPTOR_SIZE - 1)
  const sourceY = y * (SHAPE_DESCRIPTOR_SIZE - 1)
  const x0 = Math.floor(sourceX)
  const y0 = Math.floor(sourceY)
  const x1 = Math.min(SHAPE_DESCRIPTOR_SIZE - 1, x0 + 1)
  const y1 = Math.min(SHAPE_DESCRIPTOR_SIZE - 1, y0 + 1)
  const tx = sourceX - x0
  const ty = sourceY - y0
  const at = (sampleX: number, sampleY: number) => descriptor[sampleY * SHAPE_DESCRIPTOR_SIZE + sampleX]
  return (
    at(x0, y0) * (1 - tx) * (1 - ty)
    + at(x1, y0) * tx * (1 - ty)
    + at(x0, y1) * (1 - tx) * ty
    + at(x1, y1) * tx * ty
  )
}

interface TextureShape {
  descriptor: Float32Array
  contentCenter: [number, number]
  contentSpan: [number, number]
}

function textureShapeDescriptor(texture: DecodedDds): TextureShape {
  const intensity = new Float32Array(texture.width * texture.height)
  let colorEnergy = 0
  let alphaEnergy = 0
  for (let index = 0; index < intensity.length; index += 1) {
    const offset = index * 4
    const alpha = texture.pixels[offset + 3] / 255
    const color = Math.max(
      texture.pixels[offset],
      texture.pixels[offset + 1],
      texture.pixels[offset + 2],
    ) / 255
    intensity[index] = alpha * color
    colorEnergy += intensity[index]
    alphaEnergy += alpha
  }
  if (colorEnergy < alphaEnergy * 0.05) {
    for (let index = 0; index < intensity.length; index += 1) {
      intensity[index] = texture.pixels[index * 4 + 3] / 255
    }
  }
  let minimumX = texture.width
  let minimumY = texture.height
  let maximumX = -1
  let maximumY = -1
  let weightedX = 0
  let weightedY = 0
  let totalWeight = 0
  for (let y = 0; y < texture.height; y += 1) {
    for (let x = 0; x < texture.width; x += 1) {
      const weight = intensity[y * texture.width + x]
      if (weight < 0.04) continue
      minimumX = Math.min(minimumX, x)
      minimumY = Math.min(minimumY, y)
      maximumX = Math.max(maximumX, x)
      maximumY = Math.max(maximumY, y)
      weightedX += (x + 0.5) * weight
      weightedY += (y + 0.5) * weight
      totalWeight += weight
    }
  }
  if (maximumX < minimumX || maximumY < minimumY) {
    return {
      descriptor: new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE),
      contentCenter: [0.5, 0.5],
      contentSpan: [1, 1],
    }
  }
  const spanX = Math.max(1, maximumX - minimumX + 1)
  const spanY = Math.max(1, maximumY - minimumY + 1)
  const result = new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE)
  for (let y = 0; y < SHAPE_DESCRIPTOR_SIZE; y += 1) {
    const sourceY = clamp(
      Math.floor(minimumY + (y + 0.5) * spanY / SHAPE_DESCRIPTOR_SIZE),
      minimumY,
      maximumY,
    )
    for (let x = 0; x < SHAPE_DESCRIPTOR_SIZE; x += 1) {
      const sourceX = clamp(
        Math.floor(minimumX + (x + 0.5) * spanX / SHAPE_DESCRIPTOR_SIZE),
        minimumX,
        maximumX,
      )
      result[y * SHAPE_DESCRIPTOR_SIZE + x] = intensity[sourceY * texture.width + sourceX]
    }
  }
  return {
    descriptor: result,
    contentCenter: [
      totalWeight > 0 ? weightedX / totalWeight / texture.width : 0.5,
      totalWeight > 0 ? weightedY / totalWeight / texture.height : 0.5,
    ],
    contentSpan: [spanX / texture.width, spanY / texture.height],
  }
}

function descriptorDistance(
  target: Float32Array,
  candidate: Float32Array,
  rotation: number,
  flip: number,
): number {
  // CK3 applies positive serialized rotation clockwise in screen space.
  const radians = -rotation * Math.PI / 180
  const cosine = Math.cos(radians)
  const sine = Math.sin(radians)
  const rotatedSpan = Math.abs(cosine) + Math.abs(sine)
  let overlap = 0
  let targetEnergy = 0
  let candidateEnergy = 0
  let squaredError = 0
  for (let y = 0; y < SHAPE_DESCRIPTOR_SIZE; y += 1) {
    for (let x = 0; x < SHAPE_DESCRIPTOR_SIZE; x += 1) {
      const centeredX = ((x + 0.5) / SHAPE_DESCRIPTOR_SIZE - 0.5) * rotatedSpan
      const centeredY = ((y + 0.5) / SHAPE_DESCRIPTOR_SIZE - 0.5) * rotatedSpan
      let sourceX = cosine * centeredX + sine * centeredY + 0.5
      const sourceY = -sine * centeredX + cosine * centeredY + 0.5
      if (flip < 0) sourceX = 1 - sourceX
      const candidateValue = sampleDescriptor(candidate, sourceX, sourceY)
      const targetValue = target[y * SHAPE_DESCRIPTOR_SIZE + x]
      overlap += Math.min(targetValue, candidateValue)
      targetEnergy += targetValue
      candidateEnergy += candidateValue
      const delta = targetValue - candidateValue
      squaredError += delta * delta
    }
  }
  const diceLoss = targetEnergy + candidateEnergy > 1e-8
    ? 1 - 2 * overlap / (targetEnergy + candidateEnergy)
    : 1
  return diceLoss * 0.7 + squaredError / target.length * 0.3
}

interface ShapeMatch {
  asset: FitTextureCandidate
  shape: TextureShape
  rotation: number
  flip: number
  loss: number
}

function rankShapes(
  focus: ResidualFocus,
  emblems: FitTextureCandidate[],
  descriptors: Map<string, TextureShape>,
  onItem?: (completed: number) => void,
): ShapeMatch[] {
  const rotations = Array.from({ length: 12 }, (_, index) => index * 30)
  return emblems.map((asset, index) => {
    let descriptor = descriptors.get(asset.assetSha256)
    if (!descriptor) {
      descriptor = textureShapeDescriptor(asset.texture)
      descriptors.set(asset.assetSha256, descriptor)
    }
    let best: ShapeMatch | null = null
    for (const rotation of rotations) {
      for (const flip of [1, -1]) {
        const loss = descriptorDistance(focus.descriptor, descriptor.descriptor, rotation, flip)
        if (!best || loss < best.loss) best = { asset, shape: descriptor, rotation, flip, loss }
      }
    }
    onItem?.(index + 1)
    return best!
  }).sort((left, right) => left.loss - right.loss || left.asset.name.localeCompare(right.asset.name))
}

function initialLayerGeometry(
  focus: ResidualFocus,
  match: ShapeMatch,
  minimumScale = 0.035,
): Pick<LayerParameters, 'position' | 'scale'> {
  const radians = -match.rotation * Math.PI / 180
  const cosine = Math.cos(radians)
  const sine = Math.sin(radians)
  const [contentWidth, contentHeight] = match.shape.contentSpan
  const rotatedWidth = Math.max(0.02, Math.abs(cosine) * contentWidth + Math.abs(sine) * contentHeight)
  const rotatedHeight = Math.max(0.02, Math.abs(sine) * contentWidth + Math.abs(cosine) * contentHeight)
  const scale: [number, number] = [
    clamp(focus.scale[0] / rotatedWidth, minimumScale, 2.5),
    clamp(focus.scale[1] / rotatedHeight, minimumScale, 2.5),
  ]
  const sourceX = (match.shape.contentCenter[0] * 2 - 1) * match.flip
  const sourceY = 1 - match.shape.contentCenter[1] * 2
  const rotatedX = cosine * sourceX - sine * sourceY
  const rotatedY = sine * sourceX + cosine * sourceY
  return {
    position: [
      clamp(focus.position[0] - rotatedX * scale[0] / 2, 0, 1),
      clamp(focus.position[1] + rotatedY * scale[1] / 2, 0, 1),
    ],
    scale,
  }
}

function residualColors(target: FitImage, rendered: RenderedCoatOfArms, count = 3): ByteRgb[] {
  const buckets = new Map<number, { weight: number, sums: [number, number, number] }>()
  for (let y = 0; y < target.height; y += 1) {
    for (let x = 0; x < target.width; x += 1) {
      const offset = (y * target.width + x) * 4
      const alpha = target.pixels[offset + 3] / 255
      if (alpha <= 0) continue
      const weight = alpha * [0, 1, 2].reduce((sum, channel) => {
        const delta = target.pixels[offset + channel] - rendered.pixels[offset + channel]
        return sum + delta * delta
      }, 0)
      if (weight < 64) continue
      const values = [0, 1, 2].map((channel) => target.pixels[offset + channel]) as ByteRgb
      const key = ((values[0] >> 4) << 8) | ((values[1] >> 4) << 4) | (values[2] >> 4)
      const bucket = buckets.get(key) ?? { weight: 0, sums: [0, 0, 0] }
      bucket.weight += weight
      for (let channel = 0; channel < 3; channel += 1) bucket.sums[channel] += values[channel] * weight
      buckets.set(key, bucket)
    }
  }
  const fallback = dominantColors(target, count)
  const result = [...buckets.entries()]
    .sort((left, right) => right[1].weight - left[1].weight || left[0] - right[0])
    .slice(0, count)
    .map(([, bucket]) => bucket.sums.map((sum) => Math.round(sum / bucket.weight)) as ByteRgb)
  while (result.length < count) result.push(fallback[result.length])
  return result
}

interface LayerParameters {
  colors: ByteRgb[]
  position: [number, number]
  scale: [number, number]
  rotation: number
  flip: number
}

interface LayerChoice {
  asset: FitTextureCandidate
  candidate: ScoredCandidate
  parameters: LayerParameters
}

interface EvaluationCounter {
  value: number
}

function layerChoice(
  base: ScoredCandidate,
  pattern: DecodedDds,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  target: FitImage,
  asset: FitTextureCandidate,
  parameters: LayerParameters,
  depth: number,
  evaluated: EvaluationCounter,
): LayerChoice {
  const instance = {
    position: [...parameters.position] as [number, number],
    scale: [parameters.scale[0] * parameters.flip, parameters.scale[1]] as [number, number],
    rotation: ((parameters.rotation % 360) + 360) % 360,
    depth,
  }
  const emblem = {
    texture: asset.name,
    colors: parameters.colors.map(expression) as [string, string, string],
    mask: [] as number[],
    instances: [instance],
  }
  const coatOfArms: CoatOfArms = {
    ...base.coatOfArms,
    coloredEmblems: [...base.coatOfArms.coloredEmblems, emblem],
  }
  const rendered = renderColoredEmblemLayer(
    base.rendered,
    pattern,
    surfaceMask,
    asset.texture,
    emblem,
    instance,
    namedColors,
  )
  evaluated.value += 1
  const key = `${base.key}\0${asset.name}\0${parameters.colors.flat().join(',')}\0${parameters.position.join(',')}\0${parameters.scale.join(',')}\0${instance.rotation}\0${parameters.flip}`
  return {
    asset,
    candidate: { coatOfArms, rendered, ...measureImageFitLosses(target, rendered), key },
    parameters: {
      colors: parameters.colors.map((color) => [...color] as ByteRgb),
      position: [...parameters.position],
      scale: [...parameters.scale],
      rotation: instance.rotation,
      flip: parameters.flip,
    },
  }
}

interface PaintLayerChoice extends LayerChoice {
  emblem: ColoredEmblem
}

/**
 * Tile painting has a single forward state, so trial choices do not need to
 * copy every previously accepted block. The accepted block is appended only
 * after both coverage-safe scale choices have been compared. This preserves
 * exact rendering while avoiding quadratic array and tie-key growth.
 */
function paintLayerChoice(
  base: ScoredCandidate,
  pattern: DecodedDds,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  target: FitImage,
  asset: FitTextureCandidate,
  parameters: LayerParameters,
  depth: number,
  evaluated: EvaluationCounter,
): PaintLayerChoice {
  const instance = {
    position: [...parameters.position] as [number, number],
    scale: [parameters.scale[0] * parameters.flip, parameters.scale[1]] as [number, number],
    rotation: ((parameters.rotation % 360) + 360) % 360,
    depth,
  }
  const emblem: ColoredEmblem = {
    texture: asset.name,
    colors: parameters.colors.map(expression) as [string, string, string],
    mask: [],
    instances: [instance],
  }
  const rendered = renderColoredEmblemLayer(
    base.rendered,
    pattern,
    surfaceMask,
    asset.texture,
    emblem,
    instance,
    namedColors,
  )
  evaluated.value += 1
  const localKey = `${asset.name}\0${parameters.colors.flat().join(',')}\0${parameters.position.join(',')}\0${parameters.scale.join(',')}\0${instance.rotation}\0${parameters.flip}`
  return {
    asset,
    emblem,
    candidate: {
      coatOfArms: base.coatOfArms,
      rendered,
      ...measureImageFitLosses(target, rendered),
      key: `${base.key.slice(0, 256)}\0paint:${depth}\0${localKey}`,
    },
    parameters: {
      colors: parameters.colors.map((color) => [...color] as ByteRgb),
      position: [...parameters.position],
      scale: [...parameters.scale],
      rotation: instance.rotation,
      flip: parameters.flip,
    },
  }
}

function optimizeLayerChoice(
  initial: LayerChoice,
  shapeMatch: ShapeMatch,
  focus: ResidualFocus,
  base: ScoredCandidate,
  pattern: DecodedDds,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  target: FitImage,
  palettes: ByteRgb[][],
  depth: number,
  evaluated: EvaluationCounter,
  onEvaluation: () => void,
): LayerChoice {
  let best = initial
  const evaluate = (parameters: LayerParameters) => {
    const candidate = layerChoice(
      base, pattern, surfaceMask, namedColors, target,
      initial.asset, parameters, depth, evaluated,
    )
    onEvaluation()
    if (better(candidate.candidate, best.candidate)) best = candidate
  }
  // Shape descriptors can have rotational aliases after their content is
  // normalized (a padded square is the simplest example). For the best assets,
  // cover the full circle before local descent so a bad coarse angle cannot
  // trap the fit. Scale is solved independently on both axes at every seed.
  for (let rotation = 0; rotation < 360; rotation += 45) {
    for (const flip of [shapeMatch.flip, -shapeMatch.flip]) {
      const geometry = initialLayerGeometry(focus, { ...shapeMatch, rotation, flip })
      for (const scaleYFactor of [0.85, 1, 1.15]) {
        for (const scaleXFactor of [0.85, 1, 1.15]) {
          evaluate({
            ...best.parameters,
            position: geometry.position,
            scale: [
              clamp(geometry.scale[0] * scaleXFactor, 0.035, 2.5),
              clamp(geometry.scale[1] * scaleYFactor, 0.035, 2.5),
            ],
            rotation,
            flip,
          })
        }
      }
    }
  }
  const tuningPasses = [
    { position: 0.14, scale: 0.16, rotation: 15 },
    { position: 0.055, scale: 0.065, rotation: 4 },
    { position: 0.025, scale: 0.03, rotation: 2 },
    { position: 0.012, scale: 0.015, rotation: 1 },
    { position: 0.006, scale: 0.007, rotation: 0.5 },
  ]
  for (const tuning of tuningPasses) {
    const positionDelta = Math.max(0.001, Math.min(...best.parameters.scale) * tuning.position)
    const anchorPosition = [...best.parameters.position] as [number, number]
    for (const deltaY of [-positionDelta, 0, positionDelta]) {
      for (const deltaX of [-positionDelta, 0, positionDelta]) {
        evaluate({
          ...best.parameters,
          position: [
            clamp(anchorPosition[0] + deltaX, 0, 1),
            clamp(anchorPosition[1] + deltaY, 0, 1),
          ],
        })
      }
    }
    const scaleDelta = tuning.scale
    const anchorScale = [...best.parameters.scale] as [number, number]
    for (const scaleY of [1 - scaleDelta, 1, 1 + scaleDelta]) {
      for (const scaleX of [1 - scaleDelta, 1, 1 + scaleDelta]) {
        evaluate({
          ...best.parameters,
          scale: [
            clamp(anchorScale[0] * scaleX, 0.035, 2.5),
            clamp(anchorScale[1] * scaleY, 0.035, 2.5),
          ],
        })
      }
    }
    const rotationDelta = tuning.rotation
    const anchorRotation = best.parameters.rotation
    for (const offset of [-rotationDelta, -rotationDelta / 2, 0, rotationDelta / 2, rotationDelta]) {
      evaluate({ ...best.parameters, rotation: anchorRotation + offset })
    }
    for (const flip of [1, -1]) evaluate({ ...best.parameters, flip })
    for (const colors of palettes) evaluate({ ...best.parameters, colors })
  }
  // The broad silhouette pass is intentionally coarse, but the emitted CK3
  // angle is not quantized: finish with a one-degree sweep, then binary-search
  // below a tenth of a degree (0.125 / 2 maximum residual angular error).
  const finalRotation = best.parameters.rotation
  for (let offset = -3; offset <= 3; offset += 1) {
    evaluate({ ...best.parameters, rotation: finalRotation + offset })
  }
  for (const rotationDelta of [0.5, 0.25, 0.125]) {
    const anchorRotation = best.parameters.rotation
    evaluate({ ...best.parameters, rotation: anchorRotation - rotationDelta })
    evaluate({ ...best.parameters, rotation: anchorRotation + rotationDelta })
  }
  return best
}

export interface PaintTile {
  minimumX: number
  minimumY: number
  maximumX: number
  maximumY: number
  color: ByteRgb
  variance: number
  residual: number
}

export interface NativePaintPlacement {
  tile: PaintTile
  instance: CoatOfArmsInstance
}

const NATIVE_TILE_VALIDATION_RESOLUTIONS = [96, 230, 512] as const

function markRectangle(
  target: Uint8Array,
  resolution: number,
  minimumX: number,
  minimumY: number,
  maximumX: number,
  maximumY: number,
): void {
  const startX = clamp(Math.ceil(minimumX * resolution - 0.5), 0, resolution - 1)
  const startY = clamp(Math.ceil(minimumY * resolution - 0.5), 0, resolution - 1)
  const endX = clamp(Math.floor(maximumX * resolution - 0.5), 0, resolution - 1)
  const endY = clamp(Math.floor(maximumY * resolution - 0.5), 0, resolution - 1)
  if (endX < startX || endY < startY) return
  for (let y = startY; y <= endY; y += 1) {
    target.fill(1, y * resolution + startX, y * resolution + endX + 1)
  }
}

function validateNativeTileSeams(
  placements: NativePaintPlacement[],
  searchWidth: number,
  searchHeight: number,
): NativeTileSeamValidation {
  if (!placements.length) return {
    status: 'not-applicable',
    samplingContract: 'pixel-center-hard-geometry-v1',
    metrics: [],
  }
  const metrics = NATIVE_TILE_VALIDATION_RESOLUTIONS.map((resolution) => {
    const expected = new Uint8Array(resolution * resolution)
    const actual = new Uint8Array(resolution * resolution)
    for (const { tile, instance } of placements) {
      markRectangle(
        expected,
        resolution,
        tile.minimumX / searchWidth,
        tile.minimumY / searchHeight,
        tile.maximumX / searchWidth,
        tile.maximumY / searchHeight,
      )
      const halfWidth = Math.abs(instance.scale[0]) / 2
      const halfHeight = Math.abs(instance.scale[1]) / 2
      markRectangle(
        actual,
        resolution,
        instance.position[0] - halfWidth,
        instance.position[1] - halfHeight,
        instance.position[0] + halfWidth,
        instance.position[1] + halfHeight,
      )
    }
    let backgroundLeakPixels = 0
    let peakRowLeakPixels = 0
    const columnLeaks = new Uint32Array(resolution)
    for (let y = 0; y < resolution; y += 1) {
      let rowLeaks = 0
      for (let x = 0; x < resolution; x += 1) {
        const index = y * resolution + x
        if (!expected[index] || actual[index]) continue
        backgroundLeakPixels += 1
        rowLeaks += 1
        columnLeaks[x] += 1
      }
      peakRowLeakPixels = Math.max(peakRowLeakPixels, rowLeaks)
    }
    return {
      resolution,
      backgroundLeakPixels,
      maximumLeakAmount: backgroundLeakPixels > 0 ? 1 : 0,
      peakRowLeakPixels,
      peakColumnLeakPixels: Math.max(...columnLeaks),
    }
  })
  return {
    status: metrics.every((metric) => metric.backgroundLeakPixels === 0) ? 'passed' : 'failed',
    samplingContract: 'pixel-center-hard-geometry-v1',
    metrics,
  }
}

function paintTileStats(
  target: FitImage,
  rendered: RenderedCoatOfArms,
  minimumX: number,
  minimumY: number,
  maximumX: number,
  maximumY: number,
): PaintTile {
  const sums = [0, 0, 0]
  let weight = 0
  let residual = 0
  for (let y = minimumY; y < maximumY; y += 1) {
    for (let x = minimumX; x < maximumX; x += 1) {
      const offset = (y * target.width + x) * 4
      const alpha = target.pixels[offset + 3] / 255
      if (alpha <= 0) continue
      weight += alpha
      for (let channel = 0; channel < 3; channel += 1) {
        sums[channel] += target.pixels[offset + channel] * alpha
        const delta = (target.pixels[offset + channel] - rendered.pixels[offset + channel]) / 255
        residual += delta * delta * alpha
      }
    }
  }
  const color = sums.map((sum) => Math.round(sum / Math.max(weight, 1e-12))) as ByteRgb
  let variance = 0
  for (let y = minimumY; y < maximumY; y += 1) {
    for (let x = minimumX; x < maximumX; x += 1) {
      const offset = (y * target.width + x) * 4
      const alpha = target.pixels[offset + 3] / 255
      for (let channel = 0; channel < 3; channel += 1) {
        const delta = (target.pixels[offset + channel] - color[channel]) / 255
        variance += delta * delta * alpha
      }
    }
  }
  return {
    minimumX,
    minimumY,
    maximumX,
    maximumY,
    color,
    variance: variance / Math.max(weight * 3, 1e-12),
    residual,
  }
}

function nativePaintTiles(
  target: FitImage,
  rendered: RenderedCoatOfArms,
  layerBudget: number,
): PaintTile[] {
  const maximumDepth = nativeTileMaximumDepth(target, layerBudget)
  const leaves: PaintTile[] = []
  const visit = (
    minimumX: number,
    minimumY: number,
    maximumX: number,
    maximumY: number,
    depth: number,
  ) => {
    const tile = paintTileStats(target, rendered, minimumX, minimumY, maximumX, maximumY)
    const width = maximumX - minimumX
    const height = maximumY - minimumY
    if (depth >= maximumDepth || width <= 1 || height <= 1 || tile.variance <= 0.0002) {
      leaves.push(tile)
      return
    }
    const middleX = minimumX + Math.floor(width / 2)
    const middleY = minimumY + Math.floor(height / 2)
    for (const [left, top, right, bottom] of [
      [minimumX, minimumY, middleX, middleY],
      [middleX, minimumY, maximumX, middleY],
      [minimumX, middleY, middleX, maximumY],
      [middleX, middleY, maximumX, maximumY],
    ]) {
      if (right > left && bottom > top) visit(left, top, right, bottom, depth + 1)
    }
  }
  visit(0, 0, target.width, target.height, 0)
  return leaves
    .filter((tile) => tile.residual > 1e-8)
    .sort((left, right) => right.residual - left.residual
      || left.minimumY - right.minimumY
      || left.minimumX - right.minimumX)
}

function nativeTileMaximumDepth(target: Pick<FitImage, 'width' | 'height'>, layerBudget: number): number {
  const resolutionDepth = Math.ceil(Math.log2(Math.max(target.width, target.height)))
  const budgetDepth = Math.ceil(Math.log(Math.max(4, layerBudget * 2)) / Math.log(4))
  return Math.max(2, Math.min(resolutionDepth, budgetDepth))
}

interface NativePaintCheckpointContext {
  lane: ImageFitCheckpoint['lane']
  inputSha256: string
  assetPackManifestSha256: string
  resolution: number
  sourceWidth: number
  sourceHeight: number
  layerBudget: number
  resumeCheckpoint?: ImageFitCheckpoint
  onCheckpoint?: (checkpoint: ImageFitCheckpoint) => void
  emblemAssets: Map<string, FitTextureCandidate>
}

function cloneInstance(instance: CoatOfArmsInstance): CoatOfArmsInstance {
  return {
    position: [...instance.position],
    scale: [...instance.scale],
    rotation: instance.rotation,
    depth: instance.depth,
  }
}

function cloneCheckpointCoatOfArms(coatOfArms: CoatOfArms): CoatOfArms {
  return {
    outerKey: coatOfArms.outerKey,
    parent: coatOfArms.parent,
    pattern: coatOfArms.pattern,
    colors: [...coatOfArms.colors],
    coloredEmblems: coatOfArms.coloredEmblems.map((emblem) => ({
      texture: emblem.texture,
      colors: [...emblem.colors],
      mask: [...emblem.mask],
      instances: emblem.instances.map(cloneInstance),
    })),
    texturedEmblems: coatOfArms.texturedEmblems.map((emblem) => ({ ...emblem })),
    rootPresence: coatOfArms.rootPresence ? {
      pattern: coatOfArms.rootPresence.pattern,
      colors: [...coatOfArms.rootPresence.colors],
    } : undefined,
  }
}

function encodeNativeDepthOrder(coatOfArms: CoatOfArms): CoatOfArms {
  const depths = coatOfArms.coloredEmblems.flatMap((emblem) => (
    emblem.instances.map((instance) => instance.depth)
  ))
  if (!depths.length) return cloneCheckpointCoatOfArms(coatOfArms)
  const minimumDepth = Math.min(...depths)
  const maximumDepth = Math.max(...depths)
  const result = cloneCheckpointCoatOfArms(coatOfArms)
  for (const emblem of result.coloredEmblems) {
    for (const instance of emblem.instances) {
      instance.depth = minimumDepth + maximumDepth - instance.depth
    }
  }
  return result
}

function checkpointFromPaintState(
  context: NativePaintCheckpointContext,
  state: SearchState,
  tiles: PaintTile[],
  nextTileIndex: number,
  evaluatedCandidates: number,
): ImageFitCheckpoint {
  return {
    contract: 'ck3-coa-fit-checkpoint-v1',
    algorithm: 'ck3-coa-browser-fit-v6-budget-exhaustive-edge',
    lane: context.lane,
    inputSha256: context.inputSha256,
    assetPackManifestSha256: context.assetPackManifestSha256,
    resolution: context.resolution,
    sourceWidth: context.sourceWidth,
    sourceHeight: context.sourceHeight,
    layerBudget: context.layerBudget,
    randomSeed: null,
    nextTileIndex,
    tileCount: tiles.length,
    evaluatedCandidates,
    tiles: tiles.map((tile) => ({ ...tile, color: [...tile.color] as ByteRgb })),
    state: {
      coatOfArms: cloneCheckpointCoatOfArms(state.candidate.coatOfArms),
      candidateKey: state.candidate.key,
      patternName: state.patternAsset.name,
      selectedAssetNames: state.selectedAssets.map((asset) => asset.name),
      layerLosses: [...state.layerLosses],
      reconstructionMode: state.reconstructionMode,
      paintPlacements: state.paintPlacements.map((placement) => ({
        tile: { ...placement.tile, color: [...placement.tile.color] as ByteRgb },
        instance: cloneInstance(placement.instance),
      })),
    },
  }
}

function restorePaintState(
  checkpoint: ImageFitCheckpoint,
  initial: SearchState,
  target: FitImage,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  emblemAssets: Map<string, FitTextureCandidate>,
): SearchState {
  if (checkpoint.state.patternName !== initial.patternAsset.name) {
    throw new Error('拟合 checkpoint 的 pattern 与当前搜索路径不一致')
  }
  const selectedAssets = checkpoint.state.selectedAssetNames.map((name) => {
    const asset = emblemAssets.get(name)
    if (!asset) throw new Error(`拟合 checkpoint 引用当前素材包中不存在的 emblem：${name}`)
    return asset
  })
  const coatOfArms = cloneCheckpointCoatOfArms(checkpoint.state.coatOfArms)
  const candidate = score(
    coatOfArms,
    initial.patternAsset.texture,
    Object.fromEntries([...emblemAssets].map(([name, asset]) => [name, asset.texture])),
    target,
    checkpoint.state.candidateKey,
    surfaceMask,
    namedColors,
  )
  return {
    candidate,
    patternAsset: initial.patternAsset,
    selectedAssets,
    layerLosses: [...checkpoint.state.layerLosses],
    reconstructionMode: checkpoint.state.reconstructionMode,
    paintPlacements: checkpoint.state.paintPlacements.map((placement) => ({
      tile: { ...placement.tile, color: [...placement.tile.color] as ByteRgb },
      instance: cloneInstance(placement.instance),
    })),
  }
}

function paintWithNativeTiles(
  initial: SearchState,
  brush: FitTextureCandidate,
  target: FitImage,
  maxLayers: number,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  evaluated: EvaluationCounter,
  onProgress?: (progress: ImageFitProgress) => void,
  checkpointContext?: NativePaintCheckpointContext,
): SearchState {
  const remaining = Math.max(0, maxLayers - initial.selectedAssets.length)
  if (remaining === 0) return initial
  const resumeCheckpoint = checkpointContext
    && checkpointContext.resumeCheckpoint?.lane === checkpointContext.lane
    ? checkpointContext.resumeCheckpoint
    : undefined
  if (
    resumeCheckpoint
    && (
      resumeCheckpoint.tileCount !== resumeCheckpoint.tiles.length
      || resumeCheckpoint.tileCount > remaining
      || !Number.isSafeInteger(resumeCheckpoint.nextTileIndex)
      || resumeCheckpoint.nextTileIndex < 0
      || resumeCheckpoint.nextTileIndex > resumeCheckpoint.tileCount
    )
  ) throw new Error('拟合 checkpoint 的原生块游标或规模不合法')
  const tiles = resumeCheckpoint
    ? resumeCheckpoint.tiles.map((tile) => ({ ...tile, color: [...tile.color] as ByteRgb }))
    : nativePaintTiles(target, initial.candidate.rendered, remaining).slice(0, remaining)
  const shape = textureShapeDescriptor(brush.texture)
  // The CPU reference renderer clips geometry at normalized instance bounds
  // and samples output pixel centers. Exact nominal coverage (factor 1) is
  // therefore the smallest proven crack-free footprint at every resolution;
  // 1.04 remains only as a scored overlap candidate for a genuine loss gain.
  const coverageFactors = [1, 1.04] as const
  const total = Math.max(1, tiles.length * coverageFactors.length)
  const resumeIndex = resumeCheckpoint?.nextTileIndex ?? 0
  const resumedState = resumeCheckpoint && checkpointContext
    ? restorePaintState(
        resumeCheckpoint, initial, target, surfaceMask, namedColors, checkpointContext.emblemAssets,
      )
    : initial
  if (resumeCheckpoint) evaluated.value = Math.max(evaluated.value, resumeCheckpoint.evaluatedCandidates)
  let completed = resumeIndex * coverageFactors.length
  const selectedAssets = [...resumedState.selectedAssets]
  const layerLosses = [...resumedState.layerLosses]
  const paintPlacements = [...resumedState.paintPlacements]
  const coloredEmblems = [...resumedState.candidate.coatOfArms.coloredEmblems]
  const coatOfArms: CoatOfArms = { ...resumedState.candidate.coatOfArms, coloredEmblems }
  let candidate: ScoredCandidate = { ...resumedState.candidate, coatOfArms }
  const state = (): SearchState => ({
    candidate,
    patternAsset: initial.patternAsset,
    selectedAssets,
    layerLosses,
    reconstructionMode: initial.selectedAssets.length > 0
      ? 'hybrid-native-paint'
      : 'native-tile-paint',
    paintPlacements,
  })
  reportProgress(
    onProgress, 'paint', completed, total,
    selectedAssets.length + 1, maxLayers, evaluated.value,
  )
  checkpointContext?.onCheckpoint?.(checkpointFromPaintState(
    checkpointContext, state(), tiles, resumeIndex, evaluated.value,
  ))
  const checkpointInterval = Math.max(1, Math.ceil(tiles.length / 100))
  for (let tileIndex = resumeIndex; tileIndex < tiles.length; tileIndex += 1) {
    const tile = tiles[tileIndex]
    const focus: ResidualFocus = {
      position: [
        (tile.minimumX + tile.maximumX) / 2 / target.width,
        (tile.minimumY + tile.maximumY) / 2 / target.height,
      ],
      scale: [
        (tile.maximumX - tile.minimumX) / target.width,
        (tile.maximumY - tile.minimumY) / target.height,
      ],
      descriptor: new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE),
    }
    const match: ShapeMatch = { asset: brush, shape, rotation: 0, flip: 1, loss: 0 }
    const geometry = initialLayerGeometry(focus, match, 0.005)
    let best: { choice: PaintLayerChoice, scaleFactor: number } | null = null
    for (const scaleFactor of coverageFactors) {
      const choice = paintLayerChoice(
        candidate,
        initial.patternAsset.texture,
        surfaceMask,
        namedColors,
        target,
        brush,
        {
          colors: [tile.color, tile.color, tile.color],
          position: geometry.position,
          scale: [geometry.scale[0] * scaleFactor, geometry.scale[1] * scaleFactor],
          rotation: 0,
          flip: 1,
        },
        selectedAssets.length + 1,
        evaluated,
      )
      completed += 1
      if (
        !best
        || choice.candidate.totalLoss < best.choice.candidate.totalLoss - 1e-12
        || (
          Math.abs(choice.candidate.totalLoss - best.choice.candidate.totalLoss) <= 1e-12
          && (
            scaleFactor < best.scaleFactor
            || (scaleFactor === best.scaleFactor && choice.candidate.key < best.choice.candidate.key)
          )
        )
      ) best = { choice, scaleFactor }
      if (shouldReportProgress(completed, total)) {
        reportProgress(
          onProgress, 'paint', completed, total,
          selectedAssets.length + 1, maxLayers, evaluated.value,
        )
      }
    }
    if (best && best.choice.candidate.totalLoss < candidate.totalLoss - 1e-12) {
      coloredEmblems.push(best.choice.emblem)
      candidate = best.choice.candidate
      selectedAssets.push(brush)
      layerLosses.push(candidate.totalLoss)
      paintPlacements.push({ tile, instance: best.choice.emblem.instances[0] })
    }
    const nextTileIndex = tileIndex + 1
    if (
      checkpointContext
      && (nextTileIndex === tiles.length || nextTileIndex % checkpointInterval === 0)
    ) {
      checkpointContext.onCheckpoint?.(checkpointFromPaintState(
        checkpointContext, state(), tiles, nextTileIndex, evaluated.value,
      ))
    }
  }
  reportProgress(
    onProgress, 'paint', total, total,
    selectedAssets.length, maxLayers, evaluated.value,
  )
  if (selectedAssets.length === initial.selectedAssets.length) return initial
  return state()
}

function edgeResidualHotspots(
  target: FitImage,
  rendered: RenderedCoatOfArms,
  limit: number,
): { x: number, y: number, error: number }[] {
  const hotspots: { x: number, y: number, error: number }[] = []
  for (let y = 0; y < target.height; y += 1) {
    for (let x = 0; x < target.width; x += 1) {
      const offset = (y * target.width + x) * 4
      const alpha = target.pixels[offset + 3] / 255
      if (alpha <= 0) continue
      let colorError = 0
      for (let channel = 0; channel < 3; channel += 1) {
        const delta = (target.pixels[offset + channel] - rendered.pixels[offset + channel]) / 255
        colorError += delta * delta
      }
      let edgeError = 0
      for (const previous of [
        x > 0 ? offset - 4 : -1,
        y > 0 ? offset - target.width * 4 : -1,
      ]) {
        if (previous < 0) continue
        edgeError += Math.abs(
          (luminance(target.pixels, offset) - luminance(target.pixels, previous))
          - (luminance(rendered.pixels, offset) - luminance(rendered.pixels, previous)),
        ) / 255
      }
      const error = alpha * (colorError * 0.62 / 3 + edgeError * 0.38)
      if (error > 1e-12) hotspots.push({ x, y, error })
    }
  }
  return hotspots
    .sort((left, right) => right.error - left.error || left.y - right.y || left.x - right.x)
    .slice(0, limit)
}

function refinePaintedStateAtEdgeHotspots(
  initial: SearchState,
  brush: FitTextureCandidate,
  target: FitImage,
  maxLayers: number,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  evaluated: EvaluationCounter,
  onProgress?: (progress: ImageFitProgress) => void,
): SearchState {
  let state = initial
  // Continue until the user's remaining instance budget is exhausted or an
  // entire pass has no independently total-safe, edge-improving candidate.
  // The previous constant eight-pass ceiling silently left hundreds of
  // strictly improving slots unused in portrait fits.
  const maximumLayers = maxLayers - initial.selectedAssets.length
  if (maximumLayers <= 0) return state
  const shape = textureShapeDescriptor(brush.texture)
  const patchSizes = [[1, 1], [2, 1], [1, 2], [2, 2], [3, 1], [1, 3]] as const
  const coverageFactors = [1, 1.04] as const
  // Edge-search breadth is computational work, not a hidden layer clamp.
  // Scale it with the user's budget so the 128-instance reference point does
  // not pay the same 32-hotspot exhaustive pass as 512+ instance runs.
  const normalizedHotspotBudget = Math.min(maxLayers, 1_024) / 1_024
  const hotspotLimit = Math.max(1, Math.floor(32 * normalizedHotspotBudget * normalizedHotspotBudget))
  for (let layer = 0; layer < maximumLayers; layer += 1) {
    const hotspots = edgeResidualHotspots(target, state.candidate.rendered, hotspotLimit)
    const rectangles = new Map<string, [number, number, number, number]>()
    for (const hotspot of hotspots) {
      for (const [width, height] of patchSizes) {
        const minimumX = clamp(hotspot.x - Math.floor((width - 1) / 2), 0, target.width - width)
        const minimumY = clamp(hotspot.y - Math.floor((height - 1) / 2), 0, target.height - height)
        const rectangle: [number, number, number, number] = [
          minimumX, minimumY, minimumX + width, minimumY + height,
        ]
        rectangles.set(rectangle.join(','), rectangle)
      }
    }
    const total = Math.max(1, rectangles.size * coverageFactors.length)
    let completed = 0
    let best: { choice: LayerChoice, tile: PaintTile, scaleFactor: number } | null = null
    reportProgress(
      onProgress, 'refine', 0, total,
      state.selectedAssets.length + 1, maxLayers, evaluated.value,
    )
    for (const [minimumX, minimumY, maximumX, maximumY] of rectangles.values()) {
      const tile = paintTileStats(
        target, state.candidate.rendered,
        minimumX, minimumY, maximumX, maximumY,
      )
      const focus: ResidualFocus = {
        position: [
          (minimumX + maximumX) / 2 / target.width,
          (minimumY + maximumY) / 2 / target.height,
        ],
        scale: [
          (maximumX - minimumX) / target.width,
          (maximumY - minimumY) / target.height,
        ],
        descriptor: new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE),
      }
      const geometry = initialLayerGeometry(
        focus,
        { asset: brush, shape, rotation: 0, flip: 1, loss: 0 },
        0.001,
      )
      for (const scaleFactor of coverageFactors) {
        const choice = layerChoice(
          state.candidate,
          state.patternAsset.texture,
          surfaceMask,
          namedColors,
          target,
          brush,
          {
            colors: [tile.color, tile.color, tile.color],
            position: geometry.position,
            scale: [geometry.scale[0] * scaleFactor, geometry.scale[1] * scaleFactor],
            rotation: 0,
            flip: 1,
          },
          state.selectedAssets.length + 1,
          evaluated,
        )
        completed += 1
        const passesGate = choice.candidate.totalLoss <= state.candidate.totalLoss + 1e-12
          && choice.candidate.edgeLoss < state.candidate.edgeLoss - 1e-12
        if (
          passesGate
          && (
            !best
            || choice.candidate.totalLoss < best.choice.candidate.totalLoss - 1e-12
            || (
              Math.abs(choice.candidate.totalLoss - best.choice.candidate.totalLoss) <= 1e-12
              && (
                choice.candidate.edgeLoss < best.choice.candidate.edgeLoss - 1e-12
                || (
                  Math.abs(choice.candidate.edgeLoss - best.choice.candidate.edgeLoss) <= 1e-12
                  && (
                    scaleFactor < best.scaleFactor
                    || (scaleFactor === best.scaleFactor && choice.candidate.key < best.choice.candidate.key)
                  )
                )
              )
            )
          )
        ) best = { choice, tile, scaleFactor }
        if (shouldReportProgress(completed, total)) {
          reportProgress(
            onProgress, 'refine', completed, total,
            state.selectedAssets.length + 1, maxLayers, evaluated.value,
          )
        }
      }
    }
    if (!best) break
    const acceptedEmblems = best.choice.candidate.coatOfArms.coloredEmblems
    const acceptedInstance = acceptedEmblems[acceptedEmblems.length - 1].instances[0]
    state = {
      candidate: best.choice.candidate,
      patternAsset: state.patternAsset,
      selectedAssets: [...state.selectedAssets, brush],
      layerLosses: [...state.layerLosses, best.choice.candidate.totalLoss],
      reconstructionMode: 'native-edge-refined',
      paintPlacements: [...state.paintPlacements, { tile: best.tile, instance: acceptedInstance }],
    }
  }
  return state
}

function refinePaintedStateAtHighResolution(
  initial: SearchState,
  brush: FitTextureCandidate,
  emblemTextures: Record<string, DecodedDds>,
  target: FitImage,
  highResolutionTarget: FitImage,
  maxLayers: number,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  evaluated: EvaluationCounter,
  onProgress?: (progress: ImageFitProgress) => void,
): SearchState {
  const remaining = maxLayers - initial.selectedAssets.length
  if (
    remaining <= 0
    || highResolutionTarget.width <= target.width
    || highResolutionTarget.height <= target.height
  ) return initial
  let highResolutionCandidate = score(
    initial.candidate.coatOfArms,
    initial.patternAsset.texture,
    emblemTextures,
    highResolutionTarget,
    `${initial.candidate.key}\0high-resolution:${highResolutionTarget.width}`,
    surfaceMask,
    namedColors,
  )
  evaluated.value += 1
  const tiles = nativePaintTiles(
    highResolutionTarget,
    highResolutionCandidate.rendered,
    remaining,
  ).slice(0, remaining)
  if (!tiles.length) return initial
  const shape = textureShapeDescriptor(brush.texture)
  const coverageFactors = [1, 1.04] as const
  const total = Math.max(1, tiles.length * (coverageFactors.length + 1))
  let completed = 0
  let state = initial
  reportProgress(
    onProgress, 'refine', 0, total,
    state.selectedAssets.length + 1, maxLayers, evaluated.value,
  )
  for (const tile of tiles) {
    if (state.selectedAssets.length >= maxLayers) break
    const focus: ResidualFocus = {
      position: [
        (tile.minimumX + tile.maximumX) / 2 / highResolutionTarget.width,
        (tile.minimumY + tile.maximumY) / 2 / highResolutionTarget.height,
      ],
      scale: [
        (tile.maximumX - tile.minimumX) / highResolutionTarget.width,
        (tile.maximumY - tile.minimumY) / highResolutionTarget.height,
      ],
      descriptor: new Float32Array(SHAPE_DESCRIPTOR_SIZE * SHAPE_DESCRIPTOR_SIZE),
    }
    const geometry = initialLayerGeometry(
      focus,
      { asset: brush, shape, rotation: 0, flip: 1, loss: 0 },
      0.001,
    )
    let best: { choice: PaintLayerChoice, parameters: LayerParameters, scaleFactor: number } | null = null
    for (const scaleFactor of coverageFactors) {
      const parameters: LayerParameters = {
        colors: [tile.color, tile.color, tile.color],
        position: geometry.position,
        scale: [geometry.scale[0] * scaleFactor, geometry.scale[1] * scaleFactor],
        rotation: 0,
        flip: 1,
      }
      const choice = paintLayerChoice(
        highResolutionCandidate,
        initial.patternAsset.texture,
        surfaceMask,
        namedColors,
        highResolutionTarget,
        brush,
        parameters,
        state.selectedAssets.length + 1,
        evaluated,
      )
      completed += 1
      const highResolutionImprovement = (
        choice.candidate.totalLoss < highResolutionCandidate.totalLoss - 1e-12
        && choice.candidate.edgeLoss <= highResolutionCandidate.edgeLoss + 1e-12
      ) || (
        choice.candidate.edgeLoss < highResolutionCandidate.edgeLoss - 1e-12
        && choice.candidate.totalLoss <= highResolutionCandidate.totalLoss + 1e-12
      )
      if (
        highResolutionImprovement
        && (
          !best
          || choice.candidate.totalLoss < best.choice.candidate.totalLoss - 1e-12
          || (
            Math.abs(choice.candidate.totalLoss - best.choice.candidate.totalLoss) <= 1e-12
            && (
              choice.candidate.edgeLoss < best.choice.candidate.edgeLoss - 1e-12
              || (
                Math.abs(choice.candidate.edgeLoss - best.choice.candidate.edgeLoss) <= 1e-12
                && scaleFactor < best.scaleFactor
              )
            )
          )
        )
      ) best = { choice, parameters, scaleFactor }
    }
    if (best) {
      const lowResolutionChoice = layerChoice(
        state.candidate,
        initial.patternAsset.texture,
        surfaceMask,
        namedColors,
        target,
        brush,
        best.parameters,
        state.selectedAssets.length + 1,
        evaluated,
      )
      completed += 1
      if (
        lowResolutionChoice.candidate.totalLoss <= state.candidate.totalLoss + 1e-12
        && lowResolutionChoice.candidate.edgeLoss <= state.candidate.edgeLoss + 1e-12
      ) {
        state = {
          candidate: lowResolutionChoice.candidate,
          patternAsset: state.patternAsset,
          selectedAssets: [...state.selectedAssets, brush],
          layerLosses: [...state.layerLosses, lowResolutionChoice.candidate.totalLoss],
          reconstructionMode: 'native-high-resolution-edge-refined',
          paintPlacements: state.paintPlacements,
        }
        highResolutionCandidate = {
          ...best.choice.candidate,
          coatOfArms: lowResolutionChoice.candidate.coatOfArms,
        }
      }
    } else {
      completed += 1
    }
    if (shouldReportProgress(completed, total)) {
      reportProgress(
        onProgress, 'refine', completed, total,
        state.selectedAssets.length + 1, maxLayers, evaluated.value,
      )
    }
  }
  reportProgress(
    onProgress, 'refine', total, total,
    state.selectedAssets.length, maxLayers, evaluated.value,
  )
  return state
}

function refinePaintedStateWithNativeShape(
  initial: SearchState,
  emblems: FitTextureCandidate[],
  shapeDescriptors: Map<string, TextureShape>,
  target: FitImage,
  maxLayers: number,
  surfaceMask: DecodedDds | undefined,
  namedColors: NamedColorMap,
  evaluated: EvaluationCounter,
  shapeCandidateCount: number,
  onProgress?: (progress: ImageFitProgress) => void,
): SearchState {
  if (initial.selectedAssets.length >= maxLayers) return initial
  // The coverage brush is also a useful rotated local primitive. Keeping it
  // eligible here lets the refinement improve a curved boundary even when no
  // semantic emblem survives the independent total/edge gate. Mixed-texture
  // candidates are still measured separately through textureNames.
  const refiners = emblems
  if (!refiners.length) return initial
  const focus = residualGeometry(target, initial.candidate.rendered)
  const ranked = rankShapes(focus, refiners, shapeDescriptors)
  const shortlistNames = new Set(selectMixedNativeShapeCandidateNames(
    ranked.map((item) => item.asset.name),
    Math.min(12, shapeCandidateCount, refiners.length),
  ))
  const shortlist = ranked.filter((item) => shortlistNames.has(item.asset.name))
  const palettes = permutations(residualColors(target, initial.candidate.rendered))
  const coarseEvaluations = shortlist.length * palettes.length * 3 * 3
  const localPasses = [
    { position: 0.05, scale: 0.08, rotation: 5 },
    { position: 0.018, scale: 0.025, rotation: 1 },
    { position: 0.006, scale: 0.008, rotation: 0.25 },
  ]
  const localEvaluations = localPasses.length * (9 + 9 + 5 + 2 + palettes.length)
  const total = Math.max(1, coarseEvaluations + localEvaluations)
  let completed = 0
  let best: LayerChoice | null = null
  const accept = (choice: LayerChoice) => {
    completed += 1
    const passesGate = choice.candidate.totalLoss <= initial.candidate.totalLoss + 1e-12
      && choice.candidate.edgeLoss < initial.candidate.edgeLoss - 1e-12
    if (
      passesGate
      && (
        !best
        || choice.candidate.totalLoss < best.candidate.totalLoss - 1e-12
        || (
          Math.abs(choice.candidate.totalLoss - best.candidate.totalLoss) <= 1e-12
          && (
            choice.candidate.edgeLoss < best.candidate.edgeLoss - 1e-12
            || (
              Math.abs(choice.candidate.edgeLoss - best.candidate.edgeLoss) <= 1e-12
              && choice.candidate.key < best.candidate.key
            )
          )
        )
      )
    ) best = choice
    if (shouldReportProgress(completed, total)) {
      reportProgress(
        onProgress, 'refine', completed, total,
        initial.selectedAssets.length + 1, maxLayers, evaluated.value,
      )
    }
  }
  reportProgress(
    onProgress, 'refine', 0, total,
    initial.selectedAssets.length + 1, maxLayers, evaluated.value,
  )
  for (const match of shortlist) {
    const geometry = initialLayerGeometry(focus, match, 0.012)
    for (const colors of palettes) {
      for (const scaleFactor of [0.82, 1, 1.18]) {
        for (const rotationOffset of [-20, 0, 20]) {
          accept(layerChoice(
            initial.candidate,
            initial.patternAsset.texture,
            surfaceMask,
            namedColors,
            target,
            match.asset,
            {
              colors,
              position: [...geometry.position],
              scale: [
                clamp(geometry.scale[0] * scaleFactor, 0.012, 2.5),
                clamp(geometry.scale[1] * scaleFactor, 0.012, 2.5),
              ],
              rotation: match.rotation + rotationOffset,
              flip: match.flip,
            },
            initial.selectedAssets.length + 1,
            evaluated,
          ))
        }
      }
    }
  }
  if (best as LayerChoice | null) {
    for (const tuning of localPasses) {
      const currentBest = best as LayerChoice | null
      if (!currentBest) break
      const anchor = currentBest.parameters
      const positionDelta = Math.max(0.001, Math.min(...anchor.scale) * tuning.position)
      for (const deltaY of [-positionDelta, 0, positionDelta]) {
        for (const deltaX of [-positionDelta, 0, positionDelta]) {
          accept(layerChoice(
            initial.candidate, initial.patternAsset.texture, surfaceMask, namedColors, target,
            currentBest.asset,
            { ...anchor, position: [
              clamp(anchor.position[0] + deltaX, 0, 1),
              clamp(anchor.position[1] + deltaY, 0, 1),
            ] },
            initial.selectedAssets.length + 1, evaluated,
          ))
        }
      }
      for (const scaleY of [1 - tuning.scale, 1, 1 + tuning.scale]) {
        for (const scaleX of [1 - tuning.scale, 1, 1 + tuning.scale]) {
          accept(layerChoice(
            initial.candidate, initial.patternAsset.texture, surfaceMask, namedColors, target,
            currentBest.asset,
            { ...anchor, scale: [
              clamp(anchor.scale[0] * scaleX, 0.012, 2.5),
              clamp(anchor.scale[1] * scaleY, 0.012, 2.5),
            ] },
            initial.selectedAssets.length + 1, evaluated,
          ))
        }
      }
      for (const offset of [-tuning.rotation, -tuning.rotation / 2, 0, tuning.rotation / 2, tuning.rotation]) {
        accept(layerChoice(
          initial.candidate, initial.patternAsset.texture, surfaceMask, namedColors, target,
          currentBest.asset, { ...anchor, rotation: anchor.rotation + offset },
          initial.selectedAssets.length + 1, evaluated,
        ))
      }
      for (const flip of [1, -1]) {
        accept(layerChoice(
          initial.candidate, initial.patternAsset.texture, surfaceMask, namedColors, target,
          currentBest.asset, { ...anchor, flip },
          initial.selectedAssets.length + 1, evaluated,
        ))
      }
      for (const colors of palettes) {
        accept(layerChoice(
          initial.candidate, initial.patternAsset.texture, surfaceMask, namedColors, target,
          currentBest.asset, { ...anchor, colors },
          initial.selectedAssets.length + 1, evaluated,
        ))
      }
    }
  }
  reportProgress(
    onProgress, 'refine', total, total,
    best ? initial.selectedAssets.length + 1 : initial.selectedAssets.length,
    maxLayers, evaluated.value,
  )
  const selected = best as LayerChoice | null
  if (!selected) return initial
  return {
    candidate: selected.candidate,
    patternAsset: initial.patternAsset,
    selectedAssets: [...initial.selectedAssets, selected.asset],
    layerLosses: [...initial.layerLosses, selected.candidate.totalLoss],
    reconstructionMode: 'hybrid-native-paint',
    paintPlacements: initial.paintPlacements,
  }
}

export function fitImageToCoatOfArms(
  image: FitImage,
  patternCandidates: FitTextureCandidate[],
  emblemCandidates: FitTextureCandidate[],
  options: ImageFitOptions = {},
): ImageFitResult {
  validateImage(image)
  const resolution = options.resolution ?? DEFAULT_RESOLUTION
  const target = resizeFitImage(image, resolution)
  const sourceWidth = options.sourceWidth ?? image.width
  const sourceHeight = options.sourceHeight ?? image.height
  if (
    !Number.isSafeInteger(sourceWidth)
    || !Number.isSafeInteger(sourceHeight)
    || sourceWidth < 1
    || sourceHeight < 1
  ) throw new Error('原始图片尺寸不合法')
  const suppliedPyramid = options.pyramidImages ?? []
  for (const pyramidImage of suppliedPyramid) validateImage(pyramidImage)
  const pyramidTargets = new Map<number, FitImage>([[resolution, target]])
  for (const pyramidImage of suppliedPyramid) {
    if (pyramidImage.width === pyramidImage.height) {
      pyramidTargets.set(pyramidImage.width, pyramidImage)
    }
  }
  const pyramidResolutions = [...pyramidTargets.keys()].sort((left, right) => left - right)
  const surfaceMask = options.surfaceMask
  const namedColors = options.namedColors ?? {}
  const patterns = [...patternCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxPatterns ?? 64)
  const emblems = [...emblemCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxEmblemCandidates ?? emblemCandidates.length)
  const maxLayers = normalizeLayerBudget(options.maxLayers)
  const inputSha256 = options.inputSha256 ?? ''
  const assetPackManifestSha256 = options.assetPackManifestSha256 ?? ''
  const resumeCheckpoint = options.resumeCheckpoint
  if (resumeCheckpoint) {
    if (
      resumeCheckpoint.contract !== 'ck3-coa-fit-checkpoint-v1'
      || resumeCheckpoint.algorithm !== 'ck3-coa-browser-fit-v6-budget-exhaustive-edge'
    ) throw new Error('拟合 checkpoint 版本不兼容')
    if (
      resumeCheckpoint.inputSha256 !== inputSha256
      || resumeCheckpoint.assetPackManifestSha256 !== assetPackManifestSha256
    ) throw new Error('拟合 checkpoint 的输入图片或素材包标识不匹配')
    if (
      resumeCheckpoint.resolution !== resolution
      || resumeCheckpoint.sourceWidth !== sourceWidth
      || resumeCheckpoint.sourceHeight !== sourceHeight
      || resumeCheckpoint.layerBudget !== maxLayers
    ) throw new Error('拟合 checkpoint 的搜索配置不匹配')
  }
  const shapeCandidateCount = clamp(Math.floor(options.refinementCandidates ?? 48), 8, 128)
  const beamWidth = clamp(Math.floor(options.beamWidth ?? 2), 1, 4)
  const minRelativeLayerImprovement = clamp(options.minRelativeLayerImprovement ?? 0, 0, 1)
  if (!patterns.length) throw new Error('素材包没有可用于拟合的 pattern')
  const palette = dominantColors(target)
  const backgroundPalettes = permutations(palette)
  const evaluated: EvaluationCounter = { value: 0 }
  const batchScorer = options.batchScorer
  const batchReferenceTolerance = 2e-6
  const batchSearch: ImageFitBatchSearchReceipt = {
    requested: options.batchSearchRequested === true,
    backend: batchScorer?.backend ?? null,
    status: 'unavailable_fallback',
    batches: 0,
    candidates: 0,
    maximumBatchSize: batchScorer?.maximumBatchSize ?? 0,
    cpuReferenceTolerance: batchReferenceTolerance,
    maximumMetricDelta: 0,
    cpuReferenceAgreement: false,
  }
  let batchSearchDisabled = false
  const rankWithBatchScorer = <T>(
    items: readonly T[],
    candidateOf: (item: T) => ScoredCandidate,
  ): T[] => {
    const cpuRanked = [...items].sort((left, right) => (
      candidateOf(left).totalLoss - candidateOf(right).totalLoss
      || candidateOf(left).key.localeCompare(candidateOf(right).key)
    ))
    if (!batchScorer || batchSearchDisabled || items.length < 2) return cpuRanked
    const gpuMetrics: ImageFitMetrics[] = []
    for (let first = 0; first < items.length; first += batchScorer.maximumBatchSize) {
      const batch = items.slice(first, first + batchScorer.maximumBatchSize)
      const metrics = batchScorer.score(batch.map((item) => candidateOf(item).rendered))
      if (!metrics || metrics.length !== batch.length) break
      batchSearch.batches += 1
      batchSearch.candidates += batch.length
      gpuMetrics.push(...metrics)
    }
    if (gpuMetrics.length !== items.length) {
      const scorerStatus = batchScorer.status()
      batchSearch.status = scorerStatus === 'context_lost'
        ? 'context_lost_fallback'
        : scorerStatus === 'runtime_error'
          ? 'runtime_error_fallback'
          : 'unavailable_fallback'
      batchSearch.cpuReferenceAgreement = false
      batchSearchDisabled = true
      return cpuRanked
    }
    let maximumMetricDelta = 0
    for (let index = 0; index < gpuMetrics.length; index += 1) {
      const reference = candidateOf(items[index])
      const metric = gpuMetrics[index]
      maximumMetricDelta = Math.max(
        maximumMetricDelta,
        Math.abs(metric.colorLoss - reference.colorLoss),
        Math.abs(metric.edgeLoss - reference.edgeLoss),
        Math.abs(metric.totalLoss - reference.totalLoss),
      )
    }
    batchSearch.maximumMetricDelta = Math.max(batchSearch.maximumMetricDelta, maximumMetricDelta)
    const gpuRanked = items
      .map((item, index) => ({ item, metric: gpuMetrics[index] }))
      .sort((left, right) => (
        left.metric.totalLoss - right.metric.totalLoss
        || candidateOf(left.item).key.localeCompare(candidateOf(right.item).key)
      ))
      .map(({ item }) => item)
    const referenceAgreement = maximumMetricDelta <= batchReferenceTolerance
      && gpuRanked.every((item, index) => candidateOf(item).key === candidateOf(cpuRanked[index]).key)
    batchSearch.cpuReferenceAgreement = referenceAgreement
    if (!referenceAgreement) {
      batchSearch.status = 'reference_mismatch_fallback'
      batchSearchDisabled = true
      return cpuRanked
    }
    batchSearch.status = 'active'
    return gpuRanked
  }
  let bestBackground: ScoredCandidate | null = null
  const backgroundCandidates: { candidate: ScoredCandidate, patternAsset: FitTextureCandidate }[] = []
  const backgroundTotal = patterns.length * backgroundPalettes.length
  let backgroundCompleted = 0
  reportProgress(options.onProgress, 'background', 0, backgroundTotal, 0, maxLayers, evaluated.value)
  for (const pattern of patterns) {
    for (const colors of backgroundPalettes) {
      const coatOfArms: CoatOfArms = {
        outerKey: 'coa', parent: '', pattern: pattern.name,
        colors: colors.map(expression) as [string, string, string],
        coloredEmblems: [], texturedEmblems: [],
      }
      const candidate = score(
        coatOfArms,
        pattern.texture,
        {},
        target,
        `${pattern.name}\0${colors.flat().join(',')}`,
        surfaceMask,
        namedColors,
      )
      evaluated.value += 1
      backgroundCompleted += 1
      if (shouldReportProgress(backgroundCompleted, backgroundTotal)) {
        reportProgress(
          options.onProgress, 'background', backgroundCompleted, backgroundTotal,
          0, maxLayers, evaluated.value,
        )
      }
      if (better(candidate, bestBackground)) {
        bestBackground = candidate
      }
      backgroundCandidates.push({ candidate, patternAsset: pattern })
    }
  }
  if (!bestBackground) throw new Error('无法生成背景候选')

  const initialLoss = bestBackground.totalLoss
  const rankedBackgrounds = rankWithBatchScorer(backgroundCandidates, (item) => item.candidate)
  const backgroundSeeds = rankedBackgrounds.slice(0, beamWidth)
  const bestSolidBackground = rankedBackgrounds.find((item) => item.patternAsset.name === 'pattern_solid.dds')
  if (
    beamWidth > 1
    && bestSolidBackground
    && !backgroundSeeds.some((item) => item.patternAsset.name === 'pattern_solid.dds')
  ) backgroundSeeds[backgroundSeeds.length - 1] = bestSolidBackground
  let beam: SearchState[] = backgroundSeeds.map(({ candidate, patternAsset }) => ({
    candidate,
    patternAsset,
    selectedAssets: [],
    layerLosses: [candidate.totalLoss],
    reconstructionMode: 'semantic-search',
    paintPlacements: [],
  }))
  const shapeDescriptors = new Map<string, TextureShape>()
  const paintBrush = emblems.find((item) => item.name === 'ce_block_02.dds')
    ?? emblems.find((item) => item.name === 'ce_billet.dds')
    ?? emblems.find((item) => item.name === 'ce_circle.dds')
  const emblemAssetMap = new Map(emblems.map((item) => [item.name, item]))
  const emblemTextureMap = Object.fromEntries(emblems.map((item) => [item.name, item.texture]))
  let terminationReason: ImageFitResult['provenance']['terminationReason'] = 'layer_budget'
  // Large-budget runs used to force this value to zero, which made the
  // algorithm unconditionally collapse to a single rectangular texture.
  // Keep a bounded semantic seed stage, then spend the remaining user budget
  // painting the residual. The pure tile candidate remains as an ablation.
  const hasSemanticAlternative = !paintBrush
    || emblems.some((item) => item.name !== paintBrush.name)
  const semanticLayerBudget = Math.min(
    maxLayers,
    maxLayers >= 128 && paintBrush
      ? (hasSemanticAlternative ? 1 : 0)
      : 6,
  )
  for (let layer = 0; layer < semanticLayerBudget && emblems.length; layer += 1) {
    if (beam[0].candidate.totalLoss <= 1e-12) {
      terminationReason = 'exact_match'
      break
    }
    const activeBeamWidth = layer < 6 ? beamWidth : 1
    const expansions: SearchState[] = []
    let foundStrictImprovement = false
    for (const state of beam) {
      const focus = residualGeometry(target, state.candidate.rendered)
      reportProgress(options.onProgress, 'coarse', 0, emblems.length, layer + 1, maxLayers, evaluated.value)
      const rankedShapes = rankShapes(focus, emblems, shapeDescriptors, (completed) => {
        if (shouldReportProgress(completed, emblems.length)) {
          reportProgress(
            options.onProgress, 'coarse', completed, emblems.length,
            layer + 1, maxLayers, evaluated.value,
          )
        }
      })
      const shortlist = rankedShapes.slice(0, Math.min(shapeCandidateCount, rankedShapes.length))
      const palettes = permutations(residualColors(target, state.candidate.rendered))
      // Full-circle transform fitting is the expensive stage. The descriptor
      // shortlist is broad, then real-render coarse scoring promotes only the
      // best three assets to continuous local optimization.
      const localCandidateCount = Math.min(3, shortlist.length)
      const refinementTotal = shortlist.length * palettes.length * 3 * 3
        + localCandidateCount * (144 + 5 * (9 + 9 + 5 + 2 + palettes.length) + 13)
      let refinementCompleted = 0
      const reportRefinement = () => {
        refinementCompleted += 1
        if (shouldReportProgress(refinementCompleted, refinementTotal)) {
          reportProgress(
            options.onProgress, 'refine', refinementCompleted, refinementTotal,
            layer + 1, maxLayers, evaluated.value,
          )
        }
      }
      reportProgress(
        options.onProgress, 'refine', 0, refinementTotal,
        layer + 1, maxLayers, evaluated.value,
      )
      const coarseChoices: { choice: LayerChoice, match: ShapeMatch }[] = []
      for (const match of shortlist) {
        let assetBest: LayerChoice | null = null
        const geometry = initialLayerGeometry(focus, match)
        for (const colors of palettes) {
          for (const scaleFactor of [0.88, 1, 1.12]) {
            for (const rotationOffset of [-15, 0, 15]) {
              const choice = layerChoice(
                state.candidate,
                state.patternAsset.texture,
                surfaceMask,
                namedColors,
                target,
                match.asset,
                {
                  colors,
                  position: [...geometry.position],
                  scale: [
                    clamp(geometry.scale[0] * scaleFactor, 0.035, 2.5),
                    clamp(geometry.scale[1] * scaleFactor, 0.035, 2.5),
                  ],
                  rotation: match.rotation + rotationOffset,
                  flip: match.flip,
                },
                layer + 1,
                evaluated,
              )
              reportRefinement()
              if (!assetBest || better(choice.candidate, assetBest.candidate)) assetBest = choice
            }
          }
        }
        if (assetBest) coarseChoices.push({ choice: assetBest, match })
      }
      const localChoices = rankWithBatchScorer(coarseChoices, (item) => item.choice.candidate)
        .slice(0, localCandidateCount)
        .map(({ choice, match }) => optimizeLayerChoice(
          choice, match, focus,
          state.candidate,
          state.patternAsset.texture,
          surfaceMask,
          namedColors,
          target,
          palettes,
          layer + 1,
          evaluated,
          reportRefinement,
        ))
      const rankedLocalChoices = rankWithBatchScorer(localChoices, (item) => item.candidate)

      for (const choice of rankedLocalChoices.slice(0, activeBeamWidth)) {
        if (choice.candidate.totalLoss >= state.candidate.totalLoss - 1e-12) continue
        foundStrictImprovement = true
        const relativeGain = (state.candidate.totalLoss - choice.candidate.totalLoss)
          / Math.max(state.candidate.totalLoss, 1e-12)
        if (relativeGain + 1e-12 < minRelativeLayerImprovement) continue
        expansions.push({
          candidate: choice.candidate,
          patternAsset: state.patternAsset,
          selectedAssets: [...state.selectedAssets, choice.asset],
          layerLosses: [...state.layerLosses, choice.candidate.totalLoss],
          reconstructionMode: 'semantic-search',
          paintPlacements: [],
        })
      }
    }
    if (!expansions.length) {
      terminationReason = foundStrictImprovement ? 'minimum_improvement' : 'no_improvement'
      break
    }
    const rankedExpansions = expansions
      .sort((left, right) => left.candidate.totalLoss - right.candidate.totalLoss
        || left.candidate.key.localeCompare(right.candidate.key))
      .filter((state, index, items) => items.findIndex((item) => item.candidate.key === state.candidate.key) === index)
    if (layer < 6 && activeBeamWidth > 1) {
      const diverse = [...new Set(beam.map((state) => state.patternAsset.name))]
        .map((patternName) => rankedExpansions.find((state) => state.patternAsset.name === patternName))
        .filter((state): state is SearchState => Boolean(state))
      for (const state of rankedExpansions) {
        if (diverse.length >= activeBeamWidth) break
        if (!diverse.includes(state)) diverse.push(state)
      }
      beam = diverse
        .sort((left, right) => left.candidate.totalLoss - right.candidate.totalLoss
          || left.candidate.key.localeCompare(right.candidate.key))
        .slice(0, activeBeamWidth)
    } else {
      beam = rankedExpansions.slice(0, activeBeamWidth)
    }
  }
  const finalists = [...beam]
  let nativePaintBaseline: SearchState | undefined
  let baselineEdgeRepair: ImageFitResult['provenance']['baselineEdgeRepair'] = {
    availableSlots: 0,
    acceptedLayers: 0,
    evaluatedCandidates: 0,
    terminationReason: 'not_applicable',
  }
  let highResolutionEdgeRepair: ImageFitResult['provenance']['highResolutionEdgeRepair'] = {
    resolution: null,
    availableSlots: 0,
    acceptedLayers: 0,
    evaluatedCandidates: 0,
    terminationReason: 'not_applicable',
  }
  let nativeShapeRefinement: ImageFitResult['provenance']['nativeShapeRefinement'] = {
    requestedPasses: 0,
    completedPasses: 0,
    acceptedLayers: 0,
    evaluatedCandidates: 0,
    primitiveTextureNames: [],
    acceptedTextureNames: [],
    terminationReason: 'not_applicable',
  }
  if (paintBrush && bestSolidBackground) {
    const solidState: SearchState = {
      candidate: bestSolidBackground.candidate,
      patternAsset: bestSolidBackground.patternAsset,
      selectedAssets: [],
      layerLosses: [bestSolidBackground.candidate.totalLoss],
      reconstructionMode: 'native-tile-paint',
      paintPlacements: [],
    }
    // Keep a pure raster-like reconstruction as the deterministic ablation.
    const paintState = paintWithNativeTiles(
      solidState,
      paintBrush,
      target,
      maxLayers,
      surfaceMask,
      namedColors,
      evaluated,
      options.onProgress,
      {
        lane: 'baseline', inputSha256, assetPackManifestSha256,
        resolution, sourceWidth, sourceHeight, layerBudget: maxLayers,
        resumeCheckpoint,
        onCheckpoint: resumeCheckpoint?.lane === 'hybrid' ? undefined : options.onCheckpoint,
        emblemAssets: emblemAssetMap,
      },
    )
    const seamValidation = validateNativeTileSeams(
      paintState.paintPlacements,
      target.width,
      target.height,
    )
    if (seamValidation.metrics.some((metric) => metric.backgroundLeakPixels > 0)) {
      throw new Error('原生块候选未通过 96/230/512 高分辨率覆盖门禁')
    }
    nativePaintBaseline = paintState
    finalists.push(paintState)
    const availableEdgeSlots = maxLayers - paintState.selectedAssets.length
    const evaluatedBeforeEdgeRepair = evaluated.value
    const edgeRefinedPaintState = refinePaintedStateAtEdgeHotspots(
      paintState,
      paintBrush,
      target,
      maxLayers,
      surfaceMask,
      namedColors,
      evaluated,
      options.onProgress,
    )
    const acceptedEdgeLayers = edgeRefinedPaintState.selectedAssets.length - paintState.selectedAssets.length
    baselineEdgeRepair = {
      availableSlots: availableEdgeSlots,
      acceptedLayers: acceptedEdgeLayers,
      evaluatedCandidates: evaluated.value - evaluatedBeforeEdgeRepair,
      terminationReason: availableEdgeSlots === 0 || acceptedEdgeLayers === availableEdgeSlots
        ? 'layer_budget'
        : 'no_improvement',
    }
    if (edgeRefinedPaintState !== paintState) finalists.push(edgeRefinedPaintState)
    const highResolutionTarget = [...pyramidTargets.values()]
      .filter((pyramidTarget) => (
        pyramidTarget.width > target.width
        && pyramidTarget.height > target.height
      ))
      .sort((left, right) => right.width - left.width || right.height - left.height)[0]
    let highResolutionSeed = edgeRefinedPaintState
    const semanticSeed = beam
      .filter((state) => state.selectedAssets.length > 0)
      .sort((left, right) => left.candidate.totalLoss - right.candidate.totalLoss
        || left.candidate.key.localeCompare(right.candidate.key))[0]
    if (semanticSeed) {
      const hybridState = paintWithNativeTiles(
        semanticSeed,
        paintBrush,
        target,
        maxLayers,
        surfaceMask,
        namedColors,
        evaluated,
        options.onProgress,
        {
          lane: 'hybrid', inputSha256, assetPackManifestSha256,
          resolution, sourceWidth, sourceHeight, layerBudget: maxLayers,
          resumeCheckpoint, onCheckpoint: options.onCheckpoint,
          emblemAssets: emblemAssetMap,
        },
      )
      const hybridSeamValidation = validateNativeTileSeams(
        hybridState.paintPlacements,
        target.width,
        target.height,
      )
      if (hybridSeamValidation.metrics.some((metric) => metric.backgroundLeakPixels > 0)) {
        throw new Error('混合原生块候选未通过 96/230/512 高分辨率覆盖门禁')
      }
      finalists.push(hybridState)
      highResolutionSeed = hybridState
    }
    // Spend a budget-scaled number of passes on scored native shapes before
    // the final high-resolution block repair. This is deliberately a search
    // sub-phase rather than a product layer cap: every pass is bounded by the
    // user's remaining instance budget and stops at the first non-improvement.
    const requestedShapePasses = hasSemanticAlternative
      ? Math.min(
          maxLayers - highResolutionSeed.selectedAssets.length,
          Math.max(1, Math.ceil(Math.log2(maxLayers + 1) / 3)),
        )
      : 0
    const evaluatedBeforeShapeRefinement = evaluated.value
    const shapeSeedAssetCount = highResolutionSeed.selectedAssets.length
    let completedShapePasses = 0
    while (completedShapePasses < requestedShapePasses) {
      const refined = refinePaintedStateWithNativeShape(
        highResolutionSeed,
        emblems,
        shapeDescriptors,
        target,
        maxLayers,
        surfaceMask,
        namedColors,
        evaluated,
        shapeCandidateCount,
        options.onProgress,
      )
      completedShapePasses += 1
      if (refined === highResolutionSeed) break
      highResolutionSeed = refined
    }
    const acceptedShapeAssets = highResolutionSeed.selectedAssets.slice(shapeSeedAssetCount)
    nativeShapeRefinement = {
      requestedPasses: requestedShapePasses,
      completedPasses: completedShapePasses,
      acceptedLayers: acceptedShapeAssets.length,
      evaluatedCandidates: evaluated.value - evaluatedBeforeShapeRefinement,
      primitiveTextureNames: MIXED_NATIVE_PRIMITIVE_TEXTURES
        .filter((name) => emblemAssetMap.has(name)),
      acceptedTextureNames: acceptedShapeAssets.map((item) => item.name),
      terminationReason: requestedShapePasses === 0
        ? 'not_applicable'
        : highResolutionSeed.selectedAssets.length >= maxLayers
          ? 'layer_budget'
          : acceptedShapeAssets.length < requestedShapePasses
            ? 'no_improvement'
            : 'pass_budget',
    }
    if (acceptedShapeAssets.length > 0) finalists.push(highResolutionSeed)
    const availableHighResolutionSlots = maxLayers - highResolutionSeed.selectedAssets.length
    const evaluatedBeforeHighResolutionRepair = evaluated.value
    const highResolutionPaintState = highResolutionTarget
      ? refinePaintedStateAtHighResolution(
          highResolutionSeed,
          paintBrush,
          emblemTextureMap,
          target,
          highResolutionTarget,
          maxLayers,
          surfaceMask,
          namedColors,
          evaluated,
          options.onProgress,
        )
      : highResolutionSeed
    const acceptedHighResolutionLayers = highResolutionPaintState.selectedAssets.length
      - highResolutionSeed.selectedAssets.length
    highResolutionEdgeRepair = {
      resolution: highResolutionTarget?.width ?? null,
      availableSlots: availableHighResolutionSlots,
      acceptedLayers: acceptedHighResolutionLayers,
      evaluatedCandidates: evaluated.value - evaluatedBeforeHighResolutionRepair,
      terminationReason: !highResolutionTarget
        ? 'not_applicable'
        : availableHighResolutionSlots === 0
          || acceptedHighResolutionLayers === availableHighResolutionSlots
          ? 'layer_budget'
          : 'no_improvement',
    }
    if (highResolutionPaintState !== highResolutionSeed) finalists.push(highResolutionPaintState)
  }
  const candidateMultiscaleMetrics = new Map<SearchState, MultiscaleFitMetric[]>()
  for (const state of finalists) {
    const metrics = pyramidResolutions.map((pyramidResolution) => {
      if (pyramidResolution === resolution) return {
        resolution: pyramidResolution,
        colorLoss: state.candidate.colorLoss,
        edgeLoss: state.candidate.edgeLoss,
        totalLoss: state.candidate.totalLoss,
      }
      const pyramidTarget = pyramidTargets.get(pyramidResolution)
        ?? resizeFitImage(image, pyramidResolution)
      const pyramidCandidate = score(
        state.candidate.coatOfArms,
        state.patternAsset.texture,
        emblemTextureMap,
        pyramidTarget,
        state.candidate.key,
        surfaceMask,
        namedColors,
      )
      return {
        resolution: pyramidResolution,
        colorLoss: pyramidCandidate.colorLoss,
        edgeLoss: pyramidCandidate.edgeLoss,
        totalLoss: pyramidCandidate.totalLoss,
      }
    })
    candidateMultiscaleMetrics.set(state, metrics)
  }
  const nonRegressingFinalists = nativePaintBaseline
    ? finalists.filter((state) => (
        state.candidate.totalLoss <= nativePaintBaseline!.candidate.totalLoss + 1e-12
        && state.candidate.edgeLoss <= nativePaintBaseline!.candidate.edgeLoss + 1e-12
      ))
    : finalists
  const winner = nonRegressingFinalists.sort((left, right) => left.candidate.totalLoss - right.candidate.totalLoss
    || (candidateMultiscaleMetrics.get(left)?.at(-1)?.edgeLoss ?? Number.POSITIVE_INFINITY)
      - (candidateMultiscaleMetrics.get(right)?.at(-1)?.edgeLoss ?? Number.POSITIVE_INFINITY)
    || left.candidate.key.localeCompare(right.candidate.key))[0]
  const best = winner.candidate
  const nativeCoatOfArms = encodeNativeDepthOrder(best.coatOfArms)
  const nativeRendered = renderCoatOfArms(
    nativeCoatOfArms,
    {
      pattern: winner.patternAsset.texture,
      coloredEmblems: emblemTextureMap,
      surfaceMask,
    },
    namedColors,
    target.width,
  )
  if (
    !nativeRendered
    || nativeRendered.pixels.length !== best.rendered.pixels.length
    || nativeRendered.pixels.some((value, index) => value !== best.rendered.pixels[index])
  ) throw new Error('CK3 原生 depth 编码没有保持拟合器的最终构图')
  const selectedEmblemAssets = winner.selectedAssets
  const logicalLayers = best.coatOfArms.coloredEmblems.length + best.coatOfArms.texturedEmblems.length
  const drawnInstances = best.coatOfArms.coloredEmblems.reduce(
    (total, emblem) => total + emblem.instances.length,
    0,
  )
  if (!emblems.length) terminationReason = 'no_emblems'
  else if (best.totalLoss <= 1e-12) terminationReason = 'exact_match'
  else if (selectedEmblemAssets.length >= maxLayers) terminationReason = 'layer_budget'
  else if (winner.reconstructionMode !== 'semantic-search' || semanticLayerBudget < maxLayers) {
    terminationReason = 'no_improvement'
  }
  const improvement = initialLoss <= 1e-12 ? 0 : Math.max(0, (initialLoss - best.totalLoss) / initialLoss)
  return {
    coatOfArms: nativeCoatOfArms,
    metrics: {
      colorLoss: best.colorLoss,
      edgeLoss: best.edgeLoss,
      totalLoss: best.totalLoss,
      relativeImprovement: improvement,
    },
    provenance: {
      algorithm: 'ck3-coa-browser-fit-v6-budget-exhaustive-edge',
      searchBackend: batchSearch.status === 'active'
        ? 'webgl2-batch+cpu-reference'
        : 'cpu-reference',
      batchSearch,
      scoringContract: 'alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1',
      rendererContract: 'cpu-rgba8-bilinear-clamp-pixel-center-native-clockwise-depth-descending-v3',
      randomSeed: null,
      surfaceMaskApplied: Boolean(surfaceMask),
      sourceWidth,
      sourceHeight,
      resolution,
      pyramidResolutions,
      evaluatedCandidates: evaluated.value,
      patternAssets: patterns.length,
      emblemAssets: emblems.length,
      layerBudget: maxLayers,
      logicalLayers,
      coloredEmblemBlocks: best.coatOfArms.coloredEmblems.length,
      drawnInstances,
      selectedLayers: drawnInstances,
      layerLosses: winner.layerLosses,
      reconstructionMode: winner.reconstructionMode,
      candidateLosses: finalists.map((state) => ({
        mode: state.reconstructionMode,
        layers: state.selectedAssets.length,
        totalLoss: state.candidate.totalLoss,
        edgeLoss: state.candidate.edgeLoss,
        textureNames: [...new Set(state.selectedAssets.map((item) => item.name))],
        multiscaleMetrics: candidateMultiscaleMetrics.get(state) ?? [],
        passesPrimaryNonRegression: !nativePaintBaseline || (
          state.candidate.totalLoss <= nativePaintBaseline.candidate.totalLoss + 1e-12
          && state.candidate.edgeLoss <= nativePaintBaseline.candidate.edgeLoss + 1e-12
        ),
      })),
      selectedMultiscaleMetrics: candidateMultiscaleMetrics.get(winner) ?? [],
      baselineEdgeRepair,
      highResolutionEdgeRepair,
      nativeShapeRefinement,
      terminationReason,
      selectedAssetSha256: [
        winner.patternAsset.assetSha256,
        ...selectedEmblemAssets.map((item) => item.assetSha256),
      ],
      nativeTileSeamValidation: validateNativeTileSeams(
        winner.paintPlacements,
        target.width,
        target.height,
      ),
      nativeTileSearch: {
        contract: 'resolution-bounded-quadtree-v2',
        searchWidth: target.width,
        searchHeight: target.height,
        maximumDepth: nativeTileMaximumDepth(target, maxLayers),
        pixelLeafCapacity: target.width * target.height,
        userBudgetAppliedWithoutClamp: maxLayers,
      },
    },
  }
}
