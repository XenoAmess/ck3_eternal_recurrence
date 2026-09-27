# 现役反制同帧输入合同（2026-09-27）

`battle_control_snapshot.active_counter_inputs_v1` 是 CK3 1.19.0.6 的只读观察子域。它在现有 `ReadBattleControlSnapshotSample` 内、两侧 battle entries 读完后读取；外层 battle-control 对整个 sample（包括本字段）做两次相等比较，且要求观察前后世界修订号与日期一致。字段的 `available` 只表示**当前暂停帧的反制基础 operand census 完整**，不是下一战斗日的 retention、出伤或整场胜率已获验证。`active_combat_resume_inputs_v1` 仍返回 `unavailable/same_frame_resume_operands_incomplete`，其 `missing_required_domains` 仍含 `active_regiment_counter_class_stack_context`。

来源边界沿用[静态审计](active-combat-counter-context-source-audit-2026-09-27.md)：现役兵团逐条取自 `CCombatSide` 的 `0x60` entry，RegimentID、CArmyID、bucket/index 和 `entry+0x18` 的 Q100000 当前作战人数与 battle-control 同源。`CRegiment+0x18` 的 inner type 提供反制 class、stack 和完整目标表。`read_counter_current_chunk` 用包含同一 full RegimentID 和**现役 entry 当前人数**的 synthetic entry 调用，绝不使用 v3 预接战的 `regiment.current_soldiers * 100000`。class 为负的 MAA 是显式 `absent`，其 class、stack、chunk 都是 null，目标表为空；其他任何兵团读取、generation、target 或 chunk 失败会使**整个子域** unavailable，不能混合发布部分成功行。

双侧 `primary_owner_character_id` 与当前 `CCombatSide+0x70` 的主参战者相同。每侧原生 owner modifier 原始值发布为 `counter_efficiency_raw`（`0x106`）和 `counter_resistance_raw`（`0x107`）；两个有方向的 `context_scale_raw` 由 `get_counter_context_scale` 分别调用，方向为 `countered_side_index` ← `countering_side_index`。选中将领既不是 context owner，也不能替代主参战者。所有整数保持原版值，定点项以 `scale=100000` 表示；`stack_size_soldiers` 是原始整数人数。

生产者先校验 class count、每条 full-generation RegimentID/CArmyID、inner type、目标表 class 边界及正 stack；所有读口只读取属性或调用已核对的只读 helper，不调用战斗 mutator、RNG 或日期推进。每条兵团读后复查 generation、inner type 和所属 CArmyID；每侧读后复查 `CCombatSide+0x70` 主参战者及 owner generation。任一失败立即清空已收集的 sides/contexts，仅给 `status=unavailable`、`operand_census_complete=false` 和原因。成功时严格按两侧 battle MAA entry 原始顺序发布两侧和两个方向，并由 C++ serializer 与 Python normalizer 双重核对同一 battle entry 的 ID、CArmy、当前人数、class/target 边界、chunk 和真实主参战者；两次 native sample 任一值不等，整个 battle-control 查询按原有 `state_changed_during_read` 拒绝。

这次实现没有发布原版 `0x23CF1B0` 的 class retention 向量，也没有捕获战斗日界 `0x23CAE70` 真正使用的 owner、entry 集合和 modifier 刷新时点；因此不能把当前帧输入自动升格为下一日续算，不能让智能体用它替换 v3 的预接战向量。后续需在 exact EXE 的冻结战斗存档取得同一原生 sample 的实机回读，再以只读被动 trace 对拍日界双侧 entry、owner、context、retention 和出伤输入，覆盖人数耗尽、增援重排与混合 owner。086 旧回执能证明两种人数不得混用，不能充当这个新字段的实机验收。

静态验收：`test_battle_control_snapshot_v1_bridge.py` 覆盖完整、缺失、错误当前 chunk、ID 漂移、主参战者与选中将领分离、方向 owner 错配；`battle_control_snapshot_v1_mailbox_test.cpp` 覆盖同一 wire、不可用不泄露部分 operand 和 C++ 拒绝错配。构建及静态测试之后，下述 088 完成了本次新读口的现役同帧实机回读。

## 088 冻结战斗存档的独立只读回读

[live-observed] 独立 attempt `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-attempt-088` 使用原版 1.19.0.6 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、第 11 日冻结存档 SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953` 与新 DLL SHA-256 `F56304CC0D46BFFCDC3477FEBD823235AB956E8CAFF5DB4F1432F7C6B4279D32`。启动前的 006 独立新鲜截图 SHA-256 `8E9FE00D26A22DD3A063E3B83283549CE6840A3F97F39F57ED8BB52FFE8B1F3B` 已人工看到 Steam 左下“离线模式”；ToDesk 未重启，Steam 未切换模式。004/005 的前台拒绝记录保留，不能拿来替代这张成功截图。

查询前后均暂停于 `native:3`、public/native revision `4/3`、raw date `53146488`；其间 `ck3_query_battle_control_snapshot_v1` 返回 `CALL_COMPLETED`。实际 `CombatID=16777218`、ProvinceID `2633`、subject ArmyID `18` 位于守方 side 1、主阶段第 7 日。`active_counter_inputs_v1` 为 `available`、`operand_census_complete=true`、class count `13`。攻击方真实主参战者 CharacterID `31549`（与所选将领 `34320` 不同），18 条 MAA entry 中 5 条有 class、13 条显式 absent，效率/抗性原始值 `0/0`；守方主参战者 `29829`，14 条中 3 条有 class、11 条 absent，效率/抗性 `25000/0`。方向 context scale 分别为守方反制攻方 `125000`、攻方反制守方 `100000`（均 Q100000）。51 号兵团属于守方 ArmyID `18`，其**现役 entry** 当前人数为 `17579130` Q100000，即 `175.79130` 人的内部值，原生 counter chunk 为 `175791`；class `1`、stack `100` 人，目标 class 为 `4/5/8/9` 且各自 effectiveness `100000`。这与 v3 的预接战整数人数及 chunk 不是同一个输入。

原始前帧、battle-control、后帧 SHA-256 依次为 `95C42C520926CF3B66F106ADFBFF4D7E91577F71820F83A7EAFDA8E3E2A11FD4`、`350941D8F88EAE8BA5F91C9CBDCC8F025920D9F120842C6571E832AD86CF396F`、`5FF86DF09D0DF07F222F89DFD1D42970BA567E56B7C57F481A4D16C1F7BC0351`；清场回执 SHA-256 `050123AB77778D00B3D6E66A23C0EE033A9ADD938B8DBEBD10A326756B74164F` 记录 capture 返回 0、CK3 进程树清空。可重放的[精确投影器](../../ck3_autonomous_player/tools/project_active_counter_088.py)与[机器向量](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_active_counter_088.json)约束每份源哈希和同帧身份。

该实测只证明当前帧的原生反制基础 operand 可完整读取。`active_combat_resume_inputs_v1` 仍为 `unavailable/same_frame_resume_operands_incomplete`，包含 `active_regiment_counter_class_stack_context` 在内的四个缺域仍在；没有推进下一战斗日，也没有对拍真正进入 `0x23CF1B0` 的 class retention 向量或下一日输入。因此不得据此把下一日、整场胜率或智能体决策标成已闭合。

## 用现有拟合公式计算的当前帧向量

从同一 088 原始回执完整的 32 条 MAA entry 出发，[投影器](../../ck3_autonomous_player/tools/project_active_counter_088.py)复用游玩智能体的 `fixed_mul/fixed_div`，按每个方向逐 class 累加真实 chunk、目标 effectiveness 和 context scale，生成单独的[模型推算向量](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_model_derived_active_counter_088.json)。它的 `scope=current_paused_frame_only_not_native_output_or_next_day` 是合同的一部分；旧的 088 实测向量字节保持原样。

具体地，守方 side 1 的 class 1 目前只有 51 号团贡献自有 chunk `175791`；攻方对 class 1 产生压力 `178698`。现有模型按 Q100000 逐次截断：`fixed_div(178698,175791)=101653`，再 `fixed_div(101653,200000)=50826`，乘最高 90% 减伤得 `45743`，所以推算保留比例 `100000-45743=54257`，即约 54.257% 的原伤害。攻方 side 0 的 class 8 自有 chunk `83240`、守方压力 `219738`，模型比例降至下限 `10000`。这些是**原生同帧 operand 驱动的模型结果**，尚无原版 `0x23CF1B0` 同边界输出对照，也未包含下一日事件、人数和 owner 更新；只有完成该对照才能将比例称为原生实测。
