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

沿用 pairwise 核心的 `raiktor-campaign-dominance-certificate-v1`。证书必须绑定同一
paused frame、candidate SHA-256、六域 terms SHA-256 与 owner pairwise limits
SHA-256，并完整声明：

- campaign outcome distribution 与所有合理 encounter；
- 当前可动员兵、reserve、补员、围城与增援 ETA；
- finance endurance；
- model risk、tail risk、sunk-cost exclusion；
- claims base 和六域的 valuation；
- continue/surrender 的保守 utility interval 与 hard-budget breaches。

当前仓库没有生产该证书的 provider。战分和战争时长只是必须 hash-bind 的模型输入，
不是替代证书的投降阈值。

### Owner budget profile

`raiktor-owner-budget-profile-v1` 显式包含 profile identity、provenance、source artifact
SHA-256 与 production eligibility。它复用 pairwise limits，并另外冻结 white peace
允许的 gold transfer、prestige loss、removed claims、favor hook 与 truce days。外层
profile identity 必须与内嵌 pairwise limits 完全一致。

当前没有 owner-approved profile provider，因此真实 checkpoint 返回
`owner_budget_profile_unavailable`。测试里的数值全部标为 synthetic/do-not-ship；核心
没有默认阈值，也不会从玩家余额、战分或历史行为猜 owner 偏好。

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
由 provider 发布。当前这个 provider 也不存在，所以真实 checkpoint 返回
`white_peace_comparison_certificate_unavailable`。

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
  paused/live shape evidence；
- `raiktor-campaign-dominance-certificate-provider-v1` unavailable；
- `raiktor-owner-budget-profile-provider-v1` unavailable；
- `raiktor-white-peace-comparison-provider-v1` unavailable。

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

后续最小路径是先补上述只读 provider、剩余 aggregate public wire，并完成 truce
`evaluated_days` 的 paused/live shape probe，再把静态 recommendation 接入 typed
termination submit gate；最后在一次 CK3 启动里完成双查询、唯一 submit、六域
postcondition、postwar checkpoint。不得用 OCR 或重复跑局替代缺失 provider。

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
