# P175：公共诊断 capture 的本次副本复用，限定软件分配源码采用

Root批准本次窄源码的allocation-only软件采用。测量目标仅`BridgeDiagnosticsCapture.capture`，不是成功Report／encode、observe、完整worker或Runtime。完整功能通过且8组分配均下降；capture墙钟4好4坏、外层中位反向及CPU描述性上升全部保留，不授稳健速度、CPU或整体延迟收益。本发表切点软件仍actual current355；后到356候选须正式SHA、manifest及Root独立实际采用，不预填装载、Runtime或SAVE。

## 两行生产差分与来源

[NativeTransportDiagnostics.java](../../java/ck3-control/native-transport/src/main/java/org/xar/ck3/control/nativebridge/NativeTransportDiagnostics.java)基底是已采用P174的8255B／`e94ff2ddd6acb3bad17344e25a9e051ae8e3e74c3728b922f198b89db190e4b7`，本次8264B／`9905db4e0e962f0ccb7673909d9fe5b970873bfbf86f08288c5ac4b031bc46a5`，89行不变。只有fields()原28／29两行：原首个`originalPacket.value()`产物放本方法local byte[]；`originalObject`及后续payload copyOfRange均读这份私有副本。整叶逆向精确回formal8677／P174；构造26、所有其他helper／parser／Guard／token／hash／oldencode与错误顺序逐字保。

实际Bytes是final record／private final owned array，原ctor及getter仍防御clone。originalObject只读首副本的length／LE头，向NativeWire.parse传新body副本，不修改、返回或交给外部回调首数组。首getter仍在旧operand位置，originalObject失败仍先于payloadcopy。没有新field／type／publicAPI／helper／cache／carrier／trustedflag，原native checks与fullparse未删。正常标准不可变DATA域下，每次完成fields的getter副本从3降至1；这是源码机制，不是观测到的运行调用频率或精确总分配功劳。local首数组可能跨后续fields工作延寿，原分配／OOME时序自然改变，不宣称峰值、GC或全部Throwable等价。

必要生产1TU10以Java21／-g／-parameters首次真实0accepted，CLOSE06:07:45.199505Z。9个其他class逐SHA与P174完全同，仅ReceivedSnapshot5767B变化；旧字段／API／参数元数据／Nests保持，fields以外的8个旧方法Code保持（构造及另外7个方法），fields实际getter3→1、其他callee次序保持。整个历史C0 compiler-source仍UNPROVEN；精确actual class／选定Code与formal源绑定，不把FQName授为全C0来源。

## 精确公有目标与实际接线

[DiagnosticFields175Test.java](../../tools/performance/diagnostic-fields175/DiagnosticFields175Test.java)是44884B／`e505f44a398d66caf0e7f33b157bfd51ae37efd765832cd345950b93d916499a`，显式tools/performance离线入口，不进默认Maven自动Test，不改pom／隐式skip。必要新Test1TU6、soleJUnit1P／0F／0E／0skip，testcase **3.797s**／Jupiter engine **3.826s**；无旧生产、Transport、Wire、DTO、Main或SDK重编。

每侧完整own46：共同P171 Transport26第一URL、各自Diag10第二URL、共同BridgeDiagnostics8＋Capture1＋Codec1第三URL。Wire11、Endpoint／Api、ObservedFrame及模型父共享；所有反射仅公有方法／DATA构造，Endpoint脚本沿既有同package软件入口，不造私有issuer或adopter。实际11父＋92 child＝**103来源行／67独立物理文件**全部CodeSource／SHA核同，不能混作103文件。A为actual current355的旧fields行为，B仅P175 Diag；B不前置父CP。compile355、run Test＋355＝356是测试列表，不能与后继生产356列表混同。

原大包仍P164归档整packet **3400700B**／`4084dcb52ed1ecafadf7fbe6fd11998ff2ed2c06fd22ac077025e519044e4e5d`，opaque3400000字符；不重新编码、不造自然频率或大N。另取既有NativeTransportDiagnosticsTest第50行原malformed packet：138B／`89bd06a9dca217a0eab5a435b87aa37647a161621576936f27b21b796f4f0723`，snapshot_id null、revision1.0、date bool true、speed null、paused false、map_ready缺失。

两个持久实例各自真实HELLO→bad observe(maxFrames1)→good observe：总 **2HELLO、4次setup observe**，不能写0STATE准备。bad实际拒绝是IOException `nonempty JSON string required`，原observe以frame-budget exhausted结束且非terminal，随后good被真实接受。每侧57次ReadFile／3401169B／77guard（331B HELLO＋138B bad＋3400700B good），received2／rejected1、最新good／lastRejected bad、order3／publicrev2均通过。绝不调用recordAdoptionObserved／Refused；实际Production.adoption始终Unobserved，软件接收不是Driver adopter成功。

固定first8ABBA32 capture、各16，**0额外capture warmup**；首冷、后暖与所有outlier不删。每row先在target外取得真实diagnostics()及retainedSnapshot，计入enclosing／全窗；target完整公有capture本身，不能把参数取得或post混报target。全部Returned Received原original／retained Optional／frame／token身份、session／custody、raw good／bad／HELLO与state SHA、typed原state、原计数通过。系统UTC／custodyUUID只侧内相等，不伪跨侧身份。capture与post均0新增endpoint reads／readbytes／guards／writes，capture不产生接收事件。

32之后单列两对公有fields，共 **4次direct fields**：good六role的原始token与bad缺失／null／bool／float token分别核对。再一对public Report／encode仅验证负可用性：外层完整IllegalArgumentException `actual original Native diagnostic producer is incomplete`，cause为各child MissingInputs，missing仅TRANSPORT_REFUSAL、received仍原引用。encode先原mandatory recapture一次，再被真实Unobserved拒绝；rejected formatter不可达，没有成功完整export。Supplement只是未被消费的纯DATA负例参数，不授查询producer／known-null或adoption。最后2次公有close保全部原件及首错＋suppressed清理错误。

正32对应fields32，加4post fields、2negativeencode中的强制recapture fields2，共38是源码／Code调用边推导，**不是仪器运行计数**。普通完整capture→Report→encode且latest＋rejected均在时原三次fields仍保，但本测试没有越过真实adoption缺口来冒成功路径；P174旧32本来fields0，不借旧样本授此项收益。

## 全32与所有反向观察

| 每调用 | A | B | 限定观察 |
| --- | ---: | ---: | --- |
| 分配均值 | 115331898 B | 108528633 B | −5.89886% |
| 分配中位 | 115326792 B | 108525352 B | −6801440B／−5.89754%，8组全降 |
| capture wall均值 | 22.9515375 ms | 21.27144375 ms | −7.32018%，不授稳健提速 |
| capture wall中位 | 21.4348 ms | 20.5693 ms | −4.03783%，4好4坏 |
| enclosing均值 | 30.0300875 ms | 29.00334375 ms | −3.41905% |
| enclosing中位 | 27.68705 ms | 28.026 ms | **＋1.22422%**，4好4坏 |
| CPU中位 | 15.625 ms | 15.625 ms | 粗量化，不授因果 |

capture cycle0／1／6／7的两调用B−A合计 **＋4.3373／＋0.9505／＋1.3594／＋10.2274ms**全部保；最后组每调用均值＋5.1137ms／约27.077%，不混作单call合计。首A target23.6876ms／outer31.4803ms／分配115407040B，首B29.8223ms／outer41.2464ms／108576888B也保；A最大值在index15，target38.4064ms／outer47.2051ms。首A并非最大值，首／暖／GC／初始化额外来源UNKNOWN，不为均值或分配归因删行。

CPU累计 **218.75→312.5ms（＋42.857%描述性反向）**，8组为0好／4同／4差，A3／B2行0；实际0／15.625／31.25／46.875ms粗粒，causal比率UNKNOWN，不把零当零成本或宣称CPU收益。Root按原capture目标、完整功能及8组稳定allocation下降批准限定源码采用；不以mean绿色覆盖4组反向，也不把外层或wholeworker授为更快。无加warmup／补样本／放大N／改loader重测／JFR／fullcase，不拼旧P174时间或比例。

## 全费用与原件

setup至首capture **2.3861943s**，两侧准备0.440378／0.0882092s均保；后置功能0.0710963s、close0.0037509／0.0009956s，before-report3.4157413s。32target合0.7075677s、enclosing合0.9445349s、参数取得0.0111599s，互为包含／重叠，不能相加作总耗时。before-report不含报告materialize／写盘／JUnit尾部，static常量／类加载也可能在方法计时前，实际actor／operator另计。

共享heap152751632→318950776B、committed389283840B；GC5→42、51→138ms。两实例、P171既有Node、共同父JIT、3.4M oracle／post解析与原件副本混合，post观测非侧别retained heap或Java／OS峰值、GC因果或OOME证明，无强制GC。三实际root metadata **1913550B＜4MiB**，含JNA273408B与全部tmp；原大packet只读外置，report73669B＜256KiB、NEVER／existingemptyRoot／CREATE_NEW保留。

Native已知原件锚 **06:02:17.515329Z→lastCLOSE06:40:28.930950Z＝2291.415621s**，至qual06:43:34.257489Z＝2476.742160s；更早实际研究／Root／组合begin UNKNOWN，不能记0。三VM actor18.504506s／operator25.8983181s仅资源子窗，不替准备、源审、编译、冷暖、失败证据、等待、结算与Git。前期0VM SourceReady schema键误读、Windows超长命令206及Native只读准备错误均保，不伪Java／功能失败或已采样重跑；三次实际Java均0accepted／CLOSE且资源释放。

- `N/p175-diagnostic-fields-test01/reports-component/p175-public-capture-fields-fixed32.json`：73669B／`c541a422c599b8fd20c44d3ef15a19a061a7bb55d10fa96ef88e0b6254a751da`。
- 同根`QUALIFIED-P175-FIRST32-PUBLICCAPTURE-ALLCOST01.json`：97428B／`3388d4abe7dbfab0e9f04cc8a39ea6d6bd1e6cfee9ee0c16e4a292660607d997`；Root全278引用／267独立原件核同。
- `R/P175-FINAL-LIMITED-ALLOCATION-SOURCE-ACCEPTANCE01.json`：5450B／`64d68b1ae07beebe64b8548193208f64698e2d7e07eeb49a8ea746a42c270394`。
- `J/construction-diagnostic-fields175/OWNER-ACTUAL-FIRST32-PUBLICCAPTURE-REVIEW01.json`：27967B／`8e38146e4502c4f31e0083f48b49f4d600817326ac0dbbd67008bc823c6bab17`；独审6972B／`40019388…`。

N／R／J是离线具名证据根。源码批准、正式Git、后到software356及Runtime各自记账；本切点current355，0新增SAVE不报有限秒／日，不授10秒目标／Game／GET／P100／部署／热载。P176只另D源码原型、没有Test／CFG／VM／Git或采用权限，旧PARK保持，持续性能主线。
