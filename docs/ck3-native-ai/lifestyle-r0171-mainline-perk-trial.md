# R0171 Robert wartime perk: independent mainline candidate

Status: **static-ready only**. The action runner has not been used in CK3. It
does not close the R0171 war RED, the peaceful M4 two-year gate, or public
LIFE registration.

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
