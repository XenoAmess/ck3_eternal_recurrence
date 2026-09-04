# B3 trigger body 互斥二分候选（2026-09-04）

状态：**V1 / V2 均为 `GREEN_NO_LAUNCH`，仅供一次性诊断，不是 production candidate。**

## 目的与单变量边界

r5 A 相对 r4 唯一新增的产品文件是
`common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`。双 `always = no`
候选只能判定两个真实 body 的联合影响；本组在同一 frozen r5 A 上做正交互补：

- V1：`zg361_p2c_m360_candidate_ready_trigger` 保持 r5 A 真实正文，
  `zg361_p2c_m360_frozen_manager_exact_trigger` 换成最小 `always = no`；
- V2：`candidate_ready` 换成最小 `always = no`，`frozen_manager_exact` 保持 r5 A
  真实正文；后者内部调用仍指向同名的 `candidate_ready` stub。

两棵树都只有上述 trigger provider 的 SHA/bytes 变化，没有增加、删除或修改其他路径。
这些 stub 不进入 `tools/gen_361_phase2_central_runtime.py`、正式 projection 或 production；无论
live 结果如何，都不得把它们合回生成器。

## 冻结输入与计数口径

- frozen r5 A：
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\product-source`
- 基线：565 files / 21,607,125 bytes / tree
  `50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f`
- 基线 projection manifest：
  `2052dada087a91273a3b15587a34b00c861cca543dbe14926026f3a2ba29b298`
- 基线 trigger provider：16,712 bytes /
  `ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7`
- 候选根：
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z`
- attempt manifest SHA-256：
  `3d5a711f8c00cb0a1c7dd3ff3b8a64ca81e01486f2afc342cf3dbb7898094651`

冻结 r5 A 的 565 是**总文件数且包含 trigger provider**，因此每份候选是 565 files，
其中该 provider 修改 1 个、其余 **564** 个逐字节不变；不是“565 个其他文件”。机器清单对
changed/added/removed 做了集合和 SHA 双重检查。

## V1

- product：`...\20260904T0835Z\v1\product-source`
- 565 files / 21,606,417 bytes；564 unchanged；added=0，removed=0
- tree SHA-256：`47b077bc1a71229219d7b4c2c8e5064d055ae74c15a183ab1047455ebfbf85fd`
- trigger provider：16,004 bytes /
  `4c13d55bd363a348873c0f0cbc8af5945865bf244d7d70d05b7c8f54411df632`
- projection manifest SHA-256：
  `1e67b19b607b1117d96794c5626563a1f1cb18931be6e3a8a2ae2791e667ac9f`
- real `candidate_ready` body SHA-256：
  `5bfe697f42cebda0e70f04e3df65c76f486e2320ebca878f0ae5116786c12c92`
  （与 r5 A 完全一致）
- false `frozen_manager_exact` body SHA-256：
  `481bf258f20e21fda5d10249ff9b9e938c041c687efa147d36988692f2032367`

## V2

- product：`...\20260904T0835Z\v2\product-source`
- 565 files / 21,591,507 bytes；564 unchanged；added=0，removed=0
- tree SHA-256：`88d4889a7d6491a260e29b06f3251d79ed79948c7b3d1f7b7f9777e20c76535c`
- trigger provider：1,094 bytes /
  `a6c72b0c8d1580b72cd56207bc4729159fd9cfe0debe4eb0a8dda00b366f43a2`
- projection manifest SHA-256：
  `260d1cdff93b5fefde72f3b1ca48186c19e8f4767b9682843ad1ba3d28fd0205`
- real `frozen_manager_exact` body SHA-256：
  `34ef467740aeaa5ff734613d777ece39b1feca036aa011885a28bb635c81676b`
  （与 r5 A 完全一致且仍调用同名 `candidate_ready`）
- false `candidate_ready` body SHA-256：
  `7c91b16df8e284db92893cb7845fa4b9e557ebce31e8c2104e2b6256a27c9a44`

## Parser、闭包与 no-launch

两份候选均满足：

- BOM 与 `GENERATED FILE` header 保留；顶层 parser 精确得到两个原名称、一个真实正文、一个
  最小 false stub；
- open_kaishek parser：521 files / 0 diagnostics，root parser：520 files / 0
  diagnostics；V1 报告 SHA
  `d86465d77d7dad8aa96761eab41f40d6ec8d62443dd4abc78542e722a9f2f481`，V2
  报告 SHA
  `6c95a8db445b0b079ef3e82a6f2d3a69a29fef4e4db0f901c4e2c2b784fc2b49`；
- open_kaishek profile validator 的 schema-only RED 不冒充 CK3 语义结论；本轮只采用 parser 与
  root-parser GREEN；
- central closure GREEN：reachable effect/event/trigger = 1,868 / 560 / 16，三类
  missing 均为 0；
- formal `--preflight` GREEN；V1 日志 SHA
  `02d679048ed7ec9ef8e4bd96f66cd5fc66759ceff920e6d71849976b1294b5a9`，V2 日志
  SHA `349e42c46c78c9250710d06e63ace61e6c42ac7f5444d18e8c384f10f36a2d79`；
- 两个 `artifacts-live` 路径均不存在；`ck3_launched=false`。

最初两次派生只形成不完整 harness 尝试：第一次从独立 worktree 执行 runner，缺少被 Git
忽略的原版 game tree；第二次误指向旧主 checkout 的 runner，参数 ABI 过期。两次均未启动
CK3，也没有进入候选清单。最终版本显式绑定 canonical runner root，避免把 checkout 环境问题
误记成产品 RED。

## 唯一 live 命令

V1：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_74f5d7bfba66c4cb3cb2be9b23c87747 --phase2-seed-contract Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z\v1\product-source --phase2-product-projection b3-r5-trigger-body-bisect-v1 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z\v1\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z\v1\artifacts-live --discard-userdir
```

V2：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_6ec18ab84953f5709c71cbc4030c6cf5 --phase2-seed-contract Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z\v2\product-source --phase2-product-projection b3-r5-trigger-body-bisect-v2 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z\v2\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z\v2\artifacts-live --discard-userdir
```

两条命令的 product、projection manifest、artifact 目录和 32-hex pipe 均互异。它们尚未
执行；必须由 CK3 排他调度者按实验顺序逐条启动和回收。
