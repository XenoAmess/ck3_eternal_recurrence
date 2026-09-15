import type { CoatOfArms, CoatOfArmsInstance, ColoredEmblem } from './types'
import type { DecodedDds } from './dds'

export type Rgb = [number, number, number]
export type NamedColorMap = Record<string, Rgb>

export interface RenderedCoatOfArms {
  width: number
  height: number
  pixels: Uint8ClampedArray
}

export type EmblemTransformConvention =
  | 'scale-after-rotation'
  | 'rotation-after-scale'

export interface CoatOfArmsRenderOptions {
  /**
   * Kept explicit so native framebuffer diagnostics can compare the two
   * plausible affine orders without changing the production default.
   */
  emblemTransformConvention?: EmblemTransformConvention
  /** Diagnostic rotation polarity. CK3's native screen-space contract uses -1. */
  emblemRotationSign?: 1 | -1
}

interface RenderAssets {
  pattern?: DecodedDds
  coloredEmblems: Record<string, DecodedDds>
  texturedEmblems?: Record<string, DecodedDds>
  surfaceMask?: DecodedDds
}

const clamp = (value: number) => Math.min(1, Math.max(0, value))
const mix = (from: number, to: number, amount: number) => from + (to - from) * amount

function mixRgb(from: Rgb, to: Rgb, amount: number): Rgb {
  return [
    mix(from[0], to[0], amount),
    mix(from[1], to[1], amount),
    mix(from[2], to[2], amount),
  ]
}

function overlay(base: number, blend: number): number {
  return base < 0.5
    ? 2 * base * blend
    : 1 - 2 * (1 - base) * (1 - blend)
}

/** Exact translation of Clausewitz GetOverlay, including its legacy parameter flip. */
export function getOverlay(color: Rgb, overlayColor: Rgb, strength: number): Rgb {
  return [0, 1, 2].map((index) => mix(
    color[index],
    overlay(overlayColor[index], color[index]),
    strength,
  )) as Rgb
}

function hsvToRgb(hue: number, saturation: number, value: number): Rgb {
  const normalizedHue = ((hue % 1) + 1) % 1
  const sector = normalizedHue * 6
  const index = Math.floor(sector)
  const fraction = sector - index
  const p = value * (1 - saturation)
  const q = value * (1 - saturation * fraction)
  const t = value * (1 - saturation * (1 - fraction))
  return [
    [value, t, p], [q, value, p], [p, value, t],
    [p, q, value], [t, p, value], [value, p, q],
  ][index % 6] as Rgb
}

function colorComponents(expression: string): { model: string, values: number[] } | null {
  const match = expression.trim().toLowerCase().match(
    /^(rgb|hsv360|hsv)?\s*\{\s*([-+.\de]+)\s+([-+.\de]+)\s+([-+.\de]+)\s*\}$/,
  )
  if (!match) return null
  const values = match.slice(2).map(Number)
  return values.every(Number.isFinite) ? { model: match[1] || 'rgb', values } : null
}

export function resolveColor(expression: string, namedColors: NamedColorMap): Rgb | null {
  const normalized = expression.trim().replaceAll('"', '').toLowerCase()
  const named = namedColors[normalized]
  if (named) return [...named] as Rgb
  const parsed = colorComponents(normalized)
  if (!parsed) return null
  const [first, second, third] = parsed.values
  let rgb: Rgb
  if (parsed.model === 'hsv') rgb = hsvToRgb(first, second, third)
  else if (parsed.model === 'hsv360') rgb = hsvToRgb(first / 360, second / 100, third / 100)
  else {
    const divisor = parsed.values.some((value) => value > 1) ? 255 : 1
    rgb = [first / divisor, second / divisor, third / divisor]
  }
  return rgb.every((value) => value >= 0 && value <= 1) ? rgb : null
}

function pixel(texture: DecodedDds, x: number, y: number): [number, number, number, number] {
  const offset = (y * texture.width + x) * 4
  return [
    texture.pixels[offset] / 255,
    texture.pixels[offset + 1] / 255,
    texture.pixels[offset + 2] / 255,
    texture.pixels[offset + 3] / 255,
  ]
}

function sample(texture: DecodedDds, u: number, v: number): [number, number, number, number] {
  const wrappedU = ((u % 1) + 1) % 1
  const wrappedV = ((v % 1) + 1) % 1
  const x = wrappedU * texture.width - 0.5
  const y = wrappedV * texture.height - 0.5
  const x0 = Math.floor(x)
  const y0 = Math.floor(y)
  const tx = x - x0
  const ty = y - y0
  const at = (px: number, py: number) => pixel(
    texture,
    ((px % texture.width) + texture.width) % texture.width,
    ((py % texture.height) + texture.height) % texture.height,
  )
  const topLeft = at(x0, y0)
  const topRight = at(x0 + 1, y0)
  const bottomLeft = at(x0, y0 + 1)
  const bottomRight = at(x0 + 1, y0 + 1)
  return [0, 1, 2, 3].map((channel) => mix(
    mix(topLeft[channel], topRight[channel], tx),
    mix(bottomLeft[channel], bottomRight[channel], tx),
    ty,
  )) as [number, number, number, number]
}

function resolvedColors(values: [string, string, string], namedColors: NamedColorMap): [Rgb, Rgb, Rgb] {
  const fallback: Rgb = [0.435, 0.384, 0.329]
  return values.map((value) => resolveColor(value, namedColors) ?? fallback) as [Rgb, Rgb, Rgb]
}

export function shadePattern(mask: Rgb, colors: [Rgb, Rgb, Rgb]): Rgb {
  // The engine's FallbackColor binding is not published. Designer textures cover
  // their surface channels, so Color1 is the least surprising offline fallback.
  let result = colors[0]
  result = mixRgb(result, colors[0], mask[0])
  result = mixRgb(result, colors[1], mask[1])
  return mixRgb(result, colors[2], mask[2])
}

export function shadeColoredEmblem(mask: Rgb, colors: [Rgb, Rgb, Rgb]): Rgb {
  let result = mixRgb(colors[0], colors[1], mask[1])
  result = mixRgb(result, colors[2], mask[0])
  return getOverlay(result, [mask[2], mask[2], mask[2]], 1)
}

export function patternMaskAlpha(mask: Rgb, selected: number[]): number {
  if (!selected.length) return 1
  const isolated: Rgb = [
    clamp(mask[0] - mask[1] - mask[2]),
    clamp(mask[1] - mask[2]),
    mask[2],
  ]
  return clamp(isolated.reduce(
    (sum, value, index) => sum + (selected.includes(index + 1) ? value : 0),
    0,
  ))
}

function instanceUv(
  u: number,
  v: number,
  instance: CoatOfArmsInstance,
  options: CoatOfArmsRenderOptions,
): [number, number] | null {
  const width = Math.abs(instance.scale[0])
  const height = Math.abs(instance.scale[1])
  if (width < 1e-8 || height < 1e-8) return null
  const deltaX = (u - instance.position[0]) * 2
  const deltaY = -(v - instance.position[1]) * 2
  const radians = instance.rotation * (options.emblemRotationSign ?? -1) * Math.PI / 180
  const cosine = Math.cos(radians)
  const sine = Math.sin(radians)
  let sourceX: number
  let sourceY: number
  if ((options.emblemTransformConvention ?? 'scale-after-rotation') === 'rotation-after-scale') {
    const unrotatedX = cosine * deltaX + sine * deltaY
    const unrotatedY = -sine * deltaX + cosine * deltaY
    sourceX = unrotatedX / width
    sourceY = unrotatedY / height
  } else {
    const scaledX = deltaX / width
    const scaledY = deltaY / height
    sourceX = cosine * scaledX + sine * scaledY
    sourceY = -sine * scaledX + cosine * scaledY
  }
  if (Math.abs(sourceX) > 1 || Math.abs(sourceY) > 1) return null
  let localU = (sourceX + 1) / 2
  let localV = (1 - sourceY) / 2
  if (instance.scale[0] < 0) localU = 1 - localU
  if (instance.scale[1] < 0) localV = 1 - localV
  return [localU, localV]
}

function drawInstance(
  target: Uint8ClampedArray,
  width: number,
  height: number,
  pattern: DecodedDds,
  surfaceMask: DecodedDds | undefined,
  emblemTexture: DecodedDds,
  emblem: ColoredEmblem,
  instance: CoatOfArmsInstance,
  namedColors: NamedColorMap,
  options: CoatOfArmsRenderOptions = {},
) {
  const colors = resolvedColors(emblem.colors, namedColors)
  const radians = instance.rotation * Math.PI / 180
  const absoluteCosine = Math.abs(Math.cos(radians))
  const absoluteSine = Math.abs(Math.sin(radians))
  const scaleX = Math.abs(instance.scale[0])
  const scaleY = Math.abs(instance.scale[1])
  const rotationAfterScale = options.emblemTransformConvention === 'rotation-after-scale'
  const halfWidth = rotationAfterScale
    ? (scaleX * absoluteCosine + scaleY * absoluteSine) / 2
    : scaleX * (absoluteCosine + absoluteSine) / 2
  const halfHeight = rotationAfterScale
    ? (scaleX * absoluteSine + scaleY * absoluteCosine) / 2
    : scaleY * (absoluteCosine + absoluteSine) / 2
  const minimumX = Math.max(0, Math.floor((instance.position[0] - halfWidth) * width - 1))
  const maximumX = Math.min(width, Math.ceil((instance.position[0] + halfWidth) * width + 1))
  const minimumY = Math.max(0, Math.floor((instance.position[1] - halfHeight) * height - 1))
  const maximumY = Math.min(height, Math.ceil((instance.position[1] + halfHeight) * height + 1))
  for (let y = minimumY; y < maximumY; y += 1) {
    const v = (y + 0.5) / height
    for (let x = minimumX; x < maximumX; x += 1) {
      const u = (x + 0.5) / width
      const local = instanceUv(u, v, instance, options)
      if (!local) continue
      const emblemSample = sample(emblemTexture, local[0], local[1])
      let alpha = emblemSample[3]
      if (alpha <= 0) continue
      if (emblem.mask.length) {
        const patternSample = sample(pattern, u, v)
        alpha *= patternMaskAlpha(
          [patternSample[0], patternSample[1], patternSample[2]],
          emblem.mask,
        )
      }
      let color = shadeColoredEmblem(
        [emblemSample[0], emblemSample[1], emblemSample[2]],
        colors,
      )
      if (surfaceMask) {
        const detail = sample(surfaceMask, u, v)
        color = getOverlay(color, [detail[2], detail[2], detail[2]], 0.2)
        alpha *= detail[1] * 2
      }
      alpha = clamp(alpha)
      const offset = (y * width + x) * 4
      for (let channel = 0; channel < 3; channel += 1) {
        const destination = target[offset + channel] / 255
        target[offset + channel] = Math.round(clamp(
          color[channel] * alpha + destination * (1 - alpha),
        ) * 255)
      }
    }
  }
}

function drawTexturedEmblem(
  target: Uint8ClampedArray,
  width: number,
  height: number,
  surfaceMask: DecodedDds | undefined,
  texture: DecodedDds,
) {
  for (let y = 0; y < height; y += 1) {
    const v = (y + 0.5) / height
    for (let x = 0; x < width; x += 1) {
      const u = (x + 0.5) / width
      const textureSample = sample(texture, u, v)
      let color: Rgb = [textureSample[0], textureSample[1], textureSample[2]]
      let alpha = textureSample[3]
      if (surfaceMask) {
        const detail = sample(surfaceMask, u, v)
        color = getOverlay(color, [detail[2], detail[2], detail[2]], 0.2)
        alpha *= detail[1] * 2
      }
      alpha = clamp(alpha)
      if (alpha <= 0) continue
      const offset = (y * width + x) * 4
      for (let channel = 0; channel < 3; channel += 1) {
        const destination = target[offset + channel] / 255
        target[offset + channel] = Math.round(clamp(
          color[channel] * alpha + destination * (1 - alpha),
        ) * 255)
      }
    }
  }
}

export function renderColoredEmblemLayer(
  base: RenderedCoatOfArms,
  pattern: DecodedDds,
  surfaceMask: DecodedDds | undefined,
  emblemTexture: DecodedDds,
  emblem: ColoredEmblem,
  instance: CoatOfArmsInstance,
  namedColors: NamedColorMap,
): RenderedCoatOfArms {
  if (
    base.width < 1
    || base.height < 1
    || base.pixels.length !== base.width * base.height * 4
  ) throw new Error('增量纹章渲染的基础画布不合法')
  const pixels = new Uint8ClampedArray(base.pixels)
  drawInstance(
    pixels,
    base.width,
    base.height,
    pattern,
    surfaceMask,
    emblemTexture,
    emblem,
    instance,
    namedColors,
  )
  return { width: base.width, height: base.height, pixels }
}

export function renderCoatOfArms(
  coatOfArms: CoatOfArms,
  assets: RenderAssets,
  namedColors: NamedColorMap,
  size = 230,
  options: CoatOfArmsRenderOptions = {},
): RenderedCoatOfArms | null {
  if (!assets.pattern || size < 1 || !Number.isSafeInteger(size)) return null
  const result = new Uint8ClampedArray(size * size * 4)
  const colors = resolvedColors(coatOfArms.colors, namedColors)
  for (let y = 0; y < size; y += 1) {
    const v = (y + 0.5) / size
    for (let x = 0; x < size; x += 1) {
      const u = (x + 0.5) / size
      const patternSample = sample(assets.pattern, u, v)
      let color = shadePattern(
        [patternSample[0], patternSample[1], patternSample[2]],
        colors,
      )
      if (assets.surfaceMask) {
        const detail = sample(assets.surfaceMask, u, v)
        color = getOverlay(color, [detail[2], detail[2], detail[2]], 0.2)
      }
      const offset = (y * size + x) * 4
      result[offset] = Math.round(clamp(color[0]) * 255)
      result[offset + 1] = Math.round(clamp(color[1]) * 255)
      result[offset + 2] = Math.round(clamp(color[2]) * 255)
      result[offset + 3] = 255
    }
  }

  for (const emblem of coatOfArms.texturedEmblems) {
    const texture = assets.texturedEmblems?.[emblem.texture]
    if (texture) drawTexturedEmblem(result, size, size, assets.surfaceMask, texture)
  }

  let sourceOrder = 0
  const instances = coatOfArms.coloredEmblems.flatMap((emblem) =>
    emblem.instances.map((instance) => ({
      emblem,
      instance,
      order: sourceOrder++,
    })))
    .sort((left, right) => left.instance.depth - right.instance.depth || left.order - right.order)
  for (const { emblem, instance } of instances) {
    const texture = assets.coloredEmblems[emblem.texture]
    if (texture) drawInstance(
      result,
      size,
      size,
      assets.pattern,
      assets.surfaceMask,
      texture,
      emblem,
      instance,
      namedColors,
      options,
    )
  }
  return { width: size, height: size, pixels: result }
}

export function renderedCoatOfArmsToDataUrl(rendered: RenderedCoatOfArms): string {
  const canvas = document.createElement('canvas')
  canvas.width = rendered.width
  canvas.height = rendered.height
  const context = canvas.getContext('2d')
  if (!context) throw new Error('浏览器没有 Canvas 2D context')
  const image = context.createImageData(rendered.width, rendered.height)
  image.data.set(rendered.pixels)
  context.putImageData(image, 0, 0)
  return canvas.toDataURL('image/png')
}
