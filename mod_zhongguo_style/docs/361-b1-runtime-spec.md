# 361 二期 B1：完整绩效事实季运行规范

> 状态：施工规范，2026-08-31（Asia/Shanghai）
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
  raw/floor/remainder/award/conservation before-image 回写双方 quota book。当前“同职能”使用 governor/非 governor
  两类最小映射，尚不是完整职位族谱。
- 已接入名册离开/失地/换上司的单次 amendment receipt 与 denominator consumer；唯一 3+4 池可执行一次固定
  TOP↔MIDDLE 单槽交易，双方 book version 与 creditor/debtor/liability 收据同步，责任债在 `created_cycle + 1`
  到期且只结一次。锁定后新加入、完整 backfill 与灰色离任占档仍未实现。
- 已接入完整 agenda list、跨周期稳定轮换、三席 attention 与有成本的 10 分钟加班换席；同轮可为多名已消费
  attention 的边界 subject 各开一个 pending，逐人冻结 milestone/verifier/deadline/reward，并走成功或失败终态。
  pending 先冻结 `min(late evidence + 1, 100)` 的目标，30 天独立事件再读取新的 live KPI；fallback MIDDLE 容量逐人预留，
  成功奖励直到重开门关闭且 board/reward revision seal 再校验后才支付。封榜后同一绝对阈值的正负 live KPI 变化可在付款前
  对称重开一次、重排固定档位。当前每个 cohort 只预选 agenda 第一名作为单探针，不代表所有 subject 都有独立重开观察；
  stale 授权使用 case-scoped quota-book revision seal，`Σ(agenda order × grade)` 仅作为可能碰撞的展示校验和，不作为身份门。
  冻结奖励另有 expected/paid 完整性对账，未付齐时不得公示。
- 考核榜已生成事实/互评/配额/审计四个案卷内页，使用冻结 owner/cycle/case 身份与 received 本人缓冲；这只是
  static-ready，named-widget MCP、ACL 与多分辨率实机仍未 GREEN。
- 尚未完成：具体三维互评与共同任务证据对象、可核验的补证材料、锁名册后新增/backfill、完整职能分类、程序退回、
  回避席、盲审实名差、反馈债消费、机会偏置、三窗证据权重、匿名样本阈值、真实预会、pending 局部提前公示、
  实名异议与 band order 消费。
  pending verifier 当前是冻结经理 + 30 天 live KPI 比较的确定性最小实现，成功奖励固定为 25 威望，不代表外部
  材料核验完成。现有榜单/结算是 manager 级原子发布，因此任一 pending 会让同 cohort 全员等待至所有 pending 结束；
  非 pending 人员档位不会改变，但尚未实现“先局部公示、后补 pending 行”。
- `zg361_b1_mNNN_receipt_serial` 目前只是阶段施工追踪；在对应 meaningful write 与 consumer 都落地并通过同批 CK3 fixture 前，
  receipt 的存在不得用于把任何编号升级为 `complete` 或 `fixture-live`。

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
| 007 | 邀评窗 + 提交互动 | 每名 subject 最多三槽 `evaluator/subject/cycle` 反馈；保存三维分、事例、共同任务来源与封存状态，不再直接写 KPI。 |
| 008 | 互评封存 | evaluator 人物保存样本、均值、方差、翻案率与信用；原分、修正分和权重并列保留，修正分进入 aggregate。 |
| 009 | 待定档→校准→公示 | 复用原子配额中性交换，但补齐 calibration ID、状态、双方、理由、attention 和重复/旧轮拒绝。 |
| 010 | 全员达标/护人案 | C 承担者与保护对象都要明确；护人支付实际威望或下一轮管理扣分，且必须由另一合法人承接同一 C。 |
| 011 | common-superior oversight | 隔级只可检查程序并退回直属经理一次，不得越级写孙级 final grade；退回会阻塞公示直到重开或到期。 |
| 012 | 校准前 conflict case | 冻结关系类型、回避者、替代席与前后建议；回避者对该 subject 的 grade write 必须被 trigger 拒绝。 |
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
| 141 | common-superior must-review | 高层每周期最多一宗必议，只强制进入议程并消耗 attention，不得直接改孙级档位。 |
| 142 | calibration exception | 每名边界人最多一个 pending；同轮允许多人，逐人预留 held/fallback slot、冻结奖励，guarded deadline 各自只结一次；当前保持单榜原子发布，其他人的档位不变但会等待最后一个 pending。 |
| 143 | 封榜后、付款前 | 对预选单探针而言，同绝对 severity 的重大正负事实拥有相同重开资格，每轮至多一次，保存 old/new revision seal 与展示 checksum；已支付奖励不倒扣。全 cohort 独立探针仍未实现。 |
| 144 | 校准动作 | 实名异议必须附 subject 和事实理由，并强制一次独立复阅/attention 消耗；空白异议无效。 |
| 145 | 待定档后 | 每档内部冻结 band order；A 只供辅导/机会且奖金没有 consumer，B 私下用于机会会产生黑箱 audit。 |

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

当前仓库对 named scripted widget 的查询/动作仍只有 MCP 能力合同，既有 runner 的 scoreboard 审计主要依赖 OCR 与坐标。因此五页
只能先做到 static-ready，不能据现有 runner 签 MCP-first GREEN。正式 L1 前 MCP 夹具至少需要：

1. allowlist 内 named widget 状态：identity、rect、visible、focus、modal/blocking、外层/内层 tab、selected
   source/slot/cycle/case 与 revision；
2. named widget activate/close/reopen 的独立 ACK；
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

`tools/test_zg361_b1_quota_model.py` 当前为 55/55 GREEN。模型显式声明
`READINESS = python-l0-reference-only`、`CK3_IMPLEMENTED = False`；该声明仍准确，因为 Python 模型本身不是 CK3 证据。
`gen_361_b1_runtime.py` 现已消费其中的确定性纵切：整数最大余数配额、唯一同职能 3+4 池、离开名册 amendment、
TOP↔MIDDLE 单槽交易与次周期 one-shot 债、agenda/attention/overtime、多人 pending 及付款前对称重开。runtime 专测当前
22/22 GREEN，且共享案卷内核调用只达到 source-contract/static-ready；尚无 CK3 fixture，因此不得把上述静态实现写成
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
