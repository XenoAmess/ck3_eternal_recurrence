# 《战斗后半笔账》研究与智能体共用计划（2026-09-26）

本计划对接 [系列下一期](../../promo/ck3_native_war_ai/series-roadmap.md)与[有界整场策略估计](general-battle-strategy-forecast-2026-09-26.md)。目标是让每个片中计算都能回到确切原版 CombatID、同日输入、逐步整数计算、次日/终局状态；同一计算及其证据也进入游玩智能体。`planner_usable=false` 表示原版整场逐日同构尚未证成，不再作为禁用已有有界估计的理由。每个历史 RED 和独立回放保持原身份，不拼接为同一随机轨迹。

## 跨任务战争请求优先队列

按用户 2026-09-27 指令，[战争请求目录](../autonomous-agent-progress/coordination/war-requests/README.md)中的新请求优先于本计划下方的独立研究。活动研究期间每次 15 分钟任务总线 heartbeat、每次提交前，以及每个长时间实机尝试之间，先 `git fetch origin master` 并从远端 `master` 的 `war-requests/requests/`、`responses/`、`verifications/` 复查状态；新 request 立即加入本节并处理，不能仅依赖本机通知。`R0244` 的精确 v3 查询修复 `ba623c137`、同帧首跳动作投影 `90afa9fef` 与[交付响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-INPUT-R0244-20260927.json)均已在 `master`；请求方原始 Robert War `48` 存档/DLL 仍须正式配对复验并写 verification。本机独立 War `4` 的早期夹具虽选择守住首都，[后续 067 实机复验](war-contact-attempt-067-same-frame-common-combat-2026-09-27.md)已证明同帧交互查询写入历史、合法答复解除阻断，并在第 26 天观察三支玩家军队共同进入 CombatID `2`；这仍不能代称原始 War `48` 已通过。复验若发现新缺口，立即重新提到本队列最前。

| 顺序 | 要回答的具体问题 | 当前证据与状态 | 下一道可核验门 | 产出 |
| --- | --- | --- | --- | --- |
| 1. 追击三日 | 第 28 日的 soft 如何逐团写成第 29–31 日 hard，余数落在哪里？ | **本案条件计算通过**：同一 attempt-004，24 团×3 日软伤 72/72 零差；可读逐团硬伤 69/69 零差，参战者硬伤总账 3/3 零差；第 28 日状态独立连算三日仍 72/72。见[原版回读](battle-simulation-episode01-live-case.md#2026-09-26-追击三日同一独立回放的逐团与账本对拍)。 | 换不同兵种/掩护非零/追击修正条件的独立原版战例复核，不将单例扩大为全部条件。 | 可复跑比较器、逐团报告、片用三日数字板、模拟器 golden。 |
| 2. 骑士深层抽签 | 选中事件后，谁被抽中，伤/残/死的下一抽是什么？ | 第 26 日 load index 11 `knight_killed` 的**击杀者抽签**直接复算：14 名候选中 `1,400,813,912 % 14=8`，索引 8 是 34120。[修正的原生回读](combat-phase-event-trace.md#2026-09-26-第-26-日成长随机列表的实际分支与抽签)用父作用域 seed、子作用域真实抽签 `51,510,340` 和原生子节点指针闭合成长列表第 0 项；权重 `40/30/15` 仍仅是条件推算。[第 5 日独立实采](combat-phase-event-trace.md#2026-09-27-第-5-日随机列表选择器入口实采勘误)直接回读三个列表的调整后权重 `54/30/10`、`4/2/4/4`、`40/50`，与三次实际子抽签和执行子节点匹配；前两组与现有模拟器同帧计算一致，第三组医师输入未建模。此前将两个列表的父作用域 draw 当成实际抽签的 v1 报告均已保留并标为失效。 | 在第 26 日独立回读成长列表调整后权重；补治疗医师输入、实际成长与无对手分支，并核对写回与刷新。 | 原版抽签树、可复跑本案目标选择、智能体随机核。 |
| 3. 人物与兵团写回 | 战报、trait/death、勇武、兵团韧性/伤害和对手奖励何时生效？ | 七边界与同日存档再证死亡/退出、对手威望 +150，并把 `4→2` 定位为**有效勇武刷新**，基础勇武前后均为 2。[第 27 日 v3 直接回读](combat-phase-event-trace.md#事件后的下一帧智能体输入)证明击杀从智能体输入移除 65 号兵团/33437 号骑士，余下 68 团、29 名骑士对应行相同。[独立第 5→6 日致残复载](combat-phase-event-trace.md#致残写回进入第-6-天智能体输入)证明目标 34333 保留在名册，有效勇武 `11→7`、61 号兵团伤害 `962.5→612.5`、坚韧 `192.5→122.5`，进入下一帧智能体 v3。[第 6→8 日逐日复载](combat-phase-event-trace.md#两日后治疗失败事件的原版写回)再证排队 `health.0101` 到期后写入 365 日、健康修正 -0.5 的失败治疗 modifier；本案目标 v3 伤害/坚韧没有再次改变。 | 补 full mutable write-set、重算调用时点、跨 root/side 贡献与将领替换；用受伤/实际成长分支再核，验证健康修正对后续死亡风险的作用。 | 事件回流逐日模型、伤/死状态卡和后续结算画面。 |
| 4. 增援/退出 | 到达日先合流还是先出伤、战宽与反制何时刷新？ | 两次自然增援在到达同一天已受伤；给定名单/有效属性的伤亡 38/38、42/42，反制 46/46 条件零差。新[完整七边界回放](battle-reinforcement-and-join.md#2026-09-26两次自然增援的七边界身份同日出伤与逐团写回闭合)分别以候选 ArmyID `22`、`28` 预登记 full generation，在首次 side0 phase-fire **入口前**观察原生追加名单，七条捕获标志均为 0，新增兵团 12/12 与 5/5 的同日软/硬伤亡零差；旧 RED attempt 保留历史身份。新[有效属性刷新链](battle-reinforcement-and-join.md#2026-09-26到达日首次安排事件前会重算兵团有效属性)静态闭合 `0x27FB57A` 先写伤害/坚韧、`0x27FB58F` 后安排事件，两次暂停→schedule 实机分别有 32/51、37/63 团属性变化；按原生身份分成骑士 24+27、职业兵士 8+10、征召兵 0。51 个变化骑士的刷新后数值全部满足勇武×效能×库存常数公式；骑士效能的九个原生 modifier **入口名称**也已闭合，但当时的逐项值、旧缓存变化原因仍未闭合。两个 manager 的 vtable 身份已核验，跨 manager 全局先后仍未直接实测。 | 用两个 GREEN 回执闭合 roll/event/width/counter；在同一帧采集骑士九项 modifier 值与职业兵士有效属性的修正来源；将有 route/ETA 证据的 join-day 转移接入 trial kernel，并覆盖撤退重入、第三方或另一种路线。 | 动态 timeline 输入、可重复的增援结算、片用同日对照。 |
| 5. 撤退与终局 | 谁在何时选择撤退，追击何时跳过，结果如何写入战争？ | 共用合法性与 full-/partial-side transition 静态核已闭合；墨西拿正常结果 side0 胜、玩家撤退、战争进攻方 -50 有原版回读。[实机战分对拍](battle-terminal-and-reentry.md#2026-09-26-梅西纳单场战分同一次原生-writer-的完整输入与写回)在同一 writer 读取败方八桶 `996`、CB 倍率 `150`、分子 `536.62042 人当量`、未封顶 `80.8155` 与封顶 row `50`，由[智能体共用整数模块](../../ck3_autonomous_player/src/xar_autoplayer/simulation/native_battle_score.py)复算。[独立战争解散实机回读](battle-terminal-and-reentry.md#2026-09-27-战争解散触发的无正常战果独立实机回读)再证同日 `no_normal_result`、无单场战分、旧战斗/ResultID 清理和参战军队解绑。[AI 败方完整逐日回放](active-combat-retreat.md#2026-09-27-普通战争-ai-接管后的完整战斗观察)新增 27 帧：第 0–25 帧无主动撤退，第 26 日正常败战后才撤退；同场第 6/16 日的真实 roster 尾插不重置 main day。 | 自愿撤退的通用 AI 选择/目的地另查；覆盖不同 CB/胜负、正常结果 effect、同省 residual 和 AI assignment-reopened 分支。`successor=unavailable` 不可判作无残余。 | 战斗结果状态机、战分账及下一期结尾镜头。 |
| 6. 整场分布校准 | 模拟赢/输/未决与实战误差是多少？ | 现有有界 256/512-trial 估计供策略使用，附输入哈希/假设；三次墨西拿回放都败退但非独立样本证明。 | 先将 2–5 的已验证转移接入 trial kernel；再以不同条件、独立原版战例对拍逐日与终局，分别统计采集器 RED、模型残差和抽样不确定性。 | 可供视频引用的有条件胜率及误差；更新智能体风险预算。 |

第 2 项权重更新：[070 独立实机](combat-phase-event-trace.md#2026-09-27-第-26-日成长列表选择器权重实采)直接采到第 26 日 `knight_killed` 成长列表的原生 `int32` 权重 `[40,30,15]`、子抽签 `51,510,340`、阈值 `2`、第 0 项；同帧智能体 evaluator 的 Q100000 `[4,000,000,3,000,000,1,500,000]` 与原生零差。原始证据、冻结向量、只读投影器及聚焦测试已经入库。这一列表的权重门闭合，其他事件写回和逐日 trial 接线仍待研究。

第 1 项掩护边界补研：[非零掩护静态向量与下一次同帧采集合同](pursuit-screen-nonzero-branch-contract-2026-09-27.md)确认 004 三日零差样本的**败方掩护聚合每天均为 0**；胜方条目有非零掩护不能代替败方分支证据。现有整数核对 `screen > pursuit`、`extra=0`、minimum 托底和逐团余数的离线向量通过，但尚未出现非零败方掩护的原版同帧逐团对拍。视频只能用 004 解释其真实输入，智能体仍须把未来追击修正与掩护条件保留为未校准风险。

[冻结候选全量审计](pursuit-screen-frozen-candidate-audit-2026-09-27.md)用逐文件 SHA 扫描本机已有的 252 份原生控制回执：251 份可用，其中 32 份为追击期，均属同一梅西纳 CombatID，**败方非零掩护样本 0 份**。胜方有非零掩护，不能据此声称目标分支已覆盖。因此不再从现有冻结资产反复挑候选；下一次须先取得有非零败方 `effective_screen_raw` 的新自然战例，再按上述合同做同帧逐团对拍。

第 5 项后备派令更新：[072 独立实机](winner-ai-terminal-reentry-live-072.md)把 065 的胜方路线疑点定位为 builder 返回未处理（`+8=0/+9=0`，主提交 0 次），外层 fallback 向 ProvinceID `2639` 提交一次 kind-2 move 且队列接受；26 项审计通过，原始证据与机器向量绑定。共享 gate 的通用语义及命令次日是否真正执行仍未证成，不能把这个单样本外推为普通战争 AI 的完整派令策略。

第 5 项次日回读：[074 独立实机](winner-ai-postsubmit-next-day-live-074.md)复现同一终局分支和后备队列接受，在第 27 日仍读到胜方军队位于 ProvinceID `2633`、目标与路线为 `2639`，没有新 builder/submit；31 项审计通过。原始公开/私有回读都没有 AI 军队的 MovePath ETA 或队列 apply 事件，因此“入队接受”和“次日路线非空”仍不能证明命令执行。后续 076 应优先只读回读该 CUnit 的 MovePath/首跳 ETA；若无法安全取得，则有限逐日观察位置、目标与路线，保留命令归因未知。

第 5 项战中主动撤退与智能体缺口：[普通战争队列生产端静态审计](ordinary-war-active-retreat-queue-audit-2026-09-27.md)又排除了六个邻近入队点，它们分别是创教、头衔、首都、宫廷设置和雇佣类命令，不能据此声称已找到普通战争 AI 的败势撤退策略；纯 AI 连续观察仍只见败后自动撤退。更直接的智能体缺口是：当前生产策略仅消费原生撤退合法性的 `too_early` 日期门来安排观察，**尚未在已开战状态用整场有界估计选择继续打或主动撤退**。原生 typed preview/order 能力已存在，下一步须先证明同一暂停帧的 active CombatID 输入足以从当前兵力/软硬损失起算，再接我方自有风险阈值、原生合法性、确切目的地预览和动作后新 revision 读回；不能把战前 `contact_admission` 反过来当作战中撤退策略，也不能称其为原版 AI parity。

[战中预测输入审计](active-combat-forecast-input-gap-2026-09-27.md)进一步确认：v3 的 `ongoing_combats` 只来自**本次请求选中的军队**，并非全局其他战斗，因此生产 `forecast_fixed_contact` 现在会在所选军队已参战或该观察字段缺失时返回 typed unavailable，防止把“重新从第 0 日接战”的结果冒充现役 CombatID 的续算；其他独立军队的战前接战估计照常使用。battle-control 已有真实阶段、roll、双方逐团 current/soft 与战宽，但缺同一次 native application-main 的完整续算输入，现有 trial 也没有从主阶段第 N 日起跑的入口。下一步是独立 resumed 初态、同帧输入与原版对拍，然后把“继续/合法撤退”接进实际游玩策略；单纯解除这道 guard 不能解决问题。

[主战阶段续算最小核](active-main-combat-resume-kernel-2026-09-27.md)已实现独立 `ActiveMainResumeState`/`ActiveMainResumeResearchKernel`：显式接收 CombatID、当前 entry/有效伤害、roll cadence/当前 roll、非 roll 优势与缓存战宽，只输出快照之后的天数和新增硬伤，拒绝战前 participant policy、跨快照和非主战阶段。46 项聚焦测试通过，但目前仅由合成续算状态检验内核行为；没有能提供这些操作数的同一 native application-main 生产读口，智能体尚未调用现役续算。下一步优先实现原生 typed producer 和真实暂停战斗下一日对拍，不能把这些静态测试算作已获得战中胜率。

[现役战斗策略入口审计](active-combat-strategy-forecast-ingress-audit-2026-09-27.md)进一步确认，生产智能体当前使用同帧 battle-control 执行现役战斗的撤退与限时推进，**未使用现役续算胜率**。原生 sibling `active_combat_resume_inputs_v1=unavailable` 已可观察，但还未进入策略层的 snapshot 投影。通用首次接战 ingress 已加 guard：拟移动军或目标守军处于 `in_combat` 时，不得拿缓存 v3 或战前接战模型冒充现役战斗预测。下一步仍是补齐同帧操作数、将 typed receipt 接入策略，再以实机下一日对拍决定续算是否可用于实际游玩。

[战中撤退目的地种子](active-combat-retreat-destination-seeds-2026-09-27.md)已接入智能体的**只读动作预览**：可控且仍在战斗的军队现在能以同帧其他驻扎我军省份为初始候选，排除已观测敌军当前/目标/路线省；长路线第一站在战中只生成重新预览与接触查询，不派生可绕过撤退 token 的直接 move 命令。30 项聚焦测试通过。种子不是安全目的地证明，尚无战中 route-contact ETA 覆盖及撤退后速度的实机配对，因此自动撤退 order 尚未接线；后续必须在同一暂停帧通过 native legality、完整敌军作用域、全程到站门、typed token 和新 revision 回读。

[战中路线窗口复核](active-combat-retreat-destination-seeds-2026-09-27.md#战中-route-contact-与到站时间的静态复核)确认当前 route-contact 只覆盖 `date_raw..+24` 的一天，战中 subject 虽未被静态代码显式拒绝，但下令前普通移动的 ETA 不可直接当作撤退后 ETA；原版另有 `MOVEMENT_SPEED_RETREAT=4.5`。后续需分别实采战中只读查询和合法撤退后的独立恢复回读；单日无接敌不能证明一条超过一天的撤退路线全程安全。

第 5 项延长回放启动门：[076 预检诊断](winner-ai-postsubmit-076-prelaunch-steam-diagnostic.md)发现 Steam 桌面画面与 074 旧图逐字节相同、任务栏时钟冻结；UI Automation、直接窗口采样和可恢复重绘也未给出可读的当前离线状态。076 因此在 **CK3 启动前**保留 environment RED，没有新增 AI 移动或 ETA 结果。Steam 本次进程的离线启动日志和持久偏好是旁证，不冒充实时 UI；下一次新 attempt 须先恢复可靠离线状态取证，再执行已冻结的有限日观察计划。

第 4 项片中身份映射：[两份配对原生存档的只读复核](maa-regiment-87-save-name-identity-2026-09-27.md)均把 RegimentID `87` 绑定为 `mubarizun`，原版简中为“穆巴里尊”，属职业兵士重步兵；ProvinceID `2633` 为“墨西拿”。该身份可用于视频文字与智能体解释层，但兵种定义的基础坚韧 `25` 与同帧有效值 `26.25` 的差额仍不能仅由名称推断修正来源。

[87 号兵团有效属性来源的进一步静态复核](maa-regiment-87-dual-type-source-boundary-2026-09-27.md)把固定坚韧 enum、动态 class 行、定点乘法和目标向量后加链收窄；同时发现 v3 的 counter class 从 `CRegiment+0x18` 类型读取，实际有效属性从 `+0x118` 类型读取，两指针是否同一尚无同帧证据。因此不能拿 v3 的 class index `0` 或 `25×1.05=26.25` 直接指认某个生效修正。旧缓存形成时、暂停直接求值与下次 schedule 入口须分别采实际 enum/向量，才可解释 `25→26.25` 的变化来源。

第 4 项输入回归更新：两个新增隔离暂停帧的原生 v2 **直接属性求值**与下一次 schedule 对拍为 `51/51 + 63/63 = 114/114` 零差；智能体实际使用的 v3 `base_inputs` 与 v2 全对象一致。故当前帧试算应保持 v3 直接输入，不把旧战斗 entry 缓存误当作下一次 schedule 的属性；待研究的是未来逐日 modifier 转移以及发生变化的 18 个职业兵团的具体修正来源。完整证据与边界见[增援和日内属性专题](battle-reinforcement-and-join.md#2026-09-26暂停帧直接查询可得到本案下一次-schedule-的有效属性)。

第 4 项跨日端点更新：第 11/21 日共有 `51` 团，两次原生直接求值的征召兵 `19/19`、职业兵士 `8/8` 相同，骑士 `22/24` 相同；变化的两名骑士有效勇武分别 `13→14`、`2→5`，效能不变。[逐团交叉日回执](battle-reinforcement-and-join.md#2026-09-26两份暂停帧之间的原生有效属性稳定性)绑定各日完整原始来源。中间各日与其他环境尚未采集，不能据此去掉试算器的未来状态变化风险；下一步优先补逐日事件/人物写回及不同地形/驻扎条件。

第 4 项骑士效能来源更新：同一第 11 日暂停帧已将九项原生修正逐名回读，`24/24` 名骑士的加权和与原生效能零差；本案后八项皆零，前项分别给出 `+10000/+85000/+75000`。同时纠正共用 modifier 读取器入口，发现旧同源 v2 中两项将领掷骰界限和一项守方反制效率误读；新 v3 输入与新 v2 完全相同，旧冻结估计必须重算。[完整回执与勘误](battle-reinforcement-and-join.md#2026-09-26骑士效能九项修正逐项回读以及共用-modifier-读取器勘误)。剩余门槛是非零的后八项样本、效能上下文身份、职业兵士修正链，以及跨日状态转移，不能把本案首项数值固定到任意未来日。

第 4 项多军求援结构更新：[第 21 日三军夹具](battle-reinforcement-and-join.md#2026-09-27三军结构门通过但自然求援未触发)已在同一原生 AI parent 中直接证明撤离一支后仍有两个 anchor，随后以 production 合法撤退、切回 AI、独立冷载观察了 11 日。撤离者次日恢复完整 AI membership，第 10 日以普通移动朝旧战斗省返回，但 anchor 全程不发 `asking_for_help`，没有 help target/ETA，旧战斗第 11 日先终局。这把原来的 singleton fixture 缺陷关闭为**结构门通过**，却仍未关闭实际 requester/assignment/rejoin 的业务门；下一夹具必须同时有需要帮助的战况与足够的回场时间。

第 4 项日内安排边界复核：[两次自然增援的掷骰、事件及战宽字段投影](battle-join-schedule-boundaries-2026-09-27.md)确认完整七边界内保留的优势掷骰分别为 `7/8`、`3/8`，抵达日首次出伤前名单已扩为 `27→40`、`39→44` 团；事件 load index 与显式战宽输入仍未捕获。这些原始字段不能替代下一次针对 roll/event/width/counter 的同日入口观察，也不能把局部 RNG `word0` 的数值差直接视作抽签次数。

第 4 项战宽静态生产/消费链：[exact-build 调用与字段追踪](join-width-production-and-fire.md)确认增援 join 刷新双方人数缓存后，符合旧 base width 门时更新历史最大 base `+0x6C0` 与 final `+0x6C4`；随后主阶段出伤读取存储的 final width。078 之前两次自然增援回放尚无 join 前后战宽数值；完整只读探针必须把 join 入口、正常返回和首次出伤前绑定同一 CombatID/日期，不能预设三点都在同一线程。

第 4 项战宽局部实测更新：[078 独立回放](join-width-production-and-fire.md#078-两点战宽实采与第三点线程门)在同一 CombatID `16777218`、原生日期 `53146512` 见 ArmyID `22` 加入 side 0；join 入口→正常返回的 base width `1645→2467`、final width `1480→2220`。078 的完整三点 collector 仍为 RED，[079](join-width-production-and-fire.md#079-实机前环境-red) 仍为启动前环境 RED；两者保留历史身份。[083 新独立实机回放](join-width-production-and-fire.md#083-同一次自然增援的三点实采)在 Steam 实时离线画面恢复后补齐同一增援的第三点：首次 side0 出伤实际入参 `R8D=2220`，三点 collector captured、clean exit。上段旧的“同线程”取证要求以专题中的 077/078 勘误为准：join 两点自身同线程，phase-fire 可在另一线程，但必须同 CombatID/日期和 side；083 此次三点恰好都在实际战斗线程 `19936`，与 mailbox `25740` 不同。

078 的局部模型对拍还确认：以原版森林宽度乘数 `90000` 和实采双方 totals 为输入，已有 `update_combat_width` 对入口/返回两组 base/final 共四个数值零差。它是**给定当日参战身份和人数**后的算术核，不产生未来增援到达日；后续 trial 必须同时更新 roster、entry 状态、双方人数缓存和宽度。旧 side0 缓存与新 ArmyID `22` 的人数直接相加会高出实采返回值 `5627319` Q100000。[同一原始回执的七边界 entry 交叉核算](join-width-production-and-fire.md#078-七边界-entry-交叉核算2026-09-27-追加证据)又发现：前一日旧 side0 缓存 `160317482` 高于 27 条旧 entry 的合计 `154690163`，正差 `5627319`；次日旧 entry 逐 ID 未变，新增 ArmyID `22` 的 13 条合计 `256000000`，join 返回 `410690163=154690163+256000000`。这定位了观测窗口内的旧缓存差，但前一日记录不是 join 入口同一钩子边界，仍不能把简单加法写成通用转移。下一版 080 已冻结同帧入口/返回 full-entry 只读采集合同；Steam 离线实时画面门在 083 已通过，080 仍需自己独立的新鲜门禁与新 attempt。

[未来增援路线输入审计](future-reinforcement-trial-input-boundary-2026-09-27.md)确认现有 route ETA、AI 求援 assignment 和一日接战查询只给**当前路线的条件候选**：assignment 目标是 Province，`contact_if_now_selected_combat_id` 只指现在，不能提前指定到达日的 CombatID、side 或完整 entry 状态。078 的实测 join 也不能替未来所有日子造名单。因此后续先逐日采真实 help-assignment→到达→同 CombatID join，再以 080 同一 hook 的完整 entry 与旧团刷新状态生成 typed `participant-update`；trial 接线必须在该日同时更新 roster、属性、反制、人数缓存和战宽。既有固定参战者模型仍可在标注条件与未知项后供战前策略使用。

第 4 项人物与军队称呼更新：[双日存档身份映射](episode01-day11-day21-combat-human-names-2026-09-27.md)已将 87 号穆巴里尊归到阿里的 ArmyID `16777221`，这场战斗是阿里一方、拉马丹指挥，对罗贝尔一方；第 21 日新增 ArmyID `22` 是穆尼斯的军队。视频与智能体解释层可以用这些带 ID 的称呼。[军队标题静态边界](episode01-army-ui-name-boundary-2026-09-27.md)尚未读到 `Army.GetNameNoTooltip` 的本场返回，不能把存档中的 name seed 拼成精确 UI 军队标题。

第 5 项胜方 AI 重入勘误：[065 独立终局回放与有界静态提交门闩](winner-ai-builder-submit-gate.md)记录同场 day 26 正常结果后胜方路线出现 `[2639]`，但私有目标 `2639` 在 day 25 已存在；被动 observer 见 builder 调用 `1`、所监控提交点调用 `0`。原版 builder 有早退和共享门闩绕过分支，外层仅在 builder 返回未处理时才有后备提交；本案未采门闩原值和返回字节，不能判定具体路径或把路线显现说成新派令。065 启动时 Steam 截图新鲜度也已另记为未独立确认；下次须强化离线门并采实际分支。

第 5 项普通终局后续 effect 的新增静态边界：[败方战分门与正统性/战争条件](normal-result-loser-effect-war-score-gate-2026-09-27.md)把原生 row `+0x40` → ResultData `+0x40` → `warscore_value` accessor → loser on-action 脚本连成可复核的同 build 链。脚本声明单场幅度 `>=15` 且身份合法时的 `-50` 正统性 effect；同一外层分支再以战争方总分 `<=-25` 等条件筛选 marshal 事件。这里只闭合调用顺序、字段身份与脚本声明；字面量比较编译和实际 effect 写回还需同场实机，不能宣称战争已经结束或 R0244 已通过。

同项比较器补研：[原生 `setge` 分支与 loaded-node 缺口](warscore-trigger-generic-ge-and-loaded-node-gap-2026-09-27.md)已证 `CCombatWarscoreTrigger` 的虚表通向 generic 比较器，操作码 `0x3CB` 对两侧 raw qword 执行包含等号的 signed `>=`。脚本实例的操作码及 RHS `1,500,000` 尚未从实际载入节点读回；这仍需同场、同 CombatID、带 VFS 来源的被动实机采样。

[败方 on-action 名称与执行根的同序号静态映射](loser-on-action-name-root-index-map-2026-09-27.md)已把 `on_combat_end_loser` 名称槽 `0x980/0x20=76` 对到同一数据库的根指针槽 `0x260/8=76`，纠正了此前拿不同表的同一个字节偏移相互配对的错误。它只闭合到败方执行根，尚未唯一定位第 563 行的具体 loaded trigger；原版另一份 `combat_events.txt` 也有逐字相同的 `warscore_value >= 15`，所以仅采到比较类型、操作码与数字仍不够，必须绑定父链和 VFS 来源。

[败方根的条件门与 child 遍历](loser-effect-root-gate-and-child-dispatch-static-2026-09-27.md)再证同一 loaded root 在执行 child 前会先经节点 `+0x338` 求条件；失败时直接跳过后续两种数组与递归。0x30／0x48 步幅的两数组和 `+0x348` 递归顺序已由 exact-build verifier 核验，但具体哪个子对象来自脚本第 563 行、它的 RHS 是否为 `1,500,000` 及败方正统性写回仍未被唯一证成。下一步查 parser/VFS 源路径与真实 loaded 节点的父链，不用仅凭同文字面量越过身份门。

同项败方正统性配对审计：[11 份原生存档与 14 份正式回执](normal-result-loser-legitimacy-pair-gap-2026-09-27.md)只在墨西拿正常终局前证明败方罗贝尔 CharacterID `29829` 的正统性为 `321`；终局后没有对同一人物的原生读数。072/074 此时控制的是胜方阿里 CharacterID `31549`，其 `played` 字段不能作败方的后值。[下次同角色读回合同](normal-result-loser-legitimacy-readback-contract-2026-09-27.md)确认现有 root 查询只能读当前玩家，要求新败方控制 attempt 在终局前后稳定暂停帧成对查询；即使读到净差 `-50`，仍须另外排除其他写者并绑定脚本 loaded 节点，才能归因为败方 effect。当前 `-50` 只有脚本声明，不得记为已实测写回。

执行纪律：每个新证据先保存原始 bytes/SHA、源存档、游戏 build、CombatID/WarID、参战双方与日期，再生成只读投影。静态公式向量、条件计算、独立回放与自然 AI 行为在文档、智能体和画面中均分开标注。任何残差先查同帧输入与定点截断，再查参与者/事件边界；不能为凑零差修改历史原始回执或把模型自生成数当 expected。

2026-09-26 工具勘误：`native_bridge/research/find_xrefs.py` 原来把 CK3 整个可执行节一次交给 Capstone，在本机 EXE 上以 `CS_ERR_MEM` 失败；现按指令边界分块并保留最长 x64 指令的跨块余量，另提供 `--direct-only` 快速扫绝对指针与 E8/E9 候选。跨块引用测试通过。`--direct-only` 的 E8/E9 结果仍是**字节候选**，必须对命中的 RVA 再做有界反汇编审阅；vtable 相邻槽也只证明接口身份，不自动证明跨 manager 的全局调用先后。实际用它复核了 contact `0x2208320` 的 `0x220D3BA/0x27C0FDF/0x2277F6B` 三处候选，以及 combat manager `0x27FB4D0/0x27FB5D0` 的相邻函数指针；未据此冒称已闭合全局调度顺序。
