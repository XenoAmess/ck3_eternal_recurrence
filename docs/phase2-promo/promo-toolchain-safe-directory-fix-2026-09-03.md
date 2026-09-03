# Promo toolchain checkout identity fix (2026-09-03)

## Reproducible symptom

The standalone promo-tool checkout is intentionally kept outside the mod
source tree.  On this machine it is owned by a different Windows service
account than the account running the production scripts.  Before this fix, a
real read-only media preflight failed at the checkout identity probe:

```text
fatal: detected dubious ownership in repository at
'Z:/ck3_mod_rewrite/_runtime/promo-tool-fresh-20260903'
```

The failure happened before footage validation, even though the checkout was
clean and `HEAD == origin/main`.

## Minimal fix

Both production identity paths now bind every read-only Git probe to the exact
selected checkout:

```text
git -c safe.directory=<resolved-checkout> -C <resolved-checkout> rev-parse HEAD
git -c safe.directory=<resolved-checkout> -C <resolved-checkout> rev-parse origin/main
git -c safe.directory=<resolved-checkout> -C <resolved-checkout> status --short
```

The change is in `preflight_phase2_media.py` and
`build_phase2_promo_video.py`.  It does not add a global Git configuration
entry, broaden the trusted path, fetch anything, or relax the `HEAD ==
origin/main` and clean-worktree checks.

## Verification

- Fresh checkout was fetched with `git fetch origin main --prune`.
- Checkout remains clean at
  `57c42fca13ea459432c1caf76e069a1fbccf602c`, equal to `origin/main`.
- Focused preflight + builder tests: `33 passed`.
- Full phase-two promo test selection (queue/intake/completion/authoring/
  preflight/promotion/planner/builder): `78 passed`.
- Real no-media preflight was run once for each cut.  Both returned process
  exit `0` and `PHASE2 MEDIA PREFLIGHT: GREEN`; the final readiness remains
  honestly `RED` only for `footage_pending` and `publish_target_pending`.
- The resulting receipts explicitly report `ck3_started=false`,
  `tts_synthesis_performed=false`, `subtitle_media_written=false`, and
  `ffmpeg_encode_started=false`.

This fixes the checkout-ownership blocker only.  It does not promote the old
fixture to phase-two footage and does not create TTS, subtitles, candidate
media, or MP4 files.  Before real rendering, repeat the required fresh fetch,
HEAD/clean check, and media preflight against the then-current tool commit.
