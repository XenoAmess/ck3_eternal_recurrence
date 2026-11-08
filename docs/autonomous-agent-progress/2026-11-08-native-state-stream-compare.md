# Native state 精确生成比较与原解析回退（P137）

Root 仅采用条件命中路径的分配优化，不授 CPU、整体延迟、Runtime 或10秒目标通过。命中两次 B 的分配都低于最小 A；合法 pretty-whitespace 回退两次 B 的 wall 都慢于两次 A，风险原样保留。自然 hitrate 未知，两个场景不能合并成实际智能体提速。Owner-original，模型 NONE、0 HTTP。

P136 对同一 P135 原 JFR 的流式解码定位到实际 `DriverObservationAssembler.originalNativeState` 调用。这里的 packet 内 state 和 actual state 是两份独立 DATA，旧路径必须分别解析并比较；不能直接删除后一个校验。候选只在该公开方法内保留 packet 解析和包头校验，取得一次防御性 state bytes，再用原 Driver 字节生成器流式比较 packet 私有解析所得 Obj 与这些 bytes。完全逐字相同才复用该私有 Obj；空白、顺序、escape、数字词法、非 Obj、超原 native 上限或生成异常均走原 state 解析和模型比较。

Driver 只新增同包 DATA helper 和私有比较 sink，没有输出全文数组；生成器关闭完成、无差异且长度完全相等才命中。复用条件仍受原 native64MiB 上限约束。原 encode/write/parser/hash/Guard 算法保持，另一个 private packet-input 路径不改。比较 IOException／RuntimeException 只视为 miss，旧解析异常顺序和消息保留；不吞 VM Error。expected 来自同一 final RawJson 的防御 clone，没有可变回调或跨 capture cache。生产02消除01 miss 后再次克隆同一 state 的已知额外成本，Driver 字节不变，只必要重编 Assembler。

必要有效输出是 Driver2＋Assembler6，共8类；新增一私有 sink 类型。首次 Native prepare 把实际 `-cp` 中 P134 输出误替为空新目录，javac1／0classes；原参数、错误与5.6041617秒 actor保留。字段级修正后同两生产 TU 编译0／8类（actor11.2675928秒），随后 final02 仅 Assembler1TU6类编译0（actor5.166202秒），Driver2精确复用。源码类型、软件 class 可见性和 Runtime 热载继续分层，不授新类型装载。

测试为修改现310和首次必要编译原 SemanticReplay 两 TU，共8类（5＋3），不运行支持源码的 `@Test`。第一次 Test 编译因新报告处缺 `FullJsonTree` import 为1／0classes／0JUnit；只补完整类名30B后原数据和断言不变，必要同两 TU 编译0。未采用的单前导空格 Draft03 保留在 D；实际用批准的原 pretty-whitespace Draft02。

六个不同方法在三个 JUnit JVM 全部通过（2 new、4 affected）：

- 功能四方法：新增完整字节比较／原回退 DATA，真实 profile4 缺失、null、retained 原件重播，version3 原重播，以及原 Assembler framing／packet mismatch。新增断言覆盖精度／负零／exponent／顺序／Unicode、完整长度前缀和末尾超字节、包头优先与多故障、非 Obj／深度、生成 RuntimeException 回退；profile4 原 Complete 独立重播保持。
- 真正归档集成：复用 compiled15 完整10类的 public Applied 一项，case118.883秒／suite118.912秒。软件210／240秒，原业务120秒期限不改、不刷新。
- 独立组件一项：case2.415秒／suite2.443秒，八行全部 completed、post checks 和输入／输出 SHA 一致。

组件 A 是具名已通过的 P134 Assembler 完整六类，仅它们 child-first；B 是新 Assembler 与新 Driver 在同一 parent loader。两边调用相同公开 Method.invoke，其他依赖共享，不复制历史算法。它是 selected-leaf old/new binary、同进程/common dependencies；不是 same-binary 两入口，也不是 whole old/new CP、实际 IO 或智能体运行。输入为原310公开 DATA，含3,400,000个 ASCII opaque 字符；canonical 命中和原合法 pretty-whitespace miss 分开，各固定 A/B/B/A、每入口两样本、0额外预热。

| 场景 | 行／入口 | wall ms | 当前线程 CPU ms | 当前线程 allocation B |
| --- | --- | ---: | ---: | ---: |
| canonical match | 0 A | 42.5423 | 46.875 | 57,820,640 |
| canonical match | 1 B | 9.0857 | 0 | 33,908,000 |
| canonical match | 2 B | 10.2124 | 0 | 33,906,840 |
| canonical match | 3 A | 15.1375 | 0 | 57,606,912 |
| pretty-whitespace miss | 0 A | 12.8470 | 15.625 | 57,606,096 |
| pretty-whitespace miss | 1 B | 14.1776 | 31.25 | 57,610,920 |
| pretty-whitespace miss | 2 B | 20.2268 | 15.625 | 57,610,920 |
| pretty-whitespace miss | 3 A | 12.5476 | 15.625 | 57,606,096 |

命中场景 allocation 均值57,713,776→33,907,420 B，少23,806,356 B（−41.2490%）；wall均值28.8399→9.64905 ms（−66.5427%）仅描述，A42.54→15.14漂移明显。CPU计时粗量化出现0，不能写成 CPU 成本消失或100%收益，CPU／allocation查询包住 wall，原值不修剪。

**回退不是免费路径。** 原 pretty-whitespace miss 保留旧解析，并增加比较成本：allocation57,606,096→57,610,920 B（多4,824 B，+0.008374%）；wall12.6973→17.2022 ms（+35.4792%）；CPU15.625→23.4375 ms（+50%）也只为粗量化两样本描述。未知实际 hitrate，两个场景不得合并成总体 headline；没有依据将 canonical 命中率外推至实际 worker。Root 选择保留明确的大额条件分配降低与4.8KB miss增量，同时保留回退延迟风险供后继排查；这不是整体性能目标完成。

| 必要阶段 | recording actor 秒 | outer 秒 |
| --- | ---: | ---: |
| 首次生产2TU，Native实际 CP 错误／0classes | 5.6041617 | 6.3406710 |
| 修正 CP 后生产2TU8类 | 11.2675928 | 12.1078499 |
| final02 Assembler1TU6类 | 5.1662020 | 5.8912051 |
| 首次 Test2TU，缺类名／0classes | 6.2264120 | 7.0165169 |
| 精确 FQN 后 Test2TU8类 | 6.1576324 | 6.9832293 |
| 功能四方法 | 4.3642849 | 5.2076720 |
| public Applied15 | 121.2715717 | 122.1098283 |
| 八行组件 | 5.2254264 | 7.0748101 |

recording actor 含父 recorder 校验，不能写成完整 child JVM wall；outer是另一窗口，不与其子区间相加。首生产 BEGIN10:21:00.771710Z→末组件 close10:56:19.412415Z共2118.640705秒，含两次真实 typing RED、必要修正、准备和等待。Java曾将 compaction 重现的旧 AGENTS 误当新 stop，Root 给出真实后到用户消息时间序后撤销暂停后继的提醒；Applied始终收同一原 handle，0重复 Java／0生产改码，该等待留在总窗。owner一次纯 Python 只读命令转义错误及准备脚本保护性断言错误保留，不计 Java／模型失败。

源码／逆向 proof／两版正式 Ready 在 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-native-state-compare137`。最终生产 SourceReady02为3194 B／`6e4898b1bf4965000fa6204cb20757d22ba50445147e4d85b3476d3adc519994`，最终 TestReady02为10890 B／`a483dce8d3f64fef0c3f37b4113b7a453e6fc29cfb4bd0b7888fc53380eabe2f`。Native 原件为 `p137-native-state-prod01/02/03` 和 `p137-native-state-test01/02`，没有覆盖首次失败或未采用 Draft03。owner 全八行／ACTUAL／CLOSE／XML复核19083 B／`04671688a2caec2fd8045337842c8d86ee94b526c04188ff978240c7a8c69d91`。

源码可核对 [DriverJson](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/driver/DriverJson.java)、[Assembler](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/driver/DriverObservationAssembler.java) 与 [310 测试](../../java/ck3-control/application/src/test/java/org/xar/ck3/control/application/driver/DriverFrameJoin310Test.java)。正常发表只含这三源码和本单元／日周三文档；未修改 Replay、支持类和未采用 Draft03 不混入提交。正式 Git 与软件采用、实际 Runtime 装载继续分开记录。

0 HTTP、Main03／SDK／JFR重跑、额外预热、Runtime或Game操作。P100拒绝链／原账本／UNKNOWN／deadline／Guard边界不变，不授新类型热载、head47、SAVE或10秒目标。持续演进继续，下一源证据任务不以本次发表或 Runtime 不可用为停工理由。
