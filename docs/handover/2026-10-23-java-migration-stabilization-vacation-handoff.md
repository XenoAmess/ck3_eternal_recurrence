# Java 迁移稳定化休假交接（2026-10-23）

## 最新指令与停工边界

用户最新指令是“你要去度假了。温和地收尾手上的每件事，然后编写交接文档到 docs”。它覆盖此前 56 并发与自主领取后继的要求：不再开迁移项、补充测试批或 SDK/Game 运行；只收尾已实际启动的有限作业，保存候选和真实失败，交接后停止调度。

本文承接 [上次休假交接](2026-10-22-java-migration-stabilization-vacation-handoff.md) 和 [本轮增量](2026-10-23-java-migration-stabilization-resume-increment.md)。源码就绪、编译测试、消费者接管和实机业务结果分开记账；**迁移尚未全部完成，游戏没有新增日数**。

- `machine_id: xenoamess-full-tower-eb9d2c1186`；观察日期为北京时间 2026-10-23，证据时间使用 UTC。
- `R = Z:/ck3_mod_rewrite`；`J = D:/codex-ck3-demos/2026-10-22-java-phase1`。
- `C = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01`。
- 当前 Z 工作树原 HEAD 为 `4a999f3ef5aa6770345832ed6a3ed47602c3c4f4`，包含跨线程未提交成果。**不要 reset、clean、add 全树，或把它当 clean runtime。** 正常发布使用 `J/scratch/java-publish01` 的隔离 detached worktree；最终提交以本文件所在提交为准。
- 不得调用禁止的 Windows Shell，遵循 [AGENTS](../../AGENTS.md)。Maven 使用各机器命令行默认 `mvn`，最低 3.10.0；本机已有实际 3.10.0 回执，不把观察到的安装路径变成后续命令规范。

## 已验结果

| 工作包 | 实际结果与范围 | 主要证据（相对 J） |
| --- | --- | --- |
| tools24-03 | 19:02:31.3045204Z 完整 Maven PASS；13 suites、118 tests，0 failure/error/skip；Job0，峰值 968728576 B / 2 GiB；31 source 与 compiled source 均 MATCH，6 件完整运行依赖；19:04:24.4564982Z 新 reader accepted | `logs/build-java-tools24-03.json`；`logs/TOOLS24-ACCEPTED-READBACK01.json`；`logs/TOOLS24-QUALIFIED-PUBLICATION-DELIVERY01.json` |
| Java18 恢复闭包 | 七模块完整 verify/accepted；663 tests 全通过、零跳过；包含真实退出后复核、清理与库存上限回归。不是全 17/29 模块通过 | `logs/build-java18.json`；`logs/JAVA18-QUALIFIED-RUNTIME-CLOSURE01.json` |
| Java19 恢复闭包 | 19:29:48.3388838Z 七模块完整 PASS；52 suites、712 tests，零失败/错误/跳过；Maven/outer0、Job0、双source MATCH，227.1955026 s，峰1112326144 B / 2 GiB；19:30:14.9848603Z accepted | `logs/build-java19.json`；`logs/JAVA19-QUALIFIED-RUNTIME-CLOSURE01.json` |
| CI12 | 19:21:14.278964Z，30/30 命令 PASS；独立 SDK continuation、真实 WAL 诊断均到达；27 文件为 227 PASS + 93 subtests PASS，零跳过；source post MATCH、Job0；375.952 s，峰 1246560256 B / 1.5 GiB | `artifacts/coldwarm-ci12/TERMINAL-INDEX01.json`；`artifacts/coldwarm-ci12/actual.json` |
| SDK 静态补验 | 当前精确 11 定义严格检查 PASS；monthly 完整模块 Python 3.13 严格检查 PASS。完整 MCP 文件的 10 个运行测试已由 CI12 整组执行，含真实 MCP 参数拒绝和空参数正例 | `artifacts/coldwarm-sdk24-static02/TERMINAL-INDEX01.json`；`artifacts/ci-closeout-vacation01/CI-CLOSEOUT-FINAL01.json` |
| 原始样本 | finance 原 65 项已实际 PASS，86 向量及来源/token 独审；planning 合计 10 项捕获 PASS；events 最后 interaction 的 12 案例已通过并交原字节资源 | `logs/WAR-CASH-ORACLE-AUDIT06.json`；`scratch/planning-resume02/PLANNING-ACTUAL-RESUME03.json`；`scratch/events-finite-resume02/goldens06/INTERACTION-ADOPTION06.json` |

关键原件哈希：tools24 actual `bb6331832fd68e36574c7d8f68d0928ab068673bcac72e5a4818d526a0e5fdd6`（22528 B）；CI12 actual `2b095789c3867366e12f266d9fb2b9d3f118fa28b6df72388cb7b537680d04d3`（1402572 B）。工具主 JAR 为 456174 B / `614d20039246d97a4a8d93e3fa8c43be319d1e7f8879acc3d154fc615602cc6d`；运行必须消费完整 6 件闭包，不能挑出中间 class 混包。

Java19 在用户收尾指令前于19:24:19Z实际启动，session `23146`，收尾期间自然完成。它修正 canonical provenance 与 fresh transport repo 的混绑、显式 Python 导入路径，并加入有限 Preparation CLI；9项新增真实回归全通过。actual 为197759 B / `e749f06b6720da27259766b44b2c95c6d5d1e10bccefca02179c5ac346ff1e2b`；qualified closure 为80991 B / `28daa68c242651a7fd80e89374693bd9c23ea6564c45441ecf411eedf16b8b53`，包括131件deployment与CLI/RootSession实际类条目。7份Python05来源前后精确MATCH。它只授恢复七模块的软件资格，不授实测token或全29资格。

## 保留的 RED 与尚未验收部分

- Java17 完整批仍为 1984 = 1890 PASS + 44 FAIL + 50 ERROR，零跳过；16 个 child SUCCESS、唯一失败 child 为 `wave2-military`，另有 parent SUCCESS。注册 17/29 = 58.6%；该批 child 成功 16/29 = 55.2%，不是迁移业务完成率；1890/1984 = 95.3% 也不是实机通过率。
- 完整 34 文件补充回归实际为 41 parent：38 PASS、3 FAIL；另 6 subtests PASS、5 FAIL，零跳过，Job0/source MATCH。三处 DTO/compact MCP 测试边界夹具已由 CI 唯一 adopter 修正并读回，原业务断言保留；**修后完整 34 文件没有重跑**。
- 七个补充完整 fixture 静态检查当时均 RED（17/8/9/28/8/21/31 个错误）。随后三份夹具改变了来源，未再整模块静态检查。SDK 11 定义 PASS 只能证明其精确范围。
- 上个远端提交 `ccaea6d0d7f56e22843843d283c91a12808a0107` 的 Official CI `39824334365` 实际失败：step40 默认 Maven 扩展名解析拒绝，17:56:29.8504641Z 报 `unsupported default command extension order`；Linear history `39824334366` 成功。tools23/24 已修该共享路径并有真实回归；新提交远端结果不能由本地通过推定。
- finance readers02/三个 gift 原采集仍缺实际编译资格消费；V13 不接受 `.class`，V14 typed compiled-capture profile 未资格化。不能把原 65 项 PASS 当作这些读者/同宿主消费者已通过。

## Java29：真实部分源树，不是已迁移产品

物理目录是 `D:/codex-ck3-demos/2026-10-22-java29-final-source01`，虽然名称含 final，当前仍是未完成、未编译的源树。正式 Z parent 仍注册 17 children；候选 parent 有 29 children（30 个 reactor 项含 parent）。

第一次物化实际 75.06 s 后 RED，Job0：qualified patcher 拒绝无上下文纯插入。完整库存确认当时 1370 files、唯一成功 prefix361；首次实际失败是 planning RealmDifference，先前 Budget 归因只是静态猜测，不能沿用。已把 planning/finance/coalition 的既有补丁规范为非空上下文 n3，保全部 pre/post；另外按真实 `***` header 修正错误的补丁格式声明，没有放宽 patcher。

续行卡72在收尾指令前已实际启动，session `61091`；现已自然 RED：exit1、14.8963722 s、峰 241156096 B、Job0、stop=null。失败为 `military:0546 ProbeCompiledSupplyConsumers.java` 的 `Duplicate exact selected patch section`（同一 CODEX target 多节）。184 个后继 stage 已执行。闭场1451文件逐SHA已精确匹配唯一prefix545：17,682,691 logical B、1057 dirs、原生file allocation20,625,496 B加目录guard4,329,472 B，共24,954,968 B，errors/reparse0；旧1370/prefix361只是历史。

- 主要入口：`J/scratch/reactor-integration-resume02/`；原698-step plan、compact resume、原命令/失败与快照都保留。
- 续行命令证据：`J/scratch/reactor-integration-resume02/JAVA29-RESUME-ACTUAL01-COMMAND.json`。
- 停止继续修复/重跑；不修改已完成的 partial 树来伪造成功。
- 当前tools24的30个src引用只有10 MATCH，20缺失或不同；不能称当前树“只差六处”。Java19四源仍为旧2/缺2。原698步剩153步和33项extras均未完成；接手必须使用新pinned snapshot，不能直接重跑旧skip361。
- 没有 Java29 capture-only receipt、全29 verify、真实统一 HTTP/全部消费者资格；没有把跳过测试算作通过。`TEST_COMPILED_CAPTURE_ONLY` 只是已实现且经过工具回归的新模式，业务采集和默认 full verify 仍须实际执行。

## SDK 与真实恢复停在何处

- 旧 SDK Src32 是 1468 leaves。当前 R SDK inventory 是 1494 leaves；不能把它叫作 Source32，也不能改旧 43 epochs/8 delta/2 new anchor 使其看似兼容。
- phaseA 三份 Request01 选择旧1468、SDK code delta=0，只叠当前机械 transport/test/support；暂绑定 Java18 deployment。`J/scratch/remote-ci-graph02/phaseA24/PHASEA-REQUEST-INDEX01.json` 是其单一入口。
- `J/scratch/remote-ci-graph02/owned03/SdkSourceAssemblyOwnedMain.java` 已保存，25708 B / `def966077541d2178872fabd738e11e64347c4fca9107b21b3d4e2a3651f5b49`。它只是共享三API的机械 caller，未编译、未运行。Review/Assembly/实际三视图全部未产生；空目录和卡不能证明组装成功。
- Java19 Preparation 将两个不可变 canonical manifests 与 fresh transport repo 显式分开，原 SHA、prior 等式、88 来源守卫不变；CLI prepare/refresh/bind 均不能签票或交易。源入口 `J/scratch/closedadoption-root-session02/preparation/FRESH-REPO-CLI19-SOURCE-READY01.json`，12899 B / `70edba93bbca2d19f1b6f5314a30cd30a939264c5bd37e727fea798e5c9e3e32`。
- 真实 fresh refresh、note/roster、ticket、nonce、invocation、Review.Plan、Root approval、同 JVM measurement/cache、临时/生产 writer/cold 验收全部未执行。本轮未签发新的 Driver/SAVE 读取票；旧 unsigned 15:30Z proposal 已过期，绝不沿用。
- stat thin source4451 B和准备 JSON4220 B保存在 `J/scratch/clockreader-resume02/native-stat01/`，0 JVM、无 fresh stat。两路径不能放入通用 FileRef hash 列表；只有已放行原 SDK 可以做一次 Driver 读取与一次 SAVE hash。
- 团队曾有过宽 rg 搜索可能触及 Driver 正文，次数/字节未知；事故原件 `J/scratch/ci-resume03/consumer-prepared/WAL-SEARCH-INCIDENT01.json` 保留。**本域0不得外推整轮0，团队历史聚合仍 UNKNOWN。**

## 原生与 sharedwire 后继候选

原生仅两个已指定 target：`ck3_12003_prisoner_native_kinship_test` 与 `xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test`。二者 BUILD、Defender 精确登记、fixture 执行仍 NOTRUN，raw=0；没有 contact FIRST 三项目资格。

08 用完整 qualified24 工具编译/DTO roundtrip 实际通过；配置真实 RED，CMake root exit0 后唯一受管存活成员确认为 MSVC `vctip.exe`，不是 PDB/conhost 推断。清理前诊断 COMPLETE、IsInOwnedJob=true、wait258/exit259，最终 Job0，原 stop=`root_exited_with_live_children` 保留。闭场入口 `J/scratch/native-fixture-execution01/NATIVE-FIXTURE-CLOSEOUT01.json`（3703 B，`29dbc65d19483f6445d74ef31aa229e93706818e0ec271bdc358858bcc6d6304`）。

WJ25/Native09 只保存候选：旧3/4参仍默认5秒，新增 typed per-call policy 允许在原有限 command deadline 内真正等待 Job0，不杀/忽略助手，不改系统、不猜 telemetry 环境键。**候选120测试不是已验118；25/09未编译、未运行。**

sharedwire 原公共对象图无固定8/64MiB上限，旧小输入候选没有完整接管。新增 artifact input05/domain06/client05 仍 source-only；不增151 operation、不换服务，不借event角色授I/O。Owner V3/config/lease 的实际实现及资格仍缺；完整容量、循环/顺序语义、真实HTTP与全套消费者未跑，公共 producer 仍 UNMIGRATED，不准 Python 业务 fallback。候选指针：

- `J/scratch/projection-client-resume02/followup05/PROJECTION-CLIENT-ARTIFACT05-SOURCE-READY.json`。
- `J/scratch/military-sharedwire-candidate06/SHAREDWIRE06-SOURCE-STOP.json`。
- `J/scratch/host-assembly-resume02/` 中04冻结来源与05后继，最终闭场指针以实际文件为准。

已落的Host05指针为 `J/scratch/host-assembly-resume02/HOST-ARTIFACT-INPUT05-SOURCE-STOP.json`（7734 B / `25835a2c35ac994ae89d04e8549229e3bffc643be100b5e8ed8c9e3e8e5e8e01`）。11份Java源码/有序patch保全，Owner V3未实现。该candidate独立256KiB帽实际超57,720 B必须保留为真实超额；parent实际1,618,352 B仍小于2MiB，不追认旧candidate合规。client05只有AST等静态检查；domain06所有运行测试仍UNRUN。

## 游戏和现场事实

N46 已关闭；src32、H、N46 冻结图不热改。最新已观测 canonical 为 head240、`repair_required`、settled5189；SAVE11469为 settled5182/raw53279400；pending5190=`auto_unsettled`，AUTO11558结果未知，NEXT11559。未知10565/11386/11404同样不能重放或补记成功。head/event240 的精确观察是17:42:49Z历史，并非闭场新重验。

保存成绩仍 **5628/10950日，剩5322日**；本轮新增游戏日、普通周期及实机决策提升信用均0。不能套用旧“无pending”的 completed-unsaved-tail 路径。

Steam 后台 offline 正例为17:41:47.823525Z，仅证明该时该机；三个旧 CK3 对象已原生证明 signalled/not live，不能把 tasklist 行当当前活跃游戏，也不因此获得新Game启动权。新启动必须重新后台核机器、离线状态、实际EXE/版本/来源与账号占用，不抢焦点、不截图。证据 `J/logs/STEAM-GAME-PREFLIGHT-METADATA03.json`；无新Game启动/接管/结束操作。

## 资源与接手顺序

- 原D总池4GiB、source96MiB属于同一 scratch512MiB内部，Z32MiB；不是新增take。最近 source assigned94.75MiB/guard1.25MiB只作当时账，后续实际保全/闭场以storage最终ledger为准。
- 执行期限/复核线20:00Z不自动续；已有卡未启动均取消或HOLD，已用卡保真实终态，磁盘原件不冒充已释放。
- 闭场容量必须在 Java19 Job0 后再做一次：运行中第一次scan有JUnit目录删除竞态，不能称全0error。按 [通用存储策略](../storage-retention-policy.md) 与 [参数](../storage-retention-policy.json) 重新核用途、引用、期限与容量；不自动删除partial、冻结基线、唯一原件、失败或个人文件，也不永久无期限续存。
- 65个Agent节点不等于65并发执行；19:05:44–19:06:05Z实际为15 running children，49 completed。收尾后不以等待/新拆占位补到56。

接手时先读最终CI/构建/源树/storage闭场指针与本文件；核机器、Git与预算，再决定新工作包。先修34真实夹具回归和partial源图剩余严格补丁问题，补齐qualified24/19源码后做真实capture-only、原生产者采集、批量资源采用与默认全verify。SDK恢复另用新资源窗与fresh三视图/prepare，Root独立新票、同JVM一次measurement、实际结果/challenge审批和原锁内reducer重验；不得从本交接、成功JSON或编译成功直接授Game/账本权限。原生25/09与sharedwire05/06须各自完成实际资格后再采用。

## 最终闭场补注

- 已启动的最后两个有限作业均自然完成：Java19 PASS712；source29续行RED。19:30后确认本轮Maven/CI/native/capture/SDK均无活动Job，不再新dispatch。
- CI最终单一指针：`J/artifacts/ci-closeout-vacation01/CI-CLOSEOUT-FINAL01.json`，7064 B / `fa0092a09b8ce77bd92878355582cde8e4a5457151515357465fd2c24e177090`。
- source29最终指针：`J/scratch/reactor-integration-resume02/materialize29/JAVA29-HOLIDAY-HANDOFF01.json`，21868 B / `0e1131d53b05e67cc218220e4a13898434d110743844f5445b783d73926721b3`。没有完整typed SourceManifest。
- SDK待执行指针：`J/scratch/remote-ci-graph02/PHASEA-VACATION-CLOSEOUT01.json`，10729 B / `0ab7733e003c35ed19e9d1002ef47f52a283253e1a3e2352c4c8463bb571c605`。compile/Review/assembly/freshrefresh/ticket全部未执行。
- WJ25保存于 `J/scratch/windows-job-drain25-source01/WINDOWS-JOB-DRAIN25-SOURCE-HANDOFF01.json`，8138 B / `63d0cc80cf43bda430c7351aa94818752dd5b01843304c4a52699042931d4621`；5件含目录guard实际102400 B，候选120项从未运行。
- 恢复最终指针：`J/scratch/closedadoption-root-session02/CLOSED-ADOPTION-VACATION-FINAL01.json`，8119 B / `4d121a10789ead477483c1764ccce8dabec05e247fb5eb81fc42464c9381b077`；全部实际恢复操作引用仍为null。构建操作补充见 `J/logs/BUILD-VACATION-HANDOFF01.md`。
- 闭场容量原件：`J/logs/JAVA-PHASE1-VACATION-CAPACITY-CLOSEOUT81.json`，9184 B / `4f504d0fa28b6c565467335ad54ded687c7ea23c264e5eb50c4d8e63b585f89c`。19:32:55Z最终六part、wholeJ、六外根均0error/0reparse；J与外根合1,508,175,320 B，加64KiB闭场回执余量后4GiB帽余2,786,726,440 B；scratch含外源425,535,176 B＜512MiB。source96MiB assigned94.75/guard1.25是预算账，不能冒充原生全域source census。全部活动build session已清空，未使用RAM与后继输出预留已撤回，现有文件未删。
- 正常发布范围是已合格工具24、已完成CI12/SDK补验的机械适配与进度/休假文档；其余Z/D候选按上述精确引用保全，不表示全部接管或全部进入master。特别不要清掉Z未提交的恢复源码。
- 发布前fetch观察远端已到`036600913ea7d735ceed15fafa6d457ae0fa0892`，随后线性rebase。Maven解析冲突采用已验qualified24的原始两文件；其实现包含远端“只拒绝实际选中的不支持扩展名”修复及更严格的执行前后绑定，测试使用该已验闭包。rebase后29份工具Java逐字节匹配原qualified24来源，其他机器的日报段保留。远端并行改动与最终整合提交不由旧本地通过外推验收；Hosted CI以新提交实际结果为准。
