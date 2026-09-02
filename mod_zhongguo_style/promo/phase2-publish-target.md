# Phase-two final-video publication target

## Current state: `publish_target_pending`

The 2026-09-02 handover and the phase-two promo documents do not name an
external video platform, publishing account, credential reference, or owner
authorization for the final video. Therefore the planner must not infer a
destination and must not upload anything.

The existing paths have narrower meanings:

- `Z:\ck3_mod_rewrite_process_assets\zg361\promo\...` and
  `artifacts/demos/YYYY-MM-DD/` are local large-media/evidence conventions.
- `xar-promo export` creates an offline `xar_promo_release_bundle`; its manifest
  records `network_used=false` and `publish_performed=false`. The tool has no
  publish/upload command.
- Steam Workshop item `3784706360` distributes the main mod. The ZhongGuo
  Workshop media procedure authorizes eight static images for the Steam media
  strip and explicitly treats the final video as separate work. It is not an
  authorization to publish the video to that item or any other service.

## Explicit authority input

After the project owner selects the real destination, create an external JSON
authority receipt and pass it to the planner with
`--publish-target-authority <authority.json>`. Do not store secret material in
the JSON. The validate-only adapter
`tools/zhongguo_phase2_publish_target.py` requires:

- `schema_version=1`, `kind=zg361_phase2_publish_target_authority`;
- explicit `target_id`, `platform`, `account_id`, and non-placeholder HTTPS
  `locator_prefix`;
- `authorization.upload_authorized=true`, with named `approved_by` and a
  timezone-qualified `approved_at`;
- an opaque `credentials.reference`, plus operator-attested
  `availability_verified=true` and `verified_at` (never the credential itself);
- a fixed publication receipt contract: schema 1,
  `kind=zg361_phase2_publish_receipt`, and
  `remote_verification_required=true`.

Validation only reads and hashes that file. It does not resolve the credential,
contact the platform, create output directories, or upload media. Until all
fields are present and valid, the target gate remains typed
`publish_target_pending`.

## Publication receipt

The external operator action is outside the repository tools. After an
authorized upload, its receipt must bind the same `target_id`, `platform`,
`account_id`, candidate/exported media bytes and SHA-256, offline export
manifest bytes and SHA-256, and the authority receipt SHA-256. It must include a timezone-qualified publication
timestamp, `remote_verified=true`, and a real HTTPS locator under the authorized
prefix. The final completion gate remains pending if either the authority or
this receipt is absent or mismatched.
