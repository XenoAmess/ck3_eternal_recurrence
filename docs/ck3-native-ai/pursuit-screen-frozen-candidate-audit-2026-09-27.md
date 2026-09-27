# 非零败方掩护：现有冻结战例的候选盘点

结论：**当前盘点范围内没有可直接用于非零败方掩护对拍的冻结原版战例。** 只读扫描本机 `D:/workspace/ck3_native_war_ai_promo_work/` 各 run 的 `ck3-output/interactive-requests-responses/*control.json`，共 252 份回执，其中 251 份 `battle_control_snapshot.status=available`、32 份 `phase=pursuit` 且 `winner_side` 已定。这 32 份均为 `CombatID 16777218` 的梅西纳战斗回放，败方是 defender，败方每个 levy／职业兵士／骑士 entry 的 `effective_screen_raw` 都是 **0**；既没有败方非零掩护，更没有 `screen_raw>0 && soft_casualties_raw>0` 的生效项。没有启动 CK3，也没有修改 080 collector。

[只读盘点脚本](../../ck3_autonomous_player/tools/audit_frozen_pursuit_screen_candidates.py)与[32 份逐文件哈希、CombatID、日期和阵营投影](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_pursuit_screen_frozen_inventory_v1.json)已冻结；投影 SHA-256 为 `311E1C300BBF5811D1A8414D8A56E92D6C4288EBC38A18A758710087408CBEF4`。逐组如下，每组四个 pursuit day 的 `date_raw` 均为 `53146896/53146920/53146944/53146968`，`phase_day=0/1/2/3`；它们是重复或独立回放，**不是 32 场不同战斗**。

| 冻结 run | pursuit 控制回执 | 败方非零 screen 回执 |
| --- | ---: | ---: |
| `episode01-denominator-live-attempt-023` | 4 | 0 |
| `episode01-denominator-live-attempt-024` | 4 | 0 |
| `episode01-full-edge-attempt-002` | 4 | 0 |
| `episode01-full-edge-attempt-004` | 4 | 0 |
| `episode01-native-repeatability-attempt-007` 的三条回放 | 12 | 0 |
| `episode01-terminal-loss-live-attempt-021` | 4 | 0 |

具体可核对的配对例子：attempt-004 的 `trace-d27-immutable.ck3` SHA-256 为 `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3`；同一回放第 28 日 `term-d28-control.json` SHA-256 为 `098BD65D68ED7FBE3B16A004A50D3520F49C94B6506A31FF53C78C69E98D94C8`。控制回执给出 `CombatID 16777218`、`date_raw=53146896`、`phase=pursuit`、`phase_day=0`、winner `attacker`。败方 defender 有 24 个 entry，全部 `effective_screen_raw=0`。[既有三日追击条件对拍](pursuit-screen-nonzero-branch-contract-2026-09-27.md)也只覆盖这一零掩护分支。

不能仅全文检索 `effective_screen_raw>0` 就报候选。上述**胜方** attacker 的 RegimentID `104` 与 `106` 分别有 `400,000` 与 `2,000,000` 的有效掩护，且其 soft pool 非零；它们位于胜方 entry，不能进入败方 `screen×soft` 聚合。32 份 pursuit 控制回执的胜方都至少有一个非零 screen entry，这正是原始字符串检索会产生假阳性的原因。第 27 日存档可以重放同一个 CombatID，但已存轨迹的败方 screen 为零；不能把它写作“已找到非零分支”的可用 save。

此结论仅覆盖上述本机工作目录中按标准命名保存的原生 `*control.json` 回执及已有[追击对拍投影](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_pursuit_parity_v4.json)，不声称已经普查机器上每个任意命名的历史文件或所有可能的 CK3 存档。其他暂停快照里的胜方 screen、主战期尚未定胜负的 screen，均不能替代追击期败方输入。因此目前不应凭这些旧资产启动“非零败方掩护已可对拍”的新 attempt。

后续若自然取得新候选，先冻结**同一场** `CombatID` 的追击前不可变 save、pursuit day 0 原生控制回执和下一日回执，逐项核对 save SHA、EXE/DLL SHA、`date_raw`、winner／loser side、完整 RegimentID 与 ArmyID、entry 存储顺序、`soft_casualties_raw>0` 和败方 `effective_screen_raw>0`。再依[非零分支合同](pursuit-screen-nonzero-branch-contract-2026-09-27.md)被动采 `0x23CD2E0` 输入与 `0x23CD660` 预算／写回；任何同帧身份不符的旧回执都不能当原版对拍。实机仍受 Steam 离线新鲜画面门约束。

复核本盘点只需在已确认的 Python 环境运行脚本 `--root D:/workspace/ck3_native_war_ai_promo_work --check-sidecar ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_pursuit_screen_frozen_inventory_v1.json`。该命令只读本地冻结回执，逐文件校验投影的路径、字节 SHA 和字段，不连接游戏。
