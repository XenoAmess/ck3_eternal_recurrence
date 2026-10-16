# R07七日原卡：已证单海边为何仍需要31日

机器 `machine_id: desktop-3fevhd2-1c74096080`。本次观察时间与每份源码/小证据pin见`SOURCE-INCREMENT.actual.json`。本增量只读现有便携R0177/178/179证据、仓库已闭源码和实际安装目录的文本定义；没有SDK、桌面、EXE/存档/完整Driver/视频读取，没有新付款consumer重跑，也没有新场、路线、pair或R07信用。

**当前已验证的正常coastal S0不能用于原R07七日正例。** R0177保存`e6ee95c3184c00989af660c5d765a27622fd5b93f9e8930fdc5a5ed56e157d67`、71,631,396B、date53146848，选定Unit93/native85在2624陆地regular、空route。R0178从这里正常新Move到海1036，实际route只有`[1036]`；它已经是首海单边，31日并非多段内陆路程。R0179同S0静止对照只完成30日，第31日原地接战。不能再重复同源31日，期望战斗这次不发生。

## 新补齐的定义与源码边界

本次实际读取的原版`common/defines/00_defines.txt:1188–1190`为：

```text
NPathFinding = {
    EMBARK_COST = 30
    DISEMBARK_COST = 10
}
```

原注释明确它是从陆到海时设置的**pathfinding cost**。这个文本声明与R0178实际首边`3000000/Q100000=30`相符，但不是“所有军队固定30天”的证明。本次没有读取运行时loaded global或扩展`2649300`几何helper，所以不将声明直接升级为所有将领、mod、边和future frame的实际成本。

同文件另有`NFleet.EMBARK_GOLD_COST_PER_HUNDRED=1`、`NArmy.DISEMBARK_PENALTY_DAYS=30`，以及**角色旅行而非军队**的`NTravel.TRAVEL_EMBARK_COST=15`；这些是不同规则，不能拿30天登陆战斗惩罚或15天角色旅行抵扣军队登船首边。

原版创新`innovation_longboats`声明`embarkation_cost_mult=-0.75`与`naval_movement_speed_mult=0.25`；`engineered_for_destruction_perk`也有naval speed+0.25。它们证明脚本有相关独立修正入口，**不证明当前Army93/34232有该修正，也不证明修正能把本条陆转海边缩到七日**。`embarkation_cost_mult`不能仅凭名称当作时间百分比；金额源链和移动成本不是一个字段。

既有`.3`速度源码闭合了owner/current commander的effective修正汇总和land/naval totals；`.4`metadata迁移定位了对应三个getter。它们支持继续使用实际selected native total，不能从角色特质标签或普通海上速度倒填陆转海耗时。尤其exact`.4`的Unit NewDate movement前缀先选**正数Unit190缓存**，只有缓存非正才读current-edge fallback rate。R0178实值缓存为100000，fallback raw为null是该帧不要求它，并不是速率缺失。即使另一查询的naval total更高，也不能替代已选择的正缓存增量；换将后是否改变缓存必须新读实际后态，不推测。

## 本条单边的七日NO-GO是整数事实

R0178 day29实读weight2900000、cache100000、cost3000000、provider0；day30实读weight3000000=cost、remaining0、provider0，仍moving@2624且route`[1036]`。exact`.4`比较为signed **weight>cost**；小于或等于时仅provider byteE非零才进入arrival分支。因此100%进度/remaining0不是抵达。第31日独立端点才实际1036/embarked/空route，付款原闭链对应Unit93实扣1金币。

对新边若实际W0=0、cache=100000、cost=3000000、provider0且每天确实发生一次同条件ADD，则七次最多700000，不能越过3000000；条件最早次数为`floor((cost-W0)/rate)+1=31`。这只是对保持不变输入及调度的条件预算；R0178实际31日是独立实证。不是所有军队固定31日，也不是允许从day24移动中存档截七天改称静止T0后新Move。

## 下一执行选择：停止旧短边搜索，不再造31日pair命令

本轮查阅范围没有另一条已封存、普通静止S0出发、七日内真实陆转海的合格短边。2635/2624“临海”、capability列出某海目标或合法preview都不足以授时间。现有legal preview不返回ETA；合法可达与行程预算必须分开。

**已知2624→1036无需新增查询即可判原七日NO-GO。** 不再为相同S0、同单边追加一个32日对照。R0178付款实证保留，R0179战斗中断保留，R07-v2与七日原卡分开，不能改名把v2算原卡。

若正常游玩未来自然出现真正不同的静止近海候选，唯一有用的路线筛选读数是：在单独普通pilot中已有合法preview并正常Move一次后，从其**明确成功的scoped ordinary Army query完整Driver**读取`current_movement_progress`的实际W0、正cache或被要求的fallback rate、first-edge cost、provider byteE、remaining duration，以及真实current/首海target/完整route、native state/陆海definition与调度/准入。一次该read可同时取这些字段；当前empty-route的typed commander query中current_edge是not_applicable，不能提前代替post-Move读数。

这并不是“一次readonly就可解锁七日pair”：还欠原卡的**避开actual actor经济结算机会**。现有cash private合同发布余额、月收入/支出/费率和wallet/payment journals，没有可供调用的已闭next-economic-settlement-date/cadence字段。Unit NewDate调度不是actor经济调度，没跨日历1号或generic付款列表空也不能证明避开了结算。须先取得既有源码来源绑定的actual cadence或完整机会观测合同；本包不发明新query、不重做已闭boarding付款getter。

未来若两项准入同时真实具备，正式两fresh arms才固定同一静止normal S0、相同source/DLL/cohort/commander/钱包，control完全不Move/Halt、treatment一次新Move，严格同N≤7个exact日。实际入水、选定Unit的来源合格正额SUB、control同期未入水/无该Unit的boarding callback分别验。七日仍未入水就停止，不能延长后保留七日标签。本包没有生成这样的现场命令，因为当前两项资格尚未取得。

导演可准确表述：“这支军队已经只走一个陆转海边；这次首边成本是30、每日进度是1。第30日进度刚好等于成本，画面仍在岸上；下一日才真正入水。”不能说所有部队登船固定30/31日，也不能将R0178片外入水填进day30陆地原片。

智能体预算应在正常Move后先读实际cost/cache-or-rate/remaining，按strict比较留后验余量，并将31日敌军/事件暴露计入pilot风险；preview的合法回包不授ETA。无新短边正例时停止这条筛选线，继续已有有价值的自然游玩与R04/R06；不把失败场景反复重开当成策略搜索。

计划按`native_research_plan.py`真实init/check/render保存，mode仍offline-only；无新live窗口、无for-observation、无actual通过。统一存储1.0.0：本小记录180日复核，派生helper48h复核；没有新增raw、复制checkpoint或续期旧S0保护。
