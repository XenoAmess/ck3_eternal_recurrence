# P121：同一JVM固定三次Main的独立诊断

只运行一次当前B18的持续JVM软件DATA诊断，没有A/B比较，也不替换P120原四进程ABBA。新增test目录wrapper直接调用原Main03三次；原Main、SDK、Lifecycle、源码与物理input／Q2／source／绝对CAS／EXPECTED均未改。三次共18call（原6warm＋12measure）全部marker、warm CAS、cache和11phase wall／CPU／allocation之和通过，三张新software allocation card各异；冷首pass和全部setup完整保留。后两pass的measured均值约0.535／0.543秒只是这组后继调用观察，不是实际worker或新提速结论。

## 包装器范围与一次实际执行

ConstructionContinuingData121Main采用与实际编测相同的10990B／a825b94ec1c48451e53cbd32bc8e57978434d1f3a9d799687352cb5a7fd515ff源码。它固定3passes，无可选warmup／重试／pass筛选，所有调用使用原Main的B0 cache-lane标签，不是假造新的ABBA。输出目录必须新建且独占、在input根外，三个pass原report与CREATE_NEW summary不覆盖既有文件。首个Throwable即停止；原始错误保留，后续aux或summary错误仅suppressed到首错。各次Main正常退出后原Environment.close释放实际software guard scope，下一次才重新创建同锁的新card；没有绕过Guard或伪造资源许可。

草稿01的Main throws声明先由Root静读发现不匹配：原Main.main实际throws Throwable，owner在任何javac前修正wrapper的throws／catch与首错保存，并明确11phase／3card；原草稿留存，不算真实compilerRED。最终仅必要wrapper1TU一次0／1class／actor5.1934034秒；Root明确有限授权后只启动一个workload JVM，CPU1／Xmx384MiB／90秒、outer120秒、小元数据4MiB。原Main／SDK／App／旧Test没有重编，无新PREP、HTTP、JFR、P119 flags或collector／JIT参数调整。wrapper源注释中的DRAFT为编测前阶段标签，原字节保留；当时D-only执行许可与后来正式test源码采用分别记录，不把原qualification的尚未formal事实回写。

wrapper只读原EXPECTED及各小report并复核18call；编译MXBean及GC MXBean前后值只是同进程辅助元数据。没有thread CPU名称采样、栈profile或新增Native查询。输入／head／anchor／lock／payload／commit等原11文件物理身份不变；旧26卡不改、新3卡分列，不能称整个目录逐byte相同。common first-origin快照包含原共同类，wrapper自己的class在独立CP0／OUTPUTS证明，不误称common快照包含它。

## 全部三pass与冷启动

| 观测 | pass0 | pass1 | pass2 |
| --- | ---: | ---: | ---: |
| 原Main完整调用wall | 9.6915655s | 3.7422275s | 3.6328295s |
| 原Main setup | 2.1324233s | 0.2783664s | 0.2483553s |
| 原Main序列化前完整main | 9.4129631s | 3.7195841s | 3.629912s |
| 该pass全部6call wall总和 | 7.139978s | 3.4321753s | 3.3697825s |
| 原4measure whole均值 | 699.262025ms | 534.739125ms | 542.783075ms |
| 原4measure whole中位数 | 728.20025ms | 542.19675ms | 537.44535ms |
| 原4measure main-thread allocated均值 | 711315580B | 711326630B | 711331414B |
| CompilationMX近似累计elapsed增量 | 4254ms | 531ms | 251ms |
| Copy／Full GC次数增量 | 42／5 | 40／6 | 42／6 |
| GC bean近似elapsed增量 | 1702ms | 1358ms | 1507ms |

后pass的setup与编译MX增量较低，仍每call约0.54秒且主线程累计分配约711MB；这支持继续查实际重复成本，不能把后pass当作新A/B结果或证明某个方法／GC的唯一因果。CompilationMX elapsed不是compiler CPU；GC bean count／time是近似累计计数，不是P119 stdout那种逐暂停精确时间，不能与编译MX、Main wall或进程CPU相加。辅助getter和report复核本身也在完整wrapper／process窗口中，没有假装零成本。

全部18call当前线程wall累计13.9419358秒、CPU5.46875秒、allocated12824309424B；allocated是累计字节，不是heap或resident峰。进程累计CPU18.15625秒（kernel3.34375＋user14.8125）另列，二者差额还包含setup、类初始化、其它JVM线程及wrapper工作，不能全归GC／JIT。owned OS峰working set480440320B／pagefile500322304B均不是heap实占。

## 分开的完整窗口与证据

三次Main完整调用合17.0666225秒；wrapper在summary输出前18.9841203秒；actor20.3208997秒；outer21.3498631秒。workload operator BEGIN03:00:55.303355Z至MANAGED-CLOSE03:01:16.585936Z为21.282581秒，close明确terminal／reservation=false；outer还包含控制器尾部。首必要compile BEGIN03:00:03.862231Z至该close为72.723705秒；从具名zero-JVM准备02:52:49.719749Z至close为506.866187秒，含源码静读修正、准备、编译、等待与执行，不把这个具名起点冒充更早研究开始，也不把后到文档耗时塞进call分母。

所有18call及三个完整raw报告、异常通道、setup／main／actor／outer／OS峰均保留，实际未触发fail-stop，不为更快数字追加运行。P120 primary结果保持；本单没有Policy.evaluate／Native fresh READ／SEM／owning publication／实际worker／Runtime或确认保存日资格，10秒目标仍未通过。

Native根D:/ck3-state/resume91-native-integration/p121-continuing-data01：
QUALIFIED-P121-CONTINUING-DIAGNOSTIC01.json33035B／f5f5e13fab77f95b5b1e06d2bcdfab5ec43b117d6fa23a433efc740b30dff311；
ALL-P121-CONTINUING-18-CALLS01.json94588B／29fbf12e37bea86a1a19452157ae5fc77be229781e35976b717db557bcdd28b5；
fixed identity／3cards6099B／8b641b9c242f77e34e26c070d5e8f858c0bdf74251d2fe4bbb544b4599cd8b18。
WRAPPER.json5180B／1edcd207a6c0f0bfcf35fd4985c6eecd52a83ecad9695b5af2895dd38dd4da94，
pass0／1／2原报告分别16810／16772／16741B，SHA837f6475…、a76f0dd0…、0891b63a…，完整SHA保存在wrapper和qualification中。

Root逐件18call复核proof75794B／6285f125173324a14f2a9c1a8da3e39feb16241ab10477f1c914241b581b5064，aux／OS proof2974B／3e2eab75771752abf5aef937af5fc0d89d35b939823344315403955fd0cbee84，最终qual43pins独核375B／071e93f9c26418b65e7856596312138d236757f4b3d2d50fee7663d8513f76a7另存。源根construction-continuing-data120/wrapper-draft02，原D source与正式test源码逐byte一致；不为正式采用重新编跑已绿。下一P122只研究／验证精确比较时省一次原query clone，继续保encode、memcmp、fallback与全部cold原件核验，不据本次后pass预授收益。
