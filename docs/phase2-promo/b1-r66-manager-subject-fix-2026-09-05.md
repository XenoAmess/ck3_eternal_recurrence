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
