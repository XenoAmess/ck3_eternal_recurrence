import { createCoatOfArms } from './types'
import type { CoatOfArms } from './types'

/**
 * Reference-machine gates fixed before running the first 10,000-instance test.
 * These are deliberately generous enough for GitHub's Windows runner while
 * still detecting an accidental quadratic parser/serializer regression.
 */
export const LARGE_DOCUMENT_CONTRACT = {
  contract: 'ck3-coa-large-document-v1',
  drawnInstances: 10_000,
  maximumSerializeMs: 5_000,
  maximumParseMs: 5_000,
  maximumProjectSerializeMs: 5_000,
  maximumProjectParseMs: 5_000,
  maximumTailEditMs: 250,
  maximumBrowserProjectImportMs: 15_000,
  maximumBrowserWindowJumpAndEditMs: 1_000,
  maximumBrowserClipboardCopyMs: 5_000,
  maximumBrowserProjectDownloadMs: 10_000,
  maximumMeasuredJsHeapDeltaBytes: 256 * 1024 * 1024,
  memoryEvidenceScope: 'JavaScript heap delta only; excludes GPU and browser-process memory',
} as const

export function buildLargeDocumentFixture(
  drawnInstances = LARGE_DOCUMENT_CONTRACT.drawnInstances,
): CoatOfArms {
  if (!Number.isSafeInteger(drawnInstances) || drawnInstances < 0) {
    throw new Error('drawnInstances must be a non-negative safe integer')
  }
  const coatOfArms = createCoatOfArms()
  coatOfArms.colors = ['rgb { 18 24 31 }', 'white', 'black']
  coatOfArms.coloredEmblems = [{
    texture: 'ce_block_02.dds',
    colors: ['rgb { 215 34 47 }', 'rgb { 215 34 47 }', 'rgb { 215 34 47 }'],
    mask: [],
    instances: Array.from({ length: drawnInstances }, (_, index) => ({
      position: [((index % 100) + 0.5) / 100, ((Math.floor(index / 100) % 100) + 0.5) / 100],
      scale: [0.01, 0.01],
      rotation: (index % 3600) / 10,
      depth: index + 1,
    })),
  }]
  return coatOfArms
}
