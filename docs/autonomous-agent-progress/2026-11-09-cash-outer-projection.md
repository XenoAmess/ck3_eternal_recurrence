# P190：两处外层投影更新共用私有Map，四个公开DATA场景通过

Root接受本单元有限正常不可变DATA的源码／实际Code等价与公开API功能回归。只合并projectCashContext的两处outer替换；snapshot内diagnostics投影、financingFields、全部role白名单和其它生产源保持。**只有两个outer分支都命中时，4个浅Map／2个Obj构造位置变为2个Map／1个Obj；单分支和nested成本不变。这是源码／Code代数，未测实际heap allocation、生产命中／频率、CPU／wall或吞吐收益，也不是N²修复。**

本次正式源码切点actual软件仍current362，候选及Root后到实际离线采用另账。不授JVM装载、body热更、Runtime、Game、GET、P100、账本或SAVE；零新增确认保存日，秒／新增保存日为null，持续性能目标未完成。

## 两个层级分开，身份与原求值次序保留

[OrdinaryFinanceCollector.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/OrdinaryFinanceCollector.java)正式基底43600B／`b23777886790bb7c4532d2c3c303822f1299e2965d0b9d87e361b2dce9b8d90b`，新43805B／`5c73c35eb1097c9cf171ed9334a966a7b80aa883fbaceff262b039c4a53983dd`。只改390、398、400、401、403、404六物理行，488行数保持；整叶inverse精确恢复基底，P188发表只推进parent，未改此基底叶。

snapshot和root条件仍依原顺序读取original，绝不从已更新的外层Map读取root。snapshot的financingFields及397的nested diagnostics条件／with／三键投影逐字保持，整个snapshot RHS完成后才在原outer更新位置首次复制original.members并替换snapshot。root分支同样先完整计算原financingFields(root,原白名单)的RHS；若是root-only路径，随后才首次复制Map，再put同一projectedRoot。两分支都命中则共用这一个方法局部owned Map，依旧snapshot后root更新。

两分支均不命中，仍返回**原Obj同一引用**；任一命中则最终new Obj并保其owncopy，不能因投影值equals原值而返回原Obj。LinkedHashMap覆盖旧键不移动键位置，未知outer字段和值引用保留，所有保留叶Value及opaque对象引用保持；新的投影容器仍独立，不能把它们与保留叶的sameRef混为一谈。Obj构造器仍自行复制并包装unmodifiable Map，方法局部可变Map不外泄。

financingFields302–305仍按original.members输入迭代序过滤，**不是按白名单顺序排序**；snapshot／root／diagnostics的所有原键名单、调用参数、条件顺序和字段角色保持。cashContext及其余52方法、旧Obj定义、Guard、融资、parser／hash／oldencode不改，无新API、field、type、helper、cache、raw+typed桥或权限结果复用。

正常producer-built标准不可变DATA下保值、键序、引用和公开身份；移除中间分配／OOME机会，不授恶意Map、反射／Unsafe、伪null私态或所有Throwable／资源失败时序等价。此仅固定小元数据，不是大JSON物化消除，不借旧partial采样权重或P189结论授调用数和收益。

## 实际编源与全部非目标Code

旧Finance实际P113 classes-app完整12族，旧Top60746B／`b5f861c60f92567f897eea3451cf3a78954ad08e361d822f342a34bb9d095e14`；精确编源43600B／b237…与正式基底整字节相同，本轮沿旧release21、无显式-g／-parameters profile，不用source307或CRLF猜测替代。P129 Obj／Text／IntegerValue的已持编源与实际callee Code复用；不扩成全部C0源码或动态loaded SHA证明。

唯一生产1TU12实际0accepted，CLOSE **2026-11-09T15:00:22.289233Z**、fenced／released；11个nested SHA与旧完全相同，仅Top60814B／`cb2e4e5edbba9bb298f32cffa0452c3bb4a99999095bbbb06ca10da45614e6f8`变。旧API、fields、方法声明、MethodParameters、Nests保持，无结构性API增量，但不据此补授实际热载。

Top53方法中，目标projectCashContext Code368→413B；其它 **52方法normalized Code／resolved CP operands／常量／控制流／异常表／完整bootstrap参数相同，其中40 raw Code同、12仅CP索引重排**。实际snapshot与nested投影区域、root RHS调用／白名单保持；成员Map非null才复用、root-only在RHS之后copy、none直接返回original及最终new Obj四分支数据流已核，不能用全部raw相同代替归一证据。

## 一个新独立Test，四个字面期望场景

[CashProjection190Test.java](../../tools/performance/cash-projection190/CashProjection190Test.java)为10569B／`068fd1f68b4ac40b30bf27be12713a8328adb4e9cc34f48a6296f0a78ea227ca`，独立tools目录，不加入默认Maven自动Test。唯一新Test1TU／1class实际编译0，CLOSE **15:06:14.805010Z**。没有旧SDK／Main／Test全树重编；原CashContextRole110Test的全局@BeforeAll私反射不符合本范围，未选择／裁剪复用。

一个@Test内固定四个独立literal DATA场景，每场景公开projectCashContext一次，共4次；0 setup目标预跑，0 benchmark／性能样本。仅公开Obj／Text／IntegerValue／Bool／Nil，固定BigInteger含大于2^53的值，不经协议／JSON解析，不造Guard、ACK、Attempt、issuer或真实业务fixture。

场景分别检查：none的nonObj snapshot／root返回原Obj；snapshot-only和root-only的投影值刻意等于原值，外层仍须新Obj；both把同一个Obj作为两种输入role，outer特意root先snapshot，保留共有date Value引用，同时按各自role裁剪字段。snapshot nested diagnostics只保三声明键，secret移除，root保身份／收入，unknownOuter仍同一引用。每层输出键序显式检查，输入顺序刻意反白名单顺序；全部保留叶sameRef、输入字段／键序／alias未变。

期望由独立字面键值对构造；literal helper只按明确给出的pairs创建Map，没有筛字段算法或with链镜像。新snapshot／root／diagnostics容器检查fresh identity，保留叶与未知outer才检查sameRef。没有额外异常域、私反射、原始来源许可或跨call缓存测试。

唯一JUnit **1P／0F／0E／0skip**，testcase **0.078s**、Jupiter suite **0.102s**；实际0accepted、CLOSE **2026-11-09T15:15:37.945155Z**、fenced／released。该时长仅功能测试费用，不是performance window。P190没有完整APPLIED workload、allocation／CPU／wall测量或生产频率验收，不把P188原完整case搬作本单元新结果。

## 全费用与预算

生产actor6.3000689s／operator8.0501041s，Test编译actor4.8076731s／operator5.9383526s，JUnit actor2.2806683s／operator3.1117608s；合计三actor **13.3884103s**、operator **17.1002175s**仅资源子窗。

owner已持SourceReady **14:28:16.365755Z → 最后CLOSE2841.5794s → final qualification3049.694591s**；Native首持artifact **14:40:44.992145Z → CLOSE2092.95301s → qualification2301.068201s**是较窄内窗，不相加。更早真实研究起点UNKNOWN，不记0；全部源码／role测试排除、preflight、审阅、准备、调度等待、资格与Git费用保留。

原CFG argv／classpath检查器0VM映射错误及后到final writer映射错误／更正均保存，不是Java失败或额外编测。三实际phase均首次唯一0accepted／terminal后fenced释放，没有补采或重跑追结果。

Root早期metadata1220930B／91文件快照保持；final **1257969B／97文件**在原4MiB内，所有tmp／classfiles／XML／日志／错误原件都计metadata，业务fixture为0。ownedroots DLL文件为0，仅描述这些证据目录，**不是进程JNI模块未加载证明**。保留逻辑静态尺寸不是连续硬峰值或Java heap peak；没有强制GC或heap／OOME性能结论。

可核原件：`R/P190-FINAL-LIMITED-OUTER-PROJECTION-SOURCE-ACCEPTANCE01.json`12343B／`32cd2eb7be0e43def62c2ffebc1564a95db619f1e9ca4c6cc2f0253f195c7623`；`N/p190-cash-projection-prod01/QUALIFIED-P190-PUBLIC4DATA-1P-ALL3COST-FINAL01.json`14008B／`4ce83ace2a85ec8dab800982815fcab8ed0773cbfbdb75e02609b266d673b48c`，32个引用原件SHA全核；实际Code41509B／`5931522caa883d2e8c13ac047e7c46f2c52600ac8a007f193d1e926fe400868a`；Jupiter XML44959B／`40bfd63c8f3a630f9a2624a5844cef970aa70549aeccaa1ecd8a7642cd307cfa`。J／N／R为隔离Java交付、Native与Root证据根。

exact5仅本生产叶、独立Test和unit／daily／weekly；旧Obj／Test、角色定义、其它Source、P191、AGENTS、CI、pom及任何实际运行文件不混。源码、typing、公开DATA功能、Git、后到软件基线及Runtime／SAVE继续分账，独立主线不因本单元发表结束。
