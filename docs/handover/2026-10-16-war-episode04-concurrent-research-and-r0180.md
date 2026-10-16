# 战争四期：并发研究接点与R0180普通陆路抵达

编制时间：2026-10-16T01:52:24.990573+00:00；执行机器`machine_id=desktop-3fevhd2-1c74096080`。
本页供其他机器和智能体发现可复用知识；机器部署、安装、容量与实机结果只属于列明的来源机器和当次PID。
新机器须另核自己的machine_id、Steam离线、EXE/build、runtime与存储准入。

## 当前严格状态

研究核心 **R00/R02/R03/R11/R12/R13，6/14＝42.9%**；R03–R13业务核心 **4/11＝36.4%**；
新版合格动态 **0/11**。本轮知识归档和source/fixture代码没有增加上述信用。
R01 ready T0尚待实际同帧/统帅/地点/正常保存绑定，R04/R05/R06及R07完整配对未闭；
R10三臂未完成，没有winner。人工1×完整观看、签核和新版完整成片交付尚未完成。

编制时Root已把约200个并发成果路径放入主树，提交/推送另由Root收口。
R0180实际source和native build均是`c4992c304d196135d9590799d69ffb3c9f5510e6`，运行a09，
不能把后来接收的源码追认为R0180已部署或已有新live业务验收。

## 新的共享接点

| 工作 | 文档/代码入口 | 可用事实与限制 |
| --- | --- | --- |
| 县进入predicate | [condition](../ck3-native-ai/episode04-county-entry-condition-12004.md)、[actor wrapper](../ck3-native-ai/episode04-county-entry-actor-wrapper-12004.md)、[relation core](../ck3-native-ai/episode04-county-entry-relation-core-12004.md)、[CCounty receiver](../ck3-native-ai/war-county-receiver-pointer-12004.md) | exact4来源树与原条件分支，不把地区/日期或净减少直接授作county writer。 |
| 县预览 | [preview condition](../ck3-native-ai/episode04-county-entry-preview-condition-12004.md)、[strict contract](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_preview_condition_contract.py) | 同当前主体/目标的只读输入；preview不是实际进入或actual debit。 |
| ready T0 | [决策入口](../ck3-native-ai/episode04-ready-t0-decision-12004.md)、[strict consumer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_ready_t0_12004.py) | 复用full DATA、typed current commander、cash、occupation，产出下一窗口clock/fences；不自动授R01闭合或新信用。 |
| 实际ADD | [instruction publisher](../ck3-native-ai/episode04-refill-instruction-add-provider-12004.md)、[hardware observer](../ck3-native-ai/episode04-refill-hardware-add-observer-12004.md)、[live consumer源码](../../ck3_autonomous_player/native_bridge/research/refill_add_live_12004/consume_live_refill_add.py)、[下一场](../ck3-native-ai/episode04-zero-readiness-publication-next-scene-12004.md) | 新publisher与线程owner修正、严格consumer为source/fixture能力；实际ADD、自然owner及R06卡还需真正新现场。 |
| 补员开关 | [12FF8D0 command](../ck3-native-ai/military-refill-toggle-command-12ff8d0-12004.md)、[1303D40 final target](../ck3-native-ai/military-refill-finaltarget-1303d40-12004.md) | `12FF8D0`目前只证owner+desired与submission。它不证明命令何时真正执行，也不把提交ACK或目标状态端点推成callback执行。 |
| R10共同终点 | [A/B阶段入口](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/README.strategy_a_stages.md)、[B horizon](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_common_horizon.py)、[C horizon](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/common_horizon.py) | 三臂共用absolute horizon、抵达/停止/失败按实际保留；source-only，不补三臂终点、同长实付或胜负。 |
| R10证据容量 | [比较consumer](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py)、[阶段A](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_a_stages.py)、[B](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b.py) | 按证据文件角色在读取前检查上限；完整Driver结果与compact MCP摘要分列，不复制大query给多个消费者或把预算放宽当验收。 |

## R0180的实际身份、推进、关闭

来源根`C:/ck3-e04-resume-20261015-a01/live12004-logistics-next-a09-a01/`；
run `desktop-3fevhd2-1c74096080--vanilla--R0180`，PID **16736**、create FILETIME **134365825176284454**、
generation **1**、episode **native-31254-75ef9942b4cf**，actual actor **31254**、Army **18**。
稳定角色来源是历史人物1128/Robert Guiscard；1128不是游戏年份，29829是旧scope错误期望，不能跨进程硬搬runtime ID。
实际游戏目标为1.20.0.4/Steam25734779，既有exact EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本页没有重新hash游戏EXE。

Root CLOSED记录共 **5个实际自然日**。仓内[native boundary](../ck3-native-ai/acceptance/2026-10-16-r0180-land-arrival-media/native-boundary.actual-a01.json)
独立保留day3/4/5的sentinel start/end、generation和每次exact1tick：day3 raw53147544、day4 raw53147568，
仍在2635、route[2645]、native/UI为sieging3；day5 raw **53147592**到2645，空完整route、**regular1**、非combat/retreat。
有Move路线不等于原生状态已是moving。R04 actual条件false、县正physical事件0且完整窗口缺失；
“无匹配事件”不等于观测到零总损失，不授县损耗正例。

关闭前`arrival-closure-a01/SAMPLING-OFF.actual.json`于 **2026-10-16T01:07:46.106355Z**
记录natural phase/regular core/assault/gathering/cleanup/prefix及payment已独立读回OFF、busy=false、clear完成。
随后正常保存于 **2026-10-16T01:08:00.410881Z**：date53147592、actor31254、normal ordinary/xar_off，
**72,973,969B**，SHA **`e4cac633d1b27ecaa063ecf6a8ae7f31ac8b9ca99edf1fb8517ec4d2844e4892`**。
这里只复用1379B正常保存回执，不读大存档。

[CLOSED](../ck3-native-ai/acceptance/2026-10-16-r0180-land-arrival-media/CLOSED.actual-a01.json)
于 **2026-10-16T01:15:12.595077Z**证明normal exit0、game/recorder/SDK/keeper关闭及source freeze释放；
3476B，SHA **`3afa91133b708a1ecdad4a0745c2fdaf9d1e4fa4b925dea4ec467ed8ddc05955`**。
采样OFF和正常退出不自动扩大为下一场部署/权限/业务资格。

## 45秒普通抵达媒体及可说范围

[仓内小索引](../ck3-native-ai/acceptance/2026-10-16-r0180-land-arrival-media/INDEX.actual-a01.json)
绑定原片 **94,042,804B**、SHA **`c51352cc2ac0f43766bc42c6439569cf62316db84c9cf6adb6e1ee9dc59d8964`**。
已完成一次whole strict decode：**45.000000秒、1350帧、2560×1440、30fps、无音轨**。
记录在[媒体报告](../ck3-native-ai/acceptance/2026-10-16-r0180-land-arrival-media/attempt-a01/report.json)。
本次知识增量只读小JSON，没有重读/hash/decode原片，也不复制视频、音频或大packet。

[已有AI视审](../ck3-native-ai/acceptance/2026-10-16-r0180-land-arrival-media/visual-review-and-spans.actual-a01.json)
实际样本为原片PTS **0/4/8/12/18/40秒**：前四样本在旧位置、面板“围攻”及1%；18/40秒在新位置“待命”及0%。
六样本选中军队均为 **1184人、300/300**。右军务面板的总军力/事件兵属于不同集合，其下降不能当选中Army18县损耗。
候选素材范围为0–8秒地理/围城上下文、**(12,18]秒抵达视觉bracket**、18–40秒抵达后留屏。
右侧军事面板是持续构图限制，需按实际剪辑政策处理。

六帧不构成连续观看；样本均暂停不能证明整段一直暂停。原生回执墙钟与encoded PTS未标定，
exact first-arrival PTS仍null；不把ACK相差15.74秒叫实际事件时码。
这些只是候选，**continuous clean=false、human1×=false、human signoff=false、dynamic credit=false**。
可供普通陆路抵达说明，不授R04真实扣兵、整章闭合或新版完整成片。

## 真实wire纠正：ready T0 regular为1

R180 day5真实字段揭示a15消费者与合成fixture曾误用regular0。旧8项synthetic GREEN保留为当时历史，
不能证明这个实际enum入口。Root随后明确授权只改消费者和fixture这两个main路径。
已改为`regular:1`，新增“actual enum1接受、legacy0拒收”的反例；一次focused **9项通过**，
观察时间 **2026-10-16T01:44:24.690894+00:00**。仍是语义/源码资格，没有新SDK、构建或实际ready T0信用。

修正后消费者18513B，SHA`c32ada93dda23e9ef19c64250bd95b84ff89c98b816b5b9c9ae755eb9ce2417c`；
fixture11504B，SHA`589e0fbe8bda965e9da800b6d9c834204585c21ffe37d0336b90189ddf1eacbb`。
外置`knowledge-index-r0180-a16/READY-T0-ENUM-FIX.actual.json`和标记`ALREADY-APPLIED`的exact diff保存此次授权、
唯一一次结果与前后pins；不要用旧a15 candidate覆写这两个已修正文件。

## 已执行清理与不可再承诺的输入

本机清理逐项按[统一存储政策](../storage-retention-policy.md)及明确用途审阅执行。以下是实际删除的逻辑字节，
不是对磁盘可用空间净增的独占归因，也不表示其他机器已清理或未来容量已准入。

| 实际清理 | 删除逻辑字节 | 精确小回执来源 |
| --- | --- | --- |
| 旧OBJ/intermediates，2233项 | **699,285,156B** | `capacity-lane/old-controls-intermediates-a10-retirement-a01/RESULT.actual-a01.json`，2026-10-16T00:48:14.493729Z。 |
| E02旧working，36项 | **1,146,465,214B** | `capacity-independent-old-video-retirement-a03/RESULT.actual-a01.json`，2026-10-16T00:59:55.825999Z。 |
| E03完成用途的3个无损stem | **1,515,045,948B** | [retirement.actual](../maintenance/storage-retention-2026-10-16-e03-completed-stems/retirement.actual.json)，2026-10-16T01:19:39.701473Z。 |

上述外置相对来源均在`C:/ck3-e04-resume-20261015-a01/`下，机器ID见各回执；本页不遍历/重hash旧媒体。
E03 a03/a04 lossless picture与a04 narration-grid已`retired_unavailable`，旧manifest和此前别名历史保留，
压缩final不能代替那些相同字节的角色输入，**不再承诺无损重剪/重建**。a03/a04 final、现用theme保留；
**D盘v4原raw仍HELD、不删除**，v4草稿final也保留，不能因此宣称已完成交付。
准确源可用性见[availability](../maintenance/storage-retention-2026-10-16-e03-completed-stems/availability.actual.json)。

## 下一步执行顺序

Root先收口本次source/知识提交、推送与必要检查；本页不冒称这些步骤已完成。
下一现场另核actual build/hello/observer gates，用新暂停F的Army18及真实目标决定ready T0、县条件或ADD机会；
normal save、clock、完整DATA与journal fences分别保留。普通抵达片段可进入候选素材池，
连续clean、人工1×和完整成片签核继续独立完成，不能用source结果或六张图代替。

本批组合验证：17 个 Python 入口、66 个聚合行为案例已覆盖；新增历史 sidecar 准入连接检查通过，44 个 Python 文件 AST、45 个已有 JSON、5 个 ZIP CRC 与改动范围 Python-only 检查通过。修复了 B 测试替身的旧构造签名，以及 actual regular=1 与旧 synthetic=0 的不一致（旧0明确拒收）。Windows 原生构建、原生 fixture 和下一场运行仍待执行，详见 [source qualification](../ck3-native-ai/acceptance/2026-10-16-concurrent-source-intake/QUALIFICATION.json)。
