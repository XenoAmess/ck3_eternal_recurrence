# P214：私有 Observation 保存本次已拥有图，仅源码与实际 Code 资格

仅改 OrdinaryWarPriority 私有Observation构造器第38行两个RHS：保留本次observe已拥有的snapshot/priority引用，仍按snapshot→priority顺序赋给原两个private final字段。24454→24432B，290物理行中其它所有字节保持，整叶逆回P211正式d615源。初始D稿e004切点保原；P213后到80b仅三事实文档，同生产blob，不回填早来源。

所有权限于原正常public Input路径：final record构造时克隆两个byte[]、getter再克隆，observe独立parse出snapshot/root并新建out；唯一private构造调用在199，没有外部typed JsonNode或回调注入。两图可共享本次私有子树，但之后只读，value()/snapshot()仍deepCopy，两个序列化出口仍给新byte[]，boolean/count不返回可变树。Input clone、双parse、全部Guard/理由/排序/count/encoder及P211第187行原样，无API/field/helper/flag/cache/trusted桥或权限变化。

公开count的BigInteger输入域不缩窄，也不借P197被否的typed-input前提：原count程序全部保持，只在本地比较/集合中使用用户参数，不将其放入私有图或暴露JsonNode。标准解析图的封装使内部alias不可观察；恶意反射/Unsafe私态、null调用私构造、OOME/资源异常时序及GC不授全等价。两deepCopy主要复制容器/引用结构，不是每次复制全部大String或2倍raw字节；实际容器数、自然频率、allocation/CPU/wall/retainedheap未知。

唯一1TU4生产编译首actual exit0、fencedreleased。Observation6701→6695B/new SHA f9499404411e01a09c69d36bddb0918e14239a89757396aed467f8faa3b570ab；private ctor21→15B，只去old6/14两invokevirtual，完整余下9指令及stack2/local3保持，new fieldstore6/11仍snapshot→priority。fields/API/params/Nests、CP完整符号多重集与BSM保持，没有global slot/name mask、dummy helper或synthetic迁移。

Observation实际11程序是ctor+8源码方法+2synthetic；其它10完整程序1raw/9resolved相同，两个getter的deepCopy PC4/4不动。另Top/Input/Finance三class整字节相同，46+6+10=62程序；合other72完整保留，唯一observe构造调用仍PC1966。原计划“8other”只是源码声明数，后到11程序澄清保原并采用更完整口径。FullJsonTree/factory仅必要fresh NEW/只读原Code前提；其旧C0 compilerCFG/整编源谱系NOT_HELD，不扩全SDK审计、不改parser，也不授Instrumentation或Runtime装载。

本轮 **0Tests、0JUnit/1P、0benchmark/新fixture/完整case**。原Chooser完整helper含GuardEvidence/ACK/replay/ledger，整体排除，不裁剪/包装；没有已资格pure ownership/count selector，P212政治四例不能当此分支或复制出口覆盖。接受依据为正常DATA封装/source和实际全部Code，不冒已运行别名/ownership测试或性能通过。

actor4.760833500069566s、operator5.936386400018819s仅嵌套子窗，不相加代替整轮。Planning 2026-11-10T03:44:37.519144Z→CLOSE1234.062039s→Native final1514.157802s；Root实际source接受→331.840840/611.936603s是内窗，AUTH→BEGIN28.940017s等待亦保。真正ownerReady在CLOSE后165.864556s才封，Native原CFG/Ready的owner seal null保持，不补造JVM前文档门。后到owner实际Code与Git另件，Native早peer[]不回填；更早真实begin UNKNOWN不记0。

所有源/前检/私有图证明、授权、Code、准备、错误和等待保原。Native两个只读Codehex形状、fieldref/call误分类tool wall0.2059595/0.5788198s保，精确进程耗时NOT_HELD；一条原preparer大小消息11957误写已勘误为实际8608B，原文件/预算始终8608，不是源码/标准变化或Java重跑。两Native根及额外固定8608B原preparer，含budget/final写后快照580641B，在4MiB内；tmp/owned DLL/Test/fixture0不是内存0、全JVM JNI未载或hard峰值证明。

证据根J/N/R沿用：J/construction-observation-owned214/candidate01-owner源码24432B/a9a9b3f4…、inverse1118B/407b2700…、后到Ready4913B/fc59a4d1…、ownership5400B/3e802e5b…；同unit owner-review01实际Code proof13014B/9ac5b16a…。N/p214-observation-owned-prod01/QUALIFIED-P214-CODEONLY-OWNEDGRAPHS-SINGLECOST-FINAL01.json14435B/5ee1acad…；Root交付接受2121B/764d5da1…；完整路径/SHA由发表Ready保。

正常exact4仅该生产叶与unit/daily11-10/W46，原Test/helper/parser/Guard/hash/oldencode/CI/pom/AGENTS不变。当前offline374，future375候选与Root后到实际离线选择另账；无新Runtime/Game/GET/P100/账本/UNKNOWN、SAVE或10秒达标。新增确认保存日0、秒/日null，主性能任务继续。
