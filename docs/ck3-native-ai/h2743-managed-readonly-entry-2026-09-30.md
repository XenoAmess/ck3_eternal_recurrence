# H2743 managed read-only entry, 2026-09-30

## Scope and current evidence

The new entry is `xar_autoplayer.h2743_exit_readonly_live`. It prepares frozen
source assets without starting CK3, or performs three explicitly admitted native
queries in one managed session. The session runs in a worker thread and shares
one `ScreenLeaseKeeper` with the query driver. Its `process_create_gate` is passed
to the current common `native_session`; this entry creates no supervisor child
and no second renewal owner.

The historical `run_h2743_dejure_readonly_v3.py` current-HEAD STOP remains intact.
No old runtime, native driver or C++ file is projected over the current common
implementation. The only existing query module needed alongside the new entry
is the exact `bridge/defender_dejure_exit_terms_v1.py` normalizer.

The reused Release pair was built from
`24c51a37d2facd2dcf24da2d54e5f0c4548833cb` and preserved with Draft #723:

- Pair manifest SHA-256: `183BF62461AE3C2B382F9367C657C923D5D412883ADE45FA7F24B7E31BC0E42C`.
- DLL SHA-256: `A73EBA509729D64E5DBC453791E48BEF8CF2DBCAE95C4F0BA2AA73D958B1C5EF`.
- Injector SHA-256: `3E9339B4C96A77AD96C8566D6707387DEBBB1C3E044B323DF2E0AD479F16A595`.
- Frozen native source manifest SHA-256: `3CC643CD3F73B63AC576361C5E99B34592F83B4DB0AE9875D4061325AB6611B3`.

The 14:28 local recheck compared all 1,564 frozen native paths: 1,563 were
identical and the only changed file was the historical Python research runner.
Compiled CMake/include/src inputs were identical. The 173 DLL and one injector
actual project dependencies were also identical. There was no new compilation.
The new entry independently rehashes these compilation inputs, frozen build
receipts, source quartet and binary bytes before preparation or a live read.

Nine focused tests passed in normal Python and `python -O`. They cover exact
frame/capability dispatch, stale-frame rejection, loading readiness, unavailable
storage, the same-process session gate and single keeper, lease abort, cleanup
failure remaining RED, and retention of a failed no-launch attempt. Actual logs
and argv are preserved at
`C:/Users/1/ck3-h2743-resume-20260930/attempt-02/`; `test-report.json` SHA-256 is
`7BC8E89173503B07115BAD147F8B372AA6815DCAFC3A61900871B48D0495B72A`.
These tests use synthetic sessions and do not constitute live evidence.

## Actual command interface

Use the current common source tree with its reviewed `screen_bus_lease.py` and
native launch provider, plus the new entry files and exact normalizer. Bind
`PYTHONPATH` explicitly to that tree's `ck3_autonomous_player/src`. The separate
`--native-source-checkout` must contain the frozen Release compilation inputs;
it need not be the Python runtime tree. Use the verified interpreter
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`
(Python 3.14.7, mcp 2.0.0, psutil 7.2.2). No relative venv exists in the short
H2743 worktree.

Each mode requires a new, nonexistent `--attempt-dir`. The entry preserves
completed artifacts and reports a RED attempt on failure; it never repairs an
old attempt.

```text
<verified-python> -m xar_autoplayer.h2743_exit_readonly_live --no-launch
  --pair-manifest D:/ck3-research-artifacts/h2743-v5-build-20260930/pair-proposal-head24c51-unreviewed.json
  --native-source-checkout C:/h274330
  --game-dir C:/SteamLibrary/steamapps/common/Crusader Kings III
  --attempt-dir <new-external-attempt>
```

`--no-launch` verifies source/binary/game bytes and the actual Python/provider
fingerprint. It does not claim a lease, prepare a profile or create a process.
Replace `--no-launch` with `--prepare` to create a fresh ordinary-campaign,
`xar_off`, windowed profile; copy and hash the source checkpoint, driver state
and formal heir receipt; rebind the seed pipe; and run the existing one-generation
native preflight. Preparation also starts no CK3 process. Its
`prepared-source.json` freezes the runtime files and prepared input bytes, which
are verified again immediately before a live session.

The mutually exclusive `--live` mode additionally requires:

```text
--prepared-manifest <prepared-source.json>
--go <new-exact-go.json> --steam-gate <new-reviewed-steam-gate.json>
--round-id <current-round> --screen-task-id <exclusive-owner-task>
--screen-sequence <exact-claim-sequence>
--task-bus-source <actual-cas-bus-source> --task-bus-sha256 <actual-source-sha256>
--bus-dir <actual-shared-bus-dir>
```

GO is a JSON object with schema `xar.ck3.h2743.managed-readonly-go.v1`, exact
`round_id`, `task_id`, `pair_sha256`, `prepared_manifest_sha256` and
`steam_gate_sha256`; `allowed_query_steps` must be exactly
`["query-defender-de-jure-exit-terms-v1-16777231", "query-war-termination-options-16777231"]`,
and `allowed_gameplay_steps` must be `[]`. The Steam gate binds the same task,
reviewer, UTC review time, visible offline mode, exact screenshot bytes and fresh
moving-frame receipt. Root obtains and directly reviews this evidence and owns
the screen claim. This author has not started CK3, Steam or desktop operations.

## Interpretation of a live result

The entry waits for the original bounded readiness period (at most 1,800 seconds),
then requires actor 29829, episode `native-29829-2bc2d599f7f9`, paused date 53217264,
War 16777231, primary defender, opponent 30097 and title 2128. It takes two baseline
reads around one read-only termination-options query and checks the same native
frame, connection generation and target war before and after. The original
1,200-second post-read session allowance remains available; this entry does not
introduce a new theoretical deadline budget.

`READONLY_BASELINE_AVAILABLE_MATERIAL_PENDING` requires matching double reads,
the shared managed session's cleanup receipt, an exited session thread, zero final
CK3 inventory and no lease failure. Storage remains `structural_candidate_only`.
The report always retains `material_complete=false`, `action_literal=null` and
zero gameplay/date-advance actions. It does not prove stock border-raid polarity,
full termination effects, FP2 payment amounts, post-surrender expiry or a complete
exit decision. No live run or current human review is certified by this document.
