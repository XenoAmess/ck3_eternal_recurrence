# Review and human sign-off

The review pipeline deliberately separates three facts that must never be
collapsed into one another:

1. `xar-promo review` plans or materializes evidence for a human review;
2. a named human watches the exact deliverable and decides whether it is
   acceptable;
3. `xar-promo signoff` records that human decision against the already
   preserved artifact's exact byte count and SHA-256.

A successful frame extraction, a `pending-human-review` package, or a GREEN
automated audit is not approval. Neither `review` nor `audit` calls the sign-off
operation. Conversely, `signoff` only records a decision supplied by a human;
it does not play, inspect, OCR, or otherwise review the video on that person's
behalf.

## State flow

```text
generated deliverable
  -> review --plan-only                 (planned; zero writes)
  -> review                             (pending-human-review package)
  -> named human watches exact bytes at 1.0x
  -> preserve exact deliverable in a native RunManifest
  -> signoff --decision approved        (release may continue)
  -> signoff --decision rejected        (retain it; render a new artifact)
```

The order of review-package creation and preservation may be swapped, but the
human decision must identify the same bytes that are preserved and signed off.
If the bytes change at any point, the previous review and approval do not carry
forward.

## Plan-only review

Use plan-only mode before running FFmpeg when validating a proposed storyboard,
probe, timeline, paths, and extraction points:

First create the required byte-bound v1 probe envelope through the public live
producer. This runs ffprobe and retains its command audit; it refuses to wrap a
probe whose reported filename or byte count does not match the deliverable:

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

The envelope has the strict shape below. `subject` binds the embedded raw
ffprobe result to the exact deliverable bytes:

```json
{
  "format_version": 1,
  "kind": "xar-promo-bound-media-probe",
  "subject": {"bytes": 12345, "sha256": "<64 hex characters>"},
  "ffprobe": {"streams": [], "format": {}}
}
```

```powershell
xar-promo review artifacts/final.mp4 `
  --storyboard artifacts/storyboard.json `
  --probe artifacts/final.bound-probe.json `
  --output-directory artifacts/review-attempt-001 `
  --audit-directory artifacts/review-audit-attempt-001 `
  --ffmpeg ffmpeg `
  --plan-only
```

`--plan-only` reads and hashes the deliverable, reads the storyboard and
retained bound-probe envelope, validates its byte/SHA binding and the timeline,
and prints the deterministic frame plan as JSON. It performs no `mkdir`, process invocation, template write,
package write, sign-off, or approval. The returned state is `planned`, with
`writes_performed=false`, `is_signoff=false`, and
`approval_granted=false`.

Invalid or bare JSON, a missing deliverable, a stale byte binding, a probe without usable video duration, an
overlapping or out-of-range chapter, or an unsafe output plan fails closed.

## Creating a pending review package

Run the same command without `--plan-only` to execute the declared FFmpeg frame
extractions:

```powershell
xar-promo review artifacts/final.mp4 `
  --storyboard artifacts/storyboard.json `
  --probe artifacts/final.bound-probe.json `
  --output-directory artifacts/review-attempt-001 `
  --audit-directory artifacts/review-audit-attempt-001 `
  --ffmpeg ffmpeg
```

On success the output directory contains extracted PNG frames,
`review-template.json`, and `review-package.json`. The package binds the
deliverable bytes and SHA-256, storyboard chapters, frame timestamps, frame
bytes and hashes, and command-audit directories. Its state remains
`pending-human-review`; its human fields are empty and it explicitly records
`is_signoff=false` and `approval_granted=false`.

The package is a navigation and evidence aid. Sampled frames help inspect the
first frame, final frame, chapter edges, and declared internal boundaries, but
they do not replace continuous playback of the source clips or final
deliverable.

The stable programmatic equivalent is:

```python
from pathlib import Path

from xar_promo.review_commands import run_review_command

result = run_review_command(
    ffmpeg="ffmpeg",
    deliverable_path=Path("artifacts/final.mp4"),
    storyboard_path=Path("artifacts/storyboard.json"),
    probe_path=Path("artifacts/final.bound-probe.json"),
    output_directory=Path("artifacts/review-attempt-001"),
    audit_directory=Path("artifacts/review-audit-attempt-001"),
    plan_only=False,
)
print(result.to_dict())
```

## What the human must review at 1x

The reviewer must play the exact artifact continuously from the first frame to
the final frame at exactly `1.0x`, without skipping, scrubbing, or fast
playback. At minimum, the generic checklist requires the reviewer to confirm:

- picture and sound remain present, synchronized, and uninterrupted;
- subtitles and on-screen text are readable, correctly timed, and inside the
  visible frame;
- the first and final frames enter and exit cleanly;
- every storyboard chapter is watched continuously and its start, end, and
  declared boundaries agree with the extracted evidence.

Project adapters and release presets may add stricter content attestations.
The established CK3 promotional preset uses these five explicit attestations:

| Attestation | Human meaning |
|---|---|
| `historical_characters_only` | Every visible character covered by the policy is an authorized historical/provenance-bound character, not a temporary or generated substitute. |
| `no_generated_official_name_visible` | No prohibited world-generated official name is visible anywhere in the reviewed material. |
| `fixture_test_ui_absent` | No fixture-only or test-only decision, button, event, label, marker, or other test UI is visible. |
| `full_clip_reviewed` | Every included live clip is watched in full at 1.0x and every included still is inspected; frame sampling is not substituted for this review. |
| `no_crop_mask_or_redaction` | Compliance comes from clean source material, not from hiding disallowed content with cropping, masking, blurring, or redaction. |

These five names are a preset contract, not hard-coded universal assumptions
inside the generic review command. An adapter that requires them must retain a
separate structured human-response record or signed review spec containing all
five results and bind that record to the reviewed artifact. The generic
`signoff` note may cite that record, but a prose note is not a replacement for
structured attestations required by the adapter.

Source-footage review and final-deliverable review are separate gates. A final
composition can introduce broken overlays, clipped lower thirds, mistimed
subtitles, contaminated labels, or a bad first/final frame after every source
clip has passed. The finished deliverable therefore needs its own complete
1.0x viewing and its own decision bound to the final MP4 bytes.

## Recording the human decision

The deliverable must first be present as an artifact in a native run manifest.
For example:

```powershell
xar-promo preserve artifacts/final.mp4 `
  --run-manifest runs/release-001/run-manifest.json `
  --artifact-id promo-final-r001 `
  --collection derived `
  --role deliverable `
  --media-type video/mp4
```

After a named reviewer has actually completed the applicable checklist, record
their decision:

```powershell
xar-promo signoff `
  --run-manifest runs/release-001/run-manifest.json `
  --artifact-id promo-final-r001 `
  --reviewer XenoAmess `
  --decision approved `
  --reviewed-at 2026-09-01T12:00:00+08:00 `
  --note "Watched continuously at 1.0x; structured review record: review-response-r001.json"
```

Use `--decision rejected` whenever any required check fails. `signoff` appends a
record containing its sequence, reviewer, timestamp, decision, artifact ID,
byte count, and SHA-256. It refuses unknown artifact IDs and does not rewrite
old sign-off rows. The latest sign-off for an artifact controls current release
validation, and the policy-selected deliverable must have its own latest
`approved` decision; approval of some other deliverable is insufficient.

The reviewer identity and decision are human assertions. Automation must not
fill them, infer them from a GREEN command, or call `signoff` as a side effect
of review, audit, build, or export.

## Rejection and replacement artifacts

A rejected artifact and its evidence remain part of the history. Do not delete
the rejection, edit the failed video in place, overwrite its review package, or
change the original artifact binding.

When a defect is fixed:

1. render new bytes to a new candidate path;
2. preserve them with a new artifact ID (and normally a new run/attempt ID);
3. create a new review package in new output and audit directories;
4. repeat the complete 1.0x human viewing and every applicable attestation;
5. sign off the new artifact ID with a new decision.

A later approval on unchanged bytes may record a genuine human re-review, but
it must not be used to pretend that rejected bytes were modified. Changed bytes
always mean a new artifact and a new review.

## Audit is not sign-off

| Record | What it proves | What it cannot prove |
|---|---|---|
| Review package | The deliverable, timeline, frame plan, extracted frames, and command evidence are byte/hash bound and ready for a person. | That a person watched it or approved it. |
| Automated audit | Artifact integrity and declared evidence completeness passed deterministic checks. It always reports `manual_approval_granted=false`. | Visual taste, semantic correctness, the five human attestations, or release approval. |
| Human sign-off | A named human explicitly recorded `approved` or `rejected` for exact preserved bytes. | That automated audit checks passed, or that an external publication occurred. |

An audit may read an already existing sign-off from a run manifest and report
its state alongside automated results. That read does not create, upgrade, or
replace the sign-off. Likewise, an approved sign-off does not repair a failed
audit; both gates must independently satisfy the selected release policy.

## Failure-material retention

Frame extraction writes a partial PNG before promoting it to the final frame.
If any command fails, completed frames, the failed partial, and that command's
`command.json`, `stdout.txt`, `stderr.txt`, and `result.json` audit material are
left in place. The pending template and package are written only after every
planned extraction succeeds.

Do not clean or reuse a failed attempt directory. Existing final frames,
partials, templates, packages, and command-audit paths are collision protected
and intentionally fail closed. Retry in a new attempt directory, preserving the
old raw renders, probes, sidecars, review material, automated RED reports, and
human rejection records for diagnosis and provenance.

No command in this workflow uploads, publishes, or grants external-platform
approval.
