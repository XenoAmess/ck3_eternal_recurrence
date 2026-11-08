# P123：readback比较省clone候选未采用

本候选的软件行为通过，但整体墙钟结果反向，决定不采用。完整输入readback比较少一次6831978B原文数组clone，preserve阶段累计分配恰少6832000B；whole主线程累计分配均值704496019→697691649B（约-.966%）。同一固定ABBA的whole墙钟均值却762.6028→857.4797125ms（+12.44%）、中位766.5117→861.0573ms（+12.33%），actor均值也13.7594844→14.6883395秒。保留全部样本，不为约1%的分配收益保留这组墙钟负结果，也不宣称已经证明唯一因果。

## 候选范围及真实软件验证

仅ConstructionOriginalSource.preserve第二次Arrays.equals(full,reopened.bytes())改用既有RawJson.contentEquals(full)。第一scoped.loadFullMaterial及exact(reference,reopened.bytes())实际读回／长度／SHA校验完全保持且先执行，所有small分支、融资header、manifest／command预算、cold及物理Guard不改；无新API／类型／字段。Root还在实际ordered CP核过RawJson现有contentEquals方法，无需重编它。

真实单POST于03:17:56.406799Z开始，200／stop／DONE，3.5716317s、TTFT1.1805411s，6515prompt／358output、cached=null。三份完整当前Source／RawJson／meaningful custody Test原件26122B，task2620B。输出是完整valid JSON，但把单path／old／new放顶层，没有按任务放edits数组；owner只投影该原literal代码块，无代码改写／重HTTP。首提取器因预期edits而KeyError，在任何candidate写入或JVM前失败，原输出与错误保留，不能称整份schema原样合规或Java编译失败。

后到Root授权使该独立源码可与P122文档并行，旧DReady中的after-publication计划保留为历史，不回写。必要Source1TU／3class一次0，actor4.8839481s；唯一既有largeOwnedRawSurvivesCallerMutationAndColdConsumersStillRequireActualFullOriginal受影响方法1P，actor12.7500616s／close03:24:47.110269Z，0Test TU／newunique=0。该方法实际走同writer重复preserve、完整原文／caller变异、cold／坏原件／恢复等合同；没新增镜像Arrays suite、没重small。软件green与性能采用分别判断。

## 全部固定ABBA负结果

原Main03、当前P122的SDK／Lifecycle及其它CP、6831978B input／Q2／source／绝对CAS／EXPECTED均沿用；只Source3族A／B不同。logical A0／B0／B1／A1仍映射原raw B0／B0／B1／B1，无Main重编、PREP、DATA刷新、P119flags或P121后pass样本替代。四JVM各2warm＋4measure，CPU1／384MiB／90秒；全部8warm／16measure及24call保留，原marker／warm CAS／cache通过，whole等于11phase wall／CPU／allocated之和。固定物理文件／四新card分别核验，无过滤／forceGC／补跑挑绿。

| 指标 | 当前Source基线A | P123候选B |
| --- | ---: | ---: |
| whole墙钟均值 | 762.6028ms | 857.4797125ms |
| whole墙钟中位数 | 766.5117ms | 861.0573ms |
| whole当前线程CPU均值 | 320.3125ms | 302.734375ms |
| whole allocated均值 | 704496019B | 697691649B |
| preserve墙钟均值 | 97.2533625ms | 113.595025ms |
| preserve allocated均值 | 124026940B | 117194940B |
| actor均值 | 13.7594844s | 14.6883395s |
| setup均值 | 2.47998335s | 2.8507278s |
| 序列化前main均值 | 10.19414565s | 11.1839883s |

固定顺序whole均值A0 762.46405／B0 788.7744／B1 926.185025／A1 762.74155ms，两个A接近、两个B都慢；preserve对应95.744275／100.474725／126.715325／98.76245ms。没有删除B1或其它慢点。当前线程CPU／分配较少不等于wall／进程更快；保留JIT／GC／setup与未改phase成本，但这次没有新的方法栈或因果诊断，不把所有反向变化归给唯一comparison机制。

ABBA从03:25:37.646042Z至A1close03:26:40.782503Z，共63.136461秒含phase间隔；首实际生产BEGIN03:23:32.458436Z至末close188.324067秒，包含必要编测、准备、等待。此前模型／源审与后到文档另记，累计allocated不是heap／resident；所有warm、measured、setup／main／OS／actor／outer原件留存，不追加一次运行来挽救候选。

## 恢复与当前基线

候选从未提交进业务Git。原Source仅此一个未提交文件，按current-source01及现有HEAD原件逐byte恢复9567B／ab1083f2d2d4b3486e901758f423cade7ea331aeae98ad6ced5dbf53af26ff79；写前候选9559B／20c615083347c1bac7a2a31365ff2d739910cddc0fa57c650acf6910e5de4d91已核。未reset／amend／覆盖其它源或重跑；P122两源保持。当前后继基线回P122及旧Source3，P123 B编译产物／baseline仅保candidate-only，不作为已采用版本。正常发表只含本负结果、日记、周记三文档。

Native原qualification最初的allocation-only标签保持历史，后到Root明确not_adopted_after_negative_latency覆盖该采用取舍；旧observedfalse恢复观察也保留，后续新观测再核实际恢复。不改原模型、D候选、软件通过、24样本或qualification来洗成从未尝试。

证据根D:/ck3-state/resume91-native-integration/p123-consumer-execution01：
QUALIFIED-P123-READBACK-COMPARE-AND-CONSUMER-DATA01.json40055B／4d38576847646fbea3c356e6f6e43c8bcd22a767008aee5c2754ad1b323c5f47；
全raw394409B／2800e4c06cdafaa587ebe8724c296138b3b5742898be16fd2bf593e44f8c10b1；
identity6593B／c356eaab5674c9e4397721923168b959f14fec13d661a7ea26e3f98ce02b2e2d；
Root负采用决定3522B／7cdb6210f89548e93c3c06b5214a01e741da3185d08010c38a211505a3fd5444。
业务根construction-preserve-readback123的SOURCE-RESTORED01.json1288B／7bbb33926349b1e124eb6de43e39ff463647570bd4e0153279077da586fc6818，Native后到恢复实读1389B／346a7fd8f8e3af320099f6a017359e2fe144349f48af8afd4c8c7c53f311d5bc；Root24call独核proof112212B／1038a36cb67f599f468a7ccfc3ded15bf03deea2fff8e941a4698952d5df9964另存。

没有Runtime装载／Native动作／新确认保存日或目标通过。后继仍按真实量级与封闭所有权选择源码工作，不为重解析造泛化平台，也不机械追逐更好数字。
