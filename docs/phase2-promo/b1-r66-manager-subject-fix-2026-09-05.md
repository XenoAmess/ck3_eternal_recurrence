# R66 B1 dual-role identity fix — 2026-09-05

Status: `static-ready / production-live-pending`. This package did not start
or attach CK3. Root owns the next frozen candidate and live gate; no commit
was made by this package.

## Observed failure, not a speculative collision

Frozen `Z:\b3r66\cell\final_debug.log` lines 4139 onward identify player
Character `29037` as both an active manager and the emperor's subject:

- 11:15:16: own manager cycle/case/state `19/19/1`; incoming subject `1/1`.
- 11:15:18: the same character's shared cycle/case is now `1/1`; incoming `2/2`.
- 11:16:25 (`.100`, line 4599): saved ticket `17/17/1` versus current `2/2/1`.

The first two writes prove the actual-use field collision. They do **not**
prove ticket 17 was the latest valid manager ticket: manager-only historical
witnesses, not the queued ticket or overwritten subject fields, determine
migration. A genuinely stale ticket must remain stale.

The real path is superior `open_cycle` → per-subject `initialize_subject_case`
while the subject has its own active manager cycle → manager delayed `.100`.
This also ran in the reverse direction before the fix: a manager increment
could overwrite its identity as a subject in its superior's cohort.

R66 `final_error.log` line 14144 onward separately records unset
`capital_county` from `finalize_subject_facts` through `open_shadow` →
`run_review` → `.102`. Root's same-run diagnostic also located Character
`45425`'s unavailable weak reference being read repeatedly downstream of
`.102`; reusing the existing availability prune at that entry is the limited
fix. These are business failures, not global error-count inference.

## Production changes and ownership

| Role / path | Current serial fields |
| --- | --- |
| Manager opener, stage tickets, policy debt, quota/calibration/publication | `zg361_b1_manager_cycle_serial`, `zg361_b1_manager_case_serial` |
| Subject initializer, self/shadow/peer, pending deadline, subject facts/results | Existing `zg361_b1_cycle_serial`, `zg361_b1_case_serial` |
| Mixed subject-list / owner comparison | Subject old field on the left, manager new field on the right |
| Central publication hook, frozen tuple, pump, delayed manager continuation | New manager fields |
| B2 KPI owner-side source and Incident expected/cohort source | New manager fields; their subject ABI fields remain unchanged |
| MG distribution policy | New manager cycle only; organization/refusal keep subject cycle |
| Promotion manager witness / GUI projection | New manager fields; read-only GUI does not migrate |

Authoritative B1 generator writes the product artifacts. The new
`zg361_b1_manager_identity_effects.txt` contains exactly **one** migration
effect; it is not appended to the legacy 42/36 definition shards.

`zg361_b1_migrate_manager_identity_effect` fills each missing new field
independently and never overwrites an existing new identity:

- Cycle recovery: `zg361_b1_policy_next_review_serial - 1`.
- Case recovery: `zg361_b1_m053_receipt_serial`.

Each witness has one manager-only producer. The helper reads neither old
shared field; absent witnesses do not manufacture identity. New managers
are initialized by the real opener with independent counters at zero before
increment. Calls occur at opener, all manager delayed entries, before an
active manager's subject initialization, and Central's independent manager
entry points. Subject-only entry points and native subject ABI are unchanged.

The no-capital branch sets `baseline_available=0` and `baseline_state_delta=0`
with marker `ZG361B1:baseline-unavailable-no-capital`. The difficulty adjustment
already starts at zero. The capital-present calculation is unchanged. Frozen
start facts, KPI, roster membership and cohort denominator are preserved.

Both `.100` and `.102` now call the existing `prune_unavailable_subjects`
before their first roster consumer. Its `is_alive` semantics are unchanged;
no `is_landed` filter was added, so living departed subjects remain in cohort.
`.103` and later pruning behavior were not expanded.

## Validation and file-boundary evidence

- B1 generator: **13** current generated outputs, BOM retained.
- B1 tests normal / `-O`: **63 / 63 GREEN** each, including four focused
  regressions for migration/shard, source-derived R66 assignment vectors,
  manager entries versus subject ABI, and no-capital preservation. Existing
  weak-subject test now covers both `.100` and `.102` prune-before-consumption.
- External Central/B2/Incident/MG suites normal / `-O`: **164 tests plus
  677 subtests GREEN** each, reported by the exclusive external-consumer writer.
- Promotion D0 witness normal / `-O`: **4 / 4 GREEN** each.
- `validate_local.py`, root `tools/validate_static.py`, `git diff --check`: GREEN.
- Effect boundary: **428 files / 3721 effects**, target misses 0, >20
  violations 0, maximum non-legacy definitions 10. Legacy counts remain 42/36;
  this change grants no new >20 exception.

The numeric regression is explicitly a narrow source-derived assignment
model, not CK3 execution. `open_kaishek`'s current finite runtime does not
certify the full production effect/list chain, so parser success must not be
described as runtime reproduction.

Keep the earlier file-boundary lesson separate from this business cause:
file boundaries/size remain a likely contributor to the earlier startup RED;
this R66 evidence establishes serial aliasing after successful load. If the
next candidate regresses to loading-performance RED, inspect its exact shard
sizes and try a purpose split, keeping each new shard at 1–10 effects and
never silently adding a >20 exception.

## Remaining live gates

1. The same human may receive new subject cycles while its independent
   manager identity and valid manager ticket continue through `.100/.102`.
2. A still-valid saved manager pair resumes via its private witnesses;
   genuinely obsolete tickets stay no-op. Do not force recovery to ticket 17.
3. Capital-less living departed subjects retain frozen evidence without
   baseline native-read errors. The existing `is_alive` pruning actually
   prevents the observed unavailable weak-object reads at D+300.
4. Player Central source chain reaches `.146` and D+1 `.147` with correct
   frozen owner/cycle/case. AI silent summary/abort is not player closure.

Frozen log SHA-256:

- `Z:\b3r66\cell\final_debug.log`:
  `8CEB947FA316EA1418626340425D4570F47ED8673643858B0C18DEC0DEB5BBCD`.
- `Z:\b3r66\cell\final_error.log`:
  `A60B2BBC08192D031D77C812E78CC57181F93DDAE1E88BCFBB36AF2C2D61F58C`.

Exact CK3 build: `1.19.0.6`, EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`.

## R67: old-save read-only migration gap

R67 used the repaired 636-file production closure at `Z:\p2ac\p`
(`3,708 effects / 988 events / 24 triggers / missing 0`, tree SHA-256
`e59ed83c91c3556408178bc938f6dcb690884e4db64976cf31fcf6938243c38a`).
The loader was GREEN, but the runner stopped before a product action because
all three active-source projections and review-now were false on the frozen
seed.  The seed retained `zg361_b1_cycle_active` and the old manager-only
`zg361_b1_policy_next_review_serial`, but had not yet executed a business
effect that creates `zg361_b1_manager_cycle_serial`.

This is an old-save compatibility gap, not a file-size/load-performance RED.
Direct `-load_save` skips the lobby path, so a read-only GUI query may precede
the first idempotent business migration.  The B1 active projection now accepts
one additional, mutation-free branch only when the new manager cycle is absent:
active-cycle/review flag, valid cycle state, and manager-only
`policy_next_review_serial > 1`.  Because that witness is produced only for
the manager and equals manager cycle plus one, subject-only legacy fields still
cannot impersonate manager identity.  The first real `.100` entry remains
responsible for the actual migration and ticket comparison.

Frozen R67 SHA-256:

- outer report: `EA23AF89CB786755388C88528213197A6B339D747D28C77832D8796CE4FFF48A`
- evidence index: `279DF9622D30DDC58E8DD364490520EBDDAE53D1E77FCA919A3509C0189EB91A`
- promotion entry: `2CDAB8C205FF3411AABC5B06A6C38A1572ED9D29A1D9499DEFFE5316CD58C89A`
- loader gate: `A771A66C3BB19248B18927AB5999E3AFCBBA534631C26AC2879C11CBD250DB78`
- cleanup: `BAE137B0EC4F2FA6EB33C60A1125AD256B58BA314305CCD681E171CA418717CE`

## R68: bank-descendant self-review frame

R68 proved the old-save active witness in CK3: the initial B1 widget was
`effective_visible=true`, review-now remained false during the already-active
cycle, and the runner advanced through the real product timeline.  Loader was
GREEN and the mounted/product/canonical trees remained unchanged.

The run stopped before action at `zg361b1.200`, date raw `53156232`, instance
18, player `29037`, manager `36354`.  The exact frame contains the nine existing
self-review/manager ticket scopes plus the four
`zg361_b1_bank_ticket_{owner,season,case,state}` scopes.  Product source shows
that `.110` receives this four-field bank ticket and calls the bank-close path;
the descendant manager/self-review event can retain those scopes.  The runner
contract therefore adds only the exact 13-name set (and its existing optional
seed-scope variant), requires all three bank values to be `value`, requires the
bank owner to be a non-player character, and aliases it to the review-ticket
manager.  Arbitrary extra scopes and a different bank owner remain RED.

R68 remained `static-ready-live-pending`; it did not submit `.200`, reach
`.146/.147`, or create a registry entry.  It is a post-loader choreography
contract RED, not a file-size/load-performance RED, so no effect split follows.

Frozen R68 SHA-256:

- outer report: `F2EB34AAEEA2321B34C323B72526E5EBB90102CA1C0FF8CAB892E088A66C379A`
- evidence index: `4321004D974E056A1CC4F3EA9374D792CA788845B781B420BDFA9384F91445B5`
- promotion entry: `C0BE2B9D4A18DE0A4919E526EC275E34D7C048668DA0762C4D92FAEAE6120CBB`
- loader gate: `DD87111238CBB70B5D3FF16D284906AF3499380B842A663EA0E1B477EEF52292`
- cleanup: `253F67A80A3E9921EB22F1751131C02E09139A057CCDBA3ACBE55C774BA9BB34`

## R69: source-proven Find Secrets boolean branch

R69 reused the unchanged 636-file R68 product tree. The final loader gate was
GREEN and the mounted product remained unchanged. The run then stopped before
action at vanilla `spymaster_task.0399`, date raw `53152896`, event instance
`18`, root/player `29037`. Its exact saved scopes were three Characters
(`councillor=27963`, `councillor_liege=29037`,
`target_character=27051`) plus Boolean `secrets_to_be_found`; both rendered
options were shown and enabled, mapping to native indices 0/1.

The frozen CK3 1.19.0.6 source in
`events/councillor_task_events/spymaster_task_events.txt` proves that `.0399`
uses an immediate 5/5 `random_list` and saves exactly one of two Boolean
scopes: `secrets_to_be_found=yes` or `no_secrets_here=yes`. R60 had observed
the latter at raw date `53148768`; R69 observed the former with the same three
character identities and option shape. This is legitimate source-defined
random state and delivery timing, not arbitrary schema drift.

The runner contract now binds `.0399` to the existing per-run 550-day product
observation window and accepts only the two exact four-name saved-scope sets.
The selected action remains authored option 2/native index 1, which preserves
the current Find Secrets task. Both Boolean names at once, the wrong scope
type, an unrelated extra scope, or an out-of-window date remain RED. This is a
runner choreography correction; it does not change the product projection.

R69 is still incomplete for the promotion registry: it submitted no `.0399`
action after the mismatch, reached neither `.146` nor `.147`, and created no
valid source entry. The correct canonical registry count remains **0/4**, not
the runner mode label that says it is attacking category one.

Frozen R69 SHA-256:

- outer report: `232312121E7ED5420B4CA4FCC12CDED9CA7FF41E781F630DCA22E654EB5041A9`
- evidence index: `5823FA259D7CC61F064B91BBAB72C00FF731AFF20B20196DA0B596B92E3CC3D7`
- promotion entry: `4B0E20EE40C40BA366B543A7B6FB8EEFC262ED761EE62CCAABBBE336FE96EF29`
- loader gate: `45461BCA8DDF84095CC7EED1E822AFBB75B5A96A18E5E0668BCEBB1318524083`
- cleanup: `A089E17F194050F52E385313205F9A059711D8B6D93242A43FB40914026D99A2`

R69 adds another negative file-boundary datum: the 636-file product loaded
GREEN and the failure occurred only after load at an exact event-contract
check. There is no loader/file-size/performance RED, so no effect file is
split for this failure. The B2+ policy remains purpose grouping, target 1–10
effects per file, hard-normal ceiling 20; any future loader-performance RED
must again be tested against exact shard sizes before a purpose split.

## R70: source-randomized sway compliment options

R70 ran from committed `34d2dbf` against the same unchanged 636-file product.
The formal loader gate, native readiness, capability preflight, error scan,
mount, protected storage and cleanup were GREEN. It drained B2 PIP and vanilla
`spymaster_task.0381`, then stopped before action at the previously unregistered
vanilla `sway_ongoing.1002`, date raw `53149920`, event instance `15`, root
`29037`. R69's `.0399` event did not recur, so its dual-Boolean correction
remains live-pending rather than being claimed as R70-verified.

The exact `.1002` frame has five saved scopes: Characters `owner=29037`,
`target=27051`, `compliment_receiver=27051`, plus typed `scheme` and `artifact`.
Four shown/enabled rows map to native option indices `(1, 3, 8, 12)`. Frozen
1.19.0.6 source establishes that the no-friend branch randomly selects three
distinct compliment flags from twelve authored compliment options. The final,
thirteenth authored option has only a name; unlike the compliment branches it
does not evaluate a compliment or invoke the common outcome effect. All paths
still run the event-wide `after` cleanup, and the 3650-day scheme flag was set
in `immediate` before the window opened.

The runner therefore does not freeze the random `(1, 3, 8)` prefix. It accepts
exactly three strictly increasing, distinct native indices in `0..11`, followed
by native index `12`, while retaining the exact root/owner/target/receiver,
scope types, five-scope count, four rendered rows and thirteen-authored-option
snapshot. It selects authored option number **13** (native index `12`), not
rendered row number 4. Duplicate/out-of-range compliment indices, a missing
final index, or a wrong receiver identity remain RED. Delivery is sourced from
the monthly randomized sway on-action, so the date is bound to the existing
per-run product observation window.

R70 reached only raw date `53149920`, before B1 D+180. Zero weak-variable,
no-capital, B1 diagnostic, P2C and `.146/.147` markers at that stop do not close
their live gates. Registry remains **0/4**.

Frozen R70 SHA-256:

- outer report: `232983ED61746AC7330BEABE565DE4A767A9A905C185CDA844583924D02E23D9`
- evidence index: `76E5B855C0466D736E822BEC4AF6827B3C8D257D5D641D77E4F246A3FB69AC9E`
- promotion entry: `21B846EAC8D090485BA5F3A15837BEA9A4590E72429247C00A6098D1A73B1F98`
- loader gate: `E8D5C58E234277C1123C48F5A03E075E0EAEC100A4473E59A7F323E6F380E751`
- cleanup: `C290AF4C37FB0B5D58DDEC38D234B247E19F9E8A143D66DDB15A58EDDB49F331`
- driver state: `A4F93A28D78C7C5155DAEC993AC621E62CF5FCA81AE2E39384F52C24512FAC51`
- vanilla sway event: `F646FAE510A66A87A01B464140F7206921B141E6F3D3D06CE20570C18C7B9759`

This is another post-loader choreography RED. The 636-file tree again loaded
GREEN, so R70 supplies no evidence for an additional effect split. The B2+
purpose-shard target and ceiling remain unchanged.

## R71: inherited bank-ticket payload is opaque on `.200`

R71 ran from committed `bab9679` against the unchanged 636-file product. The
frontend-first warmup, final native bridge, capability preflight, product
mount, loader error scan and managed cleanup were GREEN. The run drained B2
PIP, vanilla `spymaster_task.0381` and product `zg361.40`, then stopped before
action at `zg361b1.200`, raw date `53152728`, instance `18`, player `29037`.
It therefore did not exercise the R69 `.0399` or R70 `.1002` branches and did
not reach `.146/.147`.

The exact 13 saved-scope names added after R68 were present, but five R68
payload assumptions failed: the three inherited bank values no longer had
type `value`, and `zg361_b1_bank_ticket_owner` neither matched the active
review manager nor remained a provable unique non-player character. Product
source explains the boundary. The four bank-ticket fields are authored for
the outer `.110` bank-close event; `.200` neither reads nor validates them.
Only the nine manager/self-review ticket fields are created for and consumed
by `.200`. Descendant context can preserve the four outer names after their
payload bindings cease to be meaningful.

The R71 correction therefore keeps exact 9/10 and 13/14 name-set admission,
keeps player subject, review-manager alias, manager non-player identity, all
six consumed value types, exact three-option shape and honest option 1, but
treats the four inherited bank payloads as opaque. Missing or extra names and
any drift in a field actually consumed by `.200` remain RED. The focused
checkpoint suite passes 8/8 in normal and `-O` modes. This is a runner
contract correction only; the production tree did not change.

Frozen R71 SHA-256:

- outer report: `398A1F0290402C856EF20226356D50036A9CFD10434121A192A5BF05A376CF49`
- evidence index: `C7ACC748707B90D402C8FC21244AB709D2A8EFC02B7189356A066ECE6B3114EB`
- promotion entry: `241F661FC7AE86547D5418D2921ADCF58CF9F32695823FE66134AB1137210470`
- loader gate: `0986ECFA2F1A94EB5063668B8694721FF62FA2CF399312C115A326D16700C1B3`
- cleanup: `9D69DBF388742B6F41E300543E9D6CD70339D9BEC89D65C6C041E34E031C9A08`

R71 again separates loader health from event choreography: load remained
GREEN and the failure occurred roughly eight minutes later at an action gate.
It is negative evidence against file size being this failure's cause. No
effect split is triggered; the B2+ purpose grouping target of 1–10 and normal
ceiling of 20 remains enforced.

## R72: Friends & Foes yearly interruption

R72 started from committed `81d5c63` and the unchanged 636-file product.
Frontend-first, final native/capability readiness, product mount, loader scan,
protected storage and cleanup were GREEN. Before any new action, the runner
stopped at previously unregistered vanilla `bp1_yearly.9006`, raw date
`53147520`, instance `14`, root `29037`. The complete frozen window is retained
in driver-state: one Character scope
`bp1_yearly_9006_sinful_courtier=29068`, two shown/enabled options mapped to
native indices 0/1, and no conditional animal scopes. R71's `.200` branch did
not recur and therefore remains live-pending.

Exact CK3 1.19.0.6 source shows that the narrow-yearly event randomly selects
one courtier or vassal, distinct from root, who shares a qualifying trait.
Option 1 creates or advances friendship and also changes root piety/stress;
option 2 changes only root piety/stress. The runner binds the dynamic courtier
as one unique non-player Character, exact one-scope/two-option shape and the
existing product observation window, then selects authored option 2/native
index 1 as the minimum external-side-effect path. The same yearly source can
legally recur at most twice inside the 550-day run. A player-valued courtier,
extra scope or option drift remains RED.

The runner now also retains a full `unexpected_event` snapshot/query in its
top-level evidence before failing, so the next genuinely unknown event no
longer requires recovering context from driver-state. This changes only
harness evidence, not product behavior.

Frozen R72 SHA-256:

- outer report: `EB76555AD4AF5DF5E4078BDDDD917C086DB3AA278A99E06252F981DCEA2243A8`
- evidence index: `376745C06DC8E6BB6B2DC6A42F16C573F9E631C087777A6047BE4AFC886EEC4C`
- promotion entry: `B36CDC6D8EB7910FCEE2081D86C317A090F70A1E9B29122B88C81EED96F8075A`
- loader gate: `EA3F537C723951BB0F768D7F89B7FF2D68522BE94456EE7016DB53A2D27C60DD`
- cleanup: `13C9D2C4D1526933BB3A4B283BA2D16188168AFC51F262F5DC568A8E603F1FEA`
- driver-state: `E1A371641FAD29EDD376EF22DD231BE526D685822FE88B7452ADC79F76788F0A`
- vanilla event: `013A6B602C8C344D27944D99020D1DA11E088C00354A542A97C0AE96FED0401B`

R72 failed after a finalized GREEN loader, not during load. It adds no
file-size/performance RED and triggers no effect split.

## R73: unavoidable fragile-bones acknowledgement

R73 ran from committed `d0212c1` against the unchanged product. The finalized
loader and managed cleanup were GREEN. It drained B2 PIP,
`spymaster_task.0381` and `zg361.40`, then stopped before action at previously
unregistered vanilla `health.7500`, raw date `53152296`, instance `16`, root
`29037`. The new top-level `unexpected_event` evidence worked as designed:
the artifact itself contains zero saved scopes, one shown/enabled native
option 0, and the `fragile_bones` add-trait indicator. R72's `.9006` did not
recur, so that contract remains live-pending.

Exact `health_events.txt` proves that `.7500` has one option whose sole effect
is `add_trait = fragile_bones`; the health pulse source selects it as an
age-related ailment. There is no alternative branch. The runner now binds the
exact date/root/zero-scope/one-option frame and acknowledges authored option
1/native index 0. An extra scope or option drift remains RED. Focused
checkpoint tests pass 10/10 in normal and `-O` modes.

R73 reached raw date `53152296` (D+220). Its final error log contains one weak
Character `has_variable` error, but the complete source chain is vanilla
`tribute_mission.0001`; there are zero references to
`zg361_b1_runtime_effects.txt`. The accompanying invalid court/province errors
are from the same vanilla event. They are not attributed to the product and
do not justify changing the mod. The absence of product-file weak-scope errors
through D+220 is useful partial evidence, not the still-missing 550-day B1
closure.

Frozen R73 SHA-256:

- outer report: `DF77359176D13828123560BC4706BBF069B7F13182CC5D609F6E32DF58C5DFB3`
- evidence index: `78A91B3140714FCEDC6EFC0EC7E2DD82CECE29671C0E4847C49275946AD88BDD`
- promotion entry: `6026F19099FC0213E4FE9F7A99E3C122714F17265CCA917D3790A1AF5043076E`
- loader gate: `122E3E3A450A83002164763B6A8B46F80C67FDD697E2F48B7376B3A8E9D1095B`
- cleanup: `6F5FB9EA682F42BA2A051654F8EBB5B3DDB561454D4EE6C67F4A1CD117235AE0`
- vanilla health events: `8CAB7F230E09A37C15F7C088383D40752D970918D44D86762FDD068EE168EFEB`

This is another post-loader event-choreography stop. It adds no
file-size/performance RED and triggers no effect split.

## R74: first full product-error inventory and mechanism policy card

R74 used committed `4adf315`, the unchanged 636-file `Z:\p2ad\p` product,
and exact CK3 1.19.0.6. R73's `health.7500` acknowledgement passed: the run
continued beyond D+220 and reached December 1067. Frontend, final loader,
unique mount, protected storage, source/product immutability and managed
cleanup were GREEN; no CK3 process remained. The run then stopped before
action on previously unregistered product event `zg361m.1`, raw date
`53156376`, instance `19`, root `29037`, with three shown/enabled native
options `0/1/2`.

The exact generated source defines this as mechanism 001's player policy
card. Every branch writes a bounded ledger; option A is the reference charter
and is also the product's deterministic default. The runner contract therefore
binds the product observation window, exact root and three-option shape, then
selects authored option 1/native 0. Twenty-three inherited B1 ticket scopes are
not consumed by this event and remain opaque instead of being mislabelled as
mechanism inputs. Wrong root or option shape stays RED.

Unlike R67–R73, R74 also reached enough product execution to expose a real
post-loader error inventory. The actionable families are:

- no-current-liege reads in the KPI values and current-review trigger;
- stale weak Character reads at `.101` and late publication consumers;
- optional huddle, departed-grade and Central portfolio fields read before
  their variables exist, because CK3 trigger lists do not short-circuit;
- six Career/HC dual-payment mechanisms using a negative `add_gold`, which
  CK3 1.19 rejects at runtime;
- `ordered_in_list` capping caused by the processing count/list drifting after
  a weak Character disappeared.

The minimal static repair now guards `liege` before context switches, nests
presence gates before value comparisons, rebuilds both manager-owned Character
lists at each observed delayed consumer, updates the processing count from the
rebuilt list, and uses `remove_short_term_gold` for real debits. The same
engine-proven negative-`add_gold` form was removed from Career Learning too.
Generated files were rebuilt only through their four generators.

Focused results are checkpoint `11/11`, choreography `5/5`, B1 `64/64`,
Central `41/41`, Career/HC `42/42`, Career Learning `34/34` and scoreboard
`32/32`; generator parity, product-local validation and root static validation
are GREEN. Effect boundaries remain **428 files / 3721 effects / maximum
non-legacy 10 / target misses 0 / over-20 violations 0**. These are static
results; R75 must prove the error families absent in a fresh production CK3
run.

Frozen R74 SHA-256:

- outer report: `E35572FB4E654CF0821188D967A8F7428CFCF710D823B51006721EA404F5CC31`
- evidence index: `1C3F7BFF766289AC7CD3A3D41B0237063697C7EEA184FF625FA29F95070CA124`
- cell report: `180722211C636A6A6AA8FDECD7A32DC905C9D95BA91E1CE13D0DD54B6C27F1A2`
- loader gate: `7771D01A078E4E3139E1C338FC2BFA34431F298490269E73440E3CA167098983`
- promotion entry: `5A7B424E8C382848F106BCCD6E53D9ABA6B5710EC828B76FCCC2C4C2A0333F0B`
- cleanup: `C6D5D682AEEAED44599CD7E7E1579D4B6404C5C727AD9F3BA488EF30D59547AD`

The largest loaded mechanism event/effect sources were still 429,368 and
1,019,397 bytes. They loaded normally, and the first actionable errors arrived
only during gameplay. R74 is therefore further negative evidence against file
size as this run's cause. No performance-driven split is triggered; the B2+
purpose-shard limit remains independently GREEN.

## R75: loader performance RED and boundary-only fallback trigger

R75 used committed `5b696f7` and the fresh 636-file `Z:\p2ae\p` product
projection (`98db471b68c3734108c2ee0f5428d4db49406072397e02a1a6b7a8a88a6ce668`).
The generic promotion entry preflight and projection generation were GREEN,
and CK3 1.19.0.6 started under the managed supervisor as PID `64232`.

This time the 300-second loader gate returned `RED / loader_stage_timeout`.
All 303 database callbacks completed and history loading ended, with
`CJominiInGameMusicDatabase` as the last callback (`10 ms`), but no database
completion publication, post-init, Frontend, Load Save, In Game or native
readiness followed. Elapsed time was `299.745s`; callback-completion quiet time
was `183.784s`. Fatal and theme-warning counts were both zero. Cleanup and
protected-storage checks were GREEN and no CK3 process remained.

Because R75 never entered gameplay, it is inconclusive for the R74 runtime
error regression: no liege/weak-list/optional-field/negative-gold family may be
promoted on this attempt. It is, however, a genuine load-performance RED and
therefore triggers the previously prepared boundary-only A/B fallback.

Frozen R75 SHA-256:

- outer report: `A48246F29F8373C4C2FDBB5C8BAD8922C4346FA75A0C6D1919F398ECFBC4AD2D`
- evidence index: `8395C211429A81B72E5DF5A41E0F8DC719663785AA556F0488EB103464676632`
- cell report: `8686E0B71F856C9C2F4BE998DA5C8C967577A231318A7F6C568C3A45960021DD`
- loader gate: `5EFD65FDB519239EB7A1764A944EA1A89275D16F2E0E21F96D22435959EC29D7`
- cleanup: `996598774A9E3B24B6147A1BFD6472AA9D677931A7AACCCE68FB90C8305CE447`
- final error log: `F3CAF5C41C4808F4FA4FE1AAD4E8052D491E19B636C65451C217174FD765EE2E`

The refreshed boundary tool recognized the new
`zg361_b1_prune_unavailable_subjects_effect` as part of the cycle/self-review
purpose group, bringing that shard to exactly 10 effects. It materialized
`Z:\p2af\p` from the exact R75 product without changing an effect body: three
legacy owners were replaced by 198 purpose shards, producing 618 effect files
and 3,708 parsed definitions with maximum 10 per file, zero target misses and
zero over-20 exceptions. The definition-surface and call-graph digests are
`622010396d1e0f71d06eabb91d83dd736b187f103fe3274a66d1e85dee2b2c29`
and `c774a0da4c2752f0ec191add1be3e587f3eafc57f3db400b82c4cf2f8617072e`.
The sidecar SHA-256 is
`A07E065DBA90CEBB486ACF854153AF9B0D3E89AF4E8A006DE1CFF12E7999A393`;
the 831-file R76 projection tree is
`e842e6967d754c8e6f5d46ac3ed9ad045d86abfac6f0273d160e8c3883000289`.
R76 must now determine whether this current-tree split clears the loader gate;
the older ABBA experiment remains negative evidence against declaring file
size the root cause from a single run.
