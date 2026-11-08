# Native state 的有界空白前缀 veto（P138）

Root 采用本次改动为已证明的 pretty-whitespace 场景中额外比较器分配的消除，不授稳定 CPU、整体延迟、Runtime 或10秒目标通过。回退两次 B 都分配57,606,096 B，较后一次 A 的57,610,920 B精确少4,824 B；首 A 含冷成本，不能把均值差全归本方法。Owner-original，模型 NONE、0 HTTP。

P137 保留了完整解析回退，但其 pretty-whitespace 输入不可能与冻结的紧凑字节生成器逐字相同，仍创建比较器直到缓冲写出才发现差异。P138 仅在公开 `originalNativeState` 的同调用私有 byte-parsed Obj、原 native64MiB 条件内，先检查最多256字节。两个 bool 跟踪字符串与 escape，遇到字符串外 ASCII space/tab/LF/CR 即取消这次优化，直接进入原 parse／equals。未发现空白、截在字符串、escape 或 UTF-8 字节中，都继续原完整比较器；它不判结构、UTF-8、数字或有效性，不返回模型、异常或权限。

证明只适用于此处 parse 所得标准标量和冻结 compact writer。generic DriverJson helper 可接 custom BigInteger，完全不改，也不向其推广 compact 假设。原 parser/encode/write/hash/Guard、包头／预算／错误顺序和另一 private packet-input 路径保持。helper 无分配、无新 field/type/API、无跨 capture cache；原件仍由原 parser 接受或拒绝，不把 prefix veto 当 JSON 验证器。原测量 pretty STATE 首个字符串外 LF 位于零基 byte62，属源静态位置证明，不是额外一次 Java 测试。

生产只必要 Assembler1TU／6类首次编译0，Driver2原字节复用，私有静态 helper descriptor为`([B)Z`。只必要修改现310 Test1TU／5类首次编译0；原 Replay3和P134支持4类复用、支持源码0@Test。无生产／Driver／SDK／Main重编补绿。六个不同既有受影响方法在三个 JUnit JVM 全部通过，new unique0：

- 功能四方法：原P137完整字节／错误／clone oracle、真实 profile4 缺失/null/retained 重播、version3原重播、原 framing／packet mismatch。现原方法内增加13个有限 DATA 输入，覆盖字符串空格、escaped quote、奇偶 slash、literal u0020、四种空白、byte255/256边界和字符串／escape／UTF-8截断；只反射私有纯 bool，各合法输入另经真实旧／新公开入口完整 byte/model/原件不变对照，不是13个新JUnit方法。
- 真正归档：compiled15完整10类的 public Applied 一项，case113.047／suite113.076秒。软件210/240秒，业务原120秒不修改、不刷新。
- 原组件方法一项：case2.378／suite2.405秒，全部8行 completed／post checks／输入输出SHA通过。

组件 A 是精确旧 P137 Assembler6＋Driver2，两个具名目录中的完整8类在同一 child loader；否则其 package-private helper 会失去运行时包访问。DTO、Opportunity、Jackson等由 parent 提供，B 是新 Assembler与既有Driver同一parent。两边 Driver 字节相同但各自有独立 static factory，不能称共享同一个 factory。各自显式 `Class.forName(true)` 在 setup 计时：旧 Driver325.5473 ms、parent Driver1.2231 ms，全部计入setup和全JUnit成本，未调用target预热；这不是实际 agent 初始化热点测量。

它是 selected-leaf old/new binary、同进程有界组件，不是 same-binary 两入口或 whole old/new CP。仍为原3,400,000 ASCII opaque DATA，canonical命中与原pretty-whitespace回退分开，各固定 A/B/B/A、每入口两样本、0 target warmup。实际命中率未知，不合并两个场景，不叠加P137不同cohort的百分比。

| 场景 | 行／入口 | wall ms | 当前线程 CPU ms | 当前线程 allocation B |
| --- | --- | ---: | ---: | ---: |
| canonical match | 0 A | 22.5234 | 0 | 33,977,168 |
| canonical match | 1 B | 9.8157 | 15.625 | 33,908,000 |
| canonical match | 2 B | 7.8709 | 15.625 | 33,906,840 |
| canonical match | 3 A | 8.3804 | 0 | 33,906,856 |
| pretty-whitespace miss | 0 A | 20.2216 | 15.625 | 57,781,608 |
| pretty-whitespace miss | 1 B | 19.5540 | 0 | 57,606,096 |
| pretty-whitespace miss | 2 B | 12.9200 | 0 | 57,606,096 |
| pretty-whitespace miss | 3 A | 19.7291 | 0 | 57,610,920 |

pretty-whitespace 两次 B 较末次 A 恰少4,824 B，与省掉比较器的源成本吻合；A首57,781,608 B含冷分配，均值57,696,264→57,606,096 B（−90,168 B／−0.15628%）只能描述该组，不能当成源码可省量。wall均值19.97535→16.237 ms（−18.7148%）也仅描述两样本，不授稳健延迟。canonical没有新的命中分配优化机制：均值33,942,012→33,907,420 B（−0.101915%）主要受首A冷差影响，不宣称新收益；wall均值15.4519→8.8433 ms，A22.52→8.38漂移，B0仍慢于末A。

CPU 原值大量为0／15.625 ms：命中 A0/0、B15.625/15.625；回退 A15.625/0、B0/0。性能百分比 UNKNOWN，既不报告回退CPU减100%，也不把命中零基准算成有限百分比。CPU／allocation查询包住wall区间，粒度、查询和冷成本不扣除。保留每行而非挑选有利样本。

| 必要阶段 | recording actor 秒 | outer 秒 |
| --- | ---: | ---: |
| 生产1TU6类 | 5.3053650 | 6.1628574 |
| 修改的 Test1TU5类 | 6.6643724 | 7.6417388 |
| 功能四方法 | 4.4086438 | 5.6036142 |
| public Applied15 | 115.3824787 | 116.2611458 |
| 八行组件 | 4.3423746 | 5.1746806 |

组件setup1.7217012秒，开始至报告materialization前1.9492385秒；class加载、双factory初始化、fixture parse/encode、postchecks、close和报告成本均在全JUnit／actor窗口，不当稳态target速度。actor含父 recorder 验证，不是child完整wall，outer也不与其子区间相加。首生产BEGIN11:15:23.080995Z→末close11:27:51.884732Z共748.803737秒，含测试源准备／审核／编测／等待；更早D CandidateReady11:09:05.551949Z→末close为1126.332783秒，首Ready前源准备另存，均不以抽样行代总窗。

全部实际阶段0退出、accepted、无timeout且close资源释放。源自旧collector的operator schema标签仍保原件，真实CONFIG／source／selector／class来源均指本单。源准备中owner曾误读工具JSON显示的反斜杠层，以为Java literal多转义；拟修脚本首个保护assert即停止、0候选写入／0formal修改／0Java，逐字符核验后确认01本来合法，按同一01字节采用。该只读判断／准备错误保留，不冒Java或模型失败，不抹去等待成本。

源／逆向／正式Ready在 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-native-prefix-veto138`；生产源码33526 B／`b00b98ebf23849932deb9a36e29db40df387ab2be6fdf767f52316a934e9c6cd`，Test43068 B／`07196d031dc3d4911b2c04c853b9073cfe2ab79ac97521574f48f75e9fec3c45`，Driver原074...未改。原Native ACTUAL/CLOSE/XML在 `p138-native-prefix-prod01`、`p138-native-prefix-test01`；组件report6785 B／`0bd4fe0394873404af9ca0b70388fd4e3949e2e5a43554357a0d22a0d43e0537`。owner全8行／实际回执复核19321 B／`9400b5fbe8c6c305dc84994699e125c2da27f73fcf8758ed57009bdc6af8edeb`，Root生产源审2645 B／`a5fba3fc652d33467be69fdd488d616772950c95ecfc18f431d4f318acba5859`、测试源审3221 B／`92ccd8c7c991e8877bba0c72c090f1ab2cfb49422d28a1863da6c28258437d96`另钉原件。

正式仅 [Assembler](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/driver/DriverObservationAssembler.java)、[现310测试](../../java/ck3-control/application/src/test/java/org/xar/ck3/control/application/driver/DriverFrameJoin310Test.java)和本单元／日周三文档。无HTTP／新JFR／Main03／额外JVM挑绿。P100拒绝链、账本、UNKNOWN、deadline、Guard和Runtime唯一owner边界不变，不授方法布局热载、head47、SAVE或实际智能体速度。下一借用bytes回调闭合复用仅独立源可行性研究，持续目标不在本单发表结束。
