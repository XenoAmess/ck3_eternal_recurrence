export const PERCEPTUAL_FIT_SCORING_CONTRACT =
  'linear-rgb40-multiscale30-gradient20-bidirectional-edge7-structure3-shadow-v2' as const

export interface PerceptualImage {
  width: number
  height: number
  pixels: Uint8ClampedArray
}

export interface PerceptualFitMetricsV2 {
  linearColorLoss: number
  multiscaleColorLoss: number
  edgeGradientLoss: number
  bidirectionalEdgeDistanceLoss: number
  structureLoss: number
  totalLoss: number
  structure: {
    edgeMassLoss: number
    edgeCentroidLoss: number
    componentCountLoss: number
    enclosedRegionCountLoss: number
    targetComponents: number
    renderedComponents: number
    targetEnclosedRegions: number
    renderedEnclosedRegions: number
  }
}

const SQRT_TWO = Math.SQRT2

function validatePair(target: PerceptualImage, rendered: PerceptualImage): void {
  for (const image of [target, rendered]) {
    if (
      !Number.isSafeInteger(image.width)
      || !Number.isSafeInteger(image.height)
      || image.width < 2
      || image.height < 2
      || image.pixels.length !== image.width * image.height * 4
    ) throw new Error('感知评分图片尺寸或 RGBA 数据不合法')
  }
  if (target.width !== rendered.width || target.height !== rendered.height) {
    throw new Error('感知评分目标与候选尺寸不一致')
  }
}

function srgbToLinear(value: number): number {
  const normalized = value / 255
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4
}

function linearChannels(image: PerceptualImage): Float64Array {
  const channels = new Float64Array(image.width * image.height * 4)
  for (let offset = 0; offset < image.pixels.length; offset += 4) {
    channels[offset] = srgbToLinear(image.pixels[offset])
    channels[offset + 1] = srgbToLinear(image.pixels[offset + 1])
    channels[offset + 2] = srgbToLinear(image.pixels[offset + 2])
    channels[offset + 3] = image.pixels[offset + 3] / 255
  }
  return channels
}

function linearColorLoss(target: Float64Array, rendered: Float64Array): number {
  let loss = 0
  let weight = 0
  for (let offset = 0; offset < target.length; offset += 4) {
    const alpha = target[offset + 3]
    if (alpha <= 0) continue
    for (let channel = 0; channel < 3; channel += 1) {
      const delta = target[offset + channel] - rendered[offset + channel]
      loss += delta * delta * alpha
    }
    weight += alpha
  }
  if (weight <= 0) throw new Error('感知评分目标没有可见像素')
  return loss / (weight * 3)
}

function blockColorLoss(
  target: Float64Array,
  rendered: Float64Array,
  width: number,
  height: number,
  grid: number,
): number {
  let loss = 0
  let compared = 0
  for (let blockY = 0; blockY < grid; blockY += 1) {
    const minimumY = Math.floor(blockY * height / grid)
    const maximumY = Math.max(minimumY + 1, Math.floor((blockY + 1) * height / grid))
    for (let blockX = 0; blockX < grid; blockX += 1) {
      const minimumX = Math.floor(blockX * width / grid)
      const maximumX = Math.max(minimumX + 1, Math.floor((blockX + 1) * width / grid))
      const targetSums = [0, 0, 0]
      const renderedSums = [0, 0, 0]
      let weight = 0
      for (let y = minimumY; y < Math.min(maximumY, height); y += 1) {
        for (let x = minimumX; x < Math.min(maximumX, width); x += 1) {
          const offset = (y * width + x) * 4
          const alpha = target[offset + 3]
          if (alpha <= 0) continue
          weight += alpha
          for (let channel = 0; channel < 3; channel += 1) {
            targetSums[channel] += target[offset + channel] * alpha
            renderedSums[channel] += rendered[offset + channel] * alpha
          }
        }
      }
      if (weight <= 0) continue
      for (let channel = 0; channel < 3; channel += 1) {
        const delta = (targetSums[channel] - renderedSums[channel]) / weight
        loss += delta * delta
      }
      compared += 1
    }
  }
  return compared ? loss / (compared * 3) : 0
}

function luminanceMap(channels: Float64Array): Float64Array {
  const result = new Float64Array(channels.length / 4)
  for (let index = 0; index < result.length; index += 1) {
    const offset = index * 4
    result[index] = (
      channels[offset] * 0.2126
      + channels[offset + 1] * 0.7152
      + channels[offset + 2] * 0.0722
    ) * channels[offset + 3]
  }
  return result
}

function edgeMap(luminance: Float64Array, width: number, height: number): Float64Array {
  const result = new Float64Array(width * height)
  for (let y = 0; y < height; y += 1) {
    const previousY = Math.max(0, y - 1)
    const nextY = Math.min(height - 1, y + 1)
    for (let x = 0; x < width; x += 1) {
      const previousX = Math.max(0, x - 1)
      const nextX = Math.min(width - 1, x + 1)
      const horizontal = (
        luminance[y * width + nextX] - luminance[y * width + previousX]
      ) / Math.max(1, nextX - previousX)
      const vertical = (
        luminance[nextY * width + x] - luminance[previousY * width + x]
      ) / Math.max(1, nextY - previousY)
      result[y * width + x] = Math.min(1, Math.hypot(horizontal, vertical))
    }
  }
  return result
}

function edgeMask(edges: Float64Array): Uint8Array {
  const result = new Uint8Array(edges.length)
  for (let index = 0; index < edges.length; index += 1) {
    if (edges[index] >= 0.035) result[index] = 1
  }
  return result
}

function distanceTransform(mask: Uint8Array, width: number, height: number): Float64Array {
  const maximum = width + height
  const distance = new Float64Array(mask.length)
  for (let index = 0; index < mask.length; index += 1) distance[index] = mask[index] ? 0 : maximum
  const relax = (index: number, candidate: number) => {
    if (candidate < distance[index]) distance[index] = candidate
  }
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const index = y * width + x
      if (x > 0) relax(index, distance[index - 1] + 1)
      if (y > 0) relax(index, distance[index - width] + 1)
      if (x > 0 && y > 0) relax(index, distance[index - width - 1] + SQRT_TWO)
      if (x + 1 < width && y > 0) relax(index, distance[index - width + 1] + SQRT_TWO)
    }
  }
  for (let y = height - 1; y >= 0; y -= 1) {
    for (let x = width - 1; x >= 0; x -= 1) {
      const index = y * width + x
      if (x + 1 < width) relax(index, distance[index + 1] + 1)
      if (y + 1 < height) relax(index, distance[index + width] + 1)
      if (x + 1 < width && y + 1 < height) relax(index, distance[index + width + 1] + SQRT_TWO)
      if (x > 0 && y + 1 < height) relax(index, distance[index + width - 1] + SQRT_TWO)
    }
  }
  return distance
}

function directionalEdgeDistance(
  sourceEdges: Float64Array,
  sourceMask: Uint8Array,
  targetMask: Uint8Array,
  width: number,
  height: number,
): number {
  const sourceCount = sourceMask.reduce((sum, value) => sum + value, 0)
  const targetCount = targetMask.reduce((sum, value) => sum + value, 0)
  if (!sourceCount) return targetCount ? 1 : 0
  if (!targetCount) return 1
  const distances = distanceTransform(targetMask, width, height)
  const normalizer = Math.max(1, Math.hypot(width, height))
  let loss = 0
  let weight = 0
  for (let index = 0; index < sourceMask.length; index += 1) {
    if (!sourceMask[index]) continue
    const edgeWeight = Math.max(0.035, sourceEdges[index])
    loss += Math.min(1, distances[index] / normalizer) * edgeWeight
    weight += edgeWeight
  }
  return weight > 0 ? loss / weight : 0
}

function edgeMassAndCentroid(edges: Float64Array, width: number): { mass: number, x: number, y: number } {
  let mass = 0
  let xSum = 0
  let ySum = 0
  for (let index = 0; index < edges.length; index += 1) {
    const value = edges[index]
    mass += value
    xSum += (index % width + 0.5) * value
    ySum += (Math.floor(index / width) + 0.5) * value
  }
  return mass > 0
    ? { mass, x: xSum / mass, y: ySum / mass }
    : { mass: 0, x: 0, y: 0 }
}

function countComponents(mask: Uint8Array, width: number, height: number, foreground: boolean): number {
  const visited = new Uint8Array(mask.length)
  let components = 0
  const queue = new Int32Array(mask.length)
  const expected = foreground ? 1 : 0
  for (let start = 0; start < mask.length; start += 1) {
    if (visited[start] || mask[start] !== expected) continue
    components += 1
    let first = 0
    let last = 0
    queue[last++] = start
    visited[start] = 1
    while (first < last) {
      const index = queue[first++]
      const x = index % width
      const y = Math.floor(index / width)
      const neighbours = [
        x > 0 ? index - 1 : -1,
        x + 1 < width ? index + 1 : -1,
        y > 0 ? index - width : -1,
        y + 1 < height ? index + width : -1,
      ]
      for (const neighbour of neighbours) {
        if (neighbour < 0 || visited[neighbour] || mask[neighbour] !== expected) continue
        visited[neighbour] = 1
        queue[last++] = neighbour
      }
    }
  }
  return components
}

function countEnclosedRegions(mask: Uint8Array, width: number, height: number): number {
  const inverted = new Uint8Array(mask.length)
  for (let index = 0; index < mask.length; index += 1) inverted[index] = mask[index] ? 0 : 1
  const allBackgroundComponents = countComponents(inverted, width, height, true)
  const borderBackground = new Uint8Array(mask.length)
  for (let x = 0; x < width; x += 1) {
    borderBackground[x] = inverted[x]
    borderBackground[(height - 1) * width + x] = inverted[(height - 1) * width + x]
  }
  for (let y = 0; y < height; y += 1) {
    borderBackground[y * width] = inverted[y * width]
    borderBackground[y * width + width - 1] = inverted[y * width + width - 1]
  }
  const touchesBorder = borderBackground.some((value) => value > 0) ? 1 : 0
  return Math.max(0, allBackgroundComponents - touchesBorder)
}

function normalizedCountDifference(left: number, right: number): number {
  return Math.min(1, Math.abs(left - right) / Math.max(1, left, right))
}

export function measurePerceptualFitMetricsV2(
  targetImage: PerceptualImage,
  renderedImage: PerceptualImage,
): PerceptualFitMetricsV2 {
  validatePair(targetImage, renderedImage)
  const target = linearChannels(targetImage)
  const rendered = linearChannels(renderedImage)
  const color = linearColorLoss(target, rendered)
  const grids = [4, 8, 16].filter((grid) => grid <= Math.min(targetImage.width, targetImage.height))
  const multiscale = grids.reduce((sum, grid) => (
    sum + blockColorLoss(target, rendered, targetImage.width, targetImage.height, grid)
  ), 0) / Math.max(1, grids.length)
  const targetEdges = edgeMap(luminanceMap(target), targetImage.width, targetImage.height)
  const renderedEdges = edgeMap(luminanceMap(rendered), targetImage.width, targetImage.height)
  const targetMask = edgeMask(targetEdges)
  const renderedMask = edgeMask(renderedEdges)
  let edgeGradientLoss = 0
  for (let index = 0; index < targetEdges.length; index += 1) {
    edgeGradientLoss += Math.abs(targetEdges[index] - renderedEdges[index])
  }
  edgeGradientLoss /= targetEdges.length
  const edgeDistance = (
    directionalEdgeDistance(targetEdges, targetMask, renderedMask, targetImage.width, targetImage.height)
    + directionalEdgeDistance(renderedEdges, renderedMask, targetMask, targetImage.width, targetImage.height)
  ) / 2
  const targetMass = edgeMassAndCentroid(targetEdges, targetImage.width)
  const renderedMass = edgeMassAndCentroid(renderedEdges, targetImage.width)
  const edgeMassLoss = Math.min(
    1,
    Math.abs(targetMass.mass - renderedMass.mass) / Math.max(1e-12, targetMass.mass, renderedMass.mass),
  )
  const edgeCentroidLoss = targetMass.mass > 0 && renderedMass.mass > 0
    ? Math.min(1, Math.hypot(targetMass.x - renderedMass.x, targetMass.y - renderedMass.y)
      / Math.hypot(targetImage.width, targetImage.height))
    : targetMass.mass === renderedMass.mass ? 0 : 1
  const targetComponents = countComponents(targetMask, targetImage.width, targetImage.height, true)
  const renderedComponents = countComponents(renderedMask, targetImage.width, targetImage.height, true)
  const targetEnclosedRegions = countEnclosedRegions(targetMask, targetImage.width, targetImage.height)
  const renderedEnclosedRegions = countEnclosedRegions(renderedMask, targetImage.width, targetImage.height)
  const componentCountLoss = normalizedCountDifference(targetComponents, renderedComponents)
  const enclosedRegionCountLoss = normalizedCountDifference(targetEnclosedRegions, renderedEnclosedRegions)
  const structureLoss = (
    edgeMassLoss * 0.35
    + edgeCentroidLoss * 0.30
    + componentCountLoss * 0.20
    + enclosedRegionCountLoss * 0.15
  )
  return {
    linearColorLoss: color,
    multiscaleColorLoss: multiscale,
    edgeGradientLoss,
    bidirectionalEdgeDistanceLoss: edgeDistance,
    structureLoss,
    totalLoss: (
      color * 0.40
      + multiscale * 0.30
      + edgeGradientLoss * 0.20
      + edgeDistance * 0.07
      + structureLoss * 0.03
    ),
    structure: {
      edgeMassLoss,
      edgeCentroidLoss,
      componentCountLoss,
      enclosedRegionCountLoss,
      targetComponents,
      renderedComponents,
      targetEnclosedRegions,
      renderedEnclosedRegions,
    },
  }
}
