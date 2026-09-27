# 098 原版日界反制输出与增援后兵团交叉核验

本页是 CK3 **1.19.0.6** 的单次原版只读交叉核验。EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，注入 DLL SHA-256 为 `ABEE0A5AD16347A9EA2F10454D111A769CEDB84E343010792619CBB27A4CD858`。原始 attempt 位于 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-098`；本次分析没有再次启动 CK3。三份关键回执 `c098-before-control.json`、`c098-trace-finish.json`、`c098-after-control.json` 的 SHA-256 依次是 `2244E1144D7F5708B19BD2DE50311BCCA38481EFD0BC98165FC48AEA8C0602AA`、`6B158A07A6071D058DE6F3E8994CA0065F09B2311EF79004EB1DDD445B1B8198`、`236E67C10CFABBABEDE2822A40074458ABF8EFCA019CE54A3C88CC669EA217EC`。

可重跑的只读 [投影器](../../tools/project_active_counter_output_098.py) 先核对上述原始字节、冻结的 EXE 哈希声明及 DLL 实际字节、同一 full-generation CombatID `16777218`、从 `53146488` 到 `53146512` 的一天及 `phase_day 7→8`，再把 `runtime_join_full_entries` 的日界条目按 regiment ID、native army ID、owner 与 after-control 反制 census 对齐。EXE 哈希来自冻结清单，本脚本没有再次读取 EXE 本体。逐兵团的 `before_current_raw`、增援后且开火前的 `post_join_current_raw`、日界开火后的 `post_tick_current_raw`，以及 owner/class，保存在[机器夹具](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_counter_output_098_projection.json)。已有兵团的 class、stack、target 元数据在前后 census 中逐项一致；新兵团的类别只从后帧 census 取得，不能声称在增援前可读。

| 战斗侧 | 主参与者 owner | 增援前→增援后 MAA 条目 | 反制 context | 原生非满额 retention 类别 | 用增援后条目重算 |
| --- | ---: | ---: | ---: | --- | --- |
| side 0，对方 | 31549 | 18→24 | 125000/100000 | class 8 = 10000/100000；其余 12 类 = 100000/100000 | 13/13 完全一致 |
| side 1，玩家 | 29829 | 14→14 | 100000/100000 | class 0、1 = 10000/100000；其余 11 类 = 100000/100000 | 13/13 完全一致 |

日界加入 side 0 的 Army `22` 带来 6 个新 MAA regiment ID：`176,177,179,180,181,182`；父帧还显示该侧 levy 条目 `9→16`。原生 hook 返回 `countered_entry_count=24/14`、反向 `countering_entry_count=14/24`，与**加入之后**两侧 MAA census 一致。`failure_flags=0`、`pair_complete=true`、两侧 `class_count=13`。投影器用当前 `combat_input.dynamic_counter_retention_by_class_raw` 的定点计算顺序，对增援后 full-entry 的 fighting men、后帧可核对的 class/stack/target 元数据与本次原生 context 重算，所得两侧向量逐项吻合。对于未增援的旧条目，元数据的前后稳定性已逐项检查。

**可明确指出的不符：**若错误地用增援前兵团当前量计算，同一个模型给玩家 side 1 的 class 1 retention `54257/100000`，而原生该日是 `10000/100000`；其余类在这个样本可能恰好相同。因此这次直接否定“冻结前一帧反制向量可代表增援后的日界输出”。用 after-control 的开火后当前量重算，也恰好得到同一向量；多个类别达到 `10000` 下限，向量一致本身无法唯一反推引擎在哪一个瞬间读取每项当前兵力。增援先于本次 main-phase fire 的顺序另有 join boundary 与 `24/14` hook 条目数作证。

此结果只闭合**这一天、这一个 CombatID、这份原生 hook 的两侧 class retention 输出对照**。它没有验证整个 `post_counter_attack` 到出伤、软硬伤与终局写回的逐兵团全链：回执明示 `full_mutable_transition_bundle_complete=false`、`original_trace_ready=false`。`active_combat_resume_inputs_v1` 仍列 `active_regiment_counter_class_stack_context`、下一日非骰子优势、骑士参与与动态 entry 转换为缺域；单日 hook 能观察实际向量，不等于智能体在未来每一天都能先验取得全部变化，也不产生整场胜率。

本机复核命令：`D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe tools\project_active_counter_output_098.py --check`。`--check` 会校验原始 SHA 和入库 fixture 的精确投影字节；原始 attempt 不在仓库，其他机器要先取得相同哈希的原始回执，不能仅凭 fixture 冒充原始实机回读。

## 研究模拟器的增援后动态反制回归

后续[聚焦测试](../../ck3_autonomous_player/tests/unit/test_active_counter_output_098_envelope.py)直接从上述哈希绑定夹具重建同一 24/14 MAA 身份、owner、class、stack、target 和增援前后 fighting men；它故意把 `FrozenCombatSimulationInput.counter_resolutions` 内的玩家 class 1 留在旧值 `54257`。调用真实 `dynamic_counter_retention_by_class_raw` 后，增援前仍为 `54257`，增援后为原生 `10000`，两侧各 13 类都与 098 hook 一致。另以**明确标成 test-only 的合成完整输入**调用 `ActiveMainResumeResearchKernel.simulate_trial` 一天，并捕获该内核实际传入动态反制计算的向量；玩家 class 1 仍是 `10000`。这能防止未来把静态旧向量误用进这条研究路径。

真实 098 回执的 `active_combat_resume_inputs_v1` 仍是 `unavailable`，且缺未来动态 entry 转换等域。测试中为执行研究内核而手工设置的 `input_observation_ready=true` **不是原版观察结论**；目前没有把 join 后 24 条兵团、此日原生 class 向量自动映射成可用于真实游玩预测的完整 `ActiveMainResumeState`。`PhaseEventsDisabledResearchKernel` 的首次接战输入还假定未来参战者固定，不模拟这次真实的外部增援；测试通过不提高整场胜率的原生对拍等级。
