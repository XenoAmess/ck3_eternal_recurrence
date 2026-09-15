import { describe, expect, it } from 'vitest'
import { scoreWithWebGl2 } from './webglScorer'

describe('WebGL2 scorer boundary', () => {
  it('returns an explicit unavailable result outside a browser DOM', () => {
    const image = { width: 1, height: 1, pixels: new Uint8ClampedArray([0, 0, 0, 255]) }
    expect(scoreWithWebGl2(image, image)).toBeNull()
  })
})
