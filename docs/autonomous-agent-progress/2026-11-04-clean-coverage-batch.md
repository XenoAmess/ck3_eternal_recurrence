# clean coverage 复用既有批量成员校验

machine_id: `xenoamess-full-tower-eb9d2c1186`。实际来源为同Game／同host的restart13在14:54:11Z取得的一次66帧线程栈，以及Runtime具名冻结的六份完整源码。原件导航 `D:/ck3-state/resume91-runtime/clean-restart-readonly-io-phase-fix01/clean-coverage-membership-observation01/SOURCE-READY01.json`（7020B／d9541801…）；不是新采样，也不从该单栈推CPU比例、实测调用次数或唯一热点。

具体重复已由调用者与被调用者核实：Bootstrap的clean恢复在同一withFrozen中逐条validateCoverage，canonical或带source的legacy行调用Codec的Session verifier，再逐次进入Journal.requireHistoricalReceipt；它每次都fresh historical遍历整个保留record链并调用Archive.loadRecord。因此R条需membership的行、H个链节点时，仅该部分会重复R次完整链读取。当前实际Codec／Journal已经有requireCanonicalMemberships／requireHistoricalReceipts批量DATA合同，可以在一次新鲜链上保留每个完整receipt、source.record、支持材料、capturePin／verifyPin及逐项head校验；不需要新增类加载依赖。

候选只改实际DriverBootstrap五处span：仅cleanRestart.present分支在原逐条DATA验证后，按原顺序收集actual与精确Source，再调用既有batch。保留proof.receipt与完整编码receipt比较、canonical材料／evidence验证、legacy ordinal／原行bytes-SHA／expected row／command／ok／SOURCE_FIELD及Gift支持；第二次canonical Source读取仍核bytes／SHA。预loop捕获实际head，逐covered row后和batch前后拒绝漂移，batch本身逐项head／support／pin检查保持。待整批成功才把临时行合入最终Known的行集合，不缓存或带出任何证明。

非clean路径仍走原Session verifier，原323调用点与operator路径不动。完整baseline／full decode、project／gaps、单次lazy IO期限、handshake／fresh READ、固定overload与旧命令期限都不变；Archive／Store／Identity源码未改，动态容量、身份及bytes／SHA检查保留。只读验证的先后次序可以改变，但失败仍在Known／project与首个后继IO前退出，不发布部分结果。完整等价审阅在 `D:/ck3-state/resume91-java-delivery/clean-coverage-existing-batch-p0-next/SOURCE-EQUIVALENCE01.json`。

模型唯一新请求HTTP200但length10000，65.1545966秒／有效TTFT10.1475993秒；整份CONTENT未读、未解析、未拼接、0代码采用，不自动R2，不据此评分语义能力。owner接管实现。首candidate01实际javac1／6.599368秒／0class，原byte[]original与新增JSON局部变量重名，JUnit未启动；原红、fence／close1与释放回执保留。新candidate02仅将该局部变量改名sourceRow，保所有批量语义与其它源码字节，whole inverse到原before保持exact。

candidate02实际139691B／16784318…，其必要1TU首编0／18class／6.859393秒／stderr空，持久fence／terminal／close0及资源释放已核；原55输出作为后续classpath复用，新的Bootstrap18 family位于最前，未重编其它生产源、旧Test／Fixture／Support。源与元数据入口为任务根的 `SOURCE-READY-CANDIDATE02.json`（c7ceadc2…）、`OWNED-SPANS02.json`与`native-prod-first02/`。原Test05的三个受影响方法binary RUN-only已真实3P／0skip-abort-fail、48.9985758秒／stderr0，XML43634B／1124be65…及fence／close0／资源释放已独核，原件在`native-affected-run01/`。它只验证原IO期限路径，新的多行行为另由下述真实独立结果承担。

正式Bootstrap的before恰与实际98c2源逐字一致；按五span投影后的单文件也与16784318候选逐字相同，不授整个正式依赖组合通过。本改动没有新业务类型或public API，但增加了同class内private overload，不能称仅改方法体、或宣称当前JVM原地instrument已兼容。当前restart13健康正常游玩继续，Runtime独占未来必要清洁采用边界，不为本候选重载；尚无本改动实际装载、提速、新游戏日或SAVE信用。10秒／新增SAVE_CONFIRMED日目标仍未达，G2仍6/8。


最终独立Test04为32122B／fea429e8…，仅新1TU首编0／10class／6.1961237秒；原Fixture37／Support2／生产18及其它55输出复用，未重复旧IO三方法。正例与负例分别独立RUN90／phase TOTAL120，真实1P／50.4003298秒与1P／50.154996秒，均0skip-abort-fail、fence／terminal／close0及资源释放已逐项独核；不跨phase合称TOTAL120。XML分别42250B／72c40515…与42251B／b3f01b7d…，原件在`native-mixed-test-first04/reports-positive`、`reports-negative`及对应actual目录。

正例通过实际Publisher、两条已结算拒绝回执、controller capture／canonical admit、public Bootstrap及软件Native端点：同一冻结链的canonical和legacy完整record按真实Journal从新到旧顺序保持，supplier一次、fresh一次、head及软件World写入次数不增。负例分别真实触发source bytes、support bytes及注册FACTION的实际preview／commitImport导致的读取期head漂移，均在supplier／fresh前拒绝。没有伪造链读取次数；legacy无SOURCE_FIELD、Gift、Operator、物理Managed／Core／Prepared完整入口及实际性能不由这两方法验完。

所有前序harness事实保留：Test01两处import先在源码审阅修正、0JVM，不作compiler红；Test02首轮2errors在coordinator.execute的fresh协议、尚未到Bootstrap；03只补既有公开fixture版本／capability与fresh-read配置，随后whole2的60.315444秒、90.362186秒timeout都没有完整Jupiter终态，不授case通过；独立positive首次49.780988秒1F是admission append顺序与Journal newest-first顺序被错误强比。04只按已核Journal合同排序expected后仍List全record比较，未用set、删字段或改生产。后续正／负独立运行没有扩大原90秒预算。模型新Test14000length整份未读／未采用，owner接管，无R2。

最终资格导航为任务根`SOURCE-READY-SOFTWARE-QUALIFIED01.json`（7091B／2d44afbe…）、`QUALIFIED-SOFTWARE-COHORT02.json`（01a8e3e6…）、`QUALIFIED-MIXED-TEST04.json`（101893d2…），独立作者结果为`D:/ck3-state/resume91-root/clean-coverage-batch-independent-test01/INDEPENDENT-RESULT04.json`（15130B／3c4c4ff1…）。新增private overload之外，实际javac synthetic lambda$adoptInternal$19的capture descriptor也变化；public／protected集合保持不等于private ABI全部保持或原地redefine兼容。正式仅五span投影一个Bootstrap leaf，逐字同软件16784318候选，并逐字发表该新Test；未wholecopy实际工程或注入离线class。

本单元实际正式准备跨至北京时间11月5日，记录于2026-11-04T16:03:38.024686+00:00（北京时间2026-11-05T00:03:38.024686+08:00）。当前实例未采用此coverage候选。原restart13同局正常游玩另有2399父APPLIED及8日observed，午夜末次持有仍C67、待C68结算、保存仍365；不得把本软件绿授8日运行归因或速度。普通批126完整1509.34261秒中PLANNING1070.147709003、OBSERVATION348.8599043、OUTCOME87.1561677、JOURNAL2.888156399秒，0nonreturn；剩292.322983秒小于原reserve1425.1937321秒，未提交Life INTENT，以原预算规则收束并同委托进入127。原件`ordinary-publication-liveness01/BATCH126-ACTUAL.json`（c917a03c…），没有因此刷新旧命令期限或重载当前健康Java。


后到实机独验（收到／核对发生在北京时间11月5日00:02之后，事件发生在11月4日23:58:44）：Root于16:02:09.460716Z独核2402冻结99900B／d4d3c7e49e3d5be496bebd3b1ea2d3a0d6b9cd1bed1c105c53f82011a500399b、cycle68／ff0a9752…→新父2399／16b14931…→两个新child2391／2397 SETTLED，并接prevC67／71a1227b…。SETTLE实际15:58:44.309959700Z，date53157624→53157816、native1412／public1307、C68／ELIGIBLE_ADVANCE／pending=null，本次新增8eligible、累计493已结算。保存仍cycle51／date53154744、365日，未存128日、新SAVE0；未将午夜后收到回执误作今日再推进8日，也未倒称午夜初始交接已经持有它。来源为 `D:/ck3-state/resume91-root/resume-after-vacation-20261104/FIRST-C68-INDEPENDENT-VERIFIED.json` 及Runtime `D:/ck3-state/resume91-runtime/clean-restart-readonly-io-phase-fix01/first-new-cycle68-accepted01/ACCEPTANCE68.json`（5105B／e10b95f1…），Java已精读这些具名验证包，没有新Game查询。

该次运行intent13:10:04.725045Z至SETTLE完整10119.5849147秒，含该窗准备、失败、等待、切换与恢复；更早阅读交接不在此计时窗，不能把它冒作用户指令起的全部耗时。最后GET至SETTLE4429.0800857秒、restart13 START至SETTLE4421.7919721秒各保原切点，均不能替代前述完整窗。新增确认保存0，主指标没有有限秒／保存日，10秒目标未达，不借493累计旧日或8eligible作保存分母。

北京时间11月5日00:01后自然续行：普通127于16:01:11.901101700Z按原WALL_TIMEOUT收束，1807.1967781秒／attempt1／applied1；ACTION1200.6186001、PLANNING290.878330899、OBSERVATION170.794615099、JOURNAL103.286408498、OUTCOME41.517341298秒，各0nonreturn。父与C68已在旧deadline内结算，随后2404 Deferred→2405于16:01:19.439416600Z在同bc4467bc／restart13／host76092／原Game自然开始128。原件 `first-new-cycle68-accepted01/BATCH127-ACTUAL.json`（3184B／c3d84768…）；未重放控制、刷新旧deadline、重启Game／host／keeper或采用coverage候选，不外推未来健康。
