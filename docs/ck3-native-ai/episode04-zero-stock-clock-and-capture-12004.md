# R05 零库存扣兵：时钟、顺序与最小自然观察

源码结论：**库存0并不单独触发扣兵；实际供给桶机会、updater准入、更新后的损耗分量和整数预算必须依次经过。** 最小观察可以是一笔自然 callback 中的零库存 supply writer 和完整物理扣兵，无需等待整月或整个30相位周期。

本包仅作离线源码组合。`machine_id: desktop-3fevhd2-1c74096080`，实际读取时间见外置 `DELIVERY.json`；读取源树 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。目标为 CK3 `1.20.0.4` / build `25734779` / EXE SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。没有本轮实机、安装状态或新扣兵事实。历史文档的机器状态不外推；本包的机器身份来自当次 `tools/ck3_live_run_id.py machine`。

## 已闭合的最小触发链

实际 `.4` dispatcher `2A9A570..2A9AB73`（1539B，已持 instruction-byte SHA `60520f156b0b4c3a9f0846d67f322f620ac0ed9e946052e7cf328f4f2a4ca4a7`）读取 **GameState+9C stored D**，按 `uint32(D)%30` 选原始 CArmy* bucket。桶内每个8B指针 occurrence 都调用 `24E3410`，直接返回地址 `2A9AB4B`；重复指针保留原顺序，不是一次预算的复制。[实际调度与 late stage](native71-army-post-date-callback-stage-12004.md)已经闭合这些事实。

当前查询中的 `army_update_clock_v1.observed_army_bucket_phase` 是第一次 pointer-match，不能代表全部重复或多桶 membership。精确下一机会使用同一行 `future_daily_supply_schedule_inputs_v1` 的30个原始相位/positions，和 `source_derived_next_daily_supply_frame_inputs_v1`，不由 ArmyID 取模。

下一对日期/D由已有 `.4`155B source 闭合并生产：`nextRaw=signed32(uint32(currentRaw)+24)`，`nextD=trunc0(signed32(uint32(nextRaw)-43800000)/24)`，下一相位 `uint32(nextD)%30`。**不能把当前 stored D 直接加1。** 当前D和当前日期是分别读取的字段；既有 Service `same_input_conditional_future_daily_supply_schedule_v1` 已连接同query source pair 与 all30 bucket。[已有 source pair](army-next-admitted-supply-tick-input-12004.md)及生产代码保留这一独立性。

进入 updater 后按顺序拒绝 Unit170=3、native combat、native gathering、Army5C非0。剩余年龄条件是：

```text
trunc0(signed32(passedDate.low32 - CArmy190.low32) / 24) > loaded_signed_grace
```

等于宽限天数仍拒绝；负年龄保留有符号截断。**+190是 gathering 完成锚点，+188是成功供给更新时间。** updater 不写190，不检查距188是否又过30天。重复 callback 可能各自成功；不能用一次时间戳变化反推只有一个成功调用。[已有 updater 写入投影](army-source-derived-next-updater-writes-12004.md)已经按该实际顺序消费这些字段。

实际 `.4` gathering/due 阶段 `2A9AF20` 位于同一 dispatcher 的供给桶之前。due record 减Army5C至0时，会写新的完整GameState日期到Army190。因此一个推进日前查得的“年龄足够”可能被**本tick早先 gathering 完成**改变；当前查询不能补成未来 callback 的准入值。完整实际条件见 [actual4 gathering/due](native71-army-gathering-due-stage-12004.md)，不是从旧 `.3` 地址平移所得。

## 同 tick 与同 callback 的顺序

| 边界 | 已证原生顺序 / 能说的事实 |
|---|---|
| Army manager之前 | Unit NewDate可以移动、到达、改变province/fleet；当前 query 只是此前输入。 |
| Army manager桶之前 | cleanup → gathering/due → saved-bit2 regular refill → assault → late Army roster/事件 → stored-D bucket。月首补员不是供给桶时钟。 |
| `24E4D00` | updater先写Army22=1，再检查准入；该字节不是成功证据。 |
| `24E4E07`，成功准入 | 完整passedDate64写Army188，先于 rate 和库存ADD。 |
| `24E4E60..4EAF` | 当前原生 rate求值 → Army180一次signed64 ADD → floor0/cap → 返回ALtrue；整月rate不除30、不乘已过天数。 |
| `24E3437/343E` | callback消费AL；true才求更新后库存的整数供给预算，false使用预算0。 |
| return `24E35FF`；residual outer `24E3638`, flags2 | supply preferred及supply residual执行真实兵力writer。 |
| return `24E377C`；residual outer `24E37B3`, flags0 | 后续独立siege/raid合并分量；相同callback/token不把它变成供给分量。 |
| physical writer内部 | 完整唯一物理槽before/after才证明实际扣兵；request、ArRg cache或Army净兵数均不能替代。 |

表中库存0→0、损耗5%以及物理整数截断，复用R05 a04已经逐体闭合的 [零库存源码](episode04-zero-supply-loss-source-12004.md)，本轮没有重读这些旧函数。Stock0+负rate floor回0仍可返回成功并有正预算；stock0+正rate可能先补到无损耗状态。库存不变不能证明updater没执行，callback入口0不能证明writer时仍0。

需要拍到正扣兵，还要实际供给分量未被fleet/commander等抑制、整数预算正、writer实际准入且发生完整物理扣除。按默认且实际加载的5%和普通非负算术，eligible19预算0、20预算1只是预算层例子；不保证任意团writer最终扣1。使用现有query的实际加载表/资格/count，不把stock常量或总Army人数替代它们。

## Root 可直接执行的 phased recipe

此步骤用于Root下一**正常a07** scene；不接管R0176，不要求新增detour、native getter或证据协议。沿已有scene归档/sentinel/视频流程执行，每次参数用当次真实revision、public ArmyID，不照抄历史ID。

1. **先选当前自然主体。** `ck3_take_snapshot()`取本session暂停帧；`ck3_get_capabilities()`确认 `life-advance-one-day` composite及既有Army查询。`ck3_query_army_strengths(army_ids=[actualPublicID], expected_revision=freshRevision, profile="observed_history_full_v1")`读同帧全历史。保存实际public/native FullID、PID/连接代、日期、stock/rate/cap、190/grace、准入、原始roster/物理槽和observer安装状态。自然库存0优先；无0时保留负rate的真实候选，等待其实际库存成为0，不能导入或写库存。未安装/缺共同token字段即如实未知，不以query假造观测。
2. **定位最近单日机会。** 既有Service字段 `same_input_conditional_future_daily_supply_schedule_v1` 给下一source pair及selected phase的实际positions；`source_derived_next_updater_writes_v1.next_admission`给该日期的条件准入。新只读 `project_zero_stock_next_callback_candidate_12004(row)`仅将二者与当前stock0组合：`True`是值得拍摄的**条件窗口**。其他29个桶不可读不抹掉已完整的selected phase；selected phase不可读则unknown。若下一桶无主体，下一日不能按冻结桶声称有机会；在Root已批准的推进上限内逐日独立读回并重新选择，不自动增设30/61天预算。
3. **保持可见的一个自然边界。** 选stationary、无gathering/combat、无同日入县/重新编组的真实主体，可减少早先阶段干扰。开始前取两个journal各自的 `latest_sequence` fence；保留full-history及实际GUI供给/兵力画面。用 `ck3_execute_step(step="life-advance-one-day", expected_revision=freshRevision)`推进一次。该现有composite使用exact-one-day/speed1；若当前能力不提供或sentinel停在弹窗/局面变化，按实际回执处理，不换成长推进强行越过。
4. **独立读回业务。** 再 `ck3_take_snapshot()`，再同ID full-history Army query。验证实际低32日期推进+24、同进程/episode/连接代及双FullID，保留实际D/phase、190、188、roster/位置变化。两journal用各自fence筛新事件；即使callback库存0→0、supply_drain_raw=0也必须保留。行动ACK不替代此读回。
5. **先拿最小正证据。** 现有 `join_actual_supply_parent_writer_observations_v1`要求复制的同callback token/thread/depth/双ID/date和writer时Army180。新 `select_actual_zero_stock_supply_preferred_12004`只认 actual daily return2A9AB4B + direct supply return24E35FF + **stock_at_writer_entry_raw精确等于0** + 完整唯一物理槽debit>0。命中即可结束本R05拍摄，不必等一个完整周期。它故意不处理residual正例；原a04 classifier可另按outer3638/flags2识别supply residual，不能按inner2A958E8、同日或相同token猜原因。county2630/flags0、combined377C及37B3/flags0单列。
6. **若没有正例，保留真实缺口。** callback未保留、admission未观察、stock变正、预算/取整为0、writer跳过或capture缺失各自保留；不写“零库存不扣兵”。a07可选的R03 combined budget leaf仅在真实377C writer存在时观测 original_supply_budget_soldiers；该leaf缺失/无mixed writer时，不能补出AL或供给预算0。查询后可重新选下一个真正候选，仍受Root原推进边界约束。

旧 `tools/run_ck3_native_army_update_clock.py` 实际仍输出 `exact_12003` 并嵌入 `.3`日历表。本包没有运行它，也不把它作为 `.4`当次生产证据；使用上列现成 `.4`同query source pair与Service projection即可。

## 单笔、周期、视频与智能体

单笔完整正例可说：“这次自然供给结算中，实际库存为0时，供给writer从这些已识别的物理槽扣除了X人。” source可另解释库存先更新、再计算供给损耗，0没有额外一档。**不能说每一天都扣X、整月死亡X、所有损失都来自饥饿，或0比0至10之间另加惩罚。** 5%只在实际加载表/commander分量条件满足时适用，最终整数扣除还有分配/截断。

30个桶是时钟结构，不是一次观测完成的30天业务周期。即使普通非溢出日段的连续30个phase各经过一次，也需独立证明原桶membership、全部repeats、各次准入/stock/rate/物理写与history覆盖，才能谈完整该区间；月首regular refill还可能在同日抵消净兵数。新helper始终保留 `complete_cycle_observed=false`、`complete_interval_loss_total_ready=false`。一个event的positive可用，一个整月总数仍未知，两者不矛盾。

智能体可以用条件next opportunity及严格grace决定**何时再次查询/拍摄**，并用精确零库存physical正例记录已经发生的一笔实际损耗。不能把候选True或当前attrition当预计死亡数，也不因无writer就选择长期“零库存安全”策略。本增量不改planner的出兵/行军策略，不执行任何动作。
