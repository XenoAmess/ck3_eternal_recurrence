# 现役战斗 coalition side 同帧映射输入（2026-09-27）

`active_combat_resume_inputs_v1.observed.battle_side_mapping` 现在从已经通过 `ValidateSnapshot` 的**同一个** `BattleControlSnapshot` 写出，不另查询 v3 或游戏状态。battle-control 在原生 application-main 内双采样整份快照，前后还核对 paused 世界帧；新增观察字段继承这个边界。088 的原生同帧反制实采和 087 的实际将领实采进一步确认这个读口可以返回真实两侧，但本次没有启动 CK3，新增字段本身仍需独立实机回读。

映射包含 `status=available`、subject 所在 `side_index`、对侧 index、subject CUnit 的真实 owner CharacterID、`full_side|owner_subset`、双方按 `CCombatSide` 原始顺序排列的 PublicCUnitID，以及同侧该 owner 的受影响/其他 owner 的未受影响有序子集。它直接使用 `selected_public_cunit_id`、`selected_native_carmy_id`、`selected_owner_character_id`、`side_index`、双侧 `ordered_armies` 和既有撤退范围投影。C++ 合同先校验 subject 恰在一侧，full CArmy/CUnit 身份及 combat backlink 匹配、两侧无重叠，再按每军 owner 重建并比较子集；Python 合同把 typed 字段逐项与同份 battle frame 复核。选中将领、首军 owner、假定接战请求顺序都不参与映射。

新 native 回执只有在这些条件全过时才省去 `missing_required_domains` 中的 `active_coalition_side_mapping`。历史 086/087/088 回执保持原字节：没有 `observed.battle_side_mapping` 时，Python 仅在缺域仍列有该项时接受；有字段却仍列缺域，或缺字段却声称已闭合，都拒绝。策略端优先使用已验证的 typed 映射；旧回执仍按已验证 battle frame 投影供诊断，不据此把历史缺域改写成已满足。测试覆盖 subject 为 attacker/defender、owner subset、军队错序、错误 owner/side/scope 与缺域声明不一致。

这只关闭**当前暂停帧 subject 与两侧 coalition 的身份归属**。它不证明下一战斗日 coalition、owner 或 entry 集合不变，也不替未来增援、撤退、骑士与非掷骰优势建立转移模型。整个 resume 回执仍为 `unavailable/same_frame_resume_operands_incomplete`、`input_observation_ready=false`；智能体不得用它声称整场现役胜率或解除续算 guard。下一步需在新独立只读实机 attempt 中回读该字段，与 087/088 的原生 side/owner/ordered armies 比对，并保留这次新回执和清场证据；该 live 验收属于后续工作。
