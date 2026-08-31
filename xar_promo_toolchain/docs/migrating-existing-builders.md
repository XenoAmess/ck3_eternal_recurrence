# Migrating existing builders

This guide describes how to move a working promotional-video builder into
`xar_promo_toolchain` without breaking its callers or losing process material. It
is based on two repository entry points that have already completed the first two
migration stages:

- `tools/build_full_agent_showcase.py`;
- `mod_zhongguo_style/tools/build_promo_video.py`.

Their exact observable compatibility baseline is recorded in
[legacy-entrypoint-contracts.md](legacy-entrypoint-contracts.md). Read that
contract before changing either wrapper. The migration target is not "the new
code ran once"; it is that existing callers keep the same command line, validation
boundary, output/sidecar contract, cache identity, and retained material until a
separately tested replacement is ready.

## Current truth boundary

The two example builders are **not** fully rendered by the generic pipeline.
Their current state is:

| Layer | Generic showcase | ZhongGuo 361 promo |
| --- | --- | --- |
| TTS write | Delegates the provider call through `EdgeTtsProvider` and `TtsRequest` | Delegates each cue's provider call through the same API |
| Media probe | Uses `ffprobe_command` and `parse_ffprobe_json`, then restores the legacy raw-dictionary/error boundary | Reuses the showcase probe boundary |
| Layout/subtitle/media formatting | Uses generic balancing and compatibility projections for ASS/time/concat behavior | Keeps its project-specific bilingual layout and uses compatible shared media/time/concat primitives where equivalent |
| Validation pipeline | Projects chapters to `LegacyPipelineSegment`, canonical `VisualSource`, and `SegmentDraft`, then calls `run_pipeline(validate_only=True)` | Uses the same read-only projection after its 361-specific manifest, evidence, and layout checks |
| Real TTS cache, render, concat execution, sidecar | Still owned by the legacy builder | Still owned by the legacy builder |

The read-only projection is a real call through the frozen pipeline API, but it
does not produce media and is not evidence that the old render path has been
replaced. Project-specific story, voice, colors, bilingual policy, visual audit,
and release gates remain in the wrapper or preset.

## Migration stages

### Stage 0: freeze the observable contract

Before extracting code, record and test what callers can observe:

1. CLI flags, required arguments, defaults, value ranges, path resolution, stdout
   markers, stderr prefix, and exit codes.
2. Manifest validation, dependency discovery, and the exact difference between a
   normal build and validation-only mode.
3. Final output name, sibling sidecar name and schema, media properties, overwrite
   or archive behavior, and atomic replacement behavior.
4. Cache directory layout, fingerprint inputs, force/take semantics, retry policy,
   and invalid-cache recovery.
5. Every retained source, narration, subtitle, frame, segment, concat file,
   command log, partial, failed attempt, and superseded artifact.
6. Python seams used by existing tests or downstream scripts, including patched
   module globals and error types.

Create regression tests before replacing a seam. Both example builders retain
their existing suites (`tools/test_build_full_agent_showcase.py` and
`mod_zhongguo_style/tools/test_promo_video.py`), while
`xar_promo_toolchain/tests/test_legacy.py` covers package delegation and legacy
edge bytes. Run normal and `python -O` variants; a test that relies only on
`assert` is not an optimization-safe gate.

### Stage 1: delegate compatible primitives

Move one effect or pure transformation at a time, keeping the old orchestration
around it.

#### TTS

Start by replacing only the provider-specific network/write call with a
`TtsProvider` and `TtsRequest`. Keep the wrapper's existing:

- filenames and directory layout;
- cache fingerprint and metadata schema;
- `--force` or take identity;
- bounded retry/backoff behavior;
- temporary-file validation and atomic commit;
- legacy exception type and error text boundary.

Do not switch to `TtsCache` in the same change unless cache-path and metadata
parity have independent coverage. The pipeline deliberately supports
`prepared_narration` and `narration_resolver` so an established cache can remain
authoritative while rendering migrates later.

#### Media, layout, and subtitles

Delegate command construction and parsing separately from process execution.
This preserves wrapper-owned executable discovery, logging, monkey-patching, and
errors. If a generic formatter is intentionally stricter than the old builder,
use a compatibility projection that calls the generic implementation for the
common case and preserves the old result for historical edge cases. The existing
ASS timestamp, escaping, seconds, and concat adapters demonstrate this pattern.

Keep project policy outside the primitive. A generic line balancer must not learn
the ZhongGuo font, colors, two-language hierarchy, Xiaoxiao voice, 361 vocabulary,
or CK3 release rules merely because one wrapper uses them.

#### Stage 1 acceptance

For each delegated seam, require:

- the old unit tests to remain green without rewriting their expected public
  behavior;
- a focused test proving that the generic callable was actually reached;
- legacy errors to remain inside the old wrapper's exception/exit-code boundary;
- no cache or output path changes;
- failure before atomic rename to leave no valid-looking cache entry;
- `--help` and validation-only behavior to remain unchanged.

If one seam fails parity, roll back only that delegation. Do not revert unrelated
green primitives and do not delete the cache or failed material used to diagnose
the mismatch.

### Stage 2: add a validate-only pipeline projection

Once the primitives are stable, project the legacy chapter model into the generic
orchestration model without moving real rendering yet:

1. Translate each chapter to a stable `SegmentDraft` with caller-selected
   `RenderOptions`, subtitle tracks, and timing.
2. Use `xar_promo.sources.VisualSource` as the only visual ABI. For a legacy
   adapter that still normalizes or generates visuals, declare the planned media
   as `requires_resolution=True` beneath the attempt work directory.
3. Supply legacy narration through the resolver seam rather than changing its
   cache during this stage.
4. Call `run_pipeline(..., validate_only=True)` in a fresh, uncreated attempt
   path.
5. Translate a failed `PipelineResult` back to the wrapper's existing error type;
   keep the wrapper's `0/2/130` process boundary.

Every effectful dependency should be an injected sentinel during this projection.
A successful validation must prove that the pipeline did not call the visual
resolver/probe, narration resolver, TTS cache/provider, subtitle renderer,
planner, command runner, or FFmpeg. It must not create the attempt directory,
append a run ledger, write a sidecar, or touch the output.

This stage supplements the legacy preflight; it does not replace project checks.
The showcase still validates its source hashes, video ranges, fonts, and text
layout. The 361 wrapper still validates its fixed language/voice policy, topic
coverage, release provenance, clean visual-audit binding, duration rules, and
test-only-text exclusions before reporting `VALID:`.

### Stage 3: move real execution to the pipeline

Do this only after a project-owned `PipelineComposer` can express every real
chapter, source, narration, subtitle, render option, and deliverable without
weakening the frozen contract.

The frozen native command surface has ten commands: `init`, `start-run`,
`validate`, `preserve`, `signoff`, `plan`, `build`, `audit`, `review`, and
`export`. For a native migration:

- `plan DOCUMENT --workdir ... --composer MODULE:ATTRIBUTE` is read-only;
- `build RUN_MANIFEST --workdir ... --composer MODULE:ATTRIBUTE` runs a composed
  pipeline, preserves successful or failed material, and appends runlog facts;
- `audit` records an automated audit only;
- `review` creates or plans a pending review package only;
- `signoff` is the separate explicit human-decision operation;
- `export` creates an offline bundle and does not publish it.

The command layer resolves adapter and preset factories but does not interpret
their open-ended call signatures. The explicit composer owns that project
composition. See [pipeline-composition.md](pipeline-composition.md) for the frozen
Python ABI and [cli-and-manifest-v1.md](cli-and-manifest-v1.md) for the native
document boundary.

Use a shadow period before routing the old wrapper to real pipeline execution:

1. Create a new native run and a fresh attempt directory; never point a comparison
   build at the legacy output or reusable cache directory.
2. If final timing depends on synthesized narration, prepare/cache it, probe its
   real duration, and compose a second bound invocation. An estimate-only draft
   remains an authoring candidate, not a release candidate.
3. Resolve generated visuals to their exact planned paths and probe the actual
   media family and dimensions. Keep byte/SHA bindings in the attempt result.
4. Render and retain every segment, command audit, partial, failure artifact, and
   concat input. A RED attempt stays RED.
5. Compare observable compatibility: media streams and duration, chapter timing,
   subtitle rendering, audible narration, sidecar fields and hashes, cache reuse,
   stdout markers, exit codes, overwrite/archive behavior, and project audits.
   Encoding bytes need not be identical unless the old contract explicitly says
   so.
6. Have a human review the actual candidate where the project requires it. A
   pipeline success or automated audit cannot manufacture approval.
7. Only then change the wrapper's real-build route. Keep translating the old CLI
   and sidecar until every repository caller has moved.

Do not deprecate the legacy renderer merely because `plan` is green or one shadow
build completed. Full migration requires representative cache-hit/cache-miss,
failure, interruption, overwrite/archive, and release-gate cases.

## Compatibility checklist

### CLI and Python ABI

- [ ] Existing flag names, requiredness, defaults, ranges, and precedence are
      unchanged.
- [ ] Manifest-relative paths still resolve from the manifest directory.
- [ ] Success, actionable failure, and interruption remain `0`, `2`, and `130`
      where the old entry point promises them.
- [ ] `VALID:`, `VIDEO:`, `SIDECAR:`, and any project-specific marker such as
      `WORK:` retain their machine-readable meaning.
- [ ] Old wrapper exception classes still contain generic provider/parser/pipeline
      failures.
- [ ] Patched module globals and call signatures used by existing tests remain
      available until deliberately versioned or deprecated.
- [ ] Validation-only performs zero synthesis, resolution, rendering, mutation,
      or output writes.

### Sidecar and deliverable

- [ ] The final media and sibling `*.video.json` paths are unchanged.
- [ ] Existing top-level and chapter fields are not removed or reinterpreted.
- [ ] Manifest, source, narration, subtitle, segment, and deliverable identities
      still bind the expected bytes and SHA-256 values.
- [ ] Chapter order, timeline, language labels, voice/provider data,
      classifications, readiness, and honest-boundary fields remain truthful.
- [ ] Media geometry, codecs, pixel format, audio rate/channels, and duration gates
      match the wrapper contract.
- [ ] Generic pipeline success remains `pending-project-audit`; it is not written
      into the old sidecar as approval.
- [ ] Sidecar commit remains atomic, and an output is never silently substituted
      after a human sign-off.

### Cache

- [ ] The legacy fingerprint still includes every old identity input: text,
      provider/tool version, voice, rate, volume, pitch, and project-specific
      values such as `take-id` where applicable.
- [ ] A cache hit still validates metadata, exact media bytes/hash, and any media
      probe required by the wrapper.
- [ ] `--force`, take changes, and content changes retain their old invalidation
      behavior.
- [ ] Retry count and backoff remain bounded and unchanged.
- [ ] Synthesis uses a distinct partial path; only validated bytes are renamed
      into the cache.
- [ ] A failed attempt cannot leave a partial file or metadata row that is accepted
      as a later cache hit.
- [ ] Moving to `TtsCache`, if desired, is its own measured migration step rather
      than an incidental consequence of pipeline rendering.

### Process material and overwrite policy

- [ ] Existing work-root and per-chapter naming remain discoverable while the old
      wrapper contract is active.
- [ ] Narration text/audio/metadata, generated frames or overlays, ASS files,
      segment media/build metadata, concat inputs, logs, and sidecars are retained.
- [ ] Partial, failed, and superseded attempts remain available for diagnosis.
- [ ] No successful path automatically deletes a legacy cache or work tree.
- [ ] Direct replacement and archive-on-request policies are not mixed between
      builders: the showcase replacement behavior and the 361 default refusal plus
      explicit archive behavior remain distinct.
- [ ] Native `build` preservation and runlog appends add evidence; they do not
      rewrite an older RED attempt into GREEN.
- [ ] Cleanup and publication remain separate, explicitly authorized operations.

## Rollback procedure

Rollback is routing recovery, not evidence erasure.

1. Stop before writing another candidate to the affected public output path.
2. Preserve the failing command output, partials, work directory, sidecar diff,
   cache metadata, and test logs. If a native run exists, leave its failure and
   retained artifacts in the runlog.
3. Identify the smallest migration stage that changed behavior:
   - for a primitive mismatch, restore only the wrapper's old implementation at
     that call site;
   - for a validate-only mismatch, remove or bypass only the supplemental
     projection while retaining the old preflight;
   - for a real-pipeline mismatch, route the old wrapper back to its retained
     legacy renderer and keep the new attempt as RED evidence.
4. Do not rename failed output into a cache hit, rewrite a sidecar as successful,
   edit a RED run into GREEN, or delete the comparison attempt.
5. Re-run the old wrapper tests, package tests, `--help`, validation-only no-write
   checks, and the case that triggered rollback.
6. Resume migration only with a focused parity test that reproduces the failure.

Rollback should not require changing a caller's command line or restoring deleted
materials. If it does, the earlier compatibility or retention gate was incomplete.

## Completion criteria

An existing builder is fully migrated only when its public wrapper can perform a
real build through the generic pipeline for its supported matrix, all compatibility
checklists pass, project audits and human review still operate on exact resulting
bytes, and the legacy renderer can be retired without losing historical projects
or process material.

The two repository examples have not reached that final state. They are validated
case studies for Stage 1 and Stage 2, with their established real render and
sidecar implementations intentionally retained as the production path.
