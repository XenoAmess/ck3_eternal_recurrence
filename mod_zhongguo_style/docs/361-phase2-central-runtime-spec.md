# 361 二期中央串行调度层：CK3 runtime 合同

Readiness: `static-ready`

MCP evidence: `none`

CK3 live evidence: `none`

## 1. 权限和冻结身份

- 中央 ROOT 必须通过 `zg361_is_celestial_liege_trigger`：天朝制、在世、有地、公爵及以上。
- 伯爵和男爵可以作为直属受评 subject，但永远不能成为中央 manager。
- B1 公示后，从本轮已冻结结果 cohort 里按 `stewardship / position = 0` 冻结一个 primary subject。
- 中央案固定 `manager + B1 cycle/case + review cycle + subject + result case`；死亡、调任、换 owner/cycle/case 都 typed RED，绝不换人续跑。
- #360 的 C1 必须就是该 primary subject 且其本人为天朝制公爵以上经理；C2/C3 只能从 stage 10 已冻结的
  `zg361_p2c_mg_subjects` 按冻结序号选择。首个三人总 quota 在 1..6 的完整组合被冻结；超限组合整体跳过，绝不截断 quota 或成员。
- #360 只冻结 manager 以及 B1/MG source identity，不预先决定 forced/exception partition。A/B 选项提交后才由
  Workforce 产品 wrapper 读取三组真实 source 并 materialize；C 不 begin、不 append、不 seal。

## 2. 两阶段 hook

1. `zg361_apply_pending_grades_effect` 先完成榜单、`zg361_b1_mark_published_effect`、清除 `zg361_review_in_progress`，随后只调用 `zg361_p2c_on_review_published_effect`。它只初始化并排 D+2 pump，不开领域。
2. `zg361_settle_delivered_325_effect` 先写 state 3、settlement receipt，并调用 `zg361_b2_on_notice_delivered_effect`，随后调用 `zg361_p2c_on_result_delivered_effect`。它仅用 exact owner/subject/cycle/result-case 唤醒正在等待的 Compensation/P3。

B1 open、D+180、事实冻结以及未送达的 3.25 都不是二期入口。
M013 公示闭合证明按显式 mode 严格互斥：route A/B 必须同时满足 `m013_mode` 存在且 `mode!=3`、`receipt_serial=current case`；合法 route C 必须同时满足 `mode=3`、`policy_debt_serial=current case`。`mode=3` 即使遗留或伪造了本轮 receipt 也不能走 A/B，`mode!=3` 即使存在本轮 policy debt 也不能走 C；缺失 mode 同样不能初始化中央案。延期披露不会丢掉合法 route C 的二期链。

## 3. 串行顺序

| Stage | 领域 | Public ABI | 中央终态 |
|---:|---|---|---|
| 1 | Career/HC | `zg361_career_hc_open_portfolio_effect` | manager completed cycle + 同一 subject closed |
| 2 | Compensation/LTI | `zg361_comp_portfolio_open_next_effect` | exact result snapshot + completed cycle；每域 ACK 后重复 pump |
| 3 | Feedback/Promotion/PIP | `zg361_pp_manager_portfolio_adapter_effect` | T→U→V→W→complete，五次单 adapter pump |
| 4–6 | Incident X/Y/Z | 三个 public domain opener | 严格 X→Y→Z；正案必须携带真实事故与后果、next-KPI staged receipt；无事故只认 exact probe/N/A tuple 并记 status 3；禁止 all-domain opener |
| 7 | Metrics/Delivery | `zg361_p3_open_portfolio_effect` | 同 result case、closed、conservation OK |
| 8 | Credit/Project | `zg361_cp_open_portfolio_effect` | closed + conservation OK；无 distinct reviewer 为 N/A |
| 9 | Career/Learning | `zg361_cl_dispatch_direct_reports_effect` | expected/completed 全齐；玩家 digest 已 ACK |
| 10 | Manager/Governance | `zg361_mg_dispatch_subordinate_managers_effect` | 冻结带 owner/cycle/case/order 的 strict-lag manager cohort，全部 F/AK terminal；空集 N/A |
| 11 | Workforce/Endgame | 初始 `zg361_we_open_portfolio_effect`；#360 `zg361_we_resume_m360_from_central_source_effect` | status 6 success；status 8 为真实 history-accruing terminal；status 7 为 count/baron 或 manager structural N/A；status 5 是外部等待 |

每次中央 pump 的 `if/else_if` 只进入一个 stage；每个 stage 每次最多调用一个 public adapter/domain opener。玩家与 AI 走同一业务 ABI 和同一顺序，差异仅是玩家 UI lane 与最终摘要；AI 后台静默。

## 4. UI、等待与 replay

- 公示后 D+2 才开首域；领域 terminal 后再 D+2 才进下一域，给 D+1 完成卡留出 ACK 时间。
- PP 的 queue lock、Compensation 的 active flag、Career/Learning 的 digest pending 都是中央真实等待条件。
- Incident X/Y/Z 的 success 额外要求 `applicable=1`、positive incident/source/consequence 与 `final_kpi_staged=1`；N/A 必须同时冻结 owner/subject/cycle、reason=1、probe/receipt serial，并回指同周期 `probe_result/source/consequence=0/0/0`。缺字段或任意旧零值都不能冒充 N/A。
- Career/HC、Compensation、PP 的 manager-only ABI 会先按各自同一筛选器预选；只有候选仍等于 frozen primary 才调用，防止资格漂移在别人身上留下 active orphan。
- Career/Learning 冻结直属 cohort/count，AH/AI expected 必须各自等于该 count；partial open 等已开案终态后记 RED。Manager/Governance 同样核对 frozen cohort 的 exact F/AK started/active/terminal，failed open 不会无限轮询。
- #360 source status 严格分为 READY=1、consumed=2、RED=4、WAIT=5、structural N/A=7。B1 status 2 的 route C、
  zero quota、absolute-grade C、单 cohort quota>6 只排除该 manager；B1 status 3 的 agenda/member/#137/#357/
  result/hash/quota 不一致是 RED，禁止换一组经理掩盖。未发布且合法流程仍 active 才是 WAIT；同轮 B1 已 terminal
  却没有 diagnostic status 同样是 RED。
- READY 同时要求每名 manager 的 exact B1 source、六槽以内真实 #357 candidate，以及同一 Central cycle 的 MG F/m036
  terminal snapshot；`team_n/member_count`、`team_bottom_n/quota` 与 snapshot 的 B1 source serial 必须一致。冻结后任一
  manager、B1 source id/hash/quota 或 MG case/revision 漂移立即 RED，绝不重选。
- delayed poll 带 `manager + cycle + central case + stage + ticket serial`；新 ticket 使旧事件 strict no-op。
- #275-A runner-up 招聘是独立于 stage 11 的 Central 产品入口：旧 AD 案 D+90 到期后只排
  `zg361p2c.4`，再以三个自然帧完成 canonical source commit → Workforce consume → Central verify/close。
  source 在拒绝候选 subject 上冻结 owner、original subject、runner/evidence、cycle/old case/state、旧 HC flight、
  m266 lineage、专用 owner 单调 serial、distinct new case 与自产 receipt/hash；`committed=1` 是 source 最后业务写。
  exact replay 不增 serial、不重签，碰撞只写诊断且不覆盖 source。
- Workforce adapter 成功前 `m275_hold_pending=1`、旧 candidate inactive、旧 owner HC flight 不变；成功后才一次性激活
  runner-up、把 `candidate_active_case` 和 owner flight 切到新案并清两个 pending。`m266_hc_receipt` 与 reserved 数量保持
  原值，不重跑 #266、不 reserve/release HC。Central 只在下一帧核对完整 durable result 后消费 source；中断重入只修复
  未完成的 consume/verify。route B 仍只走 remediation release，route C 只退役 source/debt，二者都不调用本 producer。
- 新一轮 B1 公示若撞上旧中央案，会先把旧 immutable tuple 记为 typed RED，给旧摘要 D+1 ACK 窗口，再在 D+2 精确初始化新案；禁止原地覆盖或清掉旧摘要。
- P3、Credit/Project 与 Workforce 的 D+1 域切换空档只轮询同一 portfolio tuple，不会误判 RED。
- 3.25 state 1/2 以及 Workforce status 5 都记录 external wait，绝不伪装 success。manager 的 status 5 会先调用
  `zg361_b2_submit_completed_al_receipts_effect`：它只读取 B1 #357 与 B2 #358/#359 已由真实 consumer 发布的来源票据，中央不能
  传入 receipt ID/hash；strict bridge 验证成功后才准备 route-neutral source。只有 READY 才调用新的 gated resume seam；
  WAIT 不弹窗，structural N/A 调用不造 collective 的 manager N/A close seam，RED 不再 resume。
- `zg361_we_portfolio_status=8` 必须同时带 history-accruing、39 owned operations、skipped-charter、success=0、守恒和
  closed AL state 8；中央把它当合法完成推进，而不是误落 `RED 1161`。
- 最终每名玩家 manager 只收到一张中央聚合摘要；AI 不收到中央可见事件。

## 5. 已知外部依赖

- Workforce 357–359 的 B1/B2 真实来源、产品 adapter 与中央调用已经接线；但同案 receipt 尚未到达（例如没有已裁决申诉、
  翻案后尚未完成配额回流，或走 policy route C）时，本中央案仍会诚实停在 stage 11/status 5，不会生成完成标记。
- Central 已冻结 `zg361_p2c_m360_source_*` route-neutral ABI，并引用两个同批 Workforce public ABI：
  `zg361_we_resume_m360_from_central_source_effect` 与 `zg361_we_finalize_manager_collective_na_effect`。它们必须由 Workforce
  生成器在同一集成批次实现后，本候选树才可称为可加载；旧 opener 不得承担 #360 READY resume，以免提前弹玩家事件。
- Workforce runtime 的初始 AB/AC/AD 必须允许普通 assessed count/baron；只有 #360/#361 resume 才可追加 manager 条件。中央层已经按此权限合同调用 public seam，但不修改该并发领域文件。
- 普通 count/baron 的 N/A-close seam 必须冻结 `terminal_na=1/reason=360361/owned_operations=38/skipped_manager_only=2/success=0`、`final_conservation_ok=1`、清 AL active 并写 closed=1/status=7；中央据此把 stage 11 记为 N/A。旧 runtime 若没有该 seam，中央仍以 `terminal_state=5` 外部阻点暂停：不调用无权限 ABI、不写 completed-cycle、不伪造 Workforce success，也不每两日永久重试。
- 所有结论目前只是生成可复现、静态语法/结构测试证据；尚未经过 MCP-first CK3 paused snapshot、存读档或多轮实机验收。

## 6. 测试口径

`tools/test_zg361_phase2_central_runtime.py` 静态证明：两处 hook 顺序、M013 proof 互斥、D+2 初始化、exact 3.25 wake、
单 opener、PP/Incident 顺序、权限边界、stale ticket、CP N/A、CL digest、MG strict lag、#360 frozen-order 组合、
B1 diagnostic WAIT/N/A/RED、B1+MG exact source、READY-only gated resume、manager structural-N/A、status 8 history terminal、
AI/玩家共同业务路径、#275-A 三帧 distinct requisition/receipt/hash 与 HC 守恒、BOM 与生成可复现。它不构成
fixture-live 或 production-live 证据。
