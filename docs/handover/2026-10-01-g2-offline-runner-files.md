# 2026-10-01 新 G2 candidate 的纯文件 runner 准备

本包接续 [非战争 runner 交付](2026-10-01-nonwar-12002-offline-runner.md)，仅准备新一轮非战争 G2 集成候选。旧 `da05c04b…` profile 与 `nw12002/g2of` 冻结证据保持原样；新版 Council、faction/gift、Sway、law、Feast、government、family obligation、prisoner 的 source/binary 输入变化，使用独立新 profile 和 receipt，不能倒填成旧候选已经验收。用户随后暂缓战争研究，本轮 war cash、prewar 两项保持 OFF，不把它们记成候选已启用。

## 新候选实际消费入口

[prepare_g2_12002_candidate_files.py](../../tools/prepare_g2_12002_candidate_files.py) 消费中央最终 `integration-build-manifest.json`，schema 为 `xar.g2.offline.central-native-build.v1`。使用 `source_head` 与 `build.selected_private` / `build.shipping` 的 DLL、injector SHA/size 和 `flags`；只验证本次新实体的冻结输入，不重验旧 profile 或旧 DLL。配置 [ck3-1.20.0.2-g2-offline-runner.json](../../ck3_autonomous_player/configs/ck3-1.20.0.2-g2-offline-runner.json) 记录 **40 项 private native ON**（包含新增 law enact native 包装器），planner diag、war cash、prewar、legacy council probe 四项为 OFF，shipping 对应项全部 OFF。Council APPLICATION_MAIN / ASSIGN / FINAL_GATE 保持 ON；full candidate reader 使用已迁移 runtime slot 41，不启用没有 1.20 callback 的旧 slot 33 probe。

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

源码输入与中央新 binary freeze 尚未提供时，不执行真实 candidate prepare。最终冻结后立即在后台创建全新 `Z:/ck3_mod_rewrite_process_assets/g2-12002-canonical-independent-20261001/state`，输出至 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/runner-files`。真实执行与 SHA 将追加于本节，原旧 receipt 保留。

后续最小实机工作为：official exact zero-process preflight、新 PID cold restore/readiness、新域代表性 paused queries、必要 action 的独立 receipt/下一 turn/checkpoint。**只有 root 操作游戏**；本轮 `NEXT-LIVE-PHASES.json` 只计划 run ID allocation 和 `native-session --cold-start-checkpoint` 受管监督，不执行带自动策略循环的 rogue lifetime/native-auto-run。原始 lifetime argv 仍只存在于通用 runner 计划，不能作为本轮默认下一步。普通 G2 另以合法普通 seed 和 durable lineage 记账。

`PAUSED-MCP-SUPERVISION-PLAN.json` 保存真实 CLI 的 session argv 与观察顺序。`native-session` 没有 `--start-paused` 参数，也不自行选择 gameplay action；监督启动后由 root 使用 MCP `ck3_take_snapshot` 验证实际 paused/readiness。若正在运行，可按当前 revision 显式 `ck3_execute_step(step="pause-map")`，然后重新 snapshot 验证；暂停 ACK 不替代状态。随后只读八个非战域，并对确有必要的动作显式选择 typed action。命令没有在后台执行。

`open_kaishek` 为 not-applicable：本包是 manifest/argv/filesystem composition，无 CK3 script、IR 或 replay 语义。**用户已授权宗教研究，并停止战争研究**；本轮 candidate 没有宗教查询，原因是尚未接线，不能据此继续声称宗教域被用户暂缓或已经完成。
