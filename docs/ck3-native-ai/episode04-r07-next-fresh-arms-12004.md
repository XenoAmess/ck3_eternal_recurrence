# R07：下一组同静止 T0 双 fresh arms 的准入与付款闭环

machine_id: `desktop-3fevhd2-1c74096080`

reviewed_at_utc: `2026-10-16T09:56:50Z`

reviewed_source_head: `20c7319b6964c80fa419540cf4e30852feff4810`
status: `offline_design_only / no_new_live_credit`

本次只读既有专题与生产消费者，新增本页；没有游戏、SDK、桌面、构建、EXE 读取或新的付款样本。机器 ID 来自当次 `tools/ck3_live_run_id.py machine`，时间来自当次 UTC 时钟。以下历史实机均属于该来源机器，不代表另一台机器的安装、部署、容量或实机资格。

**当前不能把原 R07 的“七日内、避经济结算、静止 T0 后新 Move、两臂新加载”写成已可执行方案。** 已实测的新登船边需要 30 日，第 30 日还因严格到达比较留在陆地，第 31 日才观察到入水；实际经济结算调度也尚未闭合。正确下一步是有界筛选。筛选不通过即停止原卡；已有 [R07-v2 的 30 日＋最多 2 日余量设计](episode04-r07-v2-boarding-control-12004.md)是明确的另版合同，不能暗中替换七日原卡。

## 已有两臂究竟证明了什么

| 项目 | R0173 历史处理组 | R0174 历史驻地对照 | 下一组要求 |
| --- | --- | --- | --- |
| 输入与加载 | 先正常 load R0172 的 `be327...`，正常保存成 `9ab3...` 后直接继续 | 新 PID 正常 load `9ab3...` | 两个新 PID 都正常 load 同一静止 S0 的精确 bytes/SHA |
| T0 | raw53145048，Army18@2624，已经 moving，route `[1036,8653,1034,1033]` | 同保存状态加载后，一次正常 Halt 才清空 route | 每臂独立读回即为 regular/陆地/空 route；control 不发 Move 或 Halt |
| 观察期 | day21 入水；22 个 exact 自然日总记录 | 21 个 exact 自然日驻地 | 原卡双方同 N，`1<=N<=7`；v2 双方同 N，`N<=32` |
| 登船费用 | 一笔个人 SUB：300000/Q100000，3 金币；实际 whole-callback 余额25448407→25148407 | 没有该驻地军的合格 boarding callback | 新处理组自身的选定军 U、真实付款链；不能搬用旧3金币 |
| pair 等级 | 历史保存后 continuation | 与该历史 continuation 的有限配对 PASS | `two_new_loaded_arms`，不能用一臂“保存后继续”抵扣 |

精确旧来源、归档和可移机重算见 [R0173](episode04-r0173-boarding-halt-12004.md)、[R0174](episode04-r0174-common-t0-control-12004.md)与 [common-T0](episode04-common-t0-control-12004.md)。同一个数字 window1/epoch1 在不同 PID 下不是共享窗口；旧序号16/17/18不能接到新场。旧 pair checker 硬编码21日/2624，其 PASS 不授七日或 v2 全卡资格。

## 七日原卡：先做有限筛选，当前默认 NO-GO

候选必须来自正常保存的陆地静止军队，不改存档、不瞬移、不改速度规则、不复制旧进度。当前已知正常海岸 S0 是 [R0177](episode04-r0177-coastal-normalprep-12004.md) 的 Army93/native85@2624：date53146848，250/250、4 团/4 DATA、stock10000000，normal S0 71631396B、SHA `e6ee95c3184c00989af660c5d765a27622fd5b93f9e8930fdc5a5ed56e157d67`。其存在与可读性须重新核验；这不是新的活跃存储保护。Army94/95 保存时在战斗，不能因同属玩家就当作同等候选。

Root 在一个可正常闭场的筛选场，最多筛现有93/94/95三军、每军最多两个原生合法首海目标；海1036仅是候选，不能预填“合法”。筛选不产生 R07 信用，也不允许向 SDK 重复提交结果未知的 Move。

1. 正常加载后独立 snapshot 与 scoped ordinary：living actor、可控 U、owner、陆地/regular、非战斗/撤退、完整空 route、无实际 move target；核完整 DATA、人数、库存、指挥官与战争。缺任何项就排除该候选，不能用摘要空数组替代完整 route。
2. 当帧 native legal preview 只授路线合法性，**不返回 ETA**。若要取得新边真实 duration/rate/cost，只能在筛选场发一次正常 Move，再独立读取其已应用后态。这个筛选场随后正常关闭；不能成为正式 treatment 的替代。
3. 保留 `current_movement_progress` 的实际初始 weight、`current_edge_movement_rate_raw`、`first_route_edge_weight_cost_raw`、`first_route_edge_remaining_duration`、provider byteE、native state、首目标与完整 route。不得以海岸距离、旧 `.3` 偏移或归一化百分比推 ETA。
4. 七日条件只作候选预算：在 receiver/route/cost/rate/调度不变且每天确有一次相应 ADD 的条件下，需 `W0+7*rate>cost`，或真实 provider 分支满足到达条件。它不承诺未来调度或实际到达；provider 非零也不能凭空假定。建议投影不晚于第6日，留一天独立后验，仍以实际 N<=7 为最终限制。
5. 已知实测 cost3000000、rate100000、provider0 的新边直接 NO-GO：从零进度七日只能积累700000；R0178 day30 的 weight=cost、remaining0 仍 moving@2624，day31才独立观察到1036/embarked。见 [严格 JG 源码与当前字段](unit-first-edge-arrival-selection-12004.md)及 [R0178 实际边界](episode04-r178-zero-remaining-not-arrival-12004.md)。不能从 day24/29 的移动中 checkpoint 截七天，把它称作静止 T0 后新 Move。
6. “避经济结算”必须由该 actual actor 的真实结算调度来源或另行合格的完整机会观察合同支持。`current_unit_new_date_schedule_inputs_v1` 是 Unit 调度，不能改名为经济调度；不跨日历1号、个人钱包没变或 generic 列表为空均不证明无经济结算机会。现有 [R0174 父链](war-payment-r0174-actual-parent-source-12004.md)和 [R0178 raw writer](war-payment-r0178-writer-source-12004.md)的 cadence 仍 unknown；因此即使找到快速军队，这项也暂不通过。

两项条件任一未闭，Root 不应启动一个自称七日正式 pair 的重型 run。可以按现有 v2 单独完成同静止 S0 双 fresh arms；输出明确为 v2，并保留 `original_R07_v1_qualified=false`。本页没有授权改写原卡或将本次设计计入研究完成率。

## 已有字段与唯一需要补齐的新付款连接

无需为登船付款新增顶层 query、钱包差算法或另一个 DTO。现有实现已经能把一笔自然登船真实费用完整重联：

`post-date原返回 → transition24E8DB0 → gateway28B9950 → personal285EED0 / Land285EFF0 SUB → 同次原返回余额`

[静态源链](war-payment-passive-12004.md)已经限定 Province/Army1D4 门、金额计算和两种实际 payer。`component=3` 是子余额扣减偏好，不能命名为军费；上下文 Character 也不能直接等同最终付款账户。

| 复用入口/字段 | 正式用途 | 仍须本场取得 |
| --- | --- | --- |
| snapshot 与 runtime receipt | machine/PID/create-time/generation/episode/actor/date/revision、实际 EXE/source/DLL | 两臂各自独立实际身份；复制另一臂 baseline 无效 |
| ordinary Army U + `army_history_evidence.raw_result_reference` | public U→完整 CArmy resolution、完整 route、current movement、兵数、supply/commander | 每次读取完整成功 Driver 原件及 bytes/SHA，不能只留 compact MCP 摘要 |
| `regiment_replenishment_records_v1` | 选定 Army 的同序完整 DATA/chunk/ArRg/persistent ID/current/max/state 对照 | 比较逻辑 ID 与整数值；不比较跨进程裸指针；玩家全部库存不替代选定军构成 |
| cash private query + `war_payment_observations_v1` | 原始 natural return、transition/gateway/SUB entry/return、账户与金额 | 新 treatment 对选定 U 的正额回调；真实入水前后独立状态 |
| `normalize_journal` 的 `qualified_boarding_debits` | 重新验证源、原调用一次、clock/thread嵌套、natural返回、session、正额及账户减法 | 再从 transition 的 before/after `requested_unit_id==U` 绑定到本实验；其他军的付款另列 |
| `r07_v2_contract.consume_window` | 单个明确 response 的 selected/otherArmy分账、ring止线和generic原样保留 | 它永远不授全 pair PASS；还须完整双臂 baseline/日期/route/事件/终态 |

真正还缺的付款连接是：**新 fresh-load treatment 内，实际选定 U 的入水 transition，经同一自然父调用连接到它自己的正额 personal/Land SUB 和该账户的 entry/return 余额。** R0173 已证明观察器有此能力，但不能代替新 U 的交易。R0178 Army93 入水 endpoint 的小摘要没有在该专题重跑完整 cash formal consumer，不能据此先填新 fee 或 R07 PASS。无需等待 R08 军事维护归因完成才做此登船连接；普通钱包 ADD/SUB仍另列 `maintenance_attribution=unclosed`。

生产消费者为 [war_payment_observations_v1.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py)。它按完整 raw records 重新计算，不信任 native 自报 qualified flag；正额、实际 wrapper减法、personal/Land合法账户、完整 TLS/natural嵌套与原返回均缺一不可。journal publication在函数返回后发生，不能用 journal序号大小充当入口调用顺序。余额边界始终是 `whole_original_callback_entry_return`，不是 leaf指令 store或整天 NET。

## Root 的最小正式执行序列

以下是已存在 MCP 接口的参数示意，R/U/P/D 都必须由当场回包填入；不是可直接运行的固定路径脚本，也不自动发送命令。原卡只有通过上述筛选后才适用；v2使用自己的 N<=32 和换段合同。

1. 当前容量/存储检查、当次 Steam 离线新鲜画面、屏幕独占和正常加载资格先完成。两个新 profile/run/PID均使用同一 actual source/DLL、EXE和静止 S0 bytes/SHA；不同的 episode/window是预期事实。历史 `2026-10-16T07:45:01.597Z` 额度已经到期，本页不延长；使用 Root 当前实际新准入。
2. 每臂 `ck3_take_snapshot()`；在该 fresh R 上调用 `ck3_query_army_strengths(army_ids=[U], profile="ordinary_core_v1", ordered_refill_entry_mode="observed_prepared", ordered_besieging_entry_mode="observed_prepared", expected_revision=R)` 与 cash查询。独立比对两臂T0日期、Army身份/完整DATA/人数/库存/指挥官/战争/route/钱包；任一不同则保留差异，pair停止。
3. 用现有 `ck3_set_army_observer_research_sampling_v1(enabled=true, observer_family="natural_phase", expected_revision=R)`，随后 `ck3_query_army_observer_research_sampling_v1(observer_family="all", expected_revision=R)`，实际确认 natural ON、另8族OFF。不能为了得到全族OFF而清掉他人或尚未解释的记录。
4. 付款 `ck3_query_war_cash_current_resources_private_v1(payment_sampling="enable", payment_window_contract="same_owned_process_no_load_v1", expected_revision=R)` 一次；随后 fresh snapshot与 `payment_sampling="query"` 独立确认 admitted/installed/capture_enabled、自己的window/epoch及无丢样。`None` 不会替你开启。两臂都启用同样采样。
5. control始终驻地且不发Move/Halt；treatment先 `ck3_execute_step(step="preview-move-army-U-to-P", expected_revision=R)`，保全合法回包，再在 fresh R 上一次 `ck3_move_army(army_id=U, target_province_id=P, expected_revision=R)`。独立后态须实际新route、首海边和预算条件；异步读到旧route时只读补查，不重发Move。
6. 每日沿用现有 reviewed exact-day runner：暂停态 Arm一次 `research-arm-tactical-daily-sentinel-v1-D-to-DPLUS24-speed-5-mode-terminal-a-1-U`，其中D/DPLUS24/U替换真实整数；fresh帧后 `ck3_execute_step(step="resume", expected_revision=R)` 一次。独立暂停/哨兵查询/现金和scoped军队后验，要求date+24、tick1、overshoot0。未知弹窗采集原生ID/实际选项后按既定策略续行；不能重Arm/Resume已经执行的日步。
7. 两臂严格同 N，记录所有自然日、modal处分歧和完整 cash引用。treatment真实入水后查正式源链；control每个对应日期都须同地完整空route且未入水。以 actual省份/state/route判到达，不能以remaining0判到达。七日到期未入水即停止原卡；不得临场延长为21/31日后保留七日标签。
8. 一包一审计：用 [现有 v2 reader](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/r07_v2_contract.py) 的真实 `--repo-root / --response / --snapshot / --binding` 参数读取一份明确原件；binding逐项填写machine/PID/create/generation/episode/actor/U/date/segment/window/epoch/本段previous_latest。不用glob/latest，不跨窗相减sequence。全pair结论另由Root按本页或v2合同审结，不能把单包exit0写成全卡完成。

正常关闭与保存、录制结束、keeper/SDK退场、屏幕CAS释放和闭场容量检查继续走既有流程。本页未启动录制；新镜头需在实际recorder active之后另记run/日期/PTS。业务观察不等于连续clean或人工1×签核。

## Halt 的合法使用窗口

Halt通过已有 `ck3_execute_step(step="halt-army-U", expected_revision=R)`。`halt_submitted/postcondition_verified=false`只表示提交；必须用独立后态判断效果。

- 若要从移动中的准备场制造新的**正常静止 S0**，先独立读同帧真实progress/cutoff；在已观察的 `progress<cutoff` 未锁窗口发Halt一次，独立确认原陆地位置、完整空route、无实际target、日期不变，再正常保存。这个新的保存才是两fresh arms共同输入。旧R0174的31717/50000属于历史实例，不是新场常数。
- 若进度已经严格 `>cutoff`，当前锁定语义是保留原front、截掉tail；它不能制造原地静止control。独立后态须 `[old_front]`且进度保留，再自然抵达该front；不能把Halt ACK称作立即驻地。等号、missing或状态未知均不在现有已验锁定/未锁定实例内，不用作准备捷径。
- 正式pair的control本来就静止，无需Halt。treatment若只Move到首海单跳，入水后route自然空，也无需补Halt。为了费用观察在半途Halt会改变处理，须标为abort或另一实验；不能继续与原control比较。

同帧资格与后果检查可复用 [locked-routes工具](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/README.md)；本页不增加 R12/R13信用。

## 停止线与智能体消费

立即停止当前card、保全真实partial：source/DLL/EXE不一致；两臂S0或DATA条件不匹配；无合法首海route；七日预算/经济调度未过；任一日非exact；owner/actor/PID/generation/load变化；未知动作结果；付款失窗/读失败/覆盖/failedappend；control移动/战斗/入水；全引用无法复读；磁盘准入到期或超预算。付款natural retained到48或payment到320先暂停评审，56/384为既有硬止线；读取不会drain。v2跨月需要按其显式暂停归档/disable-clear-enable分段，禁止跨segment接父链。

Agent可用本页来筛选下一场、拒绝错误费用归因、识别Halt的路线后果，并消费每笔源资格登船支出。它不能从净钱包差、月费率、generic ADD、空付款列表、ETA或100%进度推“实付/免费/到达”；不能把旧3金币当跨军队统一价；不能将R08未知军事分量填0或再从NET重复扣一次。新pair的缺口应保持具名pending，未知动作禁止自动重投。研究完成率与视频动态资格由Root总账决定，本页新增信用为0。
