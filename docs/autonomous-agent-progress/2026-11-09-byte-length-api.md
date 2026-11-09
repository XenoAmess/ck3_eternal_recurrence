# P174：Bytes标量长度API与诊断caller，限定软件分配源码采用

本次新增NativeWire.Bytes的纯元数据`byteLength()`，Diagnostics仅用它取得已持packet的长度，免去仅为长度而取防御副本。Root批准限定软件API／分配源码采用；不是整体worker、CPU、Runtime或SAVE收益。此记录切点软件仍current353；后到355候选须正式SHA、manifest与Root独立实际采用，不能预填。本次A共享扩展容器的行为对照及新增publicmethod结构，均不得称原物理353或已验body-only热载。

## 两叶窄改与实际二进制界限

Wire基底18430B／`0c8b499fcaf65e864def0ab4015ac3781ec6c33a70bbf7ee105f450510096e04`，source307与formal逐字同。候选18476B／`ecb92d7b82fd43f7d6fdc16c2f9266571c9b8238a8ee0debf4ed49cae907eb1c`只在原第43行追加`public int byteLength(){return value.length;}`；245行保持。旧Bytes构造器／value防御clone与所有parser／Unicode／token／hash／oldencode等方法体逐字保持，无新field／type／helper／cache／carrier／trustedflag。**Bytes新增一个public()I方法是结构及反射可见API变化，不能写API完全不变或已body-only redefine。**

Diagnostics基底是已采用P172的8257B／`517668280f3cbae3e4db9771a98b9d2765b35fa00bf63aa34e65774e4edcc5c9`，不是旧source3078220。新8255B／`e94ff2ddd6acb3bad17344e25a9e051ae8e3e74c3728b922f198b89db190e4b7`仅第26行已有int RHS从`originalPacket.value().length`换`originalPacket.byteLength()`；89行保持。四个前置检查、首次取值位置、两bounds／短路／require原消息／隐式四字段赋值与其他方法全原序，fields()未改。

实际Bytes final record／private final array由原构造clone持有、getter继续clone；新int不暴露raw引用，只说明长度，不是frame有效、来源、身份、权限或Guard结果证明。empty／invalid Bytes仍纯DATA。只限标准不可变生产域；原克隆资源／OOME发生时序自然改变，不承诺反射／Unsafe或全部Throwable等价。整个历史C0编译源码谱系仍UNPROVEN，精确formal／source与定点实际Code分别持有，不外推全C0来源。

必要生产编译严格分根：Wire1TU11先闭合，Diagnostics1TU10以`[newWire11]+current353`编译并独立输出，无class复制／合根。两次从首编`-g -parameters`／Java21，真实exit0accepted／CLOSE；Wire10个其他class逐SHA原同，仅Bytes1687B变化，新scalar实际6B getfield／arraylength／ireturn。旧5方法Code、resolved refs、bootstrap／字符串数字constants与旧字段／API／params／Nests保持。Diag9个class原同，ctor PC25唯一byteLength()I、原arraylength去掉，其余checks／bounds保持；三个生成record方法的raw CP索引重排，但resolved语义相同，**不写所有rawCode相同**。

## A/B实际范围与首次有限测试

必要新Test1TU6／soleJUnit1P／0F／0E／0skip，testcase **5.301s**／Jupiter engine **5.327s**。Test41383B／`0889f73baf9547f490bb11641ad74f25437ddc7ea060e273d8e0dc1acb56aa7a`精确放tools/performance/byte-length174，六个props为显式离线入口，不入默认Maven自动Test；无pom／隐式skip／旧Test或生产绿重编。

父仅前置新Wire11；两侧child各own36（共同P171 Transport26第一URL，各自Diag10第二URL），其余共享父。A为实际P172旧clone caller＋共同API扩展Wire，B同容器＋新scalar caller；**A并非物理完全current353**。旧Wire所有方法的实际等价资格是对照前提，不用类名假装旧SDK A/B。测试compile354为Wire＋353、run355为Test＋Wire＋353；生产355候选的Diag＋Wire＋353是另一个有序列表，不能因条目数相同混作已采用。

每类CodeSource／SHA实际核对：11父Wire＋72 child来源＝83 rows／57个独立物理文件。父Diag仍旧A根，B不能泄漏到父。own Production／Rejected／Received只公有getter遍历，不做跨loader cast或private issuer／cache反射。两侧Transport Top同3143b501…、相同既有P171 cache／fixed codec定义；本次没有改变其epoch或Node生命期限制。

原输入仍P164整framed STATE **3400700B**／`4084dcb52ed1ecafadf7fbe6fd11998ff2ed2c06fd22ac077025e519044e4e5d`，opaque3400000字符，不重encode或放大N。两个持久实例，固定first8ABBA32、各16，setup仅HELLO、0STATE目标暖机／0额外warmup；真实observe(Instant)，不用retained重载。每行实际ReadFile53／3400700B／guard60，新frame、完整raw Obj／原packet与stateSHA、canonicalSHA、revision2、chronology2…17、旧token仅接受其原frame与全部post通过。系统UTC／custodyUUID只侧内核，不伪相等。

原32＋20功能＝52observe（A26B26），6HELLO、10功能行、6close全部通过；first／equal／change／ABA／date拒／恢复／nativeRevision回归／secondHELLO／close保原异常全文与引用。之后仍是6DTOpairs12公有ReceivedSnapshot构造：5拒／length5纯DATA接受，四字段引用不变；null packet／time同NPE不能单凭消息辨先后，source／Code顺序佐证；上界仅Code-only，无65MiB压力输入。

再后追加三个共同容器值case：empty／1／5 bytes，共 **3 Bytes构造、9 byteLength、9防御value getter**，各自单计且0observe。1／5修改原输入与getter副本，内部内容／长度不变；empty不假称能写入，验证distinct clone与长度0。以上metadata接受均不授NativeWire帧合法、接收事件或Native权限，也不计作性能样本。私有slot失配／清零／overflow／fixed-clock仍只原Source／Code证明。

## 全32及全部不利证据

| 每调用 | A | B | 限定观察 |
| --- | ---: | ---: | --- |
| 分配均值 | 135340064.5 B | 131703591 B | −2.68692% |
| 分配中位 | 135105296 B | 131704568 B | −3400728B／−2.51709%，8配对全降 |
| target wall均值 | 55.74711875 ms | 39.9226625 ms | −28.38614%，冷首影响 |
| target wall中位 | 38.2367 ms | 34.7072 ms | −9.23066%，5好3差 |
| enclosing中位 | 72.9458 ms | 66.1775 ms | −9.27853%，7好1差 |
| CPU中位 | 31.25 ms | 31.25 ms | 粗量化，不授因果 |

target cycle1／5／6反向的两调用B−A合计 **＋6.0684／＋5.1946／＋14.3006ms**全部保；配对数值区分合计与每调用均值，不混报。首A target323.9475ms、分配138860160B，额外来源UNKNOWN，均值下降不能全归机制。B index2 target86.1277ms／outer182.4807ms也保。

**B index25 outer214.0449ms／target29.6004ms** 与cycle6两调用outer＋190.3089ms保留。enclosing均值−4.66892%是本完整row观察，不是wholeworker结论。CPU累计 **421.875→468.75ms（＋11.111%描述性反向）**，4组好／4组差，A1行0／B0行0、中位同31.25，不能以0作零成本或授CPU改善；causal百分比UNKNOWN。共同父JIT、A-first／同JVM GC、post预热与API扩展对照的限制不删，不拼接旧P172时间成提速。

Root按完整功能、稳定8组分配下降与预定完整observe非material退化规则，批准限定软件源码／API采用。不是只看绿色均值，也不承诺自然频率、每次请求、峰值／CPU或总体延迟。没有增warmup、补样本、删首行／outlier、放大N、JFR／fullcase或再跑找绿。

## 全成本与边界

setup至first target2.0675914s，原功能0.0418351s／DTO0.0027706s／scalar0.0045959s，before-report4.9298614s。32target合1.5307165s、enclosing合2.8003167s、packet准备0.0093847s；raw／canonical／SHA／身份／heap post在target外但全row／case内，报告materialize／write／JUnit尾部不在before-report中，不能以此代全部费用。

共享heap33,387,976→289,942,312B，committed389,283,840B；GC2→71、24→275ms。两实例、共同P171 Node、3.4M raw oracle与post转换混合，不能按侧归因，post采样不是Java或OS峰值／OOME证明，没有强制GC。总metadata2056825B＜4MiB，含JNA273408B及全部tmp／classfiles／logs；原packet外置只读、不改分类。

Native已知 **05:08:34.521016Z→lastCLOSE05:44:10.344952Z＝2135.823936s**，至qual05:47:56.672070Z＝2362.151054s，更早实际研究／Root起点UNKNOWN非0。四VM actor27.1820956s／operator35.5661449s仅资源子窗，不替源审、21typed资格、配置、等待、全冷暖、报告、结算或Git成本。两生产分阶段授权／实际root、Test编译与soleJUnit四个0accepted／CLOSE均保，无copy／重编旧绿。

Native原qual继承current352／all3／46旧标签，由后到clarification澄清为operative **353／all4／83rows57files**；旧qual／raw／XML不改写。主指标、CPU反向和全部费用未变。owner初件operator pending由final小append补持，原件保。外置existingemptyRoot／CREATE_NEW≤256KiB／NEVER与首错＋cleanup suppression保持。

## 具名原件

- `N/p174-byte-length-test01/reports-component/p174-byte-length-public-observe-fixed32.json`：79926B／`5c573c94eaaa4a881f578dd385eb495d0e8df0abe24a488f5efb784ae3d7487c`。
- 同根`QUALIFIED-P174-FIRST32-PUBLICOBSERVE-DTO12-SCALAR3-ALLCOST01.json`：73357B／`0fdeda2ccde441129b2f12ea37a3741382f249d1ed7530931e903871667a1a54`；label clarification1340B／`6eee1cd1…`。Root169次引用／135独立原件与四close核同。
- `R/P174-FINAL-LIMITED-SOFTWARE-SOURCE-AND-API-ACCEPTANCE01.json`：5133B／`135687f330428bbeafae3af357c3ca284fb7a183d82e51b43d8632504ffb7a4e`。
- `J/construction-byte-length174/OWNER-ACTUAL-FIRST32-SCALAR-SOFTWARE-REVIEW01.json`：10053B／`baf3f0631ee2d835f1ec7508841488d705b2f6d02566721fd057ea02fbeba78f`；`OWNER-FINAL-COST-LABEL-APPEND01.json`：1517B／`8388de185ab727de80fcc61ae419f8f225bfa3d62b67db8a37b73c8db3d6940e`。

N／R／J是离线具名证据根。无Runtime／Game／HTTP／GET／P100／部署或新增SAVE；0确认保存日不报有限秒／日，不授10秒目标。P175仅另D源准备，未因本次批准其Test／VM／采用；所有旧PARK保持。
