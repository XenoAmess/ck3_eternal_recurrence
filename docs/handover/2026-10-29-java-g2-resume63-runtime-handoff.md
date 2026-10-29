# resume63 Java 实机与 Quarkus 接续交接

machine_id: `xenoamess-full-tower-eb9d2c1186`。现场只读观察时间：2026-10-29T14:12:33Z、14:14:37Z（北京时间22:12、22:14）。

用户最新要求温和收尾，覆盖此前持续推进及60并发要求。本段没有启动 Main318、dev58、新业务 worker 或新 Game；不为交接修复新问题。现有 CK3 和独立 supervisor 保留，**不得把 worker 退出当作需要重新开局**。本文件是现场和恢复导航，不授予自动启动或 UNKNOWN 重放。

总交接入口：[vacation handoff](2026-10-29-java-g2-resume63-vacation-handoff.md)。

## 现场状态

| 对象 | 最后实际状态与出处 |
| --- | --- |
| CK3 | `tasklist`在14:12:33Z仍观察到`ck3.exe` PID **171676**。owner和最后原生/业务回执绑定出生值 **134376899432680684**。这次收尾未另取 Win32 FILETIME，不能把 owner 的历史出生字段称作新的出生观测。Root明确本场为无Mod的1066罗贝尔；未在收尾重扫Mod树。 |
| 独立 supervisor | `tasklist`在14:14:37Z仍观察到`java.exe` PID **147108**。owner记录出生值`134376899414027849`；`terminal.json`和`stop-request.json`不存在。未给 supervisor STOP，也未杀进程。`jcmd -l`未列出该 supervisor，因此进程存在与 JVM attach 可见性分开记录。 |
| 业务 worker57 | PID **287096**，13:35:29.232Z启动，**13:58:41.917Z真实退出4**，stderr0。最后结果为`WORKER_TERMINAL_FAILURE`，不是clean0；无自动重启。 |
| dev / Maven | 14:12只读`jcmd -l`未列出普通worker、DevModeMain或Maven目标，`netstat`无8089监听。最后实际Main是 **317 exit0**。318从未启动，dev58和后继worker从未启动。此处没有通过HTTP触发扫描。 |
| 执行协调状态 | `O/CURRENT-MAVEN-STATUS.json`在14:14:37Z记`execution_owner=/root/runtime63`、`running=false`、最后317/0、`phase=USER_REQUESTED_HANDOFF_NO_NEW_EXECUTIONS`、`shared_source_write_allowed=false`。idle不代表允许自动启动，不能沿旧GO继续。 |

缩写仅用于阅读，实际命令使用展开后的路径：

```text
S  = D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control
W  = D:/codex-ck3-demos/2026-10-22-java-phase1
O  = D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration
V  = D:/ck3-state/ck3-java-g2-resume63-vanilla01
MB = D:/codex-ck3-demos/2026-10-22-java-phase1/build/complete35-candidate31-h5r5
```

活跃 owner：`V/state/game-supervisor02/owner.json`，session为`resume63_vanilla_game02_20261029`。owner中的原HELLO指向`V/artifacts/native-persistent02/native-hello.packet`，不是新worker的新HELLO。Game只有supervisor持Job/STOP权；业务ATTACHED会话关闭只断pipe/观察handle。

## worker57的实际结果与账本

原件目录：`V/artifacts/persistent-java02/worker-resume57/`，保留`started.json`、`stdout.log`、`stderr.log`、`terminal.json`。

- 实际从batch17开始。17、18、19均`WALL_TIMEOUT`，每批attempt0、ACK0、applied0、committed_saved_days0。finance已明确clear，下一stage被`independent same-frame native query unavailable`阻住，原文如此，不是新读回成功。
- batch20从13:53:19.169Z到13:58:41.645Z，完整墙钟322.475秒，超过本批300秒预算。末detail为`actual plan publication blocked: actual Council/Crown planning reconciliation unavailable: runtime context deadline expired`，terminal为`INCOMPLETE_MIGRATION`。Main随之返回4。
- 最后实际帧仍是player31254、`date_raw=53144328`、native_revision182。本段未取得首普通业务动作确认或新增游戏日；loop运行、原生读取和编译均不算游玩进度。

14:14:37Z的精确小文件：

| 原件 | bytes / SHA256 |
| --- | --- |
| `V/continuity/continuity.json` | 87857 / `13b72cf971b9028d5dc84fb62207652f837c8d78594011570c25dd0887e4f5c9` |
| `V/state/worker-restart-ticket.json` | 583 / `882ab7a9ac3914c63fa50430956ad89c12f567d040b903ef1df306203c6bd4a5` |
| `worker-resume57/stdout.log` | 16786 / `ba7a1ed75b6ae4ea93f69f7218046e1f3b90bc8288c139b462d5f32a93285182` |
| `worker-resume57/terminal.json` | 349 / `6696581a9225f3bb906f9ac7273a7033d3967e2b0a29d2444618f7c753761321` |

当前canonical状态为`repair_required`、sequence **71**、batch20 `BATCH_INTERRUPTED`。`latest_binding`保留原actor31254、date53144328和native_revision159。实际events目录是 **`V/continuity/ROOT-CONTINUITY-WINDOW-EVENTS/`**，不是猜测的JSONL文件。

旧ticket修改时间仍为11:15:55.837Z，ticket.sequence **57**，head_digest为`578ec43ed498168f6d9a57e677162f65ceb713f7224fbcfacacc643084227b8b`；它不是worker57本次新发的票，也不能把batch序号当ticket序号。下一次不得伪clean或把这张旧票直接追认为当前head。

Launcher定点读到的真实suffix：57为capture/next15；58/59为START15/INTERRUPTED；60为INITIAL_NO_DISPATCH_RECOVERY/next16；61/62为START16/INTERRUPTED；63为recovery/next17；64/65为START17/DEFERRED；66/67为START18/DEFERRED；68/69为START19/DEFERRED；70/71为START20/INTERRUPTED。该范围未见ACTION/READ/SAVE事件，**这个实际事件读取结论不能由0attempt代替**。现有suffix parser不接受其中DEFERRED，不能为继续运行而手改ledger或跳过reducer。

## 协作停止文件的完整事实

runtime63在13:54:08.881Z以CREATE_NEW写了`V/state/worker-stop.request`，只请求worker57正常批间停止，不是Game STOP。原body：

```json
{"schema":"xar.java-ordinary-worker-cooperative-stop/v1","machine_id":"xenoamess-full-tower-eb9d2c1186","observed_at_utc":"2026-10-29T13:54:08.881Z","execution_owner":"/root/runtime63","worker_pid":287096,"reason":"Same-Game clean handoff to repaired Java/dev worker; no Game STOP or START","token":"c12eeb73-916c-4ca8-adf9-9efc55dfd059"}
```

worker57实际先遇上述失败返回4，不能因为存在stop请求就说它正常clean停止。**在收到温和收尾指令之前**，runtime63于14:04:15.620Z归档其退出4与请求原文，再核对完整token/owner/pid/原bytes，只删除自己的该请求以准备当时已授权的显式接续；没有删除外部operator请求、没有改票或ledger、没有发新worker。14:12和14:14实际stopPath均ABSENT。

归档：`V/artifacts/persistent-java02/runtime-handoff58/STOP57-OWNER-CONSUMED01.json`，1295B，SHA256`12e4ea6fe0fca3e1811626b3e40ef1de379e0ce6be3fc239ad0787b34233f7bd`。`runtime-handoff58`只是控制记录目录名，**不代表58已执行**。

## 已采用与未采用的修复边界

以下是下一次必要增量候选，收尾时没有为它们再编译或重启：

1. **Events读取失败原因传播：S已采用，未进入Main317。** `D:/ck3-state/events63-war-window-read01/read-reason318/SOURCE-ADOPT01.json`记录真实9叶before/after。`EventReadBinding`改为封闭Captured/Unavailable并保原Unavailable对象，4个生产调用及既有tests同步。D严格16源javac0，原EventPolicies整12P、PendingCollector2P；其余迁移测试仅编译未重跑。它只补完整原因，仍Wait/原拒绝，不放宽guard。Main318未执行，不能说实机已加载新诊断。
2. **DriverPlanningEvidence：S已采用，未进入Main317。** `D:/ck3-state/ck3-java-g2-resume63-readiness-evidence-native-packet01/SOURCE-STOP-ACTUAL01.json`记录2叶；production6818B/SHA`9926f967958ecf9766734668505c66a0dfb84abed9b69020798741e4b120139e`。实际修复是以lease.semantic的原native packet独立重放两manifest并验证身份/bytes，删除实施源码资格重读；不是伪造cache，也不改Collector firstguard/prune。D javac0+Owned4P。
3. **批预算到期分类：仅D候选，NOT_ADOPTED。** `O/local-model-boundary-experiments/PLANNING_DEADLINE22/candidate/{SessionController.java,SessionControllerRegressionTest.java}`拟在planner、afterPlanning返回后补本批`requireTime`，保真finite guard及UNKNOWN。最后实际命令把`-J-Xmx256m`错放`@argfile`，javac exit2/0.190s；baseline及whole61均NOT_RUN。不要把候选当已编译/通过。
4. **广义suffix proof：仅D候选，NOT_ADOPTED。** `D:/ck3-state/ck3-java-g2-resume63-journal-dirty-suffix01/candidate/`含Journal/Cycles/OriginalReducer及test副本。此前JAVAC03=0/4.319s不包含最后DEFERRED parser hunk；该新hunk未编未验。修复必须保持实际业务前沿，不能按“无动作”直接重建任意旧票。
5. **captured当前日期/actor消费者：没有实际实现或采用。** `O/dirty-current-recovery01/src/.../{FreshGameplayEntryAuthority.java,DriverBootstrap.java}`仍与before/S相同；`PREPARED-ACTUAL03.json`保留准备边界，MODEL02.request.json从未POST。不能将其描述为修好了无票/dirty恢复。

**纠正早期推断：没有证明startup寿命被用于整个长跑。** Service实读`RootRuntimeContext`只检查调用者传入的当前deadline，本身不存startup deadline；Loop每批也新建预算。实际可证的是末批已越300秒并报告上述治理错误。定点源码分析支持的候选根因是planner返回后缺少本批时间检查，随后治理completion才按过期操作deadline报错，被归为INCOMPLETE_MIGRATION；该候选尚未通过回归确认。保持Context操作限时；不要因旧消息删掉它或简单延长所有deadline。

其他已STOP源码（Family、ordinary等）的最终清单以总source-index为准。本岗没有以局部D测试外推整个源码图、Main317或实机通过。

## 恢复执行时的最短路径（本次全部未执行）

用户恢复工作后，先消费当前Game/supervisor和canonical实际状态，再完成suffix producer/消费者及预算分类的必要软件回归；保留UNKNOWN、动作identity、原writer及真实后态。不得新START、SAVE、RESTORE来绕恢复，也不补旧ENV/BUILD/REGISTER/Source/Quote/Definitions资格链。

必要修复闭合后，沿同一S、MB、m2做一次实际受影响模块增量。历史可复用命令对象为`O/MAINDEV317-command.json`，默认`mvn`、offline、`-T2`、`-pl local-service -am compile`，不clean/fresh、不重拷全图。例如展开路径后：

```text
mvn --offline --fail-at-end -B -ntp -e -f D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control/pom.xml -Dmaven.repo.local=D:/codex-ck3-demos/2026-10-22-java-phase1/m2 -Dck3.build.root=D:/codex-ck3-demos/2026-10-22-java-phase1/build/complete35-candidate31-h5r5 -Djava.io.tmpdir=D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/complete35-candidate31-h5r5-tmp -Dmaven.compiler.useIncrementalCompilation=true -Dmaven.compiler.showCompilationChanges=true -DskipTests=true -Dmaven.test.skip=true -T2 -pl local-service -am compile
```

实际普通worker的旧argfile为`V/artifacts/persistent-java02/worker-resume-freshness15s-operation60s01.args`，Main为`org.xar.ck3.control.service.root.RootOrdinaryWorkerMain`，参数owner、business config、`resume`。这只是路径导航，不是允许忽略当前repair状态的重试按钮。

优先Quarkus接续的现成结构化调用：`O/quarkus-worker-dev01/PRODUCTION-DEV-INVOCATION03.json`。它使用默认mvn和原S/MB/m2：

- 完整goal `io.quarkus.platform:quarkus-maven-plugin:3.40.1.1:dev`，不靠失效的offline prefix；`quarkus.package.main-class=ordinary-worker-dev`、`xar.worker.dev.enabled=true`、`quarkus.live-reload.instrumentation=false`、`noDeps=false`。
- 保`quarkus.bootstrap.effective-model-builder=false`；**没有**`maven.top-level-basedir`。LS POM已经去掉引发运行期javac `invalid flag:1000`的拆分诊断参数；不改个人application.properties。
- HTTP只监听`127.0.0.1:8089`；2个原args为`V/state/game-supervisor02/owner.json`与`V/artifacts/persistent-java02/ordinary-business-freshness15s-operation60s01.json`。DevMain内部固定调用原Main的`resume`，不fresh。
- JVM512MiB、metaspace256MiB，java/JNA临时目录在`V/state/runtime-tmp01`；JNA使用manifest已有实际本地库配置。dev开始后它成为MB唯一输出authority，不能另起Maven同时热写。

DevMain v4已在S/Z（7122B，SHA`12aa89ce53ae82bb855ebf0f7d66c1bb4eb37de03bf390d900e2e4623560a40e`），正常reload用原stopPath请求原worker批间退出，等真实Main资源finally后释放FileLock；不interrupt Native，不STOP Game。失败4保持宿主，等待显式修改，不自动重放业务；原canonical票/UNKNOWN仍由生产Main检查。新Native连接必须得到真正新HELLO代次，不能复用旧transport/token。

已有D软件证据`O/quarkus-worker-dev01/HANDOFF-MULTIMODULE09.json`：实际v4原文、独立依赖模块三次真实编译/reload，同JVM新loader，旧业务先finally/释放OS锁、新批次再开始，失败4宿主保持且无自动retry。它**没有**执行真实Game的Native新HELLO、当前repair状态恢复、实际Quarkus业务批次，因此不是实机接续P。保存Java后HTTP触发扫描；单次HTTP200可能还是旧代，不能作为实际业务更新证明。

## 保留与未验证边界

Game仍活跃时，owner、实际Native部署、profile、当前continuity/events/artifacts、旧票及worker57失败原件都是活跃输入，不能因目录旧而清理。普通D测试/模型材料按共享存储策略48小时用途复核，不无限期保留全部派生副本；不要在此次收尾删除。

交接明确未完成：当前账本修复、DEFERRED suffix新回归、批限时分类回归、Main318、新Quarkus实机接续、首普通业务动作确认、真实新增游戏日与后继长跑。没有用编译、HTTP、ACK、loop存活替代这些结果。
