# P183：长度标量 API 与正常 DATA 计数等价的限定源码采用

Root批准本单元有限软件源码采用：RawJson增加一个纯长度标量，NativeEffectRegistry只在原116行计数位置使用该标量。依据分别为完整旧Code／Guard保持、预冻结API组件门通过，以及原有完整公开软件case真实1P。本单元不把这三层合并成116分支已经执行、真实兼容结果有多大、调用频率或caller提速的证明；这些仍 **NOT_HELD**。

本次正式切点离线软件仍actual current357，后继359候选与Root独立实际软件采用另账，不预填实际装载、Runtime或SAVE。新增public方法是结构／反射可见API变化，不能称body-only热更已验；没有Game、Native live、GET、P100、账本、部署、装载、launch或热载操作。零新增确认保存日不报有限秒／日。

## 精确两叶与不可变值边界

[RawJson.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/action/RawJson.java)基底5806B／`4b80f8ff4c407cd860f3011a246e085df716f117b2ab5cd1ba5f4fd3b51b866b`，新5855B／`b580c8f475fb78f73d991bae600bd46b33a82079868a526af3ec46fe455b597b`。只在原47物理行的原bytes()声明之后增加 `public int byteLength() { return bytes.length; }`，99行保持。旧fields、构造器、factory、bytes()防御clone、全部parser／Unicode／协议数值预算／equals／hashCode／contentEquals方法体逐字保留。这个方法只暴露已有值的长度，不授有效帧、身份、来源、权限或Guard资格，没有新field、type、helper、cache、raw+typed carrier或trusted flag。

[NativeEffectRegistry.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/effects/NativeEffectRegistry.java)基底11551B／`b92b0335e2e0889e7a9b57d6391653ab75edfab835572f0c07757f3d5017581f`，新11549B／`539e4574544bead61a8d8ed4a2faba8a62a9e6092bbd0d0bd4377d54ca30cf1f`。仅116行记账RHS `result.bytes().length` 改 `result.byteLength()`，148行保持；原compatible.put仍在记账前，109行ActionEffects.validate、111–115冲突／数量／材料字节Guard、**115行首份防御copy**及短路顺序全部原字节保留。整叶inverse分别精确恢复两份基底，没有修改Guard／parser／hash／oldencode算法或输入校验。

RawJson实际为final类，唯一private ctor把input.clone写入private final bytes；旧getter只返回clone。数组长度不随内容改变，新标量与旧clone.length在正常已构造不可变DATA域相等，不把比较结果跨调用缓存。去掉一处分配改变OOME等资源失败机会，不承诺全部资源失败时序等价、峰值或GC改善。原getter仍防御复制，也没有把内部数组泄漏给caller。

两叶formal来源与source307分清：RawJson整字节不同，仅CRLF归一化后LF exact；Registry wholebyte exact。实际C0原compiler命令、完整编源绑定及原flags **UNPROVEN／NOT_HELD**，不从SourceFile或相同源文猜测。本次新源码则由实际受控编译精确绑定，旧Code／元数据逐项比较，不把它扩成全SDK谱系授信。

## 真实最小编译与旧行为保持

生产分根顺序为Raw1TU1，再以newRaw前缀编Registry1TU5，没有copy／合并class根，没有旧绿Main／SDK／Test重编。actual RawJson7110B／`1881791b630c1942c5c51ce0576dcedb3da3cd61bfe08296811939e073024139`：旧14个方法Code及resolved refs、旧API声明、fields、decoded参数与Nests保持，唯一新()I标量Code6B。Registry实际5族，四nested SHA旧同；Top21345B／8949f066…，其余16方法Code与refs相同，目标lambda158→157B仅原148位置改scalar及必要branch offset，机械Code inverse恢复旧体；原validate、首clone、require、Map.put与记账次序核同。

没有从这次typing授予动态分支覆盖、来源身份或性能。Raw增加public方法这一结构差异始终保留；软件基线、正式Git、JVM装载与Runtime采用各自待真实回执。

## 独立 API 组件：first32，不造兼容结果

[RawJsonLength183Test.java](../../tools/performance/rawjson-length183/RawJsonLength183Test.java)原受测字节11466B／`881c58026fce2d3f0aed70d72a03452f5ca0de493d8e8a93596ae58ca9434b9f`，只放显式tools/performance，不进入默认Maven自动Test，不改pom或隐式skip。必要新Test1TU1与唯一API JUnit实际1P、0F、0E、0skip，case **2.139s**、Jupiter engine **2.164s**。实际Raw1来源SHA与测试class逐项核同。

输入直接读取已资格P164物理packet **3400700B**／`4084dcb52ed1ecafadf7fbe6fd11998ff2ed2c06fd22ac077025e519044e4e5d`；只按LE32拆出既有valid JSON body **3400696B**／`3f05b00dbe620b779df9b86986ced9e702885ad2bee0c3dfc91504c26bc3cd19`，不parse／reencode另造输入。它含既有3400000字符opaque扩展，不代表真实compatibleResult或自然分布。

同一个共同new API-extended RawJson实例上，A调用原 `bytes().length`，B调用新 `byteLength()`；**A是旧getter行为控制，不是literal physical357**。parent只前置newRaw1，不混入新Registry。compile358／run359是测试CP条目数，不是离线软件359已经采用。

固定首8ABBA32／各16，setup只做文件读取／SHA／framing／RawJson构造和来源检查，getter或scalar额外warmup为0。target仅直接旧getter.length或新scalar及同一分支；只消费int，没有把clone数组强迫逃逸、blackhole或人为禁止合法JIT消除。若旧clone在合法JIT下消除，也必须保实际结果，不换输入、增N、预热或重采找绿。原件SHA、长度、每行endpoints在target外而在enclosing／whole内后验，冷首与所有outlier全留。

32之后仅三个小public DATA case：`0`为1B，`{}`为2B，含汉字和emoji的JSON文本为12个UTF-8字节。它们合计3ctor、3scalar、6getter，分别证明ctor后改input与改getter副本均不影响内部值，两个getter返回不同数组且长度一致；不是性能样本、NativeWire有效帧或权限证明。总setup大Raw构造1次，Registry.observe调用0；没有伪compatible、Attempt、Guard、ledger、adopter或私有issuer。最终原物理packet重读／SHA与内存body后验保持。

预冻结门为全部功能／原件／来源与旧方法Code资格通过，allocation八组不劣且至少六组下降，target均值与中位均不劣，paired每调用B−A差中位≤0，否则PARK且不补样。实际全部通过。

| API每调用指标 | A旧getter | B标量 | 本次限定事实 |
| --- | ---: | ---: | --- |
| allocation均值 | 3400721.5B | 0B | 八组下降，非整条业务零分配 |
| allocation中位 | 3400712B | 0B | paired每调用差中位−3400712B |
| target均值 | 873287.5ns | 300ns | 八组好；受A7 outlier影响 |
| target中位 | 172250ns | 100ns | paired差中位−187675ns |
| enclosing均值 | 4434950ns | 3497706.25ns | post包含输入SHA和heap观测 |
| enclosing中位 | 3420100ns | 3339300ns | **四好四差**，不替代target |

反向enclosing组2／4／6／7的每调用均值B−A分别 **+238200／+75000／+60150／+277650ns**，全部保留。A7 target **10.9521ms**／enclosing **14.1704ms**明显抬高均值；A0 target0.1869ms、allocation3400864B也保，不把所有冷额外或差异归为单一机制。B的百ns量级接近时钟粒度，保绝对数，不包装成全业务加速比例。

CPU全32测量为0，比例为 **null／UNKNOWN**，不能说无CPU成本或−100%提速。共享heap50684152→64095984B、GC1→2／10→21ms只是同窗口post观察，不是A／B独立retained heap、Java峰值、GC因果或OOME保证，无强制GC。setup文件读取2.276ms、大Raw构造386.4962ms、三个小case0.9634ms、最终文件后验6.6282ms、before-report595.24ms均保；before-report不含报告materialize／write／JUnit尾部与pre-method成本。

## 现成完整 public 软件回归与116未持证

另获独立授权后，原cached P153 Test10、原APPLIED软件场景与唯一完整方法真实再过 **1P、0F、0E、0skip**：case **109.566s**、Jupiter engine **109.598s**，CLOSE **2026-11-09T11:20:11.561551Z**，exit0accepted、inputs unchanged、fenced／released。没有新编旧Test、Main、SDK或support，没有JFR／Tool／新sample；原business120秒、deadline与原断言保持。CP360逐序为cached Test10、新Raw1、新Registry5、exact current357尾；新6及旧10的全部16物理class来源／SHA和首origin分别0／1／2核同。

这证明新6类链接与现有合法public软件行为回归；输出未带116命中观测，故 **Registry116 dynamic hit、真实compatibleResult尺寸／频率、caller分配或速度收益仍NOT_HELD**。不把API的3.4M输入嫁接给真实兼容结果，不制造私态、伪Guard、补采或额外用例来填这个空缺。

本次109.566s与P182 current357的118.481s是不同JVM、不同环境窗口，没有受控A/B，既不宣称因果提速，也不据先后差异判定源码退化。源码接受范围仅为纯标量API及正常DATA计数等价，不授worker吞吐、全局CPU、Runtime／Game／SAVE。

## 五阶段及所有费用

| 实际phase | actor秒 | operator秒 |
| --- | ---: | ---: |
| Raw1首编 | 8.7665334 | 9.9612427 |
| Registry5首编 | 4.6860657 | 6.6156460 |
| 新API Test1首编 | 4.0691619 | 5.2433657 |
| 唯一API JUnit | 4.1142561 | 5.0622989 |
| 唯一cached完整回归 | 112.0119950 | 113.4239298 |

五actor合计 **133.6480121s**、五operator合计 **140.3064831s**仅资源子窗。Native最早已持切点 **10:07:54.750707Z → 最后CLOSE 4336.810844s → qualification 4844.770836s**；更早实际起点 **UNKNOWN，不记0**。初始FQName／路径／helper／语法／属性／regex／inverse元数据准备错误、source与owner调度、Root审阅及等待成本全保，不拿actor子窗掩盖完整费用，也不盲加重叠epoch。

原D计划拟JUnit384的历史完整保留，Root在API运行前选定CPU1／Xmx192，实际API按192执行；后置完整case按原P153 CPU1／Xmx384、child210／outer240运行，两种scope不混报。四个API业务properties只packetInput／rawJsonRoot／rawJsonSha256／reportRoot，先前口算第五项的消息已更正，未变源或增加隐藏输入。原报告CREATE_NEW／外置existing-empty根／TempNEVER／262144B上限及primary+suppressed保全；原plan pending产物字样保当时事实，后到Ready绑定实际Raw1，不轮换源或样本。

whole OS kernel CPU49.609375s、user26.484375s保原记录；原P153 OS结构没有exit FILETIME等字段，OS child lifetime／相关creationMatches缺口仍 **NOT_HELD**，不拿别字段冒充、不为补数字新查进程。报告序列化、JUnit尾部、JNA、资格与Git费用按实际另层保留。

最终Native静态metadata **2551216B**在4MiB内（budget自件前2549279B加该1937B原件），原guarded fixture **38304786B／343文件**在64MiB内；JNA DLL273408B及全部其他operator／tmp均计metadata，不把all tmp排除或重分类。所有原件／准备错误保留，无删除或截断。静态快照和原Guard不证明连续metadata硬峰值或Java heap peak，未知仍UNKNOWN。

## 可核原件

- `R/P183-FINAL-LIMITED-SCALAR-API-COUNTER-SOURCE-ACCEPTANCE01.json`：7392B／`7916e18ac07501499188b5b3c0d0aaa8bbea540edabcf8c0b63693fab5d14105`。
- `N/p183-current-integration-regression01/QUALIFIED-P183-WHOLE-REGRESSION-API-AND-ALL5COST01.json`：127742B／`9907fa57b9596e2310ae891cacddde2bdd09091029fff65301d2464a17cbd54a`。
- `N/p183-rawjson-length-test01/reports-component/p183-rawjson-length-component-fixed32.json`：21654B／`2be4a06f1b5e30a37849fc35b2eccb328c13781a9b280ae13cb68b9cf79892c9`。
- `J/construction-rawjson-length183/OWNER-ACTUAL-API-FIRST32-REVIEW01.json`：14576B／`d1281a2f787954e6f7cc49c5b354c4021fd073ea86f58a758f6aef69ee7aa473`；同根 `OWNER-API-AND-WHOLECASE-LIMITED-RECOMMENDATION01.json`：15194B／`f4050c109a3462900779870655936d0251ae3592164643e2f7002f4c9b4e6bf1`。
- `N/p183-rawjson-length-prod01/QUALIFIED-P183-STAGE1-RAW1-API-OLD-CODE01.json`：36178B／4e83a970…；同根split资格42996B／9dce7f99…；完整旧Code、元数据、原freeze范围与实际6类pins均可回查。

N、R、J是隔离证据根。只发表两生产叶、受测Test和本单元／日／周记录；不改AGENTS／CI／pom或其它Source，不复活旧PARK／UNKNOWN或P100拒绝主题。正常源码Git、后到软件359独立实际采用与Runtime严格分别记账，后继研究不以本文档ACK或发表作为停工点。
