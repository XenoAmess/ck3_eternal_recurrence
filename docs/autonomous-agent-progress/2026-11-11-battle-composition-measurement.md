# P225：原normalized_route完整Battle组合的固定组件测量

本单元比较A历史OFFLINE379的完整BattleRetreatPolicy22类与B=P224完整owner扫描后的22类。两侧各自同loader拥有同字节BattleRetreatCodec和同一Caller，严格24名/侧。目标按原Test真实组合 `encodeDecision(assess(decode(raw)))`，三个公开调用各一次，返回自然byte[]并存入Object[64]；Codec没有evaluate API，也没有checked异常包装。没有将目标缩成扫描循环或在kernel增加oracle、反射、黑洞或额外逃逸。

输入固定为原current-retreat-golden.json第0项normalized_route：完整input五节点、side0、owner29829、原ownLoss列表一行/匹配一行及完整preview，原expected全部24字段。107656B资源/SHA1351a9dce0f3dce0619dc13bf65b66c9c74dd30f03691930a0cec410b8c59613直接原路径读取，不复制到fixture目录。资源超过64KiB，沿原Test严格duplicate detection、USE_BIG_INTEGER_FOR_INTS的ObjectMapper及170000+EOF上界，不能用StrictJson解析整资源。setup按原Test53唯一 `StrictJson.canonical(vector.input)` 生成请求；真实Java wire为1870B/SHA5520643ba866a06b117bc20bae8d568eeb15ad70973b3f8de1872498eda3c66a，没有用Python预测wire或重建字段。

双方共享同一个Object[1]和同一raw引用。完整raw备份及107656B resourceRaw/独立backup在每行前后、final按完整bytes/身份/SHA核验；物理资源仅在setup/final重新读取并与原backup比较，不把内存核验冒称每行磁盘读取。输入保护开销按真实位置进入row enclosing或POST，未从总成本剔除。每个输出在target计量后由共享parent StrictJson.parse和原完整expected JsonNode相等验证，共2304次parse/完整golden；保字段集合/值和数组顺序，不新增object wire-order黄金标准。没有不存在的assertReadOnly、NEW首A基线、encodeRequest或setup/POST额外decode/assess/encodeDecision。原37例的输入模型roundtrip资格独立保留，本次未重跑原Test。

严格child拥有Policy Top+21nested、Codec和Caller，B22根优先于共同旧Codec根，DTO始终同一child，不在parent转换业务记录。实际48个child命名来源和单列parent StrictJson共49角色/47个physical文件；全pin、CodeSource、loader和前后约束通过，不冒称总JVM/hidden类数或OS-held defineClass bytes。父尾冻结历史379条，compact UTF8列表SHA66e5fae55df1b85b11959827a44edca4f15545e62d166db41156c86e5770314b；新harness+379的runtime380与独立production OFFLINE380是不同列表，未追随新选择或加入资源前缀。共享parent JSON/JDK、两child自然初始化和原Codec switch/lambda机制均计成本，不宣称完全冷或稳定JIT。

新harness两TU实际编译出六文件/60程序：Main38、Fixture11、Counters5、Loader2、Side1、Caller3。原Fixture五字段扩为七字段/两新accessor、构造器和完整Record BSM已核，不沿旧58猜测资格。全Code中38完整程序仅六owner符号映射，另外三程序各只有声明过的单一literal变化，其余19个必要glue逐项核验；clinit516指令栈执行出的五数组与原23family/46实际pin/CASE/ABBA一致。Caller5/18/9B按PC8 decode、11 assess、14 encodeDecision，kernel591 apply→596 Object存储、1038进入POST，POST124 parse→135完整golden，均为实际Code事实。Source01/02/03仅报告caption修正的原件保留；六个Source03模型辅助审空findings、0模型代码采用，不代替编译或运行资格。

唯一固定Main实际exit0、契约接收及CLOSE fenced/released。4ABBA warm为16行×16次，8ABBA measured为32行×64次，总48行2304次；每侧measured1024次、retain64，signed(B1+B2−A1−A2)按每侧2×64除128。全部原始端点/差额、逐行完成和完整POST数、输入/资源、49来源角色、supported且already-enabled的三份Counter状态、两个loader关闭和finish SHA由独立Fraction重算通过。计数器从不主动启用或fallback；improved严格w<0，false/MIXED也是合法数据，不调N或重采。

| 指标 | A均值 | B均值 | 均值变化 | A中位 | B中位 | 中位变化 |
|---|---:|---:|---:|---:|---:|---:|
| target wall，ns/次 | 161025.097656 | 75171.484375 | -53.316914% | 37563.281250 | 37091.406250 | -1.256213% |
| target allocation，B/次 | 59413.742188 | 59036.953125 | -0.634178% | 59296 | 58976 | -0.539665% |
| row enclosing，ns/次 | 229342.675781 | 99465.722656 | -56.630085% | 68113.281250 | 54443.750000 | -20.068819% |
| POST+clear，ns/次 | 66242.871094 | 21331.738281 | -67.797685% | 12298.437500 | 7763.281250 | -36.875873% |

预声明allocation/latency/合取三门均true，只支持这个固定完整组件。八组allocation全负，中位少320B/次；target六好两反，配对中位−3089.453125ns与两侧中位差−471.875ns是不同统计量。target的cycle1/2反向配对为+12714.84375/+89909.375ns；outer六好两反、POST六好两反同报，不以其它窗口消掉坏组。mean下降53.316914%与median只下降1.256213%的差异很大，不能将mean当稳定提速、扫描机制/JIT/GC因果或整局收益。

全部冷值与离群保留：warm B6 target120.5661ms、A0 target96.0794ms；measured A16 target93.706ms/outer131.8332ms、A19 target20.5765ms、B22 target13.6731ms均未剔除。measured每次target min/max为A18903.125/1464156.25ns、B18159.375/213642.1875ns；五指标按warm/measured和A/B的完整min/max见独算原件。CPU measured28/32为0（A13/B15），warm12/16为0，正值15.625/31.25ms等粗粒度量化完整保留；relative/causal百分比为null，不以均值或全零推CPU因果。whole-JVM heap/GC前后不是每侧live或连续峰值。

本轮仅两个软件JVM：新2TU6/60程序harness编译及唯一Main测量，无生产/旧Test/SDK重编或额外样本/profile。actor合9.260845100041479秒嵌在operator合12.211864299955778秒内，不可相加或代替整轮。Plan05:44:40.867820Z→末CLOSE06:32:31.762794Z为2870.894974秒，至final06:38:45.345203Z为3244.477383秒；SourceReady03→CLOSE1341.327994秒/至final1714.910403秒。测量Ready→CLOSE282.754306秒；本次AUTH→operator start36.495434秒、→managed BEGIN37.417573秒分别记账。全部25个UTC窗口独立重算通过，完整准备、审阅、修正和等待未减。Main setup2.1288985秒、warm含POST0.4749542秒、measured含POST0.3368219秒、到cleanup2.9752449秒均只子窗。final前的三根metadata2442426B<4MiB，未当连续内存峰值；tmp-prod/tmp-measure各一空目录、regular files/bytes为0，原资源无fixture复制，不授process-wide JNI为0。到发表的成本另后到记录。

Source两步caption修正、Code checker遗漏精确CallerFQN映射、一次PowerShell quoting、display诊断误把InvokeDynamic符号当字符串，以及Native所有准备/reader/forecast修正均按原件和实际成本保留；没有因此改变业务源、类、raw、门限或样本。Models六审仅静态辅助；三处文字更正为Top+21nested、16warmrows与32measuredrows、资源物理setup/final与内存每行，不给模型修复实现信用。更早真实begin UNKNOWN，原件不轮换，发表全窗口成本后到另记。

主要原件（J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-battle-composition-measure225，Q=D:/ck3-state/resume91-native-integration/p225-battle-composition-measure-test01）：

- J/source03-owner/SOURCE-READY01.json6971B/cf701e2f…，Main46213B/630a6c47…、Caller524B/4d3f4f37…；J/ACTUAL6-60-CLOSED24-ORIGINAL24-GOLDEN-CODE-OWNER01.json43560B/01f6353c…保完整60inventory和有限变化义务。
- Q/reports-component/battle-composition-measure225-report.json121872B/0937273f…、finish715B/196b56db…；actual/measure/ACTUAL.json1783B/ff3c0c19…、CLOSE240B/c68a0fd0…。
- J/owner-review01/ACTUAL-ALL48-EXACT-PAIRS-INPUT47FILES-ORIGINALFULL24-OWNER01.json18336B/fbb58490…；Root独立12543B/128440b0…，各自全48原始端点/Fraction复算，不执行Native helper或相信derived字段代替验收。
- Q/FINAL-P225-ORIGINAL24-PUBLICCOMPOSITION-ALL2COST01.json26367B/40e57869…；J/owner-review01/FINAL-ALLREFS-TWOACTUALS-WINDOWS-CONSISTENCY01.json2557B/b0e3dc07…保fresh40唯一引用、两actual/CLOSE及全部25窗口。成本reader首轮误把省略phase的operator_start当独立key，0VM修正lookup后通过，原错误/耗时保；快讯曾误写24窗口而原proof已列全25，正文据真实keys更正、不重写原件。

本次正常exact3仅新事实单元、daily11-11和W46；生产Java、Test/资源、benchmark源、tools、CI、pom、AGENTS及source307均不改。不采用测试Main为生产基线，不授Game/Runtime/P100-Sway诊断或额外GET/保存；不以组件TTT恢复同链准入。新增确认保存0，秒/新增保存日无有效数字，10秒/保存日目标未由本单元通过，主任务继续。
