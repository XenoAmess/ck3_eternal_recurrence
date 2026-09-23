# M4-LIFE-READBACK-ENTRY: bounded private input readback

Status: R0110 startup RED, R0111 live readback RED, and R0128 h1094
`evidence_insufficient` remain preserved. R0167 completed the three-query
private read-only gate on a distinct Robert h1082 frame with an already
selected focus and two unspent stewardship points. Neither run proves a typed
perk action or G2-M4 completion. This entry is not a public capability. See
the [R0128 immutable evidence index](lifestyle-r0128-readback.md) and the
[R0167 Robert evidence index](lifestyle-r0167-robert-readback.md).
It follows the exact 1.19.0.6 native decision tree in
`lifestyle-focus-perk-ai.md` and the versioned LIFE2, stock-perk, and
stock-focus ABI files under `native_bridge/research/`. Frozen CK3 EXE SHA-256:
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

R0110 attempted the first cold readback from the prepared ordinary checkpoint,
but stopped RED during bridge hello before any private query or gameplay action:
the runner constructed its driver with the default one-life lifecycle while
the persisted checkpoint was ordinary `xar_off`. The CK3/operator/watchdog
processes were recovered after an operator interrupt; no normal runner report
was produced, and the abandoned owner marker was preserved then reconciled
through the existing exclusive-state-lock contract. The runner now derives
the ordinary binding from the verified prepared profile, requires it to match
the checkpoint, and passes it into the driver constructor. R0111 proved that
this lifecycle correction reached the paused readback: LIFE2 reported current
focus and lifestyle progress both `absent`, with seven owned perks. The formal
perk query returned `native_lifestyle_windowless_policy_perk_unavailable_state`
and the runner stopped RED before its stock-focus query. The exact-build
`ReadStockPerkPlayerState` fallback requires current lifestyle progress to be
present; this particular absent-progress state makes perk legality unavailable,
not false or successful. R0111 remains RED and supplies no focus-query or
gameplay-action evidence.

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
prepared profile. The R0112 private Release DLL SHA-256 was
`C9466D358F4F36BE68E7CF4ECA6BEC9E20490AEE7D99469736B368A9C7F4D0FE`.
It predates target-lifestyle progress. The M4-FOCUS-OBS private Release DLL
SHA-256 `3778DBE7BBE5C62BCD7A50F93E82FF1B337E34160F6E821F21215B2599C39460`
is a new offline candidate and needs its own exact source/manifest pairing.
These hashes identify candidates, not an instruction to hot-swap R0101's
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
R<n> --evidence <fresh-Z-dir>` to execute the bounded cold-start. No complete
three-query live readback has passed. A corrected runner is a new candidate
version and needs a new round only when the sole-owner queue authorizes it.

## Readback contract

The runner calls exactly these allowlisted private steps on one paused,
map-ready native frame, in order: `private-query-player-lifestyle-current-state-v1`,
`private-query-player-lifestyle-stock-focus-v1`, then
`private-query-player-lifestyle-formal-v1`. The stock-focus query is scoped to
`stewardship_wealth_focus`; the formal query supplies the policy perk candidate
view. Each request carries native revision, snapshot ID, date, actor and
episode bindings, then receives a separate paused-frame readback.
The script sends no gameplay action or date-advance step. Native `unavailable`
is evidence-insufficient, not legal false or an empty candidate set. Only the
exact formal-perk error `native_lifestyle_windowless_policy_perk_unavailable_state`
paired with a validated same-frame LIFE2 `current_lifestyle_progress.presence:
absent` is recorded as `typed_legal_unavailable`; it is not a perk legality
decision, earned point, submitted action, or completed gate. The raw native
response stays in evidence. Any other native command rejection, malformed
binding or frame drift stays RED. A full observation yields
`three_queries_observed` only if all three typed reads and frame checks pass.

For the post-R0112 target-progress extension, the focus read now additionally
requires `target_lifestyle_key=stewardship_lifestyle` and a same-frame
`target_lifestyle_progress` with `presence=present`, `source=exact_native_getters`,
and typed total/within-level XP, XP-per-level and unspent/used perk points.
Only then is the focus step `observed`; `presence=unavailable` is
`evidence_insufficient`, with no invented zero, and a native source/read/ABI
failure remains RED. The runner delegates these checks to the versioned
private typed parser, retains the raw response and checks the independent
after-frame. R0112 proved stock focus legality but used the older DLL and
cannot prove these new target-progress fields. This runner change itself is
no-launch and does not supply a focus action or public capability.

R0128 exercised this path on the h1094 no-focus frame. The fixed focus and
target-progress query passed; the formal perk query remained typed unavailable
because its exact-build player-state callback requires current lifestyle
progress. The target-progress readback subgate is production-live primitive
for that actor and build, while the overall report remains
`evidence_insufficient`. The runner's post-run prepared driver now has a live
restore tail and cannot be used as the source for another fresh candidate.

R0167 used the immutable R0164 Robert h1082 ordinary `xar_off` pair and a
fresh official prepare/rebind. The exact-build cold readback observed LIFE2
current `stewardship_wealth_focus`, `2131.25` total stewardship XP, two
unspent points, a native rejection of selecting that same focus again, and
the single final-legal policy perk `cutting_corners_perk`. The three queries
remained on one paused native frame with zero gameplay actions and zero date
movement. The R0164 source's active defensive wars keep the existing formal
consumer outside its peaceful action scene; R0167 is read-only evidence,
not permission to submit the perk in war. The frozen report, full hashes and
the two subsequent legal action routes are in the
[R0167 evidence index](lifestyle-r0167-robert-readback.md).

The report and each raw query response are written under the fresh evidence
directory. The final report includes candidate hashes, process identity,
cleanup result, postflight global process inventory, unchanged source save
hash and wall time. A failed run is preserved; do not retry uncertain actions
or call this a production strategy loop. Even a GREEN readback only closes the
M4 input gate. Focus/perk choice, typed submission, independent material
result, next formal turn consumption, and cold restore remain separate gates.
