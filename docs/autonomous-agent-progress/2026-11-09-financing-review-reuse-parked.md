# P170：同次融资review复用功能通过，目标时间反向，PARK

候选只改OrdinaryWartimeConstruction：保留原private五参result完整body及180／182两个早退；183首次reviewFinancing原位不动，后11个出口给新private六参重载传已持local。重载压在原238空行，260物理行、旧规则与构造、Guard／parser／hash／oldencode体逐字保持，无新字段、类型、公有API或跨call cache。原始临时review此前只供内部replay枚举判断、不外泄；在正常producer-built标准不可变值与固定定义下复用，不改变原请求frame／pending／quote等引用，也不跨compose共享。恶意可变BigInteger、Unsafe／重定义及资源／OOME时序不作等价保证。

原叶18,916B／`1ca232a3936790578ce6a73b1924a91604d862029585c30985fa9d235db27412`与formal相同；候选19,454B／`353a4a5aedeed131dadc8ffce5088a4462eeb1759bf3570e761074d62c67002a`整叶逆回精确。actual选定callee／record／纯读闭域已独立核，不把它扩为全部历史C0编源已知。生产首次1TU12实际exit0／accepted／CLOSE；唯Top字节改变，11个nested新旧SHA完全相同，字段／公开声明／原private五参保留，新增private六参。2early旧五参、11late新六参、首review原位由实际Code闭合；后段review二次变一次是Source／Code推导，不是运行精确计数器观测。

测试A／B只child-load各自Top，父11nested／Codec4／NativeQuote／OwnedProjection及current351其余依赖共享。实际33条Top到nested成员引用均public，反射公有compose的参数和返回都断言父Request／Result，避免拆开私有owned projection或伪称whole SDK二进制对照。公有ObservedRequest.fromFullMaterial仅在setup取真实closedRequest，不调用Codec.evaluate或verifyResponse偷换为父旧compose，也不额外预热目标。

输入沿P164原件与回执精确来源：6,828,464B／`f09f466d62dda3fe52f185a667d22bbe2c58452de0dee66900b8cd766eee1daf`，1legal／1active construction、融资wars0／prior0；没有人为放大表或推自然频率。固定首8ABBA＝32次、16A16B，setup目标0／额外warmup0。每row都为QUOTED_CANDIDATE＋financing CURRENT，排除落入未优化early路径；完整结果9,726B／`1b1c292fd9e348d9ac845e3cb7f638f25dcbebb4def9c50e7fedc0f169b44a71`，与实际receipt.command.arguments.ordinary_cash_result全typed模型相等且A／B完整wire SHA一致。原件SHA、selection／cash.frame／candidate／融资sourceFrame／pending／planningOptional引用保留，跨返回的review／assessment仍新建。

| 指标 | A | B | 8轮两调用合计 B−A |
|---|---:|---:|---|
| allocation mean（B/call） | 120,305.5 | 3,974.5 | 8负0正 |
| allocation median（B/call） | 3,448 | 2,952 | 8负0正 |
| target wall mean（ms/call） | 3.67793125 | 0.52854375 | 3负5正 |
| target wall median（ms/call） | 0.17555 | 0.229 | 3负5正 |
| thread CPU median（ms/call） | 0 | 0 | 1负7零0正 |

稳定分配中位少496B（−14.3851508%），保留减少重复typed评估／对象构造的机制事实；不是省掉6.8MiB解析、encode或巨大候选遍历。首A55.5326ms／1,873,056B全部保留，不能把均值wall−85.6293%或allocation−96.6963%全归机制。目标中位增加30.4471660%（53.45微秒）、5/8配对更慢，未满足原“无明显material目标墙钟退化”条件。含post的row中位10.5779→7.5532ms（−28.5945%）不能替代compose边界；CPU A15/16与B16/16为0，累计46.875→0ms只含首A的粗量化，不报−100%或有效CPU比例。

之后8个成功pair与3个失败pair共22次compose，另1个Request构造前拒绝0目标；合计54实际目标／12功能row全过。公有DTO衍生数据覆盖两早优先／cash拒绝、BEFORE分支、融资CURRENT／UNAVAILABLE／SOURCE_FRAME_MISMATCH、PEACE下pendingUnavailable及UNKNOWN不得重放；真实badPlanningFrame在late quote fault前抛同类／全文相同错误，两个early仍保原融资检查。quoted stage shape在public ctor拒收，不冒compose覆盖。其它未达quote枝仅source／Code证明，无私有Quote、issuer或资格mint；功能衍生数据不冒实际观察。

新Test源22,487B／`425b14ec870012fac34eff4b224d08c595a0c86b8d2fe2f589bb8d512296120d`仅D；首次1TestTU3与唯一JUnit1P0F0E0skip，生产12、旧Codec／SDK／Main／Test不重编，共3个实际成功Java进程。SourceReady准备时把P125物理15误当选中12的断言、owner分析脚本语法错误等0VM准备问题照保，不伪称Java RED或删除费用。源与输入不因结果再调。

setup1.8852195s，含公有full-material factory0.3565005s；功能0.0347228s、before-report2.5332213s不含报告写出和JUnit／VM尾部。完整wire编码／typed回执／身份／6.8M SHA后验在target timer外、仍计enclosing row和全case。NEVER＋外置既有空reportRoot＋CREATE_NEW／256KiB保报告28,165B／`426825e8b2c8a32e71abc8a0f9422cfd504bc0416483771c47a3dee9b2809b66`，全部32端点与13类来源独核。

已知最早具名Native报告切点 `2026-11-09T02:04:18.140060Z` 至末CLOSE2789.339133s／Native最终资格3117.549314s；更早Root或实际研究起点UNKNOWN，不记0，切点不是任务开始。包括准备、原件／闭域审查、错误修正、调度等待、初始化、冷暖、后验与结算；P171并行窗不相加。三actor合17.0260208s／operator合20.2110766s仅子窗，不能替代全部已知窗口。三根metadata1,370,434B＜4MiB，所有owned tmp／classfiles计入，外部6.8M原件与回执只读且未复制归入元数据。

Root按原rule默认PARK，生产源及Test都只D保留，不发表、不切candidate baseline，current351不变，无回滚（从未采用P170）。不补warmup／样本／大N／JFR／fullcase追绿，本次仅unit／daily11-09／W46三事实docs。0新增SAVE，不报有限秒／保存日，不授整体worker、Runtime或10秒目标；P171另有条件源码原型授权，当前不含其测试／VM／装载或性能。

原件：[Root全部32／13来源／PARK独核](D:/ck3-state/resume91-root/post-vacation-20261107/P170-ACTUAL-FIRST32-13ORIGINS-FULLRECEIPT-FUNCTIONAL-AND-PARK01.json)（20,028B／`e804b2055d235eda3b7824c455165be37fc886ff0757eeeb416aa284669ca6ac`）；[Native最终资格](D:/ck3-state/resume91-native-integration/p170-financing-review-test01/QUALIFIED-P170-FIRST32-COMPOSE-FUNCTIONAL-ALLCOST01.json)（57,038B／`dd21bb1b15f58f32aedc92981c274da1fe3b6c3ff26f00418a59bdcd63ac98fc`）；[全部32原数](D:/ck3-state/resume91-native-integration/p170-financing-review-test01/reports-component/p170-financing-review-compose-fixed32.json)；[owner逐值独算](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-financing-review170/OWNER-ACTUAL-FIRST32-AND-PARK-REVIEW01.json)；[独立PARK审阅](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-financing-review170/read-only-fixed32-review01/REVIEW.json)。
