# G2 非战争方向休假交接（2026-09-28）

> 2026-10-03 授权更新：项目所有者已撤销非战争限定、战争停研及战争只能由另一维护者承担的后续约束，全面授权战争原生研究、实现、bridge/MCP、策略、战斗执行与实机验收，并允许按候选需要启用战争执行开关。历史 OFF/false、零动作、readiness、计数、失败与证据哈希仍是当时事实，授权不等于能力完成。正式测试仍沿 Robert（actor29829）唯一原始 campaign 及合法继承，先研究原生 AI、绑定 exact build，并保持最小化后台运行与 noFocus。 本文件保留 09-28 交付快照；下文旧分工不能作为继续停研或仅消费战争模型的指令。

> 截止：2026-09-28 09:40（Asia/Shanghai），R0269 已完成、进程已回收。接班时以本文件的证据定位为入口，再读取 [G2 验收合同](g2-requirements-v1.json)、[当前包状态](../project-state/current-state.json)及其声明的本机 live source。文档中的 PID、owner 与远端 HEAD 均是记录时快照，不能代替接班时的实时核查。

## 1. 本轮交付与真实能力边界

本次收尾没有新建功能工作包。已完成的在途工作包括：R0268 Robert 正式续跑与 H3326 原件配对、#434 文档/状态线性集成、生活方式重心切换价值核查、和平囚犯释放场景核查，以及已冻结 H3326 候选的 R0269 有界运行与 H3388 原件配对。R0269 的最终结果见下节。没有独立后置的 typed 动作不得算作新增自动决策；静态合同、只读候选与 CI 通过不得换算为实机闭环。

现有局部能力仍可复用：旧 R0186 的 `professional_workforce_perk` 花点并在 R0187 冷恢复读回；本次派生 R0263/R0265 的首次 `martial_authority_focus` typed 动作与新 PID 冷恢复；旧 R0081 的私有首笔建设开工/回执/恢复；正式主线首继承人 38822 与 38718 的已成立订婚及冷恢复。它们均不自动满足完整 M4/M5 条件。R0268 的三个囚犯只读 v5 证实都不是玩家子女，未释放任何人。

## 2. Robert 原件、运行现场与冻结制品

| 项目 | 接班值与边界 |
| --- | --- |
| 正式主线 | 1066 Robert 及合法继承，profile `ordinary_campaign_succession/xar_off`；不计旧 Murchad、派生试验或重放日期。 |
| R0269 来源 | H3326/raw53218776，持久 **3,102/36,524** 天；[原件配对](Z:/h3326-source-freeze-20260928/PAIR-IDENTITY.json) SHA-256 `C62C55A75693C6300D4F03AD1848DB285452D5597FFA4D60A2A96A6B8B8733F3`，官方 family pair、rebind、no-launch 通过。 |
| R0269 候选 | 来源 master `98be42250294cbf88a9f0e1e0c0518de72264ccc`，官方 CI `36364662653` SUCCESS；[候选索引](Z:/h3326-nextcandidate-20260928/H3326-CANDIDATE-INDEX.json) SHA-256 `87ACF80E821F81DE093E2EBC7BE4634A4FDC499789F892EF11B656997A5D33AD`；Release DLL SHA-256 `87AD7A8A8E8A9D1113E0938D2532C7B456570C28EAC4A1ABBD75310A15F60AAA`。本机 operator 预检 21/21，已由正式分配器分配完整 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0269`；运行期间本机唯一 CK3 窗口保持最小化，结束后已清空。 |
| R0269 最终 | [正式报告](Z:/h3388-source-freeze-20260928/evidence/formal-report.txt) SHA-256 `310F673EC9D13DD4DC2F6250B5773D41830AB1D3C0772CAFAF255936D7F1F8C0`：36/36 `turn_limit/qualified`，25 query、11 gameplay、3 checkpoint，operator exit0、canonical `completed-green`、无 RED。H3388/raw53218968 比 H3326 增 8 个持久 Robert 日，累计 **3,110/36,524**。M5 35/35 仍为 `incomplete_war_cash`，无新增非战争 typed 动作；WarID 16777231 仍 active。 [operator 回执](Z:/h3388-source-freeze-20260928/evidence/operator-receipt.json) SHA-256 `4CC944A4B1F57D8E5081EC1C3E1F20C8BE1D5890D197AD7E9CB4E153315A2577`。 |
| 下一合法来源 | [H3388 原件配对](Z:/h3388-source-freeze-20260928/PAIR-IDENTITY.json) SHA-256 `C8E0064F1324C848E0B166689D0EDEB66F7C3B07068022FF592AA54F052DAB5A`，15 个固定文件哈希匹配；save `9FC52CD2E59F65683FBDACF71FA46DDEB25F60E32606CF9DC60D361EBBEC1B17`、driver `99C58301C212ABCDBBEDD74D92AE74FCFE23719B927377C93FE7C7D0F54C5C50`、完整家庭 sidecar `C5B0E9AF69928003F3AF34FAC05240E384BDEA44A9C4227CA66BC269F2979AEC`，DLL 仍为上行 `87AD...AAA`。官方 family pair、rebind 与 no-launch PASS。接班者仍须为自己的候选做官方配对、no-launch、实时 operator 预检及新轮次分配；不得沿用本轮已加载配置热换 DLL。 |
| 实时实例 | 收尾时 `operator_get_status` 显示 R0269 job `exited/exit0`、CK3/injector 均空；随后核验本机 CK3/injector/operator job/server 进程及端口 8766 均为 0，无窗口占用，canonical 状态 `completed-green`。下一执行者仍须重新实时核 owner/RED。本机 MCP 只管理本机实例；每台运行机器各自部署 MCP、各自最多一个 CK3，不调用另一台机器的 MCP。 |

R0269 的正式 job 为 `robert-h3326-nonwar-prisoner-m5-observation-36`，唯一窗口请求 `robert-h3326-87acf80e-20260928`。现场在 `Z:\h3326-nextcandidate-20260928\run-formal-36`；状态源在 `Z:\ck3_mod_rewrite_process_assets\g2-live-run-ids-v1\xenoamess-full-tower-eb9d2c1186\eternal-recurrence`。operator 本机状态源以 `operator_get_status` 为准；仅有文档中的旧 PID 不授权启动。本次在最小化期间，driver 历史与正式 turn 连续写入，日期在可推进阶段增长；最终 job 完成后已清空本机 CK3 与 operator 进程。后续运行仍须用心跳、turn 回执及应推进阶段的日期核对后台进展。

## 3. 未闭合的真实消费缺口

| 包 | 已证实事实与下一次可施工入口 |
| --- | --- |
| NW-LIFE | R0268 Robert 已有 `stewardship_wealth_focus`，管理 XP raw65,000,000、可用点数 0；`martial_authority_focus` 原生最终判定合法，但军事 XP raw0、可用点数 0。现有正式策略只给无 focus 角色做首次选择，已知 focus 不重投。缺少未来 60 个月目标 XP/战争收益相对财富 +10% 收入和切换成本的净值，故本帧**没有已证明应切换而漏提交**。继承后首个可操作帧已有开局 gate；尚无自然继承下的完整新角色阳性。 |
| NW-ECON / NW-JOINT | R0268 同帧 `farm_estates_01` 是合法战时只读候选，成本 raw18,000,000、现金 raw111,925,059、定义月收入增量 70 百分之一；M5 turn2–36 **35/35** 判 `incomplete_war_cash`、`formal_action_ready=false` 并保留战争步骤。缺 `pending_war_cash_raw`、`immediate_war_action_cost_raw`、`future_war_cost_upper_raw`、`future_risk_budget_raw`、`policy_minimum_gold_reserve_raw`、`horizon_days`、`future_bound_assumptions`。这些值不能填零；没有扣款、开工、完工或收入收益。既有和平建设动作不因这个战时比较被全局关停。 |
| NW-FAMILY | 首继承人订婚已成立，家庭 sidecar `pending=null`；双方仍未结盟。现有消费者避免重复提案；当前无可证实的新婚配漏消费。下一位未婚继承人出现真实竞争候选时，核本人提案资格、宗族归属、接受条件与长期义务，再提交并独立验证。 |
| 囚犯/其他 | WarID 16777231 现有三囚犯 34486/44484/47028 的赎金为 `option_unavailable`；R0268 亲子谓词均 false。战俘保留条款仍未知。master `98be422` 新增的 `prisoner_war_retention.py` 是只读 Python join，尚无通用原生 PoW 数据源或正式 caller；现有释放动作核心也缺生产 exact command adapter。有证据的三囚犯帧均在战时，旧和平 h115/h133 无囚犯集合，故没有可证明的和平释放漏消费。不要仅凭释放的原版 +20 好感推定当前净收益。 |

2026-09-28 当时由另一机器的战争维护者承担研究，本执行者只消费已交付模型/资源输入，`COMBAT_ENTRY_EU_ACTIVATION_ENABLED=false` 是当时合同状态。2026-10-03 所有者已撤销该后续分工限制，本执行者可以研究、实现与验证战争模型、资源观测、策略及战斗执行，并按冻结候选配置启用该开关。Git 跨机器需求通道为 [war-requests/README](coordination/war-requests/README.md) 下的 `requests/`、`responses/`、`evidence/`：已提交 [同帧战争现金请求](coordination/war-requests/requests/WAR-ROBERT-R0266-JOINT-CASH-20260928.json)及[静态接口回应](coordination/war-requests/responses/WAR-ROBERT-R0266-JOINT-CASH-20260928.json)，回应的 `live_evidence=null`，不能据此批准建设。[囚犯保留请求](coordination/war-requests/requests/WAR-PRISONER-RETENTION-H2825-20260928.json)仍需原生通用数据源及正式接线；新源码在当前候选中未生产有效战俘配对。接班时先读最新 master 增量和同一请求的新增回应，不重复建请求或用本机 MCP 访问对方机器。

## 4. 制品传输、保护范围与状态门

PRV008 冻结 ZIP `g2-preview-ordinary-h1662-ca852d1-prv008.zip` 的 SHA-256 是 `B9952E544C78D51F650FCBF252D2DE81B1E005B0EA5081880AEE9FDECC2BD9F3`；本机 OneDrive 副本在 `C:\Users\xenoa\OneDrive\PRV008-frozen-preview-2026-09-28`，与原件逐项核对。另一机器的实际可读路径和哈希回执**未收到**，不能声称已跨机交付。原始 release、`START-HERE.txt`、`QUALIFICATION.json` 与 `Z:\ck3_mod_rewrite\.task-tmp\PRV008-FROZEN-EARLY-PAIR` 必须保留；资格只覆盖旧 R0074 派生 actor31853 的普通封建有界预览，未证明自然继承或任意存档。Robert 新候选与 PRV008 无共同制品资格。

H2825 的原始 save、driver、完整 sidecar 与对应 DLL 已经由战争同事在另一机器哈希核对，接收目录为 `D:/ck3-research-artifacts/war31-h2825-20260928/source-verified-01/`，见[接收记录](../ck3-native-ai/h2825-onedrive-exact-input-2026-09-28.md)；不再把本机 OneDrive 的 Sync pending 误写成对方未收到。

[G2 合同](g2-requirements-v1.json)仍为 **3/8**：M0/M1/M3 complete，M2/M4 in progress，M5–M7 not started；百年 **0/1**、首整局 **0/1**、独立种子 **0/2**。不计算总体百分比，不以候选、查询或单次局部动作提升完整里程碑。正式主线最后持久 H3388/raw53218968，**3,110/36,524** 日。

## 5. Git、工作区与接班顺序

#434 的 R0268/H3326 日报、W40 和状态投影已线性合入 master `d96c4ba503eaeb69ea20011d2732541e4dd19e79`，exact-master 官方 CI `36365781462` SUCCESS，远端/本地临时分支及 `Z:\r0268-h3326-docs-20260928` 源码 worktree 按核验 tip 清理。**本交接文档的最终提交、master 和官方检查以合入后的 Git/CI 回执为准，文件内不预填自身 SHA。** 根目录 `Z:\ck3_mod_rewrite` 是历史脏现场，禁止 reset、全量 stash/clean。所有新临时源码/构建/cache 放实际非 C 盘；OneDrive 的 C 盘路径仅是用户指定的文件交付目的地。

状态投影本轮无验证参数渲染 GREEN，`tools.test_project_delivery_state` 普通与 `-O` 各 6/6 通过。`render --verify-artifacts` 被早期 R506 的 `Z:\_runtime\p2-endgame-source-r505-r506-3f7b8e7-20260912\live-artifacts\af5-red.json` 缺失挡住；这不是 R0269 新证据失败，也未据此改写旧 RED。R0269 原件另由正式配对、15 项 pin 和本机报告核实。

先前 #421/#424/#427 等部分源码 worktree 或临时缓存的清理被自动审批以 `blocked by policy` 拒绝，保留原状，**不能换工具绕过**。接班者可依据原包记录和最新审批策略处理；这些包不因远端合入而被写成完整 DONE。冻结运行资产和不可变证据独立保留，不按 `.task-tmp` 名称删除。

下一执行者先按本机 `operator_get_status` 核实际实例/owner/RED，再用最新原始配对和新冻结候选执行官方 no-launch；在源码层面先处理真实观测缺项与可行动机会。按真实战争与其他可行动机会推进；当前任何模态事件实际挡住操作时均可提为 P0。约 30 分钟在安全边界同步 master，并只重验受影响接口。每个新增动作都需要独立游戏后置、下一 turn、规定的 checkpoint 与新 PID 冷恢复。战争模型与 PoW 原生数据源可由本执行者研究、实现和实机验证，也可通过 Git 请求/回应协作；不由本机跨机调用对方 MCP。

本次 H3326 候选源码 worktree `Z:\h3326-nextcandidate-20260928\src` 在 R0269 终止、H3388 配对完成后核查为 clean 且无独有提交；本地临时分支与 worktree 已移除，远端同名分支不存在。候选索引、正式报告及 H3326/H3388 冻结运行资产均保留。
