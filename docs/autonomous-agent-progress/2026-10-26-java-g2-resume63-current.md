# resume63：REA、Java 全能力迁移与 G2 接续

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26T14:50Z 实时记录；执行仍在进行。本页接续 [resume62 交接](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff.md)与[来源索引](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)，不改变历史失败。

当前目标是研究并使用 REA，完成 G2 M0–M7 的原生研究和 Java 落地，完成 Python 能力迁移后使用 Java 继续普通自动游玩。[完整迁移与八 M 对照](2026-10-26-resume63-migration-and-g2-matrix.md)区分八个业务门槛与 Python 全功能范围；两者不能互相替代。

以下原表保留14:50Z及其后各次观察；最新状态以前向时间记录为准，不把新结果倒填到旧cut。2026-10-27 00:00（Asia/Shanghai）已跨日，午夜后事实另计27日。

## 已确认的基线

- 本轮实际执行 `py tools/ck3_live_run_id.py machine`，机器与交接相符；14:35:37Z 重新读取来源索引全部43份原件，大小及SHA全部MATCH。
- 复用交接的同一SRC、BUILD、m2与TMP。Host实测默认Maven3.10.0，原构建锁可取得并立即释放。没有每次修错重新复制源码或重建全部输出。
- 存储协调者读取实际 `Z:/.codex-task-bus`，新财务181与task-start回执在 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/capacity/`。采用完整旧hold保守上界；新增预算有明确子分配，不以空闲截图取代执行准入。当前复核期限16:40:26Z。
- 后台WMI观测存在多个CK3进程，但本轮尚未核实其完整身份和所有权；没有接管、终止或新启动。本轮新增游戏日与保存均0，Java完整G2业务仍0/8。

## 并行工作与下一门槛

| 工作包 | 本轮变化 | 下一门槛 |
|---|---|---|
| REA框架 | [真实源码与可执行方法](../rea-ck3-research/resume63-framework-workflow.md)已记录；复核23份旧来源。统一后端准备0x1D64290的有限查询 | 实际字节/CFG与独立解释；不重复全PE导入 |
| Host/SDK | MavenArgumentFile及其测试两叶已精确采用；v2 config仅属性，其余argv走CLI，保v1 | 实际增量编译、默认mvn离线POM回归、完整Tools VERIFY，随后LS与SDK完整step |
| M1 | 派系Known读取接共享语义槽的10叶已采用，加入真实source冷清槽/原件重放测试 | 编译及原APP/LS整类实际运行；自然继承重绑另验 |
| M2 | 首显示项处理三叶已采用，测试显式分开public/native revision | 原生产链整类；failed READ→journal→scan完整接续仍有未采用叶 |
| M4 | CASH刷新类型贯穿五叶已采用；同帧ROOT收入fallback正在补迁 | reducer/生产集成实际回归及原M4业务 |
| M6 | 活动对象消失后读取既有原生终态journal的五叶已采用 | 实际transport→归档→重放回归；四类业务分别实机 |
| M7 | cap四叶20操作已采用 | 实际cap回归；真实恢复后完整ordinary plan，不能只验replacement snapshot |
| M0/M3/M5 | 终战跨WarID归档、同Game自然继承Family闭包、婚配receipt日期接续各自正在独审/采用 | Host模块增量与真正consumer回归；M3用JFR定位已知过期而不放TTL |
| Runtime | 同Prepared FILE_REPLY及RootInvocation/v5分开施工，补原producer→全部consumer | 完整源码、测试及真实受管入口；不得伪造Session或独立issuer |
| Native | 四模块曾101/101；随后类型修正后的重跑实际100通过/1ERROR，暴露链接器删临时文件与容量枚举的竞争。已做窄修，最终回归待执行；strict仍有旧债 | 最终完整软件回归、实际修改范围类型、持续CI、Java UAC候选编测与实际设置读回 |
| Delivery | 只读恢复SRC/i61真实差异；保用户477B配置与原POM赢家 | 小型独立文档包先交付；最终图仅一次增量对齐，不提交未验源码 |

源码采用、软件测试、完整构建与实机信用分别记录。上述Java新采用项尚不能记为本轮测试通过。Tools旧完整失败、LS75不完整、M3五项失败、Cold17超时均保留。

14:54Z补记：原S26 Shared在子进程启动前拒绝新REA请求，原因是历史completed工具来源递归重验已被合法CAS更新的mutable容量head。没有新230B字节或REA后端结果。已安排共享历史读取最小修复；开发增量改走已有默认Maven、只读研究改走官方REA入口，分别记录实际命令和范围，不授旧Shared成功信用。

15:23Z前向结果：官方REA直接路径已实际完成230B/48指令及119B/35指令两题，局部CFG分别5块6边、4块4边；两题按各自新窗口闭场，第二题独审仍在进行。第一题返回被调结果低字节、第二题只规范AL，不能解释为兵力或胜率。原Shared失败保持。

Java原八整类实际两轮均未全过：第二轮68通过/1失败。随后查明默认Maven启动脚本额外运行一个未展开MAVEN_OPTS的版本探针；测试恢复与生产相同的双环境预算，保持384MiB，原失败方法真实通过、内层峰值238931968B。见[具体诊断](../maintenance/2026-10-26-default-maven-jvm-probe-memory.md)。完整Tools仍待后继，不拼接测试数。

首49份文档包已普通FF推送 `e735f2a0ed56e666e5f5d0977a7e532ff861f23c`；Linear history成功，Official Runner尚在运行。Native交付前发现旧工作树落后主线，改为fresh主线前向移植helper两叶；fresh四模块127/127软件通过，原CI另有三个消费者测试，完整step还在验收。既有主线configured实现和两项同义回归保持，不用旧源码覆盖。

## 执行约束

Host唯一写BUILD/m2及build-tools，各领域按精确源码文件分工，capture前协调短冻结。REA由单一后端执行岗采样，八M共享原件并独立解释；不按人数重复重分析。原Genesis已真实创建，禁止重新初始化。Steam确认只用后台原生回执，不抢焦点或自动联网。

本轮实际总线任务为 `ck3-java-g2-rea-resume63-20261026`。仓库原有489项dirty不清理、不整体stage；现有Git index约10.6MiB，超出小型预算，Delivery从新鲜origin/master保留未改子树，通过Git树对象交付明确文件，普通fast-forward push。源码和文档交付commit/CI终态随后追加。

## 2026-10-26T16:09Z 前向接续（本地27日00:09）

- Tools accounting修订的受影响11整类实际112/112通过，exit0、72.3101985s，重编2 main和1 test；独立核验保存在 [ACCOUNTING63-AFFECTED11-INDEPENDENT-RESULT01.json](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/ACCOUNTING63-AFFECTED11-INDEPENDENT-RESULT01.json>)。不能将此前68通过与单例重跑拼成这一批。
- v5/R34先局编实际重编5 main、3 test，7.4593416s、exit0；随后13个整类实际121/121、零失败/错误/跳过，191.7773433s、exit0，这次没有重新编译。325个源码pins前后匹配，独核为 [V5-R34-AFFECTED13-INDEPENDENT-RESULT01.json](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/V5-R34-AFFECTED13-INDEPENDENT-RESULT01.json>)。它与112是不同测试选择，不能相加冒完整Tools通过。普通Jar82也仍属于较早cut。
- M0六叶、M1十叶、M2二十三个唯一叶、M3自然继承十叶、M4五叶、M5日期接续八叶、M6六叶、M7七叶及FILE_REPLY六叶均已有源码接续；四个零JUnit helper同步改名为Assertions，LS标准test-jar POM已采用。各自精确范围见八M专题及[FILE_REPLY记录](2026-10-26-java-g2-resume63-file-reply.md)。领域编译和JUnit仍须实际执行；Host只清理adapters-storage/local-service两个模块，不-am clean，不清m2或其余缓存。
- R34旧计划把S26 receipt SHA/大小写死，Source/ENV/BUILD/inventory多处也正确要求同一实际producer。选用现有 `NativeCombinedSourceCut.sealExisting`：最终新Tools实际qualified后，对同一native源码树生成新来源控制原件，再用原ENV、缓存BUILD及inventory生产链接续，不热改Source15/ENV22/BUILD24。新的UAC v2候选仍待编测；Root独审已指出两处public CLI分派只认v1，修复必须同时到达这两个真实调用者。121软件通过不授新qualified carrier。
- Native在fresh主线前向移植后的四模块实际127/127通过；configured两完整叶strict通过，helper只对明确提取的修改范围strict通过。旧helper全模块201个错误是旧cohort事实，不能写成新全模块绿。原CI三个SDK消费者本包未执行，官方步骤保持。[原件及边界](../handover/2026-10-26-java-g2-resume63-native-helper-review.md)。两helper和持续CI hunk已FF推送 `7ecb8b1d10b88eeaed389ca76251eb5d679c652e`，configured生产叶保持fresh原样。
- REA两题230B/48指令与119B/35指令均已有独审，第二题另建独审记录，原close的PENDING不改写。[实验记录](../rea-ck3-research/experiments.md)维护具体引用、成本、opaque调用和未知。第三题只准备 `2B9D260` 的当前RF metadata及最多64B前缀，不预设包含关系，不自动追callee。旧 `28BFCD0` 完整103B与 `A11F60` 模型优先复用。
- [后台只读核对](../handover/2026-10-26-java-g2-resume63-runtime-readiness.md)已辨明三个旧CK3 generation的kernel handle均signaled，不能因WMI仍列PID或exit code259称它们仍在运行；其EXE路径查询失败仍为UNKNOWN。现存operator只绑定旧Python job，不是新Java路由。Genesis两份719B原件身份未变，仍seq0，未重建；SERVICE/新Java运行组装和实际权威尚未成立。
- 普通SAVE由真实Root普通动作后产生，不是可以预造的初始DATA。起步准备与M7恢复验收按真实顺序安排：完成必要迁移及运行资格→首场普通动作→canonical SAVE→public RESTORE→同高级意图的完整ordinary plan；不得将首场尚不能产生的SAVE设为循环前置。
- 官方CI `40345540217`（e735文档包）实际FAILURE：bootstrap与qualified Tools各636/636通过，但 `ControlCi.runQualified` 缺实际fixture-production request，在full parity前明确NOT EXECUTED、child exit1；并非编译失败。实际新SDK和完整cold/warm仍未执行，已沿原生产链修入口。`7ecb` 官方CI截至本记录仍未取得绿色终态。

Root已明确授权新的有限容量review至2026-10-26T17:40:26.824464Z，原quota和总hold保持；发新财务/执行卡前鲜读卷/RAM与实际基线，不追认或延长旧卡。任务总线15:59:17Z heartbeat为9027。午夜报告另按实际时间收口与建会。

本轮新增游戏日0、SAVE0、RESTORE0，Java完整G2仍0/8。下一门槛是实际领域编测、新Tools完整验收与SDK完整step、原生后继及设置读回、真实首场Java权威接通；当前继续执行，不以文档、普通Jar、构造器或ACK授业务完成。

## 16:43Z 前向结果（本地27日00:43）

compile87实际26.056s退出1，五个模块尝试重编，唯一错误是M2 ActionPorts缺Optional导入，后续依赖未执行；compile88修复后实际139.8657807s退出1，APP/存储/transport及LS606个主类编过，唯一测试编译错误是M1 callback未处理IOException。两次真实失败保留，分别窄修显式导入与保cause的UncheckedIOException。

compile89在同缓存实际39.7115206s退出0；compile90加入首次selected-registration生产入口后实际28.3738348s退出0，source5855前后MATCH。90实际只重编APP一个测试、transport一个主文件、LS一个主文件及两个测试文件；reactor列34不代表34模块全部重编。原91只有42选择器/43个module-class元数据，未执行测试；LifeAdvance同FQCN分属两个模块，后继结果必须按模块分别计数。

首次selected生产链已补具体file-driven工厂，不再留外部不存在的类名；同时已将i61用户477B application.properties精确复制到开发SRC，i61原件未写。最终资源字节将随新源码接受后续编测，不能拿旧363B产物授最终图。采用回执为 [FACTORY-PROPS92-SOURCE-ADOPTED01.json](</D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration/FACTORY-PROPS92-SOURCE-ADOPTED01.json>)。实际selected正例仍需真实NativePlan/profile、capability路径后继及独立issuer绑定，见[完整生产顺序](../handover/2026-10-26-java-g2-resume63-ordinary-root-production-chain.md)，不能由base5或编译替代。

新DEV27已由原public producer实际accepted，FIN183及其资源卡按17:40:26有限复核窗口继续，未自动延旧26卡。中断恢复后读回90真实终态、确认91未启动，再继续同缓存；不因观察中断而重启已完成命令。

REA C4新64B与旧64B拼接后，M5以原字节、ModRM、分支及数据流独审了69B/21条可达指令、10块12边、两个RET。无故障正常路径AL=(A/B均非FFFFFFFF且相等)，完整EAX仍含B高位；字段含义、外层caller和缓存时效未闭。采样整体迟闭场78.399s及Rizin的omj错误仍是RED，不授128B双解码通过。见[独审记录](../ck3-native-ai/2026-10-27-m5-rea-callee2b9d260-normal-path-resume63.md)。M1下一题已按[实际成员写入seed](../ck3-native-ai/2026-10-27-m1-member-validity-followup.md)排队，先当前RF/cache，再条件补缺，不把局部writer冒自然继承caller。

后台Steam预检于16:37:51.621899Z实际确认offline=true，原CLI760ms/exit0，绑定当前Steam PID/出生时间、版本及SteamUI来源；没有窗口操作或模式切换。[新回执](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/steam-offline-resume63-precheck01.json>)2480B/SHA43d9d3f9606f6068079893b109cb1facf96cfaa3c6a6855acecd8ccf679b774a。它只证明当时状态，实际Game启动前必须另取新鲜准入。

文档包后续FF为a9d621fdf19bb2914aaf3559b4f0c2bcd63196d0、午夜六件af523899475246d62963956f4cb635cf9f614dc3；fresh remote后有同事的d42bb259055e62ba430675ad7e9cec684cccf493，未用旧root覆盖其增量。7ecb官方Runner40351720817也已实际FAILURE：两段Tools各636通过，仍缺实际fixture-production request，configured后续step未执行，不能称整CI绿。新鲜hosted初始化缺口已单独记录，不为本轮局部编译扩成平台重构，也不阻塞本机合法Source32的实际验收。

截至本段，最终四叶/477资源的后继编测、完整Tools/SDK30、SERVICE、原生后继与实机仍待执行；本轮新增游戏日/SAVE/RESTORE继续为0，完整G2为0/8。

## 17:17Z 前向结果（本地27日01:17）

machine_id仍为`xenoamess-full-tower-eb9d2c1186`。93批受影响测试确有失败，且内层Maven退出码因外层结果处理错误丢失：新鲜XML共213项，194成功、18失败、1错误；24个模块类未执行，不能补成通过。94局部123项中其余八类103通过，APP Life仍4失败/3错误；窄修测试fixture的实际完整材料读取后，95该APP Life整类20/20、exit0、14.4344s。旧94 Life XML已被95覆盖，仍保日志/旧exact ref，不能冒称旧XML可再次读取。

96继续未执行类时，NT3三类18/18通过，APP Life20再次通过，建设reducer13/13通过；LS Life26项全部错误。该批达到600s超时，随后只停止同出生时间/父链的自有Surefire，已核实本树全部handle signaled，源码5856 pins前后MATCH。11份实际XML共106项，55成功、11失败、40错误；14类未产生XML。原始超时、失败与未知分别保留在[96终态](</D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration/AFFECTED96-CANCELLED-FINAL-CLOSE01.json>)，不重跑整批。

已有源码归因的最窄修复已采用：Large测试三处大材料解析改用生产材料同一4MiB上限；LS Life的watch战争原包补真实合同必填player_side；中央AWIF在明确active_new的软件辅助状态补episode_identity_pending=false。Native包、生产parser、TTL及原26断言均未放宽。97于17:16:05Z开始同SRC/BUILD/m2/TMP的`mvn -T2 -pl local-service -am`受影响测试：Runtime七类、建设两类、LS Life，加依赖中同名APP Life共11个模块类；本段时仍运行，尚无通过结论。M0归档/PublicCheckpoint的超时及M2 Unknown/Mcp的独立fixture缺口另外诊断，不随共享修复自动变绿。

用户指出有效并发低后，已撤销前文“REA单一后端执行岗”的本轮调度限制，改为最多四个独立官方REA/Rizin provider并发，由Capacity根据新鲜RAM/commit与各自PLAN/最小close分槽。M2事件caller、M3继承分支缺失111B、M5互动predicate106B、M6四个已知候选委托694B及REA岗M1 gate在四槽内轮转；不为人数重复采样。M0复用已持context/answer ABI缓存准备最小原生观测接入，不占采样槽。M4/M7已完成具体夹具修复后释放源码短窗，Host仍是唯一Maven输出writer；互不冲突的Native target构建可并行。对应方法见[四槽raw研究方法](../rea-ck3-research/resume63-parallel-raw-method.md)。

REA已完成M1成员writer的1766B有限主体研究与独审：普通分支具有两道门，但特定incoming flag可绕过，不能据局部writer授持久成员资格或自然继承完整caller信用。C4字段依actual4生产源码合同可收敛为同有效邦联ID比较，当前build的named getter注册仍未补证。完整八M原生树和全Python迁移均未完成。

Root有限存储复核新授权至18:40:26.824464Z；不自动续旧执行卡。17:16:39Z任务总线heartbeat序号9033。新的Java CK3启动、真实新增游戏日、SAVE、RESTORE仍全部0；下一步是97局验、恢复测试JFR真实归因、完整Tools/SDK及原生后继，再进入首场Java实机。
