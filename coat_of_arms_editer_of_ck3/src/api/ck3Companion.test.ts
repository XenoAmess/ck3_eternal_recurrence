import { afterEach, describe, expect, it, vi } from 'vitest'
import { CompanionRequestError, createCk3CompanionClient } from './ck3Companion'

afterEach(() => vi.unstubAllGlobals())

describe('CK3 companion client', () => {
  it('encodes catalog filters and preserves the structured response', async () => {
    const payload = { schema: 'ck3-coat-of-arms-resource-catalog-v1', items: [] }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient('http://127.0.0.1:9090/').resources({
      kind: 'colored_emblem',
      query: 'lion rampant',
      limit: 200,
    })

    expect(result).toEqual(payload)
    const requestUrl = new URL(fetchMock.mock.calls[0][0])
    expect(requestUrl.origin).toBe('http://127.0.0.1:9090')
    expect(requestUrl.pathname).toBe('/api/ck3/coat-of-arms/resources')
    expect(requestUrl.searchParams.get('kind')).toBe('colored_emblem')
    expect(requestUrl.searchParams.get('query')).toBe('lion rampant')
    expect(requestUrl.searchParams.get('limit')).toBe('200')
  })

  it('sends typed probe and export bodies', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'detected' }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'exported', source: 'coa={}' }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    const client = createCk3CompanionClient('http://localhost:8080')

    await client.probe('coa={}', 7, true)
    await client.exportSource(8)

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      source: 'coa={}', expectedRevision: 7, apply: true,
    })
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ expectedRevision: 8 })
  })

  it('opens the native CoA page through the closed zero-input route', async () => {
    const payload = {
      status: 'verified',
      action: 'open_coat_of_arms_designer',
      postcondition_verified: true,
      after: { route: 'coat_of_arms_designer' },
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(
      JSON.stringify(payload),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient().openNativeDesigner()

    expect(result).toEqual(payload)
    expect(new URL(fetchMock.mock.calls[0][0]).pathname)
      .toBe('/api/ck3/coat-of-arms/open-native-designer')
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({})
  })

  it('commits the native dynasty coat of arms through a zero-input POST', async () => {
    const payload = {
      status: 'verified',
      action: 'commit_dynasty_coat_of_arms',
      postcondition_verified: true,
      after: { route: 'ruler_designer' },
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(
      JSON.stringify(payload),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient().commitNativeDesign()

    expect(result).toEqual(payload)
    expect(new URL(fetchMock.mock.calls[0][0]).pathname)
      .toBe('/api/ck3/coat-of-arms/commit-native-design')
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({})
  })

  it('reads the exact CoA source binding independently of gameplay snapshots', async () => {
    const payload = {
      schema: 'coat-of-arms-source-binding-v1',
      schema_version: 1,
      status: 'bound',
      revision_source: 'frontend',
      revision: 0,
      connection_generation: 3,
      bridge_pid: 19424,
      game_version: '1.19.0.6',
      executable_sha256: '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86',
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(
      JSON.stringify(payload),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient().sourceBinding()

    expect(result).toEqual(payload)
    expect(new URL(fetchMock.mock.calls[0][0]).pathname)
      .toBe('/api/ck3/coat-of-arms/binding')
    expect(fetchMock.mock.calls[0][1].method).toBeUndefined()
  })

  it('encodes an exact manifest asset name', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      schema: 'ck3-coat-of-arms-resource-asset-v1',
      asset_base64: 'RERTIA==',
    }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await createCk3CompanionClient('http://localhost:8080').asset(
      'colored_emblem',
      'ce lion&crown.dds',
    )

    const requestUrl = new URL(fetchMock.mock.calls[0][0])
    expect(requestUrl.searchParams.get('kind')).toBe('colored_emblem')
    expect(requestUrl.searchParams.get('name')).toBe('ce lion&crown.dds')
  })

  it('reads shader-grounded render support from its dedicated endpoint', async () => {
    const payload = { schema: 'ck3-coat-of-arms-render-support-v1', named_colors: [] }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient('http://localhost:8080').renderSupport()

    expect(result).toEqual(payload)
    expect(new URL(fetchMock.mock.calls[0][0]).pathname)
      .toBe('/api/ck3/coat-of-arms/render-support')
  })

  it('reads configured mods without treating them as engine-mounted', async () => {
    const payload = {
      schema: 'ck3-coat-of-arms-load-configuration-v1',
      enabled_mod_count: 2,
      provenance: { engine_mount_observed: false },
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient('http://localhost:8080')
      .loadConfiguration()

    expect(result).toEqual(payload)
    expect(new URL(fetchMock.mock.calls[0][0]).pathname)
      .toBe('/api/ck3/coat-of-arms/load-configuration')
  })

  it('reads installed DLC files without treating them as entitlement', async () => {
    const payload = {
      schema: 'ck3-coat-of-arms-installed-dlc-sources-v1',
      installed_descriptor_count: 29,
      dlc_with_coa_candidates: 0,
      provenance: { store_entitlement_observed: false },
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient('http://localhost:8080')
      .installedDlcSources()

    expect(result).toEqual(payload)
    expect(new URL(fetchMock.mock.calls[0][0]).pathname)
      .toBe('/api/ck3/coat-of-arms/dlc-sources')
  })

  it('binds runtime feature truth to the current snapshot revision', async () => {
    const payload = {
      schema: 'loaded-feature-manifest-v1',
      status: 'available',
      snapshot_revision: 31,
      effective_feature_flags: { native_count: 44, items: [] },
      script_dlc_keys: { enumerated_count: 29, keys: [] },
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createCk3CompanionClient('http://localhost:8080')
      .runtimeFeatures(7)

    expect(result).toEqual(payload)
    const requestUrl = new URL(fetchMock.mock.calls[0][0])
    expect(requestUrl.pathname).toBe('/api/ck3/coat-of-arms/runtime-features')
    expect(requestUrl.searchParams.get('expectedRevision')).toBe('7')
  })

  it('encodes configured candidate filters and opaque asset identities', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        schema: 'ck3-coat-of-arms-configured-resource-catalog-v1',
        items: [],
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        schema: 'ck3-coat-of-arms-configured-resource-asset-v1',
        asset_base64: 'RERTIA==',
      }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    const client = createCk3CompanionClient('http://localhost:8080')

    await client.configuredResources({
      kind: 'colored_emblem', query: 'lion & crown', limit: 25,
    })
    await client.configuredAsset('colored_emblem', 'A'.repeat(64))

    const catalogUrl = new URL(fetchMock.mock.calls[0][0])
    const assetUrl = new URL(fetchMock.mock.calls[1][0])
    expect(catalogUrl.pathname).toBe('/api/ck3/coat-of-arms/configured-resources')
    expect(catalogUrl.searchParams.get('query')).toBe('lion & crown')
    expect(catalogUrl.searchParams.get('limit')).toBe('25')
    expect(assetUrl.pathname).toBe('/api/ck3/coat-of-arms/configured-asset')
    expect(assetUrl.searchParams.get('candidateId')).toBe('A'.repeat(64))
  })

  it('surfaces the companion error message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ message: 'CK3 bridge is unavailable' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } },
    )))

    await expect(createCk3CompanionClient().session()).rejects.toEqual(
      new CompanionRequestError('CK3 bridge is unavailable', 503),
    )
  })
})
