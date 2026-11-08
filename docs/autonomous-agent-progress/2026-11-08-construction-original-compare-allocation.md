# P122：省去intent精确比较前的一次原文clone

本次保留query编码、完整字节比较、cache短路及fallback，只省去比较右侧NativeQuote.original()的一次数组clone。必要2TU／20class及两个既有meaningful affected方法通过，没有新Test／newunique。固定原DATA的主线程累计分配均值711341801→704523144B（-0.95856%），intent阶段61135112→54316456B，约少6.82MB/call，与一次query clone的源成本吻合。

本cohort whole墙钟均值783.496675→678.252425ms（-13.43%）、中位745.26925→661.0281ms（-11.30%）；A1两慢样本和未改phase波动对结果有明显影响。保留为窄分配优化，不能把13.43%全归因于这个约1%的分配减少，也不授持续worker、Runtime或保存日延迟收益。P120 primary与P121独立三pass均保留，不拿后pass替换本对照。

## 仅两个源码点

NativeQuote新增DATA boolean originalContentEquals(expected)，直接Arrays.equals(expected,private original)，不暴露、clone或保留expected；原original()／exact getter、四条合法构造入口、private raw＋SDK pair全部保持。每个入口得到自己的原文数组：small clone、full先clone、外部carrier及内部OwnedToken均用clone getters。存储的private final original无正常可变alias；外部mutable probe也不获得新的原子快照承诺。RawJson已有同模式contentEquals是提供的完整实际合同。

Lifecycle仅把原Arrays.equals(queryBytes,quote.original())改调用该boolean。既有DriverJson.encode(query)仍先执行，cachedQuote.isPresent仍先短路，任何不同字节／无cache仍走原finalizeQuery。所有随后source／frame／candidate／proof／expected／income／cash／canonical body及实际同session归档读写、len／SHA／header／cold核验不改。没有encoder全域等价假设、hash代替memcmp、新缓存／字段／类型或泛化DOM平台；5add／1del反向撤销可恢复原两个文件全部其余字节。

一次真实模型任务使用完整当前两目标＋RawJson合同72818B、强指导task3448B；03:02:20.597082Z POST_BEGIN，200／stop／DONE，6.261943s、TTFT2.2199283s，15755prompt／654output、cached=null。两bounded edit均exact anchor唯一匹配，代码literal采用，无owner实现修正或重HTTP；这不是独立设计见证。

## 必要验证与元数据勘误

Native实际只编OrdinaryWartimeConstruction与Lifecycle两个TU，20class（12＋8），exit0／19.5094797s，无新class。原ACTUAL的execution_counts.source_tu_count误留模板3；实际source_tu_names、config.sources、javac显式两个source tokens、两个top、OUTPUTS.SourceFile均证明2。原ACTUAL不覆盖，METADATA-ERRATA-SOURCE-TU-COUNT01.json另记3→2，0额外JVM；不能写本单零元数据误标，也不把它算Java编译RED。

只复用P117已编译的两个受影响旧方法：fullResolvedIntentMatchesOldFinalizerBodyWithExactPrecisionAndOwnedCache与unequalRawQueryWithPresentOtherInstanceCacheUsesOriginalFinalizer。同JVM2P0F0E0skip，actor19.3261638s／XMLsuite15.824s／close03:09:36.489967Z、reservation=false；0Test TU、newunique=0，未重其small方法或新增镜像Arrays探针suite。它们验证实际fullLoaded canonical intent、高精度原文及不同raw／proof时fallback，原件／body语义保持；编测、正式发表与Runtime装载继续分层。

## 同一主DATA边界，保留顺序波动

仍用未改Main03及同6831978B input／Q2／source／绝对CAS／EXPECTED。A为P120B18相关SDK12＋P117Lifecycle8旧完整族，B仅换这两个新完整族；其它Query／Codec／Source／Policy等相同。无Main／Test重编、新PREP、DATA deadline刷新、P121wrapper或P119 flags混入。logical A0／B0／B1／A1对应raw B0／B0／B1／B1，原label不改，actual variant由完整family／first-origin／ordered CP区别；cached=true不是新comparator计数。

四独立JVM，每个2warm＋4measure，CPU1／384MiB／90秒。全部8warm／16measure、24call及所有慢点保留；marker等于原EXPECTED，whole等于11个disjoint phase的wall／CPU／allocation之和。真实CAS preserve／readback／cold resolve、独立固定DATA Q2、pure intent、全部clone／memcmp／classinit／JIT／GC及setup／process／outer都计入或分列；无forceGC／过滤／挑绿重跑。原11个固定物理文件不变，四新cards独立记，不称整个FS相同。

| 指标 | 当前P120基线A | P122 B |
| --- | ---: | ---: |
| whole墙钟均值 | 783.496675ms | 678.252425ms |
| whole墙钟中位数 | 745.26925ms | 661.0281ms |
| whole当前线程CPU均值 | 300.78125ms | 273.4375ms |
| whole allocated均值 | 711341801B | 704523144B |
| whole allocated中位数 | 711341848B | 704523200B |
| intent allocated均值 | 61135112B | 54316456B |
| actor均值 | 13.33278225s | 12.6861464s |
| 序列化前main均值 | 9.97910855s | 9.51459265s |
| setup均值 | 2.3775377s | 2.44281665s |

per-JVM measure均值按固定顺序为A0 679.4587、B0 710.83795、B1 645.6669、A1 887.53465ms；B0比A0慢，A1的1087.9297／967.3439ms两点未剔除。未改construct／resolve／Q2全mode均值130.796525→125.1792、295.8794375→258.846075、113.7689375→85.815625ms，intent119.628275→99.5593375ms；不能把未改phase的整体变动当作comparator单点因果。分配前三phase基本保持114953499→114953488、278145497→278145550、114994648→114994640B，intent少6818656B／whole少6818657B的对照更直接。

ABBA从03:11:47.833495Z至A1close03:12:45.906651Z，58.073156秒含phase间隔；四actor合52.037857300136秒。首实际生产BEGIN03:06:20.507759Z至末close385.398892秒包含编译、affected验证、准备及等待，此前模型／源码研究另存，不将具名生产起点当作最初研究开始。所有setup／main／process／outer／OS峰及错误／勘误原件保留；累计allocated不是heap／resident。

Native根D:/ck3-state/resume91-native-integration/p122-consumer-execution01：
QUALIFIED-P122-CONTENT-COMPARE-AND-CONSUMER-DATA01.json36297B／730bacb43e2ed0c00ed941372b499346d9eacf8f125840f5601f6f6e59d62de7；
全raw417057B／7c1af7b64d5ee144f95c6b694ba4fea1e8c95c0e988b0af4b292c66cf9012f47；
identity6593B／ce7ca0bc31b2f86e3037bfdd47b8f11f2eb468bd35b4b3e09e7218b7c2b341d3。
原TU标签勘误1410B／ae6976daeb7c4b3c7d71b2f480d35fbea4d638d4984dfe972c4f973977709ba1另在p122-content-prod01。
Root全24call proof112235B／64be5263c89c86ed32070d75d485c259fb028bd6a9d7f7dbde17a8aa308d0eb2、51pin独核390B／c6966eafb98deb68ecb0ae5d2e64cc27d5f0deb2172881debd989b361e3cd2a8另存；owner也只读核过全部raw／phase sums／close。业务源根construction-original-content122，原模型与literal edit、全部旧身体恢复证明保留。

新增public方法的软件通过不授当前Runtime可替换或装载；没有Native动作／新确认保存日，10秒目标仍未达到。下一P123另单元继续归档readback内容比较的第二次clone消除，源码验证与本单文档并行，第一真实load／lenSHA校验仍在，不扩大为全parse平台，也不作本单正常发表的前置。
