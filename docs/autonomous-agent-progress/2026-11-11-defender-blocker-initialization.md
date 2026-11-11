# P222：Defender blocker初始化省去临时列表

本单元只改 `DefenderContinueRisk.observe(Request)` 原191–195行：将新建的本地 `TreeSet<Blocker>` 上 `addAll(List.of(原五个枚举))` 换成同原顺序五次 `add`。比较器、原 `List` import、初始require以及后续contact、siege和最终不可变结果逐字保留；不改任何Guard、Codec、parser、hash、oldencode、公共API或数据类型。源14177B/929f3617…变14189B/6ae0c943…，行数相同，五行逆换后整叶bytes与正式7ff19e671e基准完全相等。

原容器是本方法独占的具体TreeSet，比较器只比较固定Blocker枚举的wire字符串。原List.of5不是SortedSet，本机JDK21的TreeSet.addAll走AbstractCollection逐项add；因此五次同序add保留原插入和比较顺序。原五个枚举均非null；不引入缓存、常驻集合、共享builder或提前返回。TreeSet节点和最终List.copyOf仍保留。这里只消除这段临时List.of及遍历接线，不给出实际分配字节、GC、寿命、自然调用频率或耗时收益；OOM、异常栈和调试信息不冒称逐字不变。

唯一生产TU实际编译成功，得到完整17个类、118个Code程序。16个嵌套类二进制完全相同；目标外117个程序、公开API/字段/Nests、五个BSM和全部局部操作保持。目标observe的428B变453B：旧PC27..52的五个字段引用、List.of及Set.addAll，替为PC27..77的五组aload1/getstatic/Set.add/pop。169条外部指令、26个分支及完整contact/siege/return路径逐项映射；CP376→368仅删除上述两个已不用调用的八个精确条目，无新增CP或LDC缩宽。LNT32→36，增加各add的192–195行记录，其余行号不变；全部LVT起止、StackMap及参数名按实际PC映射核验，没有全局mask或省略局部load/store。

必要的原Test只增编1TU/1类，原完整类首次JUnit实际25通过、0失败/错误/跳过：14个原producer-golden向量和11个静态测试，suite2.328秒。原资源38052B/SHA3efece10495c0cd208d27f251056593aabf047f259844e265cbed8efc3323656直接读取，未复制、裁剪或扩大；逐个factory[i]的完整UID/display对应原cases[i−1].name，不要求XML文档次序。保留完整expected JSON、read_only/非授权字段、encode/decode roundtrip、严格数值与缺失/未知字段、源帧/省份/arrival/bounds及集合不可变断言。没有新增镜像测试、假fixture、GuardEvidence/ACK/ledger、原producer调用或benchmark；原25软件资格不代表所有输入穷举或性能通过。

本轮实际共三个软件JVM：生产编译、必要原Test编译及唯一JUnit，均exit0、契约接收、CLOSE fenced/released。actor合18.957819999777712秒嵌在operator合23.173805100028403秒内，二者不可相加或代替整轮。SourceReady04:21:27.429434Z→末JUnit CLOSE04:30:25.445046Z为538.015612秒，至final04:33:01.070066Z为693.640632秒；Plan文件04:22:25.659791Z是后到封件，不能冒作更早许可或开始。更早真实起点UNKNOWN；全部准备、源/Code/测试/XML审阅、错误和等待保留，到正式发表的后到全窗另记。

准备消息曾把静态测试手数12，已在实施和Java前纠正为11；owner首次Code checker把复用LVT的(start,end)误作(start,length)，写证明前KeyError，0VM工具窗0.2046987秒，02只纠正坐标读取，成功窗0.2044272秒。原件和未知process耗时保留，不改被测源、类、原Test或标准来换绿。final写后五个元数据根1082894B，小于4MiB；三个tmp各仅保留一个空hsperfdata目录，regular files为0。原final的tmp_files=1是目录entry计数口径，后到澄清不回写原件；不推断运行内存峰值或process-wide JNI为0。

主要具名原件（J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-defender-blockers222，N=D:/ck3-state/resume91-native-integration）：

- J/candidate01-owner/SOURCE-READY01.json：2606B/4365e4c7…；源码14189B/6ae0c943…及wholeinverse patch原件。
- J/owner-review01/ACTUAL17-117OTHER-FIVE-ORDERED-ADDS-CODE01.json：13939B/92bf426e…；原118程序全覆盖，无Java或Native helper执行。
- N/p222-defender-blockers-junit01/reports-junit/TEST-junit-jupiter.xml：57959B/4f62f2d3…；J/owner-review01/ORIGINAL25-FIRST-FULLCLASS-XML-OWNER01.json：11150B/7986d7f2…。
- N/p222-defender-blockers-junit01/FINAL-P222-SOURCE-CODE-ORIGINAL25-ALL3COST01.json：18759B/deae21b2…；J/owner-review01/FINAL-ALLREFS-THREEACTUALS-ALLWINDOWS-CONSISTENCY01.json：1664B/18a72c79…，独核44个唯一pin、三份actual/CLOSE及17个完整UTC窗口。原final的后到peer切点保留。

正常exact4只发表唯一生产叶、本单元及daily11-11/W46追加；原Test/资源、其他生产源码、tools、CI、pom、AGENTS与运行source307不动。历史OFFLINE378输入和current-mode P0运行资格分账，发表不自动换离线基线或实机装载；不补授热重定义、P100/Sway诊断或运行准入。本轮无量测、无新增确认保存，秒/新增保存日为null，10秒目标未通过，主目标继续。
