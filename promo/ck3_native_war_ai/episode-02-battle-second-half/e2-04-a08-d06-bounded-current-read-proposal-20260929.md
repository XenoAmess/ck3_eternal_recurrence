# E2-04 a08 d06：按 ID 的当前骑士数值窄读口

2026-09-29 静态复核。本文没有运行 CK3、重发已超时的 V3 请求、构建 DLL 或产生新的 d06 数值回执。a08 的 d06 存档已冻结；本次仅只读检查已经封存的原生 JSON 与当前 #451 源码。d06 名单原图有两个同名 Geoffroy（第 4 行 12 勇武、第 5 行 7 勇武）；姓名或行序不能证明 CharacterID `34333`。

## 现有窄读口可证明的部分

- a08 第二次冷载的不可变 d06 存档 SHA-256 `F05A48A0839E76DD05D053FACBA524405FD547DD0A6CA07396ADB8ABE42A0B5A`，真实保存 sidecar SHA-256 `85C226E247AF4D32E246DCCF9F4C7323106D3A6BD0F12FCB883ABE843D3B785B`。来源与媒体边界见 [d06 冷载回执](e2-04-a08-d06-coldload-media-boundary-20260929.md)。
- 同会话 `ck3-output/a08-d06-observation.json` SHA-256 `8E36F3FE8F2B51D69340940D5444A579F8453AEEFCE7107439DA1ED0E139A56D` 的 paused snapshot 为 `date_raw=53146368`、actor `29829`、War `4`、public CUnit/Army `18`、Combat `16777218`、province `2633`、wrapper revision `4`、native revision `3`、snapshot ID `native:3`。`a08-d06-cold-control.json` 的 body 是既有 `query-battle-control-snapshot-v1` 双采样；原件 66,331 B、SHA-256 `5469D9F7F066B805581038E8D9735CF51C3616823E5CAAFEF390059E73983C19`。其 `battle_control_snapshot` 自报 available、同一 d06/Combat/province、defender side 1、subject public CUnit `18`。
- 该 control 的 `defender.men_at_arms_entries[7]` 是唯一 `regiment_id=61` 行，native CArmy/public CUnit 均为 `18`、owner `29829`，读到 **战斗 entry 内存储的** `effective_damage_raw=15000000`、`effective_toughness_raw=3000000`（Q100000 即 150／30）。这是 `ck3_11906.cpp:14403–14419` 从 `CCombatRegiment` entry 字段直接加载的数值；不能将其重命名为下一帧按省份重新评估的骑士伤害／坚韧。旧 a08 DLL 的该 JSON 行没有 `knight_character_id_raw`，也没有 `34333` 的当前勇武。它不能独立证明第 5 行 7 勇武属于 CharacterID `34333`，更不能证明 612.5／122.5。
- 当前源码的 `ReadBattleControlSnapshot`（`ck3_11906.cpp:16275–16363`）已具备暂停要求、可控 CUnit、当前 combat、完整双采样与 world snapshot 前后相等门；它不需 route 或未来场景。`ReadCombatKnights`（`:8736–8893`）虽能按生成有效的 regiment/character 双向链接读 `character+0xE8` 当前有效勇武，并把 `ReadEncounterEffectiveStats` 的攻防与原生骑士效能公式交叉核对，却嵌在全 V3 的 route/scenario 查询里。`ReadEncounterEffectiveStats`（`:8477–8524`）自身只需精确 regiment、目标省份和原生 `evaluate_regiment_stats_at_province`，不需要 attacker-entry 路线。

## 最小安全移植合同

建议新增**独立、只读、单目标** private native command，例如 `query-current-battle-knight-v1`，不扩写既有 battle-control 生产 ABI，也不把 66 KB 完整 V3 及 route 预测搬进此命令。请求须显式带：`subject_public_cunit_id=18`、`character_id=34333`、`regiment_id=61`、`expected_revision=4`、`expected_native_revision=3`、`expected_snapshot_id=native:3`、`expected_date_raw=53146368`、`expected_combat_id=16777218`、`expected_province_id=2633`。这些值是 **a08 旧会话的审查基准**；未来复载需重新取得该会话自己的当前 revision/snapshot，而不能硬编码 4/3。

1. 在现有 application-main query mailbox 上执行，先取 paused snapshot 并精确比较 date、actor、revision 域及 Combat/War/Army 身份；过期、查询已执行但超时、或令牌不符时 fail closed，不自动重发。以 CUnit `18` 的当前 `ReadBattleControlSnapshot`（或等价的同源最小采样）确认 combat/side/province 和 regiment `61` **唯一**地属于 Army `18`；不要由视频姓名、历史 039→040 或 route candidate 定 ID。
2. 用 generation-valid `ResolveStoredComponent` 分别解析 CRegiment `61`、CCharacter `34333`；严格核团的 `knight_character_id`、army ID、character knight-link 回指团 ID、人物有效性和战斗 roster。读取 `character+0xE8` 的当前有效勇武；另外标注存档里的 base prowess 是另一字段，不能混用。对 CombatID、日期、对象代际任何变化都返回 typed unavailable。
3. **只用 battle-control 已证的当前 combat province `2633`** 解析省份对象，调用现有 `ReadEncounterEffectiveStats`／`evaluate_regiment_stats_at_province` 读团 `61` 当前按该省份评估的 damage/toughness。用 `get_knight_effectiveness_context`、`read_knight_effectiveness` 及已有 V3 的乘法/系数交叉检查；同时输出 battle entry 存储值 150/30，但以不同字段名隔开。省份不一致、原生 helper 失败、溢出或公式不合时整项 unavailable，绝不回退到 entry 值或历史 040 值。
4. 对目标最小采样两次，前后再读 paused world snapshot，要求两次相等且 `date_raw`、CombatID、CUnit、RegimentID、CharacterID、generation、revision 全部稳定。结果只放一个由上述 ID 锁定的目标，不排序、不按 UI 行名匹配。正式响应保留 request/response 原字节、DLL/injector/EXE SHA、source save/sidecar SHA 和 session/run ID。

离线测试至少覆盖同名不同 ID、团-人单向或双向回指不符、错代际、团不在当前 combat、重复团行、错误 province、过期 revision/date、非暂停、helper 失败、乘法溢出、前后采样变化和 entry 150/30 被误当作 freshly evaluated 攻防。正常夹具必须验证 CharacterID 与团 ID 精确绑定，且分别序列化 **current effective prowess**、**province-evaluated knight damage/toughness**、**stored combat-entry damage/toughness**。不能用合成 7／612.5／122.5 夹具冒充 a08 实机事实。

只有候选代码、负例、完整 native target 测试、精确 EXE ABI 与新 DLL/injector 字节门都通过后，才可在**新的独立 managed 冷载会话**复载上述 d06 不变存档并执行一次只读查询。该新会话与 a08 d05 推进、a08 d06 媒体会话均不同，须保留来源卡；其实际数值若不符或命令 unavailable，就保留 UNKNOWN。当前视频可使用同轨可见的「第 5 行 7 勇武」画面，但 `34333→7` 身份对应和团 61 的 `612.5／122.5` 口播仍不能升格为同帧原生证明。状态：**静态方案 READY；目标数值 RED**。
