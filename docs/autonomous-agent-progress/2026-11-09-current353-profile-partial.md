# P173：当前353完整软件case与新profile，应用轴仍部分覆盖

本次对实际已采用的离线软件 current353 运行一个新完整fixture，再由单独授权的唯一Tool02读其新原JFR至EOF。完整case与读取通过，不等于整体性能目标、Runtime、CK3／Native live、GET、P100、装载或新增SAVE通过；没有新业务源码。本单元只发表事实记录，不修改Source／Test／AGENTS／CI。历史P164 case121.336s不是受控A/B，不用新115.144s算稳健提速，也不合并P171／P172组件百分比。

## 实际来源、case与两个切点

workload classpath354为既有P153缓存Test10前置实际current353原序；current353包含已采用P171 Transport26、P172 Diagnostics10、P163 Collector38与全部旧尾项，原Main／SDK／Fixture等沿用，不重编。精确selector为ConstructionFullProduction113Test#fullFuturePlanRunsActualIntentEffectColdVerifierAndFullMaterialPublication；运行源是P153已编38984B／`815f2d214d823af324f1034f35ea286c9a98573b0c3c43d1dbbfcc195dec72f8`，不是从formal猜当前测试版本。原120秒业务deadline、material沿旧command.deadline、lazy bounded reason保持；本次1P没有触发失败reason，不补授P152原1F原因或修复。

实际JUnit **1P／0F／0E／0skip**，唯一testcase **115.144s**，Jupiter engine **115.162s**，actor118.8289445s／phase operator119.8148719s；实际exit0accepted、04:47:22.638377Z CLOSE／fenced释放。一次新workload，无额外plain／feasibility运行、暖机或重复录制，Xmx384m／1CPU／child210s／outer240s及原JFC、stackdepth64、disk／dumponexit、maxsize0／不设duration／maxage保留。

workload薄件的Tool0／事件EOF未知是其当时真实切点，原件不改写。随后Root另给单Tool授权，实际Tool exit0accepted、04:58:41.824179Z CLOSE。Tool为现有62429B／`e2cf412dc62721bb27283f8f5b254727de2ad9f4c881327e33fd0ca09fd3eb7a`源码模式，**1TU／14声明类型内部编译**、AppCP0，无持久compiled14 cache、无额外javac JVM，也没有业务／Main／SDK／旧Test编译。不能把source-mode写成完全0编译。Tool heap192m／1CPU／child30s／outer45s，无第二个Tool／重录／新source实现。

## Raw、EOF与物理身份局限

唯一新raw **8230827B**／`e3e2bd4f62ad5b4f7efc99f5b099e517197a857fca6eb1185649e55bb14bf625`。68-byte头为JFR2.1、一个finished chunk，chunk_size恰等文件长，duration116.8451314s，pool offset8230732／metadata offset164946／state字节[0,0,0,3]。这是文件头及完整extent事实，先前不冒事件EOF。

随后新report1066120B／`0b31db3f0a4491529b4235ffe6cec0d7f9f287af3461cc6ba6df3c86fd602204`实际completed／read_to_EOF／input_unchanged，全 **26677 events**。raw前后SHA与可得attributes相同，但filekey unavailable／comparison null、retained raw OS HANDLE proof false保留，不将哈希或路径稳定伪装成完整OS物理身份证明；JFR与OS跨clock对齐仍UNKNOWN。

## 所有事件与分区

| 类型 | 原events |
| --- | ---: |
| ExecutionSample | 687 |
| NativeMethodSample | 4110 |
| ObjectAllocationSample | 20515 |
| GarbageCollection／GCPhasePause | 各487 |
| Compilation／ActiveRecording／ActiveSetting | 8／1／372 |
| 四JUnit自定义类型 | 合10（3＋1＋5＋1） |

12个实际类型之和26677；7个thread组的events／statistical weight／重叠duration总数与原类型表核同。四JUnit类型为EngineDiscovery、LauncherDiscovery、TestExecution、TestPlanExecution，10个事件包含嵌套容器，不能称10个workload。

Execution687＝admitted687，全部recorded-truncated64；Native4110＝admitted4110，其中4106截断／4未截。Allocation **20515＝20470 admitted＋45原始missing stack**，admitted又为9963截断＋10507未截；统计weight **50846150480＝50846104072 admitted＋46408 missing**。三类capacity drop均0，但missing和原逻辑尾部并未因此消失。最大recorded frames64，method定义／axis容量overflow0、未知recorded method frames0、未知weight samples0，均限已记录前缀。

Allocation class118组的events与weight总数也核同；这是statistical pressure，不是精确分配字节或某method独占bytes。Execution／native样本数不是CPU秒或nativewall。叶保持原frame0，inclusive在单事件内按method去重但不同method贡献重叠，不能相加成互斥CPU。原sample state均RUNNABLE也不等于该区间全部在CPU执行。

内部admitted chain keys12194，只按每类top32输出共96条。原report的902个frame定义／777个旧method定义及各top引用闭合；应用轴另有61个needed method定义，不为它修改旧字典。不要展开、复制96条大栈或将top显示数当全部记录数。FQName、package选择或JFR method metadata本身不授整个C0编译源码来源。

GC／pause合974事件，保64详情、**910因详情容量省略**，不是sample loss；全487＋487计数与global duration保持，detail＋overflow的duration恒等式通过。GC类型各1.5989381s含相同暂停区间；Compilation8详情保全、sum0.9834298s。GC、JUnit容器等duration彼此重叠，不作OSCPU或独占worker墙钟相加。

## Settings、DataLoss与应用轴PARTIAL

372条ActiveSettings实际记录：9个显式JDK enabled设置与请求同，另4个JUnit类型运行时动态开启。Execution period10ms、Native20ms、alloc throttle300/s、GC／pause threshold0ms、Compilation100ms。请求188名、观测metadata187（报告内字段均保），五个禁用占位名 **jdk.Duration／jdk.Instant／jdk.Text／jdk.Value／jdk.ZThreadDebug** 没有metadata，如实保留，不能写全188均出现。没有其他额外enabled JDK类型。

ActiveRecording1条，历史名字P135SoftwareApplied而destination为本次P173raw，disk=true／maxSize0；maxAge与recordingDuration均原Long.MAX_VALUE，按原metadata单位保留，不重新解释为launch的具体age／duration。**DataLoss events0**、amount_sum0／已知amount事件0、total_maximum null，不表示无截断／完整逻辑采样或冷热前缀完全覆盖。

新应用轴仍 **PARTIAL**、first-seen有界入表：687＝0missing＋0empty＋627观察到eligible namespace＋60记录前缀无eligible；distinct contexts **7769＝4811 admitted＋2958 text overflow**。83keys未到128key上限（key overflow0），但conservative payload48913／49152B先满；入表贡献和4811与原rows相同、serialization省略0，实际83行、61必要method定义。ASCII section38912B＜65536B不代表入表前没有丢贡献。

所有687样本均原64截断；unknown line1216次、excluded fixture4048次、outside namespace32068次是重叠frame occurrence计数，不能加成丢失样本或伪distinct。2958是未入表贡献，不是2958个丢失CPU样本。unknown class／eligible method／existing methodID／BCI／context与read failure均0，仍不授完整untruncated调用图或global top。精选namespace／排除fixture名单只界定记录上下文，不自动证明production源码与实际callee谱系。

## 全成本、预算与保留

两个actor合 **125.1305194s**，两个phase operator合 **126.7843175s**，仅资源子窗。Native已知04:33:19.161899Z→最后CLOSE04:58:41.824179Z **1522.662280s**，至final qual **1709.000934s**；更早实际Root／研究起点UNKNOWN非0。workload先前843.476478s至其CLOSE／1009.837135s至thinqual、SourceReady至CLOSE458.889708s均保为较窄切点，不替整个单元。准备、审阅、等待、JFR启动／exit dump、source-mode内部编译、全raw读取、报告与结算不删。

Tool actor6.3015749s／operator6.9694456s；main-before-report2.4906265s不含premain源码编译、class init以及postmain materialize／serialize／write／exit，不能以2.49秒替完整工具费用。workload整个controller operator119.978174s也与phase119.8148719s分开。

workload retained-HANDLE OS lifetime118.2461559s、kernel CPU56.28125s／user29.375s，peak working set **563863552B**／pagefile **572563456B** 是进程生命周期OS事实，**不是Java heapPeak／machinePeak**。其observer自身CPU7.109375s／scan wall14.3026214s、maxgap403.144ms；Tool OS lifetime5.8573845s／kernel0.375s／user4s，observerCPU0.625s／scan1.0760947s／gap381.9485ms。扫描与子进程墙钟重叠，不另加成独立墙钟，也不据差值补造未知parent全CPU。

final raw8230827B＜12MiB、derived1066120B＜8MiB、metadata1625172B＜4MiB，repository20MiB／fixture CAS64MiB旧界不变。workload曾观察repo8206226B，JDK dump后repo为空；父未删／截／复制raw，不把临时chunk释放等同streamloss。100ms软观察、mandatory256KiB reserve、ID tops27295B＜32KiB、全部tmp／JNA／logs／工具编译成本保留；短瞬态与连续postclose尾部peak仍UNKNOWN，不称硬filesystem或总heap上限，不能把不同category各自峰值相加当同刻总峰值。

保留P173薄件Tool0历史切点、旧P152 FAILED utility0／P141 PARTIAL与所有PARK，不以新通过回填。owner仅0VM核验，读取摘要中BEGIN predecessor实际20件（Diag10＋cached10）已在02纠正原范围措辞；Transport26／Collector38由已采用353和精确CP链持有，不假称本次全family重hash。没有新增Source/Test、再decode、模型HTTP或现场操作。

## 具名原件

- `N/p173-current-integration-profile01/QUALIFIED-P173-ONE-WORKLOAD-RAW-HEADER-UTILITY0-THIN01.json`：74131B／`19b30b3a420fbfbde3d7344217cc0f3f7d529ec87cc61f558076582e808dd46f`。
- `N/p173-current-integration-decode01/QUALIFIED-P173-CURRENT353-FULLCASE-RAW-EOF-AND-PARTIAL-AXIS01.json`：39216B／`bc1f714a739e24c60ef2fc671f450d18d047fce7dd147fbc8c9e65986c62d36b`。Root实际55次引用／47独立原件；先前workload244次引用／230独立另件链接，**不相加为unique总数**。
- `R/P173-ACTUAL-EOF-ALLPARTITIONS-SETTINGS-PARTIAL-CURRENT353-ANALYSIS01.json`：31676B／`d526181eafea0c7f0625a5acec140748b924488dee3437ca317314aacc10f8da`。
- `J/construction-integration-profile173/OWNER-ONE-CASE-RAW-HEADER-REVIEW02.json`：7365B／`1d6bfe1370e52831c4a9dab5eddb0d5f098ac9bc87b948a41df8c264e6e2be5d`；`OWNER-EOF-PARTITIONS-SETTINGS-COST-REVIEW01.json`：9141B／`b76eee8faf5eecde1a9a6302c68010dcefa2b84bfc8ee907e54a22bfb5a560a1`。

N、R、J为本机具名证据根。软件current353不变，source通过／软件class图／实际Runtime／SAVE分别记账；零新增确认保存日，不报有限秒／日，不宣称10秒目标通过。后继两个caller只读研究独立，不能借本次事件表放宽fresh Guard／hash／parser或复活已拒平台。
