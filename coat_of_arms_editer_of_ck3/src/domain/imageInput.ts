import type { FitImage } from './imageFitter'

export const MAX_IMAGE_FILE_BYTES = 16 * 1024 * 1024
export const MAX_IMAGE_DIMENSION = 4096
export const SUPPORTED_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp'])

export interface DecodedFitImage {
  image: FitImage
  pyramid: FitImage[]
  originalFile: File
  originalWidth: number
  originalHeight: number
  workingResolution: number
  mimeType: string
  bytes: number
  previewUrl: string
}

export async function decodeFitImageFile(file: File, size = 96): Promise<DecodedFitImage> {
  if (!SUPPORTED_IMAGE_TYPES.has(file.type)) throw new Error('只接受 PNG、JPEG 或 WebP 图片')
  if (file.size < 1 || file.size > MAX_IMAGE_FILE_BYTES) throw new Error('图片必须在 1 B..16 MiB')
  if (!Number.isSafeInteger(size) || size < 32 || size > 256) throw new Error('目标预览尺寸必须在 32..256')
  const bitmap = await createImageBitmap(file)
  try {
    if (
      bitmap.width < 1 || bitmap.height < 1
      || bitmap.width > MAX_IMAGE_DIMENSION || bitmap.height > MAX_IMAGE_DIMENSION
    ) throw new Error('图片尺寸必须在 1..4096 像素')
    const maximumSourceSpan = Math.max(bitmap.width, bitmap.height)
    const primaryResolution = Math.min(size, maximumSourceSpan)
    const pyramidResolutions = [...new Set([primaryResolution, 96, 192, 256]
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
      previewUrl: preview.previewUrl,
    }
  } finally {
    bitmap.close()
  }
}
