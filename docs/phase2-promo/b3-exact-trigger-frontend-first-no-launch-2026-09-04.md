# B3 显式 AND frontend-first autosave 候选（2026-09-04）

状态：**GREEN_NO_LAUNCH / frontend-first-autosave-live-pending**。本工作包没有启动 CK3；只有根任务的 CK3 排他调度者可以执行文末唯一命令。

## 目的与固定输入

前一轮显式 AND 产品已经在 `125.965s` 到达 Frontend，但原直载流程最终为 `save_resume_red / frontend_without_load_save`。下一轮不改产品文件，改用 runner 已有的受管启动编排：先不带 save 参数启动到 Frontend，停止第一 PID，再在**同一 pipe** 上启动第二 PID 并加载已安装的 `autosave`。

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

## No-launch freeze

外部根：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-frontend-first-1beb8d1-20260904T101416Z`

- `next-attempt-manifest.json` SHA-256：`1a683b1f7857b3776dc16fae68532ae2093e15437058d816194ce8ed166109e0`
- formal preflight log SHA-256：`28956e63d654c467485dcb2c088d47331a3cb53d0ae8b537dd0d76e6c48e32a2`
- formal preflight：GREEN。
- fresh pipe：`\\.\pipe\xar_ck3_bridge_zg361_8357298ee3e7895ad1c3012f464e53b5`
- fresh artifact：`...\artifacts-live`，当前不存在。
- 生成完成后 CK3 process count 为 0；`ck3_launched=false`、`launch.executed=false`。

## 唯一实机命令

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_8357298ee3e7895ad1c3012f464e53b5 --phase2-seed-contract Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source --phase2-product-projection b3-r5-exact-trigger-explicit-and-4d3c284 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\projection.json --phase2-frontend-first-load-save-name autosave --phase2-frontend-first-timeout-seconds 180 --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-frontend-first-1beb8d1-20260904T101416Z\artifacts-live --discard-userdir
```

该命令只能串行执行一次，不得复用 pipe、userdir 或 artifact 根。只有第二 PID 真正进入 Load Save/In Game 后才解除当前 `frontend_without_load_save`；Frontend warm-up 本身不得冒充完整 acceptance、B3 gameplay、T0 完成或 footage。
