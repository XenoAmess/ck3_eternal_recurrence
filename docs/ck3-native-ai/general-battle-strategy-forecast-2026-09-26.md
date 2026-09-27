# 游玩智能体通用战斗预测接线（2026-09-26）

2026-09-27 增补：前接战 v3 原生选中将领与零掷骰优势已进入有界预测；完整 base 而 phase unavailable 时明确回退 generic 近似，未来日仍冻结同帧值。证据、算式、回退门与受控前后向量见[专项接线记录](precontact-native-advantage-forecast-2026-09-27.md)。

## 2026-09-27：R0244 同帧输入阻塞与独立原版回读

[source-confirmed] [战争请求 R0244](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0244-20260927.json) 的正式失败帧在 War `48`、Army `16777237` 对 `16777417`、Province `2640`，已有同帧路线预览和全敌接触窗，但 `native_war_general_battle_inputs_query` 返回 `selected_step=null`，未提交游戏动作。根因是通用策略曾要求精确的 `query-combat-simulation-inputs-v3-<战场>-<入场边>-...` 字面量存在于 `action_steps`；原生驱动按设计只发布其能力模板，不枚举任意战场/参战者组合。修复现在从已观察的玩家军队、目标省、路线末边和敌军当前省精确构造只读字面量，以 v3 桥接能力作执行门，不放开无能力后端或任意写入动作。聚焦测试 `6/6`，v3 桥接与生产合同测试 `22/22`（另 `43` 个 subtest）通过；源码已于 `ba623c137` 推送。

[live-confirmed, analogous encounter only] 在**另一份独立配对**的纯原版存档（SHA-256 `77BE86B0FDE44D348807B201B9809A29F8099A4FF005A9C12D632045B4AB0DE9`）暂停 raw `53144520`，对 Character `29829` 的 Army `18` 与当前 Province `2638` 的敌 Army `24` 实际调用精确只读 v3 查询，路线末边 `2643→2638`。原版返回 `status=available`、输入完整性为真，查询绑定 `snapshot_id=native:3`、公开 revision `4`、原生 revision `3`，与前后暂停帧一致；查询响应 SHA-256 `0D252C2EDF307AFA7AD12650E7F3255B73FB65E41535AC71ADDF6D2DD9200107`。同一输入的 256 次有界估计在本例通过风险预算，但 `native_parity=false` 且人物死亡、未来属性刷新仍未量化，不能把 `256/256` 模型胜样称为原版实战胜率。原始请求/响应、源档、bridge、模型报告与进程清理保留于 `D:/workspace/ck3_native_war_ai_promo_work/war-input-r0244-analog-v3-attempt-062/`。

这证明已修复的**只读查询路径**在本机等价接口上可用，尚未复演另一台机器的 R0244 原始 War `48`。后续 `90afa9fef` 修复了长路线首跳动作投影：只从当前暂停帧的成功原生路线预览提取首个实际行进省，绑定 snapshot ID、公开/原生 revision、连接代次、episode、日期与军队起点后，提供该省的预览、全敌接触查询及移动步骤；策略仍逐一要求模型风险准入、精确单跳预览和无接触的一日窗口。原生路线若以当前省开头，只剥离这一处起点前缀。相关策略、首跳投影及桥接测试 `252/252` 通过，另有 `248` 个 subtest。

[live-confirmed, policy RED on a different local encounter] 独立 attempt `063` 从**驻军**存档 SHA-256 `91CEE43C055AA7C1412E5D5CD26CFEDE75E9459B4783E8C8BE8257908BEDD592` 恢复同一原版日期；Army `18` 驻 Province `2619`，到敌 Army `24` 所在 Province `2638` 的原生路线为 `2624→2631→2630→2629→8753→2626→2627→2633→2639→2643→2638`。全敌路线接触查询、一日无接触和精确 v3 输入均在 `native:3` / revision `4` / native revision `3` 的暂停帧成功，256 次有界估计通过风险预算。该估计只模拟 Army `18` 对目标处 Army `24` 的固定接战，并未把沿途其他敌军并入同一战斗；同帧原生总兵力为我方 `1,298`、五支敌军合计 `5,110`，`hostile_operational_overmatch=true`。生产计划最终返回 `native_war_capital_regroup_hold_progress / life-advance`：静态全路线审查标出敌军在 `2627`、`2633` 的未来路径交叉和目标省 `2638` 的敌军当前占位，随后即使原生窗口证明**第一天**无接触，策略仍以总敌军优势和目标占位拒绝把整条路线视为安全，未提交首跳动作。一日接触证明、单场模型准入和整条路线安全是三个不同合同；不能把其中一个替代另外两个。完整原始回执和 RED 摘要保留于 `D:/workspace/ck3_native_war_ai_promo_work/war-input-r0244-firsthop-attempt-063/`，进程清理清单为空。此例不能证明 R0244 原始战局的首跳执行；[交付响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-INPUT-R0244-20260927.json) 已在 `master`，仍需请求方以原始 save/DLL/EXE 成对复验并记录 verification。

## 当前行为

本次把研究版整场模拟接入 `choose_one_life_turn` 的战争动作边界。`planner_usable=false` 仍准确表示**尚未达到原版逐日转移完全对拍**；它不再作为“所有战争动作一律不看模型”的开关。智能体现在使用模型估计作决策，同时在计划回执中保留模型来源、输入哈希、样本数、假设、未知项及风险阈值。不能把模型输出称为原版准确胜率。

| 场景 | 输入与算法 | 行动规则 |
| --- | --- | --- |
| 已开战、原策略拟向敌军所在省份行军 | 精确同帧 route preview、全敌 route-contact horizon、`combat-simulation-inputs-v3` 有序参战者和逐兵团输入；`general_battle_forecast.py` 调用既有 `research_envelope.py`，默认 256 trial、120 日 | Wilson 已结算胜利下界至少 0.65，p90 硬伤亡至多 25%，模型全军覆没至多 5%，未决战斗至多 10%。**人物死亡尚未建模，回执为 null/unknown，不把研究核的 0% 当原版风险，也不因此禁用现有有界决策。**单跳且一日内抵达才可提交该接战移动；长路线只可在再次证明首跳无接战后移动一跳，并在下一帧重估。 |
| 已有主防守战争解围 | 原先 512 trial 的窄门仍在，Wilson 下界 0.70、p90 硬伤亡 20%、全军覆没 2%、未决至多 10%；该核的人物死亡同样未建模 | 保留已有同帧战争退出比较和短段行军限制；通用动作审查不会重复运行该窄门。 |
| 和平时原生 final-legal 宣战候选 | 兵团尚未物化；`prewar_battle_proxy.py` 用同帧原生 actor base power 与 target total power 做 256 次、120 日**聚合战斗代理试算** | 只在既有合法候选、同帧标准封建/经济/身份约束及 Wilson 下界 ≥0.95、未决 ≤5% 时提交 typed declaration；其余候选继续观察或查询。代理模型不是逐兵团模拟，也不是校准的 CK3 战斗概率。 |

聚合代理的显式政策假设：己方可到场 base power 取原值 65%–100%，敌方取 total power 的 110%–145%，双方未知将领掷骰各取 0–20；每轮双方按剩余聚合力量的 3% 同时出伤。种子绑定宣战 ID 与原生 power 输入。它用于**压倒性优势候选的行动先验**，并不把战争战略军力比改名为“原版胜率”。一旦可获取真实参战者和 v3 输入，改用逐兵团整场试算。

## 不一致性与下一轮研究

- 首轮接线回归发现，若只以 `source=native` 与 typed step 为准入，通用宣战入口会绕过玩家本人 claim、标准封建政府、同帧经济与派系约束；该不一致已在提交前修复，通用入口现重新核对这些字段。对应战争入口测试保留错误身份/政体/旧帧样本作回归。
- 路线回归发现，较远终点的预期敌军接触不能直接视为**当天首跳**的冲突；现在先核对全路线只含目标战斗，再用独立的一跳原生预览和接触查询证明首跳安全，下一帧重估。同样，其他战争的空敌军列表不会中断接战审查。
- 宣战回执区分“预测已计算但风险准入失败”和“原生输入缺失”；前者保留完整代理试算，并将 `prewar_forecast_admission_available` 记为 true。未进入代理模型的合法候选回执列出实际不满足的同帧策略约束，不能再笼统写成“模型不完备”。
- 实机每次接战后应把预测输入哈希、模型构建、三分结果（赢/输/未决）、p90 损失与实际 CombatID/战果对齐，分开统计“结果预测偏差”和“原版采集器 RED”。Episode 1 Messina 早期的增援日 attempt 因预备身份表缺新军而 RED，不能冒充模型公式偏差；后来从两个源日重放的[七边界 GREEN 回执](battle-reinforcement-and-join.md#2026-09-26两次自然增援的七边界身份同日出伤与逐团写回闭合)已修复这个**采集器**缺口。人物/兵团 full mutable 写回及未来路线预测仍是独立研究项；见[实机案例](battle-simulation-episode01-live-case.md)。
- 固定参战者研究核仍禁用 loaded phase-event effects 与自愿撤退，未纳入途中新军加入；战争中的计划会在每个新暂停帧重新读取路线、敌军与输入，不复用旧候选。两次原版增援日已证明：若有实际到达的候选，新军在当天首次主阶段出伤前入场并同日承伤。将它用于**未来** trial 时，必须先有当前帧可信 route/ETA 与参战身份，再在到达日主阶段前扩名册；当前估计继续明确标记 `fixed_participants`，不凭这两次旧战例虚构未来增援。原版 effect/撤退/属性刷新对拍完成后应继续替换相应研究假设。
- [同源原生日内属性对照](battle-reinforcement-and-join.md#2026-09-26到达日首次安排事件前会重算兵团有效属性)发现，旧战斗 entry 缓存到当天 schedule 入口已有 32/51、37/63 团的有效伤害或坚韧改变；静态写入链也位于 schedule 前。随后[两个独立暂停帧直接求值](battle-reinforcement-and-join.md#2026-09-26暂停帧直接查询可得到本案下一次-schedule-的有效属性)证明，原生 v2 对这 51/63 团直接计算的当前属性与下一 schedule `114/114` 零差，智能体实际消费的 v3 `base_inputs` 与 v2 又是精确同对象。因此**当前帧接战试算的属性输入可用**，无需把旧 entry 缓存当成唯一来源；但冻结该输入做未来每一日仍不精确，决策回执保留 `future_daily_effective_stat_refresh` 未量化风险，预测假设也保留对应标签。后续应在 modifier 来源闭合后实现未来逐日刷新，并以原生回执回归。
- [增援后战宽缓存的静态追踪](join-width-production-and-fire.md)证明原版可能在 join 时刷新历史 base/final width，随后主阶段从缓存读取 final width；当前研究核则在整次 trial 固定使用初始接战 `final_width`。预测回执现在显式带 `future_daily_combat_width_refresh_unmodeled` 假设与 `future_daily_combat_width_refresh` 未量化风险，**不改变已有有界模型的决策准入**。两个自然增援战例还没有 join 前后具体宽度值，下一步须按同一 CombatID/日更边界回读并校准转移。
- 2026-09-26 审计发现，禁用 phase events 的研究核总把 `commander_or_knight_death` 记为 false，聚合后为 `0%`；这只是**模型没有死亡转移**，不是原版人物无风险。接战预测适配器现把公开的死亡概率置为 `null`、状态标成 `unmodeled_phase_events`，准入回执把死亡阈值记为未应用并列入 `unquantified_risks`；其他可计算风险预算照常使用。下一步用[第 26 日原生击杀者抽签与写回](combat-phase-event-trace.md#2026-09-26-第-26-日骑士击杀者抽签实机闭合)及其他事件样本逐步替换该未知域，而不是把一次击杀见证外推成精确全程死亡率。
- 2026-09-26 后续实机核发现桥接层把外层人物 modifier 聚合器错传给内部集合读取器，造成部分反制、将领修正值静默归零。桥已改用原版聚合器入口 `0x21D3F20`；同源第 11 日回执中，将领掷骰界限 `0/10→2/9`，守方反制效率 `0→25000`，除此之外旧 v2 输入不变，且新 v3 与新 v2 全对象相同。[九项骑士效能与桥接勘误](battle-reinforcement-and-join.md#2026-09-26骑士效能九项修正逐项回读以及共用-modifier-读取器勘误)已给出 `24/24` 原版效能零差。智能体的同帧模型入口无需另起一套算法：使用修正后的原生桥查询 v3、按原有风险预算重新试算即可；旧输入哈希和旧胜率估计不适用于新输入。跨未来日的 modifier 更新仍标为未知。
- `COMBAT_ENTRY_EU_ACTIVATION_ENABLED=false` 仍表示**正式的胜率＋战役期望效用合同**未启用；本次启用的是独立、有风险预算和来源标记的 bounded-model 动作路径。二者状态不得混写。

## 2026-09-27：战中输入与未来增援的生产边界

现有 v3 `ongoing_combats` 仅枚举本次请求所选军队实际参与的 CombatID，不是地图上其他战斗的全局列表。生产 `forecast_fixed_contact` 现对所选军队已在战斗或该字段缺失返回 `active_combat_requires_resume_input` / typed mismatch；对另一支尚未接战的军队继续按上表进行战前条件估计。原因是现有 trial 固定从首次接战第 0 日起跑，不能用它回答正在进行的战斗“继续打还是撤退”。[战中输入审计](active-combat-forecast-input-gap-2026-09-27.md)列出 battle-control 已可读的真实阶段、逐团当前/软伤和战宽，以及仍需同帧冻结并接入 resumed kernel 的状态。这个防误用门不代表停止使用现有战前模型，也不把原生撤退合法性自动等同于撤退效用判断。

对增援，上文“有 route/ETA 后扩名册”只是必要条件，不是可以预测未来参战身份的充分条件。[未来路线输入审计](future-reinforcement-trial-input-boundary-2026-09-27.md)确认 assignment 只有 Province，路线读口的接战证明只覆盖一日，当前 CombatID 不保证到达日仍存在或仍是同一 side；到达日还需旧/新 entry 的状态与刷新后的两侧人数缓存。078 已在**实际 join 入口/返回**见到 base/final width `1645/1480 → 2467/2220`，所以较早的“尚无具体战宽值”描述只适用于当时的两份旧回放；首次 side0 出伤器读取的 width 仍未采到。这些差额只支持给定实测参战者的局部算术，不提升未来 `participant-update` 或无条件整场胜率的证据等级。

随后[083 同场独立回放](join-width-production-and-fire.md#083-同一次自然增援的三点实采)取得首次 side0 出伤的实际 `R8D=2220`，故上段“仍未采到”只描述 078 当时的证据状态。[现役战斗策略入口审计](active-combat-strategy-forecast-ingress-audit-2026-09-27.md)又修复一个生产漏口：拟移动军或目标守军已在战斗中时，通用首次接战入口即使看到缓存 v3，也不能把第 0 日模型当作现役续算。当前智能体仍以同帧 battle-control 控制撤退与限时推进；现役胜率的同帧操作数未齐，策略尚未调用 resumed kernel。战前固定参战者估计与上表风险预算继续实际使用，回执继续标示未来日增援、属性和人物风险的未量化边界。

[085 同钩子逐团回放](join-width-production-and-fire.md#085-双方-full-entry-同钩子实采与缓存差额)进一步把这一次已发生增援的双方缓存、旧 entry、incoming 13 团、新 entry 和战宽算术固化为[机器向量](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_join_full_entry_085.json)。它给**条件** participant-update 提供了可复算实例：旧团不变，新增军 starting 2570 人但当次 current 2560 人，双方原有缓存与 entry 残差在 join 返回后归零。通用策略仍不能从当前帧自动得知未来入场日与该日全部逐团状态，因此不把该向量当成未来整场胜率的无条件输入。085 的只读 battle-control 查询另暴露了 service 对新增 typed 续算 sibling 的白名单滞后；接口已同步容纳并按同帧父战斗校验，保留这一 RED 的原始回执。

[086 同暂停帧回放](active-combat-forecast-input-gap-2026-09-27.md#086-同暂停帧双查询实采)实证修复后的 battle-control 返回成功，也把现役输入边界量化：真实战宽 `1645/1480`，同帧 v3 的假定首次接战战宽 `1539/1385`。v3 的 `available` 指向可读的 precontact slice，不是对已开战 CombatID 续算的授权；现役 typed receipt 仍报告五个操作数域未齐。当前战前估计继续实际使用，现役继续由独立 battle-control 读口与撤退合法性控制。

## 静态验收

```text
tools\.venv\Scripts\python.exe -m pytest ck3_autonomous_player\tests\unit\test_general_battle_forecast.py ck3_autonomous_player\tests\unit\test_general_battle_strategy.py ck3_autonomous_player\tests\unit\test_prewar_battle_proxy.py ck3_autonomous_player\tests\unit\test_combat_provisional_defense_canary.py ck3_autonomous_player\tests\unit\test_war_entry_assessments_bridge.py -q
```

该验收证明代码接入、冻结实机输入计算和拒绝/放行分支，不声称已在当前实机完成一次新宣战或接战后的战果回读。
