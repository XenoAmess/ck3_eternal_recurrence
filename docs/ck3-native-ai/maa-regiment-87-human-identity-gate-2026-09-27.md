# 职业兵团 87：冻结输入的人类名称映射门禁

本次只读检查第 11／21 日已经冻结的原生 v3 输入，未启动 CK3。结果是 **兵种类型缺失，名称映射停止**；不能把 class index、有效伤害或坚韧倒推成某一个玩家可见兵种，也不能据此枚举“该兵种”的具体坚韧 modifier 并宣称解释了 [125,000 的旧缓存差额](maa-regiment-87-refresh-source-boundary-2026-09-27.md)。

| 冻结回执 | SHA-256 | `base_inputs.armies[0].regiments[0]` 身份 |
| --- | --- | --- |
| 外置 `episode01-daily-stats-live-attempt-028/ck3-output/interactive-requests-responses/d11-direct-stats-v3.json` | `50F1FE7946F846E237AAC2003B98BF540363C133AA8EE93AB69F388E2472E2BE` | RegimentID `87`；`kind=men_at_arms`；`maa_type={status:absent,key:null}` |
| 外置 `episode01-daily-stats-live-attempt-029/ck3-output/interactive-requests-responses/d21-direct-stats-v3.json` | `A8B257EE743B593DBE145ED2D6E152DC7791C092EB0B6C95BE8943B1C23AE1E1` | 同上 |

两份回执均将该兵团列在 ArmyID `16777221`，`encounter_role=attacker`、`scope_role=active_war_enemy`、WarID `4`；army owner 与 commander 的 CharacterID 均为 `31549`。目标 `body.target_province_id` 与该团 `effective_stats.source_target_province_id` 都是 `2633`；`base_inputs.target_province.province_id=2633`，terrain key 为 `forest`。这些是**机器身份**，不是已冻结的玩家可见人物名、省份名或兵种名。`counter.class_index=0` 只是数值类别，不能唯一确定 `maa_type`。两日有效属性均为 Q100000 伤害 `4,500,000`、坚韧 `2,625,000`，受上下文修正影响，也不能倒推 type。

[v3/v2 同帧对照](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_paused_v3_stat_base_parity_v1.json)已将两日 `v3.base_inputs` 与 v2 全对象精确对齐；v2 原始回执 SHA-256 分别为 `A91BD7A7119799109D042CFFEC58F9A3595EEE5ED7B75FB8C3322E724B107820` 和 `B6433227E4C625C377A8019A53B18B1C587C2925E6653F25B7AB9A50E3408406`。因此回退 v2 不能填补此字段。本包按“冻结输入缺类型即停止”的门禁，没有继续检索原版脚本/本地化、没有生成视频展示名称或智能体日志别名；目标省份的玩家可见名称也未在这两份 v3 回执内给出。

后续要继续名称映射，须先在同一来源存档或等价冻结证据中取得 RegimentID `87 →` 原生 `CMenAtArmsType` key 的只读、全 generation 身份绑定，并取得 `ProvinceID 2633 →` 可见地名的可复核本地化链。随后才能按已绑定 type/target 列出原版 modifier **候选入口**；仍须同帧采其实际值和中间聚合，才能判断 `+5%` 旧缓存差额的来源。
