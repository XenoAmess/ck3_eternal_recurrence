# G2 剩余里程碑的并行离线研究

2026-10-16。此轮研究全程不操作 CK3、Steam、OBS、桌面、Native pipe 或活跃 Driver。自动游玩与演进由原 owner 持续运行；研究候选不作为当前会话的停机条件。

新目标是**连续三十游戏年没有需要停机修复、阻塞自动游玩的错误**，由主 continuity ledger 单独计量。它与原 G2 八项资格、累计已玩年数分开；既往带修复的累计约二十一年不追认为稳定三十年。

## 八项定义与本轮范围

原定义和分母见 [g2-requirements-v1.json](../autonomous-agent-progress/g2-requirements-v1.json)。编号为 M0–M7，正式累计仍为 **6/8**。

| 项 | 原完成条件摘要 | 原状态 |
| --- | --- | --- |
| M0 | 同帧继续/白和/投降比较、一次退出、后置与冷恢复 | complete |
| M1 | 当前统治者/领地/关系实体目录及核心警报 | complete |
| M2 | 三个自然事件，其中两个多选，独立材料变化 | complete |
| M3 | 自然死亡前预测、继承对账、真实后继继续玩 | complete |
| M4 | 两年内建设、有用合法议会调整、真实封臣/派系干预 | complete |
| M5 | 至少五个合法外交或战争候选，完成选定路径 | complete |
| M6 | 谋略、制度/囚犯、非宗教决议/法律、活动生命周期 | in_progress |
| M7 | 多 ruler/seed/government，以及意图跨存档/继承恢复 | in_progress |

完成项只保留原合同信用，不外推为所有版本、战争、政府或未来事件全覆盖。本轮只拆 M6 谋略、M7 goal、M7 government 三个互不占用现场的小包。

## M6：普通回合缺 fresh Sway 接入口

源码基线为 00a70009。普通 Service 在已有 applied Sway ledger 上观察终态和材料；fresh Start 的 formal consumer 只由 native_auto_run 的 explicit-target bounded 分支调用。该分支会额外 checkpoint，并在多数结果后 break，不能整段搬入持续流程。

现成 MCP query/start/receipt 已在 bridge/mcp_server.py 注册。源码亦已有具体 completion 因果关联、中立 common end、独立具名材料和 following/cold writer。本次没有发现需重写这些 writer 的新缺陷，也不新增“必须穷尽所有终止原因”的门槛。

最小下一施工是在普通 life-advance 候选阶段复用 once-only consumer，由当前角色的有用 selected relation、同帧 native final legality 和材料基线生成一次机会；缺输入则继续游戏。query/submit 仍经同一串行 owner，不每日扫全部目标，不调用 bounded runner，不改变正常九十游戏日存档节奏。实际新 Start、真实终态、有益材料与后续普通回合仍待观察，M6不授完成。

离线 source 路径和下一 recipe 位于外置研究根的 m6-scheme；REPORT.md SHA-256 bbe01faa6871758ff8fdf7cd64f3f76e2ed238572ce800e8241020262897c3ce。没有新增游戏动作、Native 构建或终态矩阵复验。

## M7：已保留真实 successor goal，政府玩法仍需分项施工

[新罗贝尔继承后意图观测](g2-successor-goal-observation-2026-10-16.md)复用两份闭场小回执，确认31254→40526的同一 dynasty_continuity goal已进入真实 successor SAVE，并在另一实际 Game PID 语义帧保留。随后已闭场 P06普通plan的 campaign_goal_plan_used又确认同一goal/campaign/current/progress四项全等，实际普通planner消费已补齐。完整物理 cold anchor 对比字段仍单列，不能据不同 PID、同日期自动补齐。

政府身份 observer 的 core_supported 是身份/core verdict。原始00a70009普通 planner 已通过 CampaignRoot 消费当前政府 key/flags，当时建设、LIFE、三类主动宣战入口均明确限 feudal；本日后续只拆建设的 Clan 窄分支，LIFE/战争不扩。普通路径没有调用旧内部 nonwar Government context leaf，不应为补 metadata 恢复旧公共受限模式或增加重查询。

一次合成的生产 scope 验证4/4：feudal admitted，clan/tribal/administrative outside_scene。建设 outside_scene 会保留原计划继续推进；这没有证明当前封建局有政府适配停机故障。

未来具体入口是独立 Clan construction scope，复用实际 native final legality、gold-only quote 与现有交易/材料消费者，并核对其真实净收益输入；Tribal 非金币资源身份/余额和 Tribal authority 为不同 provider 缺口，不随身份白名单一起放开。不为本场研究切换 ruler/seed 或重启游戏。

外置 m7-government/FINDINGS.md SHA-256 0bb109fda10617ba0ca41c73b9799a02c61ff64e81a6578fa7fcfaabd8ebbf69；SCOPE-PROBE-RESULT.json SHA-256 230b22d561307271ba9ee0b83012e691464c3303fd37544a99ad3490120f21eb。4-case仅证明合成生产 scope 分支，未增加政府资格或M7完成。

## 03:22 CST 后续静态/离线增量

[Sway ordinary scheduler](sway-ordinary-target-scheduler-12004.md)已核对当前 .4 两份完整 stock 文本与旧 .3 SHA完全相同，关闭该特定版本文本差异缺口；两块分别通过既有 open_kaishek parser/CST。新纯 helper 使用当前同帧 direct-vassal 原生顺序轮换，复用原 once-only consumer，pending/applied只读观察按月，两次真实无操作冷却30日。10项初始合成、terminal1与full32-ID1增量分别通过，未重复旧测试。普通 Service hook仍未应用，native最高 sender score并未宣称复现；新真实 Start、终态、有益材料与following仍缺，M6不变。

[Clan construction scene](m7-clan-construction-scene-12004.md)公共源码仅拆建设资格，复用当前 played actor自身地产、native final CanConstruct/gold-only quote和同帧cash-v2 NET预算；Clan可选观测缺失保留原推进。原封建 helper逐字委托、pending/material/cold逻辑保留；Tribal/LIFE/战争不扩。新增Clan stock块实际parser通过，一次原外置10项合成与一次新增可移植投影compound分别通过；全部0实机动作。公共代码存在不授Clan业务/政府资格，真实quote→动作→独立material→following/cold仍缺。

原G2仍6/8；M7后继普通goal消费已有真实材料，但完整physical cold-anchor字段与广ruler/seed/government资格未补齐。连续30年计数由主流程独立重起，研究不增加任何天数、录像或战争成绩。

## 出处与边界

本机外置研究根为 D:/codex-ck3-demos/2026-10-14-robert-30year/g2-m-gap-research-20261016，各包有 source pins、研究图、精简结果和存储分类。共同存储策略1.0.0；只生成小型记录，无重型写入、游戏复制或旧现场清理。

首轮 Python/JSON与原生 copied-callback接线没有 open_kaishek 可覆盖的语义，已记录 not-applicable；后续新增 stock 输入已各自实际 parser/CST 预验，仍不冒充 .4 native AI/政府语义验收。checkout1643d03d 与既有 jar 身份分别登记；不为形式重跑不相关矩阵。exact CK3 为1.20.0.4，绑定复用既有 EXE SHA-256 98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518。

三个并行包的 research、fixture、既有实机证据分别记账；没有新游戏日、稳定窗口天数或整项完成信用。
