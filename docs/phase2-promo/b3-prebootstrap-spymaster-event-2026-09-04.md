# B3 pre-bootstrap `spymaster_task.0381` handling (2026-09-04)

Status: **static-ready only; seed remains RED/pending**.  This change did not
launch CK3 and does not upgrade B3 gameplay readiness.

## Why this handler exists

The frozen short-root attempt `Z:\p2o\a` loaded the exact checkpoint and
reached a paused map, but the seed waiter stopped on a visible vanilla event:

- source commit: `ae55180a1fd5933d1725a30d9b56083be0f77383`;
- source save SHA-256:
  `bfc73fd9e7e80145cdf39aabc66bc2d731881122adab0cc0ba675fa07d1e6733`;
- observed frame: `date_raw=53148768`, root `CharacterID=29037`, native event
  `spymaster_task.0381`, instance `11`, exactly two enabled options;
- `runner-report.json` SHA-256:
  `59f204c4d670314100b0290ba8e4c0ea16eb83a3ec1602ba5b1bc0ebf4379b43`;
- `bootstrap-event-wait.jsonl` SHA-256:
  `ab61fe58a509dee2dc4b549363fcd849919d0de68d391598c5de0706400c081c`.

The actual failing entry point in that immutable attempt is
`tools/run_zg361_phase2_seed_capture.py::wait_for_bootstrap_event`.  There is
no tracked `tools/run_zg361_phase2_b3_manager_governance_acceptance.py` in the
current repository or fetched refs, so the fix belongs at the real shared
pre-bootstrap wait boundary.

## Exact vanilla semantics and bounded action

The installed exact-build source is
`game/events/councillor_task_events/spymaster_task_events.txt`, SHA-256
`2d7f0237d9888812a55c14b7a8a3bba551ff64d8ae72ae28088456af93fcff57`.
Its two options have no side-effect-free dismissal:

1. option 1 spends short-term gold and fabricates a hook;
2. option 2 spends no resource and gives `character_to_hook` a decaying
   `grateful_opinion` of root, value `+30`.

The runner therefore selects option 2 only after every explicit gate passes:

- exact source-save SHA, event key, event instance, `date_raw`, unique current
  event window, schema/version/status and root `CharacterID=29037`;
- active event source is `native` with exactly two options;
- both option rows are in rendered/native order and are
  shown/enabled/non-fallback/non-cancel;
- saved scope `character_to_hook` resolves to exactly one typed character and
  is neither root `29037` nor the known superior `32904`;
- the fresh pre-selection snapshot still has the same date, event instance,
  option count and paused state;
- the action ACK confirms option number `2`, native index `1`, verified event
  transition, and removal of the old instance.

Any drift is a typed RED and performs no selection.  Any other vanilla event,
including another `spymaster_task.*` key, remains `unexpected_visible_event`;
there is deliberately no namespace or arbitrary-event ignore rule.  Evidence
is written separately to
`known-pre-bootstrap-vanilla-event-drain.json`, so it cannot overwrite the
existing exact `zg361.4` drain.

After an exact registered event closes, the waiter resumes the map and keeps
waiting under the original total deadline.  Draining does not create or reset
a five-second deadline.  A sequence containing both registered events is
supported, while a repeated/already-drained or unregistered event remains RED.

## Primary blocker remains delivery state, not the incidental event

Closing `spymaster_task.0381` is only an auditable prerequisite.  The same
attempt proves the fixture bootstrap is still waiting on the product delivery
transition:

- `debug.log` records `ZGAP2SEED: waiting for witnessed delivery before B2
  checkpoint` from `zga_phase2_seed.102`;
- the checkpoint is still `zg361_result_case_state=2` (carrier pending);
- the later product callback logs `ZG361P2: stale witnessed-delivery token
  ignored` from `zg361.51`, followed by an event with no valid options;
- `spymaster_task.0381` appears only after 77 additional game days.  It is a
  secondary timeline interruption, not the reason the delivery failed.

The next capability blocker is therefore the stale witnessed-delivery carrier
and the state-2-to-delivered transition.  A future live retry may still reach
the full event timeout after cleanly dismissing the vanilla event.  This patch
must not be reported as a seed, B3 action-cell, or full Phase2 fix.

The result is also unrelated to effect-file size: no product effect file is
changed, no loader-performance experiment is performed, and no new CK3 launch
evidence is claimed.

## CK3-free regression evidence

`tools/test_run_zg361_phase2_seed_capture.py` now covers:

- exact option-2 selection and typed drain evidence;
- product `zg361.4` followed by the exact vanilla event in one wait;
- root/saved-scope/option-shape drift failing before action;
- an unregistered vanilla event remaining explicit RED;
- a wrong native option index in the ACK remaining RED;
- post-drain map resume and exhaustion of the original total timeout.

Command:

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -B `
  "tools/test_run_zg361_phase2_seed_capture.py"
```

Result: GREEN.  CK3 launch count for this implementation task: `0`.
