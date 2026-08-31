# Troubleshooting

This page covers only failure modes already observed in this repository or
explicitly represented by the current toolchain contracts. A failed attempt is
evidence: do not delete it, overwrite it, or relabel it GREEN. Diagnose it in
place, then use a new run, work directory, review directory, report path, or
export destination for the retry.

The commands below use `python -m xar_promo` deliberately. This makes the
selected interpreter visible and avoids accidentally invoking a console script
installed into some other environment.

## Secondary worktree is using the wrong Python or source tree

Typical symptoms are `ModuleNotFoundError`, an older CLI that does not list all
ten commands, missing Pillow or `edge-tts` despite their presence in the main
environment, or `xar_promo.__file__` pointing at the main worktree while the
attempt is running from a secondary worktree.

Use the secondary worktree's own agreed relative virtual environment when it
exists. If it does not exist, select the main worktree interpreter explicitly
and prepend the current secondary source tree to `PYTHONPATH`:

```powershell
$taskRoot = (Resolve-Path .).Path
$mainWorktree = "C:\path\to\main-worktree"
$localPython = Join-Path $taskRoot "tools\.venv\Scripts\python.exe"
$promoPython = if (Test-Path -LiteralPath $localPython) {
  (Resolve-Path $localPython).Path
} else {
  (Resolve-Path (Join-Path $mainWorktree "tools\.venv\Scripts\python.exe")).Path
}
$promoSource = (Resolve-Path (Join-Path $taskRoot "xar_promo_toolchain\src")).Path
$env:PYTHONPATH = @($promoSource, $taskRoot, $env:PYTHONPATH) -join [IO.Path]::PathSeparator

& $promoPython -c "import sys, xar_promo; print(sys.executable); print(sys.version); print(xar_promo.__file__)"
& $promoPython -m xar_promo --help
& $promoPython -c "import importlib.util as u; print('Pillow/PIL:', u.find_spec('PIL')); print('edge_tts:', u.find_spec('edge_tts'))"
```

The module path must resolve beneath the current secondary worktree's
`xar_promo_toolchain\src`. The frozen CLI lists exactly `init`, `start-run`,
`validate`, `preserve`, `signoff`, `plan`, `build`, `audit`, `review`, and
`export`. Until both checks agree, classify the result as an environment RED,
not a product-code RED.

Do not silently fall back to bare `py` or system Python, and do not create,
overwrite, or upgrade the main virtual environment from a secondary worktree.
Record the interpreter path, version, module path, and dependency probe with the
attempt.

## Adapter or preset entry point is missing

`plan`, `build`, and `audit` resolve the adapter and preset IDs stored in the
bound `ProjectConfig`. The generic CLI uses Python entry points in these two
groups:

- `xar_promo.adapters`
- `xar_promo.presets`

There are no CLI flags for injecting adapter or preset factories. `init` can
write arbitrary IDs and therefore succeeding at `init` does not prove that the
pipeline components are installed. A missing component produces an error such
as:

```text
adapter id 'example' is not registered locally and was not found in Python entry-point group 'xar_promo.adapters'
```

Read the intended IDs and enumerate what the selected interpreter can actually
discover:

```powershell
$config = Get-Content -Raw .\promo-project.json | ConvertFrom-Json
$config.pipeline | Format-List adapter, preset

& $promoPython -c 'from importlib.metadata import entry_points; eps=entry_points(); print("adapters:", sorted((e.name,e.value) for e in eps.select(group="xar_promo.adapters"))); print("presets:", sorted((e.name,e.value) for e in eps.select(group="xar_promo.presets")))'
```

Install the intended integration distribution into the already selected
environment, or use the stable programmatic handlers with an explicit local
`ComponentRegistry` when the integration is intentionally in-tree. Do not edit
an old run's snapshotted adapter/preset IDs just to suppress the error; create a
new correctly bound run if authoring intent changes.

## Composer `MODULE:ATTRIBUTE` cannot be loaded

`plan` and `build` require one project-owned composer. The frozen syntax is a
Python importable module, one colon, and a callable attribute path:

```powershell
& $promoPython -m xar_promo plan .\promo-project.json `
  --workdir .\attempts\plan-001 `
  --composer my_project.promo:compose `
  --validate-only
```

The loader distinguishes three defined failures:

- `composer must use MODULE:ATTRIBUTE syntax`: the colon, module, or attribute
  is missing;
- `could not load composer ...`: the module is not on the selected
  interpreter's import path or an attribute does not exist;
- `resolved to non-callable`: the named object exists but cannot be called.

Probe the same object with the same interpreter and `PYTHONPATH`:

```powershell
& $promoPython -c 'import importlib; m=importlib.import_module("my_project.promo"); v=getattr(m,"compose"); print(m.__file__); print(v); print("callable:", callable(v))'
```

The value is not a filesystem path and should not include parentheses. Dotted
attribute paths after the colon are supported. A callable that later fails must
still satisfy the documented `PipelineComposer` call shape and return a
`PipelineInvocation`; that later error is a composition RED, not a loader RED.

## FFmpeg or ffprobe is unavailable or wrong

FFmpeg and ffprobe are external programs. No Python extra installs them.
`build` receives its executable choices through the project composer and
`PipelineDependencies`; the CLI intentionally has no `--ffmpeg` or `--ffprobe`
guessing flags. `review` is the exception and requires an explicit `--ffmpeg`
argument. A GREEN `plan` is read-only and invokes neither program, so it does
not prove that a later build can start them.

Resolve and probe the exact executables before a media attempt:

```powershell
$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
& $ffmpeg -version
& $ffprobe -version
& $ffprobe -v error -show_streams -show_format -of json .\artifacts\candidate.mp4
```

If the integration uses explicit paths, run these commands against those exact
paths instead of the PATH results. `CommandStartError` means the process could
not start; a nonzero program exit is `CommandFailedError`; malformed probe
output is a `MediaProbeError`. Shell-free argv, stdout, stderr, return status,
and partial-output snapshots are retained in the command audit directory:

```powershell
Get-ChildItem -Recurse -Filter command.json .\attempts\build-001
Get-ChildItem -Recurse -Filter result.json .\attempts\build-001
Get-ChildItem -Recurse -Include stdout.txt,stderr.txt .\attempts\build-001
```

Inspect those files before retrying. Keep the failed attempt and pass corrected
executable paths through the composer into a new build work directory.

## AAC padding makes the container longer than the video stream

Real MP4 output can report a format/container duration slightly longer than its
primary video stream because the AAC stream contains encoder padding. Seeking a
final review frame from the container duration can then land after the last
video frame and make FFmpeg return no image.

Compare the embedded full ffprobe result in the retained byte-bound envelope
rather than looking at only one duration:

```powershell
$boundProbe = Get-Content -Raw .\artifacts\candidate.bound-probe.json | ConvertFrom-Json
$boundProbe.subject | Select-Object bytes, sha256
$boundProbe.ffprobe.format | Select-Object format_name, duration
$boundProbe.ffprobe.streams | Select-Object index, codec_type, codec_name, duration, avg_frame_rate
```

The current review planner preserves the honest container duration in artifact
metadata and in the full-watch requirement, but clips frame seeks to the
primary video stream and subtracts one frame interval. Confirm the computed
last seek without writing anything:

```powershell
$reviewPlan = & $promoPython -m xar_promo review .\artifacts\candidate.mp4 `
  --storyboard .\artifacts\storyboard.json `
  --probe .\artifacts\candidate.bound-probe.json `
  --output-directory .\attempts\review-plan-001 `
  --audit-directory .\attempts\review-plan-audit-001 `
  --ffmpeg $ffmpeg `
  --plan-only | ConvertFrom-Json
$reviewPlan.artifact.duration_seconds
$reviewPlan.frame_plan[-1] | ConvertTo-Json -Depth 8
```

The last `-ss` must be before the reported primary-video duration. If it is
derived only from the longer container, first confirm that the current
worktree's `xar_promo.review` is loaded, then regenerate the bound probe through
`xar_promo.probe_and_write_bound_media`, which invokes ffprobe with both
`-show_streams` and `-show_format` and retains the command audit. Bare ffprobe
JSON is not accepted by `review`. Do not falsify or shorten the declared
artifact duration to make the extraction pass.

## Stale partial or exclusive output collision

The pipeline intentionally refuses to overwrite attempt material. Defined
messages include:

- `attempt output already exists; use a new workdir and retain the old one`;
- `stale partial output must be audited or moved before retry`;
- `refusing to overwrite final output`, review frame, review template, review
  package, process audit material, audit report, run manifest, or release
  bundle.

Inventory the named location and its command evidence:

```powershell
$failedAttempt = ".\attempts\build-001"
Get-ChildItem -LiteralPath $failedAttempt -Force -Recurse |
  Select-Object FullName, Length, LastWriteTime
Get-ChildItem -LiteralPath $failedAttempt -Recurse -Include command.json,result.json,stdout.txt,stderr.txt
```

An existing `.partial` file is evidence of an interrupted or failed producer,
not permission to promote it. Keep the complete old directory untouched. Retry
with `build-002`, `review-002`, a new audit report path/artifact ID, or a new
export destination as applicable. Never delete a collision merely to reuse an
attempt number, and never overwrite a RED report with a GREEN retry.

## Edge TTS cache, offline miss, or network failure

The optional live provider is pinned by this package to `edge-tts==7.2.8`.
Verify the selected interpreter before diagnosing the service:

```powershell
& $promoPython -c 'import importlib.metadata as m, edge_tts; print(m.version("edge-tts")); print(edge_tts.__file__)'
```

The cache fingerprint includes provider ID/version, text, voice, rate, pitch,
volume, audio format, and `cache_salt`. A change to any of them is a different
cache entry. Existing entries are accepted only when metadata, bytes, SHA-256,
and offline audio validation all agree.

Use the frozen offline switch to distinguish a local-cache problem from a live
provider attempt:

```powershell
& $promoPython -m xar_promo build .\runs\render-001\run-manifest.json `
  --workdir .\attempts\build-offline-001 `
  --composer my_project.promo:compose `
  --offline-tts
```

`offline TTS cache validation found no valid entry: <fingerprint>` means no
network call was attempted and no valid local entry matched the exact request.
Do not reinterpret it as an Edge service outage. Check the request inputs,
provider version, configured cache root, and preserved cache metadata.

Without `--offline-tts`, a cache miss may call Edge TTS. Provider exceptions,
including network failures, are retried only up to `--max-tts-attempts` with
the configured `--retry-backoff-seconds`; exhaustion produces
`TtsSynthesisError` with every attempt's error and does not publish partial
audio as a valid cache entry. Keep the build outcome, run phase record,
workdir, existing cache, and `.quarantine` entries. Retry later in a new build
workdir with identical request inputs; do not edit cache metadata or copy a
partial file into a content-addressed entry.

## Planned or unsigned work makes release validation RED

`plan`, successful `build`, `audit`, and `review` never create human approval.
A plan may be GREEN while chapters remain `planned`; a successful build ends
with project audit pending and `signoff_recorded=false`; an automated audit
records `manual_approval_granted=false`; and a review package remains
`pending-human-review`.

Run both the release validator and an offline export preflight:

```powershell
& $promoPython -m xar_promo validate .\runs\render-001\run-manifest.json `
  --profile release `
  --json

& $promoPython -m xar_promo export .\runs\render-001\run-manifest.json `
  .\dist\release-check-001 `
  --policy .\release-export-policy.json `
  --validate-only
```

Release validation fails closed if the input is not a native run, if the bound
config has no chapters or any chapter is still `planned`, if referenced
artifacts/locales are missing, if there is no preserved `role="deliverable"`
artifact, or if no deliverable has a latest explicit human `approved` sign-off.
Export additionally requires the policy-selected deliverable itself to be the
approved one.

Do not edit an old run's bound config snapshot. Mark the checked-in authoring
chapters ready only after their real prerequisites are met, start a new run,
build and preserve the exact candidate, create the pending review material,
have a named human watch the exact bytes at 1.0x, and only then record
`signoff --decision approved`. Preserve the earlier planned/unsigned RED run as
process history.
