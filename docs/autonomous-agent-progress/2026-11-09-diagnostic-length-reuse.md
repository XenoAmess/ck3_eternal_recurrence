# P172：诊断 DATA 构造只取一次包长度，限定源码采用

本次只在 NativeTransportDiagnostics.ReceivedSnapshot 的 compact constructor 取一次包长度，免去仅为第二个长度比较而生成的防御副本。Root 根据完整公有 observe 首32与功能证据，批准限定的软件分配优化源码采用；不授整体 worker／端到端／CPU 提速。本记录切点软件基线为 current352，后继生产353须另有正式 SHA、manifest 与 Root 实际软件采用回执；测试 runtime 的 Test＋352＝353项不是生产353已采用。Runtime、Quarkus 装载、Game、P100及SAVE仍独立，没有新增保存信用。

## 一个构造行，原校验与所有权不变

现有受管 NativeTransportDiagnostics.java／source307 整叶8220B／`8e1596d7ec0bdaabf1eacdc92bf34c689d5f42299204cbb4e1643e076a1fa29b`，候选8257B／`517668280f3cbae3e4db9771a98b9d2765b35fa00bf63aa34e65774e4edcc5c9`，89行保持，仅第26物理行变化。整叶逆向精确还原 formal8cb／source307；整个历史C0编译来源仍UNPROVEN，精确源码对应及选定实际构造／getter Code是分别闭合的事实。

原 session 非null→positive(ordinal)→packet 非null→observedAt 非null 顺序逐字保留，然后在原首次 getter 位置取得 `int originalPacketLength=originalPacket.value().length`。原 `>=5 && <=MAXIMUM_FRAME_BYTES+4` 两个界、短路、StrictJson.require、原消息与隐式四字段赋值顺序保持。int不保存raw引用，临时数组取完length即可不再由局部持有；没有新增field、type、public API、helper、cache或跨调用 Guard 结果复用。原fields()、positive／unsigned、Bytes ctor/getter、parser、hash、oldencode、Fingerprint等方法体不改。

Actual NativeWire.Bytes 为final record／private final数组，构造防御clone、getter仅clone，外部数组或getter返回值不能改变其内部长度；不依赖回调、provider或任意可变getter。静态Code中有效长度原getter在PC25／34两次，新构造只PC25一次，短于5的旧／新路径均一次；这是Source／Code推导，不冒运行getter计数。省掉的分配和OOME发生时序自然可能不同，不承诺所有资源失败等价，不以减少Guard、fresh I/O或权威检查取得收益。

## 首次必要编译与完整接收边界

生产唯一1TU10从首编使用 `-g -parameters`／Java21，exit0 accepted、实际全10；9个类逐SHA与旧完全同，仅ReceivedSnapshot.class变化。字段、旧API、hierarchy、Nests、decoded MethodParameters保持；原四前置检查与字段赋值由实际Code核对。P172没有复编Wire、Transport、旧SDK或Main，也没有新增结构字段；即使单方法体变更，仍不据此授实际Quarkus body热替验收。

必要新离线Test1TU6／soleJUnit1P／0F／0E／0skip。真实XML Jupiter engine **4.992s**，唯一testcase **4.964s**；早期消息把engine叫case的标签不沿用，原XML／raw不改。Test精确37206B／`0e0280b88840f9fa415499ad1e5144e68198d3c5c681b1d082deacabd902aaa0`放tools/performance/diagnostic-length172，依赖五个显式props及已资格class根，不进默认Maven自动Test，不改pom／隐式skip。

两侧完整own36：第一URL共同使用已采用P171 prod02 Transport26（Top SHA3143b501…），第二URL分别是A旧Diagnostics10／B新Diagnostics10。严格白名单、每类CodeSource／SHA与根核对，72个loaded origin记录对应46个独立物理文件，不能说72独立文件。父CP仍current352，B Diagnostics不前置污染父；Production／RejectedSnapshot／ReceivedSnapshot改为own公有getter逐级遍历并assert child类，不能套用P171的父Production强转。Bytes／Endpoint／DriverJson／DTO仍父共享，不mint私有issuer。

直接重放已资格P164原framed STATE：3400700B／`4084dcb52ed1ecafadf7fbe6fd11998ff2ed2c06fd22ac077025e519044e4e5d`，native:2／revision2／date53144328，opaque_unconsumed_extension3400000字符。性能原包不重新encode，不扩大N或从该opaque尺寸推自然频率。两个持久实例，固定首8ABBA32、各16；setup仅HELLO，0STATE目标预热／0额外observe。实际每次`observe(Instant)`都新ReadFile53次／3400700B／guard60次，原32端点、typed完整raw Obj／原包与stateSHA、canonicalSHA、token与actual引用、new chronology order2…17／publicrev2、时间与所有post通过。相同字节不是同次接收，旧token只接受其identical原frame。系统UTC与custodyUUID只侧内核对，不强迫侧间字面相等。

另20功能observe与原32合计 **52**（A26／B26），6HELLO-only、10功能行、6公开close：first／equal／change／ABA／date拒收／恢复／nativeRevision回归／secondHELLO／关闭后拒收均通过。接收slot清零本身、owner miss／node-null、uint64 overflow与fixed-clock只Source／Code证明，不伪造private状态。底层共同P171 node仍有原固定codec与跨capture存活边界，两侧一致，不算P172新增收益。

在32及既有功能之后，另有 **6对DATA ctor检查／12次直接公有构造**，不计observe：session null、ordinal0、packet null、observedAt null、length4拒、length5接受。所有异常类／完整消息相同，成功保四字段原引用。ordinal0先于packet/time错误、time null先于length4等可区分；packet与time两null都为无消息NPE，单凭动态异常不能分辨哪一个，原Code／源码顺序佐证。Bytes防御性与上界MAX+4仍preflight／source-only，没有冒mutation测试，也不新造65MiB输入。五个零字节只被本DATA构造接受，绝不授NativeWire合法帧、实际接收、token、readiness或权限。

## 全部首32指标及不利结果

| 每调用指标 | A | B | 限定观察 |
| --- | ---: | ---: | --- |
| 分配均值 | 138735982.5 B | 135107422 B | −2.61544% |
| 分配中位 | 138506008 B | 135105288 B | −3400720B／−2.45529%，8配对全降 |
| target observe wall均值 | 47.52041875 ms | 35.20780625 ms | −25.91015%，冷首影响保留 |
| target observe wall中位 | 36.9949 ms | 33.9622 ms | −8.19762%，6好2差 |
| CPU中位 | 31.25 ms | 31.25 ms | 粗量化，不授因果比率 |
| enclosing整行均值 | 78.8347625 ms | 79.474525 ms | **＋0.81152%** |
| enclosing整行中位 | 66.5609 ms | 68.2814 ms | **＋2.58485%** |

target两组反向cycle3／6的两调用B−A合计 **＋0.7546／＋0.332ms**保留；A首192.2116ms及全部冷首／outlier未删，均值下降不能全归机制。首A分配142201056B高于其中位138506008B，额外归因UNKNOWN；稳定约3.40072MB与移除同call clone一致，不据Code调用数假造动态计数。

**row25 B的target31.9174ms，整行却235.7141ms**；其后验／准备外开销不能藏掉或当作target，不能用6好配对把整体worker说成提速。CPU只有15.625／31.25／46.875／125ms四值、全部非0；配对2好／2平／4差，中位相同，累计500／468.75ms仅描述，causal百分比UNKNOWN。两侧整行和target分别列出，不改变已声明的完整observe目标边界。

Root以全部功能／稳定8配对分配下降及原target非material退化规则批准限定allocation source采用，不是整体wall或每次输入收益证明。没有加暖机、追绿重采、删冷首、扩大N、JFR或fullcase。A-first、共同父JIT／codec、同进程GC与检查后的预热偏差均保；不能把本次与P171时间拼成因果。

## 全费用、保留与内存边界

setup至首目标2.0086071s；32target wall合计1.3236516s、enclosing合计2.5329486s、packet准备0.008958s；observe功能0.0393072s、额外DTO0.0029228s，before-report4.5964505s。packet clone／offer、完整raw／canonical／SHA／身份／heap后验在target外但enclosing／全case内；报告序列化、写出和JUnit尾部不在before-report中，不能说该数是完整交付费用。

共享heap在32前31466264B、后330935184B，committed389283840B；GC计数2→72、时间26→272ms。两持久实例、原包／完整typed oracle与post分配混在一个heap，不能按侧归因，也不授峰值或OOME安全。没有强制GC；P172 local int不保留克隆array，但不能将分配下降推为整体peak下降。metadata1688216B＜4MiB，actual JNA273408B及全部tmp计入，3.4M原packet外置只读、不复制成metadata。

Native已知切点 **04:02:33.112227Z→末CLOSE04:20:31.703844Z＝1078.591617s**，至qual04:23:46.464488Z＝1273.352261s，更早Root／研究起点UNKNOWN，非0。旧消息误数581不作为本次完整准备耗时，原件保留。三VM actor19.0069191s／operator26.4633167s仅资源子窗，不能替代全部研究、read-only证据、D源／36loader适配、审阅、配置、等待、报告和结算。三个VM均真实exit0accepted／CLOSE／fenced释放，未额外试跑；准备、冷暖、反向与所有原件都保。

外置existingempty reportRoot／CREATE_NEW≤256KiB／NEVER、原primary失败加cleanup suppressed规则保持。公有软件Endpoint／Api并非真实Game/pipe，未发WriteFile、HTTP、P100、GET、部署或SAVE。所有旧PARK保留；零新增确认保存日，不报有限秒／日。

## 具名来源

- `N/p172-diagnostic-length-test01/reports-component/p172-diagnostic-length-public-observe-fixed32.json`：75585B／`f10c22d5a46401cb0f62a9d58fbb24f12351688b387014fa8645cb140a2056d9`。
- 同根`QUALIFIED-P172-FIRST32-PUBLICOBSERVE-DTO12-ALLCOST01.json`：61534B／`ea132e20cb36be0702765716c3f4111644f579f85c3ba67bf17e3c077bdd0939`，Root131次引用／111独立原件实核。
- `N/p172-diagnostic-length-prod01/QUALIFIED-P172-STAGE1-ONLY-TYPING10-API-CODE01.json`：32480B／`66c04a2c0619c154b21e0b22d4923a8855e9fa8917502515bf3cc0d35539112e`。
- `R/P172-ACTUAL-FIRST32-72ORIGINS-DTO12-AND-LIMITED-SOURCE-ACCEPTANCE01.json`：15871B／`d8775d4d7a92d482f11015554bf90c6d964cd8fd129c07985793648759bf9ba3`。
- `J/construction-diagnostic-length172/OWNER-ACTUAL-FIRST32-DTO12-SOFTWARE-REVIEW01.json`：9236B／`f2fad97fcb731746e45929c4a09d91b98a9faae6c15b6dd4ff3047aee52454eb`。

N／R／J是本机具名证据根，不把来源路径当当前Runtime或权限。正式源码、有限软件实验、软件353采用与Runtime继续分账，后到状态另件，不改写本切点。
