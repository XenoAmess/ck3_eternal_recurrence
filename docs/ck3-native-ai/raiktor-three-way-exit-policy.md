# Raiktor 三方退出决策静态核心

状态：**static policy / public session binding production-live evidence，not action-ready**。本专题记录
`raiktor-three-way-exit-policy-v1` 的输入、选择规则和当前真实 RED；它不修改
native bridge、MCP、planner 或 CK3 写口，也不关闭 `GEN-034`。

## 目标与边界

当前 G2 冻结点中，玩家 CharacterID `29829` 是 WarID `50331699` 的 primary
attacker，CB 为 `raiktor_claim_cb`，战分 `-50`、持续 1281 日。原生查询已经证明
surrender 合法且会被接受，但这些事实只建立候选，不能证明“现在投降最好”。

新核心把已有两项合同组合起来：

1. `raiktor-surrender-six-domain-v1`：投降 claims base 与六个 dynamic domain；
2. `raiktor-continue-vs-surrender-policy-v1`：continue 与 surrender 的保守 pairwise
   比较。

它再要求显式 owner budget 和 white-peace comparison，才能比较 continue、white
peace、surrender。输出最多是静态 `recommended_outcome`；始终保持
`action_ready=false / action_literal=null / automatic_surrender_ready=false`。pending、
cooldown、唯一 submit、ACK 后状态与六域 action-boundary postcondition 都不在本核心
内，不能由 fixture GREEN 推导为已完成。

还有一个必须保留的继承边界：six-domain v1 child 本身只携带
revision/date/WarID/CB/角色身份，不能单独证明跨 connection/episode/PID 的 session
provenance。public aggregate 的 additive session wrapper 现已补齐并实机验证这些字段，
所以该 wrapper 可以作为 production-live session-binding evidence；它不会反向改写 child
schema，也不会替代 campaign、owner budget、white-peace、truce 或 war-bound provider。
因而本静态核心仍固定保持 `production_recommendation_ready=false`。

## 三类新增输入

### Campaign dominance certificate

历史 pairwise 核心的 `raiktor-campaign-dominance-certificate-v1` 仍描述完整 forecast/utility 输入。证书必须绑定同一
paused frame、candidate SHA-256、六域 terms SHA-256 与 owner pairwise limits
SHA-256，并完整声明：

- campaign outcome distribution 与所有合理 encounter；
- 当前可动员兵、reserve、补员、围城与增援 ETA；
- finance endurance；
- model risk、tail risk、sunk-cost exclusion；
- claims base 和六域的 valuation；
- continue/surrender 的保守 utility interval 与 hard-budget breaches。

该 v1 完整 forecast 仍没有生产 provider。战分和战争时长只是必须 hash-bind 的模型输入，
不是替代证书的投降阈值。2026-09-06 的施工审计进一步确认：当前只有 strict consumer，
没有 campaign-level production producer；v3 hypothetical combat fixture 与 100,000 次
research-only fixed-contact 输出都明确不可用于 planner。因而本项暂不新增 schema wrapper，
生产入口与重开条件见
[g2-campaign-provider-go-no-go-2026-09-06.md](g2-campaign-provider-go-no-go-2026-09-06.md)。

2026-09-12 的当前 G2 规划将 GEN-034-A 裁成可交付的 measured-power 层：
[`raiktor-campaign-dominance-certificate-v2`](g2-campaign-dominance-certificate-v2-2026-09-12.md)
只把 R471 的稳定双查询转换为 `actor_stronger / opponent_stronger / equal`，并接入 three-way intake。它明确保持
forecast、utility、recommendation 和 action 关闭，因此不会把单一兵力比伪装成完整 v1 战役模型。

### Owner budget profile

`raiktor-owner-budget-profile-v1` 显式包含 profile identity、provenance、source artifact
SHA-256 与 production eligibility。它复用 pairwise limits，并另外冻结 white peace
允许的 gold transfer、prestige loss、removed claims、favor hook 与 truce days。外层
profile identity 必须与内嵌 pairwise limits 完全一致。

owner-authored file provider 已完成静态实现，但当前仓库没有 owner-approved source artifact，
因此真实 checkpoint 仍返回 `owner_budget_profile_unavailable`。测试里的数值全部标为
synthetic/do-not-ship；核心和 provider 都没有默认阈值，也不会从玩家余额、战分或历史行为猜
owner 偏好。provider 合同与审批边界见
[g2-owner-budget-profile-provider-2026-09-06.md](g2-owner-budget-profile-provider-2026-09-06.md)。

### White-peace comparison certificate

`raiktor-white-peace-comparison-certificate-v1` 必须同时绑定 candidate、surrender
terms、campaign certificate 与 owner budget 的 SHA-256，并在相同 paused frame 提供：

- context、native validator、available 与 typed final recipient response；
- declared-target claim retention 与 title-holder change count；
- actual primary gold transfer、attacker prestige delta、truce duration；
- prisoner-release pairs、favor-hook application 与 hostage variant；
- 同一 `owner_utility_q100000` 单位的 conservative white-peace interval；
- completeness、model risk、hard-budget breach 与 producer provenance。

只读到“白和按钮可点”或 acceptance raw 为正不够；final typed response 和实际条款仍须
由 provider 发布。四输入 comparison provider 已 static-ready，但当前没有完整同帧 Raiktor
white-peace terms observation、owner utility evaluation、campaign certificate 与可用 owner profile，
所以真实 checkpoint 仍返回 `white_peace_comparison_certificate_unavailable`。合取合同见
[g2-raiktor-white-peace-comparison-provider-2026-09-06.md](g2-raiktor-white-peace-comparison-provider-2026-09-06.md)。

## 选择规则

先剔除未通过 candidate-specific legality / hard budget 的结果。对剩余候选，仅当某一
候选的 utility lower bound 至少高于所有其它候选的 utility upper bound 加上 owner
`minimum_switch_margin_raw` 时，才发布该唯一 `recommended_outcome`。否则返回
`three_way_underdetermined`。

这个规则允许三种静态结果都被独立覆盖：

- safe objective 已证明、continue 在 tail/hard budget 内且稳健占优：`continue`；
- white peace 的完整条款在 budget 内且稳健占优：`white_peace`；
- 无 safe objective、无及时可信援军、continue tail budget 已越界，且 surrender
  条款在 budget 内并稳健占优：`surrender`。

缺 provider 是 `evidence_required`，不是 underdetermined。提供了证书但区间重叠才是
`three_way_underdetermined`。这样可以区分“还没观测”与“已经观测但没有稳健赢家”。

## 不得猜测的战争兵力

Raiktor 脚本最初生成六支、每支 500 人的事件军，只证明 authored source count。
`3000` 不是 measured pre-soldiers，也不是 current soldiers 或 proven loss。现有 generic
war-bound current 只能作为 conservative exposure；没有 source attribution / pre snapshot /
action-bound loss provider 时，这三项继续为 false。新核心没有 `3000` 数值字段，也不因
缺失这些字段把它填入 campaign certificate。

## 当前真实 readiness

当前冻结 checkpoint 的 typed RED 是：

- public same-frame aggregate 的 connection/episode/PID/revision/cache session binding 已有
  production-live evidence，但 aggregate 仍因 truce 与 source-specific war-bound 缺失而
  `status=incomplete`；
- truce 的 `evaluated_days` leaf 已接入 terms/MCP public wire，但尚无可提升 readiness 的
  paused/live shape evidence；passive callsite postprocessor 已有静态 intake，可在 GREEN、
  两处 return 稳定相等且 manifest/source/session identity 全匹配时复用现有 truce v1，
  但当前没有该 GREEN live artifact，因此本项仍 unavailable；
- `raiktor-campaign-dominance-certificate-provider-v1` 经施工审计为 NO-GO：当前没有 production
  producer，不实现 synthetic/external JSON wrapper，certificate 继续 unavailable；
- `raiktor-owner-budget-profile-provider-v1` 实现 static-ready，但无 owner-approved source，
  当前 profile instance unavailable；
- `raiktor-white-peace-comparison-provider-v1` 实现 static-ready，但 terms/utility/campaign/owner
  输入未闭合，当前 comparison instance unavailable。

所以当前仍是：

```text
recommended_outcome = null
production_recommendation_ready = false
full_exit_decision_ready = false
action_ready = false
action_literal = null
automatic_surrender_ready = false
GEN-034 = unresolved
```

后续最小路径不是先空造 campaign provider，而是先取得它所要求的 production producer：
planner-usable encounter forecast、同帧 campaign state/finance/ETA 和 owner-approved valuation。
与此同时只推进已有明确生产入口的剩余 aggregate/live 工作；输入闭合后再把静态
recommendation 接入 typed termination submit gate。最后在一次 CK3 启动里完成双查询、
唯一 submit、六域 postcondition、postwar checkpoint。不得用 OCR、测试 fixture 或重复跑局
替代缺失 producer。

2026-09-07 已增加
[统一 fail-closed intake](g2-three-way-exit-intake-2026-09-07.md)，将 owner source provider、
white-peace provider 和本策略接成一个纯离线调用入口。它只消除了未来真实产物消费时的手工拼接，
不产生任何缺失 provider，也固定保持 production/action 门关闭；上述真实 blocker 和后续路径不变。

## 离线验收

```powershell
$env:PYTHONPATH = "ck3_autonomous_player/src;ck3_autonomous_player/tests/unit"
py -m unittest ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_policy.py
py -O -m unittest ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_policy.py
```

测试覆盖三种稳健赢家、区间重叠、missing provider、stale hash、incomplete domain、owner
profile identity drift、white-peace budget breach、claim retention 未证明，以及所有 action/live
字段继续关闭。测试只使用 synthetic fixture，不是 CK3 paused artifact。

## 2026-09-02: post-race MCP-first probe

The previously observed launch-before RED was rerun once after the
`prepare_profile` Git-status stabilization (`6e27221`). The attempt reached
profile preparation and cold-checkpoint validation successfully, so the old
`git status` failure did not recur. It then launched the exact-build,
non-debug CK3 process, but native readiness never became available within the
bounded 120-second window. No snapshot, terms query, mutation, or surrender
action was issued.

Evidence is retained at
`C:\\Users\\xenoa\\AppData\\Local\\Temp\\xar-g2-truce-paused-live-20260902T012000\\report.json`
(5,920 bytes, SHA-256
`C9EB36E1861037A7AC25ED16494FCD41EC921851343D531B09FFBAD9A9D313E4`). The
report binds checkpoint SHA
`60108A5DA03DC3A8315A3E79897D9CF2F49763910A8AA15A462E7DD0B6AAF164`, driver
state SHA
`4FB901C77AF6D95A05EAB2B0E900AE2E07A652B4C14729835DECB69FC8CFF57E`, and the
expected CK3 executable SHA. Preparation and cold validation are present;
cleanup is proven GREEN; the capability result is **harness/startup RED**, not
truce capability evidence. The exact-build paused MCP gate and `GEN-034`
remain unresolved. Do not repeat this same checkpoint attempt until the
startup/readiness cause is changed or a new frozen artifact is supplied.

## 2026-09-02 fresh semantic-ready evidence

The next bounded entry did reach a semantic-ready paused frame after the
required offline accelerator preflight. The retained report is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\report.json`
(SHA-256
`4A7C66D34C851698572F4BBA2970ECAA00C005C2DC338ABCD75A7FD304F0B991`), bound
to `open_kaishek` `757fb1b` and JAR SHA
`D4BA0FF5E6A9C85ED0853FD78D44940E98445F2867E9D6CA5902AF0E19B29476`.

The concrete terms step was advertised and two read-only queries returned
equal normalized payloads on `native:3 / revision=4 / native_revision=3`
(`date_raw=53223936`, player `29829`, WarID `50331699`, opponent `36769`).
The four narrow component rows (gold, prestige, prisoner release, and favor
hook) are live/read-only available. The six-domain decision is not ready:
`evaluated_days_observable=false`, `evaluated_days=null`, expiry and
war-bound losses remain unobserved, so `truce_ready=false`,
`production_recommendation_ready=false`, `action_ready=false`, and
`GEN-034` remains unresolved. No action or mutation was sent; cleanup and
checkpoint/driver invariants were GREEN. This artifact supersedes the earlier
"no paused artifact" wording for the narrow component rows while preserving
the full-exit RED boundary.

## 2026-09-02 evaluator evidence and current preflight

The frozen exact-build evaluator contract was rechecked statically: RVA
`0x3373000` takes `(script_value, effect_context, evaluation_context)` and
returns `int32`; both CAddTruce callers use `+0x108` and `context+0x28`.
There is no evidence-backed alternate offset, so the public v1 wire and
six-domain frozen hashes remain unchanged. A future paused probe must bind
`open_kaishek` `36b4743d5da013ba1f85790ebcffad2629442ed1` and JAR SHA
`DFEA464B657D627BBB1AEF34C12CD91419830644D47F891782A3C9D718C44D61`; its
offline preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T1042-war-days\open-kaishek-preflight-war-days.json`
(SHA-256
`CDC7DCD22888208C7585A2932F266912CAE4C08A9D0836D7EF6580796FC8571F`).
No CK3 rerun or termination write is justified by this static result.

## 2026-09-02 surrender execution-readiness projection

[static-ready; no CK3 launch; no mutation] The pure
`raiktor-surrender-execution-policy-v1` projection now composes the frozen
three-way decision with the six-domain aggregate and separates three gates:
production decision readiness, typed surrender submission, and the
action-boundary postcondition bundle. It never accepts score, duration, an ACK,
or old-WarID disappearance as a substitute for those gates, and it emits no
action literal while readiness is false.

The current typed blockers are explicit rather than implicit in the native
driver's blanket rejection: the three-way providers and production decision
are not ready; the v1 aggregate lacks connection/episode/PID provenance;
truce `evaluated_days` is still pending paused/live evidence and persisted
expiry is unobservable; source-specific war-bound pre/action/post identity is
unavailable; and typed-submit pending/cooldown plus post-state observers are
not implemented. The postcondition contract requires all eight observations
in one lifecycle: old WarID absence, both gold sides, attacker prestige,
declared-target claim removal, directional truce days and expiry, exact
prisoner releases, conditional favor hook, and source-specific regiment
cleanup. ACK and WarID absence alone remain insufficient.

The executable contract and synthetic tests live in
`ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_surrender_execution_policy.py`
and `ck3_autonomous_player/tests/unit/test_raiktor_surrender_execution_policy.py`.
This is a static construction seam for the future live provider; it does not
change `automatic_surrender_ready=false`, `GEN-034=unresolved`, the public
action surface, or any production-live claim.

## 2026-09-02 aggregate session-binding seam

[static-ready; read-only; no CK3 launch] The new
`raiktor-six-domain-session-binding-v1` aggregator binds an already normalized
six-domain result to fields already published by the Python bridge. It requires
one paused snapshot, its terms-query receipt, and the aggregate to agree on
snapshot/public/native revisions and date. It also requires the snapshot and
receipt to agree on `connection_generation` and `episode_run_id`, binds
`episode_character_id` to the aggregate primary attacker, and projects the
existing `snapshot.diagnostics.bridge_pid` unchanged as canonical
`process_id`.

Missing, invalid, or drifting fields return typed `status=unavailable`; no
default identity, PID lookup, inferred episode, or cross-frame fallback exists.
The surrender execution projection consumes an exact available binding and
also hashes the enclosed aggregate against its terms input. A static fixture
can therefore remove only the old `six_domain_session_provenance_not_bound`
blocker. Truce expiry, source-specific war-bound attribution, production
decision providers, typed submit, pending/cooldown, and action-boundary
observers remain blocked, so no surrender literal is advertised.

This package added no native reader, RVA/RTTI work, or mutation. At this static
stage the binding was not production-live; the later paused acceptance below
closes only that session-binding evidence gap.

The unified `raiktor-three-way-exit-intake-provider-v1` now publishes this
existing execution projection beside its three-way assessment. A supplied
exact aggregate session binding is forwarded only to this projection; it does
not promote the intake's production recommendation, action literal, submit
capability, cooldown or postcondition gates. Outcome-only historical adapters
without candidate/terms expose no execution projection rather than inventing
those inputs.

## 2026-09-02 public query wiring

[static-ready; read-only; no CK3 launch] The existing
`ck3_query_war_termination_terms` driver/service/MCP path now publishes one
additive `raiktor_surrender_aggregate_session` wrapper. The projection reuses
the query receipt's snapshot/public/native revisions, connection generation,
episode run, episode character and bridge PID. The same wrapper is retained in
the exact-frame `war_termination_terms` snapshot cache; existing terms fields
and the generic `claim_cb` response remain unchanged.

For `raiktor_claim_cb`, the adapter can promote the already normalized public
claims base plus live gold, prestige, prisoner-release and favor-hook rows into
the frozen six-domain shape. It deliberately leaves truce unavailable because
the public terms row does not carry the strict pointer-shape and evaluator
double-read proof, even when `evaluated_days` is present. Generic war-bound is
also unavailable until its strict same-frame payload reaches this query. A
missing episode, process, receipt or aggregate field returns typed
`status=unavailable`; it is never defaulted.

Focused driver and MCP SDK tests proved the additive wrapper survives the real
public return and cache paths. At this static stage it was not production-live
evidence:
`action_terms_ready=false`, `automatic_surrender_ready=false`, and no surrender
literal or mutation was added. The paused run below later validates the
wrapper's session binding; strict truce and generic war-bound public inputs
remain missing.

## 2026-09-02 paused session-binding acceptance entry

[ready-to-run; no CK3 launch in this package] The dedicated
`run_raiktor_surrender_session_binding_live_acceptance.py` wrapper reuses the
existing terms runner's exact-build, cold-checkpoint, double-query and cleanup
flow. It adds strict checks for the query receipt's connection generation,
episode run, snapshot/public/native revisions, and the wrapper's episode
character plus CK3 process ID. After each query it also requires the matching
`war_termination_terms` cache row to carry the same wrapper, query sequence and
session fields.

The acceptance remains read-only: the only permitted gameplay commands are
two `query-war-termination-terms-v1-<WarID>` calls. Both projected aggregates
must remain incomplete with truce and generic war-bound typed unavailable,
`action_terms_ready=false`, and `automatic_surrender_ready=false`.

Run `--preflight-only` first with the frozen checkpoint/driver-state inputs.
This mode hashes the input bundle, exact CK3 executable and bridge binaries,
checks the driver episode/date anchor and frozen public-wiring contract, writes
a `ready-to-run` JSON report, and exits without preparing a profile or calling
the managed CK3 session. Omit `--preflight-only` only after the exclusive CK3
slot is assigned; the wrapper repeats this no-launch check immediately before
delegating to the live runner. Before the later report existed, both the
session-binding live claim and surrender readiness remained false.

The frozen-input preflight is retained at
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-public-session-binding-ready-20260902\no-launch-preflight-v2.json`
(SHA-256
`8A71627001E8B0AA3C974BCE016A7710078ADE6B9F4F089B665EEF8F30DC61DB`).
All checks are GREEN, `ck3_started=false`, `profile_prepared=false`, and at
preflight capture time the reserved `live-attempt` path did not exist. This is
readiness evidence, not a paused/live capability artifact.

## 2026-09-02 patched public session-binding GREEN

[production-live evidence; read-only session binding only] The patched wrapper
completed one exact-build, cold-checkpoint paused acceptance at
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-public-session-binding-live-patched-20260902T2010\report.json`.
The report is GREEN (`ok=true`, `error=null`) with SHA-256
`DD46F69ABB6B1DFA2C35B5FA72D394EC99291CA6F4421C37B8179343432B135D`.
Its canonical session-binding summary SHA-256 is
`118A7D0C2FF12A419E99221CF2A8126FA8DB95143BB34C6F26A0978EAEA60FDD`;
the embedded cleanup summary SHA-256 is
`AF1263B34F0AE88FE52148903470CEC1FEF2D1E5C4477F80C585EF0A9E564D9B`.

The runner issued exactly two
`query-war-termination-terms-v1-50331699` commands (`query_sequence=1 -> 2`)
and `mutation_commands=[]`. Both results and their matching cache rows bind
the same `snapshot_id=native:3`, public revision `4`, native revision `3`,
connection generation `1`, episode `native-29829-809d91e48a8d`, character
`29829`, CK3 PID `10360`, and WarID `50331699`. Both session normalization,
query-receipt, cache equality, repeat-binding, and read-only boundary checks
are GREEN.

The observed result deliberately remains an incomplete six-domain aggregate:
`missing_domains=[truce, generic_war_bound_current]`, with both domains typed
`{"available": false}`. `action_terms_ready=false` and
`automatic_surrender_ready=false`; cleanup proves shutdown, process-tree
removal, and driver closure. This artifact promotes only the additive public
session binding to production-live evidence. It does **not** promote truce,
generic/source-specific war-bound loss, the complete six-domain decision, any
termination action, or automatic surrender; `GEN-034` remains unresolved.

## 2026-09-03 generic war-bound aggregate intake

[static/fixture-ready; no CK3 launch; no mutation] The public aggregate adapter
now has an optional intake for the already frozen
`generic_war_bound_visible_source_unattributed` payload.  It accepts the value
only after the existing strict normalizer binds its paused snapshot/native
revision, date, full WarID, primary attacker/defender and CB database index to
the aggregate frame.  Missing input, malformed generations, aggregate drift,
or any frame/CB mismatch remains the existing typed
`{"available": false}` domain.

An accepted payload promotes only `generic_war_bound_current_ready`; source
attribution, pre soldiers and proven loss stay false, and authored `3000` is
not used as any observed soldier value.  The production driver does not yet
supply this optional payload, so the real public query and cached session
binding remain wire-compatible and still return generic war-bound unavailable.
No surrender recommendation, command literal, postcondition claim, or
automatic policy is added; `GEN-034` remains unresolved.

The next distinct live gate is to publish the strict generic payload on the
same paused public query frame and prove two identical, session/cache-bound
queries.  This is separate from the action-bound source/pre/loss capture and
from persisted truce-expiry observation.

## 2026-09-04 actual-expiry provider candidate

The exact-build static chain for the persisted one-way truce expiry is now
closed and compiled behind a default-off option. This differs from the earlier
duration leaf: the new provider calls CK3's lookup-only `has_truce` predicate
and native end-date getter after result application, with owner fixed to the
living player and toward fixed to a full-generation CharacterID. It never
derives expiry from `evaluated_days`.

This is still `static-ready / live-pending`. An ACK is only transport success;
`readiness=true` requires same-frame stable native predicate/getter results and
a future persisted date. Therefore the policy's production recommendation,
action readiness, automatic surrender, and `GEN-034` remain false. The next
distinct checkpoint is two identical provider frames after surrender has
applied and the old WarID is absent; see
`g2-actual-truce-expiry-candidate-2026-09-04.md`.

## 2026-09-03 generic war-bound public query-frame producer

[static/fixture-ready; no CK3 launch; no mutation] The exact-build production
terms reader now consumes the already frozen generic war-bound observer. It
double-reads the full-generation persistent/current/CArmy identity graph and
each exact current `CArmyRegiment+0x38` soldier count, then passes those inputs
through the existing strict builder. The production DLL now links that builder
and emits its result as an optional `generic_war_bound_current` child in the
existing Raiktor terms envelope.

The DLL child is stamped with the native state revision. The public driver
accepts it only when that revision, paused date, WarID, CB database index and
primary attacker/defender match the query's admission snapshot; it then binds
the child to that snapshot's public revision before projecting the aggregate,
session wrapper and exact-frame cache row. Old artifacts without the additive
child remain valid and yield typed unavailable; any identity or revision drift
fails the query instead of falling back to a guessed frame.

This producer can make only
`generic_war_bound_current_ready=true`. `source_attribution.mode` remains
`authored_candidate_only`; source-specific readiness, pre soldiers, proven
loss, cleanup, action terms and automatic surrender all remain false/null.
Authored `3000` is metadata only and is never substituted for observed current
or pre-action soldiers. The native and Python deterministic fixtures exercise
the `80 + 60 + 40 = 180` current total, all seven composition rows, public
revision binding, CB/revision rejection and the unchanged action boundary.

The next distinct live prerequisite is a single paused read-only run with the
new DLL, exactly two terms queries, and equality across strict child,
six-domain aggregate, session identity and cache binding. Until that artifact
exists this is not production-live evidence, and it does not advance truce,
source-specific war-bound loss, surrender action or `GEN-034` completion.

## 2026-09-05 R3 postwar outcome consumer

[static/no-launch consumer GREEN; decision still RED] The retained private R3
report (SHA-256
`44E1F7C0B470B2CF7B6549192865402F21F88C7CF073E896DE1B93632311D5D0`)
is now consumed by this policy through the optional
`observed_surrender_outcome_value` input. The adapter revalidates the existing
retention ticket and the complete action-bound receipt before projecting the
same PID/generation/episode surrender, generic exact-store `598 -> 0`
cleanup, and non-formula persisted expiry with `evaluated_days=1825`.

The output is intentionally
`observed_generic_boundary_source_attribution_required`. It records the
measured postwar checkpoint, but keeps
`source_specific_loss_comparison_ready=false` and
`comparison_input_ready=false`; the generic rows cannot enter campaign utility
as Raiktor-source losses. It also cannot replace the missing campaign,
owner-budget, or white-peace providers, so `recommended_outcome=null` for the
current checkpoint and action/readiness/automatic surrender/`GEN-034` remain
false.

The compact no-launch consumer artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-postwar-comparison-intake-e72f9fa-20260905\intake-r1.json`
(SHA-256
`01C0EBAAB1B5BF59EC077118C9DF9C23FC380668D4D10101874AF3DA98939C9E`).
Its exact next source-attribution entry remains the already frozen
`bookmark.1071.a` `spawn_army` post-finalize window at RVA `0x2E7F951`: bind
all six executions to the selected loaded node and exact WarID, then freeze
their created persistent/current/CArmy generations before gameplay advances.
See
[g2-postwar-outcome-comparison-intake-2026-09-05.md](g2-postwar-outcome-comparison-intake-2026-09-05.md).


## 2026-09-11 R459 observed surrender input

R459 supplies the previously missing production source-specific surrender observation. The six captured event-army executions measured 3000 soldiers at creation and before termination; one accepted surrender destroyed the exact bound generations to zero. The same postwar frame also provides persisted truce expiry `53227656` for the evaluated 1825-day duration. Offline intake `43B0A053...4FE1` normalizes this as observation `BA139830...F462` with `source_specific_loss_comparison_ready=true` and `comparison_input_ready=true`.

This closes the observed-surrender input only. The policy still returns `evidence_required` with exactly three providers: campaign dominance, owner-authored budget, and same-frame white-peace comparison. `recommended_outcome`, decision/action readiness, automatic surrender, and `GEN-034` remain false.

## 2026-09-12 active-war strategic-power input

The Python/MCP layer now admits the current
`active_wars[*].primary_opponent_character_id`, in addition to a current
declaration target, and returns an explicit `target_scopes` classification.
R470 showed that the old native DLL still rejects that opponent with
`target_not_declarable` before evaluator execution, so this input remains a
production RED and requires a narrow native admission update. See
[active-war-strategic-power-query.md](active-war-strategic-power-query.md).

The Python package remains statically verified (`23/23` in normal and optimized
tests), but the end-to-end capability is not ready. R470 issued one read-only
query, then stopped without retry, time advance, or mutation. Campaign dominance,
owner-authored budget, same-frame white-peace comparison, recommendation,
action readiness, automatic surrender, and `GEN-034` therefore remain false.

## 2026-09-12 R471 active-war strategic-power observation

R471 closes the missing live observation primitive for the current opponent.
Two official MCP queries on the same paused snapshot returned identical native
payloads: player `29829` power `13075500000`, opponent `28551` total power
`16770900000`, and native ratio `128262/100000` (opponent 1.28262 times the
player). The target source is `active_war_primary_opponent`, all native
readiness bits are true, and the only two new native-history rows are the two
successful read-only queries.

The original report's RED is an explained harness audit error: it read
`history`, while the public snapshot field is `native_command_history`. The
corrected offline reclassification is GREEN and preserves the original report;
no query was replayed and no CK3 process was restarted. Report/reclassification
SHA-256 values are `F4676762...E7CD` and `D8F43EAB...24C9`.

This promotes only the current-opponent strategic-power provider to
`production-live primitive`. A single ratio is an input to campaign dominance,
not the campaign-dominance certificate itself. Recommendation,
decision/action readiness, automatic surrender, and `GEN-034` remain false.

## 2026-09-12 versioned strategy budget profile

`GEN-034-B` now has an active repository profile at
`ck3_autonomous_player/strategies/raiktor_exit_budget_v1.json`. Its identity is
`raiktor-exit-balanced-v1 / 1.0.0`; exact source bytes are SHA-256
`4206D725EC702701725221EB274E1F248E607F3127B720D033779FD71154FD11`.
The provider uses this path when no external source is supplied. A complete
versioned operator override remains available, but it must declare the default
profile ID/version as its base; a stale or unrelated override is rejected.
Legacy explicit owner artifacts remain readable for compatibility.

The reusable offline CLI emitted GREEN receipt
`Z:\ck3_mod_rewrite\_runtime\g2-gen034-strategy-profile-20260912\repository-default-profile.json`,
SHA-256 `BB20D87233DF6C854DD668FD1641AE590DFFA3BD87CF82099A1A97EBF20C7981`.
It starts no CK3 process, supplies no campaign or white-peace evidence and
authorizes no action. Focused provider/intake/file-intake tests pass `25/25`
under normal and optimized Python.

GEN-034-A now converts this production-live primitive into a v2 measured-power
dominance certificate. Its receipt is `AB0DB567...E0569`, and the three-way
intake retains it while forecast, utility, recommendation and action remain
false. GEN-034 is now `2/4`: same-frame white-peace comparison and the
integrated recommendation/action package remain.
Whole-program G2 remains `0/8`; the former `T1=90%` label is retired.
