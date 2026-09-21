import type { FitImage } from './imageFitter'

export const EPSILON_QUALITY_CORPUS_CONTRACT =
  'epsilon-q-programmatic-corpus-32-split-v1' as const

export type EpsilonQualityCategory =
  | 'flat-contour'
  | 'fine-detail'
  | 'color-overlap'
  | 'texture-gradient'

export type EpsilonQualitySplit = 'development' | 'sealed-holdout'

export interface EpsilonQualityScenario {
  id: string
  family: string
  category: EpsilonQualityCategory
  split: EpsilonQualitySplit
  generatorRevision: typeof EPSILON_QUALITY_CORPUS_CONTRACT
}

const CATEGORIES: readonly EpsilonQualityCategory[] = [
  'flat-contour',
  'fine-detail',
  'color-overlap',
  'texture-gradient',
]

/**
 * Frozen, independent programmatic scenes. A family has exactly one member,
 * so no transformed sibling can leak from development into the sealed set.
 */
export const EPSILON_QUALITY_SCENARIOS: readonly EpsilonQualityScenario[] = Object.freeze(
  CATEGORIES.flatMap((category) => Array.from({ length: 8 }, (_, index) => ({
    id: `epsilon-${category}-${String(index + 1).padStart(2, '0')}`,
    family: `${category}-family-${String(index + 1).padStart(2, '0')}`,
    category,
    split: index % 2 === 0 ? 'development' as const : 'sealed-holdout' as const,
    generatorRevision: EPSILON_QUALITY_CORPUS_CONTRACT,
  }))),
)

type Rgb = readonly [number, number, number]

function clampByte(value: number): number {
  return Math.max(0, Math.min(255, Math.round(value)))
}

function paintPixel(image: FitImage, x: number, y: number, color: Rgb, alpha = 1): void {
  if (x < 0 || y < 0 || x >= image.width || y >= image.height || alpha <= 0) return
  const offset = (y * image.width + x) * 4
  const boundedAlpha = Math.max(0, Math.min(1, alpha))
  for (let channel = 0; channel < 3; channel += 1) {
    image.pixels[offset + channel] = clampByte(
      image.pixels[offset + channel] * (1 - boundedAlpha) + color[channel] * boundedAlpha,
    )
  }
}

function palette(index: number): readonly [Rgb, Rgb, Rgb] {
  return [
    [35 + index * 17, 44 + index * 9, 72 + index * 11],
    [220 - index * 9, 74 + index * 16, 82 + index * 7],
    [58 + index * 13, 194 - index * 8, 166 + index * 9],
  ]
}

function flatContour(image: FitImage, index: number, colors: readonly [Rgb, Rgb, Rgb]): void {
  const centerX = image.width * (0.38 + (index % 3) * 0.1)
  const centerY = image.height * (0.42 + (index % 2) * 0.13)
  const radius = image.width * (0.17 + index * 0.008)
  for (let y = 0; y < image.height; y += 1) {
    for (let x = 0; x < image.width; x += 1) {
      const dx = x + 0.5 - centerX
      const dy = y + 0.5 - centerY
      const insideDisk = dx * dx + dy * dy <= radius * radius
      const insideWedge = y > image.height * 0.18
        && y < image.height * 0.82
        && Math.abs(x - image.width * 0.64) < (y - image.height * 0.12) * 0.36
      if (insideDisk) paintPixel(image, x, y, colors[1])
      else if (insideWedge) paintPixel(image, x, y, colors[2])
    }
  }
}

function fineDetail(image: FitImage, index: number, colors: readonly [Rgb, Rgb, Rgb]): void {
  const slope = (index - 3.5) * 0.12
  for (let x = 5; x < image.width - 5; x += 1) {
    const y = Math.round(image.height * 0.28 + slope * (x - image.width / 2))
    paintPixel(image, x, y, colors[1])
    if (index % 2 === 0) paintPixel(image, x, y + 1, colors[1])
  }
  const radius = image.width * 0.12
  for (let y = 0; y < image.height; y += 1) {
    for (let x = 0; x < image.width; x += 1) {
      const distance = Math.hypot(x - image.width * 0.5, y - image.height * 0.63)
      if (Math.abs(distance - radius) < 1.15) paintPixel(image, x, y, colors[2])
    }
  }
}

function colorOverlap(image: FitImage, index: number, colors: readonly [Rgb, Rgb, Rgb]): void {
  const centers = [
    [0.38, 0.48, colors[1]],
    [0.60, 0.48, colors[2]],
    [0.49, 0.64, [238 - index * 5, 188, 54] as Rgb],
  ] as const
  for (const [cx, cy, color] of centers) {
    for (let y = 0; y < image.height; y += 1) {
      for (let x = 0; x < image.width; x += 1) {
        if (Math.hypot(x / image.width - cx, y / image.height - cy) < 0.205) {
          paintPixel(image, x, y, color, 0.68)
        }
      }
    }
  }
}

function textureGradient(image: FitImage, index: number, colors: readonly [Rgb, Rgb, Rgb]): void {
  for (let y = 0; y < image.height; y += 1) {
    for (let x = 0; x < image.width; x += 1) {
      const u = x / Math.max(1, image.width - 1)
      const v = y / Math.max(1, image.height - 1)
      const wave = (Math.sin((u * (3 + index % 3) + v * 2) * Math.PI * 2) + 1) / 2
      const mix = Math.max(0, Math.min(1, u * 0.55 + v * 0.25 + wave * 0.2))
      paintPixel(image, x, y, [
        colors[1][0] * (1 - mix) + colors[2][0] * mix,
        colors[1][1] * (1 - mix) + colors[2][1] * mix,
        colors[1][2] * (1 - mix) + colors[2][2] * mix,
      ])
    }
  }
}

export function renderEpsilonQualityScenario(
  scenario: EpsilonQualityScenario,
  size = 96,
): FitImage {
  if (!Number.isSafeInteger(size) || size < 16 || size > 1024) {
    throw new Error('Epsilon-Q 场景尺寸必须在 16..1024')
  }
  const known = EPSILON_QUALITY_SCENARIOS.find((item) => item.id === scenario.id)
  if (!known || known.generatorRevision !== scenario.generatorRevision) {
    throw new Error('Epsilon-Q 场景不属于冻结语料 revision')
  }
  const categoryIndex = CATEGORIES.indexOf(scenario.category)
  const withinCategory = EPSILON_QUALITY_SCENARIOS
    .filter((item) => item.category === scenario.category)
    .findIndex((item) => item.id === scenario.id)
  const colors = palette(withinCategory)
  const image: FitImage = {
    width: size,
    height: size,
    pixels: new Uint8ClampedArray(size * size * 4),
  }
  for (let offset = 0; offset < image.pixels.length; offset += 4) {
    image.pixels[offset] = colors[0][0]
    image.pixels[offset + 1] = colors[0][1]
    image.pixels[offset + 2] = colors[0][2]
    image.pixels[offset + 3] = 255
  }
  const generators = [flatContour, fineDetail, colorOverlap, textureGradient] as const
  generators[categoryIndex](image, withinCategory, colors)
  return image
}
