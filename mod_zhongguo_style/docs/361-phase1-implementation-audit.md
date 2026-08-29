# 361 Phase 1 首批垂直切片实现审计

> 审计日期：2026-08-29（Asia/Shanghai）
> 审计类型：static audit
> 审计范围：`mod_zhongguo_style` 现有 CK3 脚本、生成器、机器可读验收合同与既有实机报告
> 实机边界：本次只读审计未启动 CK3、未生成新的 live artifact，也不把既有 fixture 证据扩写为领域语义实机通过。

本文聚焦 Phase 1 首批十五个垂直切片：`001`、`002`、`004`、`007`、`008`、`009`、`010`、`014`、`015`、`018`、`032`、`033`、`045`、`049`、`069`。目标是逐项回答：现有代码中哪些真实 hook、effect、变量和 GUI 可以复用，哪些领域对象、状态、期限、资源与反馈仍然缺失，以及最小新增文件和作用域风险是什么。

## 一、结论与证据边界

361 条机制尚未完成领域玩法实现。当前已经成立的准确表述是：

- 361 项编号、设计文案、A/B/C 政策选择和本地化目录已经完成；
- 361 个参考政策选择及其共享组织账投影已经在冻结 CK3 fixture 中执行；
- 现有实机 PASS 证明 choice 变量、14 本组织账、组合校验和与幂等性进入了真实 CK3 引擎；
- 它不证明 361 个领域对象、状态机、期限、资源事务和玩家可见闭环已经实现，也不证明 1083 个 A/B/C 分支均已逐一验收。

静态证据如下：

1. `tools/zg361_mechanism_data.py` 只有 17 个 `PROFILE_DELTAS` profile；每个 profile 复用一套 A/B payload，361 条 C 路全部复用同一 `DEFER_DELTAS`。实际只有 `17 × 2 + 1 = 35` 种账本 payload。
2. `tools/gen_361_mechanisms.py` 的每号 choice effect 只设置 `zg361_mechanism_NNN_choice`、修改共享组织账、增加配置计数与 checksum，并写入编号化 debug marker。
3. `tools/gen_zhongguo_acceptance_cases.py` 的 361 批量 fixture 逐号只检查 choice 值，随后检查账本总和、checksum 和重复部署幂等性。
4. `tools/gen_361_mechanisms.py` 生成 manifest 时明确给出：

   ```text
   catalogue            = complete
   policy_configuration = fixture-live
   ledger_projection    = fixture-live
   domain_runtime       = not-implemented
   player_visible_loop  = partial
   ```

5. `docs/361-domain-runtime-architecture.md` 已记录同一诚实边界；`docs/361-mechanism-implementation-manifest.md` 对 361 项均未把 `domain_runtime` 升级为已实现。

因此，#009、#014、#018 等编号虽然各自拥有相似的真实基础玩法内核，也不能称为该编号已经实现：对应 `zg361_mechanism_NNN_choice` 目前并不控制那些内核，只控制共享账本变化。

## 二、权限矩阵与第二 AI 例外

| 角色/入口 | 当前静态结论 | Phase 1 要求 |
|---|---|---|
| 玩家天朝制公爵及以上管理者 | GREEN。`zg361_is_celestial_liege_trigger` 要求天朝政府、有地、在世、最高头衔至少公爵。 | 所有玩家管理 operation 必须继续同时要求 `is_ai = no` 和统一 manager trigger。 |
| AI 天朝制公爵及以上管理者 | GREEN。年度 dispatch 对合格 AI 走后台 review，不要求独立或皇帝；既有报告也有非独立 AI 公爵实机证据。 | 这是本 mod 经所有者授权的第二个 AI 例外，只能覆盖本 mod 的合格 AI 管理者，不得外推到其他政府或其他 mod。 |
| 直属伯爵、男爵作为受评对象 | GREEN。其直属上司满足 manager trigger 时可进入 `zg361_is_reviewable_vassal_trigger`。 | 可以提交自己的自评/证据、签收自己的结果、申诉自己的结果、履行自己的 PIP；不得执行 manager operation。 |
| 伯爵、男爵建立 cohort、定档、分配 C、发起他人 PIP | 正式考核入口为 RED；其爵位无法通过公爵门槛。 | 新 runtime effect 自身也必须有统一权限 wrapper，不能只依赖上游事件或决议安全。 |
| 公爵同时受评并管理下属 | GREEN。只要其直属上司合格，公爵既可作为 subject，也可拥有自己的直属 cohort。 | manager case 与其本人被上司考核的 subject case 必须使用不同 owner/case serial，不能混用 ROOT。 |
| 伯爵、男爵参与背靠背反馈 | 当前 `recommend`/`slander` 可直接写同侪下期 KPI，和最终权限合同冲突。 | 只能提交 manager-owned 待核验证据；采纳、信用校正、加权和最终定档仍由合格直属上司执行。 |

当前生成的政策事件和决议入口使用了 manager trigger，AI batch 也只从 AI review 结算链进入；但生成的内部 choice effect 本身没有权限 guard。Phase 1 应统一生成三类公开 wrapper：

```text
player_manager_operation = is_ai=no  + eligible manager
ai_manager_operation     = is_ai=yes + eligible manager
assessed_self_response   = reviewable subject + matching owner/case serial
```

内部状态迁移 effect 可以保持私有，但不得成为无 guard 的跨域公共入口。

## 三、十五项逐项映射

| ID | 可复用的真实 hook / effect / 变量 / GUI | 缺失对象、状态、期限、资源与反馈 | 最小施工落点与作用域风险 |
|---:|---|---|---|
| 001 KPI 分项证据单 | `zg361_compute_kpi_effect`；`zg361_kpi_value`；人物变量 `zg361_kpi`、`zg361_efficiency`、`zg361_values`、`zg361_last_reviewer`、`zg361_last_review_serial`、`zg361_last_grade`；固定考核榜的 KPI/rank/values/grade 槽。 | 缺 `evidence_sheet_id`；治理成果、效率、成长、协作、价值观、京察履责、奖惩、政治修正八类冻结分项；每项事例 ID/来源日/符号/数值；合计校验；供申诉、PIP、晋升包引用的持久 ID；告身明细。 | 把聚合 KPI 拆为八个可冻结 script value，在 compute 时写入 `review_case`；榜单增加只读详情投影。当前 compute 依赖 live `liege` 和隐式 ROOT，转封或玩家校准延迟期间存在 reviewer 漂移风险，必须在 hook 入口显式保存 manager、subject、review serial。 |
| 002 年度目标责任书 | 京察年度 dispatch、mandate year/reviewer、review serial、现有治理 KPI。 | 每名 subject 的 `goal_contract_id`、方向、强度、期初基线、权重、截止日、接受/协商/保守回应、完成率、3.75 硬上限。 | 必须先把当前单 tick review 拆为跨周期流程：上轮结算后开启下轮目标，下一次京察才消费它。若在 `zg361_run_review_effect` 内先立目标再立刻评分，只是伪闭环。玩家/AI manager 负责冻结目标；伯爵、男爵只响应自己的合同。 |
| 004 自评与认知差 | `zg361_pending_grade`、最终 `zg361_last_grade`、KPI、values 和校准前事件入口可复用。 | `self_review_id`、自评档位、代表成果、提交日、一次性提交锁、认知差、可信度/可见度修正、上司回应、稳定 AI 自评策略。 | 在 `precalibration` 前开放一次 subject-owned 提交，manager-owned review case 只引用其冻结副本。修改 pending/final grade 不得反写自评。伯爵、男爵只能提交自己，不能替别人自评或采纳证据。 |
| 007 背靠背 360 邀评 | `zg361_recommend_interaction`、`zg361_slander_interaction` 的同侪交互表面；`zg361_has_ranked_peer_cohort_trigger` 的直属 cohort 判定。 | `peer_review_id`、真实共同战争/治理任务 ID、邀请来源和额度、subject/evaluator、业绩/协作/价值观三维分、事例、匿名展示、去重、10%–15% 权重 cap、manager 采纳状态。 | 重写举荐/攻讦，使其只创建 peer evidence，不再直接写 recipient KPI。最大事实阻点是目前没有可靠的真实共同任务索引；不能以“同一上司”冒充协作证据。评价者即使是伯爵/男爵也只提交，不能加权或定档。 |
| 008 评价者手松手紧与信用 | #014 的 regrade 结果、`last_penalty_serial` 可作为翻案事实；#007 的原始互评可作为输入。 | `evaluator_profile_id`、样本数、历史均值/方差、命中率、翻案率、统计截止轮、中性先验、可信权重、原分到修正分的可逆映射、反馈标签。 | profile 应存在 evaluator 人物 scope，并按 peer/appeal ID 增量更新。翻案只能回写一次，不能追改原留言。不能把 profile 存在 manager 或 title 上，否则换任会错误继承。 |
| 009 校准会驾驶舱 | `zg361.10–12`；稳定唯一 rank；`pending_375/35/325_n`；`top_cut`、`top_cut_next`、`bottom_slots`；`zg361_calibrate_promote_effect` 和 `zg361_calibrate_demote_effect` 的配额中性交换；现有考核榜表格。 | `calibration_id`、owner/review serial、open/closed/deadline state、目标/360/趋势/申诉风险列、交换双方与 reason trail、旧轮/双击/缺对象可见失败原因。 | 这是复用程度最高的一项。扩展榜单生成器输出预发布槽和交换记录，保留现有原子 effect。事件必须校验 owner+review serial+round state；不能只依赖当前 liege 或临时 scope。 |
| 010 背 C 与护人 | bottom slots、pending grade、新人保护 `zg361_newcomer_this_cycle`、demote 原子交换。 | `forced_bottom_case_id`、全员绝对达标判定、明确承担者/保护对象、威望 transaction/receipt、下轮 manager KPI 债、怨恨/申诉/流失 reason code。 | 在 calibration round 内建立 forced-bottom case。护人后仍须有另一人承担 C，配额不变。新人保护优先于 B 路“压给新人”文案，只能选合法边缘人。顶级独立领主没有可考核其管理 KPI 的上司，不能创建 orphan debt，只能支付实际威望等即时成本。 |
| 014 绩效申诉案卷 | `zg361_appeal_interaction`；`zg361_appeal_regrade_to_35_effect`；三笔固定收据退款；PIP/3.25 modifier 移除；managed/received 汇总和固定榜槽修正；现有 stale guard。 | `appeal_case_id`、五类 reason code、冻结附件、提交→沟通→复核→终态、申诉期限、独立复核席、失败/恶意申诉信用、AI subject 自我响应。 | 保留现有退款内核，外围新增 appeal case。当前逻辑使用“当前 liege”和其当前 review serial；subject 转封后原 reviewer 的旧案无法正常处理。所有退款、榜单修正和责任必须改用显式 original owner/case serial。 |
| 015 PIP 改进任务书 | `zg361_pip` 一年 modifier、`zg361_streak_bottom`、`zg361_eliminate_n`、降岗/退出/延期 effect。 | `pip_case_id`、任务类型、subject 权限证据、里程碑、支持、复盘点、截止日、接受/协商/拒绝，以及 success/failure/timeout/refused 四个互斥终态。 | 只在 3.25 正式送达后创建任务；隐藏到期事件必须带 owner+case serial+expected state stale guard。必须先定义总督、伯爵、男爵各自真正可控的 CK3 指标，不能给男爵下达其无权完成的财政、军备或治理任务。拒绝只能写一次下轮负面证据，不能在当前 serial 再扣一次资源。 |
| 018 个人告身与四重清算 | `zg361_snapshot_player_result_effect`；`zg361_result_kpi`、rank、reviewing superior、cohort；地方国库 -50、个人金币 -25、贤能 -60、一年俸禄 -25%；三笔退款收据；3.25/PIP modifier；冻结榜单。 | 持久 `result_receipt_id`、结算时间、完整 reason codes、每笔支付/退款/止扣/到期状态、可重复打开的详情页、已扣俸禄与剩余止扣显示。 | 现有 snapshot 主要服务一次性事件，并非可重开的持久案卷。更大的冲突是三笔罚没和 modifier 在送达前已经执行；必须和 #069 一起拆为 `freeze → service → settle`。当前收据写固定 50/25/60，尚未静态证明等于实际可付额，不能直接宣称逐笔实际支付守恒。 |
| 032 管理者自己的团队绩效 | 京察 pending/mandate year/reviewer；`zg361_skipped_jingcha_superior/year`；精确 -50 的一次 KPI consumption；managed 榜汇总；`zg361_manager_mechanism_kpi_value`。 | `manager_review_id`、严格更早的 `source_team_serial`、目标完成、按期京察、校准质量、PIP 成功、翻案率、人才留存、HC 效率七项冻结快照、理由行与非递归 guard。 | 在 `cycle_closed` 时冻结 manager-owned 团队快照；经理作为其直属上司的 subject 时只能消费严格更早 serial。现有 manager mechanism KPI 读取当前累计组织账，不能冒充上一轮团队绩效。同日 yearly pulse 的角色执行顺序不可作为正确性前提。只有本身也是天朝公爵以上的受评人才能产生 manager-review 分项。 |
| 033 管理者画像与理由码 | 现有正直、诚实、勤勉、仁厚、专断、冷酷、欺诈、野心等 trait resolver 可作为输入。 | 数据派、护犊型、政治型、仁厚型、残酷型五类稳定 profile；权重版本和生效周期；校准/申诉/PIP/奖金/HC 偏好；硬证据 cap；逐项 reason code；确定性结果。 | trait 只用于初始化/更新画像，不再只决定一次政策卡 A/B/C。profile 存人物 scope，successor 不继承。固定输入必须可复现；若需要随机性，应先冻结决议及理由，不能让重读档重新抽签。 |
| 045 不得惊讶反馈债 | `zg361_review_talk_interaction` 可复用交互表面；拒办京察跨轮扣分的保存 superior/year→下轮一次消费模式可复用。 | feedback record ID、事实发生/送达顺序、辅导动作、subject 确认/异议、反馈覆盖率、3.25 reason 引用、无预警申诉理由、manager feedback debt。 | 新建期中反馈 interaction 或重构 review-talk；现有 talk 只有结果 modifier 已存在时才开放，不能证明期中预警。状态必须阻止终评后回溯补造。伯爵/男爵只确认或异议自己的记录。 |
| 049 封存提交与截止时点 | #007 peer round；`zg361.41` 已有的 scheduled hidden event + pending/stale guard 模式。 | 统一截止、提交时间、不可变内容 token、准时标记、一次补交信用、监督人、补交截止、证据缺口和评价者履责记录。 | 与 #007 同批实现。CK3 脚本层不应承诺真正密码学 hash；使用唯一 submission ID、冻结字段校验和和不可修改状态即可。死亡、转封、改系统时间或存读档不得重新开放已封存轮次。 |
| 069 正式送达与申诉时钟 | 榜单发布；玩家结果事件 `zg361.2–4` 延迟一天；现有 grade、penalty、PIP、appeal 链。 | `notice_case`、冻结理由 hash/token、签收/异议签收/拒收见证、实际送达日、申诉起止、奖惩执行状态、manager 送达期限及逾期责任。 | 这是全批最高风险的核心改造。当前 `zg361_apply_pending_grades_effect` 在个人告身送达前已加 modifier、扣资源、启动 PIP，并可能处理淘汰，直接违反“delivered=false 不得执行后果”。必须先冻结并发布榜，再逐人送达，最后一次性结算；伯爵/男爵只能签收自己的告身。 |

## 四、最小文件方案

不要为十五项各建一套独立脚本。最小共享增量建议如下：

1. 新增 `tools/mechanism_domains/domains.json`，定义 Phase 1 涉及的 review、peer/calibration、appeal/PIP/result、manager review、notice/feedback 状态图与合法迁移。
2. 新增 `tools/mechanism_runtime/runtime_001_120.json`，为本批十五项填写 typed operation、对象、hook、from/to、期限、事务、反馈、玩家/AI 路径和验收映射；其余编号可以暂时保持明确的未实现状态，但 schema 不得伪造案件。
3. 新增一个 runtime 生成器，例如 `tools/gen_361_runtime.py`，统一生成：
   - domain runtime scripted effects；
   - deadline/stale hidden events；
   - runtime scripted GUI predicates；
   - runtime script values/modifiers；
   - manifest 的逐项 domain/player 状态。
4. 修改现有 `common/scripted_effects/zg361_effects.txt`，只负责插入权威 phase hooks，并把结果处理拆成 freeze、service、settle；不要在这里手写十五套平行状态机。
5. 修改现有 `common/character_interactions/zg361_interactions.txt`，承载自评、互评、期中反馈和申诉等人物动作；所有 manager action 使用统一 wrapper。
6. 扩展 `tools/gen_scoreboard_snapshot.py` 及其生成 GUI，在同一个安全入口增加案卷、校准、申诉/PIP 等少量上下文页签；不要新增十五个 HUD 按钮，也不要手改标为 `GENERATED FILE` 的 GUI。
7. 扩展 `tools/gen_zhongguo_acceptance_cases.py`，让逐项 PASS 验证对象、状态、期限、资源恒等式、stale/idempotence 和可见反馈。旧 choice/ledger/校验和检查继续保留，但降级为兼容 smoke。

## 五、七个首要阻塞

1. **单 tick 单体流程**：现有 `zg361_run_review_effect` 在一次链中计算、排名、校准、结算，无法真实容纳目标制定、期中反馈、自评、背靠背互评和截止日。
2. **送达与结算顺序冲突**：#069 要求正式送达后才启动申诉和奖惩，现有代码却在结果事件出现前已经处罚、启动 PIP 和处理淘汰。
3. **共享 runtime 内核缺失**：还没有统一 case serial、owner/subject binding、deadline ticket、expected-state stale guard 和 transaction receipt journal。
4. **真实协作事实源缺失**：#007 尚无可靠的共同战争/治理任务索引；只用同一 cohort 或关系值不满足合同。
5. **PIP 原生可完成性缺失**：#015 尚未按总督、伯爵、男爵划分其真实可控制且可观测的里程碑。
6. **玩家可见案件表面缺失**：现有 GUI 只有最新冻结考核榜和共享组织账，没有证据单、校准记录、申诉/PIP 状态、送达时钟和理由码详情。
7. **语义验收夹具缺失**：现有 361/361 fixture 不读取新 acceptance contract 中的对象、期限、资源和反馈断言，不能用于升级 `domain_runtime`。

## 六、建议施工顺序

在不逐项启动 CK3 的前提下，建议按依赖关系施工：

1. 共享 runtime 内核：权限 wrapper、case serial、owner/subject binding、phase hook、deadline/stale guard、receipt journal。
2. `001 → 002 → 004 → 045`：建立跨周期 review、证据、目标、自评和期中反馈。
3. `007 → 049 → 008`：建立 peer round、封存截止和评价者信用。
4. `009 → 010`：在同一 calibration round 上完成驾驶舱、原子交换、背 C 与护人。
5. `069 → 018 → 014 → 015`：先闭合正式送达，再接持久告身、收据申诉和 PIP 四终态。
6. `032 → 033`：最后消费前述真实案件的上一轮团队快照，生成经理绩效与稳定理由码。
7. 全部 L0/schema/model/生成可复现门通过后，再冻结代码并在一次 CK3 启动内批量验收本批十五项；只有明确 RED 才做定向重跑。

本审计没有修改产品实现、没有运行生成器、没有启动 CK3。其结论是 Phase 1 的施工输入和风险账本，不是新的实机验收结果。

## 七、版本冻结与原型归档

项目所有者于 2026-08-29 进一步冻结当前版本范围：本审计提出的新领域功能只继续预研和文档化，代码实现留到下一版本；当前最高优先级是现有功能验收、MCP 阻塞项、发布、上传和演示物料。任何 Phase 0/1 原型都不得接入当前产品树、release staging 或本轮 CK3 验收口径。

冻结指令下达前已经产生但从未接入产品树的三个 Python 原型已移出 `mod_zhongguo_style/tools/`，保存在：

`artifacts/mod_zhongguo_style/next-version-runtime-prototypes/2026-08-29/`

| 文件 | SHA-256 | 状态 |
|---|---|---|
| `zg361_domain_data.py` | `BF2AFB9C39C5772D33728B5D5673F68B1A95A1093C603B771964DE7167D47AE4` | 中断时的 domain schema 草稿；未完成、未测试、不得用于当前版本 |
| `zg361_case_kernel.py` | `2396BED6B14F24392827992CEE4597A9B7F128D06C7DD3FE679A8462FF9E9DC3` | 独立模型原型；未接产品树 |
| `test_zg361_case_kernel.py` | `3C2A8C25E4C7389119B9D24D48B9AB66D54D13F5EB1322597F64D0490D5DACE6` | 原型的 27 项模型测试；不能冒充 CK3 或产品验收 |

这些文件只作为下一版本设计素材保留。恢复施工前必须重新审阅当时的产品版本、领域 schema 和权限合同，不能直接复制进当前生成链。
