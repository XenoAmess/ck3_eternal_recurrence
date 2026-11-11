# Sway P0：保留旧编码的 import 安全整数载体

用户已明确“解除该限制，诊断并最小修复”“允许本轮诊断和最小修复”。这次解除的是相关同链诊断限制；旧 UNKNOWN、原件、期限与 Guard/parser/hash/oldencode 边界保持。唯一 Runtime owner 负责实机与实际采用，本次源码发表不补授动作或保存。

实际首栈来自 owner23 的 stdout：Quarkus 将诊断 `System.err` 路由到 stdout，因此 stderr 为零不能说明日志未命中。9618B 真栈/SHA760dc14a51f9433295d8bf33bcd35236631d138d12cddbf99636c5ac5c85bf02 经 `StrictJson.integer → ContinuityJson.append95 → WriterContracts.canonical → DomainBodies.ImportRequest65 → SwayCanonicalDomain.commitScoped108 → pendingProducer68 → Coordinator198`。ImportRequest canonical 的是 producerInput，不是 originalBody。`change.target.native_body.container_generation=7611325349788850593` 在 native UInt64/有符号 long 域内，却超过 continuity JSON 的 ±9007199254740991 安全整数域；target_opinion_of_actor=-61 合法，未截断或丢弃。

前三段公共纯 DATA 原件路径均通过，只排除了各自覆盖的 read/bind、旧 transition/reducer、frame/context；没有覆盖 ImportRequest 边界，不能据此说整个 producer 正常。新增原构造器反例严格重建旧2079B/SHA5555b8ff94aba92aba14c6fd74a53dbfa8e1e1d4f17ee52c02481e6875db98db producer，以及原已保存1991B/SHA023d33a850534b26c08c5e40500088a8749fb5f9c8747569618528dbcb1ff477 body/真实 ExactRef，并复现同一安全整数异常。已有 target dispatch 是 READ，不能概括为零 Native dispatch，更不能据异常栈授 NoDispatch。

业务修复只有两叶。SwayTransitionCodec 保留原 encode/decode 的完整字节与旧版本：新增 `xar.java.sway-domain-transition-import/v1` 外层，严格只有 schema 和 original_transition_base64 两键，使用既有2048字符 canonical base64 chunks 无损携带旧 producer 全 bytes。新解码先严格识别外层，再走原 decoder，检查旧 inner 再编码 exact 和新 outer 再编码 exact；未知字段/版本、嵌套、错误 base64、非 canonical 分块/内外 bytes 和截断均拒绝。仍受原 DOCUMENT65536 上限；base64 额外开销超过此上限时明确拒绝，不省略、截断或抬 cap。

SwayCanonicalDomain 仅改新发布 encoder、两处 producer decoder 和 registration 的版本化 digest 分支。新分支绑定实际收到且经双重 exact 验证的 canonical outer bytes；旧分支仍是原 encode(input) 的哈希。原 verifyOriginals、predecessor/evidence、完整 reducer/body 比较和 publication witness 的实际 producer 哈希不变。Fresh/NEXT/初始 import、FormalCodec/native body、通用 ContinuityJson/StrictJson、Guard、旧编码与哈希函数本体均未改。

必要2TU首次编译 exit0，14文件/150方法声明，其中4抽象、146个 Code；原148声明仅新增两静态方法。独立核验141个完整 Code、三个必要修改程序、两个新增程序及20处明确 LDC 宽度映射。Registration 完整前324条指令仅换声明过的 decoder，原旧哈希尾与新 actual-request 分支逐项核对，不遮蔽字符串、数值、字段或 BSM。原 Port.unavailable 唯一诊断前缀为 printStackTrace(System.err)，其1TU9类/other72完整 Code 已核；它是诊断信息，不是业务修复。

真实 test02 首次编译及 DATA 执行 exit0/accepted，CLOSE `2026-11-11T08:51:41.463142+00:00` fenced/released。旧反例仍拒绝；新2863B/SHA905530d9c8a85b00aaf978f0a14ade4960af3ccd13c78d0f2247c83294af71ff 载体通过原 ImportRequest，旧2079B producer、1991B body、证明引用和历史 raw 解码保持。九个畸形负例全部拒绝；另一个69627B上限负例先证明内外 JSON/版本结构合法，再核原构造器确切 size-limit 消息。test01 原 NUL 数组不能独证 size cap，已保原件并在实际首次测试前换成 test02；不是 JVM 测试失败。该 DATA 没有调用 registration.verifyOriginals、previewImport、commit、session、Guard issuer 或 Native，不授完整事务或恢复通过。

本次真实软件阶段共12个 JVM：前三段各编译/执行、诊断叶编译、原构造器反例编译/执行、修复2TU编译、test02编译/执行。actor 累计 50.8190873001003643 秒嵌在 operator 63.3295407998375602 秒内，不能相加或冒充整轮。明确授权 2026-11-11T06:59:58.320837+00:00 到末 DATA CLOSE 为 6703.142305 秒，包含准备、错误、审阅、诊断与等待；发表后的完整墙钟另附实际回执，更早真实开始 UNKNOWN。Runtime/Maven/Game 不在这12个软件进程子窗之内。原路径误猜、方法148误加为157、尾13误写14、cap负例修正、Native prelaunch 配置拒绝及全部模型误报/截断、等待保留，不删除失败窗口。模型本轮6请求为5完整/1截断，0实现采用，不替代实际编测。

正式源仅移植四个 fix hunk 并合入诊断叶。Codec 与实测 active 变体相同；Domain 正式原叶83519B保留原 Instant.parse 和 NativeCharacterId.fromJson 两处既有表达式，active 原叶83481B对应 StrictJson.utc/SwayNativeWire.integer。本次不顺带回滚这两行；Native 实测资格属于真实 active 变体，正式源与 active 来源差额分列，不冒称整个 formal bytes 已编成同一 class。

当前原件记录新 Game04、owner23 首批失败后 parent36 UNKNOWN/registered child1、无 child Intent/receipt/Run.child；期限08:49:49.300706500Z保持，不刷新。诊断日志已实际采用并命中，codec 修复截至本切点只有软件资格，尚无其 Runtime 采用或当前同ID恢复回执。不能删 reservation、造 child receipt、削弱覆盖守卫或冷启新业务绕过 UNKNOWN；LOOP 历史起点不外推为当前持续运行。新增 SAVE=0，秒/新增确认保存日=null，不授性能或整局速度收益。

证据根为 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/sway-integer-preintent-p0-20261111` 与 `D:/ck3-state/resume91-native-integration/sway-preintent-p0-20261111`。源 Ready5124/ec513bd2、formal mapping3956/61968df8、owner Code24429/14122ace +3121/2cdebf26、Root Code1584/eb3aea42、新构造器 stdout1478/b30a8222、实际14输出59904/057d53ab、12阶段完整引用见 PREPUBLICATION-12JVM-COST01.json；Runtime 真栈位于 attempt23/new-batch0-terminal-20261111-04，原诊断采用/9类实际匹配/真栈三层分别保留。

后到成本偏差（初次源码发表29c6b01f00之后到达）：Native按原aggregate roots重算 F4523948B+J988043B=5511991B，超过原4194304B元数据预算1317687B，metadata-budget=FAILED。12个真实软件JVM及功能/Code/构造器正负例结果保持，但不能改述全部资源预算通过。保留全部CFG/BEGIN/源与错误原件，不删除、搬移、重分类、抬旧cap或重跑补绿；这是成本控制偏差，不改变producer原65536上限。原提交切点保持，本条为正常后到追加；Runtime采用、当前UNKNOWN恢复及新增保存仍未由本条授信。
