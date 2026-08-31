# 361 二期中央串行调度层：CK3 runtime 合同

Readiness: `static-ready`

MCP evidence: `none`

CK3 live evidence: `none`

## 1. 权限和冻结身份

- 中央 ROOT 必须通过 `zg361_is_celestial_liege_trigger`：天朝制、在世、有地、公爵及以上。
- 伯爵和男爵可以作为直属受评 subject，但永远不能成为中央 manager。
- B1 公示后，从本轮已冻结结果 cohort 里按 `stewardship / position = 0` 冻结一个 primary subject。
- 中央案固定 `manager + B1 cycle/case + review cycle + subject + result case`；死亡、调任、换 owner/cycle/case 都 typed RED，绝不换人续跑。

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
| 4–6 | Incident X/Y/Z | 三个 public domain opener | 严格 X→Y→Z；禁止 all-domain opener |
| 7 | Metrics/Delivery | `zg361_p3_open_portfolio_effect` | 同 result case、closed、conservation OK |
| 8 | Credit/Project | `zg361_cp_open_portfolio_effect` | closed + conservation OK；无 distinct reviewer 为 N/A |
| 9 | Career/Learning | `zg361_cl_dispatch_direct_reports_effect` | expected/completed 全齐；玩家 digest 已 ACK |
| 10 | Manager/Governance | `zg361_mg_dispatch_subordinate_managers_effect` | 冻结 strict-lag manager cohort 全部 F/AK terminal；空集 N/A |
| 11 | Workforce/Endgame | `zg361_we_open_portfolio_effect` | success 只认 closed=1/status=6；非 manager 的 closed=1/status=7 为 N/A；status=5 是 357–359 外部等待 |

每次中央 pump 的 `if/else_if` 只进入一个 stage；每个 stage 每次最多调用一个 public adapter/domain opener。玩家与 AI 走同一业务 ABI 和同一顺序，差异仅是玩家 UI lane 与最终摘要；AI 后台静默。

## 4. UI、等待与 replay

- 公示后 D+2 才开首域；领域 terminal 后再 D+2 才进下一域，给 D+1 完成卡留出 ACK 时间。
- PP 的 queue lock、Compensation 的 active flag、Career/Learning 的 digest pending 都是中央真实等待条件。
- Career/HC、Compensation、PP 的 manager-only ABI 会先按各自同一筛选器预选；只有候选仍等于 frozen primary 才调用，防止资格漂移在别人身上留下 active orphan。
- Career/Learning 冻结直属 cohort/count，AH/AI expected 必须各自等于该 count；partial open 等已开案终态后记 RED。Manager/Governance 同样核对 frozen cohort 的 exact F/AK started/active/terminal，failed open 不会无限轮询。
- delayed poll 带 `manager + cycle + central case + stage + ticket serial`；新 ticket 使旧事件 strict no-op。
- 新一轮 B1 公示若撞上旧中央案，会先把旧 immutable tuple 记为 typed RED，给旧摘要 D+1 ACK 窗口，再在 D+2 精确初始化新案；禁止原地覆盖或清掉旧摘要。
- P3、Credit/Project 与 Workforce 的 D+1 域切换空档只轮询同一 portfolio tuple，不会误判 RED。
- 3.25 state 1/2 以及 Workforce status 5 都记录 external wait，绝不伪装 success。manager 的 status 5 会先调用
  `zg361_b2_submit_completed_al_receipts_effect`：它只读取 B1 #357 与 B2 #358/#359 已由真实 consumer 发布的来源票据，中央不能
  传入 receipt ID/hash；strict bridge 验证成功后才调用既有 resume seam。
- 最终每名玩家 manager 只收到一张中央聚合摘要；AI 不收到中央可见事件。

## 5. 已知外部依赖

- Workforce 357–359 的 B1/B2 真实来源、产品 adapter 与中央调用已经接线；但同案 receipt 尚未到达（例如没有已裁决申诉、
  翻案后尚未完成配额回流，或走 policy route C）时，本中央案仍会诚实停在 stage 11/status 5，不会生成完成标记。
- Workforce runtime 的初始 AB/AC/AD 必须允许普通 assessed count/baron；只有 #360/#361 resume 才可追加 manager 条件。中央层已经按此权限合同调用 public seam，但不修改该并发领域文件。
- 普通 count/baron 的 N/A-close seam 必须冻结 `terminal_na=1/reason=360361/owned_operations=38/skipped_manager_only=2/success=0`、`final_conservation_ok=1`、清 AL active 并写 closed=1/status=7；中央据此把 stage 11 记为 N/A。旧 runtime 若没有该 seam，中央仍以 `terminal_state=5` 外部阻点暂停：不调用无权限 ABI、不写 completed-cycle、不伪造 Workforce success，也不每两日永久重试。
- 所有结论目前只是生成可复现、静态语法/结构测试证据；尚未经过 MCP-first CK3 paused snapshot、存读档或多轮实机验收。

## 6. 测试口径

`tools/test_zg361_phase2_central_runtime.py` 静态证明：两处 hook 顺序、M013 两套公示证明的 mode 互斥与混用反例、D+2 初始化、exact 3.25 wake、单 opener、PP/Incident 顺序、权限边界、stale ticket、CP N/A、CL digest、MG strict lag、Workforce 来源 adapter→verified→resume 顺序与 status 5 等待、AI/玩家共同业务路径、BOM 与生成可复现。它不构成 fixture-live 或 production-live 证据。
