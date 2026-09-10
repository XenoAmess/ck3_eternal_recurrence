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
    probe: (source: string, expectedRevision: number, apply = false) =>
      post<CoatOfArmsProbeResult>('/probe', { source, expectedRevision, apply }),
    exportSource: (expectedRevision: number) =>
      post<CoatOfArmsExportResult>('/export', { expectedRevision }),
  }
}
