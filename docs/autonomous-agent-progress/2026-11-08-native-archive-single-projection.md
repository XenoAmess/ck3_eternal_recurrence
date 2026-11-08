# 归档 Driver 帧消除同调用第二次完整投影（P134）

Root 采用本次改动为软件组件的 allocation 优化。固定四行中，两次 B 的当前线程分配均低于两次 A；CPU 与 wall 均值只作本次小样本描述，不授稳定 CPU 或延迟通过。模型 NONE，owner-original，0 HTTP。

`DriverFrameEvidenceLoader.load` 原来先经 `loadFull` 读取原件并完成完整投影，随后 `assembler.assemble` 再对同一次调用的数据完整投影。候选保留原件读取前缀，让 Reader 从字节自行严格解码，Assembler 内部生成一次投影后进入唯一身份校验尾段。没有接收公有 `FullSnapshot`、任意 raw/facts 配对、callback 或可信标志，也没有全局或跨调用缓存。

manifest → Native → Driver 的实际读取、精确长度与 SHA 校验、Native 包边界及防御克隆顺序保留。首次投影错误仍在原 catch 外直接抛出，较晚的身份和 `Complete` 构造错误仍进入原 `Incomplete` 层。原 `loadFull` 和 Reader 原公开入口、两段完整投影算法以及 profile4 `Complete` 构造器的独立重播均保留。消除重复投影自然也少做其中重复的纯 state SHA 与 binding 摘要；所有 fresh custody 和首投影校验保留，hash/codec/Guard 算法未修改，不声称所有 hash 调用次数不变。

三生产 TU 首次编译0，完整输出11类。当前有效旧家族是 Loader1、Reader1、Assembler6，共8类；候选为 Loader2、Reader3、Assembler6。源码本次新增 Loader 私有 `OriginalBytes` 一类，另外两个 Reader 内部类型原已存在于发表源码中，但首次进入这组实际输出，不能借旧 Reader1 证明其可见性或历史装载。实际核验含完整 SourceFile、major65、双向 nests 和私有构造器；不授新增类型、布局或 Runtime 热载。

必要三测试 TU 首次编译0、7类：修改的旧310测试3类、原 Assembler 测试1类、必要原 StateAssembler 支持源码3类。后两份源码与 Git 原件逐字一致；支持源码所有 `@Test` 都不运行。六个不同方法在三个 JUnit JVM 全部通过（2 new、4 affected），不是旧整套重跑：

- 功能四方法：旧310两项、原 Assembler framing/mismatch 一项，以及新增 `paused` 字符串直接投影错误／较晚 actor 身份错误对照一项。
- 真正归档集成：复用 compiled15 完整10类家族的 public Applied 方法一项，case142.188秒、suite142.238秒。其软件执行窗210/240秒，原业务120秒期限不改、不刷新；不借 compiled16 或当前同名源码的旧通过。
- 独立组件方法一项：suite3.387秒、case3.342秒，保留四行和所有输出断言。

组件使用原310纯原件 fixture，Native 包3,400,438 B、state3,400,339 B，含3,400,000个 ASCII opaque 字符；manifest985 B、Driver708 B。它通过内存 archive 回调运行生产解码入口，不是物理 IO 或 Game。A 是同一候选二进制的旧源码链 `loadFull → assemble → requireComplete`，B 是新 `load`；不是旧8类与新11类二进制 AB。固定 A/B/B/A，无额外预热，每个入口仅两个样本。每行均保 manifest→Native→Driver 三次回调和 SHA 顺序、完整 semantic/binding/identity、独立 `1.00` token 和 opaque 长度，四行输入散列不变。只有 global completed、全部 post checks 与 JUnit P 同时成立才计为合格。

| 行 | 入口 | wall ms | 当前线程 CPU ms | 当前线程 allocation B |
| --- | --- | ---: | ---: | ---: |
| 0 | A | 295.9346 | 109.375 | 197,368,456 |
| 1 | B | 109.4031 | 31.25 | 125,528,584 |
| 2 | B | 56.0658 | 62.5 | 125,526,488 |
| 3 | A | 95.9664 | 46.875 | 193,372,000 |

均值 allocation195,370,228→125,527,536 B（减少69,842,692 B，−35.7489%）。当前线程 CPU均值78.125→46.875 ms（−40%）、wall均值195.9505→82.73445 ms（−57.7779%）仅是本次两样本描述：A首末295.9346→95.9664明显漂移，B0 wall慢于A1，B1 CPU又高于A1，不能宣称稳定 CPU、稳健延迟、真实归档 IO、whole outcome 或实际智能体提速。CPU和 allocation 查询包住wall区间，量化和查询成本不扣除；B1 CPU62.5 ms高于其wall56.0658 ms的原值保留，不强行修正或把两种区间等同。

| 必要阶段 | recording actor 秒 | outer 秒 |
| --- | ---: | ---: |
| 生产3TU首次编译 | 8.2518828 | 9.3126815 |
| 测试3TU首次编译 | 8.2702309 | 9.3000818 |
| 功能4方法 | 6.4498866 | 7.5502605 |
| public Applied15 | 145.1197926 | 146.0981632 |
| 组件方法 | 5.8661855 | 6.9414358 |

recording actor 含父 recorder 校验等成本，不能写为完整 child JVM wall；outer 独立分列，不与子区间相加。组件 setup2.2081563秒，开始至报告输出前2.8460272秒，均另保原字段。首生产 BEGIN08:08:49.611590Z至末 close08:28:55.425818Z共1205.814228秒，含测试准备、首次编译、三个完整 JVM 和等待；更早 D 源码准备另保原件，不用抽样均值替换总成本。无额外 JVM 挑绿、Main03/JFR/PREP 或现场操作。

所有实际阶段0退出、无timeout、contract accepted，close均已释放。BEGIN 的资源 scope 沿用旧 p115 别名，真实配置、selector、源码与输出为 P134，原标签保留，不为标签重跑。组件 stderr299 B为本机编码的 JUnit `CleanupMode.NEVER` 保目录信息；owner首次按UTF-8显示产生只读解码错误，随后按gb18030读取，原件未改，0 Java 重试。没有将这类元数据读取问题记为模型或 Java 测试失败。

源码可核对 [Loader](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/effects/DriverFrameEvidenceLoader.java)、[Reader](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/driver/DriverObservationEvidenceReader.java)、[Assembler](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/driver/DriverObservationAssembler.java) 和 [310 测试](../../java/ck3-control/application/src/test/java/org/xar/ck3/control/application/driver/DriverFrameJoin310Test.java)。SourceReady、三叶逆向证明和正式 Test Ready 位于 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-native-replay134`；各阶段 ACTUAL/CLOSE/XML 与原四行报告位于 Native 的 `p134-native-replay-prod01`、`p134-native-replay-test01`，原 report5278 B，SHA `8a2a7b078bcdfcf160a16aebfe82f5fe9fa2f3da1310aa7c8ad47749addc8316`。

Native 完整资格 `QUALIFIED-P134-FUNCTIONAL-AND-MEMORY-COMPONENT01.json` 为76199 B／`477410ee1daa4c9d2522dc7206d3f7376ba1973f86df6d40b45662eb323da8c8`。Root 独立核实际六方法／来源／四行的报告为37879 B／`345241e30b4990ab9b61be9b6ca7d3d8b5e4c8fe60ae3a89199f36b6ec2f415c`，最终 `P134-ALLOCATION-ONLY-SOFTWARE-ADOPTION01.json` 为4771 B／`1ce78b48edbb896b11709a5e96fd47104e20752e3075ee3eb07413ebed216981`；owner 四行复核为8605 B／`4ba0b2463a6774639bebe3116aba0e0b33cff4fd1ff59f227e0c45ae298c4603`。正常发表回执另钉精确源与文档 blob，不回填原资格或 P133 结论。

本次仅软件 allocation 采用。P100 拒绝链、原账本、UNKNOWN、deadline 与 Runtime 唯一 owner 保持，不授新类型热载、head47、SAVE、10秒目标或实际游玩性能。
