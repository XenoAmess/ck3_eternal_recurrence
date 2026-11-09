# P179：完整证据 encode.bytes 的长度副本复用，限定软件分配源码采用

Root批准P179限定software allocation-only源码采用。首次固定32的六项预冻结门全部通过，完整公有encode(...).bytes()及全部原件／结构／负例通过；仍保冷首、反向组、外层慢值与量化CPU。不是整体worker／Runtime／SAVE或自然频率提速。本正式发表切点软件仍actual current356；后到357候选与Root独立实际采用另记，不因测试运行CP条目数357预填软件切换、部署或热载。

## 原调用点、两行差分与实际资格

[DriverObservationEvidenceReader.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/driver/DriverObservationEvidenceReader.java)基底27976B／`258c74cafaefbb645ce2c52d4b569461971ea71b49a8e801c85a45673bc812df`，正式95f0与P150实际编译来源逐字同。新28004B／`ad3feae7fc4a3fc9813a80047f3111327f3cc6f1251f7b2b8d6e7455c00cf3dc`只改52、53两物理行、三个substring，371行保持：在原52行声明local byte[]，首getter仍在原SHA参数位置赋值，下一行从local.length取数，不再仅为length克隆整个packet。整叶逆向精确恢复旧源。

Driver完整encode／exact校验、Game／source检查、state SHA、首packet getter及SHA调用一次、所有row字段／顺序、最后RawJson.fullMaterial／序列化／预算均保。这里是业务证据row builder调用点，不改DriverJson的encoder／parser／hash／Guard／TOKENS或旧算法体，无field／type／publicAPI／helper／cache／rawtyped桥／trustedflag。源方法其余字节、所有其他Reader方法原样，不复活P167 Assembler的已PARK实现或借其旧性能。

公开ObservedFrame为final record，原ctor／getter防御clone。只复用数组length；Java数组长度不变，**不依赖MessageDigest provider只读实测**，即使provider触碰该副本内容也不改变length。首getter或hash抛异常仍原样退出，不进入下一行；实际provider只读NOT_HELD不被伪造为观测，也不新增生产providercheck／Guard。少一份长度用副本是源码机制；新local可能在解释器frame跨后续row编码及RawJson构造延寿，不能从分配下降授峰值／GC／OOME或全部资源失败时序等价。

旧actual Reader4在current356 index7，P150source／CFG／ACTUAL0／CLOSE／OUTPUTS与selected encode403B闭合。首个prod01是未BEGIN的-g／-parameters配置，Root在任何BEGIN前改选匹配P150实际元数据的profile；prod01原件完整保。实际唯一prod02 1TU4 exit0accepted、CLOSE08:22:16.955219Z。三nested逐SHA旧同，仅Top27550B／a3866b0e…变；旧API／fields／decoded参数／Nests同，除encode外35方法raw Code及refs完全同。encode403→404B、首277B前缀相同；原首getterPC274保持，新hashPC280，local长度读取替代原第二getter。不是反复编译调flags追同，也不外推全SDK编源或Runtime已装载。

## 最小公开DATA与完整目标

[ReaderEncode179Test.java](../../tools/performance/reader-encode179/ReaderEncode179Test.java)是Test02，22481B／`a91307bbaa8264c0e112e07cef7daae7388e06b810944ff6a353dad344272576`，只放显式tools/performance离线入口，不进默认Maven自动Test、不改pom或隐式skip。必要新1TU4及唯一JUnit真实1P／0F／0E／0skip，testcase **2.791s**／Jupiter engine **2.816s**。无旧SDK／Assembler／Driver／Main／Test绿重编。

仅复用P167 Test02的public DATA：原WIRE／STATE及既有3400000个x的compact构造，public DriverFactsRepository.imported产生Known，actual(...)公有Frame／Session；currentDriver取 **known.driver().encode()的实际bytes／ref**，不是原WIRE ref。没有执行原fixture第84行parent encode，也没有old scoped-reader／nominal／13族功能Suite、真实Native receive或adopter。packet固定 **3400432B**／`57bf15b3d8ab9de15f5559037b789494d7f5fd7bd71ef521140276633686f19d`，state3400333B，模型与全部准备成本保留。

两侧各own Reader4，其他Known／ObservedFrame／G2Source／Obj／ExactRef／RawJson／DriverJson均parent共享，只测这个公有encode入口，不泛授其他Reader包私交互。实际8来源行＝8独立物理文件／5个distinct SHA（三nested二进制同但路径仍各自一份），CodeSource及SHA逐项核同。B root不放进parent。compile356、run Test＋356＝357是测试列表，后继生产357为newReader4＋原356尾另一个列表。

固定first8ABBA32、各16，**setup目标encode0、额外warmup0**；Class.forName initialize=false使Reader clinit留在首次target，所有首冷／后暖／outlier不删。target含真实公有static encode的全部工作、reflection、parent RawJson类型检查及其bytes防御getter。每行post在target外但enclosing／whole内核完整15字段集／顺序、typed原值／Driver及source refs／packet和state hash／publicRevision2／observationVersion3与全部原件；每成功row另2次parent public reference(DATA)解析共64，是qualified Source调用边推导、不是仪器计数，也不能声称整个Test只调用encode一个Reader入口。

32后恰两对4次encode.bytes负例尝试，第一仅currentDriver长度＋1，保原顶级ContractViolationException全文`complete Driver version exact bytes/SHA differ`；第二仅Frame Gamebirth＋1并用好ref，保`semantic producer crossed actual Game/source`，A/B全文相同。这是公开DATA负例，不授实际receive、来源或权限；未增combined-fault样本，早exact再Game的次序仍Source／Code证明。总36次attempt，正32完整返回／4预期异常分层，最后两loader close完整计费。

## 测试前Map顺序纠正与错误证据保全

编写前发现Reader.reference／session／source用Obj(Map.of(...))，Obj保当时迭代序，JDK Map.of跨JVM顺序未定义。Root在任何TestVM之前更正：历史manifest985B／42e8129b…与driver708B／b24b3188…只作历史DATA参考，不能硬断新JVM绝对SHA；不固定盐、反射JDK状态、改encoder或provider。

本轮首A目标完成后先独立核完整结构／原值／原件，才把该次完整byte[]保为同JVM基线；全32逐byte相等。实际本轮985B／`42e8129bb5cb8c6eda2c5b57fe0c43e8d1e00241d045010406d84e06a2d0ce91`及driver708B／b24b3188…恰同历史，**并不撤销跨JVM纠正或证明普遍顺序**。currentDriver始终绑定本setup实际encoding hash。

源01原件保。Test02仅在首次Test编译前补构造失败关闭loader／suppressed cleanup，以及partial receipt标记次序：typed字段先独立标记，same-JVM-byte标记在实际数组比较成功后才true，post_passed最后true。输入／计时窗口／样本／功能矩阵／判定门均未变，不是跑红后换oracle或追加样本。NEVER、existingempty externalRoot、CREATE_NEW≤256KiB、首错及suppressed全保；无需真实fixture／JNA DLL或额外support TU。

## 全32与预冻结六项门

| 每调用 | A | B | 本次限定事实 |
| --- | ---: | ---: | --- |
| 分配均值 | 10276441 B | 6845375 B | −33.38769%，含首冷额外 |
| 分配中位 | 10244760 B | 6844304 B | −3400456B／−33.19215% |
| target wall均值 | 8.656325 ms | 5.46635625 ms | −36.85131% |
| target wall中位 | 6.37505 ms | 5.10625 ms | −19.90259% |
| enclosing均值 | 21.94118125 ms | 15.11654375 ms | −31.10424% |
| enclosing中位 | 16.8677 ms | 14.5402 ms | −13.79856% |

预先冻结的六条件全部通过：所有功能／origins通过；8组分配全降；target均值不劣；target中位不劣；配对每调用B−A差中位≤0；至少4组target改善。实际target **7好1坏**、paired每调用差中位 **−1.554675ms**。allocation的两侧中位差 **−3400456B**与paired每调用差中位 **−3400448B**是两个统计量，不混报；8组分配都下降。

反向cycle5 target两调用合计 **＋1.2166ms**（每调用均值＋0.6083ms），enclosing两调用 **＋5.3942ms**（每调用＋2.6971ms）完整保留。首A target21.1667ms／outer40.3105ms／分配10746112B，首B8.8826ms／19.5142ms／6856272B保；**A index24 outer63.668ms／target8.7925ms**、B22 target8.2273ms也保。首冷、JIT、GC与额外分配归因UNKNOWN，mean下降不能全部算一个clone的因果收益，不删或重计任何行。

CPU累计109.375→46.875ms仅原始描述，中位均0、A10／B13行零，15.625ms粗量化、4好4同。mean／median／causal百分比 **null／UNKNOWN**，不能授比例CPU提速或零成本。Root据原门只授本软件分配SOURCE ACCEPT，保本固定输入的描述性墙钟，不授自然调用频率、全局worker／Runtime／Game或10秒目标；没有再warmup、改输入、补样本、JFR或wholecase刷绿。

## 全费用、边界与前序只读事实

setup至首target1.8354303s，后置功能0.0080465s，before-report2.4475563s；target32合0.2259629s、enclosing合0.5929236s，post64解析／typed／全byte原件检查和loader close全保。时钟互相包含／重叠，不能相加作全耗时；before-report不含报告materialize／write／JUnit尾部，static Test maps可能早于方法计时，actual actor／operator另账。

共享heap57772504→49320752B、committed389283840B；GC2→7、38→54ms。两Reader、parentJIT、3.4M输入／packet／state／post同窗，观测不证明侧别retained heap／峰值、GC因果或OOME安全，无强制GC。四owned roots含未执行prod01；Native pre-qualification metadata1358063B，另qual55335B／summary11533B同4MiB帽内，report45737B＜256KiB，实际tmp/JNA文件0。

Native已知 **08:13:19.435539Z→lastCLOSE08:46:20.051227Z＝1980.615688s**，至qual08:51:02.138501Z＝2262.702962s；更早实际研究／Root／组合起点UNKNOWN非0。实际三VM actor15.466218s／operator20.1714852s只是资源子窗，不替全部准备、源审、未用profile配置、Map纠正、Test02错误保全、0VM错误、冷暖、等待、结算与Git费用。prod01始终0BEGIN／prod02唯一生产编译，Test编译及soleJUnit三个0accepted／CLOSE资源释放均保，未复编旧绿。

前序P177只读限两叶，均bounded NO_CANDIDATE：Prepared.publish的rawInput/body各一次，独立verify／保存／commit／readback不能省；OrdinaryFinanceCollector.current两次encoder分别来自request snapshot与实际ROOT结果，非同源重复。inclusive链不等于leaf selfCPU，不扩大搜索或改Guard。

P178 producer713的nativeOwnedFields仅return静态集合，没有每entry分配；738／742两个Obj(extra)同call复用在标准不可变域源层可行，但只省一份浅LinkedHashMap／entries及wrapper，非大值深复制或编码，收益未知、暂不测。当前formal Producer60987／9144df9a…与source307旧wholeleaf不同，不能据类名授实际编源。两只读结论并入此单元，不另发文档／VM或借低收益凑性能样本。

- `N/p179-evidence-packet-length-test01/reports-component/p179-public-encode-bytes-fixed32.json`：45737B／`59c772dfa29a759d14a8e7242fa1f987d974f756e1be8d7b87d411c433ecdb10`。
- 同根`QUALIFIED-P179-FIRST32-FULLENCODE-ALLCOST01.json`：55335B／`6ea9e4abf9324e25c6e5300c37801202917ce148bef20d82fc8c7c8ed2ed9ffc`；Root全128引用／121独立原件核同。
- `R/P179-FINAL-LIMITED-SOFTWARE-ALLOCATION-SOURCE-ACCEPTANCE01.json`：5719B／`79d756ec…`。
- `J/construction-evidence-packet-length179/OWNER-ACTUAL-FIRST32-FULLENCODE-REVIEW01.json`：21449B／`594daf3b442ead5bab7e619426da38830eecccf913f051889f8d245733b82051`；Planning独审3495B／67dcf916…。

N／R／J是离线证据根。formal source／编译／软件357采用／Runtime分别按真实回执记账，此cutoff仍356；0新增SAVE不报有限秒／日，无Game／GET／P100／账本／部署／热载授信。所有旧PARK与UNKNOWN保留，P180只读主线继续，不以本次发表收工。
