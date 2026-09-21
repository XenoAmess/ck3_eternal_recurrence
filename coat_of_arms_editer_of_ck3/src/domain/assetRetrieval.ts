import { FIT_SHAPE_DESCRIPTOR_SIZE, type FitTextureShapeFeatures } from './shapeFeatures'

export const ASSET_RETRIEVAL_CONTRACT =
  'ck3-coa-asset-retrieval-sdf-hu-radial-orientation-topology-v2' as const
export const ASSET_RETRIEVAL_FINE_SHORTLIST = 128

export interface AssetRetrievalDescriptorV2 {
  grid: Float32Array
  signedDistanceField: Float32Array
  huMoments: Float64Array
  radialHistogram: Float64Array
  orientationHistogram: Float64Array
  symmetry: [number, number, number, number]
  topology: {
    components: number
    enclosedRegions: number
    fillRatio: number
  }
}

export interface AssetRetrievalMatch<T> {
  item: T
  name: string
  rotation: number
  flip: 1 | -1
  loss: number
  coarseLoss: number
}

const SIZE = FIT_SHAPE_DESCRIPTOR_SIZE
const CELL_COUNT = SIZE * SIZE
const ROTATIONS = Array.from({ length: 24 }, (_, index) => index * 15)
export const ASSET_RETRIEVAL_ROTATIONS = ROTATIONS as readonly number[]

function sampleGrid(grid: Float32Array, x: number, y: number): number {
  if (x < 0 || y < 0 || x > 1 || y > 1) return 0
  const sourceX = x * (SIZE - 1)
  const sourceY = y * (SIZE - 1)
  const x0 = Math.floor(sourceX)
  const y0 = Math.floor(sourceY)
  const x1 = Math.min(SIZE - 1, x0 + 1)
  const y1 = Math.min(SIZE - 1, y0 + 1)
  const tx = sourceX - x0
  const ty = sourceY - y0
  const at = (sampleX: number, sampleY: number) => grid[sampleY * SIZE + sampleX]
  return (
    at(x0, y0) * (1 - tx) * (1 - ty)
    + at(x1, y0) * tx * (1 - ty)
    + at(x0, y1) * (1 - tx) * ty
    + at(x1, y1) * tx * ty
  )
}

export function transformAssetRetrievalGrid(
  grid: Float32Array,
  rotation: number,
  flip: 1 | -1,
): Float32Array {
  if (grid.length !== CELL_COUNT) throw new Error('素材检索网格尺寸不匹配')
  const result = new Float32Array(CELL_COUNT)
  const radians = -rotation * Math.PI / 180
  const cosine = Math.cos(radians)
  const sine = Math.sin(radians)
  const rotatedSpan = Math.abs(cosine) + Math.abs(sine)
  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      const centeredX = ((x + 0.5) / SIZE - 0.5) * rotatedSpan
      const centeredY = ((y + 0.5) / SIZE - 0.5) * rotatedSpan
      let sourceX = cosine * centeredX + sine * centeredY + 0.5
      const sourceY = -sine * centeredX + cosine * centeredY + 0.5
      if (flip < 0) sourceX = 1 - sourceX
      result[y * SIZE + x] = sampleGrid(grid, sourceX, sourceY)
    }
  }
  return result
}

export function coarseMaskedAssetRetrievalLossV2(
  target: Float32Array,
  candidate: Float32Array,
  rotation: number,
  flip: 1 | -1,
  mask: Float32Array,
): number {
  if (target.length !== CELL_COUNT || candidate.length !== CELL_COUNT || mask.length !== CELL_COUNT) {
    throw new Error('素材检索粗排网格尺寸不匹配')
  }
  const radians = -rotation * Math.PI / 180
  const cosine = Math.cos(radians)
  const sine = Math.sin(radians)
  const rotatedSpan = Math.abs(cosine) + Math.abs(sine)
  let overlap = 0
  let targetEnergy = 0
  let candidateEnergy = 0
  let squaredError = 0
  let samples = 0
  for (let y = 1; y < SIZE; y += 3) {
    for (let x = 1; x < SIZE; x += 3) {
      const centeredX = ((x + 0.5) / SIZE - 0.5) * rotatedSpan
      const centeredY = ((y + 0.5) / SIZE - 0.5) * rotatedSpan
      let sourceX = cosine * centeredX + sine * centeredY + 0.5
      const sourceY = -sine * centeredX + cosine * centeredY + 0.5
      if (flip < 0) sourceX = 1 - sourceX
      const index = y * SIZE + x
      const targetValue = target[index]
      const candidateValue = sampleGrid(candidate, sourceX, sourceY) * mask[index]
      overlap += Math.min(targetValue, candidateValue)
      targetEnergy += targetValue
      candidateEnergy += candidateValue
      squaredError += (targetValue - candidateValue) ** 2
      samples += 1
    }
  }
  const diceLoss = targetEnergy + candidateEnergy > 1e-8
    ? 1 - 2 * overlap / (targetEnergy + candidateEnergy)
    : 1
  return diceLoss * 0.7 + squaredError / Math.max(1, samples) * 0.3
}

function binaryMask(grid: Float32Array): Uint8Array {
  const maximum = Math.max(...grid)
  const threshold = Math.max(0.035, maximum * 0.14)
  return Uint8Array.from(grid, (value) => value >= threshold ? 1 : 0)
}

function countComponents(mask: Uint8Array, foreground: 0 | 1): number {
  const visited = new Uint8Array(mask.length)
  const queue = new Int16Array(mask.length)
  let components = 0
  for (let start = 0; start < mask.length; start += 1) {
    if (visited[start] || mask[start] !== foreground) continue
    components += 1
    let first = 0
    let last = 0
    queue[last++] = start
    visited[start] = 1
    while (first < last) {
      const index = queue[first++]
      const x = index % SIZE
      const y = Math.floor(index / SIZE)
      const neighbours = [
        x > 0 ? index - 1 : -1,
        x + 1 < SIZE ? index + 1 : -1,
        y > 0 ? index - SIZE : -1,
        y + 1 < SIZE ? index + SIZE : -1,
      ]
      for (const neighbour of neighbours) {
        if (neighbour < 0 || visited[neighbour] || mask[neighbour] !== foreground) continue
        visited[neighbour] = 1
        queue[last++] = neighbour
      }
    }
  }
  return components
}

function enclosedRegionCount(mask: Uint8Array): number {
  const visited = new Uint8Array(mask.length)
  const queue = new Int16Array(mask.length)
  let enclosed = 0
  for (let start = 0; start < mask.length; start += 1) {
    if (visited[start] || mask[start]) continue
    let touchesBorder = false
    let first = 0
    let last = 0
    queue[last++] = start
    visited[start] = 1
    while (first < last) {
      const index = queue[first++]
      const x = index % SIZE
      const y = Math.floor(index / SIZE)
      if (x === 0 || y === 0 || x === SIZE - 1 || y === SIZE - 1) touchesBorder = true
      const neighbours = [
        x > 0 ? index - 1 : -1,
        x + 1 < SIZE ? index + 1 : -1,
        y > 0 ? index - SIZE : -1,
        y + 1 < SIZE ? index + SIZE : -1,
      ]
      for (const neighbour of neighbours) {
        if (neighbour < 0 || visited[neighbour] || mask[neighbour]) continue
        visited[neighbour] = 1
        queue[last++] = neighbour
      }
    }
    if (!touchesBorder) enclosed += 1
  }
  return enclosed
}

function distanceField(mask: Uint8Array, expected: 0 | 1): Float64Array {
  const maximum = SIZE * 2
  const distance = new Float64Array(mask.length)
  for (let index = 0; index < mask.length; index += 1) {
    distance[index] = mask[index] === expected ? 0 : maximum
  }
  const relax = (index: number, candidate: number) => {
    if (candidate < distance[index]) distance[index] = candidate
  }
  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      const index = y * SIZE + x
      if (x > 0) relax(index, distance[index - 1] + 1)
      if (y > 0) relax(index, distance[index - SIZE] + 1)
      if (x > 0 && y > 0) relax(index, distance[index - SIZE - 1] + Math.SQRT2)
      if (x + 1 < SIZE && y > 0) relax(index, distance[index - SIZE + 1] + Math.SQRT2)
    }
  }
  for (let y = SIZE - 1; y >= 0; y -= 1) {
    for (let x = SIZE - 1; x >= 0; x -= 1) {
      const index = y * SIZE + x
      if (x + 1 < SIZE) relax(index, distance[index + 1] + 1)
      if (y + 1 < SIZE) relax(index, distance[index + SIZE] + 1)
      if (x + 1 < SIZE && y + 1 < SIZE) relax(index, distance[index + SIZE + 1] + Math.SQRT2)
      if (x > 0 && y + 1 < SIZE) relax(index, distance[index + SIZE - 1] + Math.SQRT2)
    }
  }
  return distance
}

function signedDistanceField(mask: Uint8Array): Float32Array {
  const toForeground = distanceField(mask, 1)
  const toBackground = distanceField(mask, 0)
  return Float32Array.from(mask, (value, index) => (
    (value ? toBackground[index] : -toForeground[index]) / SIZE
  ))
}

function huMoments(grid: Float32Array): Float64Array {
  let mass = 0
  let centerX = 0
  let centerY = 0
  for (let index = 0; index < grid.length; index += 1) {
    const weight = grid[index]
    mass += weight
    centerX += (index % SIZE) * weight
    centerY += Math.floor(index / SIZE) * weight
  }
  if (mass <= 1e-12) return new Float64Array(7)
  centerX /= mass
  centerY /= mass
  const eta = (p: number, q: number) => {
    let moment = 0
    for (let index = 0; index < grid.length; index += 1) {
      moment += ((index % SIZE) - centerX) ** p
        * (Math.floor(index / SIZE) - centerY) ** q
        * grid[index]
    }
    return moment / mass ** (1 + (p + q) / 2)
  }
  const n20 = eta(2, 0)
  const n02 = eta(0, 2)
  const n11 = eta(1, 1)
  const n30 = eta(3, 0)
  const n12 = eta(1, 2)
  const n21 = eta(2, 1)
  const n03 = eta(0, 3)
  const values = [
    n20 + n02,
    (n20 - n02) ** 2 + 4 * n11 ** 2,
    (n30 - 3 * n12) ** 2 + (3 * n21 - n03) ** 2,
    (n30 + n12) ** 2 + (n21 + n03) ** 2,
    (n30 - 3 * n12) * (n30 + n12) * ((n30 + n12) ** 2 - 3 * (n21 + n03) ** 2)
      + (3 * n21 - n03) * (n21 + n03) * (3 * (n30 + n12) ** 2 - (n21 + n03) ** 2),
    (n20 - n02) * ((n30 + n12) ** 2 - (n21 + n03) ** 2)
      + 4 * n11 * (n30 + n12) * (n21 + n03),
    (3 * n21 - n03) * (n30 + n12) * ((n30 + n12) ** 2 - 3 * (n21 + n03) ** 2)
      - (n30 - 3 * n12) * (n21 + n03) * (3 * (n30 + n12) ** 2 - (n21 + n03) ** 2),
  ]
  return Float64Array.from(values, (value) => (
    value === 0 ? 0 : Math.sign(value) * Math.log10(1 + Math.abs(value))
  ))
}

function normalizedHistogram(values: Float64Array): Float64Array {
  const sum = values.reduce((total, value) => total + value, 0)
  return sum > 1e-12 ? Float64Array.from(values, (value) => value / sum) : values
}

function radialHistogram(grid: Float32Array): Float64Array {
  const bins = new Float64Array(8)
  const center = (SIZE - 1) / 2
  const maximum = Math.hypot(center, center)
  for (let index = 0; index < grid.length; index += 1) {
    const radius = Math.hypot(index % SIZE - center, Math.floor(index / SIZE) - center) / maximum
    bins[Math.min(bins.length - 1, Math.floor(radius * bins.length))] += grid[index]
  }
  return normalizedHistogram(bins)
}

function orientationHistogram(grid: Float32Array): Float64Array {
  const bins = new Float64Array(8)
  for (let y = 1; y + 1 < SIZE; y += 1) {
    for (let x = 1; x + 1 < SIZE; x += 1) {
      const horizontal = grid[y * SIZE + x + 1] - grid[y * SIZE + x - 1]
      const vertical = grid[(y + 1) * SIZE + x] - grid[(y - 1) * SIZE + x]
      const magnitude = Math.hypot(horizontal, vertical)
      if (magnitude <= 1e-6) continue
      const angle = (Math.atan2(vertical, horizontal) + Math.PI) / (Math.PI * 2)
      bins[Math.min(bins.length - 1, Math.floor(angle * bins.length))] += magnitude
    }
  }
  return normalizedHistogram(bins)
}

function symmetry(grid: Float32Array): [number, number, number, number] {
  let horizontal = 0
  let vertical = 0
  let diagonal = 0
  let antiDiagonal = 0
  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      const value = grid[y * SIZE + x]
      horizontal += Math.abs(value - grid[y * SIZE + (SIZE - 1 - x)])
      vertical += Math.abs(value - grid[(SIZE - 1 - y) * SIZE + x])
      diagonal += Math.abs(value - grid[x * SIZE + y])
      antiDiagonal += Math.abs(value - grid[(SIZE - 1 - x) * SIZE + (SIZE - 1 - y)])
    }
  }
  return [horizontal, vertical, diagonal, antiDiagonal].map((value) => value / CELL_COUNT) as [number, number, number, number]
}

export function computeAssetRetrievalDescriptorV2(
  source: Pick<FitTextureShapeFeatures, 'descriptor'> | Float32Array,
): AssetRetrievalDescriptorV2 {
  const grid = source instanceof Float32Array ? source : source.descriptor
  if (grid.length !== CELL_COUNT || grid.some((value) => !Number.isFinite(value) || value < 0)) {
    throw new Error('素材检索描述符包含非法值')
  }
  const copy = Float32Array.from(grid)
  const mask = binaryMask(copy)
  return {
    grid: copy,
    signedDistanceField: signedDistanceField(mask),
    huMoments: huMoments(copy),
    radialHistogram: radialHistogram(copy),
    orientationHistogram: orientationHistogram(copy),
    symmetry: symmetry(copy),
    topology: {
      components: countComponents(mask, 1),
      enclosedRegions: enclosedRegionCount(mask),
      fillRatio: mask.reduce((sum, value) => sum + value, 0) / mask.length,
    },
  }
}

function vectorDistance(left: Float64Array | readonly number[], right: Float64Array | readonly number[]): number {
  let total = 0
  for (let index = 0; index < left.length; index += 1) total += Math.abs(left[index] - right[index])
  return total / Math.max(1, left.length)
}

function cyclicHistogramDistance(left: Float64Array, right: Float64Array): number {
  let best = Number.POSITIVE_INFINITY
  for (let shift = 0; shift < left.length; shift += 1) {
    let loss = 0
    for (let index = 0; index < left.length; index += 1) {
      loss += Math.abs(left[index] - right[(index + shift) % right.length])
    }
    best = Math.min(best, loss / left.length)
  }
  return best
}

function normalizedCountLoss(left: number, right: number): number {
  return Math.min(1, Math.abs(left - right) / Math.max(1, left, right))
}

function invariantDistance(left: AssetRetrievalDescriptorV2, right: AssetRetrievalDescriptorV2): number {
  const symmetryLeft = [...left.symmetry].sort((a, b) => a - b)
  const symmetryRight = [...right.symmetry].sort((a, b) => a - b)
  return (
    vectorDistance(left.huMoments, right.huMoments) * 0.30
    + vectorDistance(left.radialHistogram, right.radialHistogram) * 0.25
    + cyclicHistogramDistance(left.orientationHistogram, right.orientationHistogram) * 0.15
    + vectorDistance(symmetryLeft, symmetryRight) * 0.10
    + normalizedCountLoss(left.topology.components, right.topology.components) * 0.08
    + normalizedCountLoss(left.topology.enclosedRegions, right.topology.enclosedRegions) * 0.07
    + Math.abs(left.topology.fillRatio - right.topology.fillRatio) * 0.05
  )
}

function coarseTransformedGridDistance(
  target: AssetRetrievalDescriptorV2,
  candidate: AssetRetrievalDescriptorV2,
): number {
  let best = Number.POSITIVE_INFINITY
  for (const rotation of ROTATIONS) {
    const radians = -rotation * Math.PI / 180
    const cosine = Math.cos(radians)
    const sine = Math.sin(radians)
    const rotatedSpan = Math.abs(cosine) + Math.abs(sine)
    for (const flip of [1, -1] as const) {
      let loss = 0
      let samples = 0
      for (let y = 1; y < SIZE; y += 3) {
        for (let x = 1; x < SIZE; x += 3) {
          const centeredX = ((x + 0.5) / SIZE - 0.5) * rotatedSpan
          const centeredY = ((y + 0.5) / SIZE - 0.5) * rotatedSpan
          let sourceX = cosine * centeredX + sine * centeredY + 0.5
          const sourceY = -sine * centeredX + cosine * centeredY + 0.5
          if (flip < 0) sourceX = 1 - sourceX
          const delta = target.grid[y * SIZE + x] - sampleGrid(candidate.grid, sourceX, sourceY)
          loss += Math.abs(delta) * 0.65 + delta * delta * 0.35
          samples += 1
        }
      }
      best = Math.min(best, loss / Math.max(1, samples))
    }
  }
  return best
}

function transformedFineDistance(
  target: AssetRetrievalDescriptorV2,
  candidate: AssetRetrievalDescriptorV2,
  rotation: number,
  flip: 1 | -1,
): number {
  const radians = -rotation * Math.PI / 180
  const cosine = Math.cos(radians)
  const sine = Math.sin(radians)
  const rotatedSpan = Math.abs(cosine) + Math.abs(sine)
  let overlap = 0
  let targetEnergy = 0
  let candidateEnergy = 0
  let squaredError = 0
  let distanceLoss = 0
  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      const centeredX = ((x + 0.5) / SIZE - 0.5) * rotatedSpan
      const centeredY = ((y + 0.5) / SIZE - 0.5) * rotatedSpan
      let sourceX = cosine * centeredX + sine * centeredY + 0.5
      const sourceY = -sine * centeredX + cosine * centeredY + 0.5
      if (flip < 0) sourceX = 1 - sourceX
      const index = y * SIZE + x
      const candidateValue = sampleGrid(candidate.grid, sourceX, sourceY)
      const targetValue = target.grid[index]
      overlap += Math.min(targetValue, candidateValue)
      targetEnergy += targetValue
      candidateEnergy += candidateValue
      squaredError += (targetValue - candidateValue) ** 2
      distanceLoss += Math.abs(
        target.signedDistanceField[index]
        - sampleGrid(candidate.signedDistanceField, sourceX, sourceY),
      )
    }
  }
  const diceLoss = targetEnergy + candidateEnergy > 1e-8
    ? 1 - 2 * overlap / (targetEnergy + candidateEnergy)
    : 1
  const pixelLoss = diceLoss * 0.68 + squaredError / CELL_COUNT * 0.32
  return pixelLoss * 0.74 + distanceLoss / CELL_COUNT * 0.18 + invariantDistance(target, candidate) * 0.08
}

export function alignedAssetRetrievalLossV2(
  target: AssetRetrievalDescriptorV2,
  candidate: AssetRetrievalDescriptorV2,
): number {
  return transformedFineDistance(target, candidate, 0, 1)
}

export function bestAssetRetrievalTransformV2(
  target: AssetRetrievalDescriptorV2,
  candidate: AssetRetrievalDescriptorV2,
): { rotation: number, flip: 1 | -1, loss: number } {
  let best = { rotation: 0, flip: 1 as 1 | -1, loss: Number.POSITIVE_INFINITY }
  for (const rotation of ROTATIONS) {
    for (const flip of [1, -1] as const) {
      const loss = transformedFineDistance(target, candidate, rotation, flip)
      if (loss < best.loss - 1e-12 || (
        Math.abs(loss - best.loss) <= 1e-12
        && (rotation < best.rotation || (rotation === best.rotation && flip > best.flip))
      )) best = { rotation, flip, loss }
    }
  }
  return best
}

export function rankAssetRetrievalV2<T>(
  target: AssetRetrievalDescriptorV2,
  candidates: readonly { item: T, name: string, descriptor: AssetRetrievalDescriptorV2 }[],
  fineShortlist = ASSET_RETRIEVAL_FINE_SHORTLIST,
): AssetRetrievalMatch<T>[] {
  const coarse = candidates.map((candidate) => ({
    ...candidate,
    coarseLoss: (
      coarseTransformedGridDistance(target, candidate.descriptor) * 0.98
      + invariantDistance(target, candidate.descriptor) * 0.02
    ),
  })).sort((left, right) => left.coarseLoss - right.coarseLoss || left.name.localeCompare(right.name))
  const promoted = new Set(coarse.slice(0, Math.max(1, Math.min(fineShortlist, coarse.length))).map((item) => item.name))
  return coarse.map((candidate) => {
    if (!promoted.has(candidate.name)) return {
      item: candidate.item,
      name: candidate.name,
      rotation: 0,
      flip: 1 as const,
      loss: 1 + candidate.coarseLoss,
      coarseLoss: candidate.coarseLoss,
    }
    return {
      item: candidate.item,
      name: candidate.name,
      ...bestAssetRetrievalTransformV2(target, candidate.descriptor),
      coarseLoss: candidate.coarseLoss,
    }
  }).sort((left, right) => left.loss - right.loss || left.name.localeCompare(right.name))
}
