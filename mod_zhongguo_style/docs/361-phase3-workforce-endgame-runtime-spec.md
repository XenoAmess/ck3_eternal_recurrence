# 361 三期：workforce / endgame Python L0 运行合同

状态：`READINESS = python-l0-only`

本规范冻结机制 **242–277、355–356、360–361** 的独立、确定性 Python 参考模型。精确集合共 40 项：
AB（242–253）12 项、AC（254–265）12 项、AD（266–277）12 项、AL 终局（355、356、360、361）4 项。

实现与测试分别位于：

- `tools/zg361_phase3_workforce_endgame_model.py`
- `tools/test_zg361_phase3_workforce_endgame_model.py`

这不是 CK3 产品运行时、fixture-live 或 production-live 声明。它不生成 scripted effect、GUI、本地化、MCP、
paused snapshot 或实机 artifact；作用是把完整施工计划中的资源方向、身份、重复/过期语义和历史不可变规则变成可执行的 L0
参考合同，供后续 generator、静态测试和 CK3 consumer 复用。

## 1. 权威输入与诚实边界

本模型以以下仓库权威输入为准：

- `361-mechanism-implementation-manifest.md`：编号、域及当前 readiness；
- `361-expansion-options.md`：逐编号 A 路线的行为语义；
- `361-domain-runtime-architecture.md`：AB/AC/AD/AL 对象、资源与跨域边界；
- `361-phase2-full-implementation-program.md`：B7 workforce 与 B8 endgame 施工门；
- `tools/mechanism_runtime/runtime_241_361.json`：通用 manifest hook 与 operation/object 映射。

manifest 对本范围仍标记 `domain_runtime=not-implemented`，player-visible loop 也未闭合。通用 runtime JSON 的机械线性边仅用于
traceability，不能冒充逐项语义已经审定。例如 #260 合同类型和 #261 执行者披露必须在交付前冻结；#256、#257 要消费交付证据；
#269 必须等录用后的延迟结果；#275 必须分叉到 held/reopen/release；#276、#277 不是 probation 线性边。Python 模型按语义约束这些
先后关系；`MechanismBinding.execution_stage` 与 `WORKFORCE_EXECUTION_ORDER` 另行冻结真实执行顺序，不再从旧 manifest hook
机械推导。CK3 静态生成器现在消费这两份模型常量：AC 为
`254→255→260→261→256→258→259→257→262→263→264→265`，AD 为
`266→273→271→267→268→270→272→274→275→269→276→277`。这只修正静态投影顺序，不提升 live readiness。

## 2. 统一命令与返回合同

所有写操作使用 `CommandToken`：

```text
model_id + owner_id + subject_id + cycle_serial + case_serial
+ expected_revision + actor_id + command_id
```

行为结果只有三种：

- `APPLIED`：所有预检与全局守恒通过，revision 恰好增加 1；
- `STALE_NOOP`：model/owner/subject/cycle/case/revision 任一过期，逐字段不变；
- `IDEMPOTENT_NOOP`：相同 command ID、机制、身份和规范化 payload 重放，逐字段不变。

同一 command ID 搭配不同机制、身份或 payload 是 `COMMAND_COLLISION` typed RED。payload 指纹递归规范化 enum、dataclass、mapping
和 sequence，因此存读档后的相同重放仍保持幂等。

值域、类型、权限、状态、资源、期限、守恒或 provenance 失败均抛出带稳定 `RedCode` 的 `DomainRed`。布尔值显式拒绝充当整数。
每个 fallible mutation 都先作用在完整深拷贝，候选快照通过 `_validate()` 后才原子替换 live snapshot；RED、stale、idempotent 后
资金、HC、工时、角色身份、receipt 与历史对象都不变化。

## 3. 权限与身份

- 管理操作：actor 必须同时是天朝政府、有地、且爵位不低于公爵。
- #361：还必须是 `is_top_celestial_liege=True` 的最高天朝领主。
- 伯爵、男爵可以是受评人、候选人、借调人、会议成员、PIP 离任人或回聘人；不能作为 manager 执行上述写操作。
- `can_handle_own_assessment()` 仅表达伯爵/男爵对自身受评入口的资格，不授予 cohort、档位、HC、薪酬、采购或宪章管理权。
- 外包转正、候选归属、借调、回聘和 PIP 退出必须引用 actor registry 中的既有角色，模型不得凭空生成人物。
- team/cohort 对象使用共享 ID 和唯一 receipt；不会按成员复制会议或集体行动来重复扣工时/配额。

## 4. 守恒式

### 4.1 金币

```text
gold.total = gold.available + gold.reserved + gold.paid
gold.paid  = Σ gold_credits[recipient]
```

合同、Offer、内推奖励和 #355 已批新增资源先从 available 转入 reserved；实际付款才从 reserved/available 转入 paid，并给真实 recipient 同额 credit。
退款/舞弊追回按原收款人精确反向，且不能超过该收款人的既有 credit 或合同未追回的 gross payment。合同 reservation 加所有
requisition 的 Offer/内推 reservation 必须恰好等于全局 gold.reserved。

### 4.2 正式 HC 与影子 HC

```text
formal_total = formal_available + formal_reserved + formal_filled + formal_vacant
shadow_total = shadow_available + shadow_active
formal_filled = Σ formal_hc_occupants[real_actor]
```

一个活动 requisition 对应且只对应一个 formal reservation。录用把 reserved 转为 filled；拒绝 hold 仍是 reserved，只有到期重开/释放
才回到 available。#277 把离任人的 filled 槽转为不可自动招聘的 vacant，并记录 displaced work；不能自动增加 available、reserved 或 total。外部容量只移动 shadow HC。
#257 先把一个 formal available 转为带真实角色和 recruitment ref 的 pending reservation；只有 model 的权威周期到达 effective cycle，
`settle_external_conversion_257` 才把 reserved 转为 filled、写入 occupant 并释放一个 shadow HC。同一角色不能拥有第二个 filled/pending HC。

### 4.3 工时

```text
accounted_hours = output + meeting + learning + on_call + leave
authorized_hours = planned_hours + verified_overtime_hours
accounted_hours <= authorized_hours
```

`delivered_value` 不是小时。会议用唯一 team-level record 结算 `duration × unique attendees`，拒会时只释放本人的 attendee-hours；
贡献证据和出席记录分账。meeting budget 在本 L0 冻结为 attendee-hours，而不是会议场次时长。

### 4.4 历史、provenance 与未来默认

- 原始面试票、旧考核案、旧目标、outcome 完成周期和 charter 报告证据只追加、不覆盖。
- #269 outcome → hire → sealed interviewer 的归因份额非排除情形恰好为 10000 bp；本 L0 冻结为“一次最终质量结算”，同一 hire
  即使更换 outcome ID 也不能覆盖或重复回写。
- #356 同一成果总 credited value 恰好等于 actual value，且全部归真实 completion cycle；迟报只增加治理/诚信成本。
- #360 每 cohort 的全员议程集合必须与权威冻结成员集合完全相等；forced C 与已批 exception 不重叠，二者数量之和恰等于冻结 C
  quota。exception 必须有爵位更高的天朝经理批准，保下人员的经理承担显式成本；强制给 C 本身不冒充该成本。
- #361 优先级必须是四项完整排列；首版与修订版有连续 version/previous 链。charter 的 `effective_cycle` 必须晚于当前 cycle，
  completed cycles 不得来自未来；A 路要求 evidence fairness / long-term innovation / organizational warmth 中至少两项排在
  forced competition 前，且采用 long-term
  delivery。`defaults_for_cycle(current)` 仍返回旧默认；charter 生效后仍是合法存量，修订不得替换 completed-cycle/report 证据，
  adopted/effective/version 必须单调。

## 5. 40 项显式映射

表中 hook 是 manifest traceability；“L0 行为/守恒”才是本参考模型实际执行的合同。

| ID | 域 / manifest hook | L0 callable | 端到端结果与关键守恒 |
|---:|---|---|---|
| 242 | AB / `capacity_planned` | `record_presence_output_242` | presence、output hours、delivered value 分账；output 不得超过 presence。 |
| 243 | AB / `capacity_planned` | `record_after_hours_reply_243` | 冻结 urgency/on-call 路由；critical 回复须有值守或全员规则，工时只进 on-call 一次。 |
| 244 | AB / `capacity_request_open` | `record_voluntary_effort_244` | 自愿/拒绝/冻结急务分离；书面约定且完成后才向真实角色付款，合理拒绝不降档，隐性强制回写经理/倦怠成本。 |
| 245 | AB / `capacity_request_open` | `record_overtime_245` | approved/retroactive/shadow 互有 provenance；真实小时形成唯一记录，shadow 回写经理责任。 |
| 246 | AB / `capacity_decided` | `settle_overtime_246` | 每笔 overtime 恰选 gold/time-off/target-relief 一条；金币付款有同额 employee credit。 |
| 247 | AB / `capacity_decided` | `open_sprint_247` | 冲刺冻结 start/end/goal/唯一 roster，窗口上限 30 日；续期批准来源显式保留。 |
| 248 | AB / `capacity_executed` | `record_understaffing_248` | 缺编路线不铸造 HC；跨轮 overtime 增加 burnout 与 manager cost。 |
| 249 | AB / `capacity_executed` | `record_meeting_249` | agenda、owner、attendees 唯一；attendee-hours 同时占 meeting budget 与 capacity 一次。 |
| 250 | AB / `compensation_due` | `record_meeting_contribution_250` | 贡献必须有独立 evidence；attendance 本身不生成贡献。 |
| 251 | AB / `compensation_due` | `record_meeting_refusal_251` | 拒会/代表 provenance 唯一；代表必须已在冻结 attendee budget 内，decision owner 未移交前不得拒会。 |
| 252 | AB / `capacity_normalized` | `normalize_leave_252` | 合法 leave 进入独立 time bucket；目标按可工作小时确定性向下取整，替补 credit 不超 100%。 |
| 253 | AB / `capacity_normalized` | `record_recovery_response_253` | recovery/minimum duty/transfer/protest 分路；完成最低职责不等于 misconduct，翻案回写 manager/trust。 |
| 254 | AC / `external_need_open` | `open_external_contract_254` | 预留采购金与 shadow HC，冻结 sunset；formal HC 不变，外部记录不进正式 cohort。 |
| 255 | AC / `external_need_open` | `compare_workforce_tco_255` | formal/external/mixed 三路线全成本同口径，确定性选择最低 TCO；比较本身不再扣资源。 |
| 256 | AC / `contract_type_locked` | `evaluate_supplier_pool_256` | 交付/质量/SLA 独立评分与续约/整改/更换；必须已有类型与执行链，不写正式档位。 |
| 257 | AC / `contract_type_locked` | `convert_external_worker_257` | 真实角色、已验收交付、一个 formal reservation 与 recruitment ref；权威周期到期再 settle，并释放一个 shadow HC。 |
| 258 | AC / `supplier_selected` | `freeze_controllable_scope_258` | 显式 `scope_frozen` 区分“空缺失集”与未执行；没有 access provenance 不得调目标，重复冻结 RED。 |
| 259 | AC / `supplier_selected` | `allocate_sla_responsibility_259` | 每个 incident 独立持久化 contract/client-change/vendor-management/executor 分层责任，逐案合计 10000 bp。 |
| 260 | AC / `contract_active` | `lock_contract_type_260` | #254 的 labor/outcome 类型只能确认、不能换型；ownership/change refs 在交付前一次持久化冻结。 |
| 261 | AC / `contract_active` | `disclose_executor_chain_261` | 链从签约 vendor 起、以 actual executor 止、无环；类型冻结后、供应商评价前披露。 |
| 262 | AC / `delivery_due` | `open_secondment_review_262` | home/host 权重合计 100，冻结 start/due/return right 与真实角色、双经理。 |
| 263 | AC / `delivery_due` | `resolve_secondment_return_263` | `as_of` 必须等于 model 权威周期；due 后可一次 bounded extend，延期不占 terminal choice，新 due 后仍可终结。 |
| 264 | AC / `contract_resolved` | `accept_knowledge_handoff_264` | 权威 model cycle 到 sunset（或有 waiver）且 documentation/shadowing/practical acceptance 齐全后才付尾款。 |
| 265 | AC / `contract_resolved` | `audit_external_fraud_265` | 冻结证据与 10000 bp liability；非 vendor 责任人必须是真实有权经理并有 duty evidence，追回精确反向。 |
| 266 | AD / `requisition_open` | `open_requisition_266` | 合法 role/requisition 唯一，恰预留一个 formal HC；bool 不得冒充 threshold/urgency。 |
| 267 | AD / `requisition_open` | `seal_interview_votes_267` | 每名有权面试官一票一 evidence；referrer 强制回避，raw votes 冻结。 |
| 268 | AD / `interview_votes_due` | `calibrate_interviewers_268` | 仅写 bounded normalization adjustment（±20），人口集合必须等于 sealed voters，原票不变。 |
| 269 | AD / `interview_votes_due` | `write_back_hire_quality_269` | 只有已录用且后续周期的最终 pass/mismatch/attrition/excluded 可回写；每 hire 一次，换 outcome ID 也不能覆盖。 |
| 270 | AD / `interview_calibration_due` | `set_hiring_risk_policy_270` | critical/growth/routine 风险偏好和 threshold 在 Offer 结果前冻结，不能倒改结果。 |
| 271 | AD / `interview_calibration_due` | `register_referral_271` | 关系披露、referrer≠candidate、最终票回避；reward 先预留，probation pass 才付款，否则释放。 |
| 272 | AD / `offer_due` | `issue_offer_272` | level band 外必须有 manager 特批；Offer promise、signing gold 与限期 premium 一次冻结。 |
| 273 | AD / `offer_due` | `assign_candidate_owner_273` | 真实 candidate 单 owner，scout+hiring credit 恰 10000 bp；不能同时被第二活动 Offer/录用占有。 |
| 274 | AD / `offer_decided` | `resolve_counteroffer_274` | competitor provenance、一次 counter、fairness cap；付款给 candidate，HC reserved→filled 恰一次。 |
| 275 | AD / `offer_decided` | `handle_offer_refusal_275` | 拒绝先释放 Offer/内推资金但 HC 保持 reserved；`as_of_cycle` 必须等于 model 权威周期，due 后才重开/释放。 |
| 276 | AD / `probation_due` | `register_rehire_276` | 历史 case/hash 和 misconduct 保留；新 evidence 只开未来 cohort gap review，本操作不造 HC、不改旧档。 |
| 277 | AD / `probation_due` | `record_pip_exit_277` | 冻结 PIP、原 slot、真实 occupant、displaced work/cost provenance；filled→vacant 守恒，vacant 不自动变为可招聘 HC。 |
| 355 | AL / `multi_cycle_facts_frozen` | `apply_target_ratchet_355` | official+closed prior cycle 唯一；新增金币真实 reserve；PEAK 即使无资源/权力也合法，但全部缺口落显式风险。 |
| 356 | AL / `multi_cycle_facts_frozen` | `settle_outcome_timing_356` | completion/report 不得来自未来，同 timestamp evidence 只消费一次；总值恰等 actual，迟报形成成本。 |
| 360 | AL / `manager_collective_action` | `resolve_collective_action_360` | 全员 agenda；forced+exception 守恒 C quota；exception 要更高爵经理批准，保人经理承担成本，改革仅未来。 |
| 361 | AL / `constitution_chartered` | `adopt_charter_361` | 最高领主、至少三轮已完成证据、A 路优先顺序、long report/cost、单调 version/previous；生效存活且只改未来默认。 |

## 6. 测试合同

`test_zg361_phase3_workforce_endgame_model.py` 包含：

1. 精确 40-ID catalogue、domain/hook/conservation/callable 完整性；
   catalogue 还冻结 40 个互不重复的 exact object type、真实 consumer callable、非空资源账与适用期限，
   以及独立于 legacy hook 的 execution stage/order，不再用 `capacity_period` / `recruitment_funnel` 四个域级泛化标签冒充业务对象；
2. AB 242–253 单链触达与金币/五类工时/会议贡献分账；
3. AC 254–265 单链触达与采购付款/追回、formal/shadow HC、借调、转正和知识移交；
4. AD 266–277 的录用成功链，以及拒绝→HC hold→到期释放、回聘历史、PIP 退出不造 HC；
5. AL 355/356/360/361 的目标棘轮、跨期成果、全员 agenda/配额守恒、宪章 current-vs-future 默认；
6. 公爵权限、伯爵自评边界、bool typed RED、live snapshot 原子性、stale、payload collision、幂等重放与 pickle round-trip；
7. 两轮只读审查反例：无值守工时、空贡献重复封存、owner 拒会、合同换型、空 scope 重放、多 incident、提前移交、ghost liability、
   双 role/candidate/conversion、extend→return、重复质量回写、事后内推、伪造 HC hold 时钟、免费资源、未来/复用证据、例外成本方向、
   宪章未来周期/A-B 混包/倒序修订/生效后存活。

本 L0 只证明确定性 Python 对象的合同。它没有证明 Paradox 脚本可解析、游戏触发顺序正确、GUI 可见、跨存档持久化、原生角色/职位
合法、真实金币/HC 已消费，或多周期 scheduler 已运行。

## 7. 后续 CK3 产品缺口

独立 CK3 静态投影现已存在，并把本模型的 exact object/consumer/resource/deadline 合同投影到 A/B；C 生成
精确五元 policy debt、逐编号 hidden 到期消费者、等量治理工时偿债、两次有界 manager 升级和保持 open 的
typed blocked 终态。它仍未中央接线、未过 parser/MCP/存读档/实机，因此至少需要：

- 用 exact-build 原生查询把 vacancy/candidate/vendor/team/cohort/charter 标识与合法 court position/council/title 结果互证；
- 在真实 CK3 中验证正式/影子 HC、国库→角色/供应商、个人信用、capacity 五桶与跨期 consumer 的读写和守恒；
- 实机覆盖 reject/withdraw/held/reopen、#257/#269/#275 延迟分支、#360 三 cohort 与 #361 多版本未来默认；
- 提供 deadline scheduler、save/load round-trip、共享 GUI/ledger、MCP query/action、paused snapshot 与实机 acceptance artifact；
- CK3 投影已提供 #264 sunset/waiver/artifact、#276 独立历史 rehire、#277 closed-PIP/exit、#275 runner-up
  central reopen、357–359 receipt bridge、#360 三 cohort producer 和 #361 三周期 rolling-chain adapter；仍需外域
  以真实角色/职位/历史/哈希调用这些 typed seam，并完成原生 court-position 任命/离任，不能把 adapter ACK 当来源证明；
- 运行 generator/static validation/真实 CK3 L1–L3，并保持本规范所列资源与历史不变量。

因此，本文件和静态投影可作为后续施工的 reference oracle，但不能据此把这些机制提高为 fixture-live、
production-live 或 complete。
