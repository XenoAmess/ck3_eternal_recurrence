# 现役反制同帧输入合同（2026-09-27）

`battle_control_snapshot.active_counter_inputs_v1` 是 CK3 1.19.0.6 的只读观察子域。它在现有 `ReadBattleControlSnapshotSample` 内、两侧 battle entries 读完后读取；外层 battle-control 对整个 sample（包括本字段）做两次相等比较，且要求观察前后世界修订号与日期一致。字段的 `available` 只表示**当前暂停帧的反制基础 operand census 完整**，不是下一战斗日的 retention、出伤或整场胜率已获验证。`active_combat_resume_inputs_v1` 仍返回 `unavailable/same_frame_resume_operands_incomplete`，其 `missing_required_domains` 仍含 `active_regiment_counter_class_stack_context`。

来源边界沿用[静态审计](active-combat-counter-context-source-audit-2026-09-27.md)：现役兵团逐条取自 `CCombatSide` 的 `0x60` entry，RegimentID、CArmyID、bucket/index 和 `entry+0x18` 的 Q100000 当前作战人数与 battle-control 同源。`CRegiment+0x18` 的 inner type 提供反制 class、stack 和完整目标表。`read_counter_current_chunk` 用包含同一 full RegimentID 和**现役 entry 当前人数**的 synthetic entry 调用，绝不使用 v3 预接战的 `regiment.current_soldiers * 100000`。class 为负的 MAA 是显式 `absent`，其 class、stack、chunk 都是 null，目标表为空；其他任何兵团读取、generation、target 或 chunk 失败会使**整个子域** unavailable，不能混合发布部分成功行。

双侧 `primary_owner_character_id` 与当前 `CCombatSide+0x70` 的主参战者相同。每侧原生 owner modifier 原始值发布为 `counter_efficiency_raw`（`0x106`）和 `counter_resistance_raw`（`0x107`）；两个有方向的 `context_scale_raw` 由 `get_counter_context_scale` 分别调用，方向为 `countered_side_index` ← `countering_side_index`。选中将领既不是 context owner，也不能替代主参战者。所有整数保持原版值，定点项以 `scale=100000` 表示；`stack_size_soldiers` 是原始整数人数。

生产者先校验 class count、每条 full-generation RegimentID/CArmyID、inner type、目标表 class 边界及正 stack；所有读口只读取属性或调用已核对的只读 helper，不调用战斗 mutator、RNG 或日期推进。每条兵团读后复查 generation、inner type 和所属 CArmyID；每侧读后复查 `CCombatSide+0x70` 主参战者及 owner generation。任一失败立即清空已收集的 sides/contexts，仅给 `status=unavailable`、`operand_census_complete=false` 和原因。成功时严格按两侧 battle MAA entry 原始顺序发布两侧和两个方向，并由 C++ serializer 与 Python normalizer 双重核对同一 battle entry 的 ID、CArmy、当前人数、class/target 边界、chunk 和真实主参战者；两次 native sample 任一值不等，整个 battle-control 查询按原有 `state_changed_during_read` 拒绝。

这次实现没有发布原版 `0x23CF1B0` 的 class retention 向量，也没有捕获战斗日界 `0x23CAE70` 真正使用的 owner、entry 集合和 modifier 刷新时点；因此不能把当前帧输入自动升格为下一日续算，不能让智能体用它替换 v3 的预接战向量。后续需在 exact EXE 的冻结战斗存档取得同一原生 sample 的实机回读，再以只读被动 trace 对拍日界双侧 entry、owner、context、retention 和出伤输入，覆盖人数耗尽、增援重排与混合 owner。086 旧回执能证明两种人数不得混用，不能充当这个新字段的实机验收。

静态验收：`test_battle_control_snapshot_v1_bridge.py` 覆盖完整、缺失、错误当前 chunk、ID 漂移、主参战者与选中将领分离、方向 owner 错配；`battle_control_snapshot_v1_mailbox_test.cpp` 覆盖同一 wire、不可用不泄露部分 operand 和 C++ 拒绝错配。测试与编译通过只证明合同及构建，**尚无本次新读口实机 GREEN**。
