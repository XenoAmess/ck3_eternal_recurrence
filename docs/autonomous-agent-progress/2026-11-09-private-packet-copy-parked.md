# P167：私有包副本复用功能通过，中位时间反向，PARK

候选仅 DriverObservationAssembler 三行私有接线：218把原216取得、217已作证据SHA校验的originalPacket传入；288私有方法增加byte[]参数；292复用该同call副本。289 null分支、293至文件末尾及公有originalNativeState完整body逐字保持，431物理行不变，可整叶逆回已采用P150的34,549B／`74e070633830ce6363719b50567eb8ce40a25ea894ef20db308a21e2e9effeb3`。无新类型、字段、公有API、cache、carrier、token或provider检查；全部Guard／hash／parser／oldencode与实际capture／clear顺序不改。仅非null私有路径可能少一次重复packet getter clone，不涉及公有解析快路或P166值API。

既有ObservedFrame构造和getter防御clone，局部副本在标准SUN SHA-256下不被digest修改，之后ByteBuffer／matchingEnvelope只读；五个本地JDK21源码条目已证明此前提。源码／配置本身不能证明运行provider，且任意恶意provider若hash后改输入就是反例。本次soleTest实际记录并核验SUN、class `sun.security.provider.Sun`、version21、服务 `sun.security.provider.SHA2$SHA256`，全部13个ordered providers的name／class／version／info前后相同。只闭合该软件测试环境，不外推Runtime、任意provider或临时注册再恢复的ABA行为。

生产首次1TU6实际exit0／accepted／CLOSE，候选34,577B／`85fab6e5a6a0cf9422a9f0b862a5a96f6c96a1627ea1839c13b7dc5a0678c403`；fields／公有protected声明／Nests相同，唯一private descriptor增加[B，不能说全部方法声明相同或可热载。新Test02首次1TU4与唯一JUnit1P0F0E0skip闭合，共3个Java进程全部成功；没有旧绿重编、额外profile、预热或补样本。Test01与02仅三处报告label澄清，执行体不变；Ready生成器曾漏识别record隐式static而断言，0VM修正仅生成器，不是Java编译失败。

测试走公有Reader173→内部capturedNativeFrame→Asm94／209／218，由原生产者自行创建holder；没有私有holder构造、字段访问或资格mint。A／B各完整13类同child：共享既有Reader4和P143 Driver3，A旧P150 Asm6，B新Asm6；A两根／B三根精确来源及26个实际class SHA全核。own Assembler.class参数、own公有构造和own结果getter消除cross-loader cast；父nominal decoder只做严格Driver字节解码，不用父Loader替换目标路径。

固定使用P150已资格WIRE／STATE与3,400,000个ASCII x的大compact构造，实际packet3,400,432B（SHA `57bf15b3d8ab9de15f5559037b789494d7f5fd7bd71ef521140276633686f19d`）、manifest985B、driver708B。一个输入8ABBA＝32次、16A16B，setup目标0／额外warmup0。首冷与后暖、A先初始化、共享父fixture／post codec／nominal decoder、固定非随机次序全部保留；不推自然频率或旧profile的clone次数／selfCPU。

| 指标 | A | B | 8轮两调用合计 B−A |
|---|---:|---:|---|
| allocation mean（B/call） | 68,128,927.5 | 64,543,749 | 8负0正 |
| allocation median（B/call） | 67,927,800 | 64,527,240 | 8负0正 |
| target wall mean（ms/call） | 34.9728375 | 31.75558125 | 3负5正 |
| target wall median（ms/call） | 25.50975 | 28.40865 | 3负5正 |
| thread CPU median（ms/call） | 31.25 | 31.25 | 2负3零3正 |

分配均值−5.26234396%／中位−5.00613887%，中位差3,400,560B符合免完整副本机制，不能把总差当精确payload分配量或峰值下降。target wall均值−9.1993%受首A155.143ms影响，全部冷行与outlier不删；中位反增11.3638903%、5/8配对更慢，不满足事前“无明显material全prefix墙钟退化”。含post的row中位32.9→35.60325ms也增8.2165653%，不能用均值改判。CPU累计437.5→390.625ms、双方各一行0，15.625ms粒度不授稳定CPU比例／零成本或整体延迟提升。

32次均Complete，类型／身份、source、session、connection、evidence、observedAt、binding、semantic SHA、member顺序及原1.00 token一致；原manifest／driver／packet SHA逐行不变。之后8个功能row全部通过：14次公有Reader含1.00／−0.0／1e+0的null-decoder词法、early conflict直接同全文ContractViolationException、late identity为原Incomplete，以及证据SHA／长度均先于semantic conflict拒收；另2次未改公有state的pretty fallback。共46次Reader＋2次公有state。所有实际observationVersion3；P4 body仅源码保留，本次不授P4 RUN。private null／holder mismatch仅整body sourceproof，不手mint来冒覆盖。

Test原字节24,462B／`4ad40206975651560576c635af5a75d8a2fbfe0c103f1d03ec17709f377da257`只D保留。NEVER＋独立既有空reportRoot＋CREATE_NEW／256KiB保报告92,338B／`4aee34f058d764252718e4df4935e7dac4f03936bed7230c89cc7705005a6bde`与失败partial。setup1.8140475s、功能0.1885472s、before-summary3.3533575s未含报告写出及JUnit／VM尾部；每行post在target计时之外、仍计enclosing row／全case。

更早具名Root切点 `2026-11-09T01:15:05.066053Z` 至末CLOSE1764.788608s／Native最终资格1920.063114s；当时Rootlog已明确继续P167私有caller只读研究，原文已入独核快照。更早实际研究／授权起点UNKNOWN，不记0；该窗口与P166事实收束重叠，不把各单位epoch加总。Native01:21:34.809511Z至CLOSE1375.045150s／资格1530.319656s更窄；Root漏followup在01:40:08.823528明确纠正；旧Nativefinal与每条消息精确送达时刻未持，不编造空等秒数，全部等待仍含在上述窗内。还包括其余调度准备／review、provider／类初始化、冷暖、后验与结算，不能只算三actor16.6144651s／operator19.8352492s。三根metadata1,184,206B＜4MiB，全部owned文件计入，无fixture或JNA例外排除。

Root依预声明默认PARK：Source与Test仅D，不发表、不建候选baseline，current351保P163采用图，不回滚（从未采用P167）。不改loader或追加样本找绿，不重录、JFR或fullcase；本次只unit／daily11-09／W46三事实docs。0新增SAVE，不报有限秒／保存日，不授整体worker／Runtime／10秒目标，所有旧PARK／失败保留；正常发表与下一独立源码热点并行。

原件：[Root全部32／provider／PARK独核](D:/ck3-state/resume91-root/post-vacation-20261107/P167-ACTUAL-FIRST32-26ORIGINS-SUN-PROVIDER-FUNCTIONAL-AND-PARK01.json)（27,408B／`dfa01f1ea03cbd65d9c77900bf043d3fb561cec3669058253a128ebbb98b0413`）；[Native最终资格](D:/ck3-state/resume91-native-integration/p167-private-packet-test01/QUALIFIED-P167-FIRST32-PUBLICREADER-FUNCTIONAL-PROVIDER01.json)（51,847B／`ac68e32f5e70f582640a1121cf13dcec8146d773cc9b49650c954f0027ba3d5b`）；[全部32及actual provider](D:/ck3-state/resume91-native-integration/p167-private-packet-test01/reports-component/p167-public-scoped-reader-packet-copy-fixed32.json)；[owner全部端点独算](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-private-packet167/OWNER-ACTUAL-FIRST32-PROVIDER-AND-PARK-REVIEW01.json)；[独立PARK审阅](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-private-packet167/read-only-fixed32-review01/REVIEW.json)。
