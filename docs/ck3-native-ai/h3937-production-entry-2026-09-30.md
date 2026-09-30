# H3937 production entry projection — 2026-09-30

## Scope and evidence

The isolated source base is `62e6cb41c575651f28c0c7c0f363f3228feeb559`.
H3937 project modules originate from #685
`e7c0727b7e851de803f79ce04806feccfa33149d`. The projection adds the two
project entry scripts, read collectors, cold observer and date hold. It adds
only the required province query, route inventory and H3937 hold hunks to
`bridge/native_driver.py`; master child defaults, piety and unrelated movement
policy remain intact. `bridge/war_contract.py` matches the source module.
Shared runtime/session/readiness hooks are delivered separately; no whole old
runtime or native source tree is substituted for current master.

The production inert launch observation is
`C:/h3937-entry-20260930/attempt-03/freeze.json`, SHA-256
`5A24B1326799A49932B3BE987C8DCF502F8CE7CFC4098698666BBDE5285E6599`.
It used a deliberately nonexistent game executable: watchdog readiness
succeeded, CreateProcess returned error 2, existing launch failure cleanup
returned true, held actual child handle returned wait 0 / RC 1, both observed
watchdog PIDs were absent afterward, and no CK3 process was started. The
actual child argv was unavailable. This does not prove the cause of a13,
the whole chain deadline, or live readiness. Earlier environment/import RED
attempts remain preserved.

New entry config gates passed 2/2 normally and 2/2 with `-O`; the newly projected
production province query path passed 1/1 in each mode. Receipts are in
`C:/h3937-entry-20260930/attempt-06/`. Existing diagnostic 4/4 and API 7/7
evidence is reused. Completed live six reads remain **0/6**.

## Explicit inputs and entry commands

Both `h3937_cold_observer_once.py` and `h3937_combined_once.py` require
`--config <absolute-json-path>`. Calling either without config exits before
the old attempt can run. The config schema is `xar.h3937.run-config.v1` and
requires these nonempty string fields:

| Fields | Input |
| --- | --- |
| `schema` | `xar.h3937.run-config.v1` |
| `round` | Allocated `R<n>` artifact round |
| `live_run_id`, `live_execution_id`, `pipe` | Fresh explicitly assigned tuple |
| `task_bus_dir`, `task_bus_cli_sha256`, `screen_task_id` | Current authority inputs |
| `no_launch_dir`, `output_dir`, `go_receipt`, `screen_attempt_dir` | Fresh absolute paths |
| `python_executable`, `python_version`, `game_dir` | Explicit verified runtime inputs |

Path fields must be absolute. The parser does not allocate IDs, prepare state,
create GO or grant gameplay authority. The supervisor preserves the exact
config bytes, includes its SHA in the claim, and passes the same config path to
the worker. A worker claim with another config SHA is rejected. Existing
10-second watchdog readiness, nonce checks, cleanup and unsafe policy remain.

For this machine the explicitly verified interpreter is
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`, Python
`3.14.7`, pywin32 `312`. The final checkout must contain its runtime imports
and `tools/build_release.py`; formal profile preparation also needs the main
mod source allowlist even for `xar_off`. A sparse environment failure before
those inputs exist must be recorded as environment RED.

After final source delivery and allocation of the actual tuple, freeze the job:

```text
<verified-python> <final-checkout>/ck3_autonomous_player/h3937_freeze_operator_profile.py --config <new-config.json> --output <new-operator-profile.json> --operator-state-dir <new-absolute-operator-state>
```

The create-only profile pins the exact config, interpreter, entry, actual
Python source closure, watchdog, release helper, DLL and injector. Target
identity is `token_user=1`, `desktop=WinSta0\Default`,
`machine=DESKTOP-3FEVHD2`; transport is local `stdio`. The configured job
`h3937-six-readonly` executes:

```text
<verified-python> -B <final-checkout>/ck3_autonomous_player/h3937_cold_observer_once.py --config <new-config.json>
```

Run the real local stdio SDK against
`<verified-python> <final-checkout>/ck3_autonomous_player/operator_mcp_server.py --profile <new-operator-profile.json>`.
Read capabilities, status and `operator_preflight_job` first. Handoff requires
the separately authorized GO, exact admission and freshly reviewed offline
screen evidence; a profile or preflight GREEN does not supply that authority.
No other-machine native-headless session is reused.

## Native pair and next actual read

The pinned existing pair is
`D:/ck3-research-artifacts/h39on14/xar_ck3_bridge.dll`, SHA-256
`3438E8725AA06839CA1F2DFAF6D6CC98D41A4F33C02AC0702AC8D48AD241531B`, and
`xar_ck3_bridge_injector.exe`, SHA-256
`ECBC1B3B24E8A9BF1F85E9CBE195E4A5B8D3E928DB0FC8124ABF4D6D95A4B0D3`.
It was built from native source `4498daa90d93e051d428ea4d4a0d35f8beb1909a`
which matches #685's native subtree, physical inventory mailbox ON, cold VFS
observer OFF. It is not described as a new build of the projected master tree.
The formal no-launch attempt must preserve the pair under `source-verified/`.

The paused subject is actor `29829`, ArmyID `83886367`, WarID `16777231`,
province `2610`, date raw `53219928`, history `3937`, episode
`native-29829-2bc2d599f7f9`. The six envelopes are province-local siege;
route/contact to 2610 using the sorted **current-frame** hostile inventory;
army strengths; province-local siege at the observed relief target; read-only
move preview to that target; and route/contact to that target. Six successful
responses must share the paused frame and produce the expected history delta.
Historical hostile IDs do not replace the current-frame roster. Date advance,
movement and attacks remain unauthorized.

Desktop recovery is pending. No new live ID or GO is consumed by this source
delivery. The next producer uses final master HEAD and a new formal no-launch
state/admission, then supplies the allocated config to the frozen operator
profile and performs one authorized local operation.
