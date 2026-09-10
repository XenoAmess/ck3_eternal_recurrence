export type CoatOfArmsResourceKind = 'pattern' | 'colored_emblem' | 'color'

export interface CoatOfArmsResourceItem {
  index: number
  name: string
  colors: number | null
  visible: boolean
  category: string | null
  relative_path: string | null
  asset_exists: boolean
  asset_bytes: number | null
  asset_sha256: string | null
}

export interface CoatOfArmsResourceCatalog {
  schema: 'ck3-coat-of-arms-resource-catalog-v1'
  schema_version: 1
  status: 'indexed'
  ck3_build: string
  kind: CoatOfArmsResourceKind
  query: string | null
  visible_only: boolean
  offset: number
  limit: number
  total: number
  returned: number
  has_more: boolean
  next_offset: number | null
  items: CoatOfArmsResourceItem[]
  provenance: {
    mode: string
    executable_sha256: string
    manifest_relative_path: string
    manifest_bytes: number
    manifest_sha256: string
    engine_registration_observed: false
    dlc_and_mod_overrides_included: false
  }
}

export interface CoatOfArmsResourceAsset {
  schema: 'ck3-coat-of-arms-resource-asset-v1'
  schema_version: 1
  status: 'read'
  ck3_build: string
  kind: Exclude<CoatOfArmsResourceKind, 'color'>
  name: string
  colors: number
  visible: boolean
  category: string | null
  relative_path: string
  content_type: 'application/octet-stream'
  asset_bytes: number
  asset_sha256: string
  asset_base64: string
  dds: {
    width: number
    height: number
    mipmap_count: number
    four_cc: string
    format: string
  }
}

export interface CoatOfArmsNamedColor {
  name: string
  model: 'rgb' | 'hsv' | 'hsv360'
  components: [number, number, number]
  rgb: [number, number, number]
  rgb_255: [number, number, number]
}

export interface CoatOfArmsRenderSupport {
  schema: 'ck3-coat-of-arms-render-support-v1'
  schema_version: 1
  status: 'read'
  ck3_build: string
  named_colors: CoatOfArmsNamedColor[]
  surface_mask: {
    relative_path: string
    content_type: 'application/octet-stream'
    asset_bytes: number
    asset_sha256: string
    asset_base64: string
    dds: {
      width: number
      height: number
      mipmap_count: number
      four_cc: string
      format: string
    }
  }
  textured_emblem_default: {
    relative_path: string
    content_type: 'application/octet-stream'
    asset_bytes: number
    asset_sha256: string
    asset_base64: string
    dds: {
      width: number
      height: number
      mipmap_count: number
      four_cc: string
      format: string
    }
  }
  render_contract: {
    overlay_function_body_available: boolean
    fallback_color_binding_available: boolean
    [key: string]: unknown
  }
  provenance: {
    mode: string
    executable_sha256: string
    limits: string[]
    [key: string]: unknown
  }
}

export interface CoatOfArmsLoadConfiguration {
  schema: 'ck3-coat-of-arms-load-configuration-v1'
  schema_version: 1
  status: 'configured'
  enabled_mod_count: number
  disabled_dlcs: string[]
  mods: Array<{
    load_order: number
    registry_path: string
    name: string | null
    content_kind: 'directory' | 'archive'
    coa_replace_paths: string[]
    resource_candidates: Record<string, {
      relative_directory: string
      directory_exists: boolean
      txt: string[]
      dds_count: number
    }>
  }>
  provenance: {
    mode: string
    load_configuration_sha256: string
    launcher_database_used: false
    engine_mount_observed: false
    resource_merge_applied: false
    archive_resource_enumeration_supported: false
    candidate_scan_depth: 'direct-files-only'
  }
}

export interface CoatOfArmsConfiguredResourceItem {
  index: number
  candidate_id: string
  load_order: number
  registry_path: string
  mod_name: string | null
  content_kind: 'directory' | 'archive'
  archive_bytes: number | null
  descriptor_sha256: string
  manifest_relative_path: string
  manifest_sha256: string
  kind: CoatOfArmsResourceKind
  name: string
  colors: number | null
  visible: boolean
  category: string | null
  asset_relative_path: string | null
  asset_exists: boolean | null
  asset_bytes: number | null
  asset_sha256: string | null
  same_name_configured_candidate_count: number
  potential_configured_name_conflict: boolean
}

export interface CoatOfArmsConfiguredResourceCatalog {
  schema: 'ck3-coat-of-arms-configured-resource-catalog-v1'
  schema_version: 1
  status: 'indexed'
  kind: CoatOfArmsResourceKind
  total: number
  returned: number
  has_more: boolean
  next_offset: number | null
  items: CoatOfArmsConfiguredResourceItem[]
  skipped_archives: Array<{
    load_order: number
    registry_path: string
    name: string | null
  }>
  archive_sources: Array<{
    load_order: number
    registry_path: string
    name: string | null
    archive_bytes: number
    member_count: number
    kind_manifest_count: number
  }>
  provenance: {
    mode: string
    enabled_mod_count: number
    configured_candidate_count: number
    archive_mods_skipped: number
    archive_mods_enumerated: number
    base_game_resources_included: false
    engine_registration_observed: false
    resource_merge_applied: false
    load_order_precedence_applied: false
  }
}

export interface CoatOfArmsConfiguredResourceAsset {
  schema: 'ck3-coat-of-arms-configured-resource-asset-v1'
  schema_version: 1
  status: 'read'
  kind: 'pattern' | 'colored_emblem'
  candidate_id: string
  name: string
  content_type: 'application/octet-stream'
  asset_bytes: number
  asset_sha256: string
  asset_base64: string
  dds: {
    width: number
    height: number
    mipmap_count: number
    four_cc: string
    format: string
  }
}

export interface Ck3SessionSnapshot {
  revision: number
  source?: string
  [key: string]: unknown
}

export interface CoatOfArmsProbeResult {
  status: 'detected' | 'applied' | 'not_detected' | 'apply_failed' | 'unavailable'
  detected: boolean
  applied: boolean
  reason?: string | null
  [key: string]: unknown
}

export interface CoatOfArmsExportResult {
  status: 'exported' | 'unavailable'
  source: string | null
  reason?: string | null
  [key: string]: unknown
}

export class CompanionRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'CompanionRequestError'
  }
}

function trimUrl(value: string): string {
  return value.replace(/\/+$/, '')
}

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null) as { message?: unknown } | null
  if (!response.ok) {
    const detail = typeof body?.message === 'string' ? body.message : response.statusText
    throw new CompanionRequestError(detail || 'CK3 companion request failed', response.status)
  }
  return body as T
}

export function createCk3CompanionClient(
  origin = import.meta.env.VITE_CK3_COMPANION_URL || 'http://localhost:8080',
) {
  const baseUrl = `${trimUrl(origin)}/api/ck3/coat-of-arms`

  async function get<T>(path: string): Promise<T> {
    return readJson<T>(await fetch(`${baseUrl}${path}`, {
      headers: { Accept: 'application/json' },
    }))
  }

  async function post<T>(path: string, body: unknown): Promise<T> {
    return readJson<T>(await fetch(`${baseUrl}${path}`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }))
  }

  return {
    session: () => get<Ck3SessionSnapshot>('/session'),
    resources: (parameters: {
      kind: CoatOfArmsResourceKind
      query?: string
      visibleOnly?: boolean
      offset?: number
      limit?: number
    }) => {
      const query = new URLSearchParams({
        kind: parameters.kind,
        visibleOnly: String(parameters.visibleOnly ?? true),
        offset: String(parameters.offset ?? 0),
        limit: String(parameters.limit ?? 50),
      })
      if (parameters.query) query.set('query', parameters.query)
      return get<CoatOfArmsResourceCatalog>(`/resources?${query}`)
    },
    asset: (kind: 'pattern' | 'colored_emblem', name: string) => {
      const query = new URLSearchParams({ kind, name })
      return get<CoatOfArmsResourceAsset>(`/asset?${query}`)
    },
    renderSupport: () => get<CoatOfArmsRenderSupport>('/render-support'),
    loadConfiguration: () =>
      get<CoatOfArmsLoadConfiguration>('/load-configuration'),
    configuredResources: (parameters: {
      kind: CoatOfArmsResourceKind
      query?: string
      visibleOnly?: boolean
      offset?: number
      limit?: number
    }) => {
      const query = new URLSearchParams({
        kind: parameters.kind,
        visibleOnly: String(parameters.visibleOnly ?? true),
        offset: String(parameters.offset ?? 0),
        limit: String(parameters.limit ?? 50),
      })
      if (parameters.query) query.set('query', parameters.query)
      return get<CoatOfArmsConfiguredResourceCatalog>(`/configured-resources?${query}`)
    },
    configuredAsset: (
      kind: 'pattern' | 'colored_emblem',
      candidateId: string,
    ) => {
      const query = new URLSearchParams({ kind, candidateId })
      return get<CoatOfArmsConfiguredResourceAsset>(`/configured-asset?${query}`)
    },
    probe: (source: string, expectedRevision: number, apply = false) =>
      post<CoatOfArmsProbeResult>('/probe', { source, expectedRevision, apply }),
    exportSource: (expectedRevision: number) =>
      post<CoatOfArmsExportResult>('/export', { expectedRevision }),
  }
}
