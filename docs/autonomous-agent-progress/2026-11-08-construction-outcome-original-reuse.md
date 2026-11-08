# P133：保留新物理验证的同调用解码复用

Root采用本单为同调用组件的当前线程CPU／分配优化。新manifest OUTCOME仍先独立打开完整sidecar；APPLIED第二次验证仍实际读取、核len／SHA／ExactRef、完整融资header和command frame，再执行原Native verifier。只有同一调用首个私有Loaded的fullref相等、fresh完整字节与其Observed防御clone逐字相等时，才复用完整Obj／Observed。它是纯DATA复用，不是IO、Guard、来源或动作许可缓存。

本单为owner-original，0模型HTTP，无模型采用案例。生产仅Source／Lifecycle两叶，新增Loaded私有ExactRef字段，旧inline为null；public resolve／resolveCommand和旧public archivedBinding都以null候选维持原路径。package立即verify helper不返回持有Loaded的Binding闭包，不存Session／authority／trustedflag，不新增global／ThreadLocal／跨call缓存。Header谓词机械移为唯一helper，fallback仍model→header→finish；原Frame、NativeEffect和三类OUTCOME尾部逐字保持。

## 软件验证及真实版本

实际必要编译为2production TU／11类、1new Test TU／4类、1必要modified old Test TU／10类，全部首次0退出。生产无新类型；Loaded字段变化不授Quarkus布局热替。旧SDK、encoder、parser、Guard和Main03零重编，Main03不运行，也不用于本分支的性能验收。

| 方法范围 | 实际结果 | JUnit case／suite秒 | 记录actor秒 |
| --- | --- | ---: | ---: |
| 新same-call命中／错ref／inline与旧入口 | 1P | 10.317 | 14.5615458（两项同JVM总窗） |
| 新fresh header／frame／缺损物理原件拒收 | 1P | 1.703，suite12.066 | 同一总窗，不另计 |
| 旧public Applied，完整compiled15家族 | 1P | case139.769／suite139.806 | 142.4793566 |
| 旧public Unknown，完整compiled15家族 | 1P | case73.173 | 76.2596649 |
| 旧public Rejected，完整compiled16家族 | 1P | case63.344 | 66.1695522 |
| 新组件measurement selector，当前modified Test | 1P | suite135.099 | 137.5975028 |

六个distinct methods＝2new功能＋3affected旧方法＋1new测量方法，分五个JUnit JVM；不是同一JVM六项。15／16虽同FQN，shared exercise真实不同：历史Rejected15的generic负ACK得到UNKNOWN失败仍保留；本单Rejected使用真正before-write拒绝的compiled16，未把旧Applied绿借给16。Measurement另必要编译当前Test并只选新方法，三个旧方法不再跑。

新DATA测试使用真实临时Store／Writer／Archive，代理的所有操作和withSession均委托真实实现。反射只观察由public物理读产生Loaded的返回identity与私有ref，不mint构造器／修改字段或发放issuer。相同字节在两个真实Store对应不同合法ExactRef，必须Stage fallback；命中仍执行header与frame检查，缺件或损坏原件在spy delegate前拒收。损坏反例归为fresh实际原件／归档失败，不凭RuntimeException单独命名为SHA类别。spy仅守委托前边界，真正Native阳性来自独立public Applied和组件用例。

## 固定同输入的两入口组件

Measurement放在真实public软件APPLIED、canonical history和一次positive cold verifier之后，pending仍在，尚未发布OUTCOME。四行固定A/B/B/A，无额外warmup：

- A：first resolve结果立即丢弃，再旧public Binding的null候选路径；不人为强持首Loaded穿过第二parse。
- B：first resolve保留局部Loaded，立即helper复用；真实clone／memcmp、延长的graph存活和全部原件读／验证成本计入。

两边都调用未包Source的原NativeConstructionEffects.archivedVerifier，计数decorator只完整委托并计成功。代理只统计目标input_ref，其他Native evidence读取不变。每行都是2次目标full read＋1次实际Native verifier；head／sequence／pending body／command字节及Native软件读写计数在前后不变。四行后才走原一次synchronizeOutcome及MATERIAL，未重放动作或reset账本。

这是**同一个新binary的两入口read＋binding component**，不是pre-P133 binary A/B、whole OUTCOME或实际worker测量。CPU／allocation查询窗口包住wall；setup、独立断言、报告、fixture和后续publication成本另计，未隐藏GC／JIT／冷启动。

| 固定行 | wall毫秒 | 当前线程CPU毫秒 | 累计分配B |
| --- | ---: | ---: | ---: |
| A0 | 558.2666 | 375.000 | 1006290136 |
| B0 | 349.1109 | 296.875 | 943884312 |
| B1 | 387.2541 | 281.250 | 943874608 |
| A1 | 397.9779 | 343.750 | 1006215464 |

A／B均值：当前线程CPU359.375→289.0625毫秒（-19.5652%），allocation1006252800→943879460B（-6.1986%，少62373340B／组件调用）。wall478.12225→368.1825毫秒（-22.9941%）仅描述这四行；A558→398漂移明显，每入口只有两样本，不能授稳健延迟、whole OUTCOME或整机提速。分配是累计计数，不是heap peak；未证明RSS／峰值降低。

固定input为6828334B／SHA `f8ca5b5c2438314b777b11821c22dca4df45e0d6d8a3c2dfffb28d2b3e8d738a`，同一绝对CAS路径、head sequence13、pending body和receipt四行一致；它不是旧Main03的6831978B输入。四行没有新Native软件提交或查询（fixture此前已实际软件执行一次，读写计数固定为1／10）；Game／Native live／HTTP／SAVE为0。

## 全成本、失败保留及限制

组件setup10.5314毫秒、窗口至报告前1.7911414秒，完整JUnit suite135.099秒、记录actor137.5975028秒、outer138.5260434秒、OS process累计CPU100.9375秒分别报告。记录actor含父端记录／验证，不能叫精确child lifetime；OS CPU也不能全部归到此组件的当前线程。报告构造／写盘、先前fixture／规划／effect／cold positive、后续OUTCOME／MATERIAL及所有等待都保留，不将1.79秒替代整个用例。

首次production BEGIN 07:20:04.433820Z→最后组件close 07:46:04.346552Z完整1559.912732秒，包含编测、审阅、配置、等待；更早D源准备另保，不冒称已量化完整开发耗时。三个编译记录actor依次6.799325／6.3189255／9.9864905秒。所有phase真实0退出、无timeout且close释放；不额外跑JVM挑绿。

原business command／request120秒只创建一次，未刷新。由于旧Applied实耗142.48秒，Root在measurement BEGIN前将原D提案150／180调整为纯软件210／240窗口；不是失败后续期，源码不变。实际command deadline为07:46:05.849477300Z。保原D草稿、所有冷／慢行和原件，未因数字调整输入或删行。

一次owner Python JSON包装错误发生在候选执行前，0candidate write／0JVM；修为ASCII D脚本后落候选，错误回执保留。新Test初Ready预计3类漏掉Store匿名TransitionAuthority，Native在BEGIN前指出，Ready02纠正为4，源码未改；不计JavaRED。组件D草稿／formal Ready和后到软件窗口分别存档。循环内首错尝试finally写partial并停止，try前setup失败可能没有组件报告，必须保外层ACTUAL／JUnit／stderr；不能只据row.completed授过，须global completed＋全post检查＋JUnit成功。

命中多保留首Obj／Observed／完整raw／query图，并新增一个ExactRef引用；额外防御clone与完整memcmp没有删除，存活／GC代价真实计入。任一ref或bytes条件未命中走原Stage完整路径，任何物理、header或frame失败不换lane。条件限私有parse闭合immutable DATA与项目冻结codec默认配置，不泛化为任意可变树／配置修改或来源许可。

具名原件位于 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-outcome-original133/` 与Native对应目录：

- `production01/SOURCE-READY01.json` 6348B／`b77a5f88a1fcd50f4bcc5319f6a985101832bb99b4f929e196e8a3dd671f166c`；两源逆向与unchanged blocks证明保留。
- `test01/TEST-SOURCE-READY02.json` 7217B／`2ae43db0f441932663334eaf2efcfb4d10d0bc7f04ac2bc3c3f2b21c055758ba`；`measurement01/MEASUREMENT-SOURCE-READY01.json` 8275B／`2c2a34ad1b7b7eda3966c7188ff8aba623b7ffe4d375a2c41da5ca288ee59321`。
- Native `p133-outcome-test01/QUALIFIED-P133-NEW2-AND-AFFECTED3-FUNCTIONAL01.json` 68503B／`2fe0f00724572e127d67b11f8509767c8cb6e03fde5676ef25ad916f4c566f77`。
- Native `p133-binding-component01/QUALIFIED-P133-SOFTWARE-AND-SAMEBINARY-COMPONENT01.json` 51942B／`624943ad92714c2c9beb150076d1bae6780feb69c7bedd18afc5f9bda90e7153`；原component report4667B和全部ACTUAL／XML／OS／close保留。
- Root `P133-COMPONENT-CPU-ALLOCATION-SOFTWARE-ADOPTION01.json` 4223B／`afed471cf2cc5a42fbae0176dbd8d6d115d51c2de6dd40c93e18f04e05231a72`，独核六方法／四行／来源／完整family，采用范围明确有限。

源码、软件、正式发表与Runtime分层。本单不授新布局热载、Source／head47、自动游玩恢复、SAVE或10秒目标；后续P134仅独立D候选，不能将Native整段约1GB分配都归给某个重复projection。
