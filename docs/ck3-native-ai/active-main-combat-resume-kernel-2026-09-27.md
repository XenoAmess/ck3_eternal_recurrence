# 现役主战阶段续算内核：静态最小增量（2026-09-27）

## 已实现的边界

[source-confirmed] `ck3_autonomous_player/src/xar_autoplayer/simulation/research_envelope.py` 新增 `ActiveMainResumeState` 和独立的 `ActiveMainResumeResearchKernel`。它仅接受标记为 `observed_active_combat_resume_fixed_future_participants`、声明 `CombatID` 和 capture snapshot/revision/date 的**主战阶段**输入；`explicit_hypothetical_fixed_at_contact_no_reinforcements` 明确被拒绝。这层静态校验不能独自证明 `CombatID` 与操作数真的来自同一 application-main，证明必须由未来原生读取器提供。内核从给定战斗 entry 的 `current_raw/soft_casualties_raw`、有效攻击/坚韧、当前战宽、roll cadence/当前 roll、非 roll 优势开始推进；输出的 `battle_days` 与硬伤只计快照**之后**，而撤退门仍使用战斗已历经的总天数。阶段事件关闭、未来增援和逐日刷新未建模，`fidelity_gate=False`，独立 build 名称也与战前研究模型不同。

这只是模型内核和 typed 输入的静态增量。**目前没有生产原生读取器生成这种输入，游玩智能体没有调用该续算核，也没有现役 CombatID 胜率结论。**测试里把战前冻结夹具的 participant policy 显式改成现役值，仅用于验证入口拒绝规则、初态使用、未来日数/伤亡和当前有效伤害覆盖；这个合成状态不是实机同帧证据，不能据此提高智能体能力等级。

## 同一 application-main 原生输入仍缺什么

下一读口必须在同一暂停世界帧、同一 native application-main 采样并双采样稳定后，一次返回下列完整字段；其中任何必需字段缺失均应 `unavailable`，不能填零：

| 域 | 续算所需事实 | 当前状态 |
| --- | --- | --- |
| 绑定 | 原版 build/EXE、full-generation `CombatID`、subject CUnit/CArmy、snapshot/native/public revision、episode/date/connection generation、查询线程与完整来源 SHA | battle-control 和 v3 分别读；没有同一个读口把它们原子绑定。 |
| 阵营/参战者 | CombatID 的实际 side0/side1、coalition、逐 army/entry 的有序完整 census、当前选中将领及身份 | battle-control 有大量真实 entry；v3 是请求者假定参战名单，不能代替真实 combat roster。 |
| 续算初态 | phase、phase day、已经历天数、roll cadence、两侧当前 roll、每个 entry 的当前 fighting/soft/hard Q100000、当前缓存战宽 | battle-control 分散提供这些值；缺组合输入和逐项可用性校验。硬伤 unavailable 时必须保留而非置零。 |
| 当日算子 | 两侧非 roll 优势、当前选中将领的后续 roll bounds、逐 entry 当前有效 damage/toughness/pursuit/screen、反制 class/stack/context、各伤亡修正、原接战地形/渡河/holding | v3 冻结的初次接战 stats/优势不能无条件用于现役下一日；需要同帧和日界刷新证据。 |
| 变化/决策 | 后续增援/撤军、动态 phase effects、伤亡写回、当前 owner 撤退合法性与安全目标 | 本核固定未来参战者、关闭事件，不能据它单独下达继续或撤退策略。 |

当前 `ActiveMainResumeState` 只支持 `CombatPhase.MAIN`，不把机动期或追击期伪装成主战阶段。它使用 `FrozenCombatSimulationInput` 承载静态军团、将领和反制操作数，因此未来原生 adapter 必须从**同帧现役 combat**构造该操作数，并重新 hash 绑定完整输入；当前 v3 解析器与其历史 hash 不能直接复用。roll/优势、当前有效攻击或战宽读不到时不得退回战前值。首个生产验收应固定一个暂停 CombatID，配对读口与下一日 native 结果，再接入 continue-vs-retreat 预算和已验证的撤退行动流程。

## 冻结证据与验收

已有局部数值对拍：[`episode01_messina_paired_day05_r14.json`](../../ck3_autonomous_player/tests/fixtures/combat/episode01_messina_paired_day05_r14.json) 的原始 SHA-256 为 `08d43ae1821538ae23f5bfc83bc724c74b102a12fdba8b6e1c30a8e11eb88126`，原版 CK3 `1.19.0.6`、episode 1 第 5 日；夹具记录 same-run v3 class/context 与 native pre-fire fighting Q100000、刷新后的 damage，原始 v3/trace response SHA 分别为 `9446F4274DED45F68A9D1DB59AB2BACED4043D4C24776D4AEAA0614A61A185F1` 与 `6B72365D4B3BD2B8ED6E54F7E0ECF8F924352F9C615A71E999FAEBF47BA2F611`。既有 `test_paired_native_day_five_r14_uses_fighting_men_and_refreshed_damage` 只校验这一天的 R14 出伤部分；夹具仍将 `base_inputs.participant_policy` 标为假定首次接战，未携完整续算 roll/phase/优势，故**不能用它宣称完整一天状态转换或整场胜率对拍**。

本次新测试 `test_active_combat_resume_kernel.py` 用合成续算状态验证：战前政策/跨快照/非主阶段/缺失有效伤害被拒；空侧在下一主战 tick 的伤亡计算前结算；每一步只增加未来天数，历史软伤不重复计作硬伤；把当前有效攻击置零会把新增硬伤归零。配合受影响的既有测试，`46 passed, 19 subtests passed`，`git diff --check` 通过。测试解释器为显式主工作区 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`（Python 3.14.7、pytest 9.1.1），从本 worktree 的 `ck3_autonomous_player/src` 运行；隔离 worktree 没有相对 venv，未静默回落系统 Python。Steam 离线画面新鲜度门当前为 RED，本轮未启动 CK3。
