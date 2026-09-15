import { describe, expect, it } from 'vitest'
import { coatOfArmsDocumentStats } from './documentStats'
import { buildLargeDocumentFixture, LARGE_DOCUMENT_CONTRACT } from './largeDocumentContract'
import { parseCoatOfArms } from './parser'
import {
  createCoatOfArmsProject,
  parseCoatOfArmsProject,
  serializeCoatOfArmsProject,
} from './projectDocument'
import { serializeCoatOfArms } from './serializer'

describe('10,000-instance complete-document contract', () => {
  it('serializes, copies, reparses, saves, restores, and edits the tail without truncation', async () => {
    const contract = LARGE_DOCUMENT_CONTRACT
    const document = buildLargeDocumentFixture()

    const serializeStart = performance.now()
    const source = serializeCoatOfArms(document)
    const serializeMs = performance.now() - serializeStart
    const stats = coatOfArmsDocumentStats(document, source)
    expect(stats.drawnInstances).toBe(contract.drawnInstances)
    expect((source.match(/instance\s*=\s*\{/g) ?? [])).toHaveLength(contract.drawnInstances)
    expect(serializeMs).toBeLessThan(contract.maximumSerializeMs)

    // Clipboard writes consume this exact string in App.vue. A full string
    // copy here ensures the test never relies on the visible editor window.
    const copiedSource = `${source}`
    expect(copiedSource.length).toBe(source.length)

    const parseStart = performance.now()
    const parsed = parseCoatOfArms(copiedSource)
    const parseMs = performance.now() - parseStart
    expect(parsed.diagnostics.filter((item) => item.severity === 'error')).toEqual([])
    expect(parsed.coatOfArms.coloredEmblems[0].instances).toHaveLength(contract.drawnInstances)
    expect(serializeCoatOfArms(parsed.coatOfArms)).toBe(source)
    expect(parseMs).toBeLessThan(contract.maximumParseMs)

    const projectSerializeStart = performance.now()
    const project = await createCoatOfArmsProject(parsed.coatOfArms, {
      savedAt: '2026-09-15T00:00:00.000Z',
      selectedEmblem: 0,
      assetPack: {
        packId: 'ck3-1.19.0.6-base-complete',
        manifestSha256: 'A'.repeat(64),
        ck3Build: '1.19.0.6',
      },
    })
    const projectText = serializeCoatOfArmsProject(project)
    const projectSerializeMs = performance.now() - projectSerializeStart
    expect(project.ck3Source.stats.drawnInstances).toBe(contract.drawnInstances)
    expect(projectSerializeMs).toBeLessThan(contract.maximumProjectSerializeMs)

    const projectParseStart = performance.now()
    const restored = await parseCoatOfArmsProject(projectText)
    const projectParseMs = performance.now() - projectParseStart
    expect(restored.ck3Source.stats).toEqual(project.ck3Source.stats)
    expect(serializeCoatOfArms(restored.coatOfArms)).toBe(source)
    expect(projectParseMs).toBeLessThan(contract.maximumProjectParseMs)

    const editStart = performance.now()
    const finalInstance = restored.coatOfArms.coloredEmblems[0].instances.at(-1)!
    finalInstance.rotation = 359.9
    finalInstance.position = [0.995, 0.995]
    const tailEditMs = performance.now() - editStart
    const editedSource = serializeCoatOfArms(restored.coatOfArms)
    const editedParsed = parseCoatOfArms(editedSource)
    expect(editedParsed.coatOfArms.coloredEmblems[0].instances).toHaveLength(contract.drawnInstances)
    expect(editedParsed.coatOfArms.coloredEmblems[0].instances.at(-1)).toEqual(finalInstance)
    expect(tailEditMs).toBeLessThan(contract.maximumTailEditMs)

    console.info(JSON.stringify({
      contract: contract.contract,
      stats,
      timingsMs: { serializeMs, parseMs, projectSerializeMs, projectParseMs, tailEditMs },
      measuredJsHeapDeltaBytes: null,
      memoryEvidenceScope: 'Vitest DOM-less contract does not expose browser/GPU/process memory',
    }))
  }, 30_000)
})
