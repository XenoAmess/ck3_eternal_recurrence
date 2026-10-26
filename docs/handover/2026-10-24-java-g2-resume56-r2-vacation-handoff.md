# Java 迁移与 G2：R2 休假交接（2026-10-24）

用户最新指令：**“你计划去度假了，收尾手上的每个任务。写交接文档到docs。”** 本文取代本轮继续开发与时间节点安排。停止新增开发、构建、原生配置、游戏启动和执行许可；已完成成果保留，未完成工作按源码交付或中断草稿交接，不能写成迁移完成。

机器：`xenoamess-full-tower-eb9d2c1186`。本次收尾从 `2026-10-23T21:49Z` 左右开始，UTC；文档日期为北京时间。机器专属事实不能外推其他机器。

先读本文，再读[本轮进展与历史执行补记](2026-10-24-java-g2-resume56-r2-progress.md)和[本次精确索引](2026-10-24-java-g2-resume56-r2-vacation-source-index.json)。更早的[resume56 交接](2026-10-24-java-g2-resume56-vacation-handoff.md)与其索引保留历史，不用旧 C13 状态覆盖本次 C16 的真实通过，也不用旧许可恢复执行。

路径缩写仅用于这台机器：

- `R = Z:/ck3_mod_rewrite`
- `J = D:/codex-ck3-demos/2026-10-22-java-phase1`
- `N24 = J/scratch/resume-current-20261024`
- `N23 = J/scratch/resume-current-20261023`
- `P = N24/revisions/budget_fast_lane/full35runtime01`

## 收尾结论

**完整 Python 能力迁移尚未完成；Java 完整自动游玩新增保存游戏日为 0。G2 八个 M 均有研究和 Java 增量，完整验收仍为 0/8。** 不给没有可靠分母的全项目完成百分比。

| 范围 | 实际终态 | 准确边界 |
| --- | --- | --- |
| C16 工具包 | PASS，517 tests / 68 suites，0 fail/error/skip | 197 来源；含整包构建、部署后验及 own-archive reader，不是 Host/SDK/Game 通过 |
| Source08/03 | PASS，3587/3587 文件物化 | 物化和来源合同通过，不是功能迁移完成 |
| 第一次 Full35 test-compile | RED，17 success、4 failure、14 skipped | 48.6% 仅此编译切面；JUnit 未运行 |
| Native32 | 源物化两次 RED；配置/编译/夹具未运行 | Request04 修复已封，r3 未执行且已被 STOP 撤销 |
| C17 | 207 来源、request/selection 已准备 | 未物化、未 Maven、未封合格包；不能替代 C16 |
| Reference1511/41、完整 cold/warm、SDK continuation | NOT_RUN | 测试方法数量和来源 SHA 相符均不计通过 |
| Java 实际游玩 | NOT_RUN，0 保存日 | 没有 Game、注入、真实账本/SAVE、Steam 模式变更 |

休假前最后一次完整团队截面为 43/56 子任务 running、13 个已完成当时源码交付，约 77% 活跃；这不是有效产出或迁移百分比。用户中断后，旧团队不再完整可见。Root 仅对仍可接续的六位负责人及预算负责人做有限收尾；**没有声称收到其余 49 位的新 STOP 回执**。索引逐一登记全部 56 owner 的现存图、未封目录和待办；其中先前已封源的成果仍保留，其余开放工作明确记为中断草稿，不为凑 56 重启开发。

长期目标已于 `2026-10-23T21:59:13Z` 经工具实际设为 `paused`，未标完成。最终可见7位均已交收尾记录；另5位显示 `pending_init`、4位 `interrupted`，其余40位不在当前可见注册表。对 pending 项已尝试 interrupt 并排入停止消息，但注册表没有取消确认，不能宣称全部旧任务均收到关闭回执；它们没有新业务/进程启动许可。最终快照和具体名单在索引中，恢复先处理此状态。

## 本轮实际执行证据

关键回执的路径、bytes、SHA 由 Root 实际读回，见 JSON 的 `critical_evidence`。主要入口：

- `J/logs/build-java-tools156-firstcut16.json`：95392 B，SHA `10d69de937ef6cfb4ef7724f6c85df356e293f9ec490144d29041cabf0fb0554`。
- `N24/bootstrap_integrated_tools/source18/QUALIFIED-DELIVERY16.json`：C16 合格交付。六件实际 runtime 位于 `J/build/java-tools156-firstcut16/ck3-control-build-tools`，主 JAR 加 Jackson 三件、JNA 两件；恢复时消费交付和构建回执中的完整合同，不凭类名拼 classpath。
- `J/artifacts/fullg2-source08-materialization01/SOURCE-GRAPH-ACTUAL01.json`：2400 B，SHA `96f9c73c43f95ec12ca17aeb32c7824e638670ee584c8ea000aac94e1849a8cf`。实际源根 `D:/codex-ck3-demos/2026-10-24-java-g2-source08`；48228782 B logical，文件实际分配加目录 guard 61640600 B，连元数据 62680984 B。
- `J/logs/build-full35-earlycompile01-compile-only.json`：2181508 B，SHA `c66a249fbd121ff96d053c4658a01c57ce58ebabeea1571649b72baedf26f897`。外层终态 `J/build/resume-current-20261024/g2-m4/tools_c15/full35-earlycompile-run01/terminal.json`，child 1、942.0798408 秒、Job 0、三个后验 MATCH。

Full35 四组实际编译问题：governance 缺 planning-runtime 依赖；wave2-runtime 引用上层 local-service；wave2-military 的 Jackson `fields()` 弃用触发 Werror；events 重复局部变量。对应 owner 已交后继源码与 POM/迁层方案，**未第二次编译**。原日志为 GB18030；旧 helper 用 UTF-8 读取失败，typed reactor summary 为空。17/4/14 来自原日志检查，不能说旧 typed receipt 已成功解析。

原 Maven 日志报告 57.765 秒，外层实际 942.0798408 秒；重复扫描约 205762 个文件/目录已定位为开销来源。WJP 结束判断、helper 首次扫描和最终截止守卫的生产修复在 C17 候选中，尚未实际测得优化后耗时，不报告秒/日改善。

`full35-raw-summary03/terminal.json` 实际 RED：child 1、0.4112556 秒、Job 0。负例误改 Build Order 同名行，正式 Reactor Summary 未变，不能把错误负例的接受当生产 parser 缺陷。raw04 修正定位的两源码已落但未执行；不能将 raw03 改写为 PASS。

## Native32 的唯一续接点

根为 `R/ck3_autonomous_player/native_bridge`，不能误用 `R/native_bridge`。旧四个 cache 共 90907232 B，却没有可复用业务对象/EXE；约 750 个 Person10 对象是旧图闭包估计，不是新构建通过。

当前 cut03：5511 文件，5501 native 加 10 sibling，54 selected，9 个严格 C++ recipe；并行 4、32 targets / 35 run descriptions，退款和贷款宏均 OFF。包含 M4 scalar08 的实际 18 行贷款与 16 case 标量夹具。**M5 Attach09、Family generic v3 等仅留下一 Native cut，不热改本图。**

- `N24/revisions/reference_main/native_combined_cut03/SOURCE-MAP03.json`
- `N24/revisions/reference_main/native_input_repair04/SOURCE-MAP04.json`
- 修复请求 `native_input_repair04/MATERIALIZATION-REQUEST04.json`，32660 B，SHA `4d5df9966bb17b6c2ac241a27d57fbb8b89ec7e33bba2cef194f9705415d74d4`。
- `N24/revisions/reference_main/native_fixture_metadata03/METADATA-MAP03.json`
- 唯一拟源根 `N24/native-frozen-combined03`；控制根 `J/build/resume-current-20261024/native_combined_control03`。最后观测源根仍 ABSENT，控制根仅 ROOT-ADMISSION；这是带时间的历史观测，恢复必须重新核验。

两次失败均在复制前：r1 JNA 临时根超出 grant；r2 已修 JNA，但严格 Jackson 缺 `append_utf8` 等 nullable creator 字段。Request04 共补 10 个显式 null，并按实际 Java record 审核；没有放宽 JSON 校验。

终态在 `J/build/resume-current-20261024/g2-m4/tools_c15/`：

| run | terminal bytes / SHA | child / 秒 / Job |
| --- | --- | --- |
| `native-sourcecut03` | 109871 / `891bd3ca8693d1697340162c8d5f5f5b3932a50b5ce0dad631347376b63018d3` | 1 / 1.0929793 / 0 |
| `native-sourcecut03-r2` | 110729 / `7f1e5673f13d6a735dd1ef94686d93414d5341112a0996f60e0984ceda28085f` | 1 / 1.6006022 / 0 |

r3 RunSpec03 仅 READY_NOT_RUN，现 STOP 覆盖其启动资格。ENV 未执行。重新准入后必须 fresh ENV 七工具、全部 5511 源及十个 sibling 的前后验；Testing ON 的研究 buildroot 与生产 ENV root 分离。全部目标共享一次新 Ninja 图。4 GiB Job 是拟运行边界，不是已测峰值。Person10 实际 producer→83 JSON、Managers/Holy/Loan 实际输出→R3 原消费者均尚待执行。

## 最关键的未闭依赖

SourceGraph 最后草稿为 95 个 current maps、3830 files、51335846 B logical、4528 refs 读回匹配，**未应用 81 项迁层**，也不是已合格 typed Plan。完整 81 表中 **35 个旧 target 位于 protected1524 baseline，7 个位于 97 个历史 layer**；早先“15 baseline”只覆盖 main 子表，不能用于全图。

现已资格化生产 Plan 为 baseline+overlay，没有 final-view retirement。简单添新 local-service 路径会保留旧类；不能删 baseline、伪 same-source、让同名类一起编译。SourceGraph 是版本化 relocation/retirement 合同唯一 owner，必须同步 Assembly/Plan/Resolver/Materializer/全部消费者与回归。收尾已保存 `relocation01/PARTIAL-SOURCE-MAP-STOP01.json`：5 production 加 4 test/helper，共9 Java、12 个测试方法，仅 DRAFT，0 编译/运行；不是已资格化 v2。旧来源继续作为祖先，旧→新路径及变体源码变更须明确证明。该合同尚未完成；C17 冻结后新增能力须走下一独立工具后继，不影子覆盖 C16/C17。

Planner08 已封完整 141 selected / 35 POM / 81 moves，静态内部依赖无环不等于编译通过。`auto_loop/actual_life_fixture06` 的外部 ClockStatusRead 旧 pin 曾被供方改写，旧路径后来缺失；内容另存不能追认原 FileID。后继 exactday02/auto07 必须用实际新 refs 重新资格，保留旧失败，不给 alias fallback。

SourceGraph 收尾还列出两处未解析 import：`NativeArmyMoveEffects → ArmyRetreatPostReadCollector` 的最终 provider/package 未闭；`Definitions → contracts.OperationKey` 的正确类型为 `application.action.OperationKey`，SDK 新修已封但尚未进入当前95图。Catalog/FIRST7 已在该草稿内，不能继续当永久缺件。

以下共享链仍是部分落源或草稿，详见 56 owner 索引：

- 实际 Startup/PreparedSources、完整 DomainAssembly/RootRuntimeCommands、17 leaf 战争 factory 与所有阶段生产者；缺实际输入必须 preNative INCOMPLETE，不能空 registry/Noop/接口授 Ready。
- 原 completed-unsaved-tail 的真正 RollbackAuthority、SDK canonical Driver/SAVE 文件校验与同 writer 重验；新 Java SavedMaterial 路径须显式 typed 分支，不能改旧 P37 字段名冒充。
- Family5 的 request-aware preparation、公共 actor redirect、played/sender 分离、pending 第六 role 的原生 ctor/copy 证据。不能由偏移数学猜 `+304`。sameSEM send 需要独立 typed 发送结算；Family14 核心 State/Ports/Codec 未落，泛 Applied 不放宽，不给关系完成/游戏日信用。
- Window2 UNKNOWN 独立 Recon 合同/allowlist、真实 installer 两阶段 quote/lease 与 afterframe contract router；不借 M5 权限、不重发结果未知动作。
- 公共 Army13 逐项原字段兼容：64 位身份/FILETIME 用 decimal string，普通有界整数保数值并校验安全范围；全整数 string+integer_paths 候选不能当原公共 ABI 已迁完。
- 公共 SELECT_EVENT_OPTION 的实际 planning scope、同事件实例原选项/效果来源及 dispatcher；READ flush 导致 refresh 时不能冒 option ACK 或偷偷改 expected_revision。
- NEXT 采用 BEGIN/AWAITING→实际首 SAVE 私有确认→BASELINE ACTIVE→M7/newcycle 资格化同一 pair；不伪 0-cycle、不拿旧 pair、不再次 SAVE。Host CAS、动态 callback、新 epoch/window ancestry、retained AUTO 尚未闭。
- 软件 transport/custody 夹具不等于完整 Root/Game 成功。ManagedGameSession 保持真实 OS/source 私有绑定；完整 Root/Family 走实际 managed Game 集成入口，缺环境明确 NOT_RUN，不能造宽测试 authority。

## G2 M0–M7 的停点

各末次图的精确路径/bytes/SHA 见索引，不按 mtime 自动采用。新研究窗口即使已读取也仍可能未封源。

| M | 最后封源与新增事实 | 仍未闭/中断草稿 |
| --- | --- | --- |
| M0 | prewar09 / 105 源；真实 V1/private war witness、完整 query 外层严格校验 | 10 history/canonical reuse/supplier；fullPower/.4完整条款、损失及 cooldown 实际持久 |
| M1 | native14 实际 batch/caller 定位；Java 仍 native07 | persistent +84 正向 writer、完整发布入口 |
| M2 | merge04 / 5 新 Java；on_action DB 来源与冷回放 | 05 Raw ScriptValue、完整 AST/dynamic scope/VFS precedence/外层失效 |
| M3 | held-title09 / 78 源，实际增删重排/比较器 | 10 SSuccessionEventData→PlayerInfo+268 实际 assembler/copy 来源；自然 episode 权威 |
| M4 | scalar08 Java8/native22；贷款/标量真实 copier 源 | TTL09/worker研究、lender/双方/选项、完整成本及到账/还款后态；宏 OFF |
| M5 | native09 Java16/native16；AttachCurrent 后继供下一 Native cut | 10完整评分函数/真实 callee；自然退却/补给实际选择与业务后态 |
| M6 | native10 / 45 源，真实终态桥与历史校验 | 11真实 manager worker/batch；+408 在 phase scheduling 也写，非完成专用戳 |
| M7 | crown09 / 33 源，同实例发布/原件重演 | 新 window Binding/事件祖先、跨 later SAVE/Next retained 恢复，完整 cold 实机 |

静态 CALL/计数/日期/窗口消失不授游戏效果。`0x310DB20` 是 mutation，禁止作只读退款报价；战斗消失不是胜利，declared cost 不是到账。当前 .4 EXE SHA 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`、101040248 B；脚本中 `pam_sf` 来源未明，EXE 相符不证明整树 stock。旧仓库 1.19 只作历史参考。

## 预算、存储和现场

最终财务 STOP 为 `N24/revisions/budget_fast_lane/VACATION-FINANCIAL-STOP01.json`：96929 B，SHA `00ca210198ff9d9cfb5a042b96a869605569d22fc23e4791da2f8cfca4e039ec`，含61联合 claim/56 owner、最后观测年龄及超额历史。原 D 工作包硬帽 6979321856 B（6.5 GiB），Z 本轮 32 MiB；whole allocated 实占仍为 null，不能将 conservative actual+future 写成实占。STOP 将 live future 执行资格清零，不能据此声称物理释放或删除资产。C17 的 P2/Maven 卡从未签，不能因 request 已封就执行。

本次两份新 docs 独立合计 128 KiB close-only 帽：`J/logs/RESUME56R2-VACATION-DOCS128K-CLOSEONLY01.json`，2574 B，SHA `399d279059f59524897a526c88d24f062126f26365dcd5d99dd9e695be5c0d78`；旧 progress 仍单独 32 KiB。所有未执行预算/standing/spec 被用户 STOP 覆盖；旧 `2026-10-23T23:30Z` 截止不授恢复执行。

Root 在 `2026-10-23T21:51:18.955997Z` 经 Windows GetDiskFreeSpaceExW 只读观察：C 可用 6805884928 B、D 797736873984 B、Z 136849252352 B。不是项目完整 census，不推导清理量，也不能拿 D 余量抵 C 写入；恢复重测各卷、安全和系统增长预留。

按[统一存储策略](../storage-retention-policy.md)与[参数](../storage-retention-policy.json)闭场；没有删除、移动大树、去重或获取物理释放信用。当前 C16、唯一 Source08、Native/Reference 必要输入、未解关键失败保留至既有 `2026-10-30T16:30Z` 用途复核，不自动续期、不因到期无条件删除。本文/索引作为 record 于 `2027-04-22` 复核。未分类中断草稿在恢复或 48 小时用途复核时逐项认领，不能无限续存。

共享 Git 工作树已有大量修改/未跟踪文件，含历史失败日志及奇怪名称；本轮不 reset/clean/add-all/提交/推送，也不替其他任务清理。交付主要在 J/N24；仓库 `java/` 不能当已整合最新候选。机器存在旧 operator/CK3 身份未明记录，未接管、未杀进程，不能把本任务 Job0 说成全机无进程。

## 恢复顺序

1. 先取得用户恢复指令；读最终 STOP/56 owner 索引，核机器、默认命令行 `mvn -version`（最低 3.10.0）、来源和存储新鲜准入。不得沿用旧运行 spec 自动启动。Maven 不绑定安装绝对路径；本轮观察的 Maven home 只是这台机器当时事实。
2. 处理过期/中断草稿、pin 漂移和实际来源冲突，确定唯一工具 cut。C17 source19 的 207 表与 typed request 可作续接输入，但必须新物化、完整 Maven 与 own-archive；raw04 的实际正例和负例分别验。新的 graph v2 若不在该冻结 cut，单独后继构建。
3. 完成 final-view relocation 合同；以 Source04 真实 current maps 和全部历史 ancestry 重算唯一 winner。执行第二次 Full35 test-compile，消费退出码/超时/Job/来源后验；失败先修共享生产链，不静默回 Python。
4. 重新准入 Native32 Request04，先源码物化，再 fresh ENV/configure/build/run 与实际产物发布。不要把未编译的 generic Family/M5 Attach 后继插入当前 cut；它们需要后续完整来源闭包。
5. 实际生成 Reference1511/41、完整 R3 输入和所需原件；运行整组持久 CI、30 cold/30 warm 及独立 SDK continuation。缺必填输入明确未执行；局部编译/JUnit不能代整个 CI step。
6. 补完实际 Root/领域/回滚/NEXT 两阶段和所有消费者；执行同宿主 Full8 合同验收与实际 Game 集成。原 Python 全能力接管达可运行条件后用新 Java 实测，G2 后续研究继续独立推进，未知能力如实限制。
7. 新鲜后台 Steam offline 准入和正确机器授权/账号占用核验后，才启动受管游戏。使用完整规划器，以1066罗贝尔重新开局；合法动作实际后态、真实推进、成对 SAVE、恢复续行逐项留证。无静默 Python fallback、无 UNKNOWN 重放、无 OCR/鼠标替代原生接口。

Root 为唯一构建/Game/真实 writer 执行者，预算唯一 issuer；子任务默认仅源码。用户要求 fast 关闭，本轮配置已设 default，但不把配置写入当会话/UI切换验收。原北京时间 06:00/07:00/09:00 检查节点因本次休假停止撤销；恢复时按实际新鲜依赖重排，不承诺原日期完成。
