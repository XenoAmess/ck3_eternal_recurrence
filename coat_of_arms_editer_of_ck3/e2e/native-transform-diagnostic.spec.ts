import { readFile, mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { test } from '@playwright/test'
import { decodeDds } from '../src/domain/dds'
import { parseCoatOfArms } from '../src/domain/parser'
import {
  renderCoatOfArms,
  type CoatOfArmsRenderOptions,
} from '../src/domain/renderer'
import type { WebAssetPack, WebAssetPackEntry } from '../src/domain/assetPack'

const enabled = process.env.COA_NATIVE_TRANSFORM_DIAGNOSTIC === 'true'
const repositoryRoot = resolve('..')
const corpusRoot = resolve(
  repositoryRoot,
  process.env.COA_NATIVE_TRANSFORM_CORPUS
    ?? 'docs/coat-of-arms-fit-artifacts/user-picture-corpus-v6-budget-1024',
)
const outputRoot = resolve(
  repositoryRoot,
  process.env.COA_NATIVE_TRANSFORM_OUTPUT
    ?? 'docs/coat-of-arms-fit-artifacts/user-picture-corpus-v6-transform-diagnostic',
)
const packRoot = resolve('public/asset-packs/ck3-1.19.0.6')

const candidates: Array<{
  id: string
  options: CoatOfArmsRenderOptions
  rotationQuantization?: 'truncate' | 'round'
}> = [
  {
    id: 'scale-after-rotation-positive',
    options: { emblemTransformConvention: 'scale-after-rotation', emblemRotationSign: 1 },
  },
  {
    id: 'scale-after-rotation-negative',
    options: { emblemTransformConvention: 'scale-after-rotation', emblemRotationSign: -1 },
  },
  {
    id: 'rotation-after-scale-positive',
    options: { emblemTransformConvention: 'rotation-after-scale', emblemRotationSign: 1 },
  },
  {
    id: 'rotation-after-scale-negative',
    options: { emblemTransformConvention: 'rotation-after-scale', emblemRotationSign: -1 },
  },
  {
    id: 'scale-after-rotation-negative-truncate',
    options: { emblemTransformConvention: 'scale-after-rotation', emblemRotationSign: -1 },
    rotationQuantization: 'truncate',
  },
  {
    id: 'scale-after-rotation-negative-round',
    options: { emblemTransformConvention: 'scale-after-rotation', emblemRotationSign: -1 },
    rotationQuantization: 'round',
  },
  {
    id: 'scale-after-rotation-negative-depth-ascending',
    options: {
      emblemTransformConvention: 'scale-after-rotation',
      emblemRotationSign: -1,
      emblemDepthOrder: 'ascending',
    },
  },
  {
    id: 'scale-after-rotation-negative-depth-descending',
    options: {
      emblemTransformConvention: 'scale-after-rotation',
      emblemRotationSign: -1,
      emblemDepthOrder: 'descending',
    },
  },
]

function asset(
  pack: WebAssetPack,
  name: string,
  kinds: WebAssetPackEntry['kind'][],
): WebAssetPackEntry {
  const result = pack.assets.find((entry) => entry.name === name && kinds.includes(entry.kind))
  if (!result) throw new Error(`missing asset ${name}`)
  return result
}

async function decode(entry: WebAssetPackEntry) {
  return decodeDds(new Uint8Array(await readFile(resolve(packRoot, entry.url))))
}

test('render native transform candidates for framebuffer comparison', async ({ page }) => {
  test.skip(!enabled, 'set COA_NATIVE_TRANSFORM_DIAGNOSTIC=true for the native diagnostic')
  const manifest = JSON.parse(await readFile(resolve(packRoot, 'manifest.json'), 'utf8')) as WebAssetPack
  const caseIds = (process.env.COA_NATIVE_TRANSFORM_CASES ?? 'picture-02,picture-05,picture-07')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)

  for (const caseId of caseIds) {
    const source = await readFile(resolve(corpusRoot, caseId, 'coat_of_arms.txt'), 'utf8')
    const parsed = parseCoatOfArms(source)
    const errors = parsed.diagnostics.filter((item) => item.severity === 'error')
    if (errors.length) throw new Error(`${caseId} parse failed: ${JSON.stringify(errors)}`)
    const coatOfArms = parsed.coatOfArms
    const patternEntry = asset(manifest, coatOfArms.pattern, ['pattern'])
    const surfaceEntry = manifest.assets.find((entry) => entry.kind === 'surface_mask')
    if (!surfaceEntry) throw new Error('missing surface mask')
    const coloredEntries = new Map<string, WebAssetPackEntry>()
    for (const emblem of coatOfArms.coloredEmblems) {
      coloredEntries.set(
        emblem.texture,
        asset(manifest, emblem.texture, ['colored_emblem', 'auxiliary_colored_emblem']),
      )
    }
    const coloredEmblems = Object.fromEntries(await Promise.all(
      [...coloredEntries].map(async ([name, entry]) => [name, await decode(entry)] as const),
    ))
    const assets = {
      pattern: await decode(patternEntry),
      surfaceMask: await decode(surfaceEntry),
      coloredEmblems,
    }
    const caseOutput = resolve(outputRoot, caseId)
    await mkdir(caseOutput, { recursive: true })
    for (const candidate of candidates) {
      const candidateCoatOfArms = structuredClone(coatOfArms)
      if (candidate.rotationQuantization) {
        for (const emblem of candidateCoatOfArms.coloredEmblems) {
          for (const instance of emblem.instances) {
            instance.rotation = candidate.rotationQuantization === 'truncate'
              ? Math.trunc(instance.rotation)
              : Math.round(instance.rotation)
          }
        }
      }
      const rendered = renderCoatOfArms(
        candidateCoatOfArms,
        assets,
        manifest.named_colors,
        230,
        candidate.options,
      )
      if (!rendered) throw new Error(`${caseId}/${candidate.id} did not render`)
      const pngBase64 = await page.evaluate(({ width, height, pixels }) => {
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const context = canvas.getContext('2d')
        if (!context) throw new Error('missing canvas context')
        const image = context.createImageData(width, height)
        image.data.set(pixels)
        context.putImageData(image, 0, 0)
        return canvas.toDataURL('image/png').slice('data:image/png;base64,'.length)
      }, {
        width: rendered.width,
        height: rendered.height,
        pixels: Array.from(rendered.pixels),
      })
      await writeFile(resolve(caseOutput, `${candidate.id}.png`), Buffer.from(pngBase64, 'base64'))
    }
  }
})
