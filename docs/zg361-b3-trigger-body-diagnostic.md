# B3 两个 trigger body 的一次性诊断候选

## 当前结论

第一版 `b3h-fecd2f2-trigger-false-20260904-081911Z` 已实机证明为 **material/provider ABI RED**，不能用于归因 trigger body：
正文删除所有 `$PARAM$` 后，CK3 把两个 provider 推断为零参数，六个原 caller 分别触发共 6 条
`Scripted trigger should have no arguments`。因此下文第一版的 terminal 结果只能保存为失败候选证据，不能与 r4/r5 比较。

替代候选 `b3i-fecd2f2-trigger-abi-false-20260904-084813Z` 仍由首项 `always = no` 恒假，但在同一 `AND` 内用原合法表达式
显式引用全部 3/12 个 `$PARAM$`；exact provider 继续把 owner/P2C cycle/case 三参数转发给 candidate provider。它是当前唯一可运行候选。

## 目的与边界

文件边界 ABBA 已证明 A1 是首轮离群值，不能把单文件体量写成本次启动问题根因。下一项最小变量来自 r4 与 r5 的真实差异：

- r4 `b3f-1341251-20260904-070920Z/product` 有 564 个文件，缺少两个 trigger provider；CK3 报两个 `Unknown trigger` 各 3 次，
  但到达 `Setting idler 'Frontend'` 和 `End loading of history`。
- r5 A 有 565 个文件，闭包只新增
  `common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`，其余 564 个文件相对 r4 逐字节不变；两个真实 trigger body
  加入后，A1/A2 都没有 `Setting idler 'Frontend'`。

本候选保留新增文件、两个 trigger 名称和六个外部 caller 的参数 ABI，只把两个 body 临时改为 `always = no`。它只能回答
“这两个真实 body 是否足以解释 r4→r5 的 terminal 差异”，不能验证业务语义，不能进入 generator、正式 projection 或 production。

## 对照证据

r4 的 Frontend 里程碑为 GREEN（整次 acceptance 仍是 RED），其 `final_error.log` 为 3,652,831 bytes / 15,044 行，SHA-256
`0b084d2b92b9673ebeeef2ad1db2cc3477e7ab8c0f083bf98b78011069d54b49`；其中 `Unrecognized loc key` 952、
set-never-used 13,996、used-never-set 90。r5 A2 为 3,650,011 bytes / 15,032 行，SHA-256
`6ac100fc74fcc36618744a2c83d837c35fdde51d8cd1f3480c4727fe9ef25050`；相应计数为 952 / 13,990 / 90。
loc 数完全相同，既有 loc/unused-variable 噪声不能解释 terminal 差异；诊断候选不得加入 loc provider，否则会破坏单变量。

r4 冻结日志直接保存：

- `final_debug.log:2937`：`Setting idler 'Frontend' with NO init options`；
- `final_debug.log:2944`：`End loading of history`。

A2 协调器现场观察已经越过 `End loading of history`，但没有 `Setting idler 'Frontend'`；冻结的 A2 `final_*` 副本没有保留前一条
literal，因此这里只把它记录为现场进度观察，不把它提升为独立 hash-bound marker。A2 hash-bound loader gate 仍是 303 callbacks、
最后节点 `CJominiInGameMusicDatabase`、post-init 0、completion publish absent 和 `loader_terminal_missing_after_database_callbacks`。

## 外置候选 v1（已 material/ABI RED）

- 根目录：`Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z`
- 输入：r5 A `product/`，565 files / 21,607,125 bytes，tree SHA-256
  `50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f`。
- 输出：565 files / 21,591,388 bytes，tree SHA-256
  `4b6d6bca975a12708d64b68c83f08ce2a1028a9ecf8ab2cde2e474d01c54eafd`。
- 文件 diff：modified 1、added 0、removed 0；其余 564 个文件 bytes/SHA 全同。
- 唯一修改文件：`zg361_phase2_central_runtime_triggers.txt`，16,712 bytes / SHA-256
  `ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7` → 975 bytes / SHA-256
  `caa8267e979898d951f7f390046d86372ddc7b0db9459fab79a73ea1d2072485`。

两个名称与 caller ABI：

| trigger | 外部 callsites | 参数 ABI | 原 body | diagnostic body |
|---|---:|---|---|---|
| `zg361_p2c_m360_candidate_ready_trigger` | 3 | `EXPECTED_OWNER`, `EXPECTED_P2C_CASE`, `EXPECTED_P2C_CYCLE` | 15,678 bytes / `5bfe697f…c12c92` | active code 仅 `always = no`；261 bytes / `13d1a193…555a1` |
| `zg361_p2c_m360_frozen_manager_exact_trigger` | 3 | `EXPECTED_B1_CASE`, `EXPECTED_B1_CYCLE`, `EXPECTED_B1_SOURCE_HASH`, `EXPECTED_B1_SOURCE_ID`, `EXPECTED_MG_CASE`, `EXPECTED_MG_CYCLE`, `EXPECTED_MG_REVISION`, `EXPECTED_MG_SOURCE_SERIAL`, `EXPECTED_OWNER`, `EXPECTED_P2C_CASE`, `EXPECTED_P2C_CYCLE`, `EXPECTED_QUOTA` | 773 bytes / `34ef4677…76b` | active code 仅 `always = no`；453 bytes / `504d1fe9…dd7c2` |

第一版曾错误地把“六个外部 call block 逐字节不变”当作 ABI 保持；实机证明 CK3 从 provider 正文的 `$PARAM$` 推断参数集合，
注释中列出参数名不能保留 ABI。正文不含 `$PARAM$` 时，caller 仍传参反而稳定触发零参数 provider 错误。

## v1 no-launch 验收（静态门禁未覆盖 provider 参数推断）

- 物化器单测：5/5 GREEN。
- `open_kaishek`：commit `a54164625b3ebb7d738d16236ca3080686fa9984` 对应 JAR 351,165 bytes / SHA-256
  `117cf7d2a768bf81455b073778b09537569a723f58f6583be2d484669b433f32`；parser 521 files / 17,226,550 bytes /
  0 diagnostics，root parser 520 files / 0 diagnostics，均 GREEN。profile validator 保持 schema-only RED / 156,698 diagnostics，
  不冒充 CK3 语义认证。
- 中央 closure：GREEN；reachable effect/event/trigger 为 1,868 / 560 / 16；missing effect/event/trigger 均 0，duplicate providers 均 0。
- projection 反向物化：565 files / 21,591,388 bytes，tree SHA 与候选相同，GREEN。
- runner 固定到 fresh worktree `f730aeb` 的 `tools/run_zhongguo_acceptance.py`：858,769 bytes / SHA-256
  `2dd1067f7a0de9076cacc552bd2f786c00f1b04af9ef969eaa258ea2e7a747c6`。该 SHA 与 A2 `git_head=5c54014` 的仓库内容
  `git show 5c54014:tools/run_zhongguo_acceptance.py` 相同，manifest 要求 `runner_matches_a2_git_head=true`，不允许退回外层
  `Z:\ck3_mod_rewrite` 的旧 runner，也不允许自动漂移到后续 integration runner。r5 freezer 的 `attempt-manifest.inputs.formal_runner`
  所记 850,377 bytes / `5614e749…bdd38` 是候选冻结时的 preflight 输入，不是 A2 git-head 文件；此诊断以 A2 git-head 内容作为运行控制。
- `diagnostic-manifest.json` SHA-256：`6efef327c9fef69efcb85d6b76367ef07833c3f0e72cbd3620d1c5775af56996`。
- `projection.json` SHA-256：`d7535663a648537b3026504a2f5b09a2017bffac546fe39227178275ec2b4953`。
- `open-kaishek-preflight.json` SHA-256：`f8a1781a2ab1224461fd0b7267bbf3683a7061466c9d4e47c888e44d7402ff4b`。
- `artifacts-live/` 尚不存在，`ck3_started=false`、`live_claimed=false`。
- 用最终 manifest 的精确 argv 加 `--preflight` 实际调用正式 runner：参数解析、pipe 合同、CK3 1.19.0.6 / EXE SHA、桌面、
  product projection 与 seed preflight 均通过，输出 `ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN`，exit 0；没有跨过 CK3 启动边界。
  外置 `formal-runner-preflight.json` SHA-256 为 `8e89f8810a9d4eb910c55949df400b50d32fa8526b0b413bb1a209daba2f30da`。

### 两次 harness prelaunch RED

这两次都发生在 CK3 启动前，不是游戏或候选能力 RED，且都没有创建 `artifacts-live/`：

1. 初版 pipe `xar_ck3_bridge_zg361_b3h_trigger_false_081911` 不满足 runner 强制的 32 位小写十六进制 nonce，参数校验拒绝。
   旧 manifest 与失败记录保存在同级外置目录 `b3h-fecd2f2-trigger-false-20260904-081911Z-superseded-invalid-pipe-prelaunch-red/`。
   `prelaunch-red-invalid-pipe.json` SHA-256 为 `631247da15e031534451b0c4ab8cf89ff079774918e879a90db72d1548198ae1`。
2. 第一次换成合法 pipe 后，fresh worktree 尚未挂接被 Git 忽略的 `Crusader Kings III/` 参考目录，runner preflight 在查找
   `binaries/ck3.exe` 时拒绝。旧 manifest 与边界保存在
   `b3h-fecd2f2-trigger-false-20260904-081911Z-superseded-worktree-ck3-reference-preflight-red/`。随后只增加本地 junction，
   指向同一外层游戏参考树；不改变候选 product、runner bytes 或 Git 内容。
   `prelaunch-red-missing-worktree-game-reference.json` SHA-256 为 `132428d5043888c834f648ef9561fbe1297d797a83d0a489a373a4cc3000d1e5`。

物化器现在在签发 manifest 前同时验证 runner SHA 与正式 pipe 正则，避免重现上述两个 harness 错误。最终 nonce 为
`b3f15e0819114a8c9d0276e3415a6c2d`。

物化命令：

```powershell
py tools/materialize_zg361_b3_trigger_body_diagnostic.py `
  --output-root "Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\product" `
  --manifest "Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\diagnostic-manifest.json" `
  --projection-manifest "Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\projection.json" `
  --parser-report "Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\open-kaishek-preflight.json" `
  --artifacts-dir "Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\artifacts-live" `
  --bridge-pipe "\\.\pipe\xar_ck3_bridge_zg361_b3f15e0819114a8c9d0276e3415a6c2d"
```

该命令只能对不存在的输出执行一次；当前候选已经物化，禁止在同一路径重跑。

## v1 实机结果（禁止重跑）

以下历史命令已经执行；对应 artifact 必须保留，不得重跑或再当作 body 归因：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_b3f15e0819114a8c9d0276e3415a6c2d --phase2-seed-contract Z:\ck3_mod_rewrite\_worktrees\b3-trigger-closure-r5\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\product --phase2-product-projection b3-trigger-body-always-false-diagnostic-fecd2f2 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\artifacts-live --discard-userdir
```

结果为 material/provider ABI RED：duration 319.506s，303 callbacks 首次完成于约 196.479s，最后节点仍为
`CJominiInGameMusicDatabase`；`End loading of history` 已出现但 Frontend 未出现，cleanup GREEN。决定性差异是
`cell/final_game.log` 对两个 provider 各报 3 次 `Scripted trigger should have no arguments`：

- outer report SHA-256：`a24f6b6105d06333fd8ff42c81a91145c302f523822ddb000cf787d5e80db59e`；
- cell report SHA-256：`c81c07bcfe11bbc44950ce9d2d3fbf856cd4e7e2fefc85568d1dcbca5da06195`；
- evidence index SHA-256：`e6e404cb2740a713ab17a75a5beed53aebe7929ef80bf7cf4b50e451d2a6fb7a`；
- `final_game.log` SHA-256：`2e0e450b9ccbfd632ecc87ed74e339a25f393e3dfa1ec4c87110d3604b5d9c26`。

这组结果不能支持或反对“真实 trigger body 导致 terminal RED”；它只证明 v1 不是 ABI 等价候选。

## v2：ABI-consuming、恒 false 候选

- 根目录：`Z:\ck3_mod_rewrite_process_assets\zg361\b3i-fecd2f2-trigger-abi-false-20260904-084813Z`；
- 输出：565 files / 21,592,523 bytes；tree SHA-256
  `d4f061f11cacf0c47d7b1407ff5aace33a91b7578ee151f7e43d82a079977ff9`；
- diff：modified 1、added 0、removed 0，其余 564 文件逐字节相同；唯一 owner 为 2,110 bytes / SHA-256
  `b6cc81d6c3a0aef20aa49072f08cdb59e0d33a9e70884f1a4b92484430d66d56`；
- candidate body：515 bytes / SHA-256 `21473950c9e4ce5f68f9a6a6694e9494dcb068e35d73675db12031a354276356`，
  provider 正文推断 token 精确等于原 3 参数；
- exact body：1,334 bytes / SHA-256 `176867517db26dffab7042a02fbef2b314beffe06656483ecc750bc79dea195e`，
  provider 正文推断 token 精确等于原 12 参数，并保留对 candidate 的 3 参数转发；
- 两个 body 都以 `AND = { always = no ... }` 开头；后续只使用原 body 中已有的合法比较/转发来消费 ABI，不增加业务状态读取；
- caller surface 与 r5 A 逐字节相同，3 + 3 callsites 参数键集合不变；
- 旧 material RED `final_game.log` 的 SHA 和六条错误已写入 manifest；新 live 日志只要再次出现
  `Scripted trigger should have no arguments`，就必须在 terminal 归因前直接判为 material/ABI RED；
- closure/parser、projection 反向校验、runner SHA 与正式 argv `--preflight` 均 GREEN；CK3 未由物化工作包启动。

sidecar：

- `diagnostic-manifest.json` SHA-256：`26f2a6bac8b245ec6ba5cb64fbcb2bbba1b9192f18c5a5a0ab3c975081da3bbd`；
- `projection.json` SHA-256：`2f4c17be61ad69d3ddf2742557f4ab982602c3b5abdbcca57eac3f30b89227b6`；
- `open-kaishek-preflight.json` SHA-256：`cfcd12b94618143c71c96f60cbfc9058f46d292d7b332e5b2680ef7829e43ab8`。

唯一 v2 live 命令：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_927e9842f6a54496abf29588dd4b93bd --phase2-seed-contract Z:\ck3_mod_rewrite\_worktrees\b3-trigger-closure-r5\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3i-fecd2f2-trigger-abi-false-20260904-084813Z\product --phase2-product-projection b3-trigger-body-abi-consuming-false-diagnostic-fecd2f2 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3i-fecd2f2-trigger-abi-false-20260904-084813Z\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3i-fecd2f2-trigger-abi-false-20260904-084813Z\artifacts-live --discard-userdir
```

v2 只有在六条 provider 参数错误为 0 时，Frontend/terminal 结果才可进入 body 归因。无论结果如何，`always = no` 都不能合回源码，
也不能用于 Phase2 gameplay、readiness 或宣传素材。
