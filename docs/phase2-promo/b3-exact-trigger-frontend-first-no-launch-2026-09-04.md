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
