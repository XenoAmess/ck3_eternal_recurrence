# REA 与 CK3 原生机制研究

这里维护 REA 框架的深入研究、CK3 使用方法、真实实验和适用边界。2026-10-26 用户要求后续机制研究使用 REA 或同类方法论开展，并实时更新本目录。自动游玩、G2 八 M 与实机准备继续并行。

## 入口

| 文件 | 内容 | 维护负责人 |
| --- | --- | --- |
| [methodology.md](methodology.md) | 问题定义、取证、验证、性能及 token 对照、研究交付模板 | Root |
| [learning-log.md](learning-log.md) | 学习过程、方法调整和新发现的实际边界 | 工具研究岗 |
| [experiments.md](experiments.md) | 安装与实际实验，失败、冷启动和重复查询结果 | REA 执行岗 |
| [tools-and-context.md](tools-and-context.md) | 工具与后端矩阵、摘要和分页、上下文交付方法 | 工具研究岗 |
| [sources.json](sources.json) | 官方来源、版本、机器与关键原件索引 | 来源审计岗 |

每个文件由指定负责人更新；跨文件结论由 Root 核对。实验原始日志、二进制、数据库和完整结果保存在获准的数据盘，本目录维护可审阅的小型结论及精确来源。


## 2026-10-27 接续状态

观察机器仍为 `xenoamess-full-tower-eb9d2c1186`。以下是研究与迁移进度，Java 完整 G2 实机仍 **0/8**；启动、新增游戏日、SAVE、RESTORE 均为 0。[当前执行记录](../autonomous-agent-progress/2026-10-26-java-g2-resume63-current.md)保存构建失败和后继结果。

| 专题 | 已推进及待验证边界 |
| --- | --- |
| [M0 终战与恢复](../ck3-native-ai/2026-10-26-m0-rea-resume63.md) | 完整 WarID、角色上下文及 Java/兼容消费者已修；19 行 Native 软件语料与两项 CTest 通过，真实终战与恢复未验。 |
| [M1 同帧与 Faction](../ck3-native-ai/2026-10-26-m1-rea-resume63.md) | 真实读取发布链已接；C17确认10596B代码与72B跳转表；第二条路径检查旧候选，完整候选来源、自然触发仍未知。 |
| [M2 事件选择](../ck3-native-ai/2026-10-26-m2-rea-resume63.md) | 显示顺序、来源知识与普通续行已接；16B叶已证unsigned WORD较大值地址、相等取左。三自然事件及独立材料后态未验。 |
| [M3 自然继承](../ck3-native-ai/2026-10-26-m3-rea-resume63.md) | 复核 getter 调用链与宗教过滤；完整身份、自然继承及恢复接续未验。 |
| [M4 建设与现金](../ck3-native-ai/2026-10-26-m4-rea-resume63.md) | 完工材料刷新已接；取消 tooltip 的有限研究仍不授退款报价或到账信用。 |
| [M5 候选与指挥官](../ck3-native-ai/2026-10-26-m5-rea-resume63.md) | 已闭部分 getter/helper 写入；两RF已证清零/发布全局槽位和间接尾跳，注册receiver别名、Commander语料及实机仍缺。 |
| [M6 四类原生链](../ck3-native-ai/2026-10-26-m6-rea-resume63.md) | 89B初始化已证57个24B槽前16B零、末8B固定地址；不能称全零或已知业务表。loaded bank和四类验收未闭。 |
| [M7 意图接续](../ck3-native-ai/2026-10-26-m7-rea-resume63.md) | 固定钟与普通意图恢复已修；内部 job state3 不等于成功，真实保存恢复后消费未验。 |

Tools155完整验收独核1140/1140P、674pins及1466class一致。Own155原41成功，但旧Own45仅40role而现合同42，OwnJava真实失败；最窄Own46及共享source pin同步后重新资格化，155冻结保留。Main160合同47类192P；通知、APP和NT后继JUnit仍有真实失败，继续增量修复与未运行类诊断，未授整图通过。Native普通535 CXX/selected1040已编过；Source146、历史ENV146及跨Source146/Tools155的Binding均真实通过，正式ENV155暂停以等待最终Tools。RuntimeInventory146已核25875文件，无约3GiB复制；精确EXE登记、正式生产及原生corpus继续。Python四整模块22P/77subtestsP；完整35修改单元、4whole及实际依赖类型检查0errors，旧whole8和scope失败保留。workflow仍为RAM候选；Own、SERVICE、SDK Fresh4/Canonical30和真实continuation尚未完成。

使用[本轮 REA 源码研究](resume63-framework-workflow.md)与[并行工作方法](resume63-parallel-raw-method.md)区分 raw Rizin、原始字节独核和 native dossier。当前有限研究不授 Ghidra 伪代码、整机制完成、整体提速或模型 token 节省。

最新有限结果见[代码/数据与receiver研究](resume63-code-data-and-receiver-results.md)：C18已实际运行REA但自动CFG有5额外边，M4/M5保留未闭业务语义。另见[四题原生结果](resume63-four-native-boundaries.md)，保留局部语义及实际provider最大1的成本边界。

## 初始工具实测（2026-10-26）

观察机器为 `xenoamess-full-tower-eb9d2c1186`，日期 2026-10-26 UTC。已安装 Node 24.22.1、REA 6.8.0、Rizin 0.9.1、Ghidra 12.1.4，根为 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01`。复用已有 JDK 21，未改变全局 PATH。该机器事实不能外推其他机器。

同一 CK3 EXE、相同 Rizin 命令的两组冷样本中，直接调用分别为 5.3282/4.6010 秒，REA 为 8.9364/6.4378 秒；指令、局部 CFG 与 xref 结果相同。封装本轮更慢，各样本仅一对，不代表全部工作流。本轮自动 CFG 由 Rizin 后端生成，未测其相对现有方法的整体效率收益。

Ghidra 经 D 盘隔离启动脚本的七处辅助 JVM 小堆修复后，实际进入全 PE 分析；首次伪代码请求约 901 秒后因 900 秒 provider 启动预算失败，未取得伪代码或同会话第二次结果。补丁状态是 `LOCAL_PATCHED`，不称原发行版未改。详情及实际终态见实验记录。

新机制案例先取得 106 字节 RF 的局部结果，再前向补取 126 字节：合计 232 字节、64 条指令逐字节独立核验，20 块/31 边在五个被调函数正常返回的前提下闭合。局部代码把候选组件 +0x308 值加到配置指向的累计量；被调语义、缓存刷新、到场及胜率仍未知。首轮出界解析错误与 PARTIAL 原件保留。完整成本及证据见实验记录，不以单个工具耗时代表全流程。

当前没有受控的整体效率或模型 token 节省结论。语义工具的摘要、保留证据及分页能力已读源码确认，实际节省仍待测量；字节量不当作 token 数。

## 后续研究方式

先提出可证伪问题，绑定版本、目标及原始字节，选择合适后端，以小范围查询取得证据，再独立核对。C17的完整RF含表数据，线性解码失败原件仍保留；代码/数据分区须由实际引用证明，再另开有限REA查询，不能改旧守卫把失败变成通过。研究答复默认给结论、范围、未知项及证据引用，需要时再读取细节。开发与实机资格继续遵守项目合同。

60 个并发工作岗共享受管的重分析资源；实际后端进程数服从内存、存储和任务窗口。已有原件可用时优先复用，不为研究人数重复导入完整 CK3。

更新实验时记录真实时间、机器、版本、命令或 RPC、状态与原件引用。源码审查、工具返回、机制解释和游戏实测分别记载；失败保留且不改写成通过。后续新观察更新索引，历史原件保持原身份，过期资料按项目存储策略复核。

当前状态观察时间（UTC）：2026-10-27T06:12:00.749Z。
