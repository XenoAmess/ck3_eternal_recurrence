# R05 c499：发布链已齐，下一场只做真实准备

机器 `desktop-3fevhd2-1c74096080`；源码 `c4992c304d196135d9590799d69ffb3c9f5510e6`。本批先记录容量估计再读具名源码，零SDK/游戏/桌面/构建/EXE读取。**R180 Army18 的300/300普通行军不计R05正例，本批没有新实际M、候选或首零事件。**

当前首零判定不缺必须新增的原生只读值。c499已经包含a09的保零守卫与 `conditional_next_zero_supply_budget_v1`；a10清单中的“待合”属于其b42封包当时状态。这里确认源码合入，不能据commit追认R180现存Python进程、DLL选项或observer已应用；离线消费应使用现有consumer的新进程，并核实际query的schema/observer状态。

| 消费用途 | 已发布原值/实际入口 | 源码证据 |
|---|---|---|
| 库存递推 | Army row的S/C/signed月率与Q | `army_strength_v1_serializer.hpp:1287/1292/1297`；a09直接读真实整数，不将candidate cap替actual C。 |
| 首次0的整数预算 | 完整 `monthly_loss_budget_inputs_v1`：loaded顺序表、fleet、当前Province definition选择的modifier ID/raw；`loss_application_inputs_v1.supply_eligible_soldiers` | `ck3_12002_army.cpp:492/527/535/1062`；serializer315/319/958/1504；`_next_zero_supply_budget`复用原预算kernel。 |
| 下一自然机会 | update clock、all30真实positions、native source next pair | serializer999/1004/1557；现有next-clock consumer独立核相位与准入，不按ArmyID取模。 |
| 当前统帅目标率/合法低cap候选 | 既有target preview optional loss operands；candidate条件cap原leaf | actual4 binder174、target collector1644、target serializer54；候选normalizer209严格保留leaf，raw64 parser只接受canonical signed64字符串。 |
| 实际通过 | 两journal安装/原event、同callback parent与writer时stock、完整unique DATA before/after | serializer886/899；现有strict physical selector及supply residual classifier。预算正只选采集窗口。 |

R177旧CONTEXT只保存monthly四个准入门，是当时约定的sliver，**不能供首零预算完整判定，也不能证明原值未发布**。Root的新compact必须保留完整monthly原family、loss E、原frame/双身份和来源指针；不要补loaded默认5%或把gate sliver冒充完整family。当前M1A9与Province损耗modifier不同；candidate只发布条件cap，正常赋任后重读当前M/实际C即可闭合，不需要新增“未来已赋任M”字段。capabilities lane确认不改capacity reader，本批也没有另造reader。

## 下一最小场景：低容量、实际负率、首个库存观察窗口

**预算：**先0推进日读完准备输入；最多1次合法任命、1次普通move。随后exact-one-day总上限为 **min(30，Root本场剩余已授权自然日额)**，期间沿现有collector/drain与compact流程；首次准备读回变化或严格R05正例即停。该上限是本场停止规则，不承诺30日内归零，不独立续到90/600日，不重启/换存档制造库存。

1. Root在R180动作正常结束并暂停后，用 `ck3_take_snapshot()` 和现有 `ck3_query_army_strengths(..., profile="observed_history_full_v1")` 取得Army18同帧S/C/r、own eligible roster/E、monthly完整family、clock/all30/next pair、实际位置及两journal状态。Army93只有新snapshot实际列为存在/可控时才追加查询；旧010的250人、stock100和M不能带入本场。先核Unit combat/gathering/retreat/Army5C及敌军实际位置，缺失或冲突即保持准备未就绪。
2. 现有 `ck3_query_army_commander_candidates_v1` 只读合法名单；选择正FullID、`can_assign=true`且有严格可用较低条件cap的候选。没有更低合法候选就保留当前统帅；不传character0，不从quality推cap，不默认一定有cap100。需要换将时只正常提交一次 `ck3_assign_army_commander_v1`，随后新snapshot＋独立strengths核实际统帅/S/C/M；旧frame全部失效，ACK不算已任命。
3. 用现有 `preview_move_army_step` 对**最多2个**真实可达候选地取同帧preview（8754/2602仅是旧记录的候选提示，不能复用旧路线/数值）。完整条件率必须r<0，或已经实际0/r0、实际C0的保零例外；target当前usage＋selected真实eligible union按现有projection计算。用既有战争路线审计避开敌军当前/目标/路径冲突，优先不自动围城/raid的驻点；有未知敌军位置/路线安全即不move。当前满库存正率、负P但总率非负，都不值得盲推进等待R05。
4. 普通move到达后新暂停query：核实际目标、r<0、C和E、当前Province的实际有效fraction F；不把海上/旧省modifier搬过来。算固定输入下的 `N` 和归零前低库存次数 `L`（既有a09/a10公式）。优先L0；L>0仅在普通DATA/cache一致、无其它损失且F保持的条件下用原预算kernel筛选首次0仍B>0。实际siege/raid、county、补员、重编组或兵力改变后重算；E19×实读5%为0，不靠下一轮小数carry“补扣”。
5. 每次推进前核新source next pair/真实positions及next门；取两journal各自sequence fence，用现有 `ck3_execute_step(step="life-advance-one-day", expected_revision=...)` 一次，再独立snapshot/query/drain。首个cap裁剪/stock读回变化可结束本准备窗口并正常保存；它只是准备结果，库存裁剪不叫供给消耗或兵员损失。若最早满足“本次post0且B>0”，直接拍这一笔；无需额外等一个零入口周期。
6. **停止与信用：**到达日额、combat/retreat/gathering或路线冲突、r不再负、fraction/资格改变、observer未安装/history漏捕，均停止沿旧计划推进并保存真实诊断。只有同一次自然callback的精确供给来源、writer时stock0、完整unique physical debit>0才结束R05验收；preferred35FF与supply residual3638/flags2分别核，combined/county不混记。零事件、AL未知、188变化、净兵数、预算或满供给行军都不给信用。

固定率条件的次数复用 `successful_supply_occurrences_to_zero_12004`：`S1=min(C,max(0,S+r))`，S>0/r<0时 `N=1(S1=0)，否则1+ceil(S1/(-r))`；已0取N0、首次新观察仍需1笔callback。未读新实际S/C/r前，本场N与实际日历上界未知；30日预算不能替代它们。

入库入口继续回链 [首次0判定](episode04-first-zero-positive-budget-decision-12004.md)、[Root清单](episode04-first-zero-root-checklist-12004.md)、[换将容量准备](episode04-commander-capacity-zero-preparation-12004.md)。不新增生产代码或测试；剩余是正常操作后的实际读回，而不是另一个未发布字段。
