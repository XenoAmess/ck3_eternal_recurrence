# R0266 H3911 receiver plan for one formal query

Status at the 2026-09-28 cutoff: **prepared on paper only**. The fixed `WAR/M5-WAR-CASH-20260928/RECEIVER-REQUEST-R0321-H3911-MATCHED-PAIR-v1.json` hashes to `1C82BD10B526179AE1AEC4CF8F8A452190089D5204DF031212B501371601769F`. Its source ACK, planned/final manifests and six payloads have not arrived. No receiver rebind, no-launch or CK3 attempt has run. All five war-cash amounts and the horizon remain `null`; M5 spending stays closed.

This plan is for a **new #449 attempt** from frozen H3911. Source-side H3911 official pairing and no-launch qualify the source pair, not a receiver run. R0321's forecast producer was RED and the failed turn selected no action; one formal `auto_turn()` may therefore select something other than the termination-options query. The `before_submit` guard must then stop it. Do not force a selected step or graft the direct H2743 query into this attempt.

## 1. Receive exact bytes, then freeze an independent input set

Wait for `SOURCE-ACK-R0321-H3911-MATCHED-PAIR-v1.json`, `SOURCE-R0321-H3911-MATCHED-PAIR-PLANNED-MANIFEST-v1.json`, all six payloads, and `SOURCE-R0321-H3911-MATCHED-PAIR-MANIFEST-v1.json`. The planned manifest must measure the two binary sizes. Independently stream-hash each local OneDrive payload against both manifests and this request, record file size, SHA-256, source/copy path and receipt SHA, and preserve an immutable out-of-OneDrive copy. Reject a missing, renamed, duplicate or mismatched item; do not substitute the source's rebound driver or an older build. The fixed WAR writer owns its receiver ACK.

| Exact target filename | Required bytes | Required SHA-256 |
| --- | ---: | --- |
| `R0321-H3911-source-xar_checkpoint.ck3` | 78,514,751 | `5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746` |
| `R0321-H3911-source-driver-state.json` | 46,002,331 | `DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33` |
| `R0321-H3911-first-heir-marriage-formal-v1.json` | 2,742 | `6F007805A9CC5B602858AF9A670F2A6A591EE269E19C6301239422FFBEEAE0B3` |
| `R0321-H3911-player-prisoner-ransom-formal-v1.json` | 1,383 | `D60736FB035B6E77D9F71641AD76B2006FB975CC1187C77CC2FB0BA91BAA115F` |
| `R0321-runtime-xar_ck3_bridge.dll` | source manifest must supply | `C71F6A5DFE8D23374B5B73F9DFA18AD9455CFF087D36EC93D2D29F7F610E8786` |
| `R0321-runtime-xar_ck3_bridge_injector.exe` | source manifest must supply | `F9F2472C5969A248E7942AC79CC17A03CFDDA24C7FF79E78DA810A66A0E30C15` |

The source pair identity is `FDE4CC3A64DF5BB5D83F7B132FE5CC2985D31ACA28F0883A1C6245C197B5915E`, with actor `29829`, episode `native-29829-2bc2d599f7f9`, history index `3911`, date raw `53219928`, WarID `16777231` and native source commit `a6d1ae845f11e1e0bae79cac3fd9c30b00afae59`. Verify these against the received source driver and sidecars; a matching filename alone is insufficient.

## 2. Independent receiver no-launch qualification

Only after all six bytes pass, create a fresh append-only external `attempt` and state/profile. Verify the current #449 Python source/CLI and the exact CK3 1.19.0.6 EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`. Audit the actual `C71F...E8786` DLL and `F9F...0C15` injector against their native source/build evidence and read-only query/zero gameplay-submit path; source commit identity and binary bytes are separate facts. Do not infer ABI compatibility from source-side no-launch.

Run the official `prepare-profile --xar-enabled xar_off`, copy the frozen save/source driver and required sidecars into the new state, run `rebind-ordinary-seed-v1` with the **source driver's exact pipe**, then run `native-one-generation-preflight` against actor `29829`, the episode above, the unchanged save SHA and the **new receiver-derived driver SHA**. Save command argv/stdout/stderr, environment, rebind and preflight reports and their hashes. Confirm `ready`, no launch attempted, and no CK3/recorder processes. Never use source rebound driver SHA `BF58AB4FE890F7AAAC6EA8F0254655DA869BB3327DF867C6D217550165D9085D` as the receiver-derived driver. A new attempt is needed after any changed input or code.

## 3. One bounded formal selected-query run, only with screen release

After the screen owner explicitly releases its lease, confirm zero CK3/recorder processes and obtain a fresh Steam **offline** desktop frame with the project recovery/freshness procedure. Use an isolated new attempt and the verified exact DLL/injector. Invoke `native-auto-run` with one turn, `--cold-start-checkpoint`, `--bridge-mode native-headless`, `--formal-war-query-receipt-dir <fresh-external-dir>` and `--formal-war-query-source-commit <receiver #449 40-hex commit>`. Verify all flags through this checkout's `--help` before launch. Use readiness at least 1,800 seconds and total session budget at least 3,000 seconds, based on this host's earlier cold-start timing. Keep the input source bytes unchanged; preserve the complete managed log and clean-exit receipt.

The runner's `service.auto_turn()` must actually select `query-war-termination-options-16777231` with typed `read_only_query` before it sends anything. It must preserve the parsed request/envelope, request ID, protocol version, native query sequence, WarID, before/after six-field frame, PID/creation FILETIME, mapped EXE/DLL **disk-file** hashes, injector hash and prelaunch/postrestore/postquery driver hashes. Require no gameplay submit or date advance, the same paused native/public revision and snapshot, and clean process teardown. A different or null selected step, forecast RED, timeout, mismatched response, missing process binding, or uncertain cleanup is a preserved RED attempt, with no query zero-fee inference.

## 4. Cash promotion gate

Review the new raw artifacts independently. The #449 binary-audit and runtime approval registries are intentionally empty, and the managed receipt itself always reports `formal_cash_receipt_eligible=false` and `immediate_war_action_cost_raw=null`. Only after exact receiver pair/no-launch, independently audited binary query path, real selected typed query, raw protocol and same-frame/no-submit receipts all match may a separately reviewed SHA-pinned approval consider **that exact query's** conditional immediate fee of integer zero. The source native commit, receiver Python commit, actual loaded DLL bytes and launch injector bytes must each retain their own provenance; never collapse them into one claimed build identity.

Even a successful conditional query fee leaves pending commitments, future war cost upper bound, future risk budget, Robert's unpublished war liquidity floor and horizon unknown. Do not backfill H3911 or any newer Robert frame, treat an empty command history as zero commitments, use a GUI fleet total as the query's fee, or open the construction/war joint cash gate.
