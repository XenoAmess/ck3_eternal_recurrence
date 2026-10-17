# 第一期 R6：准备资源联动、采用后态与两处原生缺口

`machine_id: 4-8e1c2f1861`。本页只消费 R6 的冻结原生回执和媒体小清单；运行来源为 `3d7a9f11d8fae7ca6465509a55c3999f571f1970`，CK3 1.20.0.4，PID **21920**／connection generation **1**，玩家完整 ID **15893**，日期 **51394920**。实际观察时间逐项列于下文；[小型来源与字段索引](evidence/faith-and-power-episode01-r0006/source-index.json)保存回执路径、size/SHA、帧绑定及未验边界。证据只属于本机器本场，不能移植成其他机器的安装或实机资格。

这是用户批准的独立机制实验。当前公共全流程仍为 **research holder，whole-product PASS 未授**；普通罗贝尔战役成绩不增加。本文是 R6 尚未正常退出时的阶段快照，不能作为闭场、资源已释放或 R7 已启动的证明。

## 准备输入和实际资源变化

R6 从原 F `F-pending-prepare.ck3` 冷载，输入 SHA `786afb9eb40e8952d8aeade35eebd869ad7c7383fc28894389e2859451f750f1`。挂载 0.2.0 的四文件 event-only，省去 bookmark/on_action。原 F 已含先前额外 2000；本分支 B 选项明示再加 3000、设置 once flag 并将个人礼仪改为 Maliki，累计额外准备量为 **5000**。原 F、旧 B/C 和 R5 存档均未改写。该包建立时的 `devotion_side_effect=Unverified` 保留，以下是后继实读，不回填其历史字段。

| 量 | B 前：14:00:40 UTC | B 后：14:01:20–21 UTC | 本次实际差异 |
| --- | ---: | ---: | --- |
| 虔诚钱包 `played_character_piety.raw`，scale=100000 | 225000000（2250） | 525000000（5250） | +3000 |
| 奉献度累计 `current_devotion_total_raw`，scale=100000 | 300000000（3000） | 600000000（6000） | +3000 |
| 奉献度有效等级 `effective_level` | 3 | 4 | 跨过当前等级门槛 |
| 个人 `rite_id` | 13（Hanafi） | 15（Maliki） | 个人礼仪变化 |
| `faith_id`／`faith_main_rite_id` | 50／13 | 50／13 | 未变 |
| `spiritual_fulfillment_raw` | 2000000 | 2000000 | 未变；不是虔诚钱包 |

两份 religion 回执及其快照均绑定 actor15893/date51394920；before 为 `native:2`／public revision3，after 为 `native:3`／public revision4。`r6-select-prepared-B-once-a01` 在 **14:01:19.838320Z** 对本进程 actual event1 提交 option_number2／native index1，原事件随后消失。不能把本场实例1硬写为其他进程的协议条件。

智能体应把钱包、奉献度累计、有效等级和个人／主礼仪分别建账。**本次准备同时改变了资源与个人礼仪**；若拿 R6 与只额外准备2000的 [R5](faith-and-power-episode01-r0005-adoption.md)比较，不能把许可差异只归因于 Maliki，也不能假设准备资源不影响奉献度。这里没有独立隔离“仅加资源”和“仅换礼仪”的因果试验；采用付款后的奉献度亦未在这批回执中另读。

## 一次普通采用的证据链

**14:01:22.463510Z** 的 `r6-before-adopt-detail-a01` 同帧绑定 actor15893、parameter/selected HolySite32。原版普通 `CanConfirm=true`，requirements bypass 原值 **0**，结构化报价为 piety raw100000000，即 **1000虔诚**，native_affordable=true；该决议冷却当时 absent。报价只是本场当前报价，不是所有采用的固定费率。

**14:02:04.716897Z** 的 `r6-confirm-adoption-once-a01` 只尝试一次原版 Confirm。动作包仍标 `business_outcome_observed=false`；它附带的即时快照钱包也仍为5250。实际生效由随后独立读回证明：

- `r6-after-adopt-snapshot-a01` 钱包变为 **4250**，与报价同为实付1000；玩家、暂停日期不变。
- **14:02:05.591703Z** 的 `r6-after-adopt-sites-a01` 把 Faith50 名单从 `[26,27,0,14,29]` 更新为 `[26,27,0,14,29,32]`。site32/type `nadjaf`／barony6650 的实际关联中，Faith50 为 `faith_lists_site=true, eminent=false`，因此本次新增的是**普通圣地**。
- 同一 after 包还观察到 Faith51 关联且 eminent=true、site32 库存为空。R6 的 before 没有同站51的完整等级或库存读回，不能据此声称它们前后未变；也不能由关联／空库存推导 Active 或受益者。
- 独立 `r6-after-adopt-cooldown-a01` 读到 `adopt_holy_site_decision` 的 cooldown `present=true, active=true, expiry_raw=51438720, current_counter_raw=51394920`。接口明确 `calendar_conversion_observed=false`，规划器保存原生计数并在将来重查，不自行把差值换成已验证日历期限。

对规划器而言，ACK、钱包差额、成员集合和冷却分别是四类证据。名单已新增且实付款成立时，不能因为旧详情窗口消失或 ACK 自带快照未刷新而重复 Confirm。

## C2、展示通道与下一分支

**14:02:29.577853–14:02:30.666059Z**，原生 checkpoint 实际保存 **50,210,503 B**，SHA `7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e`。**14:03:28.219596Z** 的冻结回执把同 SHA 原件保存为 `scenario/saves/C2-nadjaf-adopted-funded.ck3`。本文消费保存／冻结回执，没有重新 hash 大存档；C2 冷载、Driver 完整恢复绑定和 R7 行为仍须独立验证。R7 母档是这个 funded C2，不是 R5 的 C，也不是导演方案的第三配置。

Faith50 的 open 在 **14:05:02.691241Z** 返回 pending ACK；**14:05:03.862554–14:05:04.515816Z** 的独立 query 才读到当前 Faith50、原窗口根和 `effective_visible=true`。人物 open 的 MCP 原包在 **14:05:29.845216–14:05:30.619209Z** 请求15893，返回 pending ACK；独立 query 于 **14:05:30.943161–14:05:31.905578Z** 才读到 Character15893、有效可见。两项 open 的即时 `current_subject_id=0` 均未作为实际选择；两项独立 query 均无 dispatch。这闭合了本场目标绑定及展示后验，不能替代业务许可。

原片稀疏帧另显示 Faith 页头 Hanafi／Sunni，而人物页显示 Maliki；结合原生主礼仪13／个人礼仪15，二者对应不同对象，不应把 Faith 页头当成玩家切换礼仪失败。Faith 的圣地标签页未在该素材中打开，不授该页列表读取或导航资格。

## 两个实际缺口：保留 unknown，不能写成业务拒绝

| 本场请求 | 实际结果 | 规划器应如何继续 |
| --- | --- | --- |
| 14:03:30.826879Z，`ck3_open_holy_site_decision_v1(action='promote',holy_site_id=32)`，意图观察 Emax 分支 | `entry_parameter_self_declaration_unavailable`；accepted/available=false，native_dispatch_attempted=false，dispatch_invoked=false；后读详情 unavailable。 | 这是本工具的参数声明／入口绑定缺口，**没有得到原版 Emax 的业务拒绝，也没有 Confirm**。先修通道，再重新取得完整条件、参数、普通 CanConfirm 与报价；不修改名额规则来消除工具错误。 |
| 14:05:34.781657Z，Baghdad14／artifact64 的 relic permissions query | 玩家库存 `[188,189,237,267,277]`、原生候选 `[237,267,277]` 有实际来源；site14 slot0=64。窗口 context 因 `holy_site_window_registered_owner_unavailable` 不可用，can_enshrine/can_remove 都是 unavailable/null，action_ready=false。 | 库存与候选已知，**供奉／取出许可仍未知**，不是 false。修窗口owner绑定后读当前按钮/对象/slot，再决定；不可只凭候选列表提交动作。 |

Root 已进行有界诊断，两处 native 修复在并行；本页不提前给新候选或下一 DLL 实机信用。relic query 的 `evaluation_context` 明示无 gameplay command/window/cache 写入；script RNG effects 仍 unknown，不能扩大成无一切运行副作用的承诺。供奉、取出、晋升、降级、独立退出均未因这些观察完成。

## 影像和并发状态的同一截点

媒体来源为外置 `production-candidate/r6-media-increment-a01/R6-MEDIA-SOURCE-INCREMENT.json`（观察 **14:21:17.337709Z**），本页仅消费这份小清单，**没有重 hash、重解码或复制媒体**。

- take01 自动录制120秒，首帧 epoch13:54:08.268088Z，末帧估计13:56:08.235088Z；B 在14:01、采用在14:02，均在片外。它只能候选用于准备披露，不能剪成 R6 动作发生过程。
- take02 为55.866秒／1112帧 VFR；严格全解码／全帧PTS与稀疏画面 QA 已由制作 lane 完成，Faith／Character／Baghdad 的实际窗口切换可供剪辑。小清单声明新增上下文候选 **32秒**，但明列 take02 的8／6／10秒三段合计24秒，另8秒尚未在该清单逐段冻结，须由制作 lane 对账；本文不把32当作已独立核准的区间总和。它们不是新采用、晋升或供奉过程；最终PTS、clean-span、完整1×人审和新旁白仍未签。
- 已有29:24.267机制研究讲解审阅 MP4。**正式第一期未完成**；不能把 R5 的采用镜头改标成累计额外准备5000的 R6，研究讲解片也不抵扣正式动态镜头。

| 并行 lane | 此截点状态 | 下一门槛 |
| --- | --- | --- |
| R6 实机 owner | 准备／采用／冷却／C2及两窗口独立后验已有真实回执；Root 保留现场，尚未以本文证明正常退出。 | 原有deadline、同进程诊断与正常闭场。 |
| 两个 native 具体 bug | promote参数入口、relic窗口owner绑定正在修；已保留真实 unavailable。 | 新源冻结、适当离线资格、下一受管加载实读；不热改本场身份。 |
| R7 independent abandon | C2母档已经冻结；**等待 R6 真实退出及现场释放**。 | 独立冷载C2和完整身份，然后单次合法abandon与成员／钱包／冷却后验。 |
| creation 只读／UI | 独立来源合同、只读 MCP 和 typed UI 候选推进；不借 R6 live。 | 各自离线资格及实际新场景条件／UI后读，未执行创建。 |
| relic 动作候选 | 独立接口／来源施工；当前 permissions 尚 unknown。 | 真实许可、一次动作、库存owner／slot／资源及独立后态。 |
| CI | 运行源3d7a9f11的 shared acceptance 为旧 Character fixture 断言 RED；外置窄修8/8 PASS、文本扫描通过，待闭场后合入。 | 新提交独立 CI；保留旧 RED，不以源码夹具通过替代业务。 |
| 后期 QA／正式编辑 | 本批 raw QA 和32秒上下文候选已交付；原始动作缺片如实保留。 | 补合法业务／动态素材，再冻结声画、时间线与人审；不宣布正式片完成。 |

详细输入的限期保留与用途沿用通用存储策略；媒体清单自身复核时点为2026-10-19T14:21:17.337709Z。本页不改变大文件保护或删除范围，不自动续期。旧 R5、旧准备包和既有 CI 失败记录原样保留，此页只追加 R6 阶段实证。


## 后继闭场、本地交付与有限保留（补录2026-10-17T14:44:27.280504+00:00）

`machine_id: 4-8e1c2f1861`。前文“尚未退出”是原阶段截点，保留其索引原样；此后 [闭场追加回执](evidence/faith-and-power-episode01-r0006/closure-followup.json)消费新原件，证明 R6 已正常闭场。**14:38:33.968178–14:38:41.853679Z** 只提交一次 typed `confirm_desktop`，返回仍为dispatch_pending；**14:38:51.635291–14:38:51.880808Z** 独立 retained HANDLE observer 以0次新提交读到 CK3 PID21920／原creation identity、signaled／exit0。确认 ACK 与退出后验分别保留，未把5秒观察超时重放成第二次退出。autosave 已由 Root 查看原始未勾选画面，但本接口 `autosave_verified=false` 原字段保持。

`normal-quit-root-result.json` SHA **123590be11fbd8a7d3bc5f7efc63b6a9787129376f320465a4fe08655c04b868**；`normal-close-result.json` SHA **56c67045bd038bdc2adc13ca38ea4311d319208c33fc6c954ac3ed973f0898cf**，后者 `normal_close_qualified=true, business_pass=false`。原 public Popen（PID20628）和host（PID15708）均有actual original wait／return0；keeper原件登记PID3504，actual exit0。Root另实际报告工具会话run75438／keeper10480／overlay3505均wait0；这些会话号没有冒充OS PID，overlay的原进程回执本次未单独读回。

**14:40:07.983848Z** 任务总线 CAS **11414** 将 `faith-e01-shared-a07` 标为done／resources[]。闭场／释放这一门槛已满足，R7可按新的独立准入安排；**本补注没有启动R7**，也没有把research holder完成提升为whole-product PASS、修好promote/relic业务或补齐动作影像。

用户本会话选择“**先提供本地文件，继续制作（推荐）**”，本次授权由Root复述并见此前13:16:56 UTC后继记录；原用户消息的精确UTC未另行冻结，不补猜授权时刻。现有[本地审阅入口](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/full-review-build-a01/delivery/LOCAL-REVIEW-README.md)可先交付采用短段／机制讲解片，正式制作继续。本地交付授权不等于听审、clean-span、完整1×观看或正式第一期签核；本补注没有做云端交付或产生新MP4。

有限保留按[通用策略](../storage-retention-policy.md)／[参数](../storage-retention-policy.json)执行，owner为Root。本次文档计划把**2026-10-19T14:21:17.337709Z**作为下一复核点，与已有媒体增量清单的期限一致：仅保护R7仍需的F/C2、正式剪辑仍需的两take，以及两个未解native缺口的最小诊断／闭场原件；到点复核具体引用、替代证据和容量，不自动续期、不把整场目录永久保留。F原有更早的检查点继续有效；本补注不推迟任何既有expiry。已交付MP4按现有登记的delivered_media720小时和大文件168小时先复核规则，不因复制或本补注重置时效。这里是**有限保留计划**，没有声称已改资产台账、执行回收或部署自动GC；实际删除仍须逐项满足闭场、无占用／当前引用、无有效保护、期限和精确路径门槛。
