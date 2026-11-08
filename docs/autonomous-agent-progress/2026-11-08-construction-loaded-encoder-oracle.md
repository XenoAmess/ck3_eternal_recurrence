# 有限 Loaded 查询编码 oracle：只验证冻结域的字节等价

本单元补充 P126 源码证明，在项目当前冻结的默认写配置、FullJsonTree.parse 产生的闭合标准节点、完整不可变 Driver 模型这一条件域内，有限实测两条查询编码结果逐字相等。它没有修改生产源码、编码器、parser、mapper 配置或 Guard，也不证明公有任意 JsonNode／配置变化后的等价性。

同一完整原件分别经过独立的 FullJsonTree.parse 与 DriverJson.object，再提取 query_observation，比较 FullJsonTree.encode(query,64MiB) 与 DriverJson.encode(queryObj)（既有 256MiB 编码预算）。比较的是两个既有编码结果；原 wire 的空白、转义拼写和整数 -0 可能已在共同解析时规范化，不能称原 wire 逐字保留。原始输入直接交给两个解析器，没有先经 JSON 编码器重写。

实际只有一个手动 workload JVM，固定 24 个 case 的预期矩阵全部通过：3 个原 DATA02 完整输入、10 个 literal 正例、11 个负例／域分界。16 行实际比较了两条编码结果，包括 3 个孤立 surrogate 的纯编码行；这不是 24 个 JUnit 通过，也不是 24 个 Source 或动作准入。

| 有限输入／边界 | FullTree／Driver 解析 | RawJson.fullMaterial 物理语法校验 |
| --- | --- | --- |
| 原 Q1、Q2、small；顺序、null、空容器、长／空 opaque key；控制字符、引号、反斜杠、non-BMP；整数 -0、5001 位 BigInteger、-0.0／1.00／1e+0／长前导零指数 | 13 行接受，编码逐字相等 | 接受 |
| value-depth64 scalar、depth63 空／非空容器 | 包含在上述正例，接受 | 接受 |
| value-depth64 空／非空容器、depth65 scalar | 3 行拒收 | 接受；其原有深度域较宽 |
| 重复键、转义同名重复键、trailing document、非法 UTF-8、空文档 | 5 行拒收 | 拒收 |
| escaped 孤立高／低 surrogate value 与孤立 surrogate key | 3 行接受，编码逐字相等 | 拒收；不授物理原件或 Loaded 准入 |

Q1 为 6,831,978B／fe413956e14af2487bbec3b900e7ef6f08e653fc405ad5b71466eaa9e2cb9cdd；Q2 为 6,832,024B／a5a09c41abe1a73a358e986f241774f4cb3b9a19d85e2b70f7678a71237661be；small 为 28,318B／942dd2dab275c620bc6267182b1f1c139a8d7c6498dd8414654e5892fb938b9c。均只读自原 DATA02；结束时三份原件的 stat／hash 仍一致，没有新 PREP、Store、Guard card、归档写入或新采样。

源码证明还限定：Obj／Arr 保序并不可变；标准整数、DecimalTokenNode 原 token、String、boolean、null 落到相同 generator primitive。实际 CP 的 4 个边界类及 19 个具名 Jackson class 首来源已保全。标为 2.21.7 的这些 selected class 与本机对应 2.21.2 class 字节相同，相关源行为可用于有限核对，不能把 selected class 相同推广为所有 jar／源码谱系相同。公有 FullJsonTree.encode 接受的 custom serializer 可经 getCodec() 改 mapper 是条件域外源码反例；本次没有创建、执行或修改它，也没有新增全局配置 Guard 来掩盖这个前提。

手动入口源码 17,764B／048b3004ff8c1fa53291b11b43fd787327f0b6a1860761dfa549cab104be5cb1 原字节正式收录到 local-service/src/test/java。它没有 JUnit 方法，不进入默认测试自动执行；只新编这 1TU／1class，原 SDK／生产／Test／Main 均未重编。编译 child 7.2234333 秒；唯一 manual actor 7.1017560 秒、outer 9.5918942 秒，CPU1／384MiB／90 秒。Main 入口至最终报告序列化前为 4.4906428 秒，报告输出后至终态 stdout 前为 4.4949193 秒；这些窗口分别记录，不用较短 Main 窗口替代整个进程。

首 Native 记录器因机械缩进错误在 claim／Java／BEGIN 前失败，operator 0.1477409 秒，原 config／script／stderr 保留；修正记录器后复用已编 Oracle，未重编、未额外运行第二个 workload JVM。这不是 Oracle 编译／Java／模型失败。编译 operator BEGIN 04:27:13.653114Z 至唯一 manual close 04:30:31.264183Z 共 197.611069 秒，包含准备、该错误和等待。独占 outside-CAS 元数据受 4MiB 总预算约束，逐 case partial／首错停止机制及完整 stdout、stderr、actor、OS 峰值均保留；未为通过或更快结果重跑。

主要原件：

- Java D 源码证明：construction-loaded-intent126/read-only-sourceproof01/REVIEW.json，18545B／2821066e0c9c890f498990497f3415b3034054bd366e17b3e2a31a167e574666；库证 7927B／c141d8867bbdff008b34d8ad0c3a20ae2eec63189345de4b30e94302c7d9a81a。
- Native p126-loaded-encoder-oracle02/QUALIFIED-P126-FINITE-ENCODER-ORACLE01.json，57364B／1896f141e24a0f0bf9cf3ba922c655201a8dc5a3ef8ac6c6f26ef9399a08409c。
- 全 24 行 ALL-P126-FINITE-ORACLE-24-OUTCOMES01.json，41470B／968c21702a2cbb8598fe4a1773b7492df596ec064700d276413e69fc0c825388。
- 实际报告仍在原 p126-loaded-encoder-oracle01/exclusive-oracle01/ORACLE-RESULT.json，29109B／b64c56a955b5b9ce8fa652684d48e68c3ac6ac5726d984b524b374043d93cda3。execution02 与该输出根的不同来源明确保留。
- Root 24 行独核：7593B／035a1538aef11de7cf8c5f80f6d9e68f0410ad45440615ab4cb0f585a7051e6a；最终资格 44/44 direct pins、40 unique 独核另件保留。

这是一份有限源证明的实际补充，不是穷尽全域证明或性能实验；没有授予 Loaded／Source／command 准入、Runtime 装载、新类热替换、Game 行为或新增 SAVE。后继 P127 的私有 Loaded 双 identity 条件快路另做源码、受影响回归和原完整 DATA 对照，不能用本单替代。
