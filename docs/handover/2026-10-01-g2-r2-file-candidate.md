# G2 R2 非战争候选：新 checkpoint 的纯文件准备

**2026-10-03 战争授权更新。** 项目所有者明确命令“取消任何的非战约束”，并要求研究战斗。原战争研究停止、nonwar-only、战争执行暂缓、战争只能交由其他维护者等现行限制全部撤销；战斗、军队、行军、围城、战争理由、宣战、防御战争、议和及相关原生 AI、只读 bridge/MCP、策略、实现和实机验收均可继续。不得仅因涉及战争再次要求授权。本文历史冻结配置的 OFF、旧尝试 RED、当时未提交动作与未实现能力保留原事实，不能继承为当前禁战规则，也不能把开放授权写成能力已经完成。继续保持罗贝尔 actor29829、episode `native-29829-2bc2d599f7f9` 的原 ordinary campaign 与自然继承线，原生 AI 研究优先、exact-build 绑定、ROOT 唯一实机/pipe/Git owner，以及最小化、无焦点、无桌面输入。当前续接身份和保存锚点以[最新接续记录](2026-10-03-g2-v33-resume.md)为准，本文较早 episode、PID 和存档仅供历史证据。

本交接记录第二次冷启动前的文件工作；实际 CK3、named pipe、桌面、Steam、进程检查和 live-run allocator 均由 root 独占。本包不执行这些操作。第一轮稳定 checkout/profile、旧 canonical seed 与 Robert 历史线均保留。

## 已完成

2026-10-01 17:00 的正式 `save-checkpoint` 返回 `saved`。从 root 的 `B/targeted-sdk/nonwar-next-checkpoint-20261001T090024Z/checkpoint-result.json` 和当前 full persisted-v2 driver 读取以下真实输入，再调用既有 [stage_nonwar_12002_pair_files.py](../../tools/stage_nonwar_12002_pair_files.py) 原样冻结到 `B/r2-file-only/checkpoint-seed`。其中 `B = Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01`。

| 输入 | 实际身份 |
| --- | --- |
| checkpoint SHA-256 / bytes | `4e14c9d64bfd6a5323c8b8c9174065a43de5c963c3488e45453498e81cebbbaa` / `67,290,734` |
| full persisted-v2 driver SHA-256 / bytes | `89bf040a2a0a8e2f8ccd736f7e652deed06f9ac472fbeda9ee5b9f17c16f8efa` / `335,584` |
| actor / episode | `29829` / `native-29829-3f80e147d033` |
| date / checkpoint history / full history count | `53169096` / `82` / `82` |
| pipe | `\\.\pipe\xar_ck3_bridge_migration_12002` |
| persisted lifecycle | `rogue_one_life`, `xar_on`, `terminal_settlement_required` |
| original lifecycle environment SHA | `158fb4a4d7db2a4673566fb1f40ba7c6bd1a64c39359379c9885b31f1462b691` |

结果为 `PASS_STATIC_FILE_PAIR`，冻结后正式 resume consumer 接受完整 driver，cold checkpoint validator 接受实际 save/history anchor。episode、pipe、command history 和 lifecycle 均没有改写；没有把旧 h74/date53169072 seed 覆盖到新现场。完整报告位于 `B/r2-file-only/checkpoint-seed/PAIR-FILES-QUALIFICATION.json`，读取记录位于 `B/r2-file-only/checkpoint-pair-inspection.json`。

新增独立配置 [ck3-1.20.0.2-g2-religion-readonly-runner.json](../../ck3_autonomous_player/configs/ck3-1.20.0.2-g2-religion-readonly-runner.json)，第一轮 40 ON 配置保持原样。第二轮要求 **41 ON / 4 OFF**，新增唯一 native build 输入 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1` 与唯一 MCP query permit `--private-player-religion-context-query`。原有八项非战争 query 继续启用，typed action 和 autonomous lifetime consumer permit 均保持 OFF；该 R2 冻结配置的 war cash、prewar、planner diagnostic 与旧 council probe 为 OFF；这是旧候选的实际输入，2026-10-03 非战限制撤销后不约束新的战争候选，不能倒填旧 receipt 为已启用。

既有 [prepare_g2_12002_candidate_files.py](../../tools/prepare_g2_12002_candidate_files.py) 按配置列表验证 flag，本来就能接受 41 项，无需新参数或 flag 数量门禁。本次只让 supervision plan 的宗教接线状态从实际 readonly query permit 派生，并补充独立的 `war_private_permits_added=false` 字段，避免 R2 plan 仍误报“宗教未接线”。准备工具五项测试全部通过，其中新增用真实 MCP parser 读取 41-flag R2 plan，证明新增宗教查询开关为真而现有 typed action 开关仍为假。

## 下一实际文件阶段

由 root 提交本包及 R2 所需源文件，固定新 runtime checkout `L2` 和中央 `B/religion-integration/integration-build-manifest.json` 的最终 SHA 后，在 **L2 中的** prepare 工具运行纯文件准备。其 argv 结构如下；`L2`、最终 manifest SHA 和新 state 由 root 指定后才记录为实际 argv，当前不冒充已执行。

```text
<python> -B <L2>/tools/prepare_g2_12002_candidate_files.py
  --config <L2>/ck3_autonomous_player/configs/ck3-1.20.0.2-g2-religion-readonly-runner.json
  --integration-manifest <B>/religion-integration/integration-build-manifest.json
  --integration-manifest-sha256 <FINAL_SHA256>
  --python <python>
  --game-dir Z:/SteamLibrary/steamapps/common/Crusader Kings III
  --state-dir <new-R2-state>
  --canonical-seed-root <B>/r2-file-only/checkpoint-seed
  --output-dir <new-R2-output>
  --live-run-state-root Z:/ck3_mod_rewrite_process_assets/live-run-state
  --prepare-profile-files
```

显式 mode 仅调用现有 fresh-profile 文件核心，再原样复制新 save/full driver。输出 `NEXT-LIVE-PHASES.json`、`MCP-READONLY-NEXT-PLAN.json`、`PAUSED-MCP-SUPERVISION-PLAN.json` 与 file-pair receipt。preflight、allocator、cold session 都只写 argv，由 root 随后执行。ordinary lane 仍只生成 plan，没有 ordinary rebind 或新 ordinary 实机结论。

## 已定位的必要 runtime 依赖

新 h82 driver 已包含 R1 的非 legacy lifecycle environment SHA；R2 runtime/profile 发生实际变化后将生成新 environment SHA。当前 [one_generation_preflight.py](../../ck3_autonomous_player/src/xar_autoplayer/one_generation_preflight.py) 的 driver/checkpoint lifecycle 比较（143–175 行）要求整份 binding 相等，只额外接受旧 legacy rogue binding。因此原样保留这份实际 h82 pair 后，新 profile 的正式 preflight 会在该生产分支拒绝跨 profile 恢复。

该入口和真实输入已交给 root/runtime owner。应通过现有生产恢复路径确定性复现，再实施跨 profile rogue checkpoint 恢复所需的最小修正；本文件准备包不修改 driver、不把其环境 digest 手写替换成新 digest，也不改共享 native runtime。原始保存的 lifecycle、三份 checkpoint/history 一致性与新运行环境必须分别由真实恢复流程承担。

本包 readiness 为 `static-ready` 文件与命令准备。第二轮正式 zero-process preflight、new PID cold restore、religion paused query 和新的实际 outcome 尚未执行。独立 legacy rogue 线的这份新 checkpoint 不增加 Robert durable days，也不改变 G2 **3/8**。
