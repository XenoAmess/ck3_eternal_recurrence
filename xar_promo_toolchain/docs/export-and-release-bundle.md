# Export and release-bundle contract

`xar_promo.export_commands` is the offline programmatic boundary between an
approved native run and a local release bundle. The same handler is exposed by
the real `xar-promo export` CLI command.

The handler does not render media, inspect visual content, create a sign-off,
publish to Steam or YouTube, or make a network request. It copies only the
files named by the caller's policy into a new directory and writes a
byte/SHA-256 manifest for that exact allowlist.

## Programmatic entry point

The CLI mapping is:

```powershell
xar-promo export runs/release-001/run-manifest.json dist/release-001 `
  --policy release-export-policy.json `
  --validate-only
```

Replace `--validate-only` with `--dry-run` for the separately named no-write
preflight, or omit both flags to create the local bundle. The two flags are
mutually exclusive. JSON is written to stdout on exit `0` and stderr on exit
`2`.

The equivalent programmatic entry point is:

```python
from pathlib import Path

from xar_promo.export_commands import handle_export_command

result = handle_export_command(
    Path("runs/release-001/run-manifest.json"),
    Path("dist/release-001"),
    Path("release-export-policy.json"),
    validate_only=True,
)

print(result.to_dict())
raise SystemExit(result.exit_code)
```

The stable signature is:

```python
handle_export_command(
    run_manifest: Path,
    destination: Path,
    policy_file: Path,
    *,
    dry_run: bool = False,
    validate_only: bool = False,
) -> ExportCommandResult
```

`dry_run` and `validate_only` are mutually exclusive. Both run the same
policy, release-profile, hash, role, and selected-deliverable checks. Neither
mode calls the exporter or creates the destination directory or its parent.
The distinct mode name lets an integrating CLI preserve the caller's intent.

With both flags false, the handler repeats the same preflight and then calls
`xar_promo.export.export_release_bundle`. The exporter stages copies in a
temporary sibling directory, verifies every copied byte count and SHA-256,
writes `release-bundle-manifest.json`, and renames the completed staging
directory to the requested destination. An existing destination is always a
failure; it is never merged, emptied, or overwritten.

The lower-level library functions remain available when a command-style result
is not needed:

```python
from pathlib import Path

from xar_promo.export import export_release_bundle, verify_release_bundle
from xar_promo.export_commands import load_export_policy

policy = load_export_policy(Path("release-export-policy.json"))
manifest = export_release_bundle(
    Path("runs/release-001/run-manifest.json"),
    Path("dist/release-001"),
    policy=policy,
)
verify_release_bundle(Path("dist/release-001"))
```

## Release and approval prerequisites

The input must be a native v1 `RunManifest`, not a legacy showcase manifest or
a standalone `ProjectConfig`. Before export, the implementation loads the run
with file checking enabled and applies the core `release` validation profile.
Consequently:

1. the run's exact project-config snapshot must still match its byte count and
   SHA-256 binding;
2. every preserved run artifact must still exist with its recorded bytes and
   SHA-256;
3. the bound project config must contain at least one chapter, and every
   chapter must be `ready`;
4. the run must contain at least one `role="deliverable"` artifact with an
   explicit latest human sign-off of `approved`;
5. the policy-selected deliverable itself—not merely another deliverable in
   the run—must have `role="deliverable"` and its own latest explicit
   `approved` sign-off.

The exporter never manufactures approval and never calls `record_signoff`.
An audit artifact in the allowlist is copied as an artifact; its presence does
not make the audit pass and does not substitute for the selected deliverable's
human approval. Content review, project-specific release gates, and upload
authorization remain the caller's responsibility.

## Policy JSON v1

The policy is intentionally strict. The root has exactly these fields:

```json
{
  "format_version": 1,
  "kind": "xar_promo_release_export_policy",
  "items": []
}
```

Unknown root or item fields are rejected. There are no credential, URL,
account, publication, executable, shell-command, or upload fields.

### Preserved artifact item

An artifact item has exactly five fields:

```json
{
  "category": "deliverable",
  "destination": "video/promo-final.mp4",
  "source_kind": "artifact",
  "artifact_id": "promo-final",
  "expected_role": "deliverable"
}
```

- `category` is one of `deliverable`, `subtitle`, `thumbnail`, `sidecar`, or
  `audit`.
- `destination` is normalized to a portable relative path inside the new
  bundle. Backslashes, absolute or drive-qualified paths, and parent (`..`)
  components are rejected; redundant current-directory components are
  normalized away. The result cannot equal the reserved
  `release-bundle-manifest.json` name.
- `source_kind` is exactly `artifact`.
- `artifact_id` is the exact ID already present in `run.artifacts`.
- `expected_role` is the exact role the caller requires that artifact to have.

Neither `artifact_id` nor `expected_role` is inferred from category, filename,
extension, media type, chapter reference, or the fact that only one candidate
exists.

### Project-config snapshot item

The config snapshot is the only non-artifact source kind. Its item has exactly
three fields:

```json
{
  "category": "project-config",
  "destination": "metadata/project-config.json",
  "source_kind": "project-config-snapshot"
}
```

It copies the immutable snapshot already bound by `run.project_config`; it does
not copy the possibly newer checked-in authoring config. This item cannot have
`artifact_id` or `expected_role`.

The complete policy must select exactly one `deliverable`, at most one
`thumbnail`, and at most one project-config snapshot. Artifact IDs and
case-insensitive destination paths must be unique. Multiple independently
preserved subtitle, sidecar, or audit artifacts may be selected. Items are
sorted by destination before export so policy input order cannot change the
bundle manifest.

A minimal illustrative policy is checked in at
[`examples/minimal/release-export-policy.example.json`](../examples/minimal/release-export-policy.example.json).
It names the future `promo-final` artifact explicitly. The minimal example has
no completed run checked in, so that policy is a contract example, not a claim
that a release bundle can already be exported. It becomes runnable only after
the named deliverable has been preserved into a release-ready run and a human
has explicitly approved those exact bytes.

## Structured result and exit semantics

`ExportCommandResult.exit_code` is always `0` or `2`:

- `0` / `GREEN`: policy and release preflight passed; in `export` mode the
  bundle was created, while in `dry-run` or `validate-only` it was not created.
- `2` / `RED`: invalid policy, stale or missing bytes, non-release-ready run,
  unapproved selected deliverable, role mismatch, existing destination, or
  mutually exclusive flags.

`ExportCommandResult.to_dict()` returns these fields:

- `exit_code`: `0` or `2`;
- `status`: `GREEN` or `RED`;
- `mode`: `export`, `dry-run`, `validate-only`, or `invalid`;
- `run_manifest`, `destination`, `policy_file`: resolved command inputs;
- `release_validated`: whether the native release-profile check completed;
- `exported`: true only after normal export completed;
- `network_used`: always false;
- `publish_performed`: always false;
- `selected_files`: the normalized explicit policy entries;
- `manifest`: present only after a successful real export;
- `error`: present on a `RED` result.

The handler returns user/input failures as structured results instead of
raising them. Programming errors are not reclassified as successful command
results.

## Bundle contents and verification

The bundle contains only allowlisted copies plus
`release-bundle-manifest.json`. The manifest records:

- `format_version` and `kind` (`xar_promo_release_bundle`);
- the source run ID, run-manifest bytes/SHA-256, and bound config SHA-256;
- `network_used=false`, `publish_performed=false`, and
  `source_material_mutated=false`;
- for each copied file: category, bundle-relative path, bytes, SHA-256, and the
  originating run artifact identity/role or project-config snapshot identity.

`verify_release_bundle` recomputes every copied file binding and rejects both
missing files and files not present in the manifest allowlist. Export does not
move, edit, or delete the source artifact, run manifest, config snapshot,
failed attempts, raw captures, or other process material. Omitted run
artifacts stay in the run and simply are not copied to this bundle.

The result is a local, reviewable release bundle. It is not evidence that any
workshop, video platform, repository release, or other external destination
was contacted or updated.
