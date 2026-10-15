# 第4期 B 下一步决策适配器（1.20.0.4）

[strategy_b_next.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_next.py)把已有 [B 事件验收器](episode04-strategy-b-12004.md)的真实输入转换为一个下一步候选或具体观测依赖。它是可导入的纯函数，不新建策略平台、执行器或持久状态，不修改已有 R10 / A / C consumer。动作执行、决策展示、一次提交及原始回执保存继续由已有操作者负责。

```python
from strategy_b_next import next_decision

decision = next_decision(
    plan, arm, trace, current_endpoint, evidence,
    plan_sha256=exact_original_plan_sha256,
    capability_scope=capability_scope,
    commander_queries=commander_query_pins_by_public_army_id,
)
```

`plan / arm / trace / endpoint / evidence`沿用现有 B/R10 schema及相对pin。Python导入环境需已有comparison目录与`ck3_autonomous_player/src`，复用项目已验证环境。函数不填未来 disposition、结果或事件；缺合法既有输入时保持blocked，不能为调用它制造后验。该适配器仅供已有冻结B输入的下一步选择，普通长局的完整规划器无需以R10对照实验合同作为所有战争的前置门槛。

## 真实 `.4` 动作与合法性边界

[war_contract.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py)已有`split_army_half_step / merge_armies_step / preview_move_army_step`，本适配器直接复用它们。当前 [driver](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py)从实际snapshot与exact adapter capability展开split/merge literal；split对controllable军队公布，merge对同省且非combat/retreat的有序军队对公布。

**公布的literal不是原生IsValid已通过。** [actual `.4` Military绑定](../../ck3_autonomous_player/native_bridge/src/ck3_12004_military.cpp)的split validator为`296CF40`，merge validator为`296EF70`；已有[提交实现](../../ck3_autonomous_player/native_bridge/src/ck3_12002_military.cpp)在提交前分别调用它们，并保留validator_rejected / submission_failed等返回。适配器不会补造一个`can_split=true`或绕过校验，输出状态为`candidate_requires_native_validation`，`native_validation_pending=true`。原生命令可能合法拒绝；拒绝或结果未知仍禁止重发。

只有真实当前能力范围包含精确方向的literal，才输出：

```json
{"tool":"ck3_execute_step","arguments":{"step":"split-army-half-<actual-public-id>","expected_revision":123}}
```

capability包实际字段是`action_steps / diagnostics / backend_id / snapshot`，没有`queried_snapshot_id`。因此`capability_scope`只引用三份原包：

| 字段 | 内容 |
|---|---|
| before_snapshot | 调用`ck3_get_capabilities`前取得的实际暂停snapshot pin |
| capabilities | 实际`ck3_get_capabilities`完整返回pin |
| after_snapshot | 调用后独立保存的实际暂停snapshot pin |

两份snapshot须为不同保存文件，且frame ID、public/native revision、日期、episode、玩家、完整roster、event和interaction与`current_endpoint`一致；能力包另核connected、PID、generation、exact `.4` / EXE identity。没有夹取、scope变更、仅有template、错误方向或旧generation时`command=null`。这是供应证据的一致性检查，不证明文件取得顺序或当前实机真实性；执行端仍须以`expected_revision`及原生校验拒绝已过时的决定。

## 新军、顺序与数量

每次先通过现有`strategy_b.audit / observe`，再要求显式available query scope、实际resolved CArmy raw reference / full entry一致、合法storage index，以及完整native ArRg / DATA顺序。DATA不得排序后伪装有效：group按实际ArRg次序绑定，每group的`record_index`须为完整`0..count-1`。真实`count=0 / records=[]`是可用输入，不添加虚构persistent兵槽。

split后直接复用[R09只读helper](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_split_merge_observation_12004.py)的`identify_split_sibling`，要求独立snapshot ID变化和public/native revision均严格推进、同日期/episode/PID/generation、原玩家roster全部存续且仅一个新增public ID、原native CArmy完整generation保留。旧driver的immediate sibling差集或旧B consumer仅非递减revision，不单独授下一步新军移动资格。没有足够后态只返回依赖，不猜历史ID。

同一helper的`compare_split_merge_cohorts`分别报告原cohort和全部策略军队；新增1/1保留其分类、DATA与Character predicate的true/false/unknown。`actual_physical_refill=null`，队伍总计+1、统帅改变或无DATA的1/1都不能变成physical ADD或出生producer证据。

当前每个strategy Army还需独立`ck3_query_army_commander_candidates_v1`，由`read_bound_current_commander`核同帧actual assigned ID。`commander_queries`是public Army ID到原query pin的映射。缺哪军即给出该tool与真实`army_id / expected_revision`读取依赖；candidate或preview里的将领不是替代。已知无统帅保留null，query不可读不降成null。

## 下一步规则

| 当前实际状态 | 输出 |
|---|---|
| 完整whole且仍等于冻结冷T0 | fresh scope包含精确split才给一次候选 |
| split后尚未到冻结驻点 | 指明army/target、现有preview literal；不直接发Move |
| 实际到站且尚未记录入站 | 返回既有`rest-enter`账本事件，绑定当前endpoint |
| 已入站，真实库存/缺额达标 | 返回`rest-exit / threshold` |
| 到最长驻留仍未达标 | 返回`rest-exit / maximum_rest_days`，不制造恢复成功 |
| 尚未达退出条件 | 返回需要下一实际日读数及每军剩余驻留日，不自动推进 |
| 两军退出且实际会合驻定 | 仅冻结D/S方向、fresh scope包含对应merge时给候选 |
| 合后仍在行军或未到最终目标 | 返回移动/preview依赖；新增1/1和统帅后果继续保留 |
| 实际goal状态或day90 | 交原daily/first-arrival比较器处理，不授抵达tick或截尾 |
| 已有rejected / unknown动作 | 只读诊断、禁止再次候选 |

优先记录两军实际入站，再处理任一军的等待，避免主军未恢复导致另一军入站日期被人为记晚。普通event/interaction先交既有处理策略并重新观测。局面出现combat/retreat或缺控制/完整DATA时不继续生成此冻结后勤方案的动作。

## 新增验证与资格

[新增聚焦测试](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/test_strategy_b_next.py)只覆盖next adapter的新行为，不重复原18项B测试：fresh split候选、缺scope、错误merge方向/旧generation、单文件假夹取、typed commander缺口、缺显式query scope、DATA顺序、旧audit可接受的同revision split拒收、并行入站计时、真实max-stay退出、会合merge候选、无DATA新增1/1与统帅改变不算physical refill、unknown动作不重发。

```text
<verified-python> -B -O -m unittest discover -s promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison -p test_strategy_b_next.py -v
```

全部测试为临时目录内显式合成native形状JSON，不是实际`.4` split/merge或R09/R10结果。输出固定`live_execution_performed=false / research_card_closed=false / R10_comparison_qualified=false`。此包未打开EXE、save或raw，未访问SDK、游戏与桌面，也未构建native。
