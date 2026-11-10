# P221：原case0派系赠礼choose的固定组件测量

本单元独立比较 A=P111原完整FactionGiftPolicy三类、B=P220三组固定Set复用后的完整三类。只用原资源case0 selected-leader的完整输入，恰1条observation/1个member；默认Java ObjectMapper在setup序列化一次，实际raw1252B/SHAceba458212452295c762fff5420dadc1bb7f73807c50adfc419a8184f0de69e1。双方共用同一个Object[1]与raw引用，完整备份、每行前后及final的身份/全部bytes检查通过；原资源115155B/04e92400…前后SHA相同，不复制或扩大fixture，也不用256上界冒自然规模。

目标区间只有测试Caller读取/转换input[0]、直接public child choose、自然返回共同parent Choice并存入Object[64]，没有encode、反射目标、额外choose、blackhole或强迫其它carrier逃逸。原已编2TU6/57程序复用，不重编旧绿；Caller是此前模型完整候选原样源码采用，5/12/9B实际Code已独证，模型审阅状态不当测量资格。本次保持原historical377有序classpath，和后到离线生产选择、current-mode P0的实际65、运行source307分别记。

每个结果都在计量区间外经parent原P111 Policy encode、原完整expected12字段JSON相等、decode后模型相等、重编码bytes稳定；共2304次完整POST、4608次encode、2304次decode。没有NEW首A基线替代golden。原Test第74–75行第二次choose的input JSON-domain roundtrip没有额外塞入本测量，仍只引用独立P220原全类70通过资格。两侧各严格own Caller+Policy/Candidate/Frame四名，共8child定义；共同parent Choice六名及parent POST旧Policy另列，合15focused roles/13physical files，不称总JVM/hidden class数。文件pin/CodeSource/loader身份及父定义前后相同通过，非OSHANDLE/defineClass-bytes防并发篡改证明。

唯一固定Main实际exit0、契约接受、CLOSE fenced/released；16warm行每行16次、32measured行每行64次，4ABBA+8ABBA固定48行2304次，measured每侧1024次、retain64。全部48的顺序、完成/完整POST计数、所有原端点与差额、输入、来源、三份supported/alreadyenabled Counter状态、两loader关闭及finish报告SHA通过。支持/启用从未改动，缺支持即STOP而非fallback；没有追加样本、调参或重跑。下表从全部32实测行用Fraction独算，每行除64；八组signed(B1+B2−A1−A2)各除128，没有拿单组分子冒每次差值。

| 指标 | A均值 | B均值 | 均值变化 | A中位 | B中位 | 中位变化 |
|---|---:|---:|---:|---:|---:|---:|
| 目标wall，ns/次 | 169774.121094 | 134338.671875 | -20.872115% | 27810.156250 | 13941.406250 | -49.869371% |
| 目标allocation，B/次 | 13095.960938 | 12719.742188 | -2.872785% | 13120.000000 | 12736.000000 | -2.926829% |
| row enclosing，ns/次 | 420223.535156 | 250711.718750 | -40.338487% | 126102.343750 | 43810.937500 | -65.257634% |
| POST+clear，ns/次 | 249858.007812 | 115913.085938 | -53.608417% | 70795.312500 | 23218.750000 | -67.202984% |

冻结的allocation、latency及两者合取门均为true，仅支持这个有界组件。八组allocation全部负；target为7好1反，cycle1反向+20412.5ns/次，配对中位−21941.015625ns与两侧中位差−13868.75ns是不同统计量。outer与POST各7好1反，反向发生在cycle2，不能只凭三个true外推稳态、自然分布或对象类型因果。

所有冷值、异常值及反向都保留：warm A0目标100.7333ms/outer167.3073ms，warm B5 outer97.5212ms；measured A39目标115.3984ms、B38目标112.0993ms，A16 outer120.4875ms、B26 outer82.3653ms等均未删。目标每次min/max：A4843.75/1803100ns，B4564.0625/1751551.5625ns；全部四指标及CPU的min/max另件由同raw补算，没有新采样。CPU measured31/32为0且B16行全0，warm14/16为0，唯一measured正值是15.625ms粗粒度；CPU相对比例为null，不报−100%或因果提速。whole-JVM heap/GC仅共享观测，非每侧live/峰值。类初始化、静态图常驻、首A之后共享parent POST与JDK预热效应和全部warm成本保留，不拆出某个Set对象分配机制。

两个软件JVM仅原必要harness编译和本次唯一Main。actor合9.784054799936712秒嵌在operator合12.805963500053622秒内，不能相加或替代整轮。具名Plan→CLOSE20507.594006秒→final20825.784137秒；SourceReady→18082.525413/18400.715544秒；原measureReady→CLOSE14807.991676秒，当前MAX1 AUTH→BEGIN23.652917秒。全部用户暂停、必要P0优先/等待、源码与Code审阅、模型准备、原错误及恢复准备都在完整墙钟中，不从19:45恢复点重开端点；更早真实开始UNKNOWN。Main自身setup585.7327ms、warm含POST427.8549ms、measured含POST687.4765ms和closure等只是子窗。final写后三metadata根1262110B，小于4MiB；tmp文件0、保留空目录不冒堆/JNI/连续峰值为0。

原错误/原件不改写：source writer把Caller注释与body同token误计；owner实际Code跨classmanifest顺序误设及猜旧inline脚本路径缺失；Native Code多次薄writer/引用修正、parentorigins dict切片0VM0.2497443秒、rawchecker将已资格的measurement行标签错读为measure导致0VM0.1544186秒；修正只对原明示字段/引用，不改被测源码、actual类、raw、门限或次数。Root首次通用CPU百分比衍生了−100%不具意义，旧结果保，后到CPU相对值改null；没有凭错误derived百分比补采样。完整错误、未知进程耗时与等待由原件和全窗口保留，不把未知当0。

主要原件（J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108，Q=D:/ck3-state/resume91-native-integration/p221-faction-fixedsets-measure-test01）：

- Q/reports-component/faction-fixedsets-measure221-report.json，80327B/60dbd303…；finish712B/c0778fe2…；实际Main ACTUAL1754B/05ec7b61…和CLOSE240B/b645a082…，末CLOSE19:45:55.246476Z。
- J/construction-faction-fixedsets-measure221/owner-review01/ACTUAL-ALL48-EXACT-PAIRS-INPUT13FILES-ORIGINALFULLPOST-OWNER-REVIEW01.json，18607B/31238f47…；同raw minmax补件2488B/26e83d5d…，首次独算无新错误/无Java/未执行Native checker。
- Q/FINAL-P221-ORIGINALFULL-CHOICE-ALL2COST-FACTS01.json，24473B/38845ad3…；原Plan19182B/60ede8e4…，实际源/Code/编译、全部pause/P0长等待与后到发表成本分别保存，不倒填旧资格切点。

正常exact3只发表本事实单元、daily11-11与W46，生产Java/tools/benchmark源/CI/AGENTS/pom/活跃source307不改，不换基线或Runtime输入。本次不是P0实机或Sway验收，也不撤销P100同链限制；指标不发放运行准入。新增确认保存日为0，秒/新增保存日无有效数字，不能把上述微秒组件中位当整局/自然频率提速或10秒/保存日达标，主目标继续。
