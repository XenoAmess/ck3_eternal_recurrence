export interface DecodedDds {
  width: number
  height: number
  fourCC: 'DXT1' | 'DXT5' | 'BGRA8'
  pixels: Uint8ClampedArray
}

function uint32(data: Uint8Array, offset: number): number {
  return new DataView(data.buffer, data.byteOffset, data.byteLength).getUint32(offset, true)
}

function rgb565(value: number): [number, number, number, number] {
  return [
    Math.round(((value >>> 11) & 0x1f) * 255 / 31),
    Math.round(((value >>> 5) & 0x3f) * 255 / 63),
    Math.round((value & 0x1f) * 255 / 31),
    255,
  ]
}

function mix(
  first: [number, number, number, number],
  second: [number, number, number, number],
  firstWeight: number,
  secondWeight: number,
  divisor: number,
): [number, number, number, number] {
  return [
    Math.round((first[0] * firstWeight + second[0] * secondWeight) / divisor),
    Math.round((first[1] * firstWeight + second[1] * secondWeight) / divisor),
    Math.round((first[2] * firstWeight + second[2] * secondWeight) / divisor),
    255,
  ]
}

function colorPalette(
  color0: number,
  color1: number,
  transparentMode: boolean,
): [number, number, number, number][] {
  const first = rgb565(color0)
  const second = rgb565(color1)
  if (transparentMode && color0 <= color1) {
    return [
      first,
      second,
      mix(first, second, 1, 1, 2),
      [0, 0, 0, 0],
    ]
  }
  return [
    first,
    second,
    mix(first, second, 2, 1, 3),
    mix(first, second, 1, 2, 3),
  ]
}

function alphaPalette(alpha0: number, alpha1: number): number[] {
  if (alpha0 > alpha1) {
    return [
      alpha0,
      alpha1,
      ...Array.from({ length: 6 }, (_, index) =>
        Math.round((alpha0 * (6 - index) + alpha1 * (index + 1)) / 7)),
    ]
  }
  return [
    alpha0,
    alpha1,
    ...Array.from({ length: 4 }, (_, index) =>
      Math.round((alpha0 * (4 - index) + alpha1 * (index + 1)) / 5)),
    0,
    255,
  ]
}

function writeBlock(
  data: Uint8Array,
  blockOffset: number,
  blockX: number,
  blockY: number,
  width: number,
  height: number,
  pixels: Uint8ClampedArray,
  fourCC: 'DXT1' | 'DXT5',
) {
  const colorOffset = fourCC === 'DXT5' ? blockOffset + 8 : blockOffset
  const color0 = data[colorOffset] | (data[colorOffset + 1] << 8)
  const color1 = data[colorOffset + 2] | (data[colorOffset + 3] << 8)
  const palette = colorPalette(color0, color1, fourCC === 'DXT1')
  const colorIndices = uint32(data, colorOffset + 4)
  const alphas = fourCC === 'DXT5'
    ? alphaPalette(data[blockOffset], data[blockOffset + 1])
    : null

  for (let index = 0; index < 16; index += 1) {
    const x = blockX * 4 + index % 4
    const y = blockY * 4 + Math.floor(index / 4)
    if (x >= width || y >= height) continue
    const color = palette[(colorIndices >>> (index * 2)) & 0x3]
    let alpha = color[3]
    if (alphas) {
      const alphaBit = index * 3
      const alphaByte = blockOffset + 2 + Math.floor(alphaBit / 8)
      const packed = data[alphaByte] | ((data[alphaByte + 1] ?? 0) << 8)
      alpha = alphas[(packed >>> (alphaBit % 8)) & 0x7]
    }
    const target = (y * width + x) * 4
    pixels[target] = color[0]
    pixels[target + 1] = color[1]
    pixels[target + 2] = color[2]
    pixels[target + 3] = alpha
  }
}

export function decodeDds(data: Uint8Array): DecodedDds {
  if (data.byteLength < 128 || String.fromCharCode(...data.subarray(0, 4)) !== 'DDS ') {
    throw new Error('不是 DDS 容器')
  }
  if (uint32(data, 4) !== 124) throw new Error('DDS header size 不是 124')
  const height = uint32(data, 12)
  const width = uint32(data, 16)
  if (width < 1 || height < 1 || width > 4096 || height > 4096) {
    throw new Error('DDS 尺寸超出预览范围')
  }
  const fourCC = String.fromCharCode(...data.subarray(84, 88))
  const bgra8 = fourCC === '\0\0\0\0'
    && uint32(data, 88) === 32
    && uint32(data, 92) === 0x00ff0000
    && uint32(data, 96) === 0x0000ff00
    && uint32(data, 100) === 0x000000ff
    && uint32(data, 104) === 0xff000000
  if (bgra8) {
    const required = 128 + width * height * 4
    if (data.byteLength < required) throw new Error('DDS 顶层 mip 数据不完整')
    const pixels = new Uint8ClampedArray(width * height * 4)
    for (let source = 128, target = 0; source < required; source += 4, target += 4) {
      pixels[target] = data[source + 2]
      pixels[target + 1] = data[source + 1]
      pixels[target + 2] = data[source]
      pixels[target + 3] = data[source + 3]
    }
    return { width, height, fourCC: 'BGRA8', pixels }
  }
  if (fourCC !== 'DXT1' && fourCC !== 'DXT5') {
    throw new Error(`暂不支持 DDS ${fourCC || 'unknown'} 压缩`)
  }
  const blockBytes = fourCC === 'DXT1' ? 8 : 16
  const blocksWide = Math.ceil(width / 4)
  const blocksHigh = Math.ceil(height / 4)
  const required = 128 + blocksWide * blocksHigh * blockBytes
  if (data.byteLength < required) throw new Error('DDS 顶层 mip 数据不完整')

  const pixels = new Uint8ClampedArray(width * height * 4)
  let offset = 128
  for (let blockY = 0; blockY < blocksHigh; blockY += 1) {
    for (let blockX = 0; blockX < blocksWide; blockX += 1) {
      writeBlock(data, offset, blockX, blockY, width, height, pixels, fourCC)
      offset += blockBytes
    }
  }
  return { width, height, fourCC, pixels }
}

export function decodeDdsBase64(encoded: string): DecodedDds {
  const binary = atob(encoded)
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0))
  return decodeDds(bytes)
}

export function decodedDdsToDataUrl(decoded: DecodedDds): string {
  const canvas = document.createElement('canvas')
  canvas.width = decoded.width
  canvas.height = decoded.height
  const context = canvas.getContext('2d')
  if (!context) throw new Error('浏览器没有 Canvas 2D context')
  const image = context.createImageData(decoded.width, decoded.height)
  image.data.set(decoded.pixels)
  context.putImageData(image, 0, 0)
  return canvas.toDataURL('image/png')
}
