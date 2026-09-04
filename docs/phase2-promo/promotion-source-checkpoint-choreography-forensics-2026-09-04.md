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

R9 supplied that missing detail. On the same 630-file product, all five fixed
entries reported unavailable and the top-level promotion bridge itself was not
instantiated. The exact reason was `widget_not_instantiated`; the unavailable
list began with `zg361_promotion_source_bridge_window` and included all four
descendants. The outer report SHA-256 is
`F75F80155BC44CC898916C462C774DE7903BB47298F81EDDD2AEBBF7096A2F78`,
the evidence index SHA-256 is
`ABCD0F1BC10715C4D7D95D2F38088A5D6F8355429BA617E1227C2B8D33AD1A63`,
and cleanup SHA-256 is
`B448DD394AAB733974628E5058CC71D279940FFB96F22CB233C21F11731407D7`.

Because an absent root cannot distinguish a promotion-only registration fault
from a broader custom-window lookup mismatch, the next native candidate adds a
read-only comparison probe for the fixed scoreboard, decision-bridge and
mechanism-bridge top-level names. It changes only typed-unavailability detail;
it neither executes an action nor weakens readiness. The compensation-ON MSVC
build passed 94/94 CTest; its DLL and injector SHA-256 values are
`3CC51415C225792A0D09E8B937A207D588BFD471C79220A301AF8C7DE553D9D6` and
`8AA17A085D9D83A195D1122CED667CC1806ACA62B826E437768DBAB7B451A97D`.

## 23:22 live R10/R11 evidence update

R10 did not reach a product query. Its frontend-first warm-up hit a transient
Windows `WinError 5` while atomically replacing
`frontend-first-warmup.json`; the managed session stopped before the final
injected save-load process existed. R11 repeated the same frozen product,
seed, binary and choreography in a fresh state directory. The write completed,
the warm-up reached the exact Frontend marker in 122.181 seconds, its PID was
proven gone, and the final injected process reached a stable paused map. The
R10 error therefore remains a one-off harness/file-handle RED and is not used
as product or loader evidence.

R11 returned
`widget_not_instantiated:top_level_probe=none`. The fixed lookup failed not
only for the promotion bridge but also for the registered scoreboard,
decision-bridge and mechanism-bridge roots. Later exact-build disassembly
proved that this function searches only the GUI owner's root direct children;
R11 therefore rules out those names on that direct-child surface, not global
instantiation. Loading a custom `.gui` asset and registering it through
`scripted_widgets` still does not prove that this particular lookup can find
the resulting instance. Moving the promotion root to `{ 0 0 }` remains
unsupported by the evidence.

The R11 loader gate remained GREEN with 303 database callbacks. The scripted
effect database took 617 ms init / 779 ms inclusive, and cleanup was GREEN.
Its outer report, evidence index and cleanup SHA-256 values are
`DEBD2AEBA1D80E5ED167493B7A1718E772EA55B76629F4FF8164BF3007233F03`,
`17BF4208C83A52372ECB4428F2A77F550A8F7E913F48C5A2118A01FA96C4E65D`
and `5D858C334B338F4D0133AB7619AB5170E589A46723B7A113B7F3ABA5C166C9C9`.
No action was submitted. This is still provider/ABI RED, not a
loader-performance or file-boundary RED, so it does not trigger another
effect split.

## Direct-child ABI and recursive promotion fallback

Exact-build disassembly of `0x36D0B20..0x36D0CA8` (392 bytes, SHA-256
`AA460EB52819C0D02F64293EE7F3793DD8D3B0CB010A3347011CE04AECA4B83F`)
closed the lookup boundary. The function reads the GUI root from
`owner+0xD0`, then iterates only its direct-child vector at `+0xF0/+0xFC` and
compares exact names. It is not a general tree traversal.

R12 added native-name controls and returned
`widget_not_instantiated:custom_top_level_probe=none:native_top_level_probe=none`.
Its report/evidence/cleanup SHA-256 values are `F394343F…DF37`,
`9084615D…87A`, and `5FFDCCCA…CD0`. The next promotion-only build retained the
direct lookup, validated any returned name, and on a miss performed a bounded
fixed-name descendant search from `owner+0xD0`. The traversal remains capped
at depth 64, 4096 total widgets and 4096 children per node; callers cannot
supply a name. Native CTest was 94/94 GREEN and the candidate DLL SHA-256 is
`D512F330CE81DEF122EFAB61CF70F8E24EA82B36AB0F1EA15713C7C33B88F80E`.

R13 and R14 both crossed the initial progress/provider query with that DLL.
R13 then exposed an idempotent `resume-map/already_running` ACK that the
choreography had incorrectly rejected; R14 accepted it and reached the exact
product event `zg361b2.40`. Their report/evidence/cleanup hashes are
`55FC1E33…EB73` / `8AEA8223…F41A` / `54D28EB5…DF40` and
`53602294…A9B` / `BA8518E5…7780` / `2B8DCE28…2882`. These runs prove the
private discovery branch was exercised in live control flow, but neither
froze a standalone complete progress payload and the overall product loop was
RED. Public capability and scoreboard state remain unpromoted.

## 2026-09-05 timeline continuation

R15 bound and selected `zg361b2.40` option 1, then observed the independent
vanilla yearly event `ep3_governor_yearly.8060` at `date_raw=53147520` and
stopped before acting. The exact event has four enabled non-fallback options.
Source review selected option 4 as the least-mutating path: it performs no
gold, governance, modifier, duel or follow-up-event mutation, while retaining
the vanilla trait-conditioned stress impact. R15 report/evidence/cleanup
SHA-256 values are `55525CB8…A7A0`, `10DDA15F…08FB`, and
`9F4E72A4…E51A`; loader was GREEN at 65.696 seconds / 303 callbacks.

R16 repeated the earlier real Windows sharing failure while atomically
replacing `frontend-first-warmup.json`. Since this was the second occurrence,
the native-session supervisor now retries only WinError 5/32 for at most two
seconds; other permission failures remain immediate and the final operation is
still the same atomic replace. Focused native-session tests are 21/21 GREEN in
normal and `-O` modes.

R17 crossed that frontend write, loaded GREEN at 65.457 seconds / 303
callbacks and again selected the exact PIP option 1. Its random yearly path did
not show the governor event; it instead reached the separately reviewed
`spymaster_task.0381` at `date_raw=53148768` and stopped before acting. The
new contract selects option 2 only after binding the exact event, player,
councillor/liege/target, boolean scope, a unique third-party
`character_to_hook`, and the full two-option shape. It is not a namespace
allowlist. R18 is the next live verification; until it reaches `.147` and a
native save, source readiness remains RED and footage remains 0/8.

## R23–R36: exact timeline growth and stale saved-Character boundary

R23–R30 preserved every fail-closed stop and then added source-reviewed,
exact-key contracts for the observed succession, Jingcha, self-review, China
yearly, governor-yearly and learned-eunuch events. Each contract binds the
played root, complete typed saved-scope shape and the rendered-to-native option
mapping before selecting one fixed branch. No namespace wildcard was added,
and the incomplete GUI effect-indicator surface was not used as proof that a
branch is a no-op.

R31 and R33 then repeatedly observed active event instance `14` at
`date_raw=53147256`, but the query returned `event_saved_scope_invalid`.
R33's 20 bounded retries retained the same native frame and revision, so this
was not an inventory-construction race. At the same frame CK3 logged an effect
against a dead scope character from `intrigue_dread.1501:after`. The practical
failure was therefore narrower than a corrupt event window: the event key and
materialized options still had decision value, but one named type-4 token no
longer generation-resolved.

The production reader and serializer now retain the strict root rule while
allowing only a named saved Character to preserve its canonical name,
`raw_type_index`, subtype and `type_key=character` with
`typed_identity={status:unavailable,
reason:character_scope_identity_unavailable}`. No CharacterID is published or
guessed. Invalid names, types, vectors, root identity or double-observation
still invalidate the whole frame. The fresh `Z:\b3probe-msvc4` MSVC build
passed 94/94 CTest; its DLL SHA-256 is
`6E5BB70B5ADFE38245DED493BE7BDD451D51EFAFE25E9A8688D0F4F4B222984F`.
R34–R36 loaded GREEN and ordinary root/saved-scope queries remained available,
but the random path has not yet reproduced the exact stale-character frame, so
the specific live closure remains pending.

R34 and R36 also showed `ep3_governor_yearly.3060` with identical exact
characters, scope types and visible native option indices but adjacent dates
`53148048` and `53148072`; earlier runs supplied later values through
`53152368`. This establishes a day-tick window rather than a finite timestamp
enumeration. Only that exact key now accepts the bounded
`53148048..53152368` interval. R35 separately observed
`spymaster_task.0381` twice, at `53148768` and `53152656`, with the same fixed
actors/boolean scope/option shape and a different valid non-player
`character_to_hook`. The general one-occurrence guard remains; only this exact
event is capped at two evidence-backed occurrences.

Every valid loader gate in R23–R36 remained GREEN with 303 database nodes and
no fatal loader signature. These REDs occurred after load in event observation
or an over-strict timeline contract, so they provide additional evidence
against file size as the current cause and do not trigger another effect-file
split. The `.147` source, the four-entry registry, all eight footage spans and
both final videos remain incomplete.

## R37–R46: stale saved Character live closure and native option numbering

- R37/R38/R39 stopped on `tgp_china_yearly.0020`,
  `ep3_emperor_yearly.2200`, and `bp1_yearly.9007`. Each now has an exact
  1.19.0.6 key/date/root/saved-scope/rendered-native-option contract and a
  fixed source-reviewed bounded branch.
- R40 reached `ep3_interactions_events.0630` with three generic interaction
  Character scopes whose tokens were stale while their names and types were
  still valid. The native DLL correctly emitted
  `character_scope_identity_unavailable`; the Python normalizer rejected that
  new valid shape. The minimal downstream fix admits that exact object only
  for named saved Characters and keeps the root strict. R41 then normalized
  the same live event and reached the unknown-key policy gate, closing the
  native-to-Python live path.
- R41/R42 observed `.0630` at `53147256` and `53151600` with identical
  contractual semantic fields. Its asynchronous delivery date is bounded to
  that evidence-backed interval; no scope or option field was relaxed.
- R43 proved that the public selection number is `native_option_index + 1`,
  not the rendered ordinal. The old entry submitted public option 3 at
  `.3060` and therefore selected native index 2 once in the disposable
  userdir. Protected storage remained unchanged. `.3060`, `.8100`, and
  `.9007` are corrected, and a mapping invariant now prevents fake receipts
  from masking the same error.
- R44/R45/R46 stopped on `.2240`, `.0002`, and `.0005`; their new contracts
  use the scholar opt-out, the minimal new-governorship acknowledgement, and
  the grieving-child branch that avoids extra merit respectively. Promotion
  `.146/.147` remains unreached, so the source registry is not frozen.
- All valid R37-R46 loader gates completed 303 database nodes with fatal 0.
  R39-R46 frontend-first times were approximately
  `157/169/151/157/163/164/159/159 s`. There is no file-size/load-time RED,
  so this evidence does not authorize another effect-file split.

## R47–R52: stale purpose shard masked a current-core call

R47 through R50 added exact source-reviewed contracts for `.0010`, `.0342`,
`.8100`, and `.0346`. R51 then exhausted the 400-day gate after real B1 review
publications but produced no `ZG361P2C` trace at all. This was not evidence for
a longer business timeout: the current canonical
`zg361_apply_pending_grades_effect` calls
`zg361_p2c_on_review_published_effect`, while the loaded 630-file projection
contained the older frozen-B2 definition of the same effect without that call.
Name-only fixed-point closure saw an existing provider and could not detect the
body drift.

The B3 projection expander now regenerates the four existing purpose-grouped
core shards from the current canonical monolith before resolving dependencies.
Their 26 definitions are distributed `3/6/8/9` (maximum 9), and every emitted
block must equal the canonical block. The refreshed product adds four newly
reachable dependencies and is 634 files, tree SHA-256
`6AB2B8E159ABEADAEE88AB44698FF859263906F3E807990436FB6DD6F1FB7824`;
its closure is 3,706 effects, 988 events, 24 triggers, with no missing calls.
Projection and closure-evidence SHA-256 values are
`D99A74E9288D9C6D7655E7B54024047BF229B194D2F07E991FCAA31F1D4006B1`
and `69D7CD0AB51EA0257D4225C60BD027C741E2F6812C9BA3969FC60EF06352150C`.

This is concrete file-boundary evidence: a split product needs semantic body
synchronization, not merely name closure. It is not a file-size performance
finding. R50's one approximately 202-second frontend pass was followed by
approximately 159 seconds in R51 and 142 seconds in R52; all three loaders were
GREEN, so no additional size split is justified.

R52 crossed the refreshed loader and stopped before acting on the new vanilla
event `ep3_governor_yearly.8010`. Its exact governor/title/flag/saved-scope and
three-option contract now selects authored option 3 after source review. The
R51 and R52 report SHA-256 values are
`718F9444063EB14F46D86627EBC5AEA43B4419E01EDD4F09C988AB6DA07A5C96`
and `ECD2DFA8A7870096D370663F12A7FD220A1C029FF365B1B418E2F8C7A1450F9A`.
Promotion `.146/.147`, the four-entry registry, footage, and final videos remain
pending.

## R53: exact sway outcome interrupt

R53 ran from pushed commit `8c3a649` and crossed both frontend-first and the
final 634-file product loader. It stopped before mutation on
`sway_outcome.2001` at `date_raw=53153952`, event instance 19. The live frame
contained played root/owner 29037, target 27051, opaque scheme and artifact
scopes, four saved scopes total, and one shown/enabled native option 0.

The 1.19.0.6 source gives this event only that acknowledgement: target loses
10 opinion of owner and the already failed sway scheme ends. The new contract
therefore accepts authored option 1 only after the entire observed frame
matches. Focused normal and optimized test runs are both 14/14 GREEN. The
outer report and evidence-index SHA-256 values are
`70EA021201EF013A8548BF2C0DE786221CA5E3E3B1941A8403C013B363F0BEB0`
and `CDCE31833582F7A042B6CA9E25F30D32FAA175C87EDF8E632C91E0029524AEAC`.
Cleanup was GREEN. The run stopped before review publication, so it does not
yet provide live evidence for the restored current-core P2C hook.
