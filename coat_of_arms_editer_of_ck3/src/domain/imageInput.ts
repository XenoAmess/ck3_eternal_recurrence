import type { FitImage } from './imageFitter'
import { MAX_SVG_FILE_BYTES, sanitizeSvg } from './safeSvg'

export const MAX_IMAGE_FILE_BYTES = 16 * 1024 * 1024
export const MAX_IMAGE_DIMENSION = 4096
export const SUPPORTED_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml'])

export interface DecodedFitImage {
  image: FitImage
  pyramid: FitImage[]
  originalFile?: File
  originalWidth: number
  originalHeight: number
  workingResolution: number
  mimeType: string
  bytes: number
  sha256: string
  previewUrl: string
}

async function decodeSanitizedSvg(source: Blob): Promise<ImageBitmap> {
  const url = URL.createObjectURL(source)
  try {
    const image = new Image()
    image.decoding = 'sync'
    image.src = url
    await image.decode()
    return await createImageBitmap(image)
  } finally {
    URL.revokeObjectURL(url)
  }
}

export async function decodeFitImageFile(file: File, size = 96): Promise<DecodedFitImage> {
  if (!SUPPORTED_IMAGE_TYPES.has(file.type)) throw new Error('只接受 PNG、JPEG、WebP 或 SVG 图片')
  if (file.size < 1 || file.size > MAX_IMAGE_FILE_BYTES) throw new Error('图片必须在 1 B..16 MiB')
  if (file.type === 'image/svg+xml' && file.size > MAX_SVG_FILE_BYTES) throw new Error('SVG 必须在 1 B..2 MiB')
  if (!Number.isSafeInteger(size) || size < 32 || size > 256) throw new Error('目标预览尺寸必须在 32..256')
  const fileBytes = await file.arrayBuffer()
  const sha256 = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', fileBytes)))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()
  let bitmapSource: Blob = file
  if (file.type === 'image/svg+xml') {
    const sanitized = sanitizeSvg(new TextDecoder('utf-8', { fatal: true }).decode(fileBytes))
    bitmapSource = new Blob([sanitized.source], { type: 'image/svg+xml' })
  }
  const bitmap = file.type === 'image/svg+xml'
    ? await decodeSanitizedSvg(bitmapSource)
    : await createImageBitmap(bitmapSource)
  try {
    if (
      bitmap.width < 1 || bitmap.height < 1
      || bitmap.width > MAX_IMAGE_DIMENSION || bitmap.height > MAX_IMAGE_DIMENSION
    ) throw new Error('图片尺寸必须在 1..4096 像素')
    const maximumSourceSpan = Math.max(bitmap.width, bitmap.height)
    const primaryResolution = Math.min(size, maximumSourceSpan)
    // Keep the historical 96/192/256 search planes while retaining two exact
    // source-derived evaluation planes. Epsilon-Q final selection consumes
    // 96/230/512 directly instead of enlarging the already-downsampled 96px
    // target and thereby losing the fine contours it is meant to preserve.
    const pyramidResolutions = [...new Set([primaryResolution, 96, 192, 230, 256, 512]
      .filter((resolution) => resolution <= maximumSourceSpan))]
      .sort((left, right) => left - right)
    const renderAt = (resolution: number) => {
      const canvas = document.createElement('canvas')
      canvas.width = resolution
      canvas.height = resolution
      const context = canvas.getContext('2d', { willReadFrequently: true })
      if (!context) throw new Error('浏览器没有 Canvas 2D context')
      context.clearRect(0, 0, resolution, resolution)
      const ratio = Math.min(resolution / bitmap.width, resolution / bitmap.height)
      const width = bitmap.width * ratio
      const height = bitmap.height * ratio
      context.drawImage(bitmap, (resolution - width) / 2, (resolution - height) / 2, width, height)
      return {
        image: { width: resolution, height: resolution, pixels: context.getImageData(0, 0, resolution, resolution).data },
        previewUrl: canvas.toDataURL('image/png'),
      }
    }
    const renderedPyramid = pyramidResolutions.map(renderAt)
    const primary = renderedPyramid[pyramidResolutions.indexOf(primaryResolution)]
    const preview = renderedPyramid[renderedPyramid.length - 1]
    return {
      image: primary.image,
      pyramid: renderedPyramid.map((item) => item.image),
      originalFile: file,
      originalWidth: bitmap.width,
      originalHeight: bitmap.height,
      workingResolution: preview.image.width,
      mimeType: file.type,
      bytes: file.size,
      sha256,
      previewUrl: preview.previewUrl,
    }
  } finally {
    bitmap.close()
  }
}
