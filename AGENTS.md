# 琉焰卿的永恒轮回（AGENTS 指南）

本仓库维护 CK3 主模组、独立模组、自动游玩智能体、Java/Quarkus 控制与 Native bridge，以及验收、发布和宣传工具。先识别任务、执行机器和产物所有者，再进入相应指引。

## 按任务读取

子目录指令随工作目录加载。从仓库根启动或跨目录修改时，先显式读取表中的对应指引。普通文档按任务选读。

| 任务 | 指引 |
| --- | --- |
| Java、Maven、Quarkus、强类型合同及生产消费者 | [Java AGENTS](java/ck3-control/AGENTS.md)、[开发和验证手册](docs/maintenance/repository-development-workflow.md) |
| 自动游玩、同局恢复和规划器 | [自动游玩 AGENTS](ck3_autonomous_player/AGENTS.md)、[智能体工作手册](docs/maintenance/autoplayer-workflow.md) |
| Native bridge、原生观测、版本绑定与 MCP | [自动游玩 AGENTS](ck3_autonomous_player/AGENTS.md)、[Native AGENTS](ck3_autonomous_player/native_bridge/AGENTS.md) |
| CK3、Steam、窗口、安装、运行许可或机器例外 | [实机与机器授权](docs/maintenance/ck3-operating-authority.md) |
| 模组脚本、本地化、家徽编辑器、验收和 Workshop | [模组开发与发布手册](docs/maintenance/mod-development-workflow.md) |
| 录制、剪辑、字幕、交付与实时决策合成 | [视频 AGENTS](promo/AGENTS.md)、[视频制作手册](docs/maintenance/video-production-workflow.md) |
| 本地模型 | [开发手册中的模型入口](docs/maintenance/repository-development-workflow.md#本地模型使用范围)、[CK3 兼容配置](docs/local-model-executor-config.json) |
| 当前进度、旧交接、证据和产品版本 | [智能体迁移](docs/ck3-1.21.0-migration-2026-11-18.md)、[进度中心](docs/autonomous-agent-progress/README.md)、[发布日志](docs/release-changelogs/)、[旧 AGENTS 记录索引](docs/maintenance/agents-history-through-2026-11-25.md) |

## 权限与运行

- 本次用户指令优先。运行、交接及发布记录描述各自机器和时点。启动、附加、操作窗口、切换 Steam 在线状态或发布前，先按[实机与机器授权](docs/maintenance/ck3-operating-authority.md)核对本任务的许可与现场 owner。用户接管或暂停期间继续获准的离线工作。
- 每机至多一个受管 CK3，Steam 默认后台离线。智能体迁移默认最小化、静默、无置顶和不抢焦点。只在匹配机器与任务的授权下使用前台、截图、真实鼠标或上线窗口。绝不抢占另一操作者的账号、窗口、Game、Job、租约或冻结工作树。
- 游戏内协议和通知的既有处理授权按[智能体工作手册](docs/maintenance/autoplayer-workflow.md)执行。涉及真实货币购买、DLC、下单、付款或含糊的外部付费控件时停止输入并保留证据。游戏内资源支出按原玩法合同处理。
- Runtime 独占实机、Game/Native live、worker/keeper、账本和实际采用。Java 负责正式业务源码和 Git 集成，Native 负责 C++ 和版本绑定，Root 协调。独立工作按实际依赖、资源和文件所有权并行，无固定人数和逐项 ACK。旧 PID、期限、source、冻结配方和已消费工具只作各自证据。
- 自动游玩优先接续同一局。常规业务修复只重载智能体层。已结算和 UNKNOWN 原动作都禁止重放或续旧期限，隔离和新终态通过原权威账本正规写入。普通游玩采用独立原版无模组 profile，模组产品测试沿各自授权和验收入口执行。

## 开发与交付

- 禁用 PowerShell，包括新增或执行 `.ps1`、`powershell`、`pwsh`、cmdlet 和 PowerShell 操作命令。存量执行入口在实际整改范围内迁移。
- 新生产开发采用 Java、Maven 和 Quarkus。存量 Python 按既定一期边界逐项迁移，范围外按需维护。C++、前端与 CK3 脚本沿既有技术栈。各机使用命令行默认 `mvn`，最低 3.10.0。编译修复复用隔离目录和缓存，先选择受影响模块及依赖增量编测，再做一次对应完整验收。
- 公共和跨模块接口使用明确类型与版本合同。生产者、消费者、持久兼容和回归同步修改。入口运行时验证 JSON 和原生数据，保留缺失、null、空集合、数值宽度与真实身份。跨 Python/JavaScript 的 64 位身份和时间使用规范十进制字符串。
- 依据用户需求、实际故障或可复现证据施工。共享故障修共享生产路径，使用已有验证和最小必要测试。启动只保留执行所需配置、Steam/单实例、超时和真实就绪约束，避免重复加回历史来源审计。性能评估保持玩法策略和结果语义。
- 可独立验收的实现或诊断优先交现行本地模型提出候选，并行推进准备、编测和评审。先按[模型工作流](docs/maintenance/repository-development-workflow.md)同步共享规范。HTTP 候选由 owner 编测和审阅，按实际容量和错误调度。
- 内容玩法默认限定玩家。模组专属 AI/NPC 例外按[模组手册](docs/maintenance/mod-development-workflow.md)中的产品与触发条件执行。保持脚本 UTF-8 BOM 和生成物同步。共享验收走 `tools/ck3_mod_acceptance.py` 公共入口，产品提供数据、夹具和适配器。
- 同一审核范围只做一次必要验证。源码、测试、发布、实机装载、动作后验、日期推进和物理保存分别记录。ACK、静态或 fixture 结果按实际范围计算。

## Git、协作与存储

- `origin/master` 是唯一集成主线。同步先 `git fetch`，再 `git rebase origin/master`。项目禁用 merge 与 force-push，验证后正常 fast-forward 推送。默认每个完整工作包英文提交并及时 push。并发时用文件所有权和必要隔离检出保护在用资产。
- 任务通过本机[任务总线](docs/codex-task-bus.md)登记、轮询与收束。Git push、外部发布以及 CK3 启动前再次 `poll --ack`。受管现场的 exact HEAD、工作树与租约按 owner 冻结，实际正常退出和释放后才在该目录编辑。
- 外部贡献执行 [CLA](CLA.md) 和[贡献规则](CONTRIBUTING.md)。高权限 CLA checker 只运行默认分支的可信实现。
- 与本机相关的事实统一记录 `machine_id`、观察时间和来源。用 `tools/ck3_live_run_id.py machine` 核对本机。容量、构建、部署、权限、存档及实机验收使用本机实际证据。
- 按[通用存储策略](docs/storage-retention-policy.md)与[参数](docs/storage-retention-policy.json)管理输出、保留和回收。任务开始、重型写入前及收尾核对根与容量。当前执行根和例外按机器授权，保护活跃资产和唯一必要证据。超过保留期限的项目资产按用途与所有权复核。

## 维护指引

全仓只维护一份[当前交接](docs/handover/README.md)。交接时原地更新，核对接续状态并删除已完成事项、过期限制和失效入口。长期规则更新到相应手册，历史交接从 Git 查看。

跨仓长期规则写在本文件，单模块操作写在对应子目录，详细参数和流程写在专题手册。产品版本与发布结果更新其 changelog，日期、机器和运行证据更新进度或交接。新授权更新机器或任务入口，并链接来源与适用范围。
