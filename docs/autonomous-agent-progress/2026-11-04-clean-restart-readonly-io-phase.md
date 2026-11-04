# Clean restart：本地准备后开始独立只读 IO 阶段

machine_id: `xenoamess-full-tower-eb9d2c1186`。实际记录于 `2026-11-04T13:52:49.372727+00:00`（UTC）。

同Game77132／Quarkus宿主76092的restart11于13:11:26.909249200Z启动，13:29:50.536188Z真实IOException收束，完整1103.6269388秒，没有LOOP、新游戏日、SAVE或账本移动。原clean恢复在取得初始HELLO后做完整snapshot、两次decodeComplete、coverage与project；到DriverBootstrap原817行再awaitHello时，原13:21:46.089392100Z期限已过。不能把该完整窗口当成单次Native RPC耗时，也不能以缓存五源优化推断覆盖此路径。

本修复只让Prepared实际clean bootstrap分支提供新的延迟只读IO阶段合同。Core转传`Supplier<Instant>`，DriverBootstrap在withFrozen的完整本地准备及project/gaps之后、后继HELLO之前取值一次；同一Instant用于该阶段HELLO、handshake、fresh full READ及适用的observe。上层owner按原Clock及原10分钟Duration产生此独立只读阶段；初始HELLO／handshake仍用原initial phase。旧public Instant overload和全部其它调用保持固定原Instant，旧ARM2358／resume2364／父2366的命令期限不动，不重放动作或改账本。此前本地准备的墙钟继续计入端到端成本，未因此授予CPU提速。

实际三源DriverBootstrap／Core／Prepared只改13个具名span，全部whole-byte inverse exact。唯一模型任务完整返回56.936264秒／有效TTFT15.1122941秒；原diff有删除旧overload、Core双try／API不完整、越界改initialRecovery和漏接后继handshake等错误，整diff未采用／未编。owner只参考延迟supplier思路并完成这些纠正，不称模型自主诊断或整份代码采用。

Native必要首编仅这3TU，实际compiler0、55class、10.8812786秒、stderr空；持久fence／terminal／END和资源释放已核。实际Bootstrap与Core新增public Supplier泛型签名、有具体Code，两个旧Instant方法仍保留。来源：`D:/ck3-state/resume91-java-delivery/clean-restart-readonly-io-phase-p0-next/native-first-preparation01/QUALIFIED-PRODUCTION01.json`（ff8e0a6c…）；候选与13span原件在同任务根的`SOURCE-READY-CANDIDATE01.json`、`OWNED-SPANS01.json`。独立关键生产链Test仍由专岗实施，尚不授它通过、Runtime采用、LOOP或提速。

正式三源以同13个唯一匹配span投影，保每份正式文件的其它字节；实际编测raw变体与正式outside不同，当前没有重编正式整个组合。随本单元发表的canonical lookup新Test为原15916B／e2b91798…逐字版本：在另一个明确current五源cohort中，新1TU／7class后，真实1方法覆盖5场景×3作用域共15路径，再原12受影响方法binary RUN-only，分别1P和12P／0skip-abort-fail。其public writer／archive行为不授完整Root／GCA preview／commit成功，也不替代本P0独立Test。

其它候选边界仍独立：当前PublicData8999B／60c4只新1TU／1class后原4Testbinary的同6方法RUN-only6P；财政raw两源c624／feb首编32class后，新561e单Test TU／1class、3方法3P（含10内部负例），都未重编旧支持类。它们与正式e746或财政wrapper组合不同，未wholecopy正式源，未授装载／游戏／性能信用。精确qualified SourceReady均已交唯一Runtime owner，文档与Git不是其采用前置。

Root后到完整历史成本窗为旧ba4 START06:33:53.6863905至restart10 END12:16:55.5810062，20581.8946157秒／36新增eligible日＝571.71929488秒／eligible日；它含旧14162.5370547秒、准备／GET间隙3616.0933346秒和后到冷恢复／停止2803.2642264秒。该窗新增确认保存日0，无有限秒／保存日，且不含之后假期idle或当前restart11，不能当作当前全程速度。原505.8分段事实保留。10秒／新增SAVE_CONFIRMED日目标未达，G2仍按最后完整验收6/8。


2026-11-04T14:28:36.357667+00:00 后到独立行为与实际采用：最终原Test05／25978B／d6a1ae58…仅新1TU首编0／10class，随后原3个unique selectors真实3P／0skip-abort-fail、stderr0；JUnit ACTUAL43.239616秒、XML41.341秒、operator44.266353秒分别保留，不以XML时长替完整成本。原Fixture37class、旧881Support2class及生产55class全部复用未重编，实际JUnit预算为Root明确授权的60秒，旧SourceReady的30秒只是当时提议。独立作者与Native均实读同XML43612B／b228f0d6…及持久fence／close0／资源释放；完整结果为 `D:/ck3-state/resume91-root/clean-restart-io-phase-independent-test01/INDEPENDENT-RESULT05.json` 与P0任务根的 `SOURCE-READY-BEHAVIOR-QUALIFIED01.json`（a52cada3…）。

这三个软件方法实际经过controller capture／canonical admit、DriverBootstrap与软件NativeGameTransport端点，覆盖本地准备使初始期限真实过期后才解析一次新阶段、后继实际端点调用共用同Instant，旧fixed期限仍过期拒绝、初始HELLO提前拒绝，以及null／抛错／旧generation不能fresh-read或授信用。初始ping仅一次，没有重放handshake。物理ManagedGameSession／Core／Prepared完整入口、缓存open中的handshake参数独立可观测性及全部source／head负例仍未由这些方法验完；真实游戏IO、LOOP、推进与SAVE另验，不将3P扩成整个Root通过。

原两轮3F保留：22.253秒发生在Test reader把过大的max投给artifact-store，29.47598秒发生在fixture外部original-driver.json baseline误投CAS reader，两次均未到新Supplier；04另有未声明IOException的Test-only compiler RED且没有JUnit。最终reader只对writer当前baseline及精确fixture路径做实际bounded／length／SHA读取，其余保CAS＋clamp，Bootstrap原readExact校验未放松。测试模型新增方法全拒、owner接管，未把这些harness红伪作生产故障，生产三源始终未为harness改动。

Runtime已于14:13:10.166973Z实际采用11源，唯一必要GET于14:13:22.905465Z返回200／12.6613825秒，同host76092的 `312b94f6-4101-4e5b-a119-d548bf72c507`／restart12／loader4962708e于14:13:22.829483500Z实际START；Dev自身140个物理class输出已冻结，未注入离线class／未重启Game、keeper或宿主。运行岗先保留自有701B／9b8e8a39…的只读P0 hold，在直接核真3P后于14:24:13.377568Z仅rename保全并消费它。上述冻结切点仍BOOTSTRAP，来源文件采用、GET、START和物理输出不等于新IO阶段命中、LOOP或新游戏日；不能为本发表再发GET。其原件集中在 `D:/ck3-state/resume91-runtime/clean-restart-readonly-io-phase-fix01/runtime-adoption01/`。

Java早先soft-qualified导航包的at_utc误继承candidate13:41:37，原件保留；最终behavior-qualified已将candidate_at_utc与实际qualified_packaged_at_utc14:24:38.550330Z分列。Java在后到运行事实未送达时未授Runtime采用，其后已以 `RUNTIME-FACTS-ADDENDUM01.json`补记实际更早的11源采用／START与hold消费，不覆盖旧回执。新IO phase仍是原每操作10分钟，初始phase与本地CPU另计，旧commands期限不变；当前新增确认保存仍0、10秒目标未达，G2仍6/8。

后到实际终态：restart12于14:32:43.440378600Z因HistoricalReadScope的NoClassDefFoundError退出，完整1160.6108951秒、没有LOOP／新日／SAVE。调用已到finishObserved，确实越过旧817期限阻点；缺失类型本次已有Dev物理输出，新增类型可见性是独立故障。Runtime随后撤回整个缓存五源，保期限P0三源＋财政两源＋PublicData一源，于14:45:02.517987600Z同host实际启动restart13。其冻结切点仍BOOTSTRAP，不能授普通游玩恢复或性能通过；[类型边界、整组撤回与精确来源](2026-11-04-restart12-classloader-boundary.md)另记。历史3P和全部harness红保留，离线正规loader诊断不阻本轮六源恢复。

后到同局验收：15:05:41.991189900Z，保留期限P0三源＋财政两源＋PublicData一源的restart13／bc4467bc在同host76092、同Game77132真实进入普通LOOP／next126，从START计1239.4732023秒。Java具名核对`rollback-five-recovery01/ACTUAL-LOOP.json`：life-budget-hint restored、C67／pending=null、saved365保持。这次clean bootstrap实际通过，旧817故障已在实机越过；新World、推进、周期结算、SAVE与速度仍各等实际回执，不从LOOP授新增保存或10秒达标，不为离线候选打断当前健康委托。
