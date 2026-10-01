# 2026-10-01 新 G2 candidate 的纯文件 runner 准备

本包接续 [非战争 runner 交付](2026-10-01-nonwar-12002-offline-runner.md)，新一轮非战争 G2 candidate 已于 **16:13（Asia/Shanghai）实际完成纯文件 profile/pair 准备，状态 static-ready**，所有运行计划绑定稳定 `g2live` checkout。旧 `da05c04b…` profile 与 `nw12002/g2of` 冻结证据保持原样；新版 Council、faction/gift、Sway、law、Feast、government、family obligation、prisoner 的 source/binary 输入变化，使用独立新 profile 和 receipt，不能倒填成旧候选已经验收。用户随后暂缓战争研究，本轮 war cash、prewar 两项保持 OFF，不把它们记成候选已启用。

## 新候选实际消费入口

[prepare_g2_12002_candidate_files.py](../../tools/prepare_g2_12002_candidate_files.py) 消费中央最终 `integration-build-manifest.json`，schema 为 `xar.g2.offline.central-native-build.v1`。使用 `source_head` 与 `build.selected_private` / `build.shipping` 的 DLL、injector SHA/size 和 `flags`；只验证本次新实体的冻结输入，不重验旧 profile 或旧 DLL。配置 [ck3-1.20.0.2-g2-offline-runner.json](../../ck3_autonomous_player/configs/ck3-1.20.0.2-g2-offline-runner.json) 记录 **40 项 private native ON**（包含新增 law enact native 包装器），planner diag、war cash、prewar、legacy council probe 四项为 OFF，shipping 对应项全部 OFF。Council APPLICATION_MAIN / ASSIGN / FINAL_GATE 保持 ON；full candidate reader 使用已迁移 runtime slot 41，不启用没有 1.20 callback 的旧 slot 33 probe。

中央最终 metadata freeze 将 `source_head/final_source_head` 绑定最终已提交来源，另以 `build_source_head` 记录编译时 commit；真实 target SOURCES/pins 与 DLL/injector 保持已编译值。新 profile 消费最终 source，receipt 同时记录两种 commit，不把 metadata freeze 称为重复编译或新实机结果。

正式 Python consumer trialflags 保持 OFF。native 编译 ON 仅证明该构建包含候选入口，不能自动获得 provider 的 paused 资格、typed action 资格或普通长期 G2 credit。原 runner 与 pair staging 没有改动；新消费器复用它们已经闭合的纯文件核心。`MCP-READONLY-NEXT-PLAN.json` 另外消费当前真实 MCP stdio 的 Council、faction/gift、Sway、law、government、prisoner、Feast、family obligations 八项 query permit，生成开启这些新增只读查询口的 server argv；没有调用 server，Feast Start action 不因此开启。Council query 覆盖 composition/final gates；gift query 以 campaign root/expected revision 读取 native gift candidate。独立 Council、gift、crown law、Sway 的 typed action 开关均未加入只读计划。这些参数只属于 `mcp_server.py`，不能塞入尚无对应接线的 lifetime/native-auto-run。family obligations 仅含 native child-house preview 与 break terms，参数来自后续实际 paused frame 的 revision/subject/candidate，可显式指定 break recipient；不启用战争或 ally 专用查询。

默认只写 metadata/argv。显式 `--prepare-profile-files` 按顺序运行已有 `environment._prepare_profile_locked` + isolated lock + `verify_profile`，再通过现有 `stage_nonwar_12002_pair_files` 把 Z 盘 canonical pair 原样复制进全新 profile。没有调用包含 CK3 inventory 的 public prepare、official prepare/rebind/preflight，没有连接 pipe、桌面、Steam 或 live allocator。

可重复用于下一份真正新候选的命令为：

```text
python -B -X utf8 tools/prepare_g2_12002_candidate_files.py --integration-manifest <final-manifest> --integration-manifest-sha256 <frozen-SHA> --game-dir <game-root> --state-dir <fresh-Z-state> --canonical-seed-root <Z-frozen-canonical-pair> --output-dir <new-Z-receipt-directory> --live-run-state-root <local-allocator-root> --prepare-profile-files
```

所有路径由调用者明确提供；默认解释器是当前 Python，也可显式 `--python <python.exe>`。`--ordinary-sample-dir` 只生成普通 lane 的未来参数；省略时记录 `requires-qualified-ordinary-sample` 这一尚未提供的输入位置，不制造普通 pair。普通 state 参数单独指向 `ordinary-plan-only-state`，不会将普通 prepare 指向此次 rogue profile。

## Canonical pair 与计数边界

只复用已有冻结根：`Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/nonwar-offline-2026-10-01/canonical-seed-files`。不得读写原 P/current userdir、Robert、真实 Documents、D 盘历史资产。该 pair 的实际 source 资格与 staging fixture 已在上轮完成，不重复旧 fixture；新 profile 中的 byte pairing 属于本次新实体施工。

| 绑定 | 已冻结值 |
| --- | --- |
| CK3 / EXE SHA | `1.20.0.2` / `ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d` |
| save SHA / bytes | `15fec60d3ec284161f135b095402181be9f64de966c002e1282e9bd2e5827825` / `67,083,928` |
| full persisted-v2 driver SHA / bytes | `7eba0a48b78c06d6ee31bef47ecaf7f8408bc24702bf88a5966dd1ab94dbbaa7` / `536,722` |
| actor / episode | `29829` / `native-29829-3f80e147d033` |
| raw date / history | `53169072` / `74` |
| pipe | `\\.\pipe\xar_ck3_bridge_migration_12002` |

保留全部 pipe、episode 与完整 history，不改写 save/driver，不派生普通 lifecycle。该 legacy rogue pair 是独立新 1.20 seed，Robert 仍 **3,153/36,524**、G2 仍 **3/8**，两者增量零；它没有 Robert/Guy/首继承人/prisoner ledger 或 tutorial 延续资格。raw save 检查保留 header-only + canonical 全文件 SHA/size 的真实边界。

## 验证与交付状态

新增 [test_prepare_g2_12002_candidate_files.py](../../tools/test_prepare_g2_12002_candidate_files.py) 验证新 manifest/binary 输入消费、默认不 prepare、显式 mode 的 file core → pair 顺序、不同普通 state、后续跳过已完成 prepare，以及 query argv 直接通过真实 MCP CLI parser。使用明确 fake bundle/metadata 和 mocked profile/pair，全部临时文件在 Z；不重复已完成的生产 pair fixture，不冒充真实 profile 结果。

当前新消费器前三项测试 **3/3 PASS**：`python -B -X utf8 tools/test_prepare_g2_12002_candidate_files.py`。后来追加 gift query 时仅重跑实际受影响的 MCP parser 用例，**1/1 PASS**，其余两项直接复用。新增 supervised cold session 的真实 CLI 用例也单独 **1/1 PASS**，没有重新运行未变的旧用例。既有 runner、profile core、pair copier 的上轮测试与真实 receipt 直接引用，没有重复执行。

源码与 binary freeze 到达后，已经实际从 `Z:/ck3_mod_rewrite/.task-tmp/g2live/tools/prepare_g2_12002_candidate_files.py` 完成显式纯文件准备。施工 `g2src` 可以继续并行修改，**本次 profile、session、MCP、allocator 脚本全部指向稳定 `g2live`**，避免运行期间 Python 源码变化导致已有 `agent_runtime_fingerprint` 不匹配。没有修改稳定 checkout。实际 artifact 见下节，原旧 receipt 保留。

后续最小实机工作为：official exact zero-process preflight、新 PID cold restore/readiness、新域代表性 paused queries、必要 action 的独立 receipt/下一 turn/checkpoint。**只有 root 操作游戏**；本轮 `NEXT-LIVE-PHASES.json` 只计划 run ID allocation 和 `native-session --cold-start-checkpoint` 受管监督，不执行带自动策略循环的 rogue lifetime/native-auto-run。原始 lifetime argv 仍只存在于通用 runner 计划，不能作为本轮默认下一步。普通 G2 另以合法普通 seed 和 durable lineage 记账。

`PAUSED-MCP-SUPERVISION-PLAN.json` 保存真实 CLI 的 session argv 与观察顺序。`native-session` 没有 `--start-paused` 参数，也不自行选择 gameplay action；监督启动后由 root 使用 MCP `ck3_take_snapshot` 验证实际 paused/readiness。若正在运行，可按当前 revision 显式 `ck3_execute_step(step="pause-map")`，然后重新 snapshot 验证；暂停 ACK 不替代状态。随后只读八个非战域，并对确有必要的动作显式选择 typed action。命令没有在后台执行。

`open_kaishek` 为 not-applicable：本包是 manifest/argv/filesystem composition，无 CK3 script、IR 或 replay 语义。**用户已授权宗教研究，并停止战争研究**；本轮 candidate 没有宗教查询，原因是尚未接线，不能据此继续声称宗教域被用户暂缓或已经完成。

## 最终实际 profile/pair receipt（16:13）

本节以 `B = Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01` 为 artifact 根。真实运行耗时 **8.1 秒**，完整 receipt 为 **`B/runner-files/FINAL-G2-FILE-PROFILE-PAIR-RECEIPT.json`**，SHA-256 **`4c5b7a5781e9f75c0a0804cabbbe19cfc7f46d597c52b4767105a47ef3e86e29`**，时间 `2026-10-01T08:13:31.075767+00:00`，结果 **`PASS_STATIC_PROFILE_AND_FILE_PAIR` / `static-ready`**。

- 稳定 source：`Z:/ck3_mod_rewrite/.task-tmp/g2live`，最终 commit **`7c0e373e8b24b71fc060e2ce5cacc7ab57275b0a`**。
- Native 编译 commit：`e1d98757c2dd4a41c6f1ff5ff2072c10c53c744a`；中央 `source_freeze.status=finalized`，最终 metadata source_head 为上述 `7c0e373…`，实际 target SOURCES/pins 保持原编译值。
- 最终 `B/integration-build-manifest.json` SHA-256：**`8bd7d0b003821cb14425fa2e489a45448b6f889a7978c68bfb884d3042e90436`**，candidate **40 ON/4 OFF**。

| 真实 binary | SHA-256 | bytes |
| --- | --- | --- |
| `B/build-candidate/xar_ck3_bridge.dll` | `c9cb38e9e53ba9566465fa2e2bd0ebeb25009a748b7e8e56f64fefc3652a56b8` | `6,638,080` |
| `B/build-candidate/xar_ck3_bridge_injector.exe` | `10568e02023cfacd54b2bab86940098b33cf99914215f67f01a49c5fa9478bf5` | `39,936` |
| `B/build-default/xar_ck3_bridge.dll` | `5b42e2784e98832f04f6ee10ec7e2f46ea1587e3baf92d5b67cc9edbdd4a15aa` | `4,211,200` |
| `B/build-default/xar_ck3_bridge_injector.exe` | `0c9e1f69b9b3634871b31380d24b4a77b072cf7d844b4281af19833e985cf44e` | `39,936` |

实际新 state 为 **`Z:/ck3_mod_rewrite_process_assets/g2-12002-canonical-independent-20261001/state`**，其中 `profile` 是新 production projection，共 **86 文件**。现有 profile core 与 `verify_profile` 均通过，实际 EXE SHA 仍为上表 `AE1BA6…81B2D`。

| 实际环境/配对记录 | SHA-256 |
| --- | --- |
| environment contract | `158fb4a4d7db2a4673566fb1f40ba7c6bd1a64c39359379c9885b31f1462b691` |
| agent runtime | `eae48975a499e7ecee60d7468e6f34b5c28938083dcf84f667e0638e06961734` |
| production tree | `2c000fa0f6d30aa3c9dd58f4471aace2c408d73a0e8c7bed6509dbbe17d5cda2` |
| `state/profile/xar-autoplayer-environment.json` | `ad4acfb66f976cd05de75ac7a0d05814d3b1a6f9e0f078ca4338b18b3a43f95f` |
| `state/PAIR-FILES-QUALIFICATION.json` | `29d204666118ff2e2f7a424b26990bef3bfb9255fbc9febec43f02acdd5ed353` |
| `state/SEED-IDENTITY.json` | `0e4d144fc71ae446d293bfb7c75a078a8e515cd16199ac8a7760027e3fe4b196` |

新 profile 内的真实 save/full driver 仍逐字节匹配前文 canonical pins，actor **29829**、raw date **53169072**、history **74**、episode 与 pipe 完整保留。`persisted_lifecycle=null` 没有回写成新声明；正常 consumer 仍接受现有 `legacy-driver-default/rogue_one_life`。本次没有普通 rebind、Robert 延续或 G2 增量。

| 真实可交 root 的计划 | SHA-256 | 当前用途 |
| --- | --- | --- |
| `B/runner-files/NEXT-LIVE-PHASES.json` | `452d073aeef80d49b759cb0ae24554357e37fa654fe4d3a1679f40224f198e3a` | exact preflight → supervised run ID allocator → `native-session --cold-start-checkpoint --xar-enabled xar_on --timeout 3600`，不含 autonomous lifetime/next |
| `B/runner-files/MCP-READONLY-NEXT-PLAN.json` | `e2be67376bca198555bd1f19b7a68ca176311db76c20305c9634eadd91551c0c` | 实际存在的八项非战 query permit 与完整 stdio argv，root 可传给 SDK sampler |
| `B/runner-files/PAUSED-MCP-SUPERVISION-PLAN.json` | `f06da3819b220be82fa139246dfa337c9466dd573a5a06d1e934cfbd904a6738` | root-only supervisor/session argv、snapshot/pause 后置与非战观察顺序 |

默认只读采样器与 root 后续显式 SDK 执行入口见 [paused readonly SDK sampler](../ck3-native-ai/ck3-1.20.0.2-paused-readonly-sdk-sampler.md)。本包没有调用采样器、server、preflight、allocator、session、injector、CK3 inventory、pipe、桌面或 Steam；原 P、current userdir、Robert、旧 profile 和 frozen seed 均未写入。**正式零进程 preflight、新 PID cold restore/readiness、真实 paused 查询与必要 action 后置全部尚未完成**，这就是本包剩余的实机边界。
