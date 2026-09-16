import type { DecodedDds } from './dds'

export const FIT_SHAPE_DESCRIPTOR_SIZE = 18

export const FIT_SHAPE_SCALAR_FIELDS = [
  'content_min_x',
  'content_min_y',
  'content_max_x',
  'content_max_y',
  'content_center_x',
  'content_center_y',
  'content_span_x',
  'content_span_y',
  'alpha_energy',
  'red_energy',
  'green_energy',
  'blue_energy',
  'contour_energy',
] as const

export interface FitTextureShapeFeatures {
  /** Normalized, max-exclusive content bounds. */
  contentBounds: [number, number, number, number]
  contentCenter: [number, number]
  contentSpan: [number, number]
  /** Mean alpha coverage over the indexed texture. */
  alphaEnergy: number
  /** Mean premultiplied RGB energy over the indexed texture. */
  channelEnergy: [number, number, number]
  /** Mean right/down absolute intensity difference. */
  contourEnergy: number
  descriptor: Float32Array
}

/**
 * Deterministic shape features shared by v1 browser fallback and the v2
 * content-addressed feature sidecar. Keep this arithmetic in lockstep with
 * tools/build_web_asset_pack.py.
 */
export function computeFitTextureShapeFeatures(texture: DecodedDds): FitTextureShapeFeatures {
  const pixelCount = texture.width * texture.height
  const intensity = new Float64Array(pixelCount)
  let colorEnergy = 0
  let alphaEnergy = 0
  const channelSums: [number, number, number] = [0, 0, 0]
  for (let index = 0; index < pixelCount; index += 1) {
    const offset = index * 4
    const alpha = texture.pixels[offset + 3] / 255
    const red = texture.pixels[offset] / 255
    const green = texture.pixels[offset + 1] / 255
    const blue = texture.pixels[offset + 2] / 255
    const color = Math.max(red, green, blue)
    intensity[index] = alpha * color
    colorEnergy += intensity[index]
    alphaEnergy += alpha
    channelSums[0] += alpha * red
    channelSums[1] += alpha * green
    channelSums[2] += alpha * blue
  }
  if (colorEnergy < alphaEnergy * 0.05) {
    for (let index = 0; index < pixelCount; index += 1) {
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

  let contourSum = 0
  let contourSamples = 0
  for (let y = 0; y < texture.height; y += 1) {
    for (let x = 0; x < texture.width; x += 1) {
      const value = intensity[y * texture.width + x]
      if (x + 1 < texture.width) {
        contourSum += Math.abs(value - intensity[y * texture.width + x + 1])
        contourSamples += 1
      }
      if (y + 1 < texture.height) {
        contourSum += Math.abs(value - intensity[(y + 1) * texture.width + x])
        contourSamples += 1
      }
    }
  }

  const energyDivisor = Math.max(1, pixelCount)
  const common = {
    alphaEnergy: alphaEnergy / energyDivisor,
    channelEnergy: channelSums.map((value) => value / energyDivisor) as [number, number, number],
    contourEnergy: contourSamples > 0 ? contourSum / contourSamples : 0,
  }
  if (maximumX < minimumX || maximumY < minimumY) {
    return {
      ...common,
      contentBounds: [0, 0, 1, 1],
      contentCenter: [0.5, 0.5],
      contentSpan: [1, 1],
      descriptor: new Float32Array(FIT_SHAPE_DESCRIPTOR_SIZE * FIT_SHAPE_DESCRIPTOR_SIZE),
    }
  }

  const spanX = Math.max(1, maximumX - minimumX + 1)
  const spanY = Math.max(1, maximumY - minimumY + 1)
  const descriptor = new Float32Array(FIT_SHAPE_DESCRIPTOR_SIZE * FIT_SHAPE_DESCRIPTOR_SIZE)
  for (let y = 0; y < FIT_SHAPE_DESCRIPTOR_SIZE; y += 1) {
    const sourceY = Math.max(
      minimumY,
      Math.min(maximumY, Math.floor(minimumY + (y + 0.5) * spanY / FIT_SHAPE_DESCRIPTOR_SIZE)),
    )
    for (let x = 0; x < FIT_SHAPE_DESCRIPTOR_SIZE; x += 1) {
      const sourceX = Math.max(
        minimumX,
        Math.min(maximumX, Math.floor(minimumX + (x + 0.5) * spanX / FIT_SHAPE_DESCRIPTOR_SIZE)),
      )
      descriptor[y * FIT_SHAPE_DESCRIPTOR_SIZE + x] = intensity[sourceY * texture.width + sourceX]
    }
  }
  return {
    ...common,
    contentBounds: [
      minimumX / texture.width,
      minimumY / texture.height,
      (maximumX + 1) / texture.width,
      (maximumY + 1) / texture.height,
    ],
    contentCenter: [
      totalWeight > 0 ? weightedX / totalWeight / texture.width : 0.5,
      totalWeight > 0 ? weightedY / totalWeight / texture.height : 0.5,
    ],
    contentSpan: [spanX / texture.width, spanY / texture.height],
    descriptor,
  }
}
