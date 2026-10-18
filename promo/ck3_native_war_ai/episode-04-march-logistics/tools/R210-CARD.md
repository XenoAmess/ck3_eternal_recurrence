# Episode 04 owned client-window take candidate

Status: source-only candidate. No R210 runtime, machine qualification, capacity, take or camera signal has been admitted. Root retains the only live SDK, desktop and recorder authority.

The package targets `promo/ck3_native_war_ai/episode-04-march-logistics/tools/` in the shared repository. `window_take.py` uses the existing `capture_recorder.OwnedRecorder` and `integration/recorder_job.py`; it never creates a second SDK host. `window_take_actor.py` attaches a new `CaseClient` to the same public run. The actor does not initialize, advance days, Save, Quit, release CAS or infer business success. `window_take_probe.py` checks completed raw bytes offline.

## Two R209 failures now covered

1. `OwnedRecorder.handle(start)` invokes `start_admission` before workdir creation and again at spawn **after** creation. The callback in `TakeSpec.admission` checks capacity and deadlines but never tests workdir absence. `start` checks the fresh take directory once before passing control to the canonical recorder. The focused test executes the real canonical `handle(start)` with isolated screen and managed Job edges and observes `[False, True]` for directory existence across the two admission calls.
2. A public snapshot/control name is once-only even if FFmpeg never started. Each new attempt therefore needs a new `case_output`, `query_prefix` and `take_id`; `ui_case_output` and `ui_query_prefix` are separate again. The focused test executes the real `FullArmyResultClient`: repeating a prefix is rejected; a new prefix succeeds. Original RED, consumed control IDs and original raw directories remain intact.

## R210 planned bounds, pending actual adoption

Root proposed a public cold run with host hold 7,200 seconds, purpose deadline 12:00 UTC, maximum window recording 900 seconds, raw ceiling 1 GiB, normal-close reserve 900 seconds plus cleanup reserve 120 seconds. R209's 179.033-second raw was 95,590,470 bytes, suggesting about 480 MB for 15 minutes at similar content; it does not guarantee the next bitrate. No R210 Start is authorized by these proposed values alone. The actor requires a future exact Root-adopted capacity receipt, current source HEAD, current-machine Steam offline image review, actual public run/keeper/PID and a new Root-reviewed original client frame.

The longer window is intended to cover 11 or more actual natural days, but the public R05 observer alone submits those days. The camera never advances game time, and 900 seconds of raw footage does not itself prove 11 days occurred. Day count comes from original native before/after results and visible date changes can support only what the sampled frames show.

`TakeSpec` reads one immutable actual JSON input with schema `xar.e04.owned-window-take-input.v1`. Required keys are `repo_root`, `machine_id`, `source_head`, `scene_root`, `run_dir`, `keeper_root`, `screen_task`, exact `{path,bytes,sha256}` pins for `capacity`, `steam_offline_review` and `ffmpeg`, plus `runtime`, `products`, `product_key`, `case_key`, `context`, `prepared`, `state_dir`, `raw_root`, unique `take_id`, `case_output`, `ui_case_output`, unique `query_prefix` and `ui_query_prefix`, actual `army_id`, `content_kind`, `expected_client_size`, `recording_seconds`, `hard_terminal_seconds`, `minimum_recording_seconds`, `raw_budget_bytes`, `normal_close_reserve_seconds`, `cleanup_reserve_seconds`, `receipt_label`, and optional paired `camera_awaiting`/`camera_signal` with `camera_output_name` and `observer_result`. Actual pins and identities must come from that run; old R209 values cannot populate them.

## Army/supply framing before Start

For an `army-supply` shot, Root chooses an actual controllable owned Army ID. `ui-prepare --select-army-once` submits at most one `ck3_select_army_ui_v1` via the existing public CaseClient, then independently reads `ck3_query_ingame_ui_window_v1(window_kind='army')` with fresh revisions. The result must show the selected full Army ID, owner, date and `effective_visible=true`. A pending ACK or a siege pane does not count. Repeated selection after unknown outcome is prohibited.

The existing camera coordination wait is only 180 seconds. Build and verify the intended Army/supply composition before the post-initializer waiting point whenever the actual public case permits it, then take a new screenshot and perform one fresh native UI readback immediately before Start. R209 spent about 171 seconds from the waiting checkpoint to accepted Start even without a successful Army panel. Five new UI polls after that checkpoint are therefore too late as a default plan. If initialization changes the panel, preserve the actual new state and stop this shot rather than treating the old pre-initialization view as fresh.

The installed 1.20.0.4 contract supports Army query/select; registration of other MCP tools does not prove they are available in this build. In R207, selecting besieging Army 0 showed a siege pane while the independent ArmyWindow remained `effective_visible=false`. This package does not invent a route that forces the Army supply pane. Root may choose a different legitimate current Army/UI context, or document that the desired panel is unavailable. Before Start, `prepare-frame` captures fresh original pixels, Root visually confirms the intended supply presentation and no hover, and `film` repeats the native visible ArmyWindow query. The code does not claim a supply value from the UI tree; low-stock numeric evidence requires the separate native R05 result and a visible value in the actual frame if the video will say so. `map-context` is an explicitly separate shot type, not a substitute for the requested Army/supply shot.

## Commands after actual R210 input exists

Use the project's Python interpreter in place of `<py>` and actual paths in place of `<...>`.

```text
<py> -B window_take_actor.py source-check --repo-root <actual-repo>
<py> -B window_take_actor.py ui-prepare --config <actual-take-input.json> --select-army-once --execute
<py> -B window_take_actor.py prepare-frame --config <actual-take-input.json> --output <fresh-scene-frame-dir> --execute
```

Root directly opens `<fresh-scene-frame-dir>/ck3-client-original.png` and checks the game content, panel and pointer. If the Army/supply pane is truly visible:

```text
<py> -B window_take_actor.py review --config <actual-take-input.json> --capture <fresh-scene-frame-dir>/capture.actual.json --root-reviewed-no-hover --execute
<py> -B window_take_actor.py film --config <actual-take-input.json> --reviewed-frame <fresh-scene-frame-dir>/ROOT-REVIEW.actual.json --execute
<py> -B window_take_probe.py --config <actual-take-input.json> --output <fresh-scene-probe-dir>
```

The initial UI operation is omitted if a different legitimate action already made the correct ArmyWindow visible; in that case Root may use a new read-only UI attempt with no `--select-army-once`. Every attempt still needs fresh output and query namespaces. `film` has one canonical Start and one locked Finish. It may Finish after the actual observer result and the minimum duration; otherwise the timer is bounded by the adopted maximum. The outer `finally` closes the managed Job even if the camera actor fails. A media probe is technical only; original-frame editorial review and final video signoff remain separate.

## Evidence boundary

R209 take02 was a real 179.033-second, 95,590,470-byte client-only raw with an empty managed process tree at Finish. Three decoded frames show the CK3 map date changing from 1067-01-20 through 01-22, without a visible Army supply/stock panel. R209 later ended through managed timeout, so neither the original case nor the take claims normal CK3 exit 0. That fact remains unchanged by this reusable candidate.
