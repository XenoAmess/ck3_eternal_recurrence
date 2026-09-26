# G2 非战争方向交接（2026-09-26）

记录时间：2026-09-26 13:40（Asia/Shanghai）。本次是现状核查与研究队列调整，没有新增 CK3 轮次、动作或日期证据。

## 1. 接班结论与职责

项目所有者最新指令：**战争由其他同事研究；本执行者定期同步 master，使用已经交付的战争能力，优先推进非战争方向。** 此指令更新本执行者的工作分工；战争仍可能阻塞正式长跑，但不再占用本执行者的模型、伤害公式、路线或投降条款研究队列。

非战争主线按可见收益排序：**及时使用生活方式 → 建设与经济增长 → 婚姻及继承安排 → 同帧资源分配**。实际阻塞操作的非宗教事件优先处置；议会、派系和事件的自然阳性随正常游玩收集。谋略、囚犯、法律与活动只在前述工作释放容量或出现当前主链 B0/B1 时承接。

本次只交付分析和接班入口。下表是待接手工作包，没有声称已经启动新的实现、worker 或实机任务。战争维护者的具体任务 ID、当前 owner 和运行状态未在本轮核实，不能把历史进程清零记录当作可启动许可。

## 2. 核实基线与证据口径

- 实际远端 `master`：`1b57b3301b87231b2b71eeae9edc44e20ee01a33`，提交 `Integrate-bounded-whole-battle-forecast-into-war-strategy`。这是本次分析基线，之后集成时仍须 fetch/rebase。
- [G2 权威合同](g2-requirements-v1.json)：**3/8**，M0/M1/M3 complete，M2/M4 in progress，M5–M7 not started。不得换算整体百分比。合同中的部分 `open_blocker` 文本保留旧轮次，具体最新闭环要追到下列增量及不可变证据。
- [稳定状态投影](../project-state/current-state.json)用于包状态；当前 PID、owner、RED 要读取该投影声明的 live source。本轮未重新盘点全部受管环境，当前轮次与实例状态写作**未核实**。
- [09-24 交接](2026-09-24-g2-simulation-provisional-handoff.md)最近记录的正式 Robert 主线为 `h2134/raw53215920`，持久 **2,983/36,524 游戏日**；百年门 **0/1**，首整局 **0/1**，独立种子 **0/2**。这是文档证据基线，本轮没有新增日期。旧 Murchad 的 9,482 天及研究重放不得并入 Robert。后续仍从用户指定的 1066 罗贝尔主线及其合法继承延续，不重新换回穆尔哈德。
- CK3 仍以 `1.19.0.6-steam23530548`、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 为既有证据版本。新 live 前实际核验 EXE/DLL/profile/save/driver，不把本轮文档核查当作 no-launch 通过。

### 冻结预览仍单独保留

PRV008 的历史窄范围 GO 未变化：`g2-preview-ordinary-h1662-ca852d1-prv008.zip`，SHA-256 `B9952E544C78D51F650FCBF252D2DE81B1E005B0EA5081880AEE9FDECC2BD9F3`；智能体 `ca852d1d5b368d951a392928907c642e6b325b3c`，DLL SHA-256 `B114FD8E13AF6518D623A60E7264807D882E4F4A640AF7840F60BA3F00029FA8`。

09-24 已复核的本机交付位置为 `Z:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-ca852d1-20260922\release`；已验证命令只从 `Z:\ck3_mod_rewrite_process_assets\g2-preview-prv008-frozen-path-live-20260922\START-HERE.txt` 与 `QUALIFICATION.json` 读取。必须保留 `Z:\ck3_mod_rewrite\.task-tmp\PRV008-FROZEN-EARLY-PAIR`。本轮未另测下载渠道，不能声称其他机器已可访问这些路径。

资格限于旧 R0074 派生普通封建 actor 31853 / episode `native-31853-af642d76cb41` 的有界路径，加载仅 `mod/xar_autoplayer.mod`，profile 为 `ordinary_campaign_succession / xar_off`；该路径未发生自然继承。任意存档、无限无人值守、完整 1066→1453 和双种子仍未取得资格。新 Robert 候选、生活方式改动或新 master 均使用独立资产，不能覆盖此预览或沿用其资格。

## 3. 非战争工作队列

下列包由非战争接班人承接；每次只将依赖满足的包标 READY。待自然场景的包不计为正在工作的 worker。原生决策树与 exact-build 证据先于策略变更；复用已经实现的查询、动作和恢复入口。

| 顺序 / 包 | 已有成果及真实缺口 | 下一项有界交付与验收 | 依赖 / 状态 |
| --- | --- | --- | --- |
| P0 `NW-LIFE`：生活方式机会消费，M4 | R0186 已实际取得 `professional_workforce_perk`，点数 2→1、已用点数 5→6，并消费 receipt/checkpoint；R0187 新 PID 读回该 perk 与 `stewardship_wealth_focus`。当前策略仍是管理学财富与少量 perk 路径；开局 focus gate 是 opt-in。不能再描述成“完全没有生活方式能力”。 | 先追踪正式启动参数、开局与继承后调用顺序，定位是否遗漏 focus/点数机会；保留已有门与 receipt。随后按教育、角色条件、当前目标和原生合法性扩最小选项集合。新角色首个可操作帧检查 focus；可用点数及时评估；已有有效 focus 不重复提交。用目标 XP、点数、所选 focus 的前后读回说明实际收益，不能由人物年龄推断没吃经验。每次新增动作须独立后置、下一 turn、配对恢复。 | 源码追踪与最小策略研究可立即做；只验证实际变更。live 使用独立匹配候选。公开能力及 M4 两年门仍未关闭。 |
| P1 `NW-ECON`：建设与财政，M4 | R0081 已闭合私有建设提交、物质 receipt、新 PID 恢复及下一 turn。既有 native 成本/合法性和排序可复用；完整收益、回本与持续治理缺口仍在。 | 让实际可负担的经济建设进入正常机会评估，记录成本、工期、储备和可读收益；先用已有政策执行有收益依据的一项，再用完工/收入/建筑效果读回校准。补当前决策真正缺少的收益字段，避免为了完整 ROI 模型长期不建设。验收包括同一槽位、扣款、施工/完工实际状态及后续消费。 | 可独立准备；战争现金/军队占用读主线现有合同。战争远期成本缺失只限制相关比较，不能禁止全部和平建设。 |
| P1 `NW-FAMILY`：婚姻与继承价值，M5 输入 | 657 个 final-legal 候选是库存；R0133 五候选投影的 8 个 potential pair 均 `would_attempt_if_accepted=false`，没有可据此宣称的联盟收益。 | 扩既有五候选投影，区分成人婚姻/订婚、父系母系、实际配偶及联盟双方、继承/宗族价值、接受条件与长期义务；先补最有价值合法候选的真实结果，再与替代候选比较。经正式策略提交一个 proposal，独立读回实际婚配/联盟结果、下一 turn 和恢复。 | 已有 reader/classifier 可复用；无需增加候选数量。首继承人动作不能用玩家本人动作资格代替。信仰只读婚姻所需原生最终判定。 |
| P1 并行 `NW-JOINT`：非战争提案估值与资源分配，M5 | `m5_joint_budget_selector`、`m5_joint_dispatch`、`m5_joint_shortlist` 及 proposal collector 已存在。09-24 短名单仍 `selected_step=null`、`formal_action_ready=false`；缺真实收益/长期义务与正式消费。 | 为生活方式、建设、礼金、婚配的已有提案补同帧、同版本价值政策和资源承诺；复用现有选择器，仅预留一次金钱/角色/盟友等资源。聚焦验证真实候选比较、资源冲突、正收益可行动情形，随后接一个正式消费者及动作闭环。正式 M5 至少五个真实候选的合同不改。 | 非战争投影与接线可并行；战争提案、未来补给/战役成本由战争维护者从 master 提供。缺失字段保持明确缺项，不填零、不伪造。独立域动作按自己的合同继续。 |
| 实际模态阻塞时 P0，否则 P1 `NW-EVENT`，M2 | `death_management.1007` exact no-killer 门已由 R0126 完成；`.0110` 原差值跨 15 天，因果未闭合；`.0030` 在普通封建主线不适用。无效果单选通知消费已获用户授权并有既有实现。 | `epidemic_events.0110.c` 行动前保存将被清掉的 county 列表，同日期近邻后置读取 county modifier 与 legitimacy，分开事件效果和时间流逝；复用现有私有 observer。新阻塞事件按原版定义最小扩注册/consumer。将 `tgp_travel_events.0030` 留在后续 TGP/天朝政府专门场景队列。 | 只在自然合法场景验收；不重做已闭合 `.1007`，不强制触发、不切当前主线政府/DLC。通用无效果确认不授权展开宗教策略。 |
| P1 场景机会 `NW-COUNCIL` / `NW-FACTION`，M4 | 议会仅 already-councillor 1/4；guest/pending/replacement 缺自然阳性。派系已有私有 gift/pending/recovery 模块，count=0 只说明空场景；正式消费者及实机干预尚缺。 | 议会复用受控 runner，读出候选/现任/待命关系，场景成立才任命并核下一 paused incumbent、下一 turn。派系沿已有 native gift 路线补实际消费者与冷恢复读回，核金钱、目标 opinion、派系状态；不能以 ACK 或派系消失单独判断礼金成功。 | 先筛已有证据与正常游玩快照。没有阳性则登记等待，不开永久专题长跑。各项公共 query/action/ad 依原合同保持 OFF。 |
| P2 `NW-INSTITUTIONS`，M6 | 谋略已有私有 semantic action、binder/harness；活动已有 static-ready application glue；这些不等于正式能力全无，也不等于 live。 | 优先当前主线实际可用的囚犯赎金/释放、关系谋略、非宗教决议/法律或活动之一。复用各层，补真实调用与独立状态变化，再扩生命周期。活动现有 glue 仍需 final evaluator/语义操作和私有调用入口。 | M6 仍 not started。前列工作未释放容量且没有实际 B0/B1 时，不铺开新矩阵。 |

生活方式的具体源码入口为 `ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py` 的 `require_initial_lifestyle_focus_before_date_advance` / `allow_private_lifestyle_formal_trial`，以及同目录 `lifestyle_min_policy.py`、`lifestyle_formal_consumer.py`。当前最小政策还包含 `centralization_perk` 分支；有代码分支不代表该 perk 已实机闭环。接班先核调用及触发条件，避免重建已存在的开局 gate。

M7 的跨身份/政府目标延续与第二独立种子仍保留合同要求。M3 已 complete，旧自然继承成果继续复用；Robert 新主线和非战争新能力需要自己的适用证据。百年、整局、双种子是正式持续运行门，不拆成新的永久专项跑。

## 4. 战争能力如何跟随 master 使用

[09-26 主线战争接线](../ck3-native-ai/general-battle-strategy-forecast-2026-09-26.md)已把现有整场研究模拟接入 `choose_one_life_turn`，和平宣战也已有聚合代理试算入口。允许使用带假设、来源与风险预算的现有模型，不等待整套模拟完全精确，不另设固定 2 倍兵力门。静态接线通过仍不能声称当前实机已完成新的宣战/接战及战果回读。

本执行者的责任是兼容与消费：核对主线实际公开的输入、版本、同帧绑定、资源占用、pending/receipt 和错误结果；记录使用结果并把可复现缺口交给战争维护者。模型拟合、增援/撤退/事件公式、战争路线及退出观测由对方继续推进。`COMBAT_ENTRY_EU_ACTIVATION_ENABLED=false` 是另一套正式效用合同状态，不能据此关闭已经接入的有界模型路径。

同步执行规则：

1. 每个工作包开始、候选构建/实机冻结前、提交集成前，`git fetch origin master`，核对远端 exact SHA；隔离工作区只用 rebase 跟进，禁止 merge 与 force-push。
2. 持续工作期间约每 30 分钟在安全边界检查一次远端增量；只处理影响当前包的接口/策略变化。此为接班操作约定，本次未安装后台同步服务。
3. 已运行实例与冻结候选保持原 DLL、参数和加载环境。主线更新先进入下一候选；不在 CK3 存活时替换加载文件。Python 热恢复只用项目已有支持的正式机制。
4. 上游接口变化只重验受影响的非战争适配；缺少战争远期成本时，记录该条联合提案缺项，继续生活方式、建设、婚配等独立研究。需要战争实机解阻时进入现有单实例队列，不抢占正常运行。

## 5. 原生研究与证据入口

| 方向 | 接班应读的已有入口 |
| --- | --- |
| 生活方式 | [原生树及开局顺序](../ck3-native-ai/lifestyle-focus-perk-ai.md)、[professional workforce 读回](../ck3-native-ai/lifestyle-professional-workforce-readback-entry.md)、[W39 的 R0186/R0187 增量](weekly/2026-W39.md) |
| 建设 | [建设原生树与收益缺口](../ck3-native-ai/domain-construction-ai.md)、[G2 合同的 R0081 闭环](g2-requirements-v1.json)；原生树末尾旧 live-pending 不覆盖后来 R0081 的窄资格 |
| 家庭 / 联合调度 | [同帧调度及 09-24 短名单](../ck3-native-ai/m5-single-frame-dispatch-2026-09-22.md)、[实际机会调度](../ck3-native-ai/m5-observed-opportunity-dispatch-2026-09-23.md) |
| 事件 | [0110 近邻配对库存](../ck3-native-ai/m2-0110-near-pair-inventory-2026-09-23.md)、[county modifier observer ABI](../ck3-native-ai/m2-0110-county-modifier-observer-abi-2026-09-22.md)、[0110 原版效果](../ck3-native-ai/epidemic-events-0110-recovery.md) |
| 议会 / 派系 | [四门受控验收](../ck3-native-ai/council-four-gate-controlled-rejection.md)、[gift 正式路线缺口及后续修正](../ck3-native-ai/faction-gift-formal-route-gap.md) |
| M6 | [谋略私有动作](../ck3-native-ai/active-scheme-semantic-action-v1-private.md)、[活动应用层接线](../ck3-native-ai/activity-planning-application-glue-1.19.0.6.md)、[囚犯/犯罪/赎金](../ck3-native-ai/prisoner-crime-ransom-ai.md) |

关键复用证据：R0186 `g2-m4-professional-workforce-typed-r0186-live-20260923/report.json`，SHA-256 `656BABEE8CCB58FD69D30EF84782C95F331D5109482F9A2E5320E40FA2F98D58`，位于本机 `Z:\ck3_mod_rewrite_process_assets`；R0081 manifest SHA-256 `ED175A02101C73AD8E0B5765EBF52397154EAA134CB54974D4AE84988B8BDAA2` 见合同。它们支持相应的私有局部门，不能作为所有 M4 能力公开的依据。

## 6. 接班顺序、资源与本包交付

1. 接班先读取最新用户指令、master 增量和任务总线；确认战争维护者的当前接口/实例占用。非战争首包从 `NW-LIFE` 的正式入口与机会触发追踪开始，产出实际漏消费条件与最小改动范围；已有正常路径直接复用。
2. 有安全独立槽位时并行准备 `NW-ECON` 与 `NW-FAMILY` / `NW-JOINT` 的真实收益输入，按文件写入权隔离。没有自然阳性的议会/事件保持待场景，不计占用；不为研究启动 CK3。
3. 仅当对应候选已满足官方配对/no-launch 与自身验收边界，才申请现有唯一 CK3 窗口；启动前核对全部受管环境进程树与 owner，轮次由持久分配器分配。原战争 RED 未解除时不声称正式百年恢复，独立非战争验收照依赖排队。
4. 每项新能力按真实观测 → 策略选择 → typed 动作 → 独立后置 → 下一 turn → 合同要求的 checkpoint/恢复交付。已完成静态或局部门只补受影响项；无日期/动作的证据明确写只读。

本次登记：

| 项目 | 记录 |
| --- | --- |
| ID / 负责人 | `G2-NONWAR-HANDOFF-20260926` / 当前协调者 `/root`，仅文档写入者 |
| 隔离原因 / 基线 | 根工作区为历史脏现场；从 `1b57b3301b87231b2b71eeae9edc44e20ee01a33` 建立隔离源码工作区，不覆盖根目录 |
| 分支 / 工作区 | `wip/nonwar-priorities-handoff-20260926`；`Z:\ck3_mod_rewrite\.task-tmp\G2-NONWAR-HANDOFF-20260926\work` |
| 写入边界 | 本交接、进度导航、09-26 本包计划/日报、W39 增量；交付中实际遇到 Windows CI checkout 长路径失败，附最小 Git 作业环境修复。不改里程碑定义、状态分母、游戏代码或冻结制品 |
| worker / 实机 | 本包实际一个文档执行者；本轮未新增子 worker。其他团队容量与在途工作未知；本包不占 CK3，不分配运行编号 |
| 非 C 盘 | 本包源码、TEMP/TMP、缓存均在 Z 盘；已检查目录可写及空间。任务总线已有本机映射 `Z:\.codex-task-bus`，不机械使用失效的 D 盘安装路径 |
| 验收 / 期限 | 文档链接、引用与 diff 检查后立即 commit/push；按保护检查线性集成。exact master 官方 CI GREEN 后清理本包远端/本地分支与临时源码 worktree；实际 SHA、CI 与清理结果写最终交付回执，不预填 DONE |
| 资产保留 | PRV008 ZIP/说明/配对、Robert 与战争原始/派生配对、M4 制品、不可变证据均原地保留，由对应运行负责人维护；本包没有新运行资产 |

下一次汇报分别说明：PRV008 可获取性与边界；上游战争交付/运行阻点；本包新增证据属于源码、no-launch、只读、动作或持续运行哪一层；G2 计数、Robert 持久日期、阶段门与种子各自数值。未知项保持未知，不提供未经实测的新交付日期。

### 交付中发现的 CI 环境阻塞

首份文档提交 `db3927d6cb4e6ce34722be5a440520151147770c` 已推送至 PR #244；官方 push CI `36221771531` 与 PR CI `36221787656` 在 checkout 阶段 RED。日志明确为既有 `promo/ck3_native_war_ai/.../artifacts/project-config/sha256/...json` 的 `Filename too long`，尚未进入测试。交付附带的最小修复是在 `static` job 使用进程环境 `GIT_CONFIG_COUNT/KEY_0/VALUE_0` 设置 `core.longpaths=true`，不改全机配置或移动制品。原失败保留，修复后的官方结果见最终交付回执；此环境修复不增加任何游戏能力证据。
