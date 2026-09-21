import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const corpusPath = resolve('src/data/fit-quality-synthetic-corpus-v1.json')
const fitterPath = resolve('src/domain/imageFitter.ts')
const retrievalPath = resolve('src/domain/assetRetrieval.ts')
const manifestPath = resolve('public/asset-packs/ck3-1.19.0.6/manifest.json')
const artifactPath = process.env.COA_STRUCTURE_ARTIFACT
  ? resolve('..', process.env.COA_STRUCTURE_ARTIFACT)
  : undefined
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()
const corpusBytes = await readFile(corpusPath)
const corpus = JSON.parse(corpusBytes.toString('utf8')) as {
  samplesPayloadSha256: string
  samples: Array<{
    id: string
    split: 'dev' | 'holdout'
    truth: {
      outerKey: string
      parent: string
      pattern: string
      colors: string[]
      coloredEmblems: Array<{
        texture: string
        colors: string[]
        mask: number[]
        instances: Array<{
          position: [number, number]
          scale: [number, number]
          rotation: number
          depth: number
        }>
      }>
      texturedEmblems: unknown[]
    }
  }>
}
const holdout = corpus.samples.filter((sample) => sample.split === 'holdout')

test('structure search proposes the frozen holdout primary region and material', async ({ page }) => {
  test.setTimeout(7 * 60_000)
  expect(holdout).toHaveLength(64)
  await page.goto('/')
  const result = await page.evaluate(async (samples) => {
    const dynamicImport = (path: string) => import(/* @vite-ignore */ path)
    const [packModule, ddsModule, rendererModule, fitterModule, retrievalModule] = await Promise.all([
      dynamicImport('/src/domain/assetPack.ts'),
      dynamicImport('/src/domain/dds.ts'),
      dynamicImport('/src/domain/renderer.ts'),
      dynamicImport('/src/domain/imageFitter.ts'),
      dynamicImport('/src/domain/assetRetrieval.ts'),
    ])
    const loaded = await packModule.loadWebAssetPack('/asset-packs/ck3-1.19.0.6/manifest.json')
    const indexed = await packModule.readWebFitIndex(loaded)
    const indexedEmblems = indexed.filter((item: { entry: { kind: string } }) => item.entry.kind === 'colored_emblem')
    const retrievalCandidates = indexedEmblems.map((item: {
      entry: { name: string, asset_sha256: string }
      texture: unknown
      shapeFeatures: { descriptor: Float32Array }
    }) => ({
      item: {
        asset: {
          name: item.entry.name,
          assetSha256: item.entry.asset_sha256,
          texture: item.texture,
          shapeFeatures: item.shapeFeatures,
        },
        shape: item.shapeFeatures,
      },
      name: item.entry.name,
      descriptor: retrievalModule.computeAssetRetrievalDescriptorV2(item.shapeFeatures),
    }))
    const manifest = loaded.pack
    const textureCache = new Map<string, unknown>()
    const loadTexture = async (kind: string, name: string) => {
      const key = `${kind}/${name}`
      if (textureCache.has(key)) return textureCache.get(key)
      const entry = manifest.assets.find((item: { kind: string, name: string }) => (
        item.kind === kind && item.name === name
      ))
      if (!entry) throw new Error(`missing ${key}`)
      const buffer = await fetch(`/asset-packs/ck3-1.19.0.6/${entry.url}`)
        .then((response) => response.arrayBuffer())
      const texture = ddsModule.decodeDds(new Uint8Array(buffer))
      textureCache.set(key, texture)
      return texture
    }
    const surfaceMask = await loadTexture('surface_mask', 'coa_mask_texture.dds')
    const rows = []
    for (const sample of samples) {
      const pattern = await loadTexture('pattern', sample.truth.pattern)
      const names = [...new Set(sample.truth.coloredEmblems.map((emblem) => emblem.texture))]
      const coloredEmblems = Object.fromEntries(await Promise.all(names.map(async (name) => (
        [name, await loadTexture('colored_emblem', name)]
      ))))
      const assets = { pattern, coloredEmblems, surfaceMask }
      const target = rendererModule.renderCoatOfArms(sample.truth, assets, manifest.named_colors ?? {}, 96)
      const background = rendererModule.renderCoatOfArms(
        { ...sample.truth, coloredEmblems: [], texturedEmblems: [] },
        { pattern, coloredEmblems: {}, surfaceMask },
        manifest.named_colors ?? {},
        96,
      )
      if (!target || !background) throw new Error(`${sample.id} render failed`)
      const image = { width: target.width, height: target.height, pixels: target.pixels }
      const foci = [0, 1].map((rank) => fitterModule.residualGeometry(image, background, rank))
      const primary = sample.truth.coloredEmblems[0]
      const anchor = primary.instances[0].position
      const anchorCovered = foci.some((focus) => (
        Math.abs(focus.position[0] - anchor[0]) <= focus.scale[0] / 2 + 0.08
        && Math.abs(focus.position[1] - anchor[1]) <= focus.scale[1] / 2 + 0.08
      ))
      const retrievalRanks = foci.map((focus) => {
        const query = retrievalModule.computeAssetRetrievalDescriptorV2(focus.descriptor)
        const ranked = retrievalModule.rankAssetRetrievalV2(query, retrievalCandidates)
        const matches = ranked.map((item: {
          item: { asset: unknown, shape: unknown }
          rotation: number
          flip: number
          loss: number
        }) => ({
          ...item.item,
          mask: [],
          rotation: item.rotation,
          flip: item.flip,
          loss: item.loss,
        }))
        const reranked = fitterModule.rerankStructureShapeMasks(focus, pattern, matches)
        return reranked.findIndex((item: { asset: { name: string } }) => item.asset.name === primary.texture) + 1
      })
      const positiveRanks = retrievalRanks.filter((rank) => rank > 0)
      rows.push({
        id: sample.id,
        primaryTexture: primary.texture,
        primaryAnchor: anchor,
        anchorCovered,
        retrievalRank: positiveRanks.length ? Math.min(...positiveRanks) : 0,
        foci: foci.map((focus) => ({ position: focus.position, scale: focus.scale })),
      })
    }
    return {
      rows,
      pack: { id: manifest.pack_id, build: manifest.ck3_build, manifestSha256: loaded.manifestSha256 },
      contracts: {
        structure: 'salient-components-depth-ordered-beam-v1',
        retrieval: retrievalModule.ASSET_RETRIEVAL_CONTRACT,
      },
    }
  }, holdout)

  const anchorHits = result.rows.filter((row) => row.anchorCovered).length
  const top32Hits = result.rows.filter((row) => row.retrievalRank > 0 && row.retrievalRank <= 32).length
  const top512Hits = result.rows.filter((row) => row.retrievalRank > 0 && row.retrievalRank <= 512).length
  const anchorRecall = anchorHits / result.rows.length
  const compositeTop32Recall = top32Hits / result.rows.length
  const compositeFrontierRecall = top512Hits / result.rows.length
  const passed = anchorRecall >= 0.85 && compositeFrontierRecall >= 0.50

  if (artifactPath) {
    const [fitterBytes, retrievalBytes, manifestBytes] = await Promise.all([
      readFile(fitterPath),
      readFile(retrievalPath),
      readFile(manifestPath),
    ])
    const report = {
      schema: 'ck3-coa-structure-search-holdout-v1',
      status: passed ? 'passed' : 'red',
      corpus: {
        fileSha256: sha256(corpusBytes),
        samplesPayloadSha256: corpus.samplesPayloadSha256,
        split: 'holdout',
        samples: result.rows.length,
      },
      assetPack: { ...result.pack, manifestFileSha256: sha256(manifestBytes) },
      contracts: result.contracts,
      implementation: {
        imageFitterSha256: sha256(fitterBytes),
        assetRetrievalSha256: sha256(retrievalBytes),
      },
      gates: {
        primaryAnchorRecallMinimum: 0.85,
        compositeCandidateFrontierRecallMinimum: 0.50,
        anchorHits,
        compositeTop32Hits: top32Hits,
        compositeTop512Hits: top512Hits,
        anchorRecall,
        compositeTop32Recall,
        compositeFrontierRecall,
        status: passed ? 'passed' : 'red',
      },
      rows: result.rows,
    }
    await mkdir(dirname(artifactPath), { recursive: true })
    await writeFile(artifactPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  }
  expect(anchorRecall).toBeGreaterThanOrEqual(0.85)
  expect(compositeFrontierRecall).toBeGreaterThanOrEqual(0.50)
})
