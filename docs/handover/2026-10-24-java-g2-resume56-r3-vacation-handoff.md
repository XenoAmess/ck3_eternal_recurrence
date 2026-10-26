# Java 全能力迁移与 G2：R3 度假交接（2026-10-24）

用户最新指令：**“你要去度假了。编写交接文档，输出到docs。”** 本轮已转为交接收尾，停止新增开发、审计、采集、构建、游戏启动和执行许可。没有把长期目标标成完成。恢复工作须先明确恢复，再重验当前机器、原件、预算期限和执行租约。

先读本文及[机器可读来源索引](2026-10-24-java-g2-resume56-r3-vacation-source-index.json)，再按需读[R3 滚动记录](2026-10-24-java-g2-resume56-r3-progress.md)。本交接覆盖本轮最终现状；[R2 交接](2026-10-24-java-g2-resume56-r2-vacation-handoff.md)及旧回执仍保留历史，不能用其 C16、旧 STOP 或旧许可覆盖本轮事实。

## 先看结论

**完整 Python 能力迁移未验收完成；Java 新版实机未开始，新增保存游戏日 0；G2 八个 M 完整验收仍 0/8。** 没有可靠的全项目完成百分比，也没有可承诺的 Java 实机开始日期。

| 范围 | 交接时实际结果 | 不能外推的范围 |
| --- | --- | --- |
| 通用工具 C23 | 此前完整 611 tests / 85 XML suites，Maven 与 Own PASS | 不是完整 Host、SDK 或 Game 通过；官方 CI 最后已知仍有 Unicode/编码失败 |
| C24E bootstrap | 新 94 个生产源严格编译、967 项 archive 读回 PASS | 仅 SOURCE_BOOTSTRAP_ONLY，不能替换 C23 通用资格 |
| C24E 关键回归 | 22/22 实际 PASS，0 fail/skip/abort | 不是完整 Maven 测试集通过 |
| C24E 全测试源码 | 116 个测试源严格编译 PASS，247 classes | 该阶段没有执行全部测试方法 |
| C24E Source | 280 项物化及逐赢家来源/目标核对 PASS | 不授 Maven、Own、Host、Native、Game 资格 |
| C24E 发行 / Maven / Own | **NOT_STARTED / NOT_RUN**，Domain E、candidate E 均未发布 | 不因上述四项 PASS 宣称通用资格 |
| 完整 Host25 | R5 输入和生产请求已冻结，5234 目标 | Plan、物化、独立审计、全 35 reactor test-compile 均未执行 |
| Native08 | 组合源码和 recipe 已冻结 | ENV/build/register/profile 未执行 |
| 新 G2 Raw28 | 六组 COMPLETE、24 reads、13 个步骤全部 child0/Job0/三个 MATCH | 只证明本地静态字节采集，不证明运行态、业务或八专题完整 |
| Frontend 定位器 | 原 36 软件 PASS；配置桥另 3/3 软件 PASS | **0 CK3 read / 0 新 Admission / 0 scan**；桥尚未 Root 采用 |

旧 C24D 最后一次真实完整 Maven 为 RED：94 main、115 testCompile 通过后，盘点 JUnit 正在删除的 privateTMP 子目录遇 Win32=2，child124。CB47/Test46 已修共享生产路径且关键回归通过，**没有执行完整 Maven 复验**。历史 Source、TMP、配额及测试失败都保留，不追改为 PASS。

## 机器、仓库和路径

本交接的机器专属事实仅属于 `machine_id: xenoamess-full-tower-eb9d2c1186`。Root 于 `2026-10-24T13:12:20.720229Z` 实际执行既有身份工具核对匹配。全部时间用 UTC；北京时间为 UTC+8。

- `R = Z:/ck3_mod_rewrite`
- `J = D:/codex-ck3-demos/2026-10-22-java-phase1`
- `R3 = J/scratch/resume-current-20261024-r3`
- `B = R3/budget_fast_lane`
- `M = J/artifacts/tools-c24-control-inputs-r3-01`
- `T = J/build/resume-current-20261024-r3/g2-c24-tools24/tools_c15`
- `W = J/build/resume-current-20261024-r3/g2-native-static07/window-controls15`
- `F = J/build/resume-current-20261024-r3/frontend-lobby-locator20`

索引中 FileRef 使用完整路径、bytes、SHA256；缩写不用于执行参数。外置 D 原件没有复制进 Git。换机器后应先核 machine_id，不能沿用这些盘符、安装、离线或实机资格。

交接前实际仓库：`master`，HEAD `4a999f3ef5aa6770345832ed6a3ed47602c3c4f4`，120 个状态条目（44 modified、76 untracked）；index SHA256 为 `e735fdd21127213dc2de9140983d260fd5cccadce845c45a0569406f975eb4e0`。本次只新增两份交接文档，不 add/commit/push、不改 index、不 clean/reset/stash。大量 R3 新 Java 仍在 D 的隔离源码中，**尚未整体合回主树**；恢复不能把 master 现状当全部成果。

同机本轮默认 `mvn -version` 实测：Maven **3.10.0**，home `C:/apache-maven`，Java **21.0.10**、Eclipse Adoptium、`C:/jdk-21`，平台编码 UTF-8。安装位置只是观察，后续仍运行命令行默认 `mvn`，不锁绝对 Maven 路径、不追逐最新版。

## 停工、并发和租约

用户期望的是**不重复浪费的 56 有效并发**。本轮早段曾有 56 running 的截面，但从未据此宣称持续 56 个有效生产者。等待卡、等共享叶、完成态和模型错误都不算有效业务并发。补位过慢、预算与唯一构建入口集中确实造成空等；系统性模型容量错误又打断多人。Effect 负责唯一补位，后来将未验证旧入口拆成互斥语义审查，并将确认缺口交唯一生产者修复。

Effect 的固定截面 `13:14:25Z` 为 **56 workers = 19 running / 34 completed / 3 errored**，Root 另计；running 也含收尾与等待。三个 errored 为 NativeArmy、NativeSchemesEvents、Reference 的模型 capacity 错误。之后仍有自然 completed，不将该截面冒充最终瞬时计数。没有为交接补人数，也没有收到所有 56 人的独立进程关闭证明。

**实际执行线已闭：** Tools 的 session49052 已由原 owner 消费；最后 child0/Job active0。Forecast 于 `13:11:12Z` 确认 session=null、live owned child=0。没有新 Maven/Own/Host/Native 或扫描在后台等待代管；不需要 kill/delete。Root 没有接管或结束未知旧 CK3 进程。

Root 于 `13:16:52.434978Z` 将任务总线 `ck3-java-g2-resume56-r3-20261024` 更新到 **seq8289 / waiting / STOP-HANDOFF**。四条手工内存预留全部 RELEASED，reserved slots=0、hardJob/outer reserved=0；Host/Native 预留从未启动。磁盘保护额没有因此释放。原运行上限为最多四条非 Game 重型链、Job 合计12GiB、outer合计1GiB、Ninja合计4、单 canonical Maven writer。未来执行仍须重新登记，并逐 child 以实际 RAM/commit 覆盖保守 **38654705664 B（36GiB）**，不能沿用 seq8288 的 RESERVED 状态。

只在明确新任务且没有在产 WIP 时使用原 worker 的 `followup_task`；普通 `send_message` 不会唤醒 completed。模型错误不当成业务失败或完成；不要为绕过容量问题复制 writer。原 Reference 的 R5 工作已明确转 SDK，不能重启重复实现。

## 源码覆盖百分比的正确口径

最新正式清单仍是 `R3/planner_owner/progress_correction56/SOURCE-DELTA56.json`：**297/323 = 92.0% SOURCE_SUPPLIED_NOT_QUALIFIED，24 gap、2 config pending，完整验收百分比为 null**。这是固定截面，不是当前全语义完成率。旧 304、311、309 都是历史清单，不能取最大值。

第一轮六个互斥审查包发现此前覆盖表中12个真实反例，才有56的扣回。第二轮 G–R 和晚到 NormalExit 的 **40 个去重原名尚未结算**；没有新57/58：囚犯3、Contact2、普通交互发起1、Registry2、AUB select/confirm2、Faction1、Camera3、Decisions6、Faith4、White4、GUIWindow/Army10，加 NormalExit2。它们不是40个新增能力或40次实机失败，不能直接用40再计算一个百分比。

Gov29+test30、NormalExit22、Activity20/PublicMCP 后继已有源码修复，但尚未重新独立结算或运行，不能自动回补计数。Activity 的任意 malformed payload 原错误消息仍 NOT_VERIFIED。完整迁移还必须覆盖真实配置、全部消费者、序列化、完整 CI、独立 Python SDK continuation 及实际 Java 运行链，不能只看同名 wrapper。

## 接手后的最短执行路径

1. 明确恢复；读 AGENTS、通用存储策略、本文和 JSON 索引。核当前机器、HEAD/index/dirty，保全外置成果。处理所有已到期许可，再发当前预算/真实租约；不要为了继续使用旧 nonce 延改回执。
2. **复用 C24E 已 PASS 的 94/22/116/Source280**，原件重验一致即可，不重跑无新增观察面的阶段。恢复发行的真实源来自索引和 `B/TOOLS-C24E-SOURCE-MAVEN-OWN-STANDING54.json` 的 schedule，但该旧卡本身不是新执行许可。
3. 新鲜具体发行 READY/child0/Job0/三个 MATCH 后，实际运行完整默认 Maven；成功后跑 Own。失败修共享生产路径，执行失败路径回归。全链 PASS 再由 Root 采用新的通用工具六文件，不能用 bootstrap 六文件替代。
4. 以冻结 **Host25** 跑实际 Java Assembly → Plan → Materializer → independent audit → 全35 reactor `test-compile`。**缺 Managed/current/Native 实机输入不应阻止编译反馈。** 按真实编译错误拆给唯一 owner，不继续移动固定5234目标去追所有晚源。
5. 合格工具下执行 Native08 的完整 ENV/build/register/profile；可在总资源内与 Host 并行，保持一个 Ninja graph、总4 jobs。Reference 仍是 Native08 生产 owner；其 capacity 错误和旧槽已释放，不等于可直接继续。
6. 编译后再闭所有晚源真实装配，执行完整 CI step 命令组及独立旧 Python SDK continuation。缺配置/物理原件明确 Missing/NOT_RUN，不用 Noop、空 registry、旧 Python 活 owner 或假 Managed 正例绿化。
7. 具备可运行条件后核新鲜 Steam 后台离线、实际 CK3/SDK/部署/进程 owner、唯一 Game/账本权限，进入新 Java 的1066罗贝尔完整规划器。实际动作后态、游戏日、成对 SAVE、restore/NEXT 都单独验收；不要拿 HTTP、ACK、编译通过或旧局天数抵扣。

### C24E 的精确恢复点

源根是 `D:/codex-ck3-demos/2026-10-24-sharedwire-tools233-source24e-r3`，实际280行 = 234 TOOLS + 46 HOST。源码物化 child0/9.8971648s/peak219848704/Job0/三个 MATCH；源逻辑5675000 B，source body6598656 B。SOURCE-MAP01 为491140 B，SOURCE-INPUT-GUARD01 为367313 B；563 files、564个 Native observations，原源及目标逐赢家核对一致。

bootstrap 的 `J/artifacts/java-tools233-firstcut24e-r3/actual.json` 为196072 B，记录完整 private runtime 六件及967 ZIP entries。critical22 和 test116 的 consumed 原件位于 M，来源终态位于 `T/c24e-source01/terminal.json`。完整精确引用在索引；不手拼类库或凭类名替换完整六文件。

下一发行入口为既有 `org.xar.ck3.control.build.ManualCapacityReleaseMain`，classpath 使用现有 issuer classes 加新 private94 实际六件。物理9参数是 Config、AttemptCapacityRelease template、Domain 三份各自的 path/bytes/SHA。**Domain 严格5键**：owner、issuer_task、authorization_source、authorization、scope；叙述不得塞额外字段。所有执行 FileRef 仅 path/bytes/sha256 三键，注释放外层。过去多次手填额外键导致 child 前拒绝，不能改严格 codec 来接纳。

待用 `M/C24E-MAVEN-CONFIG01.json`、Template01 只供恢复时重发不可变后继；本轮 **Domain E / candidate E / 实际 release E 未创建**。不能先写发行 READY。执行完整 argv 以54 schedule与新真实卡为准，不把本文省略的缩写粘贴成命令。

Maven 仍为900s、Job2GiB、heap768MiB，whole84MiB = source8/build40/privateTMP16/artifacts12/logs8。private bootstrap持续计入 artifacts12；临时目录和 JNA 必须在批准路径，CB47负责创建并持住 exact TMP。完整最大链还含 Own compile180s、Own run240s和收尾，**不能缩 timeout 硬赶13:30**。

Own 使用现有两份真实 reader 源，严格编译后 against 完整 Maven 的实际六文件读回；执行前 unset `XAR_ORACLE_PYTHON`。不得省略真实历史证明、编译/JUnit/accounting/部署闭包或把 software metadata 当 whole receipt。

### R5 Host25 和 Native08

Host24 的5234文件、72526520 logical、90152960物化上界超过旧 R4 的5120/64MiB/80MiB；该事实保留。新 **R5** 为6144文件、96MiB logical、112MiB native；module src 为 local-service16MiB、application/native-transport各12MiB，其余8MiB，旧 R4/旧测试不变。SDK35/36与Parity47同步 Profile、CI、Compiler、Materializer Card；均只随 C24E 实际资格采用。

`R3/source_graph/complete_candidate25/DELIVERY25.json` 及 PRODUCTION-REQUEST25/SOURCE08 输入保持5234来源/目标，900s、child2GiB、heap768MiB，不将旧4GiB预留冒充代码支持。候选25没有吸收全部晚源。Host原独立320MiB预算对实际物理源/重复快照/控制峰还须核算；**336MiB报价（+16）未批准**，不能把72.5M logical当80MiB physical可装。

Native08 入口 `J/build/resume-current-20261024-r3/native_combined_prepare07/native08/SOURCE-MAP08.json`。组合5517文件（5507 native + 10既有Python sibling），35targets/37runs、总Ninja4；old07+08保守2871296 B在prepare4MiB内。只做了源码组合，未 ENV/build/register。Root原生动作 BEFORE须cached实际旧帧、AFTER须独立新读；原C++ revision变化语义保留。旧退款/借款宏及实验资格不由本次源码组合打开。

## 不能误选的晚源和真实缺口

| 范围 / 唯一 owner | 最后正式或真实边界 | 恢复时须做 |
| --- | --- | --- |
| PublicPause / Sway | APP Construction29、中央freeze22、Kernel21和Runtime43调用方存在；LS Runtime/Product/Test仍UNSELECTED DRAFT | M3深历史source reader、Origins warm候选守卫、Planner中央第11参、Recovery第9参及Archive非空失败消费者一组闭；不能单选43 |
| 历史来源 / M3 | Authority19仍唯一正文；`requireArchivedOrigin`只对齐API，**0首写** | v2无持久Witness/FileID，不能用hash追认；新v3真实live Witness生产者/codec/所有v2消费者同步，纯DATA冷验不能借live guard |
| Origins33/34 | Registry2只读，未首写；warm首Submitting候选真实会误拒 | canonical仍IntentDurable时candidate=head+1应按真实合法transition验；历史seq<=head用完整receipt；保source/parent/reservation，不全局放宽 |
| Stock / Recovery | 最后完整cut49；Stock50两叶已冻、PreparedSources/Test未发布 | v6 Settings/SDK37/NPI31→32同cohort；现mapper8与future Factory43 mandatory9不兼容，不能填假第9或倒选旧源绿化 |
| PublicPause中央 / Planner | 当前52仍10参，第11th只协商接口，**0代码** | 新同installation classifier/consumer正式后再用Runtime43，不把draft参数当生产接口 |
| GUI / M4 | 最新完整正式仍Native26；GuiPublicMetadata单体存在，GUI27闭包未实现 | Contract新Optional字段、Codec出口、真实before/Driverdiag/parsed/later/after生产者先闭；typed错误、null wire、ACK原义及宽数分别保真 |
| Decision / Ledger | Decision30两Java只有DRAFT-HANDOFF30 | 缺M4 Contract/Codec与真实上下文，不可编/不可选；不要造常量观测补孔 |
| Presentation / NativeArmy | 只读发现10项返回缺字段；新formatter未闭且worker capacity错误 | 原owner恢复真实接口后实现，不复制M4 binder |
| SharedOwned25 / SourceGraph | 9Java、39方法全未编跑，明确known lock gap | 多root下first-existing锁锚点会改变；26未写。须first-declared existing等真实修复/回归后再资格化；不得夹入C24E或热改C23 |
| Known | Activity20七targets及PublicMCP/RPC源码已闭，9方法未运行 | 普通交互initiate的retainedOrdinary漏当前actor，Known21未开始；原UNKNOWN不重放 |
| Route | 正式14/14A/15保留；Contact2与Route16未开始 | timeout/native拒绝原typed错误、projected stale语义；Route15误用PUBLIC pause wrapper，原internal=True应沿Life38原内部formatter修，保原件深回放 |
| Registry / Origins | snapshot/search/bundle公共revision字符串及宽数输出缺专属profile，未首写 | 与Actual SDK/RPC消费者及serde整链改，不泛化递归宽数或误限所有revision为u64 |
| Prisoner | NormalExit22/Auto53正式，5回归未运行 | 囚犯3工具原错误profile未首写；缺ACK只保真reason，NT无typed missing不能猜类别 |
| Gov | Gov29生产修Council2/Government HELLO/Crown错误；test30修夹具两ref反置 | 原29测试错误保历史；新20回归/2Python oracle均未运行，不追分 |
| later READ/BATCH | Save32+Auto52/53/54+M7 38/39+NS35源join | 历史私admission与独立current绑定分离，保持saved frontier/dirty/UNKNOWN，不松原exactpost Base；真实Managed cold/laterBATCH正例仍缺 |

多数晚源只是SOURCE_ONLY。以上之外的完整56 owner列表、最近元数据导航和当前帽见索引；mtime只用于找文件，**不能选择赢家、证明依赖闭合或授予资格**。所有目标转权须先检查原owner有无WIP。

## G2 八专题和下一有限队列

Raw28实际CODE856/META13892/DATA0、unknown0，13步骤完整墙钟88.910272s；Root核101唯一refs及全部原始Job0。六原owner都已被真正followup。没有重算整EXE SHA、复制游戏本体或把静态字节当loaded DB。研究完整仍0/8。

| M | 最新结论与Java落点 | 未闭与下一采集 |
| --- | --- | --- |
| M0 | actual receiver三RF 141/50/54，UW无CHAIN；stock37/38、oracle40、Host42源已交 | 下一CODE245+UW48；自然日期/领土receiver语义未闭，真实Release/Managed缺失 |
| M1 | 四RF共5569 CODE边界核实，flags2无CHAIN；婚姻typedfault41源闭 | 未证明自然每日Execute或CFaction+84日期writer；等完整5569代码 |
| M2 | A06830完整184：allocator virtual20能回写data/cap，不能把预zero判empty | 下一vtable DATA24+PE META888；load/frontend实际firstdraw与2–8 draw仍未全闭 |
| M3 | FullMaterial/事件/冷保存消费者多轮join，实际私票晚READ/BATCH路线已源闭 | Managed真实正例未执行；新archived source reader转M3但未首写，无当前标准待采Plan |
| M4 | 310EDC0完整468证明cost==0或signed余额>=成本，11UW槽/handler核实；六方法回归源未跑 | 完整净退款、合法贷款成本到账/还款仍未知，语言payload未知；不能授资金信用 |
| M5 | 19FF9C0完整759是计时/缓存聚合协调，不是move/retreat/supply提交；quantity RF343已定位 | 下一仅UW头META4；动态.data零尾不是loaded值，勿造悬空AI |
| M6 | wholeRF133+UW16已证，71B保持NO_RF candidate；manager保存key2820接收器不同于Activity completedByte | fullID/token/SAVE连续性/cause仍UNKNOWN；下一META920、CODE0及131072峰未fund；10回归未跑 |
| M7 | 3F927D0为ring buffer；总会调用341ED60；current38/39接真实admission/savedfrontier | 不证明通用worker/节奏；341ED60仅候选未标准Plan；不得据helper增游戏日/SAVE信用 |

未执行的五份标准队列：

1. `R3/m0_research/frontier39/NEXT-FINITE-PROPOSAL39.json`
2. `R3/m1_research/native43/PLAN-M1-WINDOWS43.json`
3. `R3/m2_research/07-scopebase-plan/WINDOW-PLAN07C.json`
4. `R3/m5_research/native15-requests/PLAN21-QUANTITY-UNWIND-HEADER01.json`
5. `R3/m6_research/save_manager31/PLAN-M6-METADATA32.json`

五组没有新Request/Admission/Index，没有执行；旧13:30期限不自动延长。Forecast仍为唯一实际文件读取owner，每批采用具体Plan、实际Source17身份及新一次性Admission。新完整峰、控制额度和原件身份先核验；后续header/callee不需再逐函数找Root口头确认，但不能复用已消费或过期卡。

Frontend另线：定位器原113effective main/36软件已限采用；配置桥新增3main+1test独立3/3实际PASS，prepare有效116与scanner113分列，Root尚未采用桥。`PREPARATION-DELIVERY26.json`等原件在F。F实际3280896 B + 已报未来966656 = **4247552 > 4194304，缺53248 B**；4.125MiB替帽尚未批准，扫描一直0。旧2MiB whole超114688的RED仍保留，软件PASS不抹掉它。

## 预算、保留与13:30硬期限

最后权威：financial29、Source80、Memory28、Native22、Docs13，索引提供完整FileRef。均固定 `2026-10-24T13:30:00Z`，不自动续。接手时间若已越界，先视为到期；就算仍在窗口，也必须遵守本轮STOP而不自动启动旧卡。

- R3 **4063MiB**，4096上层内余33MiB；Source206MiB，56owner合169107456 B + external44564480 B =213671936 B，guard2334720 B。
- Native1792MiB，future未分配1531576320 B（含corpus55181312 B）；Window20MiB、Frontend4MiB。W+其专属TMP实际18731008 B，余2240512 B；24MiB Window建议未发行。
- Tools195MiB；新whole84MiB、controls40MiB、独立source7.5MiB。旧失败保留，未花60MiB只是重分类，物理释放信用0。canonical m2增长只计一次64MiB。
- 全holds266335396732 B，D required309285069692 B。financial29实际观察12:38:47.287367Z，D available845031219200 B，差535746149508 B；不是全项目实际盘点，未知项没有当0。
- Root交接前13:12:20Z再读D可用844981846016 B、Z136007045120 B、C3609595904 B；C无新增项目输出。未扫描全盘/m2、未删资产。
- 未批报价：Host336MiB（对320增16）、Window新五组/增额、M6新131072输出、Route2097152替帽、Frontend4.125MiB。不能从其他空余额自行追认已批。

按[统一存储策略](../storage-retention-policy.md)和[版本参数](../storage-retention-policy.json)保留当前准入/故障/恢复必要原件，保护需有期限与理由。到期是复核候选，不能删唯一活跃输入；失败也不是永久保留许可。本文及索引合计限制60KiB，加原五文档129091 B仍在Z192KiB保护额内；用户本次明确授权新交接路径，无新增hold。

## 游戏现场与恢复红线

Root在11:03:56Z实际见operator gate列PID127028/139512/188168；原生句柄均exit259、exit FILETIME0，但EXE路径查询error31。**这只是当时观察，不是交接时仍运行、零进程或可接管的证明。** 未结束/接管这些未知进程。恢复必须 fresh核owner、实际EXE/build/SDK及唯一Game槽；别从历史路径或PID猜身份。

本轮没有Steam模式改变、焦点移动或截图。启动前必须用既有后台probe取得当前机器新鲜offline资格；未知不得用缓存、配置或截图兜底。在线账号占用规则照AGENTS执行。不要恢复退役蓝色面板或nonwar-only；全部战争/政务/外交/建设能力进入完整普通规划器，真实战争不能只关通知。

新生产/构建/CI一律Java+Maven+Quarkus，原C++与前端不重写；不新增Python生产模块。任何命令显式用允许的shell，**禁止PowerShell**。保强类型与入口验证，64位身份/时间用规范十进制字符串，整数拒bool/float；UNKNOWN不重放、ACK不等后态、单动作权威/唯一账本writer不分叉。不得热改冻结runtime/SDK，不能伪造归档、Noop、空provider或old-Python fallback。

交接验收只验证两文档的结构、引用、hash和Git diff；没有借交接启动新的业务测试。后续恢复先完成真实链，所有未执行项仍按NOT_RUN保留。
