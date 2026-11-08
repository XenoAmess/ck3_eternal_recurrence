# P131：一次手动调用补齐离线 Main 的计时边界

本单采用为边界观测工具，不是生产性能候选或 Runtime 验收。新增 JDK-only 手动入口 `ConstructionMainClock131Main`，在 current P129 B、原 DATA02／EXPECTED 上仅调用未改的 Main03 一次，保留原 2 warmup＋4 measured 共六次调用。唯一诊断成功退出、原 marker 与资源合同通过；不比较本单与 P129 四 JVM 的速度，不回填 P129 当时没有采集的子进程时钟，也不改变 P129 的采用结论。

本单为 owner-original，0 模型 HTTP；没有模型采用或模型案例。正式改动仅手动测试入口和本单／日／周文档，原 Main、生产源码、SDK、生产配置和 Guard 未改。

## 入口、证据和执行范围

包装入口只使用 JDK 反射、时钟和 Files。目标以字符串 FQN 传给 `Class.forName(true)`，此前不引用或初始化目标 Main、Jackson、FullJsonTree 或 SDK。分别记录目标加载初始化、getMethod 和 main.invoke 的前后点；内部固定原四参 `run ROOT B0 MAIN_REPORT`，不增加循环、warmup、PREP、JFR、GC 或 JVM flag。包装入口不解析 Main JSON，Native 在退出后读取原报告。

两个输出路径须 absent、互异并在原 DATA 根外；包装报告 CREATE_NEW。异常路径 finally 尝试保留阶段点和完成 flags，InvocationTargetException 原 cause 透传；若报告写出失败，将它 suppressed 到原异常。报告写后的时钟放在独立固定 stdout 行，避免回写报告。字段 main_invocations 是 invoke 前 attempt 计数；本次成功还实际核验 invoke_completed 和原六次完整调用，不能只据计数授过。

正式／外置源码各 7457B，SHA-256 `fa90f81033633d7fb74ed5cec2d12b8d09899d1026669b6be8a8203e34d60cb0`。首次仅此 1TU／1class 编译成功，编译记录 actor 2.3516883 秒；随后复用同一 class。唯一诊断 workload 使用 CPU1、Xmx384MiB、90秒及 outer120秒双界，未发生 timeout。原 Main03 26020B／`6660ee3c3ecf375b620eaeb63b5355c1b8cb3763dbe8e9cffbeaa0111ddd1da0` 保持；生产／SDK／旧 Test／Main 零重编，JUnit、PREP、额外工作负载 JVM 均为0。

Native parent 的02／03／04原件保留：02→03修正 report／stdout JSON 非 object 时 AttributeError 逃出资格检查的缺口；03→04修正 after-close verifier 对空 ACTUAL 点集误判完整的问题，要求 ACTUAL22 必需点、CLOSE23与值／顺序一致。它们是源码审阅阶段的 D Python reader 修正及纯 AST／Python fixture 核验，0 Java 尝试、0 claim，不计 Java 编译失败、软件重跑或模型 RED。实际只运行最终04；原 durable gate、actor tick、原始 qualification 和 retained HANDLE 保持。

## 本次实际窗口

以下为不同边界的观测，不互相替代，也不把重叠窗口相加。

| 窗口 | 实际秒数 | 边界 |
| --- | ---: | --- |
| OS 子进程生命周期 | 12.6041511 | 同 retained HANDLE 查询的 creation→exit FILETIME |
| OS 子进程累计 CPU | 10.703125 | 同一查询 kernel＋user，包含全部 JVM 线程 |
| Class.forName(true) | 2.1607420 | 目标加载／链接／依赖初始化，不是单独 clinit CPU |
| getMethod | 0.0000158 | 反射方法查找 |
| main.invoke | 10.1272451 | 一次反射调用，含 Main 最终输出与返回 |
| 原 MainBeforeOutput | 9.8290879 | 原 Main 入口后至最终报告构造／写出前 |
| invoke 余段 | 0.2981572 | invoke−MainBefore，混合反射／报告编码／写盘／stdout／return等 |
| 包装 summary 准备 | 0.0316222 | 该诊断自身额外开销 |
| 包装 summary 写出 | 0.0005766 | 包含本次写出路径，不当作生产 IO |
| 完整记录 actor | 13.0912864 | 包含 Native 父记录与验证，不是纯 child wall |
| 完整 outer | 14.0960964 | 运行管理完整窗口 |

**Class.forName 的目标是离线数据 Main，不是实际自动游玩智能体的初始化热点。** MainBeforeOutput 排除目标静态初始化，也排除其最终报告编码、写盘、stdout 和 VM exit；invoke 余段不能称纯 serialization、GC 或 JIT。包装入口本身的类装入、前置检查、报告／stdout／异常传播、VM exit 也有独立或外部边界。OS lifetime 减 wrapper nano sample 约0.278051秒仅为跨时钟的混合未覆盖余量，不精确拆成启动或退出。

Native 采用 parent monotonic、child nanoTime、OS FILETIME 三个独立时钟域，JDK UTC sample 仅提供有采样括号的近似对照，不假定同步。Popen／CHILD_START archive 可以与子进程重叠，不能再加到子进程 wall。父端 BEGIN归档、等待、终态核对、日志fsync、post source／origin hash、shared snapshot、qualification、POST和release分别保留；ACTUAL22／CLOSE23点完整，不用“Main成功”替代收尾点资格。

## 六次调用完整保留

| 原 kind／index | wall秒 | 当前线程CPU秒 | 累计分配B |
| --- | ---: | ---: | ---: |
| warmup／0 | 3.1802289 | 0.718750 | 594776248 |
| warmup／1 | 1.2410197 | 0.250000 | 573690376 |
| measured／0 | 0.7371546 | 0.187500 | 573662960 |
| measured／1 | 0.6318141 | 0.265625 | 573648400 |
| measured／2 | 0.5925863 | 0.250000 | 573647024 |
| measured／3 | 0.5525927 | 0.250000 | 573659336 |

六次总 wall6.9353963秒／当前线程CPU1.921875秒／累计分配3463084344B；分配是累计计数，不能当 heap peak。每次原 EXPECTED、cache_api_used、warm-existing CAS、11个 phase wall／CPU／allocation sum均通过，两个 warmup 和所有慢点未过滤。原 Main setup2.7464577秒；MainBefore 减 setup及六次调用另有0.1472339秒混合余段。

OS process CPU与六次当前线程CPU相差8.78125秒，包含主线程目标初始化、setup、最终输出以及其他 JVM 线程。本次没有线程身份采样或编译／GC时间线，不能将该差全归 GC、JIT、IOwait 或某个生产方法。OS peak working set503791616B、pagefile501755904B也不是 Java heap peak。

## 原件、资源与采用边界

唯一诊断0退出／contract accepted，close于2026-11-08T06:42:06.348549Z，own_reservation_still_held=false。固定11件 identity／hash与原49张软件卡保持，本次原 Main正常新增1卡，共50张；这不是新 PREP 或修改既有授权。stdout363B、stderr0B；最终诊断 metadata760530B，小于独立4MiB预算。

首次 typing BEGIN 06:26:31.038131Z→诊断最后 close 的935.310418秒包括 reader 源码迭代、审阅、配置与等待，完整保留；不把这段或14秒outer改称生产调用速度。唯一诊断没有额外重复以取得更快数字。

具名原件：

- Java正式／外置 Ready：`construction-main-clock131/wrapper01/WRAPPER-SOURCE-READY01.json`，7703B／`ae0d64dbbaf05fd1cc02cd76fd4ceb37e93a1d3025fb5be5f400900d53e85e68`。
- Native：`D:/ck3-state/resume91-native-integration/p131-combined-boundary01/` 下 ACTUAL、MANAGED-CLOSE、原 Main报告、wrapper报告、stdout、OS HANDLE及完整 parent 点均保留。
- 最终资格：`QUALIFIED-P131-COMBINED-BOUNDARY-DIAGNOSTIC01.json`，39610B／`eadf091354fcb513f78dc3a35c434445451c3a596795ad3e50f81fe321246c99`。
- 有限解释：`SHORT-ACTUAL-INTERPRETATION01.json`，2508B／`5c242f4bf29c506459b22e8e2bb5534b655040c69256f1cee346888bd0049421`；Root独核 `P131-ACTUAL-SINGLE-DIAGNOSTIC-AND-CLOCK-REVIEW01.json`，2215B／`904898f5657b00c98b773225a3a43047d2fcad972f64c6c022f7f243b590f9e3`。

Root采用为“边界观测通过／手工诊断工具”。本单无 A/B 性能结论，不修改P129原24或补授其完整 child wall，不授持续worker、Source准入、Runtime／新类型热载、Game／Native／HTTP／SAVE／head47或10秒目标。后续生产性能工作仍需具体调用链与独立必要验证，不能把本单离线 Main 初始化直接外推实际 agent。
