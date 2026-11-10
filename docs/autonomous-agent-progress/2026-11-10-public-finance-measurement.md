# P219：派生公开 finance 组件的固定测量

本轮比较 A=P216、B=P218 的完整四类，同用 P212 BudgetObservations 与原 C0 BudgetJson，只测公开 Input→FinanceRequest→finance→返回 byte[]。历史控制是 P218 CONFIG 的376项 classpath，新 harness 加前缀后377项；它与当前实际 OFFLINE377 的生产输入名单不同。没有改变生产源码、harness正式树、CI或运行输入，也不是 P217 observe 的补样。

输入来自原 WarBudgetGoldenTest.negativeTreasuryDoesNotBecomeUnsignedAndOneTimeQuoteIsNotMultiplied 第117–124行完整 JSON setup：snapshot/root 各 canonical 一次，实际122/234B，另用原 price3、months18、floor0、window6、other1。两侧共享同一个 Object[7]及七个引用，完整 raw2 备份、类型/值在每行前后和末尾检查。原第126–130行五条断言逐字保留，检查 available、-8、13、0及 retains_military_allocation=false；这是原 SUBSET，不是原 public FinanceRequest 完整 golden。每个输出先通过五条断言，再与本轮首个合格 A 输出新建的完整 bytes/tree/递归键序 baseline 比较；baseline1013B/26503576…、firstArow0、共2304次检查，属于 NEW 差分 observer，仍可能共享既有缺陷。

首次且唯一2TU6编译和唯一测量 Main 均实际 exit0、契约接受、CLOSE fenced/released。实际56程序=Main37+Counters5+Loader2+Fixture8+Side1+Caller3；Caller5/64/9B，七数组读取/cast、Integer拆箱、两个公开构造及单次 finance 都自然留在 kernel 内，没有 setup/POST 的额外 target、私有反射或强迫对象逃逸。严格两侧各7个具名定义，共14条来源、11个物理文件；共同 parent BudgetJson oracle 是同物理文件的另一运行定义，hidden/JDK生成类总数未持。

固定4ABBA×16次 warm 与8ABBA×64次 measurement，共48行2304次，测量每侧1024次；64槽保留输出，逐行64、配对128归一。原始端点、顺序、全部 POST、输入/来源、三次 Counter 状态、两 loader 关闭及 finish SHA 均通过，Counter 本来 supported/enabled，未切换状态。Owner、Root、Native 独立 Fraction 复算一致，原 allocation/latency/bounded-micro 三门 T/T/T。

| 每调用指标 | A中位数 | B中位数 | 中位数变化 | 均值变化 |
| --- | ---: | ---: | ---: | ---: |
| 分配字节 | 20944 | 20544 | −1.909855% | −2.333642% |
| target ns | 10551.5625 | 8739.84375 | −17.170147% | −27.037369% |
| outer row ns | 45938.28125 | 65357.03125 | **+42.271390%** | −52.939787% |
| POST及清理 ns | 12329.6875 | 8298.4375 | −32.695476% | −76.687619% |

八组 allocation 全负；target七好一反，paired中位−1650.78125ns，与两侧中位数之差−1811.71875ns分开；outer五好三反，POST六好二反。全部冷值和 outlier 保留：warm A0 target217.3525ms/outer257.3257ms，测量A16/B17/A28/B22及A39 outer80.0883ms等不删、不当稳态。外层中位反向必须与绿色均值、target局部结果并列，不能据此称整体提速。32条 measured CPU 全为0，warm14/16为0；CPU因果比例为null，不报零成本或−100%。共享 heap/GC 不是各 variant 峰值或机制证明。

两 JVM actor合8.646160900010727秒、operator合10.406610399950296秒仅嵌套子窗，不相加或替代整轮。Plan→末CLOSE3857.602234秒→final4304.872085秒；完整 SourceReady→CLOSE2595.670167秒→final3042.940018秒，测量 AUTH→BEGIN24.783710秒。更早真实开始 UNKNOWN，所有源码、编译、审阅、cap拒收、名字/计数/映射错误与等待完整保留：原 draft 行标签误写 observe 在首编译前仅纠正该 literal；owner gate摘要及旧Caller后缀映射修正均保原件，不改输入、门、源码语义或重跑 Java。Native四 metadata 根1216137B/104files，tmp及ownedDLL文件0；不授全进程 JNI、Java堆或机器峰值为0。

主要原件：

- N/p219-public-finance-measure-source01/SOURCE-READY01.json，9793B/5c67bef2…；原 Test11043B/5d8e5525…。
- N/p219-public-finance-measure-test01/reports-component/public-finance-measure219-report.json，125162B/b9754e7b…；finish708B/6973164e…。
- J/construction-derived-finance-measure219/owner-review01/ACTUAL6-56PROGRAMS-CALLER7-ORIGINAL5SUBSET-GLUE-OWNER-REVIEW01.json，15830B/bde07388…；独立全48复算16150B/750b6d7d…。
- N/p219-public-finance-measure-test01/QUALIFIED-P219-VALID48-PUBLICFINANCE-ALL2COST-FINAL01.json，37784B/5a203371…；Root完整成本接受1789B/ffaeff77…，后到owner一致性1151B/2fda7c8f…。

J为D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108，N为D:/ck3-state/resume91-native-integration。本次只发表本记录、日记和周记，不发布 benchmark 源码或改 baseline。固定派生组件证据不授任意数值域、自然公司规模/频率、worker、端到端、Runtime或SAVE收益；当前 OFFLINE377保持，新增确认保存日0、秒/新增保存日null，10秒目标未由此通过，主目标继续。
