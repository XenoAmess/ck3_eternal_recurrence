# XAR Promo Toolchain

`xar-promo-toolchain` is a reusable foundation for promotional-video pipelines. Version `0.1.0` provides separate project/run contracts, immutable process-material retention, provider-neutral TTS, dependency-injected media orchestration, automated-audit and human-review boundaries, and offline release-bundle export. A project supplies its own adapter, preset, and `PipelineComposer`; this is an orchestration toolchain, not a timeline editor or upload service.

The real CLI has ten commands:

- `init` creates `promo-project.json` and the first bound run;
- `start-run` creates another run with an immutable snapshot of the current config;
- `validate` checks a native config/run or a legacy showcase v1 manifest;
- `preserve` copies bytes into content-addressed run storage and appends an artifact;
- `signoff` records a named human decision bound to exact preserved bytes;
- `plan` composes and validates a pipeline attempt with zero writes;
- `build` runs a composed pipeline and preserves GREEN or RED material;
- `audit` creates and appends an automated audit without human approval;
- `review` plans or creates a pending human-review package;
- `export` validates or creates an offline, allowlisted release bundle.

There is no `publish` or upload command. `audit`, `review`, and `signoff` are intentionally separate operations.

## Release artifact handoff

The first release workflow is intentionally limited to package evidence. A
`xar-promo-v<version>` tag (or a manual workflow run) builds and checks the
0.1.0 wheel and source distribution, validates the sdist contents, performs
isolated installs of both artifacts, writes `SHA256SUMS`, and uploads those
files as a GitHub Actions artifact. It does not publish to PyPI or any other
index, create a GitHub Release, upload media, or start CK3/FFmpeg. See
[Installation and cross-machine delivery](docs/installation.md) for the exact
artifact, reproducibility, and trust boundaries.

## Install and inspect

Python 3.11 or later is required.

For Windows, Linux, macOS, wheel/sdist/source/editable installs, optional
dependencies, offline wheelhouses, verification, upgrades, and uninstall, see
[Installation and cross-machine delivery](docs/installation.md). Automation can
read the installed machine contract at
`xar_promo/schemas/install-contract-v1.json` through `importlib.resources`.

```powershell
py -m pip install -e .
py -m xar_promo --help
py -m xar_promo init --help
py -m xar_promo start-run --help
py -m xar_promo validate --help
py -m xar_promo preserve --help
py -m xar_promo signoff --help
py -m xar_promo plan --help
py -m xar_promo build --help
py -m xar_promo audit --help
py -m xar_promo review --help
py -m xar_promo export --help
```

The core has no required dependency outside the standard library. Install only the optional slice an integration needs:

```powershell
py -m pip install -e ".[tts]"     # edge-tts 7.2.8
py -m pip install -e ".[visual]"  # Pillow 12.3.0
py -m pip install -e ".[render]"  # Pillow 12.3.0
```

`edge-tts` is loaded only for live Edge synthesis. FFmpeg and ffprobe are external executables and are not Python dependencies.

## Project and run lifecycle

Create authoring intent and a first run without overwriting existing files:

```powershell
xar-promo init C:\work\my-promo `
  --project-id my-promo `
  --title "My Promo" `
  --run-id capture-001 `
  --narration-locale zh-CN `
  --subtitle-locale zh-CN `
  --subtitle-locale en

xar-promo validate C:\work\my-promo\promo-project.json
xar-promo validate C:\work\my-promo\runs\capture-001\run-manifest.json
```

The `init` defaults `adapter=generic` and `preset=default` are neutral scaffold identifiers, not bundled production components. Before `plan`, `build`, or `audit`, edit the checked-in config to the IDs supplied by an installed integration plugin. Plugins publish callables through the `xar_promo.adapters` and `xar_promo.presets` Python entry-point groups.

After changing the config, start a new run. An older run keeps its original content-addressed config snapshot.

```powershell
xar-promo start-run C:\work\my-promo\promo-project.json --run-id render-001
```

`promo-project.json` owns intent: project identity, adapter/preset IDs, locales, constraints, chapters, and cues. `runs/<id>/run-manifest.json` is an append-only evidence ledger containing a config snapshot binding, typed phase history, immutable artifacts, typed automated audits, and explicit human sign-offs. Every mutation archives the prior manifest bytes before atomic replacement.

## Plan and build

The project provides a callable implementing the documented `PipelineComposer` ABI:

```powershell
xar-promo plan C:\work\my-promo\promo-project.json `
  --workdir C:\work\my-promo\attempts\plan-001 `
  --composer my_project.promo:compose `
  --validate-only

xar-promo build C:\work\my-promo\runs\render-001\run-manifest.json `
  --workdir C:\work\my-promo\attempts\render-001 `
  --composer my_project.promo:compose
```

`plan` is always read-only, whether or not the explicit `--validate-only` marker is present. It does not create the workdir, invoke TTS/FFmpeg, or mutate a run. `build` requires a native run and preserves complete outputs plus partials, stdout/stderr, and diagnostics from a failed attempt before appending typed phases.

The composer is loaded with strict `MODULE:ATTRIBUTE` syntax. The CLI passes resolved adapter and preset factories to it without invoking them or guessing their signatures. The composer owns concrete media dependencies and executable selection.

## Audit, review, sign-off, and export

`review --probe` accepts a byte-bound v1 envelope, not bare ffprobe JSON. Create
it from a live ffprobe invocation with the public producer; the command audit,
stdout, stderr, and envelope are retained at caller-selected paths:

```python
from pathlib import Path

from xar_promo import probe_and_write_bound_media

probe_and_write_bound_media(
    r"C:\tools\ffprobe.exe",
    Path(r"C:\exports\promo-final.mp4"),
    output_path=Path(r"C:\exports\promo-final.bound-probe.json"),
    audit_directory=Path(r"C:\exports\probe-audit"),
)
```

The envelope records the exact deliverable byte count and SHA-256 and embeds
the live ffprobe result. Bare, stale, or differently bound probes are rejected,
including in zero-write `--plan-only` mode.

```powershell
xar-promo audit C:\work\my-promo\runs\render-001\run-manifest.json `
  --subject-artifact-id promo-final `
  --evidence-bundle artifacts\evidence-bundle.json `
  --report artifacts\automated-audit.json `
  --report-artifact-id automated-audit-001

xar-promo review C:\exports\promo-final.mp4 `
  --storyboard C:\exports\storyboard.json `
  --probe C:\exports\promo-final.bound-probe.json `
  --output-directory C:\exports\review `
  --audit-directory C:\exports\review-audit `
  --ffmpeg C:\tools\ffmpeg.exe `
  --plan-only
```

`--plan-only` is optional preflight and is not review evidence. Run the real review command without that flag to extract frames and create the pending package:

```powershell
xar-promo review C:\exports\promo-final.mp4 `
  --storyboard C:\exports\storyboard.json `
  --probe C:\exports\promo-final.bound-probe.json `
  --output-directory C:\exports\review `
  --audit-directory C:\exports\review-audit `
  --ffmpeg C:\tools\ffmpeg.exe
```

The named human must then review the exact deliverable bytes in full at 1× speed and explicitly state an `approved` or `rejected` decision. Only after that statement may it be recorded:

```powershell
xar-promo signoff `
  --run-manifest C:\work\my-promo\runs\render-001\run-manifest.json `
  --artifact-id promo-final `
  --reviewer "Reviewer Name" `
  --decision approved

xar-promo export C:\work\my-promo\runs\render-001\run-manifest.json `
  C:\work\my-promo\dist\release-001 `
  --policy C:\work\my-promo\release-export-policy.json `
  --validate-only
```

`audit` appends only an automated result. `review` remains `pending-human-review`; neither a plan nor a generated review package is approval. Only `signoff` records the named reviewer's explicit decision. Release-profile validation requires ready chapters and a preserved deliverable whose latest explicit sign-off is approved. `export --validate-only` and `--dry-run` are no-write preflights; normal export copies a strict allowlist into a new local directory. Export never contacts a network service.

## Retention layout

```text
my-promo/
|-- promo-project.json
`-- runs/
    `-- render-001/
        |-- run-manifest.json
        `-- artifacts/
            |-- project-config/sha256/...
            |-- raw/sha256/...
            |-- derived/sha256/...
            `-- manifest-history/sha256/...
```

Preservation copies; it never moves, edits, or deletes source material. Failed and superseded attempts remain process evidence.

## Reusable layers

- `src/xar_promo/` contains models, validation, typed runlog operations, retention, TTS, storyboard, visual-source, media/layout, pipeline, review, audit, and export primitives.
- `src/xar_promo/adapters/` contains domain adapters. The CK3 adapter verifies an existing capture bundle without OCR interpretation or mutation.
- `src/xar_promo/presets/` isolates project policy from the generic core and adapters.

See [Architecture and migration](docs/architecture-and-migration.md), [CLI and manifest v1](docs/cli-and-manifest-v1.md), [Pipeline composition](docs/pipeline-composition.md), [Human review and sign-off](docs/review-and-human-signoff.md), [Export and release bundles](docs/export-and-release-bundle.md), [Migrating existing builders](docs/migrating-existing-builders.md), and [Troubleshooting](docs/troubleshooting.md).

## Test

```powershell
py -m unittest discover -s tests -v
py -O -m unittest discover -s tests -v
```

The project is licensed under GPL-3.0-only.
