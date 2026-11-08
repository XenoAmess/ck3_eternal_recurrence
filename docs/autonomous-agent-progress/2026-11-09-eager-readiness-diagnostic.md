# P163：只在连接失败时格式化完整观测诊断

`NativeReadinessCollector.qualifyPhysical` 原先在 `require` 为 true 时也会拼接整个 `Complete`，把大 JSON 树转成诊断字符串。本单在原位置加同一个 `instanceof Complete` 条件；失败分支保留原 `require` 整条表达式，成功后原 cast、clock、物理读取、身份、hash、Guard 与后续顺序保持。没有新增接口、类型、supplier 或截断错误消息。采用范围是标准不可变 DATA 的成功诊断分配消除，不承诺恶意自定义 `toString` 或 OOME 等资源异常等价。

这是现有受管 Collector 叶的一处窄修改，不是补入未知来源的新生产文件。HEAD `4fc03036` 原叶 118,922B／SHA256 `a9e3b477c168db5160e1877a6cd8810c151218c3400d7e41e9adc7a737a9df45`；已编候选 118,984B／`d75d27819c552ef6542814e613a9a64e6726e7c67d574c6483278725d3d046ca`，去掉外层 if 并还原缩进可整叶逆回原文。该叶原有 skip-worktree 标志不代表未受管。source307 与正式叶只差 CRLF 和两处空白行尾；目标方法相同。旧 C0 全类编译源码谱系仍 UNPROVEN，但实际目标字节码的 String.valueOf／拼接先于 require 已独立核实，P157 仅一个记录样本指到该调用链，不能据此报告 CPU 秒或收益率。

必要首次生产编译 1TU38，全部字段、方法、公开 API、Nests 与旧 C0 一致。原有受影响 Test 和 Factory 不改字节，必要首次同 javac 2TU9，只运行 `NativeReadinessDriverCaptureIdentityTest#actualAssemblerReadRepackagesSameDriverWithoutInvalidatingItsRetainedPlanningRound`，1P（case1.094s），原 fixture20s 不改；不运行其余方法。另新增离线测量 Test1TU12／soleJUnit1P，64 行及真 Incomplete 两侧负例全部通过。五个实际 phase 均 exit0、accepted、CLOSE 释放，未重编 Driver、Assembler、Main、SDK 或旧绿。

测量 Test 原字节 32,210B／`9a8c34fd13e79d73cd2b6c613ab4aced746de058ed19587feac78ce1e20b10b7` 放到 [tools/performance 的显式离线入口](../../tools/performance/readiness-diagnostic163/ReadinessDiagnosticPrefix163Test.java)，不放默认 Maven Test 目录，不改 pom 或测试 oracle。它需要精确 A/B Collector 根 properties、完整依赖和已资格 Factory；作为独立 javac 输入复用本次实际字节，不表示默认 CI 或任意本机根均已验证。

两侧完整38类各自隔离，parent Driver／Assembler／DTO 共享。实际公有构造器、真实 memory-only locked／frozen callback 内，以同样反射调用实际九参数 qualifier。首个 clock 用同一 Marker 对象停止；每行要求 clock1、无正常返回、所有后续业务 callback0、原件 SHA／head／Driver stamp／包读写计数不变。这里只测 driver stamp／encode、assembler、连接诊断／cast 至首个 clock 的异常退出前缀，不是完整 capture、qualification、物理 IO 或 worker。small→large 各固定8ABBA（16A16B），共64，0 setup 目标调用、0额外 warmup，全部首行、冷／暖行与反例保留，不按未知自然频率合并。

| 输入 | allocation mean A→B（B/call） | allocation median A→B | wall mean A→B（ms） | wall median A→B（ms） | 8配对 wall B−A |
|---|---:|---:|---:|---:|---|
| 原359B state | 301,984→67,672 | 85,224→57,792 | 7.773475→7.796775 | 2.1545→3.4016 | 4负4正 |
| 3,397,386B state | 156,145,264.5→98,360,103 | 156,145,024→98,360,072 | 33.78125625→28.075725 | 30.8122→24.0187 | 6负2正 |

两输入 allocation 均8/8配对下降。small 首A为3,552,064B／84.4047ms，首B为209,696B，均值含显著冷成本；不能把均值 −77.5909% 全归诊断机制。small wall 均值反增0.2997%、median反增57.8835%，不授小输入提速。large allocation 均值少57,785,161.5B（−37.0073%），wall均值 −16.8896%／median −22.0481%只是该前缀的有限观察，末两配对 B 更慢，B最大70.1242ms略高于A69.8474ms。CPU small中位0／0（16行中A14、B15个0），large中位23.4375／15.625ms且配对3负3零2正；15.625ms量化不支持稳健 CPU 百分比或零成本。累计分配不是峰值／live heap，固定非随机顺序、共享 parent codec 状态和 JIT／冷启动偏差保留。

负例用真实 public Reader encode／decode 生成 actor74 的合法 facts，与 Driver73 交叉连接；Assembler 确实返回 Incomplete。两侧实际 qualifier 均在原连接 Guard 抛出同类 ContractViolationException，完整148B消息相同：`actual native/Driver observation join is incomplete: Incomplete[reasons=[native_driver_fact_join: unreconciled played-character/episode transition]]`，clock0／后续callback0。没有把上游拒收当成该 Guard 命中，也没有私有 Scope／Ready／Lease 构造或授权发行。

setup0.2789662s；small fixture0.2173533s／双构造绑定0.062981s／完整 frozen scene0.6217521s，large分别0.0759259s／0.0000935s／1.2743787s。负例0.0107824s，before-report2.1971597s不含写报告、JUnit／VM尾部；这些成本仍在实际进程和完整窗口。五phase actor合32.6135645s／operator合41.8479888s只是资源子窗。更早已持 Root D 锚 `2026-11-08T21:39:40.205124Z` 至最后 CLOSE 4057.552711s、至 Native最终资格4279.461868s，含源码、审阅、准备、两个0VM元数据纠正、等待与后处理；此前UNKNOWN，不记0。最终四根证据3,035,227B＜4MiB，报告85,123B＜256KiB，原件和所有反向数保留。

Root最终采用这处生产源码的 allocation 改进；不授 small wall、总体 CPU／延迟、Runtime、热载、完整游玩或10秒目标。本文发表时软件基线仍需另按正式SHA和真实38类清单接入，Git发表不等于Runtime采用。0新增SAVE，不报有限秒／保存日。P162 Ledger 因现有 `assertSame(expected, pin.reference())` 身份合同已否决；P159—161 token matcher停止，旧P149拒绝、P155／156 PARK、P152原失败与P141预算PARTIAL均不改写。下一项沿新软件基线取真实证据，不为本单补测挑绿。

原件：[最终Native资格](D:/ck3-state/resume91-native-integration/p163-eager-diagnostic-prefix-test01/QUALIFIED-P163-STAGE3-PREFIX64-REAL-INCOMPLETE2-ALLCOSTS01.json)（120,546B／`353c9ec967ebba84bfc6eb3e6c6373e9be37ac78380a451c81910c2c228e6a7a`）；[全部64原数](D:/ck3-state/resume91-native-integration/p163-eager-diagnostic-prefix-test01/tmp-junit/junit-11547588376738481966/p163-eager-diagnostic-prefix-fixed64.json)（85,123B／`0eee0c3f651d791a20e1157011f86da4483c02553a4c9d0d6132f8d9995f3863`）；[Root最终源码采用及283原件核验](D:/ck3-state/resume91-root/post-vacation-20261107/P163-FINAL-283UNIQUE-REFS-ALLRAW-INDEPENDENT-SOURCE-ADOPTION01.json)（2,419B／`e0c409cfa4fcf129fcf9a75c6abc3e71e65859cbcb3ecb960a096beddb223273`）；[Root完整配对与反例](D:/ck3-state/resume91-root/post-vacation-20261107/P163-ACTUAL64-ALL-RAW-POST-76CLASSES-NEGATIVE-AND-PAIRED-METRICS01.json)。
