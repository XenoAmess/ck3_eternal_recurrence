# QOL PAM 正例 R77：启动资格失败与实际资源闭场

范围只含体验优化与重整河山的 CK3 1.20.0.4 迁移验收发布，不涉及361。2026-10-11 14:47 CST 记录：QOL 原业务矩阵仍2/6（33.3%，ordinary_async / pam_negative），重整河山0/2（0%），合计2/8（25%）；本轮两项发布均未完成。基础设施、计划、静态测试和资源闭场不计业务通过。

## 实际运行

公共 PAM+ a180/R77 于06:31:48.842542Z启动，06:37:08.120042Z结束，run exit2；随后仅一次公共 verify，exit2。没有重跑已消费的43 state。共同 Source19 runtime、prepared sibling 及35步/12自然日、command300/readiness400/timeout4500/hold600/poll0.05均沿用原件。Source19只修共享报告writer，不更换 native DLL 或业务合同；本场没有再次发生 WinError5 writer crash。

新鲜 Steam 窗口变化与两份独立 nonce 原图已由 root 直接审阅，均显示离线模式。普通实机未将 Steam 切为在线。

冻结 profile 的 `logs/debug.log:20470` 于14:35:46 CST发出 `ZQP120: TEST FAIL actual_positive_doctrines_landed_recipient`，来源 `zqp_pam_sample_effects.txt:126`；公共启动策略正确命中广义 forbidden `ZQP120: TEST FAIL`。宋帝 actor 资格在同日志12603已PASS，但双个人教义 setter 的 `free_personal_tenet_slots >= 2` 未满足：诊断为piety level4、free slots1，两项个人教义及其fulfillment flags均FALSE，未进入queue seed/D1业务。host保留 `RuntimeError: actual fixture qualification emitted a forbidden marker`，case NOT_RUN、case/gui/acceptance均false。

43实际 modifier 与sample均带UTF-8 BOM，并与原prepare及当前对应源码逐字节一致；Source19 sibling只改变顶层manifest绑定。`personal_tenet_slot_add = 1`是该游戏版stock有效键，但本场没有actor上 `has_character_modifier` 的真实回读，因此目前只证明设置后仍为一槽，尚不能确定是modifier未生效、缓存时序或其他原因。后继须新prepare并补最小真实诊断，不删双槽、双setter、forbidden或自然回复/精确奖励门禁。

## 资源闭场，不是业务通过

失败GUI退出后实际retained CK3 OS0，native zero proof仍null、normal_close_qualified=false；failure_shutdown_proof / failure_lifecycle_completed / cleanup_ok / managed_thread_finished均true，job0、进程清单空、control/watchdog均absent。仅自有Guard251在运行已终止后行政停止，实际monitor exit15；该非零值不冒充CK3退出码。keeper/allocator均实际exit0；屏幕CAS使用停止后最新序号，实际done/resources[]，seq8724。

小型post-run-only receipt直接调用三个公共closure谓词，均true；标准 `previous_session_closure` 已通过，不使用R76 unfinished-writer-crash的特殊入口：

- `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a180/POST-RUN-FAILURE-CLOSE-01.json`，7084 B，SHA-256 `ee6ac156729f2491f5dbbf5d6b99946c6ed2b2a045aa3f7056f3414caebea1b4`。
- 原native report为23,924,202 B，SHA-256 `1ff40b240f99ad88f21574a371f557331a5ce6a6905d08b75d51cb0890249202`，原失败不改写。
- 原release回执 `C:/workspace/ck3-upgrade-20261006/resume-root-01/a180-screen-release-01.json`，SHA-256 `3b3250897864a724510ece64d23876e1b14fb51cfebf6c4b7189df934383c062`。
- 标准storage closer实际exit0，仅闭1GiB场次预约：`C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/pamplus-a180-source19-guard251-after-exact-reclaim-01-reservation-52-closed.json`，7843 B，SHA-256 `cb0d8de08c0124c6a96bea4bba0063abe7794d6523668cf0bd26bcf25923c719`。

Guard251实际基线union 3,555,336 B，最后观察净增长275,823,408 B，未触发750MiB/卷容量告警；这只是30秒采样净增高水位，不是所有瞬时写入的严格上界。闭账场次allocation280,152,032 B，项目保守usage36,553,772,656 B，整卷fresh available28,536,250,368 B；不把全卷变化归因为本场。

## 后继

并行继续PAM最小原因诊断、重整河山core开场准备，以及旧QOL R13–R17五根生成shadercache的用途替代复核。五根默认168h期限尚未到，不能称自动过期；其余原输入、SAVE、错误与业务证据保留至2026-10-18复核。任何回收只在新预约、精确根/单链接/ADS/占用/独占HANDLE核验后分批执行；候选789,999,600 B尚不是实际释放量。

优先在容量满足原2GiB估算后执行重整河山core。PAM+须修正并新prepare，再继续QOL两类任命及赎回。发布时间取决于剩余实机GREEN、正式tag staging、实际Workshop上传、匿名完整Change Notes回读、真实Steam缓存字节与加载及changelog master提交推送；当前不给未经验证的完成时刻。

## 14:54 CST：只读诊断后继，尚未实机

进一步核原日志12606/12618/12661，PAM DLC实测TRUE；原profile `disabled_dlcs=[]`。不能把禁用DLC当作本次原因。同版stock defines基础个人教义cap为1，stock `piety_level_4`有纯槽位+1，但piety getter为4不证明该派生modifier已实际计入。

只对新PAM+夹具增加条件前、原条件分支内add之后、条件后的真实 `has_character_modifier` / DLC / 空槽回读；未增加setter、日期推进、奖励或通过标记。新sample为20,593 B / SHA-256 `9d59d37136125367b5219988a65e33391ad8b9d1f40e732fa5c53072f62544da`。剥除四块明确只读诊断区域后，必须逐字节恢复原18,737 B sample及原SHA；还原唯一support pin后，整个case JSON必须恢复原SHA。两项新精确回归包含在11项followups测试中，执行者及root分别实际exit0。这里只验证诊断无业务改动，不能写为槽位问题已修复或PAM已通过。

## 15:55 CST：R78 新鲜诊断实机与标准闭场

R78/a181 使用新公共 prepare 的 `qol-pam-slot-diagnostic-20261011-01/state`，未复用 R77/43 profile。prepared 为29,919 B / SHA-256 `3d3c14d1534189340d73700c18b70ca8f1112961c21ca8442a82543607356cff`，绑定同一 Source19 runtime。原35步、12自然日、300/400/4500/600/poll0.05、双槽门槛、奖励及 forbidden 均未降低。root直接审阅本次 Steam 位移和两幅新 nonce 原图，均为离线模式；公共 preflight exit0、blockers空。

实际 run exit2，native report于07:41:30.163116Z完成；公共 verify仅执行一次，exit2，business/case_acceptance/product_release均false。新debug于15:40:10 CST记录：12614 modifier FALSE；12621及12628 TRUE；三个阶段的free_eq1均TRUE、free_ge2均FALSE。12641 piety_eq4 TRUE，12657 actor_piety_ge4 TRUE，12662/12663 cynical/zealous均FALSE；20481再次发出原资格FAIL。已排除DLC未开、modifier未加入、piety设置未执行及cynical抵消，仍不能认定缓存时序或引擎上限就是根因。双setter未执行，原业务35步未开始，不能计新增PASS。

同版stock有 `trigger_event = { id = ... delayed = yes }` 的hidden immediate先例；隔离初始化与资格读取是后继可证伪候选，不是已验证修复。公共host在资格齐全前不处理intro，并强制实际bookmark D0；不允许点击后补资格、跨日推进、先FAIL再补READY或增加原400秒等待。

CK3 retained HANDLE实际OS0、tree/job0、failure生命周期完整、cleanup_ok=true；normal_close_qualified仍false、native_zero_proof仍null。自有Guard512行政停止，实际exit15，非游戏退出码。最后30秒采样净增275,827,728 B，无告警；不作为瞬时物理峰保证。keeper实际exit0、allocator unified session1878实际wait0，屏幕CAS release实际0、seq8752、done/resources空。

allocator本次未由221包裹，初始stdout/operation没有磁盘原件，不能补造221回执。root按真实tool wait创建独立fact-02，SHA-256 `8551ab51b766a9efb52f68f7a598cb0dfa2f55bdd9170ad4a95bbf3eb85e8e39`；fact-01保留并勘误其keeper pin仅是thread report，fact-02才绑定原生parent-exit回执。闭场producer01因误用不存在的reservation字段退出1，未写闭场；独立02只纠正为原 `case_specific_peak_review_pin`，原件及失败回执均保留。02实际调用三项公共closure谓词均true，未改写业务结论。

- `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a181/POST-RUN-CLOSE-01.json`，7,967 B，SHA-256 `f5d6fc90c58ffcd451c225158144cf2dc33db33e82bffb35c125140806c230d8`。
- 原native report，23,393,128 B，SHA-256 `1bef48b563fa5a38195aeb4e1a7641fa132afa047592d2cb3a4cf629017ace23`，仍可读取。
- 标准51 storage close实际exit0：`C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/pamplus-a181-source19-slotdiag-512m-01-reservation-52-closed.json`，7,807 B，SHA-256 `8bcd07f52b30bf4bec8a47cbced0bc244de823379f4514da40038c5383fb7a83`。闭账增量280,082,480 B，保守usage36,854,826,656 B，fresh available28,849,459,200 B，释放1GiB预约；不产生未来场次额度或业务信用。

## 15:55 CST：R13–R17 缓存回收已执行，后继仍待准入

更正上文14:47的候选状态：五根生成shadercache已按用途替代提前回收，非168h自动到期。20/20批实际成功，共18,900文件，native allocation释放789,999,600 B（约753 MiB），小型摘要 `qol-r13-r17-cache-retirement-20261011-01/ACTUAL-SUMMARY-05.json` 为6,231 B / SHA-256 `a48072fbc15c11912c6d193dbfc3d7974492e70da6c898b6d0ea4182c1b24ebe`。原cache文件已不可读取，可从保留游戏和构建输入重建；SAVE、非cache、当前输入和关键错误证据未删除。部分旧native-report原文件名早已由先前gzip回收，不能因本次保留其他证据就声称所有旧原件仍可读。保护项于2026-10-18复核必要性，不自动续期。

从prepare到实际finish为576.952437秒，小于600秒；16MiB独立包已真实closed并整额计入保守usage一次。其标准237 closed为3,259 B / SHA-256 `2f80629a10d03f080f1bf97ceff151d586c263ec97d0a778d38264b907703d36`。物理释放量不等于整卷free变化，不重复记回收信用。

R78闭场后的fresh容量仍低于其他GUI场次原2GiB准入要求30,071,062,528 B。R72–R76五根新方案尚未执行，20批方案因600秒风险被拒绝准入；后继缩为R72/R73两根、最多8批/8,000文件，须先完成源码审阅、真实闭场绑定、新预约及精确metadata资格审阅，不能预记释放量。其他实机现场建议顺序为RMTM core、QOL admin、RMTM threshold、QOL merit、QOL ransom，PAM边界候选保留并行代码诊断。QOL仍2/6、RMTM仍0/2，两项均未发布；发布时刻继续受全部正式门禁约束。

## 16:05 CST：单次 delayed 边界候选，仅静态通过

只在验收fixture中将原slot设置后的整个后半段拆到 `zqp120.3` hidden continuation，通过一次 `delayed = yes` 触发；不重复初始化，不推进日期，不修改产品业务文件。新增日志只读检查current actor、此前saved scopes、piety、modifier及slots。sample/events/contract三件的tested inverse均与8384e6f3e基线Git原件逐字节相等；原35步/12自然日/readiness400、双槽双setter、奖励、support allowlist及required/forbidden均保持。

独立代码审阅仅授静态候选通过；执行者及root分别实际完成原11项与新4项回归，exit0，diff-check0。新sample为23,066 B / SHA-256 `c72ea38124468577802d81a4a791d183a7c92cf78bd8916d9a373ee819e42c7d`，events为426 B / SHA-256 `aca333d018cb82108547c7f18ebb956fa7402ed7b14a85e292e12b9c434220b4`。外置静态回执 `root-parallel-continue-236/pam-delayed-boundary-candidate-static-01.json`，6,749 B / SHA-256 `f6d5e18ade5361f0175c4c501bd930b2d69d427494bcdfdd055de9bbbc8581c9`。

尚未新prepare、分配或启动CK3。paused D0是否调度及真实scope传播均未证明；若不进入、仍单槽、跨日或scope不符，保留RED，不延长预算或连续试槽位。原Source19、R77/R78及所有旧profile/prepared不变。先让RMTM core取得现场窗口，不能把本候选或静态测试计入业务矩阵/发布完成。
