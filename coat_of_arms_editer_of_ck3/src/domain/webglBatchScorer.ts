import type { FitImage, ImageFitMetrics } from './imageFitter'

export const WEBGL_BATCH_BACKEND = 'webgl2-texture-array-reduction-float-v1' as const

export type WebGlBatchStatus =
  | 'available'
  | 'unavailable'
  | 'context_lost'
  | 'runtime_error'

export interface WebGlBatchScorer {
  readonly backend: typeof WEBGL_BATCH_BACKEND
  readonly maximumBatchSize: number
  score(candidates: readonly FitImage[]): ImageFitMetrics[] | null
  status(): WebGlBatchStatus
  loseContextForTest(): boolean
  dispose(): void
}

type CanvasSource = HTMLCanvasElement | OffscreenCanvas

function createCanvas(width: number, height: number): CanvasSource | null {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(width, height)
  if (typeof document === 'undefined') return null
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  return canvas
}

function compileShader(gl: WebGL2RenderingContext, type: number, source: string): WebGLShader {
  const shader = gl.createShader(type)
  if (!shader) throw new Error('WebGL2 shader allocation failed')
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(shader)
    gl.deleteShader(shader)
    throw new Error(`WebGL2 batch shader compile failed: ${log ?? 'unknown'}`)
  }
  return shader
}

function createProgram(gl: WebGL2RenderingContext): {
  program: WebGLProgram
  vertex: WebGLShader
  fragment: WebGLShader
} {
  const vertex = compileShader(gl, gl.VERTEX_SHADER, `#version 300 es
    const vec2 points[3] = vec2[3](vec2(-1.,-1.), vec2(3.,-1.), vec2(-1.,3.));
    void main() { gl_Position = vec4(points[gl_VertexID], 0., 1.); }
  `)
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, `#version 300 es
    precision highp float;
    precision highp sampler2DArray;
    uniform sampler2D targetTexture;
    uniform sampler2DArray candidateTextures;
    uniform int imageHeight;
    out vec4 contribution;

    float luma(vec3 rgb) {
      return dot(rgb, vec3(54., 183., 19.)) / 256.;
    }

    void main() {
      ivec2 outputPixel = ivec2(gl_FragCoord.xy);
      int layer = outputPixel.y / imageHeight;
      ivec2 pixel = ivec2(outputPixel.x, outputPixel.y - layer * imageHeight);
      vec4 target = texelFetch(targetTexture, pixel, 0);
      vec4 candidate = texelFetch(candidateTextures, ivec3(pixel, layer), 0);
      float color = dot(target.rgb - candidate.rgb, target.rgb - candidate.rgb) * target.a / 3.;
      float horizontal = 0.;
      float vertical = 0.;
      if (pixel.x > 0) {
        ivec2 previousPixel = pixel - ivec2(1, 0);
        vec4 previousTarget = texelFetch(targetTexture, previousPixel, 0);
        vec4 previousCandidate = texelFetch(candidateTextures, ivec3(previousPixel, layer), 0);
        horizontal = min(target.a, previousTarget.a) * abs(
          (luma(target.rgb) - luma(previousTarget.rgb))
          - (luma(candidate.rgb) - luma(previousCandidate.rgb))
        );
      }
      if (pixel.y > 0) {
        ivec2 previousPixel = pixel - ivec2(0, 1);
        vec4 previousTarget = texelFetch(targetTexture, previousPixel, 0);
        vec4 previousCandidate = texelFetch(candidateTextures, ivec3(previousPixel, layer), 0);
        vertical = min(target.a, previousTarget.a) * abs(
          (luma(target.rgb) - luma(previousTarget.rgb))
          - (luma(candidate.rgb) - luma(previousCandidate.rgb))
        );
      }
      contribution = vec4(color, horizontal, vertical, 0.);
    }
  `)
  const program = gl.createProgram()
  if (!program) throw new Error('WebGL2 batch program allocation failed')
  gl.attachShader(program, vertex)
  gl.attachShader(program, fragment)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error(`WebGL2 batch program link failed: ${gl.getProgramInfoLog(program) ?? 'unknown'}`)
  }
  return { program, vertex, fragment }
}

function createReductionProgram(gl: WebGL2RenderingContext): {
  program: WebGLProgram
  vertex: WebGLShader
  fragment: WebGLShader
} {
  const vertex = compileShader(gl, gl.VERTEX_SHADER, `#version 300 es
    const vec2 points[3] = vec2[3](vec2(-1.,-1.), vec2(3.,-1.), vec2(-1.,3.));
    void main() { gl_Position = vec4(points[gl_VertexID], 0., 1.); }
  `)
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, `#version 300 es
    precision highp float;
    uniform sampler2D sourceTexture;
    uniform ivec2 sourceSize;
    uniform int reducedHeight;
    out vec4 sumValue;

    void main() {
      ivec2 outputPixel = ivec2(gl_FragCoord.xy);
      int layer = outputPixel.y / reducedHeight;
      ivec2 localOutput = ivec2(outputPixel.x, outputPixel.y - layer * reducedHeight);
      ivec2 firstSource = localOutput * 2;
      int sourceLayerY = layer * sourceSize.y;
      sumValue = vec4(0.);
      for (int offsetY = 0; offsetY < 2; offsetY += 1) {
        for (int offsetX = 0; offsetX < 2; offsetX += 1) {
          ivec2 localSource = firstSource + ivec2(offsetX, offsetY);
          if (localSource.x < sourceSize.x && localSource.y < sourceSize.y) {
            sumValue += texelFetch(sourceTexture, ivec2(localSource.x, sourceLayerY + localSource.y), 0);
          }
        }
      }
    }
  `)
  const program = gl.createProgram()
  if (!program) throw new Error('WebGL2 reduction program allocation failed')
  gl.attachShader(program, vertex)
  gl.attachShader(program, fragment)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error(`WebGL2 reduction program link failed: ${gl.getProgramInfoLog(program) ?? 'unknown'}`)
  }
  return { program, vertex, fragment }
}

function allocateFloatTexture(
  gl: WebGL2RenderingContext,
  width: number,
  height: number,
): WebGLTexture {
  const texture = gl.createTexture()
  if (!texture) throw new Error('WebGL2 float texture allocation failed')
  gl.bindTexture(gl.TEXTURE_2D, texture)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, width, height, 0, gl.RGBA, gl.FLOAT, null)
  return texture
}

function uploadTexture2d(
  gl: WebGL2RenderingContext,
  unit: number,
  width: number,
  height: number,
  pixels: Uint8ClampedArray,
): WebGLTexture {
  const texture = gl.createTexture()
  if (!texture) throw new Error('WebGL2 target texture allocation failed')
  gl.activeTexture(gl.TEXTURE0 + unit)
  gl.bindTexture(gl.TEXTURE_2D, texture)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, pixels)
  return texture
}

function lossWeights(target: FitImage): { colorWeight: number, edgeWeight: number } {
  let colorWeight = 0
  let edgeWeight = 0
  for (let y = 0; y < target.height; y += 1) {
    for (let x = 0; x < target.width; x += 1) {
      const alpha = target.pixels[(y * target.width + x) * 4 + 3] / 255
      colorWeight += alpha
      if (x > 0) edgeWeight += Math.min(alpha, target.pixels[(y * target.width + x - 1) * 4 + 3] / 255)
      if (y > 0) edgeWeight += Math.min(alpha, target.pixels[((y - 1) * target.width + x) * 4 + 3] / 255)
    }
  }
  return { colorWeight, edgeWeight }
}

export function createWebGl2BatchScorer(target: FitImage): WebGlBatchScorer | null {
  if (
    target.width < 1 || target.height < 1
    || target.pixels.length !== target.width * target.height * 4
  ) throw new Error('WebGL2 batch scorer 的目标图片无效')
  const canvas = createCanvas(target.width, target.height)
  if (!canvas) return null
  let gl: WebGL2RenderingContext | null
  try {
    gl = canvas.getContext('webgl2', {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      preserveDrawingBuffer: false,
    }) as WebGL2RenderingContext | null
  } catch {
    return null
  }
  if (!gl || !gl.getExtension('EXT_color_buffer_float')) return null
  const maximumArrayLayers = gl.getParameter(gl.MAX_ARRAY_TEXTURE_LAYERS) as number
  const maximumRenderbufferSize = gl.getParameter(gl.MAX_RENDERBUFFER_SIZE) as number
  const maximumTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE) as number
  const maximumViewport = gl.getParameter(gl.MAX_VIEWPORT_DIMS) as Int32Array
  const maximumBatchSize = Math.max(1, Math.min(
    maximumArrayLayers,
    Math.floor(Math.min(maximumRenderbufferSize, maximumTextureSize, maximumViewport[1]) / target.height),
    128,
  ))
  if (maximumBatchSize < 2) return null
  let currentStatus: WebGlBatchStatus = 'available'
  let resources: ReturnType<typeof createProgram>
  let reductionResources: ReturnType<typeof createReductionProgram>
  let targetTexture: WebGLTexture
  try {
    resources = createProgram(gl)
    reductionResources = createReductionProgram(gl)
    targetTexture = uploadTexture2d(gl, 0, target.width, target.height, target.pixels)
  } catch {
    return null
  }
  gl.useProgram(resources.program)
  gl.uniform1i(gl.getUniformLocation(resources.program, 'targetTexture'), 0)
  gl.uniform1i(gl.getUniformLocation(resources.program, 'candidateTextures'), 1)
  gl.uniform1i(gl.getUniformLocation(resources.program, 'imageHeight'), target.height)
  gl.useProgram(reductionResources.program)
  gl.uniform1i(gl.getUniformLocation(reductionResources.program, 'sourceTexture'), 2)
  const weights = lossWeights(target)

  const fail = (status: WebGlBatchStatus): null => {
    currentStatus = status
    return null
  }

  return {
    backend: WEBGL_BATCH_BACKEND,
    maximumBatchSize,
    status: () => currentStatus,
    score(candidates) {
      if (currentStatus !== 'available') return null
      if (gl.isContextLost()) return fail('context_lost')
      if (!candidates.length) return []
      if (candidates.length > maximumBatchSize) throw new Error('WebGL2 batch 超过本机有界容量')
      for (const candidate of candidates) {
        if (
          candidate.width !== target.width || candidate.height !== target.height
          || candidate.pixels.length !== target.pixels.length
        ) throw new Error('WebGL2 batch scorer 要求所有候选与目标尺寸一致')
      }
      const candidateTexture = gl.createTexture()
      const framebuffer = gl.createFramebuffer()
      if (!candidateTexture || !framebuffer) return fail('runtime_error')
      const floatTextures: WebGLTexture[] = []
      try {
        const packed = new Uint8Array(target.pixels.length * candidates.length)
        candidates.forEach((candidate, index) => packed.set(candidate.pixels, index * target.pixels.length))
        gl.activeTexture(gl.TEXTURE1)
        gl.bindTexture(gl.TEXTURE_2D_ARRAY, candidateTexture)
        gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
        gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
        gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
        gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
        gl.texImage3D(
          gl.TEXTURE_2D_ARRAY, 0, gl.RGBA8, target.width, target.height, candidates.length, 0,
          gl.RGBA, gl.UNSIGNED_BYTE, packed,
        )
        const contributionTexture = allocateFloatTexture(
          gl, target.width, target.height * candidates.length,
        )
        floatTextures.push(contributionTexture)
        gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer)
        gl.framebufferTexture2D(
          gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, contributionTexture, 0,
        )
        if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
          return fail('runtime_error')
        }
        gl.useProgram(resources.program)
        gl.viewport(0, 0, target.width, target.height * candidates.length)
        gl.drawArrays(gl.TRIANGLES, 0, 3)
        let reducedTexture = contributionTexture
        let reducedWidth = target.width
        let reducedHeight = target.height
        while (reducedWidth > 1 || reducedHeight > 1) {
          const nextWidth = Math.ceil(reducedWidth / 2)
          const nextHeight = Math.ceil(reducedHeight / 2)
          const nextTexture = allocateFloatTexture(gl, nextWidth, nextHeight * candidates.length)
          floatTextures.push(nextTexture)
          gl.framebufferTexture2D(
            gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, nextTexture, 0,
          )
          if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
            return fail('runtime_error')
          }
          gl.useProgram(reductionResources.program)
          gl.activeTexture(gl.TEXTURE2)
          gl.bindTexture(gl.TEXTURE_2D, reducedTexture)
          gl.uniform2i(
            gl.getUniformLocation(reductionResources.program, 'sourceSize'),
            reducedWidth,
            reducedHeight,
          )
          gl.uniform1i(
            gl.getUniformLocation(reductionResources.program, 'reducedHeight'),
            nextHeight,
          )
          gl.viewport(0, 0, nextWidth, nextHeight * candidates.length)
          gl.drawArrays(gl.TRIANGLES, 0, 3)
          reducedTexture = nextTexture
          reducedWidth = nextWidth
          reducedHeight = nextHeight
        }
        const contributions = new Float32Array(candidates.length * 4)
        gl.readPixels(0, 0, 1, candidates.length, gl.RGBA, gl.FLOAT, contributions)
        if (gl.isContextLost()) return fail('context_lost')
        if (gl.getError() !== gl.NO_ERROR) return fail('runtime_error')
        return candidates.map((_, candidateIndex) => {
          const offset = candidateIndex * 4
          const color = contributions[offset]
          const edge = contributions[offset + 1] + contributions[offset + 2]
          const colorLoss = weights.colorWeight > 0 ? color / weights.colorWeight : 0
          const edgeLoss = weights.edgeWeight > 0 ? edge / weights.edgeWeight : 0
          return { colorLoss, edgeLoss, totalLoss: colorLoss * 0.62 + edgeLoss * 0.38, relativeImprovement: 0 }
        })
      } catch {
        return fail(gl.isContextLost() ? 'context_lost' : 'runtime_error')
      } finally {
        gl.deleteFramebuffer(framebuffer)
        floatTextures.forEach((texture) => gl.deleteTexture(texture))
        gl.deleteTexture(candidateTexture)
      }
    },
    loseContextForTest() {
      const extension = gl.getExtension('WEBGL_lose_context')
      if (!extension) return false
      extension.loseContext()
      currentStatus = 'context_lost'
      return true
    },
    dispose() {
      gl.deleteTexture(targetTexture)
      gl.deleteProgram(resources.program)
      gl.deleteShader(resources.vertex)
      gl.deleteShader(resources.fragment)
      gl.deleteProgram(reductionResources.program)
      gl.deleteShader(reductionResources.vertex)
      gl.deleteShader(reductionResources.fragment)
      currentStatus = gl.isContextLost() ? 'context_lost' : 'unavailable'
    },
  }
}
