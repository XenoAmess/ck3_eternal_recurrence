import { createHash } from 'node:crypto'

interface SyntheticAssetPackEntry {
  kind: string
  name: string
  asset_sha256: string
  source_relative_path?: string
}

export function syntheticBaseVfsReceipt(
  assets: readonly SyntheticAssetPackEntry[],
  sourceIdentitySha256: string,
) {
  const winnerSetBytes = `${assets.map((asset) => [
    asset.kind,
    asset.name,
    asset.asset_sha256,
    asset.source_relative_path ?? `legacy/${asset.name}`,
  ].join('\0')).join('\n')}\n`
  const winnerSetSha256 = createHash('sha256')
    .update(winnerSetBytes, 'utf8')
    .digest('hex')
    .toUpperCase()

  return {
    schema: 'ck3-coa-vfs-receipt-v1',
    scope: 'base_game_only',
    resolution_policy: 'single_source_no_conflicts',
    load_configuration_sha256: null,
    winner_set_sha256: winnerSetSha256,
    resolved_asset_count: assets.length,
    conflict_count: 0,
    sources: [{
      source_id: 'synthetic-base',
      source_kind: 'base_game',
      precedence_order: 0,
      source_identity_sha256: sourceIdentitySha256,
    }],
    native_precedence_evidence: {
      status: 'unverified',
      evidence_id: null,
      direct_path_winner_rule: 'unverified',
      scope: 'synthetic browser fixture only',
      uncovered: ['all native VFS behavior'],
    },
  }
}
