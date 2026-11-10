# P217：内部 Input 副本消除的固定公开路径比较

本轮为独立新测量，比较 A=P214 完整四类与 B=P216 完整四类，仅 observe 内部两个丢弃的 getter 副本不同；公开 Input 构造器及 getters 的防御 clone 仍保留。目标保持 Function.apply 的两数组读取/cast、new Input→observe→toJson 及返回 byte[] 存储。两侧使用相同 P212 BudgetObservations、原 BudgetJson 与冻结 historical374；不是当前 OFFLINE375 整体测量，也不是追加或重跑 P215 样本。

新 Main 仅1TU编译六类、65个程序；旧 Caller1250B／78bb688d…的三个程序 binary原样复用，0复制、0增编，不是新编第七类。63个完整程序仅精确 Main owner 迁移，main 分别核新 Main root、旧 Caller root、报告所属新单元及 CP0；clinit 只四个实际矩阵常量变化。严格每侧7个具名 child、四URL不添 Main，共14具名来源／11物理文件／8种SHA；parent原 BudgetJson另定义核同物理原件。这不是JVM/hidden类总数，磁盘pin/loader/CodeSource也不是OS HANDLE或实际defineClass字节证明。

输入沿原完整 sources 方法首个 available Source20／triplet145／metadata146／war0；完整 snapshot/root 各 canonical 一次，实际2664／636B，共享同 Object[2] 和两份 byte[] 引用，完整 backup/长度/SHA逐行前后及最终保持。每个输出先用原 parent BudgetJson.equal 核完整政治 SUBSET，再核本轮首合格 A 新建的完整 bytes/tree/递归键序 observer。全部2304输出通过，NEW baseline3076B／ce873a3d7cd548ea668c0fefc40e494f50f257c7d0fdb2ffdfab00f1836a9fcf；未借旧测量结果作 seed。

完整 WarPriority 原始 golden 仍 NOT_HELD；上述完整输出差分 observer 不是旧 Test 的全输出 oracle、独立政策正确性或权限证明，两侧可能共有既存缺陷。原 Chooser Guard/ACK/replay/ledger helper整体未使用或裁剪。测量正常非空 Input，不授 P216 null 分支实际负例通过。

首次新 Main 编译和唯一测量 Main 均实际 exit0／accepted／CLOSE fencedreleased。固定48行2304调用：4ABBA×16为16行256次 warmup，8ABBA×64为32行2048次 measured，各侧1024次；retain64、metric分母64、八组 signed 配对分母128。无额外 setup/POST target、N/堆/预热调参或补样，不强迫 Observation 逃逸，允许 JIT 自然消除本消费者不使用的工作。

| 每调用指标 | A | B | 变化 |
| --- | ---: | ---: | ---: |
| allocation mean，B | 98176.8984375 | 94776.546875 | −3.463495% |
| allocation median，B | 98171.0625 | 94824 | −3.409419% |
| target mean，ns | 304563.28125 | 233825.78125 | −23.225879% |
| target median，ns | 96863.28125 | 69282.8125 | −28.473606% |
| enclosing median，ns | 122225.78125 | 83339.84375 | −31.814841% |
| POST median，ns | 12353.90625 | 13850 | +12.110289% |

Root、Native、owner 独立从全部32 measured 原端点作 Fraction 计算，所有报告统计一致，原冻结 allocation／latency／combined 门均 true。allocation八配对全负，paired median−3338.65625B，区别于两侧median差−3347.0625B；target6好2反、paired median−44928.90625ns。enclosing5好3反，POST只有4好4反、paired median+1853.515625ns；POST均值受outlier影响下降，不掩其中位数反向。

cycle2、7 target配对分别反向+74767.96875／+18386.71875ns。warm A0 target185.9511ms、measured A16 target94.1917ms/B18 target71.5849ms/A23 target64.0986ms，以及 A36 target8.1898ms／enclosing93.9908ms等完整冷值/outlier全保，不作为steady-JIT或整体提速机制。CPU measured27/32、warm15/16为零；measured A总93.75ms，B的16行全部为0，比例/因果比为null，不能报−100% CPU收益。heap/GC仅共享JVM观察，不是per-variant活跃量或峰值。

两JVM actor合9.396511900005862s／operator合11.124037900008261s只是嵌套子窗，不能相加或替代整轮。Plan→末CLOSE8416.759707s／Native final8665.780599s；完整 SourceReady→6849.343019／7098.363911s；AUTH→BEGIN20.647897s，所有长等待、源/Code/CFG/审阅/错误与准备保留，更早真实begin UNKNOWN不作0。owner raw计算首次成功，无数据/Java重跑；此前raw method-key未迁移owner的0VM工具0.2047096s、inline空格语法0.1756629s及64→63程序数口径更正均保原件，不改Source/类/门，确切process耗时未持。Git成本在发表回执继续记账。

Native final封件后3root metadata1013588B／83文件，小于原4MiB，tmp/DLL文件与fixture磁盘副本0不等JVM内存或process-wide JNI为0。旧 Caller/已资格产物复用不抹历史成本，后到owner raw引用另append，不倒填旧 final peer pending。

证据根 N=D:/ck3-state/resume91-native-integration，J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108。N/p217-observe-input-measure-test01/reports-component/observe-input-measure217-report.json89390B／SHA256 8f15f5fb57605481445f701db50151a31ad3b8b857350a3d998a7b723891fe0f；同根Native final34329B／37795f0def56c9f519f23c577702225ff064395348ee97349476b7f00c8627c5。owner actualCode45268B／916fa44d…、all48 Fraction18539B／75bafbf8…保于 J/construction-observe-input-measure217/owner-review01。

测量与 Native final 时实际 OFFLINE375 的切点保留。后到 Root 以独立回执 R/P216-ACTUAL-OFFLINE-SOFTWARE-CURRENT376-SELECTION01.json（2329B／8a05a0eccdd8be06a18584330fc33b5fae10ecf0345174664537fd5c3e85db83）只选择 OFFLINE376：P216生产四类前缀加literal375，177项critical origin中4replace/0add，没有P217 Main前缀，0额外Java/load/Runtime。该生产输入列表的376与本次新Main+resources+historical374的376条测量CP是不同名单；原candidate false/null/PENDING、SourceReady/报告current375不回填。

仅发表本单元、日记和周记，不发布harness或改生产/CI/pom/AGENTS，不新增baseline选择、回滚或授装载/Runtime/GET/P100/SAVE。结论限于此固定归档消费者，不授自然输入规模/频率、count/sourceSnapshot、端到端或十秒/新增保存日达标。新增确认保存日0，秒/新增保存日null，主任务继续。
