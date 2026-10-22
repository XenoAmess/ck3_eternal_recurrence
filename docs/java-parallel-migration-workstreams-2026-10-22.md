# Java 并行迁移工作包：32 条实现线

用户于 2026-10-22 要求至少 16、优先 32 条并发迁移线。本轮分配 **32 条具体实现线**，另有构建、CI、资源协调与独立审查；该数量描述工作分配，不代表 32 个组件已完成生产接管。依据 [Java 开发规范](../AGENTS.md)、[一期边界](python-java-incremental-migration-plan-2026-10-22.md)和[目标架构](java-next-generation-architecture-2026-10-22.md)执行。

纯叶按领域组合到 Maven 模块，宿主仍为单个 Quarkus 服务。每条线独占 package、测试、样本和迁移说明；不为每个叶建立服务。来源/观察/运算合同跟随实际旧生产者，迁移者必须先查真实调用链；发现旧叶仅属历史 attempt 或已无生产消费者时，转向活跃可复用边界，不照搬硬编码 PID/序号。

## 实现分配

| 线 | Java 模块 / 独占叶 | 迁移的实际边界 |
| --- | --- | --- |
| 1 | `war-budget` | `war_emergency_budget_v1` 军费、承诺、可选建设资金 |
| 2 | `campaign-score` | `campaign_development_score_v1` 区间聚合、固定 360 分母与精确输出 |
| 3 | `replenishment-policy` | `replenishment_numeric` 原生低位回绕、定点、补员投影 |
| 4 | `closed-failure-recovery` | 失败部分 FULL 回到原 SAVE 的既有 `repair_required` 事件纯预演 |
| 5 | `late-outcome-reconciliation` | 同一 Game/原请求的迟到 sentinel 后态有界核对 |
| 6 | `finance-policy/factiongift` | 派系赠礼纯选择与精确 Fraction 排序 |
| 7 | `finance-policy/feastbudget` | 宴会资金、四类承诺与军费约束 |
| 8 | `finance-policy/feastvalue` | 宴会资源和纯价值分支 |
| 9 | `finance-policy/jointbudget` | M5 已评估候选预算、冲突和稳定排序 |
| 10 | `governance-policy/crownauthority` | 王权升级纯选择、最终许可和合并报价 |
| 11 | `governance-policy/education` | 家族教育输入组合与效果来源投影 |
| 12 | `governance-policy/marriage` | 默认婚姻候选过滤、排除与排序 |
| 13 | `governance-policy/heirpreference` | 第一继承人偏好与稳定选择 |
| 14 | `governance-policy/lifestyle` | 最低生活方式和首个 focus 规则 |
| 15 | `governance-policy/lifestyleperks` | V3 perk 选择、原 catalog 和 typed delegate |
| 16 | `event-policy/mandatorychoice` | 强制选项候选、实例与原显示顺序 |
| 17 | `event-policy/interactionfallback` | 通知左侧回退、禁用/不可用与已审来源 |
| 18 | `event-policy/vanilla` | registry 选项投影与显示映射核对 |
| 19 | `military-policy/declarationpriority` | 宣战目标优先级及实际 consumer 稳定选择 |
| 20 | `military-policy/defenderrisk` | 防御战争继续风险的只读包络 |
| 21 | `military-policy/projectedcontact` | 同帧接触观测选择、原生字段与数组顺序 |
| 22 | `military-policy/battleretreat` | 当前战斗撤退预算与原生合法性纯评估 |
| 23 | `planning-runtime/optionalcadence` | 可选查询节奏、同帧去重与 episode 隔离 |
| 24 | `planning-runtime/campaigncadence` | 月度评分日历、边界与推进 cap |
| 25 | `planning-runtime/warquerycadence` | 战争结束条件查询节奏与变化失效 |
| 26 | `planning-runtime/opportunity` | 已观测机会归一化、冲突和选择 |
| 27 | `planning-runtime/swayreuse` | Sway 空槽和来源绑定机会复用 |
| 28 | `admission-contracts/cold` | 当前正常 preflight 合同与完整纯比较 |
| 29 | `admission-contracts/ownerprepare` | 原 owner 的五字段配置、角色与 argv 合同 |
| 30 | `admission-contracts/batchtiming` | RPC 汇总、序号去重、区间并集与残差 |
| 31 | `admission-contracts/deadlinecredit` | 活跃 campaign deadline 纯配置与 endpoint 判定 |
| 32 | `admission-contracts/closedpartial` | 失败部分批次的 source-bound epoch / basis 前置证明 |

`build-tools` 的 Java 构建/进程/服务 owner、Java CI bootstrap 为额外支持线，未计入上述 32。公共 POM、Git、Game、NEXT 与 canonical writer 由 Root 统一协调；Maven 只有一个 writer。`closedpartial` 单向依赖 `closed-failure-recovery`，后者通过 verifier port 接收前置证明，不反向依赖，不形成循环。

## 交付与验收

每条线分别记录 `SOURCE_READY`、`JAVA_VERIFIED`、`CONSUMER_ADOPTED`。源码和原 Python 样本完成不等于 Java 已通过；Java 通过也不代表真实消费者已接管。默认 JUnit 读取提交的原 producer golden，不依赖个人临时 Python 文件；一次性采样保留实际原生产者与全部依赖 SHA、时间及机器。合成样本和真实故障投影必须明确标注，重编码投影不冒充原始回执。

先冻结完整模块再编译，避免同一 module 源码边写边验证。Root 按已冻结包分批纳入 reactor；未纳入的独立包不污染当前 reactor 来源闭包。golden 采样通过共享受管进程顺序执行，和唯一 Maven 窗口协调；不同时启动几十个 JVM。所有依赖、构建、TEMP 和 JNA 临时写入获准工作盘，按统一存储策略实际核对容量及期限。

新 wire 严格验证 token、必填/可空/可扩展范围和整数域。旧 SDK 可扩展容器只投影已定义字段，不能套新 exact-key 集合误拒合法扩展。严格拒绝旧 bool/float 等类型替身时记录兼容差异，不用强转掩盖；Decimal、Fraction、原生整数宽度各用其真实算法，不一律换成 double 或 signed long。

通过差分的纯叶接入同一个宿主/应用端口；旧原生观测、唯一提交者、锁和实际后验继续保留。不得为每条纯函数增加 HTTP 往返或另一个动作 writer。达到可运行闭环就实测，不等全部 32 条完成才切换。修改 SDK/cold/warm 合同仍执行对应完整 CI 命令组及独立 continuation。

## 当前已经证实的范围

`machine_id: xenoamess-full-tower-eb9d2c1186`；2026-10-22T13:27:06Z，`D:/codex-ck3-demos/2026-10-22-java-phase1/logs/build-java03.json` 记录四模块完整 Java `verify`：contracts 11、native-diagnostics 16、war-policy 71，共 98 项 JUnit，零失败/错误/跳过；44.244307 秒，Job 最终 0，峰值 839561216 B。它不包含上述新一批 32 叶的编译信用。

既有 Java map 已在 N46 实际接入，原生时钟随后失败且无新 SAVE，见[实机与闭场证据](ck3-native-ai/evidence/java-map-n46-live-cutover-and-clock-failure-20261022.json)。本轮新增叶不能据该切换继承实机资格；30 年、G2 M6/M7、1 秒/日仍按真实保存进度和原证据评价。模块数与并发数不作为游戏能力或效率成绩。

本清单按 `record` 于 2027-04-20 复核归纳；工作包容量和机器资格各有独立有限期限，不因文档期限自动续期。
