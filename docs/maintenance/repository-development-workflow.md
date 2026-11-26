# 仓库开发、构建与验证手册

按修改范围选读。构建与 fixture 说明中的版本、路径、统计和输出名称按当前机器与实际源码核对。实机、Steam 或桌面操作先读[实机与机器授权](ck3-operating-authority.md)。代码路径以仓库根为基准。

## 本地模型使用范围

可独立验收的真实实现或诊断优先用本地模型起草。提供实际生产者、消费者和版本合同，候选审阅、增量编测及下一项独立任务可重叠进行。按服务可用性、实际在途与依赖安排，不恢复固定人数或为用量派发空任务。当前兼容端点、模型和证据字段见[CK3 配置](../local-model-executor-config.json)，接入、重试和成功标准以同步后的共享规范为准。服务暂停或任务明确接管时继续必要实施。

`machine_id: xenoamess-full-tower-eb9d2c1186` 的共享仓库 checkout 为 `Z:/workspace/local-model-operations`。其它机器采用各自的实际路径。模型调用不得触发游戏原动作的再次提交。

## 范围和验证入口

下文的旧 PowerShell 整改、旧运行器和历史构建示例须按现行 Java 迁移、实际工具入口、机器策略及对应 CI 命令使用。视频依赖、录制和成片验收见[视频手册](video-production-workflow.md)。模组脚本与发布看[模组手册](mod-development-workflow.md)。

## 本地模型独立规范与 CK3 兼容入口（2026-11-01）

- 接入本地模型前，在消费项目的父目录克隆并持续同步维护 [local-model-operations](https://github.com/XenoAmess/local-model-operations)；checkout按执行机器解析到消费项目父目录；`machine_id: 4-8e1c2f1861`实际为`C:/workspace/local-model-operations`，其他机器的`Z:`路径不直接套用。缺少 checkout 时先 `git clone`；已有 checkout 时，在干净的 `main` 上执行 `git fetch origin` 与 `git merge --ff-only origin/main`。本地改动或分叉保留并按该仓库协作规则处理，不用 reset 或 force 覆盖。
- 同步后先读该仓库的 [AGENTS](https://github.com/XenoAmess/local-model-operations/blob/main/AGENTS.md)、[使用指南](https://github.com/XenoAmess/local-model-operations/blob/main/docs/usage.md)和[共享配置 config/executor.json](https://github.com/XenoAmess/local-model-operations/blob/main/config/executor.json)，再按执行机器的身份、证据目录和业务权限接入。并发与重试、能力边界和经验以该仓库现行规范为准；新经验与代码完成可审阅单元后，及时提交并推送 `main`。
- CK3 当前[业务兼容配置](../local-model-executor-config.json)仍按本项目实际消费者使用。共享配置或 caller 有更新时，依据明确来源审阅并显式更新兼容投影与接线；拉取共享仓库不自动切换活跃 Game/worker 的配置、caller 或服务参数。
- 机器本地caller、数据根、machine_id、证据路径和Game所有权按执行机器实际配置；本机D盘call91.py与当前/root/models91不是其它机器必须存在的入口/智能体。源码owner可直接使用现有兼容HTTP工具并行派发完整真实任务，准备/审阅/编测与其他HTTP重叠，12–16实际在途是初始运营目标，按真实积压/服务队列/错误继续调整，不把目标当已达。
- 固定三消息当前源码前缀、有限输出、SSE有效内容TTFT、六次瞬时错误退避、半截流丢弃而不拼接、实际REQUEST参数审计与采用分级见[独立仓库现行规范](https://github.com/XenoAmess/local-model-operations/blob/main/docs/concurrency-and-retries.md)。HTTP候选、软件验证、正式采用、运行期决策和游戏动作分别记录；不得因模型重试重放游戏动作。
- [本仓库旧 worker 指南](../local-model-worker-guide.md)的正文冻结为历史；[精确原文档案](https://github.com/XenoAmess/local-model-operations/blob/8bb613ac38663f0de2caddf16b983ff9e2d44636/docs/history/local-model-worker-guide.md)与[来源及 SHA-256](https://github.com/XenoAmess/local-model-operations/blob/8bb613ac38663f0de2caddf16b983ff9e2d44636/docs/source-origins.md)可追溯原版本。CK3 专属来源、运行权限和日常真实业务记录继续留在本项目。

## 编译修复先增量、并发，最后完整验收（2026-10-26 用户明确指令，长期记忆）

- 用户原话：“在已知存在编译问题的时候，复用独立工作目录，只编译改动模块及必要依赖，并发编译。等这样能跑起来的时候，最后再做一次完整编译验收。” 后续编译修复必须按此执行；本条覆盖旧交接中将每轮修错都做成 fresh snapshot/build 和全量 reactor 的流程。
- 已知编译失败时，使用独立、可复用的开发源码目录和构建输出目录，保留编译缓存、未改模块产物与合法依赖缓存。初始化一次后，在同一开发目录修改、编译、读取真实诊断并继续修复；不得每修一处错误就重新复制全图、物化全图或重建全部输出。冻结 runtime、SDK、旧失败快照及其证据继续保留，不在冻结目录热改。
- 先编译改动模块、受影响的消费者及必要依赖。Java 优先使用默认 `mvn` 的模块选择（如 `-pl ... -am`）与增量编译；启用有资源依据的 reactor 并发（如 `-T2`）。互不冲突的 Java 与 Native 构建同时推进；Native 仅构建受影响 target。实际内存失败时按真实 RAM/commit、编译器峰值调整并发，不能盲目提高并发造成重复失败。
- 旧构建适配器强制 fresh 输出只是实现限制，不能据此反复全量构建。优先使用现有可复用的 Maven/受管命令路径，必要时最小修复共享构建入口；不为修编译新增平行 runner、平台重构或无关研究，也不把重新封装大量证据作为下一次局部编译的前置。
- 局部修复能编译并通过必要的受影响测试后，最后执行一次完整编译验收并封存实际产物。若完整验收发现新错误，回到同一开发目录局部修复，再完成最终验收；保留真实失败，不跳过失败模块，不将局部通过外推为全图通过，更不将编译成功冒充 CK3 实机完成。
- 报告区分 reactor 列出的模块与实际重新编译的模块，记录实际命令、并发数、缓存复用、退出码和耗时；不能把依赖出现在 reactor 列表中说成全部重新编译，也不能只写“支持增量”而仍每轮全量执行。

## 项目大体量输出避开系统盘（2026-10-24 用户指令）

- 用户明确要求迁移本项目的 C 盘工作目录，并约束后续任务不要再向 C 盘累积数百 GiB 的工作树、构建、运行与证据。新任务必须先读取目标机器的根映射；小型账户配置和已安装依赖不由此迁移，不修改全局 `LOCALAPPDATA`、`TEMP` 或其他项目配置。
- 对 `machine_id: xenoamess-full-tower-eb9d2c1186`，背景工作树和构建根使用 `D:/codex-ck3-background`，隔离状态、场次及其临时输出使用 `D:/ck3-state/<工作包或原目录名>`。显式传递 `--state-dir`、`--userdir`、构建输出根，沿用本机 `XAR_AUTOPLAYER_STATE_DIR` / `XAR_PROJECT_STORAGE_ROOT` 配置；不得为新工作包在 `%LOCALAPPDATA%` 下另建真实的 `XarAutoplayer*` 大目录。
- 本机启用 `XAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK=true`。已接入 Java SDK/构建入口按解析后的实体卷检查输出，拒绝系统盘实体目录；未接入的旧工具仍须在执行前核对实际输出根和峰值，不能把局部入口保护声称为全机拦截。旧 C 路径若保留目录联接，只能指向已验证的 D 盘目标，不再存放一份 C 盘载荷。
- D 盘容量、配额、预留与期限继续按通用存储策略检查；数据卷容量不足时先按策略清理、停止重型写入或选择获准的其他数据卷，不得自动回退系统盘。本机 D 盘为机械盘，不能把迁移当作性能提升。其他机器自行选择获准数据卷，不照搬本机盘符。迁移结果、旧新路径和验收边界见 [本机迁移记录](2026-10-24-c-to-d-project-storage-xenoamess-full-tower-eb9d2c1186.md)。

## Java 优先与逐项迁移（2026-10-22 用户指令）

- 后续新开发任务全部使用 **Java + Maven + Quarkus**；新模块必须用 Java 创建，不再新增 Python 生产模块、构建编排模块或 CI 服务模块。Quarkus 作为宿主，纯领域与构建支持代码保持适当的独立模块边界，不为每个模块启动服务。
- 涉及旧 Python 的改动，若属于[一期迁移边界](../python-java-incremental-migration-plan-2026-10-22.md)，应将对应实现与修复放进 Java 版，同步实际生产者、全部消费者、序列化与回归；不得继续在 Python 增加平行业务实现。范围外的旧 Python 暂时允许按实际修改范围维护。
- 一期实际接管从共享强类型合同与地图回执 producer 开始；后继读取资格、纯预算/评分与 continuity reducer 按计划逐项接管，不把设计候选写成已迁移。现有 Python 消费者和测试在兼容期用于验证真实链，不成为新增 Python 功能的入口。
- 下一代架构以[Java 架构文档](../java-next-generation-architecture-2026-10-22.md)为入口：单一全 Game 动作提交权威、唯一账本 writer、严格版本合同、UNKNOWN 不重放、真实后态和保存验收；Java 编译或 HTTP 成功不能替代实机业务完成。
- 迁移尽量与现有实机并行；达到可运行条件就切 Java 版实测，失败修共享生产路径并保留真实证据，不静默 Python fallback，不热改已冻结 runtime/SDK 图。既有 C++、前端与 CK3 脚本等非 Python 代码不因本条强制重写；正式 Pages 保持纯前端。
- Maven 一律使用各执行机器**命令行默认的 `mvn`，版本不低于 3.10.0**，不得在规范、生产代码或构建配置中锁定某个绝对安装路径。按用户最新更正，已满足最低版本时无需追逐最新版；低于最低版本才在各机原安装位置更新，不因升级另换目录或修改 PATH 的选择顺序。逐机核验默认 `mvn -version`、实际 Maven home、版本及来源；不能从一台机器的结果追认其他机器。版本和安装路径记录是带机器/时间的事实，不是后续执行命令。2026-10-22 本机更新回执为 `D:/codex-ck3-demos/2026-10-22-java-phase1/DEFAULT-MAVEN-3100-ACTUAL01.json`（`machine_id: xenoamess-full-tower-eb9d2c1186`，`2026-10-22T12:20:12.065470Z`）；历史回执保留原路径，项目执行规范不绑定它。

## 强类型与字段合同（2026-10-20 用户指令）

- 后续新增或修改的公共、跨模块函数应明确标注参数和返回类型。Java 结构化数据优先采用共享 record、不可变领域模型与明确值对象；维护存量 Python 时使用共享 `TypedDict`、dataclass 或已有类型模型。避免无约束的 `Map<String,Object>`、`dict`、`list` 和字符串字段散落在生产者、消费者两端；历史代码按实际修改范围逐步收紧。
- 同一消息、回执或配置使用单一字段合同；Java 用 enum/sealed 状态分支，存量 Python 用 `Literal` 等，明确必填、可选和可空字段。字段改名须同步生产者、消费者、持久化兼容及测试，不能用别名兜底隐藏未迁移的调用方。
- JSON、文件及原生接口入口先做运行时校验，再构造内部类型。类型标注不能代替校验；整数 ID、序号和版本必须拒绝 `bool`、浮点数等相等但不同类型的值。保留缺失、`null`、空集合之间的语义差别。
- 跨 Python/JavaScript 的 FileID、FILETIME 等64位身份及时间字段使用规范十进制字符串；数值接口必须验证安全整数范围。不得经 JavaScript `Number` 往返损失精度，发现差异须保留旧回执并重新取证，不能将舍入值追认为实际身份。
- 明确内存模型与 JSON 表示的转换；tuple、list 等须经统一编码和解析，跨持久化比较基于约定的 JSON 类型域。验证序列化往返，不能因表现形式变化误判篡改，也不能放松真实内容、来源和文件身份守卫。
- 为修改范围运行实际静态类型检查，并逐步扩大覆盖。不得用宽泛 `Any`、未经验证的 `cast` 或成片 `type: ignore` 压掉错误；必要动态边界应集中、窄化并说明原因。回归测试覆盖真实生产者到消费者、错字段、缺字段、错误类型及序列化往返。

## 本机相关记录必须标注机器 ID（2026-10-15 用户指令）

- 与本地机器强相关的记录，必须附带明确的 `machine_id`，包括 Steam 在线/离线状态与版本切换、实际安装的 CK3 版本/build/EXE、运行环境与依赖、部署与路径映射、权限/Defender 设置、磁盘容量/清理及实机/录制结果。文档、交接、资格记录及机器可读回执均适用。
- 复用 `tools/ck3_live_run_id.py machine` 的稳定机器 ID；同时记录实际观察时间与证据出处。盘符、路径、操作者、Git commit 或“本机”字样不能代替机器 ID，也不能据这些信息推断两份记录属于同一机器。
- 读取其他机器的记录时，先核对记录中的 `machine_id` 与当前执行机器。不同机器的记录只能证明来源机器当时的状态；可复用知识和代码，但安装、下载完成、Steam 离线、部署、权限、容量及实机通过等事实必须在目标机器重新读回，不能相互外推。
- 历史记录缺少机器 ID 时，明确标为 `machine_id: unknown`、所属机器未核实，不猜测或追认其本机效力。能从原始证据核实后，追加带时间和出处的机器身份补注，保留原有历史事实；涉及多台机器时逐台列出 ID、状态和证据。

## 全部执行机器的存储时效与容量（2026-10-10 用户指令）

- 用户指出所有资料都有时效性，过时的存档、原始证据，尤其大文件，也应纳入清理。不得仅因它属于历史、失败 attempt 或过程资产，就无限期保留全部文件。本条覆盖下文及旧交接中对已过期资料的默认永久保留要求；当前必要基线、活跃输入和待解决问题的关键证据仍须明确保护。
- 回收按当前用途、后续引用、替代证据、期限和容量共同判断；不能仅凭目录叫 runtime/cache、文件较旧或场次失败就认定过期。保护项也应记录复核期限和继续保留理由，不能无期限续存。
- 大文件优先评估：完整导出已有精确摘要且可以从保留原件重建时，优先回收派生副本；相同的不可变输入避免重复存储。删除后保留小型清单与原因，并如实标明旧原件已不可读取，不制造同名替代证据。
- **所有执行机器、所有当前及未来工作包必须使用同一份 [通用存储策略](../storage-retention-policy.md) 与 [版本化参数](../storage-retention-policy.json)**；任务开始、重型写入前和闭场时执行其检查。机器只配置本机身份、获准根目录、卷映射、容量与系统增长预留，不另起一套永久保留或任意删除规则。不能把本机 `C:`、固定盘符或某次剩余容量写成跨机器前提。
- 默认期限、到期判定、限期保护、预算不足时的停工边界和精确回收流程按通用策略执行。统一自动回收器、空间预留器尚未实现时，由执行者落实相同步骤和回执；不得声称已自动部署到其他机器，不得无工具就省略检查。新规则允许回收符合条件的项目过期资产，不授权删除个人文件、其他任务资产、在用游戏/依赖或不加区分地删除整棵目录。
- [本机清点](storage-retention-2026-10-10.md)只作问题样本，不是其他机器的占用或可释放量证明。

## Windows Defender 项目构建 EXE 排除（2026-10-05 用户指令）

- 2026-10-28 用户明确要求：“你需要设计以后不进行UAC只进行这一次。” 后续以一次管理员安装的项目专用 SYSTEM 按需 broker 承接已授权构建范围内的新 EXE 登记，普通调用方提交数据并取得真实 SYSTEM 设置读回，不再逐个构建请求 UAC。该要求不授权关闭系统 UAC、放开任意管理员命令或扩大排除范围；任务、受保护代码、配置与请求边界须固定。安装后必须用普通 token 为另一个真实新构建路径完成登记，才能报告免重复 UAC 已验收。历史 broker 的安装事实只对其已核机器有效；当前机器须独立安装、读回和验收。实现进度与边界见 [broker 专题](../ck3-native-ai/project-exe-defender-broker.md)。
- 用户明确授权：现在以及后续，Windows Defender 对本项目构建的全部 EXE 进行永久排除；不再使用本次拍摄结束即撤销的临时方案。
- 本机登记使用已核验的项目构建来源和完整 EXE 路径，保全构建、文件 SHA-256、设置前后实际读回及失败回执。后续新增构建输出需继续登记，不能把旧路径已排除外推到新路径。
- 不扩展为全机 `.exe` 扩展名排除、其他程序或整个工作盘排除。构建工具只能对项目声明的可执行目标登记；第三方解释器、媒体工具、Steam 和 CK3 本体不因本授权纳入。
- 管理员权限不足、Windows 系统确认取消或设置读回缺失时，如实记录登记或验收未完成；普通 token 的隐藏空数组不能证明未生效。用户授权、调用 ACK 和管理员实际生效读回分别记录。继续执行下文 Python-only 规则。
- 当前 238 个精确路径的管理员实际回执、COM 空返回/普通 token 隐藏数组纠正、6 个已接入构建入口、161 个旧研究生产器未自动覆盖边界及显式 native UAC 登记方法见 [项目 EXE 永久排除](../ck3-native-ai/project-exe-defender-exclusions.md)。后续 hook 只在本机 Git-local `xar.defenderProjectExeExclusions=true` 时启用；非管理员登记需明确报告 admin-required，不能声称已完成全部未来输出登记。
- 2026-10-05 固定受保护 SYSTEM broker 与首批四项已由实际回执验收；源码、stock `VARIANT` 兼容修复、历史固定恢复与普通调用方后续验收状态见 [broker 专题](../ck3-native-ai/project-exe-defender-broker.md)。已安装本机的已知 CMake/MSVC producer 可经既有 helper 走普通请求；Task ACK 仍不证明登记成功，必须接收精确绑定的实际 SYSTEM 设置回执。批量运行时不入库，不由新 clone/CI 自动安装或更改系统设置。

## PowerShell 禁令

- 本项目禁止任何 PowerShell：不得新增或执行 `.ps1` 脚本，不得在代码、文档、CI、测试、构建、验收或操作命令中调用 `powershell`、`pwsh`、PowerShell cmdlet 或 PowerShell 语法。
- 发现历史已有的 PowerShell 脚本或调用时，必须移除其执行入口，并按上文 2026-10-22 Java 优先规范迁移到 Java；范围外的存量 Python 维护仅限已允许的旧模块，同时更新调用方、文档与测试，不保留 PowerShell 兼容入口。
- 此整改不扩大为重写 C++、前端或 CK3 脚本的授权；Python 的逐项迁移按上文 Java 优先规范执行。

## 构建/生成

```text
py XenoAmess_s_Eternal_Recurrence/tools/gen_highscore.py   # 位阈值体系
py tools/gen_pools.py                                       # 祝福/诅咒奖池（100+100）
py tools/gen_contracts.py                                   # 本世契约、PB、图鉴与里程碑事件
py tools/gen_scoring.py                                     # 死亡计分 effect 与规则文档
py tools/gen_score_preview.py                               # 特质 hover 只读即时分数
py tools/gen_no_heir_gui.py                                 # 原生继承窗投影 + 无继承人结算注入
py tools/gen_balance_wire.py                                # 开发用长期平衡遥测位帧
py tools/extract_courtier_traits.py                         # 从当前原版 00_traits.txt 刷新元数据快照
py tools/gen_courtier_creator.py                            # 原版廷臣特质目录、元数据与冲突
py tools/gen_vivhite_courtier.py                            # 白绮独立版廷臣目录（独立快照/ervc 命名空间）
py tools/compose_decision_art.py                            # 三张决议源图 → 1100×440 DXT1 DDS
py tools/compose_vivhite_key_art.py                         # 白绮主视觉 → 独立版 640×640 thumbnail
py tools/compose_ox_here_key_art.py                         # 牛来主视觉 → 640×640、低于 1 MB thumbnail
py tools/compose_ox_here_workshop_media.py --artifacts <run> # 牛来 GREEN 实机截图 → 四张低于 2 MB JPEG
py tools/compose_remove_mandala_key_art.py                  # 肃清曼荼罗主视觉 → 640×640、低于 1 MB thumbnail
py tools/compose_remove_mandala_workshop_media.py --artifacts <run> # GREEN 实机截图 → 两张低于 2 MB JPEG
py tools/gen_reclaim_the_motherland_title_names.py          # 后朝标准朝号的九语确定性组合 key
py tools/compose_reclaim_the_motherland_key_art.py          # 重整河山主视觉 → 640×640、低于 1 MB thumbnail
py tools/compose_tributary_expansion_directives_key_art.py  # 驱策朝贡国主视觉 → 640×640、低于 1 MB thumbnail
py tools/compose_tributary_expansion_directives_workshop_media.py --artifacts <run> # 驱策朝贡国 GREEN 实机截图 → 一张低于 2 MB JPEG
py tools/compose_auto_upgrade_buildings_decision_art.py     # 自动升级建筑源图 → 1100×440 DXT1 DDS
py tools/compose_reclaim_the_motherland_workshop_media.py --artifacts <run> # 开封镜头 GREEN 实机截图 → 三张低于 2 MB JPEG
py tools/compose_auto_upgrade_buildings_workshop_media.py --artifacts <run> # 自动升级建筑 R0033 GREEN 实机截图 → 三张低于 2 MB JPEG
py tools/compose_trait_stars.py                             # 10 级特质星标 → 120×120 RGBA DDS
py mod_zhongguo_style/tools/gen_361_mechanisms.py           # 361 目录、领域合同与制度卡
py mod_zhongguo_style/tools/gen_361_b1_runtime.py           # B1 跨周期绩效季与共同上司 barrier
py mod_zhongguo_style/tools/gen_scoreboard_snapshot.py      # 考核榜固定快照槽与 GUI 投影
py tools/build_release.py --check                           # 临时双构建，验证 manifest/ZIP 可复现
py tools/build_release.py                                   # 生成 dist staging、manifest 与 deterministic ZIP
py tools/build_vivhite_release.py --check                   # 白绮独立版临时双构建
py tools/build_vivhite_release.py                           # 生成独立 staging、manifest 与 ZIP
py tools/build_remove_mandala_release.py --check            # 肃清曼荼罗临时双构建
py tools/build_remove_mandala_release.py                    # 生成 15 文件 staging、manifest 与 ZIP
py tools/build_reclaim_the_motherland_release.py --check    # 重整河山临时双构建
py tools/build_reclaim_the_motherland_release.py            # 生成 36 文件 staging、manifest 与 ZIP
py tools/build_tributary_expansion_directives_release.py --check # 驱策朝贡国临时双构建
py tools/build_tributary_expansion_directives_release.py    # 生成 16 文件 staging、manifest 与 ZIP
py tools/run_tributary_expansion_directives_acceptance.py --preflight # 驱策朝贡国外置夹具与实机环境预检
py tools/build_celestial_commerce_corruption_release.py --check # 天朝经商贪腐维护版临时双构建
py tools/build_celestial_commerce_corruption_release.py     # 生成 22 文件 staging、manifest 与 ZIP
py tools/run_celestial_commerce_corruption_acceptance.py --preflight # 天朝经商贪腐外置夹具与实机环境预检
py tools/compose_celestial_commerce_corruption_workshop_media.py --artifacts <run> # GREEN 贪腐事件截图 → 一张低于 2 MB JPEG
py tools/gen_auto_upgrade_buildings.py                      # 自动升级建筑 165 条建筑链、605 条升级边
py tools/build_auto_upgrade_buildings_release.py --check    # 自动升级建筑临时双构建
py tools/build_auto_upgrade_buildings_release.py            # 生成 17 文件 staging、manifest 与 ZIP
py mod_de_jure_conquest/tools/build_release.py --check       # 法理征服维护版临时双构建
py mod_de_jure_conquest/tools/build_release.py --release --output <new-output> # 正式 tag 对应的 16 文件 staging
py mod_change_holding_types/tools/build_release.py --check --release-localization # 地产转换维护版临时双构建
py mod_change_holding_types/tools/build_release.py --output <new-output> --git-tag change-holding-types-v1.0.0 --release-localization # 正式 tag 对应的 17 文件 staging
py mod_superman_qiang/tools/build_release.py --check --workshop-item-id 3812991990 # 超人强独立版临时双构建
py mod_superman_qiang/tools/build_release.py --output <new-output> --git-tag superman-qiang-v1.0.0 --workshop-item-id 3812991990 # 在真实正式 tag checkout 构建 22 文件 staging
py mod_superman_qiang/tools/build_release.py --check          # 超人强独立版 22 文件临时双构建
py mod_superman_qiang/tools/build_release.py --output <new-output> --git-tag superman-qiang-v1.0.0 # 正式 tag 对应的 staging
```

上述脚本生成器与素材投影工具中，**不要手改 `GENERATED FILE` 标记的文件**。计分参数只改 `tools/scoring_data.py`，
再运行 `gen_scoring.py` 与 `gen_score_preview.py`；奖池条目改 `tools/pools_data.py`
（数据表）再跑 gen_pools.py；权威表 `docs/blessing-curse-pools.md` 由它导出。
计分生成器产出 `common/scripted_effects/xar_generated_scoring_effects.txt` 与
`docs/scoring-rules.md`；hover 生成器读取同一 schema 产出 `common/script_values/xar_generated_score_preview.txt`。
奖池稳定 ID 的独立冻结契约在 `tools/pool_semantic_contract.sha256`；普通 `gen_pools.py` 不更新它。
改池后必须先审阅权威表与 dispatcher diff，再用 `py tools/validate_static.py --print-pool-contract`
取得候选并显式更新契约，禁止为了消除校验错误盲目刷新。
契约原型、PB、图鉴、琉焰之视成长表和 28 个里程碑事件改 `tools/contracts_data.py`，再跑 `gen_contracts.py`；该生成器也产出 `common/traits/xar_traits.txt`。
无继承人结算 widget 改 `gui/xar_no_heir_settlement.gui`；原生继承窗投影必须运行 `tools/gen_no_heir_gui.py`，不要手改 `gui/window_succession_event.gui`。
长期平衡 wire 字段改 `tools/balance_wire_data.py`，再运行 `tools/gen_balance_wire.py`；两份生成结果仅供 development acceptance，release staging 必须整文件排除。
廷臣 trait 元数据快照在 `tools/courtier_traits_1_20_0_3.json`。改动或升级游戏版本时，先更新
`extract_courtier_traits.py` / `gen_courtier_creator.py` 内的版本、输出名和预期计数，再运行
`py tools/extract_courtier_traits.py` 从当前原版 `00_traits.txt` 刷新快照；审阅 snapshot diff 后才运行
`py tools/gen_courtier_creator.py`，并审阅生成的五类目录、226 项元数据与 95 组冲突（当前原版快照为 306 个 trait）。只运行生成器不会重新读取游戏文件。
三张决议源图位于 `images/decision_*.png`；修改后运行 `py tools/compose_decision_art.py`，不要手改
`gfx/interface/illustrations/decisions/decision_xar_*.dds`。静态校验会逐字节重建并检查 DXT1 输出。
自动升级建筑的决议源图为 `images/auto_upgrade_buildings_decision.png`；修改后运行
`py tools/compose_auto_upgrade_buildings_decision_art.py`，不要手改其 `decision_auto_upgrade_buildings.dds`。静态校验会逐字节重建并检查 1100×440 DXT1 输出。
白绮独立版主视觉源图为 `images/vivhite_courtier_key_art.png`；修改后运行
`py tools/compose_vivhite_key_art.py`，不要手改其 `thumbnail.png`。静态校验会逐像素重建并检查 PNG。
十级特质星标由 `tools/compose_trait_stars.py` 程序化生成；不要手改
`gfx/interface/icons/traits/_stars_10.dds`。原版只提供 0–5 级星标，静态校验会逐字节重建该 RGBA DDS。
位阈值体系生成器产出：`common/tutorial_lessons/xar_highscore.txt`、`common/customizable_localization/xar_generated_loc.txt`、
`common/scripted_guis/xar_generated_guis.txt`、`common/scripted_effects/xar_generated_effects.txt`、
`gui/xar_meta.gui`、`localization/*/xar_generated_*.yml`。

要扩上限：改生成器里的 `TIERS` 列表再跑一遍即可，旧纪录不丢（位是只增的）。

发布构建使用明确 allowlist，并从开发树渲染 production-only 投影：整文件排除 selftest/死亡探针/trait bridge，
再剥离 `# XAR_ACCEPTANCE_ONLY_BEGIN/END` 区域并展开 `# XAR_RELEASE_ONLY` 生产替代行；最终 staging 禁止出现测试标识。
未标记文件仍逐字节复制。禁止直接把 mod 源目录上传；正式上传只能使用 `build_release.py` 生成的 staging。

## 测试流程

**静态 L0（跨平台/CI）**：

```text
py -m pip install -r tools/requirements-static.txt
# The external promo wheel is intentionally a separate requirement file.
py -m pip install -r tools/requirements-promo-toolchain.txt
py tools/test_gen_no_heir_gui.py
py tools/test_build_release.py
py tools/test_build_vivhite_release.py
py tools/test_build_auto_upgrade_buildings_release.py
py tools/test_build_celestial_commerce_corruption_release.py
py tools/validate_python_only.py
py tools/validate_static.py
py tools/validate_vivhite_static.py
py tools/validate_auto_upgrade_buildings_static.py
py tools/validate_celestial_commerce_corruption_static.py
py -c "import sys; sys.path.insert(0, 'tools'); import scoring_data; scoring_data.assert_reference_vectors()"
py tools/build_release.py --check
py tools/build_vivhite_release.py --check
py tools/build_auto_upgrade_buildings_release.py --check
```

**mod 验收（统一公共入口）**：

创建或更新 `tools\.venv` 后，除 `tools/requirements.txt` 外，必须使用同一解释器单独执行
`-m pip install -r tools/requirements-promo-toolchain.txt`；该依赖不再由通用 requirements 文件间接引入。

未来新 run 只使用 `tools/ck3_mod_acceptance.py` 的 `plan / prepare / allocate / preflight / run / verify`，
通过同一份全局 common runtime manifest 的本机路径映射绑定 host/source/native。
下例中的 JSON 路径须取自当次公共绑定；`plan` 只读，不分配或启动：

```text
tools/.venv/Scripts/python.exe -B -X utf8 tools/ck3_mod_acceptance.py plan --runtime <共同runtime的本机映射JSON> --products tools/ck3_mod_acceptance_products.json --product eternal-recurrence --case source-courtier-ui
```

实际 prepare/allocate/preflight/run/verify 参数见 [公共消费顺序](../ck3-mod-upgrade-fast-validation.md#当前公共cli与本机共同版本)。
既有 builder、静态检查和不启动游戏的 preflight 保持可用；旧 `run_acceptance.py` / `run_vivhite_acceptance.py`
只供只读历史、library 和原断言复用，不直接启动未来新场。原独立加载、双 mod 顺序及其他产品业务要求保留，
不能以公共 GREEN 或三个 basic-load case 的加载边界代替产品业务 PASS。原理与历史坐标表见 `docs/testing-workflow.md`。

**CI 边界**：`.github/workflows/static-ci.yml` 使用 GitHub 官方 `windows-latest`，在 push/PR
执行三套产品 L0，并离线测试 MiniMax 候选调用器；手动触发时生成三套 ZIP/manifest，`v*`、
`vivhite-v*`、`ox-here-v*` 分别生成对应正式产物。官方 runner 没有 CK3、Steam 授权和
可靠交互桌面，只执行既有无 CK3 静态／离线检查，不调用公共 `allocate/run` 或旧 live runner，也不声称完成 L1-L3；真实游戏验收必须在本机通过公共入口运行并保存报告。

**历史缓存混用排查（不作未来同步／启动入口）**：以下是旧现场流程记录。新源码验收通过公共 prepare 的隔离 profile 绑定正式投影；不得按旧流程覆盖已发布缓存或绕过公共 run。启动器把 dev .mod（带 remote_file_id）和工坊订阅合并，
游戏实际加载的是 **工坊缓存**（`Z:\SteamLibrary\steamapps\workshop\content\1158310\3784706360`，
播放集里生效的是 `mod/ugc_3784706360.mod`）。runner 每次跑前 robocopy 同步仓库 → 工坊缓存；
手动测试前也必须先同步（或直接 `robocopy XenoAmess_s_Eternal_Recurrence <工坊缓存> /MIR`）。

历史手动兜底记录（未来新场须修复／使用公共入口，不直接执行下列旧启动流程）：
1. 通过 Python `subprocess.Popen(["binaries/ck3.exe", "-debug_mode"])` 启动
2. 日志：`Documents\Paradox Interactive\Crusader Kings III\logs\error.log`（解析/运行时错误）、
   `debug.log`（`debug_log` 标记，本项目用 `XAR:` 前缀）
3. 全局存储落盘文件：`Documents\Paradox Interactive\Crusader Kings III\tutorial.txt`
4. 流程性验证：新开局看商店事件 → 控制台 `die` → 结算事件 → 教程通知自动完成 → 再开新局看导入

## Git 约定

### 外部贡献与 CLA

- 外部贡献必须遵守根目录 `CLA.md` 与 `CONTRIBUTING.md`，并在对应 PR 中由每个被检查器识别的贡献账号发表配置中规定的精确签署声明。
- `CLA / signed` 是 `master` 的必需提交状态。CLA 检查器只允许从默认分支运行，禁止在 `pull_request_target` 或 `issue_comment` 高权限上下文中检出、构建、导入或执行 PR head、fork artifact 或其他贡献者可控代码。
- `cla:manual` 只允许维护者在已经核验企业 CLA、线下签名、无法映射作者或等效证据后添加；标签是审计记录，不是绕过入口。
- 实质修改 CLA 时必须提升版本，并同步更新 `CLA.md`、`.github/cla-config.json`、`CONTRIBUTING.md` 和检查器测试。完整运维合同见 `docs/cla-bot.md`。

### Codex 跨任务通知

- 每个独立 Codex 任务使用 `D:\workspace\.codex-task-bus\bin\codex_task_bus.py` 登记并轮询状态；完整协议与命令见
  `docs/codex-task-bus.md`。任务开始先 `register`、`poll --ack`、`list`，状态变化和共享资源取得/释放时写 `status`，长任务每
  15 分钟 `heartbeat`，完成时写 `done`。
- Git push、Workshop 外部写入和 CK3 启动前必须再 `poll --ack`；通知只用于协作，不替代 `fetch + rebase`、既有排他锁或用户授权。
- **受管实机的 clean checkout 冻结。** 当 screen keeper 将 owner checkout 的 exact HEAD 与 `dirty_entries=0` 作为准入/续租条件时，该目录内的实现和文档候选只保全到外置 runtime；正常保存并退出游戏、停止 keeper 并完成 CAS 释放后，才应用 tracked 修改、提交并为下一冷载重新冻结。不得在会话中忽略 dirty 拒绝、更新冻结 source/HEAD 来追认变更，或以无 `expected-sequence` 的 heartbeat/status 绕过条件续租；原始拒绝和最后有效序号继续保留。其他隔离目录的工作仍按其文件所有权推进。租约合同见 `docs/codex-task-bus.md`。

- **每次任务执行完成后，默认 `git commit` + `git push`**（无需另行确认，也不要等人工验证，直接提交推送）
- 提交信息用英文，简明描述改动
- **本项目严禁 merge，只允许 rebase。** 禁止执行 `git merge`、会产生 merge commit 的 `git pull`，以及任何其他合并提交；同步远端必须先 `git fetch`，再以 `git rebase origin/master`（或等效的 `git pull --rebase`）线性重放本地提交，复测后仅作普通 fast-forward push。遇到并发推送或冲突也必须继续走 rebase，不能用 merge 绕过。
- **工作包一次验证、立即交付。** 每个独立工作包只做一次与风险相称且必要的验证；验证通过或形成可复现的 RED 证据后，立即提交到主线并普通 fast-forward 推送，然后继续下一个工作包。除非出现改变结论的新证据或用户明确要求，不重复同一验证，也不把等待人工复核当作停工条件。
- **少分支、快回主线。** 默认直接从最新 `origin/master` 工作；只有真实隔离、并发冲突或高风险 live 实验才创建短期分支。短期分支完成后必须 rebase 到最新 `master` 并以 fast-forward 方式回到主线，CI 进入终态后立即删除 local/remote ref；不得为了保存过程、形式审查或“以后可能有用”长期保留游离开发分支。
- **子进程 429 直接复用。** 子进程因服务端 `429` 中断时，先用原任务线程/工作树复用并继续执行，不把 429 当作任务失败或终止；必要时再把同一 bounded 工作包转移给本地执行或另一可用线程，并保留已取得的证据，禁止从头重复无变化的验证。
- `origin/master` 是唯一集成真相，默认从最新 master 直接开发。只有具体隔离、真实并发或高风险 live 理由才建
  `wip/<topic>`；必要发布线才用 `release/<product>-<version>`。分支必须登记 reason/base/owner/acceptance/deadline，
  成品及时 rebase 到最新主线并 fast-forward 更新 `master`，等待 exact master SHA 官方 CI GREEN 后删除 local + remote ref。
- **谨慎创建 Git 分支不等于限制 Agent 子线程。** 能按文件所有权、运行现场或依赖边界安全拆分的工作应主动使用多 Agent
  并行；各线程仍共同服务于 `master`，可在同一工作树修改互不重叠文件，或使用基于 exact master 的 detached worktree。
  detached worktree 不是新分支；若产生提交，必须尽快 rebase 到最新 `master` 并 fast-forward 更新主线，不得因此保留长期游离 ref。
- 在 Windows 为并行任务新建 worktree 时，优先使用短的绝对路径（例如 `D:\w87`）；本仓深层目录曾使
  `D:\workspace\ck3_regiment87_modifier_20260927` 这种长目标在 checkout 末尾报 `Could not reset index file to revision HEAD`，
  而短路径完成同一约 9875 文件的 checkout。任务开始仍先按任务总线协议登记；`git worktree add` 完成后核对目标 `.git`
  和 `git status --short --branch` 仅有预期分支且无脏项，再开始编辑或测试，并以实际 worktree 路径重新登记任务总线 repo。
  checkout 期间的临时大量 dirty entries 不能当成真实改动。
  失败时先确认 Git 是否已自行回收目标；如需清理残留目录，须先验证解析后的绝对路径位于预期工作区，不能误删其他任务素材。
- 禁止 force-push。并发推送先 fetch/复核 remote master；远端移动时停止 push，rebase 到新 master、复测后普通 fast-forward push。
- 冻结 evidence 使用 detached HEAD 与根目录 `.xar-frozen-evidence.json`；不得把历史 runtime clone 当开发线。仅当写 marker 会
  改变所有者已冻结的 dirty tree 时，才可用记录 exact HEAD/status/diff hash 的中央 machine-readable ledger 代替。删除 branch ref
  绝不授权删除 worktree、clone、构建目录或 process assets。完整规则与跨 common-dir/独立 clone 清单见
  `docs/branch-management.md`。

## 工作流程规则

### 0. 必要性与成本优先（最高优先级）

- 如果不能用用户明确需求、当前真实故障、可复现测试、运行日志或现有数据证明必要性，严禁花费用户的模型额度和时间研究、设计或实现额外安全边界。不得在安全相关领域因为“理论上可能”“更完美”“纵深防御”而自行扩张任务；本条不限制正常的功能优化、故障修复、架构改进和主动推进。
- 提议任何新的门禁、限制、威胁模型或防御性机制前，必须先给出简短的必要性证据与预期收益；证据不足就立即停止该方向，回到用户要求的功能、稳定性和运营结果。
- 不得把假设性的 symlink、gitlink、prompt 篡改、路径逃逸等场景自动升级为当前任务；只有已经发生、能复现、用户明确要求，或存在迫近且不可逆的数据损失/凭据泄露风险时才处理。
- 本项目追求相对安全、可观测、可记录、可回退，不追求耗费大量额度证明“绝对安全”。优先采用最小有效修复并及时提交；不得以安全之名重新收紧复盘模型的文件范围或恢复全仓门禁。
- **交付节奏优先，禁止过度核对与过度谨慎。** 对同一结论只做一次与风险相称的验证；已有可核验证据、测试结果和失败 artifact 直接复用，不重复跑同一检查、不为理论风险扩展审计。验证完成即提交并继续下一个工作包；只有新证据改变结论或用户明确要求时才重新核对。
