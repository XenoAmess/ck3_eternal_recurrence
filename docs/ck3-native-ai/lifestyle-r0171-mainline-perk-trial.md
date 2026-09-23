# R0171 Robert wartime perk: independent mainline candidate

Status: **R0175 production-live typed submit pending, postcondition RED**.
The candidate has not proved a material perk, a paired post-action checkpoint,
the peaceful M4 two-year gate, or public LIFE registration. The R0171 war RED
remains separate.

## Source and entry

R0171 cold-restored the Robert h1333/raw53194440 checkpoint, actor `29829`,
then stopped on formal war-planner RED
`complete-matching-active-native-move-intent-route` after five read-only
queries. No gameplay action or date advance occurred. The source pair is
`R0171-final-frozen-pair` under
`Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-r0171-route-intent-red-20260923`:
save SHA-256 `2B8933FCD6AC1DBE29EA2796AB07AE722F0585658EA1BE01380C87FF8097F98A`,
driver SHA-256 `FBE3A287745BC4D2D4E712633688A9FDDC45CF01C0793FF70A60CD2B598DD177`.
These values identify this source, not a hardcoded policy actor or date. The
R0171 query tail after h1333 must be trimmed by the official prepare/rebind;
the original pair stays immutable.

The ordinary formal `native-auto-run` cannot reach private LIFE while the
war planner is blocked. The existing three-query runner is explicitly
read-only. `run_player_lifestyle_wartime_perk_trial.py` is a separate opt-in
action runner with its own `read_only=false` candidate schema. It reuses the
official `g2_preview_operator.py prepare-state` and no-launch pair/profile
preflight. The candidate must be built from a committed Python source and a
matching private slot43 DLL on the frozen 1.19.0.6 EXE. The 0-action R0167
readback cannot be carried forward as action legality.

## Bounded formal sequence

On a new paused frame, the runner checks the manifest actor/episode/date,
active war IDs, no event or pending character interaction, and a same-frame
campaign-root proof of ordinary feudal war scope. It obtains a fresh private
native final-legal perk query and the existing minimum policy must choose the
one allowlisted `cutting_corners_perk` from an already selected stewardship
focus with an unspent point. A formal war plan is sampled before the submit;
an executable war step takes priority, so this candidate submits nothing in
that case. A blocked or query-only war plan can leave the independent perk
trial eligible.

The existing private typed transport then submits **one** perk. The runner
waits for a later paused native revision and uses the independent native
receipt to prove `HasPerk=true`. It saves an official paired checkpoint
before further queries. A fresh LIFE2 read must prove the same actor,
episode, date and focus, target ownership, unspent points minus one and used
points plus one. The following formal turn must consume the matching
receipt. No war action or date advance is executed by this runner. Its report
records both the new checkpoint and the following war plan; a continuing war
RED is preserved as a separate blocker rather than a perk failure.

If a typed send becomes uncertain, the candidate stops. The source may not be
replayed blindly: the action's actual material state must be checked first.
If the checkpoint was saved but a later point or turn check fails, that
derived pair remains a traceable recovery source and the action is not
repeated. A successful trial changes the mainline pair to the **new** save
and driver hashes; the old h1333 pair and PRV008 remain separate. The
single-instance owner must cold-restore the derived pair and recheck the
still-open war route before advancing the date.

The exact-build native AI decision tree, perk parent graph and query/action
seams are in [lifestyle-focus-perk-ai.md](lifestyle-focus-perk-ai.md).
R0167 readback and wartime policy scope remain in
[lifestyle-r0167-robert-readback.md](lifestyle-r0167-robert-readback.md) and
[lifestyle-r0167-war-perk-scope.md](lifestyle-r0167-war-perk-scope.md).

## R0175 post-submit frame RED and focused repair

R0175 used the exact 1.19.0.6 EXE and a private slot43 DLL from native source
`66f926d339ac57c6305e3789a239b5cb9779acdd`. Its retained
`g2-m4-robert-r0175-wartime-perk-live-20260923/report.json` under the Z:
process-asset root has SHA-256
`42A80DF44D07E4C3CD8CD7C2FFA819B80AD519B0E85ACD7B0B9D4F1AE670D88B`.
The driver command history records a durable `action_state_unknown` intent at
index 1340 and `submitted_verification_pending` native ACK for the **same**
action ID at 1341. It does not contain a later paused native frame or receipt.
The save remained h1333 with SHA-256
`2B8933FCD6AC1DBE29EA2796AB07AE722F0585658EA1BE01380C87FF8097F98A`;
there is no post-action checkpoint. The process tree was actually reclaimed,
but the runner also folded its 603.8-second wall overrun into
`ck3_reclaimed=false`, mislabeling this as `red_cleanup`.

The bridge's coarse `GameAdapter::Snapshot` excludes lifestyle points and
perks. After the main-thread typed submit ACK, paused/date/map/war fields did
not change. `PublishSnapshot` therefore deduplicated every heartbeat and
kept native revision 3; both the runner and native receipt require a later
revision. This is a concrete postcondition transport defect, not evidence
that `cutting_corners_perk` was acquired or rejected. The private bridge now
forces **one real `ReadSnapshot` publication after the matching pending
submit**, even when the coarse map fields are unchanged. The native receipt
still checks the same action ID and material `HasPerk` on that later frame;
the ACK never counts as applied. The runner separately reports process
reclamation and wall-budget outcome and reserves 15 seconds for controlled
stop. The affected C++ fixture and bridge objects compile/pass in MSVC
normal `/Od` and optimized `/O2`; this is static repair evidence only.

R0175's in-process material effect remains unknown after termination. Do not
restart the mutable R0175 driver tail or resubmit from an assumed state. Any
new bounded candidate must use an official clean pair, recheck fresh native
focus/points/owned perks/final legality, and only then make its own single
typed decision. A matching rebuilt DLL and new no-launch manifest are needed
before live validation. The unchanged h1333 source, R0175 failure evidence,
and PRV008 remain distinct assets.
