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

## R54: current-core hook live, bounded after publication

R54 used the same exact seed and 634-file current-core product. Both loader
stages were GREEN. The run advanced from `date_raw=53147016` to `53156640`,
then stopped at the former 400-day gate on day 401. Before cleanup it emitted
seven `ZG361P2C` business rows: three real post-publication tuple freezes, two
unauthorized/incomplete publication ignores, one AI silent completion, and
one typed stale-tuple abort. This closes the R51 uncertainty: current canonical
publication hooks are now present and executing in the projected product.

The run did not reach paused `.146`. This does not prove a loader or file-size
failure. It proves that the old 400-day bound covered B1 but did not leave a
separate observation window for the D+2 central pumps after a publication that
can occur at that boundary. The next run keeps the 400-day authored B1 budget
and adds a finite 150-day post-publication observation budget; its wall-clock
timeout is correspondingly raised from 1200 to 1800 seconds.

R54 also recorded 34 runtime reads of unset
`zg361_b2_pip_performance_evidence_status`, all from the top-level PIP evidence
consumer. That consumer had retained six presence/read comparisons in one
same-level `limit`, so the earlier nested lazy-guard repair was incomplete.
The generator now encloses the entire tuple in one `trigger_if` / `trigger_else`
lazy boundary. Normal and `-O` B2 tests are 39/39 GREEN. The refreshed purpose
shard remains within the 1–10 effect target; no `>20` exception exists.

The refreshed 634-file product is tree
`A6C70F0648E7A8142D6E34D2A41AFFD214ED8FE993B4153BF4C93B073194576D`.
Projection and schema-3 closure evidence SHA-256 are
`0A405FD653C1BE44B7D8D7917BE5FBA9DAB190D3DC30BBF87719B3C94CB55F23`
and `40BDBCE78107D42063710A88EB103C0A7D43C6AECC691F6B23EAAD4F2BD02833`;
closure remains 3,706 effects / 988 events / 24 triggers / missing 0, and the
expander proves 630 selected same-path files byte-exact before fixed point.
R54 report/evidence-index SHA-256 are
`A7C59C3E99BA6AD1EDF8293E612FDE3F1D6C37C8E4B13C6FF13216E1F327959B`
and `4F8E907D54721071DD174AE60A8ED299D5AF43F7AF9BF6DBF50A197BE5105E80`.

## R55: B2 lazy fix live and exact flood interrupt

R55 ran from pushed commit `8aff92a` with the refreshed 634-file product. The
frontend-first pass and final loader were GREEN (`303` database nodes,
`fatal=0`); the run then stopped before mutation on vanilla
`ep3_governor_yearly.8120`. The exact frame is `date_raw=53147520`, event
instance 14, played root 29037, one opaque `landed_title` scope named
`disaster_county`, and three shown/enabled authored options at native indices
0, 1 and 2.

The vanilla event's `immediate` has already reduced the selected county's
control and development. Option 1 adds a random stewardship duel and possible
governance/character-modifier result; option 2 spends treasury/gold and adds a
county modifier. Option 3 avoids those promotion-lineage inputs and only adds
minor piety, a deterministic character modifier and trait-dependent stress,
so the exact contract chooses authored option 3.

Most importantly, all three final R55 logs contain zero instances of the R54
`zg361_b2_pip_performance_evidence_status` unset read. This is real same-product
confirmation that the whole-tuple lazy boundary fixed the concrete B2 runtime
error. It does not change the file-size finding: the product loader was GREEN,
so no additional effect split is triggered. R55 report/evidence SHA-256 are
`ED9C501EE6A94BD676E3CFEDEB64D006E2C7F53D939D1357F85F71EF25661FBE`
and `50355C965BE8E8F67C60F4DC835D3653A985FF39B39F7187DFBF36F0E385EAC1`;
native cleanup was GREEN and no CK3 process remained.

## R56: dynamic vanilla Character identities are not a stable contract

R56 ran from pushed commit `cdc3923` and passed frontend-first plus the final
634-file loader (`303` database nodes, `fatal=0`). Before any new mutation it
failed closed on the previously registered `tgp_china_yearly.0005` because
five saved Character IDs differed from the older observed frame. The outer
report and evidence-index SHA-256 values are
`3672107D691C2E215349EF7C3B896E559424591B98EF054E8F6D45C3633CEE05`
and `57604513E3835553F4BC7C6CDBC2EC24E045B7EBE045EE8DF072E817A757E070`;
cleanup was GREEN and CK3 count returned to zero.

The exact 1.19.0.6 source creates or selects the grieving child, both parents,
guardian, and messenger inside the event `immediate`. R46 and R56 therefore
legitimately observed different allocator identities while retaining the same
six canonical role names, Character types, root/date, saved-scope count,
parent-to-mother-or-father relationship, and complete rendered/native option
shape. The corrected contract binds those stable source semantics: every role
must be one unique non-player Character and `parent` must equal either
`orphan_mother` or `orphan_father`. It still selects authored option 3/native
index 2, avoiding the merit mutation in option 2.

Promotion and choreography/preflight tests pass normal and optimized at 10/10
and 6/6 respectively; the no-launch preflight is GREEN. This was another
post-loader contract RED, not a file-size or loader-performance signal, so it
does not authorize another effect-file split.

## R57: bounded recurrence date for the Find Secrets hook offer

R57 ran from pushed commit `34da1c5` and passed frontend-first plus the final
loader. It drained B2 PIP, `tgp_china_yearly.0010`, and the first
`spymaster_task.0381`, then failed closed before action on the second `.0381`
because `date_raw=53152896` was outside the old discrete date set. The frame
retained the fixed councillor/root/target identities, five saved-scope names
and types, and two shown/enabled native options 0/1. Its only new role value
was a valid non-player `character_to_hook=29363`. The `.0005` event did not
occur in this randomized run, so the R56 role-contract correction remains
live pending rather than claimed closed.

R35 observed the same second delivery at `53152656`; the exact 1.19.0.6
Find Secrets event is periodically selected and chooses `character_to_hook`
in `immediate`. The `.0381` contract now admits only the live-observed date
envelope `53148768..53152896`, while retaining its strict maximum of two
occurrences and all semantic identity/option checks. Focused normal and
optimized regressions are both 16/16 GREEN and no-launch preflight is GREEN.

R57 outer report/evidence-index SHA-256 values are
`A8F5A7E5A6F3D9D5D2C5287903A97B0A2D202B1E5987E68986524165656A9A1A`
and `9D57471CB05BEE7523FBB35094C3D28ABD4C89F640C00D609CBE8DF279497401`.
All three final logs still contain zero B2 unset-variable reads; cleanup was
GREEN and CK3 count returned to zero. This remains a post-loader timeline
contract RED and provides no basis for another effect-file size split.

## R58: mandatory vanilla withering-mind event

R58 ran from pushed commit `27536e7` and passed frontend-first plus the final
loader. It drained B2 PIP, the first `.0381`, `.3060`, and `zg361.40`, then
stopped before unknown action on vanilla `health.7200`. The second `.0381` did
not occur before this stop, so the R57 upper date bound remains live pending.

The exact frame was `date_raw=53152296`, instance 17, played root 29037, no
saved scopes, and one shown/enabled native option 0 whose native indicator adds
`withering_mind`. In the exact 1.19.0.6 `health_events.txt` source this event is
selected by `yearly_health_pulse` and exposes only that option; its sole
scripted effect adds the trait. There is therefore no lower-impact alternative
to choose. The new contract acknowledges authored option 1/native index 0 only
after the entire observed single-option frame matches.

Focused normal and optimized regression passes are both 16/16 GREEN, and the
no-launch preflight is GREEN. R58 outer report and
evidence-index SHA-256 values are
`FBED343DD372D173409E07A0E29C560E099DDB50F127769E6BB337E1C469795E`
and `B5D39ADBFD4556D9F2EF8EE810ED47DD0D2620A517853CEA60035342F86981D7`.
All final logs retain zero B2 unset-variable reads, cleanup was GREEN, and CK3
returned to zero. This random post-loader health interrupt is not evidence of
file-size or loader-performance failure and does not trigger another split.

## R59: the 550-day window contains two annual Jingcha mandates

R59 ran from pushed commit `3dcf75c`, passed both loaders, and drained PIP,
`.0630`, `.0002`, the first `zg361.40`, and `zg361b1.200`. It then stopped
before action when a second `zg361.40` exceeded the default one-occurrence
guard. The random `health.7200` event did not recur, so its new contract is
still live pending.

The two product event frames are at `date_raw=53150880` and `53159640`, exactly
8,760 hours (365 days) apart. Both have played root 29037, zero saved scopes,
and two shown/enabled native options 0/1. The loaded product source routes
`zg361_jingcha_annual_dispatch_effect` from the yearly playable pulse; after
the first option-1 commitment reaches its 300-day cleanup boundary, the next
annual mandate can legally be issued. The exact contract now admits only those
two ticks and caps this key at two occurrences. Its option and frame checks
remain unchanged. Focused normal and optimized regressions are both 16/16
GREEN, and the no-launch preflight is GREEN.

R59 also emitted 29 real `ZG361P2C` business rows: 11 post-publication tuple
freezes, eight AI silent completions, eight stale typed REDs, and two
unauthorized/incomplete ignores. No `.146` appeared before the second annual
modal. After this bounded event is drained, a 550-day exhaustion must be
analyzed from those business traces rather than answered by another blind
timeout extension.

The outer report/evidence-index SHA-256 values are
`9656A3A14469D14540FE8AFE1927D14A1088BD963DF931AAA213B2F9C74DAC90`
and `1C20F900BC509977079F344A35E3022B68B183006DBCFAE176D5642B7DFACE0C`.
All final logs contain zero B2 unset-variable reads, cleanup was GREEN, and
CK3 count returned to zero. This is a post-loader annual-event bound, not a
file-size/performance RED, and it does not trigger another effect split.

## R60: manager identity is dynamic in the player self-review ticket

R60 ran from pushed commit `8607e9a`, passed both loaders, and drained PIP,
`.3060`, `.0399`, and the first `.0381`. It then failed closed before action
on `zg361b1.200` because the old first-frame identity contract did not match.
Neither the second annual Jingcha nor the random health event occurred, so
those newer contracts remain live pending.

The R60 frame is `date_raw=53156256`, instance 17, played root and self-ticket
subject 29037, ticket/self-ticket owner 29348, six opaque value ticket scopes,
and nine saved scopes total. The older frame was at `53152728` with manager
29628 and additionally retained the acceptance-only
`zga_phase2_seed_player`, for ten scopes total. The generated product source
shows that each manager-rooted peer window sends this event to a human subject;
the stable semantics are therefore equal non-player owner roles and a player
self-ticket subject. The fixture seed scope is not part of the authored ticket.

The corrected contract binds the live date envelope, exact alternative 9/10
name sets, the owner alias, player subject, six value types, and the optional
fixture scope's identity. It still selects honest option 1, avoiding the other
branches' +15/-15 self-score bias. A negative unit case proves that an
arbitrary tenth scope is rejected. Focused normal and optimized regression
passes are both 17/17 GREEN, and the no-launch preflight is GREEN.

R60 emitted eight `ZG361P2C` business rows: three freezes, two AI silent
completions, two stale typed REDs, and one ignored hook. Its outer
report/evidence-index SHA-256 values are
`FC080F49D965782C5F5E9EAF2E3A5384D6CE083B172A9B01E1AC3FF00BE155CD`
and `C8991B49FBACEE57378664331FF0021461998AC70C6BBE99E24751C3F3D95888`.
B2 unset reads remain zero, cleanup was GREEN, and CK3 returned to zero. This
is a post-loader semantic-contract correction, not a file-size signal.

## R61: stale variable-list Character scopes fail before delayed review

R61 ran from pushed commit `04c9d1b`. Frontend was reached in 121.156 seconds,
the final loader remained GREEN, and the managed process was cleaned up. The
entry then failed closed before action on `spymaster_task.0342`: the new frame
was at `date_raw=53157024`, instance 19, root 29037, the same seven typed saved
scopes, and the same sole shown/enabled native option 0 as the older frame at
`53152896`. Exact 1.19.0.6 source exposes only that option and reveals the
already-bound secret to root. The contract therefore admits only the observed
date envelope `53152896..53157024`; root, scope names/types/identities, and
option shape remain exact.

Independently, the R61 final error log contains 119 real product errors of the
form `This scope doesn't support variables`. The manager-owned
`zg361_b1_subjects` list was populated with live Character objects at cycle
open. By the D+180 `.100` consumer, some unlanded entries had been removed from
the live character database while their list references still rendered a name
and internal ID as `weak`. Reading `has_variable` on those stale scopes failed,
and the same objects propagated into later `.101/.102/.103` consumers. This is
a production runtime/capability RED, not a hypothetical consistency issue.

The minimal correction rebuilds the list immediately before the first delayed
consumer. Its iterator has a dedicated `limit = { exists = this }` boundary;
only surviving scopes are copied, and all business-variable reads occur after
the original list is rebuilt. Removed rows increment the existing review
vacancy, roster amendment/audit, and reopen receipts rather than silently
changing a denominator. Vanilla 1.19.0.6 uses the same object-existence filter
for retained list members in `common/on_action/dlc/mpo/mpo_on_actions_2.txt`.
The correction is static-ready and still needs R62 live closure; these errors
may disrupt promotion progress, but R61 alone does not prove they are the sole
cause of the absent `.146`.

B1 generator tests pass normal and optimized at 58/58, promotion tests at
11/11, and checkpoint choreography/preflight/runner tests at 15/15. The effect
boundary audit remains GREEN at 427 files / 3,720 definitions, no target misses,
maximum non-legacy size 10, and no `>20` violations. The legacy B1 first half
grew from 41 to 42 definitions solely for this repair; no B2+ purpose shard was
expanded. The refreshed R62 product has 634 files, tree
`C3DD2D6E1C59578689EDD69F02F405258872528552866CA5310F18CBF1866D59`,
and a 3,707-effect / 988-event / 24-trigger fixed point with zero missing
providers. Projection and closure evidence SHA-256 values are
`7F2526A2D7B3C860A756EA02CB03510F9D13CF72376BE70E767D34AD149AA323`
and `B075218A96CB48403985733EFD5C31AD34921F4589E6BAF1EC0CB63538096C23`;
the no-launch preflight is GREEN.

R61 outer report/evidence-index SHA-256 values are
`86C9BF011281DC96C294A4450A418350E5DB7B860B65E46B02EB069A477558BA`
and `E994B71BF8FA2854CA022DFA8AFD37443D65E9D77DEF7FE1EFD07A74387296B0`.
The 1,087.466-second run emitted four central tuple freezes, one AI silent
completion, one typed stale RED, and three ignored hooks; neither `.146` nor
`.147` appeared. Its self-review event was the older owner/date shape, so the
R60 dynamic-manager correction also remains live pending. Loader performance
was GREEN throughout, providing no evidence for another size-driven split.
