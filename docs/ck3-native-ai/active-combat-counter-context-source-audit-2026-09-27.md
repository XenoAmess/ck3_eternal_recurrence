# 现役战斗兵种反制：class、stack 与 context 的来源边界（2026-09-27）

## 可用结论

[static-confirmed] CK3 1.19.0.6 的反制不是仅按兵种名称套一个常量：对被反制侧和实施反制侧的每个 `0x60` 字节 MAA 战斗 entry，原生读取 full `RegimentID` 与 `entry+0x18` 的当前作战人数 Q100000，借 `CRegiment+0x18` 所指的 inner type 取得 stack size、class 和目标表，再用双方**侧主参与者**的反制抵抗／效率修正生成每类 damage retention。实际选中将领不是这个 owner 的替代值。当前 `battle-control-snapshot-v1` 已读到现役 entry 的人数、顺序、side 与主参与者，却尚未在同一读口发布反制 class、stack、targets、当前 chunk 和实际 context；现役续算回执仍列 `active_regiment_counter_class_stack_context` 为缺域。

[live-observed] 086 暂停帧提供了明确反例：现役战斗的 51 条 entry 与 v3 假定接战输入按 full RegimentID 和所属 CArmyID **51/51 对上**，但 entry 当前作战人数与 v3 的军团 `current_soldiers × 100000` **51/51 不同**。因此不能把 v3 的 `current_chunk_raw` 或整条 `damage_retention_by_class_raw` 当作该 `CombatID` 下一次出伤修正。v3 的 `available` 只指 `explicit_hypothetical_contact` 的输入观察；086 的现役 typed 续算状态仍是 `unavailable/same_frame_resume_operands_incomplete`。

这份备忘录只审计原生来源与 086 已有证据，没有修改 native/Python 接口、启动游戏、推进日期或声明续算已可供智能体使用。

## 精确来源与现有读口的差异

| 项 | 原生／源码锚点 | 现役读口现状 |
| --- | --- | --- |
| 当前兵量和身份 | 原版 `0x23D2B90` 从 `Entry60+0x08` 解析 full CRegimentID，读取 `Entry60+0x18` Q100000；`ReadBattleControlEntryBucket` 逐 entry 读这两个偏移并校验 CArmy、bucket、generation（`native_bridge/src/ck3_11906.cpp:14180-14306`）。 | battle-control 发布 `current_fighting_raw`、side/army/owner、MAA/levy 原始顺序及有效属性；没有发布 counter chunk。 |
| stack／class／targets | `0x23D2B90` 由 `CRegiment+0x18` 的 inner type 取 `+0x68` int32 stack size，以 entry 当前值除以它；stack 零返回 `-1`。`ReadCombatCounter` 从同一 type 的 `+0x270` 取 signed class，`+0x2B8/+0x2C4` 取 target data/count，目标 stride `0x10`，class 与 effectiveness 在 `+0x00/+0x08`（`ck3_11906.cpp:8437-8508`）。 | v3 的 counter class/targets 由 CRegiment 读出，但 chunk 是从**军团整数人数**构造的 synthetic entry；battle-control 的 entry 结构尚无 class、stack、targets 字段（`game_contract.hpp:1257-1279`）。负 class 是 `absent`，不能替换成 class 0。 |
| 双侧 context | `0x2946B50` 使用被反制侧主参与者 modifier `0x107`（抵抗）和实施侧主参与者 `0x106`（效率）；`0x23CF1B0` 以 `countered/countering` 两组有序 entry、context scale 和原版 class count 求每类 retention。v2 `ReadCounterResolution` 在 `ck3_11906.cpp:9357-9456` 复用这两个 helper。 | v2/v3 的 `BuildCounterSideEntries` 以假定请求中**首军 owner**定 context owner，并写 `regiment.current_soldiers * 100000`（`ck3_11906.cpp:9302-9355`）；现役应从真实 `CCombatSide+0x70` 主参与者读，不借用假定请求顺序。battle-control 已发布主参与者（`ck3_11906.cpp:14372-14386`），但未求当前 context/retention。 |
| 应用点 | `0x23CAE70` 按被反制兵团的 inner-type class 选择 retention，作用于 entry 有效 damage；`100000` 表示无反制减伤，最低理论值为 `10000`。详见[原生公式](combat-simulation-inputs.md)。 | `FrozenCombatSimulationInput.dynamic_counter_retention_by_class_raw` 已能用传入的 `CombatRegimentState.current_raw` 重算 depleted chunk（`simulation/combat_input.py:218-304`），但其 class/stack/targets/context 仍来自假定首次接战的 frozen rows；不能仅替换人数就解除 active guard。 |

具体地，每个 class 的 `own_chunks` 是被反制侧该类当前 chunk 之和；`pressure` 是对方每个 chunk 乘相应 target effectiveness 和 context scale 后的和。`own_chunks=0` 时 retention 为 `100000`，否则为 `100000 - fixed_mul(min(100000, fixed_div(fixed_div(pressure, own_chunks), 200000)), 90000)`。每个乘除均为原版 Q100000 截断，不能把 v3 已求出的 retention 当成只需乘一个人数比例就可更新的数。

对 `CRegiment+0x18` 的 **counter inner type** 和 `CRegiment+0x118` 的 **有效属性 type** 不得假定为同一指针；兵团 87 的[双类型来源审计](maa-regiment-87-dual-type-source-boundary-2026-09-27.md)已把相等性列为未采。`maa_type.key`、显示兵种名和有效属性 class 均不可反推 counter class。原版 `0x23D2B90` 在本机 exact EXE `SHA-256=2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的只读反汇编核到 `+0x08` generation 检查、inner type `+0x68`、`0x186A0=100000` 的定点除法和零 stack 的 `-1` 分支；`0x2946B50` 反汇编核到 `0x107/0x106` 两个 enum，`0x23CF1B0` 核到 class count `rules+0xF14` 及 context R9 非负 clamp。这里的 RVA 只适用这个 exact EXE。

## 086 交叉核算能证明什么

086 的原始 [battle-control 回执](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_active_composite_086.json) 和同帧 v3 回执由[精确投影器](../../ck3_autonomous_player/tools/project_active_composite_086.py)绑定；外置原件在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-battle-control-composite-attempt-086\ck3-output\interactive-requests-responses\`。两份原件 SHA-256 分别为 `6DFC287C42154486D78E2609AEE1C74B2A00F7E2E018C8FBC4B90D639CC4D550`、`F191AC1EBB3C9010882B8AD2892346F8B0DAB52D7B64298C017D578B72118793`，本次只读重验；两查询的公开/native revision 均为 `5/4`、日期 `53146488`、世界暂停。两份查询**不是一次原生 application-main 联合采样**。

| 例子 | 真实 `CombatID=16777218` | v3 假定首次接战 | 解释 |
| --- | ---: | ---: | --- |
| RegimentID 51 当前 Q100000 | `17,579,130`（175.79130 人） | 军团整数 `193` 人，即 `19,300,000` Q100000 | 同兵团 ID 不代表两种人数状态等价。 |
| RegimentID 51 counter chunk | **未由现役读口发布** | `193,000` Q100000；class `1`、四个 target | 假定 chunk 与 v3 整数 193 反推 stack 为 100。若同一 inner type/stack 在现役 entry 仍有效，原版正数截断规则会给 `trunc(17,579,130 / 100)=175,791`，但这是**条件演算**，不是已实采的下一 tick 值。 |
| side 0 owner/将领 | 真实 primary `31549`，选中 commander `34320` | v3 counter owner `31549` | 本例 owner 相等源于请求首军与现役首军恰好一致；选中将领不同，不能代入 context。 |
| side 1 owner | 真实 primary `29829` | v3 counter owner `29829` | 同样不能将这次巧合推广到未来增援、重排或不同请求。 |
| context scale | **未由现役读口发布** | 玩家被反制 `100000`、敌方被反制 `125000` | v3 的数值和当前 owner 交叉吻合，仍未证明现役下一次原生调用读取同一 modifier 时点。 |

尤其不能从 v3 的 `damage_retention_by_class_raw` 反推现役 retention：分母 own chunks 和分子 target pressure 都由当前 entry 决定，某团归零也未必从假定军团 roster 消失。现有 Python 公式保留同 ID 顺序检查是有用的，但验证其现役含义须先得到真实 side entry 顺序与两个方向的同钩子 context。

## 最小生产者与升级门槛

在拟议的 `query-active-combat-forecast-inputs-v1-<subject_public_cunit_id>` 内，反制子域最小只读载荷应从**已解析的真实 CCombat 两侧**取得，不能独立拼接两次 v3/battle-control 回执：

1. 绑定 exact EXE、暂停帧、revision/episode/date、full-generation CombatID、Province、CArmy/CUnit/RegimentID、side 0/1、entry bucket/index 和原始有序 MAA entry census；排除 daily dispatch 正在写入的状态，双采样前后校验身份、entry 数组头、current 与 primary owner 未变化。
2. 对每条现役 MAA entry 发布 `counter.status=available|absent|unavailable`；`available` 才发布 inner-type class、正 stack size、完整目标表、该 entry `current_fighting_raw` 和以该值求得的 `current_chunk_raw`。所有 class/target index 须落在原版 class count；stack=0、负 chunk、generation/type 变化或目标表不完整即该子域 unavailable，不能置零。levy entry 的参与规则与 MAA counter wrapper 分开记，不把 levy 猜成可反制 MAA。
3. 对两个方向分别发布真实 `CCombatSide+0x70` 主参与者 full CharacterID、该 owner generation-valid 的抵抗/效率 modifier 原始值、`0x2946B50` context scale、`0x23CF1B0` 的完整 class retention 向量；发布所用 entry 顺序和 `countered/countering` 方向。把选中 commander、v3 首军 owner 作为交叉诊断字段，不当作默认来源。
4. 原样保留 `source_status`、`unavailable_reason`、Q100000 scale 与双采样一致性；只有同一原生 sample 的两侧 entry、owner、class/stack/targets、context、向量都齐全且彼此可复算，才把**当前帧反制观察**标为 ready。当前帧 ready 尚不等于**下一战斗日预测** ready。

验证顺序：先做零 stack、负 class、损坏 target、generation 切换、entry current 与军团 integer 不一致、首军 owner 与选中 commander 不一致、双方方向互换的聚焦静态/合成用例；然后在 exact EXE 的 086 冻结存档上同一 native application-main 回读真正的 `CombatID`，与旧 086 身份/人数交叉比对；最后以有界、默认关闭的被动原版日界 trace 对拍 `0x23CF1B0 → 0x23CAE70` 的输入 owner、两个 entry 数组、输出 retention 和实际损伤修正，涵盖一团归零、mixed owner 与增援重排。探针不得为取数调用状态 mutator 或 RNG，不能凭公式和同帧 v3 数值吻合冒充原版日界结果。下一日若可能刷新 class、owner、modifier、有效 damage 或 entry 集合，续算内核必须按已验证的时序重新读取/建模，不能冻结 086 的当前值。

在上述门槛通过前，`active_regiment_counter_class_stack_context` 继续保留在 typed `missing_required_domains`，智能体继续拒绝把 v3 假想首次接战试算当作正在进行的战斗胜率；它仍可用于独立的战前固定接战场景。
