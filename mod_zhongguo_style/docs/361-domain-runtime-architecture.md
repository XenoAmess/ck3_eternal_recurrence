# 361 领域运行时架构

> 2026-08-30 施工进度：Phase 0 的设计合同层已经落地。38 个 DomainSpec、361/361 runtime plan、1083 条 A/B/C
> typed-operation 编译和生成快照已通过 L0；真实 readiness 仍保持 `partial × 4 + not-implemented × 357`。case kernel 的 CK3
> consumer、第二批产品 effects、共享面板与实机证据尚未完成，不能把 `contract-complete` 写成玩法完成。八批执行账见
> [`361-phase2-full-implementation-program.md`](361-phase2-full-implementation-program.md)。

本文定义 361 条政策从“可配置的组织账本投影”升级为真正 CK3 决策、对象、期限与后果的施工架构。它不推翻现有考核主循环和实机证据，而是明确区分已经完成的配置投影与尚待实现的领域运行时语义。

> 2026-08-30 二期更新：项目所有者已授权 v0.4.x 实施首个纵切，并已把该成品静态里程碑收入 master 开发基线。#001/#018/#069/#357 现为 `domain_runtime = partial`、`runtime_evidence = static-ready`；其余357项仍为 `not-implemented`。实现、边界与 MCP-first 合批清单见 [phase2-slice-001-018-069-357.md](phase2-slice-001-018-069-357.md)。这不改写已公开 0.3.0 的功能或证据口径。

设计边界：

- 只有天朝制公爵及以上在任领主可以拥有考核单元并考核自己的直属官员。
- 伯爵和男爵只能作为受评对象，不能拥有 cohort、配额、校准、定档、PIP 发起或晋升审批权。
- 玩家走可见决策与案件界面；本 mod 是继 `ox_here` 后经项目所有者明确授权的第二个 AI 例外，但只允许符合上述资格的 AI 天朝制公爵及以上在后台考核直属官员。
- 不进入宗教、信仰、教义、改宗或 holy order 系统。
- 361 条不是 361 个孤立弹窗，也不能用 361 个唯一变量冒充 361 种玩法语义。

## 一、现有实现的诚实边界

当前权威数据在 `tools/zg361_mechanism_data.py`：共有 14 本组织账和 17 个 `profile`。每个 profile 只有一套 A 路与一套 B 路变化，而 361 条机制的 C 路全部复用同一份 `DEFER_DELTAS`。因此运行时一共只有：

```text
17 个 profile × 2 条 A/B 路线 + 1 条全局 C 路线 = 35 种账本 payload
```

`tools/gen_361_mechanisms.py` 当前为每号生成的独有状态只有：

- `zg361_mechanism_NNN_choice`；
- `zg361_mechanism_configured_n` 的一次增量；
- 组合校验和增量；
- 编号化 debug marker 与本地化文本。

除二期首纵切的最近一期证据/送达/清算案卷外，目标版本、完整申诉复核、HC、晋升包、事故时间线、奖金归属等概念还没有各自的运行时对象、状态迁移、期限或资源事务。现有实机夹具执行每号的 `reference_choice`，其分布为 326 个 A、4 个 B、31 个 C；随后逐号检查 choice 变量，再核对 14 本账的总和及幂等性。这证明 361 条配置投影确实进入了真实 CK3 引擎，但不证明 361 条领域语义已经实现，也不是二期新字节的 CK3 证据。

因此 manifest 应把状态拆开记录：

```text
catalogue               = complete
policy_configuration    = fixture-live
ledger_projection       = fixture-live
domain_runtime          = not-implemented / partial / fixture-live
player_visible_loop     = not-implemented / partial / fixture-live
runtime_evidence        = none / static-ready / fixture-live / production-live
```

不得删除或贬低已有 artifact；其准确名称应是“361/361 配置与账本投影 fixture-live”。只有在真实领域对象上建立前置状态、执行产品动作、验证状态/资源/期限/反馈后，对应编号的 `domain_runtime` 才能升级。

现有真正可复用的产品核心包括：

- `zg361_is_celestial_liege_trigger` 与 `zg361_is_reviewable_vassal_trigger` 的管理者/受评者边界；
- 京察召集、免费活动、拒办、300 日期限和上司问责；
- review serial、直属 cohort、稳定唯一排名、30/60/10、短名单与新人保护；
- 原子校准换档、三档结算和末位处置；
- 3.25 的地方国库、个人金币、贤能与俸禄后果，以及按 receipt 申诉退款；
- 固定 80 槽的不可变考核榜、玩家收到的榜单镜像、告身和案件人物入口；
- 非独立 AI 天朝公爵后台考核；
- 一次 CK3 启动内的外部 fixture、日志、截图、存档与证据索引管线。

这些是新架构的内核与适配入口，不应重复重写。

## 二、六层架构

### 1. 政策配置层

现有 `zg361_mechanism_NNN_choice` 可以保留，但它只表示政策选择，不能再单独计作玩法实现。每项政策增加版本、生效周期、前置条件、互斥项和领域 operation 映射。正常改制在下一周期生效，不能倒改已经封存的案件。

“一键部署参考宪章”只负责配置默认政策；它不应瞬间伪造 361 项历史案件或把所有长期后果一次性写入人物。AI 可以一次配置预设政策包，随后只在真实领域状态机到达决策点时执行后果。

### 2. 运行时对象层

领域语义必须依附真实对象，例如：

- `review_case`
- `calibration_round`
- `appeal_case`
- `pip_case`
- `promotion_packet`
- `hc_slot`
- `project_case`
- `incident_case`
- `compensation_award`
- `policy_version`

对象用 `owner scope + cycle serial + bounded slot` 唯一标识。一个受评者同周期通常只有一个 review/PIP/appeal 对象；经理侧需要列表时使用有上限的固定槽，禁止为“看起来独特”创建 `361 × cohort` 套变量。

### 3. 领域状态机层

38 个领域各有自己的状态图、入口 hook、合法迁移、终态和清理规则。361 条机制映射为状态机的参数、分支、限制或附加动作，而不是彼此孤立的脚本系统。

每次迁移必须检查：

- 对象 owner 与 subject；
- cycle/case serial；
- 当前状态；
- 触发者权限；
- 是否已结算；
- 是否仍在期限内。

### 4. 资源事务层

金币、地方国库、中央/上级国库、影响力、威望、HC、晋升槽、提名额、管理工时、值守容量和配额都必须使用明确的 reservation、receipt、settlement 与 refund。

同一种货币的转移必须写明付款方、收款方、金额、批准人、案件 serial 和退款条件；不同资源间的兑换必须有显式换算规则。惩罚若进入制度性 sink，也必须声明，而不是让钱无来源地增加或消失。容量类资源遵守“授权 = 空闲 + 预留 + 已用 + 回收/到期”的恒等式。

14 本组织账保留为实际案件结果的气候汇总，不再是主语义。账本变化应由已结算事务与状态派生，不能由政策卡点击直接替代业务过程。

### 5. 可见反馈层

复用当前考核榜安全入口，增加少量高层页签，例如考核案卷、申诉/PIP、职业/HC、项目/运营、制度审计。每号必须映射到至少一个可见反馈：

- 上下文事件；
- 案卷或表格行；
- modifier/opinion/stress/merit 等人物后果；
- 资金、HC、配额或承诺 receipt；
- tooltip 中的规则、期限和原因码。

只有真正需要裁决的迁移才打断玩家。后台记录、到期检查和汇总不应制造 361 个弹窗。

### 6. 验收与证据层

验收数据与运行时 schema 同源生成。每号的 PASS 至少包含：

```text
BEGIN
前置对象/状态/资源快照
调用产品 effect 或真实 GUI 动作
后置状态与期限 token
资源、容量或配额恒等式
可见反馈投影
PASS
```

只看到 choice 变量、debug ACK 或 aggregate ledger 不满足领域 PASS。

## 三、38 个领域状态机

| 领域 | 运行时对象与状态链 | 资源/守恒要点 | 主要可见反馈 |
|---|---|---|---|
| A `001–006` 目标、证据与评分 | `review_case`：未立项 → 目标锁定 → 期中调整 → 证据封存 → 评分 | 目标版本和基线不可倒改；行政工时真实占用 | 分项证据、基线、难度和评分明细 |
| B `007–013` 互评与校准政治 | `calibration_round`：邀评 → 封存 → 评价者校正 → 校准 → 公示 | 换档配额中性；利益冲突回避；评价权重合计守恒 | 校准驾驶舱、换档记录和回避原因 |
| C `014–018` 申诉、PIP 与退出 | `appeal_pip_case`：告身 → 申诉/PIP → 支持 → 检查 → 毕业/失败/退出 | 处罚退款不超过原 receipt；PIP 支持预算与经理容量 | 个人清算单、申诉案卷、PIP 任务 |
| D `019–025` 晋升包、薪酬与 HC | `career_allocation`：资格 → 晋升包 → 答辩 → 预算/HC 预留 → 兑现/失败/流失 | 加钱、升级、任命、给权分账；资金和名额先预留后兑现 | 职业面板、晋升包和留任结果 |
| E `026–031` 贡献、抢功与指标异化 | `contribution_case`：项目登记 → 贡献签名 → 功劳主张 → 争议/审计 → 归因 | 贡献份额有总额；Sponsor 消耗信用；审计可冲正 | 项目贡献时间线和抢功仲裁 |
| F `032–036` 管理者与制度反馈 | `manager_review`：上轮团队快照 → 经理评分 → 理由码 → 九宫格 → 长期报告 | 管理分只消费上一轮快照，严禁同轮递归 | 上司考定窗口、管理理由码和十年报告 |
| G `037–047` 强制分布配额工程 | `quota_book`：名单草案 → 锁名单 → 算配额 → 互换/欠债 → 封榜 | 三档人数恒等 cohort；新人保护；跨期配额债有方向与期限 | 配额账、分母、尾差和交换记录 |
| H `048–053` 互评微观博弈 | `peer_feedback_round`：邀请 → 提交 → 封存 → 信用/合谋审查 → 入分或仅发展 | 邀评额度、评价工时和最小匿名样本守恒 | 互评摘要、评价者信用和合谋警告 |
| I `054–061` 汇报与可见度 | `report_packet`：成果 → 材料 → 版本签名 → 逐级流转 → 确认/泄露 | 汇报工时必须挤占真实产能；签名防止截功 | 贡献/可见度双栏和材料时间线 |
| J `062–068` 矩阵、换老板与重组 | `matrix_handoff`：双线契约 → 权重锁定 → 交接 → 双签 → 映射完成 | 两位上司权重合计 100%；旧案卷不漂移 | 双线权重、交接签字和旧档映射 |
| K `069–081` 送达、申诉正义与裁员 | `notice_justice_case`：告身准备 → 送达 → 申诉时钟 → 独立复核 → 纠正/关闭 → 反报复观察 | 时间线不可改写；程序责任分级；反报复比较同口径后续动作 | 正式送达、复核结果和观察期状态 |
| L `082–091` 薪酬、奖金与长期激励 | `compensation_award`：公式锁定 → 资金预留 → 授予 → 递延/暂扣 → 支付/追索 | 同币种 debit = credit/refund；专项奖不能绕过预算 | 奖金对账单、付款状态和追索 receipt |
| M `092–097` 职级与双通道 | `career_track`：通道选择 → 资格 → 校准 → 晋升/半级/回专家岗 → 复审 | 晋升槽与薪酬、任命、权力互不冒充 | 通道、职级、复审与破格理由 |
| N `098–105` HC 生命周期 | `hc_slot`：申请分类 → 批准/冻结 → 招聘 → 占用 → 到期/回收/backfill | 授权 HC = 空缺 + 预留 + 已占 + 冻结/回收；不阻断原版生成人物 | 编制板、HC 来源和到期状态 |
| O `106–113` 人才盘点与继任 | `succession_plan`：关键岗位 → 候选池 → 准备度 → 代理试炼 → 就绪/失败 → 交接 | 高潜、关键人才、继任者分别存证；每岗位明确接替准备度 | 继任梯队、代理结果和知识移交 |
| P `114–120` 内部流动与新人落地 | `mobility_onboarding`：匿名申请 → 录用 → 放人期限 → 转岗 → 保护期 → 质量回写 | 转岗不能删除旧案卷；放人延期只有一次 | 内部应聘、交接、保护期和招聘质量 |
| Q `121–128` 管理者绩效文化 | `manager_certification`：新经理试运行 → 4-3-3 → 下属反馈 → 接班检验 → 认证/辅导/收权 | 只有合格天朝公爵以上拥有对象；团队高 KPI 不能洗掉报复或高流失 | 管理认证、管理幅度和团队气候 |
| R `129–134` 项目制与系统纠偏 | `project_governance`：提案 → 探索/承诺赛道 → 执行 → 止损/复盘 → 学习/追责 → 价值观察 | 唯一 owner；停止项目不自动算失败；共享指标只有一个仲裁 owner | 项目卡、止损理由和复盘结论 |
| S `135–145` 预校准与影子档位 | `shadow_calibration`：影子档 → 跨经理预校准 → 锚点冻结 → 例外/异议 → 待定终档 | 尾差、配额债和截止后事故按对称规则处理 | 初评/终评 diff、异议票和影子排序 |
| T `146–156` 反馈谈判与承诺债 | `feedback_commitment`：结果锁定 → 反馈会 → 签收/异议 → 行动项 → 兑现/违约 | 承诺有 owner、期限、资源与违约债；签收不等于认同 | 反馈纪要、行动时间线和承诺状态 |
| U `157–168` 晋升提名与预审 | `promotion_nomination`：达标 → 自荐/提名 → 占名额 → 部门预审 → 提交/撤包/淘汰 | 提名额度守恒；陪跑包和雪藏明星可被审计 | 候选包、额度、预审结果和经理命中率 |
| V `169–180` 晋升答辩与评委政治 | `promotion_panel`：组评委 → 回避 → 盲审 → 答辩 → 投票 → 结果/冷却/反馈 | 票数、否决规则、利益回避和答辩时间可复核 | 评委名单、票型、反馈 owner 和冷却期 |
| W `181–191` PIP 启动、毕业与复发 | `pip_case`：分诊 → 证据门槛 → 双签/拒签 → 执行 → 期中 → 毕业/复发/转岗/退出 | 经理承载量、支持预算、目标冻结与退出成本对账 | PIP 任务页、支持承诺、里程碑与结局 |
| X `192–204` 值守、故障与救火 | `incident_case`：值守排班 → 告警 → 定级 → 指挥 → 冻结时间线 → 复盘 → 行动项 → 复发 | 值守补偿和目标减免对账；纵火者不能拿完整救火功 | 事故报告、时间线、功劳归因和重复事故 |
| Y `205–216` 技术债与维护劳动 | `debt_item`：登记 → owner → 预算 → 修补/重做 → 验收 → 退役/计息 | 期末债 = 期初 + 新增 + 利息 − 偿还；维护与质量贡献可追溯 | 积弊账、偿债预算、验收与退役结果 |
| Z `217–228` 中台、共享官署与内部开源 | `platform_service`：服务提出 → 采用/分叉 → 迁移 → 双跑 → 使用/价值 → 分摊/事故结算 | 共享成本分摊合计守恒；创始人、贡献者、维护者分账 | 平台服务页、采用深度、迁移成本和事故半径 |
| AA `229–241` 数据口径与实验 | `metric_experiment`：口径定义 → 版本/对账 → 预注册 → 运行 → 冻结 → 解释 → 长尾关闭 | 分子、分母、时间窗和版本不可偷换；护栏与主指标分账 | 指标字典、实验报告、护栏和长尾结果 |
| AB `242–253` 加班、会议与在线表演 | `capacity_period`：产能计划 → 加班/会议申请 → 批准/影子执行 → 补偿 → 归一化 → 倦怠反馈 | 工时 = 产出 + 会议 + 学习 + 值守 + 休假；金币/调休/目标减免择一结算 | 工作负荷板、会议账、加班补偿和倦怠 |
| AC `254–265` 外包、派遣与借调 | `external_contract`：需求 → 合同类型 → 供应商 → SLA → 交付 → 转正/退出 → 移交 | 正式 HC 与影子 HC 分账；SLA 责任和个体责任分开 | 供应商履约、真实执行者和知识移交 |
| AD `266–277` 招聘、面试与 Offer | `recruitment_funnel`：requisition → 独立投票 → 校正 → Offer → 接受/拒绝 → 试用 → 延迟质量回写 | HC/Offer 预算预留；面试判断在新人后续表现中反结算 | 招聘漏斗、票型、Offer 状态和质量回写 |
| AE `278–289` 薪酬透明与发放纪律 | `pay_statement`：应付生成 → 到期 → 支付/延期 → 补发/纠错 → 薪酬申诉 → 关闭 | 应付 = 实付 + 欠付 − 退回；入离职折算和追溯补发有 receipt | 个人薪酬单、延期信用和薪酬申诉 |
| AF `290–300` 长期激励与流动性 | `lti_grant`：提名 → 授予 → Cliff → 归属 → 离职分类 → 流动性/回购 | 授予份额 = 未归属 + 已归属 + 没收 + 回购；组织/个人门槛双闸 | 长期激励单、估值三栏、归属和回购队列 |
| AG `301–311` 业务周期与重组折算 | `reorg_case`：重组前冻结 → 责任/容量拆分 → 静默期 → 旧档映射 → 归一化 → 关闭 | 拆分权重、工时和目标总量守恒；战略转向不倒改旧目标 | 重组前后对照、双帽容量和映射理由 |
| AH `312–322` 内部市场、离职与回流 | `internal_market_case`：岗位挂牌 → 保密申请 → 试运行 → 放人/返回 → 调任 → 校友/回聘 | 一人只能有一个活动流程；旧绩效保留；一次反 Offer 后必须放人 | 岗位市场、申请保密、回流关系和旧账 |
| AI `323–333` 学习、训练与知识扩散 | `learning_plan`：预算 → 报名 → 结课 → 应用 → 业务结果 → 授课/扩散 | 预算和受保护工时对账；证书不能直接兑换绩效 | 学习记录、应用证据、导师和知识扩散 |
| AJ `334–344` 需求入口与交付价值 | `demand_item`：入口 → 完成定义 → 估算 → 进入 WIP → 变更税 → 交付 → 采用 → 价值 | WIP 上限；范围/期限/质量三签；上线、采用、价值分别结算 | 需求板、阻塞归因、签收和价值观察 |
| AK `345–354` 制度运营与审计 | `policy_version`：草案 → 试点 → 生效 → 例外/抽查 → 测量 → 改版/迁移 | 例外自动到期；抽查与行政成本入经理分；旧记录映射显式 | 制度健康页、审计结果、通胀和版本差异 |
| AL `355–361` 制度极限与终局 | `constitution_case`：多周期事实 → 配额套用 → 翻案回流 → 经理集体行动 → 宪章 → 长期报告 | 旧案卷不可改写；翻案后配额回流守恒；宪章只改未来默认 | 《三六一绩效宪章》与十年制度报告 |

## 四、v2 runtime schema

现有 `tools/mechanism_choices/*.json` 继续只维护中英文政策选择文案、profile 和参考路线。当前运行语义权威由
`tools/zg361_domain_data.py` 与逐项 acceptance contract 共同组成，生成以下机器快照：

```text
tools/mechanism_runtime/runtime_001_120.json
tools/mechanism_runtime/runtime_121_240.json
tools/mechanism_runtime/runtime_241_361.json
tools/mechanism_domains/domains.json
```

每号 runtime 记录必须包含：

```json
{
  "id": 14,
  "domain": "C",
  "operation_key": "appeal_case_policy",
  "actor_role": "eligible_manager",
  "object_type": "appeal_case",
  "owner_scope": "reviewing_manager",
  "subject_scope": "assessed_official",
  "trigger_hook": "result_delivered",
  "applicability": [],
  "prerequisites": [],
  "conflicts": [],
  "choices": {
    "a": {
      "parameters": {},
      "allowed_from_states": ["delivered"],
      "to_state": "appeal_open",
      "deadline": {
        "kind": "scheduled_event",
        "days": 90,
        "on_due": "expire_appeal",
        "stale_guard": ["owner", "review_serial", "case_serial", "state"]
      },
      "transactions": [],
      "gameplay_effects": [],
      "visible_feedback": [],
      "ai_score_terms": [],
      "acceptance": {}
    }
  }
}
```

实际三条 choice 都必须完整填写。字段规则：

- `operation_key` 必须来自生成器白名单，runtime JSON 不接受任意 CK3 脚本文本。
- `deadline` 即使不适用也必须写 `kind = "none"` 并给出理由。
- `transactions` 即使为空也必须在 `acceptance` 中声明本项无守恒资源，防止漏做被当成无成本。
- 每号至少拥有一个非 `set_choice`、`ledger_delta`、`debug_log` 的 typed operation。
- 多个编号可以复用 operation，但“对象、hook、from→to、参数、事务、反馈”完全相同时必须显式声明 `alias_of`；否则静态 RED。
- 每条资源事务至少包含 `debit_account`、`credit_account` 或制度性 `sink`、`currency`、`amount`、`timing`、`receipt_key` 和 `refund_policy`。
- 每个 deadline 必须同时绑定 owner、cycle/case serial 与 expected state；过时事件只能留下 stale no-op marker。
- `visible_feedback` 不得为空；后台机制也至少需要在案卷、驾驶舱或 receipt 中可查询。
- `acceptance` 必须给出前置状态、动作、后置状态、资源/容量恒等式、期限负例、幂等负例和可见反馈键。

建议数据类接口：

```text
DomainSpec
MechanismRuntimeSpec
ChoiceRuntimeSpec
DeadlineSpec
TransactionSpec
FeedbackSpec
AcceptanceSpec
```

其中 `DomainSpec` 定义对象类型、owner/subject scope、状态集合、入口 hook、合法迁移、终态、容量上限及清理规则；`MechanismRuntimeSpec` 只能在该图中选择合法 hook 和迁移。

## 五、生成器与文件接口

已新增设计合同层：

```text
tools/zg361_domain_data.py
tools/zg361_operation_registry.py
tools/mechanism_domains/domains.json
tools/mechanism_runtime/runtime_001_120.json
tools/mechanism_runtime/runtime_121_240.json
tools/mechanism_runtime/runtime_241_361.json
common/scripted_effects/zg361_case_kernel_effects.txt
common/scripted_triggers/zg361_case_kernel_triggers.txt
```

其中前五项已落地；最后两份 CK3 case kernel/trigger 是下一施工项，尚不得写为已实现。

`tools/zg361_domain_data.py` 负责：

```python
load_domain_specs(mod_root) -> tuple[DomainSpec, ...]
load_runtime_specs(mod_root, domains) -> tuple[MechanismRuntimeSpec, ...]
validate_domain_graphs(domains) -> None
validate_runtime_coverage(mechanisms, domains) -> None
```

`tools/zg361_operation_registry.py` 负责把白名单 typed op 编译为固定 scope 安全模板，例如：

```python
compile_choice_ops(mechanism, choice) -> list[CompiledOperation]
render_transition_guard(operation) -> str
render_transaction(operation) -> str
render_deadline(operation) -> str
render_feedback_projection(operation) -> str
```

`tools/gen_361_mechanisms.py` 保持总编排器角色，增加：

```python
render_policy_configuration(...)
render_domain_runtime(domain, mechanisms)
render_domain_events(domain, mechanisms)
render_domain_values(...)
render_manifest_v2(...)
```

生成文件建议按领域拆分，避免继续膨胀单个百万字节 effect 文件：

```text
common/scripted_effects/zg361_generated_domain_a.txt
...
common/scripted_effects/zg361_generated_domain_al.txt
events/zg361_generated_domain_a_events.txt
...
events/zg361_generated_domain_al_events.txt
```

现有 `common/scripted_effects/zg361_effects.txt` 保留考核主循环，只在稳定节点调用总 dispatcher：

```text
cycle_open
cohort_locked
targets_locked
evidence_open
evidence_frozen
pending_grades
precalibration
calibration_complete
scoreboard_published
result_delivered
appeal_resolved
career_resources_settled
cycle_closed
```

每个 hook 进入时立即保存明确的 manager、subject、cycle 和 case scope；不得让 38 个领域长期依赖隐式 ROOT/PREV 传播。

`tools/gen_scoreboard_snapshot.py` 应扩展案卷 serial、周期、理由码、receipt 和分类 tab，但仍使用有限固定槽，不增加 361 个 HUD 按钮。

`tools/gen_zhongguo_acceptance_cases.py` 改为消费 v2 runtime/manifest，生成语义场景与断言；现有 aggregate portfolio 检查继续作为兼容 smoke，不再决定每号 `domain_runtime` 状态。

## 六、玩家、第二 AI 例外与爵位权限

### 管理权限

所有管理入口由生成器统一包装，禁止各领域自行手写弱化版 trigger：

```text
玩家管理入口：is_ai = no  + zg361_is_celestial_liege_trigger = yes
AI 管理入口：  is_ai = yes + zg361_is_celestial_liege_trigger = yes
受评对象：      zg361_is_reviewable_vassal_trigger = yes
```

AI 例外只覆盖本 mod 中符合条件的天朝制公爵及以上管理者，不能外推到其他政府、主 mod、白绮版或其他玩法。AI 不打开事件/GUI，不调用玩家互动；它只在真实领域对象到达决策点时调用该领域 resolver。

当前统一的“正直/勤勉选 A，专断/野心选 B，预算压力高选 C”只能作为旧配置兼容。v2 AI 必须结合领域事实、资源可行性、期限、人物关系、当前案件风险和政策版本计算，且每次结果保存理由码。

### 伯爵与男爵

伯爵、男爵可以：

- 被纳入直属 cohort；
- 提交自己的自评和证据；
- 签收自己的结果；
- 对自己的结果申诉；
- 履行自己的 PIP、转岗、学习或交接任务。

伯爵、男爵不能：

- 建立或拥有考核 cohort；
- 冻结别人目标或证据；
- 给别人定档、调档或分配 C；
- 发起别人的 PIP、末位退出、晋升、HC 或薪酬审批；
- 以互动直接改写同侪 KPI。

背靠背反馈若保留受评官员参与，只能形成 manager-owned 的待核验证据。正式评分、可信度校正、采纳和最终定档仍由合格直属上司执行。当前举荐/攻讦直接写同侪下期 KPI 的实现应在对应领域迁移时改造。

### 玩家路径

玩家管理者通过考核榜/制度驾驶舱进入上下文案件；玩家受评者通过告身、人物互动或案件通知处理自己的材料、申诉和任务。政策配置与案件裁决分开，避免“点一张政策卡就自动完成未来十年所有业务”。

## 七、四阶段施工与批量实机门

### Phase 0：内核迁移

实现 v2 schema、domain graph validator、case serial、事务 journal、deadline stale guard、hook dispatcher 和 manifest 分层状态。现有 361 配置继续兼容，但不升级任何领域语义状态。

本阶段只跑静态生成、图可达性、状态模型与资源恒等式测试，不启动 CK3。

### Phase 1：完整绩效季

先以现有计划中的 15 项垂直切片闭合内核：

```text
1, 2, 4, 7, 8, 9, 10, 14, 15, 18, 32, 33, 45, 49, 69
```

随后补齐 A、B、C、F、G、H、K、S、T、AK。最大限度复用当前 KPI、cohort、校准、告身、申诉、京察和考核榜。完成这组代码后一次 CK3 启动批量验收约十个领域，不为每项单独开局。

### Phase 2：职业、编制与人才

实现 D、L、M、N、O、P、Q、U、V、W、AE、AF。统一闭合晋升包、HC、PIP、薪酬、长期激励和人才流动的资源守恒。

完成整组静态门后一次 CK3 启动，使用同一批角色连续跑合法空缺、富裕/赤字、晋升成功/延期/失败、HC 冻结/回收、PIP 成败和奖金支付/退款。

### Phase 3：项目、组织与运营

实现 E、I、J、R、X、Y、Z、AA、AB、AC、AD、AG、AH、AI、AJ。一次启动内复用同一项目与组织变动，跑贡献、换老板、事故、技术债、平台、实验、工时、外包、招聘、学习和需求价值链。

各代码小批仍逐批跑静态门，但不逐项启动 CK3。

### Phase 4：终局与全量回归

实现 AL，并跨至少三轮运行目标棘轮、藏成果、事实/配额分离、申诉不加重、翻案配额回流和经理集体拒背 C。宪章只修改后续默认值，不重写旧案卷。

最后使用一次发布候选 CK3 启动连续重跑全部 38 领域和 361 条 reference scenario。只有明确 RED 才建立新 artifact 定向复跑，失败 attempt 必须保留。

## 八、批量验收门

### L0：schema 与生成

- ID 必须恰好为 1–361，domain 必须恰好为 38 个 A–AL。
- 每号对象、hook、from→to、期限声明、资源声明、反馈、玩家路径、AI 路径和验收映射齐全。
- 每个状态机所有状态可达，至少有一个终态；非法环必须显式声明。
- 每号至少一个非账本 typed operation；重复语义必须显式 `alias_of`。
- 生成输出可复现、脚本 BOM 正确、所有入口拥有统一权限 wrapper。
- 无宗教入口、无未授权 AI 入口、无伯爵/男爵管理入口。

### L0：模型与守恒

- 状态转换只允许合法 from→to。
- 重复执行不得二次扣钱、占 HC、占晋升槽、改档或退款。
- 过时 deadline 必须因 owner/serial/state 不匹配而 no-op。
- 金钱、国库、奖金、HC、晋升槽、提名额、管理容量、配额和长期激励份额分别满足恒等式。
- 申诉退款不超过原 receipt；配额换档和翻案回流不凭空产生或消灭名额。
- 存档迁移只把旧 choice 解释为政策配置，不伪造历史案件。

### L1：同一 CK3 启动内的语义 fixture

每号至少执行一条 reference route，但 PASS 必须验证领域对象和后果，而非 choice variable。每个领域至少覆盖：

1. 正常成功；
2. 拒绝或失败；
3. 到期；
4. 重复执行；
5. 旧 serial/stale event；
6. 资源或容量守恒；
7. 可见反馈 projection。

30、90、180、300、365 日等期限应分桶批量调度：同桶数十个案件一起等待和结算，避免为每项重启或单独快进。

权限矩阵必须同批验证：

- 玩家天朝公爵及以上管理入口 GREEN；
- 非独立 AI 天朝公爵管理入口 GREEN；
- 伯爵、男爵作为管理者 RED；
- 同一伯爵、男爵作为受评对象 GREEN；
- 非天朝政府管理入口 RED；
- 直属关系变化后旧 manager/case serial 不得被新上司消费。

### L2/L3：玩家可见与长期运行

- 按反馈表面类型抽检 GUI，不要求人工点击 361 次；但每号 manifest 必须映射到已经实点过的同构表面和具体字段。
- 实点考核榜、案卷、申诉/PIP、职业/HC、项目/运营、制度审计等入口，检查右窗、模态、人物跳转和关闭行为。
- 跨存读档、转封、上司死亡、重组和至少三周期，验证历史案卷、receipt、期限和映射不漂移。
- 宣传与发布录制使用史实角色，关闭并剥离测试决议、fixture GUI 和测试标签。
- release staging 中不得包含 acceptance-only 文件或 marker。

## 九、完成定义

某编号只有同时满足以下条件才算真正实现：

1. 政策配置可达；
2. 有所属领域的真实对象和合法状态迁移；
3. 参数、对象、期限和资源规则明确；
4. 对 CK3 人物、关系、国库、金币、贤能、压力、任命、容量或其他可玩状态产生实际后果；
5. 玩家能看到原因、当前状态、期限或 receipt；
6. 合格玩家管理者和授权 AI 管理者各有正确路径；
7. 伯爵、男爵只处于受评/自我响应路径；
8. 静态、模型、真实 CK3 fixture 和适用的 GUI/长期门均有可核验证据。

现有 14 本账继续有价值，但其定位应是跨领域气候汇总。最终的“361/361 完成”必须表示 361 个编号均已进入上述 38 个领域状态机并通过语义验收，而不是 361 个变量被置位或 35 种 payload 被重复执行。
