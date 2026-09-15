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
  maxEmblems?: number
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
    algorithm: 'ck3-coa-browser-fit-v1'
    searchBackend: 'cpu-reference'
    resolution: number
    evaluatedCandidates: number
    patternAssets: number
    emblemAssets: number
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

function sample(image: FitImage, x: number, y: number): ByteRgb {
  const sourceX = clamp(Math.floor((x + 0.5) * image.width / DEFAULT_RESOLUTION), 0, image.width - 1)
  const sourceY = clamp(Math.floor((y + 0.5) * image.height / DEFAULT_RESOLUTION), 0, image.height - 1)
  const offset = (sourceY * image.width + sourceX) * 4
  const alpha = image.pixels[offset + 3] / 255
  return [0, 1, 2].map((channel) => Math.round(
    image.pixels[offset + channel] * alpha + 255 * (1 - alpha),
  )) as ByteRgb
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

function foregroundGeometry(target: FitImage, background: ByteRgb): { position: [number, number], scale: number } {
  let minimumX = target.width
  let minimumY = target.height
  let maximumX = -1
  let maximumY = -1
  let weightedX = 0
  let weightedY = 0
  let totalWeight = 0
  for (let y = 0; y < target.height; y += 1) {
    for (let x = 0; x < target.width; x += 1) {
      const offset = (y * target.width + x) * 4
      const distance = Math.sqrt([0, 1, 2].reduce((sum, channel) => {
        const delta = target.pixels[offset + channel] - background[channel]
        return sum + delta * delta
      }, 0))
      if (distance < 42) continue
      minimumX = Math.min(minimumX, x)
      maximumX = Math.max(maximumX, x)
      minimumY = Math.min(minimumY, y)
      maximumY = Math.max(maximumY, y)
      weightedX += (x + 0.5) * distance
      weightedY += (y + 0.5) * distance
      totalWeight += distance
    }
  }
  if (totalWeight === 0) return { position: [0.5, 0.5], scale: 0.7 }
  const extent = Math.max(maximumX - minimumX + 1, maximumY - minimumY + 1) / target.width
  return {
    position: [weightedX / totalWeight / target.width, weightedY / totalWeight / target.height],
    scale: clamp(extent * 1.12, 0.2, 1.4),
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
  const patterns = [...patternCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxPatterns ?? 64)
  const emblems = [...emblemCandidates]
    .sort((left, right) => left.name.localeCompare(right.name))
    .slice(0, options.maxEmblems ?? 24)
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
  let bestEmblemAsset: FitTextureCandidate | null = null
  const geometry = foregroundGeometry(target, palette[0])
  const positions: [number, number][] = [geometry.position, [0.5, 0.5]]
  const scales = [geometry.scale * 0.82, geometry.scale, geometry.scale * 1.18]
    .map((value) => clamp(value, 0.15, 1.5))
  const emblemPalettes = [
    [palette[1], palette[2], palette[0]],
    [palette[2], palette[0], palette[1]],
  ]
  for (const emblem of emblems) {
    for (const colors of emblemPalettes) {
      for (const position of positions) {
        for (const scaleValue of scales) {
          for (const rotation of [0, 90, 180, 270]) {
            for (const flip of [1, -1]) {
              const coatOfArms: CoatOfArms = {
                ...bestBackground.coatOfArms,
                coloredEmblems: [{
                  texture: emblem.name,
                  colors: colors.map(expression) as [string, string, string],
                  mask: [],
                  instances: [{
                    position: [...position],
                    scale: [scaleValue * flip, scaleValue],
                    rotation,
                    depth: 1,
                  }],
                }],
              }
              const key = `${bestBackground.key}\0${emblem.name}\0${colors.flat().join(',')}\0${position.join(',')}\0${scaleValue}\0${rotation}\0${flip}`
              const candidate = score(
                coatOfArms, bestPatternAsset.texture, { [emblem.name]: emblem.texture }, target, key,
              )
              evaluated += 1
              if (better(candidate, best)) {
                best = candidate
                bestEmblemAsset = emblem
              }
            }
          }
        }
      }
    }
  }
  const improvement = initialLoss <= 1e-12 ? 0 : Math.max(0, (initialLoss - best.totalLoss) / initialLoss)
  if (improvement < 0.01) {
    best = bestBackground
    bestEmblemAsset = null
  }
  return {
    coatOfArms: best.coatOfArms,
    metrics: {
      colorLoss: best.colorLoss,
      edgeLoss: best.edgeLoss,
      totalLoss: best.totalLoss,
      relativeImprovement: improvement,
    },
    provenance: {
      algorithm: 'ck3-coa-browser-fit-v1',
      searchBackend: 'cpu-reference',
      resolution,
      evaluatedCandidates: evaluated,
      patternAssets: patterns.length,
      emblemAssets: emblems.length,
      selectedAssetSha256: [bestPatternAsset.assetSha256, bestEmblemAsset?.assetSha256]
        .filter((value): value is string => Boolean(value)),
    },
  }
}

