# R05：用真实候选容量准备零供给场景

本入口衔接 [零库存损耗源码](episode04-zero-supply-loss-source-12004.md) 与 [候选统帅条件容量](army-commander-conditional-supply-capacity-12004.md)。目的是减少正常战役的准备时间；它不授予已任命、已到零或已发生物理扣兵。可机读顺序见 [决策卡](evidence/episode04-commander-capacity-zero-preparation-12004/decision.json)。该卡是明确输入的决策知识，不会发出游戏命令。

## 现有实际输入与最短选择

下列值只属于机器 `desktop-3fevhd2-1c74096080` 的 R0177，不是跨机器固定 ID。小型来源与 SHA 见 [输入索引](evidence/episode04-commander-capacity-zero-preparation-12004/inputs.json)。R0177 的来源链记录历史角色1128的罗贝尔意图、实际 runtime ID31254；并未声称直接解码了 history→runtime 映射字段。新场次仍独立绑定实际角色、PID/create-time、generation、episode、日期及双 Army FullID。

| 真实观察 | Army18 / native18 | Army93 / native85 |
|---|---:|---:|
| 010同帧日期 | 53146632 | 53146632 |
| 地点/分支 | 海上8645，非LAND | 陆地2619 |
| 库存 / 实际容量 | 300 / 300 | 100 / 100 |
| 当前统帅 | 后续8754预览读到31254 | 34232 |
| 当帧LAND M1A9 | null，非LAND早退 | 54000，即0.54 |
| 当帧总供给率 | 0 | +20 |

后置正常 S0 的 Army93 已在2624，日期53146848、stock100、regular、complete_empty、controllable；正常保存 SHA 为 `e6ee95c3184c00989af660c5d765a27622fd5b93f9e8930fdc5a5ed56e157d67`。S0小收据不发布该帧容量、统帅和完整负率输入，不能把010在2619的 +20 或整套 context拼接成S0的目标预测。

因此先比较两条合法准备路线，而不是固定从300等起：

- **使用已有100库存军队**：重新读取 Army93 当前同帧容量/统帅/库存、目标完整LAND输入和实际可达路线。若可取得有效负率并保有足够实际合格兵员，可省去换将。小军队未必能使 usage>limit；不能仅因stock100就断言更快。
- **保留大军，正常换低容量统帅**：a08之后，用现有候选 query 读取真实 `can_assign` 与新的条件容量，再正常任命一次并独立读回。只有新实际容量、库存和新将领 M1A9 读回后，才比较到零所需的成功更新数。

现有候选测试 corpus 中的合成 Character ID 和公式案例证明接口行为，不是 R0177 的可任命名单。当前已读 CURRENT/CONTEXT 小包不含 candidate rows。尚未实际观察 a08 新条件容量，因此本包不点名一个可使 Army18 容量变100的候选，也不把 Army93 当前统帅34232追认为 Army18 的合法候选。

## 正常换将的最少步骤

1. 在新鲜暂停帧，对受当前角色控制的目标 Army 调既有 `ck3_query_army_commander_candidates_v1(army_id, expected_revision)`。保存会话、public/native Army、实际当前统帅和 candidate 完整 FullID。
2. 仅考虑同一候选 `available=true`、`final_eligibility_observable=true`、`can_assign=true`、条件容量 `status=available` 且 source ID一致的行。用严格 normalizer 核 provenance 和精确公式，再读取 canonical signed64 raw。选择较低正条件容量作为准备候选；不把 quality、另一军队 cap或条件值当任命结果。
3. 使用现有 `ck3_assign_army_commander_v1`，传该 public Army、实际候选 FullID与动作所需的新鲜 UI revision，提交一次正常动作。结果未知时先查实际状态，不重复动作。ACK只表示受理。
4. 独立 query 当前统帅并重新读取同一军队 strengths。要求实际 commander、双 Army身份、owner匹配；记录**实际** capacity、stock及新当前 M1A9。任命前的当前 M1A9不能给新将领复用；候选容量叶只有467/468，不含候选1A9。若任命结果或新容量不匹配，保留条件预测与实际差异，重新决策。
5. 以任命后实际库存为起点，选择同帧完整目标输入支持的负LAND率和合法路线。a08目标 M输入仍只服务当前实际统帅。到场后重新读取，若usage/limit、P、resupply、将领或rate改变，重算条件方案。
6. 保留自然 updater 及供给writer所需journal，按现有 exact-day runner推进、逐日drain。观察真正成功的库存更新机会及当次post-stock；不把等待天数、显示月率或无记录当成功更新次数。

既有query、正常任命、独立读回已足以完成此准备；不需要新动作、直接写 `CArmy+120`、伪造候选或调用容量函数构造临时 Army。

## 智能体使用入口

继续使用 `strategy.py::plan_r05_zero_stock_preparation`，其纯实现是 `bridge/army_zero_stock_clock_12004.py::plan_zero_stock_preparation_12004`；完整目标负率使用 `bridge/army_target_land_supply_projection_12004.py::project_conditional_target_land_rate_12004`。这些入口来自既有 R05 包与 a08 目标输入增量，本补充不重写规划器，也不让决策卡自行执行动作。

调用前收齐同帧真实库存/容量、当前统帅 M1A9、目标完整输入和 own eligible union；规划器要求缺失项时按明确需求再读现有接口，不拼旧帧。候选叶使用 `bridge/army_commander_conditional_capacity.py::normalize_candidate_conditional_supply_capacity_v1`；raw 解析复用 `parse_conditional_capacity_raw64`。规划器或上层执行者仍应把候选条件量、正常动作受理、独立任命读回、实际 updater/physical writer结果分别保留。

一般消费说明见 [已有零库存准备入口](episode04-zero-stock-preparation-consumer-12004.md)，目标条件投影见 [R05目标负率](episode04-r05-conditional-target-rate-12004.md)。本页只补“先利用已100库存军队，或正常换将再重读”这一准备选择及容量裁剪语义。

## 300→100的裁剪发生顺序

实际 `.4` updater `24E4CF0` 在准入后先于 `24E4E6F` 对 stock做一次 signed64 rate ADD，随后调用 `2C53BF0` 取**当时实际**容量，再执行负值floor0或非负值与容量取小值（`24E4E8B..24E4EB6`）。拒绝准入时不执行这一库存更新。

所以只看到新cap100，不等于stock已100。普通任命还可能有其它原生后处理；本包没有据容量getter证明“任命立即裁剪”或“任命绝不裁剪”。先独立读任命后库存S：若S仍300、实际cap100，且某次成功更新时 `S+rate>=100`，该次库存才按这条链裁至100。裁掉的差额包含cap裁剪，不全部叫供给消耗，更不是兵员损失。

下表仅是普通非负、无溢出域内的**固定负率/固定cap/每次均准入**算术说明，不是R0177未来结果或日程承诺：

| 条件例 | 首次成功更新 | 首次严格低于10 | 首次到0 |
|---|---:|---:|---:|
| S300、cap100、rate−5 | 100 | 总第20次：5 | 总第21次：0 |
| S300、cap100、rate−2 | 100 | 总第47次：8 | 总第51次：0 |
| 已观察S100、cap100、rate−5 | 95 | 第19次：5 | 第20次：0 |
| 已观察S100、cap100、rate−2 | 98 | 第46次：8 | 第50次：0 |

容量降低只减少起始库存上限；不保证损耗率更负。新将领 M1A9 可改变除数，目标P、usage/limit和补给准入也会变化。现有来源未把成功更新次数换成固定日数；不要许诺“20天见零”或把显示月率除30。

## 到零后如何验收 R05

stock0 是准备条件。新鲜 frame实际0或callback entry0都不足以单独授予饥饿扣兵：同次 updater可能补到阈值以上、被拒绝、被fleet抑制或人数预算截0。

正例继续使用已有 exact4 keyed parent链：真实writer入口stock0、同一次自然callback、精确供给preferred或已闭合supply residual、完整unique physical slots before/after，实际physical debit>0。围城/raid、county分量独立，net soldiers、请求量和cap库存delta不填physical debit。逐日无事件也不填“实际扣兵0”。若只能取得库存0、条件风险或预算，按原等级报告，继续正常推进并保存缺口。

本补充仅研究/决策知识：零新增SDK、桌面、游戏动作、EXE读取/哈希、构建及测试重跑。a08能力尚待实际候选查询；R0177上述输入不自动成为未来场次或其它机器的业务资格。外置资产沿原期限2026-10-16T07:45:01.597Z复核，不自动延长。
