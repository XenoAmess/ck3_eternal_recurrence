# Promotion source checkpoint production choreography forensics (2026-09-04)

## Outcome

At canonical `1341251dd028b68adf5a4adeb497c94acf3a9471`, the repository proves a short, executable product-only suffix from a real paused `zg361pp.146` card to the required paused `zg361pp.147` option-1 source. It does **not** yet prove an end-to-end executable path from the current Phase2 seed to that `.146` card.

The honest readiness is therefore `static-ready-live-pending`. The source capture must not start until the missing product entry action and player-owned prefix observations are available, or until a separate real product-only run supplies a qualified `.146` checkpoint.

The machine-readable companion is `tools/zg361_phase2_promotion_source_choreography_contract.json`; `tools/test_zg361_phase2_promotion_source_choreography.py` pins it to the current event/effect graph without launching CK3.

## What the current seed proves—and does not prove

The canonical seed contract freezes a 53,517,622-byte save with SHA-256 `bfc73fd9e7e80145cdf39aabc66bc2d731881122adab0cc0ba675fa07d1e6733`, `date_raw=53146920`, and played CharacterID `29037` (`han_6875`). Its live report shows that the bootstrap card `zga_phase2_seed.1` was closed before the save was materialized; the saved checkpoint is intended to be an event-free paused map even though the earlier snapshot and event-context artifacts necessarily show the pre-close fixture event.

The one `ZG361B1: performance season opened` log came from acceptance-only `zga_phase2_seed.101`. That fixture explicitly runs on the player's real **AI liege** and calls the shipped `zg361_b1_open_cycle_effect` there. It does not open a player-owned B1 cycle. Advancing that AI-owned cycle cannot yield the target visible source: `zg361_pp_dispatch_t_stage_01_effect` resolves mechanisms 146–148 silently when the case owner is AI, and schedules `zg361pp.146` only when the owner is human.

No current seed provider supplies the played character's celestial-liege eligibility, direct reviewable-vassal roster, decision validity/cost, or player-owned B1/central/PP stage. A title-history fact such as `han_6875` holding `k_hedong` is not a same-frame proof of the runtime government trigger or roster. Binary save string presence/absence is likewise diagnostic, not a typed native observation.

## Shortest legal fresh-product prefix

The committed product graph is:

1. Restore the frozen seed into a managed product-only session and independently verify paused/map-ready, player `29037`, date, save bytes, hash, and lineage.
2. Observe that the played character satisfies `zg361_is_celestial_liege_trigger`, has at least one direct `zg361_is_reviewable_vassal_trigger` vassal, has 150 prestige, is not already reviewing, and has not settled this year.
3. Activate the real `zg361_review_now_decision`. Its effect adds only `zg361_review_now_pending`; registered `zg361_review_now_bridge_gui` removes that flag and calls `zg361_b1_open_cycle_effect` on the same human player.
4. Observe the player-owned B1 tuple, then advance its real tickets: `.100` at D+180, `.101` at D+240, `.102` at D+300, and the D+330 quota path. Resolve only exact visible product events. Common-superior bank synchronization and calibration can extend this path, so D+330 is a graph landmark, not a promised source ETA.
5. On publication, `zg361_publish_scoreboard_effect` closes the review and calls `zg361_p2c_on_review_published_effect`. That hook freezes an eligible delivered result and starts the central serial pump at stage 1 with D+2 tickets.
6. Let stage 1 (career/HC) and stage 2 (compensation) reach success or a typed N/A/terminal condition. The pump cannot dispatch stage 3 early: `zg361_p2c_record_stage_effect` increments exactly one stage and schedules the next D+2 pump.
7. Stage 3 calls `zg361_p2c_call_pp_adapter_effect`. The PP adapter selects the frozen subject and `zg361_pp_open_t_case_effect` initializes the first T case. For a human owner it schedules `zg361pp.146` at D+1.

This is the shortest identified *legal product graph*, but not currently an executable headless runner plan. The Phase2 bridge exposes event-option selection, timeline controls, current-event query, and save-checkpoint; it exposes no exact stable-identity action for `zg361_review_now_decision`. The named scoreboard action cannot substitute: its allowlist only opens, switches tabs, closes, or reopens `zg361_scoreboard_modal`.

## Executable `.146 → .147` suffix

Once a real product-only paused `.146` source exists with the played character as root/owner:

1. Query the exact event window and bind root plus saved owner/subject/cycle/case/state/mechanism to the active instance and revision.
2. Select `.146` option 1 through `select-event-option-N`. A freshly opened T case begins with operation capacity 11 and capacity-hours 10; route A needs one of each, consumes m146, and all three `.146` branches schedule `.147` only after observing `zg361_pp_m146_consumed=1`. Route A is the canonical no-policy-debt choice. Option 3 is a resource-independent legal fallback, but deliberately records 90-day policy debt and is not the preferred capture route.
3. Advance at least one game day using the bounded timeline controls (`set-speed-1` + `resume-map`, or the existing `life-advance` step), then pause when the event materializes.
4. Independently query `zg361pp.147`. Require a played-character root, the six saved scopes (`owner`, `subject`, `cycle`, `case`, `state`, `mechanism`), exactly three options, and option 1 shown/enabled.
5. Do **not** select `.147` option 1. While that source remains visible, invoke `save-checkpoint`, archive the native bytes, and bind byte length/SHA-256/date/seed lineage/capture lineage to the provider and UI receipts.

The subsequent promotion action cell owns `.147` option 1 and waits for real `zg361comp.1` plus the native promotion/compensation postcondition. Source capture must stop before that action.

## Why ACK is never sufficient

`select-event-option-N` ACK proves that one revision-bound command was submitted to one event instance. It does not prove that the m146 manager guard passed, that its receipt was consumed, that the delayed `.147` ticket was scheduled, that a day advanced, that `.147` materialized, that the saved scopes still name the same owner/subject/cycle/case, or that option 1 is actually shown and enabled. Those facts require the independent current-event query on the paused `.147` frame and a native save receipt.

Likewise, the later `.147` option ACK does not prove promotion or compensation. The formal cell correctly waits for `zg361comp.1` and joins it to the read-only provider's same-case promotion choice and posted compensation receipt.

## Remaining construction entries

- Add or authorize an exact-build, stable-identity product decision action for `zg361_review_now_decision`; do not use coordinates, OCR, console, or an acceptance fixture.
- Add/read a player-owned B1/central/PP progress observer sufficient to distinguish unopened, advancing, stalled, `.146` queued, and `.147` visible states. This also determines whether the seed contains any legitimate shortcut.
- In the next live run, verify player `29037` satisfies the celestial-liege and direct-vassal preconditions before spending the decision cost.
- Preserve the entire product-only source lineage. The bootstrap fixture may explain the seed's origin, but it must not be mounted or invoked in the source-capture runtime.
- Treat elapsed time beyond the proven delayed edges as unknown until the player-owned B1 and stages 1–2 are observed live; do not hard-code D+330 as the `.147` date.

No CK3 process was started for this forensic package, and no shared runner code was modified.

## 22:53 live R8 evidence update

The first compensation-ON run from the refreshed 630-file seed reached a stable
paused map and passed the loader gate, but the first fixed promotion-progress
query returned typed-unavailable. The run therefore ended before review-now or
any event option was submitted. Its retained artifacts are `Z:\b3r8` and
`Z:\b3r8_native_state`; the outer report SHA-256 is
`F7ED52BEA4C314F4520B638172FA16DDEA6AF3D484484CF46C94F133C70CC29F`,
the evidence index SHA-256 is
`0A15C6039ED6D5901C66C72C20728B3EF7A9F58C8A9720CDCCB218C9DCB4D067`,
and cleanup SHA-256 is
`41707CB5433551F98EC14E309E711D9121B35C45840922EDA0AD8D2CBA1B0284`.

This is a provider/runtime RED, not a loader or file-boundary RED. CK3 loaded
`gui/zg361_promotion_source_bridge.gui`, completed 303 database callbacks, and
the loader gate was GREEN in 68.947 seconds. The scripted-effect database took
596 ms init / 764 ms inclusive, consistent with prior GREEN runs. No missing
effect/event/trigger/GUI loader signature was found. The existing purpose shard
policy therefore remains in force without an additional size-driven split.

The production entry now preserves the native `unavailable_reason` and the
names of widgets whose `exists` field is not positively available in the fatal
report. This diagnostic is covered in both normal and `-O` focused tests and
does not relax the fail-closed gate. The next serial attempt is diagnostic: it
must identify the exact missing runtime widget before any product/provider fix
is selected.
