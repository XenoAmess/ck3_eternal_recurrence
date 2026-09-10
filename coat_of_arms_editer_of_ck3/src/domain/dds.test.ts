import { describe, expect, it } from 'vitest'
import { decodeDds } from './dds'

function dds(fourCC: 'DXT1' | 'DXT5', block: number[]): Uint8Array {
  const data = new Uint8Array(128 + block.length)
  data.set([0x44, 0x44, 0x53, 0x20])
  new DataView(data.buffer).setUint32(4, 124, true)
  new DataView(data.buffer).setUint32(12, 4, true)
  new DataView(data.buffer).setUint32(16, 4, true)
  data.set(Array.from(fourCC, (character) => character.charCodeAt(0)), 84)
  data.set(block, 128)
  return data
}

function bgra8(pixel: [number, number, number, number]): Uint8Array {
  const data = new Uint8Array(128 + 4 * 4 * 4)
  data.set([0x44, 0x44, 0x53, 0x20])
  const view = new DataView(data.buffer)
  view.setUint32(4, 124, true)
  view.setUint32(12, 4, true)
  view.setUint32(16, 4, true)
  view.setUint32(88, 32, true)
  view.setUint32(92, 0x00ff0000, true)
  view.setUint32(96, 0x0000ff00, true)
  view.setUint32(100, 0x000000ff, true)
  view.setUint32(104, 0xff000000, true)
  for (let offset = 128; offset < data.length; offset += 4) data.set(pixel, offset)
  return data
}

describe('DDS decoder', () => {
  it('decodes a DXT1 RGB565 block', () => {
    const decoded = decodeDds(dds('DXT1', [
      0x00, 0xf8, 0xe0, 0x07,
      0x00, 0x00, 0x00, 0x00,
    ]))

    expect(decoded.fourCC).toBe('DXT1')
    expect(decoded.width).toBe(4)
    expect([...decoded.pixels.slice(0, 4)]).toEqual([255, 0, 0, 255])
    expect([...decoded.pixels.slice(-4)]).toEqual([255, 0, 0, 255])
  })

  it('decodes DXT5 alpha and color blocks', () => {
    const decoded = decodeDds(dds('DXT5', [
      255, 0, 0, 0, 0, 0, 0, 0,
      0x1f, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00,
    ]))

    expect(decoded.fourCC).toBe('DXT5')
    expect([...decoded.pixels.slice(0, 4)]).toEqual([0, 0, 255, 255])
  })

  it('decodes the uncompressed BGRA8 layout used by _default.dds', () => {
    const decoded = decodeDds(bgra8([10, 20, 30, 40]))

    expect(decoded.fourCC).toBe('BGRA8')
    expect([...decoded.pixels.slice(0, 4)]).toEqual([30, 20, 10, 40])
    expect([...decoded.pixels.slice(-4)]).toEqual([30, 20, 10, 40])
  })

  it('rejects unsupported or truncated files', () => {
    expect(() => decodeDds(new Uint8Array([1, 2, 3]))).toThrow('不是 DDS')
    expect(() => decodeDds(dds('DXT1', []))).toThrow('顶层 mip 数据不完整')
  })
})
