# 普通雇佣兵查询后的 Sway 观察窗口

2026-10-18，`machine_id: xenoamess-full-tower-eb9d2c1186`。来源为公共源码和明确合成的软件端点；封装观察时间 `2026-10-18T11:02:49Z`。本次没有连接 CK3、Steam、Native、桌面或录制，也没有读取原片、存档、Driver 状态或活跃执行树。机器可读来源与测试结果见 [证据](evidence/sway-quiet-market-observation-2026-10-18.json)。

原 [quiet Sway 观察器](p56-sway-quiet-observation-2026-10-18.md)仅在普通军力查询完成后运行。战争期间普通规划器可能先读雇佣兵市场，已启动 Sway 因而错过这次可用的只读窗口。本次把精确的 `native_war_mercenary_query` / `query-player-mercenary-context-v1` 加入观察入口；不改变战争选择、采购、提交回调或原查询结果。

新入口要求原回合 `executed`，原查询 `completed/accepted/read_only`、严格正整数 query sequence，随后独立快照仍为同玩家、episode、日期、Game PID 和连接代次。市场来源必须等于完整当前 observed frame，原生 revision/date 必须相等，且原 `normalize_player_mercenary_context_v1` 必须验证 exact build、玩家、日期和完整 DTO。只有既有 `applied + postcondition_verified` 的 Sway 可观察；空 ledger、待决提交、已终态、权限不足或未到期均保留原结果。战斗、退却、集结、强制弹窗和身份变化继续优先。财务专用查询、hold、route、hire 和其他战争阶段不因此获得入口。

观察仍使用原生命周期 reader、月度节奏和 durable ledger。它不会 Start、Stop、重发 pending、替换计划或推进时间。原普通回合的 following consumer 先完成；这次新读出的命名收益或终态只能由以后真正执行的普通回合消费。可选查询或写盘失败也不会掩盖已完成的战争回执。

验证只运行修改涉及的 unit 文件：8 项测试，`Ran 8 tests in 1.064s / OK`。新增正例经过真实 `Service.auto_turn → _execute_planned_turn → execute_step`、提交前回调、原 market DTO normalizer、Sway 生命周期及后续普通消费；仅规划输入和游戏端点为合成。正例保留早期基线、30 天后命名 `scheme_sway_opinion` 增量、无成功归因的原生终态及以后回合消费。10 个拒绝子例覆盖 ACK-only、非只读、布尔序号、其他 phase、旧帧/连接、异玩家/build、残缺 DTO 和新战斗。原 6 项军力窗口回归同时通过。

这增加一个可验证的观察机会，不能保证只有 hold/route 的长战争一定公平调度，也不能消除 new Start 仅在合格普通窗口选择的限制。下一实局仍须保留同一行动/玩家/目标/full SchemeID/代次的 Start、早期命名基线、真实增量、自然终态及以后普通执行消费证据。合成日期与 ACK 都不授业务信用；G2 仍为 **6/8**，M6/M7 未完成。当前冻结 SDK/Host06 没有采用这次公共差分，后继装配须显式绑定新叶并核真实 owner 消费。

同日 `11:06:57Z` 的第二个小修复保留每次原始 Start 的 `first_named_gain_intervention`。当前 material 在同值刷新时仍正确标为“没有新增量”；首个真实正增量另保留原日期/revision、此前基线日期/revision、命名值和原 action/actor/target/full SchemeID/代次。它只占一个记录，不随观察次数增长，不从已有旧 ledger 反推丢失的历史证据。原 following consumer 在以后的普通执行回合独立消费它，异 action/实例记录或同帧不能借此完成消费；原 current/previous interventions 机制继续保留这些信息。首个增量并不自动证明自然终态或有利的终态原因。

这一修复以原 material compound 验证基线、总好感不能替代命名增量、同值刷新保留首个增量、同帧不消费、异 action 拒绝及之后独立消费（1 passed，3.57s）；并在新 consumer 字节下只重跑新增真实 Service 市场整链，明确断言首个增量保留原基线且由以后回合消费（最终 1 test，0.107s）。第一次 pytest 收集因缺少仓库 `src` 搜索路径而失败，没有执行测试；修正运行入口后通过，未为此修改生产源码或伪造运行资格。以上均为软件验证。
