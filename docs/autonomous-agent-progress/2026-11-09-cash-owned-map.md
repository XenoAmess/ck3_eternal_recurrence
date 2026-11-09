# P188：构造现金上下文时合并固定元数据浅拷贝

Root已接受正常不可变DATA域内的窄源码／实际Code等价，以及原缓存完整APPLIED软件用例的功能回归。只把private cash末尾连续三次Obj.with改为一次局部owned Map累积和最终new Obj；cashContext及全部业务投影、融资／Guard、parser／hash／oldencode保持。**6个浅Map／3个Obj构造位置变为2个Map／1个Obj，仅是源码与Code推导，实际allocation、调用次数／频率、CPU／wall或吞吐收益均未测。** 不用不同JVM的完整case时长作因果提速。

本次源码发表切点actual离线软件仍current361，尚未采用本候选；后到软件候选与Root实际采用另账。没有JVM装载、Runtime、Game、GET、P100、账本、SAVE或10秒目标信用。零新增确认保存日，秒／新增保存日为null。P190仅独立只读研究，不混本次源码或Test。

## 两物理行及正常DATA语义

[OrdinaryConstructionCollector.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/OrdinaryConstructionCollector.java)基底30143B／`f677e747b52a1d5553e7d25fbe19fef5ea810069b35049fc8ba798f3993050f7`，新30282B／`b6655349730759a544faf58aafbedb8d493a6abd68e40fb3d312d12e7908fe9f`。仅300、301两物理行改变，326行数保留；整叶inverse精确恢复正式基底。D原型最初从fbb9610e取基底，发表parent437c5f66的该叶仍整字节相同。

cashContext(request,current,WartimeConstructionCodec.SCHEMA,null)仍只调用一次且首先执行；随后在原首with参数求值相对位置构造Text(kind)，再拷贝context.members。按kind、construction_gold_raw、procurement_decision依序put，IntegerValue(cost)在原相对位置构造，procurement保持同一引用，最终Obj构造器再拥有自己的Map副本。LinkedHashMap覆盖旧键不移动原位置，缺键依序追加；原成员和值引用、kind String／cost BigInteger引用与最终成员迭代顺序保持。中间Obj不外泄，最终两侧仍返回新的owned Obj。

现有Obj构造器是Collections.unmodifiableMap(new LinkedHashMap<>(members))；with自身先拷贝Map，再调用该构造器。未改Obj／Text／IntegerValue定义，未新增API、field、type、helper、跨call cache或raw+typed平台，只增三个方法局部变量。cashContext、before／quote与融资规则、所有role字段、Guard、parser、hash及oldencode的其它源码字节保持，不移动独立验证／来源检查。

原三个with各有一次直接Mapcopy和一次Obj内部Mapcopy，新局部Map加最终Obj内部copy，故可静态推导6→2浅Map、3→1 Obj；只是固定小外层元数据，不是深拷贝大子树、消除完整JSON编码或O(N²)修复。P180当时已记低成本未测假设，本单元没有复活PARK benchmark。正常producer-built标准不可变DATA限定下值／顺序／引用等价；移除中间分配及OOME机会，不授恶意Map、反射／Unsafe、伪null私态或全部Throwable／资源失败时序等价。

## 实际编源、Code及原完整功能入口

旧Collector实际来自P113 classes-app完整22族，旧Top39973B／d513…；实际编译输入30469B／277299…为CRLF，与正式30143B基底仅326个CRLF差异，规范为LF后整叶相同，不能误写原文件整字节相同。旧profile无显式-g／-parameters，本轮沿该profile；Obj／Text／IntegerValue实际P129编译输入8933B／`ae12db03269c0a4dba7d21970b22f4b5b4442caca770784ee2a0733814d0a9d0`与正式定义整字节相同。此为所读叶的具体来源，不扩成全部C0源码或动态loaded ClassSHA授信。

唯一新1TU22生产编译实际0accepted，CLOSE **2026-11-09T13:53:16.278280Z**、fenced／released；21个nested与旧SHA逐件相同，仅Top40012B／95c278ab…改变。旧ABI、fields、方法声明、MethodParameters、Nests保持，无结构性API增量，但不据此宣称实际body热载已验。Top25方法中另24个normalized Code／resolved CP operands／常量／控制流／异常表／完整bootstrap参数相同，其中19个raw Code相同、5个仅CP索引重排，不能写全部raw相同。

cash Code46→84B：context PC6、Text16、members27、Mapcopy30、put42／60／70、IntegerValue57、最终Obj80；参数引用、构造顺序与键顺序由实际Code核对。旧方法与callee的实际Code证明和全叶inverse共同限定本次改动。

随后只复用原P153 cached Test10，未编译Test／Support／其它旧绿，没有新fixture、镜像测试、benchmark、暖机、JFR或额外case。选择器为ConstructionFullProduction113Test#fullFuturePlanRunsActualIntentEffectColdVerifierAndFullMaterialPublication，原APPLIED模式、business120s／heap384MiB／child210s／outer240s不变。原测试source38984B／`815f2d214d823af324f1034f35ea286c9a98573b0c3c43d1dbbfcc195dec72f8`保持；新Collector22在prefix index1、原Test10在index0，32项相关firstorigins已实核，整个named来源联合重核与动态已装载class SHA是不同证据。

唯一JUnit **1P／0F／0E／0skip**，testcase **103.447s**、Jupiter suite **103.475s**，实际0accepted，CLOSE **2026-11-09T14:03:23.218412Z**、fenced／released，输入不变。原beforeIntent要求Policy revalidate的Available，实际Collector在Available前构造cash；该原成功APPLIED路径支持正常DATA的结构正例，不是运行插桩测得的cash调用数。完整功能耗时仅记实际费用，不与P182／P183等独立JVM相减或授性能胜利。

## 全费用、错误及保留预算

生产actor5.3726655s／operator6.7830972s、JUnit actor105.7450275s／operator107.2459132s；两actor合计 **111.117693s**、operator合计 **114.0290104s**仅资源子窗，不能代替任务全费用。

owner已持SourceReady **13:16:56.999791Z → 最后CLOSE2786.218621s → final qualification3057.993373s**；Native首次已持artifact **13:28:19.897083Z → CLOSE2103.321329s → qualification2375.096081s**为其内较窄窗口，不相加。更早实际研究起点UNKNOWN，不记0；全部源码／CRLF／callee／公开gate检查、准备、审阅、调度等待、资格与Git费用保留。

Native PUBLIC-GATE准备和Git-ref准备的0VM错误原件、Root原prerequisites检查器把prod-only预期用于实际prod＋复用Test的错误及更正均保留，不是Java RED或重新编测。两实际phase各只运行一次，没有以修改样本补测。

Native资格前静态快照metadata1589234B／90文件保留；final及Root接受时为 **1627878B／93文件**，guarded fixture **38291855B／343文件**，分别在原4MiB／64MiB预算内。JNA DLL273408B及其它tmp／日志／classfiles计metadata；仅原cached Test的独立软件@TempDir树计业务fixture，没有把metadata挪作业务分类。保留逻辑静态尺寸不是连续硬峰值，瞬时peak／Java heap peak仍UNKNOWN。

可核原件：`R/P188-FINAL-LIMITED-CASH-OWNED-MAP-SOURCE-ACCEPTANCE01.json`6568B／`2f779a78803e59c8059384070131ed0308fcfc07fa201077719be7a717ad7188`；`N/p188-cash-map-prod01/QUALIFIED-P188-PROD22-CACHED-APPLIED1P-ALL2COST01.json`33782B／`0cc3f5b19be5f5a4012ec7e401f36adc4971bb72c42eaa404e3e44f0a4df957b`，其中68次引用／63个独立原件SHA全核；同根实际Code24194B／`0314a1743dde39e1b99e712ea6c38373d6de92a5e3bfc6f47365456c34999f5c`；Jupiter XML45361B／`1ba761e9b9a9410261e5923e96d2042d062a0d6c8b8c47400ee1f4fee2ebaaf8`。J／N／R分别为隔离Java交付、Native和Root证据根。

exact4仅该生产叶和unit／daily／weekly；不改Test、Obj、P190源码、其它Source、AGENTS、CI、pom或任何实际运行文件。源码、编译、完整软件功能、Git、后到离线软件采用与Runtime／SAVE继续分别记账，持续性能目标未完成。
