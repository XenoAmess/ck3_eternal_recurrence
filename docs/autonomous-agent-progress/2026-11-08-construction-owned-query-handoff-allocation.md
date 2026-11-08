# P125：保留封闭query owner以减少分配，延迟未验收

本次仅让NativeQuote保留内部封闭不可变owner，省去交接时的完整query raw clone；公有original getter仍返回副本。必要2SDK TU／15class与两个旧meaningful affected方法通过，原Main03固定24call的主线程分配均值704495803→684040342B（-2.90356%，约少20.46MB/call）。保留为窄分配优化。

墙钟／CPU结果混合：whole均值738.9238→721.8332625ms（-2.31%），中位744.932→747.73015ms（+.376%），当前线程CPU均值294.921875→296.875ms，序列化前main均值也略升。不能授latency／CPU通过，更不授新对象layout在当前Runtime可热替。全部慢点保留，不重跑挑绿；与P123两个B都明显变慢的负结果分开，P123仍未采用。

## 闭合owner合同及真实留存代价

只改两个既有SDK文件，18add／4del，无新类型或新增公有API：

- NativeQuote加private final OwnedQueryProjection owner。raw模式仍保留非null original、owner=null；soleOwned模式original=null、owner非null，由新private三参构造器硬性XOR检查。旧private(raw,sdk)签名仍private，仅委托该三参构造器，共用原有唯一SDK decode／policy／selected finalizer／cache实现。
- 旧small public构造器保持decode→caller clone→policy／selected finalizer和异常顺序，仅加owner=null。公有byte full与外部B2 carrier路径仍raw模式。soleOwned经过private(token)只取SDK clone，不复制raw；没有package raw＋SDK accept／callback／任意Node mint。
- original()在raw模式clone原数组，在owner模式调用原token clone getter；originalContentEquals委托相应private bytes精确比较。token仍只有两个private final byte[]、sole private constructor和两个原clone getter，仅增加package boolean比较，不存DOM／probe／consumed flag。

这是保留封闭不可变owner，不是破坏性的单次转移。正常API不能取得或改token的数组，假设内部重复引用也只共享私有不可变字节。所有query raw／derived64MiB、SDK262144B、公有B2节点域、clone约束、outer完整parse、融资header、canonical命令／原件hash及实际sameSession归档／cold／frame／Guard保持。旧private full构造器的body发生明确共享重构，不声称整段源码未改；唯一selection／finalizer规则本身逐字保留，没复制算法。

代价是NativeQuote多一个reference，token及其SDK array与quote同寿命；实际样本SDK由源派生约2076／2122B，接受域可能接近262144B，不能拿2KB当全域上界。token raw替代旧保留raw clone，不保留parent DOM／ObservedRequest或静态缓存。三个factory的静态raw payload规模约20,455,960B，只是来源估计；数组header／alignment及owner引用成本以实际分配结果为准。累计分配不测精确live heap，新增留存对GC／进程／OS峰的影响留在完整窗口，不称留存免费或已证明heap无增加。

## 模型length整份弃用，owner独立实现

真实单POST于03:39:25.199961Z开始，200／DONE但finish_reason=length；38.0223575s、TTFT3.4741467s，25104prompt／6000output、cached=null。完整当前七份源码原件105084B含实际Query／contracts／P120和P117测试约束，强指导task6565B，有限max6000。回答整份UNUSED_LENGTH_DISCARDED，CONTENT从未读取／解析／提取，不拼接补续、不追加或扩大HTTP。不能称模型源码采用或partial采用，也不是Java编译失败。

owner完全按调用前Root／Reviewer已审设计和当前源码独立实现；旧D设计、失败REQUEST／SSE／usage、MODEL-DISCARDED01保留。Root有限源审后仅把fromOwnedProjection旧clone说明改为准确的“保留owner／仅SDK clone”，不改实现。P123拒收candidate不在当前基线，Source原9567B／ab1083…保持。

Native只必要Ordinary12＋Codec3两个TU，exit0／5.8942683s，newclass=0。只复用ConstructionOwnedQuery120Test的ownedRouteHasClosedMintAndIsolatedExactBytesAcrossInstances及ConstructionIntentResult117Test的fullResolvedIntentMatchesOldFinalizerBodyWithExactPrecisionAndOwnedCache；同JUnit2P、actor10.675269s／close03:47:44.292237Z。旧Test0重编／newunique0，不改P120 token字段／private constructor反射标准，不新建suite。actualfull raw／SDK／fixed结果、getter变异／两实例及fullLoaded canonical旧oracle继续成立；未把离线通过当Runtime资格。

## 原Main、原物理DATA完整固定对照

A为P122 NativeQuote12＋原Codec3，B为新两族15；其它Query3／P122Lifecycle8／旧Source3／Policy／Main及CP相同。原6831978B input／Q2／source／绝对CAS／EXPECTED不动，无Main／Query／Source／Test重编、新PREP、DATA刷新、P119flags或P121后pass替换。logical A0／B0／B1／A1仍对应raw B0／B0／B1／B1；真正variant由完整families、first-origin、ordered CP核验，原cache标记不假称owner mode计数。

四独立JVM各2warm＋4measure，CPU1／Xmx384MiB／90秒；全部8warm／16measure、24call保留，无forceGC／过滤／后继挑样。marker等于原EXPECTED、warm CAS／cache均true，whole等于11个disjoint phase wall／CPU／allocated之和。实际归档写入／full读回／lenSHA／cold resolve／独立固定DATA Q2／pure intent及全部clone／比较／new field／JIT／GC成本都包含或另列，原固定物理文件和四新card分开记。

| 指标 | P122当前基线A | P125 B |
| --- | ---: | ---: |
| whole墙钟均值 | 738.9238ms | 721.8332625ms |
| whole墙钟中位数 | 744.932ms | 747.73015ms |
| whole当前线程CPU均值 | 294.921875ms | 296.875ms |
| whole allocated均值 | 704495803B | 684040342B |
| whole allocated中位数 | 704495680B | 684039756B |
| construct allocated均值 | 114953502B | 108134840B |
| resolve allocated均值 | 278142100B | 271323453B |
| Q2 allocated均值 | 114994640B | 108175944B |
| actor均值 | 13.4717538s | 13.35187075s |
| 序列化前main均值 | 10.18666915s | 10.23391315s |
| setup均值 | 2.6188894s | 2.44042675s |

per-JVM whole均值A0／B0／B1／A1为725.090225／677.173725／766.4928／752.757375ms；B0较快、B1较慢，分布重叠。construct／resolve墙钟均值139.389625→118.428025、275.8285→260.33785ms，而Q2反向100.3144375→121.1611625ms、intent104.8726375→111.0139125ms。未改phase波动也全留，不将均值改善全部归因owner，median／CPU／main反向明确不授延迟或CPU通过。构造、resolve、Q2各约少6.82MB，whole少20,455,461B与三raw clone的量级一致，未把所有剩余大phase分配当成本单收益。

ABBA从03:48:20.300534Z至A1close03:49:19.184674Z为58.88414秒含间隔；四actor合53.647249100031秒。首实际生产BEGIN03:46:24.413833Z至末close174.770841秒含编译、affected验证、准备和等待；模型38.0223575秒及此前设计／owner实现另存，不把首编译当最初开始。累计allocated不是heap／resident，所有setup／main／process／outer／OS峰均保留。

Native根D:/ck3-state/resume91-native-integration/p125-consumer-execution01：
QUALIFIED-P125-OWNER-HANDOFF-AND-CONSUMER-DATA01.json49035B／5ab32dc92f6e0abeb08113ec7964b3f7385b3dbc294e10d219bc8b31d18c7ad4；
全raw410437B／4d3bcdf41a7aaeffa9f8c7fa7b84dcb97ef8d6009920c07ea07ebb6bc3d997aa；
identity6593B／ff7f2eda38ad348e45e982cc37c44e9da346c5ecf747c7b4cd0629f88f60b925。
Root全24独核proof112184B／e348c86f42d7889f1e758fb2f789e654e212821c5eb0566cdfcd5286e6b4758c，后到allocation-only采用回执1927B／f75a59d69bbb1abe7da7e02581a0a24957ea68bef62740678a167ea99b5d2c46另存；原pendingRoot qualification不覆盖。业务根construction-owned-query-handoff，模型未采用与owner实现各有原件。

正常保留为软件分配优化，current baseline可标qualified-software-not-latency，Source仍P122旧原件，不复活P123。没有实际装载、Native动作或新增确认保存日，10秒目标仍未通过；后继先D-only研究更大真实成本，不为当前约2KB SDK重复finalizer造泛化平台。
