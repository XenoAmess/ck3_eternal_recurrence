# P60：本场雇佣取舍、Native 构造器边界与撤退入口

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-18；各项实际 UTC、来源路径、帧和 SHA 见[小型证据索引](evidence/p60-native-constructor-nohire-and-retreat-2026-10-18.json)。本专题只归档已有观测和源码结论，不改变公共功能、当前 SDK/App、Native DLL 或游戏现场，不新增 G2 验收信用。

## AUTO40：584 家公司为什么均未采购

R3 AUTO40 的历史源 UTC 为 `2026-10-17T21:40:26.514812Z–21:40:29.684869Z`，当次开始日期 raw`53358576`，路线时钟实际结束于 raw`53358648`。本次只复用已封存的小型统计与资格记录，没有再次解码原 2,599,168B 响应。下列数字描述该回合留存的评估，**不是现在的报价或现有兵力**。

| 拒绝条件 | 候选数 |
|---|---:|
| 出生省不是当前己方原地友好集结点 | 584 |
| 没有反转已观测己方主导战争的兵数缺口 | 584 |
| 原生征募或支付条件拒绝 | 572 |
| 编成或合同条款尚未就绪 | 565 |
| 不能确认或保留所需军费现金 | 494 |
| 已被其他雇主雇用 | 71 |

条件有重叠，不能相加当作不同公司数。最接近的公司152，当时费用211金、856兵、36个月合同；现金424.64323金，支付后213.64323金，高于所用200金预留，但原生预测出生省为2618，当前没有符合原地集结条件的己军，没有可保证的救援 ETA，也没有反转全体已观测敌军4783的兵数差额。公司296为239金/837兵，支付后185.64323金，另不满足200金预留。

当时全市场最大公司102为2929兵、846金，无法支付；即使只作上限算术，1357+2929=4286也低于4783。此处不是战斗胜率模型：距离、军团质量、战宽、将领、未来增援、其他战争共用己军仍须分别评估；单家买兵不能反转头数不等于所有采购都没有战略价值。当前消费者采用原地集结与兵数反转的保守采购模型，不能宣称已经充分评估远程救援。

财务模型使用当时最大军费3.654金/月的18个月分配（65.772金）与200金政策预留，后者在该例占主导；4.51460金/月只是 gross income，完整 net income 未观测。36个月合同与预留用途分别记录，不能把收入当净现金流，也不能把付得起说成能赶到或能获胜。下一次采购必须重新获取当前报价、原生 CanHire/支付/完整公司ID、己军集结和财务，再单次提交并独立核雇主、军队生成及实际支出。

## Native25 的实际拒绝与公共 V3 源码是两类证据

本场冻结 Native25 **bridge 源码** SHA 为 `55cc0bd664478f64496b219445a0b5ceeb902b386bb9e1ef076f1592f0b875e9`，不是 DLL SHA。实际 R3 AUTO123 在 UTC `2026-10-17T21:56:54.020575Z–21:56:55.068333Z`，native`10327`，请求 `query-combat-simulation-inputs-v2-2619-ctor0-a-2-402653372-436207707-d-1-167772577`，被 Native 以 `combat-input query step is not canonical` 拒绝。V2 不在前置 `TypedQueryKind12002`，实际进入仅允许 exact `.3` 的 constructor long-dispatch gate；不能当作成功输入或已经攻击。

公共 `f6f64a47` 的[前置路由](../../ck3_autonomous_player/native_bridge/src/bridge.cpp)把 `.4` V3 识别为 `combat_v3`，在 long dispatch 前交给 typed executor；真正 executor 使用 `BindPhaseImage12004`，共同 constructor gate 已允许 exact `.3`/`.4`。后面 legacy `.3`-only 的 V3 分支对 `.4` 不可达，修改它不能修复本场 V2 拒绝。**本场 Native25 CAP 没有广告 V3；公共源码有该路由不代表本场 V3 可调用。**

`.4` 已有独立 Combat、Phase、Contact factories 与相关 storage/RVA，基础输入并非全缺。但共享 `ReadConstructorZeroContactGeography` 仍按 exact `.3` create-new incoming-defender 分支，直接选择 raw0/no crossing、跳过 entry 扫描。已复用 `.4` Contact 来源只闭合292B字段前缀及若干独立 callback，不覆盖完整 create-new caller：holder/fallback defender → raw0第六参数 → wrapper → CCombat保留`+6F8`及双方有序插入。尚未取得这条 `.4` 全路径来源，不能仅凭 Apply gate 或 RVA 差值放宽 V2。旧来源记录缺 machine_id 的两件明确标记 unknown，只复用源码知识，不追认本机运行资格。

后续若考虑 V2 gate 变更，须先补这条有限原生来源；保 canonical ctor0/null-entry、exact SHA、暂停/帧/代际、战争与完整双方 scope。MSVC 入口为 `tools/run_native_msvc.py`，原生产 `xar_ck3_12002_combat_test` / `xar_ck3_12002_phase_test` 及必要真实 dispatch fixture；构建须独立目录并先核存储预算。这项研究不阻塞下一次1066开局沿用现有受守卫能力。当前只做源码审查，没有 Native patch、构建或新实机资格。

R5 的 AUTO29 后续实际使用既有守备哨兵，原地2623、速度5，raw`53358936→53359104`（七天），由原 Native DTO 校验、13项负例、小型来源 epoch 与独立 MET35/turn6210闭合。新策略原 plan 没有旧 classifier 的部分声明字段，后续只建立来源绑定的 validation view，未改原 plan/Native DTO、未重放原动作。Root 已恢复后续自动批次；本文只固定这条已封七天证据，不将后续未封进度、守备或日期推进算作解围、保地成功或胜局。敌方主动接战仍可能发生；[现有被动守备合同](p55-siege-route-and-passive-defense-2026-10-18.md)保留 daily tick 后战斗暂停及停后重规划。

## 自然战斗出现时的合法撤退入口

现有 production 组合在能力与原门禁满足时，允许 Root 依用户自动游玩授权做首次自然业务验证；没有新增实验审批，也不存在“先成功才允许首次执行”的循环。旧1.19实机不能当本机`.4`验收；这限定成功声明，不禁止本次合法验证。普通自动规划器尚未接入主动撤退消费者，本专题不宣称已经部署。

1. batch边界暂停，取独立 SEM；以当前 **public revision** 调 `ck3_query_battle_control_snapshot_v1(subject_army_id, expected_revision)`，核 actual `.4` 绑定、当前 CombatID、双方完整 roster、owner/side/scope、affected/unaffected有序成员、phase/day、winner及原生 `legality/legal_now`。原 BattleControl/PreviewMove/Move 能力、H3937、Service与Native门禁照常有效。
2. 核本仗失地代价、当前战争/占领与实际伤亡趋势；必要时用 `ck3_query_battle_transition_v1(combat_id, expected_revision)` 和现有增援 assignment query。当前一 tick 伤亡诊断需要明示己方风险预算，不是原生 AI 阈值；追击损失、目的地敌军、救援 ETA 缺失就保留 unknown，不凭兵数声称胜率。
3. 选当前有据的目的省，以 `ck3_preview_active_combat_retreat_v1(selected_public_cunit_id, target_province_id, expected_revision)` 获 fresh `available/action_ready` 预览。取该预览的 `source_binding.revision`、CombatID、side、scope、target、`target_preview.candidate_token`，一次调用 `ck3_order_active_combat_retreat_v1` 的对应七个参数。期间不推进日期、不更换实例；入口会再次核成员、原生合法性和路线。合法路线不代表全程安全。
4. ACK/`accepted_verification_pending` 不是完成。独立新 SEM 逐军核退却、目标及路线，并查**原** CombatID transition/terminal。full-side 核对侧 winner/phase；owner-subset 核受影响军离场、未受影响军仍在原战斗；真实增援重开须另记录。随后核战争目标、战分与损失并按现流程保存。

超时、断连、丢 ACK 或后验未齐时只观察，不换 token重发。明确拒绝也不复用已消费 token；先新观测、排除未知已提交动作，再作新的决策。完整参数及后验操作卡为证据索引中的 `RETREAT-NATURAL-MCP-CHECKLIST.md`；原生产合同见[撤退专题](active-combat-retreat.md)，其旧实机和绝对地址必须保留版本边界。本轮不增加 M6/M7 或完整战争能力信用。
