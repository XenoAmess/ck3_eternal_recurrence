# Pipeline composition contract

## Status and scope

This document freezes the composition boundary for `xar_promo.pipeline`. The
pipeline sequences an already-composed promotional-video attempt; it does not
interpret a game, product, language, voice, story policy, adapter identifier, or
preset identifier.

The stable orchestration path is:

```text
load and bind config/run
        |
resolve adapter and preset factories (do not invoke them)
        |
project-owned PipelineComposer
        |
PipelineInvocation(draft, dependencies, workdir)
        |
run_invocation / run_pipeline
        |
attempt-local result -> artifact preservation -> canonical runlog -> audit -> human sign-off
```

The generic pipeline never publishes, uploads, mutates a `RunManifest`, records an
automated audit as passed, or creates a human sign-off.

## Composition ABI

The public composition types are imported from `xar_promo.pipeline`:

```python
PipelineComposer
PipelineInvocation
PipelineDraft
SegmentDraft
PipelineDependencies
PipelineResult
run_invocation
run_pipeline
```

`PipelineComposer` has this exact callable shape:

```python
composer(
    config: ProjectConfig,
    run: RunManifest | None,
    *,
    config_path: Path,
    run_path: Path | None,
    workdir: Path,
    adapter_factory: AdapterFactory,
    preset_factory: PresetFactory,
    validate_only: bool,
) -> PipelineInvocation
```

The command layer owns config/run loading, exact-byte binding checks, registry
resolution, and selection of a fresh attempt work directory. It passes the two
resolved factories to the composer without guessing their open-ended call
signatures. The project-owned composer is the only layer allowed to interpret
those factories and combine adapter evidence with preset policy.

The composer must reuse `xar_promo.storyboard.plan_storyboard(...)` when it turns
chapters and cues into concrete timing. Timeline estimation, narration-duration
resolution, cue/chapter spacing, and artifact availability remain preset/adapter
inputs to that function; neither the command layer nor the pipeline reimplements
its timing algorithm.

`PipelineInvocation` contains exactly:

- `draft: PipelineDraft`
- `dependencies: PipelineDependencies`
- `workdir: Path`

`run_invocation(invocation, ...)` is a thin, non-reinterpreting call to
`run_pipeline(...)`.

## Draft and dependency boundary

Each `SegmentDraft` contains:

- a stable `segment_id`;
- one canonical `xar_promo.sources.VisualSource`;
- caller-selected `RenderOptions` and `start_seconds`;
- caller-owned subtitle track text;
- either a `TtsRequest`, a prepared narration path, or a narration resolver seam.

`PipelineDraft` binds the core `ProjectConfig`, ordered segments, a relative
deliverable path, a deliverable artifact ID, and its media type. It contains no
implicit voice, language pair, codec profile, or project-specific duration rule.
The deliverable ID must be distinct from every pipeline-owned ID:
`visual.<segment>`, `narration.<segment>`, `subtitle.<segment>`,
`segment.<segment>`, and `concat.manifest`. This is rejected during draft
validation, before a work directory or production dependency is touched.

The first four `PipelineDependencies` are required:

- `ffmpeg`
- `subtitle_renderer`
- `command_runner`
- `visual_probe`

Optional dependencies are `tts_cache`, `tts_provider`, `visual_resolver`,
`narration_resolver`, `draft_validator`, and injectable render/concat planners and
plan executor. All effectful dependencies are caller-owned and test-replaceable.

The exact resolver call shapes are:

```python
visual_resolver(source: VisualSource, *, workdir: Path) -> Path
narration_resolver(segment: SegmentDraft, *, workdir: Path) -> NarrationArtifact
subtitle_renderer(
    segment: SegmentDraft,
    narration: NarrationArtifact,
    *,
    workdir: Path,
) -> str
```

## Canonical visual sources

`xar_promo.sources` is the only visual-source ABI. The pipeline does not publish a
second `VisualArtifact` or resolver protocol.

Use `VisualSource` with `VIDEO`, `STILL`, `GENERATED_CARD`, `EVIDENCE_CARD`, or an
explicit `SourceKind`. A prepared source must exist even during validation. A
generated source declares `requires_resolution=True` and an exact path beneath
the attempt work directory; that file may be absent during validation.

During a full build the pipeline delegates to `prepare_visual(...)`. The resolver
must return the exact planned path, after which the injected probe verifies actual
visual media family and positive dimensions. `PreparedVisual` binds those facts to
the file's byte count and SHA-256. A JSON manifest or subtitle document cannot be
passed off as visual media.

## Narration compatibility and precedence

Narration preparation uses this fixed precedence:

1. `SegmentDraft.prepared_narration`, when present;
2. injected `narration_resolver(segment, *, workdir)`;
3. `tts_cache.get_or_create(narration_request, tts_provider, ...)`.

The first seam preserves legacy builders whose narration filenames, caches, and
patch targets are observable contracts. The second lets a legacy wrapper retain
its existing synthesis implementation and path layout. Neither seam requires a
wrapper to migrate immediately to the new content-addressed TTS cache.

A final-duration build needs narration whose real duration is already available to
the storyboard resolver. If narration has not yet been prepared or cached, a
composer may use its pure draft estimator only for an authoring candidate. That
candidate must remain release-RED. The release path is two-pass: prepare/cache
narration, probe its real duration, then compose a new invocation from that bound
duration. The composer must not hide TTS work inside validation.

## Phase order

A full attempt records these attempt-local phases in order:

1. `draft`
2. `visual`
3. `narration`
4. `subtitle`
5. `segment-plan`
6. `segment-render`
7. `concat`
8. `audit-record-ready`

Planning all segment render commands precedes executing any of them. Successful
segment outputs remain in the work directory if a later segment or concat fails.
The final phase means only that a byte-bound deliverable is available for project
audit. Its status is `pending-project-audit`, and `human_signoff_required` remains
true.

## Validate-only is read-only

`validate_only=True` performs structural and read-only source checks, records the
attempt-local `draft` phase as validated, and marks all later phases skipped. It
does **not**:

- create the attempt work directory;
- call a visual resolver or visual probe;
- call prepared/legacy narration resolution, a TTS cache, or a TTS provider;
- call subtitle/layout rendering;
- build render/concat plans;
- invoke FFmpeg or any injected command runner;
- create partial output, process logs, or a deliverable;
- mutate a run manifest, append a runlog record, audit, or sign-off.

The injected project `draft_validator` is allowed to run and therefore must itself
be a read-only validator.

## Failure and retained evidence

An ordinary stage exception produces `PipelineResult(status="failed")` rather than
rewriting a failed attempt into success. `PipelineFailure` identifies the failed
phase and exception, captures command stdout/stderr when available, and lists
partial, stdout, stderr, and other retained paths.

The pipeline never deletes or truncates the work directory, generated visual,
narration, subtitle, completed segment, concat manifest, command audit directory,
or partial output. External-command audit files remain the responsibility of
`xar_promo.process`, which records shell-free argv, stdout, stderr, result, and
partial snapshots. `PipelineResult.require_success()` is the explicit escalation
seam and raises `PipelineExecutionError` carrying the complete result.

No failure path records a sign-off, and no success path records one automatically.

## Attempt-local records versus canonical runlog

`PipelinePhaseRecord`, `PipelineArtifactRecord`, `AuditRecordReady`, and
`PipelineFailure` describe one in-memory/filesystem attempt. Their local sequence
numbers are not global `RunManifest` sequence numbers.

After a successful or failed operation, the command layer may:

1. preserve selected exact files with the core artifact operation;
2. project preserved `SourceRecord` objects through
   `xar_promo.runlog.ArtifactReference.from_source_record(...)`;
3. create or append canonical `xar_promo.runlog.PhaseRecord` rows with global,
   gap-free sequence numbers and UTC timestamps;
4. append a canonical automated-audit record only after a real audit report and
   its subject have both been preserved;
5. leave human approval exclusively to the explicit core sign-off operation.

Canonical runlog phases permit an empty artifact tuple. This is required for
`draft-validate` and `segment-plan`; callers must never fabricate an artifact just
to populate a phase row. An automated audit still requires two genuine,
byte/SHA-bound artifacts: its subject and report.

The append functions are:

```python
append_phase_record(...)
append_automated_audit_record(...)
```

These typed functions own sequence assignment, timestamp validation, artifact
binding, and the internal atomic manifest mutation. Callers must not append raw
phase/audit dictionaries or call the lower-level manifest replacement seam. Neither
typed function can create an `approved` human state.

## Invocation examples

### Programmatic plan and build

`xar_promo.pipeline_commands` is the stable command layer. A project supplies its
composer and explicit local registrations (or a registry configured for entry-point
discovery). The following is schematic: `adapter_factory`, `preset_factory`, and
`project_composer` are project-defined callables, not names exported by the generic
package:

```python
from pathlib import Path

from xar_promo.pipeline_commands import handle_build, handle_plan
from xar_promo.registry import ComponentRegistry

registry = ComponentRegistry(
    adapters={"my-adapter": adapter_factory},
    presets={"my-preset": preset_factory},
    discover_entry_points=False,
)

planned = handle_plan(
    Path("promo-project.json"),       # a ProjectConfig or RunManifest
    workdir=Path("attempts/plan-001"),
    registry=registry,
    composer=project_composer,
)
if planned.exit_status != 0:
    raise RuntimeError(planned.failure.message)

built = handle_build(
    Path("runs/run-0001/run-manifest.json"),  # RunManifest required
    workdir=Path("attempts/build-001"),       # use a fresh directory
    registry=registry,
    composer=project_composer,
    offline_tts=False,
    max_tts_attempts=3,
    retry_backoff_seconds=1.0,
)
if built.exit_status != 0:
    # RED still carries pipeline_result, preserved_artifacts, and retained paths.
    raise RuntimeError(built.failure.message)
```

`handle_plan` resolves but does not invoke registry factories directly. It calls the
composer and pipeline with `validate_only=True`. Config and run forms are both
strictly read-only: the work directory is not created and even a supplied run
manifest remains byte-for-byte unchanged.

`handle_build` accepts only a native run manifest. It composes and executes with
`validate_only=False`, preserves every completed pipeline artifact, preserves RED
partial/stdout/stderr and other retained files, then appends typed `build.*` phase
records through `xar_promo.runlog`. Its `CommandOutcome` uses exit status `0` for
success and `2` for a typed operational failure. A RED outcome remains inspectable
without rerunning the attempt.

### Automated audit

```python
from xar_promo.pipeline_commands import handle_audit

audited = handle_audit(
    Path("runs/run-0001/run-manifest.json"),
    registry=registry,
    subject_artifact_id="release-candidate",
    evidence_bundle_path=Path("audit-input/evidence-bundle.json"),
    report_path=Path("audit-output/report.json"),
    report_artifact_id="automated-audit-report",
    created_at_utc=None,  # current UTC; inject a UTC value for reproducible tests
)
if audited.exit_status != 0:
    raise RuntimeError(audited.failure.message)
```

The audit command preserves the evidence inputs and report, appends a typed
automated-audit record, and always writes `manual_signoff.state=not-provided`. It
never reads an existing approval into the automated result and never calls the
sign-off operation.

### Real offline media smoke

The repository includes a real Pillow + ASS + FFmpeg + ffprobe + concat + review
smoke. Run this command from the repository root. It uses generated cards and
prepared WAV narration, performs validate-only and full runs, writes a pending
audit candidate, and retains every command audit and intermediate file:

```powershell
py xar_promo_toolchain/scripts/run_pipeline_smoke.py `
  --workdir C:/temp/xar-promo-smoke-attempt-001 `
  --ffmpeg C:/tools/ffmpeg/bin/ffmpeg.exe `
  --ffprobe C:/tools/ffmpeg/bin/ffprobe.exe
```

The work directory must be fresh. Success prints the retained report path and its
SHA-256; failure returns nonzero, writes `smoke-failure.json` when possible, and
keeps the failed attempt.

### Generic CLI boundary

The installed console entry point exposes the same handlers without introducing
a second protocol. The project composer must be importable in the CLI process and
is named as `MODULE:ATTRIBUTE`. The config/run's adapter and preset IDs are still
resolved through the `xar_promo.adapters` and `xar_promo.presets` Python entry-point
groups; the CLI passes both resolved factories to the composer without invoking
them itself.

Read-only planning accepts either a native `ProjectConfig` or `RunManifest`:

```powershell
xar-promo plan promo-project.json `
  --workdir C:/temp/my-promo-plan-001 `
  --composer my_project.promo:compose `
  --validate-only
```

`plan` is always validate-only. The optional flag makes that guarantee explicit
for automation but does not enable a different mode. A successful plan prints one
JSON `CommandOutcome` to stdout and exits `0`; an expected typed RED prints its
JSON outcome to stderr and exits `2`. The named work directory is checked as an
attempt location but is not created, and the input document is not mutated.

A real build requires a native run manifest and a fresh attempt directory:

```powershell
xar-promo build runs/run-0001/run-manifest.json `
  --workdir C:/temp/my-promo-build-001 `
  --composer my_project.promo:compose `
  --max-tts-attempts 3 `
  --retry-backoff-seconds 1.0
```

Add `--offline-tts` only when the composition is expected to resolve narration
entirely from prepared audio or an already-populated cache. A GREEN build
preserves all completed outputs and appends typed `build.*` phase rows. A RED
build exits `2` but still preserves completed artifacts, partial outputs,
stdout/stderr, and other retained evidence before appending the corresponding
typed phase rows. Neither result records human sign-off.

Run automated audit only after the subject artifact has been preserved in that
run:

```powershell
xar-promo audit runs/run-0001/run-manifest.json `
  --subject-artifact-id release-candidate `
  --evidence-bundle audit-input/evidence-bundle.json `
  --report audit-output/report.json `
  --report-artifact-id automated-audit-report
```

`--created-at-utc 2026-09-01T00:00:00Z` may be supplied for a reproducible test;
normal operation omits it and records current UTC. The command preserves the
evidence and report, appends the canonical automated-audit row, reports manual
sign-off as not provided, and never approves a deliverable.

Once a `CommandOutcome` exists, all three commands serialize that structured
result as JSON. Missing registry entries, contract failures, and pipeline
failures therefore remain JSON RED with exit `2`; a composer import failure
happens before handler invocation and uses the CLI's plain `RED:` diagnostic
with the same exit code. Project wrappers may call these commands or the
stable programmatic handlers above, but must not reimplement composition,
artifact preservation, typed runlog projection, or sign-off semantics.
