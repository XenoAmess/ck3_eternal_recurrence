# M1：已有cash/root DTO到月度输入的纯接线

新增[`campaign_score_existing_inputs_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py)，只把**已经取得且与当前MET同帧**的原生DTO映射为评分字段或诊断。没有新增查询、历史搜索、缓存、通用身份builder或运行树修改；当前新局尚未接入，不能因此宣称月度E/M/L/D已经可采。

本包基于`063531c4`已有SDK合同。执行`machine_id: xenoamess-full-tower-eb9d2c1186`，由本次`tools/ck3_live_run_id.py machine`读回，观察时间`2026-10-19T03:52:53.981704+00:00`。来源、8项软件验证和SHA见[小回执](evidence/g2-m1-existing-month-inputs-2026-10-19.json)。没有读取活Driver、大SAVE、桌面或游戏，没有改变runtime COW、service、cadence或Native。

## 已有合同与唯一必要来源缺口

cash公开DTO已有`queried_snapshot_id/revision/native_revision`、当前actor/date、exact build、v2月流量标记及actor-global军费范围，但没有独立保留Game/generation来源。纯叶因此要求原普通查询当时**已有的**`xar.ck3.planning-source-frame/v1`，直接沿用service现有合同中的snapshot/public/native/date/actor/episode/bridge_pid/connection_generation，逐项与当前snapshot比对；没有创造另一套身份结构。

没有原planning frame时，即使cash字段齐全也返回`existing_planning_source_frame_missing`，四项评分值都是unknown/null。不能在MET时给旧包现造新frame。帧绑定不同、钱包不符、v2标记缺失、错误net算术、费用scope不符或build未知均返回typed缺口，不能用AUTO前态覆盖after-MET。此处复用现有`normalize_war_cash_current_resources_v1`；不从名字或余额差猜收入。

## 明确映射

| 已有cash-v2字段 | 评分字段 | 原单位及处理 |
| --- | --- | --- |
| `player_monthly_gross_income.raw` | `gross_income` | Q100000金/月；除100000，绝不取net冒充 |
| `player_monthly_total_expenses.raw` | `total_expenses` | Q100000金/月；已含当前军费 |
| `military_expenses.current.gold_raw` | `military_current` | Q100000金/月；核owner、resource kind、全部当前WarID及`actor_owned_military_once_across_all_wars`，只记一次 |
| `military_expenses.all_raised.gold_raw` | `military_all_raised` | 同scope的原生全动员月费报价，不是未来战争费用上界 |

字段ready不真、值为null/负数或费用种类不符时，该项保持unknown；总支出小于当前军费时，当前军费标不兼容，不能靠裁零闭合财政。部分DTO仍可保留其余已观察流量。`due_commitments`、质量军力P、合法player-heir及全realm指标不在本叶映射内，均不能被补成0。只有四个流量仍不等于确定E/M。

现有公开campaign-root结果同样须带原planning frame；纯叶复用`build_turn_bundle_v1`的绑定、domain和territory投影，只输出`realm_diagnostics`。domain大小/上限、直接地理county和其继承转移暴露可以进入同帧诊断；全realm县数/品质、宗族县与品质仍是原先unknown。不会把个人county、domain或风险相关县子集改名为L/D。

## 最小集成位置

运行owner将来只需在**原普通query已经发生的位置**保留原DTO及其原planning frame，按当前owner/episode生命周期管理，不写入新的长期历史。MET继续使用原有一次`take_internal_semantic_snapshot()`；当该snapshot已经生成准确月界candidate时，调用：

```python
extra = project_existing_month_inputs_v1(
    snapshot,
    cash_packet=already_obtained_cash,
    cash_source_frame=original_cash_planning_frame,
    campaign_root_result=already_obtained_public_root,
    root_source_frame=original_root_planning_frame,
)
candidate["raw_metrics"].update(extra["raw_metrics"])
candidate["sources"].extend(extra["sources"])
candidate["existing_realm_diagnostics"] = extra["realm_diagnostics"]
candidate["existing_input_gaps"] = extra["input_gaps"]
```

非月界不调用本叶；缺DTO就传None，不补RPC。来源继续由既有paired-MET持久化补实际response path/SHA和Game tuple。当前MET没有上述DTO/原planning-frame交接，这是尚未实施的生产接缝；本包没有改冻结SDK或要求热采。原月样本、T0锚及旧unknown记录均不追写。

## 必要软件验证与边界

新增[`test_campaign_score_existing_inputs_v1.py`](../../ck3_autonomous_player/tests/unit/test_campaign_score_existing_inputs_v1.py)8项一次通过，内部0.004秒、外层0.957640秒，exit0。复用已有cash-v2小fixture，验证gross与net区别、两场软件战争仍只计一次actor军费、缺原frame、同日旧revision、actor/episode/PID/generation变化、给旧DTO重盖新frame仍拒绝、v2算术/scope错误、部分unknown、钱包冲突及root不冒充全realm；另将输出纯合并进现有cadence candidate，确认创始锚、gold和E/M/H未知项不变。

cash fixture原自历史P04保留DTO，但没有machine_id，故其历史机器身份为`unknown`、所属机器未核实。这里仅复用其字段布局作软件输入，日期/身份/战争变体均为合成；不是本场当前现金观测，也不是新业务/G2信用。未重复旧M1/cadence或战争矩阵。

通用存储策略1.0.0；本包仅小源码、测试、文档与JSON，低于64KiB，计Root已给共享研究额，无重型写入或新预留。当前Z只读total4,096,787,476,480 B/free178,407,550,976 B，不代表原子预留或其他任务配额；小记录180日复核。M1历史complete、G2仍6/8；Root统一stage/commit。
