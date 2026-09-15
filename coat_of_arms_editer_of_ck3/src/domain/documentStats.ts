import type { CoatOfArms } from './types'

export interface CoatOfArmsDocumentStats {
  logicalLayers: number
  coloredEmblemBlocks: number
  texturedEmblemBlocks: number
  drawnInstances: number
  utf8Bytes: number
  lines: number
}

export function countDrawnInstances(coatOfArms: CoatOfArms): number {
  return coatOfArms.coloredEmblems.reduce((sum, emblem) => sum + emblem.instances.length, 0)
}

export function coatOfArmsDocumentStats(coatOfArms: CoatOfArms, source: string): CoatOfArmsDocumentStats {
  return {
    logicalLayers: coatOfArms.coloredEmblems.length + coatOfArms.texturedEmblems.length,
    coloredEmblemBlocks: coatOfArms.coloredEmblems.length,
    texturedEmblemBlocks: coatOfArms.texturedEmblems.length,
    drawnInstances: countDrawnInstances(coatOfArms),
    utf8Bytes: new TextEncoder().encode(source).length,
    lines: source.length ? (source.match(/\n/g)?.length ?? 0) + 1 : 0,
  }
}
