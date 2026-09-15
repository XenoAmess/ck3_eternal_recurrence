import type { DecodedDds } from './dds'
import {
  renderCoatOfArms,
  renderColoredEmblemLayer,
  type NamedColorMap,
  type RenderedCoatOfArms,
} from './renderer'
import type { CoatOfArms } from './types'

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
  maxPatterns?: number
  maxEmblemCandidates?: number
  maxLayers?: number
  refinementCandidates?: number
  minRelativeLayerImprovement?: number
  surfaceMask?: DecodedDds
  namedColors?: NamedColorMap
  beamWidth?: number
  onProgress?: (progress: ImageFitProgress) => void
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

export interface ImageFitMetrics {
  colorLoss: number
  edgeLoss: number
  totalLoss: number
  relativeImprovement: number
}

export interface ImageFitResult {
  coatOfArms: CoatOfArms
  metrics: ImageFitMetrics
  provenance: {
    algorithm: 'ck3-coa-browser-fit-v3-shape-beam'
    searchBackend: 'cpu-reference'
    resolution: number
    evaluatedCandidates: number
    patternAssets: number
    emblemAssets: number
    layerBudget: number
    selectedLayers: number
    layerLosses: number[]
    reconstructionMode: 'semantic-search' | 'native-tile-paint'
    candidateLosses: { mode: 'semantic-search' | 'native-tile-paint', layers: number, totalLoss: number }[]
    terminationReason: 'layer_budget' | 'exact_match' | 'no_emblems' | 'no_improvement' | 'minimum_improvement'
    selectedAssetSha256: string[]
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
  if (!Number.isSafeInteger(size) || size < 8 || size > 128) throw new Error('搜索分辨率必须在 8..128')
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

function losses(target: FitImage, rendered: RenderedCoatOfArms): Pick<ScoredCandidate, 'colorLoss' | 'edgeLoss' | 'totalLoss'> {
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
  )
  if (!rendered) throw new Error('候选渲染失败')
  return { coatOfArms, rendered, ...losses(target, rendered), key }
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
  const radians = rotation * Math.PI / 180
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
  const radians = match.rotation * Math.PI / 180
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
    candidate: { coatOfArms, rendered, ...losses(target, rendered), key },
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

interface PaintTile {
  minimumX: number
  minimumY: number
  maximumX: number
  maximumY: number
  color: ByteRgb
  variance: number
  residual: number
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
  const maximumDepth = Math.min(6, Math.max(
    2,
    Math.ceil(Math.log(Math.max(4, layerBudget * 2)) / Math.log(4)),
  ))
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

function paintWithNativeTiles(
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
  const remaining = Math.max(0, maxLayers - state.selectedAssets.length)
  if (remaining === 0) return state
  const tiles = nativePaintTiles(target, state.candidate.rendered, remaining).slice(0, remaining)
  const shape = textureShapeDescriptor(brush.texture)
  const total = Math.max(1, tiles.length * 3)
  let completed = 0
  reportProgress(
    onProgress, 'paint', completed, total,
    state.selectedAssets.length + 1, maxLayers, evaluated.value,
  )
  for (const tile of tiles) {
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
    let best: LayerChoice | null = null
    for (const scaleFactor of [0.96, 1, 1.04]) {
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
      if (!best || better(choice.candidate, best.candidate)) best = choice
      if (shouldReportProgress(completed, total)) {
        reportProgress(
          onProgress, 'paint', completed, total,
          state.selectedAssets.length + 1, maxLayers, evaluated.value,
        )
      }
    }
    if (!best || best.candidate.totalLoss >= state.candidate.totalLoss - 1e-12) continue
    state = {
      candidate: best.candidate,
      patternAsset: state.patternAsset,
      selectedAssets: [...state.selectedAssets, brush],
      layerLosses: [...state.layerLosses, best.candidate.totalLoss],
      reconstructionMode: 'native-tile-paint',
    }
  }
  reportProgress(
    onProgress, 'paint', total, total,
    state.selectedAssets.length, maxLayers, evaluated.value,
  )
  return state
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
  const surfaceMask = options.surfaceMask
  const namedColors = options.namedColors ?? {}
  const patterns = [...patternCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxPatterns ?? 64)
  const emblems = [...emblemCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxEmblemCandidates ?? emblemCandidates.length)
  const maxLayers = normalizeLayerBudget(options.maxLayers)
  const shapeCandidateCount = clamp(Math.floor(options.refinementCandidates ?? 48), 8, 128)
  const beamWidth = clamp(Math.floor(options.beamWidth ?? 2), 1, 4)
  const minRelativeLayerImprovement = clamp(options.minRelativeLayerImprovement ?? 0, 0, 1)
  if (!patterns.length) throw new Error('素材包没有可用于拟合的 pattern')
  const palette = dominantColors(target)
  const backgroundPalettes = permutations(palette)
  const evaluated: EvaluationCounter = { value: 0 }
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
  const rankedBackgrounds = backgroundCandidates.sort((left, right) => (
    left.candidate.totalLoss - right.candidate.totalLoss
    || left.candidate.key.localeCompare(right.candidate.key)
  ))
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
  }))
  const shapeDescriptors = new Map<string, TextureShape>()
  const paintBrush = emblems.find((item) => item.name === 'ce_block_02.dds')
    ?? emblems.find((item) => item.name === 'ce_billet.dds')
    ?? emblems.find((item) => item.name === 'ce_circle.dds')
  let terminationReason: ImageFitResult['provenance']['terminationReason'] = 'layer_budget'
  const semanticLayerBudget = maxLayers >= 128 && paintBrush ? 0 : Math.min(maxLayers, 6)
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
      const localChoices = coarseChoices
        .sort((left, right) => left.choice.candidate.totalLoss - right.choice.candidate.totalLoss
          || left.choice.candidate.key.localeCompare(right.choice.candidate.key))
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
        .sort((left, right) => left.candidate.totalLoss - right.candidate.totalLoss
          || left.candidate.key.localeCompare(right.candidate.key))

      for (const choice of localChoices.slice(0, activeBeamWidth)) {
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
  if (paintBrush && bestSolidBackground) {
    const solidState: SearchState = {
      candidate: bestSolidBackground.candidate,
      patternAsset: bestSolidBackground.patternAsset,
      selectedAssets: [],
      layerLosses: [bestSolidBackground.candidate.totalLoss],
      reconstructionMode: 'native-tile-paint',
    }
    // Keep raster-like reconstruction independent from semantic emblems. A
    // numerically useful but visibly wrong large emblem is difficult to erase
    // and caused the old "pile of unrelated icons" failure mode.
    finalists.push(paintWithNativeTiles(
      solidState,
      paintBrush,
      target,
      maxLayers,
      surfaceMask,
      namedColors,
      evaluated,
      options.onProgress,
    ))
  }
  const winner = finalists.sort((left, right) => left.candidate.totalLoss - right.candidate.totalLoss
    || left.candidate.key.localeCompare(right.candidate.key))[0]
  const best = winner.candidate
  const selectedEmblemAssets = winner.selectedAssets
  if (!emblems.length) terminationReason = 'no_emblems'
  else if (best.totalLoss <= 1e-12) terminationReason = 'exact_match'
  else if (selectedEmblemAssets.length >= maxLayers) terminationReason = 'layer_budget'
  else if (winner.reconstructionMode === 'native-tile-paint' || semanticLayerBudget < maxLayers) {
    terminationReason = 'no_improvement'
  }
  const improvement = initialLoss <= 1e-12 ? 0 : Math.max(0, (initialLoss - best.totalLoss) / initialLoss)
  return {
    coatOfArms: best.coatOfArms,
    metrics: {
      colorLoss: best.colorLoss,
      edgeLoss: best.edgeLoss,
      totalLoss: best.totalLoss,
      relativeImprovement: improvement,
    },
    provenance: {
      algorithm: 'ck3-coa-browser-fit-v3-shape-beam',
      searchBackend: 'cpu-reference',
      resolution,
      evaluatedCandidates: evaluated.value,
      patternAssets: patterns.length,
      emblemAssets: emblems.length,
      layerBudget: maxLayers,
      selectedLayers: selectedEmblemAssets.length,
      layerLosses: winner.layerLosses,
      reconstructionMode: winner.reconstructionMode,
      candidateLosses: finalists.map((state) => ({
        mode: state.reconstructionMode,
        layers: state.selectedAssets.length,
        totalLoss: state.candidate.totalLoss,
      })),
      terminationReason,
      selectedAssetSha256: [
        winner.patternAsset.assetSha256,
        ...selectedEmblemAssets.map((item) => item.assetSha256),
      ],
    },
  }
}
