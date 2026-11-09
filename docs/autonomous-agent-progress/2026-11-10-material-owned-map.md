# P196：固定19个更新共用既有owned Map，有限源码与单回归接受

Root接受正常owned immutable DATA域的窄源码、完整actual Code证明与原coldCompletion单用例回归。只把ConstructionMaterialReducer.reduce(Input)的19个固定with更新改为既有局部Map的顺序put，最后一次new Obj。**不计两侧共有201的Map，39次浅Mapcopy／20个Obj构造位置变为1次copy／1个Obj，仅为源码及callee Code代数；不是N²修复，未测实际allocation／JIT、生产频率或CPU／wall、端到端收益。**

本次正式源码切点actual离线软件仍current364，future candidate365及Root实际采用另账。不授JVM装载、body热更、Runtime、Game、GET、P100、账本、SAVE或10秒目标。零新增确认保存日，秒／新增保存日为null；持续性能目标未完成。

## 只改固定链，原值、键序与Guard保持

[ConstructionMaterialReducer.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/ConstructionMaterialReducer.java)基底31361B／`7e86b48ac696eb0cc40891a06cf2425e73c3244814fe0060569f1c1838c7e357`，新31654B／`e49f126945f7e81831642bce3cf80fb3ccf33f948b01e73ba4723cdb015e905e`。改动仅204–218内14个物理行，217原RHS行保持；304行数不变，整叶inverse恢复正式基底。D稿parent753da17，随后P195只推进别的生产叶／文档，本叶基底仍逐字相同。

201原new LinkedHashMap(prior.members)和202–203原unavailable移除／条件rename保持；199–200 progress与自己的with链也保持。按原顺序执行completion_status到readonly_material_recheck的19个唯一键put，每个完整argument／RHS字节原样，包括ternary、optionalNumber、delta、provinceValue、frame.get、start_receipt同引用及最后嵌套obj。没有RHS读取已修改的retainedMembers或未初始化updated，原中间Obj不作为后续计算输入。

LinkedHashMap覆盖原键不移动位置，新增键按原序追加，所有原成员／opaque字段和Value引用保持；最后Obj构造器仍拥有自己的Map副本并包装unmodifiable，局部可变Map不外泄。旧Obj／with**允许null Value**，新put同样允许，不增加requireNonNull或其它检查。updated是原有local，只把赋值延到最终owned Obj，不加新local、field、type、API、helper、cache、raw+typed桥或issuer。

219后的preserveIncomeFields、completed CASH、全部frame／source／income验证、codec／parser／hash／oldencode、其它方法与角色数据字节保持。正常producer DATA下保值／键序／引用；删除中间分配及OOME机会，不授恶意Map／Unsafe／反射／私态或全部Throwable、资源失败时序等价。原201 Map两边都有，不能算作新省；后续条件分支／progress／nested对象成本也未被此代数删除。

## 真实编源与完整39方法Code

旧实际Reducer来自P113 construction-full-material02完整6族，Top38479B／29661e9a…。曾只有不同source307的早期不确定性，现由实际CONFIG的material.sources、ACTUAL／CLOSE／OUTPUTS闭合：精确编源就是J/construction-full-original113/material-candidate02/ConstructionMaterialReducer.java，31361B／7e86…与正式基底整字节相同；不把不同的source30729231／8808当编源，也不因此授全部C0源码。

唯一生产1TU6沿实际P113 release21无显式-g／-parameters profile编译0accepted，CLOSE **2026-11-09T16:33:59.909931Z**；5个nested SHA原样，Top38540B／`a0a68c01da05923d11d63676972d97a4457593cc189c463d7c54a2f0ed9621a5`。旧ABI、fields、方法声明、params、Nests保持；没有结构增量，但不据此授实际热载。

39方法仅reduce(Input)目标Code3704→3761B；其它 **38方法normalized Code／resolved CP operands／常量／完整bootstrap／控制流／exception table相同，其中36 raw Code相同、2仅CP重排**。目标旧区域PC2751..3296、新2751..3353：19个key／RHS全部解析操作数、调用／字段、常量／分支保持，1559条保留指令及119条branch映射核同；CP symbol multiset、literal和bootstrap保持。

其中仅两组scoped pattern临时槽共10条指令作对应：第5个completion_observed_date_raw与第18个start_receipt。旧01缺映射和后到把第18误写17的0VM错误原件保留，03按具名key纠正，不放宽源或Code。其余local operands原样；201 owned Map一直是local42，每个新put都取该receiver，最终Obj(map42)存原updated44。旧caller原先只有1个显式Obj构造，现在仍1个、位置移到最后；20个Obj是经with callee的源码构造数，不能混成20条caller new字节码。

Native证明与owner独立classfile解析交叉核：其它38、逐19 RHS、区域外Guard prefix／219+suffix和全部region receiver／pop／final Obj指令闭合。独立审阅未运行class，没有用单回归替代全Code，也未把归一相同写成全部raw相同。

## 原两Test TU，仅一个现成用例

原ConstructionMaterialReducerTest29553B／`33148ddbc61978418f34f206c68761ea20aa42bd7241faec9ac75e51a2b5ab2b`和ConstructionCoordinatorPendingTest5230B／`c1a1b12349da716d4896adb982e3b8d1b942569c32e86238eec65b2b7f933428`与正式Git整字节相同，源码未改。实际CP及Native具名查询未持qualified cache；完整主TU的未选方法引用helper.original()，故只做必要2TU2编译，未裁剪／改写，未自动扩大旧SDK／Main／其它Test编译。Test2编译0、CLOSE **16:52:22.389889Z**，实际2类major65／SourceFile正确。

只运行ConstructionMaterialReducerTest#coldCompletionRetainsTheOriginalActionAndAllowsANewWorkerCounterNamespace；主类其它12个@Test及helper3个@Test均未运行。原public reduce(byte[])→decode→reduce(Input)，inline JSON DATA，不是Native ACK／Guard／来源许可或真实世界资格；没有新fixture、warmup、benchmark、JFR、HTTP、文件业务或完整APPLIED workload。

唯一JUnit **1P／0F／0E／0skip**，testcase **2.332s**、Jupiter suite **2.365s**，CLOSE **2026-11-09T16:56:45.386664Z**；三阶段实际0accepted／terminal后fenced释放，输入不变，new Test2＋Reducer6的8个actual firstorigins及原held19核过。

该例独立断言仅19更新键中的 **5个**：completion_status、completion_observed_date_raw、observed_player_monthly_gold_income_raw、post_proof_epoch、start_receipt；另检查MATERIAL_UPDATED、candidate／pre_proof_epoch保持、post_cash_v2缺席和完整ledger encode/decode往返。**其余14值、全部key序／sameRef／输入防御copy、unavailable rename、preserveIncomeFields、completed CASH、active／incomplete／absent／restored分支不获此单例覆盖。** 全19 RHS／顺序／引用的证据是独立Source／actual Code，不是扩写测试oracle；测试时长不作性能窗口。

## 全费用与预算

生产actor5.6312199s／operator6.9066951s，Test编译6.8952844s／7.9996171s，JUnit5.339837s／6.4978601s；三actor合计 **17.8663413s**、operator合计 **21.4041723s**仅资源子窗。owner SourceReady **2026-11-09T16:14:03.934892Z → 最后CLOSE2561.451772s → final qualification2736.098081s**；Native CFG checkpoint16:28:21.493024Z→CLOSE1703.89364s／qual1878.539949s是内窗，不相加。北京时间均已11-10，更早真实研究起点UNKNOWN、不记0。

preflight cap写前拒绝／compact格式错误、ConstructionQuery非Source符号检查器错误、scoped槽检查／第18编号纠正、Root误读XML_reports嵌套pin形状KeyError，以及Source／Code审阅、actual364采用等待、授权／调度、冷启动／资格／Git费用全保；均不抹成Java RED或重跑，三phase各首次唯一。owner只做0VM源码／classfile／XML审阅，没有另启动编测。

Native final静态metadata **1192253B／96文件**在原4MiB内，tmp0、business fixture0；classfiles／XML／日志／错误件全部按metadata原分类。JNA jar仍是classpath输入，目录tmp为空不证明进程级JNI未加载，process-wide JNI为NOT_HELD；连续硬峰值／Java heap peak未知。没有actual allocation、CPUwall、生产频率或吞吐测量。

后到仅0VM的candidate365仍false／formal SHA null／PENDING，不切actual364。首次序列化131183B比128KiB cap多111B，写前拒收；02只去重复budget-root文字，172项完整origin pin／有序CP均保，不加cap。其新增candidate根合计4roots metadata1338373B为另一后到静态快照，原三roots1192253B不被覆盖；这些准备／拒收／等待费用仍保，不作源码发表或后到Root实际采用的替代回执。

P197另只读点保留为BOUNDED_NO：两个decode虽纯，但public typed Input允许自定义BigInteger令两次encode不稳定，第二packet.original写receipt可观察；不能加origin／classgate／新scan／bridge救此假设。两decode与framechecks保留，未实施、不混本源，不把它改述为成本0或停止主线。

可核：`R/P196-LIMITED-NORMALDATA-19MAP-SOURCE-AND1P-ACCEPT01.json`2542B／`031cfee1ad18448acac639d910431a7e822ef7fa4c68234ea92b359bac30f155`；`N/p196-material-owned-map-prod01/QUALIFIED-P196-PROD6-TEST2-SOLE1P-ALL3COST-FINAL01.json`16791B／`9783518eeb61bccbbc481cc9a63e9a8eacf6cf14e33b8439c06babe84a29ed91`，37个独立引用已逐SHA核；同根全部Code79899B／`4bbc247272dc825fa73c4e44124a54c31bad99325a40e37f1b0e7cc82f29c908`；Jupiter XML45308B／`9ae1174d914262e42aa03dcb630c4c2c37f163cf13b570288babcdef729ac3da`。J/construction-material-map196/owner-review01下独立Code14967B／af7c1a0f…、ownership3013B／e9fd3088…、solecase5533B／2304cae9…；P197只读6531B／90a95ecd…均原件保留。N／R／J为隔离Native、Root及Java交付证据根。

exact4仅生产Reducer和unit／daily11-10／W46追加，原Test两源、Obj、其它Source／AGENTS／CI／pom与实际运行文件不动。源码、typing、有限功能、Git、后到软件365实际采用与Runtime／SAVE继续分账，发表不标持续目标完成。
