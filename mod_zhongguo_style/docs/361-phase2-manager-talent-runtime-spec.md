# 361 二期：管理者、人才流动、学习与制度运营 L0 语义模型

状态：2026-08-30，`python-l0-only`。本包只证明纯 Python 参考模型中的确定性语义、状态守卫和守恒；**没有**接入 CK3 effect/event、考核榜、MCP 或实机 fixture，不能把下表写成 `domain_runtime complete`、`fixture-live` 或玩家闭环完成。

权威实现与测试：

- `tools/zg361_phase2_manager_talent_model.py`
- `tools/test_zg361_phase2_manager_talent_model.py`

## 一、精确范围

共 37 项，集合必须严格等于：

```text
032–036（F，5 项）
312–322（AH，11 项）
323–333（AI，11 项）
345–354（AK，10 项）
```

不包含 Q `121–128`，该范围由职业/HC 模型负责。模型内 `EXPECTED_MECHANISM_IDS`、标题、领域和 operation 四张常量表必须同集合且逐号 operation 唯一。

| ID | 模型 operation | L0 场景的核心断言 |
|---:|---|---|
| 032 | `manager.score_frozen_team` | 直属上司只消费严格早于本轮的七项团队冻结汇总；拒办京察按保存的上司/年份精确扣 50 且只消费一次；孙级个人 ID 进入上级榜即 RED |
| 033 | `manager.explain_profile_decision` | 五类画像给出可复算理由码；每项修正受硬证据 cap 限制；关系覆盖只留一次理由与申诉风险 |
| 034 | `manager.freeze_nine_box` | 至少两轮冻结绩效与冻结潜力形成九宫格；只读历史，不改 KPI、档位或资源 |
| 035 | `manager.freeze_distribution_mode` | strict/relaxed/off/mixed 分开；严格制 10%，`n>=5` 至少一名末位；混合制全员达标仍排名但减轻后果；三档人数守恒 |
| 036 | `manager.compile_decade_report` | 同 owner 十个连续且唯一年度日志汇总；奖金净流为逐年流入减流出；换 owner 不串账 |
| 312 | `market.publish_real_vacancy` | 挂牌带真实 HC、汇报线、薪酬带与目标；假挂牌降市场信用；一个 vacancy 只录用一次 |
| 313 | `market.freeze_structured_reference` | 成果、风险、PIP、交接结构化冻结；隐瞒进入洗绩效审计，报复软话进入反报复审计 |
| 314 | `market.offer_relocation_package` | 受评者本人只响应一次；接受才原子支付；拒绝不扣绩效；成本同时扣组织国库与负责经理个人金币 |
| 315 | `market.run_bilateral_trial` | 90 日试运行冻结三方退出权；源/目标分功合计 100%；失败返岗而非自动 3.25 |
| 316 | `market.freeze_pay_mapping` | 接受前冻结保薪/分期/即时映射；专业底薪和岗位津贴分账；历史实付不可追溯改写 |
| 317 | `market.project_stage_acl` | 初筛/终面/录用分阶段 ACL；提前泄露后无新证据降评触发反报复审计；访问均留日志 |
| 318 | `market.consume_application_slot` | 每轮两次正式申请；撤回仍占一次；探索面谈不占槽；经理超时必须返还受评者名额 |
| 319 | `market.counteroffer_then_release` | 原团队只有一次反 Offer；拒绝后逾期卡人扣经理人才输出；接受后逾期/未兑现承诺同样扣分 |
| 320 | `market.aggregate_exit_voice` | 实名/匿名/拒答分流；单条不定罪；达到最小同类样本才审计；重分类保留原始理由 |
| 321 | `market.maintain_alumni_relationship` | 仅经同意者可联系；每周期维护费双付款且一次；lead 幂等；删除联系投影不能洗掉羞辱史与人才声誉 |
| 322 | `market.open_returnee_case` | 旧绩效、离职原因、旧舞弊与外部新证据永久回链；同一人只有一个活动回流流程和一个新 cohort |
| 323 | `learning.allocate_dual_budget` | 金币池与受保护工时池双守恒；每笔培训费双付款；结课标签本身不加绩效 |
| 324 | `learning.advance_three_stages` | 严格按结课→应用→业务结果；无应用不能造业务结果；只有应用/结果兑现绩效 |
| 325 | `learning.assess_practical_competence` | 证书不能替代实操；成熟成果可免测；题目失真追培训 owner，不自动把员工塞 C |
| 326 | `learning.settle_conference_adoption` | 差旅费双付款并记离岗机会成本；只有带回产物被采用才形成组织贡献；曝光和外流风险分栏 |
| 327 | `learning.attribute_teaching_impact` | 授课工时扣容量；听课、应用、影响分账；教师与应用者份额合计 100% |
| 328 | `learning.settle_community_adoption` | 跨组公共产物必须有维护者；贡献工时不超各自容量；采用后才计跨组影响 |
| 329 | `learning.match_cross_team_mentor` | 一名学员同时一个导师；只允许一次冲突换导师且不得重置结束日；应用后才给导师育人信用 |
| 330 | `learning.settle_reskill_route` | 再技能化/外招路线实际扣成本且角色不复制；培养失败保留旧履历，不自动 3.25 |
| 331 | `learning.borrow_protected_time` | 受保护学习时间与交付容量守恒；只有真实危机可借；下轮等额补回，逾期扣经理分 |
| 332 | `learning.run_safe_succession_drill` | 演练明确为 safe simulation；现任最多一次紧急否决；失败只生成发展缺口，不算真实事故/C |
| 333 | `learning.settle_training_commitment` | 高价培训费双付款；返还额按月递减且不超原 receipt；组织裁撤豁免；无工作应用不计绩效 |
| 345 | `policy.freeze_next_cycle_calendar` | 年度为一次终评+一次轻 Check-in；半年/季度实例数精确；同周期玩家/AI 工作合批；只从下一完整周期生效 |
| 346 | `policy.consume_material_offcycle_signal` | 仅重大功过建案；即时奖励/调查/调目标三选一；下一正式周期消费一次且不重跑全 cohort |
| 347 | `policy.consume_override_point` | 每次 Override 同时点名受益者、承担者和理由；点数不可超预算，排名集合/配额中性；翻案回写下轮额度 |
| 348 | `policy.expire_or_renew_exception` | 例外绑定 owner/cycle/case/state/expiry；无新事实到期恢复默认；续期需新证据与新日期；旧 token 只 stale no-op |
| 349 | `policy.run_reproducible_audit` | 随机+高风险抽样由 seed 复现；透明只降比例而不免审；工时入行政成本；clean case 增制度信任 |
| 350 | `policy.version_benchmark` | 标杆只能以新版本从未来周期生效；旧值/公式/版本不可重算；变化必须有解释码 |
| 351 | `policy.measure_regional_pilot` | 试点/对照公爵领互斥；指标预注册；所有区域、所有指标齐全后才计算差异 |
| 352 | `policy.map_immutable_history` | 原值、原公式、原制度版本永久保存；可比映射另建层，或显式开启新序列断点 |
| 353 | `policy.charge_admin_capacity` | 填表、会议、申诉、校准、打断工时之和真实扣治理容量；错误/翻案反弹回写经理分 |
| 354 | `policy.recompute_fairness_metrics` | 从原始送达、申诉、翻案和离职原因重算；汇总差异标刷数；主动披露且完成修复后才给长期信用 |

## 二、共享硬合同

### 1. 身份、权限与第二 AI 例外

每个可变案件冻结 `owner_id + subject_id + cycle_serial + case_serial + expected_state`。玩家管理入口只接受天朝制有地公爵及以上；授权 AI 也必须满足同一爵位/政府边界，且只能走无 GUI 的 `background` 通道。伯爵与男爵可作为受评者处理自己的转岗、学习和回流响应，但调用任何管理命令均返回 `permission-denied`。

经理本人仍是受评对象：F 案件的 owner 是其直属合格上司，subject 是该经理。上级经理榜只接收上一轮团队汇总，不接收孙级官员个人事实，避免同轮递归和皇帝榜越级展开。

### 2. 京察合同

京察本身没有费用，也不创建金币 receipt。玩家默认必须举办；若明确拒办，立即形成上司好感 `-25` 和下一轮管理 KPI `-50` 的重大理由。扣分绑定拒办时保存的上司与 mandate year，仅在匹配的下一轮经理考核中消费一次。合格 AI 经理静默举办，不允许选择拒办。

### 3. 原子执行、期限与幂等

`GuardedCase.apply()` 顺序固定为：

```text
duplicate action → stale identity/state → legal-state check → read-only precheck
→ commit → record action serial → transition
```

任何 typed RED 发生在 commit 前，资源和案件状态必须保持原样。重复 action serial 是 `duplicate-action` no-op；owner、subject、cycle、case 或 expected state 不匹配是 `stale-token` no-op。例外期限另外绑定 exception ID 和 expiry day，续期不会让旧 token 复活。

### 4. 国库与负责经理双付款

调任、校友维护、学习预算、外部会议、再技能化和高价培训等实际金币成本统一经过 `DualPayerLedger`。总额至少 2，组织国库和负责经理个人金币的分摊都必须为正；任一方余额不足时整笔 RED，不能只扣一边。退款/追回以原 receipt 为上限，并按原分摊回到两方。

### 5. C 路线与诚实边界

`PolicyDebtBook` 为 37 项提供统一的延期参考：不创建领域结果，不修改 KPI/历史或暗中扣资源，只按 `mechanism + manager + cycle` 登记一次制度债和下一周期复议 serial。它仍只是 L0 合同；CK3 实装时必须由真实案卷、期限事件和制度驾驶舱消费。

## 三、状态族

```text
F:  SNAPSHOT_READY → MANAGER_SCORED → REASON_CODED → NINE_BOXED → REPORTED
AH: POSTED → APPLIED → TRIALED → RELEASE_DECIDED → MOVED → ALUMNI → CLOSED
AI: BUDGETED → ENROLLED → COMPLETED → APPLIED → MEASURED → SPREAD
AK: DRAFTED → PILOTED → EFFECTIVE → AUDITED → MEASURED → MIGRATED
```

同一领域的不同编号可在独立 bounded case 上消费同构迁移；测试不要求用一只对象伪装 37 个业务事实。旧历史记录、原榜、原公式和原始离职原因只读冻结，新版本、新映射和新周期另建引用。

## 四、L0 验收结果与未完成项

验证命令：

```powershell
py -m py_compile mod_zhongguo_style/tools/zg361_phase2_manager_talent_model.py mod_zhongguo_style/tools/test_zg361_phase2_manager_talent_model.py
py mod_zhongguo_style/tools/test_zg361_phase2_manager_talent_model.py
git diff --check -- mod_zhongguo_style/tools/zg361_phase2_manager_talent_model.py mod_zhongguo_style/tools/test_zg361_phase2_manager_talent_model.py mod_zhongguo_style/docs/361-phase2-manager-talent-runtime-spec.md
```

当前结果：51/51 unittest GREEN，其中 37 个分别命名为 `test_mechanism_NNN`；`py_compile` GREEN；三文件 UTF-8 BOM。测试另覆盖完整权限矩阵、经理也被考核、京察拒办、全 ID 延期幂等、stale/duplicate、布尔值不得冒充整数、双付款原子失败、冻结快照、四种分布模式、受保护工时 RED 原子性、孙级事实隔离和 receipt 退款上限。

尚未完成：CK3 生成器/effect/event、本地化、考核榜页签、MCP 查询/动作口、同一启动内的真实角色 fixture、存读档与长期轮次。因此 manifest readiness 不应由本文件自动升级。
