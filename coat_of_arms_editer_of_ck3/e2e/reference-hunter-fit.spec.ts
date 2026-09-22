import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'
import { coatOfArmsDocumentStats } from '../src/domain/documentStats'
import { parseCoatOfArms } from '../src/domain/parser'
import { serializeCoatOfArms } from '../src/domain/serializer'

const layerBudget = '1024'
const fixture = resolve('test-fixtures/xenoamess_hunter_1024_no_shade.png')
const originalFixture = resolve('test-fixtures/xenoamess_hunter_4096_no_shade.svg')
const artifactDirectory = resolve('test-results/reference-hunter-v8-pareto-candidates')
const assetPackDirectory = resolve('public/asset-packs/ck3-1.19.0.6')
const historicalArtifact = resolve('../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v4-pruned/coat_of_arms.txt')
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

test('improves hunter edges with bounded local refinement under a 1024-layer ceiling', async ({ page }) => {
  test.setTimeout(5 * 60 * 1000)
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: async (text: string) => {
          Object.assign(window, { __coaClipboardPayload: text })
        },
      },
    })
  })
  await page.goto('/')
  await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })
  await page.locator('.fit-budget input').fill(layerBudget)
  await page.locator('.image-drop input').setInputFiles(fixture)
  await page.getByRole('button', { name: '开始本地拟合' }).click()
  await expect(page.getByText(/完成 · .*从完整库评估 \d+ 个构图/)).toBeVisible({ timeout: 4 * 60 * 1000 })
  await expect(page.locator('.fit-report')).toContainText(new RegExp(`用户预算\\s*${layerBudget} 个绘制实例`))

  await mkdir(artifactDirectory, { recursive: true })
  await copyFile(fixture, resolve(artifactDirectory, 'target.png'))
  await page.getByRole('button', { name: '复制 CK3 代码' }).click()
  const source = await page.evaluate(() => (
    (window as typeof window & { __coaClipboardPayload?: string }).__coaClipboardPayload ?? ''
  ))
  const reportText = await page.locator('.fit-report').innerText()
  const evidenceText = await page.locator('.fit-report').getAttribute('data-fit-evidence')
  if (!evidenceText) throw new Error('missing machine-readable fit evidence')
  const evidence = JSON.parse(evidenceText)
  const candidateCards = page.getByTestId('candidate-comparison').locator('.candidate-card')
  const paretoCandidateCount = await candidateCards.count()
  expect(paretoCandidateCount).toBeGreaterThanOrEqual(1)
  expect(paretoCandidateCount).toBeLessThanOrEqual(3)
  expect(evidence.paretoCandidates).toHaveLength(paretoCandidateCount)
  const paretoCandidates = []
  for (let index = 0; index < paretoCandidateCount; index += 1) {
    const card = candidateCards.nth(index)
    await card.getByRole('button', { name: '复制候选代码' }).click()
    const candidateSource = await page.evaluate(() => (
      (window as typeof window & { __coaClipboardPayload?: string }).__coaClipboardPayload ?? ''
    ))
    const candidateParsed = parseCoatOfArms(candidateSource)
    const candidateErrors = candidateParsed.diagnostics.filter((item) => item.severity === 'error')
    const candidateInstances = candidateParsed.coatOfArms.coloredEmblems.reduce(
      (total, emblem) => total + emblem.instances.length,
      0,
    )
    expect(candidateErrors).toEqual([])
    expect(serializeCoatOfArms(candidateParsed.coatOfArms)).toBe(candidateSource)
    expect(evidence.paretoCandidates[index].stats.drawnInstances).toBe(candidateInstances)
    await writeFile(
      resolve(artifactDirectory, `pareto-candidate-${String(index + 1).padStart(2, '0')}.txt`),
      candidateSource,
      'utf8',
    )
    const candidatePreview = await card.locator('.candidate-shield-preview').getAttribute('src')
    if (!candidatePreview?.startsWith('data:image/png;base64,')) {
      throw new Error(`missing Pareto candidate ${index + 1} preview`)
    }
    const previewFile = `pareto-candidate-${String(index + 1).padStart(2, '0')}.png`
    await writeFile(
      resolve(artifactDirectory, previewFile),
      Buffer.from(candidatePreview.slice('data:image/png;base64,'.length), 'base64'),
    )
    paretoCandidates.push({
      index: index + 1,
      sourceFile: `pareto-candidate-${String(index + 1).padStart(2, '0')}.txt`,
      previewFile,
      sourceSha256: sha256(candidateSource),
      parseErrors: candidateErrors.length,
      drawnInstances: candidateInstances,
      ...evidence.paretoCandidates[index],
    })
  }
  for (const candidate of paretoCandidates) {
    expect(paretoCandidates.some((other) => (
      other !== candidate
      && other.metrics.totalLoss <= candidate.metrics.totalLoss
      && other.metrics.edgeLoss <= candidate.metrics.edgeLoss
      && other.drawnInstances <= candidate.drawnInstances
      && (
        other.metrics.totalLoss < candidate.metrics.totalLoss
        || other.metrics.edgeLoss < candidate.metrics.edgeLoss
        || other.drawnInstances < candidate.drawnInstances
      )
    ))).toBe(false)
  }
  const drawnInstances = Number(reportText.match(/实际绘制实例\s+(\d+)/)?.[1])
  const logicalLayers = Number(reportText.match(/逻辑图层\s+(\d+)/)?.[1])
  const coloredEmblemBlocks = Number(reportText.match(/colored_emblem 块\s+(\d+)/)?.[1])
  const instanceCount = Number(reportText.match(/instance 数\s+(\d+)/)?.[1])
  const outputBytes = Buffer.byteLength(source, 'utf8')
  const parsed = parseCoatOfArms(source)
  const outputLines = coatOfArmsDocumentStats(parsed.coatOfArms, source).lines
  const parseErrors = parsed.diagnostics.filter((item) => item.severity === 'error')
  const reparsedInstances = parsed.coatOfArms.coloredEmblems.reduce(
    (total, emblem) => total + emblem.instances.length,
    0,
  )
  expect(drawnInstances).toBeGreaterThanOrEqual(900)
  expect(drawnInstances).toBeLessThanOrEqual(1024)
  expect(coloredEmblemBlocks).toBe(drawnInstances)
  expect(instanceCount).toBe(drawnInstances)
  expect(logicalLayers).toBe(coloredEmblemBlocks)
  expect(source.match(/colored_emblem\s*=/g)).toHaveLength(coloredEmblemBlocks)
  expect(source.match(/instance\s*=/g)).toHaveLength(instanceCount)
  expect(parseErrors).toEqual([])
  expect(parsed.coatOfArms.coloredEmblems).toHaveLength(coloredEmblemBlocks)
  expect(reparsedInstances).toBe(instanceCount)
  expect(serializeCoatOfArms(parsed.coatOfArms)).toBe(source)
  expect(evidence.provenance.layerBudget).toBe(1024)
  expect(evidence.provenance.algorithm).toBe('ck3-coa-browser-fit-v13-epsilon-direct-multiscale')
  expect(evidence.provenance.sourceWidth).toBe(1024)
  expect(evidence.provenance.sourceHeight).toBe(1024)
  expect(evidence.provenance.pyramidResolutions).toEqual([96, 192, 230, 256, 512])
  expect(evidence.provenance.searchBackend).toBe('webgl2-batch+cpu-reference')
  expect(evidence.provenance.batchSearch).toMatchObject({
    backend: 'webgl2-texture-array-reduction-float-v1',
    status: 'active',
    cpuReferenceAgreement: true,
  })
  expect(evidence.provenance.batchSearch.batches).toBeGreaterThanOrEqual(3)
  expect(evidence.provenance.batchSearch.candidates).toBeGreaterThan(300)
  expect(evidence.provenance.batchSearch.maximumMetricDelta).toBeLessThanOrEqual(2e-6)
  expect(evidence.provenance.candidateLosses.map((item: { mode: string }) => item.mode)).toEqual(
    expect.arrayContaining(['semantic-search', 'native-tile-paint', 'native-edge-refined', 'hybrid-native-paint']),
  )
  const pureTileCandidate = evidence.provenance.candidateLosses.find(
    (item: { mode: string }) => item.mode === 'native-tile-paint',
  )
  const edgeRefinedCandidate = evidence.provenance.candidateLosses.find(
    (item: { mode: string }) => item.mode === 'native-edge-refined',
  )
  expect(evidence.provenance.reconstructionMode).toBe('native-edge-refined')
  expect(edgeRefinedCandidate.totalLoss).toBeLessThan(pureTileCandidate.totalLoss)
  expect(edgeRefinedCandidate.edgeLoss).toBeLessThan(pureTileCandidate.edgeLoss)
  expect(evidence.provenance.drawnInstances).toBe(drawnInstances)
  expect(evidence.provenance.nativeTileSeamValidation.status).toBe('passed')
  expect(evidence.provenance.nativeTileSeamValidation.metrics).toEqual(
    [96, 230, 512].map((resolution) => ({
      resolution,
      backgroundLeakPixels: 0,
      maximumLeakAmount: 0,
      peakRowLeakPixels: 0,
      peakColumnLeakPixels: 0,
    })),
  )
  expect(evidence.layerLossSummary).toMatchObject({
    count: drawnInstances + 1,
    strictlyDecreasing: true,
  })
  const historicalSource = await readFile(historicalArtifact, 'utf8')
  const historicalMetrics = await page.evaluate(async ({ source: v3Source }) => {
    const dynamicImport = (path: string) => import(/* @vite-ignore */ path)
    const [parserModule, rendererModule, ddsModule, inputModule, fitterModule] = await Promise.all([
      dynamicImport('/src/domain/parser.ts'),
      dynamicImport('/src/domain/renderer.ts'),
      dynamicImport('/src/domain/dds.ts'),
      dynamicImport('/src/domain/imageInput.ts'),
      dynamicImport('/src/domain/imageFitter.ts'),
    ])
    const targetResponse = await fetch('/test-fixtures/xenoamess_hunter_1024_no_shade.png')
    const targetFile = new File([await targetResponse.blob()], 'hunter.png', { type: 'image/png' })
    const target = (await inputModule.decodeFitImageFile(targetFile, 96)).image
    const manifest = await fetch('/asset-packs/ck3-1.19.0.6/manifest.json').then((response) => response.json())
    const parsedV3 = parserModule.parseCoatOfArms(v3Source).coatOfArms
    const loadTexture = async (kind: string, name: string) => {
      const entry = manifest.assets.find((item: { kind: string, name: string }) => (
        item.kind === kind && item.name === name
      ))
      if (!entry) throw new Error(`missing ${kind}/${name} in exact asset pack`)
      const bytes = await fetch(`/asset-packs/ck3-1.19.0.6/${entry.url}`)
        .then((response) => response.arrayBuffer())
      return ddsModule.decodeDds(new Uint8Array(bytes))
    }
    const pattern = await loadTexture('pattern', parsedV3.pattern)
    const emblemNames = [...new Set(parsedV3.coloredEmblems.map(
      (emblem: { texture: string }) => emblem.texture,
    ))] as string[]
    const coloredEmblems = Object.fromEntries(await Promise.all(emblemNames.map(async (name) => (
      [name, await loadTexture('colored_emblem', name)]
    ))))
    const surfaceMask = await loadTexture('surface_mask', 'coa_mask_texture.dds')
    const rendered = rendererModule.renderCoatOfArms(
      parsedV3,
      { pattern, coloredEmblems, surfaceMask },
      manifest.named_colors ?? {},
      96,
    )
    if (!rendered) throw new Error('historical v3 render failed')
    return fitterModule.measureImageFitLosses(target, rendered)
  }, { source: historicalSource })
  expect(evidence.metrics.totalLoss).toBeLessThanOrEqual(historicalMetrics.totalLoss + 1e-12)
  expect(evidence.metrics.edgeLoss).toBeLessThan(historicalMetrics.edgeLoss - 1e-12)
  expect(evidence.metrics.relativeImprovement).toBeGreaterThan(0.80)
  await writeFile(resolve(artifactDirectory, 'coat_of_arms.txt'), source, 'utf8')
  const preview = await page.getByAltText('图片拟合结果预览').getAttribute('src')
  if (!preview?.startsWith('data:image/png;base64,')) throw new Error('missing canonical fitted PNG preview')
  await writeFile(
    resolve(artifactDirectory, 'fitted-canonical-230.png'),
    Buffer.from(preview.slice('data:image/png;base64,'.length), 'base64'),
  )
  const shaderPreview = await page.locator('img.shader-preview').getAttribute('src')
  if (!shaderPreview?.startsWith('data:image/png;base64,')) throw new Error('missing shader PNG preview')
  await writeFile(
    resolve(artifactDirectory, 'fitted-shader-preview-230.png'),
    Buffer.from(shaderPreview.slice('data:image/png;base64,'.length), 'base64'),
  )
  const targetBytes = await readFile(fixture)
  const originalBytes = await readFile(originalFixture)
  const manifestBytes = await readFile(resolve(assetPackDirectory, 'manifest.json'))
  const manifest = JSON.parse(manifestBytes.toString('utf8'))
  const expectedManifestSha256 = (await readFile(resolve(assetPackDirectory, 'manifest.sha256'), 'utf8'))
    .trim().split(/\s+/)[0].toUpperCase()
  const repository = resolve('..')
  const headCommit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repository, encoding: 'utf8' }).trim()
  const workingTreePatch = execFileSync(
    'git',
    ['diff', '--binary', 'HEAD', '--', 'coat_of_arms_editer_of_ck3'],
    { cwd: repository },
  )
  const report = {
    schema: 'ck3-coa-hunter-fit-evidence-v1',
    artifactVersion: 'xenoamess-hunter-v8-pareto-candidates',
    predecessor: '../xenoamess-hunter-v7-budget-exhaustive-edge/',
    status: 'browser-quality-improvement-passed-native-roundtrip-pending',
    generatedAt: new Date().toISOString(),
    sourceRevision: {
      headCommit,
      workingTreePatchSha256: sha256(workingTreePatch),
    },
    input: {
      originalFile: 'xenoamess_hunter_4096_no_shade.svg',
      originalSha256: sha256(originalBytes),
      rasterFile: 'target.png',
      rasterSha256: sha256(targetBytes),
      originalResolution: [4096, 4096],
      rasterResolution: [1024, 1024],
    },
    assetPack: {
      packId: manifest.pack_id,
      manifestSha256: sha256(manifestBytes),
      expectedManifestSha256,
      manifestHashMatchesReceipt: sha256(manifestBytes) === expectedManifestSha256,
      sourceManifestSha256: manifest.source_manifest_sha256,
    },
    configuration: {
      userDrawInstanceBudget: 1024,
      searchResolution: 96,
      randomSeed: null,
      scoringContract: evidence.provenance.scoringContract,
      rendererContract: evidence.provenance.rendererContract,
      surfaceMaskApplied: evidence.provenance.surfaceMaskApplied,
      numericNoiseTolerance: 1e-12,
      historicalReportedPrecisionDecimals: 5,
      historicalReportedMaximumTotalLoss: 0.02590,
      historicalReportedMaximumEdgeLoss: 0.04304,
      historicalFixedThresholdStatus: 'not-directly-comparable-after-surface-mask-contract-correction',
      seamGate: {
        resolutions: [96, 230, 512],
        backgroundLeakPixels: 0,
        maximumPeriodicPeakPixels: 0,
      },
    },
    metrics: evidence.metrics,
    paretoCandidates,
    commonContractComparison: {
      baselineArtifact: '../xenoamess-hunter-v4-pruned/coat_of_arms.txt',
      baselineMetrics: historicalMetrics,
      candidateMetrics: evidence.metrics,
      tolerance: 1e-12,
      totalLossNonRegression: evidence.metrics.totalLoss <= historicalMetrics.totalLoss + 1e-12,
      edgeLossStrictImprovement: evidence.metrics.edgeLoss < historicalMetrics.edgeLoss - 1e-12,
    },
    counts: {
      userBudget: 1024,
      drawnInstances,
      logicalLayers,
      coloredEmblemBlocks,
      instances: instanceCount,
      utf8Bytes: outputBytes,
      lines: outputLines,
    },
    provenance: evidence.provenance,
    layerLossSummary: evidence.layerLossSummary,
    selectedAssetSha256: evidence.selectedAssetSha256,
    roundTrip: {
      parseErrors: parseErrors.length,
      serializeParseExact: true,
      sourceSha256: sha256(source),
      parsedColoredEmblemBlocks: parsed.coatOfArms.coloredEmblems.length,
      parsedInstances: reparsedInstances,
    },
    browserReportText: reportText,
    evidenceLevel: {
      browserRegression: 'passed',
      transferIntegrity: 'passed-for-browser-copy-interception-and-parse',
      ck3ApplyCopyRoundTrip: 'pending-for-v6-candidate',
      nativePixelComparison: 'pending-mcp-framebuffer-capability',
    },
  }
  await writeFile(resolve(artifactDirectory, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  await page.locator('.image-fit-grid').screenshot({ path: resolve(artifactDirectory, 'fit-report.png') })
  await page.locator('.preview-pane').screenshot({ path: resolve(artifactDirectory, 'preview-panel.png') })
})
