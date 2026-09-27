# WAR31 战后头衔与资源的只读存档投影（2026-09-27）

[R0221 WAR31 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json)要求在投降动作前后确认目标头衔 **2128**、人物关系、停战及双方资源。既有 [rich snapshot 离线投影](war31-postcondition-offline-projector-2026-09-27.md)只提供战争状态和玩家金币、威望。不能从这些字段推出虔诚、对手资源、title holder 或持久停战。

新增 [只读存档投影器](../../ck3_autonomous_player/tools/project_war31_save_material.py)作为独立证据面。它逐字节验证战前来源是 R0197 冻结 checkpoint（SHA-256 `1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A`）、CK3 1.19.0.6 EXE、Rakaly 0.8.19 EXE，并对战前/战后的每份原始存档重新运行 Rakaly，复算对应解码文本的 SHA-256。随后按 `landed_titles.landed_titles[2128]`、`living[29829|30097]` 与 `relations.active_relations` 中唯一的 `(first, second)=(29829,30097)` 人物对逐行读取；同名 ID 在其他 save section 不会混进结果。报告使用独占新建的 `--output`，拒绝覆盖旧 attempt。

```text
<verified-python> ck3_autonomous_player/tools/project_war31_save_material.py --before-save <R0197原始checkpoint.ck3> --before-melted <R0197-rakaly-melted.ck3> --after-save <投降后独立保存.ck3> --after-melted <投降后-rakaly-melted.ck3> --rakaly-exe <rakaly-0.8.19.exe> --exe <ck3-1.19.0.6.exe> --output <新报告.json>
```

制作两份 melted 文件时，使用已核 SHA 的 Rakaly 0.8.19 CLI：`rakaly.exe melt <原始存档.ck3> --format ck3 -o <新melted.ck3>`。不要复用另一个 checkpoint 的 melted 文本；投影器会重新解码并做字节哈希核对。它只读游戏和来源存档，不启动 CK3，也不执行投降。

| 可观察域 | 报告字段 | 语义边界 |
| --- | --- | --- |
| 目标头衔 | `target_title.holder_character_id`、`key`、holder `first_name` | 来自同一份真实存档中 ID 2128 的 `holder`；不是结算预览。 |
| 头衔层级 | `de_facto_liege_title_id`、对应 title 的 holder、`direct_de_facto_child_titles` | 保存的是**头衔层级边**；不能把这些边自动等同人物的直属领主/全部封臣。 |
| 双方资源 | 人物 29829/30097 的 `gold.value`、`piety.currency`、`prestige.currency`，定点 `scale=100000` | 负值与零保留；前后 `signed_delta_raw=after-before`。若资源字段缺失或精度超出五位，小工具拒绝，绝不填零。 |
| 人物关系 | `holder_personal_liege`、`holder_personal_vassals` | 仍为 `unavailable`。头衔链可作研究线索，不能替代独立人物关系原生读数。 |
| 持久停战 | `persisted_truce.raw_slots.truce_0/1`、`date`、`result`、同人物对 `war` | 读取存档中的**原始槽位**和到期日期；`truce_0/1` 各自对应哪一方的方向尚未由引擎读回证明，报告固定 `slot_direction=unverified`。精确人物对缺失与已存在人物对但无 truce 槽位分开表示。 |

`save_date` 和来源 SHA 让两份保存可比较，但**不构成**与即时 native `snapshot_id`、revision、episode 的同帧绑定；报告显式保留 `same_native_frame_binding=false`。受管执行者应保留实际动作/保存顺序回执、CK3 原生战前后快照及下一回合与恢复后快照，独立核对头衔、资源和行动是否匹配。即便同一人物对战后出现新 truce 槽位，也须结合投降动作回执、保存顺序和原生读数才能归因；槽位方向和人物直属关系仍保留缺口。

对原生候选的复核：`ck3_11906.cpp` 的 `ReadCharacterExitResources` 确有双方 gold/prestige/piety 的定点读数，但现有 `query-war-termination-exit-terms` 合同限 `claim_cb` 且玩家为进攻方，不能直接用于 WAR31 的防守方 de jure conquest；`campaign_root_context` 只覆盖玩家上下文，Raiktor 的实际停战 expiry 查询也绑定另一场特定战争。此处选择存档读法，避免把未验证的 DLL 读取偏移和另一场战争的私有入口扩大为生产通用查询。

离线验证：`py ck3_autonomous_player/tests/unit/test_project_war31_save_material.py` 为八个纯合成夹具 GREEN，包括人物对作用域、无 truce 槽位和重复人物对拒绝；还用已有 Episode01 两份真实 Rakaly 解码文本 `trace-d05-melted.ck3` 与 `trace-d21-melted.ck3` 单独运行 `project_melted`，分别解析 `c_foggia` title 2128 holder **33435**、上级 title 2141 holder **29829**，并读取 Robert 29829 与 Landolf 30097 的三项定点资源。这两份 Episode01 文本不是 R0197/R0221 WAR31 动作证据，不能证明本次投降后任何变化。

对精确 R0197 原件本机重解码后的战前只读回读见外置 `D:/ck3-research-artifacts/war31-live-20260927/attempt-02/R0197-before-relation-material.json`：文本 SHA-256 `FC39B744D666C649C4E54B1198F7C7C5B39847B8AB8E98BC97F16919D9603C79`；唯一人物对 `first=29829, second=30097` 位于原文本第 5859748–5859752 行，含 `war=16777231`，`raw_slots={}`。这证明战前该人物对的**关系块内**没有持久 truce 槽位；实际投降后的槽位、到期日和方向仍待实机差分。
