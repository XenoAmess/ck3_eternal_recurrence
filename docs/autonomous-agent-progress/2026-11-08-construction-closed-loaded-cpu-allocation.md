# P127：闭合 Loaded 的主线程 CPU／分配优化，whole 墙钟未通过

Root 决定保留 P127，严格标为冻结默认配置／私有 Loaded 闭合域内的主线程 CPU 与 allocation 优化，wholewallclock 未通过。只有 Loaded 所持两个不可变对象都以 identity 匹配、且已有 exact-finalized cache present 才复用结果，省去 intent 阶段再次编码完整查询及比较该数组。软件行为与原完整 DATA 对照已闭合；whole 均值与中位数方向不同，不能授整体延迟、Source 或 Runtime 通过。不同于 P123 两个 B 均有一致大回退，本次证据支持保留条件优化；不重跑挑绿、不把百分比累加到旧轮。

该实现由 owner 根据已有完整源证明和 P126 有限实际 oracle 手工完成，本单 0 HTTP／模型调用，未借用 P125 整件 length 未采用回答。条件仅限项目冻结的默认写配置、parse 产生的闭合标准节点及完整 immutable Driver 模型；不将它推广为任意 JsonNode、任意 Obj、配置变更或原始 wire 词法恒等。公有 custom serializer 可改 mapper 的前提外反例仍保留，没有执行或修改配置，也没有新增全局配置 Guard。

Loaded 只新增 package-only cacheFor(expectedObj,expectedObserved)，分别以 == 对照原两个 private final 字段，再调用已有防御 cache getter；没有新 field、bool、类型、public trusted factory 或任意 raw／typed pair。full Loaded 入口把同一对象传给私有六参数 body；原私有五参数签名保留，使用 null context。uncoupled 或 cache miss 原样执行 DriverJson.encode(query)、NativeQuote exact byte 比较和原 finalizer fallback。compose、query extraction 的错误顺序与所有后续 frame、candidate、proof、funding、cash、期望物料及 canonical body 校验保持；实际 source resolve／full readback／长度 SHA／header／command、budget 与 lease 原样。

只必要编译 2 个 App TU／11 个完整 family class，new type 0，child 7.0626675 秒；必要增编现有 ConstructionIntentResult117Test 1TU／3class，5.4174369 秒，不能称“旧 Test 0 重编”。只选两项已存在 affected 方法，同一个 JUnit 实际 2P0F0E0skip，actor 12.1273392 秒、XML suite 9.738 秒，新 unique method 0。fullResolved 在真实同 writer 物理 resolve 后验证原 pair 命中、防御拷贝、同值异 Obj identity 拒收、同 raw 异 Observed identity 拒收；原 unequalRaw／proof mismatch 仍经私有五参数入口验证原 fallback。没有新 Suite、放宽旧 oracle、私有 authority issuer 或无关旧绿重跑。

对照保留原 Main03 字节／类、同一绝对 DATA02／CAS、Q1／Q2、source／ref／原 EXPECTED。A 是 P125 SDK18＋旧 Source3／P122 Lifecycle8，B 只替换本次 Source3＋Lifecycle8；拒收 P123 B 排除。逻辑 A0/B0/B1/A1 对应原报告 raw B0/B0/B1/B1，不改写标签。cached_api_used=true 是共同 P114 API lane，不冒充新 P127 命中计数；实际 variant 来自完整 family／first origin／有序 CP。new Test、P126 Oracle、P121 wrapper、P119 flags 均未加入 Main CP。没有 PREP、数据刷新、Main／SDK 增编、forceGC、慢点过滤或追加 JVM 挑绿。

四个独立 JVM 各固定 2 warm＋4 measured，共 8 warm／16 measured／全部 24 行保留。CPU1、384MiB、原有限时窗；全原 markers、共同 cache／warm-existing CAS、11 个 disjoint phase 的 wall／CPU／allocation sums 及实际 exit0／资源释放均核对通过。每进程原 software allocation card 与固定物理身份单独记账，不宣称全部文件系统字节相同。

| 指标 | A | B | 观察 |
| --- | ---: | ---: | --- |
| whole measured wall mean | 688.7846625ms | 698.9506ms | +1.4759% |
| whole measured wall median | 706.994ms | 671.1903ms | -5.0642% |
| 主线程 CPU mean | 302.734375ms | 253.90625ms | -16.1290% |
| 主线程累计 allocation mean | 684067184B | 634818350B | -7.1994%，少 49248834B/call |
| actor mean | 12.9612724s | 12.36667325s | 另含启动／进程成本，不替代 whole |
| pure intent allocation mean | 54316456B | 5057952B | 少 49258504B |
| pure intent wall mean／median | 109.1939／75.0673ms | 66.1065125／29.91815ms | 仅此 cohort 阶段观察 |

per-JVM measured means 按固定顺序为 A0 672.8736、B0 707.722675、B1 690.178525、A1 704.695725ms：B0 比 A0 慢，B1 比 A1 快。B0 的 900.9879ms 和 B1 的 854.1622ms 等慢样本全部保留。未改 resolve mean 从 230.710575ms 到 292.585475ms，Q2 mean 从 124.5536375ms 到 129.1151625ms 反向，不能把阶段变化全部因果归到一个编码或将中位数挑作整体速度结论。allocation 为主线程累计分配，不是 heap／RSS／全部 JVM 分配；主线程 CPU 也不是 compiler／GC 等全进程 CPU。P119 的 cold compiler／GC 诊断和 P121 后 pass 结果不能代替本次 primary 对照，百分比不与旧轮相加。

ABBA 04:49:29.957849Z 至 A1 close 04:50:25.853039Z 共 55.89519 秒，含 phase gaps；首 production BEGIN 04:45:22.654580Z 至末 close 共 303.198459 秒，编译、受影响测试、准备错误和等待全部计入。Native preparer 沿旧 mapping 字段读取实际 fixed_run_order 触发 KeyError，另误尝试未生成 helper；均发生 output/config／claim／Java／BEGIN 前，0 workload JVM。原错误件保留，随后只是显式 schema adapter／helper 预检，未改 owner 合同或 Java，不能称本单 0 metadata 错误，也不能归为模型或生产失败。

主要原件：

- J/construction-loaded-intent127/production01/SOURCE-READY01.json，3829B／8340deeb45d2f81fefe4ddc3b2492cb96ed93ed2cbdff7910b801d8f3fb872f0；Root 审过同件 source 两叶逆向恢复原字节证明。
- Source 10004B／0733bb6afd4fcf17e3a430cf7980ee44e34f8c8fad37c907e895a348542fb161；Lifecycle 49831B／33e772db2a88ff248f51feaecda87b0224f77fccc52f0703b004244cab24719b；changed old Test 15683B／b386292a4431ccf46f4efa73d22aa13ae618e2fe33585bd43ad4c6450926cdf3。
- Native p127-consumer-execution01/QUALIFIED-P127-CLOSED-LOADED-AND-CONSUMER-DATA01.json，64493B／465288d5b82b3b84aed266042bbca559415f329984a13f859c84d510f6e039f6；原 adoption pending 标签保留，后到决定另件。
- ALL-P127-FIXED-ABBA-SAMPLES01.json，404364B／54838e7e1a17071402f486986aedcccbf209c63c52d9e8f2850843a2f28c6294；FIXED-P127-SHARED-CAS-IDENTITIES01.json，6593B／0a94eeeeff66378c8fb05437736bbfa65778b195b664b3f9eaeffdccc9938746。
- J/construction-loaded-intent127/OWNER-ALL24-ACTUAL-REVIEW01.json，11514B／a8a0035fd8ae13d178ea1ef5eeb5b29c88ab7ec1ac3e2c1fe2c5860813d01ac8；Native P127-NATIVE-PREPARER-CONTRACT-KEY-ERROR01.json 原件另保。
- Root 全 24 行独核 P127-ABBA-ACTUAL-DATA-REVIEW01.json，112194B／eb030c8d09a388b30111d1deaab2e23aa1a32c4bdc33edf7b03fa33e0acbff1e；后到 Root 采用决定保留条件 CPU／allocation 标签，原资格 pending 状态不覆盖。

本轮边界仍是 factory／compose／DATA args、真实 same-writer preserve／readback／resolve、独立固定 DATA Q2 和 pure intent canonical body，不是实际 Policy.evaluate／revalidate、Native fresh READ、SEM／owning publication、持续 worker 或新增保存日性能。没有实际 Runtime／source 装载、新方法热替换、Game 行为或 SAVE 资格。
