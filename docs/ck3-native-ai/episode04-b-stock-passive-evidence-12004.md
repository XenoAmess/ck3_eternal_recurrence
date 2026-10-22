# B-Stock：复用既有自然一日端点的被动证据合同（1.20.0.4）

> 2026-10-22 00:52:41 UTC 后继实际采用；machine_id: desktop-3fevhd2-1c74096080。

**不同普通战役驻点的库存阳性现为2/2，完整B与ABC仍未验收。** R0234第二站2623的独立单日与callback seq2支持 stock29894738→30000000，实际 +105262/scale100000，兵数1195不变；与R0232第一站合计两站。formal9/11、ABC0/3、fullR10false、one-lifefalse保持。[实际原件、有限连续镜头及复用规则](episode04-r0234-second-b-site-20261022.md)分列native资格与媒体QA，不能以softRED后的可用片段改写原outer2。

接近cap300时本次只增加1.05262，正率、预计+20或已抵达另一省份都不能替代实际raw差、fresh headroom和同日callback闭包。以下旧0/2及“未来输入尚未提供”等原段按2026-10-20时点保留，不是当前站点计数；原被动消费合同和禁止新增动作/未知结果重试的门槛保持。


本页供游玩智能体在**已经获准且正常执行的场次**中消费库存证据。它不启动游戏，不增加SDK/query、自然日、Move、库存初始化、换帅、observer开关或录像，也不改变原场次的目标与正常退出。当前B驻点增长实机资格仍 **0/2**，正式ABC仍 **0/3**。本页是有来源的消费合同，尚未实现R06→normal-day离线adapter，不能把方案当作已通过的单站结果。

源码切点 `31ff77a0f07fb21f528c88e56314cbb093972703`，native tree `fee86631356f556271445157523c62abfd62951e`。核心消费器 `strategy_b_site_growth.py` SHA-256为 `0db9c7e3a675c5d0e6e92824450236c904ca545eb8364b307ceb6e3b81eac71a`；R06公共actor `r06_refill_one_day.py` 为 `cc892c73bdd895b2ca1a59ad54faf997992537d70c624af634eefb917be12dbf`。全部相对路径、字节数、SHA、机器观察时间与限度见[来源索引](evidence/episode04-b-stock-passive-evidence-20261020/index.json)。源码变更后重新核对应入口，不能用本页追认新部署或跨机器实机状态。

## 智能体的直接执行规则

1. 先完成原场次。只有原执行器本来就采集的暂停before/after、完整Army row、一次claim、Arm/Resume/status和独立后态才进入被动消费。缺任何字段只报告具名缺口；不为B补发动作或重新Arm，不延长原场次、不要求重开游戏。
2. 保留原packet、原control结果和full-wire proof的精确引用。公共compact摘要不能代替完整row，production-normalized派生view不能标成原Driver packet。禁止从屏幕整数倒造stock raw，或以当前省份倒填历史callback Province。
3. 分开输出“当前可增长机会”“本日实际stock观察”“单站严格资格”。当前正率、eligible和桶命中仅是机会；真实正差仍要闭合callback/日步链；两个不同Province各自通过后才可交两站consumer。任何单项都不授普通Barm、正式ABC、公平比较、未来安全或soldier ADD/扣兵资格。
4. 现有动作结果未知时继续原有不重放语义。被动consumer失败不触发Move/clock/assign/SDK重试，原游戏/采样OFF、Save与正常close仍由原owner完成。

## 最小窗口：一个真实自然日

`strategy_b_site_growth.qualify_site`最少需要本站day0→day1、raw date恰好+24的真实原件，不要求先split、完整月或90日。并非每个自然日都有库存callback；未命中本军桶、没有事件或没有正差时，本日没有取得增长资格，不能多加一天补成绩。

| 必需输入 | 严格含义 |
|---|---|
| 原runtime/来源 | machine、PID/creation FILETIME、generation、actor、source/DLL与实际normal-source一致；两端同一Army/native完整身份。 |
| 完整独立端点 | 两端暂停、实际同省、regular、可控、无combat/retreat，route读取complete_empty、route=[]、target=null。full query分别绑定其自己的snapshot/revision/native/date/generation。 |
| 原cohort与DATA | 原ArRg与完整DATA身份、顺序、max、backlink、统帅签名不变；真实current士兵变化单列，不拿人数净变代库存证据。 |
| 实际库存 | scale100000，`0<=stock_before<stock_after<=capacity_after`；非空真实整数，不以rate或gain补值。 |
| 原callback链 | observer_installed、capture failure不增加、before fence之后无未解释覆盖缺口；至少一条新增实际callback，sequence唯一有序且每条stock首尾连续，最终等于端点stock_after。 |
| callback时空 | 每条same_instance_after=true、capture_failure_flags=0、完整passed_date_raw64与该日actual完整CDate64一致；before/after.province_id都等于本站。null、缺省或跨省不授本站资格。 |
| 原exact day | 原一次claim、实际Arm/Resume控制行、同generation的triggered stop、completed_daily_ticks=1、overshoot0、独立paused endpoint。不能只读取actor布尔true代替来源。 |

可增长机会的只读字段由现有 `QUERY-CURRENT-OPPORTUNITY.contract.json`列明：stock/cap、**当前final total monthly rate**、真实land resupply、完整province contributors、grace/updater guards、all30 buckets，以及source-derived下一date/native D。使用`uint32(nextD)%30` join下一实际桶；不能用当前phase、宿主日历或“每月1日”猜callback。正loaded_gain不是final rate；省usage不得因split而直接除2。

## 本轮R06的2170：消费既有端点，不追加观测

机器 `desktop-3fevhd2-1c74096080` 的正常Mar31 S0已经驻定2170，actor33388、日期53149056；本轮R06拟自然到53149080。**编写本页时新game尚未启动，before/after packet均未提供。** 未来只取该原场次的`r06-before`和`r06-after`完整row及独立snapshot/clock，缺实际输入就保持0/2。

R06已有strength请求保持原样：`ck3_query_army_strengths(army_ids=[实际public ID], expected_revision=该端点revision, profile='observed_history_full_v1', ordered_refill_entry_mode='fixed_chunk0_prepare', ordered_besieging_entry_mode='observed_prepared')`。不为B改请求模式、不补查询。`fixed_chunk0_prepare`只deepcopy私有prepared scalars并作same-capture条件投影，`cache_write=false`，不写实际stock、physical DATA或observed prepared148；增长消费只读原row的stock/callback，忽略`same_input_conditional_*`。这不证明实际native preparation或ADD。

R06没有Move、stock initializer或换帅；但regular_core采样ON和debugger仍须如实记为研究环境，不能默认等于普通独立Barm。B的regular/完整route、同统帅等更窄门槛仍由实际端点裁定，不能仅因R06 fence通过就自动通过B。

`actual_supply_callback_observations_v1`与九族research sampling不是同一开关。冻结native在bridge启动时安装该独立journal，hook对实际callback forward一次，query只读取已发生记录；regular_core-only不证明这个journal OFF。旧机会文档“supply journal保持OFF”的文字不能覆盖实际安装与full叶。也不能仅凭源码安装推定本次capture成功：本次observer_installed、事件Province、sequence/failure和stock链才是结果依据。不增加toggle或native hook。

## 从R06原件到现有单站consumer的最小离线适配

原R06 actor JSON不是`normal_day`格式。最小adapter应只读取下列原件，先验证一次日步与来源，再生成**明确标为派生的索引/view**；它不调用SDK，不触碰游戏，不生成未来packet。编写本页时此adapter尚未实现、没有实际R06原件，故单站CLI接线资格未授。

| 现有B字段 | R06实际来源与必须保留的出处 |
|---|---|
| runtime/source proof | frozen/runtime/Q、retained handle PID/FILETIME、实际snapshot generation/actor及normal-S0证明；不得从旧PID或路径推断。 |
| day0/day1 endpoint | 各自原snapshot + full control row/full-wire proof +完整normalized row，原ArRg/DATA及actual commander/loaded features原件。缺after实际统帅时给出缺口，不以fallback、candidate或旧query当同帧after见证。 |
| original once claims | `day-53149056.once-claim.json`与`day-53149056-initial-resume.once-claim.json`的精确pins、原Arm/Resume/status控制行；未知动作不得重放。实际日期不同则按原claim真实日期取文件，不能套该名称。 |
| normal-day派生绑定 | 现有consumer需要binding/plan/helper/before/previous_complete/start/target；R06原claim只有machine/episode/pid/status/starting_date_raw/target_date_raw。adapter须验证这些原件后显式映射，保留original_once_claim pins，不能把新派生claim叫作当时原claim，不能仅填`qualified=true`绕过检查。 |
| episode | 原ordinary `episode_run_id=null`保留。若复用公共`FullArmyResultClient.bind_common_frame` managed-run派生view，保留`research_derived_episode_binding`和原件pin，明确不是原native episode。当前R10 runtime schema只接受非空string，不能捏造EP或追授one-life；兼容出处未明确时仅报告被动stock观察。 |

有真实正增长且全部必需原件/适配合同验通后，调用现有相邻单站CLI `qualify_one_b_site.py`，它直接使用上述共同consumer，不复制增长语义。SITE schema为`xar.e04.B-rest-site-input.v1`，含实际province_id/army_id及Evidence.root内runtime、normal_day精确pins。输出仍保持two_sites_qualified=false、formal_ABC_completed_arms=0、B_live_readiness_granted=false；不得把单站pilot变成B/ABC完成。

## 第二个候选1513：复用正常到站Save

同机器R0217实际从1506一次Move、七日到1513，最后normal Save/independent-after及normal-close-qualified=true。保存文件72,796,589B、SHA `475bd703436de962bcd380eedd9c94d9cca7eb052bcf43e42a5c709d16aa27ef`、date53147544；原件见[case结果](evidence/episode04-r0217-20261020/case/R04-BAYEUX-RESULT.json)与[正常闭场](evidence/episode04-r0217-20261020/case/normal-close-result.json)。2026-10-20T08:50:17Z只重新stat文件大小一致，没有读取/重hash大Save。实际路径与stat单独存索引，不作为跨机器前提。

这使1513成为未来正常source promotion/加载候选，可省掉回1506重复七日行军；**尚未激活该source，也没有证明当地正rate/eligible或增长**。旧one-life driver_state_replace的save_binding_mismatch保留，不用正常Save抹去它。后继需新鲜机器/version/runtime/Q/cap/normal-source准入。新场若已被Root另行授权，按原公共入口取得fresh snapshot→full strength→typed commander→independent snapshot；先筛headroom/final rate/resupply/bucket，再决定事前有限窗口，不盲等。历史1506→1513不授权2170→1513路线。

两个site可分别采样、同actor，consumer不要求pilot先split或必须同进程；各自须有独立事件，不得复用callback key。不同S0的两站资格不能拼成同T0的正式B/ABC。R01的2619虽历史eligible/+20，但actor31254、选军stock=cap300/300且十跳，不能把其资格移给33388；R211的1506真实0→0和负rate仅作负对照。

本页及索引的实际工作仅为离线代码/小原件判读，新增游戏/SDK/query/day/observer/build/Save均0。被动消费的限度不改变原场次容量和时限；原R06结束后照常OFF/Save/normal close，不为取得B正例延时。文档为180日复核的小知识记录，派生helper48小时复核；不续期任何旧存档、raw或容量许可。
