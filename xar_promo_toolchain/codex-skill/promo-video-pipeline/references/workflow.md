# Workflow

## Select the project boundary

Resolve the project config, run, and project-supplied `PipelineComposer` selected by the user or repository. The checked-in config owns adapter/preset IDs, locales, voice, duration, layout, capture, render, and audit choices. Native projects separate intent at `<project>/promo-project.json` from append-only attempt evidence at `<project>/runs/<run-id>/run-manifest.json`.

Run `xar-promo --version`, `xar-promo --help`, and the relevant subcommand help. Use only the installed interface. Success returns `0`; syntax, contract, integrity, and operational failures return `2`. When their handlers are reached, `plan`, `build`, and `audit` emit structured GREEN JSON to stdout or RED JSON to stderr; argument or composer-loading failures may use plain `RED:` text, so treat the exit code as canonical.

Keep each run, build attempt, review output, process-audit directory, and export destination distinct. Never overwrite an earlier generation. Never delete a RED attempt: its partials and logs are evidence.

## Initialize or resume

Create a native project only when requested:

```text
xar-promo init <project-directory> [--project-id <id>] [--title <title>] [--adapter <id>] [--preset <id>] [--run-id <id>] [--narration-locale <locale>] [--subtitle-locale <locale>]...
```

Defaults are `adapter=generic`, `preset=default`, `run-id=run-0001`, narration locale `und`, and one matching subtitle locale. Initialization refuses to overwrite its config or initial run. It creates `promo-project.json`, `runs/<run-id>/run-manifest.json`, and run-local artifact directories.

After editing checked-in intent, create a later run bound to those exact config bytes:

```text
xar-promo start-run [<project-config>] --run-id <id> [--run-directory <directory>]
```

The default config is `./promo-project.json`; the default run directory is `<project>/runs/<run-id>`. Existing destinations are rejected. The command snapshots and hash-binds current config bytes inside the new run, so later config edits do not make old runs stale.

Validate before every phase and after every run mutation:

```text
xar-promo validate [<document>] [--profile authoring|release] [--structure-only] [--json]
```

The default document is `./promo-project.json`. Full file, byte-count, config-binding, and SHA-256 checks are the default. `--structure-only` deliberately skips referenced-file byte/hash checks and is not release evidence. Validate both the checked-in config and selected run.

## Plan without effects

```text
xar-promo plan <project-config-or-run-manifest> --workdir <fresh-proposed-directory> --composer <MODULE:ATTRIBUTE> [--validate-only]
```

`plan` is always read-only; the optional flag makes that intent explicit. It resolves the config-selected adapter and preset plus the project composer, composes a validate-only pipeline, and must not invoke TTS, FFmpeg, capture, or other production providers. It does not create the proposed work directory, mutate a run, append phase history, or create manifest history. Treat GREEN as "the plan validates," not "media exists."

If the composer or config-selected component is absent, stop and report the missing project integration. Do not replace it with ad hoc Skill logic.

## Build and retain every attempt

```text
xar-promo build <run-manifest> --workdir <fresh-attempt-directory> --composer <MODULE:ATTRIBUTE> [--offline-tts] [--max-tts-attempts <n>] [--retry-backoff-seconds <seconds>]
```

`build` requires a native run. It executes the composed project pipeline, stores completed outputs in the run's immutable content-addressed artifact store, and appends typed phase history. Its defaults are three TTS attempts and one second of retry backoff; use `--offline-tts` only when the selected project/provider supports the requested offline path.

A RED build remains RED, but materialized outputs, partial files, stdout, stderr, command audits, and other failure material are retained before exit whenever possible. Do not clean the work directory or retry over it. Start a fresh work directory, and use a new artifact ID or run when bytes change.

For material produced outside `build`, register each file explicitly:

```text
xar-promo preserve <source> --run-manifest <run-manifest> --artifact-id <id> --collection raw|derived --role <role> [--label <label>] [--media-type <type>]
```

The default manifest is `./runs/run-0001/run-manifest.json`. Use `raw` for source/input bytes and `derived` for generated material. `preserve` copies without modifying the source. Artifact IDs are immutable byte bindings.

## Automated audit

```text
xar-promo audit <run-manifest> --subject-artifact-id <id> --evidence-bundle <path> --report <new-report-path> --report-artifact-id <id> [--created-at-utc <timestamp>]
```

Audit only a subject already preserved in the native run. Relative evidence/report paths resolve from the run directory. Supply a real, hash-verifiable evidence bundle and a new report path. The command preserves referenced evidence, the bundle, and the generated report, then appends a typed automated-audit record.

An automated pass does not read, modify, or grant human approval. It records `manual_signoff.state=not-provided`. Keep audit status and signoff status separate even if a prior human decision already exists.

## Pending human review

First generate the required v1 `xar-promo-bound-media-probe` envelope for the exact deliverable bytes through the public live producer:

```python
from pathlib import Path

from xar_promo import probe_and_write_bound_media

probe_and_write_bound_media(
    "ffprobe",
    Path("artifacts/final.mp4"),
    output_path=Path("artifacts/final.bound-probe.json"),
    audit_directory=Path("artifacts/final-probe-audit"),
)
```

The stable signature is `probe_and_write_bound_media(ffprobe, media_path, *, output_path, audit_directory, command_runner=run_command) -> BoundMediaProbe`. This producer really invokes ffprobe, retains its command audit, and writes a new envelope containing the raw probe plus the subject byte count and SHA-256. Preserve both the envelope and its command-audit directory. Do not hand-wrap or reuse raw ffprobe output.

Then plan review frame extraction with exactly zero process execution and zero writes:

```text
xar-promo review <deliverable> --storyboard <timeline.json> --probe <deliverable.bound-probe.json> --output-directory <new-directory> --audit-directory <new-directory> --ffmpeg <executable> [--working-directory <directory>] --plan-only
```

`--plan-only` reads and hashes the deliverable, verifies the envelope binding and storyboard timeline, and prints the frame plan without invoking ffprobe/FFmpeg or creating directories/files. Bare raw ffprobe JSON, a stale envelope, or any byte/SHA mismatch is RED.

Run the same command without `--plan-only` to extract review frames and create a byte-bound pending review template/package. The result remains pending: the review command never calls `signoff`, never supplies a reviewer decision, and never grants approval.

Preserve the storyboard, bound probe and its live-probe command audit, extracted frames, template, package, FFmpeg command records, stdout/stderr, and any failed partials. `review` does not take a run manifest, so these outputs are not registered until `preserve` is called for each file.

## Explicit human signoff

Only after a human explicitly supplies reviewer identity and decision, bind it to the exact preserved artifact:

```text
xar-promo signoff --run-manifest <run-manifest> --artifact-id <id> --reviewer <name> --decision approved|rejected [--note <text>] [--reviewed-at <timestamp>]
```

The default manifest is `./runs/run-0001/run-manifest.json`; omitting the timestamp uses current UTC. Record stated viewing conditions, such as full-length playback and speed, in the note without embellishing the reviewer's claim. Never convert an automated audit, pending review package, generated summary, partial viewing, or Codex inspection into signoff.

## Validate and export offline

First run full authoring validation, then release validation:

```text
xar-promo validate <run-manifest>
xar-promo validate <run-manifest> --profile release
```

Release validation requires a native run, at least one chapter with every chapter ready, a preserved `deliverable`, and an explicit latest approval for at least one deliverable. It does not turn an automated audit into approval.

Use a project-owned strict JSON allowlist policy to select exactly which preserved deliverable, subtitles, thumbnail, sidecar, audit report, and optional config snapshot enter a new offline bundle:

```json
{
  "format_version": 1,
  "kind": "xar_promo_release_export_policy",
  "items": [
    {
      "category": "deliverable",
      "destination": "video/promo.mp4",
      "source_kind": "artifact",
      "artifact_id": "final-video-v1",
      "expected_role": "deliverable"
    },
    {
      "category": "project-config",
      "destination": "metadata/project-config.json",
      "source_kind": "project-config-snapshot"
    }
  ]
}
```

Artifact items require an explicit category, destination, artifact ID, and expected role; the exporter never infers them. The policy must select exactly one deliverable. Replace the example ID and destination with the project's preserved generation.

```text
xar-promo export <run-manifest> <new-destination> --policy <policy.json> [--dry-run | --validate-only]
```

Both read-only modes validate without creating the destination. Normal export refuses an existing destination, copies only allowlisted bytes, verifies them, and writes `release-bundle-manifest.json`. It does not mutate the run, use the network, or publish anything.

## Handoff

Report the config, run manifest, build work directory, preserved deliverable, automated audit report, pending review package, explicit signoff state, offline bundle, and every failed attempt by path. State the highest lifecycle state actually reached.

Publication or distribution is a separate project-side operation. Perform it only under explicit authorization and the target project's own release procedure; GREEN validation, audit, review, signoff, or export does not itself authorize upload.
