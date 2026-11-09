# P182：current357 完整软件 case 与新 JFR 的有界事实

当前离线软件 actual current357 的唯一完整 APPLIED case 真实通过：1P、0F、0E、0skip，testcase **118.481s**，Jupiter engine **118.499s**。沿用已资格 P153 的 cached Test10 与原软件场景，不重编业务、Main、SDK 或旧 Test；工作负载 CP358 是 cached Test10 前置 current357。没有修改原业务120秒预算、命令 deadline、lazy reason、Guard 或输入，也没有额外热身、重复录制或为本记录新增测试。

本单元仅发表新 profile 和只读选点事实，不修改生产源码、Test、Tool、AGENTS、CI 或 pom。current357 保持；P179 正式源码发表及后到离线软件357采用分别已有具名回执。本次不授 Runtime／Game／P100／GET／热载／SAVE，零新增确认保存日不报有限秒／日。P173 current353 的115.144s与本次118.481s属于不同JVM、不同录制，不是受控A/B；不据先后时间宣称退化或提速，也不把各候选的百分比相加。

## 原件、EOF 与全部事件分区

新 raw **8340560B**，SHA `442632bf590a2c79bc473dbb7f2d0ddc8e9e81ff9ad56dada7159790d3fe1d0f`，保留于 `N/p182-current-integration-profile01/raw/current-integration182.jfr`。首阶段只证明实际0accepted、CLOSE和完整finished chunk header，header时长 **120.409137s** 不是case或actor时长，也不先授事件覆盖。随后唯一Tool02实际0accepted、CLOSE，完整读取EOF，解码前后raw字节数、SHA与属性稳定，原raw未改写。

独立 derived report **1138852B**，SHA `67f8b6501dd77fa6a74c2cce40a02ecd5e06dcba66a51912da325452a05534ed`。全部 **26253** 个事件、按类型／线程／状态／allocation class的计数和已知权重分区均核同；DataLoss事件为0，不能据此声称缺失为0。

| 原事件 | 完整本raw计数 | 已记录范围与缺口 |
| --- | ---: | --- |
| ExecutionSample | 752 | 747 recorded-truncated、5未截断；最大记录深度64 |
| NativeMethodSample | 4325 | 4322 recorded-truncated、3未截断 |
| ObjectAllocationSample | 19817 | 19764有栈；53缺栈，已知统计权重46416 |

Allocation统计权重总数 **50902076744**，严格分解为有栈 **50902030328** 加缺栈 **46416**。有栈中9733截断、10031未截断，容量导致的chain drop为0。权重表示抽样分配压力，不是精确已分配字节、某方法调用次数或耗时；缺栈使allocation retained-top不能宣称完整全局排行。完整事件读取也不能补回逻辑调用栈尾部。

GC及pause各485事件，detail容量合计970中保留64、其余906仅detail省略，不是丢失sample。GC、JUnit容器及其他duration可重叠，不求和作独占CPU。文件key unavailable／null，retained raw OS HANDLE identity proof为false；SHA稳定不能伪装成持有同一物理文件身份。FQName、JFR class ID与方法字典不等于运行时class字节SHA，也不授whole C0编源谱系。

## 设置与应用轴的限制

实际372条ActiveSetting均按原ID／名称解释。请求配置188项、元数据187类；缺失的五个请求名 `jdk.Duration`、`jdk.Instant`、`jdk.Text`、`jdk.Value`、`jdk.ZThreadDebug` 均为disabled占位项，如实保留，不伪造元数据。9个显式启用JDK事件的实际设置全部匹配：Execution10ms、Native20ms、allocation throttle300/s、GC及pause threshold0ms、Compilation100ms等原设置保持。另外有4个动态JUnit custom事件真实enabled：EngineDiscovery、LauncherDiscovery、TestExecution、TestPlanExecution；因此不能称总共仅9个启用事件。

应用轴明确 **PARTIAL**，按first-seen有界准入，非完整全局top。83个key占用 **48894／49152B** admission payload；8314个已识别贡献严格分解为 **5013 admitted + 3301 text-overflow**，所有5013 admitted均序列化，无额外section删行。实际section **38844B < 65536B**。key上限128未满不代表文本预算没满。

752个Execution中661含可识别选定namespace，91在记录前缀内没有该namespace；unknown-line **1317**、fixture-excluded4233、outside-namespace35371是可重叠的frame occurrence，不能相加作丢失sample或CPU秒。96条选定chain和关联字典仅是有界输出；inclusive业务caller不是self CPU、自然频率或其下所有分配的归因。该记录用于继续查具体源码，不解除旧Guard／parser／hash／oldencode／fresh identity与readback边界。

## 实际资源、准备错误与完整费用

Tool02使用已审源模式：**1TU、内部声明14类**，由该唯一utility JVM内部完成源码编译、初始化、raw读取、解码和输出；无持久compiled Tool cache、无单独javac、AppCP0，不能误报零编译成本。工作负载和Tool两phase均实际exit0accepted、timeoutfalse、CLOSE、fenced／released，资源槽归零；没有后继重解码、录制或业务编测。

Root AUTH01曾缺少所需bool，实际预启动被拒，**0VM、0.3066291s**工具成本及两条拒绝原件保留；AUTH02显式修正后的验证与等待也保留。它不是case失败或重采样。所有JFR启动、exit dump、observer、报告序列化、stdout、进程尾部、0VM接线错误、准备、审阅、资格与Git成本均保，不能用短actor窗口替代全任务。

| 实际phase | actor秒 | operator phase秒 | CLOSE UTC |
| --- | ---: | ---: | --- |
| cached完整软件case | 122.4322261 | 123.6682289 | 2026-11-09T09:33:26.085681Z |
| source-mode Tool02 | 5.9697524 | 6.6185178 | 2026-11-09T09:49:30.509666Z |

两actor合计 **128.4019785s**、两operator phase合计 **130.2867467s** 仅资源子窗。Native最早已持切点 **09:22:48.485650Z → 最后CLOSE 1602.024016s → qualification 1746.071s**；更早实际研究／准备起点 **UNKNOWN，不记0**。这些窗口与后继并行工作可能重叠，不盲目相加。

workload OS child lifetime121.8350254s，kernel CPU53.15625s、user27.984375s；observer自身CPU7.171875s、scan elapsed15.0702531s、max gap0.310984s。Tool OS lifetime5.6538124s，kernel CPU0.359375s、user4.078125s；observer CPU0.59375s、scan1.2150804s、max gap0.3916741s。observer扫描与phase墙钟重叠，不能另加成互斥墙钟；全parent准备前后CPU UNKNOWN，不据这些子窗报全任务CPU。OS内存或共享heap观察也不是Java heap peak或Runtime性能证明。

预算保留原raw12MiB、repository20MiB、derived8MiB、metadata4MiB、fixture CAS64MiB、mandatory reserve256KiB。实际raw8340560B、derived1138852B；最后逻辑快照metadata **1683106B** 在4MiB内。所有原tmp、JNA、内部class、日志、失败AUTH和qualification按原分类保留；软采样与最后静态快照不证明瞬时硬峰值，post-close parent metadata tail连续峰值UNKNOWN。

## 限定两叶的只读结论

第一叶 `IdentityBearingFileAttributes.readData` 当前formal267–286：返回 `new byte[expected]` 每call一次，Memory与IntByReference在循环外复用，循环只填返回数组；最后1B读取是独立size-drift检查。不存在可删的同调用重复临时数组，且属于fresh-read算法本体，**NO_CANDIDATE**。新allocation叶的693条／统计权重5108699328不代表693次调用、真实字节或可省成本。

第二叶 `DriverActionHistoryCodec` 当前formal30372B、SHA `62d3dfb99376f2b8f1dae7d99d9e1f07501eb2efb8fa035e52246dfdaa3f5c32`。`verifyEvidence` 275–282各case的fresh load及exact保持，未发现可删副本。邻接 `loadObject` 287→`load` 285虽有hash校验用raw.bytes()后再次raw.bytes()供parse的源码假设，但新emitted链7680／8120／8350只证明requireSource→verifyEvidence的Native-frame验证，未持该loadObject路径实际命中、结果大小或频率；hash后复用内容又与P179只复用length的前提不同。故**未选实施候选**，不借3.4M native输入给legacy结果授收益，不扩大第三叶、不造新fixture或测试。

## 原件入口

- `N/p182-current-integration-decode01/QUALIFIED-P182-CURRENT357-FULLCASE-RAW-EOF-AND-PARTIAL-AXIS01.json`：40587B／`66046838dffe067bb0765603840c2f45d831641e415facafc9bbe6724a084505`。
- 同根 `derived/decoder01/DECODER-REPORT.json`：1138852B／`67f8b6501dd77fa6a74c2cce40a02ecd5e06dcba66a51912da325452a05534ed`。
- `R/P182-ACTUAL-EOF-ALLPARTITIONS-SETTINGS-PARTIAL-CURRENT357-ANALYSIS01.json`：12236B／`9b0f9c7aae314934f798635fc4e22670007a4fdc9a2e237d5765a5fac16df7f1`。
- `R/P182-FINALQUAL-ALLREFERENCES-AND-COST-INDEPENDENT01.json`：1441B／`1f375be4039b32e2739b49fae845610204f32bc7defa8b26f9aae68c2ca48d9a`。该件独核final refs56次引用／48独立原件；此前workload资格链另记，不把两份unique直接相加。
- `J/construction-profile182/read-only-coverage01/REVIEW.json`：3213B／`266c1b7f6709e6b9f49e869ff6a0cc9e58cab9a00d8be7ee0c0f85f2776bf50c`。

N、R、J为本机隔离证据根。本单元仅原有软件case与新profile事实；旧PARK、UNKNOWN、拒绝主题及Runtime独占边界保持，后续具体可行性研究独立继续，不因文档发表停止主线。
