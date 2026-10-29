# Resume64 本地模型实际执行记录

machine_id: `xenoamess-full-tower-eb9d2c1186`。配置沿用 [唯一配置](local-model-executor-config.json)；远端模型服务器的 machine_id 未核实。本文由模型协调岗独占维护，记录本轮新增结果，不覆盖历史经验。

## 调度与原件

- 2026-10-29T14:41:53Z 实际读取 `http://192.168.1.7:8080/metrics`，running=0、waiting=0、KV=0，才解除旧 HTTP HOLD。没有从客户端连接数或日志无在途推断服务端空闲。
- 先实际单请求，再按 running=2、waiting=0、KV约5.05%的观察升至4。Root随后授权吞吐调整；实测 running=1、waiting=0、KV约3.409%后，Migration、Integration、REA 三组各获2个执行 slot，总上限8。后续将中央原2槽中的1槽固定交runtime执行真实生产P0，中央保留1槽。Integration的原2槽由现有quarkus_host64代理，REA的原2槽由现有envelope代理；交接不增加槽数，lead不同时另发。叶岗不独立重试。服务出现 waiting、running>=8 或 KV>50%时停止新派发并回协调岗。
- 固定 `stable-prefix-v1` 三消息、当前源码确定顺序、任务与真实诊断在最后；temp0、thinking=false、stream/include_usage。原始 SSE 保存实际接收字节，分别记录 headers、首个非空 content delta、总耗时和 usage。未报告 cached tokens 时写 null，不推断缓存收益。
- 使用任务临时 Java HTTP caller，不改生产构建/编排模块、不新增 Python 模块。后续显式 `cmd.exe` / `login:false`；临时 PowerShell caller未执行且已删除。委派执行使用128MiB heap和1 CPU，不占业务领域编测 slot。
- 各请求开始、每次终态和退避写入原 `LOCAL-MODEL-CALLS.jsonl`。caller采用跨进程文件锁追加；委派执行记录实际 lead actor 和统一协调 authority。配置的最多6次暂错重试仅作用于模型HTTP，绝不重放游戏动作。

原件根：`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration/model-coordinator64`。每任务目录含 `REQUEST.json`、`ATTEMPTn-RESPONSE.sse`、`ATTEMPTn-CONTENT.txt`、`ATTEMPTn-RESULT.json`、前置实际 metrics 和 `SUMMARY.json`。`STATUS-NOW.json`只是带时刻的目录观察，不是游戏启动门禁。

2026-10-29T15:06:40Z 的实际小目录汇总为35个已结束调用/35次HTTP尝试，其中31个stop、4个length；另3个目录尚未有终态。该时刻没有暂错重试。此为进行中快照，不是本轮最终总数，更不是35个实际采用。

SDK current首轮在15:03:49Z的目录观察为0B；最终结束后读回SSE实际为14,099,628B，协调岗先前把早期快照外推为一直空流的判断已更正。原请求没有max_tokens，后续输出退化为重复自言自语且无完整终态。15:12:57Z核对实际命令身份后，仅结束自己的模型client PID297384；其后服务端实测running0/waiting0/KV0。原流保留，失败追加中央日志，headers/TTFT等随进程丢失的计时不补造，完整候选/采用0。未执行准备中的原样retry；改用owner明确缩为helper+一hunk、max4000的新请求。此为请求预算/输出退化及client总读期限缺陷，不冒充暂时HTTP错来重复六轮。

2026-10-29T16:14:55–16:15:28Z，首次MCP metadata selector调用连续三次实际HTTP502，按配置分别退避10.880、22.219、40.874秒。16:16:09Z第四次POST前实测running7/waiting25/KV16.54%，caller exit75，第四次未POST；16:16:42Z REA代理两包也在POST前以running32/KV65.4–66.0%拒绝入队。16:20:39Z再读实际running32/waiting0/KV68.56%，全局暂停新POST及下一次HTTP重试。八个客户端槽不是远端最多八个请求的证明；失联/502是否留下远端任务未知，不能根据本地client0宣称服务器空闲。仅协调岗在真实消化后逐步恢复，不重启远端服务。

最新小型状态入口为原件根下`CONTROL-NOW.json`，目录计数快照为`STATUS-NOW.json`；同一父根`LOCAL-MODEL-CALLS.jsonl`确已持续记录到16:16:42Z及后继协调事件，旧工具展示末尾15:29不是日志停写的证据。16:16:58Z目录快照为116个有终态目录/119个结果attempt（104 stop、11 length，其余失败）；不等于116次采用或116个owner已消费。Migration最近十包、Integration既有终态已逐包核交件，余额各0；代理继续直接交sole owner，中央逐叶ACK不作前置。

派发延迟是本轮真实协调缺陷：Legacy actor-zero完整请求等待约38分钟，owner最后人工修单TEST并实测6P、S/Z SOURCE STOP，中央仍未POST。未调用请求已取消，保留原prepared与manual先后；此例是派发与状态反馈延迟，模型调用0、能力试验0，不归为服务/API失败或模型成功。另SDKGoal原件曾因lead转交滞后未及时消费，现已补交。总调用数不能替代可用候选实际送达、编测与采用。

## 已取得的真实采用与限制

| 任务 | 模型贡献及实际结果 | 采用/验证边界 |
| --- | --- | --- |
| Runtime dirty-stop | 首轮Main两操作与新分类TEST，严格javac0，JUnit6P | S/Z SOURCE STOP；`runtime64/DIRTY-STOP-SOURCE-ADOPTED01.json`。未以此声称Main产物或Game已更新 |
| Registry预算 | 首轮两生产操作API正确，原Profile whole4由2P2E到4P；四显式源严格javac0 | S/Z两叶采用，`D:/ck3-state/mcp64-registry-budget01/SOURCE-ADOPTED01.json`。模型误述触发条件且遗漏大输入回归；后继TEST候选单独审阅 |
| Estates raw root | 唯一生产操作与已实际whole12P的候选相同，审阅接受 | S/Z两叶已采用，`D:/ck3-state/estates64/native-root01/SOURCE-ADOPTED01.json`。未采性能及更深嵌套的未测断言；不能说模型独立完成所有测试 |
| Dirty/current恢复 | 首轮候选提供部分结构/manifest非回退方向；owner纠正API与日期分支后编测和采用 | 完整首轮和窄03均不可原样采用。03仍重复被明确禁止的日期比较；主线由owner最小纠正接管，不继续让模型重试阻塞Game。详见[恢复记录](maintenance/2026-10-29-java-dirty-current-recovery64.md) |
| Dirty suffix | 首轮误读反向遍历，拒绝；次轮public fixture构造器方向部分采用 | 模型发明`RawJson.of`且误称lambda会throw；owner修正。提供的600秒又超过真实构造器1分钟上限（请求上下文与owner均漏查），最终合法60秒。最终dirty完整suffix+domain2P、109.973s，5叶S/Z采用；不能写600秒方案通过 |
| Calendar signed | 生产guard方向部分采用，owner补import；TEST不是原样采用 | 首轮漏unsigned fixture、assertThrows边界、持久化往返并猜tamper字段。已采用叶与仍待LS修复分开；不得写三叶迁移完成 |
| Quarkus观测 | 首轮大量Java API错误静态拒绝；真实反馈后02完整源码采用（仅EOF换行） | strict javac0/3.359s，原host whole3实际3P/0skip（2.300s），15:20:57Z S/Z SOURCE STOP；没有Game连接/热重载资格 |
| SourcePrep CAS | 首轮删除canonical Intent gate，实际会在pre-intent错误阶段腐蚀，静态拒绝；02按真实诊断恢复gate/head/seq/event及第二guard | 02严格javac0/3.159s，原whole4=4P/0skip、47.829s；16:09:36Z单TEST S/Z SOURCE STOP。无Game/生产来源审计恢复 |
| Scope尾部deadline | 模型提出scope正常返回后额外`requireTime` | owner只取这一新调用；原diff行号/长上下文有误，未整段套用。D javac0/4.156s，whole63由62P1F到63P/0skip（22.933s）；S/Z SOURCE STOP，不在Main318。两个新回归为owner先写；writer异常优先级保持 |
| Catalog/config phase | 模型提出两个实际后阶段独立fresh deadline | 原patch误把private finish当public，owner只提取窄语义并加实际三阶段共用的typed seam。严格javac0/3.738s、原3行为3P/2.377s、S/Z SOURCE STOP；未凭3P授同Game安装通过 |
| 恢复entry-only日期负例 | 模型04提供真实Win32 Peer/Writer/HELLO/date/canonical流程，05纠正命名/afterDigest | 04真javac1、05仍留一个head.state API错误；owner一表达式纠正后javac0/3.447s、单例1P/19.129s、S/Z TEST采用。04/05均非原样独立通过 |
| SDK saved物化 | 02生命周期hook及03 helper主体部分用于最终实现 | 02严格javac0但whole10=8P2F；03实际不可达catch编译1；最终copy/move/cleanup及六tests为owner，whole10P/1.860s，三叶S/Z SOURCE STOP。未执行已取消的04，不为完成需求补调用 |
| Warm writer复核 | 01循环退化；02仅36输出token的限定NONE分析被接受 | 模型02新代码0。APP4P与writer4P是两个cohort；最后三生产叶是既有owner候选，不追认为模型02原创或一次whole8 |
| Registry大UTF8回归 | 03单新method采用，owner纠正实际UTF8大小及浮点/整数种类断言 | strict单TEST0/1.448s，新方法1P/0skip、tool1.455s，S/Z TEST SOURCE STOP；原生产4P未重跑。owner命令中未引用`#`导致的首次参数失败另存，不算候选错误 |
| War H1原生缺backend | 首轮生产hunk原样采用；TEST由owner纠正API、负例及2.47MB原生帧输出lane | 三个H1消费者通过、whole4=3P1F；独立LoadedProof预算孔未闭，不称whole绿。生产及TEST S/Z采用，未授Game资格 |
| ContactScope分支合同 | 01静态拒绝；02三个生产叶的Optional与分支严格合同实际采用 | 两fixture literal及既有TEST覆盖为owner；7源javac0/2.289s，NT原三类whole10P/0skip、3.247s，6叶S/Z SOURCE STOP。Root FS行为未验；95KB输入不是实际改写规模 |
| Combat原生合同 | 首轮5操作可用，三个生产叶原样采用、owner重写0 | 3prod+CacheTest javac0/1.989s；新增TEST另有3个实际语法错误而未采用，消费者完整闭环仍待，不能以生产采用称全任务通过 |
| Successor queue signed | 01改公共record ABI、02仍留positive谓词，两原稿静态拒绝 | owner据解析方向做8窄操作保ABI，baseline1P2F到原whole17P，3叶S/Z SOURCE STOP；不是模型02原样通过 |
| MCP bridge诊断 | 首轮生产3操作加owner decode顺序纠正；03返回窄TEST再加owner两处纠正 | strict3源0，6个不同测试通过，双叶S/Z SOURCE STOP。01/02错误TEST未编，不能记自主测试成功 |
| Lifecycle public result | 01 API/节点类型/数组断言错误拒收；02两hunk原样、一个显式null边界由owner纠正 | strict TEST0/1.682s，原whole7由5P1F1E到7P/0skip、2.277s；仅TEST S/Z SOURCE STOP，生产0、Game0 |
| 历史批读P0 | 模型提出batch及Journal两consumer结构；owner修模块/锚点、序号、有限不可变集合及末尾exact pins/absent，保旧single API | 最终javac0/2.630s、新adapter2P/4.453s，3prod+新TEST S/Z SOURCE STOP。较早prior-head cohort另2P/115.010s，不能混作最终性能证明；实际71链由runtime后续同Game验 |
| Fresh proof相邻去重08 | 单代码hunk采用，owner仅纠注释说明两个真实caller；原分析漏识第二caller | 两consumer严格javac0/2.596s，Fresh单叶16:14:00Z S/Z SOURCE STOP；新hunk JUnit待FS，旧1P不追认新行为，更不声称125s实测加速 |

所有采用归因区分模型原样操作、模型方向后owner纠正、owner自写测试和仅独立复核。S/Z源码采用、隔离软件回归、主构建产物、同Game运行分别记录。

## 失败经验

- 单源PE capture helper两轮都不是正常“只差末尾”的截断：7000/16000输出上限分别出现约1150/2650次重复 `import java.net.*`，没有可用class/FileChannel实现，JSON未闭。两轮语义采用0；不再靠增大token重发整类，由owner接管共同原生输入。后续若探索，只交真实窄方法及精确record合同。
- SDK current退化暴露调用器自己的边界：后继请求必须显式设置正数有限max_tokens；流式读取增加180秒无字节及900秒总期限。JDK收到headers后的InputStream读取不能只依赖原HttpRequest timeout。它们只限制模型HTTP执行，不恢复任何游戏启动/来源审计门；有限输出预算不等于永久限制模型任务难度。
- NormalExit两轮均把`StrictJson.canonical`的`byte[]`交JUnit `assertEquals`；第二轮还错误声称存在自动内容比较重载。两次均静态拒绝、未执行。唯一4P来自owner明确改为`assertArrayEquals`，不给模型修正信用。
- Council第一轮发明API并误处理Obj/ObjectNode；第二轮length；第三轮两个call edits可取但helper仍错。owner helper/fixture/测试与模型调用插入分开记录，不以HTTP200算完成。
- M2 paired factory两轮忽略真实TU/匿名namespace可见性和精确路径反馈，均未编未采用，owner接管4个窄hunk。不存在“HTTP200且JSON完整即Native可编”的推论。
- Actor首轮适配器只检查两个键并静默丢字段，违反exact role/类型合同；Registry大输入TEST候选存在Java保留字、错误text block及字节数组比较；War H1第一轮生产操作可取，但TEST包含不存在API、删除absence回归、把合法seq10当非法等。静态拒绝与实际javac/JUnit失败严格区分。

方法分派继续提高复杂度和实际采用倾向：完整相关源码仍保留，输出优先有限JSON操作、目标方法或多个精确hunk；较复杂任务分轮做生产与真实测试，而非要求模型反复输出大文件。真实诊断返工不改变当前源码以追缓存；已由owner完成的工作不再伪装成模型首写任务。

### Controller→DEFERRED复杂任务的实际扩展

首轮提供14份当前相关合同/源码，83,581输入token、10,949输出token，HTTP200/stop、TTFT13.758s、总108.415s。实际候选是一个51,183字符TEST文件，含7个@Test（复制原6例）和9次直接Journal.commit，违反要求的单例真实Controller producer边界；Clock推进/空planner/observer逻辑也不能触发目标post-planner预算End。实际修正harness依赖后仍有6个候选javac错误，未执行该7例或FS。输入83k不等于模型完成83k改写。

将实际编译诊断和具体语义反馈放在最后，稳定前两消息不变，第二轮83,929输入、3,395输出，HTTP200/stop、TTFT10.962s、总31.064s；原件`model-coordinator64/controller-deferred02`。第二轮收敛为一个@Test且无手工边界commit，但实际javac仍7个错误，未执行FS。owner窄修当前API、baseline/facts与真正Blocked预算边界后D javac0/3.369s，尚无行为通过。第三轮prepared请求在POST前取消，避免挡住生产P0；不把长JSON或第二次stop计为复杂集成能力通过。

原生fixture首轮后审还受输入时序限制：输入混列pre-edit共享Event与post-edit owner D，且未给当前Frontend的7577B/3.11s独立观察；首轮不能全部归因模型。新增采用0、实际`Thread.join(5, TimeUnit.SECONDS)`在Java21编译失败，真实来源/HTTP量测及公平边界见[原生fixture后审](local-model-native-fixture-postreview-2026-10-30.md)。准备中的纠错与已POST严格分开。

中央`OWNER-REVIEWS64-01.json`已由统一锁writer追加到原调用日志，包含原样采用、部分owner纠正、静态拒绝、真实javac/JUnit失败、取消未发等分层结果；原HTTP结果和错误候选从未改写成成功。后继group lead各保独占2HTTP执行slot，直接交sole owner，不把中央逐叶ACK作为执行前置。

本文仍在更新；当前Game/业务进度由运行岗记录，本协调岗未执行游戏动作。
