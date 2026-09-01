# 361 二期 B1：完整绩效事实季运行规范

> 状态：施工规范，2026-09-01（Asia/Shanghai）
>
> 范围：`001–013`、`037–053`、`135–145`、`357`，共 42 项。
>
> 证据边界：本文只规定产品实现、GUI 与批量验收合同；在同批 CK3 fixture GREEN 以前，42 项不得标为
> `complete` 或 `fixture-live`。

本文是 `361-phase2-full-implementation-program.md` 的 B1 施工细化。B1 不是在旧的单 tick 考核链上为 42 个编号各写一个
布尔变量，而是把现有考核重构为一条真实跨周期绩效季：目标、期中检查、互评、事实封存、影子档、跨经理校准、正式公示。

## 当前施工状态（2026-08-31）

当前可称为 **B1 跨周期行为纵切 static-ready**，仍不能称 42 项已完成：

- 已落地：D+0/D+180/D+240/D+300/D+330 阶段链、最多 80 人持久名册、owner/cycle/case/state stale guard、
  三槽真实评价者互评、目标/岗位/基线与期中快照、事实封存、影子档等待、共同上司 expected/ready barrier、
  小团队真实合池排名、#357 的事实→配额顺序，以及沿用既有单一结算/榜单发布路径。
- 已接入真实选择：#002 目标强度、#003 期中重设、#006 难度校正、#041 新人路线、#053 互评用途；京察下发只开启
  绩效季，不再在活动完成或拒办时立刻结算。
- 已补行为：玩家诚实/夸大/保守自评与 AI 诚实回退；影子档接受/补证；三槽互评的权重、疲劳、跨周期信用、
  mean/variance/shape 与正向互惠降权；`peer_use_mode` 对容量和校准输入的真实分流；本地与共同池均按有界
  `calibration_score` 重排，并保持原档位数量、优先保护新人不进末档；非新人不足以填满精确末档配额时，写明
  `newcomer_bottom_exception/newcomer_forced_bottom` 后才允许新人补足。满槽假提交、跨案卷互评和 stale 可见事件均有负例门。
- 已把确定性配额纵切接入 runtime：0/1/2/3/4/7/14/23 使用整数分子最大余数法，23 人精确为 7/14/2；同一冻结
  common superior 下仅一组同职能 3 人队与 4 人队可形成唯一 7 人池，池内继续消费 `calibration_score`，并把
  raw/floor/remainder/award/conservation before-image 回写双方 quota book。当前“同职能”已统一冻结为地方治理、军务、
  财政、管理/兜底四类真实任命映射，subject scorecard 与 common pool 消费同一分类；这仍是四族 taxonomy，未细分所有头衔与兼职。
- 已接入名册离开/失地/换上司的单次 amendment receipt 与 denominator consumer；唯一 3+4 池可执行一次固定
  TOP↔MIDDLE 单槽交易，双方 book version 与 creditor/debtor/liability 收据同步，责任债在 `created_cycle + 1`
  到期且只结一次。事实冻结前也会审计锁定后的合法新加入与 departure backfill，为新增者建立完整五元案卷、写 0→1
  amendment 并重开配额；离任审计项为可追溯性仍留在持久 list，因此 backfill 后物理 list 可超过 80，但 `roster_included=1`
  的有效 denominator 仍不超过 80。灰色离任继续占档仍未实现。
- 已接入完整 agenda list、跨周期稳定轮换、三席 attention 与有成本的 10 分钟加班换席；同轮可为多名已消费
  attention 的边界 subject 各开一个 pending，逐人冻结 milestone/verifier/deadline/reward，并走成功或失败终态。
  pending 先冻结 `min(late evidence + 1, 100)` 的目标，30 天独立事件再读取新的 live KPI；fallback MIDDLE 容量逐人预留，
  成功奖励直到重开门关闭且 board/reward revision seal 再校验后才支付。封榜后同一绝对阈值的正负 live KPI 变化可在付款前
  对称重开一次、重排固定档位。当前每个 cohort 只预选 agenda 第一名作为单探针，不代表所有 subject 都有独立重开观察；
  stale 授权使用 case-scoped quota-book revision seal，`Σ(agenda order × grade)` 仅作为可能碰撞的展示校验和，不作为身份门。
  冻结奖励另有 expected/paid 完整性对账，未付齐时不得公示。
- #001–#013 已补最小 write→consumer 纵切：八项/总分事实单、目标/岗位/五类起点解释、自评三路线、三维互评槽与
  evaluator 跨周期统计、盲审→实名关系差审计、A 路校准原子交换/护人责任债、A 路隔级程序退回、关系回避、三窗权重、
  匿名样本阈值、反馈债次周期扣分和档内顺序→次周期辅导/机会。C 路统一为 defer：不创建该机制业务对象，只在经理上
  写一次制度债并于下一次真实上级考核消费；旧 ID 与 completion receipt 在新案卷初始化时清理。
- 考核榜四内页及 #013 ACL 由独立 scoreboard 工作包施工；B1 runtime 在 D+0 只冻结稳定 disclosure ABI。named-widget MCP、
  完整 ACL 矩阵、多分辨率与 CK3 实机仍未 GREEN，因此 #013 仍是 partial，不能由 ABI 字段冒充完成。
- 本批补齐：#007 不再用 cohort/case sentinel 冒充共同任务；提交只在双方为同一场 live war 的同阵营登记参与者时成立，
  并把 war-scope serial、owner/cycle/case 与主要攻守方冻结进三槽。该真实 accepted path 覆盖率有限，普通治理/项目仍缺少
  当前绩效季可用的持久共同任务信号。#008 已把通用 result case 与 B1 case 在发布时冻结成显式 adapter；真实 3.25→3.5
  胜诉 hook 会按三槽方向一次性回写 evaluator overturn/credit，五元 receipt 防重复，A 路正向意见可获印证信用，负向意见才计
  overturn。该 hook 与同阵营战争判定都只通过 source contract，尚未做 CK3 scope 求值证明。
- #009 B 已实现一次性快速关榜：不改档，只核对每人唯一 pending grade、三档合计和非负 remaining；#010 B 只给既有合法
  非新人末档承担者写一次申诉/怨恨/流失风险，若只有受保护新人则明确 blocked，绝不为制造风险绕过保护；#011 B 由隔级席
  发起、但只在直属经理唯一 quota book 内执行一组 TOP↔MIDDLE 原子代理交换，保存 reviewer、双方 before/after 与程序风险，
  不创建第二份上级 review serial，最终 owner 仍是直属经理。
- 回避 ACL 以 `freeze_conflict_recusals` 为唯一生效边界：边界后的 #009/#010/#011、pending 与 reopen 都拒绝 recused subject；
  重排先扣除 recused subject 已占的固定 top/middle/bottom，再只重排未回避者；B1 不再暴露旧 `zg361.10` 自由升降档事件，
  玩家与 AI 都只走同一 settlement commit。命名替代席必须同时不同于经理、被评人和原回避者；无合法真人时走 authority=3
  抽象复核席。两路都按冻结盲审分独立重算建议档；建议变化只能与一名未回避、目标档同案卷人员做双边原子交换，保持
  TOP/MIDDLE/BOTTOM 数量不变；目标档无席时冻结 `quota_blocked`，绝不单边改档。发布时另写
  `recusal_post_grade/lock_match`。这闭合了 #012 的静态替代复评 write→consumer，但尚无 CK3 scope/结算实证。
- 仍未完成：#003 的真实 war scope 只通过 source contract，未做 CK3 求值证明；影子补证仍是固定有界 delta，不是可核验材料
  对象；机会偏置审计、真实预会与实名异议仍未闭合。#040 B 也不能只在 B1 专属层安全闭合：共享
  `zg361_run_review_effect` 会在 B1 事实准备之后按当前直属关系再次把离任者写成 `leaver_route=1 / roster_included=0`，而共享最终结算
  只遍历当时的 `every_vassal`。因此“灰色离任者继续占本周期 C 配额”需要同时修改共享考核、结算与榜单投影；在这些消费者改造前，
  不得用 B1 局部字段冒充已完成。
  pending verifier 当前是冻结经理 + 30 天 live KPI 比较的确定性最小实现，成功奖励固定为 25 威望，不代表外部
  材料核验完成。#142 A 现为每名 subject 建独立局部公示五元对象：非 pending 且未被预留为 fallback 的稳定人员立即获得冻结档位
  与本人事件；pending 与其唯一预留 peer 只处于 WAITING。每一宗 pending 成功、失败或 watchdog 取消后，经理立即只刷新已稳定的
  subject 行并逐行推进 revision，不再等待其他 pending；#143 重排后也只对实际变化的行写 reopen revision。局部公示不提前发奖、
  不应用最终 modifier，完整奖励 seal、淘汰与最终固定考核榜仍在 cohort barrier 后一次结算，避免重开时重复奖惩。
- `zg361_b1_mNNN_receipt_serial` 目前只是阶段施工追踪；在对应 meaningful write 与 consumer 都落地并通过同批 CK3 fixture 前，
  receipt 的存在不得用于把任何编号升级为 `complete` 或 `fixture-live`。

### 001–013 静态收口矩阵

所有 C 路均已统一为“不开业务对象、只写一次 next-review 制度债”；下表的 `static-ready` 只表示生成脚本、consumer 与负例合同
闭合，不表示 CK3 已加载或实机行为 GREEN。

| ID | 当前静态口径 | 仍需实证/补齐 |
|---:|---|---|
| 001 | A 八项事实逐项求和，B 仅总分并标 incomplete，C 无 sheet。 | CK3 事实冻结与榜/申诉同 ID。 |
| 002 | goal direction/strength/baseline/weight/deadline 写入评分解释，C 无 contract。 | 跨年度目标完成的 paused artifact。 |
| 003 | A 只在冻结 war/crisis scope 允许一次 rebase，B 固定目标，C check-in unavailable。 | exact-build war scope 求值。 |
| 004 | 玩家诚实/夸大/保守三路与 AI 诚实回退；夸大/保守 gap 只产生负向有界可见度输入。 | 三选项与 stale ticket 实机。 |
| 005 | 四职能族 scorecard、权重和 next-role 分离进入总分。 | 兼职/调任覆盖率与 CK3 scope。 |
| 006 | 五类起点、难度理由、hard cap 与解释分 consumer；不改原生领地值。 | 原生数值读取实机。 |
| 007 | 三唯一评价者槽；仅同一 live war 同阵营可写真实 common-task tuple。 | shared-war CK3 求值；非战争治理/项目持久信号。 |
| 008 | n/mean/variance/shape/normalized/reciprocity/credit 进入校准；胜诉 1→2 hook 回写 evaluator credit。 | 通用 result↔B1 adapter 与 hook 实机；历史样本跨存档。 |
| 009 | A 原子边界交换；B 不改档快速关榜并逐人/配额对账；双击和旧 case no-op。 | 10+ cohort 的真实点击/事件批。 |
| 010 | A 护人双边换档、威望与次轮债；B 非新人末档承担者一次性风险，受保护新人不被绕过。 | 全员达标夹具与次轮债消费。 |
| 011 | A 上级只退回一次；B 上级发起、直属经理单账本执行一组原子代理交换并留程序风险。 | 帝—公—伯三层 owner/reviewer 实机。 |
| 012 | 冻结冲突与 authority 1/2/3；命名/抽象替代席按盲审分独立重评，差异只做双边配额中性交换；经理后续 writer 锁人。 | named 与 abstract 两路 CK3 scope、无目标档 `quota_blocked` 和最终 lock 实机。 |
| 013 | runtime disclosure ABI 与四页 scoreboard ACL 已静态接线，received 不复制 evaluator/recusal identity。 | named-widget MCP、关闭重开清理、多分辨率和三角色矩阵。 |

本轮生成器同时产出简中/英文正式文案；法德日韩波俄西只有英文结构占位，不代表翻译完成，也未执行发布审计。共享案卷
kernel 目前只接入 roster operation 与 pending deadline 的最小参数化调用；它通过 source contract 与静态测试，不构成 CK3
参数求值证明。下一步先收口生成器/本地化/布线静态回归，再继续填实上列 A/G/B/H/S 缺口；集成批稳定后只启动一次 CK3
做 MCP-first 成组验收。普通开发阶段不做七语发布审计、Workshop 上传或宣传物料。

## 一、为何必须先改时间模型

现有 `zg361_run_review_effect` 在一次调用内完成建池、KPI、排名、待定档、校准和结算。这个结构无法真实承载：

- #002 的年度目标责任书与下一期完成结果；
- #003 的期中重设；
- #007/#049 的邀评、提交和截止；
- #040 的周期内离任；
- #045 的“不得惊讶”前置反馈；
- #047 的早、中、晚证据窗；
- #135 的影子档补证窗；
- #142 的多人待定里程碑；
- #143 的封榜后对称重开。

如果这些编号仍在同一 tick 内从 `open` 走到 `closed`，即使变量、事件标题和 debug marker 都存在，也只能判定为换皮 RED。

## 二、共享绩效季与阶段 dispatcher

### 2.1 周期阶段

每名合格管理者只拥有一个 active cycle；管理者仍严格限定为有地、在世、天朝制、公爵及以上。伯爵与男爵只拥有自己的
subject case，不得建立 cohort、分配配额、校准别人或替别人提交证据。

| 阶段 | 建议时点 | 权威动作 | 关键输出 |
|---|---:|---|---|
| `TARGETS_OPEN` | D+0 | 冻结 owner、season、cohort 草案、目标、岗位、基线、披露与互评政策 | goal/scorecard/baseline version |
| `MIDCYCLE_OPEN` | D+180 | 期中检查、一次有据重设、真实预警、机会授予与证据中段快照 | check-in/feedback/opportunity records |
| `EVIDENCE_OPEN` | D+300 前 | 本人自评、三槽背靠背互评、迟交信用与封存 | self/peer submissions |
| `FACTS_FROZEN` | D+300 | 名册锁定、八项 KPI、评价者校正、匿名与形状、事实绝对档 | immutable evidence sheet |
| `SHADOW_OPEN` | 事实封存后 | 影子档通知与限期补证；不发奖、不占最终档 | shadow response case |
| `QUOTA_READY` | 所有本组经理账就绪后 | 合池、配额交换、尾差、跨期债、盲审和预校准 | quota book / common-superior barrier |
| `CALIBRATION_OPEN` | 补证截止后 | 发言席、回避、上级退回、必议、交换、异议、待定与对称重开 | calibration journal |
| `PUBLISHED` | 截止前 | 逐人冻结最终理由、公示榜、received 镜像和下一周期输入 | immutable scoreboard / case links |

隐藏到期事件必须同时校验 `owner + subject（如适用）+ cycle_serial + case_serial + expected_state`。同一 ticket 重放、旧上司、
旧周期、旧案号或错误状态必须 no-op。旧存档无 v2 字段时，只允许从现有 `review_serial/result_*` 建立下一周期基线，不得重写
已经结算的旧榜。

### 2.2 同阶段只迁移一次

Phase 0 的通用计划会让同一领域的多个编号共享 `from → to`。逐号调用 `case.transition` 会导致第一个编号推进状态后，其余编号
全部 stale。正式实现必须采用：

1. 阶段 dispatcher 验证一次 owner/cycle/case/state；
2. 在旧状态下执行本阶段全部逐号业务 operation，并分别写 mechanism receipt；
3. 每个 meaningful write 必须至少有一个评分、trigger、期限、资源或 GUI consumer；
4. 所有业务 operation 成功后，领域阶段只迁移一次。

`choice/共享账本/debug/applied_serial` 不属于 meaningful gameplay write，不能单独作为某编号的实现证据。

## 三、逐号运行绑定

### A：目标、证据与评分

| ID | hook 与对象 | 必须产生的真实结果 |
|---:|---|---|
| 001 | `FACTS_FROZEN`，subject evidence sheet | A 冻结八项且逐字对账 KPI；B 只留总分并明确 `evidence_incomplete`；告身、申诉与榜单引用同一 sheet ID。 |
| 002 | D+0 goal contract | 冻结方向、强度、基线、权重、截止与 3.75 上限；目标权重进入评分解释，保守目标不能凭完成率独自升 3.75。 |
| 003 | D+180 check-in | 危机时最多重设一次，保存旧→新版本与支持义务；旧目标不覆写。 |
| 004 | D+300 self review | 本人一次性提交自评、代表证据和日期；认知差只作有上限的主观/可见度输入，不能改硬事实或终档。 |
| 005 | D+0 role scorecard | 冻结岗位、量表版本与权重；转岗只写 next role，旧周期仍按原岗位解释。 |
| 006 | D+0 + facts freeze | 冻结期初来源、难度理由、调整前后与 hard cap；只改评分解释，不改原生领地值。 |

### B：互评与校准政治

| ID | hook 与对象 | 必须产生的真实结果 |
|---:|---|---|
| 007 | 邀评窗 + 提交互动 | 每名 subject 最多三槽 `evaluator/subject/cycle` 反馈；保存三维分、事例、封存状态以及真实同阵营 war task tuple；无共同战争时拒绝，不再回退为 case sentinel。 |
| 008 | 互评封存 + 胜诉 hook | evaluator 保存样本、均值、方差、翻案率与信用；原分、修正分和权重并列保留，修正分进入 aggregate；真实 3.25→3.5 胜诉按槽方向一次性更新信用。 |
| 009 | 待定档→校准→公示 | A 复用原子配额中性交换并补齐 ID/双方/reason/attention；B 不改档快速关榜，核对每人唯一 grade、三档和 remaining；重复/旧轮拒绝。 |
| 010 | 全员达标/护人案 | A 护人支付威望、次轮管理债并由另一合法人承接同一 C；B 只给既有非新人末档承担者一次申诉/怨恨/流失风险，不能绕过新人保护。 |
| 011 | common-superior oversight | A 只检查程序并退回直属经理一次；B 可请求一组边界点改，但由直属经理唯一 quota book 原子执行并审计，不生成第二 review serial，最终 owner 始终是直属经理。 |
| 012 | 校准前 conflict case | 冻结关系、回避者与替代席；命名/抽象席按 identity-blind score 重算建议档，同档确认或与未回避目标档人员原子互换；无席显式 quota-blocked；manager writer 均拒绝 recused subject。 |
| 013 | D+0 ACL + 公示 | 本人始终可看 final/reason/申诉；团队按模式看汇总或档位；evaluator identity 只对 manager/复核席开放。 |

### G：强制分布配额工程

| ID | hook 与对象 | 必须产生的真实结果 |
|---:|---|---|
| 037 | 两个 quota book ready | 同一上司下两队交换恰好一个档位；双方 delta 相反、总名额守恒，并有 creditor/debtor/due/settled。 |
| 038 | common-superior pool barrier | 真实小队合池；例如 3+4 必须形成唯一 7 人分母，再按原团队投影，不能各自硬切或伪造单 manager 池。 |
| 039 | 名册冻结 | 每人保存 owner/cycle/include reason；锁后变更必须有 amendment/reason/approver 并退回待校准。 |
| 040 | 周期开始与冻结名册对比 | 离任、裁撤和 backfill 分账；灰色路线可让离任者占 C，但要保留事实档、异常来源和经理责任。 |
| 041 | 名册冻结与配额资格 | 新人保护/完整参评/献祭三路线真实改变 C eligibility；保护不等于免考，并保存导师、爬坡目标和强制纳入期。 |
| 042 | 三轮历史审计 | 保存 grade/rank/evidence 三轮序列；轮流背 C 命中后重建个人证据或降低互评权重，并产生可见处置。 |
| 043 | 校准发言席 | 有限 attention 席位决定哪些边界案可人工交换；越时必须实际支付威望/上司耐心并记录被挤案件。 |
| 044 | 事实排名→实名复议 | 先保存匿名 token/blind rank，再保存实名 rank 与允许理由；差异超阈值进入 audit。 |
| 045 | D+180 反馈→终评检测 | 3.25 没有真实早期 warning/ack/objection 时生成反馈债，进入经理下轮 KPI 与申诉权重。终评后不得补造。 |
| 046 | 周期内机会授予 | 记录关键项目、援军、富庶领地或曝光机会的 grant；难度校正有上限且不能单独升 3.75，长期偏爱开启经理审计。 |
| 047 | 早/中/晚证据窗 | 保存三段 raw/weight/weighted score，合计必须是 KPI 的真实 consumer；切换政策只影响下一周期。 |

### H：互评微观博弈

| ID | hook 与对象 | 必须产生的真实结果 |
|---:|---|---|
| 048 | 邀评窗 | evaluator 保存 cap/used/over-cap/fatigue；超额真实降权或增加压力，无接触拒评不罚。 |
| 049 | 邀评截止 | submission ID、提交日、封存 serial、准时状态与一次监督补交；封存后不可编辑。 |
| 050 | 封存前互惠审计 | 双向高互惠且缺共同证据才对称降权；举报真伪回写评价者信用与关系。 |
| 051 | ACL 投影 | author count 与 threshold=3 决定摘要/延期/署名；低样本不得向普通 viewer 泄露原话、项目线索或作者。 |
| 052 | 互评聚合 | 均值、方差、上下级/同侪/跨组均值和 shape code；同均分不同形状必须产生不同辅导或经理风险。 |
| 053 | 周期策略冻结 | development 模式绝不进入 KPI/bonus，只生成辅导；pay 模式固定权重上限；价值观红线必须引用具体证据。 |

### S：预校准与影子档位

| ID | hook 与对象 | 必须产生的真实结果 |
|---:|---|---|
| 135 | 事实封存后补证窗 | shadow grade 明确标为非最终；保存通知日、截止、补证与 shadow→final 理由，不提前发奖或占最终配额。 |
| 136 | 3–4 个 ready manager 的预会 | 只讨论真实边界案，保存参会经理、标准快照、建议和正式结果 diff；单 manager 不得伪装预会。 |
| 137 | 校准前议程冻结 | 每个 case 恰出现一次；重排写新版本，后段 attention 衰减要真实影响可审字段或换档资格。 |
| 138 | rank 后、pending 前 | 保存原始小数、取整模式、remainder、受益队和轮换期，并直接生成三档配额；23 人必须是 7/14/2。 |
| 139 | quota ready / publish | 借入恰好一个档位，保存 due cycle 和 liability；到期只偿还一次，重组不删除债。 |
| 140 | D+0 到名册冻结 | 保存旧新 manager、服务天数、证据区段和 quota owner；一人只能进入一个 cohort、占一个 slot。 |
| 141 | common-superior must-review | A 只强制一宗真实边界案进入直属经理议程并守恒消耗 attention；B 也只能由直属经理在同一冻结账内原子交换一名 MIDDLE 与一名 TOP，人数守恒且 book version 只前进一版。高层不得直接写孙级档位。 |
| 142 | calibration exception | A 为逐人 pending：本人公开投影严格只有 marker/milestone/deadline；B 不持有名额、不冻结奖励且不改当期终档，本人严格只收到 current-final-unchanged/next-cycle-evidence。 |
| 143 | 封榜后、付款前 | 为整个冻结 cohort 建 batch 并逐人建立 probe；A 按绝对 severity 选至多一人重开，稳定并列规则固定；无人达阈值也必须封存 NO_QUALIFYING 结果。B 逐人生成独立次周期证据对象。 |
| 144 | 校准动作 | A 实名异议必须绑定真实 subject、事实理由、独立 reviewer 与一次 attention receipt；B 共识封存必须保存真实且唯一的参会 manager identity，不能用计数或本地变量伪造多人。 |
| 145 | 正式 MIDDLE=3.5 后 | 只允许对正式 3.5 人群排序。A 公开排序但机会名额有限；B 排序私有，所有受影响本人都获得申诉证据与 blackbox audit。绝不接入 pay/reward/bonus。 |

### S.1 #141–#145 冻结 runtime ABI、consumer 与投影 ACL

本节是 #141–#145 的权威 ABI；上表只是摘要。这里冻结的是 runtime 对象和 GUI/MCP 投影合同，**不是当前已经在
CK3 画面中可见的声明**。

#### 共同五元组与默认拒绝

每个 batch、case、probe、swap、pending、consensus、order row 和 next-cycle evidence 对象都必须保存并在每次
写入、消费、投影前逐项匹配：

```text
(object_owner, object_subject, object_cycle, object_case, object_state)
```

- `object_owner` 是该对象的真实直属经理/账本所有者；manager 级 batch 的 `object_subject` 明确取该 manager 本人，逐人对象
  则必须取真实被考核者。`object_id`、slot、当前 scope 或 live liege 不能替代五元组。
- `object_cycle` 与 `object_case` 都来自对象创建时的冻结快照；调任、死亡、新周期或重新选中 GUI 行不得把旧对象重绑到新 owner、
  subject、cycle 或 case。
- `object_state` 必须经过该机制列出的单向状态机；终态重复消费和任一五元不匹配均为 no-op，并留下 stale/duplicate receipt，
  不能重新写榜、发机会或重复扣 attention。
- manager/audit、`received/self`、team/public 是三个不同投影通道。以下白名单逐字段允许，未列字段一律拒绝；内部变量即使存在、
  即使叫 `visible`/`public`，也不会因此自动成为 GUI 或 MCP 字段。投影只能复制冻结对象，不得回读人物 live 变量。
- C 路只记该机制的 policy debt，不创建业务对象、不写任何投影；policy debt 也不允许借别的机制字段伪装成 A/B 结果。

#### #141：高层必议与直属经理守恒交换

- 必议对象五元组为 `(direct_manager, boundary_subject, cycle, must_review_case, OPEN)`。高层只提交
  recommendation/agenda reason，并预留一份真实 attention；它不是 owner，也没有 grade writer。
- A 的唯一 consumer 是直属经理的校准议程：经理完成复阅后把对象置为 `REVIEWED`，attention 由 reservation→receipt 恰好一次；
  不存在换档 payload。
- B 必须在同一 `direct_manager`、同一 cycle/case、同一本冻结 quota book 内同时找到
  `boundary_subject=MIDDLE(3.5)` 与 `swap_peer=TOP(3.75)`。唯一合法提交是一个原子事务：subject
  `MIDDLE→TOP` 且 peer `TOP→MIDDLE`。提交前后 TOP/MIDDLE/BOTTOM 总数和各档人数完全相等；任何半边写入、跨经理 peer、
  无真实 peer 或档位已漂移都进入 `NO_PAIR`/`CANCELLED`，不得伪造 `SWAPPED`。
- B receipt 必须冻结 `book_version_before`、`book_version_after=before+1`、双方 before/after band、交换前后档位计数及
  `attention_receipt`；该 receipt 才是 quota book 和上级判断信用的 consumer。重复调用不得产生第二个版本。
- manager/audit 白名单：`recommendation_owner`、`direct_manager`、`subject`、`swap_peer`、`agenda_reason`、
  `attention_reservation/receipt`、双方 before/after band、交换前后计数、book version、终态与判断信用结果。
  `received/self` 白名单：`must_review_marker`、`agenda_reason`、`review_outcome`、`own_final_band`。team/public 为空；本人不得看到
  peer identity、对方档位、内部计数、book version 或经理信用。

#### #142：pending 与延期承诺的严格分路

- A 的 pending 五元组为 `(direct_manager, pending_subject, cycle, pending_case, PENDING_OPEN)`；每个 subject/cycle
  最多一个。状态只能走 `PENDING_OPEN→SUCCEEDED|FAILED|CANCELLED`，所有 pending 都必须各自到达终态后 batch barrier 才能关闭。
- A 内部 ledger 可以保存 `held_slot`、`fallback_slot`、provisional/fallback band、verifier、reward freeze、reserved peer、
  quota count、hash 与结算 receipt；这些字段只供 manager/audit 的里程碑验证、配额守恒和一次性结算 consumer 使用。
  **本人公开投影的精确白名单只有** `pending_marker`、`milestone`、`deadline`；不得投影 held/fallback/provisional band、
  verifier identity、冻结/释放/到期/已支付 reward、reserved peer、quota count、hash 或内部终态分支。
- A 在 pending 创建时持久化 typed `open_date=current_date` 与独立的 `deadline_days=30`。当前 exact-build 尚未冻结可靠的
  date-plus-days 赋值语法，因此不伪造 exact due-date 变量；provider 必须用这两个字段严格计算，轮次 deadline 继续独立保存。
- A 同时建立与 pending 对象分离的逐人局部公示五元组。稳定的非 pending subject 立即从 `WAITING→PUBLISHED` 并冻结档位、
  object revision 与 receipt；pending subject 及其被预留的 MIDDLE peer 在原子成功/失败前都保持 `WAITING`。每次单人结算后立即
  重扫冻结 `processing_subjects`，只追加刚稳定或档位实际改变的行，其他 pending 不构成 barrier；watchdog 取消和 #143 重排也走
  同一逐行 revision。本人事件只显示本人当前档位与“首次/追加/重开”类型，不显示 verifier、预留 peer、quota 或他人身份。
  该局部公示不调用 `zg361_apply_grade_effect`、不发奖励、不触发淘汰；最终 modifier、奖励 seal 与固定考核榜仍在全组终态后一次结算，
  从而避免一行被重开时重复发钱、重复扣钱或重复处分。
- B 不创建 pending、不持有 held/fallback slot、不冻结或支付 reward，也不重写当期榜。它创建独立的次周期对象
  `(direct_manager, subject, next_cycle, deferred_case, DEFERRED_OPEN)`，由下一周期证据入口一次消费后置为 `CONSUMED`；
  stale/调任/死亡走 `CANCELLED`。**本人公开投影的精确白名单只有** `current_final_unchanged`、
  `next_cycle_evidence`。manager/audit 可看该对象完整五元组和消费 receipt；team/public 为空。
- #142 B 的 next-cycle 字段必须使用自己的 namespace，不得与 #143 的 reopen probe/next-cycle object 共用 marker、state 或 receipt。

#### #143：全 cohort batch、唯一结果与稳定并列

- manager batch 五元组为 `(direct_manager, direct_manager, cycle, reopen_batch_case, COLLECTING)`；冻结 source board/reward/book
  seal、cohort size、pending/processed/cancelled count 与 route。每名冻结 cohort 成员都必须另有
  `(direct_manager, member, cycle, probe_case, PROBE_OPEN)`，不能预选一个人来冒充全 cohort。
- cutoff 后每个 probe 至多接收一条 fresh observation，并冻结 sign、absolute severity、source serial 与 eligible。stale、死亡、
  调任或取消也必须把该 probe 恰好一次计入 barrier，不能让 batch 永久停在 `COLLECTING`。
- A 只有在全部 probe 终结后才选择 `abs(severity)` 达阈值的至多一人。稳定排序依次为：绝对 severity 降序、冻结 roster
  order 升序、object case 升序；正负同绝对强度没有额外偏置。选中者产生 `REOPENED`；无人达阈值产生真实终态
  `NO_QUALIFYING`。后者必须有 result/receipt 且保持 board/reward/book seal 不变，不能被当作 C 或“没执行”。
- A 重开只发生在付款前：固定配额重排、产生新 board/reward/book version 与 old/new seal，最多一次。其唯一 consumer 是
  重算/重新封榜；B 不改旧榜，而为每名有合格 observation 的 subject 创建独立
  `(direct_manager, subject, next_cycle, next_evidence_case, NEXT_OPEN)`，只由下一周期 evidence ingestion 一次消费。
- manager/audit 白名单：batch/probe/result 五元组、冻结 cohort identities、sign/severity/source、计数、稳定排序键、阈值、
  selected/no-qualifying、old/new seals/versions 与 consumption receipt。A 的 `received/self` 白名单：`reopen_result`、
  `own_final_band`、`reason_code`；B 的 `received/self` 白名单：`next_cycle_evidence`、`target_cycle`。team/public 为空，且任何本人
  投影都不得包含其他 cohort identity、severity、排序键、账本 seal 或 reward ledger。
- GUI 不直接消费 batch/probe 或 next-cycle 业务对象。A/B 各物化一个 subject-local、完整五元组的终态投影：A 仅带
  `reopen_result/reason_code`，B 仅带 `next_cycle_evidence/target_cycle`。

#### #144：独立复阅、attention receipt 与真实共识身份

- A dissent 五元组为 `(direct_manager, dissent_subject, cycle, dissent_case, DISSENT_OPEN)`，必须同时冻结非空 fact reason、
  advocated band、原档位与真实 named dissenter。reviewer 必须是冻结时真实、合格且独立的参与者：
  `reviewer != direct_manager`、`reviewer != subject`；没有独立 reviewer 就 `CANCELLED`，不能让原经理自审或制造抽象 reviewer。
- 独立 reviewer 必须消费一份有限 attention reservation，并生成与五元组相绑的唯一 `attention_receipt`。结果只能是
  `OVERTURNED` 或 `NOT_VALIDATED`，同时冻结 final band、judgment credit/procedural-risk consumer；重复复阅不得再扣 attention。
- B consensus 对象也必须有完整五元组 `(direct_manager, consensus_subject, cycle, consensus_case, CONSENSUS_OPEN)`。
  `attending_manager_ids` 必须来自真实冻结参会者、逐一唯一，count 必须等于 identity 集合大小；subject、final band 与 consensus
  reason 必须冻结后才可 `SEALED`。单一 manager 的多个本地变量、重复 identity 或只有 count 没有 identity 一律无效。
- manager/audit 白名单：上述五元组、dissenter/reviewer/attendee identities、事实理由、advocated/original/final band、attention
  reservation/receipt、review/consensus outcome、credit 与 procedural risk。A 的 `received/self` 白名单：`dissent_marker`、
  `fact_reason`、`review_outcome`、`own_final_band`；B 的 `received/self` 白名单：`consensus_marker`、`own_final_band`。
  本批 GUI 的 team/public 为空；`consensus_marker/final_band` 只进入符合 #013 A 的 received-self，不得出现
  dissenter、reviewer、attendee identity、attention 或信用账。未来若新增 team/public，必须单独冻结并验收 ACL，不得自动继承。

#### #145：仅 3.5、有限机会、私排申诉，永不接薪酬

- order batch 五元组为 `(direct_manager, direct_manager, cycle, middle_order_case, ORDER_OPEN)`；每一行另存
  `(direct_manager, middle_subject, cycle, order_row_case, ORDER_FROZEN)`。进入 cohort 的硬条件是正式终档恰为
  `MIDDLE=3.5`；TOP=3.75、BOTTOM=3.25、shadow/pending grade 均不得进入。通用 rerank order 不能冒充 #145 order。
- 排序键固定为校准分降序、冻结 roster order 升序、object case 升序。机会/辅导 capacity 必须是有限整数
  `1..cohort_size-1`；不足两名 MIDDLE 时状态为 `NO_COHORT`，不创建假排序或假机会。
- A 的唯一 consumer 是有限机会/辅导分配；不改变任何正式档位。本批 team/public 为空，`received/self` 的精确白名单为
  `formal_band=3.5`、`within_middle_order`、`opportunity_capacity`、`opportunity_selected`、`coaching_selected`。
- B 的完整 order 与 selection 只进 manager/audit。team/public 为空；**每一名**冻结 MIDDLE 成员，无论是否入选机会，都必须获得
  本人投影，精确白名单为 `formal_band=3.5`、`own_opportunity_selected`、`appeal_evidence_available`、`blackbox_audit`。
  本人不得看到自己的数值 rank/order、他人 identity/selection 或完整排序；appeal/blackbox consumer 必须覆盖全部 affected self，
  不能只覆盖落选者或第一名。
- #145 在所有路线都没有且永远不得新增 compensation consumer：不得读写 personal gold、国库、俸禄、工资、奖金、bonus、
  reward、分红或其他物质 payout；不得复用 reward ledger，也不得被 band/grade writer 读取。它只能分配有限机会/辅导并生成
  appeal/blackbox audit。出现任何 pay/reward/bonus 写入即为 RED。
- #145 route 在 D+0 manager case 创建前冻结到 `zg361_b1_m145_mode`；后续 band-order consumer 只能读取该冻结 route，禁止回读
  live `zg361_mechanism_145_choice`。

#### GUI binder 的 static-ready 可见性边界

仓库现已用独立 `B1_OBJECT_FIELDS` schema 把上述安全字段接入既有考核榜四内页。managed 只冻结该 manager 自有对象；
received-self 再与冻结 #013 A 取交集；B、C/旧存档与 team/public 均不会因新增字段扩权。binding、identity、raw、recusal、swap
和薪酬字段不生成详情行。榜单仍先于淘汰发布；mark state 8 后用同轮一次性 strict patch 补 #141 最终结果而不改行序、分页或数量。

这只把 binder 与 ACL 提升到 `static-ready`。尚无对应的 MCP named-widget snapshot 与真实 CK3 可见 artifact；在 MCP-first 实机证据
闭合以前，不得称“游戏中已验证”、`fixture-live`、`production-live` 或完成。简体中文与英文是本批原创文案，其他七语仅英文结构
占位，不是发布翻译。

### #357：跨域事实→配额适配器

#357 不是 AL 领域里的“配额申诉退款”。其正确生命周期是：

```text
A / facts frozen
        ↓
G / quota snapshot opened
        ↓
B / calibration adjustment
        ↓
result case / final reason frozen
```

必须保存 `fact_closed_serial/day`、`quota_opened_day`、`quota_snapshot`、`absolute_grade`、`final_grade`、
`adjustment_reason` 与 `forced_down`。事实关闭后修改 live KPI 或八项输入不得改变旧案。#357 不得继承 `transaction.refund`，
退款只属于后续申诉领域。

产品接线在 `zg361_b1_mark_published_effect` 中完成：只有 #357 本轮 facts→quota consumer 已写
`m357_receipt_serial=current B1 case`，且当前 final result 已与冻结的 B1/result 两套独立案号 adapter 精确绑定后，才写
`m357_external_receipt_*`。来源票据冻结 absolute/final grade、final reason、forced-down、B1 case 与 result case；receipt
ID/hash 从这两个真实案卷确定性派生。它只是一张后续 Workforce 可消费的不可变来源票据，不直接调用 Workforce bridge，
也不写任何 readiness 布尔；缺失真实配额写入或错 result case 时保持无票据。该接线仍只有 L0 静态证据，尚未升级 live readiness。

### #360：B1 真实 cohort 来源投影

`zg361_b1_mark_published_effect` 在所有 subject 已经写完 state 8 与 #357 来源票后，调用
`zg361_b1_publish_m360_cohort_source_effect`。该 effect 只发布本经理已经完成的 B1 cohort，不接受 Central、Workforce 或测试 caller
传入成员、档位、票据或哈希。经理侧固定 ABI 为：

- `zg361_b1_m360_source_{status,reason,manager,cycle,case,state}`；当前 manager/cycle/case 的 mark 前没有 exact status，表示 upstream
  WAIT（上一轮不可变 source 即使仍保留也不能匹配新 tuple）；mark 后
  `status=1/2/3` 分别表示 READY / STRUCTURAL_NA / INVALID_DRIFT；
- READY 独有 `zg361_b1_m360_source_{available,sealed,id,hash}`，严格为 `available=1, sealed=1` 且 ID/hash 为正；ID 由
  cycle/case/#360 派生，hash 还绑定成员/议程 hash、C quota、all-meet 收据和所有入槽 #357 receipt hash；
- `zg361_b1_m360_source_{member_count,member_hash,agenda_count,agenda_hash,quota,all_meet_receipt_serial,forced_count}`；
- 最多六个 `zg361_b1_m360_source_forced_{1..6}_*` 槽。每槽冻结真实 character、`processing_order`、#357 receipt ID/hash，
  以及 B1/result 各自的 owner/subject/cycle/case tuple。

来源门不是“有一名 C 就算完成”。它重新遍历完整 `processing_subjects`，用冻结 roster order × processing order 独立重算 member hash，
并要求 `member_count=agenda_count`、`member_hash=agenda_new_hash=agenda_hash`。每名成员必须恰好属于当前 manager/cycle/case、已经关闭为
state 8、absolute grade 至少为 3.5、具有同案 #137 议程收据，以及与 B1/result adapter 完全一致的真实 #357 来源票。最终
`final_grade=3.25 && forced_down=1` 的人数必须恰等于本账实际 `pending_325_n`，并按 processing order 稳定写入六个有界槽。

旧 payload 总是先清除。#137 route C、零个最终 C、存在 absolute 3.25、总配额超过 Workforce 当前六槽容量分别写
`status=2, reason=1/2/3/4`；议程不完整、成员字段缺失、B1/result/#137/#357 tuple 漂移、重算成员 count/hash 不等、forced C
与最终配额不守恒分别写 `status=3, reason=101/102/103/104/105`。N/A/INVALID 只保留精确 manager/cycle/case/state 与诊断，
不生成 business ID/hash/payload。不得写 `available=0`、零 quota、零 receipt 或任意默认 character 冒充失败结果。Central 负责从
三个互异经理来源派生三个互异 cohort ID、选择 collective route 并调用 Workforce；B1 不越权生成 exception、approver、
manager cost、realm-trust 或结算结果。本节仍是 static-ready，
等待同一批 MCP-first CK3 paused/live 验收后才能升级状态。

## 四、共同上司 barrier

#037/#038/#011/#136/#141/#144 需要多个真实 manager；不得用一个 manager 的多个本地变量伪造会议。

- 同一上司在同一 season 打开其直属合格 manager 的周期，使兄弟团队尽量同日起跑。
- 每个 manager 在 `FACTS_FROZEN` 后发布只读 quota book ready receipt。
- barrier 在所有预期账 ready 或明确 deadline 到期后运行；迟到、换上司、上司死亡均有确定性降级路径，不能死锁。
- 配额交换、合池和借位必须在共同上司账上双边记账，两个 manager 的 delta 相反。
- oversight、must-review 和 dissent 只能退回、强制议程或要求复阅；越级直接写孙级 grade 是 RED。

## 五、考核榜信息架构

仍只使用现有“考核榜”HUD 入口，新增以下内部页，不增加顶层按钮：

- `facts`：cycle/case/sheet、目标、岗位、基线/难度、八项与合计、自评差、事实档/终档/理由；
- `peer`：三槽匿名摘要、cap/used/deadline、raw→normalized、mean/variance/shape、样本阈值、串谋风险和 use mode；
- `quota`：锁定名册、原始小数→三档配额、pool/trade/debt、新人/离任、盲审/影子/终档、attention、议程、回避、待定、重开、异议和交换日志；
- `received`：本人目标、证据、自评差、shadow 倒计时、终档与理由；伯爵/男爵只能看自己；
- `audit`：反馈债、机会偏置、轮转合谋、上级退回、高层必议和 ACL 模式。

### 5.1 生成与 ACL 方案

- 保留唯一 `zg361_scoreboard_toggle`、唯一 `zg361_scoreboard_window` 和现有 managed/received/system 外层页；不得新增 HUD
  按钮、顶层 window 或 scripted widget 注册。
- 名单行保留原有“打开人物页”按钮，并在其旁增加同级“案卷”按钮，禁止交互按钮互相嵌套。案卷按钮先执行该槽 selector，
  把冻结字段复制到唯一 `zg361_sb_detail_*` buffer，再进入 facts/peer/quota/audit。全 GUI 只能生成一个详情 pane，严禁复制
  `160×4` 套详情页面。
- managed 槽冻结经理可见案卷；received 团队行只复制公开榜单字段。玩家本人另有固定 self buffer，直接由玩家自己的冻结结果
  写入；评价者身份、原话、回避身份和内部交易对手永远不得进入通用 `r_XX_*` 镜像。
- 所有字段由声明式 schema 同时驱动 clear/write/copy/select/GUI/test；缺失值写显式 availability/sentinel。详情不得通过
  `Character.MakeScope.Var('zg361_result_*')` 回读人物 live 变量，否则旧榜会随调任、重算或新周期漂移。
- 发布新榜、切外层页、返回、X、backdrop 和 Escape 都清 selected/detail 状态；送达 3.25 或改判只可在 owner/cycle/subject
  全匹配时同步 final/reason/audit 等可变投影。
- modal 自身必须复用 HUD toggle 已验证的原生 overlay gate。按钮被右抽屉挡住还不够；榜单已经打开后再出现事件、决议或原生右窗，
  也必须隐藏或阻塞一致，不能叠压和穿透。

### 5.2 GUI 实机阻塞项

当前仓库已有 15 个固定 scoreboard identity 的只读 state provider，以及
`open/switch-managed/switch-received/switch-system/close/reopen` 的独立 static
action contract/fixture；但 enabled/callback/revision 和共享 MCP wiring 尚未
exact-build/live 闭合。既有 OCR/坐标 runner 仍不能签 MCP-first GREEN。完整 action
边界见 `361-scoreboard-mcp-action-cell.md`。正式 L1 前 MCP 夹具至少需要：

1. allowlist 内 named widget 状态：identity、rect、visible、focus、modal/blocking、外层/内层 tab、selected
   source/slot/cycle/case 与 revision；
2. 六个 allowlisted named-widget action 的独立 ACK 与 later-query 后置；
3. bounded scoreboard/case snapshot，返回 ACL 过滤后的冻结字段；
4. 公爵玩家 managed、伯爵/男爵 self-only、AI 公爵后台案卷无 HUD 三角色矩阵；
5. list/detail/back、四内页、X/Escape/backdrop、人物页跳转、原生窗互斥、100/125/150% UI scale 与
   1366×768/1920×1080/2560×1440 阻塞审计。

在上述 native/MCP 状态闭合前，OCR 只可在最后截取视觉素材，不得承担导航、状态真值或 GREEN 判定。

每个固定榜单 slot 必须携带 bounded `case_serial` 和必要摘要，或提供受 ACL 保护的案卷详情 action。当前“点击人物行只开人物页”
不能冒充案卷详情。GUI 隐藏与 MCP 查询必须执行同一 ACL；仅把文本设为 invisible 但 MCP 仍返回作者身份，同样判 RED。

## 六、B1 批量验收门

### 配额、议程、债务与 pending 的确定性参考模型

`tools/zg361_b1_quota_model.py` 现已把下列 A 路语义冻结为可执行 Python L0 reference：

- 0/1/2/3/4/7/14/23 人精确最大余数法，23 人固定为 7/14/2；3+4 只有同一共同上司、同一职能才能组成唯一 7 人池；
- 新人、离任、调任、长休、周期后加入的 denominator/bottom 资格与名册变更 receipt；
- 一次只交易一个 top 或 bottom 槽，交易同时产生双方责任、到期周期为 `created_cycle + 1` 的 one-shot 配额债；
- 议程必须与冻结 cohort 一一相等；attention 席、转让和加班都守恒，并记录被挤占对象与成本，不改冻结档位；
- 每名边界人最多一个 pending slot，绑定 milestone、verifier、deadline、冻结奖励与成功/失败终态；失败不能直接换成 3.75；
- 同等强度的正面成果与负面事故可对称重开，旧/新 board hash、recalculation receipt 与发奖互斥均为一次性；
- typed RED、失败前置原子性、stale 与重复 operation 分离。

`tools/test_zg361_b1_quota_model.py` 当前为 69/69 GREEN。模型显式声明
`READINESS = python-l0-reference-only`、`CK3_IMPLEMENTED = False`；该声明仍准确，因为 Python 模型本身不是 CK3 证据。
`gen_361_b1_runtime.py` 现已消费其中的确定性纵切：整数最大余数配额、唯一同职能 3+4 池、离开名册 amendment、
TOP↔MIDDLE 单槽交易与次周期 one-shot 债、agenda/attention/overtime、多人 pending、逐人局部公示及付款前对称重开。runtime 专测当前
51/51 GREEN，且共享案卷内核调用只达到 source-contract/static-ready；尚无 CK3 fixture，因此不得把上述静态实现写成
`CK3_IMPLEMENTED=True`、`fixture-live` 或 42 项完成。

L0 至少覆盖：

1. 42 个 ID exact；每个 variant 有具体 CK3 effect、唯一 dispatcher hook 和 meaningful write→consumer；
2. 同阶段逐号 receipt 后只 transition 一次；重复 dispatcher 与五元 stale token 全 no-op；
3. 跨年 D+0→D+180→D+300→facts→shadow→quota→calibration→publish；版本不可倒改；
4. 真实 evaluator/subject/cycle 三槽，0–4 作者、迟交/补交、重复提交、互抬/恶意低分、同均分不同 shape 与 ACL observer；
5. cohort 0/1/2/3/4/7/14/23；1–2 中性、3+4 唯一合池 7、23 严格 7/14/2；trade/debt/rounding/swap 守恒；
6. 两 manager ready、一个迟到、换上司、共同上司死亡；barrier 不死锁，且上级不能直接改孙级档位；
7. shadow 补证、同轮多人且逐人唯一的 pending slot、正负同 severity 重开、dissent 复阅与 band order 无奖金 consumer；
8. #357 facts 必先于 quota，冻结后 live KPI 无效，事实 3.75/3.5→最终 3.25 明确 reason=quota，旧 AL refund 静态 RED；
9. 玩家/授权 AI 天朝制有地公爵+可管理；非天朝、无地、伯爵、男爵管理 RED；subject 自评/补证/看本人案卷 GREEN；
10. 旧存档 bootstrap 不改旧榜、不重复结算；旧 `review_in_progress` 有确定性迁移；
11. 所有 GUI 字段有写入和绑定，ACL、关闭重开、tab、modal 阻塞、DPI/分辨率和 production projection 通过；
12. L1 前 readiness 不提升；一次 MCP-first CK3 批次 GREEN 后，才把本批 42 项升为 `complete / fixture-live`，其余 317 项保持不变。

L1 使用 native/MCP snapshot → 产品动作 → 独立 ACK → 新 revision query。OCR 只允许在 native 状态已闭合后截取最终画面，不能导航、
不能提供状态真值、不能判 GREEN。B1 完成前不继续七语发布审计、Workshop 上传、发布截图或宣传片。

## 七、已核对的 CK3 持久化与调度写法

以下不是猜测，而是 2026-08-30 对原版 1.19.0.6 脚本与本项目既有实机链的只读核对结果。

- 临时 `add_to_list` 不能跨 delayed event。管理者的最多 80 名 subject 必须写入角色上的 variable list：
  `add_to_variable_list = { name = zg361_b1_subjects target = scope:subject }`；恢复用
  `every_in_list = { variable = zg361_b1_subjects ... }`，并在新周期前用 `clear_variable_list` 清理。语法证据在原版
  `game/tests/event_target_lists_tests.txt:95-238`。
- 先用临时候选列表排序，再以实际 `list_size` 把 `ordered_in_list max` clamp 到 80。不能假定 tooltip 预演已经提交前一条
  `add_to_list`；现有考核榜 `zg361_effects.txt:1077-1111` 已用同一写法规避空列表越界。
- subject 自身必须同时冻结 owner/cycle/case/state。旧 delayed ticket 要先比管理者 token，再逐 subject 比五元 token；即使旧事件看到
  新周期重建后的 variable list，也只能 stale no-op。
- character scope 可用 `set_variable = { name = ... value = scope:... }` 持久保存，并以 `var:name = { ... }` 或
  `scope:manager.var:name = { ... }` 恢复。原版证据见
  `events/yearly_events/bp1_yearly_james.txt:1067-1079,1153-1166` 与
  `events/story_cycles/story_cycle_tax_rivalry_events.txt:501-547`。
- delayed hidden event 可以保存 scope/value token；本项目 `zg361_events.txt:156-228` 已有实机通过的 owner/cycle/case/state 模板。
  B1 的 guard 放在 `immediate` 内：外层只查存在性，内层才读取 `var:` 并比较；失败显式记 stale 日志。不要把完整 guard 放进
  event `trigger` 后静默丢单。
- common-superior barrier 必须两阶段：上司保存 frozen `expected_managers` 与 `ready_managers` 两个 variable list；经理只提交一次
  ready receipt；全部就绪或 deadline 才由上司一次关账，再把 allocation receipt 写回各经理。调任仍归 frozen superior/season，
  不能按 live `liege` 搬旧账；上司死亡走本地确定性降级。
- variable list 不假定自动去重。追加前先用存在性分支与 `is_target_in_variable_list` 检查；不存在的列表不能直接做 size/membership 求值。
- 同层 AND/OR/NOT 不保证短路。所有 state/receipt/cursor 在创建案卷时显式初始化；不得用
  `has_variable = x` 与 `var:x = ...` 平铺在同一层来保护未设置读取。
- visible option、decision effect 与 `hidden_effect` 都可能被 tooltip 预演追入。任何依赖初始化的消费者必须放在初始化已真实提交后的阶段，
  必要时至少隔 `days = 1`。
