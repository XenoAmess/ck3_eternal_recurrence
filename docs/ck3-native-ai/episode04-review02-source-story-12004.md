# Episode04 Review02：机制、现场结果、镜头与agent消费

2026-10-15，来源机器 `desktop-3fevhd2-1c74096080`，只读基线 `1463bd9b4b89612d283dd45ac4ec9efbf22f048d`。
本页连接视频解释与agent开发；不产生新的游戏、研究卡、clean素材或影片信用。

## 录音与编辑落点

[24段中文草稿](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a02/narration.zh-CN.md)将旧William/.3结果改成当前可讲的有界内容。
[逐段claim→结论→shot→缺拍→API](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a02/claim-shot-agent-map.json)保留原段ID。
[精确来源与实际行号](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a02/source-index.json)列本轮小包与接口定义。
这是24段替换草稿；另45段、整片顺序与时长需总稿收束，不把旧数字直接接上。没有TTS或新编码。

## 源码与实机分别回答什么

| 主题 | 当前可讲机制 / 实际事实 | 智能体消费入口与unknown | 现场和主片仍缺 |
|---|---|---|---|
| [R03围城扣兵](episode04-siege-loss-12004.md) | 完整同实例writer可证一次unique physical debit；围城/raid共用阶段，因果解释还需实际围城且raid=false等上下文 | `evaluate_army_physical_loss_evidence_12004`；预算、request、cache差、Army净差不填physical值；空史不等于零损失 | 自然正事件与稳定上下文、动态结算；当前离线实际Query3空史被正确拒收 |
| [R04县进入](episode04-county-entry-loss-12004.md) | actual4 direct return24E25EE与周期direct不同；residual2A958E8共用，外层原因未知 | `army_county_entry_loss_evidence_12004`复用R03primitive，保留native原标签/完整generation/fence；不猜invocation owner或县损失总额 | 真跨县→county-primary正physical事件；若要residual总额还缺外层parent关联 |
| [R05低库存](episode04-starvation-loss-12004.md) | runtime loaded表原版边界S<10，exact10非正例；先更新stock再算supply预算；loaded覆盖、fleet/grace和整数条件保留 | `assess_episode04_starvation_loss_12004`区分preferred physical primitive和端点候选；旧日志无共同invocation，严格饥饿归因unknown | 正常临阈值场；[新join](army-actual-supply-parent-join-observation-12004.md)离线编译/wire GREEN但未进当前R0174/a05，仍缺新生产部署及自然实测 |
| [R06补员](episode04-refill-application-12004.md) | prepared/F、request/q、actual ADD、pair clear与cache refresh分层；物理七槽窗口净差不是正补兵总量 | `qualify_regular_refill_application_12004`→`refill_application_qualification_v1`；actual_ADD=false/applied_positive_refill=null不提升；开关不是所有q乘一个enabled | instruction ADD producer、合法toggle callback及独立state；同自然机会对照/动态画面 |
| [P0-SPLIT / R09特殊记录](episode04-special-troops-split-merge-12004.md) | 1/1是ArRg缓存，不自动是骑士/物理补兵；实际统帅与capacity另读；当前.4 getter不替旧.3executor授资格 | `classify_regiment_observation / identify_split_sibling / compare_split_merge_cohorts / read_bound_current_commander`；Character bool true/false/null分开，原cohort与extra不删 | 正常.4 split/merge微实验、出生producer及真实统帅/库存后态；旧B拒收保留 |
| [R07登船实付](episode04-r0173-boarding-halt-12004.md) | R0173一笔personal SUB3金币，whole原callback账户余额25448407→25148407，不是指令局部probe；其他军队费率未知 | 复用现有现金query与生产strict journal normalizer；[便携R0173重算](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/verify_r0173_evidence.py) | 同T0无登船对照未补，整卡partial；20.1秒候选连续审阅/时码绑定 |
| [R08军事维护](war-payment-generic-context-12004.md) | generic personal ADD上下文raw公式已读，字段生产者/更新节奏/军事applied分量未闭；NET/余额差非军费账 | 现有cash query/strictconsumer只保真raw；军事维护仍null，不由正ADD/当前月率推免费或实付 | 自然真实settlement cadence、实际军事component与同次wallet write；不无限等或做ABC费用排名 |
| [A整军直达](episode04-strategy-a-12004.md) | 已有离线决策/后态consumer，无新T0/结果；真正到场必须current/state/empty route | `admit→observe_move→update→report`；一次Move建议、ACK不授后态，current和first arrival分开 | 新正常T0全输入、preview/一次Move、逐日真实到场与镜头 |
| [B拆分休整重并](episode04-strategy-b-12004.md) | 正变化率不等于库存增长；驻留阈值/最长时间预冻结；合法新增记录/统帅不删 | `strategy_b.py`只读事件链；unknown/rejected不自动重发；原cohort/allstrategy分列 | 两处真实stock增长驻点、R09短微实验、新B全链与共同目标到场 |
| [C整军经中转](episode04-strategy-c-12004.md) | whole-via保持整军，不变成等补给策略；真中转到达后才提下一段 | `start→propose_move→observe / stop / outcome`，非空完整route与原路线后缀；unknown不重发 | 新C逐段preview/后态、逐exact日/真实终点；旧15次偏差不复绿 |

以上新增Python接口仍以各自外置补丁为候选；只有既有比较合同/普通MCP路由是本基线已入库能力。该表不声称补丁已经应用或planner已经调用。
公开入口复用 `ck3_take_snapshot`、`ck3_query_army_strengths`、`ck3_query_army_commander_candidates_v1`、`ck3_move_army`；preview是现有 `ck3_execute_step(step="preview-move-army-…-to-…")`，没有发明新preview/toggle MCP。完整full Driver JSON和同帧snapshot是consumer输入，MCP摘要不能代替完整journal。

## 三方案结果表的使用边界

沿用[比较合同](episode04-comparison-contract-12004.md)：同正常opaque save SHA、独立冷载同T0、完整原始整数/DATA与实际统帅，逐日native exact+24，实际首次到达区间≤1日。到达表按各自到场时点；共同日期表仅在三臂都有相同第7/14/21/28日读数时横比。D90只在预注册统一到达后政策且实际续到共同日期时输出。

费用需真实R07/R08 applied ledger与同账户/区间核销，未合格保持null。钱包净差单列，expenses/NET已含军费则不重复扣。B合法自然新增1/1与换将保留为策略后果，不静默修复；原cohort和全部strategyArmy分列。world events保留，测量失格不改成策略失败。

旧B在+38日冻结条件未通过而停止，剩52日、London=null；旧C有15次两日偏差，抵达(75,77]、NOT_GRANTED。离线consumer能实际拒收这些旧小记录，却没有新A/B/C实机结果，不给胜负或费用排名。

## 当前镜头与下一步

R0173现成候选为原片147.5–153.5、153.5–161.6、168.9–174.9秒，共20.1秒；只够供登船前/转换/船模后态选镜。三段均未连续clean签核，不能据抽帧认定全段干净。费用归因来自原生证据，不能由顶栏像素倒推；SDK wall timestamp与encoded时间未精确校准，不给精确付款帧。

R0173未锁Halt原生后态已闭，操作晚于360秒原片结束，Halt没有入镜。R0174在本稿来源切点只已加载；当前正在由Root现场执行的动作或新录像一律pending，待实际回执再追加，不能将R0173镜头改名新场。

最短编辑收口先完成Halt原速动作/次日后态和登船候选连续审阅；R03/R04以现有writer取得真正正事件；R05/R06按具名native缺口各闭一条最短真实应用；R09微实验后再冻结正式ABC。解释卡只解释已闭源码，不能填缺失动态过程。

严格研究仍R00/R02/R11=3/14=21.4%，R07部分闭；本页新增信用0。原Review01 28:55.80成片/既有交付事实保留。此24段是新录音草稿，整69段全文/TTS/重剪/新成片均未由本包完成，机器审计与人工1×审片/精确bytes签核分别记录。

## 编号与跨机器复用

导演案用P0-SPLIT等主题编号；原Review02实验卡R08是维护费、R09是特殊1/1/统帅拆合。本页同时纳入这两个主题，不静默更改卡号、旧账或分母。
代码和共享专题落入仓库后，其他机器可按相对路径读取、重算已归档小证据；本机绝对来源路径只追溯来源，不是运行依赖。各机器的新实机仍独立绑定版本/build、普通来源、machine/PID/create-time/generation/episode与实际结果。

## 2026-10-16 本机R0177闭场、R03原件与story-a05草稿

本段所有现场、素材和稿件事实均属 machine_id: `desktop-3fevhd2-1c74096080`，按Root本次实际回执滚动追加。

- R0177已有Root实际CLOSED回执：3219 B，SHA-256 `9a2f12db0d934f8cb01236c7ca8e88a1515b18ef552677ccc13df70841bc9797`。coastal原片45秒/1350帧，完整解码PASS；`clean=false`、`human=false`，不授连续clean或人工签核。
- R03原件在raw53147472、同一callback188中，7条preferred writer实际扣兵11（1+1+3+1+2+1+2），siege11/raid0，原件正消费通过。正式整卡审结仍待Root；本次汇报暂保留整卡5/14＝35.7%、核心业务3/11，不先增加分子。
- [story-a05完整草稿](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a05/README.md)为69/69＝100%，8351字；`TTS/provider=0`。这是草稿接受率，不等于最终冻结、声音、新成片或人审完成。
- 共享源码解释见[拆合军库存权重/取整顺序](episode04-split-merge-stock-weight-order-12004.md)、[统帅容量与零准备量](episode04-commander-capacity-zero-preparation-12004.md)。新增source的最终提交、a08 DLL、构建及新冷验结果由实际回执另记，本段不预填未来SHA、CI通过或实机资格。

当前交接与后续来源以[本机交接入口](../handover/2026-10-15-war-episode04-machine-resume.md)为统一转链。
