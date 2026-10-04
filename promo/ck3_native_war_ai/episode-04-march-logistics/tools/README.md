# Episode04 managed capture tools

`capture_bootstrap.py` reuses Episode03's managed `native_session`, SDK service,
ordinary pure-vanilla lifecycle and single `ScreenLeaseKeeper`. It prepares a
fresh isolated profile and can bind an exact existing saved checkpoint. No
driver, SDK session or process is created by `prepare`, `check` or `--help`.

`capture_recorder.py` handles one explicit recorder request inside that owner,
with the existing suspended Windows Job primitive and the same keeper's
process-create gate. `sample_paused.py` publishes once to that SDK owner's file
queue, checks paused source identity, and preserves army supply/strength and
optional actor-global cash packets. Import and help perform no live operations.
No external Episode03 helper path is needed by these tools after checkout.

Every prepare and sample command requires `--assets-root`; state/run/raw/outputs
must remain below this explicit root, outside the source repository. Run them
with the task's explicit verified venv interpreter. Root freezes actual source,
native artifacts, same-baseline saves, live run-ID, exclusive screen admission,
fresh directly reviewed Steam-offline image and original desktop geometry.
Pure-offline checks do not certify live loading, game days, footage or approval.

Real command sequence:

```text
<verified-python> -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py prepare --assets-root <external-root> --game-dir <actual-game-dir> --state-dir <new-state> --output-dir <new-prepared> --bridge-dll <current-dll> --bridge-injector <current-injector> --bridge-host <current-host> --pipe-name <unique-pipe> --checkpoint-save <frozen.ck3> --checkpoint-receipt <actual-sdk-packet.json> --checkpoint-build-receipt <source-build-prepared.json>
<verified-python> -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py check --prepared <new-prepared>/prepared.json
<verified-python> -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py run --prepared <new-prepared>/prepared.json --run-dir <new-live> --steam-offline-receipt <fresh-root-review.json> --screen-cli <checkout>/tools/codex_task_bus.py --task-bus <bus-dir> --screen-repo <checkout> --screen-task-id <unique-screen-owner> --screen-expected-sequence <fresh-sequence> --screen-cli-sha256 <reviewed-current-sha> --timeout 21600 --default-desktop --private-war-cash-queries
<verified-python> -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/sample_paused.py sample --assets-root <external-root> --run-dir <new-live> --output-dir <new-operations> --pipe-name <unique-pipe> --actor-id <actual-actor> --expected-date-raw <actual-date> --bootstrap-sha256 <reviewed-bootstrap-sha> --tag <new-tag> --include-cash
```

All checkpoint options are supplied together or omitted. The actual SDK packet
must have `is_error:false`, `request.tool=ck3_save_checkpoint`, `accepted:true`
and materialized `checkpoint.status=saved`; its bytes, actor/date, lifecycle and
original build/profile are verified. The copied save is loaded with the existing
`frontend_first_load_save_name` library option; no old driver history is copied.
Root waits for actual full identity/native hello/pump stability and directly
reviews HUD after loading. `sdk-ready` alone is no loading proof.

`--private-war-cash-queries` sets `driver.allow_private_war_cash_query=True`
before the real `create_server` call and publishes that setting in sdk-ready.
Both `ck3_query_war_cash_current_resources_private_v1` and termination-cost
query registration depend on it. The actual DLL must also contain
`XAR_CK3_ENABLE_G2_M5_WAR_CASH_PRIVATE_QUERY_V1=ON`; a Python switch alone cannot
create a producer. Core supply, movement, army clock and Halt are existing
public/typed paths and do not need PREWAR or legacy military-preparation flags.
Samples preserve null fields and signed Q100000 monthly values. Cash is the
whole player's current flow, not a per-ArmyID allocation; net wallet/strength
changes are not automatically embark payments or attrition casualties.

`advance-samples` is explicitly live and sends at most90 `life-advance` steps,
checks each actual raw increment and stops at events/combat/retreat/roster
changes. The legacy primitive has sometimes advanced8/11 days. An increment
different from `--expected-day-raw-units 24` is retained RED and never retried;
do not advertise daily coverage until the actual date/clock evidence closes it.

Root publishes explicit `gameplay_recorder` requests via bootstrap `request`.
Start arguments are exactly `operation,start workdir,ffmpeg,ffmpeg_sha256,
target_pid,source_image,seconds`, with keys `operation` set to `start`. The path,
positive owned PID, reviewed original image dimensions and actual desktop,
paused map, actor and one-recorder policy are checked. `status` and `finish`
accept only their operation. Recording contains cursor, native-sized30fps raw
MKV, no audio, and is bounded1..3600seconds. Terminal Job must query empty;
source PTS, action spans and visual review remain independent work.

Finish raw and obtain `NORMAL_TREE_EMPTY`, then send tool `stop` with `{}`.
Observe actual session cleanup, SDK/keeper thread exits and all owned processes
absent; restore original display and fresh Steam-offline pixels before lease
release. Retain raw/partial, all saves, failures, argv/stdio, source snapshots,
requests/responses, marks, sample timelines and reports. No source/runtime
cleanup or upload is performed by these tools. Machine audit is never human
approval. A/B/C each use fresh state/output/pipe/session from one frozen save.

The original development package's eleven offline checks, with0 live sessions,
is retained separately. Its external source paths and source identity remain
history. These tools require their own exact-source focused check before use.
Open_kaishek is not applicable to this Python/native process and DTO wrapper;
game/script experiments must assess applicable deterministic semantics afresh.
