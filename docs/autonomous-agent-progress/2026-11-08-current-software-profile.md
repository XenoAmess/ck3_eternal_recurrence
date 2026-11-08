# P148：当前软件完整 publicApplied 的有界采样

本次唯一离线 publicApplied 与一次流式解码均实际成功退出、释放资源；原 JFR 读至 EOF，元数据预算通过。它提供当前软件的有限调用前缀线索，不是性能 A/B、完整调用图或自动游玩验收。录制发生于上海本地 2026-11-08，后续只读归因在 11-09 继续，按事件日归档。

实际输入为 P147 已采用的软件 classpath350，加 compiled15 原完整10类的 `ConstructionFullProduction113Test#fullFuturePlanRunsActualIntentEffectColdVerifierAndFullMaterialPublication`。唯一 JUnit 1P，Jupiter 138.576秒。没有重新编译业务生产、Test、Main 或 SDK；复用 P136 decoder，以 source-file mode 在同一个 utility JVM 内编译1TU／14声明类型并解码，没有另发 javac、JFR CLI、重录或补跑。

原 JFR 9,608,599B，compact report 1,133,702B，实际 EOF 30,260事件，原件 hash／可用属性前后稳定。fileKey 不可用时身份仍为 UNKNOWN，不把内容稳定说成已持有物理身份。Root 独核139个原件引用、chunk header、两个 ACTUAL／CLOSE、XML 与预算；Native tail在summary前1,333,893B，加5,758B summary仍低于4MiB。观察器是软采样，尾部复读不是连续瞬时峰值证明，也没有移动或删除原件以满足预算。

## 采样能支持的范围

DataLoss事件0不等于全采样。原始 recorded stack limit64：Execution 1,127、Native 4,898、allocation 11,518条栈截断；allocation另58条原缺栈，statistical weight46,744。GC细节容量遗漏966条，它不是样本丢失；4类 JUnit 自定义事件也保留，没有声称只有9类事件。compact表示没有链容量丢弃，仍不能恢复原本缺失或截断的尾部。样本次数不是 CPU 秒，allocation statistical weight不是逐调用实际分配字节，重叠 GC／Compilation duration不能相加归因 CPU。

仅从原 report 字典展开少数 emitted recorded chains，未另写完整大栈文件。Execution leaf 中 `_decodeEscaped`194、`_writeStringSegments`77、`ensureCapacityInternal`65、`NativeWire.unicode`53、`RawJson.validate`27只是采样观察；以下每个选中链都只有2个截断样本，不能把整体 leaf 次数归给某一调用点。

- chain8423定位 Reader `capturedNativeFrame:290` 的首包解析；chain8425定位 Assembler `originalNativeStateWithNativePacket:302` 的后继 state 解析。当前已有包内标准不可变树，但私有 state 路径恒解析；已有公共路径则使用 compact veto、完整逐字编码比较和原 parse／equals 回退。下一 P149 仅审机械共享该校验尾段，所有包头、fresh原件、hash、错误边界与清理保持；净 CPU 仍需独立验证。
- chain5078定位 Collector `envelope:308` → `ObservedRequest.fromFullMaterial:111`。该完整文档已经加入后到 cash、frame 与 financing 数据，不能用先前 query-only NativeQuote 授权跳过完整解析。小 SDK 投影复用不等于消除完整外层解析，当前无窄闭合 API，本轮保留。
- Planning 独立证实 material `fullInput`→`preserve` 的重复 encode／验证，但无现成私有验证桥；不能靠 Obj 身份跳过第二次编码、改变 custom BigInteger／异常语义或换名复活 raw+typed 平台，本轮不实施。

源码谱系已核：Assembler 当前 Git／实际P147编译源逐字相等，Codec 当前 Git／P129编译源逐字相等；Collector 的 P113编译源到当前 Git 仅 CRLF→LF。当前 workload 的首来源分别是 P147 Assembler、P129 Codec、P113 Collector，未把旧 build307 的未知源码映射当证明。原算法体冻结，未修改 parser、writer、hash、Guard 或 oldencode。

## 完整费用与未证明部分

| 窗口 | workload | utility |
|---|---:|---:|
| parent recorder actor（含父验证） | 143.4598543s | 6.1170145s |
| phase outer operator | 144.4246224s | 6.8263344s |
| 同 OS birth 的 child lifetime | 142.9277268s | 5.7671533s |
| child process CPU | 94.703125s | 4.984375s |
| 独立观察线程 CPU | 15.375s | 0.671875s |
| 观察扫描 elapsed | 22.7883378s | 1.6444526s |
| 最大观察间隔 | 301.6867ms | 495.5894ms |

完整 controller operator151.679131秒；Java SourceReady→最后CLOSE547.823491秒，首准备原件15:38:28.481291Z→最后CLOSE548.077925秒。更早准备耗时 UNKNOWN，不记0。启动、录制、dump、source-mode编译、解码、父校验、观察、等待和后处理全部保留；这些重叠窗口不相加或相减成“纯序列化／GC”。完整父进程 CPU及未观察尾部峰值未知。不能拿旧 P141 约129秒与本次比较授提速。

P141历史 `PARTIAL_BUDGET_FAILURE` 原件保持，本单独立预算通过不修复或覆盖它。P147当前软件350不变，无生产／测试源码采用、Runtime／新类型热载／P100／head47／Game／SAVE信用，10秒／新增确认保存日目标未通过；后续性能主线继续。

原件：[Native最终资格](D:/ck3-state/resume91-native-integration/p148-current-applied-profile01/QUALIFIED-P148-CURRENT-SOFTWARE-PROFILE01.json)（61,464B，SHA256 `40e3d02daf432d02773858979feff276f76c13a68bda882c9c6739eade5175a3`）；[compact report](D:/ck3-state/resume91-native-integration/p148-current-applied-profile01/derived/decoder01/DECODER-REPORT.json)（1,133,702B，`82c7f1b3f6316d9651636da988c54cda9518fdcd7e3d922b418b5976218c1e3d`）；[Root独核](D:/ck3-state/resume91-root/post-vacation-20261107/P148-ACTUAL-RAW-EOF-BOUNDED-METADATA-AND-SAMPLE-COVERAGE-REVIEW01.json)（3,312B，`a61d5558cc4e31ef9e7031c8f3e293df36f7a5655f39bdc1f1ebdc88c8f9464f`）；[费用与尾部边界](D:/ck3-state/resume91-native-integration/p148-current-applied-profile01/P148-ACTUAL-COST-AND-FINAL-METADATA-TAIL-SUMMARY01.json)；[owner只读归因](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-current-profile148/java-readonly01/REPORT.json)（7,468B，`1c273e43e9ed3749da3cc3febaacfd1775851d68796325f770f504e8633dc12a`）；[Planning material归因](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-profile148/read-only-attribution01/REVIEW.json)。0新HTTP／模型案例。
