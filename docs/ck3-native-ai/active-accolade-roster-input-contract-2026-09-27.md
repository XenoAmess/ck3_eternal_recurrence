# 现役称号优势的名单缺口与最小同帧合同（2026-09-27）

本页沿[缓存前刷新链](active-advantage-refresh-source-2026-09-27.md)继续审 CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。只读 [`verify_active_accolade_source_gate.py`](../../ck3_autonomous_player/native_bridge/research/verify_active_accolade_source_gate.py) 复核既有 40 个刷新锚点后，再核 `0x251C200..0x251C271` 的 `.pdata` owner、15 处精确指令和三个失败分支的共同目标；[冻结夹具](../../ck3_autonomous_player/native_bridge/research/fixtures/active_accolade_all_row_gate_11906.json) SHA-256 `9A74A520FC1BD1813B7A90FE7AC7934A1A7023F899AE821C49F54DB5E2D83BE4`。本轮未启动 CK3，未调用原版 helper。仓库现有 v3/现役结构比对基于 `830fe47b3` 的 `combat_v3.cpp`、`combat_v3.hpp`、`ck3_11906.cpp` 与 `game_contract.hpp`。

## 缺的不是一个“骑士列表”

原版 `0x23CBCE0` 每次从**所有 MAA-like entry 原序**重建称号聚合器；`CRegiment+0x148 == -1` 的空骑士槽也属于输入顺序，只是该槽被跳过。非空槽再经 Character generation、角色有效性虚调用、Character `+0x1A8` 称号链接、Accolade full ID generation 和称号有效性虚调用，才可能调用 `0x251B8F0(accolade, side+0x110)`。`0x251B8F0` 在追加前还调用 `0x251C200`：它遍历 Accolade `+0x58/count+0x64` 的**每一条** `0x18` row，要求 row `+0x10` 来源指针非空，且该来源对象 vtable `+0x00` 返回真。遇到任一失败即从中途跳到 `0x251C242`，返回 false，整次该称号的 modifier 追加被跳过；空 row 集合则通过门但没有 row 可追加。这不是“只过滤失败 row 后继续追加其余 row”。

当前两个已发布名单的用途不同：

| 现有结构 | 已有字段 | 对称号刷新缺的内容 |
| --- | --- | --- |
| v3 假想接战 `CombatPhaseCandidateSourceProofV3.ordered_sources` | 原生顺序的非空 `{role, source_army_id, source_regiment_id, character_id}`；`ReadNativeCandidateSourceRowsV3` 对 `CRegiment+0x148 == -1` 使用 `continue`。local-shell 随后确实调用原版 `0x2308D50`，故其**假想场景**总结果可以和原版 helper 对拍。 | 序列化行不保留空 MAA 槽的位置，也无 Character/Accolade 有效性虚调用结果、AccoladeID、`+0x58/+0x64` 来源 rows 或 `0x251C200` 全 row gate。它不能仅凭自己的候选行反演称号聚合器的生成。 |
| 现役 `BattleControlSideSnapshot.men_at_arms_entries` | 全部 MAA entry 的 `bucket_index`、full RegimentID、ArmyID、owner、当前兵力与有效伤害/坚韧等；`ReadBattleControlEntryBucket` 已按 generation 解析 Regiment 并验证 Army backlink。 | 未读取每个 Regiment `+0x148` 的当刻 CharacterID，更没有经 Character `+0x1A8` 到 Accolade full ID、来源 row 以及原调用门结果。`owner_character_id` 是军队 owner，不是该 entry 的骑士。 |

因此不能把 v3 `ordered_knight_ids`、现役 entry 的军队 owner，或当前暂停帧 `side+0x110` 的汇总值当成**下一次** `0x23CBCE0` 的精确原始输入。称号增益的空槽、有效性和整组来源门都可改变结果；同日增援/撤退、骑士伤亡和称号状态变化还会改变 entry 与 row。

## 最小 typed 同帧只读输入合同

新增诊断块应明确分成 `stored_roster_at_pause` 与 `original_refresh_outcome` 两个证据层；二者不能用一个 `available` 混写：

| 字段组 | 只读暂停帧可复制的类型和约束 | 必须由原调用边界观测的内容 |
| --- | --- | --- |
| 来源身份 | `snapshot_revision:uint64`、`date_raw:int64`、`combat_id:full-id`、`side_index:0|1`、`target_province_id:full-id`；读前后复核 Combat/side、phase/day、Province、同帧 revision。 | `materialization_ordinal:uint32`、原日更线程、helper 入口/出口日期与 side identity，以把暂停样本和**随后实际发生**的刷新配对。 |
| 完整 MAA 顺序 | 有界数组一行对一条 `side+0x40/count+0x4C` entry：`bucket_index:int32`、`regiment_id:full-id`、`army_id:full-id`、`regiment_character_id_raw:int32`（允许 `-1`）；保留空槽，不按 CharacterID 去重/排序。Regiment 与 Army 回指复核。 | 该 entry 在本次刷新是否仍存在、当次原序、当次 `CRegiment+0x148` 与 generation 解析结果；join/leave 后不得沿用暂停位置。 |
| 角色和称号链接 | 当 `regiment_character_id_raw != -1` 时记录 generation-valid CharacterID、`character_accolade_link_present:bool`、链接 `+0x568` full AccoladeID 或 null；按身份再次读取校验。源 row 只在 count/capacity、指针、加载对象身份都可验证时复制 `{row_index, selector_raw:int32, source_loaded_identity}`。 | 角色与称号虚调用门、`0x251C200` 每 row 的来源虚调用结果，以及 `all_rows_gate:bool`；这三个虚调用当前不具备暂停重调的副作用证明，只能在原游戏调用中受管采样。 |
| 结果 | 当前只读块最多 `stored_roster_observed=true`。若任何身份或 span 不安全，整个块 unavailable。 | 保存刷新后 `side+0x110` 的有序规范化 modifier 来源与原 `aggregator_raw`，并与同一 ordinal 的将领嵌套/side 主调用分项相等核对。原调用结果是事后证据，不变成未来日常数。 |

这个合同可复用 v3 已有的 generation-safe Regiment/Character resolver、全 MAA entry 验证与有序 Army 映射，但必须以**现役 Combat 的原始 entry**作 source，不可把 v3 local shell 的假想名单和现役快照拼成一个同帧。`original_refresh_outcome` 缺失时，`active_combat_resume_inputs_v1.next_day_non_roll_advantage_sources` 仍为 missing；即使已拿到一次 outcome，跨日预测仍须重新求值角色、称号来源及其他将领/side modifier。

## 第一层只读暴露（静态实现，待实机）

`query_battle_control_snapshot_v1` 的每条 `men_at_arms_entries` 新增可选的 `knight_character_id_raw:int32`。读取同一条 entry 已验证的 `CRegiment+0x148`，在调用既有 entry-strength getter 后复读，变动则整帧拒绝；序列化保留 `-1` 空槽和带符号 full ID，不将其改写为军队 owner，也不跳过零兵力 entry。徵召兵条目不带该字段。Python 标准化同时接受没有此字段的历史回执，新增字段只接受 int32（拒绝 bool/null/越界）。原战斗查询其余字段和 `active_combat_resume_inputs_v1` 的缺域判定保持原样。这只封闭「暂停帧完整 MAA 槽位与骑士 ID」这一层，尚不证明称号资格或下一日优势。
