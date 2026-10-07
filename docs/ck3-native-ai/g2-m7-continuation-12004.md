# G2 M7 ordinary goal restoration on exact 1.20.0.4

2026-10-07 / W41. Source baseline: `23c3c4bc7fdf261f46174d35db12732808523463`.
This is the short execution recipe for the existing ordinary goal, checkpoint
and natural successor consumers. It adds no second restore helper or driver.
The current live entry remains Robert29829 in the original ordinary campaign
`native-29829-2bc2d599f7f9`; natural successors come from CK3, not an authored
CharacterID. Multi-government/seed qualification is tracked separately in
[the government/seed recipe](g2-government-seed-qualification-12004.md).

## Current frame and evidence boundary

Exact game: CK3 **1.20.0.4**, Steam25734779, EXE SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The Root-owned `R0061` small receipts at
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/managed-full-h9613-finaltools10/operator/`
are `ROOT-FULL-ORIGINAL-PAUSED-SNAPSHOT-QUALIFIED.json` and
`final-owner-fields/SCENE-FIELDS.json`. They prove a minimized actual game
PID109764, Robert alive, spouse34730, unchanged raw53288256, map-ready/paused,
and no current event or pending interaction. Root reports snapshot `native:2`,
public revision3/native revision2 and the unchanged original episode.

Those two small scene receipts do **not** publish the actual `campaign_goal`
or succession expectation. Their at-time fields retain
`checkpoint_save_added=false`, `migration_complete=false` and
`g2_resume_ready=false`. The later Root-owned
`final-owner-fields/NORMAL-SAVE-FIELDS.json` independently records GREEN normal
SAVE014: **h9626**, raw53288256, 104,698,239 bytes, SHA-256
`253823552760e5361d252f5f73861f7cde3e059343853ef7547c87e19828782e`,
original episode/Robert29829 and ordinary `xar_off` lifecycle with environment
`52f0a2f1d548c812a3a87ed262c6f994641925a764c2ec19e887754288436c34`.
Its production save hash is reused; no second save read/hash occurs here.
The save adds0 days and no natural succession or goal/cold proof. This lane
does not read the large whole003/SAVE014 responses, Driver history, CK3 save or
executable.

The already accepted `.4` government owner review is
`managed-full-h9613-entry02/actual-live-review/government.json` under the same
migration root. It qualifies **R0054**'s actual base04 paused query for
Robert29829/date53288256: `feudal_government`, `core_supported/core_landed`,
44 effective features, and true same-frame/core-adapter readiness. Its native
revision2/public3 and exact build are recorded separately. It is an existing
production-live read-only primitive, not a new R0061 government observation,
new family or normal-policy outcome. Reuse that accepted scope and Root's input
ledger; do not repeat the query to refresh this document.

The existing historical same-ruler goal/cold proof remains valid only for its
recorded `.3` build and scope in
[ordinary campaign goal continuity](ordinary-campaign-goal-continuity.md).
There is no observed `.4` natural death or new government-family qualification
in this source package.

## Engine and source chain before policy

The [succession transition tree](succession-transition-v1.md) consumes current
engine heir/title projections. It is an engine-transition observer rather than
a counter to an NPC decision. The exact `.4`
[death-modal migration](death-succession-modal-migration-12004.md) owns the
controller/predicate ABI. Goal policy continues to use the original
[campaign/family input ledger](ordinary-campaign-goal-continuity.md#source-inputs-and-policy-boundary).

```mermaid
flowchart TD
    P[Accepted ordinary checkpoint and real paused current ruler] --> H[Existing hot or cold identity adoption]
    H --> G[Retain goal key, campaign ID and origin ruler]
    G --> F[Normal plan consumes goal with current ruler]
    F --> E[Service freezes current same-frame title-heir expectation]
    E --> N[CK3 naturally changes the played ruler]
    N --> R[First paused successor turn bundle and matched estate reconciliation]
    R --> C[Existing continue-as-reconciled-successor]
    C --> U[Update goal current ruler and reconciled succession count]
    U --> T[Exact current timeline blocker query]
    T -->|already clear| S[Normal successor checkpoint]
    T -->|supported death modal| X[Existing typed Close once]
    X --> V[Independent GUI and predicate clearance plus date proof]
    V --> S
    S --> A[Later normal successor turn consumes same campaign goal]
    A --> K[Normal new-PID cold restore of the successor pair]
    K --> F
    N -. actual .4 natural transition not yet observed .-> Q[Pending M7 natural qualification]
    T -. actual .4 supported modal not yet observed .-> Q
```

Existing source seams, all at the baseline above:

| Seam | Production owner and behavior |
| --- | --- |
| Goal creation/current-frame export | `bridge/native_driver.py:4178` creates only a missing ordinary goal; line4315 exports it. |
| Same-PID restore | `bridge/native_driver.py:10304` restores the persisted goal with the accepted episode and expectation. |
| Physical cold restore | `bridge/native_driver.py:10605` retains the goal; line10613 clears old expectation/reconciliation so the next plan samples the restored frame. |
| Fresh expectation/actual reconciliation | `bridge/service.py:710` prepares the existing transition before both planners; `bridge/native_driver.py:4042` and4096 own the expectation and reconciliation. |
| Normal goal consumption | `bridge/service.py:1035` constructs the goal plan; line1123 publishes `campaign_goal_plan_used` after the normal shared selector consumes it. |
| Natural goal update | `bridge/native_driver.py:20742` invokes `strategy.py:6143` after matched predecessor/successor/title checks. Campaign/origin stay stable, current ruler changes, progress increases by one. |
| Natural timeline/checkpoint owner | `native_auto_run.py:2943` retains the transition, line2981 queries the timeline, line3047 handles the exact modal, line3148 defers a checkpoint for a newly opened player decision, line3163 saves a clean successor. |
| Durable report | `native_auto_run.py:4598` publishes `natural_succession_transitions`; original failures and submitted/unconfirmed Close results remain retained. |

## Current normal-route government consumer seam

One source seam is concrete: `bridge/service.py:957` attaches
`campaign_government_context_used` only in `plan_nonwar_turn`. The fully
authorized normal `plan_turn` already consumes the goal, but does not call the
same government-context leaf. This metadata difference alone is not an
observed gameplay failure or a new blocker. Current Robert's government query
is implemented and already has the narrow `.4` primitive above; the normal
planner retains its existing gameplay decisions and native legality inputs.

When a future actual M7 government policy needs this adapter input, the smallest
reuse seam is immediately after normal `planned` is constructed, before its
opening-focus early return (`bridge/service.py:1271` at this base):

```python
        if campaign_goal_plan is not None:
            planned["plan"]["campaign_government_context_used"] = (
                self._ordinary_government_context_v1(snapshot)
            )
```

This reuses the existing exact-build/current-player/same-frame query and
`ordinary_campaign_government_context_v1.py` consumer. It adds no selection
rule, changes no selected step or priority and creates no new readiness gate.
The existing explicit private-query option controls whether an actual query is
permitted. Missing/current-unavailable identity remains reported in the
existing context. **No shared hook is adopted merely to add this metadata**;
future policy work must identify the useful decision consumer before adopting
and qualifying it. This lane does not mutate Service, build or run a fixture.

## Root execution recipe

The companion [JSON recipe](g2-m7-continuation-12004.recipe.json) uses only
existing registered tools. `ck3_take_snapshot` defaults to omitting the native
transcript, so no new projection helper is required. Reuse an already retained
same-frame goal/plan/government/SAVE result instead of repeating its query.
Each expected revision comes from that actual latest response; public and
native revisions are distinct.

For the current living Robert frame, retain the normal plan's
`campaign_goal_plan_used`, observed goal and current-government result around
the already scheduled normal save. Reuse the original campaign ID, current
actor and progress exactly as returned. When Root next performs an ordinary
new-process restore, compare the restored same-ruler goal/episode and actual
checkpoint source, then consume it on a normal planner turn. Do not substitute
an immutable-seed restart, archive restaging or hand-written goal/history.

If natural `played_character_changed` occurs, the existing `native-auto-run`
owner performs reconciliation, Python episode rebinding, exact timeline
continuation and successor save. A Root MCP loop can follow the equivalent
registered-tool branch in the JSON recipe: consume the planner's existing
matched continuation once, inspect the actual successor blocker, and use the
typed Close only if that query exposes the supported modal. The Close helper
already owns independent predicate/GUI clearance and its date proof. Do not
call Close again after a submitted/unconfirmed result. Already-clear means no
Close is needed. A naturally opened ordinary player decision is consumed by
the next formal turn before a clean successor checkpoint.

The successor's observed current CharacterID and episode come from the
continued result; the original goal key, campaign ID and origin are retained.
After successful successor gameplay and normal save, the existing physical
cold consumer restores that same successor pair and a later normal plan must
consume the same high-level goal. Future government reads use that actual
successor, never Robert's retained government. No forced death, fixed heir,
new seed or new character start is part of this recipe.

Oct7/W41 lane result: source chain and concrete normal-route government hook
identified; existing restore/continuation APIs and report fields located;
current Root small scene/save and government-owner receipts reused once.
**Research / source recipe**,
no new test/build/game/SDK/Steam execution, saved days, natural transitions,
government families or M7 completion. Root owns shared-hook adoption and all
subsequent actual qualification.
