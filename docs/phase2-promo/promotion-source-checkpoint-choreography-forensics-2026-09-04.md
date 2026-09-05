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

## R62: `exists = this` is true for the failing weak Character scope

R62 ran from pushed commit `eb667da` and the 634-file product tree
`C3DD2D6E1C59578689EDD69F02F405258872528552866CA5310F18CBF1866D59`.
Frontend took 131.735 seconds and the final loader remained GREEN. The run then
failed closed before action on `spymaster_task.0346` at `date_raw=53152920`.
The older frame was one day earlier at `53152896`; root 29037, all eight saved
scopes including lover 45267, and the sole shown/enabled native option 0 were
otherwise exact. The contract now binds only that observed date envelope.

More importantly, R62 directly falsified the first pruning predicate. The
`.100` event invoked the new prune effect, but two weak Character rows still
reached `zg361_b1_midcycle_dispatcher_effect`; the final log contains four
`This scope doesn't support variables` errors and no prune marker. Therefore
`exists = this` remains true for a weak Character that retains display
identity, even though that scope cannot host variables. Because R62 stopped
earlier than R61, four versus 119 is not a valid total-error performance
comparison; the same-call-stack recurrence after the filter is the evidence.

The R63 correction changes the dedicated iterator predicate to
`is_alive = yes`, then performs the same scratch-list rebuild before any
variable read. Exact vanilla 1.19.0.6 source documents and uses this rule for
dead people that enter a retained list at
`common/scripted_effects/06_dlc_ce1_epidemics_effects.txt:867-874`.
Vacancy/amendment/audit receipts remain unchanged. Normal and optimized B1,
promotion, and checkpoint suites pass at 58/58, 11/11, and 15/15 respectively;
the effect boundary remains 427 files / 3,720 definitions, maximum non-legacy
10, and no `>20` violation. The change remains live pending until R63.

The frozen R63 product at `Z:\p2w\p` has 634 files, tree
`B0CF1632AFA61E508C1F469E8346954ADB8B768E1BF961500F220FE897F2CB81`,
and a 3,707-effect / 988-event / 24-trigger fixed point with no missing
provider. Projection and closure SHA-256 values are
`577876F01EEA6E0FD9633F8C866D3E3433D2CB98EC694EE85324D66AA5176312`
and `601D8D1670E6E74A7B6E896AD8E7CB5E2EE25F5688819DA0C60C081D97BA827F`.
The complete Zhongguo static validator and R63 no-launch preflight are GREEN.

R62 outer report/evidence-index SHA-256 values are
`986E2AC2CDE5153CC26DA82D2093C71E0BC1FD3EA66607BB516F0B66E2399E38`
and `4B102D0ACB3C362AE78FC8EAE007763E2D988C45D3354E3EDB0916AD7177231B`.
Duration was 756.753 seconds; cleanup was GREEN and CK3 returned to zero. No
P2C, `.146`, or `.147` trace appeared before the stop. This remains a product
runtime correctness RED after a healthy loader and does not authorize another
file-size split.

## R63: one-option foreign-affairs success letter

R63 ran from pushed commit `af9502d` and the unchanged 634-file R63 product.
Frontend took 120.172 seconds and the final loader was GREEN. Before D+180 it
failed closed without action on the previously unregistered vanilla event
`chancellor_task.1104`. The exact frame was `date_raw=53149872`, instance 15,
played root 29037, five Character scopes, and one shown/enabled native option 0.

Exact 1.19.0.6 source at `chancellor_task_events.txt:765-783` shows that `.1103`
has already chosen a neighboring ruler. The `.1104` letter exposes only one
option, which adds a bounded positive opinion of root to that neighbor. The
new contract binds `councillor_liege` to root, requires
`councillor=chancellor=active_councillor`, requires all dynamic roles to be
non-player, and requires neighbor to differ from the three chancellor aliases.
It does not freeze allocator IDs and selects authored option 1/native index 0.
A negative test rejects a collapsed neighbor/chancellor identity; promotion
tests pass normal and optimized at 12/12 and checkpoint tests at 15/15.

R63 recorded zero weak-scope errors, but it stopped before `.100`/D+180 and
emitted no prune marker. The `is_alive` correction therefore remains live
pending. Outer report/evidence-index SHA-256 values are
`8D5520CEE1E85D9F3290630CC8D7C05DD54CF076CA1E0FBCCA877C97BD7EB5D5`
and `5EC3218F1FE6384ADA372FA8AFCDF12F4CD320CDB5ED57C32F3803F1687E0DBD`;
duration was 482.618 seconds, cleanup was GREEN, and CK3 returned to zero. This
was another post-loader vanilla interruption and is not a file-size signal.

## 2026-09-05 10:31: source-semantic dates and preserved failure timelines

R57 `.0381`, R61 `.0342` and R62 `.0346` failed on delivery-date drift, not on
changed authored choices. Exact 1.19.0.6 `00_spymaster_tasks.txt:350-355,381-457,674-707`
uses progress, `restart_on_finish=yes` and random discovery;
`councillor_on_actions.txt:516-532` dispatches task outcomes and first-valid
secret types. `spymaster_task_events.txt:143-174,208-210,336-371` freezes the
secret before dispatch. `.0342:583-594` and `.0346:1028-1073` reveal that scoped
secret; `.0381:1746-1854` freezes a hook target and our second option adds its
opinion. These effects contain no calendar eligibility or cost branch. Opinion
duration still begins on the actual click date; time does affect world state.

Only these three encountered keys now bind their dates to the existing run's
`starting_date_raw .. starting_date_raw + 550*24` window. The 550 days remain a
harness bound, not a claimed vanilla task period. Per-run copied contracts
leave historical observed dates untouched; role/type/option and occurrence
checks remain unchanged. Source SHA-256 values, in the order above:

- `EBE10909D2618AE9B6360C738397F6304C6D61FA597DBA16232772C05B4E0613`
- `5629D03928014BAFDAB3E42576D20BBE13F2A76F0BECC0219B729515010EA95E`
- `2D7F0237D9888812A55C14B7A8A3BBA551FF64D8AE72AE28088456AF93FCFF57`

R59/R61 also exposed an actual diagnostic loss: a raised entry exception lost
the accumulated local observations and before/after GUI query results because
the runner wrote them only after a successful return. An optional mutable
`evidence_out` now retains them; the runner writes the existing
`03_promotion_source_production_entry.json` in `finally`, retaining RED and its
error. It does not treat an ACK as state evidence. The focused suite passed
31 tests; the subsequently extended runner suite passed 5, including persisted
failure observations and no downstream capture after failure. This is
static-ready; R65b was already running the previous imported code.

Two important corrections to earlier interpretation: vanilla
`ep3_interactions_events.0630` is not a harmless post-resolution notice. Its
only option executes `governor_resignation_title_transfer_effect`
(`ep3_interactions_events.txt:4577-4583`); R59 then saw the player's new-holder
`.0002` event. Also `eligible AI central portfolio completed silently` is
emitted by the summary helper on stale abort as well as success, so those
lines cannot be counted as successful AI portfolio completion. Neither fact
alone proves why the human `.146` is absent. Targeted B1 owner/subject identity
diagnostics are being prepared; no global business rewrite is justified yet.

## R82: military-aid acknowledgement and final weak Character call sites

R82 used the 936-file release-identical product from pushed commit `e442893`.
Formal verification, the `626 files / 3721 effects / max 10 / target miss 0 /
over-20 0 / exceptions 0` effect boundary, and the CK3 1.19.0.6 no-launch
preflight were GREEN. After frontend warmup, the native timeline advanced about
540 game days at the acceptance default speed 5 before failing closed on the
previously unregistered vanilla `tgp_interaction_event.0016`.

The paused MCP frame froze `date_raw=53159976`, event instance 20, player root
29037, five available Character scopes, two typed Character scopes with
unavailable identity, seven saved scopes, and one shown/enabled native option
0. Exact source in `events/dlc/tgp/tgp_interaction_events.txt:338` gives the
letter no scripted option effect. The originating military-aid interaction in
`common/character_interactions/10_tgp_interactions.txt:6703` joins the governor
to the recipient's wars before it opens the letter. The bounded contract may
therefore acknowledge its sole option only after all identities, weak slots,
scope count, option shape and observation-window date pass. Negative tests
reject an invented weak identity, a different joining governor, and an extra
saved scope. The source file SHA-256 values are
`C845EBEB53A7D80E5155AF1D6FC42D03A86931C7088613CFA39A19B0DF468C75`
and `D081DD47F856C4F62313BDD1512177BCA049EADCE224F274A8E635F851576822`.

R82 reduced the previous run's 102 product weak-variable errors to three. Two
now originate in the subject-rooted `.121` deadline and one in the `.125`
manager watchdog. The deadline now requires an available live Character root;
the manager D+31 watchdog remains the owner-side accounting path. The watchdog
now places every pending-object variable read inside a nested `is_alive=yes`
branch. Thirteen separate `ordered_in_list max bigger than list` errors were
also mapped to full-list walks whose explicit maxima were derived from an
unfiltered list; those invalid maxima are removed while existing assignment
counters retain all bounded selection semantics. B1 normal and optimized suites
are GREEN at 66/66, and the checkpoint suite is GREEN at 15/15 in both modes.

The outer report, evidence index, cell report, promotion entry, loader and
cleanup SHA-256 values are respectively
`1ED926666B53F844058A77D9853F470F4ABCF129D5B3F488D41235DB990B2483`,
`ACD738C00461A2585942C4D02F425E981AC5CFE18D7FEB52C591BB904052CCCF`,
`B765E40C19EF4C4D867DDF1F498F72EA25D7B9A9EFC4A8043A5AD836069CA1F1`,
`F079ADBA8D922F1C1A4852A01E7830E80E78B44ACBCE3A3E160340A59AF00E2D`,
`8465CC0EBF62519FE6F060B7A7BA1D3FC49AAFF891C1612B7D51AA511FFE193F`,
and `5A05D5777CC585E77E95729FCAF4B1ECC43CA9F95E2E95DA06B2FB61EC209DB7`.
Cleanup was GREEN and CK3 returned to zero. R83 must prove the three weak errors
and thirteen ordered-list errors absent, drain the registered vanilla letter,
and continue the `.146 -> .147` product chain.

## R83: first product shadow-response frame

The weak-scope and ordered-list patch was pushed as `d869194`. Its fresh R83
release contained 936 files with source tree
`24D9463AAEE34F2D42038B1A8C19317751C9F6F0306FFE3D1C5D7ECF49A6C5B4`;
formal verification, no-launch preflight and the complete effect boundary were
GREEN. The loader completed and the default speed-5 loop drained seven exact
events before stopping without action on the first observed product
`zg361b1.201` frame at `date_raw=53157672`.

This is the authored non-final shadow-grade response opened by `.102`, not the
promotion-source `.146/.147` target. The native MCP frame bound player/root
29037, manager 36354, 18 saved scopes and two shown/enabled native options 0/1.
The five scopes consumed by `.201` are the shadow ticket owner, subject, cycle,
case and state. The remaining bank, manager and self-review ticket names are
the exact inherited shape from the preceding product chain. Existing production
choreography already selects option 1: accept the frozen shadow record without
adding a new calibration delta. The new contract binds the five consumed
fields, the manager aliases, four already-proven inherited name sets, the full
two-option shape and the product observation date window. Negative tests reject
a different manager, different player subject, wrong value type and any extra
saved scope. Checkpoint tests pass at 16/16 in normal and optimized modes.

R83 is the production-live proof for the preceding fixes: both
`This scope doesn't support variables` and
`ordered_in_list max bigger than list` occur zero times. The outer report,
evidence index, cell report, production entry, loader and cleanup SHA-256 values
are respectively
`CFCC0157C836E121EA3277629B4FFAEBBBF785FCD990BB6B69216AFE16D3481A`,
`2476C6F6C42183EAC8252DBF429BD9B056F055964823A738B255AB98630733A6`,
`F9B0B7413FAFF8BE3131686451C3BD8768B8941730726DF1A18D781236B0F9CF`,
`9BD46C1814BDEB9F234F8CE99C4DE31F6E002015B2E8CB3093B42F342F94D619`,
`E7F74303AD3B929B300B424B51C78817232F3BAA7EF3E44BB06C40D2657C4066`,
and `E68AA0378448D609DDF037FC82DFDF439291B4733879D6B3398F7C267DB7BF67`.
Cleanup was GREEN and CK3 returned to zero. R84 must accept the exact `.201`
frame and continue through bank close, calibration, publication and `.146/.147`.

## R84: shadow response passed; full-walk regression located

R84 used the fresh 936-file release-identical product from pushed commit
`45e0ce1`. Its source tree remained
`24D9463AAEE34F2D42038B1A8C19317751C9F6F0306FFE3D1C5D7ECF49A6C5B4`;
formal verification, no-launch preflight and the complete effect-file boundary
(`626 files / 3721 effects / max 10 / target miss 0 / >20 0`) were GREEN.
The default speed-5 loop selected the registered `.201` option and drained ten
exact events in total, but the 550-day product observation bound expired before
the player's `.146/.147` pair appeared. Initial native progress showed the
player B1 marker visible, while review-now, Central and PP were not visible.

The complete log disproved the initial idea that Central had never run: P2C
froze twice, while later publications were either unauthorized or stale. The
actual product RED was earlier in the B1 data path. Removing `max` from thirteen
full-list `ordered_in_list` walks had changed them into one-row walks, leaving
the rest of `zg361_b1_local_rank` unset before subsequent sorting. The corrected
contract retains each explicit full-walk maximum, adds
`check_range_bounds = no` for lists that can shrink, and prunes unavailable
subjects before quota or reopen processing. The `.122` cancellation callback
now reads subject variables only inside an `is_alive=yes` branch. Finally,
`.201.desc` and the identical `.126.desc` variable projection use the proven
character-localization form `ROOT.Char.MakeScope.Var(...)`; R84 had logged the
invalid `ROOT.MakeScope` data error three times. B1 tests pass 66/66 in normal
and optimized modes. These repairs are static-ready and require fresh R85 live
proof; R84 itself remains RED and does not close the migration tree.

The outer report, evidence index, cell report, production entry, loader and
cleanup SHA-256 values are respectively
`A0C3C80AAD96DF2E62BB8C1B48EF98352EC46CCC7B20739AD2A41C377EEE69DF`,
`DFB5B80F284AE9BA7D0438ABFB7877911A10608D7A381D77A40AAB319C3E0933`,
`DC17BAD4EC5A9BC9C5FB21A1D26554D984CB12E92E470E95764C18A3FE98179E`,
`C7174ABE9ED9043B48E14377CEF3124DBC63E2DDCD8B36842191B6E79BF7DBB7`,
`B7E428055D2954ED2EFDAE5BF95E5D00200C3BBD877D901AD4A0E62E31681158`
and `F5983C07239A0FA6794A29822F0CF3111417DC23BD634645D74E497CCC727E8D`.
Cleanup was GREEN and CK3 returned to zero.

## R85: `yearly.1040` frozen before action

Commit `a6c0c86` produced a fresh 936-file R85 release with manifest
`45BF2E1760B2F2A0E8909BC81E45BB331F715DF92CC3AA890B5FC4D1B336C981`,
ZIP `68EEB734A9ABD14924DBF80DBE4F615767096F201AD20F8BD22F7205EBCBB7B3`
and product tree
`8EB6F597FB42884695B2073D85198A2CB7316F8E219BC39FD0CC10BEAE953C98`.
Formal verification and the CK3 1.19.0.6 no-launch preflight were GREEN.
The product loader completed, then the speed-5 timeline safely stopped before
acting on the previously unregistered vanilla `yearly.1040` at
`date_raw=53147520`.

The native frame binds root/player 29037, a unique third-party `suspicious`
Character 31647, opaque `suspicious_type` and `surprise_type` flag scopes, and
exact native options 0/1/2. Exact source is CK3 1.19.0.6
`events/yearly_events/yearly_events_2.txt`, SHA-256
`64B778B7B3DFE1056EB0151A7ED3AA7CFB3E6E738E68144006BAF97E93E0A3E8`.
The frame is the good-surprise branch. Option 3 would schedule `.1044` and add
a later resource/relationship outcome; option 2 adds a duel. Option 1 makes
one opinion change and immediately enters the source-defined one-option
`.1041`, which adds no new scope and only discloses the already-frozen branch.
Both `.1040` and its direct `.1041` continuation now have fail-closed contracts;
wrong target, wrong flag type, extra scope or option drift remains RED. The
checkpoint suite passes 17/17 and choreography 5/5 in both modes.

R85 ended before the repaired B1 quota path was due, so zero occurrences of
the old signatures in this short run are not promoted to regression proof.
The outer report, evidence index, cell report, production entry, loader and
cleanup SHA-256 values are respectively
`1DAF60238A09B56696A66215DEE5CE8F66A4D84EB023D1653C950F78A56F4EFF`,
`BF94792EA61D691D8101E626DD5CD1C12CB6CCE1D75CFE043B9AF2883A2429AC`,
`7416B75839D0CF42503D5E3D065D316E3604B0485111D5B71284E9910040A7DB`,
`EB6FA73DB56CA3F4A2881ECA7EF2E2B3FCFD6079037F85E4ECC00AD268140470`,
`B22EAAA46C6A97F9D43890F7AE7AFC012CC009542397A7E39B5B9DFC9CEB0DE3`
and `64E4068582255DF68BA4E8C986737407CCFB940C803061CE18281FF5D0E91F1D`.
Cleanup was GREEN and CK3 returned to zero. R86 must consume both exact
contracts and reach the repaired B1 quota/reopen path.

## R86: dynamic merchant identities corrected

R86 bound the same product bytes to pushed commit `a26c46a`; the release
manifest was
`9B98C28B72D5EE1C4B34E63089CE4E027D34932BCFEA3FF382645842470FA75A`
and formal/no-launch checks were GREEN. This seed reinstall did not encounter
the newly registered `yearly.1040/.1041` pair. It instead reached the already
known `tgp_china_yearly.0015` at `date_raw=53147520` and correctly stopped
before action because the contract had frozen two obsolete allocator IDs.

Exact 1.19.0.6 source creates `market_vendor` and `traveling_merchant` inside
the event's `immediate` block, so their numeric Character IDs are not stable
across reinstalls. The source file is
`events/dlc/tgp/tgp_china_yearly_events.txt`, SHA-256
`4E722C41EE880085BD81E4793BADE40CC75B32933E7DC9AE6ED860C9879CB227`.
The corrected contract requires exactly two distinct, non-player Character
scopes with those source-defined names, retains the exact rendered/native
option shape and continues to select native option 2. Negative tests reject a
player merchant, aliased merchants and any extra scope. The checkpoint suite
passes 18/18 in both modes.

R86 stopped before the repaired B1 quota path, so it is not regression proof
for that repair. The outer report, evidence index, cell report, production
entry, loader and cleanup SHA-256 values are respectively
`DDD499A8535CB4E1D576AA5140F456830718DBE3D8F02574B00DCC96C32615FB`,
`CCC890B2DA4374DDA0A94876DE609794A81151E53E4925A8662F8E8737F278B5`,
`0B371F3828E98E349BD8816639D8874C7D4AB7DA993AFFAC2E8F6CF85C2BE9BC`,
`7445EDFC54B6922598438B36C45635186ECA6C9CBB413CE11B84E473083F8CAE`,
`1F945543A52FA768107F4254F480A31892815FE0BB6A6539113DB48E8570967D`
and `A8F45B8DA7A6B6880DAC8EE1803D398208CE533AF43AA76A5D909751D924AC37`.
Cleanup was GREEN and CK3 returned to zero.

## R87: dynamic military-aid role and nested weak fallback

R87 used fresh projection `phase2-full-release-r87-d2001b2` from the pushed
936-file product. Its manifest was
`48480C8F7867ED523F34948181068BE1004E724AD716562B5CEDD9E87372201D`;
formal verification, no-launch preflight and the complete effect boundary
(`626 files / 3721 effects / max 10 / target miss 0 / >20 0`) were GREEN.
The CK3 1.19.0.6 loader completed with 303/303 callbacks, fatal count zero,
then the default speed-5 native/MCP timeline made 394 observations and drained
seven exact events. It stopped before action on known
`tgp_interaction_event.0016` because only `recipient` and
`governor_at_war` had changed from their previously frozen numeric IDs.

Exact source shows why those IDs are not stable. The interaction chooses its
recipient dynamically, then
`common/character_interactions/10_tgp_interactions.txt:6658` saves that same
scope as `governor_at_war`; the joining governor is likewise both
`secondary_recipient` and `governor_joining`. The corrected contract freezes
these source-defined aliases, the fixed player/joining role, distinct
non-player recipient, typed unavailable generic slots, scope count and the
single option. Negative tests reject an alias mismatch or player recipient.
Source SHA-256 values remain
`C845EBEB53A7D80E5155AF1D6FC42D03A86931C7088613CFA39A19B0DF468C75`
and `D081DD47F856C4F62313BDD1512177BCA049EADCE224F274A8E635F851576822`.

This longer run reached B1 pending resolution and found five product
`This scope doesn't support variables` errors: three in
`zg361_b1_resolve_pending_subject_effect` and two in the `.125` watchdog.
All five dereferenced the pending subject's separately stored fallback
Character after the outer subject had already passed its own guard. Three
additional occurrences were exact-build vanilla combat/accolade paths and are
not attributed to the mod. Each fallback dereference now has its own outer
`is_alive=yes` branch before reservation variables are evaluated; the
manager-owned watchdog still closes the pending barrier when the fallback is
unavailable. The old ordered-list and localization signatures remained zero.
B1 tests are GREEN at 66/66 and checkpoint tests at 18/18 in normal and
optimized modes; choreography, capture, static validation, build tests and the
effect boundary are GREEN. These repairs remain static-ready until R88 proves
the five product errors absent and continues toward `.146 -> .147`.

R87 outer report, evidence index, cell report, promotion entry, loader and
cleanup SHA-256 values are respectively
`9612F7A1294EECDAB72C1EF526BC8D0A0E38F85760F501BB095B0426DF9CDE9F`,
`316A24B24F781B8171B306D9224BCE10F22C767ABC32EA678807E8AB8287CAC1`,
`4C83636EC729B5E3C19DFE8BD6F5DFCCCC4244EF07A00E1F32257B2EB99C67B9`,
`018C1A5065F6304E3ABE83E5F1B88C47C4AE4CE28B1492AB239291B7343D1514`,
`7148C7C9C4D14E9D0AD0947F21579ADD5EDE289261D60A56A396C9E5AE252615`
and `F0D50BFCBE76F2516216D5F7D6CA0AAD26FA42A993F5C3306EA3983204AFDD2D`.
Cleanup completed and CK3 returned to zero.

## R88: regressions cleared; player promotion path still absent

R88 used release-identical projection `phase2-full-release-r88-24189c1`
from pushed commit `24189c1`. The product contains 936 files; its release
manifest and product-tree SHA-256 values are respectively
`B27E1A420949DF213460F59FDA2A27518467418077BC6B378C209B0C64C46015`
and `A9FED5E8BFEB41E539FC28EC32F9CDAEF924F3E3A3DBE046A8B99C94030269D1`.
The exact-build loader completed all 303 database nodes with zero fatal
matches. The same managed CK3 process then ran the product timeline at speed
5 for the complete 550-day bound.

The native/MCP driver made 398 observations and safely drained seven exact
events: `zg361b2.40`, `zg361.40`, `zg361b1.200`,
`spymaster_task.0381`, `ep3_governor_yearly.3060`,
`spymaster_task.0342`, then a second `zg361.40`. It used neither fixture nor
console state. The final product log has zero occurrences of
`This scope doesn't support variables`, `ordered_in_list max bigger than list`,
`zg361b1.201.desc`, `Could not find promote for`,
`Variable 'zg361_b1_local_rank' is not set`, and any B1 product path in
`final_error.log`. This supplies production-live regression evidence for the
R84/R87 repairs.

The run is still RED. Product trace now proves that B1 seasons can rerank,
publish and call the Central lifecycle hook, but each affected Central tuple
either completes as an eligible AI portfolio or is rejected as stale. The
played-character `zg361pp.146` source and delayed `.147` source never appeared
before the 550-day bound expired. This is progress beyond the earlier
pre-publication failures, not completion of the player promotion path and not
a reason to inflate the per-mechanism fixture-live count.

R88 outer report, evidence index, cell report, promotion entry, loader-native
readiness and cleanup SHA-256 values are respectively
`2471ABD31F25E4A9B1FC24E9991464F17CF2D5D10F75E60D7398DD96B22EC8DC`,
`3F6980618C78AF1832722C161B660C7AEC42FD54A7C95E3D2CE1ADB93DE65F8B`,
`599BFD0CF275AF72C3A41DC547BA86685BDAFDA9C53F29898CFC241F91058639`,
`772208CDD4272AECD5D4C39BD6AE1B58DD3470824E21BCE15D72013CB0077678`,
`65CB35CCA192FD717137421DF878F279225A81922A4FB4D02598159A8F3DABAD`
and `A041FC4F9E4D6703797A4FAE1922EEB9F3BD6CE6C27FA4782C6DFDA3AC3C4EC1`.
Cleanup was GREEN and CK3 returned to zero.

## R89 precondition: player-owned progress time series

R88's 398 timeline rows carried only date, pause and active-event state. The
native `query-zhongguo-promotion-source-progress-v1` observer was queried once
before the run, when it proved only that the played character's B1 cycle was
active. Consequently the later product logs prove that *some* managers
published and reached Central, but cannot distinguish a played-character
Central activation from the many AI managers' silent paths. Inferring the
player path from those aggregate logs would be unsound.

The R89 runner precondition now samples that existing read-only native/MCP
observer on every product-timeline observation and retains compact
played-character booleans for review-now eligibility, B1 active, Central
active and PP active. Any unavailable widget stops the run instead of being
recorded as false. This does not change gameplay or add an acceptance fixture;
it closes the missing observation channel needed to decide whether the player
never starts Central, starts and immediately becomes stale, or reaches stage
3 without materializing `.146`. Runner tests pass 19/19 in normal and
optimized Python; choreography, B1 witness and runner-plumbing suites pass
5/5, 5/5 and 18/18 respectively in both modes. This remains static-ready until
R89 supplies a real time series.

## R89: running-frame query rejected before business progression

R89 passed the no-launch preflight, exact 303-node loader gate and managed
native-session startup on PID 98608. The first two compact progress samples at
`date_raw=53147016` consistently showed played-character B1 active, Central
inactive and PP inactive. On the next running-frame sample the native bridge
rejected the GUI-backed progress command with `ZhongGuo promotion source
progress binding changed or is not ready`.

This is a harness RED, not a product-capability RED: the query contract is
paused-frame bound, while the first implementation issued it before pausing a
running map. The runner now explicitly pauses before every progress sample,
rebinds the same player/connection/date, queries, then resumes at speed 5 when
there is no event. The focused fake rejects any poll made while running and
locks the pause/query/resume order. Runner tests are again 19/19 in normal and
optimized modes. R90 must verify the corrected sampling loop in CK3 before its
time series can be used to diagnose the player path.

R89 outer report, evidence index, cell report, promotion entry and cleanup
SHA-256 values are respectively
`96737B540EF20905D9481A3EAC3C4FDB78E8B3AABD6B0726A200B0B18F431B6B`,
`D60A08FA033C539308F7CB3CFF70F9102212C85E00DB695339B7822E12A19DA7`,
`2643D6F5CBB88816CA03118E93C17B00AA91FC785C16FD4C3F3BFE3F1B8EC66A`,
`6E37FEA597112699DBCD63BFCD2D658F5EC8834B5A5E3C1AA052934D44C71391`
and `241DF92FC5D508E6453AF2051BDB2778A79AA0276709B062B340D89426438FB2`.
Cleanup was GREEN and CK3 returned to zero.

## R90: paused speed-transition snapshot drift

R90 again passed the no-launch preflight and exact 303-node loader gate, then
started the managed native session on PID 90888. The initial query and first
timeline query both bound the played character at `date_raw=53147016`; the
compact player state remained `B1=true / Central=false / PP=false`. Before any
game day advanced, the second timeline query was rejected with `ZhongGuo
promotion source progress binding changed or is not ready`.

The retained entry proves two observations at the same public revision and
date, but only one successful timeline progress row. This is a second harness
RED, not a product-path result. The runner set speed 5 while paused and left
the map paused until the next loop. CK3 applies that speed command
asynchronously: the cached bridge snapshot could still describe the old speed
when the command returned, while the next query's direct native read already
saw the new value. The query correctly rejected that mixed snapshot. The
runner now completes `set-speed-5 -> fresh binding -> resume-map` in the same
loop; no progress query may bisect a paused speed transition. The focused fake
models this transition and fails if a poll occurs between those commands.
Runner tests pass 19/19 in normal and optimized Python; choreography and
capture suites pass 5/5 each.

R90 outer report, evidence index, cell report, promotion entry and cleanup
SHA-256 values are respectively
`03AFACDBA444A26045A5127D156E94D72E37B6A6C2D0300604C9F79B3B357C5C`,
`F98CFFCC29DAA319F524469B327F280B4ABAF78235BD8C1B714C5A440AC605FF`,
`FA7AF3830FD4D4011CA7EDF3F9E087B49B7AC87923D5CAA4227994879A674071`,
`380E5B779E6535EA41B601947C7779A3CB828D77F89091E42C7EBCA4A5E92909`
and `CC42A1A1533A4193A7FC8DDC2CAB3EC69E5F198EA839E448F1938D161EA0406C`.
Cleanup was GREEN and CK3 returned to zero. R91 is the first live verification
of the complete pause/query/set-speed/resume cadence.

## R91: same-date pause churn exposed the remaining race

R91 passed formal preflight, the 303-node loader gate and managed startup on
PID 98452. Its first timeline progress sample was again available at public
revision 4 and `date_raw=53147016`. The runner then resumed at speed 5 but
polled again after only 50 ms, paused before one game day advanced, and reached
public revision 5 at the same date. That first post-pause query was rejected by
the native direct-read equality gate. Cleanup was GREEN and CK3 returned to
zero.

This narrows the remaining harness defect beyond R90: immediate resume alone
was insufficient because the loop still manufactured rapid same-date
pause/resume churn and queried before the bridge's 250 ms heartbeat had settled
the complete native Snapshot. The R92 runner therefore keeps an unchanged,
event-free date running at speed 5. It pauses only after a new native date or
rendered event exists, then waits 350 ms (one heartbeat plus margin), rebinds
the exact player/connection/revision and performs the read-only query. The
focused fake holds the first running poll on the same date and independently
rejects both a paused-speed-transition query and a pre-heartbeat query.

R91 outer report, evidence index, cell report, promotion entry, loader scan and
cleanup SHA-256 values are respectively
`34BF8002B469EDC1E0118910B129198FCF339A13FDBCB658FA0CB66C26AA1B17`,
`7EC760898F62292CD1ED097999F4FE191E032F0C1996E9B3CC22B70FAE20621C`,
`50B1F6D11C0DBFC5C8970863C9F905748C9C0C1745B49165B8FD15A107EDA66F`,
`6473277DA9245B022D75C0B8E6E445ED998A557B15F53C78F104555C24EF7112`,
`754A00259845E7380088BF9C9F94B0B9793E3FFEBF4C1904BAD0D175BC15E762`
and `0D02B8F5F0989665305FB7172C01DD530CDCCA158F503A16423B72B5126A93BB`.
The loader scan was GREEN; the product path did not advance far enough to
change B1 readiness.

## R92: long-running sampling succeeded; resume used a stale public revision

R92 passed preflight and the complete 303/303 loader gate, then kept the same
product session running at speed 5 from `date_raw=53147016` to
`53150352` (139 game days). It collected 33 successful paused-frame player
progress observations and drained `zg361b2.40` plus
`spymaster_task.0381`; every sample remained
`B1=true / Central=false / PP=false`. This proves the R92 date/heartbeat
cadence works and supplies real player-owned progress, but the elapsed window
is still too short to judge the full authored B1 bound.

The RED occurred after progress query 33. A later native heartbeat advanced
the public revision from 118 to 119 before `resume-map`; the old runner sent
118 and the driver rejected it *before submission*. No gameplay input crossed
that stale binding. The resume helper now takes a fresh binding immediately
before the idempotent map-state request and retries only
`PreSubmissionRevisionMismatchError`, with every rejected revision recorded
as `request_submitted=false`.

R92 outer report, evidence index, cell report, promotion entry and cleanup
SHA-256 values are respectively
`D247A2ACEED79BAE1E59D7A44F6F21CEC67A46629F9C66D72BA0544BC6B0437A`,
`0EF2D2113AE7597E6844F8BFE6E2231CFA89DAFF0F9E0ADA55D907FBF5129CF4`,
`05D71C704046F402D170C8ED5C59155AC1478DF16B61649073BFFE24D78BC6EA`,
`6B208B61EBA731BEABBC2C188A1281B0A2C9A8E69CB2D05EDE2CE8FE46A68E79`
and
`085B9D0C3C5548F6129567533FF2F9E37E513B99F0F5B8724C2FD726E882FDB6`.
Cleanup was GREEN and CK3 returned to zero.

R92 also exposed a lifecycle defect: a healthy CK3 was terminated merely
because its Python client raised. The runner now supports
`--retain-healthy-phase2-session-on-red`. On a Phase2 RED it verifies the
live supervisor, exact PID/pipe/generation, map readiness and played-character
binding, writes `09_phase2_native_session_retained.json`, closes only the
failed client, and leaves the owning CK3 session available. The separate
`resume_zg361_phase2_promotion_source_session.py` client validates the
retention, seed and loader receipts before reconnecting. It neither launches
nor stops CK3 by default. Product/mod or bridge changes still require a new
session; Python harness changes do not.

## R93: retained-session 1,256-day trace found the cross-year bank reset

R93 loaded the unchanged R88 release-identical 936-file product through all
303 database nodes with no fatal loader error. The cold-start client and two
replacement Python clients then kept CK3 PID 71148 and the same exact pipe and
episode alive from `date_raw=53147016` through `53177160`: 1,256 game days,
296 paused-frame player progress queries, and 10 exact event drains. Every
player sample was `B1=true / Central=false / PP=false`. The continuation is
therefore strong contrary evidence to the earlier idea that the 550-day bound
was simply too short.

The live product log records `ZG361B1: stale common-superior bank ticket
ignored` at `zg361b1.110`. Source reconstruction closes the causal chain. A
common-superior bank schedules its closure at D+335, but registration formerly
reinitialized the bank whenever `zg361_b1_bank_season != current_year`. A new
manager registering after the calendar rollover could replace the active
bank's season/case/state before the old deadline arrived. The old ticket then
failed its exact identity checks, and existing manager cycles—including the
player's—could remain active indefinitely.

The authoritative B1 generator now initializes only when bank state is absent
or is not the active value `1`. A live bank therefore retains its original
season, case and deadline across the year boundary; a closed or absent bank
still starts a new current-year season. The generated purpose shard remains
at eight top-level effects. Focused B1 tests pass 67/67 in normal and `-O`,
effect-boundary tests pass 4/4 in both modes, the promotion runner passes 24/24
in both modes, choreography passes 5/5, and the whole static gate is GREEN.
This is static-ready pending R94 production verification; it does not yet
promote the `.146/.147` registry.

R93 report, evidence index, entry and retention SHA-256 values are respectively
`CDC26175696F7C477CB9D0EDFE75C48AD93E0743087F2EB60FC5B9C410EAE481`,
`A7EDB3AEA8E228E74F850718C1BFD3A6E9F19CEB2440655F4597CFBC6A805C3C`,
`3EF27660BFB0756EB608AB5F1225DCF072B38A7C952988F765DBC4909A3F4C87`
and `45A20A96D71DFD52EB838FC5BD14E0531CA039CA82872949E0349BA9D6216151`.
The resume6 and resume8 entry SHA-256 values are
`ED46F363BBEACFC6087DE2063D836211B29F7B6DF53CA8141132D617B2D7FA29`
and `F22563B20893C59CFB1AEFC75DAD65CF584C8B60611E6E7D2EDEDDC95FBAE5DB`.
The old session was then stopped through its managed file queue. Because the
fix changes mod bytes, R94 requires one fresh CK3 startup.

## R94: current bank bytes exposed a pre-v2 active-cycle migration boundary

R94 cold-started the committed `4bc9561` product projection
`phase2-full-release-r94-4bc9561`. The staging contained 936 verified files;
its tree SHA-256 was
`2641FA92F0440EC6725106851A37F340DCF1E3EB15058E8B65FF9E36CD39A281`
and its release-manifest SHA-256 was
`EF68228351E4BE3592B6151D66EA1C0851504665ED117B69ED14CE5A67CA3E94`.
All 303 database nodes loaded with no fatal loader error.

The first client stopped before original event `ep3_governor_yearly.8160`
because the harness had frozen one allocator ID for `scope:administrator`.
Exact-build source proves that `.8160` creates a fresh administrator in its
`immediate` block. The contract now requires the live administrator to be a
unique non-player Character distinct from the known councillor, while keeping
the native option shape and selecting empty dismissal option 3. A replacement
client applied that correction to the retained PID and drained the event
GREEN; no CK3 restart was performed for this harness-only change.

Across the cold client and continuation, the same process advanced from
`53147016` to `53160672`: 569 game days, 135 paused player progress samples,
and eight exact drains (`zg361b2.40`, `.8160`, two `.0381`, `zg361b1.200`,
`.0342`, `zg361.40`, and `.0016`). Every sample remained
`B1=true / Central=false / PP=false`. The R94 report, evidence index, cold
entry, continuation report, and continuation entry SHA-256 values are:

- `4E6A43B06084DDDA0CAF342C84305B109DE25B8DBB37EDBBF3CFF7D74157BC35`
- `A164CD3CA6F0555BDE172290F25D68B9DAB4F9DA683ECE6B084F6B903A2F4A9D`
- `185234021B2FEF1516C91B102EF5C3E7181C18EEAF894C279ED48B39EDB29F27`
- `D9BBB7D96C22C89CCFB403F7C5B071F8DC1B8702AC9A8229E6CF9052B8EC40C2`
- `FD1D5DDF7760C5B4282943DF1C33EF58E9867D6E07001179407CB830243EA738`

The seed receipt binds the canonical save to source commit
`218026a65d61db0a4c0d5248a2a68d3a4f42ce4e`, and the very first R94 progress
frame already has player B1 active. The cross-year registration fix therefore
cannot rewrite that saved manager cycle in place. This is the narrow evidence
for a backward-compatible migration, not a claim that the new-bank rule failed
for a newly opened cycle.

The generator now assigns schema version 2 to both fresh manager cycles and
common-superior banks. At the next real annual entry, an active pre-v2 cycle is
retired with exact owner/subject/cycle/case checks, no publication and no
reward; its stale lists and review flag are cleared, then the same invocation
opens a fresh v2 cycle. A pre-v2 bank is likewise rebuilt only once. The new
recovery code occupies its own one-effect purpose shard, while every generated
effect shard remains within the 1-10 contract. Focused B1 tests pass 68/68,
effect-boundary tests 4/4, and promotion-runner tests 25/25 in both normal and
`-O`; the full static gate is GREEN. R95 must cold-start because these are mod
bytes, and remains responsible for production verification through publication
and `.146/.147`.
