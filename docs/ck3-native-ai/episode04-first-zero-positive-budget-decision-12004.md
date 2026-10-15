# R05 首次归零与同一次供给扣兵的最短决策

本批机器 `desktop-3fevhd2-1c74096080`，2026-10-15 UTC 离线分析；Git 基线 `b42afbbd85df3802b1fa6222f7aac403c2adf735`。复用已闭 actual .4 源及现有 consumer，没有重读 EXE、构建、SDK、桌面或游戏动作。新 a08 实际 commander/M/候选尚未读到，本页不拼 R0177 010 的旧帧。

## 固定负 raw 率不会因小数库存“永远不归零”

令 S、C 为同帧实际非负 signed64 raw 库存/容量，r 为实际 signed64 raw 月变。每次成功 updater 是一次 raw ADD，不除30、不按经过天数缩放；然后 floor0/cap。对 r<0，S+r 不会发生 signed64 加法溢出，因为两项异号。首次之后 S1=min(C,max(0,S+r))，后续每次至少减少1 raw直到0：

`N = 0 if S==0 else 1 if S1==0 else 1+ceil(S1/(-r))`。

这是既有 `successful_supply_occurrences_to_zero_12004` 的公式。即使 r=-1（供给0.00001），也会在有限次**成功原指针结算**后到0；库存保存 raw，没有“每次减小数被丢掉”这条路径。N可能非常大，不能把有限解释为短期或固定日数。重复 bucket pointer 是独立成功机会；拒绝 updater 的日子不计入N。无法保证未来 member、grace、gathering、rate或cap保持时，实际日程继续 unknown。

与之不同，完整 LAND rate 计算内部可能先截成 raw0：例如极小负 P 经很大正除数截向零。若实际/条件总 r==0、C>0且S>0，固定输入下不会归零；正 r 同理。源上 divisor0还可能返回正4294967295，不能只见负P便判耗尽。目标 consumer 已复用相同 fixed kernel，不以显示数值或默认−5/−10替代 raw。负 S/C 不在上述普通域证明内，现有准备器保持 unknown，不据此断言不能到零。

合法例外是**当前已0且r0**：成功 updater仍ALtrue，post-stock仍0，可以紧接着算非零供给预算。实际 C0也使首次成功 post-stock0，包含r0或正r；仅有候选条件C0不能当实际C0。原准备器一律拒r>=0，误拒这些源上合法的零库存机会，本批仅修该守卫。仍拒 S>0/C>0/r0，以及 S0/C>0/正r，因为后者会先离开0。

## 首次0不保证正整数预算，更不保证物理扣兵

库存先更新，随后同一 `24E3410` callback读取更新后state，所以首次从正stock降到0时，**不必多等下一次零入口callback**。原 `conditional_zero_entry_capture_candidate` 只描述入口已0，语义保留；新增同函数的 `conditional_next_zero_supply_budget_v1` 复用实际 source next pair、原bucket positions、next updater门及原供给预算 kernel，识别“正入口→post0→正整数供给预算”的最短观察机会。它不把budget叫physical loss，也不把重复positions复制成同额预算。

按实际表和已读 modifier得到有效分量F后，普通非负且无溢出域的供给整数预算为 `B=min(E,floor(E*F/Q))`。表若实际为 `[60,10,0]/[0,0,5000]`，且实际修正不改变5%，E19给0、E20给1。并无最少扣1或保存分数carry；F=0、fleet抑制、整军预算低32取负、writer skip/空DATA/分配截断都可能使首次0无正physical debit。

特别要防止“先耗很久再拍0”的计划：在严格stock<10后，**归零之前**每个成功供给callback已经可能扣兵。若负率极小，许多这样的调用可先将合格兵员降至整数预算0（普通5%全额扣除的简单路径可停在E19）；之后库存仍可继续缓慢到0，但首次0时没有正供给人数预算。完整physical writer会否按预算扣除仍须逐笔确认，这里只指出存在合法反例，不预测本场E必降到19。

若目标负率足够大、首个损耗state更新直接跳到0，可以避免这一段预先损耗；若必须经过多个低stock更新，应逐次读实际E与供给预算并重算。N是固定率库存计数，不能暗含合格兵力在漫长途中不变。当前较低cap能缩短库存准备，换将又可能改变rate、损耗分量和目标条件，必须正常任命后实际重读。

M1A9 是 LAND rate除数操作数。**供给损耗分量的 commander modifier 是当前 ProvinceType definition+770 指定的实际 ordinal**，由 `MonthlyBudgetSample` 读回，不能用 M1A9代替，也不能把另一省或任命前的值移过来。新下一机会 helper调用既有 `_derive_supply_component`，保留loaded顺序、native fixedmul、absent/invalid分支不补clamp、整数预算signed32语义。它不新增5%常量或另一套代数工具。

## 现有接口的决策表

| 同一新鲜暂停帧实际条件 | 下一最小合法操作 | 可以给智能体的判断 |
|---|---|---|
| 尚无真实当前candidate/M/cap/目标完整输入 | 既有candidate query、target preview与full-history Army query；一次正常任命后独立重读 | 候选cap仅条件值，旧帧M不参加当前计算；不下实际耗尽承诺。 |
| S>0、固定条件r<0，实际cap/eligible union完整 | 用现有目标 rate projection、普通路线审计选试驻点；到场重读后按既有exact-day流程逐次推进/drain | N仅成功机会数；提前监视stock<10的E和预算，避免只追0而兵力先截至无预算。 |
| S>0/C>0且r==0或正r | 重选有来源的负率试驻条件或正常合法候选；不为这个常量状态盲等 | 不会因“再等一个周期”自行耗到0；先排除当前正gain、underlimit、M截0。 |
| 已0/r0，或实际C0使post0 | 沿既有 source next pair/all30真实membership找最近条件机会；无需另外制造负率 | 源上合法的zero-retaining更新；不是“rate0所以不会扣兵”。 |
| 下一真实桶含主体、next门通过，post-stock0且新leaf的B>0 | 先取两journal独立fence，执行一次现有exact-one-day，随后snapshot/full-history独立读回 | `conditional_positive_budget_capture_candidate=true`只选拍摄窗口；正入口首次到0也可直接拍，不能等额复制到其它pointer。 |
| 下一post0但B==0/负、fleet抑制或分量归0 | 重查实际合格人数、当前Province ordinal和modifier，保留原因；选择另一合法主体/条件 | 这次无正供给人数预算，不能声称物理饥饿扣兵。缺字段时保持unknown，不补默认5%。 |
| 同次实际writer时stock0且完整unique DATA debit>0 | 用现有keyed callback→writer join与preferred/residual source classifier验收 | 才能说这一笔零库存供给physical loss；request、byte22、188变化、net Army人数均不替代。 |

新leaf要求当前receiver/Province与完整实际monthly table、当前损耗modifier和eligible count；对尚未到达目标的准备预测，抵达后再读此leaf，不借海上ordinal判断陆地损耗。它使用 source next updater 的日期门，故不会把“当前grace恰等于30而下一日31”错误套成当前预算0；也没有改写任何观测clock来伪造未来输入。

下一日没有真实pointer或门已拒绝时，候选false可以不要求后面未执行的fraction数据。selected bucket/clock/source pair、fleet或table缺失时是unknown。`+188`不是30日冷却门；`+190`年龄严格大于grace，且 earlier gathering/due可以改它。只按已有source-pair/D选择器与实际all30 membership，不按ArmyID取模或把stored D一般直接加1。

## 首次0的验收边界与来源

preferred正证据仍是 `select_actual_zero_stock_supply_preferred_12004`：真实自然 daily callback return2A9AB4B、同invocation身份/thread/token、direct供给return24E35FF、writer当时stock恰0、完整唯一物理槽实际debit>0。供给residual另按已有classifier核外return24E3638/flags2；combined377C/37B3、county2630独立，不因同callback/同stock归供给。一笔可完成本镜头，不等待完整30桶周期；整周期总死亡仍需要完整区间证据。

复用 [零库存执行/5%与截断源码](episode04-zero-supply-loss-source-12004.md)、[时钟和同tick顺序](episode04-zero-stock-clock-and-capture-12004.md)、[目标条件率](episode04-r05-conditional-target-rate-12004.md) 及 [正常换将容量准备](episode04-commander-capacity-zero-preparation-12004.md)。关键已held PC：stock ADD24E4E6F/floor-cap4E8B..4EB6、state4FA9..4FE0、component5007..5145、整军预算33BF..33F5、preferred request35E9..35F3、physical DATA2634259..263434E。本批不重复读取旧body或旧测试套。

新7个行为方法首次通过，含raw−1的有限界、ADD后cap、已0/r0、实际cap0、首次正入口→0且E20/B1、E19/B0、modifier/fleet抑制、缺表unknown、原普通decision和无将领大fraction导致signed预算负值。补出首pointer和modifier ordinal字段后，窄重跑首次归零1方法；旧测试执行0。没有实际新a08数据或physical loss资格。外置预算128KiB，Root统一512MiB池；原07:45Z截止不延长，原件/候选按统一policy1.0.0到期复核，派生48小时/文档180日复核，不新增永久保留或自动清理声明。
