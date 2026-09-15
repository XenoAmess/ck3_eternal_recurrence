import type { FitImage } from './imageFitter'

export interface WebGlScore {
  backend: 'webgl2-rgba8'
  meanSquaredRgbError: number
}

function shader(gl: WebGL2RenderingContext, type: number, source: string): WebGLShader {
  const compiled = gl.createShader(type)
  if (!compiled) throw new Error('WebGL2 shader allocation failed')
  gl.shaderSource(compiled, source)
  gl.compileShader(compiled)
  if (!gl.getShaderParameter(compiled, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(compiled)
    gl.deleteShader(compiled)
    throw new Error(`WebGL2 shader compile failed: ${log ?? 'unknown'}`)
  }
  return compiled
}

export function scoreWithWebGl2(target: FitImage, candidate: FitImage): WebGlScore | null {
  if (typeof document === 'undefined') return null
  if (
    target.width !== candidate.width || target.height !== candidate.height
    || target.pixels.length !== candidate.pixels.length
  ) throw new Error('WebGL2 scorer 要求相同尺寸的 RGBA 图片')
  const canvas = document.createElement('canvas')
  canvas.width = target.width
  canvas.height = target.height
  const gl = canvas.getContext('webgl2', { alpha: false, antialias: false, depth: false, stencil: false })
  if (!gl) return null
  const vertex = shader(gl, gl.VERTEX_SHADER, `#version 300 es
    const vec2 points[3] = vec2[3](vec2(-1.,-1.), vec2(3.,-1.), vec2(-1.,3.));
    out vec2 uv;
    void main() { gl_Position = vec4(points[gl_VertexID],0.,1.); uv = points[gl_VertexID] * .5 + .5; }
  `)
  const fragment = shader(gl, gl.FRAGMENT_SHADER, `#version 300 es
    precision highp float;
    uniform sampler2D targetTexture;
    uniform sampler2D candidateTexture;
    in vec2 uv;
    out vec4 color;
    void main() {
      vec4 target = texture(targetTexture, uv);
      vec3 delta = target.rgb - texture(candidateTexture, uv).rgb;
      color = vec4(delta * delta * target.a, target.a);
    }
  `)
  const program = gl.createProgram()
  if (!program) throw new Error('WebGL2 program allocation failed')
  gl.attachShader(program, vertex)
  gl.attachShader(program, fragment)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error(`WebGL2 program link failed: ${gl.getProgramInfoLog(program) ?? 'unknown'}`)
  }
  gl.useProgram(program)
  const upload = (unit: number, pixels: Uint8ClampedArray, uniformName: string) => {
    const texture = gl.createTexture()
    if (!texture) throw new Error('WebGL2 texture allocation failed')
    gl.activeTexture(gl.TEXTURE0 + unit)
    gl.bindTexture(gl.TEXTURE_2D, texture)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    gl.texImage2D(
      gl.TEXTURE_2D, 0, gl.RGBA8, target.width, target.height, 0,
      gl.RGBA, gl.UNSIGNED_BYTE, pixels,
    )
    gl.uniform1i(gl.getUniformLocation(program, uniformName), unit)
  }
  upload(0, target.pixels, 'targetTexture')
  upload(1, candidate.pixels, 'candidateTexture')
  gl.viewport(0, 0, target.width, target.height)
  gl.drawArrays(gl.TRIANGLES, 0, 3)
  const result = new Uint8Array(target.width * target.height * 4)
  gl.readPixels(0, 0, target.width, target.height, gl.RGBA, gl.UNSIGNED_BYTE, result)
  let sum = 0
  let weight = 0
  for (let offset = 0; offset < result.length; offset += 4) {
    sum += result[offset] + result[offset + 1] + result[offset + 2]
    weight += result[offset + 3]
  }
  gl.deleteProgram(program)
  gl.deleteShader(vertex)
  gl.deleteShader(fragment)
  return { backend: 'webgl2-rgba8', meanSquaredRgbError: weight > 0 ? sum / (weight * 3) : 0 }
}
