# P143：私有解析域完整计数，省去预算检查的输出数组

Assembler 的 `normalizeCanonicalState` 和历史 v2 `canonicalMilitaryState` 都把同次 strict byte-parse 得到的标准 immutable 模型交给 `DriverJson.toNode`；原方法先完整编码，仅用输出数组长度检查预算，再构建节点。两处现在使用 package-only `parsedNode`，仍由原 JSON factory／private write 完整遍历并 close，只把输出接收器换成私有 long 计数器。close 后依次执行原256MiB上限、caller64MiB上限和原 node 转换，消息及 IOException／runtime 顺序保持，不提前截断或以 raw／UTF16 长度估算。

公共 generic toNode／encode／normalized／encodeNode、custom BigInteger 第二次编码、parser、hash、Guard 与 normalizer 算法原文保持。新 helper 仅由上述私有 byte-parsed 标准模型调用，不把证明推广到任意 custom／mutable payload。它仍做完整 UTF8 编码遍历和节点物化，只省 ByteArrayOutputStream 增长及 toByteArray 数组。owner-original、0模型 HTTP；新增一个私有 counter 类型，不授 Runtime 热载。

## 必要验证，包含真实失败

两生产 TU／9类首次必要编译通过；修改既有310 Test 1TU／5类通过。功能首轮实际为4P／2E：新 finite oracle（token／顺序／Unicode、精确 caller byte budget、非BMP扩张、深度与 late writer 错误优先、公开 v2 projectFull 和当前 canonical 调用）及原 BigInteger Boundary3 都 P；Replay P4／v3 因 Native classpath 漏既有 P134 helpers4 root，报 NoClassDefFoundError。原错误 CFG／XML／stderr 全保，仅新不可变配置补原 support root，重验这两项得到2P，四绿和生产／Test不重复。

随后仅运行原计划、此前未开始的组件1P。因此最终7个不同成功方法（2new＋5affected），共3个 JUnit JVM／9次 case 执行，绝非首次全绿或2JVM。Boundary2类、Replay3类与 support4类均复用既有合格缓存，support0@Test；无 Applied／Main／SDK重编、额外 JFR／HTTP／Game操作。首次 Test 派发前另一次 toolcall aborted，按 BEGIN／claim／child 均未出现核实为0 Java，保留原件，不计新增编译失败。

## 实际公开 canonical 调用的四行组件

A 为当前有效的 P138 Assembler6＋P137 Driver2，两 root 同 child runtime package；B 为新 Assembler6＋Driver3 parent。两侧均反射调用真正公开 `canonicalNativeState` 并取得完整 semantic，DTO／Jackson／normalizer 共享，独立 factory 初始化在 setup 显式计账。输入为同一大 pretty state，opaque 3400000字符；逐行核 semantic bytes／member order／decimal token、完整 opaque、原 state／packet SHA。不用 target warmup。

| 行 | wall ms | 当前线程 CPU ms | 当前线程累计分配 B |
| --- | ---: | ---: | ---: |
| A0 | 141.4645 | 62.500 | 73029704 |
| B0 | 31.0687 | 15.625 | 57702384 |
| B1 | 20.7936 | 15.625 | 57632056 |
| A1 | 19.0538 | 15.625 | 68874960 |

分配均值70952332→57667220B，少13285112B（18.7239963%），两 B 均低于最小 A。相对末 A，两 B 分别少11172576／11242904B；首 A 额外4154744B、B0额外70328B，不能将全部均值差归于数组机制。累计分配不是 live／peak heap。

wall 均值80.25915→25.93115ms（−67.6907%），CPU均值39.0625→15.625ms（−60%）仅为冷样本描述。两个 B wall 都慢于末 A，且末 A／两个 B 的 CPU 同为15.625ms；不能据冷均值授 CPU 或延迟提升。Root 只采用软件 allocation 优化。本组件是实际 normalization caller，不是完整 verify、物理 IO、worker 或实机速度，也不按未知自然频率推广。

## 全部窗口和原件

旧／parent Driver显式初始化320.6368／1.1428ms，Assembler load/init0.9412ms，setup1.6483631秒；报告物化前1.8985497秒。生产编译 actor／outer5.2485332／6.0749291秒；Test编译6.1556067／6.9566847秒，首错功能4.2437209／5.0914880秒，Replay重验4.2237210／5.2956027秒，唯一组件4.5457903／5.3931326秒。actor含父记录及验证，不称纯 child wall；首错／重验／组件 child stderr300／0／299B分别保留。

首生产 BEGIN `13:17:36.428508Z` 至末组件 CLOSE `13:38:44.111423Z` 为1267.682915秒，候选 Ready 至末 CLOSE为1655.700296秒，包含准备、审阅、错误、修复和等待。全部实际进程终态／释放独立核验，未追加 JVM挑绿。P141历史整体 `PARTIAL_BUDGET_FAILURE` 保留，仅作调用链线索；本单薄资格与元数据预写预算通过。

本单0 saved；源码、软件通过、发表与新类型可载／Runtime／SAVE分层，不授 head47／P100、完整端到端改善或10秒／新增确认保存日目标。下一源码证据审阅独立继续，不把本单完成当全局目标完成。

- [Root allocation-only 采用决定](D:/ck3-state/resume91-root/post-vacation-20261107/P143-PRIVATE-COMPLETE-WRITER-COUNT-ALLOCATION-SOFTWARE-ADOPTION01.json)：9086B／`e640cb83b2c648e0c69e792ebe902e834d69002e7b29be0baf672a1b570cb914`。
- [Native 最终资格](D:/ck3-state/resume91-native-integration/p143-private-count-test02/QUALIFIED-P143-SEVEN-METHOD-SOFTWARE-AND-CANONICAL-COMPONENT01.json)：100506B／`013a2f537578f8dc0e5b6a6cbfc5ad88cbf4e7d2b77f0da68404c3f61c45895e`；[唯一四行原件](D:/ck3-state/resume91-native-integration/p143-private-count-test02/tmp-component/junit-12008226583879599267/p143-private-count-component.json)。
- [Owner 全部实际复核](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-count143/P143-OWNER-ACTUAL-REVIEW01.json)、[首轮4P／2E记录](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-count143/FIRST-FUNCTIONAL-4P2E-OWNER-RECORD01.json)及[同字节正式采用回执](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-count143/FORMAL-ADOPTED-AFTER-ACTUAL01.json)。
