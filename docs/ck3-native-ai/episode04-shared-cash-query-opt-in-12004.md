machine_id: `desktop-3fevhd2-1c74096080`；来源观察 UTC 2026-10-18T05:10:18.287109+00:00。以下为作者原 ROOT-USE 正文（6992B / SHA-256 71e529c286a7fa36306bb8f9586a08575a27160e31f9fc611515c42d82257ad5），本段为整合补注。原件与资格在 [source delivery](evidence/episode04-shared-cash-query-opt-in-12004/SOURCE-DELIVERY.original.json)。

本次只修改公共 host 的 Python 开关与 binder；native_bridge 整棵 Git tree 因 research Python 文件而变化，C++、headers、CMake、flags 零差异。旧 a36 q 与当前 R207 source6a5a 仍按各自实际绑定使用，不追认新 host 已注册、不热启 sampling 或 debugger。旧 writer 模块是调用方显式提供的独立依赖；其本机路径仅来源，不是跨机部署协议，binder 本身不包含完整 observer 部署资格。研究9/14、业务6/11、动态0/11、ABC0/3不涨。

# Common cash opt-in and same-owner writer binding

Source candidate only. Base 6a5a42eb563aa12951f9a0d16141146a9fdeec1d; native remains the already selected a36. Current R207 host was started without cash registration and cannot acquire this tool from a source edit. Use the opt-in only in a later freshly prepared shared manifest/host. No SDK, host, observer, process-handle read, or native execution was performed by this package.

Apply the two-path relative patch, then copy the binder and its focused test to the targets in ROOT-DELIVERY.actual.json. Future shared manifest: `"host_features":{"war_cash_queries":true}` (retain other declared features). This flows through the existing shared argv, host parser, MCP child argv, and RecordingDriver attribute into the existing MCP registration gate. Missing/false stays OFF; nonboolean is rejected. Re-pin changed shared host/source-index/runtime selection through the existing preparation path. No native flag or build changes. The existing gate registers the private cash family, including its two other existing cash outcome queries; it does not start sampling or a debugger.

Actual cash request:

```python
tool = 'ck3_query_war_cash_current_resources_private_v1'
arguments = {'expected_revision': fresh_snapshot['revision'], 'payment_sampling': 'query'}
```

The response body preserves `war_payment_observations_v1` and the optional `current_raw_context_v1`. The query alone does not enable a window. Existing payment enable needs natural-phase already ON, a paused same-owned-process no-load window, fresh revision, and `payment_window_contract='same_owned_process_no_load_v1'`. The binder never sends enable/disable/clear.

Root invokes this from its existing common case callback, with the **same** actual `context` and `client` owned by `run_case`; no standalone live CLI creates another host/client:

```python
from tools.ck3_mod_acceptance_cases import r08_writer_common_adapter as common
from tools.ck3_live_run_id import current_machine_id

inputs = common.collect_current_context(context, client,
    machine=current_machine_id(), prefix='r207-cd-inputs-unique',
    packet_root=Path(context['output']) / 'r08-current-inputs-unique')
# inputs['expected'] contains actual PID, exact retained-handle FILETIME,
# generation, actor, episode, revisions/date, window and epoch. OFF/null is
# reported as observed; it is not promoted to observer admission.
```

Public `adapter_context` does not provide machine_id; it is an explicit argument, matching the existing R05 relay. `CommonPackets` calls `CaseClient.execute_plan` with fresh unique IDs, complete tool body, and continue_on_error to preserve the original RED without premature host shutdown while Root converges an attached observer. Every derived legacy-shaped view carries exact original `*.actual-results.json` pin and `/rows/0/result`, and is labelled `derived_common_case_control_row_not_original_SDK_transport`. No fabricated SDK transport. Unknown original requests are never retried.

For a later **independently authorized** Root 45-second DR window only:

```python
writer = common.bind_legacy_driver(verified_writer_module, context, client,
    machine=current_machine_id(), root_window_guard=root_existing_45s_guard)
prepared = writer.prepare(config_pin)
session, result = writer.observe_prepared(config_pin)
# Retain writer/session/Popen in this process. If cleanup remains unproved:
# writer.finalize(session); no restart/kill/new debugger or replayed game day.
```

`verified_writer_module` is the existing pinned Root driver, not its old R206 runtime: `C:/ck3-e04-resume-20261015-a01/r206-cd-writer-root-driver-a01/writer_root_driver.py`, 29902 bytes, SHA256 a1d2cd48085b66c132f07f0fc96ae8b30909505bdf326fcd7019b266f9460b74. Its pinned card, selector, and exact-day validator remain recorded dependencies. The common binder replaces only this passed module's `load_config` and `RootRuntime`; it does not load its old R206 entry, hardcode actor33388, or choose native/host. Do not run that old driver's standalone source-check as a claim about the new common runtime. Portability of this callable requires distributing that exact dependency and its recorded pins alongside the existing observer tooling; this package does not silently copy or rename it.

Common driver config extends the existing writer config with:

```json
{
  "schema": "xar.e04.common-cd-writer-driver-input.v1",
  "request_prefix": "r207-cd-observe-unique",
  "control_root": "<new path within context.output>",
  "common_packet_root": "<path within context.output>",
  "watch": {
    "repo": "<current context.repo_root>", "python": "<selected common interpreter>",
    "source_head": "<actual next shared source HEAD>",
    "before_response": "<inputs.before_response.path>",
    "cash_response": "<inputs.cash_response.path>",
    "expected": "<inputs.expected OBJECT, not this placeholder>",
    "build_dir": "<existing qualified a07 observer directory>",
    "machine_execution_gate": "<actual a07 SYSTEM execution gate>",
    "watch_output_root": "<new finite observer directory>",
    "timeout_ms": 30000, "max_slot_hits": 128
  }
}
```

Root's existing independent guard must bind actual scene/source/identity/deadline, the explicit external-debugger exception, the finite day allowance and R06 mutual exclusion. Default guard None rejects before prepare/observe. Ordinary scene/noobserver capacity and native/SYSTEM qualification alone never authorize attachment. Actual a07 watch is fixed four DR slots, 30 seconds and 128 aggregate hits, not c/d-only. The unchanged driver retains Popen through ready true + armed_thread_count>0, fresh cash/window checks, the one existing native-composite `ck3_execute_step {'step':'life-advance-one-day','expected_revision':None}`, independent after, natural terminal/restore/detach, and strict consumer. No new Arm/Resume, no alternative clock protocol, no force-kill or unknown retry. Current R207 explicit observer window is not granted by this candidate.

Only the new combined offline test ran: real source AST fragments for the shared feature/parser/child/driver/existing MCP gate, plus actual binder with a fake common control transport writing original-row files. It checks absent/false/true/nonboolean, exact cash forwarding, same client/derived provenance, OFF unchanged, missing Root guard, and RED no replay. It does not qualify a real host/adapter/observer or payment business.

Canonical focused smoke after integration (one test, no SDK):

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -O -X utf8 tools/test_r08_writer_common_adapter.py --repo D:/workspace/ck3_eternal_recurrence --scratch-root <new external small scratch>
```

Before apply, exact executed argv with candidate-builder/adapter paths is in FOCUSED.actual.json. No additional case matrix is needed. Raw c/d writer PC -> same NET -> payer/cadence remains unclosed; no sample or R08 credit follows from this registration fix.
