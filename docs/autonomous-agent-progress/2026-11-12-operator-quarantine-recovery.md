# 操作员隔离未知效果与同局恢复

用户明确要求恢复正常工作、终止旧事故并允许清理失效停止说明。本单元使用新的操作员决定退役原自动批次，不证明旧动作没有效果。原 UNKNOWN、全部子预留、原命令和过期期限、原回执与账本历史均保留，原父／子 ID 永久禁止重新执行。历史 NoDispatch 方案缺少的 loaded-issuer 证明没有补造，也不成为新操作员授权的等待门。授权原件 USER-NORMAL-WORK-CONTINUOUS-AND-PREINTENT-PROTOCOL-AUTH01.json，1749B／SHA256 bcaea4b5c4e82092e83d43acf28cc245ed63136cc97170429747d158d7b55c19。

新增 CompositeOperatorQuarantined(execution, observationRef) 和 OPERATOR_ABANDONED_UNKNOWN_EFFECT，与 APPLIED、无效果和普通结算分开。独立 versioned receipt codec 通过真实原 UNKNOWN 回执恢复完整命令、execution 和 children；普通 receipt 编码／解码算法保留，只在稳定入口分流新 schema。Archive 重开核验 observation、原回执、请求材料、原前驱及实际首个 reservation record。Native verifier 在原 composite Guard 回放之后、settlement-null 返回之前，要求实际安装的同 operation callback 验证新协议；DATA roundtrip 本身没有权威。

配置增加显式 operator_quarantine ExactRef，Dev/Main 使用 operator-quarantine 模式。实际安装的 source 固定真实授权、machine、Game PID/birth、episode、原 parent/body、完整顺序 children 和预期 head。新观察在同 writer 锁内核前驱和独立有限期限；归档回放改核原事件因果链，不要求当前 head 永远等于旧37，也不把观察期限用于否定已提交历史。新窗口不刷新原 action deadline。

同 Game/episode 的整项 optional Sway 暂时隔离：policy 在 collector 前 Keep，真实 ACTION admission 同时拒绝新 Sway parent/start/stop；不是仅一个 target，也不授完整 G2 功能恢复。原 Sway domain、active stage/pending 和 Driver v7 全量保留。Driver 对实际 source-verified 新状态走独立无 recorder 分支，不造 Legacy row、coverage、版本 CAS 或无效果证明。规划输入核真实配置的 source 后，不把这份 canonical 操作员退役当成普通 GLOBAL-UNKNOWN 待决 fact；原 UNKNOWN 的全局约束及 Sway 两层禁入保持。

独立 OPERATOR_QUARANTINE_RECOVERY event 将 repair_required 恢复到 running，保留起始／保存日期、saved/eligible/completed credit、Driver 和原已消费身份。它消费 batch0，后继从 batch1 开始，不套用 initial-no-dispatch、身份 rebind 或已完成 cycle 的 admission。真实零 cycle、一个 reserved child、无 WORKER_RESTART_CAPTURE 的前沿最初不符合旧 reader；新增 request-bound 专用完整历史读取和只读 Driver adoption，未放宽旧 Sway NoWrite 的零 children／完整 cycle 条件，也未伪造 capture。首次入口不是任意未来 cold recovery。

软件结果按实际覆盖分层：

- Core14 首编74类；原生 writer fixture 新1P通过，覆盖缺 callback／错 reservation 拒绝、真实 append、UNKNOWN_EFFECT、零 Native／零 credit、旧 parent/child 的 coordinator 与 writer 双拒、旧 bytes／新 codec roundtrip、下一 head 和过期观察的历史回放。
- 差额17编译188类，真实首次 reader 修复4TU编译76类。Driver/Sway代表1P通过：原 Driver bytes／版本保持，无 Legacy／coverage／CAS，fresh ready；collector0／对照1，三类新 Sway ACTION 拒绝。不冒完整生产 Sway 执行或私有 Controller 恢复通过。
- Runtime24 Maven 首次因 DecisionDisplay 的 Outcome switch 不穷尽失败，未启动 host/delegate 或业务。必要四叶兼容中又真实发现 MCP sealed-state guard switch 缺项；首 RED／partial14 保留且未采用。修正后4TU成功35类：显示未知效果、AUTO 为 BLOCKED、婚姻接口拒绝不适用结果；原 execution.guard 仅作历史上下文，不发行新 Guard，旧分支保持。
- public37 DATA adapter 未实现／未运行，不补软件通过。真实 reader、adopt、observer、recovery 和 Controller 在 Runtime25 首次现场验收。

正式源只移植新协议 hunk，保正式 HEAD 既有 Saved、Archive diagnostics、typed actor 等差异；正式 RuntimeAssembly 沿原 fresh OrdinarySessionHost 构造方式，不回滚成 active 的 DI 变体。36生产叶为30修改／6新增，另发表两份实际已验新 Test；已发表 safe-producer2 不重复修改。11正式差异变体初次缺旧 Saved API，再补原 HEAD 的5份未改依赖；两次 formal RED 保留。复用已独核的8个完整 SourceFile／130类，仅增编剩7叶加1依赖，成功49类，共16 SourceFile／179完整类取得正式变体 typing 资格。没有重编整树、重跑两个旧绿 case，或把这些正式 Saved 依赖部署到现场。

实际现场另列38源＝36协议源＋原已验 safe-producer2。Runtime25 保持 Game145132／birth134388549310428814、keeper56732。request24 issued15:47:04Z／deadline16:17:04Z 未重签；原 command 08:49:49.300706500Z 期限保持。观察于16:11:58.257394100Z完成；38为专用733B receipt，39为恢复 event，40为原 episode 的 batch1开始。39中 retained_driver 和 SEM original_driver 均为真实 v7、263887B／SHA256前缀 fbf062e2，actor31254/date53168040。16:12:01.922003300Z实际 LOOP next1，不把初始 marker 当动作或保存。本次通过了 terminal append 后的消费者窗口；若将来该窗口中断，必须核原 proof／真实事件最小续行，不能另签观察或重放。该任意 partial-write 冷续行不由本次通过预授。

首新增保存真实通过：65于16:16:33.445941600Z SETTLE；71于16:17:10.968224200Z SAVE_CONFIRMED，53168040→53168232，新增8确认保存日，pair native27/public26、cycle1。同 host132588／delegate f194c13e…继续游玩。完整首保存窗口为2026-11-10T16:39:03.070767Z→2026-11-11T16:17:10.968224200Z，85087.8974572秒／8＝10635.98718215秒／新增保存日；包括存档选择、Steam/launch失败、权限与准备等待、软件、Maven、Java交接及游玩，未借旧保存日，10秒目标未达。恢复后的短窗不替代主窗口，后继 observed/unsaved 不冒新增 SAVE。

本新单元 Native 13软件 JVM为9 exit0／4 RED（首 JNA runner、MCP遗漏、两次正式 Saved依赖缺项）。actor194.964334499905817秒嵌在 operator218.468746899859982秒内，不能相加或当整轮，Runtime Maven/Game 不在该子窗内。全部 BEGIN/END、UTC墙钟、工具错误和等待保留。首 Native operator 14:04:51.361890Z 至 cost cut03 16:41:47.065124Z为9415.703234秒，已持 Native preflight至该cut为11016.503337秒，包含中间设计、准备、失败、交接和等待；更早真实任务开始仍为 UNKNOWN_NOT_ZERO，不填零。cost cut03 六根实际33124073B＋本件29558B＝33153631B，小于本阶段33554432B；这是具名切点，持续 Runtime 日志不预授未来预算通过。旧4/8/12/16等配置与上一 import 修复5511991B超4194304B的 metadata-budget=FAILED 均不改，不删移、重分类、抬旧 cap或重跑补绿。

关键原件不重复读取存档/checkpoint大体或查询 Game：

- Java证据根：D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/composite-operator-quarantine-p0-20261111。实际38源 Ready04 25414B／dd86a710fed724a90153f3b1bdebb40c0db3dfced69acf09740c18bbb30a7db0；正式 hunk review61047B／78a32347468cd085fc386332afc78c99ddf95f109a5b8cbde24f422b328f37e0。
- Native同名单元：Core writer XML41743B／1aa98e860a4a03e017a55160d24d6136a7c91a0ac559aa1e5b8deac22c644bda；Driver/Sway XML42273B／1ea3a1ed456a90fb49421c8dec4c495e1dea08ee643437364fe9d6503549995c。ACTUAL38-COHERENT-PREFIXES-OUTCOME-COMPAT-SUPPLEMENT01.json28770B／e3bd1e32c5f8eb06b4d09ae36a49129d6791243815791e6604a67fc2751819e4；FORMAL16-SOURCEFILE-TYPING-COMBINED01.json9913B／16aa00381032b600e884c797a7c233b4704bb62f1ccacab32bb3eed7f21beab3；NATIVE13-ACTUALS-SIXROOTS-WHOLECOST-CUT03.json29558B／bac56526065f2dc78b90cec6abb89e3f040b949cc191dc56d95263b85f81d43f。
- Runtime attempt25/first-save-confirmed/FIRST-NEW-SAVE-CONFIRMED25.json7154B／ddd06201c884698db5fe7c866d73e40c6dc51d4d549f94efacff8736cbaf9d1f；原71事件97523B／a994b2d864aaff6ef450df479fdbb508645da876ecd1d36cab00f11ab62642a0；原65事件96106B／87d85bf3548e78504f4f9a9f220250c18f918d7d7e5a6b67ce6367363a24d83b。

AGENTS 失效停止门已单独正式发表；Z工作区仅同步该文件，保原本地规则与工程后缀，不碰其他脏文件。历史 Git/docs 与原账本可追。本文是后到事实，不把此前“未采用／零保存／失败”倒填成当时成功；正常 worker 不等待本次 Git 发表。
