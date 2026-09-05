# 361 薪酬、发放与长期激励 CK3 运行时

状态：**CK3 script static-ready；尚无 CK3 解析日志、MCP paused snapshot 或玩家实机证据**

生成器：`tools/gen_361_compensation_runtime.py`

生成结果：

- `common/scripted_effects/zg361_compensation_00_*_effects.txt` 至
  `zg361_compensation_24_*_effects.txt`（25 份按基础设施、财务、案卷、阶段与屏障用途拆分的 effect 文件）
- `events/zg361_generated_compensation_runtime_events.txt`
- `localization/*/zg361_compensation_runtime_l_*.yml`（共 9 份；简中、英文原创；其余七语为日常开发期英文结构占位）

25 份 effect 文件各含 1–9 个顶层 effect，目标上限 10、原则硬上限 20；当前没有例外。
生成器保留拆分前 148 个 effect 的完整正文与全局顺序，并在 `--check` 时拒绝旧单体文件或过时分片残留。

L0 合同：`tools/test_zg361_compensation_runtime.py`；既有领域模型：
`tools/zg361_phase2_compensation_model.py`。模型与 CK3 投影现在共享精确的 33 ID、99 条 A/B/C 数值资源合同、
#290 `375` 门槛、#299 Good Leaver 默认不加速和九个 C 路线 `no-object` 集合；Python 模型仍只是 L0 oracle，
不能覆盖 actual CK3 投影或替代实机证据。

本层只投影 L、AE、AF 三个共享案卷，不修改中央考核 hook、B1/B2、考核榜 GUI 或共享案卷内核。开放 effect
留给后续集成调用；没有真实 CK3 启动证据前，不得标成 fixture-live、production-live 或 complete。

## 一、精确覆盖与状态分组

本批精确覆盖 **33 个编号**：`082–091`、`278–300`，没有吸收相邻领域。
编号写入发生在表中“当前状态”，本阶段全部消费者完成后，唯一 stage dispatcher 才进入箭头右侧状态。

| 领域 / 案卷 | 阶段 | 状态迁移 | 本阶段编号与行为 |
|---|---:|---|---|
| L `compensation_award` | 1 | `formula_locked -> funds_reserved` | 082 `total_reward_quote`；083 `three_factor_bonus`；084 `grant_bonus` |
| L | 2 | `funds_reserved -> granted` | 085 `retention_cliff_gap`；086 `hold_and_clawback_bonus` |
| L | 3 | `granted -> held` | 087 `pay_band_position`；088 `allocate_raise_pool`；089 `career_package` |
| L | 4 | `held -> settled` | 090 `pay_spot_award`；091 `separate_award_accounts` |
| AE `pay_statement` | 1 | `payable -> due` | 278 `pay_statement`；279 `extra_month_contract`；280 `prorate_award` |
| AE | 2 | `due -> decided` | 281 `defer_statement`；282 `apply_backpay` |
| AE | 3 | `decided -> corrected` | 283 `dry_promotion_commitment`；284 `demotion_pay_schedule`；285 `allocate_raise_pool` |
| AE | 4 | `corrected -> appealed` | 286 `band_correction`；287 `pay_visibility` |
| AE | 5 | `appealed -> closed` | 288 `repair_pay_inversion`；289 `compensation_appeal` |
| AF `lti_grant` | 1 | `nominated -> granted` | 290 `select_lti_nominations`；291 `grant_units`；292 `risk_award_choice` |
| AF | 2 | `granted -> cliff_reached` | 293 `convert_bonus_to_units`；294 `valuation_columns` |
| AF | 3 | `cliff_reached -> vesting` | 295 `lti_cliff`；296 `lti_cadence` |
| AF | 4 | `vesting -> exit_classified` | 297 `lti_tracks`；298 `lti_double_gate` |
| AF | 5 | `exit_classified -> settled` | 299 `classify_lti_leaver`；300 `settle_repurchase` |

L 的五状态、AE/AF 的六状态均直接复用 `zg361_case_l/ae/af_*`；编号 operation 不得自行改共享 state。

## 二、入口、权限与单卡适配器

唯一对未来 central dispatcher 暴露的入口是 manager-scope
`zg361_comp_portfolio_open_next_effect`。以下三个 effect 只是本包 portfolio 在 L → AE → AF 顺序中调用的内部
domain opener，不能绕过 portfolio 直接开案：

```text
zg361_comp_open_l_case_effect
zg361_comp_open_ae_case_effect
zg361_comp_open_af_case_effect
```

每个编号只有一个管理入口：

```text
zg361_comp_mNNN_manager_apply_effect = { ROUTE = 1|2|3 }
```

调用上下文冻结为 `ROOT = 直属管理者`、`THIS = 直属受评者`。管理者必须通过
`zg361_is_celestial_liege_trigger`，即在任、有地、天朝制、公爵及以上。入口不加 `is_ai = no`：玩家管理者与
项目明确授权的 AI 管理者使用同一套 duke+ resolver；AI 只走 hidden 后台路线，不打开玩家事件。

受评者必须通过 `zg361_is_reviewable_vassal_trigger` 且 `liege = ROOT`。伯爵、男爵可以被考核，但不能因此获得
open、manager core、stage advance、付款批准或回购批准权。AE 申诉中的本人响应另走
`zg361_comp_ae_subject_appeal_response_effect`，只允许本人写自己的响应，不调用任何管理入口。

`zg361_comp_portfolio_*` 是 manager-scope 适配器：一个管理者同一时刻只持有一个选中受评者、一个 L/AE/AF
活动案卷和一个当前阶段卡。首次选案只接受当前直属受评者已经正式送达的本轮结果，并一次冻结
`result_owner/result_subject/result_cycle/result_case/result_state/result_grade`；其中 `result_owner` 必须是当前管理者、
`result_cycle` 必须等于其当前 `zg361_review_serial`，`result_state >= 3`，grade 只允许 `1/2/3`。缺字段、旧轮、
owner 不符或 state 仍为 1/2 的未送达结果一律不选、不打开任何 L/AE/AF 案卷。

grade 的唯一数值投影为 `1 -> 325 (3.25)`、`2 -> 350 (3.50)`、`3 -> 375 (3.75)`。L 结案后 portfolio
保留同一 subject 和同一结果快照开启 AE，AE 结案后再以同一快照开启 AF；中途不得重新按 stewardship 选人，
也不得从可能已经变化的 current result 重读 grade。玩家仅看到统一的 `zg361comp.1` 三路线事件；不存在 33 个
编号窗口。授权 AI 由 `zg361comp.2` 静默选择后台路线，结案后 hidden queue 再取下一 domain。

统一玩家事件不是三个空泛按钮：L 四阶段、AE 五阶段、AF 五阶段共 14 组 `triggered_desc` 在选择前列明该阶段
A/B/C 的实际双账户金额、欠付/期限、份额、门槛和离任后果。结案卡再直接投影奖金、薪酬单与长期份额账的数值；
薪酬透明度只显示制度口径和匿名数值，不泄露具名同僚薪酬。当前这些仍只是静态可加载投影，尚未获得玩家实机证据。

## 三、五元身份、receipt 与写入消费链

每次内部 domain open 成功后，还会把 manager portfolio 的六元结果来源复制为 subject-scope
`zg361_comp_result_*` 快照；AE/AF 只消费这份同源快照。编号 core、consumer、阶段屏障、资金 journal 和
delayed event 继续检查各自同一五元案卷身份：

```text
owner + subject + cycle_serial + case_serial + expected_state
```

每个编号先由 `zg361_case_kernel_record_operation_effect` 写
`receipt_owner/subject/cycle/case/state/route`，再由本域 single-use `receipt_active` 锁定同案路线。同一五元身份、
同一路线重放是 idempotent no-op；同一 receipt 偷换路线为 typed RED；旧 cycle/case/state 为 stale no-op，不能改
新案。

资金 receipt 还必须冻结实际身份，而不能结算时重新从当前关系推断：

```text
treasury_payer
personal_payer
recipient
approver
frozen_owner / frozen_subject / frozen_cycle / frozen_case / frozen_state
```

33 项统一执行 `manager_apply -> core write -> consume`：core 写机制专有字段和 operation receipt；consumer 将这些
字段投进 L 奖金桶、AE 薪酬单或 AF 份额账，写 `mNNN_consumed = 1`；阶段屏障只有在本组所有编号都 consumed
且领域守恒成立时才调用共享 dispatcher。由此每个 write 都有后续 consumer，不以 debug ACK 或裸 `choice` 冒充玩法。

统一卡片的一次 A/B/C 选择会应用到该阶段的全部编号。每个编号都必须冻结至少一个数值业务资源，并由后续
计算、付款、期限、归属、离任或只读投影消费。明确拒绝业务对象的 C 路线集合固定为
`084/088/090/282/283/285/288/293/300`；这些路线只留下已选择但 `no-object` 的审计结果，不能伪造一笔奖金、
欠款、转换或回购。其余路线即使金额为零，也保留真实合同/可见性/门槛对象。

所有真实期限先保存五元 ticket，再调度 hidden character event；到期事件必须先调用共享 expire helper，只有
`kernel_applied = 1` 才可进入领域 resolver。旧 ticket 因任一字段不符只能 no-op。当前期限包括 L 递延结算、AE
90/180 日应付、AF 30/90/180/365/730 日归属和 90 日回购。

## 四、双付款与原子守恒

所有真实制度支出有两个实际账户：组织国库是案主的 CK3 `treasury`（以原生 `has_treasury = yes` 验证），负责人个人付款是同一案主的 `gold`；受款人
获得个人 `gold`。默认资金政策为 **70% 国库 / 30% 负责人个人金币**。动态金额先按冻结的整数口径拆分；固定
10/20 金额分别为 `7+3`、`14+6`。整数极小额按可表示的已冻结份额处理，退款和追回始终复用原 receipt 的两边
金额，禁止重新按比例计算或改换付款人。

静态语法依据当前仓库冻结的原版脚本：`10_tgp_interactions.txt` 以 `has_treasury = yes` 判断国库账户，
`10_dlc_tgp_scripted_effects.txt` 以 `remove_treasury = { value = ... }` 扣动态国库值。本包沿用这两个原生形式；
这只是 exact-source 依据，不等于 CK3 parser/live 验收。

事务顺序固定为：

1. 同时预检国库余额、负责人个人金币、领域 treasury/personal budget 和 receipt 状态；
2. 两本共享 journal 都成功 reserve 后才 settle；
3. 两边 receipt 都处于 settled 才执行真实 `remove_treasury`、个人 `gold` 扣款和受款人 `add_gold`；
4. 任一预检或 journal 失败即 typed RED，不产生半笔真实付款；
5. 未用预留走 exact refund，已付追回走带 source receipt 的 bounded return，并按原付款账户返回。

L 的奖金守恒为：

```text
grant_total = immediate_unpaid + deferred_unpaid + held + net_paid + forfeited
net_paid = paid - returned
```

AE 的显式薪酬单始终满足：

```text
payable = paid + owed - returned
```

AF 的份额账始终满足：

```text
granted_units = unvested_service + unvested_performance + vested + forfeited + repurchased
```

份额授予和归属不是现金支出；只有现金替代或真实回购才触发双付款。

## 五、L：奖金、递延、追回与专项奖

082–084 先分别写五栏总回报、三系数公式和公式锁，084 再冻结前两项的实际数值。A 路线为总额 20：
`14 treasury + 6 personal`，即时桶 `10+4` 当场结算给受评者，递延桶 `3+1` 与暂扣桶 `1+1` 留在 reserve；
B 路线为总额 16：`11 treasury + 5 personal`，即时 10、递延 4、暂扣 2；C 路线不创建奖金对象。到期 resolver
只能结算冻结的剩余总额，或按该路线原两本 receipt 原路退款，不能拿 A 路线常量结算 B 路线。

L 中 `performance_bonus`、`individual_bps`、`performance_award` 是金额/公式输出，不是另一套绩效 rating 输入；
本次审阅确认它们不写 `grade/rating = 350/375`，因此不把这些既有合同常量伪改成结果档位。实际 rating 只来自
上述 portfolio 结果快照。

086 的追回必须引用即时付款 source receipt，且不超过该 receipt 尚可追回金额；未付金额只可暂扣/没收，不能
伪装成已付追回。090 A 路线专项奖总额 10，实际付款 `7 treasury + 3 personal`；B 路线总额 6，实际付款
`4 treasury + 2 personal`；C 路线不创建专项奖。091 把 090 的实际已付总额分别按 `3+7` 或 `4+2` 分成
年功/绩效两账，不能再凭空承诺第二笔 10。087 带位和 088 调薪池由 089 的职级/任命/权力/现金包消费；冻结的
现金增量进入随后 AE 薪酬单基础额，降薪缓冲则只进入下一周期 carry-over，避免在本期已付款后破坏守恒。

## 六、AE：显式薪酬单状态与申诉分轨

AE 不用一个“已付款”布尔量折叠流程，而是完整保留：

```text
payable -> due -> decided -> corrected -> appealed -> closed
```

278–280 生成并冻结应付、额外月俸合同属性和折算；其中绩效型额外月俸使用 portfolio 实际结果，不再以 `375`
初始化。281 必须立即支付或生成新的 90/180 日到期 ticket，连续延期写
兑现信用；282 的追溯补发写独立债和 receipt。283–288 继续消费干升职期限、降薪缓冲、同档调薪、带外修复、可见
口径和新老倒挂，但每次都重算 `payable/paid/owed/returned` 守恒。285 的同档校准也复制同一冻结实际 grade，
不能另写一个固定 `375`。

281 选择延期后，必须等同阶段的 282 写完补发债，再在 state 3 冻结完整 `gross/treasury/personal` 三元金额和
付款人、受款人、案卷五元身份，之后才调度 90/180 日 ticket。到期 consumer 只读这份冻结金额，不重新读取可能
变化的 `statement_owed`；余额不足时不移动任一账户，欠付仍原样可见。

289 只开放 compensation appeal：受评者先在 `appealed` 状态写本人响应，管理者随后才可裁决。补发/纠错只改钱账，
`frozen_performance_grade` 不得被薪酬申诉重写；绩效申诉仍属于另一案轨。玩家本人可见申诉事件，AI 当事人保持后台。
后台 AI 当事人采用证据优先的“提出薪酬申诉”响应，使管理者的 A 路线具备可执行前置条件；不得记录“未申诉”后仍向
组合案卷派发同一条 A 路线并把 289 留在未消费状态。所有付款 helper 的 `financial_applied` 是总定义的 0/1 临时结果；
事件选项 tooltip 中读取它时必须先用 `has_variable` 的 `trigger_if/trigger_else` 包装，避免 CK3 的说明求值读取未设变量。

283、285、286、288 和 289-B 写入的金额是显式 `owed`，不是“已经付款”的文字。它们持续保留在
`payable = paid + owed - returned` 中；实际支付时仍必须经过同一双账户 precheck/journal。任何小于无法同时表示
国库与个人份额的单笔付款都不得假装完成。

## 七、AF：提名、归属、离任与 FIFO 回购

290 的提名资格门槛明确是冻结结果 **grade = 3 且 rating = 3.75**（脚本定点值 `375`）；**真实 grade = 2
映射出的 3.50 (`350`) 是明确负例**，不能因处于相邻档位而入池。三条路线只决定提名后的方案，任何路线都不能
改写 rating 或把 3.50 伪造成 3.75。资格只允许进入提名池，不等于自动授予。

291–294 冻结固定份额/固定价值、风险形态、自愿奖金转换和授予价/现值/可变现值。293 A 路线把 4 转为单位并
真实支付现金余量 6（`4 treasury + 2 personal`），B 路线保留全现金 10（`7+3`），C 路线不创建转换对象；
禁止再只写一个 `cash_remaining` 数字却不实际扣款。295–296 冻结 Cliff 与
月/季/年 cadence，并用真实 delayed event 重复归属。297 将服务轨和绩效轨分开，298 要求组织门槛与个人门槛
同时满足才归属绩效轨；服务轨不被一次低档吞掉。状态 4 会保持 `vesting`，直到管理者显式请求离任分类，不能把
多期归属压缩成一次状态跳转。

299 的默认合同冻结为 `good_leaver_acceleration = 0`：Good Leaver 保留已经 vested 的份额，但**不自动加速任何尚未
归属的服务份额**；未归属服务/绩效份额按默认合同没收。只有未来明确写进冻结合同的独立加速条款才可改变这一点。
Bad Leaver 可标记 clawback eligibility，但该标记本身不能直接吞掉已归属份额。
第三条“正常调动/保留已归属但不回购”路线同样结清未归属桶，避免案卷关闭后留下永不再归属的悬空单位。

300 只处理已经 vested 的单位，按管理者队列 `queue_tail -> queue_head` 严格 FIFO。立即或 90 日回购成功时才支付
总额 10：组织 `treasury -7`、负责人 `personal_gold -3`、持有人 `gold +10`；两本 receipt 都 settled 后才把
`vested -10` 搬到 `repurchased +10`。余额不足、非队首、窗口关闭或单位不足均不能移动单位。

## 八、L0 门、MCP-first 实机计划与诚实边界

静态验收应运行：

```powershell
py mod_zhongguo_style/tools/gen_361_compensation_runtime.py --check
py mod_zhongguo_style/tools/test_zg361_compensation_runtime.py
py mod_zhongguo_style/tools/test_zg361_phase2_compensation_model.py
py mod_zhongguo_style/tools/test_zg361_case_kernel.py
```

专用 L0 合同当前为 runtime 27 条、model 58 条，normal 与 `python -O` 均须 GREEN。它们固定检查 33 ID/阶段、
99 条 A/B/C 数值资源、35 个生成结果的确定性与 BOM、25 个 effect 分片的 148 段正文/全局顺序等价、9 语言 key parity、权限矩阵、每项 write-to-consumer、九个 no-object C 路线、
五元 receipt/deadline、双付款预检、reserve/settle/refund/return、欠付/延期付款、L/AE/AF 三条守恒式、current delivered result 六元冻结、
跨 L/AE/AF 同 subject/同结果、3.75/3.50 真值映射、Good Leaver 默认不加速、AF FIFO `7+3` 回购、单可见卡和
AI 静默。七个非日常语言只是英文结构占位，不得称为完成翻译。

后续实机验收必须 **MCP-first**：先提供 named open/apply/query 和变量 snapshot，在同一 paused CK3 会话中批量读取
管理者国库、个人金币、受款人金币、五元案卷、operation/cash receipt、statement 与 unit ledger，再验证成功、延期、
退款、追回、重复、改路、stale、权限和 FIFO。OCR 不得作为导航依据、数值来源或状态真值，只可在必要时做非权威
画面辅助。

当前尚未完成中央 hook 接线、CK3 parser log、真实 delayed-event 等待、paused snapshot、存读档或 live artifact。
因此本文只能声明 **CK3 script static-ready**。
