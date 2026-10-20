# R08 public one-opportunity entry

`r10_prepare` accepts an optional `case_inputs.r08_writer_one_day`, mutually
exclusive with R04/R06. The public prepare, allocate, preflight, run and verify
commands stay unchanged. Readiness and R08 use the same original `CaseClient`;
ordinary native `episode_run_id: null` remains null. This is one predeclared
natural opportunity, not a full R08 application, payment or cadence result.

The settings are `scene_root`, `source_head`, `native_build_source_head`,
`build_dir`, exact `{path,bytes,sha256}` `machine_execution_gate`, `actor_id`,
`expected_start_date_raw`, `expected_source_save_sha256`, `profile_limit_bytes`,
`driver_limit_bytes`, `deadline_utc`, a fresh lowercase `r08-...` `prefix`, and
explicit boolean `payment_enable_once_authorized`. Optional defaults are
`admission_timeout_seconds:600` (maximum900), `normal_close_reserve:900`,
`cleanup_save_reserve:120`, `poll_seconds:0.25`. Source/date/actor must match the
selected normal saved campaign. No run ID, PID or capacity is guessed at prepare.
`native_build_source_head` is the carrier's original native compile identity in
the existing Root-admission field; the standalone observer's separate build and
SYSTEM qualification belong to its exact machine execution gate. These origins
may differ. A pending or historical ordinary-incompatible gate grants no launch.

The actor first claims one opportunity, queries payment sampling, and only enables
it once if explicitly authorized and needed. It independently reads ON, collects
fresh ordinary snapshot/cash plus retained-handle FILETIME, and publishes:

- `R08-COMMON-IDENTITY.actual.json`: actual current identity, not an admission.
- `r08-before-observer-awaiting.json`: actual input pins, expected Root identity,
  current start and target start+24, and the create-only signal path.
- `r08-root-observer-admission.json`: Root supplies this after reviewing those
  actual facts. It is the existing
  `xar.e04.r206-cd-writer-explicit-root-admission.v1`, status
  `ROOT_ADOPTED_R206_INDEPENDENT_CD_WRITER_WINDOW`.

The Root grant must bind the actual scene capacity and identity pins, machine,
run, source, roots, original carrier compile head, typed expected identity with
null episode, future quota within the scene deadline, explicit no concurrent R06,
and `overrides_observer_policy_of_sha256` equal to that capacity SHA. Existing
scope is `independent-unfilmed-cd-writer-window`, `maximum_watch_ms:30000`,
`maximum_aggregate_slot_hits:128`, and payment policy
`preserve_existing_owned_window_no_enable_clear`. This actor's new control/watch
roots are inside the current case output. A scene budget alone permits no DR
observer. The selected profile, actual control/retained identity and original
normal-save provenance are checked before canonical prepare.

Only then does the existing controller prepare admission, start one observer,
require actual positive armed READY and a living original Popen, independently
re-read the same owner/window/cash, and submit one native composite exact day.
The fixed slots remain 0x2c0/0x2c8/0x28/0x30 with an aggregate128 bound and30s
watch. Unknown start or action is never replayed. After an unknown day, an
independent endpoint is retained without granting exact-day qualification.
Natural observer wait is bounded by the original45s controller deadline; no kill
or restart is added. Its current canonical consumer and C/D selector retain the
complete original raw evidence. No C/D hit means input not obtained.

The controller lifecycle is extracted from the actual ordinary-v2 source
`writer_root_driver_owner_v2.py`, SHA256
`ef27ce235ae7158ccc1dc3fae2a84110761903bfcf7bbfaafd8e2df84a1f6746`.
Historical host construction, machine paths and CLI were removed; the existing
public binder supplies the current owner and Root guard. Exact-day validation
uses the repository's existing `exact_one_day_postcondition`.

Cleanup keeps errors and original rows. With proven restore/detach, it pauses,
queries/cancels an armed original clock, disables payment sampling once, checks
independent OFF/idle/clear/zero records, then performs one ordinary Save and
independent same-date readback. This case instance wraps the original shared
normal-close method: unproved restore or OFF/clear refuses Quit and records a
normal-close error. Other case instances are unchanged. A normal stock Save
receipt is never promoted to one-life or full R08 qualification.

`R08-WRITER-RESULT.json` and `R08-WRITER-TERMINAL.json` preserve actual days,
exact-day, restoration, OFF/clear and Save separately; `full_R08_qualified` and
`business_pass` remain false. Deterministic tests exercise routing and refusal
behavior; they do not qualify native code, a machine gate or a live opportunity.

## 2026-10-20 R0222 source-only follow-up

The optional boolean `natural_phase_enable_once_authorized` defaults to `false`.
Before opening a new payment window, the actor reads natural-phase sampling;
when OFF it requires explicit once-enable authorization, submits once, then
independently reads available ON/idle state. Unknown controls are never replayed.

Cleanup independently attempts payment OFF/clear and all nine Army sampling
families OFF/clear even after a clock diagnostic error. A literal native
never-armed idle generation0/speed0 leaf is accepted only before observer claim.
Malformed or active state keeps Save/Quit withheld. Available independent OFF
readbacks, restored observer, and quiescent clock precede one Save. The close
gate additionally requires `save_verified`, set only after a successful Save
and independent same-date endpoint; unknown Save/after result cannot authorize
Quit. These are source contracts, not R0222 runtime success or full R08 credit.


## R0222 对运行边界的实证补注（2026-10-20）

适用于人工读取本专题的游玩/研究智能体；`machine_id: desktop-3fevhd2-1c74096080`，实证 source39e59acc，原件13:29–14:03Z。对应[本场专题](episode04-r0222-failed-writer-and-administrative-close-20261020.md)。原文描述的是设计流程，不是每次执行都已走完的保证；这些研究 Markdown 不会被 runtime 自动读取或执行。

- 研究源码/小测试通过不证明 runtime Python import 可用。R0222 的首次 payment query 在 native request 构造前报缺少 `tools`，当场不能把该查询当作已读取 payment 状态或可安全重放。
- actor 终态与后续行政闭场是不同事实。原 actor day/OFFclear/Save 必须保留；后续成功的行政 Save、OS/native 退出或关闭资格不回填原 actor、不生成业务信用。
- 缺失/形状不合的 sentinel speed 应按真实 malformed refusal 保留，不能拿“看起来仍暂停”替代严格 idle 证明。现有 source 下实际拒绝与后续 fix/test 候选分别记载；候选 Save gate 也必须独立验证，不提前宣称已实机修复。
- 九族 sampling、独立 supply journal、payment window 是不同开关。source 默认 payment OFF 与无 enable command 的 wire-prefix 支持有限的“未 enable”结论；独立 payment OFF/clear 仍 unknown 时必须保留 null。
- 普通 `native_campaign` Save 的 episode null 保留为 null；不得捏造 one-life。OS0/native0、原 host/public 退出码、独立 admin Popen、keeper/allocator 与 screen CAS 分别记录。
- 原 quit/menu 和 manual-review helper 对路径有固定合同。R0222 通过外置 exact-path 副本处理实际行政目录；没有修改原 helper，不能把该次适配泛化成公共 custom-output 支持。manualreview 旧失败无本地 stderr 原件时，明确引用 Root transcript，不生成假原件。
