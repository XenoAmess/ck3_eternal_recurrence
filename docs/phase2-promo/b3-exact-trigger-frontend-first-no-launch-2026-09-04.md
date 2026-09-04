# B3 显式 AND frontend-first autosave 候选（2026-09-04）

状态：**long-root HARNESS/PATH-LENGTH RED；short-root startup chain GREEN；full acceptance RED**。本页原先冻结的 long-root 命令已由根任务的 CK3 排他调度者执行，不得再次运行；本次文档闭合没有启动 CK3。

## 目的与固定输入

前一轮显式 AND 产品已经在 `125.965s` 到达 Frontend，但原直载流程最终为 `save_resume_red / frontend_without_load_save`。本页原计划不改产品文件，改用 runner 已有的受管启动编排：先不带 save 参数启动到 Frontend，停止第一 PID，再在**同一 pipe** 上启动第二 PID 并加载已安装的 `autosave`。

固定产品仍是：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source`

- 565 files；tree SHA-256 `d94c2d5d23e9ad254f4b20988fbf3c8e08408baa61070bd85f42b2d2fcbea35d`。
- projection SHA-256 `241db7b5e2df451aadbfaeb4570b083c8563239bc0158530682b9a77da2f4acd`。
- 前轮 live verdict SHA-256 `abb706b08d6dcf8319bf7046567f27a28049d745fef4be104cb5cdeb38d260a2`。
- 生成 next-attempt manifest 前逐一复核 projection 的 565 个 size/SHA 条目；`mutated=false`。
- A2 runner SHA-256 `2dd1067f7a0de9076cacc552bd2f786c00f1b04af9ef969eaa258ea2e7a747c6`。

本轮唯一命令层增量为：

```text
--phase2-frontend-first-load-save-name autosave
--phase2-frontend-first-timeout-seconds 180
```

## No-launch freeze（执行前历史状态）

外部根：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-frontend-first-1beb8d1-20260904T101416Z`

- `next-attempt-manifest.json` SHA-256：`1a683b1f7857b3776dc16fae68532ae2093e15437058d816194ce8ed166109e0`
- formal preflight log SHA-256：`28956e63d654c467485dcb2c088d47331a3cb53d0ae8b537dd0d76e6c48e32a2`
- formal preflight：GREEN。
- fresh pipe：`\\.\pipe\xar_ck3_bridge_zg361_8357298ee3e7895ad1c3012f464e53b5`
- fresh artifact：`...\artifacts-live`，冻结命令时尚不存在。
- 生成完成后 CK3 process count 为 0；`ck3_launched=false`、`launch.executed=false`。

## 已消费的 long-root 命令

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_8357298ee3e7895ad1c3012f464e53b5 --phase2-seed-contract Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source --phase2-product-projection b3-r5-exact-trigger-explicit-and-4d3c284 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\projection.json --phase2-frontend-first-load-save-name autosave --phase2-frontend-first-timeout-seconds 180 --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-frontend-first-1beb8d1-20260904T101416Z\artifacts-live --discard-userdir
```

该命令已经消费，不得复用 pipe、userdir 或 artifact 根。

## Long-root：harness/path-length RED

实际 artifact：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-frontend-first-1beb8d1-20260904T101416Z\artifacts-live`

runner 最终把产品实现到：

`...\artifacts-live_native_state\profile\mod-content\zhongguo_361`

- immutable product 仍为 565 files；实现后最长完整物理路径为 `264` 字符，多条路径超过 250。
- `error.log` 点名的 `common\scripted_effects\zg361_feedback_promotion_pip_038_w_m189_m190_lifecycle_effects.txt` 完整物理路径为 `255` 字符，并报告 `path is over 250 characters long and will likely cause a crash on open`。
- warm-up 没有到 Frontend；marker wait 约 `5.16s` 后进程以 code 1 退出。
- outer/cell 均为 RED；启动/session 未成功，因此 native cleanup 也为 RED。protected storage 保持不变，gameplay 为 false。
- outer report SHA-256：`6bd454f9da8023dc07eaa9b45d10d88daf8a0bf7b91118a936cc27fcb1706f92`
- evidence index SHA-256：`d7caa853c28a293acb52c795676d65964709f4a52f305e6ceaa6221211eff535`
- cell report SHA-256：`a338cfada9d2978b2da1c4dfe14cc58257ef2256f1d474bc7a239cb662eabb75`
- final error SHA-256：`290f7205483a4decc74a9bf513b1842007fbc4f752f00e74700eb3980a2450e6`

formal no-launch preflight 对 source/projection 与命令合同为 GREEN，但没有阻止 runner 后续追加 `_native_state/profile/mod-content/zhongguo_361` 后形成超限物理路径。以后 path preflight 必须对**最终 materialized mount** 枚举完整路径，而不能只看 source、artifact root 或相对文件名。

## Short-root replay：Frontend / autosave / map chain GREEN

根任务随后用同一 frozen product 和 frontend-first 编排在短根串行重放：

- artifact root：`Z:\ck3_mod_rewrite_process_assets\zg361\b3j-ff-1817`
- native state root：`Z:\ck3_mod_rewrite_process_assets\zg361\b3j-ff-1817_native_state`
- 仍为相同 565-file product；最长完整物理路径降为 `197` 字符，没有改 effect 文件、定义边界或产品树。
- warm-up 在 `121.449s` 到达 Frontend，四类 frontend signals 全部为 true；首 PID `72688` 受管退出，job count 回到 0。
- 安装并由第二 PID `40172` 加载 `save games\autosave.ck3`：`53,517,622 B`，SHA-256 `bfc73fd9e7e80145cdf39aabc66bc2d731881122adab0cc0ba675fa07d1e6733`。
- native session、seed install、loader readiness 全部 GREEN；同一 pipe connection generation 稳定为 1，paused snapshot `map_ready=true`。
- native cleanup GREEN、job active processes final 为 0；protected storage 保持不变。
- outer report SHA-256：`fc8af93d63b0201198b26ba00935fee312702ccd2b35cb5044f401070272dd3e`
- evidence index SHA-256：`1a71351e5f1513d7a0c5eca8f377d3202626edd075e75b36b6df7f5b7eaa2cb5`
- cell report SHA-256：`4ed6c3b0fbb96598d6c35103b48720f695c41c14678be4a20ea4794e65ab79f2`
- native session SHA-256：`cddb8388b8962f1f8967beaf5c22b0b229d533b1f3494ac940d619e633017c84`
- loader readiness SHA-256：`3c222b0008386da39c5e4c0a36e66f58c50b2f90a938b5d9129667ccc0be1597`
- seed install SHA-256：`49a48828d552b38870a05839b2b1fdba9d47cd2ee4db469bb55ff0ed430c7cf9`

short-root outer/cell 最终仍为 RED，但已经发生在更晚的 MCP capability gate：缺少 `query-zhongguo-promotion-compensation-postcondition-v1`、`zhongguo_promotion_compensation_v1_query_supported` 与 `query-zhongguo-result-case-snapshot-v1`。因此只能宣称 `Frontend → autosave → paused map` 启动链已恢复，不能宣称完整 acceptance、B3 gameplay、T0 完成或 footage。

## 结论

这是一组 harness path-length 单变量对照：相同 565-file immutable product 在 long mount 的 `max=264` 时由 PhysFS 报错并崩溃，在 short mount 的 `max=197` 时进入 Frontend、加载 autosave 并到达 paused map。它证明本次 long-root RED 来自 runner 实现出的物理路径超过 250，**不是 effect 单文件体量回归，也不需要通过拆分 effect 文件修复**。此前“显式 `AND` 恢复 Frontend”仍是独立的 AST-shape 语义证据；两类故障与结论必须分账。

## Current canonical capability 审计与最小 runner 修复

2026-09-04 18:41（Asia/Shanghai）对 current canonical
`Z:\ck3_mod_rewrite\_root-promo-split-20260902` / `cac1e85b616827a9ae11d755dd71f119325e6f3f` 做了只读静态审计；
runner SHA-256 为 `8B526960AFA57C01361C1CFE30526A1AF5B808538F208C7EF855BB1900486581`。
完整 Phase2 capability preflight 的 mandatory 集合为 21 个 bridge capabilities、12 个 derived query/support flags，以及修复前
7 个 materialized action steps。short-root live descriptor 的 79 个 bridge capabilities / 18 个 action steps 与该集合比较后，
只有三条缺失：

| 层 | 缺失 | 证据与分类 |
|---|---|---|
| bridge advertisement | `game.command.query-zhongguo-promotion-compensation-postcondition-v1` | promotion provider 已布线，但所用 bridge 没有广告；21 项中通过 20 项 |
| managed derived flag | `zhongguo_promotion_compensation_v1_query_supported` | `native_driver` 从上述 bridge capability 成员关系派生；12 项中通过 11 项，不是第二个独立 provider 缺陷 |
| runner materialized action step | `query-zhongguo-result-case-snapshot-v1` | bridge capability 与 derived flag 都已为 true；缺的是 runner 错误要求的零参 action-step 形态，7 项中通过 6 项 |

live preflight artifact 为
`Z:\ck3_mod_rewrite_process_assets\zg361\b3j-ff-1817\cell\02_phase2_mcp_capabilities.json`，SHA-256
`FFD160C0F6643FF6BC20B5B140BC5C7912F1127F2CE7135F464C39BC1F7F1865`。其中 promotion 两行和 result-case
action-step 一行是完整的 `missing_requirements`，其余 mandatory capability/query/action 项均通过。

三层结论必须分开：

1. **Python runner / MCP tool 层**：`mcp_server.py` 已注册
   `ck3_query_zhongguo_result_case_snapshot_v1` 与
   `ck3_query_zhongguo_promotion_compensation_postcondition_v1`；`service.py` 和 `native_driver.py` 也都有对应 typed query
   调用链。result-case 需要 `owner_character_id`、`request_nonce` 与 revision；`native_driver._action_steps` 因此按设计显式
   不把它投影成无参数 planner action。旧第三条 RED 不是 MCP tool 缺失。
2. **bridge advertised capability 层**：canonical `cac1e85` 已加入默认 `OFF` 的
   `XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1`；只有 private candidate 以 `ON` 重建时才把 promotion
   capability 加进 exact adapter。derived flag 会随之自动变为 true。当前最新已构建 DLL 仍是修复前
   `971d1f9` 的
   `Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-product-native-candidate-971d1f9-20260904T102926Z\xar_ck3_bridge.dll`
   （`2,425,856 B`，SHA-256 `EE1A55085D2321409D7F201B0EFB5575F7FF2D5A1214BEB64147F93C0F00C72E`）；其
   CMake cache 没有新 flag，虽 94/94 native tests GREEN，也不能通过完整 Phase2 promotion capability 门。默认-OFF
   重建同样不会广告，必须明确构建 private flag-ON candidate。
3. **provider business readiness 层**：广告 capability 只允许调用，不证明业务结果。promotion registry 仍是
   `live-pending / native-provider-wired-default-off-live-pending / gameplay_action_complete=false`，必须取得真实 paused
   `zg361pp.147 → zg361comp.1` 同 generation provider result；manager governance 仍为
   `static-ready-live-pending`，scoreboard 仍为 `product-surface-checkpoints-pending`。三者仍列在
   `PHASE2_MISSING_GAMEPLAY_ACTION_CELLS`，不得因 preflight GREEN 宣称完整 Phase2 GREEN。

本提交同时闭合第三条 runner 缺口：从 `PHASE2_REQUIRED_ACTION_STEPS` 删除 `result_case_snapshot`，保留它原有的 bridge
capability 与 derived query flag 两道 mandatory 门。完整 preflight 因此改为 21 bridge / 12 flags / **6 action steps**；没有
把 typed query 降级成零参 action，也没有削弱真实可调用性检查。精确 regression test 证明：descriptor 不提供 result-case
action step 时 preflight 可 GREEN；删除其 bridge capability 或把 query flag 置 false 时仍分别 fail closed。no-launch 验证为
`Phase2FullCapabilityPreflightTests` 1/1 GREEN、`test_run_zhongguo_focused_b2.py` 16/16 GREEN，以及
`test_run_zhongguo_promo_capture.py` GREEN；没有启动 CK3。
