import { describe, expect, it } from 'vitest'
import { createCoatOfArms } from './types'
import {
  createCoatOfArmsProject,
  parseCoatOfArmsProject,
  serializeCoatOfArmsProject,
} from './projectDocument'

describe('browser project document', () => {
  it('round-trips a SHA-256-bound editable model', async () => {
    const source = createCoatOfArms()
    source.coloredEmblems[0].instances[0].rotation = 12.3
    const project = await createCoatOfArmsProject(source, {
      savedAt: '2026-09-15T00:00:00.000Z', selectedEmblem: 0,
    })
    const restored = await parseCoatOfArmsProject(serializeCoatOfArmsProject(project))

    expect(restored.coatOfArms).toEqual(source)
    expect(restored.coatOfArms).not.toBe(source)
    expect(restored.ck3Source.sha256).toMatch(/^[0-9A-F]{64}$/)
    expect(restored.ck3Source.stats.drawnInstances).toBe(1)
  })

  it('fails closed on content, count, and version tampering', async () => {
    const project = await createCoatOfArmsProject(createCoatOfArms(), {
      savedAt: '2026-09-15T00:00:00.000Z',
    })
    const contentTamper = structuredClone(project)
    contentTamper.coatOfArms.coloredEmblems[0].instances[0].depth = 999
    await expect(parseCoatOfArmsProject(JSON.stringify(contentTamper))).rejects.toThrow('SHA-256')

    const countTamper = structuredClone(project)
    countTamper.ck3Source.stats.drawnInstances = 999
    await expect(parseCoatOfArmsProject(JSON.stringify(countTamper))).rejects.toThrow('计数')

    const versionTamper = { ...project, schemaVersion: 2 }
    await expect(parseCoatOfArmsProject(JSON.stringify(versionTamper))).rejects.toThrow('schemaVersion')
  })

  it('rejects non-finite instance values before saving', async () => {
    const source = createCoatOfArms()
    source.coloredEmblems[0].instances[0].rotation = Number.NaN
    await expect(createCoatOfArmsProject(source)).rejects.toThrow('有限数值')
  })
})
