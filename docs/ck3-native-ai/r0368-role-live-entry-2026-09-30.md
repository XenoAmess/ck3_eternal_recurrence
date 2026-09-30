# R0368: executable managed role entry

The new module `xar_autoplayer.r0368_actor_army_role_live` replaces the dormant
worker path for a new attempt. It has `--no-launch`, `--prepare`, and `--live`
modes. Preparation creates a separate isolated profile with the production mod
disabled, copies the frozen source checkpoint/driver/sidecar, and calls the
existing ordinary seed rebinder. It does not launch a game.

Native inputs remain the exact Release attempt 005 pair, tied to clean role
source checkout `2ad213f569d1f8369b4b9ae56728780d94cdfb28`, whose native tree
equals build source `7457ef060cdfa1c943c86be619df02dbbb247dd0`. The Python
runtime comes from the new current master source; its commit is recorded
separately. A changed master native tree does not reinterpret or rebuild this
historical pair. The 915/915 build and two 173/173 CTest/JUnit runs are reused.

The module CLI is run with the explicitly verified project venv and project
`ck3_autonomous_player/src` on `PYTHONPATH`. All three modes require
`--candidate-manifest`, `--release-pair-manifest`, `--role-source-checkout` and
a fresh `--attempt-dir`. Prepare also requires `--game-dir`. Live additionally
requires the prepared manifest, fresh role GO, full live run ID, exact actor,
episode, WarID and ArmyID, plus the canonical bus source/SHA and current screen
task/sequence. The entry renews one `ScreenLeaseKeeper`; its creation gate is
passed to the common `native_session` through `before_process_create`.

The one native query uses the already reviewed transport and collector. A new
semantic frame must be paused/map-ready, contain the played actor and one
current owned army matching one allied army in the requested war, and publish
positive native revision plus connection/PID/hello identity. The source
candidate's WarID `16777231` and ArmyID `83886367` are only historical hints;
the new frame must validate them. Before/after frames and raw typed role are
saved separately. No gameplay action, date advance, role release or activity
Start is submitted. Global role remains unknown and safe release remains null.

The previous R0368 source run ended without a typed role row. Its original
tuple is actor `29829`, episode `native-29829-2bc2d599f7f9`, H3928, raw date
`53219928`, checkpoint SHA
`A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C`.
The later H3937 checkpoint SHA `92A06F...DAF6` is a distinct new source input;
it is never a retroactive R0368 observation. Fixed WAR ZIP
`14C19E307AD624095C95476EBF626BF006AB29E03334F55A7D1CA2DB081EE557`
contains a historical report and receipt, and adds no current typed role row.

The worker stops its managed session, closes the driver, stops lease renewal,
and reads the final CK3 inventory before completing. The source remains
**live 0/1** until a new actual role read and complete process cleanup succeed.
No screen lease or Steam operation was performed while writing this source.

## 2026-09-30 15:03 correction

The first entry draft constructed the generic driver with its default rogue
one-life binding. That does not match the officially rebound ordinary
`xar_off` driver-state and would stop at hello adoption. The corrected entry
verifies the prepared `xar_off` profile, derives the existing ordinary/no-pact
binding, and supplies `succession_lifecycle_binding` to the driver constructor.
Its focused execution fixture now checks that exact constructor input. The
first draft, freeze and no-launch/preparation receipts remain preserved; none
of those receipts represented a live role read.
