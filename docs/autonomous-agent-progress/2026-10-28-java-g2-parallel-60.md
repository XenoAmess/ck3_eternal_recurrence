# Java 迁移与 G2：并发调整记录（固定 60 已撤销）

machine_id: `xenoamess-full-tower-eb9d2c1186`

用户于 2026-10-28 后续明确：“好了 现在开始不用强行维持60并发了，恢复成按照项目实际来”。当前按实际可执行任务、依赖、互斥和资源安排并发；取消固定人数、自动补位和为人数保留等待岗。仅待未来输入的岗位保存唯一候选及必要交接后结束，实际采用或具体失败再恢复。

下表保留本日先前“固定以60并发”“维持60并发”阶段的历史分工（原30岗、M6已有2岗、新增28岗），不表示当前仍有60岗运行。Migration继续汇总真实修复队列，Accounting维护能力及实际结果，均停止固定人数轮询和补位。

目标为完整迁移Python已有能力到Java + Maven + Quarkus，使用新Java继续完整普通自动游玩；REA的M0–M7研究并行，发现落实到实际生产者、单一强类型合同、全部消费者、持久化与回归。旧Python没有的完整借款到账、取消退款、新地产等能力不能列为漏迁，也不能宣称已完成。

首场主线独立推进：真正通过的Tools交正式Native登记；并行完成Main必要增编和成功捕获，随后原NativePlan/公共配置链→Menu→1066 entry。新增非首场必要修复进入后继队列，不把八M完整闭合作为首次启动前置。菜单启动、完整普通游玩、新增游戏日、SAVE、RESTORE分别记实。

本机约32逻辑CPU；2026-10-28T03:42:40Z样本RAM可用约39.71GiB、commit可用约117.16GiB，不能作为后续准入。REA重provider最多4，Maven、Native、Game各自限流。复用现有开发目录、输出及缓存，只增编改动模块、消费者和必要依赖，最后完整验收；不创建60棵工作树或重复导入CK3。项目大输出沿已核D盘根。

| 工作智能体（相对/root） | 工作范围 |
| --- | --- |
| acceptance63 | 主线实际结果独立验收 |
| accounting63 | 能力矩阵、实际并发状态 |
| capacity63 | 统一容量与资源调度 |
| delivery63 | 同事改动、Git集成、实际CI |
| host63 | 当前Java源码采用和构建协调 |
| launcher63 | Main增编与必要回归窗口 |
| m0_rea63 | M0终战六后态与恢复证据 |
| m1_rea63 | M1同帧Faction与危险告警 |
| m2_rea63 | M2显示选项与原生receiver |
| m3_rea63 | M3自然继承和原生角色身份 |
| m4_rea63 | M4取消资格与净退款来源 |
| m5_rea63 | M5候选、指挥官与receiver别名 |
| m6_rea63 | M6定义库、初始化、loaded资格 |
| m7_rea63 | M7原生SAVE/RESTORE完成后验 |
| migration63 | 历史60岗协调；现仅互斥叶与迁移修复队列 |
| native63 | Binding、ENV、warm BUILD、正式登记 |
| native_fixtures63 | 真实NativePlan fixture生产路径 |
| parity_autorun63 | 来源验证、动作时效、局部优化 |
| parity_events63 | 事件续行、离线worker与知识消费 |
| parity_finance63 | 战争预算与承诺费用 |
| parity_governance63 | 治理观测与普通策略 |
| parity_military63 | Army读取、Known、Core/CAS |
| parity_notifications63 | 通知左按钮与独立闭窗 |
| parity_planning63 | 完整规划器与战争分流 |
| parity_religion63 | 宗教、朝圣、成人生活方式 |
| parity_runtime63 | WorkerLoop、urgent、quiet、uncertain |
| rea63 | REA框架与四provider协调 |
| readiness63 | 首Menu生产链和独占CREATE |
| runtime63 | 1066 entry和现场采集 |
| sdk_current | 新Main实际classpath与源码闭包 |
| m6_rea63/abi552 | M6独立ABI证伪 |
| m6_rea63/java_consumer552 | M6事实到Java消费与回归 |
| sdk_canonical60 | Canonical30完整step |
| sdk_fresh60 | Fresh4完整组 |
| sdk_continuation60 | 独立进程SDK continuation |
| service_lifecycle60 | 实际Managed provider和七态资格 |
| cold_warm60 | cold/warm整组与导入顺序 |
| mcp_dispatch60 | 递归MCP目录与非战争分派 |
| diplomacy60 | 非战外交与claim消费边界 |
| dynasty_marriage60 | 婚配战争资格与deferred字段 |
| prisoners60 | 囚犯、赎金、释放后态 |
| travel_activity60 | Feast终态counter/value消费 |
| artifacts60 | 宝物、装备、背包、relic |
| mercenary60 | 报价、关系、付款与部队身份 |
| war_peace60 | 宣战、CB、白和平提案登记 |
| council60 | 内阁holder、任务与普通消费 |
| construction60 | 建造、升级、项目与扣款 |
| education60 | 教育、监护人与儿童focus |
| estates60 | 头衔授予与产权字段 |
| actor_contract60 | 四个signed actor入口与legacy兼容 |
| gui_public60 | GUI ACK、Confirm、实际闭窗 |
| checkpoint60 | Checkpoint5F与typed SAVE/cold适配 |
| termination60 | 出生身份、取消与进程终态 |
| query_archive60 | 原件归档和失败consumer |
| persistence60 | 唯一writer、reducer与锁内重验 |
| public_war60 | 公共战争MCP8和参数边界 |
| ci_r08_60 | 官方R08 fixture协议失败 |
| json_contract60 | 64位身份与严格JSON往返 |
| life_duplex60 | LifeLS26和Duplex9剩余回归 |
| sourceprep60 | SourcePrep请求准备与来源 |

Tools224正式回执已PASS，受管Maven正常退出且Job active=0；独立核验151份fresh XML为1156P、零失败/错误/skip。Main44于2026-10-28T03:47:57Z完成必要源码采用。后续增编、正式登记、实际Game以各自真实回执为准；本文创建时尚无Java Game、新增游戏日、SAVE、RESTORE可记信用。

来源为本轮用户指令及其后续撤销、历史60个工作位、AGENTS、通用存储策略、Tools224正式回执、Main44采用回执与负责人消息。持续状态沿用当前执行记录与能力矩阵，不新增调度平台。
