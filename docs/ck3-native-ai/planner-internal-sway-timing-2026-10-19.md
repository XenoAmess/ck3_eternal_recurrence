# Public planner internal/Sway timing

Source-only observation change, qualified on `xenoamess-full-tower-eb9d2c1186` at `2026-10-19T07:45:23Z`. Machine identity was read with `py tools/ck3_live_run_id.py machine`; source pins and test output were read from this workspace.

The public `GameplayBridgeService.plan_turn` previously timed the outer call and final public-plan copy, leaving the interval after choice ambiguous. Two existing calls now use the unchanged `_timed_planning_call_v1` helper:

| Stage | Existing operation |
| --- | --- |
| `service.planner_internal` | `_plan_turn_internal()` including its existing readers/retry path |
| `service.planner_sway_staging` | `stage_ordinary_sway_v1(self, planned)` |

The Sway import remains after the internal call; return values, exceptions, call order and final deep copy remain unchanged. No additional observation or RPC is introduced. The internal span includes existing capability/history/choice spans, and the outer normal-plan span includes both new spans; these nested durations must not be added as independent costs.

Validation reused `test_planner_stage_timing_v1.py`: sink-on/off results and read/submit counts remain identical. Two targeted failure cases preserve the original exception object, operation order and inner/outer `finally` timing receipts. The single test file passed `3 passed in 2.55s`; `git diff --check` passed.

```text
py -m pytest -q ck3_autonomous_player/tests/unit/test_planner_stage_timing_v1.py --basetemp D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/perf-harness-planning-timing01
```

Changed source: `service.py` SHA256 `0adead831ceec7d2c2de779171de6e1b02bbd5c5d9fb236cdea12bc46a3d555c`; test SHA256 `49f96b33fe93f02546f22f145126657ddeb6516e5afbe41a8c1edfe39455d6e4`. Current C7, immutable SDK snapshots, Native and the live campaign were not modified. These tests provide no new attribution of the historical 2.2s/0.6s interval and no measured game-day speedup.
