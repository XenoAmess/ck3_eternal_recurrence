# 361 二期全量实施总纲

状态：2026-08-30 建立。它把既有 361 条预研目录转换成可逐批施工、可批量验收、最终可归零
`not-implemented` 的执行账本。现实语境与去重依据见
[`361-next-version-research-audit-2026-08-30.md`](361-next-version-research-audit-2026-08-30.md)，38 个领域图见
[`361-domain-runtime-architecture.md`](361-domain-runtime-architecture.md)。

## 一、当前诚实基线

- 361/361 已有编号文案、三条政策选择与逐项 acceptance contract。
- 361/361 已有 v2 运行设计合同：领域对象、owner/subject、hook、合法迁移、A/B/C typed operation、期限、事务候选、反馈和负例。
- 运行设计合同是 `contract-complete`，不等于 CK3 玩法实现。
- 当前领域运行时仍精确为：`partial × 4`（001/018/069/357）与 `not-implemented × 357`。
- 当前玩家闭环仍为 `partial × 361`；任何批次只有在产品脚本、共享表面和同批 CK3 fixture 证据一起 GREEN 后才升级。
- v0.4 全量功能完成前不做七语发布审计、Workshop 上传、宣传片或发布物料重制。

机器合同来源：

- `tools/zg361_domain_data.py`：38 个 DomainSpec、资源候选、状态图和全量计划编译；
- `tools/zg361_operation_registry.py`：封闭的 domain recipe 与 primitive whitelist；
- `tools/mechanism_domains/domains.json`：生成的 38 领域快照；
- `tools/mechanism_runtime/runtime_001_120.json`、`runtime_121_240.json`、`runtime_241_361.json`：361 条生成快照；
- `docs/361-mechanism-manifest.json`：把 `runtime_plan` 与真实 `domain_runtime` readiness 分栏，防止设计完成冒充实装。

## 二、八批精确覆盖

剩余 357 个 `not-implemented` ID 的集合必须精确满足：

```text
40 + 40 + 23 + 59 + 56 + 62 + 73 + 4 = 357
```

| 批次 | 领域与精确 ID | 本批新实现 | 同批收口既有 partial | 累计 complete | 剩余 not-implemented |
|---|---|---:|---|---:|---:|
| B1/R1 完整绩效事实季 | 002–006、007–013、037–047、048–053、135–145 | 40 | 001、357 | 42 | 317 |
| B2/R2 送达、申诉、反馈与 PIP | 014–017、070–081、146–156、181–191、358–359 | 40 | 018、069 | 84 | 277 |
| B3/R3 管理者与制度 | 032–036、121–128、345–354 | 23 | 无 | 107 | 254 |
| B4/R4 晋升、职级与现金 | 019–025、082–097、157–180、278–289 | 59 | 无 | 166 | 195 |
| B5/R5 HC、继任、流动、学习与递延功赏 | 098–120、290–300、312–333 | 56 | 无 | 222 | 139 |
| B6/R6 项目、贡献、矩阵、指标、重组与需求 | 026–031、054–068、129–134、229–241、301–311、334–344 | 62 | 无 | 284 | 77 |
| B7/R7 事故、积弊、共享官署、工时、外包与招聘 | 192–228、242–277 | 73 | 无 | 357 | 4 |
| B8 终局 | 355–356、360–361 | 4 | 无 | 361 | 0 |

依赖顺序固定为 `Phase 0 → B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8`。B6 虽有部分模块可理论并行，
但这是单人项目，所有批次共用生成器、案卷内核和有限 GUI 表面；为避免长期分支、双写和回合成本，不并行施工。

## 三、共享内核，不造 361 个换皮弹窗

### 1. 两层 typed operation

底层 primitive 只允许从封闭白名单取值：case create/transition、binding freeze、record version、policy bind/parameter/defer、
evidence attach/freeze、score compute、rule evaluate、cohort lock、vote record、deadline schedule/expire、notice deliver、
access project、transaction reserve/settle/refund、capacity reserve/release、obligation open/resolve、candidate advance、
audit open/resolve、timeline append、feedback project、relationship apply 与 modifier apply。

上层只建立 38 个领域 recipe。每个编号选择一个 recipe、mechanism-specific variant、hook、状态迁移、参数、事务和反馈；JSON
不得携带任意 CK3 脚本文本。A/B/C 三路都必须经过 registry：C 是本机制自己的 `policy.defer`、明确复议期限和制度债案件，
不能只加共享总账。

### 2. 真机制最低门槛

每个编号必须同时具备：

1. 一个真实领域对象与冻结 owner/subject/cycle/case identity；
2. 一个实际消费它的生命周期 hook；
3. A/B/C 至少一个会改变状态、容量、事务、ACL、期限、证据、关系或 modifier 的 typed operation；
4. 政策参数必须改变后续 transition，view/notice 项必须改变字段级访问或可查询投影；
5. 一个复用共享表面的可见字段和逐项 acceptance route。

只 `set choice`、改 14 项气候总账、打一条 debug marker 或换一段互联网黑话，均为 RED。

### 3. 有限玩家表面

真实玩家交互集中在少数 cohort/case 门：目标与事实、校准、告身/申诉/PIP、职业/HC、项目/运营、制度审计。后台记录、期限到期和
审计汇总进入表格行、案卷或通知；不得制造 361 个定期弹窗。考核榜只增加内页，不增加新的 HUD 顶层按钮。

## 四、B1：42 项完整绩效事实季

B1 是下一项施工，不再挑零散卡片。它在一个周期内闭合 A/B/G/H/S，并让既有 001/357 从 `partial` 收口。

逐号 hook、跨周期阶段、共同上司 barrier、考核榜字段和批量测试的权威施工细则见
[`361-b1-runtime-spec.md`](361-b1-runtime-spec.md)。如果通用 Phase 0 计划与该细则冲突，以 B1 细则为准；尤其 #357 不得走
AL 的申诉退款迁移。

### 生命周期

```text
cycle_open / targets_locked
→ evidence_open（目标、期中、自评、互评邀请）
→ evidence_frozen（八项事实、互评封存、cohort 锁定）
→ pending_grades（绝对事实档）
→ precalibration（配额快照、影子档、议程、尾差与债）
→ calibration_complete（换档、回避、隔级复核、事实→配额理由）
→ scoreboard_published（公示 ACL、初终档 diff、反馈债与机会审计）
```

校准只允许交换边界两人；3.75/3.5/3.25 的人数在换档前后分别守恒。事实档永不被配额档覆盖。

### 逐号 recipe

- A：001 `evidence.freeze_sheet`；002 `goal.lock_contract`；003 `goal.rebaseline_once`；004
  `self_review.submit_gap`；005 `scorecard.bind_role`；006 `baseline.freeze_adjust`。
- B：007 `peer.invite_back_to_back`；008 `evaluator.normalize_credit`；009 `calibration.open_swap`；010
  `quota.force_or_protect`；011 `oversight.return_to_owner`；012 `reviewer.recuse`；013 `disclosure.apply_acl`。
- G：037 `quota.exchange`；038 `cohort.pool_small`；039 `cohort.lock_amend`；040 `cohort.apply_leaver_rule`；041
  `newcomer.route`；042 `quota.detect_rotation_debt`；043 `attention.reserve`；044 `calibration.blind_snapshot_reveal`；045
  `feedback.debt`；046 `opportunity.audit`；047 `evidence.window_freeze`。
- H：048 `feedback.capacity_reserve`；049 `feedback.seal_deadline`；050 `feedback.detect_reciprocity`；051
  `feedback.anonymity_threshold`；052 `feedback.shape_preserve`；053 `feedback.route_development_or_pay`。
- S：135 `shadow_grade.open`；136 `precalibration.open`；137 `agenda.freeze`；138 `quota.round`；139
  `quota.debt_carry`；140 `reorg.quota_owner_freeze`；141 `executive.must_review`；142 `grade.pending_milestone`；143
  `board.symmetric_reopen`；144 `dissent.record`；145 `shadow_rank.freeze`。
- AL 兼容 adapter：357 `grade.resolve_fact_then_quota`，复用已验过的事实档/配额档分离与 grade guards，不重写首纵切链。

真实交互只保留每周期目标、事实冻结、校准、发布四个 cohort 级门；互评、审计和债务默认表现为面板行或通知，只有条件性个案弹窗。

## 五、B2–B8 的可见闭环

- B2：直签、异议、拒签→D+7 见证、target-bound 申诉时钟、同案 receipt 幂等、申诉不加重、配额回流、PIP 支持/中期/毕业/
  复发/转岗/退出、反报复。国库、个人金币、贤能与退款逐项核对。
- B3：经理只消费上一轮团队快照，不得同轮递归；京察免费但默认必须举办，拒办给上司好感下降及下一轮重大扣分理由；授权 AI
  经理同规则；制度例外到期、试点、版本迁移和行政成本入账。
- B4：资格→提名→预审→评委→答辩/投票→成功或失败冷却；HC、奖金先预留，失败释放；职级、任命、权力、现金分账；
  应付、实付、欠付、补发和薪酬申诉守恒。
- B5：使用真实空缺、候选与现任角色；HC 到期/backfill、继任代理、匿名内投、放人、保护期、学习应用、递延功赏的 cliff/
  归属/离职分类/回购；旧案、存读档和换上司均不漂移。内部顺序 N→O/P/AH/AI→AF。
- B6：贡献份额、签名版本、双线权重 100%、项目止损不自动记差绩效、指标分母/时间窗冻结、实验样本容量、重组映射、WIP
  以及上线→采用→价值三阶段。
- B7：用一条相连长链验证“缺编/工时→外包或招聘→共享官署/积弊→事故→复盘行动→质量回写”；必须使用真实角色、职位和领地
  输入，闭合值守补偿、工时、shadow HC、Offer/HC 资金守恒。技术债翻译为领地积弊与维护劳动，共享平台翻译为共享官署/
  共同设施，禁止只有现代术语。
- B8：多周期目标棘轮、截止套利、成功申诉后的配额回流、经理集体拒背 C 的真实个人/团队代价，以及只改变未来默认的
  《三六一绩效宪章》。最后执行全域一次启动 smoke、共享表面抽样与三周期长测。

## 六、批量验收矩阵

### 全局 L0

1. ID 恰好 001–361，领域恰好 38 个，八批集合无重叠无遗漏；
2. DomainSpec 全状态可达，终态和清理合法；
3. 每号 kind/roles/native binding/dependency/source 齐全，已实现项 A/B/C 全 typed operation，alias 精确且无环；
4. deadline 绑定 owner、subject、cycle、case、expected state，stale 必须 no-op；
5. transaction 满足 debit=credit/sink、receipt 唯一、refund≤settled；容量、配额、权重与 WIP 守恒；
6. 玩家和授权 AI 的天朝制有地公爵及以上可管理；伯爵、男爵管理入口 RED，但自有受评案卷处理 GREEN；
7. 生成可复现、脚本/YML BOM、中英键、scope/hook consumer 齐全；
8. readiness diff allowlist 只能提升当前批次 ID，禁止全表状态漂移；
9. 首纵切迁移和旧存档兼容。

### 每号与每域

- 每号至少一条 CK3 reference route 返回 object ID、operation key、pre/post state 与 visible-feedback key；
- 每个共享 recipe 至少对 A/B/C 各跑一条 live；
- 每域同批覆盖 normal、denied/illegal、due、duplicate、stale、resource/capacity、feedback 与 save/load；
- 不做 361 次人工点卡，也不为每号重启游戏。

### 每批一次 CK3

fixture 只能写前置，产品 effect 必须产生后置。同一局创建多个 bounded case slot，把 D+7/D+30/D+90/D+180/D+300/D+365
期限分桶一起推进。动作前取 MCP snapshot，动作后等独立 ACK，再读取新 revision；失败 attempt 全保留，关闭真实 blocker 后才重跑同矩阵。

B1 的队列矩阵包含 1/2/3 人、4 人合池及 7/14/23 人；23 人必须严格 `7/14/2`。另验八项和=KPI、目标版本不可倒改、匿名
阈值、评价形状、利益回避、盲审→实名、尾差与跨期债、事实/配额分离、考核榜内页关闭重开和无新 HUD 按钮。

## 七、readiness 与发布门

- 每批 L1 GREEN 后，才把当批 `domain_runtime`、`player_visible_loop` 升为 `complete`，并令 `runtime_evidence ≥ fixture-live`。
- B1 后 partial 只允许剩 018/069；B2 后 partial 必须为 0；B8 后 complete=361、not-implemented=0。
- `fixture-live` 不得冒充 `production-live`；自然路径长期证据单独记账。
- 只有 B8 和全量回归完成后，才恢复七语发布审计、release staging、Workshop、宣传片和最终实机截图。
