# P118：减少派生查询重复解析的分配，whole墙钟未改善

P118在同一完整DATA消费者中确认主线程分配下降约130.09MB／call（-14.58%），whole墙钟保持在相近水平，不能称延迟或端到端提速。均值755.6689125→756.1310875ms（+0.06116%），中位768.7978→768.68315ms（-0.01491%）；actor均值12.6033036→12.22259645秒是本cohort进程观察，不能外推稳态或Runtime收益。基线是[P117当前B](2026-11-08-construction-intent-allocation.md)，其本来也是分配改善而未确认墙钟改善；不累加百分比、不复跑挑选绿色速度样本。

优化仅覆盖SDK内部第三遍多MB查询解析。旧路径在app物理full读取及DriverJson完整解析之后，ObservedRequest再解析完整outer；其quoted分支编码已私有的queryNode，NativeQuote.full factory随后又解析该派生query做角色投影。新路径保留前两次完整解析及全部外层custody，只把第三遍改成受限标准节点快照与同源raw／SDK派生。

## 源码与封闭DATA合同

三处既有SDK源新增一个nested QueryProjectionCarrier，private构造器只由单Node工厂创建，存private owned raw／SDK byte[]、getter clone，不持久保留JsonNode。NativeQuote的package-private入口仅消费该封闭载体，原private(raw,sdk)配对构造器未开放；原public small和public full byte工厂body保持。ObservedRequest只替换其内部已私有queryNode的encode→reparse调用链，其完整outer原文、cash／financing／当前header缓存均保持。

ConstructionQueryCodec把唯一八字段／schema／snapshot角色算法提取到private projector。旧byte方法仍FullJsonTree.parse64MiB后delegate，预算、次序、输出和拒绝行为保留；这是body refactor，不谎称方法源码逐字未动，也没有复制两份白名单算法。派生query编码仍原64MiB、SDK投影仍262144B，不借P116融资wrapper的256MiB额度。

公有单Node工厂先递归重建私有ObjectNode／ArrayNode，原成员／数组顺序保留，只共享FullJsonTree实际产出的不可变标准scalar：exact Text／Bool／Null、exact BigIntegerNode且payload为exact BigInteger、final DecimalTokenNode。custom subclasses、Int／Long／Double／Decimal等非该新域节点、Java null child／key、null text／integer payload均拒绝；JSON NullNode仍保留。opaque空串／长串／escaped lone surrogate不借StrictJson.text新增拒绝。该Node域显式受限，不能称接受任意Jackson树，更不是source／Native／动作许可。所有快照、完整编码、载体及getter clone成本全部计入。

真实模型单POST于01:25:46.099000Z的POST_BEGIN事件开始，17.6957008秒／200／stop，TTFT2.0760856秒、14560prompt／2586output、cached tokens=null。仅partial-core采用；owner补全其遗漏的exact容器／null／payload／class检查、actual imports，把不存在的StrictJson.array改为已有JSON.createArrayNode，并明确精确API名和实际parser容器计数。未为显然错误重HTTP，也未编译原错误稿。深度边界曾有Reviewer只看value递归的静态误解，随后实际2.21.7 stream classfile及第一次新JUnit的oldbyte oracle确认；原HTTP／Task未改写。

## 六个新方法与边界实测

必要3SDK TU一次实际green，17class（原16＋新carrier1），actor5.649052秒。新Test首编因故意被拒的ObjectNode／ArrayNode匿名子类继承deepCopy产生两条unchecked warning，在全局-Werror下RED，0class／0JUnit；只对该负例方法局部SuppressWarnings，不改全局-Xlint／-Werror或生产。必要changedTest TU通过后，普通五方法同JVM5P，独立大case另JVM1P，合计6unique跨两个JUnit JVM，非同JVM6P；无旧绿套件重跑。普通actor5.9714668秒／XMLsuite3.984秒，大caseactor6.2312174秒／XMLsuite4.107秒，console时间另存。

普通正例先raw→FullJsonTree.parse得到标准节点，避免把默认ObjectMapper的IntNode误称新域正例。真实139历史行的约6.8MB outer通过实际Observed full入口，对旧public byte路径逐byte比较派生query原文、SDK、exact finalizer及fixed whole typed result，并比observation／selected／kind；高精度小数、负零／指数、原顺序和opaque值保持。caller节点／raw数组、carrier及quote getter返回数组变异、独立两实例不会串用。13个不支持／custom／null payload反例按新域拒绝，不冒称其相同JSON表达在旧byte域也必拒。

深度测试用手工ASCII placeholder替换生成raw，避免先被FullJsonTree.encode挡掉而未测旧parser；另独立手工构造Node树。object／array共12行实际oldbyte oracle验证scalar value-depth64接受、65拒绝，empty／nonempty container-depth63接受、64拒绝，再核新Node同结果；键不另加层。未知snapshot扩展仍仅由同一角色投影省略，完整Native envelope／consumed子树与其原262K边界不减校验。

独立大case实测literal query raw67108863B、重编码67156863B：旧public byte入口仍可selected并保原raw，但旧Observed的FullJsonTree.encode(query,64MiB)那一段和新Node64MiB均因明确lease超限拒绝。这区分旧byte原域与旧derived域，不能断言所有旧byte接受的Node新工厂都接受；也不要求巨型manifest通过原动作上限。测试中256MiB编码只观测膨胀大小，生产query仍64MiB。大case1CPU／Xmx1024MiB／90秒，owned OS峰working set983629824B、pagefile1151549440B，均不是heap实占；其高峰和完整耗时与性能cohort分列。P116纯融资near64M案例不受quoted分支影响，未机械重跑。

## 同Main、同物理DATA完整对照

沿用Main03原binary（26020B／6660ee3c3ecf375b620eaeb63b5355c1b8cb3763dbe8e9cffbeaa0111ddd1da0）、原6831978B input／Q2、source／绝对CAS／DATA／EXPECTED，无Main重编、新PREP或刷新旧DATA描述deadline。A是P117成功B的旧SDK16族，B是新SDK17族；A不声明不存在的carrier origin，B显式核第17class。共同Lifecycle／Source／Policy等依赖不变，新Test不进入ABBA CP。logical A0／B0／B1／A1对应raw label B0／B0／B1／B1，raw不改写，实际variant靠完整family SHA、first-origin和ordered CP。

四独立JVM，各2warm＋4measure，CPU1／384MiB／90秒。全部8warm／16measure、全部错误／慢样本保留，无forceGC和速度assert；24call的cached=true／warm=true／全部marker等于原EXPECTED，whole等于disjoint阶段wall／CPU／allocation之和。每进程新allocation card单记，原head／anchor／lock／store／payload／commit身份保持，不称整个FS字节相同。所有构造、snapshot／clone、真实CAS保存读回、cold resolve、固定DATA Q2、pure intent、writer获取释放、setup／main／process／outer均计入或另存。该窗口不是实际Policy.evaluate／revalidate、Native fresh READ、SEM准入或owning publication。

| 指标 | P117基线A | P118 B |
| --- | ---: | ---: |
| whole墙钟均值 | 755.6689125ms | 756.1310875ms |
| whole墙钟中位数 | 768.7978ms | 768.68315ms |
| whole主线程CPU均值 | 333.984375ms | 328.125ms |
| whole allocated均值 | 892,130,235B | 762,038,705B |
| whole allocated中位数 | 892,130,276B | 762,038,912B |
| construct allocated均值 | 175,216,264B | 131,852,464B |
| resolve allocated均值 | 338,408,294B | 295,044,468B |
| Q2 allocated均值 | 175,257,552B | 131,893,616B |
| process actor均值 | 12.6033036s | 12.22259645s |

三个受影响phase各约少43.36MB；分配缩减不等于延迟改善。construct／resolve墙钟均值146.1325375→129.987775、269.0089625→237.276975ms，而Q2反向111.1359625→145.7206875ms；未改intent也102.6909625→132.789325ms、分配均值完全同61135112B。preserve98.4555→79.636575ms等未改phase波动同样保留，不选择性归因，也不把actor的此cohort观察称稳态提速。

四actor合49.651800099993秒；ABBA含阶段间隔54.786904秒；从首生产BEGIN至末close1024.723985秒包含warning修正、Native preBEGIN元数据拒绝、编测、审阅及等待。后者不包含此前模型和材料准备，相关原件另存，不把任何窄窗口充作完整保存日分母。Native旧helper basename／execution01遗留schema在claim／JVM／BEGIN前被拒，0新增Main JVM；execution02只改机械metadata，原件不覆写、不归模型或Java功能失败。

业务证据根D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-derived-query118。Native最终QUALIFIED-P118-DERIVED-QUERY-AND-CONSUMER-DATA01.json51659B／9b639bb91f96ab07e9c3627f8d173d9ca77abe554fa1fca3b8cebdc3cc5af697；全样本411118B／b00912195d62d9a34283808ce23a193d0861f4493386363e8629ce31c1547161；identity6593B／c92cb29ab3086a3ae558227dab3c4f08779f52b159736e582a5b11326322a710。Root逐件核24call、原EXPECTED、phase sums和close的独立proof112188B／b3cd9a00c0e264600552807b30821578450410d1dba21b384eb46f39901e3faf另存。

本次正常保留为窄分配优化，whole墙钟未改善；原16族也独立保存。17类软件通过不授新增carrier可在当前Runtime装载，未部署或新增SAVE，10秒／已保存游戏日目标仍未通过。P119先安排一次独立有界软件JFR／GC诊断厘清GC／JIT／其它JVM线程CPU与主线程wall差额，明确不属于对照速度cohort，不修改Main／Java、重跑挑绿或盲加缓存；结果再决定后继，持续目标继续。
