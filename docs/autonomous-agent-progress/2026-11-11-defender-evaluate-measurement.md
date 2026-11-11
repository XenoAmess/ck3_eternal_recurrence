# P223：原case0完整Defender evaluate的固定组件测量

本单元比较A历史OFFLINE378的完整DefenderContinueRisk17类与B=P222五次同序add后的完整17类，两侧各自同loader拥有同字节Codec1和同一个测试Caller，共19名/侧。目标是公开 `DefenderContinueRiskCodec.evaluate(raw)` 的整个decode→observe→encode，返回自然byte[]并存入Object[64]；没有把目标缩成五次add，也没有在kernel增加POST、私有反射、黑洞或人工carrier逃逸。实际Caller5/12/9B直接调用；真实API不声明checked异常，故没有不必要异常包装。

输入固定为原producer-golden-v1.json的第0项r0271-contact：完整frame/contact、1个offsite arrival、0个conflict、siege为null，原expected15字段/7个排序blocker，不添加或裁剪观测。原资源38052B/SHA3efece10495c0cd208d27f251056593aabf047f259844e265cbed8efc3323656直接读取；setup按原Test35/42用共享StrictJson解析资源，再将完整request.toString()转UTF8一次。双方使用同一个Object[1]和同一raw引用，完整backup、每行前后及final的身份/全bytes校验通过。原Java wire实测 921B/SHAb405d7c8e1f62f8e14b15b017ffaced3bd628341713fca9ea413fe1c93321816；没有以Python预测或其它历史wire冒充。

每个结果均在计量区间外由共享parent StrictJson.parse、原完整expected JsonNode相等及原assertReadOnly210–219整方法验证，共2304次parse、golden和read-only检查。保留read_only=true、material_comparison_ready=false、原五个null结果字段，以及siege/contact的非授权标志；对象比较保字段集合/值和数组顺序，不新增object wire-order或稳定编码golden。没有NEW首A基线替代golden，也没有setup/POST的额外evaluate、Codec.decode、observe或encode。P222原全25例的软件资格独立保留，本次未重跑原Test。

严格loader各自拥有Risk Top+16nested、Codec和Caller；B17根在共同旧Codec根之前，包私normalizeConflictJson与记录类型保持同一child runtime package，不在parent转换Risk DTO。实际38个child命名来源、单列parent StrictJson共39个角色/37个physical文件；文件SHA/CodeSource/loader和前后约束通过，不冒称总JVM/hidden类数或OS-held defineClass bytes。父尾冻结历史378条，compact UTF8列表SHAc7771bb10ba8ff0c448cccc8f2fd3c5dfc93f9224b8253d774d77ee36ce85214；新harness+378的runtime379仅是条目数，与随后实际选择的production OFFLINE379不同，不切换尾表或加入资源前缀。parent JSON/JDK在setup被使用、两个child初始化自然落在各自首次target，均计成本，不宣称完全冷或稳定JIT。

唯一固定Main实际exit0、契约接收、CLOSE fenced/released：4ABBA warm共16行×16次，8ABBA measured共32行×64次，总48行2304次；每侧measured1024次，retain64，配对每侧2×64所以signed(B1+B2−A1−A2)除128。全部端点、差额、完成/完整POST次数、38命名来源、input/resource、三份supported/already-enabled Counter状态、两个loader关闭及finish报告SHA由独立Fraction重算通过。计数器不主动启用，无fallback；原门槛中improved_cycles严格w<0，false/MIXED也是合法数据，不补样本或调N。

| 指标 | A均值 | B均值 | 均值变化 | A中位 | B中位 | 中位变化 |
|---|---:|---:|---:|---:|---:|---:|
| target wall，ns/次 | 171484.667969 | 100905.273438 | -41.157845% | 130950.781250 | 29095.312500 | -77.781490% |
| target allocation，B/次 | 39064.812500 | 38938.906250 | -0.322301% | 38688.312500 | 38580.562500 | -0.278508% |
| row enclosing，ns/次 | 193135.644531 | 124167.187500 | -35.709854% | 171558.593750 | 44060.156250 | -74.317721% |
| POST+clear，ns/次 | 21083.007812 | 22627.148438 | +7.324100% | 13006.250000 | 9107.812500 | -29.973570% |

冻结的allocation、latency和两者合取三门均true，只支持本原case0完整软件组件。八组allocation全负，target七好一反；target配对中位−93987.5ns与两侧中位差−101855.46875ns是不同统计量。outer七好一反；POST四好四反，虽然POST中位下降29.973570%，均值反向增加7.324100%，不能漏报。目标中位大降与分配仅约0.28%变化不构成五add机制、JIT、类常驻或GC的因果分解，也不替代自然规模/权重或置信度分析。

全部冷值、反向和离群保留：warm A0 target69.0102ms/outer95.518ms，warm B6 target66.322ms；measured B18 target31.2345ms、A23 target30.8709ms、A20 target29.8925ms均未剔除。目标每次min/max为A14843.75/482982.8125ns、B14571.875/488039.0625ns，完整五指标的warm/measured min/max另件同raw补算。CPU measured29/32为0（A15、B14），warm14/16为0，正值按15.625ms等粗粒度量化；比例为null，不因均值变化宣称CPU因果提速。shared whole-JVM heap/GC前后值不是每侧live/连续峰值。

仅两个软件JVM：新2TU6/58程序harness编译及唯一Main测量，没有生产/旧Test重编、额外样本或profile。actor合8.326825500000268秒嵌在operator合9.936224200064316秒内，二者不可相加或代替整轮。Plan04:36:27.329725Z→末CLOSE05:07:36.633334Z为1869.303609秒，至final05:12:17.960872Z为2150.631147秒；SourceReady→CLOSE958.444116秒/至final1239.771654秒，measureReady→CLOSE129.301817秒，当前MAX1→BEGIN21.62198秒。更早真实begin UNKNOWN，全部source/API校准、模型辅助审阅、准备、编译、Code审阅、失败修正和等待保留，到发表成本后到另记。Main setup2.2185343秒、warm含POST0.3722914秒、measured含POST0.325045秒等只为子窗。

原件/错误不改写：Caller01把条件checked前提误当事实，直接Git及实际Exceptions核验后在任何Java前移除，不算模型发现或编译失败；generator方法声明regex预write拒收、owner Caller精确FQCN映射遗漏、reader-preparer宽token误撞显式zeroextra标签，均只修本岗工具，原错与未知process耗时保留。Native Python括号、精确LDC宽度和完整BSM对照错误也保留；没有为绿色更改被测源、类、raw、门槛或次数。四个模型完整源审仅辅助，0模型代码采用，不作运行准入。final写后三根1345538B<4MiB；tmp-prod/tmp-measure各保留一个空目录、regular files/bytes为0，原资源未复制，不授连续内存峰值或process-wide JNI为0。

主要原件（J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-defender-evaluate-measure223，Q=D:/ck3-state/resume91-native-integration/p223-defender-evaluate-measure-test01）：

- J/source02-owner/SOURCE-READY01.json：6907B/1575e3eb…，完整Main43758B/e772548c…及Caller460B/bb59c845…；J/owner-review01/ACTUAL6-58-THIN-BSM-READONLY-WIDTH-OWNER01.json：5128B/c01d3ceb…，43成熟完整程序和两精确binding变化的分组与Native41口径分列，BSM14→12仅原索引7/8删除，原readOnly47指令的两个LDC宽度单列。
- Q/reports-component/defender-evaluate-measure223-report.json：95327B/7caca5b1…；finish710B/cdeaff2a…；actual/measure/ACTUAL.json1743B/8d5456e9…及CLOSE240B/61870d9e…。
- J/owner-review01/ACTUAL-ALL48-EXACT-PAIRS-INPUT37FILES-ORIGINALFULLPOST-OWNER01.json：16545B/82d3180d…；同raw minmax/逆向补件8318B/64bd8a41…；Root独立Fraction件10178B/a12e258b…，各自独算不以Native helper或derived字段冒证据。
- Q/FINAL-P223-FULLPUBLIC-ORIGINAL15-ALL2COST01.json：24649B/99c99753…；J/owner-review01/FINAL-ALLREFS-TWOACTUALS-WINDOWS-FRACTION-CONSISTENCY01.json：1630B/640b495f…，fresh40唯一pin、两actual/CLOSE、19完整UTC窗口与四指标全均值/中位/八配对相符。

本次正常exact3只追加本单元、daily11-11和W46，生产Java、Test、资源、benchmark源、tools、CI、pom、AGENTS及运行source307均不改。既有production OFFLINE379不因测试Main被采用或回滚；不授Game/Runtime/P100-Sway诊断、额外GET或保存。新增确认保存0，秒/新增保存日无有效数字，不能把微秒组件结果当作整局提速或10秒/保存日达标，主目标继续。
