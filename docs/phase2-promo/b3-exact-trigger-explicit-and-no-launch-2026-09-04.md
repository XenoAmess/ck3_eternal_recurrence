# B3 exact trigger 显式 AND 生产候选（2026-09-04）

状态：**Frontend loader GREEN / full acceptance RED**。排他调度者已经执行一次文末命令；显式 AND 候选恢复了 Frontend，但没有进入 Load Save/In Game，未执行 gameplay，也未生成宣传素材。原命令已经消费，不得再次执行或复用 pipe、userdir、artifacts 根。

## Live verdict

实机 artifact：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\artifacts-live`

- 303 个 database callbacks：`123.801s`；Frontend：`125.965s`。
- terminal：`save_resume_red / frontend_without_load_save`，`299.845s`，Frontend quiet `173.88s`。
- zero-argument provider、unknown trigger、unknown effect、parser error：全部 0。
- 已知非终止噪声：unrecognized loc `952`、set-but-never-used `13,990`、used-but-never-set `90`。
- native cleanup 的全部 checks 为 true、failed checks 为空、最终 CK3 process count 为 0；protected storage 与 source/product/runtime trees 均未改变。
- outer report SHA-256：`f0abc5f24505019061b986db8992ca0ddd95c0d584c6c9f24b5d4bf6bb9b9b70`
- evidence index SHA-256：`a6049d099759571921a5e81a0634517e25c91e5a0452aaba0d583041f6bfce5f`
- cell report SHA-256：`9a9ae5c6f52aab6fc99f6d44d918c9556a8c43bcef25c430583097d8846b9e17`
- final error SHA-256：`5acd90c8c74a82014abe065b33cb51d6bdef2df6298c0e83d9e296333b818a9d`
- fail-closed `live-verdict.json` SHA-256：`abb706b08d6dcf8319bf7046567f27a28049d745fef4be104cb5cdeb38d260a2`

`tools/postprocess_zg361_b3_exact_and_wrapper_live.py` 对 no-launch manifest、projection、outer/cell/evidence、error/debug、loader gate 和 append-only progress 的完整 SHA-256 fail-closed，并精确断言上述阶段、时间、噪声、单文件 delta、参数 ABI 与 cleanup。后处理结果为 `GREEN_EVIDENCE`，其含义只是在冻结的 CK3 1.19.0.6/r5 投影上闭合“exact trigger AST shape 敏感且显式 AND 是最小修复”这一结论；整体 acceptance 仍为 RED。

## 为什么只改这一处

ABI-safe V1/V2 实机互斥隔离已经把启动差异缩到 `zg361_p2c_m360_frozen_manager_exact_trigger` 正文：

- V1 保留真实 `candidate_ready`、把 `frozen_manager_exact` 换成消费全部参数的 false stub；约 `114.894s` 到达 Frontend。
- V2 把 `candidate_ready` 换成消费全部参数的 false stub、保留真实 `frozen_manager_exact`；完成 303 个 database callbacks 后仍没有 Frontend，terminal elapsed 约 `299.912s`。
- 两份 live 的 unknown trigger/effect、event not found、parser、recursion 和 `should have no arguments` 材料错误计数均为 0，native cleanup 均为 GREEN。artifact 分别位于
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z\v1\artifacts-live` 与
  `...\v2\artifacts-live`。

因此本候选只做一个 AST-shape 变量：在生成器中把 exact trigger 原来的顶层隐式 AND 正文原样嵌入一个显式 `AND = { ... }`。没有增加 `always = no`，没有删除、增加或改写任何业务条件、参数、嵌套 `candidate_ready` 调用或三个产品调用点。该实验检验的是 CK3 对这段 trigger AST 形状的加载行为，不把文件大小或文件边界宣称为根因；此前 r5 A/B/B/A 实机也没有给出稳定的文件体量收益。

候选提交为 `4d3c284749f217aac1a2b291721ebd30a2c84a0a`，分支为 `codex/b3-exact-and-wrapper-20260904`。新候选已到达 Frontend，因此 loader 修复具备合入 canonical 的实机依据；这不等于 B3 gameplay、Phase2 或 T0 完成。

## 单变量与 ABI 证明

冻结基线是 r5 A：565 files，tree SHA-256
`50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f`。新候选仍为 565 files，其中 564 files 逐字节不变，唯一变化路径是：

`common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`

- r5 provider：16,712 bytes，SHA-256 `ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7`
- candidate provider：16,786 bytes，SHA-256 `bb771a488fecc9fc131a20c562ab621d432414fa864e838c35d7e28520d7e411`
- candidate tree：21,607,199 bytes，SHA-256 `d94c2d5d23e9ad254f4b20988fbf3c8e08408baa61070bd85f42b2d2fcbea35d`
- 原 exact body SHA-256：`34ef467740aeaa5ff734613d777ece39b1feca036aa011885a28bb635c81676b`
- 显式 AND exact body SHA-256：`cef67162605e6fc404cb1b584726efd573522243d9965ac79bd785a609a05e28`

freezer 先对旧 exact block 执行唯一确定的 wrapper 变换，再要求生成结果与期望 provider 逐字节相等；同时断言 `candidate_ready` block 逐字节不变、exact 解包后的条件逐字节不变、调用图不变、两个 definition 及 provider union 的 `$PARAM$` 集合与 r5 精确相等。

## No-launch 门禁

外部冻结根：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z`

- `attempt-manifest.json` SHA-256：`e07bf7605aeaf47d533f9c4cb28895fe3ecd7028ae32f92d6ed84c879f9a62d7`
- `projection.json` SHA-256：`241db7b5e2df451aadbfaeb4570b083c8563239bc0158530682b9a77da2f4acd`
- open_kaishek parser report SHA-256：`5fd2f86c4ce0e5097474389c9fe39606301f56b6b01b3400150df36aecb5dc71`
- formal preflight log SHA-256：`9296d3ba103ab30907edc2c93dd5bf7e9582ecbecc6a4187efb123a5e2ec3287`
- A2 runner SHA-256：`2dd1067f7a0de9076cacc552bd2f786c00f1b04af9ef969eaa258ea2e7a747c6`
- open_kaishek parser/root-parser：0 diagnostics / GREEN；offline provenance GREEN。
- Central custom-call closure：GREEN；reachable effect/event/trigger 为 `1868 / 560 / 16`，三类 missing 均为 0。
- generator `--check`、Central tests 与 freezer tests 的普通及 `-O` 共 5 条命令全 GREEN。
- formal `--preflight`：GREEN；`artifacts-live` 不存在；freezer 前后 CK3 process count 为 0。

## 唯一实机命令

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_3807cfd9441d07411928006105d1cc17 --phase2-seed-contract Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source --phase2-product-projection b3-r5-exact-trigger-explicit-and-4d3c284 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\artifacts-live --discard-userdir
```

该命令已经执行并消费；pipe、userdir 与 artifacts 根不得复用。Frontend GREEN 只证明 loader 假设，不等于 B3 gameplay 或 T0 全量 GREEN。
