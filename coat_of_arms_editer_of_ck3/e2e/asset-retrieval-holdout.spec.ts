import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const corpusPath = resolve('src/data/fit-quality-synthetic-corpus-v1.json')
const implementationPath = resolve('src/domain/assetRetrieval.ts')
const manifestPath = resolve('public/asset-packs/ck3-1.19.0.6/manifest.json')
const artifactPath = process.env.COA_RETRIEVAL_ARTIFACT
  ? resolve('..', process.env.COA_RETRIEVAL_ARTIFACT)
  : undefined
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

const corpusBytes = await readFile(corpusPath)
const corpus = JSON.parse(corpusBytes.toString('utf8')) as {
  samplesPayloadSha256: string
  samples: Array<{
    id: string
    split: 'dev' | 'holdout'
    truth: {
      coloredEmblems: Array<{
        texture: string
        textureSha256: string
        mask: number[]
        instances: Array<{ rotation: number, scale: [number, number] }>
      }>
    }
  }>
}
const holdout = corpus.samples.filter((sample) => sample.split === 'holdout').map((sample) => {
  const primary = sample.truth.coloredEmblems[0]
  return {
    id: sample.id,
    texture: primary.texture,
    textureSha256: primary.textureSha256,
    rotation: primary.instances[0].rotation,
    flip: primary.instances[0].scale[0] < 0 ? -1 : 1,
    mask: primary.mask,
  }
})

test('retrieval v2 clears frozen holdout Top-8 and Top-32 gates', async ({ page }) => {
  test.setTimeout(5 * 60_000)
  expect(holdout).toHaveLength(64)
  await page.goto('/')
  const result = await page.evaluate(async (queries) => {
    const dynamicImport = (path: string) => import(/* @vite-ignore */ path)
    const [packModule, retrievalModule] = await Promise.all([
      dynamicImport('/src/domain/assetPack.ts'),
      dynamicImport('/src/domain/assetRetrieval.ts'),
    ])
    const loaded = await packModule.loadWebAssetPack('/asset-packs/ck3-1.19.0.6/manifest.json')
    const indexed = await packModule.readWebFitIndex(loaded)
    const emblems = indexed.filter((item: { entry: { kind: string } }) => item.entry.kind === 'colored_emblem')
    const candidates = emblems.map((item: {
      entry: { name: string, asset_sha256: string }
      shapeFeatures: { descriptor: Float32Array }
    }) => ({
      item: { name: item.entry.name, sha256: item.entry.asset_sha256 },
      name: item.entry.name,
      descriptor: retrievalModule.computeAssetRetrievalDescriptorV2(item.shapeFeatures),
    }))
    const byName = new Map(candidates.map((item: { name: string }) => [item.name, item]))
    const rows = []
    for (const query of queries) {
      const truth = byName.get(query.texture) as { descriptor: { grid: Float32Array } } | undefined
      if (!truth) throw new Error(`missing indexed truth ${query.texture}`)
      const transformed = retrievalModule.transformAssetRetrievalGrid(
        truth.descriptor.grid,
        query.rotation,
        query.flip,
      )
      const target = retrievalModule.computeAssetRetrievalDescriptorV2(transformed)
      const ranked = retrievalModule.rankAssetRetrievalV2(target, candidates)
      const rank = ranked.findIndex((item: { name: string }) => item.name === query.texture) + 1
      rows.push({
        ...query,
        rank,
        top8: ranked.slice(0, 8).map((item: { name: string }) => item.name),
        top32ContainsTruth: ranked.slice(0, 32).some((item: { name: string }) => item.name === query.texture),
        selectedTransform: rank > 0 ? {
          rotation: ranked[rank - 1].rotation,
          flip: ranked[rank - 1].flip,
          loss: ranked[rank - 1].loss,
        } : null,
      })
    }
    return {
      contract: retrievalModule.ASSET_RETRIEVAL_CONTRACT,
      fineShortlist: retrievalModule.ASSET_RETRIEVAL_FINE_SHORTLIST,
      pack: {
        id: loaded.pack.pack_id,
        build: loaded.pack.ck3_build,
        manifestSha256: loaded.manifestSha256,
      },
      indexedEmblems: emblems.length,
      rows,
    }
  }, holdout)

  const top8Hits = result.rows.filter((row) => row.rank > 0 && row.rank <= 8).length
  const top32Hits = result.rows.filter((row) => row.rank > 0 && row.rank <= 32).length
  const top8Recall = top8Hits / result.rows.length
  const top32Recall = top32Hits / result.rows.length
  if (artifactPath) {
    const [implementationBytes, manifestBytes] = await Promise.all([
      readFile(implementationPath),
      readFile(manifestPath),
    ])
    const report = {
      schema: 'ck3-coa-asset-retrieval-holdout-v1',
      status: top8Recall >= 0.85 && top32Recall >= 0.95 ? 'passed' : 'red',
      contract: result.contract,
      corpus: {
        file: 'src/data/fit-quality-synthetic-corpus-v1.json',
        fileSha256: sha256(corpusBytes),
        samplesPayloadSha256: corpus.samplesPayloadSha256,
        split: 'holdout',
        samples: result.rows.length,
      },
      assetPack: {
        ...result.pack,
        manifestFileSha256: sha256(manifestBytes),
        indexedEmblems: result.indexedEmblems,
      },
      implementationSha256: sha256(implementationBytes),
      queryContract: {
        identity: 'primary-truth-colored-emblem',
        rotation: 'truth-instance-rotation',
        mirror: 'truth-instance-scale-x-sign',
        maskRecorded: true,
        transformCandidates: { rotations: 24, stepDegrees: 15, mirrors: 2 },
        fineShortlist: result.fineShortlist,
      },
      gates: {
        top8Minimum: 0.85,
        top32Minimum: 0.95,
        top8Hits,
        top32Hits,
        top8Recall,
        top32Recall,
        allTruthAssetsIndexed: result.rows.every((row) => row.rank > 0),
        status: top8Recall >= 0.85 && top32Recall >= 0.95 ? 'passed' : 'red',
      },
      rows: result.rows,
    }
    await mkdir(dirname(artifactPath), { recursive: true })
    await writeFile(artifactPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  }
  expect(top8Recall).toBeGreaterThanOrEqual(0.85)
  expect(top32Recall).toBeGreaterThanOrEqual(0.95)
  expect(result.rows.every((row) => row.rank > 0)).toBe(true)
})
