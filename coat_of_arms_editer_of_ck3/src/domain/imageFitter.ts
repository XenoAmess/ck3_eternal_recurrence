import type { DecodedDds } from './dds'
import { renderCoatOfArms, type RenderedCoatOfArms } from './renderer'
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
    algorithm: 'ck3-coa-browser-fit-v2-multilayer'
    searchBackend: 'cpu-reference'
    resolution: number
    evaluatedCandidates: number
    patternAssets: number
    emblemAssets: number
    layerBudget: number
    selectedLayers: number
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

type ByteRgb = [number, number, number]

const DEFAULT_RESOLUTION = 40

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value))
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
    const sourceY = clamp(Math.floor((y + 0.5) * image.height / size), 0, image.height - 1)
    for (let x = 0; x < size; x += 1) {
      const sourceX = clamp(Math.floor((x + 0.5) * image.width / size), 0, image.width - 1)
      const source = (sourceY * image.width + sourceX) * 4
      const target = (y * size + x) * 4
      const alpha = image.pixels[source + 3] / 255
      for (let channel = 0; channel < 3; channel += 1) {
        pixels[target + channel] = Math.round(
          image.pixels[source + channel] * alpha + 255 * (1 - alpha),
        )
      }
      pixels[target + 3] = 255
    }
  }
  return { width: size, height: size, pixels }
}

export function dominantColors(image: FitImage, count = 3): ByteRgb[] {
  validateImage(image)
  const buckets = new Map<number, { weight: number, sums: [number, number, number] }>()
  for (let offset = 0; offset < image.pixels.length; offset += 4) {
    const alpha = image.pixels[offset + 3] / 255
    const values = [0, 1, 2].map((channel) => Math.round(
      image.pixels[offset + channel] * alpha + 255 * (1 - alpha),
    )) as ByteRgb
    const key = ((values[0] >> 4) << 8) | ((values[1] >> 4) << 4) | (values[2] >> 4)
    const bucket = buckets.get(key) ?? { weight: 0, sums: [0, 0, 0] }
    bucket.weight += 1
    for (let channel = 0; channel < 3; channel += 1) bucket.sums[channel] += values[channel]
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
  const pixels = target.width * target.height
  for (let y = 0; y < target.height; y += 1) {
    for (let x = 0; x < target.width; x += 1) {
      const offset = (y * target.width + x) * 4
      for (let channel = 0; channel < 3; channel += 1) {
        const delta = (target.pixels[offset + channel] - rendered.pixels[offset + channel]) / 255
        color += delta * delta
      }
      if (x > 0) {
        const previous = offset - 4
        edge += Math.abs(
          (luminance(target.pixels, offset) - luminance(target.pixels, previous))
          - (luminance(rendered.pixels, offset) - luminance(rendered.pixels, previous)),
        ) / 255
      }
      if (y > 0) {
        const previous = offset - target.width * 4
        edge += Math.abs(
          (luminance(target.pixels, offset) - luminance(target.pixels, previous))
          - (luminance(rendered.pixels, offset) - luminance(rendered.pixels, previous)),
        ) / 255
      }
    }
  }
  const colorLoss = color / (pixels * 3)
  const edgeLoss = edge / (pixels * 2)
  return { colorLoss, edgeLoss, totalLoss: colorLoss * 0.78 + edgeLoss * 0.22 }
}

function score(
  coatOfArms: CoatOfArms,
  pattern: DecodedDds,
  emblems: Record<string, DecodedDds>,
  target: FitImage,
  key: string,
): ScoredCandidate {
  const rendered = renderCoatOfArms(coatOfArms, { pattern, coloredEmblems: emblems }, {}, target.width)
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
    result[index] = Math.sqrt([0, 1, 2].reduce((sum, channel) => {
      const delta = target.pixels[offset + channel] - rendered.pixels[offset + channel]
      return sum + delta * delta
    }, 0))
  }
  return result
}

function residualGeometry(
  target: FitImage,
  rendered: RenderedCoatOfArms,
): { position: [number, number], scale: number } {
  const weights = residualWeights(target, rendered)
  const maximumWeight = Math.max(...weights)
  if (maximumWeight < 1) return { position: [0.5, 0.5], scale: 0.5 }
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
  if (totalWeight === 0) return { position: [0.5, 0.5], scale: 0.5 }
  const extent = Math.max(
    (maximumX - minimumX + 1) / target.width,
    (maximumY - minimumY + 1) / target.height,
  )
  return {
    position: [weightedX / totalWeight / target.width, weightedY / totalWeight / target.height],
    scale: clamp(extent * 1.18, 0.1, 1.5),
  }
}

function residualColors(target: FitImage, rendered: RenderedCoatOfArms, count = 3): ByteRgb[] {
  const buckets = new Map<number, { weight: number, sums: [number, number, number] }>()
  for (let y = 0; y < target.height; y += 1) {
    for (let x = 0; x < target.width; x += 1) {
      const offset = (y * target.width + x) * 4
      const weight = [0, 1, 2].reduce((sum, channel) => {
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

export function fitImageToCoatOfArms(
  image: FitImage,
  patternCandidates: FitTextureCandidate[],
  emblemCandidates: FitTextureCandidate[],
  options: ImageFitOptions = {},
): ImageFitResult {
  validateImage(image)
  const resolution = options.resolution ?? DEFAULT_RESOLUTION
  const target = resizeFitImage(image, resolution)
  const patterns = [...patternCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxPatterns ?? 64)
  const emblems = [...emblemCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxEmblemCandidates ?? emblemCandidates.length)
  const maxLayers = clamp(Math.floor(options.maxLayers ?? 6), 0, 24)
  const refinementCandidates = clamp(Math.floor(options.refinementCandidates ?? 8), 1, 64)
  const minRelativeLayerImprovement = clamp(options.minRelativeLayerImprovement ?? 0.005, 0, 1)
  if (!patterns.length) throw new Error('素材包没有可用于拟合的 pattern')
  const palette = dominantColors(target)
  let evaluated = 0
  let bestBackground: ScoredCandidate | null = null
  let bestPatternAsset: FitTextureCandidate | null = null
  for (const pattern of patterns) {
    for (const colors of permutations(palette)) {
      const coatOfArms: CoatOfArms = {
        outerKey: 'coa', parent: '', pattern: pattern.name,
        colors: colors.map(expression) as [string, string, string],
        coloredEmblems: [], texturedEmblems: [],
      }
      const candidate = score(coatOfArms, pattern.texture, {}, target, `${pattern.name}\0${colors.flat().join(',')}`)
      evaluated += 1
      if (better(candidate, bestBackground)) {
        bestBackground = candidate
        bestPatternAsset = pattern
      }
    }
  }
  if (!bestBackground || !bestPatternAsset) throw new Error('无法生成背景候选')

  const initialLoss = bestBackground.totalLoss
  let best = bestBackground
  const selectedEmblemAssets: FitTextureCandidate[] = []
  const emblemTextures = Object.fromEntries(emblems.map((item) => [item.name, item.texture]))
  for (let layer = 0; layer < maxLayers && emblems.length && best.totalLoss > 1e-12; layer += 1) {
    const geometry = residualGeometry(target, best.rendered)
    const layerPalettes = permutations(residualColors(target, best.rendered))
    const coarse: { asset: FitTextureCandidate, candidate: ScoredCandidate }[] = []
    for (const emblem of emblems) {
      const colors = layerPalettes[0]
      const coatOfArms: CoatOfArms = {
        ...best.coatOfArms,
        coloredEmblems: [...best.coatOfArms.coloredEmblems, {
          texture: emblem.name,
          colors: colors.map(expression) as [string, string, string],
          mask: [],
          instances: [{
            position: [...geometry.position], scale: [geometry.scale, geometry.scale],
            rotation: 0, depth: layer + 1,
          }],
        }],
      }
      const key = `${best.key}\0L${layer}\0${emblem.name}\0coarse`
      const candidate = score(coatOfArms, bestPatternAsset.texture, emblemTextures, target, key)
      evaluated += 1
      coarse.push({ asset: emblem, candidate })
    }
    const shortlist = coarse
      .sort((left, right) => left.candidate.totalLoss - right.candidate.totalLoss
        || left.candidate.key.localeCompare(right.candidate.key))
      .slice(0, refinementCandidates)
    let layerBest: { asset: FitTextureCandidate, candidate: ScoredCandidate } | null = null
    const positions: [number, number][] = [geometry.position]
    if (Math.abs(geometry.position[0] - 0.5) > 0.04 || Math.abs(geometry.position[1] - 0.5) > 0.04) {
      positions.push([0.5, 0.5])
    }
    const scales = [geometry.scale * 0.78, geometry.scale, geometry.scale * 1.22]
      .map((value) => clamp(value, 0.08, 1.8))
    for (const { asset } of shortlist) {
      for (const colors of layerPalettes) {
        for (const position of positions) {
          for (const scaleValue of scales) {
            for (const rotation of [0, 45, 90, 135, 180, 225, 270, 315]) {
              for (const flip of [1, -1]) {
                const coatOfArms: CoatOfArms = {
                  ...best.coatOfArms,
                  coloredEmblems: [...best.coatOfArms.coloredEmblems, {
                    texture: asset.name,
                    colors: colors.map(expression) as [string, string, string],
                    mask: [],
                    instances: [{
                      position: [...position], scale: [scaleValue * flip, scaleValue],
                      rotation, depth: layer + 1,
                    }],
                  }],
                }
                const key = `${best.key}\0L${layer}\0${asset.name}\0${colors.flat().join(',')}\0${position.join(',')}\0${scaleValue}\0${rotation}\0${flip}`
                const candidate = score(coatOfArms, bestPatternAsset.texture, emblemTextures, target, key)
                evaluated += 1
                if (!layerBest || better(candidate, layerBest.candidate)) layerBest = { asset, candidate }
              }
            }
          }
        }
      }
    }
    if (!layerBest || layerBest.candidate.totalLoss >= best.totalLoss) break
    const relativeGain = (best.totalLoss - layerBest.candidate.totalLoss) / best.totalLoss
    if (relativeGain < minRelativeLayerImprovement) break
    best = layerBest.candidate
    selectedEmblemAssets.push(layerBest.asset)
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
      algorithm: 'ck3-coa-browser-fit-v2-multilayer',
      searchBackend: 'cpu-reference',
      resolution,
      evaluatedCandidates: evaluated,
      patternAssets: patterns.length,
      emblemAssets: emblems.length,
      layerBudget: maxLayers,
      selectedLayers: selectedEmblemAssets.length,
      selectedAssetSha256: [
        bestPatternAsset.assetSha256,
        ...selectedEmblemAssets.map((item) => item.assetSha256),
      ],
    },
  }
}
