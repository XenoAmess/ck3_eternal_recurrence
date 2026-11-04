# Clean restart：本地准备后开始独立只读 IO 阶段

machine_id: `xenoamess-full-tower-eb9d2c1186`。实际记录于 `2026-11-04T13:52:49.372727+00:00`（UTC）。

同Game77132／Quarkus宿主76092的restart11于13:11:26.909249200Z启动，13:29:50.536188Z真实IOException收束，完整1103.6269388秒，没有LOOP、新游戏日、SAVE或账本移动。原clean恢复在取得初始HELLO后做完整snapshot、两次decodeComplete、coverage与project；到DriverBootstrap原817行再awaitHello时，原13:21:46.089392100Z期限已过。不能把该完整窗口当成单次Native RPC耗时，也不能以缓存五源优化推断覆盖此路径。

本修复只让Prepared实际clean bootstrap分支提供新的延迟只读IO阶段合同。Core转传`Supplier<Instant>`，DriverBootstrap在withFrozen的完整本地准备及project/gaps之后、后继HELLO之前取值一次；同一Instant用于该阶段HELLO、handshake、fresh full READ及适用的observe。上层owner按原Clock及原10分钟Duration产生此独立只读阶段；初始HELLO／handshake仍用原initial phase。旧public Instant overload和全部其它调用保持固定原Instant，旧ARM2358／resume2364／父2366的命令期限不动，不重放动作或改账本。此前本地准备的墙钟继续计入端到端成本，未因此授予CPU提速。

实际三源DriverBootstrap／Core／Prepared只改13个具名span，全部whole-byte inverse exact。唯一模型任务完整返回56.936264秒／有效TTFT15.1122941秒；原diff有删除旧overload、Core双try／API不完整、越界改initialRecovery和漏接后继handshake等错误，整diff未采用／未编。owner只参考延迟supplier思路并完成这些纠正，不称模型自主诊断或整份代码采用。

Native必要首编仅这3TU，实际compiler0、55class、10.8812786秒、stderr空；持久fence／terminal／END和资源释放已核。实际Bootstrap与Core新增public Supplier泛型签名、有具体Code，两个旧Instant方法仍保留。来源：`D:/ck3-state/resume91-java-delivery/clean-restart-readonly-io-phase-p0-next/native-first-preparation01/QUALIFIED-PRODUCTION01.json`（ff8e0a6c…）；候选与13span原件在同任务根的`SOURCE-READY-CANDIDATE01.json`、`OWNED-SPANS01.json`。独立关键生产链Test仍由专岗实施，尚不授它通过、Runtime采用、LOOP或提速。

正式三源以同13个唯一匹配span投影，保每份正式文件的其它字节；实际编测raw变体与正式outside不同，当前没有重编正式整个组合。随本单元发表的canonical lookup新Test为原15916B／e2b91798…逐字版本：在另一个明确current五源cohort中，新1TU／7class后，真实1方法覆盖5场景×3作用域共15路径，再原12受影响方法binary RUN-only，分别1P和12P／0skip-abort-fail。其public writer／archive行为不授完整Root／GCA preview／commit成功，也不替代本P0独立Test。

其它候选边界仍独立：当前PublicData8999B／60c4只新1TU／1class后原4Testbinary的同6方法RUN-only6P；财政raw两源c624／feb首编32class后，新561e单Test TU／1class、3方法3P（含10内部负例），都未重编旧支持类。它们与正式e746或财政wrapper组合不同，未wholecopy正式源，未授装载／游戏／性能信用。精确qualified SourceReady均已交唯一Runtime owner，文档与Git不是其采用前置。

Root后到完整历史成本窗为旧ba4 START06:33:53.6863905至restart10 END12:16:55.5810062，20581.8946157秒／36新增eligible日＝571.71929488秒／eligible日；它含旧14162.5370547秒、准备／GET间隙3616.0933346秒和后到冷恢复／停止2803.2642264秒。该窗新增确认保存日0，无有限秒／保存日，且不含之后假期idle或当前restart11，不能当作当前全程速度。原505.8分段事实保留。10秒／新增SAVE_CONFIRMED日目标未达，G2仍按最后完整验收6/8。
