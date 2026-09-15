import { serializeCoatOfArms } from './serializer'
import type { CoatOfArms, CoatOfArmsInstance, ColoredEmblem } from './types'

export interface StructuralCompressionReceipt {
  strategy: 'adjacent-equal-style-v1'
  exactStructureOnly: true
  coloredEmblemBlocksBefore: number
  coloredEmblemBlocksAfter: number
  mergedBlocks: number
  drawnInstancesBefore: number
  drawnInstancesAfter: number
  utf8BytesBefore: number
  utf8BytesAfter: number
  linesBefore: number
  linesAfter: number
}

export interface StructuralCompressionResult {
  coatOfArms: CoatOfArms
  receipt: StructuralCompressionReceipt
}

const cloneInstance = (instance: CoatOfArmsInstance): CoatOfArmsInstance => ({
  position: [...instance.position],
  scale: [...instance.scale],
  rotation: instance.rotation,
  depth: instance.depth,
})

const cloneColoredEmblem = (emblem: ColoredEmblem): ColoredEmblem => ({
  texture: emblem.texture,
  colors: [...emblem.colors],
  mask: [...emblem.mask],
  instances: emblem.instances.map(cloneInstance),
})

const sameStyle = (left: ColoredEmblem, right: ColoredEmblem): boolean => (
  left.texture === right.texture
  && left.colors.every((color, index) => color === right.colors[index])
  && left.mask.length === right.mask.length
  && left.mask.every((value, index) => value === right.mask[index])
)

const drawnInstances = (coatOfArms: CoatOfArms): number => (
  coatOfArms.coloredEmblems.reduce((total, emblem) => total + emblem.instances.length, 0)
)

const sourceMetrics = (coatOfArms: CoatOfArms) => {
  const source = serializeCoatOfArms(coatOfArms)
  return {
    bytes: new TextEncoder().encode(source).length,
    lines: source.match(/\n/g)?.length ?? 0,
  }
}

/**
 * Merge only adjacent equal-style blocks. This preserves the flattened
 * instance sequence, every depth value, and all style bindings. It deliberately
 * does not group matching blocks across an intervening block because equal
 * depths may make source order observable in CK3.
 */
export function structurallyCompressCoatOfArms(
  coatOfArms: CoatOfArms,
): StructuralCompressionResult {
  const beforeSource = sourceMetrics(coatOfArms)
  const beforeInstances = drawnInstances(coatOfArms)
  const compressedBlocks: ColoredEmblem[] = []
  for (const sourceBlock of coatOfArms.coloredEmblems) {
    const block = cloneColoredEmblem(sourceBlock)
    const previous = compressedBlocks.at(-1)
    if (previous && sameStyle(previous, block)) {
      previous.instances.push(...block.instances)
    } else {
      compressedBlocks.push(block)
    }
  }
  const compressed: CoatOfArms = {
    outerKey: coatOfArms.outerKey,
    parent: coatOfArms.parent,
    pattern: coatOfArms.pattern,
    colors: [...coatOfArms.colors],
    coloredEmblems: compressedBlocks,
    texturedEmblems: coatOfArms.texturedEmblems.map((emblem) => ({ ...emblem })),
    rootPresence: coatOfArms.rootPresence ? {
      pattern: coatOfArms.rootPresence.pattern,
      colors: [...coatOfArms.rootPresence.colors],
    } : undefined,
  }
  const afterInstances = drawnInstances(compressed)
  if (afterInstances !== beforeInstances) {
    throw new Error('结构压缩改变了绘制实例数')
  }
  const afterSource = sourceMetrics(compressed)
  return {
    coatOfArms: compressed,
    receipt: {
      strategy: 'adjacent-equal-style-v1',
      exactStructureOnly: true,
      coloredEmblemBlocksBefore: coatOfArms.coloredEmblems.length,
      coloredEmblemBlocksAfter: compressed.coloredEmblems.length,
      mergedBlocks: coatOfArms.coloredEmblems.length - compressed.coloredEmblems.length,
      drawnInstancesBefore: beforeInstances,
      drawnInstancesAfter: afterInstances,
      utf8BytesBefore: beforeSource.bytes,
      utf8BytesAfter: afterSource.bytes,
      linesBefore: beforeSource.lines,
      linesAfter: afterSource.lines,
    },
  }
}
