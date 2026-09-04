# Projects/metrics provider no-launch candidate (2026-09-04)

This freeze starts from canonical `13d78c6dedb3da866d075fa0ce70cb2c4307dcb5`.
The source, ABI, serializer, application-main mailbox slot, bridge dispatch,
service/MCP facade, and the independent projects/metrics gameplay action cell
remain complete.  The candidate source commit is
`bd0c4080d165d77a6dc22b2158072b3fabd5f231`.

## Candidate boundary

`XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1` is a new CMake option
whose default is `OFF`.  An explicitly opted-in private build adds only
`game.command.query-zhongguo-projects-metrics-postcondition-v1` to the exact
1.19.0.6 adapter descriptor.  The query implementation was already present;
no variable allowlist, serializer, mailbox protocol, MCP schema, gameplay
mutation, or formal runner registry changed.  Default production advertisement
and `production_live_ready` both remain false.

The existing `bind_projects_metrics_event_snapshots_v1` facade remains the
only source/result event binder.  It binds `zg361cp.26` to `zg361p3.229` when
the corresponding event snapshots exist.  It must not collapse the visual
checkpoint into the background action cell: the two visible events are rooted
at the non-AI project owner, while the provider deliberately reads the played
project subject under a distinct bounded AI owner.  The action cell's success
is still a later paused provider read proving that the same CP26 receipt was
consumed by a committed P3M229 result; a transport ACK is never success.

## Frozen pair and checks

The read-only frozen pair is under
`Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-provider-private-candidate-bd0c408-20260904T054627Z-r2`:

- `xar_ck3_bridge.dll`: 2,323,456 bytes, SHA-256
  `7F81BADB294B843BA59B4B09142361C38C9FFD806F3260DB35BBF7CFB95B1EA9`;
- `xar_ck3_bridge_injector.exe`: 39,936 bytes, SHA-256
  `58DE92DAF24EBE3848D6F97EBA147113F26B25988B1D83EE1DF68C5A0C7B2B08`;
- `CMakeCache.txt`: SHA-256
  `9AE0ABA72F77CC8F3973D9C507D4842F0C4A9A38D541D10EB0D847104B7FD51D`,
  with the candidate option exactly `ON`.

The opted-in descriptor fixture plus the provider and mailbox native fixtures
are GREEN (`3/3`).  The focused Python contract/action/verifier suite is GREEN
in normal and optimized modes (`27 passed, 4 subtests passed` each).  A prior
full native baseline built directly from canonical `13d78c6` compiled the pair
but finished `75/90`: all 15 failures were stale, unrelated source-contract
assertions after shared integrations; both projects/metrics native tests were
GREEN in that same run.  This baseline RED is retained and is not represented
as candidate success.

## Exact no-launch preflight

From the worktree root:

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools/verify_zg361_projects_metrics_no_launch_candidate.py --manifest ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_projects_metrics_postcondition_v1_no_launch_candidate_20260904.json --check
```

The verifier requires the exact CK3 executable hash, all pinned provider and
action-cell source hashes, the opted-in CMake cache, both binary hashes, the
default-OFF source gate, the existing source/result facade, an empty CK3 and
injector process inventory, and an absent attempt path.  It does not create the
attempt or launch a process.

The reserved attempt is
`zg361-projects-metrics-bd0c408-20260904T054627Z`; its directory
`Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-provider-live-attempt-bd0c408-20260904T054627Z`
is absent.  A live is not runnable until a hash-bound save supplies the exact
checkpoint: played subject, distinct bounded AI project owner, paused map, no
active event, CP26 route-A/B receipt prepared for that subject/cycle, and P3
initialization not yet run.  Once that save exists, the integration point is a
dedicated wrapper around `preflight_projects_metrics_gameplay_action_cell` and
`run_projects_metrics_gameplay_action_cell`, before any owner-role switch for
the separate visual event capture.  No production readiness changes before
that real paused artifact succeeds.
