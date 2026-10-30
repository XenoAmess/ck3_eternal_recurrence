# runtime91 同局续行

machine_id: `xenoamess-full-tower-eb9d2c1186`。唯一运行 owner `/root/runtime91`，独占运行 S/MB、Game、supervisor、账本和业务 worker。用户于本轮明确结束休假停止，要求自动游玩第一优先、八 M 并行和本地模型高并发。

- 已读取 resume90 总交接、运行交接与各 source-index；不恢复旧 60 人编制要求。
- `2026-10-30T18:47:19.333554Z` Win32 实读确认同一无 mod Game71464 / FILETIME134378397668266369、supervisor305760 / FILETIME134378397644711323 均 wait0=258/exit259；未出现 supervisor stop/terminal。原件 `D:/ck3-state/resume90-runtime/INITIAL-RESUME91-PROCESS-READBACK.json`。
- 接手仍为 canonical102 / repair_required / BATCH_INTERRUPTED15、next16，保留原已结算军事 FOCUS 与 dirty/未保存状态；不重放 FOCUS 或 UNKNOWN，不新增 SAVE 热接续前置。当前新增普通动作与游戏日仍为 0。
- worker103 的真实首故障为 `ContinuityBatchJournal.settledSemanticTransport:853` 以 ledger 预算读取完整 SEM。精确当前源码和真实 stderr 已交唯一源码 HTTP 协调 `/root/models91` 出最小方法候选；D 隔离验证并行准备。
- D 隔离岗同时处理已保留的 FamilyObligations exactBuild SHA 误比，以及复用既有普通 selector 的 qwen 配置/参数。它们不写 S/MB/账本，也不操作 Game；运行期模型并发预留 1，由运行 owner 发起。

S: `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control`；MB: `D:/codex-ck3-demos/2026-10-22-java-phase1/build/complete35-candidate31-h5r5`；当前局: `D:/ck3-state/ck3-java-g2-resume85-vanilla02`。本轮 D 小型输出根 `D:/ck3-state/resume91-runtime`。只采用具体叶与必要局部增编，不全树覆盖、reset、stash 或 stage。

## 103恢复修复与104启动

- 源码模型任务 `runtime-sem103` 首次 HTTP200/完整 JSON stop，TTFT14.446秒、总25.645秒。候选仅把 SEM 解析切换到 `DriverJson.object(...MAX_NATIVE_BYTES)`，引用解析同步用对应 typed reader；原 machine/Game/session guard 保持。
- D 隔离真实 canonical102 + 全102历史事件回归：旧实现2F均复现853预算错误；候选严格 javac0，完整 `readSettledSameGame` 与实际529451B SEM的 TransportSession/错Game拒绝共2P/0F/0skip。next16/used0..15、dirty Focus1、pending0、SAVE0、committedDays0保持，fixture commits0。冻结仍依赖原 NV 不可变 CAS，不宣称完整可搬迁闭包。证据 `D:/ck3-state/resume91-runtime/sem103-regression/{SUMMARY.json,README.txt,DELIVERY.json}`。
- S/Z最小采用两行后，MB104于 `2026-10-30T18:51:55.401536Z`–`18:52:41.351776Z` 真实exit0/45.950秒；默认mvn、`-T2 -pl application -am`、复用MB无clean，日志明确只增编application的1个源码文件。精确交付patch已交Java正式owner，不覆盖Z历史整叶。
- worker104 / PID131356于 `18:52:54.284719Z` 在同Game启动，使用 `provider/worker-start91-qwen.args`。维护原 `run-worker90.py` 只加可选args及如实配置元数据；`decision_provider` 已配置为qwen38-coder，不能据此授运行模型HTTP或决策信用。
- provider复用既有普通accept/wait selector，配置最多6次/固定10秒退避，共用实际当前planning/command/provider总deadline；现schema不支持完整10/20/40/60/60秒序列。非ActionSelected结果不会调用模型。
- 18:54:05Z/elapsed70.90秒窄jcmd显示prepare阶段在ConstructionDomainLifecycle类加载；18:55:04Z/elapsed130.10秒已推进到NativeGameAttachment.attach/NativePipeEndpoint.Config，仍为FileInputStream.open0，CPU仅3.39秒。stdout/stderr当时仍空；不臆测根因、不重启Game，也不在活worker下写MB。尚无loop/普通模型HTTP/新动作/新增日证明。

## 下一消费链候选

FamilyObligations真实102输入新鲜复现错误；模型首候选严格编译0但行为0P1F，大小写不足被拒，未POST纠错前owner接管。最终D候选按SourceReference实际raw EXE SHA与`CURRENT4.sha256()`做忽略大小写比较；version、version@SHA及错误SHA仍拒绝。严格javac0、真实102输入1P/0F/0skip，仅到admission sentinel，实际Root admission/Native preview0。`D:/ck3-state/resume91-runtime/obligations/DELIVERY.json` 为候选回执。104真实END后已S/Z小叶采用，正式Java owner正常发表 `8611e0f227`，MB尚待与下述P0合并局部增编，不把候选绿色计作游戏动作。

## 104真实终态与下一安装期限修复

worker104于 `2026-10-30T18:57:40.464349Z` 真实exit1/286.179647秒，未进入ordinary loop，未产生普通模型决策/新动作/新增日。stdout明确 `WORKER_FAILED`，stderr新确定原因为 `RootRuntimeCatalogFactory.install:379` 在纯本地catalog装配尾部调用 `RootRuntimeContext.requireCurrent:358`，以装配开始时operation deadline授资格而报过期。103的历史SEM恢复错误已实际越过；canonical仍102/repair_required、next16、pending null、原dirty Focus保持，Game/supervisor保留。

Root有界资源实读 `D:/ck3-state/resume91-root/P0-RESOURCE-OBSERVATION01.json` 与前述类加载栈一致显示等待，但不能单凭IO字节计数认定物理I/O根因。不修改Game，不重复全树/来源审计，不把新的长整体期限作为修复。

新模型任务 `runtime-install104` 已真实完整回包，TTFT3.355秒、总16.634秒。候选将Game存活/退休检查抽为 `requireActiveGame()`，真实操作的 `requireCurrent` 仍先检查原deadline；catalog纯本地装配使用active检查。owner审阅补同方法入口277的同类时间误用（模型首版仅尾端），D小候选/回归正由provider91处理。后继sessionConfiguration与session.install本已分别使用新的runOperationPhase期限；暂不扩大无真实失败范围。

## 105实际重新进入普通循环

- 上述deadline两叶已S/Z最小采用；strict javac exit0/6.911秒，现成 `RootOrdinaryRuntimePhaseDeadlineTest` 实际4P/0F/0skip。第一次test args反斜杠转义导致javac1，未进JUnit；更正参数后通过，原红保留。离线未搭新的active-Game大fixture，不宣称完整catalog正向通过。
- MB105于 `19:03:56.180821Z`–`19:04:19.541554Z` 真实exit0/23.361秒，默认mvn `-T2 -pl local-service -am`，复用MB无clean；实际重编native-transport的1个Family源和local-service的2个deadline源，其余reactor缓存复用。证据 `D:/ck3-state/resume91-runtime/combined105-build/ACTUAL.json`。
- worker105/PID323888于 `19:05:18.446439Z` 同Game启动；`19:05:50.0109348Z` 已真实emit `ORDINARY_WORKER_LOOP_START` / next16，启动后31.564秒。105实际越过104的catalog安装故障。开始实际普通batch16，Game不重启、旧FOCUS不重放。
- Root在105安装阶段暂缓研究新编译；进入loop后恢复统一单研究编译槽/P0优先。该资源处理不外推为I/O根因证明。
- qwen普通selector已配置；尚无新的实际HTTP/模型决策/动作/新增游戏日回执，不把LOOP_START当游玩完成。
