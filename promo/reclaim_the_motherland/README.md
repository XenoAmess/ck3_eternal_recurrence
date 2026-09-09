# Reclaim the Motherland promo project

This directory contains project-specific intent and integration for the reusable
`xar-promo` toolchain. It deliberately lives outside
`mod_reclaim_the_motherland/`, whose exact runtime tree is protected by the
release and CK3 preflight allowlists.

Authoritative inputs:

- `promo-project.json` — checked-in `ProjectConfig`.
- `promo-policy.json` — approved 88-second picture body plus 8-second music tail.
- `music-selection-a03.json` — A03 identity and the user's source/rights attestation.
- `integration/` — entry-point adapter, preset, composer, narration preparation,
  and focused tests.

Use the verified project interpreter and install the integration before invoking
the generic CLI:

```powershell
$python = 'D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe'
& $python -m pip install -e 'promo\reclaim_the_motherland\integration'
& $python -m xar_promo validate 'promo\reclaim_the_motherland\promo-project.json' --json
```

Every narration, capture, render, audit and review attempt uses a new directory
under `D:\workspace\ck3_reclaim_promo_work`. Failed attempts and all process
materials are retained. Automated audit is not human signoff; final MP4 bytes
must be watched continuously at 1× before `signoff` and release export.

CK3 recording is gated on the real game window but uses full-desktop GDI capture:
direct GDI capture of CK3's GPU-rendered window can produce an all-black stream.
Each attempt sparsely extracts and hashes frames after recording; fewer than two
distinct non-black samples makes the attempt RED even when FFmpeg exits cleanly.
