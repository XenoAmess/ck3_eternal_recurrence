export const MAX_SVG_FILE_BYTES = 2 * 1024 * 1024
export const MAX_SVG_ELEMENTS = 5_000
export const MAX_SVG_DEPTH = 64
export const MAX_SVG_DIMENSION = 4_096

const ALLOWED_ELEMENTS = new Set([
  'svg', 'g', 'defs', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
  'clippath', 'mask', 'use', 'lineargradient', 'radialgradient', 'stop', 'title', 'desc',
])

const ALLOWED_ATTRIBUTES = new Set([
  'xmlns', 'xmlns:xlink', 'version', 'viewbox', 'width', 'height', 'preserveaspectratio',
  'id', 'x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'd', 'points',
  'fill', 'fill-opacity', 'fill-rule', 'stroke', 'stroke-width', 'stroke-opacity',
  'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'stroke-dasharray',
  'stroke-dashoffset', 'opacity', 'transform', 'clip-rule', 'clip-path', 'mask', 'href',
  'xlink:href', 'offset', 'stop-color', 'stop-opacity', 'gradientunits', 'gradienttransform',
  'spreadmethod', 'fx', 'fy', 'fr',
])

const SAFE_FRAGMENT = /^#[A-Za-z_][A-Za-z0-9_.:-]*$/
const SAFE_LOCAL_URL = /^url\(\s*#[A-Za-z_][A-Za-z0-9_.:-]*\s*\)$/i

function parseLength(value: string | null): number | undefined {
  if (!value) return undefined
  const match = value.trim().match(/^([+]?(?:\d+(?:\.\d*)?|\.\d+))(?:px)?$/i)
  if (!match) return undefined
  const result = Number(match[1])
  return Number.isFinite(result) && result > 0 ? result : undefined
}

function svgDimensions(root: Element): { width: number, height: number } {
  let width = parseLength(root.getAttribute('width'))
  let height = parseLength(root.getAttribute('height'))
  const viewBox = root.getAttribute('viewBox')?.trim().split(/[\s,]+/).map(Number)
  if (viewBox?.length === 4 && viewBox.every(Number.isFinite) && viewBox[2] > 0 && viewBox[3] > 0) {
    width ??= viewBox[2]
    height ??= viewBox[3]
  }
  if (!width || !height) throw new Error('SVG 必须提供有限的 width/height 或四分量 viewBox')
  if (width > MAX_SVG_DIMENSION || height > MAX_SVG_DIMENSION) {
    throw new Error(`SVG 栅格尺寸不得超过 ${MAX_SVG_DIMENSION}×${MAX_SVG_DIMENSION}`)
  }
  return { width: Math.ceil(width), height: Math.ceil(height) }
}

export interface SanitizedSvg {
  source: string
  width: number
  height: number
  elementCount: number
}

export function sanitizeSvg(source: string): SanitizedSvg {
  if (/<!DOCTYPE|<!ENTITY/i.test(source)) throw new Error('SVG 不允许 DOCTYPE 或实体声明')
  const document = new DOMParser().parseFromString(source, 'image/svg+xml')
  if (document.querySelector('parsererror')) throw new Error('SVG XML 无法解析')
  const root = document.documentElement
  if (root.localName.toLowerCase() !== 'svg') throw new Error('根元素必须是 svg')
  const { width, height } = svgDimensions(root)
  const elements = [...document.querySelectorAll('*')]
  if (elements.length > MAX_SVG_ELEMENTS) throw new Error(`SVG 元素超过 ${MAX_SVG_ELEMENTS} 个安全上限`)
  for (const element of elements) {
    if (!ALLOWED_ELEMENTS.has(element.localName.toLowerCase())) {
      throw new Error(`SVG 包含不允许的元素 <${element.localName}>`)
    }
    let depth = 0
    for (let parent = element.parentElement; parent; parent = parent.parentElement) depth += 1
    if (depth > MAX_SVG_DEPTH) throw new Error(`SVG 嵌套深度超过 ${MAX_SVG_DEPTH}`)
    for (const attribute of [...element.attributes]) {
      const name = attribute.name.toLowerCase()
      const value = attribute.value.trim()
      if (name.startsWith('on') || name === 'style') {
        throw new Error(`SVG 不允许属性 ${attribute.name}`)
      }
      if (!ALLOWED_ATTRIBUTES.has(name)) throw new Error(`SVG 包含不允许的属性 ${attribute.name}`)
      if (name === 'xmlns' || name === 'xmlns:xlink') continue
      if (/(?:javascript|vbscript|data|https?|file):/i.test(value)) {
        throw new Error(`SVG 属性 ${attribute.name} 不允许外部或可执行 URI`)
      }
      if ((name === 'href' || name === 'xlink:href') && !SAFE_FRAGMENT.test(value)) {
        throw new Error(`SVG ${attribute.name} 只允许引用当前文档的 #id`)
      }
      if (/url\s*\(/i.test(value) && !SAFE_LOCAL_URL.test(value)) {
        throw new Error(`SVG 属性 ${attribute.name} 只允许 url(#id)`)
      }
    }
  }
  root.setAttribute('width', String(width))
  root.setAttribute('height', String(height))
  return {
    source: new XMLSerializer().serializeToString(document),
    width,
    height,
    elementCount: elements.length,
  }
}
