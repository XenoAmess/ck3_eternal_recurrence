# Java / G2 resume63 休假交接（2026-10-29）

machine_id: xenoamess-full-tower-eb9d2c1186  
交接原因：用户最新明确“你要去度假了。温和地收尾手上的工作，梳理交接文档到docs中。”本轮停止新增执行和并发补位，保存在途结果与现场；这不是项目目标已完成。  
本文件为接手总入口；较早的 [resume62 交接](2026-10-26-java-g2-resume62-rea-runtime-handoff.md)及其 source-index 保留历史，不能据旧资格、旧进程或旧失败覆盖本次状态。

## 接手先知道的事实

**原版 CK3 已进入 1066 罗贝尔地图，但尚无确认的业务动作，新增游戏日仍为 0。** 不要把“进程进入地图”、Java 编译通过、READ 成功或软件测试通过写成自动游玩完成。Python 能力尚未全部迁完，G2 八 M 的完整原生研究与实机验收也尚未完成。

2026-10-29 14:12–14:14Z 运行岗最后只读观察：

- 同一 Game PID 171676，creation_filetime 134376899432680684，独立 supervisor PID 147108；实际现场末态以运行岗交接为准，接手时只需读回该进程是否仍存活，不必重做历史全树资格。
- Java Main317 于 13:35:29.213Z 编译成功；worker57 随后接续同 Game，13:58:41.917Z **真实 exit4**。最后批次20不是干净停止。
- Main318、dev58、新 worker 均未启动；317之后又有共享源码采用，不能假定最新源码已在 Main317 产物中。
- 实际账本出现 repair_required / seq71 / BATCH_INTERRUPTED20；seq57→71 后缀含 DEFERRED。即使 attempted/applied 为 0，也不能把整个后缀当作无业务变化、直接清零或造 clean ticket。
- Game 不随 worker 退出而关闭；收尾不发新 START、SAVE、RESTORE，不部署 Native DLL，不重启 CK3。
- Runtime63 在收尾前是唯一生产 Maven/dev/worker 操作岗；接手必须重新明确一个执行 owner，避免 Root、dev 与 plain worker 同时写共享构建或同一账本。

## 分项交接

| 文档 | 接手用途 |
| --- | --- |
| [实机现场与接续](2026-10-29-java-g2-resume63-runtime-handoff.md) | 当前 PID、owner、worker57、账本、stop marker、ticket、可复用命令与实际失败 |
| [Root 组收尾](2026-10-29-java-g2-root-group-close.md) | 宿主、事件、生命周期、SDK/CI、Quarkus、Native 与共享集成的完成/未完成边界 |
| [迁移组收尾](2026-10-29-java-g2-migration-group-close.md) | 20 个业务域、S/Z 已采用与 D 候选、真实回归与仍缺的能力 |
| [REA M0–M7 收尾](2026-10-29-java-g2-rea-m0-m7-close.md) | 八 M 逐项原生结论、Java 落地、尚缺字节/同帧输入/实机后态 |
| [本次 source-index](2026-10-29-java-g2-resume63-vacation-handoff-source-index.json) | 精确原件导航、交接时状态与读取结果；不是新的启动门禁 |
| [长期执行记录](../autonomous-agent-progress/2026-10-26-java-g2-resume63-current.md) | 本轮失败与修复的时间线，包含 Root 调度失误及后续更正 |
| [本地模型配置](../local-model-executor-config.json) / [能力经验](../local-model-capability-boundary-2026-10-28.md) | 不丢失 8080 新地址、提示布局、重试边界和真实试用结果 |
| [REA 研究入口](../rea-ck3-research/README.md) | 框架方法、后端实测、专题与原件导航 |

四份分项文档均已落盘。Root 最后核对本页相对链接与 source-index 的实际可读性；这是交接文档检查，不作为未来启动门禁。

## 第一优先：恢复同一局并产生真实进度

原目标仍是：完全迁移 Python 版能力后，使用 Java + Maven + Quarkus 继续完整普通规划器自动游玩 1066 罗贝尔；研究同步落到生产 Java。用户反复要求优先实机。接手不要先扩一轮论文、来源资格、全图审计或并发状态报表。

建议顺序：

1. 读取运行岗交接，确认当前 Game/owner 与真实账本尾。解决 seq71 的实际恢复路径，保留 DEFERRED、UNKNOWN、所有已记录状态；不重放未知动作，不手工改 canonical JSON 或追认旧 clean ticket。Persistence 准备件在 dirty-current-recovery01/PREPARED-ACTUAL03.json，**两处恢复消费者未修改、模型请求未发、新回归未跑**。
2. 审阅实际超时及其候选根因。最后批次约 322.475 秒超过本批 300 秒，真实末报 Council/Crown 回调中的 runtime context deadline expired / INCOMPLETE_MIGRATION。源码分析支持“planner 返回后缺少及时 requireTime、后续回调才发现过期”的候选解释，尚无回归确认。**“RootRuntimeContext 保存了 startup deadline 导致长期寿命过期”这一早先推断已撤回**；它检查的是调用方本批 deadline。SessionController 候选只在 D，首次 javac 因将 -J-Xmx256m 放入参数文件而 exit2，未进入有效编译/测试，不能当成修复完成。
3. Events 已在共享 S 采用九叶原始 Unavailable reason 传播，隔离 javac0、EventPolicies12P、PendingCollector2P；这九叶未进 Main317。保留真实 Wait 与拒绝语义，下一次实际同 Game READ 才能看见更深原因，**仍未证明事件门已实机闭合**。
4. 与其他已 STOP 源码做最小集成，复用 S、MB、m2，只增编修改模块与必要依赖，安排下一次 Main318。不要复制新全图，不用背景全绿或模型响应作为主线启动前置。
5. 用既有 owner + 普通业务配置做 resume；仅重启智能体。取得一轮真实普通动作的原生后态及新增游戏日，连续长跑并监测新失败。未覆盖事件按实际显示第一项通过原生通道继续，批后离线补共享规则，不逐个研究后重启游戏。
6. Quarkus dev 使用下文已测入口接替 plain worker，实际连接与新 HELLO/同账本接续尚需验证；如果 dev 仍有宿主问题，plain worker 是当前 Java 生产路径，不回退 Python、不阻塞游戏进度。两者必须互斥。

最后一次 finance 规划已真实 KEPT，原因是 imported pending bodies 明确 clear；当前没有理由为同一历史 producer 门再次重做 source audit。清理 dirty-stop 路径也不以先 SAVE 为前提。运行岗14:04在收尾指令前已归档退出4和原stop请求，只核对token后删除自己的请求；14:12/14:14 stopPath实际ABSENT，未修改ledger或旧票。

## 目录、源码与产物：不要混淆

| 名称 | 当前机器实际路径 | 状态 |
| --- | --- | --- |
| 仓库 Z | Z:/ck3_mod_rewrite | 规范源码及 docs；大量未提交改动和未跟踪文件 |
| S | D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control | 复用的开发源码，主线实际从这里编译；并非冻结 SDK |
| MB | D:/codex-ck3-demos/2026-10-22-java-phase1/build/complete35-candidate31-h5r5 | 当前 Maven 增量输出；Main317 后未重编 |
| m2 | D:/codex-ck3-demos/2026-10-22-java-phase1/m2 | 已有合法 Maven 缓存 |
| 构建临时根 | D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/complete35-candidate31-h5r5-tmp | 复用；不转 C 盘 |
| V | D:/ck3-state/ck3-java-g2-resume63-vanilla01 | 现存原版场次，唯一活跃 Game/Driver/WAL 输入 |
| O | D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration | 主构建、模型调用、各专项实际回执 |
| REA | D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01 | REA 原始片段、工具与 cases |

重要现场路径：
- V/state/game-supervisor02/owner.json
- V/artifacts/persistent-java02/worker-resume57/{started.json,stdout.log,stderr.log,terminal.json}
- V/state/worker-stop.request（Runtime 自有停止标记；是否仍存在以现场交接为准）
- V/state/worker-restart-ticket.json（旧票 mtime 仍 11:15Z，不能当作57的新票）
- O/CURRENT-MAVEN-STATUS.json（当前构建状态；不能沿用旧消息的“冻结中”）
- O/MAINDEV317-COMPILE-ACTUAL.json（真实命令、退出码、10个实际 javac 模块）
- O/quarkus-worker-dev01/PRODUCTION-DEV-INVOCATION03.json（实际 dev 参数模板）
- O/LOCAL-MODEL-CALLS.jsonl（本地模型 start/end 和原始输出导航）

S/Z 当前并非所有文件完全一致，也不是所有 D 候选均采用；以组交接的精确叶和回执为准。不要整树覆盖、重放旧 after-image 或覆盖个人 application.properties。Git HEAD 在交接观察时为 4a999f3ef5aa6770345832ed6a3ed47602c3c4f4；master 相对本地 origin/master 显示 ahead2/behind390，**不是刚做远端查询**。未 commit/push/fetch/merge。14:10:57Z 的 porcelain 观察为111个跟踪变化、881个 untracked 条目（目录可合为一个条目，不等于文件数）；其中包含历史工作和早期误转义产生的可疑名字，未为收尾自动清理。

Delivery 最终已同步37个规范文件、40次采用；**另17叶未启动复制并已取消：Mercenary7、PublicSemantic TEST1、Events read-reason9。** 这些叶在S已采用，Z仍旧像，新Mercenary test在Z不存在，未在收尾强行补齐。精确状态见 delivery-canonical-integration01/working-diff01.json。

## 最近构建与修复覆盖

Main317：13:33:21.367Z → 13:35:29.213Z，exit0，127.846s，默认 mvn、-T2、离线缓存、-pl local-service -am compile；本次不执行测试。实际 javac 为 wave2-governance36、wave3-governance61、wave2-planning54、wave3-planning38、wave3-development26、g2-research130、application754、adapters-storage9、native-transport446、local-service624；其余 reactor 模块复用缓存。**这是增编，不是最后一次完整编译验收，也不是实机完成。**

近期实际工具链为默认 Maven3.10.0、既有 C:/jdk-21、Quarkus3.40.1.1。Maven 继续使用命令行默认 mvn；这里记录机器事实，不把安装绝对路径变成执行规范，也不为收尾再次升级或改全局 PATH。

下列是已落共享生产的关键方向，详细叶以分项文档为准：
- 删除普通启动与规划中的历史来源/全树/重复资格审计；实际命令超时、必要解码、单 writer 和 UNKNOWN 不重放保留。
- 普通原版 SuccessionLifecycleBinding 显式配置；不假装有旧模组 ENV，不把 xar_off 当无 mod。
- 同 Game clean restart 采用真实 Controller/full Driver/KnownFacts；对象字段顺序差异用严格类型化 JSON 语义比较；不得重造 day0。
- PlanningReadScope 在本轮同 lease 内复用实际 Captured，finally 清除，避免规划读取自己制造帧漂移。
- Finance 共享 borrowedSession 接齐，历史 producer audit 不再阻塞当前合法 payload；保实际内容与合同。
- Event installer 使用实际持有轮次 lease 描述，九叶 reason 传播为317后继源码。
- Continuity/archive 的重复昂贵检查有局部削减，真实 writer、提交顺序与 UNKNOWN 保留。

317以后仍有已采用但未主编叶，例如 read-reason、dirty restart evidence_id、dirty-stop loop、readiness packet、mercenary UNKNOWN、业务域修复等。**不要根据“SOURCE STOP”推断 MB 已更新。** 对仅保留在 D 的 SessionController deadline、恢复消费者、部分外交/生活/研究候选，必须先读当前源码后最小合并，不能直接整份覆盖。

可复用增编形状（路径展开见上表，执行时沿用默认 mvn，不锁绝对 Maven home）：

~~~cmd
mvn --offline --fail-at-end -B -ntp -e -f S/pom.xml -Dmaven.repo.local=M2 -Dck3.build.root=MB -Djava.io.tmpdir=TMP -Dmaven.compiler.useIncrementalCompilation=true -Dmaven.compiler.showCompilationChanges=true -DskipTests=true -Dmaven.test.skip=true -T2 -pl local-service -am compile
~~~

这里 S/M2/MB/TMP 是上表的说明用占位符，不能直接照抄；精确 argv 在 MAINDEV317-COMPILE-ACTUAL.json。修改编译问题时复用同目录迭代，能跑后再做一次最终完整验收。

## Quarkus dev 的真实边界

用户明确要求评估自动热编译/重载。当前源码 RootOrdinaryWorkerDevMain v4 已走同一普通 worker 生产委托；多模块隔离测试同一 JVM、四个 classloader A→B→C→D，三次真实编译/重载约2.260/1.078/1.203秒，旧资源关闭先于新业务，实际 OS FileLock 没有重叠；return4 保 host 存活且不自动重试，显式下一编辑后才继续。**该软件结果没有连接当前 Game，不是实机热重载通过。**

实际调用使用 io.quarkus.platform:quarkus-maven-plugin:3.40.1.1:dev，ordinary-worker-dev、xar.worker.dev.enabled=true、127.0.0.1:8089、noDeps=false、effective-model-builder=false、instrumentation=false；不要设置 maven.top-level-basedir。使用真实 m2 辅助 test-JAR，不伪造依赖。旧 POM -Xmaxerrs 1000 的 Set 参数次序问题已移除。启动命令、JNA/D 盘 TMP 与内存参数在 O/quarkus-worker-dev01/PRODUCTION-DEV-INVOCATION03.json，接手仍需核对当前文件而不是重跑旧输出目录。

## 本地模型：配置保留，排队已经暂停

- 当前唯一地址 **http://192.168.1.7:8080/v1**，模型 **qwen38-coder**，无需 key；客户端必填用 local。8000 是同一服务迁移前地址，不回退。
- 固定 system 模板；当前稳定源码在前、变化任务和诊断在后。temp0、enable_thinking=false，Chat Completions。对模型候选实际编测、语义复核，HTTP200 不算完成。
- 实际有多文件合同传播、方法修复和负例生成成功，也有 API 幻觉、截断、误读分支和伪通过；owner 手工纠正与模型采用分开记录，详见统一经验文档。一次失败不是能力上限。
- 服务暂错通常按配置最多6次、10/20/40/60/60秒加抖动；400先修请求。**重试只用于模型 HTTP，绝不重放游戏动作。**
- 收尾前曾发生客户端超时后服务端仍排队、独立重试累计31 running/10 waiting/KV约64%的过载。随后已全局 HOLD 新 POST 和下一次 retry；当前队列是否已排空未知，收尾不为此重启远端服务。
- 接手有真实任务时先由单一 coordinator 看实际服务队列，再小批发请求；不要用“客户端日志无在途”推断服务端空闲，不让60岗独立六轮重试。持续高倾向使用的用户要求仍在，但本轮暂停期间不继续派发。

## REA 与八 M

使用 REA 框架先读 methodology、真实工具结果和专题；不要把后端包装、反汇编条数或部分 CFG 当作完整机制。八 M 仍需逐项闭到现有 Java 消费者及真实游戏后态。

- M0：v1/v2终战合同已有回归与兼容；新发现 backend_id 可能与原生 ACK 不一致，只是未验证候选，首 javac 参数错误，业务测试未跑。
- M1：县风险告警优先于 count0，installed faction read 提前查询已有软件回归；当前帧真实风险与完整候选仍缺。
- M2：Locator/Notice/711 witness 等原生软件边界推进；最新真实 Notice factory 离线5阶段全通过，完整 Native Envelope 尚未由真实 Java Transport 消费，更未部署当前 Game。不要换 DLL 只为“把研究算进去”。
- M3：正式 producer golden 已接资源，原四 Python whole24P、Java三whole133P；最新另一候选基线14例为8P、2F、4E，候选未编，不能混为全绿。自然继承/实际 successor 仍缺。
- M4：正成本钱包扣减与模式槽路径已证，最终净退款未知；Java仍空报价/credit0。
- M5：新增112B闭合正常路径 R10 与容量增长边界；对象别名、当前帧、战争实机资格未知。
- M6：有限 predicate/RF 已补，后继162B未采；loaded bank与四域完整性未闭，Java无已证新增修点。
- M7：443B/107指令已解，局部无 owner+318 安装；state3不等于成功，SAVE callback及真实保存恢复仍缺。文件摘要检查仅静态风险，未构成已复现 Game 缺陷。

精确原始片段与下一最小输入由 [REA 分项交接](2026-10-29-java-g2-rea-m0-m7-close.md)保存。不得重新全 PE 导入或让八岗各自提取同一大块，已有原件先复用。

## 验证与尚未通过项

- 原 SDK CI30 有真实30命令/30退出检查，18测试组513P，12静态检查通过；不等于本轮所有 Java/Native/实机资格通过。
- 软件 Quarkus 多模块重载证明、dirty restart 5P、部分合同 producer→consumer 闭环已跑；各自覆盖范围见组交接。
- Archive whole19 后继仍18P1F（readiness时间），并非整类全绿；public tools 原件缺失为 NOT_RUN；MCP8余SAVE未跑，排队在收尾时取消。
- 最终整图编译、对应完整官方 CI step、真正 Game 动作/日期推进、同 Game dev 热重载、新真实事件/终战/继承/保存恢复均有未完成项。
- 不为收尾追加全量构建或重跑已绿组，既有失败原样保留。

## 资源与关闭边界

本次只写小型交接，不清理现有 runtime、候选、个人资产或旧证据。按通用存储策略在 14:10:57Z 读取卷容量：D 可用624422957056B（总14000483987456B），C 可用171490455552B，Z 可用137813942272B；这是本机当时观察，不是跨机预算证明。普通开发共享2GiB pool 原回执在 resume63/capacity/ORDINARY-D-DEVELOPMENT-SHARED-POOL01.json，原48小时复核在10月31日，不能因休假自动续期。未做全目录物理占用普查，不声称全机回收器部署。

当前 Game、V 的 Driver/WAL/owner、复用 S/MB/m2、活动候选和未解决故障关键原件仍是接手输入；建议10月31日复核用途和容量，不自动删除或无限延长。不要把 D 空间充裕变成 C 盘大输出授权。

## 调度经验必须保留

Root 曾把离线修复/测试当成过重前置，又被并发汇报牵走注意力；worker56已退出而19分钟后才读终态，是主线值守失误，不是缺用户授权或额外安全顾虑。后续把生产运行交给独立 sole owner，背景迁移/REA由 coordinator 汇总，主线失败先处理；不要让 Root 单点接收每叶 ACK、slot 请求或模型响应后才推进。

60曾为用户明确要求，收尾前也确有掉到22/24再补位，不能虚报始终60。**本次最新用户收尾指令已停止自动补位、派发和长跑；不要因为旧 AGENTS/日志写“维持60”就在交接结束后自动启动任务。** 下次明确续行时再恢复真实工作分派；保留单一生产 owner、资源并发与智能体人数分开。

用户未要求 commit/push、强停 Game、发布或继续修 bug，本次均未据交接扩展执行。最终收尾时刻与后台进程详情以运行岗交接及本次 source-index 为准。

