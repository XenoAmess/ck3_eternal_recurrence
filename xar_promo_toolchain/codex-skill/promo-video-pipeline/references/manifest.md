# Project Config and Native Manifest

The native `promo-project.json` expresses checked-in project intent. Each `runs/<run-id>/run-manifest.json` binds the exact config bytes and records evidence for one attempt. Keep those responsibilities separate.

## Project config

The native project config identifies:

- project identity;
- the capture/render adapter ID and style preset ID;
- narration and subtitle locales;
- project constraints;
- chapters, cues, and their planned/ready state.

Adapter-specific detail can live in checked-in project files interpreted by that adapter. Keep voice, visual layout, capture behavior, and audit thresholds out of the Skill. Secrets and machine-local credentials do not belong in either native document.

## Run manifest

`xar-promo init` creates an initial `<project>/runs/<run-id>/run-manifest.json`; `xar-promo start-run` creates later attempts. Each run preserves the selected ProjectConfig bytes at `artifacts/project-config/sha256/<prefix>/<SHA256>.json` and binds that snapshot by relative path, byte count, and SHA-256. Later checked-in config edits do not change old runs. Relative artifact paths resolve from the run directory and use portable `/` separators. Its native v1 roots are:

- `format_version` and `kind=xar_promo_run_manifest`;
- `run` and `project_config` binding;
- `artifact_policy`;
- append-only `phase_history`;
- `artifacts`;
- append-only `audits`;
- ordered, append-only `signoffs`.

Artifacts record ID, collection (`raw` or `derived`), semantic role, relative stored path, label, byte count, SHA-256, and optional media type/source name. Typed phase records identify the phase, UTC time, status, optional detail, and zero or more exact artifact bindings; a read-only or validation-only phase may honestly have no artifacts. Typed automated-audit records bind a check result to exact subject and report artifact bytes. Signoffs separately record the artifact ID plus its exact byte/hash binding, reviewer, `approved` or `rejected`, timestamp, and optional note. Missing audit or review evidence remains missing; an empty record is never success.

`plan` reads either native document without mutating it. `build` requires a native run, executes the project composer, preserves completed and failure material, and appends typed phase facts. `audit` requires a native run and preserved subject; it preserves evidence and its generated report, then appends a typed automated result without reading or creating approval. `review` accepts only a v1 `xar-promo-bound-media-probe` envelope bound to the exact deliverable bytes and creates files outside the manifest boundary, so explicitly preserve that probe, its live ffprobe command audit, frame samples, template, package, and review process audit files afterward. `export` reads a release-ready run and creates a separate offline bundle without mutating the run.

## Artifact retention

Treat raw recordings, scripts, narration audio, subtitle sources, intermediate encodes, thumbnails, frame samples, review packages, audit evidence/reports, command logs, partials, and failed outputs as retained process artifacts. `preserve` stores them under the run's `artifacts/<raw|derived>/sha256/<prefix>/<SHA256><suffix>` and does not alter their source files. Before every run-manifest mutation, the CLI retains the previous run-manifest bytes in that run's `artifacts/manifest-history`.

Artifact IDs are immutable bindings. Reusing an ID for different bytes is an error; create a new generation-specific ID. Stored content-addressed bytes are reused only when identical.

## Validation profiles

`authoring` validates a native config, native run manifest, or read-only legacy structure and, unless `--structure-only` is explicit, every referenced file's existence, byte count, config binding, and hash. `release` requires a native run manifest, at least one chapter, all chapters ready, at least one `deliverable` artifact, and an explicit latest approval for at least one deliverable.

Legacy showcase/promo manifests are validate-only. `preserve`, `build`, `audit`, and `signoff` require a native run manifest and never rewrite legacy JSON; `export` likewise requires a native release-ready run.
