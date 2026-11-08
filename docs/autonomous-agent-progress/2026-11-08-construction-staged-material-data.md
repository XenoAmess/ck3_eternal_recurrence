# P129：私有解析暂存复用，当前线程 CPU／分配改善

Root 决定保留 P129，标签限定为同输入闭合 DATA 路径的当前线程 CPU／分配优化。本轮测量调用 wall mean／median 改善；完整软件记录 actor（含父进程验证）的耗时反向，完整 child JVM wall 是否改善尚未证明，全进程 CPU 也未通过。它不是自动游玩、Runtime 装载或新增保存日性能验收，不把旧轮百分比相加，也不重跑挑绿。

这是一项具名授权的 owner-original 四叶有界重构，0 HTTP／模型调用。P128“现有 API 无闭合桥”的 PARK 结论保留；本次通过必要的小范围重构建立施工专用暂存，没有共享 DOM、任意 raw／typed pair、callback 或 public trusted flag，也没有复活 P123 负结果或 P124 tiny SDK carrier。

DriverJson 的原 private model 完整 body 只搬到已有 planning-runtime 的 OpportunityJson，递归方法名是唯一正文替换；Driver 保原 depth 参数委托，normalizedModel 不从 0 重算。新纯结构转换保留 StrictJson 的原异常类型／文本、对象和数组次序、未知字段、BigInteger／DecimalToken、null payload 及 custom BigInteger 既有行为。旧 OpportunityJson 32 层 parser、所有 encode、Driver repeatableEncoding、FullJsonTree／StrictJson parser／编码实现与配置均未改；没有复制第二套模型规则或反向依赖 App。

SDK 的 FullMaterialStage 只有私有 byte 构造器：先 clone＋FullTree.parse，DOM 与 raw 私有持有，公有 model 只返回完整 immutable Obj 并保原“full JSON”根对象强制，finish 为零参数。model／finish／close 同锁；finish 先标记消费，再运行原唯一 private SDK decoder body，成功或异常均 finally 清 Stage 的 DOM／raw 引用。close 幂等、无 checked 异常，只丢引用，绝不 zero／fill 数组；返回的 Observed 仍持有完整 raw，close 不损坏它。重复 finish、close 后 finish／model 明确拒绝，不存异常／结果作隐式重试。原 fromFullMaterial 的 guard／clone／parse 前缀保留，再进入同一 private decoder body，原公开 byte 入口不先走 model。

Source full 分支以 try-with-resources 包住 stage.model → 原完整融资 header exact 检查 → stage.finish；旧 inline、真实同 writer full 物理读、len／SHA、manifest／frame／command、budget、lease 及 P127 Loaded 双 identity／cache 条件保持。header 不匹配仍先于 SDK closed schema／enum／query／cash 错误，root 非 Obj 的原错误位置也保留，失败没有跨 lane fallback。

新增 Stage 对象／锁／consumed 状态、跨模块方法及初始化成本纳入实际窗口。未 finish／close 的外部 Stage 会暂存至多 64MiB raw＋DOM，直到消费、close 或 GC；Source 自身总用 try-with-resources。header 检查前现在较早 clone raw，并同时持有 DOM 与完整模型，失败路径暂存成本不是零。成功／失败／close 的引用清除已实测，但不把字段清除当作已经发生 GC，也不把 OS 峰值当作 heap 峰值。

实际首次必要编译 4TU／17 个完整 class，新增 Stage 1 类型：Driver1＋Opportunity9＋Codec4＋Source3；其余 NQ／Query／Lifecycle／Main 没有重编。生产编译记录 actor 7.6591196 秒。只必要新 Stage Test 1TU／3class，加未改旧 Driver Boundary Test 的第一次必要 1TU／2class，测试编译记录 actor 7.9457307 秒；旧 117 与 113 类直接复用。

唯一 JUnit 8 项全 8P0F0E0skip，3 new unique＋5 affected existing；记录 actor 17.3546139 秒、XML suite 14.77 秒。新三项涵盖 small＋139 large 的完整 Obj／raw／native／typed result／exact cache 与原 byte API 对照、caller／getter 隔离及 close 后有效；成功／SDK 异常／close／reentry 的资源释放、同步与私有构造边界；真实 32MiB software CAS 中 header 先于坏 SDK schema／enum／closed shape，正确 header 才到原 SDK 错误，head 与物理原件不变。补充独立 literal depth33／64 接受、原 Opportunity32 拒收、65 拒收，直接断言 -0.0／1e+0、雪与 emoji／成员次序，不只比较两份都经迁移 converter 的结果；坏 query 与坏 cash 先确有不同错误，both 必须 query 先发生。旧 Driver 三项仍守 ChangingInteger 第二次编码值、同 RuntimeException 对象、null integer 与 mixed tokens；旧 117 real-CAS／P127 身份隔离及旧 113 wrong lane／header／物理原件也通过。没有 private authority issuer 反射，资源字段仅仅读。Draft01 合理但缺两项边界，未编跑；原件保留，新 Draft02 补齐，不计为 Java／模型／测试失败。JUnit stderr 1190B 的 NEVER 清理 info 也保留，不洗成空 stderr。

原 Main03／类字节未改，同一绝对 DATA02／CAS／source／ref／Q1／Q2／EXPECTED，无 PREP、刷新或新 benchmark。A 为当前 P127 的旧四 family16，B 仅替换本次四 family17，Stage 只在 B；主名 46／47 及所有 top＋nested 首来源按实际分别核。逻辑 A0/B0/B1/A1 保原报告 raw B0/B0/B1/B1，common cached_api_used=true 属 P114，不假作新 Stage 计数。新测试／Oracle／P121 wrapper／P119 flags 未加入 Main CP。

四个 JVM 各 2 warm＋4 measured，全部 24 行（8 warm／16 measured）保留。原 markers、warm-existing CAS、11 个 disjoint phase wall／CPU／allocation sums、4 个 actual0／终态／资源释放核对通过。固定 11 个物理对象与每进程一个新 software card 分开核，不称整个文件系统字节完全相同。

| 有限 cohort 指标 | A | B | 观察 |
| --- | ---: | ---: | --- |
| 测量调用 wall mean | 637.3447125ms | 592.2611875ms | -7.07365% |
| 测量调用 wall median | 632.25745ms | 592.0166ms | -6.36463% |
| 当前线程 CPU mean | 267.578125ms | 244.140625ms | -8.75912% |
| 当前线程累计 allocation mean | 634779525B | 573605484B | -9.63705%，少 61174041B/call |
| resolve phase wall mean | 243.19525ms | 156.4206125ms | 包含整个阶段，不全归单 parse |
| resolve phase allocation mean | 271324660B | 210122801B | 保留完整模型／SDK 与 harness 两次 raw getter 等 |
| MainBeforeOutput mean | 9.25316875s | 9.25011385s | 约平 |
| 完整软件记录 actor mean | 12.3538781s | 12.90598645s | +4.469%，含父进程校验 |
| OS 全 child 进程 CPU mean | 10.453125s | 10.640625s | +1.7937%，未通过 |

per-JVM measured means 按原序为 A0 712.89015、B0 571.41585、B1 613.106525、A1 561.799275ms，A0／A1 漂移及所有慢点保留。两个 B 的记录 actor 都比相邻 A 慢；setup mean 2.4625049→2.5686278 秒，未改 Q2 wall mean 105.2029125→145.506825ms、preserve 73.250875→75.60075ms 反向，不藏掉或因果全归新代码。累计分配是当前线程数据，不是 heap／RSS／所有 JVM 分配。OS peak WS A 506626048～512626688B、B 503754752～504266752B，以及 pagefile 峰值均保留，不用于声称精确 live retention 或 heap 改善。

时钟口径以后到源码核对为准：ACTUAL.seconds 是 Native 父记录器 actor，从 BEGIN 之前起，含 BEGIN／fsync、Popen／JVM、终态观察／日志 fsync、post 输入／class／first-origin／共享 root 递归哈希和 consumer 资格验证、POST fsync；不含其后的 ACTUAL／fence／release／close。它不能直接命名为纯 child JVM 完整 wall。MainBeforeOutput 又排除入口前 static init 和最终报告 tree encode／write／stdout／VM exit。不能把 actor−Main 差额全归 GC／JIT／启动；P130 只据现有原锚继续拆分，不新跑或用旧 P121 warm 窗替换 primary。本单也不因此补授完整 child wall 改善。

ABBA 05:57:05.007572Z 至 A1 close 05:58:00.080740Z 共 55.073168 秒，含 gaps；首生产 BEGIN 05:35:32.089385Z 至末 close 共 1347.991355 秒，准备、源审补充、两 Test 编译、8 项测试与等待全计，不仅取短采样分母。新 17 类、Stage 暂存、完整 cold source、初始化、保全与所有反向成本都留下，没有追加 JVM 挑绿。旧 113 stdout 的 fixture 6818278B 与 Main Q1 6831978B 是不同具名输入，未混作大小／SHA。

主要原件：

- J/construction-staged-material129/production01/SOURCE-READY01.json，5089B／b3af5f64003f5a7f460824d2e02288573b82cd24f1e9757de38368caa7817d1e；四旧源及唯一 body 机械逆向证明保留。test02/TEST-SOURCE-READY02.json，4011B／946d557a461193178d5c64406d9b0189d90d8eec212db8a55b89991c8786ae74。
- Native p129-consumer-execution01/QUALIFIED-P129-STAGED-MATERIAL-AND-CONSUMER-DATA01.json，94739B／ca2c54bedbc2a809872c46ff68e86006bc80a0be4a8c1082951d0329917f2308；原 pending 标签／时钟旧词保历史，后到采用及口径更正另件。
- ALL-P129-FIXED-ABBA-SAMPLES01.json，412426B／0593010ad83b7eec4dc879655ba46980a8cef4d0f5153874e12c499c86fb0836；FIXED-P129-SHARED-CAS-IDENTITIES01.json，6593B／ee018e5089c1c9fb46889e1ceb59db17699634d630105ef036003ea5fdc85a59。
- CLOCK-BOUNDARY-ADOPTION-CLARIFICATION01.json，2333B／42840ef22b66a1a785caf759d6c74fce9467de420fe802f3b96fdae9e128b7ce，明确 recording actor 未通过／child wall 未证明／OS CPU 独立。
- J/construction-staged-material129/OWNER-ALL24-ACTUAL-REVIEW01.json，11412B／2324f1fc2f98b2b9a87117e6e2bf2ea048acef855d5235764e9ed9ec4e33ac8b；Root 全 24 行独核 111951B／887fc44eb54975afed6ea482200bb04f211e42fac0c78c8b7e6c97e4c761c404，qualification／class／CP／物理身份独核 106543B／e2601a022d81df4ef845cc6555d039821fa594def43089f3b908bc2c03a8f5ce。

本轮仍为 SDK／DATA 构造、真实 same-writer preserve／full reread／resolve、固定 DATA Q2 及 pure intent，不是实际 Policy.evaluate／revalidate、Native fresh READ、SEM／owning publication、持续 worker 或已保存日指标。源、软件验证、装载、Runtime 行为和 SAVE 分层；新增 Stage 类型未获热载／当前 source 闭合准入，head47／P100 原链保持冻结边界。
