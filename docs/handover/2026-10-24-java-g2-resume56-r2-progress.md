# Java 全能力迁移与 G2：第二轮恢复进展

**休假停止：** 用户已要求收尾，本文以下为历史进展；当前停点、撤销许可与恢复顺序以 [R2 休假交接](2026-10-24-java-g2-resume56-r2-vacation-handoff.md)及其[精确索引](2026-10-24-java-g2-resume56-r2-vacation-source-index.json)为准，不按旧时间节点自动继续。

接续 [度假交接](2026-10-24-java-g2-resume56-vacation-handoff.md)及其[来源索引](2026-10-24-java-g2-resume56-vacation-source-index.json)。用户已明确恢复执行：完整迁移 Python 能力后用 Java 继续自动游玩，同时继续 G2 M0–M7 完整原生研究及落地。本文是进行中的记录，不是完成或实机通过声明。

`machine_id: xenoamess-full-tower-eb9d2c1186`。本轮工具验收事实截至 `2026-10-23T19:37:31.977667500Z`，后续财务复核至 `19:43:40Z`；标题日期为北京时间。`R=Z:/ck3_mod_rewrite`，`J=D:/codex-ck3-demos/2026-10-22-java-phase1`，`N24=J/scratch/resume-current-20261024`。容量、工具及执行事实只属于此机器。

## 并发与调度

恢复起点仅 Root；本轮实际创建了 56 个子智能体，Root 另计。完成第一批交付的线程继续承接明确缺块，没有为保持数字另开第 57 个子线程。协作目录的 running/已分配数量不等于持续有效开发数量；初期确有预算通知和共享 ABI 等待。

初次后台资源观察为 32 逻辑处理器、CPU 约 8.50%、物理可用约 27.31 GiB，出处 `N24/launcher_refresh/source01/RECEIPT01.json`。56 路源码/研究不等于 56 个 JVM。普通本地进程池仍建议 12 槽/6 GiB，Root 构建另计并受当前准入约束。

已确认并纠正的效率问题：新 source 卡已签发后，部分线程仍等逐条通知；现在按同一批量卡的本人精确 claim 直接执行，不再把额外 ACK 当成写入前提。来源图统一消费 `selected_files` 中的 `target_relative` 与精确 `source_ref`，避免为旧异构 map 维护多套猜测解析器。未改源码只引用，不复制正文。

Root 仍唯一执行 Maven、Game/注入和真实账本；`budget_fast_lane` 为唯一财务 issuer，`launcher_refresh` 为唯一 queue writer。43 组旧 operator profile、旧录制 adapter 等消费者已发现并隔离；没有以旧总线无新鲜任务推断系统无消费者，没有接管或改写其准入。

## 已实际执行的验证

本轮 Windows 原生 Python fresh machine 结果为上述 ID。默认命令行 `mvn -version` 实际返回 Maven 3.10.0、Maven home `C:/apache-maven`、Java 21.0.10；这只是机器/时间事实，执行仍调用默认 `mvn`。

C15 阶段 1 已由合格 C13 的 `SharedOwnedCommand` 真实执行：

- 终态：`J/build/resume-current-20261024/g2-m4/tools_c15/c15-helper01/terminal.json`。
- 外层退出 0；严格 `javac --release 21 -proc:none -Xlint:all -Werror` 子进程退出 0。
- Job `active_processes=0`，`stop_reason=null`；输入前验、输入后验、运行时后验均 `MATCH`。
- 实际 Job 峰值 234364928 B；输出计量 205112 B。

阶段 2 已真实物化 `D:/codex-ck3-demos/2026-10-24-sharedwire-tools151-source15`：151 Tools + 41 Host，192 个选源；外层和子进程退出均 0，Job active 0、stop null，三类校验均 MATCH。终态为 `J/build/resume-current-20261024/g2-m4/tools_c15/c15-assemble192-01/terminal.json`，Job 峰值 439443456 B。输出来源表 321752 B、SHA256 `44b0d2e6d7437d6bde9dd1fe9cb0d5b35b72278817355dc1cd5edcf61afbc113`。

完整 Maven 已实际执行，attempt `java-tools151-firstcut15-r2`，结果 RED：501 项测试，0 failure、3 error、0 skipped；Maven exit 1，223.443571 s，Job active 0、stop null、峰值 1247440896 B。两项 error 缺少实际 `XAR_REPO_ROOT` 环境绑定；第三项为 `NativeBridgeBuild` 生产 INTENT/ACTUAL 写读不支持 `Instant`。出处 `J/logs/build-java-tools151-firstcut15-r2.json`（91514 B，SHA256 `7be54161bae76d97cadb1911b89aea96bded35dfb7399eea6cd383afc6adf63a`）；来源前后检查 MATCH，完整部署为空。前两次更早尝试分别因未来不存在的 Source08 根及缺少 oracle 环境而拒绝，保留原件，不算测试通过。

C13 仍是已合格工具基准；C14、C15 RED 保留。Full35、SDK、Full8、Native、Game、SAVE 均未取得本轮通过。Bridge26 已将 INTENT/ACTUAL 的生产写读统一为已有严格 UTC codec，补三条回归源码；C16 正同步三项实际环境绑定和新显式 Full35 R2 有限规模合同，尚未执行。

上述是 C15 失败后的历史状态。**C16 现已实际取得完整工具软件资格**：

- 唯一物化树 `D:/codex-ck3-demos/2026-10-24-sharedwire-tools156-source16`，156 Tools + 41 Host，共 197 个选源。P2 outer/child/Job 均 0，三种来源校验 MATCH。物化来源表 338107 B，SHA256 `60c18d256efc488e263ce507cdb9141656bd24a94129502183e618a12e6f0848`。
- 全量 Maven `java-tools156-firstcut16`：517 tests、68 suites，failures/errors/skipped 全 0；outer 0、Maven 0，Job active 0、stop null，峰值 1148952576 B。Maven 受管耗时 242.998692 s，工具链探测 70.9986934 s；不是游戏效率指标。
- 真实 v5 build receipt `J/logs/build-java-tools156-firstcut16.json`，95392 B，SHA256 `10d69de937ef6cfb4ef7724f6c85df356e293f9ec490144d29041cabf0fb0554`。source/compiled-source 后验 MATCH，六件运行时齐全；主 JAR 1695742 B，SHA256 `e49756a134bf33cd2346ff3f79a722b91fcc2de50753032345c4708fee889e04`。
- P4 首次启动包重复指定 caller 管理的临时目录，在 child 启动前拒绝；保留 reader01 痕迹，不复用同 attempt。修正包 reader02 严格 javac 退出 0，真实三 classes 全匹配，未重跑已通过 Maven。
- P5 `c16-reader-run01` outer/child 0、Job active 0、stop null，pre/post/runtime 全 MATCH。own-reader 实际采用新六件归档，核 67 个主类同 archive，实际清除三个 oracle 环境变量，并正确拒绝两个历史 live lease。`actual.json` 6763 B，SHA256 `4bf7107fb4f0b12203c3f70106e090c56053b94c56bcd5a8a86e2958708be8a0`。
- 资格入口 `N24/bootstrap_integrated_tools/source18/QUALIFIED-DELIVERY16.json`，14577 B，SHA256 `43daa51094c5c819171754234931bf5cb34282ea32008995fc30ad0bda9ce690`；范围严格为工具软件，Host/SDK/Native/Game/SAVE 均未据此授予资格。

## 当前构建主链

C15 最终软件 cut 已收敛为 151 Tools + 41 Host，共 192 个来源文件；64 个 main 工具类。只合已确认的 Bridge25 守卫和 Full35 fixture/NativeIT 消费者修复，之后仅因实际编验失败再出后继。

冻结 C15 入口为 `N24/bootstrap_integrated_tools/source17/ROOT-SEQUENCE02.json`、`SOURCE151-REQUEST02.json`、`SELECTED-FILES02.json`。C16 使用独立后继，不修改此树；随后完整 Maven、新 archive 编译 own reader、实际读回逐步消费退出码、超时、Job 终态和来源后验。新 live 执行必须明确 `XAR_ORACLE_PYTHON`、`XAR_ORACLE_REPO`、`XAR_REPO_ROOT`；历史完成回执回放不得新依赖当前环境变量。

Reference 首次 fresh 采用 1511 叶/41 路由，补齐 Construction 真消费者所需的三个原测试；不先做已知不闭合的 1508 再重复生成。Source08 使用现成 typed request/plan producer，保留原 1524 基线、Plan16 91 层及 Source07 97 层真实祖先；新完整 35 项目仍须固定 winner 并实际物化、编验。

## 已落源码与必须闭合的真实缺口

第一批后继已实际落盘并陆续交给 `source_graph`，包括 writer/session、动作协调、自动循环、SAVE/restore、Driver/history、readiness、archive、效果观察、三种复合推进、普通领域及协议合同。它们大多仍是 `SOURCE_ONLY / NOT_COMPILED / NOT_RUN`；回归方法数量不计测试通过。

GameplayEntry 的真实启动、首份 Driver、4SEM、独立 root/pump、同 writer 提交和同 producer 晋升已交 13 个 Java 源，仍未编验。新一轮明确拆分真实空缺：origins 终态来源、Council 持久续行、自然继承原包生产者、restore 材料 reducer 与接管后采集、完整 PlanningInputsPort 工厂和 runtime 中央 installer。不能以旧 Game 的捕获对象复用为新/恢复会话已装配。M5 strengths 剩余 family/stage 按互斥来源组分派已完成的线程，不能把空 registry/descriptor 计为实现。

本轮确认并推进修复的跨模块问题包括：

- 原生 push 快照没有查询请求 ID，而旧 Java 强制要求；现采用共享 typed Query/Push 来源并同步持久化及消费者，禁止制造请求 ID。
- 普通 Applied 动作被错误归为 control-only，可能不置 dirty、不触发 SAVE；分类修在共享 receipt 路径。
- ACK 后异常、提交结果未知及恢复查询不确定性必须持久 UNKNOWN，不能重放或继续 cleanup。
- 同一 writer Session 的借锁入口、字段所有权、cycle 真实记录链、恢复材料及 native 原包证据必须共同验证。
- 实际 outbound ACK 原包应归档；重复提交许可分支不能重编码一份请求冒充已发送原件。

仍有大量真实能力缺块。已复用线程承接 GameplayEntry、WarCore early factories、Siege daily、实际战斗模型、control/terminal 严格合同与外部叶、军队完整路由及 strengths producer、普通交互 once-claim、能力缓存生产者等。缺代码或缺真实来源继续明确 RED/UNKNOWN，不以接口、descriptor 或局部测试代完整迁移。

## G2 研究边界

M0–M7 均有专责线程继续追候选来源、索引/缓存、过滤评分、重算、真正 caller 及执行后态，并把结果落入 Java。新增静态调用链不是实机通过。M4 已确认 `0x310DB20` 是 mutation，不能作只读退款 quote；M6 CALL/counter 不授最终收益或终态；M5 战斗消失不授胜利；M7 日期或截止不授动作资格。

当前安装 .4 来源逐 EXE/脚本绑定，仓库旧 1.19 只作历史参考。安装脚本中 `pam_sf` 修改来源未明，不能因 EXE SHA 相符将整树称为 stock。研究新旧版本、事实和未知边分别保留。

## 有限预算与资产

新源窗口：`J/logs/RESUME56R2-SOURCE208-WINDOW14.json`，再消费其 supplement/reallocation。第二批精确源根：`RESUME56R2-SOURCE-WAVE2-BATCH01.json`。

为解除反复等待小额叶帽、并容纳唯一 Source08/构建/Reference/SDK 链，Root 已授权新有限窗口增加最多 512 MiB，旧 4 GiB 卡不改写。权威 `RESUME56R2-CAPACITY216-PLUS512-WINDOW14.json`：新上限 4831838208 B，保守 actual+全部 future 4822205256 B；新增额为未来预留，不是实际写入或物理释放。全工作包实占未知仍为 null。窗口复核 `2026-10-23T23:30:00Z`；不授 Game、注入、UAC、Steam 切换或真实 ledger/SAVE。

必要候选与原件按统一存储策略复核至 `2026-10-30T16:30:00Z`，不自动续期、不授权到点删除。本文作为 record 于 2027-04-22 复核。没有清理其他机器、改变 Steam 模式或修改系统权限。

后续已签发按 owner 分支累计的 SOURCE3 与 SOURCE4 卡，56 位 owner 已实际逐一获通知；fresh child 共用本人联合硬帽，不再逐几 KiB 等额外 ACK。旧冻结正文不改，继承未改源只列精确引用。发现的少量预算预测超支保留原观测并前瞻更正，不追认旧峰合规。

原生冷构调查确认四棵旧 cache 合计实际计费 90907232 B，却没有可复用业务对象或 EXE。原 Person10 目标闭包包含约 750 个对象，合 Context/M4/M3 拟单目录至少约 761 个对象；这些是旧图结构计数，新冻结图仍须重算，不能当实际新占用或资格。原生源基线实际为 `R/ck3_autonomous_player/native_bridge`，其中旧生成树/二进制不得随 source inventory 重复复制。

为容纳这一已证实的冷构需求及后续 Full35，Root 批准独立有限 +2 GiB，issuer 已 fresh 复核并签 `J/logs/RESUME56R2-CAPACITY60-PLUS2G-WINDOW15.json`（13534 B，SHA256 `c9502ea8a15e8553389771df7df2271b05f44bca79d3ebbc5fe9342b8447d344`）。新 D 工作包上限 6979321856 B，保守 actual+全部 future 6969688904 B；未知全包实占仍为 null。Native 1536 MiB 仅财务预留，须先统一冻结全部源码、实际 ENV、目标和操作准入才构建。新来源 16 MiB 的分支增额不是实际支出；Z 仍仅既有 32 MiB，有限 quota 4.02 TB 例外同至 `2026-10-23T23:30Z` 复核。旧卡不改，无新增 Game、注入、Steam、UAC 或真实账本操作。

## 2026-10-23T20:31Z 实际执行补记

机器仍为 `xenoamess-full-tower-eb9d2c1186`。Root 用 Windows Python313 与仓库 venv 双入口重新运行 `tools/ck3_live_run_id.py machine`，均同此 ID；另一线程经 Cygwin Python 得到的不同 ID 是 POSIX fallback，不能作为 Windows 执行机器身份或静默别名。

Full35 独立编译辅助入口已实际严格编译，`full35-compiler-helper02/terminal.json` 为 PASS（17570 B，SHA256 `1c216fc5e23cdf2d578115883b6495d73ea57bd630f413a09179fa2f20ccbacc`），child 0、Job 0、三个来源后验 MATCH，实际产生 9 个 class。这仅资格化辅助入口，不计 Full35 已编译或已测试。此前启动前拒绝分别是 outer 缺少显式 JNA 临时目录、资源卡 outer 384 MiB 与生产要求 256 MiB 不符；均未启动子任务，旧记录保留。

Source08 Input02 经真实 C16 生产者生成请求后，PlanProducer 实际 RED：父 POM 与请求最后三个模块顺序不一致。Input03 仅修顺序，保持全部 77 owner 层、97 祖先层、326 个显式 winner，最终 3587 文件、48228782 B logical、62005248 B 文件分配规划。Input03 请求生产已实际 PASS，`source08-request03/SOURCE08-ASSEMBLY-REQUEST03.json` 为 1154842 B，SHA256 `08873978c6a9cf67fa6280971b37acba6b34627944e969a9a0d992651491d015`；当时尚无合格 Plan、未物化、未执行 Full35 编译。

另发现 C16 Materializer.Card 的预算白名单遗漏 R2 80 MiB，实际合法输入不能通过。修复在独立生产后继及持久回归中完成源码，不改冻结 C16；Root 仍需严格编译、执行实际 admit 边界及物化。所有后续源交付留下一 cut，不热改已执行输入。

**完整 Python 能力迁移尚未完成；Java 完整自动游玩新增保存日仍为 0。** 新 Java 运行须完成整图和完整 cold/warm CI（含独立 SDK continuation）、同宿主 Full8、当前来源与后台 fresh Steam offline，再验合法动作真实后态、实际推进、成对 SAVE 和恢复续行。1066 罗贝尔新开局成绩不得继承旧演示或研究 fixture。

## 2026-10-23T21:40Z 执行与进度补记

machine_id: `xenoamess-full-tower-eb9d2c1186`。以下时间为 UTC；用户检查节点使用北京时间。

C16 工具包已完整实际通过：197 个来源、517 tests / 68 suites，0 failure、0 error、0 skip；构建回执 `J/logs/build-java-tools156-firstcut16.json` 为 95392 B，SHA256 `10d69de937ef6cfb4ef7724f6c85df356e293f9ec490144d29041cabf0fb0554`。新包自身 archive reader 实际验证通过。它不授予 Host、完整 SDK 或 Game 资格。

Source08 Plan03、Materializer 80 MiB 边界实际回归及唯一物化均已通过。物化 3587 文件，48228782 B logical；文件实际分配加目录 guard 为 61640600 B，连元数据为 62680984 B。实际回执 `J/artifacts/fullg2-source08-materialization01/SOURCE-GRAPH-ACTUAL01.json` 为 2400 B，SHA256 `96f9c73c43f95ec12ca17aeb32c7824e638670ee584c8ea000aac94e1849a8cf`。不能把物化通过当成编译或功能完成。

第一次完整 35 项目 test-compile 实际 RED：17 success、4 failure、14 skipped；仅该编译切面的通过率为 48.6%。四组实际问题是 governance 对 planning-runtime 缺依赖、wave2-runtime 引用了上层 local-service、wave2-military 已弃用 Jackson API 被 Werror 拒绝、events 重复局部变量。修复与迁层已交独立后继，尚未第二轮编译。原始日志为 GB18030；旧 helper 将其按 UTF-8 读取失败，typed reactor summary 为空，17/4/14 来自对原日志的检查。编译回执 `J/logs/build-full35-earlycompile01-compile-only.json` 为 2181508 B，SHA256 `c66a249fbd121ff96d053c4658a01c57ce58ebabeea1571649b72baedf26f897`。

原 Maven 日志报告 57.765 秒，但外层命令实耗 942.0798408 秒；全树约 205762 个文件/目录的重复元数据扫描是已定位开销，不能把 Maven 时间当完整批耗时。WJP 已退出子进程的扫描顺序、SharedOwned 完成截止校验和 helper 首次扫描等生产修复已落 C17 候选，必须整包重新 Maven、封包和 own-archive 验收，不松绑冻结 C16。raw-summary03 实际负例回归 RED（负例改错 Build Order 同名行而非 Reactor Summary），新 harness 将修真实输入定位，不能将其报为通过。

Native32 已冻结为 5511 文件和单一并发 4 构建图；尚未实际配置/编译。sourcecut03 首次因 JNA 临时目录超出私有容量合同失败；fresh r2 修复后，实际在复制前因 CMake composition 缺必填 nullable 字段 append_utf8 失败。两次 child 均退出 1、Job 0，保留原终态；Reference 负责修生产请求，严格解码不放宽。当前原生夹具通过数仍为 0。

第二轮 Source04 收集真实后继时，发现 81 项迁层中 15 项来自原 1524 baseline；现 Plan 没有最终视图退役合同，简单加新路径会保留旧类。SourceGraph 唯一负责版本化 relocation 合同，保留原来源作为祖先并精确证明旧路径到新路径，不删 baseline 或靠别名绕过。该合同与完整编译仍未验收。

北京时间 05:20 的并发截面为 30/56 active，26 已完成当时子任务；随后已复用闲置线程承担真实战争工厂、公共事件、回滚资格、窗口 Recon、Family 原生字段及 M1–M7 后续研究。56 是有效并发目标，不是始终有 56 项独立可写工作或 56 项已通过验收。八个 M 都有研究/Java 增量，完整验收仍为 0/8。

用户进度节点：北京时间 06:00 检查修复与并发，07:00 检查第二轮编译和 Native32 首轮实际结果，09:00 检查完整 CI/SDK 接管余项并更新实机计划。它们是检查节点，不是全部迁移完成承诺；当前不能可靠给出完全迁移、Full8 全部研究及真实游玩完成时间。Java 新增保存游戏日仍为 0。
