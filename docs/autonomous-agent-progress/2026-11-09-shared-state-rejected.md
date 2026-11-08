# P149：共享私有 state 快路，不采纳生产候选

Root 最终决定不将本候选纳入当前软件350。compact 输入有明确条件收益，但 pretty 输入8轮中5轮墙钟配对更慢、尾部更差；自然输入频率未知，不能为10秒性能目标默认接受负输入。本单发表有限对照测试和负结果，生产 Assembler 从未正式采用，无需回滚；P147 正式源码和当前软件 classpath350保持。

候选只在一个 Assembler 叶内机械抽取原公共 state 校验尾段，让原私有 closed-packet 路径共享 compact veto／完整逐字编码比较／原 parse+equals 回退。原包头、fresh custody、parser／writer／hash／Guard／oldencode、identity错误边界和 finally清理不改，无新type／publicAPI。生产候选仅D编译1TU6，测试1TU5，两新方法跨两个JUnit均1P，旧Test／support／Reader／Driver／SDK／Main0重编或补跑，无JFR／HTTP。软件正确不等于性能采用。

固定计划在任何执行前锁定：compact先pretty，每输入8轮ABBA＝32调用（16A16B），共64，0额外warmup／补样本。A为当前P147完整10类加P143 Driver3，两根同child13；B为原P147 Reader4＋候选P149 Assembler6＋同Driver3 parent，分别核CodeSource，调用适配／名义strictdecoder对称。功能保留真实公有scoped null／nominal、earlythrow／lateIncomplete、借用数组回调突变和P4自重播，并加入compact／pretty／Unicode词法／integer-0及原公共state错误优先级。64行完整semantic／binding／member order／原件SHA与所有post均一致。

| 同输入32行统计 | compact A→B | pretty A→B |
|---|---:|---:|
| wall总毫秒（各16调用） | 837.0021→620.2374 | 609.9493→768.9740 |
| wall中位毫秒 | 43.52845→37.93320 | 36.15955→42.39475 |
| wall最大毫秒 | 145.7961→54.7482 | 55.1664→105.1316 |
| 8轮wall配对B−A（负／零／正） | 8／0／0 | 3／0／5 |
| 当前线程CPU总毫秒 | 578.125→484.375 | 468.750→515.625 |
| CPU中位毫秒 | 31.25→31.25 | 31.25→31.25 |
| allocation均值B | 95,235,334→71,341,053 | 95,029,170.5→95,029,199.5 |
| allocation中位B | 95,029,280→71,329,840 | 95,029,400→95,029,400 |
| 8轮allocation配对（负／零／正） | 8／0／0 | 3／1／4 |

compact 的大额分配减少与省去重复state parse／树物化相符，后段两调用配对约少47.398MB，首A冷差不全归机制。pretty 的均值分配仅+29B、无收益机制；wall均值+26.0718%、中位和尾部均回退，CPU累计+10%且含15.625ms粒度，不能称免费回退。全部CPU中位31.25ms、pretty A含一次0量化，不报零cost或稳健CPU提速。源码上pretty短前缀veto后仍走原parse／equals；新增准入／helper／prefix成本与JIT／GC／存活期均真实，但这份数据不能确认回退的唯一原因。

原始全部64行／16配对保留，不删除首A、不排除慢B、不混合未知自然频率。A独立factory初始化306.404ms、parent3.3221ms、来源与反射16.0476ms计setup；setup2.1390543秒，组件before-report5.5499531秒，64 targetwall合2.8361628秒、row enclosing3.3988331秒仅资源统计，非自然频率headline。parent B与fixture／postwriter共享、pretty继承前32调用及非随机JIT／GC偏差明示；累计allocation不是peak／live heap。

首生产operator16:18:51.846456Z→末组件operator16:30:36.266916Z窗口704.420460秒，包含该锚内准备／审阅／等待；生产BEGIN→末CLOSE703.182059秒另记。四phase actor合33.1083254秒、outer合38.6527343秒不是完整窗口；actor含父BEGIN／POST校验，不是纯child wall，未持久化exit FILETIME，精确child lifetime UNKNOWN。功能case3.193秒、组件case6.002秒分别记，不代总费用。末operator后资格整理288.930582秒，首operator→资格Ready993.351042秒；再到Root决定overlay为1128.642728秒，含后续135.291686秒等待／记账，都不删。704秒不是完整交付成本，更早准备与此后的费用仍不按0计。没有追加Java重测。Native三根最终元数据1,564,194B低于4MiB，原日志及阶段原件保留，原P141预算失败不改写。

owner曾建议仅保留conditional allocation；Root后到[默认不采纳裁定](D:/ck3-state/resume91-root/post-vacation-20261107/P149-ACTUAL-QUALIFICATION-AND-DEFAULT-PERFORMANCE-ADOPTION-REJECTION01.json)（3,556B，`5183e5389d576cd3a79c3d62436ef4458371f4ed8ae1b3b9667c6d8e5ca9f305`）覆盖该建议，原建议件保留历史。Native较早qual的pending字样同样保留，由后到决定记账。发表的测试只用于显式给定冻结A/B class roots的离线对照，不授当前生产／Runtime／热载／Game／SAVE或10秒目标通过。下一P150另作只读契约，不是重测本候选追绿。

原件：[全部64行](D:/ck3-state/resume91-native-integration/p149-private-state-test01/tmp-component/junit-13266535755505284203/p149-scoped-reader-shared-state-fixed64.json)（155,750B，SHA256 `23c791365c1b9ac38ddf2f8195792a9f55b3b7e43cee0b59d65342e9dcbefba6`）；[Native最终资格](D:/ck3-state/resume91-native-integration/p149-private-state-test01/QUALIFIED-P149-SHARED-STATE-FUNCTIONAL-AND-FIXED64-SOFTWARE01.json)（67,147B，`f30233dc5176302232d7ecb04aa75f72cb101f6b2b0620b7ba367cd57eeb99a1`）；[费用摘要](D:/ck3-state/resume91-native-integration/p149-private-state-test01/P149-FUNCTIONAL-AND-FIXED64-SHORT-SUMMARY01.json)；[Root全部端点独核](D:/ck3-state/resume91-root/post-vacation-20261107/P149-ACTUAL-ALL64-ENDPOINTS-POST-DISTRIBUTIONS-AND-PAIRS-REVIEW01.json)（5,518B，`0a6332d24386dbdfd5731e6a5c769930c0579c765ba8f1d66db9b085cbc4fd57`）；[候选源与逆证明](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-private-state149/candidate01-owner/CANDIDATE-SOURCE-READY01.json)；[原owner建议](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-private-state149/P149-OWNER-ALL64-TAKE-REJECT-RECOMMENDATION01.json)。
