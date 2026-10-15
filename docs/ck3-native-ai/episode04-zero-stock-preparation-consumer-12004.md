# R05 正常零库存准备：已有输入的纯候选与决策入口

本增量复用 `army_zero_stock_clock_12004.py`，新增两个纯函数；既有 `strategy.py` 的显式 `plan_r05_zero_stock_preparation` 委托该consumer，并返回普通 `one-life-turn-v1` decision形状。只用已有query/preview/候选将领/单日step名称。函数不调用backend或提交动作。

`machine_id: desktop-3fevhd2-1c74096080`；实际离线消费时间、HEAD与SHA见外置 `zero-route-precondition-a07/DELIVERY.json`。本包不读EXE、不接SDK/游戏/桌面、不构建、不写主树；计Root原active32内2MiB，原截止 `2026-10-16T07:45:01.597Z`不续。

## 已有 DTO 的实际边界

现有preview的 `province_supply.target` 提供当前目标地limit/usage、P与原生resupply verdict；没有抵达后的实际月变，也没有候选统帅的假设容量。目标usage明确不替未来入县贡献作假。当前海上0月变或另一省负月变，不能直接附到远处8个地点上。

因此准备分为已验证当前驻地与仍需真实读回的目标：

- 只有同暂停帧、同进程episode/generation/revision、exact `.4` 来源、双FullID，实际当前位置匹配、signed monthly<0、当前原生供给资格人数>0，才计算可用准备。
- 复用现有strategy的 `_fresh_move_route_preview`、`_same_frame_readonly_result_lease` 和 `_audit_war_route`。几何route安全沿用现有ordinary war语义；不称未来整个行程绝无敌人。active wars/敌军位置缺失不当成空敌军。
- 既有R05 nextpair/all30/strict190 admission仍独立消费。已观察gate拒绝不选成可结算主体；combat/retreating实际状态缺失保留required。
- 实际候选角色必须正ID、available、final eligibility可观测且can_assign=true。角色0不作为卸将按钮。候选列表不提供cap/rate，所以返回正常assignment step及**指派后的实际cap和rate读回要求**；不按quality、trait猜它必降容量。当前已验证上下文仍可单独排序，未验证换将潜力不变成“全局最快”保证。

`required_fields`直接指向已有当前query/arrival query/assignment readback字段。没有默认5、10、20或stock常量。

## 精确成功机会数

`successful_supply_occurrences_to_zero_12004(S,C,r)`只接受实际signed64 raw，S/C非负且r<0。设d=-r：

```text
S1 = min(C, max(0, S+r))
S=0 时 N=0
S>0 且 S1=0 时 N=1
否则 N=1+ceil(S1/d)
```

这是同rate/cap保持、每个原始bucket指针callback都成功的**条件算术**。例如S300/C100/r-10，首笔ADD后clamp得到100，故N=11；不能先把S改100再减10得到N=10。首次归零的同一次callback随后即可计算供给损耗，不必另等一轮。已有stock0时，N=0仅表示无需再降库存，新的物理writer证据仍需实际新opportunity。

一次桶访问可含多个同Army指针occurrence；成功callback次数不等于访问次数或天数。输出 `bucket_visits=null`、`actual_days=null`，并始终不把算术当已死亡。排序只是在**当前已验证上下文**中按N、实际native route hops作确定顺序；`shortest_actual_calendar_preparation_ready=false`，不按静态坐标距离或山地名决定。

## 直接调用与现成文件消费

```python
from xar_autoplayer.strategy import plan_r05_zero_stock_preparation

decision = plan_r05_zero_stock_preparation(
    army_query=actual_current_query, sites=static_candidate_sites,
    snapshot=actual_same_frame_snapshot, commands=existing_command_history,
    active_wars=actual_same_frame_active_wars,
    commander_queries=actual_same_frame_commander_queries,
    available_steps=actual_available_steps, army_ids=(18, 93),
)
```

`army_query`接受已有Service `army_strengths`，也可消费Root具名compact `rows`。compact缺少来源/frame/native字段时只是required，不能伪装完整query。`commands`仍是现有 `{command, ok, result}` 历史，不创造新preview协议。正常Root执行者读取decision，实际动作继续走既有planner/driver守卫。

薄CLI只读给定小包，源文件SHA与machine_id进入回执；不同已声明机器直接拒绝，历史缺machine_id标unknown。单输入上限2MiB，避免旁路重开数十MiB原query。使用Root已经封出的compact extract：

```text
py -B tools/consume_r05_zero_preparation.py --army-query <compact-query.json> --sites <CANDIDATES.actual.json> --snapshot <snapshot.json> --commands <existing-commands.json> --wars <active-wars.json> --commander-query <actual-candidate-query.json> --available-step query-army-strengths-v1 --output <fresh-external-result.json>
```

## 当前真实输入与行为验证

首次消费Root `continuation-a07/saved-r0176-supplies.literal-a01.json` 和8个静态地点包（另3anchors），18/93共22个组合。结果selected=null，下一只读step为既有query-army-strengths-v1，列12类缺字段。当前18为300/300、monthly0；93为100/100、monthly+20。静态山地/距离、null native limit/safety均没有变成负月变或安全路线证据。

Root随后报告R0177 preview93→2624 target L5657/U0、resupplytrue/gain20/P0；18→2635 target L9880/U0、resupplyfalse/P0。两者不是负月变证据；本lane仅复用Root报告，等待integration owner的既有小extract，不重复读30,670,516B完整query。这些自然移动/围城由Root推进，不能为R05把+20或0改称负率。

新增8项行为checks首跑 `-O`通过：ADD后clamp、first-zero同笔、缺/非负/bool输入、strategy真实委托、远省不贴当前rate、敌军冲突/跨generation、事件兵非补员不代供给资格、角色0与假容量拒绝、gate/静态意图拒绝。随后只收紧exact `.4` query source绑定，再首跑一个新的正/负绑定反例；之前8项和旧夹具均未重跑。精确代码/测试SHA及该差异顺序见回执。没有新增native观测或实机扣兵信用。

## R0177 新原件即时消费

integration owner从已绑定010原query的最后一次读取中给出 `CONTEXT.actual-a01.json`，64,049B，SHA `ba556ebde9639f7cc7c0b936928d312b440f47862156daab0950b42e93d80860`。本lane只读该小包，未重开30,670,516B原件。原frame为native:3/public4/native revision3、generation1、episode `native-31254-00b796ef873c`；原件SHA `3f8d01c5a9390d0bd387d86e15af9133a36ca9a0fe4a85149a7b1e410ae88a32`。

- Army18/CArmy18在8645：stock/cap300/300、signed monthly0；其available own occurrence供给资格current1195。
- Army93/CArmy85在2619：stock/cap100/100、signed monthly+20；其available own occurrence供给资格current250，四ArRg资格均true。这是当前原生供给资格观测，与不能补员独立。
- Army93实际loaded slope100/min500000/max1000000/floor10000，P0、M1A9=54000、scale100000。保留实际数值，没有代入原版默认。当前正月变不能变成未来超限负率。

全Province的contributors可能因无关stale occurrence而partial；完整available的**主体正资格见证**仍可保留，不能要求无关全省闭合才能证明这个正人数。consumer已按该实际缺口作小修正，不据此声称全Province总量/完整absence。又首跑一个新增反例验证partial不抹own正资格、缺Snapshot仍不选择；之前9项及旧tests未重跑。

首次actual摘要harness误以为当前省一定在候选site集合，遇海域8645停止；随后修正该摘要假设并成功消费，生产decision未因此改变。输入组合保留原scalar/sliver/family JSON pointers，未把4字段gate sliver伪称完整family。小包没有的EXE来源leaf、完整Snapshot、路线安全和候选统帅读数继续缺省，不制造快照。因此当前仍selected=null，R05负率条件未闭合；Root正常移动/围城不是本包动作信用。
