# CK3 profile-state A/B control (2026-09-03)

This note indexes the disposable profile controls prepared for the startup
forensics.  Materialization was data-only: no CK3 process was started, no real
`Documents\Paradox Interactive\Crusader Kings III` profile was touched, and
no agreement/store/payment/gameplay action was performed.

## Controls

The seed profiles and complete per-file inventory are outside the release tree:

* `Z:\ck3_mod_rewrite\_runtime\startup-profile-ab-20260903\A-known-good-bare-nomod\profile`
* `Z:\ck3_mod_rewrite\_runtime\startup-profile-ab-20260903\B-stale-presets-tutorial-no-etags\profile`
* manifest: `Z:\ck3_mod_rewrite\_runtime\startup-profile-ab-20260903\manifest.json`
* runner handoff: `Z:\ck3_mod_rewrite\_runtime\startup-profile-ab-20260903\README.md`

| arm | files | bytes | tree SHA-256 |
|---|---:|---:|---|
| A known-good bare no-mod | 4,973 | 217,205,780 | `c73c23d2566a79dc5c5835b70da5720b554ea85ed025f08ef7b8e85c6e12c85f` |
| B stale profile-state variant | 4,974 | 217,208,525 | `8443cc2fcfc79563cc939055fb67b32928697600ac243f54f90d354043369922` |

Both arms use the same `pdx_settings.txt` (6,882 B,
`e04dddc053e2850407da6c40d044e241f355e5bb079d4608331789494e45e887`),
`dlc_signature` (33 B,
`4088d58f8d14f174f83e4cde0de6a3c6fe45011b546d6a407589f261bf0d7498`),
account bytes, and all 4,968 DX11 shader-cache files.  Mods, saves,
`dlc_load.json`, and transient logs/crash dumps are excluded; matching empty
runtime directories are present.

The original stale run's cache had 4,940 files / 215,365,589 bytes.  It is a
strict subset of the known-good cache: all 4,940 common paths have identical
hashes and the known-good cache has 28 additional files.  B deliberately uses
the complete known-good cache so cache coverage cannot confound this three-path
profile-state comparison.  B is therefore a synthetic stale-state variant,
not a whole-profile clone of the earlier timeout run.

Exactly three file paths differ:

| path | A | B |
|---|---|---|
| `account/PDX/SDK/ck3/eTags.json` | present, 12 B, SHA `936e00ad675372f7a84189a0fe9b236238c781da119b3fd7b074060f0efb7947` | absent |
| `player/game_rules/presets.txt` | absent | stale source bytes, 2,699 B, SHA `de89cb7ad380d0df87ca087896a02b46de9c3334d78b1a31cb7c81a014337574` |
| `tutorial.txt` | absent | profile-source bytes, 58 B, SHA `4e009f2b0764d78793a89e109fc5bc019b6c1e3f65c8553bd085a0af483217aa`; same as the normal formal-runner default, so presence/absence only |

## Read-only validation contract

These are seed controls, not writable run directories.  The recovery runner
must clone one arm into a fresh per-run `-userdir`, use one CK3 process at a
time, and hold the pinned executable/build, CWD, desktop, argument vector, and
bridge-disabled mode constant.  The recommended no-mod command shape is
`-nolauncher -noWorkshop -debug_mode -gdpr-compliant -userdir=<fresh clone>`;
do not add `-loadsave` or `-continuelastsave`, inject a bridge, or send gameplay
input.  Capture Frontend/history markers, screenshot/window evidence,
`debug.log`/`error.log`, crash RVA/exit code, cleanup proof, and before/after
clone inventories.

The A/B result is currently a hypothesis pending that single-slot run.  A is
the known-good baseline; B tests whether the three stale profile-state paths
alter startup.  A difference is follow-up evidence, not causal proof by itself.
