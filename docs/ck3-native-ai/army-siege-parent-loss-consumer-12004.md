# 同回调 supply / 围城或劫掠 writer 消费：1.20.0.4

2026-10-15，`machine_id=desktop-3fevhd2-1c74096080`。审阅基线是
`1463bd9b4b89612d283dd45ac4ec9efbf22f048d` 和外置 parent-join 候选；游戏来源仍绑定
1.20.0.4 / Steam25734779 / EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
本包没有重新读取EXE、触及SDK/游戏/桌面或重新构建。

## 生产接线审阅结论

候选可最小解锁**真实自然writer与其当次callback的归属，以及writer时库存**。未发现需要修改的生产接线问题。
审阅依据是两个实际生产wrapper的差异、共享TLS上下文、strict contract、keyed summary和已有ON/OFF compiled-wire回执。
这不是新的实机资格，也不把typed-original fixture当作原游戏调用。

下列行号针对 `high-parallel-starvation-a01/parent-join-a01/candidate/ck3_autonomous_player/` 的冻结候选：

| 文件/行 | 实际检查结果 |
| --- | --- |
| `native_bridge/src/ck3_12004_actual_supply_callback_journal.cpp:344–358` | 从typed callback真实RCX receiver读双FullID，构造scope；未缓存stock到TLS。 |
| 同文件 `361–376` | 唯一`original(army,date)`保留于363；正常返回后独立读取identity/values并publish，scope寿命覆盖同步原调用。 |
| `native_bridge/src/ck3_12004_actual_loss_writer_journal.cpp:512–520` | 每次writer entry调用context捕获；guarded reader读的是scope实际CArmy，未把ArRg误作CArmy。 |
| 同文件 `532–548` | 唯一`original(regiment,request_raw)`在534；后置physical读取和publish仍沿原路径，不借query执行。 |
| `native_bridge/include/xar_bridge/ck3_12004_supply_parent_join_context.hpp:18–40` | 一个Runtime image内共享atomic token和thread-local current；token耗尽不wrap重用。 |
| 同文件 `45–74` | scope保存previous，nested即使identity partial也遮蔽outer；析构恢复previous，没有跨线程继承。 |
| 同文件 `84–118` | writer entry重新读receiver `+124/+10/+180`；双FullID与entry一致才置identity match；stock失败保留null和flag，不回退before/after。 |
| `native_bridge/include/xar_bridge/army_actual_supply_parent_join_v1.hpp:10–31,44–86` | wire只发owned token/thread/depth/双ID/stock及明确receiver basis，不导出receiver裸指针。 |
| `native_bridge/cmake/actual_supply_callback_observations_12004.cmake:1–7` | 新选项默认OFF；ON只由下一coherent runtime构建选择，当前运行DLL不能因此获得该字段。 |
| `src/xar_autoplayer/bridge/army_actual_supply_parent_join_summary.py:47–105` | 独立callback/loss fences；token唯一匹配、整份invocation/thread/depth/route相等、双ID/实际date/stock读回；不靠两个journal sequence或同日巧合连接。 |

callback entry stock、callback return stock和writer stock是三个实际时点，不能相互替代。
同token的多个writer保留各自stock、physical debit与caller；residual仍不因有parent就变成supply或siege。
direct `24E35FF` 和 `24E377C` 分别支持source supply preferred、combined siege/raid preferred。

真实core仍在 `2A9A8E2`返回，较后 `2A9AB46`才调用loss callback；因此core七槽delta不能补后续writer账本。
新join直接进入现有callback/writer seam，覆盖的正是这个较后边界，不需要改core采集或借core推算stock。

## R03共同消费器

[army_siege_parent_loss_evidence_12004.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_siege_parent_loss_evidence_12004.py)
组合既有physical判定与新keyed summary：

```python
result = evaluate_siege_parent_loss_evidence_12004(
    normalized_army_row,
    game_version=bound_game_version,
    executable_sha256=bound_exe_sha256,
    callback_after_sequence=callback_baseline_latest,
    loss_after_sequence=writer_baseline_latest,
    date_raw_min_exclusive=actual_before_date,
    date_raw_max_inclusive=actual_after_date,
    previously_reported_sequences=used_writer_sequences_in_this_journal,
)
```

只接受已安装两journal、新鲜完整positive physical event、唯一parent join、direct combined stage和真实daily callback return `2A9AB4B`。
返回每笔事件的token、callback sequence、writer sequence、writer时stock，以及同token的source supply preferred兄弟。
不同callback的supply、同日但无token、跨thread、partial physical、residual或其它callback caller都不升级为本R03阶段证据。

`same_callback_combined_stage_positive_observed=true` 只表示该项原生事实。
`siege_only_causal_attribution_ready`、`residual_cause_attribution_ready`和`complete_interval_loss_total_ready`仍为false。
R03正式画面继续独立核真实siege association、raid=false、该窗库存/loaded state、完整稳定roster、无重组/战斗/强攻等上下文，
把围城解释标为来源＋上下文支持；不能用此consumer制造当前未采到的predicate或clean span。

调用者必须绑定实际进程/创建时间、connection generation、episode和journal lifetime；两个journal各保存自己的baseline fence。
新字段默认OFF时是正常的缺失，不得把old-wire兼容或installed=true当成join已启用。
下一正常构建显式ON后，以实际full-history query中非空context和实际自然事件为准，不hotpatch当前进程。

## 资格范围

已复核的上游小型native回执来自同机
`C:/ck3-war-episode04-research-20261004-a01/e04-parent-join-20261015-a02/RESULT.actual.json`，
实际时间15:10:36–15:12:24 UTC；ON/OFF各3TU窄构建、SYSTEM实际verified、fixture返回0，typed originals为4 callback/10 writer。
ON wire包含nested恢复、foreign-thread无parent、stock999999/1000000/500000及读失败/换generation。
没有重新运行producer或上游7tests，也没有重复R03原9tests。

本包只运行新R03消费者的6个synthetic用例，并将上游保存的ON/OFF wire各交给新消费者一次。
fixture observer未安装且caller不在game RVA，真实结果必须拒绝R03现场ready。
用例/样本消费回执和source pins在外置`high-parallel-siege-a02/`，以实际回执为准；新增live证据为0。

本包依赖先合入[物理扣兵共同消费者](episode04-siege-loss-12004.md)及[parent join候选](army-actual-supply-parent-join-observation-12004.md)。
主树保持冻结；外置包≤8MiB，共用Root已接受512MiB池，复核截止`2026-10-16T07:45:01.597Z`，没有延期。


## 2026-10-16：原预算栈leaf使单笔siege-only原因可准入

上述旧wire的原因unknown保持原历史边界。下一正常构建默认OFF的可选`siege_budget_at_writer_v1`从真实writer incoming return slot复制原siege/combined及独立supply预算；来源、偏移与actual1999B新源字节见[原预算栈专题](army-siege-budget-writer-stack-12004.md)。同callback/direct preferred/positive physical均合格后，原siege>0且derived raid=0才进入`siege_only_positive_writer_events`；旧wire、partial和mixed raid仍不授此原因。该变化只授单笔writer的来源原因，完整区间与residual仍不ready；当前a06/R0175未据此取得新live资格。
