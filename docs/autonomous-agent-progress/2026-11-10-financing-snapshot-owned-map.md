# P198：融资快照四个固定更新共用局部 Map

Root 已接受正常 DATA 域的有限源码、完整实际 Code 与独立六 literal 单用例功能回归。接受不包含真实 allocation、CPUwall、生产命中/频率、全部组合、Runtime 或 SAVE。

本单元仅合并 OrdinaryFinanceCollector.financingSnapshot 的四个固定 outer 更新。初始角色投影、每个完整 RHS 和嵌套 hello 投影照旧执行，局部 Map 只在首次更新需要时创建，最后构造一个拥有自己副本的 Obj。正常 immutable DATA 的值、键序、保留叶引用与输入不变由源码、实际 Code 和六个独立 literal case 分层验证；没有 allocation、CPU、wall、生产调用频率或热点收益测量。

若有 k 个 outer 分支命中，旧链的 2k 次浅 Map copy、k 个 Obj 构造位置变为 2 次 copy、1 个 Obj；k=4 时为 8 Maps/4 Objs→2 Maps/1 Obj，k=1 不节省构造，k=0 不增加 outer Map。这只是源码及 Obj.with/构造器的代数，不是实际 JIT 分配计数，也不是 N² 修复。初始 12-key 投影、各角色子投影、wars stream/Arr 以及 nested hello.with 成本均保留。

本切点 actual 离线软件仍为 current365。正式源码、编译、功能、Git、后到软件采用与 Runtime/SAVE 分别记账；不预填 candidate366 实际采用，不授 JVM 装载、热更或端到端加速。没有新增确认保存日，秒/新增保存日为 null，持续性能目标未完成。

## 原角色数据和求值顺序

[OrdinaryFinanceCollector.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/OrdinaryFinanceCollector.java) 基底为 43805B、`5c73c35eb1097c9cf171ed9334a966a7b80aa883fbaceff262b039c4a53983dd`，候选为 44231B、`f2c9b4c21a323db6d0188c10c21312f7aaf59b1850fbb7c0482c4ad25cd5aac8`。只改八个物理行，整叶 inverse 恢复基底，488 行保持。P196 发表推进 parent 至 6a2c4714，本 Finance 叶仍与 P190 实际编源完全相同；旧 current364 前检和后到 actual365 first-origin overlay 保留为独立切点，不旋转旧证据。

284–285 的 financingFields(original, exact12keys) 仍首先执行。该 helper 按原输入成员顺序过滤，并创建初始 projected result；不按白名单声明顺序重排。新 Map 从这个 result.members() 复制，绝不从 original 复制，避免泄露已排除字段。

四个原 type guard 依次检查 played_character、played_character_gold、active_wars、diagnostics。每个完整 RHS 都先完成，再于需要时复制 projected members、按原键和顺序 put。actor/gold 保持各自 financingFields；wars 保留整个 items.stream().map(...).toList() 和 new Arr，非 Obj 行按原值保留；diagnostics 295–297 及 nested hello.with 原字节不变。没有删除角色、改白名单、展开 helper、移动 Guard、parser、hash 或 oldencode。

四个被更新键互不相同。旧链前一次 with 只更换已读过的另一个键，不改变后续 guard/RHS 所取的子值；因此新实现读取同一个初始 result，与旧逐次更新后的读取在正常 DATA 域等价。原 result 及其成员均不变，局部 Map 不外泄，最终 Obj 仍创建拥有自己的副本。无分支命中时返回初始 projected result 的同身份，**不是 original**；任一分支命中仍构造最终 Obj，不因 equals 相同省略。私有初始 result 的精确身份由 Source/Code 证明，未冒作测试可直接观测的内部值。

无新 API、field、type、helper、跨调用 cache、raw+typed bridge、issuer 或权限。Obj 原定义允许 null Value，不增加校验；Arr 原 List.copyOf 和全部角色处理保留。删除中间分配会改变资源耗尽/OOME 的机会和存活期，不授恶意 Map/私态、Unsafe、反射或所有 Throwable 时序等价。

## 实际十二类与完整 Code

旧 actual Finance12 来自 P190 classes-prod，whole source 43805/5c73 与正式基底相同。生产只作必要 1TU12，沿旧实际 release21、无显式 -g/-parameters 的 profile；没有重编旧 SDK、Main 或旧绿族。实际 exit0、accepted，CLOSE 为 **2026-11-09T17:47:38.403100Z**，terminal 后 fenced 释放。

11 个 nested class 逐 SHA 与旧相同；新 Top 为 60947B、`9d511e5efd2facacbebdf71b37381eb7588b13374c1d1f950540ba44abbedf3f`，旧 Top 为 60814B、cb2e4e5e…。旧 API、fields、声明/flags、签名、参数、SourceFile、Nests 和 InnerClasses 保持。53 个方法中其余 **52 个 normalized Code 与异常表相同，38 个 raw Code 相同、14 个仅 CP 索引重排**；不把归一相同写成 raw 全同。CP 均为 1730 entries，完整 resolved symbol multiset、字面量与全部 bootstrap handles/args 相同；旧 LinkedHashMap.put Methodref877 已存在，没有新增语义 symbol。

目标 financingSnapshot 为 package-private static，Code 332→438B。新增 lazy-null、map-present 和最终 none/new Obj 分支是设计内，不要求旧新整图同构。Native 与 owner 分别解析实际 classfile，四个 guard/RHS 按局部槽和原后继逐指令核对，新旧目标全部指令恰分区一次，无未解释区域；0..90 初始投影 raw Code 相同。nested hello.with 为 old317→new390，wars invokedynamic 仍绑定原完整 stream lambda。

实际 base result 为 local1，只在初始投影后写一次；owned Map 为 local2，初始 null。四个静态构造位置 131/195/277/399 并不等于四次运行构造：后续受非 null 条件控制，最多动态创建一次 Map。四个 put 为 PC149/213/295/417；所有 members() 都读取 base1。none 在 PC425 取初始 result，any 在 PC429/434 new Obj(map2)。这些是实际 Code 证明，不是生产分支命中或执行次数测量。

## 一个 JUnit、六个 literal DATA case

[FinancingSnapshot198Test.java](../../tools/performance/financing-snapshot198/FinancingSnapshot198Test.java) 为独立 opt-in 工具源码，15112B、`0efd10bdabeff29cd9ff654c46f8500306aaa6a6104093977149eb0059a6c818`。同 package 直接调用既有 static 方法，未加 public 桥、私有反射、Guard/ACK/issuer、实际业务 fixture、I/O、协议 parse/encode、计时窗口、warmup 或 benchmark。

原样新 Test 1TU1 编译为 11924B、`2b5b930ed1a189080d7cd6474c3a0806bcc80e232567389d6081591077c35dae`，major65、SourceFile 正确；实际 CONFIG/source pin、Test class 与 Run367 的 Test1+Finance12 first origins 均核。唯一 selector 为 `FinancingSnapshot198Test#sixLiteralCasesPreserveProjectedRolesOrderAndReferences`。实际 entry 顺序调用六个 helper，每 helper 一次目标调用；完整通过意味着六次调用，没有 setup 偷跑。这不是六个 JUnit tests，也不是带计数插桩的生产调用数。

- none：去掉 secret_outer，保留缺失、Nil 和 malformed 非 Obj 值、原输入顺序及叶引用；初始投影仍执行，结果不同于 original。
- actor-only：alive 先于 character_id，保留大于 2^53 的精确整数；投影值即使 equals 相同，actor 容器仍新建，叶引用和输入保持。
- gold-only：secret 裁剪，raw 先于 scale；小于 -2^53 的负整数、叶引用及输入顺序保持。
- wars-only：Obj 行只保留 war_id；Text 和 Nil 行保持原位置及身份，原 Arr/row 不变。
- diagnostics-only：非 Obj hello 仍是原 Text DATA，pid/generation 保原输入顺序，secret 裁剪、输入不变。
- all：actor/gold/war 共享同一个输入 Obj，分别正确投影且不混角色；nested hello 删除 secret，保留与白名单反序的输入键序；outer 键序、所有保留叶引用、alias 和输入原值保持。

三引擎 XML 合计唯一 **1P、0F、0E、0skip**，其余两个引擎 0 tests；testcase **0.092s**、Jupiter suite **0.122s**，CLOSE **2026-11-09T17:58:19.143665Z**，exit0 accepted、输入不变、terminal/fence 释放。此运行没有性能窗口，时长不作为 CPU/wall 收益；六个选择的 case 不授全部 16 个 outer 组合、异常域全覆盖或真实 caller 命中。

## 费用、预算与可核原件

生产 actor13.5829215s/operator15.8081829s；Test 编译4.797795s/5.7601363s；JUnit2.7022632s/3.5849706s，三 actor 合计 **21.0829797s**、operator 合计 **25.1532898s**，均只是资源子窗。最早具名 Native 只读 checkpoint **2026-11-09T17:14:43.790861Z→末 CLOSE2615.352804s→final qualification2771.203029s**；Owner SourceReady17:20:44.675712Z→末 CLOSE2254.467953s/qual2410.318178s；后面的 scaffold17:27:34.756240Z 是更短内窗，不相加。更早实际研究起点 UNKNOWN，不记 0。上述 UTC 时刻在北京时间均为 11 月 10 日。

前检表格格式、最终费用锚点 lookup、Root 路径分隔符误比，以及 owner 工具外层 JS 语法错误均保留原件。最后一项在 exec_command 启动前被拒，没有 Java、源码/Test 或 Git 改动；修正只写 metadata。准备、角色与 Code 审阅、调度、授权、等待、费用核验及 Git 费用不删除；三阶段各第一次唯一 JVM，没有 Java 失败后重跑。

Native final 之前三 roots metadata 为 1221759B/97 文件，final 写入后为 1244675B/98 文件；后到 budget/summary 的静态切点为 **1247354B/100 文件**，均在原 4MiB cap 内。原预算和切点保留，不覆盖。tmp、owned DLL files 与 business fixture 均为 0，但目录无 DLL 不证明进程级 JNI 未加载；process-wide JNI、连续硬峰值和 Java heap peak 均未持证。classfile、XML、脚本、日志、错误件按 metadata 原分类，不当作性能测量。

可核原件：`N/p198-financing-snapshot-prod01/QUALIFIED-P198-PROD12-TEST1-SOLE6LITERAL1P-ALL3COST-FINAL01.json`22916B、`ead9b8d47b64099f219b139a2e91f3a90af3dbcc34bd1eeacebe3e107e2ef383`；同根 Code55937B、`7a4c471b37e0336c987ea0e90a7a70bf2fb42d996745162d9200ff32472e6e10`，以及 `ACTUAL-ALL3ROOTS-METADATA-BUDGET01.json`1566B、`35bea5e8d7c21e65d131db6121686117d9d846dcb50b26fa3f6d2b67a778ff3c`。Jupiter XML45293B、`922da814c1a21a82fd97977b73328226054f7e87ee5afbd9e3e14101904f39c9`；owner 独立 Code22267B、`5c3597e501db0611a045afe4968a4fcea60f66c11b2b5771f8f7fe4444be3786`、solecase6421B、`87672aaea6e218f80e27b6dd5ddbd76e40c768c350c4115174a6e43060a0010c`。N/J/R 分别是独立 Native、Java 交付及 Root 证据根，原件未复制为新的业务来源。

exact5 仅本生产 Finance 叶、standalone Test 和 unit/daily11-10/W46。Obj/Arr、role 白名单、financingFields、其它生产源、旧 Test、AGENTS、CI、pom 及运行文件不变。源码、实际 Code、有限功能与后到软件采用继续分层，不以本单元交付作为持续优化目标完成。

Root 最终接受：`R/P198-LIMITED-FOURROLE-SOURCE-CODE-SIXCASE1P-ACCEPT01.json`9963B、`82de5f43a9108a55c12da405e201dcfee71f01d2567c59781bc0cf93c199ff64`；三阶段实际、原件与预算另核通过。正式发表不补授 current366 实际采用，后到 Root 回执独立。
