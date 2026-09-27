# C156 derived h223 construction progress/watch queue

Status: source change and focused tests only. No matching candidate was
prepared, no CK3 was launched, and no completion or income result was seen.
This is a derived Robert replay, separate from the official high-water line.

## Frozen input

The original four-file source is
`Z:\rc100-war-cont-h223-12-nolaunch\source-pair`; its
`PAIR-IDENTITY.json` SHA-256 is
`833D16DC048EF9254C364B1DACBB12117B58C780E68A2D34DE9DEBD596D2F013`.
The exact input files and SHA-256 values are:

| File | SHA-256 |
| --- | --- |
| `xar_checkpoint.ck3` | `0FE3B10545CD512BFFE4B83E94B96961037466E323F2019E1523E11CA320578D` |
| `driver-state.json` | `3F8B85A00C2E9F21ED2640D2B4E699A83DFA788BCF5EBCFD0BCD8113620E2A0A` |
| `construction-formal-pending-v1.json` | `54654CBF58F8E0FF0DA5E65750F09EB08E80081986865D14B238FCDC59E26391` |
| `first-heir-marriage-formal-v1.json` | `0ECC7B580B90DC850AD91CCEE2EEA427162ED7537B127ABD47737CBC7DDBCF0E` |

The pair is actor 29829, episode `native-29829-2bc2d599f7f9`,
h223/raw `53155056`. Its construction ledger has pending `null`, applied
`in_progress`, request `construction-submit-d28196e1a4994ef9b7930a3f935d21e1`,
and `hill_farms_01` on barony 2174/province 2629/type 628/slot 1.
Its first-heir marriage sidecar is resolved; it still belongs in the pair.
Do not reuse the old h223 no-launch qualification: that bound Python
`e61995a3f8f1c03c07aa0f80b347f2859835ddcc` and DLL SHA-256
`7B66A1CDF24D1D89DB4649258E4094DE0510A97F6390EF56334D73397698ADF4`.

## Queue-ready admission sequence

1. Wait for the official high-water candidate's freeze and for the sole CK3
   instance to become available. Fetch `origin master` at the candidate
   boundary and record the exact SHA. At this preparation check, master was
   `49877564038a28ee8af2d04fe7c0c05de4216690`; it is not a future pin.
   Use a clean detached non-C worktree for the fetched source and a separate
   non-C build/cache/state directory. Leave the four input files unchanged.
2. Build a fresh Release native DLL from that worktree's native tree with the
   same six private options used by the matched Robert candidate:
   `XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1`,
   `XAR_CK3_ENABLE_G2_PLAYER_WORLD_BUILDING_ACTION_PRIVATE_V1`,
   `XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1`,
   `XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1`,
   `XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1`, and
   `XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1` all `ON`.
   Run the focused native tests and hash DLL/injector. Bind the exact frozen
   CK3 1.19.0.6 EXE SHA-256
   `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
   A DLL from the old h223 candidate, another source tree, or a later master
   is not the same candidate.
3. Create a new operator manifest using the clean worktree, source commit,
   newly built DLL/injector, new empty state directory, source save/driver
   SHA pins, actor/episode/h223/raw pins, local pipe, `xar_off`,
   `ordinary_campaign_succession`, `ordinary_campaign_no_pact=true`, and
   ordinary windowed profile with only `mod/xar_autoplayer.mod`. Verify the
   game path and native build/source fingerprints. Configure process-local
   `TEMP`/`TMP` and caches on a writable non-C volume.
4. The repository's `tools/g2_preview_operator.py prepare-state` takes that
   manifest plus `--sample-dir` pointing to the four-file source; explicitly
   pass `--construction-sidecar` and `--family-sidecar` from that directory.
   It copies the paired state into a new state directory, runs the official
   ordinary rebind and no-launch preflight, and records the resulting
   environment/driver hashes in the manifest. Run
   `verify-private-lifestyle-dll` against the pinned manifest as well.
   Check every input/copy hash and exact source/DLL pin. This whole step is
   still no-launch evidence, not a game observation.
5. Only after owner/RED/process checks and an available sole CK3 window, run
   a bounded formal candidate through the local operator MCP. Keep the game
   minimized after loading. Use private LIFE, construction, family and M5
   flags plus the initial-focus gate, matching the paired state. A first
   36-turn/1800-second bound can capture the new-PID cold material receipt
   and any ordinary date advance; it does **not** guarantee 25 game days.
   Stop at a real RED or the bound and retain its paired checkpoint.
   Subsequent 36-turn bounded continuations are permitted only from a new
   officially paired checkpoint. The strategy chooses every action/date
   advance; do not force date, alter save/ledger, or turn a war block into a
   claimed construction result.

At the first paused material receipt, record date/revision/PID, same tuple,
`completion_status`, and the new `construction_progress_observation` raw
work/divisor. The next formal turn should consume that receipt without another
submit. If a normal date advance occurs, use a paired new-PID continuation's
cold receipt to compare raw progress on a later paused frame. A positive,
unchanged divisor permits comparison with the exact-source integer quotient
`10000000000 / divisor`; changed/zero divisor or no date advance remains a
separate observation. The native query is private and read-only; it does not
advertise general construction capability.

The saved ledger's **pre-cold** 30-day watch threshold is raw `53155656`,
25 days after h223. The first new-PID recheck updates the last check if still
active. If it occurs at raw `53155056`, the next **warm** threshold becomes
`53155776`, 30 days after that receipt. Recalculate from each actual receipt;
do not claim a 25-day warm watch merely by reaching the old threshold. At an
actual due watch, independently check the same active tuple or the completed
built slot after the manager update, then the next-turn receipt consumption.
Read province aggregate and player monthly income separately. Start receipt,
completed slot and income effect are three different evidence claims.

This candidate's complete no-launch check cannot be inherited from the old
h223 status or done before a current-source DLL/manifest exists. The
independent build and source work can proceed off-instance; final rebind and
preflight require a clean candidate and local zero-instance/owner checks.
Nothing here adds replay days to official Robert or modifies PRV008.
