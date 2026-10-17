# R196：100补给容量候选与受控多自然日准备窗口

本页将 R196 新实机输入和已存在的原生多日入口并列保存，供视频解释和智能体准备决策复用。**未执行换帅，未取得新容量应用、库存裁剪、零库存或饥饿物理扣兵正例。** 本页不增加 R05、动态镜头或 ABC 完成率。

来源机器 `machine_id: desktop-3fevhd2-1c74096080`。R196 原观察为 2026-10-17 02:16–02:17 UTC、date raw53148192、actor31254、Army/CArmy18、PID36072、generation1、episode `native-31254-2bac783421ef`；原 source611bc985ae95f477dd7314df11f8602cd1e595f3/a33。2026-10-17 04:03 UTC 离线整理时主树为4f3b6c4f4c0a359b4133789675a7a02514b6ef58，不将该新源码视为原场运行版本。目标 CK3 1.20.0.4/build25734779，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；其他机器只可复用代码/来源合同，需重新核实际安装、权限和实机。

## R196 实际候选：不是从评分猜容量

[R01 原始便携包](episode04-r196-r01-ready-t0-12004.md)已有唯一 Commander 原件和完整 Driver；本页只引用其 [source-index](evidence/episode04-r196-r01-ready-t0-12004/source-index.json)和[本页小索引](evidence/episode04-r196-cap100-and-multiday-preparation-12004/source-index.json)，不再复制或重读11MB Driver。Commander 原件92,806B，SHA `0930493bc12cca4df3318d6bcd81349a6a7ec8beadd0baf60e4c823f8cdc7e1c`；实际语义为 `/body/army_commander_candidates`，不是 SDK 文本副本。

| 实际对象 | 原生资格与条件容量 |
| --- | --- |
| 当前统帅31254 | observed current；loaded FULL10000000、additive0、multiplier200000，条件容量30000000/Q100000。当前Army stock/cap300/300来自同帧R01输入。 |
| 32236、34975、37244、37702、35899、34232、36445、33946、45458、45464 | **10人**的 available、final_eligibility_observable、can_assign 均true；各有完整 available `conditional_supply_capacity_v1`，loaded FULL10000000、additive0、multiplier0、条件容量10000000/Q100000，即100。 |
| 34973 | 当场可任命，但 multiplier200000、条件容量300，不能用来缩容量。 |
| 50631、50632 | 条件容量100，但 can_assign=false，不能据容量选为合法任命。 |

34232 是这10名合法低容量候选中实际 `native_ai_base_quality` 最高者27；其 `generic_advantage_points=27`、`siege_phase_time_modifier_raw=-10000` 独立保留。这个优先级只用于缩容量候选之间的取舍，不证明战争胜率或补给消耗率更优。没有根据角色名字或熟悉程度选人。

完整 raw 字段是实际读取的十进制 signed64 字符串，包括明确的`"0"`；不是将 missing modifier填0。容量 provenance 为getter2C53BF0、loaded FULL5C68C70、ordinal467/468；[条件容量合同](army-commander-conditional-supply-capacity-12004.md)以真实候选 aggregate解释公式，并固定 `assignment_applied=false`、`candidate_aggregate_unchanged_after_assignment`。原资料当时“未生产部署”的状态保留；本页记录的是随后R196已经实际出现的候选字段，不倒改历史。

候选 payload **没有供给消耗修正 M1A9**。容量 ordinal468、AI评分、优势和围城修正都不能补这个缺失，也不能证明换帅后的rate仍−5或更快。2619原生 resupply eligible/gain20是恢复补给候选；2645的负率来源仍须保持其原条件与实际到站读回边界，不把选点预览冒充抵达后的真实消耗。

## 下一场正常动作与新的准备 T0

既有[typed MCP](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py#L3017)先 fresh查询 `ck3_query_army_commander_candidates_v1(army_id=18, expected_revision=<当次PUBLIC>)`，重新核34232的可任命资格和条件容量。若仍成立，既有动作 `ck3_assign_army_commander_v1(army_id=18, commander_character_id=34232, expected_revision=<最新PUBLIC>)` 仅提交一次。底层 canonical step 为 `assign-army-commander-v1-army-18-to-character-34232`；18/34232是该场真实完整handle，不是历史人物ID或数组下标。[assignment合同](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_commander_assignment.py)分别保留提交与独立 current commander后验。

之后独立 typed commander须实际显示34232，同日期/Army/CArmy/owner不变；独立完整Army row须给实际 capacity/current stock/rate。**容量getter没有库存clamp；任命ACK或条件容量100不证明库存立即300→100。** 只有随后真实原生updater的ADD/floor/cap及其实际前后值能支持裁剪事实。身份、率或容量变化时以新值重估。

R197本次额度最多32自然日，只能用于已有县P/补员任务后的有限正常准备和一次更新机会观察；不足或未见更新就闭场pending，不延长。正常换帅后的准备状态必须另作普通checkpoint并绑定真实身份/精确save SHA，才可成为后续R05新T0；原R191 S0继续保持原身份，不改名、不覆盖。机器本地操作 wrapper不是跨机器运行库，本页不要求复刻其绝对路径。

## 已有原生多日入口，不等于供给结算日预测

当前生产 parser已接受：

```text
ck3_execute_step(step="research-arm-tactical-daily-sentinel-v1-<start>-to-<start+24*N>-speed-3-mode-decision-a-1-<FullArmyID>", expected_revision=<fresh PUBLIC>)
```

这是真实既有step，不是新增CLI或`days`参数。Python[canonical parser](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py#L28471)及C++[parser/arm/evaluator](../../ck3_autonomous_player/native_bridge/src/tactical_daily_sentinel_v1.cpp#L508)允许正signed32 start/target、target>start、差值为24倍数；没有只限1日的ABI门槛。先设置并读回speed，再在paused场景Arm并核实际generation/dates/watch，最后Resume一次。2026-10-17离线对隔离的既有Python parser执行1/21/28日literal，均接受；非24倍数拒绝。它只授参数准入，不是native arm或实机多日资格，本页未重跑该检查。

哨兵每个**真实自然日**在原生final-stage后检查：日期序列、world指针、watched Army双向身份、位置、目标、战斗/撤退变化、已监视战斗变化及native pause；到target或发生触发时暂停。它**不监测stock阈值、统帅容量、玩家角色变化或新接近敌军**。每个21/28日粗窗口前后仍需fresh actor/episode/generation、Army/CArmy/owner、stock/cap/rate、route和threat闭包。异常/弹窗/未知动作不重复Arm；原生事件处理和真实后验由现场owner续行。

远离低库存可在实际samplers OFF回读后作粗窗口，减少逐日SDK/full-history导出；接近临界区再显式启用所需采样、读回完成并取独立fences，改exact+24日取得首零当场stock及physical writer。OFF区间没有完整历史信用，若意外归零，不能补造首次跨阈值因果。[R05严格证据合同](episode04-r05-next-starvation-12004.md)和[零库存来源](episode04-zero-supply-loss-source-12004.md)继续适用。

条件预算示例：若任命后**实际**cap100、stock仍300、rate固定−5，首次成功updater先算295再cap100；后20次成功更新才到0，合计21次，而旧cap300的相同率情景需60次。若stock已实际为100则20次。只有桶稳定、每30自然日恰一次且admission持续允许时，21次才给最多630日的条件情景；这不是21天，不是未来保证。未来独立R05可提出660日硬上限、每不超过112日复核的有限提案，但必须由Root另行adopt容量/时限，不能挪进R197的32日额度。rate、capacity、桶、身份或战局改变即重新估算；getter名字中的monthly不能决定结算天。

此页新增实机、换帅、normal save、R05 positive、clean span与人工签核均0。小型知识和索引按[统一存储策略](../storage-retention-policy.md)复核；未续期保存大原件。
