# 现役骑士与动态 entry 的续算输入门槛（CK3 1.19.0.6）

本文是[现有静态边界](active-battle-knight-entry-transitions-2026-09-27.md)面向游玩智能体的收口，不改动既有结论。它把“此帧读到的数值”与“下一原生日更会采用的数值”分开；静态指令证据不被写作新实机样本，也不把一次死亡或两次增援外推成所有战斗。

## 可复核的原版顺序

只读提取器 [`extract_active_knight_entry_transitions.py`](../../ck3_autonomous_player/native_bridge/research/extract_active_knight_entry_transitions.py) 对 exact-build `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 同时检查文件哈希、指令地址和操作数，冻结输出为 [`active_knight_entry_static_anchors_11906.json`](../../ck3_autonomous_player/native_bridge/research/fixtures/active_knight_entry_static_anchors_11906.json)，SHA-256 `DC802DFA29F2A7740968628E9309355C0BBF7DF99BB51E29C948925A84751F9F`。提取器可用相同 EXE 的 `--verify --expected <冻结 JSON>` 只读重跑；hash 或任一指令不符即失败。它不调用游戏函数、不启动游戏。

| 顺序/身份 | exact-build 锚点 | 对续算输入的含义 |
| --- | --- | --- |
| 日更刷新在排程前 | manager `0x27FB57A` 调 `0x2308D50`，后在 `0x27FB58F` 调 side0 `0x23C8750`；`0x2308D66/72` 两侧 modifier，`0x2308D82/95` 两侧 entry | 暂停帧的 effective damage/toughness 只是当帧缓存；下一原生日更可以先覆盖，再进入事件/出伤。 |
| 两类 entry 均重算 | `0x23CC2E8` levy、`0x23CC316` MAA-like 均调 `0x23D2CE0`；其 `0x23D2D2F` 调 `0x239CAE0`，随后 `0x23D2D46/4E` 写 entry `+0x40/+0x48` | 只刷新骑士名单、却让其他兵团沿用旧有效属性，也不忠于这条原版路径。来源修正仍要逐项证明，不能用当前差值猜原因。 |
| 排程不是固定人物快照 | `0x23C87AD` 清 schedule count；`0x23C87B7` 读 MAA entry；`0x23C8843` 读 `CRegiment+0x148`；`0x23C88A6/AA` 以当前角色 ID 与 day index 做取模门；`0x23C893D/40` 将 **RegimentID** 写入排程 row | 身份应至少同时保留 full RegimentID、当刻 CharacterID、row 顺序/载入事件索引；不能用按人物去重的骑士表替代排程。 |
| 火点再次取现态 | `0x23C99A5/F6` 从排程 row 重解 RegimentID，`0x23C9A62` 核所属 Army 仍在本 Combat，`0x23C9A6E` 再读 `CRegiment+0x148` | 安排时的 CharacterID 与火点时的 CharacterID 必须分列；火点前死亡、detach 或 army 离场均可能使旧 row 失效。 |
| 下一日将领先重选 | `0x27FB683`、`0x27FB6A2` 分别调 side0/side1 `0x23C8A60`，随后 `0x27FB6FD` 进入主战 tick | 当前 selected commander 可作本帧说明，不能在伤亡/增援/撤军后无条件当下一日选中人。精确多候选 ranking/tiebreak 仍未闭合。 |

以上锚点证明的是同一函数/manager 局部控制流和读写位置。不同 combat manager 的全局顺序、所有受伤效果写集、未来入场/离场路线与刷新值均未由静态指令单独证明。

## 与实机同身份数据交叉核对

已有第 11 日[排程前属性回执](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_daily_stat_refresh_day11_v1.json)（SHA-256 `E36224201492080046FE37E6C27653B6F38D8C7B97651BBEC86EC718A8A3AB06`）在同一 CombatID `16777218` 的 27+24 个 entry 中记录 32 个 effective damage 或 toughness 变化。side0 的 RegimentID `220` 是直观反例：damage Q100000 `20,000,000→18,500,000`，toughness `4,000,000→3,700,000`；它否定“暂停有效属性照搬至下一排程/火点”的恒等假设，不能证明这次变化由哪一个修正单独造成。

[第 11/21 日跨日回执](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_cross_day_stat_stability_v1.json)（SHA-256 `38486D71F2466775C6D7EE4D96536046BFC97ECB17EFCE49F186FA8F15BB8DFF`）中 51 个共同 RegimentID 里有 24 个骑士，2 个骑士有效属性改变，且伴随有效勇武改变；中间每日值未观察，不应把这个第 11→21 日对照命名为一步转移。[自然增援两案](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_join_schedule_boundary_v1.json)（SHA-256 `CBB7956D8D3B1F466F3D09FD8C79F8ECD960A7C0FC8954703921747FD59D4DFB`）在抵达日 side0 首次火点前分别将 entry 数 27→40、39→44；[第 26 日骑士击杀回执](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_knight_kill_writeback.json)（SHA-256 `752D2257D358159FCA918885A9B16B6909D81FEC835F0FA9205868CE882876CA`）记录角色 `33437` 从 RegimentID `65` detach、死亡存档 attribution。这些是不同回放/日期，不能拼成一条完整随机轨迹。

## 给智能体的分级入口

| 用途 | 允许读取 | 必须显式处理 | 不得声称 |
| --- | --- | --- | --- |
| 当前暂停帧战况和即时风险比较 | 同一 generation/revision 的 CombatID、side、两 bucket 有序 full RegimentID、current/soft/effective stats、当前 commander/phase/roll/width | 将当帧数值标记为 `observed_at_revision`，说明下一日 refresh/entry/event 是模型风险；每次新帧重新读并重算 | 当帧属性就是下一日真实属性，或已有原版整场胜率 |
| 条件性下一日场景演算 | 以上输入，加 **明确假设**的 refresh 后属性、将领重选、排程/火点身份、join/leave 分支及阶段结果；若实际边界读口可用则优先采它 | 输出区间或情景及缺域，战术动作继续使用既有可用近似决策并在后续帧纠偏 | 情景条件被原版确定选择，或单一百分比已原生校准 |
| 原生逐日校准与整场概率 | 同一 CombatID/原始线程的 pre-schedule 刷新与两侧 entry、原调用将领、事件安排/火点、join/leave、伤亡写回、下一暂停帧的逐日闭环及分支频率 | 字段丢失、generation 变化或跨 revision 时整组 native parity `unavailable`；保留近似策略并标注不确定性 | 用单次死亡、两次增援或静态 RVA 补出所有未来分支概率 |

因此现有近似计算仍可作为**有条件的行动比较器**，并应尽快接入游玩智能体；上述缺口限定的是“原版逐日对拍/整场胜率校准”宣称。后续优先级是只读采真实 refresh 后 entry、将领选择与 event row/fire 同日身份，再增加非致命 wound 与死亡后的下一帧属性/名单对拍；任何实机需由主任务受管 runner 在独立 attempt 执行，本页不要求或授权启动 CK3。
