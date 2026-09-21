import type { FitTextureShapeFeatures } from './shapeFeatures'
import type { CoatOfArmsInstance } from './types'

export const FIT_CONTOUR_PROPOSAL_CONTRACT =
  'residual-roi-oriented-native-primitives-v1' as const

export type ContourPrimitiveFamily = 'block' | 'circle' | 'diamond' | 'wedge'
export type ContourRegionKind = 'fine-line' | 'directional' | 'curved' | 'compact' | 'region'

export interface ContourImagePlane {
  width: number
  height: number
  pixels: ArrayLike<number>
}

export interface ContourPrimitiveAsset<TIdentity = string> {
  /** Stable, caller-owned identity used for deterministic tie breaking. */
  id: string
  identity: TIdentity
  texture: string
  family: ContourPrimitiveFamily
  mask?: readonly number[]
  shapeFeatures?: Partial<Pick<
    FitTextureShapeFeatures,
    'contentSpan' | 'alphaEnergy' | 'contourEnergy'
  >>
}

export interface ContourProposalOptions {
  maximumRegions?: number
  maximumCandidates?: number
  maximumCandidatesPerRegion?: number
  minimumRegionPixels?: number
  /** Normalized premultiplied RGBA residual in the inclusive [0, 1] range. */
  residualThreshold?: number
  depth?: number
}

export interface ContourResidualAnalysisOptions {
  maximumRegions?: number
  minimumRegionPixels?: number
  residualThreshold?: number
}

export interface ContourRegionDiagnostic {
  id: string
  kind: ContourRegionKind
  pixelBounds: [number, number, number, number]
  /** Normalized max-exclusive bounds. */
  bounds: [number, number, number, number]
  center: [number, number]
  pixelCount: number
  residualMass: number
  meanResidual: number
  maximumResidual: number
  dominantAngleDegrees: number
  majorSpan: number
  minorSpan: number
  elongation: number
  fillRatio: number
  compactness: number
  orientationCoherence: number
  curvature: number
  targetColor: [number, number, number]
  score: number
}

export interface ContourResidualAnalysis {
  contract: typeof FIT_CONTOUR_PROPOSAL_CONTRACT
  width: number
  height: number
  residualThreshold: number
  meanResidual: number
  maximumResidual: number
  activePixels: number
  discardedRegions: number
  truncatedRegions: number
  regions: ContourRegionDiagnostic[]
}

export interface ContourProposal<TIdentity = string> {
  stableKey: string
  regionId: string
  regionKind: ContourRegionKind
  assetId: string
  assetIdentity: TIdentity
  texture: string
  family: ContourPrimitiveFamily
  mask: number[]
  instance: CoatOfArmsInstance
  targetColor: [number, number, number]
  regionScore: number
  assetSuitabilityLoss: number
}

export interface ContourProposalResult<TIdentity = string> {
  contract: typeof FIT_CONTOUR_PROPOSAL_CONTRACT
  analysis: ContourResidualAnalysis
  proposals: ContourProposal<TIdentity>[]
  diagnostics: {
    suppliedAssets: number
    eligibleAssets: number
    emittedCandidates: number
    truncatedCandidates: number
    maximumRegions: number
    maximumCandidates: number
    maximumCandidatesPerRegion: number
  }
}

interface ResidualPlane {
  values: Float64Array
  mean: number
  maximum: number
}

interface Component {
  pixels: number[]
  minimumX: number
  minimumY: number
  maximumX: number
  maximumY: number
}

const FAMILIES: readonly ContourPrimitiveFamily[] = ['block', 'circle', 'diamond', 'wedge']
const EPSILON = 1e-12

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value))
}

function finiteInteger(value: number | undefined, fallback: number, minimum: number): number {
  return Number.isFinite(value) ? Math.max(minimum, Math.floor(value!)) : fallback
}

function rounded(value: number, digits = 8): number {
  return Number(value.toFixed(digits))
}

function validateImagePair(target: ContourImagePlane, rendered: ContourImagePlane): void {
  if (!Number.isInteger(target.width) || !Number.isInteger(target.height) || target.width <= 0 || target.height <= 0) {
    throw new Error('轮廓候选目标图尺寸非法')
  }
  if (rendered.width !== target.width || rendered.height !== target.height) {
    throw new Error('轮廓候选目标图与渲染图尺寸不匹配')
  }
  const expected = target.width * target.height * 4
  if (target.pixels.length !== expected || rendered.pixels.length !== expected) {
    throw new Error('轮廓候选 RGBA 像素数量不匹配')
  }
}

function residualPlane(target: ContourImagePlane, rendered: ContourImagePlane): ResidualPlane {
  const values = new Float64Array(target.width * target.height)
  let sum = 0
  let maximum = 0
  for (let index = 0; index < values.length; index += 1) {
    const offset = index * 4
    const targetAlpha = clamp(Number(target.pixels[offset + 3]) / 255, 0, 1)
    const renderedAlpha = clamp(Number(rendered.pixels[offset + 3]) / 255, 0, 1)
    let colorSquared = 0
    for (let channel = 0; channel < 3; channel += 1) {
      const targetValue = clamp(Number(target.pixels[offset + channel]) / 255, 0, 1) * targetAlpha
      const renderedValue = clamp(Number(rendered.pixels[offset + channel]) / 255, 0, 1) * renderedAlpha
      colorSquared += (targetValue - renderedValue) ** 2
    }
    const colorResidual = Math.sqrt(colorSquared / 3)
    const alphaResidual = Math.abs(targetAlpha - renderedAlpha)
    const value = colorResidual * 0.88 + alphaResidual * 0.12
    values[index] = value
    sum += value
    maximum = Math.max(maximum, value)
  }
  return { values, mean: sum / values.length, maximum }
}

function extractComponents(
  residual: Float64Array,
  width: number,
  height: number,
  threshold: number,
): Component[] {
  const active = Uint8Array.from(residual, (value) => value >= threshold ? 1 : 0)
  const visited = new Uint8Array(active.length)
  const components: Component[] = []
  for (let seed = 0; seed < active.length; seed += 1) {
    if (!active[seed] || visited[seed]) continue
    const pixels: number[] = []
    const queue = [seed]
    visited[seed] = 1
    let minimumX = width
    let minimumY = height
    let maximumX = -1
    let maximumY = -1
    for (let cursor = 0; cursor < queue.length; cursor += 1) {
      const index = queue[cursor]
      pixels.push(index)
      const x = index % width
      const y = Math.floor(index / width)
      minimumX = Math.min(minimumX, x)
      minimumY = Math.min(minimumY, y)
      maximumX = Math.max(maximumX, x)
      maximumY = Math.max(maximumY, y)
      for (let deltaY = -1; deltaY <= 1; deltaY += 1) {
        for (let deltaX = -1; deltaX <= 1; deltaX += 1) {
          if (deltaX === 0 && deltaY === 0) continue
          const neighbourX = x + deltaX
          const neighbourY = y + deltaY
          if (neighbourX < 0 || neighbourY < 0 || neighbourX >= width || neighbourY >= height) continue
          const neighbour = neighbourY * width + neighbourX
          if (!active[neighbour] || visited[neighbour]) continue
          visited[neighbour] = 1
          queue.push(neighbour)
        }
      }
    }
    components.push({ pixels, minimumX, minimumY, maximumX, maximumY })
  }
  return components
}

function normalizeAngle(angle: number): number {
  let normalized = angle % 180
  if (normalized < 0) normalized += 180
  if (Math.abs(normalized - 180) <= 1e-8) normalized = 0
  return rounded(normalized, 6)
}

function regionDiagnostic(
  component: Component,
  ordinal: number,
  target: ContourImagePlane,
  residual: Float64Array,
): ContourRegionDiagnostic {
  const { width, height } = target
  let residualMass = 0
  let maximumResidual = 0
  let centerX = 0
  let centerY = 0
  let targetRed = 0
  let targetGreen = 0
  let targetBlue = 0
  for (const index of component.pixels) {
    const weight = residual[index]
    const x = (index % width + 0.5) / width
    const y = (Math.floor(index / width) + 0.5) / height
    const offset = index * 4
    residualMass += weight
    maximumResidual = Math.max(maximumResidual, weight)
    centerX += x * weight
    centerY += y * weight
    targetRed += Number(target.pixels[offset]) * weight
    targetGreen += Number(target.pixels[offset + 1]) * weight
    targetBlue += Number(target.pixels[offset + 2]) * weight
  }
  const divisor = Math.max(EPSILON, residualMass)
  centerX /= divisor
  centerY /= divisor

  let covarianceXX = 0
  let covarianceXY = 0
  let covarianceYY = 0
  for (const index of component.pixels) {
    const weight = residual[index]
    const deltaX = (index % width + 0.5) / width - centerX
    const deltaY = (Math.floor(index / width) + 0.5) / height - centerY
    covarianceXX += deltaX * deltaX * weight
    covarianceXY += deltaX * deltaY * weight
    covarianceYY += deltaY * deltaY * weight
  }
  covarianceXX /= divisor
  covarianceXY /= divisor
  covarianceYY /= divisor
  let angleRadians = 0.5 * Math.atan2(2 * covarianceXY, covarianceXX - covarianceYY)
  const trace = covarianceXX + covarianceYY
  const discriminant = Math.sqrt(Math.max(0, (covarianceXX - covarianceYY) ** 2 + 4 * covarianceXY ** 2))
  if (trace <= EPSILON || discriminant <= EPSILON) angleRadians = 0
  const axisX = Math.cos(angleRadians)
  const axisY = Math.sin(angleRadians)
  const normalX = -axisY
  const normalY = axisX
  let minimumMajor = Number.POSITIVE_INFINITY
  let maximumMajor = Number.NEGATIVE_INFINITY
  let minimumMinor = Number.POSITIVE_INFINITY
  let maximumMinor = Number.NEGATIVE_INFINITY
  for (const index of component.pixels) {
    const x = (index % width + 0.5) / width - centerX
    const y = (Math.floor(index / width) + 0.5) / height - centerY
    const major = x * axisX + y * axisY
    const minor = x * normalX + y * normalY
    minimumMajor = Math.min(minimumMajor, major)
    maximumMajor = Math.max(maximumMajor, major)
    minimumMinor = Math.min(minimumMinor, minor)
    maximumMinor = Math.max(maximumMinor, minor)
  }
  const majorPixelSpan = Math.abs(axisX) / width + Math.abs(axisY) / height
  const minorPixelSpan = Math.abs(normalX) / width + Math.abs(normalY) / height
  const majorSpan = Math.max(majorPixelSpan, maximumMajor - minimumMajor + majorPixelSpan)
  const minorSpan = Math.max(minorPixelSpan, maximumMinor - minimumMinor + minorPixelSpan)
  const elongation = majorSpan / Math.max(minorSpan, 1 / Math.max(width, height))

  const member = new Set(component.pixels)
  let perimeter = 0
  for (const index of component.pixels) {
    const x = index % width
    const y = Math.floor(index / width)
    if (x === 0 || !member.has(index - 1)) perimeter += 1
    if (x + 1 === width || !member.has(index + 1)) perimeter += 1
    if (y === 0 || !member.has(index - width)) perimeter += 1
    if (y + 1 === height || !member.has(index + width)) perimeter += 1
  }
  const boundingPixels = (component.maximumX - component.minimumX + 1)
    * (component.maximumY - component.minimumY + 1)
  const fillRatio = component.pixels.length / Math.max(1, boundingPixels)
  const compactness = clamp(
    4 * Math.PI * component.pixels.length / Math.max(1, perimeter * perimeter),
    0,
    1,
  )

  let orientationCosine = 0
  let orientationSine = 0
  let orientationMass = 0
  for (const index of component.pixels) {
    const x = index % width
    const y = Math.floor(index / width)
    const left = residual[y * width + Math.max(0, x - 1)]
    const right = residual[y * width + Math.min(width - 1, x + 1)]
    const above = residual[Math.max(0, y - 1) * width + x]
    const below = residual[Math.min(height - 1, y + 1) * width + x]
    const gradientX = right - left
    const gradientY = below - above
    const magnitude = Math.hypot(gradientX, gradientY)
    if (magnitude <= EPSILON) continue
    const gradientAngle = Math.atan2(gradientY, gradientX)
    orientationCosine += Math.cos(gradientAngle * 2) * magnitude
    orientationSine += Math.sin(gradientAngle * 2) * magnitude
    orientationMass += magnitude
  }
  const orientationCoherence = orientationMass > EPSILON
    ? clamp(Math.hypot(orientationCosine, orientationSine) / orientationMass, 0, 1)
    : 0
  const curvature = 1 - orientationCoherence

  const normalizedMinorSpan = minorSpan * Math.min(width, height)
  let kind: ContourRegionKind
  if (elongation >= 3.1 && normalizedMinorSpan <= 5.5) kind = 'fine-line'
  else if (elongation < 1.75 && fillRatio >= 0.58) kind = 'compact'
  else if (curvature >= 0.34 && fillRatio < 0.72) kind = 'curved'
  else if (elongation >= 1.5 || orientationCoherence >= 0.56) kind = 'directional'
  else kind = 'region'

  const detailMultiplier = kind === 'fine-line' ? 1.35 : kind === 'curved' ? 1.25 : 1
  const score = residualMass * detailMultiplier + maximumResidual * Math.sqrt(component.pixels.length) * 0.08
  return {
    id: `roi-${String(ordinal + 1).padStart(3, '0')}`,
    kind,
    pixelBounds: [component.minimumX, component.minimumY, component.maximumX + 1, component.maximumY + 1],
    bounds: [
      rounded(component.minimumX / width),
      rounded(component.minimumY / height),
      rounded((component.maximumX + 1) / width),
      rounded((component.maximumY + 1) / height),
    ],
    center: [rounded(centerX), rounded(centerY)],
    pixelCount: component.pixels.length,
    residualMass: rounded(residualMass),
    meanResidual: rounded(residualMass / component.pixels.length),
    maximumResidual: rounded(maximumResidual),
    dominantAngleDegrees: normalizeAngle(angleRadians * 180 / Math.PI),
    majorSpan: rounded(majorSpan),
    minorSpan: rounded(minorSpan),
    elongation: rounded(elongation),
    fillRatio: rounded(fillRatio),
    compactness: rounded(compactness),
    orientationCoherence: rounded(orientationCoherence),
    curvature: rounded(curvature),
    targetColor: [targetRed, targetGreen, targetBlue].map((value) => (
      Math.round(clamp(value / divisor, 0, 255))
    )) as [number, number, number],
    score: rounded(score),
  }
}

export function analyzeContourResidual(
  target: ContourImagePlane,
  rendered: ContourImagePlane,
  options: ContourResidualAnalysisOptions = {},
): ContourResidualAnalysis {
  validateImagePair(target, rendered)
  const residual = residualPlane(target, rendered)
  const maximumRegions = finiteInteger(options.maximumRegions, 12, 1)
  const minimumRegionPixels = finiteInteger(
    options.minimumRegionPixels,
    Math.max(2, Math.floor(target.width * target.height / 20_000)),
    1,
  )
  const requestedThreshold = options.residualThreshold
  if (requestedThreshold !== undefined && (!Number.isFinite(requestedThreshold) || requestedThreshold < 0 || requestedThreshold > 1)) {
    throw new Error('轮廓候选残差阈值必须位于 0 到 1')
  }
  const threshold = requestedThreshold ?? Math.max(1 / 255, residual.maximum * 0.18)
  const components = residual.maximum <= EPSILON
    ? []
    : extractComponents(residual.values, target.width, target.height, threshold)
  const eligible = components.filter((component) => component.pixels.length >= minimumRegionPixels)
  const regions = eligible
    .map((component, index) => regionDiagnostic(component, index, target, residual.values))
    .sort((left, right) => (
      right.score - left.score
      || right.maximumResidual - left.maximumResidual
      || left.pixelBounds[1] - right.pixelBounds[1]
      || left.pixelBounds[0] - right.pixelBounds[0]
      || left.pixelBounds[3] - right.pixelBounds[3]
      || left.pixelBounds[2] - right.pixelBounds[2]
    ))
    .slice(0, maximumRegions)
    .map((region, index) => ({ ...region, id: `roi-${String(index + 1).padStart(3, '0')}` }))
  return {
    contract: FIT_CONTOUR_PROPOSAL_CONTRACT,
    width: target.width,
    height: target.height,
    residualThreshold: rounded(threshold),
    meanResidual: rounded(residual.mean),
    maximumResidual: rounded(residual.maximum),
    activePixels: residual.values.reduce((sum, value) => sum + (value >= threshold ? 1 : 0), 0),
    discardedRegions: components.length - eligible.length,
    truncatedRegions: Math.max(0, eligible.length - maximumRegions),
    regions,
  }
}

function familyOrder(kind: ContourRegionKind): readonly ContourPrimitiveFamily[] {
  if (kind === 'compact') return ['block', 'circle', 'diamond', 'wedge']
  if (kind === 'curved') return ['block', 'wedge', 'circle', 'diamond']
  if (kind === 'fine-line' || kind === 'directional') return ['block', 'wedge', 'diamond', 'circle']
  return ['block', 'circle', 'diamond', 'wedge']
}

function assetSuitabilityLoss<TIdentity>(
  region: ContourRegionDiagnostic,
  asset: ContourPrimitiveAsset<TIdentity>,
): number {
  const span = asset.shapeFeatures?.contentSpan
  const spanX = Math.max(0.01, span?.[0] ?? 1)
  const spanY = Math.max(0.01, span?.[1] ?? 1)
  const assetAspect = Math.max(spanX, spanY) / Math.min(spanX, spanY)
  const regionAspect = Math.max(1, region.elongation)
  const aspectLoss = Math.abs(Math.log(regionAspect / assetAspect))
  const alphaEnergy = clamp(asset.shapeFeatures?.alphaEnergy ?? 0.65, 0, 1)
  const fillLoss = Math.abs(region.fillRatio - alphaEnergy)
  const contourEnergy = clamp((asset.shapeFeatures?.contourEnergy ?? 0.08) * 8, 0, 1)
  const contourLoss = Math.abs(region.curvature - contourEnergy)
  return rounded(aspectLoss * 0.52 + fillLoss * 0.28 + contourLoss * 0.20)
}

function proposalGeometry<TIdentity>(
  region: ContourRegionDiagnostic,
  asset: ContourPrimitiveAsset<TIdentity>,
  depth: number,
): CoatOfArmsInstance {
  const span = asset.shapeFeatures?.contentSpan
  const contentX = Math.max(0.02, span?.[0] ?? 1)
  const contentY = Math.max(0.02, span?.[1] ?? 1)
  const [minimumX, minimumY, maximumX, maximumY] = region.bounds
  const boundsWidth = maximumX - minimumX
  const boundsHeight = maximumY - minimumY
  let scaleX: number
  let scaleY: number
  let rotation: number
  if (asset.family === 'circle') {
    scaleX = boundsWidth / contentX
    scaleY = boundsHeight / contentY
    rotation = 0
  } else if (asset.family === 'diamond' && region.kind === 'compact') {
    scaleX = boundsWidth / contentX
    scaleY = boundsHeight / contentY
    rotation = 0
  } else {
    scaleX = region.majorSpan / contentX
    scaleY = region.minorSpan / contentY
    rotation = region.dominantAngleDegrees
  }
  const padding = asset.family === 'block' ? 1.04 : 1.08
  return {
    position: [region.center[0], region.center[1]],
    scale: [rounded(clamp(scaleX * padding, 0.012, 2.5)), rounded(clamp(scaleY * padding, 0.012, 2.5))],
    rotation: normalizeAngle(rotation),
    depth: rounded(depth),
  }
}

function proposalKey<TIdentity>(
  region: ContourRegionDiagnostic,
  asset: ContourPrimitiveAsset<TIdentity>,
  instance: CoatOfArmsInstance,
): string {
  return [
    region.id,
    asset.family,
    asset.id,
    instance.position.join(','),
    instance.scale.join(','),
    instance.rotation,
  ].join('|')
}

export function proposeContourCandidates<TIdentity = string>(
  target: ContourImagePlane,
  rendered: ContourImagePlane,
  assets: readonly ContourPrimitiveAsset<TIdentity>[],
  options: ContourProposalOptions = {},
): ContourProposalResult<TIdentity> {
  const maximumRegions = finiteInteger(options.maximumRegions, 12, 1)
  const maximumCandidates = finiteInteger(options.maximumCandidates, 32, 0)
  const maximumCandidatesPerRegion = finiteInteger(options.maximumCandidatesPerRegion, 4, 1)
  const depth = Number.isFinite(options.depth) ? Number(options.depth) : 1
  const analysis = analyzeContourResidual(target, rendered, {
    maximumRegions,
    minimumRegionPixels: options.minimumRegionPixels,
    residualThreshold: options.residualThreshold,
  })
  const eligibleAssets = assets
    .filter((asset) => (
      asset.id.length > 0
      && asset.texture.length > 0
      && FAMILIES.includes(asset.family)
    ))
    .sort((left, right) => left.id.localeCompare(right.id) || left.texture.localeCompare(right.texture))
    .filter((asset, index, sorted) => index === 0 || asset.id !== sorted[index - 1].id)
  if (!eligibleAssets.some((asset) => asset.family === 'block')) {
    throw new Error('轮廓候选需要至少一个合法 block brush')
  }

  const proposalsByRegion = analysis.regions.map((region) => {
    const proposals: ContourProposal<TIdentity>[] = []
    for (const family of familyOrder(region.kind)) {
      const familyAssets = eligibleAssets
        .filter((asset) => asset.family === family)
        .map((asset) => ({ asset, loss: assetSuitabilityLoss(region, asset) }))
        .sort((left, right) => left.loss - right.loss || left.asset.id.localeCompare(right.asset.id))
      const selected = familyAssets[0]
      if (!selected) continue
      const instance = proposalGeometry(region, selected.asset, depth)
      proposals.push({
        stableKey: proposalKey(region, selected.asset, instance),
        regionId: region.id,
        regionKind: region.kind,
        assetId: selected.asset.id,
        assetIdentity: selected.asset.identity,
        texture: selected.asset.texture,
        family,
        mask: [...(selected.asset.mask ?? [1])],
        instance,
        targetColor: [...region.targetColor],
        regionScore: region.score,
        assetSuitabilityLoss: selected.loss,
      })
      if (proposals.length >= maximumCandidatesPerRegion) break
    }
    return proposals
  })

  const proposals: ContourProposal<TIdentity>[] = []
  for (let rank = 0; rank < maximumCandidatesPerRegion && proposals.length < maximumCandidates; rank += 1) {
    for (const regionProposals of proposalsByRegion) {
      const proposal = regionProposals[rank]
      if (!proposal) continue
      proposals.push(proposal)
      if (proposals.length >= maximumCandidates) break
    }
  }
  const availableCandidates = proposalsByRegion.reduce((sum, items) => sum + items.length, 0)
  return {
    contract: FIT_CONTOUR_PROPOSAL_CONTRACT,
    analysis,
    proposals,
    diagnostics: {
      suppliedAssets: assets.length,
      eligibleAssets: eligibleAssets.length,
      emittedCandidates: proposals.length,
      truncatedCandidates: Math.max(0, availableCandidates - proposals.length),
      maximumRegions,
      maximumCandidates,
      maximumCandidatesPerRegion,
    },
  }
}
