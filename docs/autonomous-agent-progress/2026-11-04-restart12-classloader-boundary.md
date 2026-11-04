# restart12 新增类型加载边界与六源恢复

machine_id: `xenoamess-full-tower-eb9d2c1186`。本记录实际封包于2026-11-04T15:02:14Z，时间均为UTC；承接[clean-restart只读IO阶段修复](2026-11-04-clean-restart-readonly-io-phase.md)，保留所有更早软件与运行切点。

restart12于14:32:43.440378600Z真实结束，故障为 `NoClassDefFoundError: DriverReadHistoryPublisher$HistoricalReadScope`。具名调用链为RootInstalledCatalog.planningInputs260→RootRuntimeReadiness.construct169→Core.finishObserved1556→finishCleanRestart1481，cause包括AppClassLoader与QuarkusClassLoader父回退。14:13:22.829483500Z START至该终态完整1160.6108951秒，实际LOOP、新推进、新SAVE均为0，head2370／C67／pending=null、已保存365日保持。

这次确实越过了restart11的817期限阻点并进入finishObserved，须与后继类型故障分开记。该事实不提供新只读阶段各RPC独立耗时或CPU提速；独立3P、生产3TU／55class及既有缓存软件13P仍是原有限软件结果，不能扩成实际LOOP、完整Root或10秒／新增保存日达标。

`HistoricalReadScope`与另一个新嵌套类型已列入本次Dev changed-class清单，冻结的140个实际Dev family输出中也确有application/classes文件，不能解释成未编译或磁盘缺失。实际故障与原件：`D:/ck3-state/resume91-runtime/clean-restart-readonly-io-phase-fix01/runtime-adoption01/FAILURE12.json`（3224B／af7a1e72…）、同根`FAILURE12.stdout-suffix.bin`（13527B／4cdc8644…）及`DEV-MODULE-OUTPUTS.json`（64521B／7674079f…）。只有具名冻结原件核对，没有为本文新增Game查询或重试。

Quarkus3.40.1.1的[PathTreeClassPathElement实现](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/independent-projects/bootstrap/core/src/main/java/io/quarkus/bootstrap/classloading/PathTreeClassPathElement.java)会先检查非空资源名单；缺名时直接返回null。因此物理class存在不能单独证明可见。官方[类加载说明](https://quarkus.io/guides/class-loading-reference/)区分持续存在的Base Runtime与每次重建的Runtime层；reloadable依赖及引用方需要匹配层次，早期类加载配置不能靠后改磁盘文件追认本host生效。上述机制与本次栈相容，当前尚未持有该host实际定义加载器与资源名单的直接回执，不授唯一根因。

Runtime优先恢复正常游玩，已于14:44:54.948346Z逐字撤回整个缓存五源到本次采用前的实际preimages：Publisher123683B／50a52e6c…、Lineage20928B／4549f9af…、RootInstalledCatalog55968B／92307376…、NativeOutcomeArchive124074B／88063e3a…、GovernanceCadenceActions11905B／8a1915af…。这是一致撤回五源，包含跨文件新增类型依赖；没有只移除Root的一处lambda后遗留其它引用，也没有删除或注入class。

实际保留六源为期限P0的DriverBootstrap／RootApplicationAssembly／RootOrdinaryRuntimeAssembly，财政的OrdinaryCycleTransitions／FinanceRuntimeInstaller，以及当前60c4 PublicDataJson。每份bytes／SHA在 `D:/ck3-state/resume91-runtime/clean-restart-readonly-io-phase-fix01/rollback-five-recovery01/SOURCE-ADOPTED.json`中逐项对应。Game、keeper、Quarkus宿主及账本原位保留，原命令没有重放。

唯一必要GET于14:44:55.229874Z开始，14:45:02.570376Z返回200／7.3405095秒；同host76092的新委托 `bc4467bc-13a9-4893-8304-371824856190`／restart13／loader2a50eaed于14:45:02.517987600Z实际START。`rollback-five-recovery01/ACTUAL-START.json`冻结切点仍BOOTSTRAP，未授后继LOOP、新日或SAVE；正式发表和离线检查器不作为此次恢复前置，也不引发下一次GET。

离线诊断只消费Runtime冻结的serialized-dev-app-model、dev.jar、dev-mode-context、三POM、properties与launch元数据，导航为 `classloader-failure12-inputs01/SOURCE-READY-LOADER-INPUTS01.json`（7018B／6d0378a8…）。其中实际后到instrumentation=true保持为事实；CDI index声明不等于类加载路由。新模型任务仅为有限磁盘模型检查器，HTTP200但length6000，整份候选未读／未解析／未采用、不拼接、不自动重发。

原工具合同误把`.dat`当Java ObjectInputStream格式。owner接管的168行只读检查器首编1TU／2class通过，1.6338443秒；唯一模型读取run真实1／0.3027204秒、stdout0，构造即报invalid stream header7B22706C，尚未调用getter或产生目标行。fence／terminal／close及资源释放均真实保全，不能从该工具红推断模型无资源或当前host根因。原件在 `D:/ck3-state/resume91-java-delivery/classloader-failure12-model-inspector01/native-preparation01/RESULT-FIRST02.json`（13906B／0faccea6…），不再为这个格式假设重编或重复JVM。

后续纯Python对精确344353B／57b661d4…冻结文件做JSON解析成功，顶层6个键、dependencies331、local-projects33；只投影三个目标模块，所有resolved／source路径只作为字符串，没有跟随到C。结果 `classloader-failure12-model-inspector01/FROZEN-JSON-MODEL-PROJECTION01.json`（23211B／49d55a24…）持有application／native-transport原flags110，各自workspace与classes路径，以及app-artifact localservice原flags36。依对应版本的[DependencyFlags源码常量](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/independent-projects/bootstrap/app-model/src/main/java/io/quarkus/maven/dependency/DependencyFlags.java)，两份依赖都已声明RELOADABLE且非parent-first；app root另有路由，不能因其缺依赖RELOADABLE位就说root不可热载。因此这份磁盘声明不支持“application没有声明reloadable”的解释，也不证明当前host的定义loader或资源名单；未盲加late property并称已修。

后继正规接线修复以实际磁盘声明和必要软件复现为依据，不以旧309资源缓存软件证明代替本次新增类可载验收。若最终确需重建Java Quarkus宿主／模型，必须先给必要性、候选配置及同Game／keeper／账本保留的唯一owner交接，由Runtime控制实际采用；本岗不改C、不操作host或GET。当前六源恢复独立继续。新增确认保存仍0，无有限秒／保存日，目标10秒未达，G2仍6/8。
