# B3 两个 trigger body 的一次性诊断候选

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

## 外置候选

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

定义里的参数占位符因 body 被诊断性移除而不再求值；ABI 保持指六个外部 call block 本身逐字节不变、参数键集合与 r5 完全相同。
新 body 的注释也列出 accepted caller ABI，但不含 `$PARAM$`，不会额外触发替换或求值。

## no-launch 验收

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

## 唯一 CK3 命令与判定

以下命令由 diagnostic manifest 生成，当前未执行。CK3 启动槽只能执行这一条：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_b3f15e0819114a8c9d0276e3415a6c2d --phase2-seed-contract Z:\ck3_mod_rewrite\_worktrees\b3-trigger-closure-r5\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\product --phase2-product-projection b3-trigger-body-always-false-diagnostic-fecd2f2 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\artifacts-live --discard-userdir
```

判定规则：

- 若到达 Frontend，支持“两个真实 trigger body 的联合存在与 terminal 差异相关”；仍不能判定是哪一个 trigger 或哪条表达式，下一步只能做
  单 trigger 复原的正交诊断。
- 若仍在同一 post-history/post-callback 点缺 Frontend，则这两个真实 body 不是该 terminal RED 的充分解释；停止沿 trigger-body 猜测，调查
  history→idler/completion-publish 的共同引擎/runner 边界。
- 若出现仅候选有的 parser、invalid trigger 或 unknown parameter，则候选产品 RED，本轮归因无效。

无论结果如何，`always = no` 都不能合回源码，也不能用于 Phase2 gameplay、readiness 或宣传素材。
