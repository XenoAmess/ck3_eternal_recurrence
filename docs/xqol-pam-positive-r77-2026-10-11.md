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

## 16:25 CST：R72/R73 精确清点停止，零回收已闭账

候选提交 `70e2d01729f9378d3429d1e8973293b8fb162483` 的官方 CI [38123666594](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38123666594) 已实际读回 completed/success；仍只证明代码门禁，不是 PAM 或发布验收。

新两根缓存包经 root 全文审阅 producer/admission/matching closer 及独立只读审阅后，实际 admission exit0；prepare 于08:22:26.873440Z开始，在 R72 精确 `shadercache/dx11/{ps_5_0,vs_5_0}` 范围读到空集合，按原门禁 exit1，未继续 R73，未生成 QUALIFIED 或 SUMMARY，也未执行任何删除批。不能沿用此前每根3,780文件/约158MB的估算，不能由 R72 空外推 R73 或其他根为空。

实际 review 后按失败路径 close exit0，标准237回执 `C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/post-r76-r72-r73-cache-retirement-01-reservation-237-closed.json` 为2,871 B / SHA-256 `49da1aea5d203aaf5b47cb89dd5690b3d58c8dc28cc6f7f5afd3221035afdd16`。原 prepare exit1 保留，删除0、释放0、子进程0、unspent0；完整16MiB只保守计入一次，不减 usage，也不产生后继预算信用。SAVE、错误日志、原业务证据及当前输入未动，保护项仍于2026-10-18复核。

该回执的全卷 fresh free 为28,602,040,320 B，低于默认2GiB场次所需30,071,062,528 B；全卷变化不归因为本包。后继先在新限额工作包内调查其他已结束精确缓存根的实际metadata，再决定是否有可回收资产；不能降低6GiB系统增长、6MiB其他预约或20GiB安全预留。RMTM core 的默认2GiB观察器只完成源码/纯边界自测，尚未准入、分配或启动。业务进度保持 QOL 2/6、RMTM 0/2，两项均未发布。

## 16:40 CST：实际缓存容量调查与实机容量阻挡

既有本机小台账 `qol-r57-r75-generated-cache-metadata-review-240.json`（05:43Z、17,992 B、SHA-256 `d9195dc95b3bfc4300e6716513d850e8c8f2e33e4c12ac07bd27f8fcea49d75e`）已记录其实际16个runs缓存为空，包含R72/R73/R74；本轮在准备回收前没有及时复用该信息，后续纠正，不再按旧估算反复申请回收。它明确排除R60/R71及已清理R75，不能把连续编号外推为全部为空。其他旧大候选已删除或已被较新小台账修正，本轮不重复计释放量。

R76/R77/R78另作只读metadata调查：root全文审读冻结9,420 B源码，因其110秒门禁是协作式截止，另用只允许该冻结调查子进程的115秒timeout runner，再由221记录实际wait；不是把没有timeout的旧221当作自带超时。实际exit0、stderr空，调查43.246912秒/23,176 work units；缓存正文读取/哈希0、删除0。只写现有2MiB helper池内小回执，不创建新场次预约或重型资产；代码首稿超出原8KiB子限额已如实记录，root明确改为12KiB，整个小调查仍按40KiB限额，未降低任何其他预留。

结果分别为R76 3,816文件/161,276,720 B native allocation，R77及R78各3,780文件/157,999,920 B，三根identity union合477,276,560 B。R77有Source19现存控制及prepared引用，R78有诊断prepared引用，保持保护且均未取得删除资格；R76也只是调查量。报告 `C:/workspace/ck3-upgrade-20261010/root-parallel-continue-236/qol-r76-r77-r78-cache-metadata-survey-01.json` 为7,640 B / SHA-256 `26254b9732c7082acca4c2187811625bca0f7ca045947168fd860e29b3250e1f`。保护的是用途待明确的实际输入关系，不把任何历史路径自动等同于永续引用；本轮未修改这些引用或删除缓存。

调查后fresh free 28,577,722,368 B，距默认场次门槛仍差1,493,340,160 B；477,276,560 B不是已释放量，即使全数另行合格回收也不能独自补足缺口。RMTM a182的task/attempt/keeper、state父级single-use-ledger及原消费标记均实际不存在，准备文件与Source19匹配；仍不是原子准入。官方CI在提交 `dfe2e8c3bc8925da3815c0b8534a7fdae6405dd4` 已completed/success。已请求用户先在本机腾出至少3GB或指定另一获准执行位置；现场容量达标后优先RMTM core，再按原业务矩阵推进，不能承诺未经验证的发布时间。所有业务通过率及未发布状态不变。

## 17:52 CST：按用户指令自主回收，容量阻挡已解除

用户随后明确要求root按最新规则自主清理，不再询问其腾空间。经当前用途与精确路径复核，09:52:05Z实际完成15,936文件/2,910,665,920 B native allocation回收，221原进程wait0；09:52:38Z预约close实际exit0、children0、unspent0。闭场后fresh free 31,473,754,112 B，超过原默认场次门槛30,071,062,528 B；没有降低任何安全、系统或其他预约参数。

R76/R77/R78缓存的旧保护候选经具体用途重审，确认生成shadercache非未消费Source19 prepared的输入；仅回收缓存，非缓存与代表问题证据未动。重复原件、旧截图与导出等各组资格、原件不可读状态、完整SHA和期限见[实际清理回执](maintenance/storage-retention-2026-10-11-release-capacity.md)。这不改写16:40调查时未取得资格/未删除的历史事实，也不把清理计作业务PASS。下一步仍按原默认2GiB原子准入优先RMTM core，QOL 2/6、RMTM 0/2及未发布状态不变，361不在范围。

## 20:23 CST：后继PAM delayed-boundary输入已实际准备

RMTM R14/a182已运行，因adapter重复就绪等待在D0前停止；三行最小修复及8项离线回归已推送 `c1b55f130e05bcfdae5d6694db969a398bcfc9be`，见[实际失败及修复](ck3-mod-upgrade-fast-validation.md#2026-10-11-rmtm-r14公共就绪等待的唯一所有者)。本场原OS0、keeper/allocator0、CAS8778与closure3成立，标准52预约已实际释放：7,760 B / SHA-256 `8f731558c2001cd7c1856c39b40f1228d87372d30d7a9f1df2a99c62a6e9bc63`；保守项目占用37,112,474,752 B。闭账生产器变量遮蔽及第一版storage adapter提前stdout造成的metadata不一致均保留原失败；只修局部输出后实际成功，不改业务或原51门禁。

PAM新工作包只复用正式27文件与plain输入、生成未消费新state；原35步/12自然日/400秒资格及全部预算不变，不复制旧profile/cache、不重建正式产品。[实际准备READY](C:/workspace/ck3-upgrade-20261010/qol-pam-delayed-boundary-20261011-01/PUBLICPREPARE-READY.json) 7,942 B / `02d1af3de2594ff31434b2e6e49e78fd1b147721e741b661695e0d3f72e2738f`；prepared-case 29,973 B / `7e3709a2d01da1b0b181c3f87597dcb529e48e3fa797c1037159c72d5db2da9c`。真正公共prepare与prepared-plan各执行一次均0，elapsed1.049719秒；尚未分配或启动。

[标准262闭账](C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/source19-pam-delayed-boundary-01-reservation-262-closed.json) 4,633 B / `ff9e58b427c71b3563bdd2dd67cb5cf27a35a04dfc8e785211d2ed6f8ab5a2e0`：真实后代写入0、native最终路径上界2,018,792 B，physical_peak_proven=false；完整4MiB后继只保守计入一次，usage37,116,669,056 B，不发回收或未来容量信用。next-scene consumer必须显式识别这个新262闭包，原52不会自动扫描它。小control artifacts在原other6MiB内另限128KiB，不降或扩大6MiB；新scene仍单独申请原默认2GiB。准备成功不授PAM业务PASS，两产品未发布状态保持。
