# 活跃战斗：日末到终局的控制流静态核（CK3 1.19.0.6）

本页只补足“**何时算结束**”的调用边界和当前续算器的输入缺口；完整撤退资格、追击伤害与结果 envelope 已分别记录在 [战斗模拟](battle-simulation.md)、[战中撤退](active-combat-retreat.md) 和 [终局与再接战](battle-terminal-and-reentry.md)。证据是原版 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的**离线反汇编**。本轮未启动游戏、未取得新的 live parity。

## 冻结的调用顺序

[静态确认] manager `0x27FB5D0` 在 `0x27FB6C6` 先把当前 `phase_day` 加一，再按 `phase` 派发：main/1 于 `0x27FB6FD` 调 `0x2309E80`，pursuit/2 于 `0x27FB6DF` 调 `0x230A2A0`。`0x2309E80` 首先重算双方 total，在 `+0x700` 有 forced winner 时优先采用；否则依次测试 side0 `+0xB8<=0`（winner=side1）、side1 `+0x400<=0`（winner=side0），两侧都正数才运行当天效果、roll、出伤与写伤亡。因此**当天伤害刚把一侧打空，不在该函数尾部立刻定胜负**；下一次 main tick 开头才看到该条件，除非另外的 effect/命令同步推动阶段。

[静态确认] `0x230A010` 先写 `winner_raw +0x6E0`，再以败方首个 stored Army 检查 `0x2308250`。不能 route 时，按顺序对败方两组 entry 调 `0x23D2E30` 清当前量/soft，清 side totals，写 `phase=3, phase_day=0`。能 route 时先把两组初始 soft pool 冻结到 `+0x6E8/+0x6F0`，写 `phase=2, phase_day=0`；败方 `skip_pursuit +0xC2` 为真才在同一调用栈同步调用一次 `0x230A2A0`。该函数开头测试 skip flag，直接转 finish，故这不是一次正常的追击伤害日。

[静态确认] 每日追击 tick `0x230A2A0` 先读既有 winner，按其反侧选败方；败方 skip flag 或 `phase_day > PURSUIT_PHASE_DAYS` 走 finish，否则调用 `0x23CD2E0` 结算。原版常量为三天，即 phase-day 1、2、3 可以发生追击计算，day 4 走 finish。finish 在 `0x230A3F9` 写 `phase=3, phase_day=0`，随后还调用 `0x23068E0` 并处理其它状态；**不能只因看到 phase=3，就把对象当作已完成 finalizer/已从 storage 删除**。其余 finish 子调用的全部业务名，本核没有另行命名。

[静态确认] 回到 manager，当轮 tick guard 清除后，如果 invalidation flag `manager+0x58` 已置位，优先进入 `0x27FBE50` sweep，跳过普通 phase-done 分支。否则 `phase=3` 才于 `0x27FB73E` 调 `0x230A590(combat,false)` 构造正常结果，再于 `0x27FB74A` 调 `0x27FDC50` 移除旧 CombatID。sweep 满足自身身份/guard gate 时则于 `0x27FBF85` 调 `0x230A590(combat,true)`，随后移除，**即使当时仍是 main 阶段**。这条路径不产生正常胜负结果；不得把 `winner_raw`、phase3、retreating 或旧 CombatID 消失中的任一项单独当成“正常胜利”。战中 owner-subset 撤退只抽出该 owner，仍存活的同侧 owner 留在本 CombatID；full-side 撤退才记录对侧 winner。追击中加入新参战者还可重开 main、重置 winner，见上述专题。

按这个控制流，观察/预测结果至少应区分：`active_main`、`winner_recorded_pursuit`、`phase_done_pending_finalizer`、`normal_result_removed`、`no_normal_result_removed`、`owner_subset_left_battle_combat_continues`、`pursuit_reopened_main`。这不是说当前 query 没有字段：已有 battle-control 暴露 phase/day/winner/forced/finalized 与 ordered sides，terminal journal 记录 finalizer kind；**分类必须把同一 CombatID/revision 的暂停帧与 terminal journal 连起来**，不能从单个 raw 字段推断历史事件。

## 对现有算法和智能体的具体影响

- `simulation/combat_core.py::transition_after_winner_is_known` 已镜像败方 route gate、无 route 清零及追击入口；`research_envelope.py` 的 whole-battle trial 却把败方 `disallow=false / allow_early=false / landless=false / skip_pursuit=false` 写死，并在定胜方后固定三次追击，没有动态命令、reopen 或 no-normal sweep。此结果只适用于它声明的冻结条件，不能作为真实下一日与整场结果的无条件分布。
- `ActiveMainResumeState` 明确只接受 main；从已处于 pursuit 的存档继续计算没有同帧 `phase_day`、已冻结 `+0x6E8/+0x6F0`、败方 skip flag、当日参战者变更的生产输入。下一步应先补只读生产 census 和 same-revision 绑定，再接续算器；不得用 pre-contact 快照代替。
- `research_envelope.py` 的 `battle_days += 3` 记录三次**伤害 tick**，但原版普通追击还有 day 4 的 finish/finalizer tick。若向智能体报告“何日终局/行军何日可重新接令”，必须另行对齐原生日历，不能把伤害 tick 数直接当成 CombatID 移除日期。当前 `horizon_days` 循环还只限制 main 部分，进入追击后可以超过该 horizon；要求截止日期的决策器须显式处理。
- 智能体已有 active-retreat typed action 和 postcondition，terminal journal 也能验证已发生的结束；策略层不能把“可撤退”推成“原生 AI 会撤退”，也不能把 owner-subset 离场当成整场结束。对于 hold/forecast，应以 roster/phase/winner/reopen/terminal 的真实状态转移触发重判，而非只等固定三日。

## 可复核静态门与下一项实机对拍

运行 `tools/.venv/Scripts/python.exe ck3_autonomous_player/native_bridge/research/verify_combat_terminal_controlflow.py --exe <CK3 1.19.0.6 ck3.exe> --expected ck3_autonomous_player/native_bridge/research/fixtures/combat_terminal_controlflow_1_19_0_6.json`。脚本拒绝错误 EXE 哈希，并逐条比对 main 起始胜方判定、winner/route/phase 写入、追击和 manager 两种 finalizer 入口的确切机器指令与冻结报告；它**不是** live trace 或完整 CFG 等价证明。

下一项 live matrix 应至少冻结同一 CombatID 的：(1) 伤害将一侧打空后的当日帧与次日 winner/phase；(2) 正常追击 1/2/3 日与第 4 日 finalizer 日期；(3) skip-pursuit 当日同步结束；(4) owner-subset 撤退后 combat 继续；(5) pursuit 增援重开 main；(6) no-normal sweep。每个样本都需同一 revision 的 battle-control、participant/entry ledger、terminal journal 与原生日历。`no-normal` 和 `reopen` 尚不能因本次静态核而改成 live-confirmed。
