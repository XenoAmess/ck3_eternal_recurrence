# M4-LIFE-READBACK-ENTRY: bounded private input readback

Status: static-ready, no CK3 execution in this package. This entry is not a
public capability and cannot prove a lifestyle action or G2-M4 completion.
It follows the exact 1.19.0.6 native decision tree in
`lifestyle-focus-perk-ai.md` and the versioned LIFE2, stock-perk, and
stock-focus ABI files under `native_bridge/research/`. Frozen CK3 EXE SHA-256:
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Candidate manifest and sole-owner use

The sole CK3 owner prepares `candidate-manifest.json` in a Z-drive isolated
candidate root after checking the current run-ID ledger and global instance
inventory. The runner requires schema
`xar.ck3.g2_m4_lifestyle_three_query_candidate_v1`,
`status: "ready-no-launch"`, `read_only: true`, and
`public_registered_or_advertised: false`. Its required fields are:

| Field group | Exact meaning |
| --- | --- |
| `candidate_root`, `source_repo`, `python_source_commit`, `native_source_commit` | Absolute candidate root; checked-out Python source and its HEAD; source commit of the frozen native DLL. The DLL itself is independently hashed. |
| `game_dir`, `state_dir`, `game_exe_sha256`, `profile_environment_sha256`, `pipe` | Frozen CK3 install, isolated prepared profile, exact EXE SHA, `verify_profile` fingerprint, unique pipe. |
| `dll`, `injector`, `source_save`, `source_driver`, `prepared_save`, `prepared_driver`, `cmake_cache_path` | Absolute existing files; each has a corresponding `<field>_sha256`. The save source and prepared copy must be byte-identical. CMakeCache must show `XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1:BOOL=ON`. |
| `expected_actor_id`, `episode_run_id`, `expected_date_raw`, `expected_history_index` | Values from the paired checkpoint and driver state, not guessed from a save label. |
| `bounds` | `overall_seconds: 600`, `readiness_seconds` at most 300, `native_query_seconds` at most 60. |

The R0101 h1094 safe checkpoint has actor `36403`, date raw `53368176`,
episode `native-36403-2b4b233056bd`, save SHA-256
`2F6F3DCA9E9CD92D87FDE1CD296A581F6A3A38F11E2781765E99815B7769C39A`,
but R0101 post-RED driver-state SHA-256
`95959FB66C457B12E38690B0B1D05E208DC08FB28A80AAC9A393C4C70712536E`
has an unpaired read-only h1095–h1097 tail. Do not copy it directly as
the prepared driver. The R0103 `source-pair` contains the same h1094 save
and h1097 driver tail as input to the ordinary-seed rebinder. Its R0103
*prepared* driver at SHA-256
`A220A68946DDE4EDE22E831CFB628A47CCD77C83EC7912E421017F4F79C4EC12`
was bound to a different profile and is not a portable ready pair. Copy the
source pair, rebind its driver to the new profile's environment fingerprint,
then validate the cold checkpoint. On successful cold start, the official
driver reconciles to h1094, discards unpaired h1095–h1097, and records the
new process's restore row; until then the tail is not paired with the save.
The owner must read the paired checkpoint metadata to fill
`expected_history_index`; the runner validates it and refuses a mismatched
prepared profile. The existing private Release DLL SHA-256 is
`C9466D358F4F36BE68E7CF4ECA6BEC9E20490AEE7D99469736B368A9C7F4D0FE`.
These hashes identify a candidate, not an instruction to hot-swap R0101's
loaded files. A new run must cold-start only after the previous instance is
dead and a new monotonic R-number is allocated.
`source_repo` must be a retained candidate checkout, not a temporary
development worktree that integration cleanup will remove.
The prepared ordinary campaign profile must be verified with
`xar_enabled="xar_off"`; the default `xar_on` verifier is incompatible with
this checkpoint and is not an indicator of corrupt save data.

The command entry is
`ck3_autonomous_player/native_bridge/research/run_player_lifestyle_three_query_readback.py`.
`--candidate-root <prepared-root> --preflight-only` checks the manifest,
profile, hashes, checkpoint and zero-instance state without launching CK3.
Only the sole owner may then supply `--candidate-root <prepared-root> --round
R<n> --evidence <fresh-Z-dir>` to execute the bounded cold-start. No live
invocation of this new entry has yet been performed; the parameter interface
has only focused offline tests. The actual next-round values and command must
be recorded by that owner before launch.

## Readback contract

The runner calls exactly these allowlisted private steps on one paused,
map-ready native frame: `private-query-player-lifestyle-current-state-v1`,
`private-query-player-lifestyle-formal-v1`, and
`private-query-player-lifestyle-stock-focus-v1`. The final focus query is
scoped to `stewardship_wealth_focus`; the formal query supplies the policy
perk candidate view. Each request carries native revision, snapshot ID, date,
actor and episode bindings, then receives a separate paused-frame readback.
The script sends no gameplay action or date-advance step. Native `unavailable`
is evidence-insufficient, not legal false or an empty candidate set; command
rejection, malformed binding or frame drift is RED. A full observation yields
`three_queries_observed` only if all three typed reads and frame checks pass.

The report and each raw query response are written under the fresh evidence
directory. The final report includes candidate hashes, process identity,
cleanup result, postflight global process inventory, unchanged source save
hash and wall time. A failed run is preserved; do not retry uncertain actions
or call this a production strategy loop. Even a GREEN readback only closes the
M4 input gate. Focus/perk choice, typed submission, independent material
result, next formal turn consumption, and cold restore remain separate gates.
