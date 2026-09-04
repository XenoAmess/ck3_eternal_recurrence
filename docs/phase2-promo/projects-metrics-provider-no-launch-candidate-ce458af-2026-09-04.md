# Projects/metrics provider ce458af no-launch candidate (2026-09-04)

This freeze supersedes the binary and source hashes in the earlier
`bd0c408` candidate.  It was rebuilt from canonical
`ce458af71a2a44decc085766720082a8b724edb8` after the shared native bridge
continued evolving.  The capability remains a private, default-OFF candidate;
production advertisement and readiness remain false.

## Exact build and focused checks

The native bridge was configured in the Visual Studio x64 developer
environment with MSVC `19.51.36248.0`, Ninja, Release, and
`XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1=ON`.  The current
native source fingerprint covers 289 C/C++/header/CMake files and is
`19B04B4855A8E65C979FCBA56FF46D37BAD0477F40036587C236A28BFC02F0A1`.

The read-only frozen pair is under
`Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-provider-private-candidate-ce458af-20260904T061634Z`:

- `xar_ck3_bridge.dll`: 2,352,640 bytes, SHA-256
  `F03DF885B93A62A44903C3B732A5E2164AF115B4DA02C887425486DACD7B4CF8`;
- `xar_ck3_bridge_injector.exe`: 39,936 bytes, SHA-256
  `FC47FD40E2414377F25EF13C6504FDBEEBB1DC73B451495A423B8CA051F08663`;
- `CMakeCache.txt`: SHA-256
  `72405E42BEC0A1B85F532E0E10A1430AB3E8168031D719D8111D3C6455C81091`.

Focused native tests are GREEN (`3/3`): adapter registry, projects/metrics
provider, and projects/metrics mailbox.  Focused Python tests are GREEN in
normal mode (`27 passed, 4 subtests passed`) and optimized mode (`27 passed,
1 warning, 4 subtests passed`).  The optimized warning is pytest's expected
warning that assertions are disabled under `-O`; it is not a product failure.

## Read-only checkpoint audit

No verified retained checkpoint satisfies the CP26/P3 projects-metrics
conditions.  The artifact search found zero snapshots advertising
`zhongguo_projects_metrics_v1_query_supported: true`, zero live
`zg361cp.26` event snapshots, and zero live `zg361p3.229` event snapshots.
Seven retained episode-seed metadata files identify only immutable save hash,
date, and player; they do not expose the required project variables.  Five
older user saves and the episode seeds use an opaque/compressed save format,
so absence of raw variable strings is not evidence that the variables are
absent.

The latest inspected B2 checkpoint is explicitly an `zg361b2.40` event for
player/subject `29037`, owner `32904`, paused at date `53147040`; it is not a
CP26/P3 checkpoint.  The honest checkpoint status is therefore `not_found`,
not a fabricated reusable save.

The still-required live checkpoint is: played character equals project
subject; distinct bounded AI project owner; paused map; no active event; CP26
route-A/B receipt prepared for the same subject/cycle; P3 initializer not yet
run.  The action cell may claim success only after a later provider read proves
that exact receipt was consumed by committed P3M229 state.  A transport ACK is
never the business postcondition.

## Exact no-launch preflight and live boundary

From the worktree root:

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools/verify_zg361_projects_metrics_no_launch_candidate.py --manifest ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_projects_metrics_postcondition_v1_no_launch_candidate_ce458af_20260904.json --check
```

The reserved attempt is
`zg361-projects-metrics-ce458af-20260904T061634Z`; its directory
`Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-provider-live-attempt-ce458af-20260904T061634Z`
is absent.  No CK3 or injector process was started.  Once an exact checkpoint
exists, the integration point remains a dedicated wrapper around
`preflight_projects_metrics_gameplay_action_cell` and
`run_projects_metrics_gameplay_action_cell`, before any owner-role switch for
the separate visual event capture through
`bind_projects_metrics_event_snapshots_v1`.  Until that real paused run
succeeds, readiness remains `static-ready-live-pending`.
