# CLI and manifest v1 contract

The checked-in config is `promo-project.json`. The initial append-only run is `runs/run-0001/run-manifest.json`. Relative artifact paths are resolved from the run directory and always use `/` separators.

Implemented commands:

- `init PROJECT_DIRECTORY`: creates a ProjectConfig and a bound initial RunManifest plus run-local artifact directories. It refuses to overwrite either document.
- `start-run [PROJECT_CONFIG] --run-id ID`: preserves the config's current exact bytes inside the new run and binds the run to that immutable snapshot. The default directory is `<project>/runs/<id>`; `--run-directory` selects another directory. Editing the checked-in config later does not invalidate old runs, and existing runs are never overwritten.
- `validate [MANIFEST]`: validates native v1 manifests and the repository's pre-extraction `format_version: 1` showcase/promo manifests. File existence and declared byte/hash bindings are checked unless `--structure-only` is explicit. `--profile release` is native-only and requires ready chapters, a `deliverable` artifact, and an explicit latest approval for at least one deliverable.
- `preserve SOURCE`: copies bytes to `<raw|derived>/sha256/<prefix>/<SHA256><suffix>`, verifies them, and appends a `SourceRecord` to `--run-manifest`. Existing identical bytes are reused; conflicting IDs or bytes are rejected.
- `signoff`: appends an `approved` or `rejected` human decision bound to an existing artifact ID, byte count, and SHA-256. It never infers or manufactures approval.
- `plan DOCUMENT --workdir DIR --composer MODULE:ATTRIBUTE [--validate-only]`: resolves the config's adapter and preset through their installed entry points, loads the explicit project composer, and runs the real pipeline validator. Planning is always validate-only and does not create the workdir, invoke a provider or executable, or mutate a run.
- `build RUN_MANIFEST --workdir DIR --composer MODULE:ATTRIBUTE`: executes the composed pipeline. Completed outputs and RED attempt material are preserved into the run before typed phase records are appended. TTS execution policy is explicit through `--offline-tts`, `--max-tts-attempts`, and `--retry-backoff-seconds`.
- `audit RUN_MANIFEST --subject-artifact-id ID --evidence-bundle PATH --report PATH --report-artifact-id ID`: creates and preserves an automated audit report plus its evidence bindings, then appends a typed automated-audit record. It never reads or writes human sign-off.
- `review DELIVERABLE --storyboard PATH --probe PATH --output-directory DIR --audit-directory DIR --ffmpeg EXEC`: creates a pending human-review package. `--probe` must be a v1 `xar-promo-bound-media-probe` envelope produced for the exact deliverable bytes; bare or stale ffprobe JSON is rejected. `--plan-only` validates and prints the frame extraction plan without creating directories, executing FFmpeg, or writing files.
- `export RUN_MANIFEST DESTINATION --policy POLICY`: validates and creates an offline allowlisted release bundle. `--dry-run` and `--validate-only` are mutually exclusive no-write preflights. Export never uploads or publishes.

All successful commands return `0`. Contract or integrity failures return `2`. Argparse syntax failures also return `2`. Completed `plan`, `build`, `audit`, `review`, and `export` handlers print JSON-encoded results; handler GREEN goes to stdout and handler RED goes to stderr. Errors that occur before a handler outcome exists, such as argparse errors or a composer module failing during import, use argparse usage or plain `RED:` diagnostics on stderr. Paths and current-time fields reflect the actual invocation; pass explicit timestamps such as `audit --created-at-utc` when a reproducible fixture requires stable time bytes.

`--composer` uses strict `MODULE:ATTRIBUTE` import syntax and must resolve to a callable implementing `PipelineComposer`. The CLI passes the resolved adapter and preset factories to that callable without invoking them or guessing their signatures. Adapter and preset IDs are resolved through the standard `xar_promo.adapters` and `xar_promo.presets` Python entry-point groups; projects install their integration plugin rather than encoding Python import paths in `promo-project.json`.

The `init` defaults `generic` / `default` are neutral authoring placeholders. They are intentionally not built-in production factories, so a newly scaffolded project must select IDs supplied by an installed integration before `plan`, `build`, or `audit` can resolve components.

ProjectConfig contains intent (`project`, `pipeline.adapter`, `pipeline.preset`, `locales`, `constraints`, `chapters`). RunManifest binds the config by relative path, bytes, and SHA-256 and separately owns `phase_history`, `artifacts`, `audits`, and `signoffs`. The dependency-free Python model enforces cross-record identities, immutable hashes, and ordered append-only records that JSON Schema cannot express alone.

Legacy compatibility is intentionally read-only. `validate` understands the existing `SourceRecord` shapes (`source`, `sources`, and `evidence_sources`, including optional `bytes` and `sha256`) without rewriting the source JSON. Mutating commands require a native manifest.

There is deliberately no `publish` or upload command. `build` stops at a byte-bound deliverable pending automated audit and explicit human review; `review` never signs off, `audit` never approves, and `export` only copies a release-ready allowlist into a local directory.
