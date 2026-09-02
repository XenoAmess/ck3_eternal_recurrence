# ZhongGuo phase-two bounded gate (2026-09-02)

This is the one new exact-build bounded seed attempt requested for the phase-two
priority blocker. It is evidence, not a release claim.

## Frozen inputs

- Source: `8c7e9ceb5a5aadcbf82ac9632422e5972f83a412` (`origin/master` at gate
  start), including the China tutorial-prompt settings fix.
- CK3: `1.19.0.6`, executable SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Game tree: the project copy at `Z:\ck3_mod_rewrite\Crusader Kings III`
  (the Steam tree and overlay were not used).
- Bridge: `xar_ck3_bridge.dll` SHA-256
  `B018FB8C55E99E915E728166BBF1934518095CF4E4981114970FC0CEE69026F0` and
  injector SHA-256
  `8F4E9C6E36BA50B976909E3AC54B3B6A655F39EBED81F42993E517F0E40BF65D`.
- A fresh profile and named pipe were used. No prior checkpoint or Steam
  overlay was mounted.

## open_kaishek offline preflight

Artifact: `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\open-kaishek-preflight.json`.
The CLI was built from `open_kaishek` commit `b306a95`; the shaded jar SHA-256
is `1EA26AB19761CAB14EECA2E2D106B7353D9CBD606BA091D3C0EF8C67D2AA4A8B`.
The command used profile `ck3-1.19.0.6-zg361` and fixture
`synthetic-361-014`.

The preflight is intentionally layered: parser `GREEN` (root and combined),
synthetic IR `GREEN`, and synthetic runtime `GREEN` (`execution=SUCCESS`).
The root/combined validator is `RED` with 92 `UNKNOWN_OPCODE`/
`WRONG_DOMAIN` diagnostics because this profile is explicitly
`schema-only`; it does not certify full CK3 semantics. Overall CLI exit is 1,
so this must not be reported as an overall offline `GREEN`.

## Gate attempts and result

Two launch-boundary setup failures are retained separately:

1. System `py` stopped before CK3 because `pyautogui` was unavailable.
2. Project virtualenv had `pyautogui 0.9.54`, but the first retry used a pipe
   name outside the runner's required 32-lowercase-hex contract.

Neither setup failure launched CK3. The final contract-valid attempt used one
fresh profile and one fresh pipe. Its report is:

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\artifacts-final-8c7e9ceb\runner-report.json`

Report SHA-256:
`75B939210DF1D502AA4B635159F776D9A143D9675A6954F73A787A5AF5EBF5B5`.

Result: `RED` at loader `database_init` (`event_wait_authorized=false`). CK3
did bind the native MCP pipe and the exact-build adapter reported a matching
build, but it never reached Load Save/In Game or a paused frame. No provider
query, seed capture, or capability claim was made. CK3 exited with code 1;
managed cleanup and driver close were `GREEN` and no CK3 process remained.

The loader recorded 15 fatal script diagnostics, all in the workforce fact
effects:

- `zg361_workforce_rehire_fact_effects.txt`
- `zg361_workforce_exit_fact_effects.txt`
- `zg361_workforce_normal_exit_fact_effects.txt`

The diagnostics are `Unknown trigger: value`, `add`, and `subtract` caused by
calculated-value blocks on trigger-side exact equality. This is a startup /
readiness RED, distinct from the previously known particle2 null-slot crash;
that crash was not repeated.

The runner also recorded six generated Python bytecode files during its static
preflight, making its source immutability after-check `RED`. Those files were
removed after the run; the retained report is not rewritten and therefore
continues to document that boundary accurately.

## Offline repair follow-up (not live evidence)

The three generator sources were repaired without hand-editing generated files.
Every trigger-side computed equality now uses the documented inclusive pair
(`>=` and `<=`) with the same calculated-value RHS; effect-side
`set_variable`/`change_variable` arithmetic was left unchanged.  Regenerated
outputs contain zero direct computed-variable equality guards in the affected
effects (the forbidden shape is `var:<name> = { value = ... add/subtract/multiply }`),
including the previously unreported #277 consume guard.

Focused generator contracts are green: rehire 25 tests, exit 26 tests, and
normal-exit 29 tests.  `tools/validate_static.py` is also green.  The bounded
offline parser pass using the same open_kaishek CLI produced `PARSED`, zero
diagnostics, and `roundTrip=true` for each repaired effects file; artifacts are
under
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postfix-parser\`.
The formal preflight's 92 validator diagnostics remain the declared
`schema-only`/`UNSUPPORTED` boundary and are not reclassified by this parser
pass.  No CK3 launch was repeated; a future loader gate must be separately
authorized.

## 2026-09-02 03:12 offline preflight refresh

After the narrow `open_kaishek` profile slice (`d207707`), the same product
root was preflighted with the rebuilt JAR
`CBCD5F868F5C46AA7B5A2C70E11705B978F95DE3437E0809D20A4139F62DD0E4`.
The machine-readable artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postschema-preflight-d207707.json`
with SHA-256
`570BB393FC84E3E87AE69141AF1D036FC63434BB410B9F99A17F197F032DC2D8`.
It completed in `3.144s`: parser `GREEN` (76 files, 0 diagnostics), fixture
IR/runtime `GREEN`, and bounded root validator `RED` (233,708 diagnostics).
This is an offline schema boundary, not a CK3 loader result; no CK3 process,
save, or network was used.

## 2026-09-02 03:16 delta isolation gate

The only follow-up CK3 attempt used a source candidate that was byte-identical
to the current parent tree except for removal of the 249-line d692 role-failure
block in `zg361_workforce_exit_fact_effects.txt`.  The candidate passed source
archive equivalence, static preflight, bridge identity, and exact-build
dependency checks.  Its source tree SHA was
`1b1db97883b4eb65b8a221aa888476587c19c5d71f808a3c82bb58da5fc37583` and the
source ZIP SHA was
`145b466757fec58ff7fbe3ab5c74cd807f9d9454447eadf90fbad7f948f27499`.

The retained report is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\delta-live-pre-d692-20260902\artifacts\runner-report.json`
with SHA-256
`9EA7AFBEBCD210997B77F794574E7D36FEE3CA1C700C02EE707FE7389F9DF460`.
It is `RED/LoaderStageTimeout` at `database_init` after `299.9s` (quiet
`141.194s`), with `fatal_error_count=0` and no Frontend, Load Save, or native
readiness.  The candidate also exposed one concrete dangling reference:
`Unknown effect: zg361_workforce_exit_fact_verify_role_failure_publish_effect`
at `events/zg361_workforce_exit_fact_events.txt:64`, because the removed block
owned that effect.  Therefore the removal is not a shippable fix and was not
merged.  Cleanup/driver close and external dependency immutability remained
GREEN; no further same-shape CK3 attempt is scheduled until a new compatible
stub or call-site change is statically prepared.

## 2026-09-02 03:24 compatibility-candidate closure

The proposed compatibility follow-up was checked offline against the retained
delta tree and was intentionally not merged. Removing the d692 role-failure
block leaves the event call at
`events/zg361_workforce_exit_fact_events.txt:64` pointing at the undefined
`zg361_workforce_exit_fact_verify_role_failure_publish_effect`. A no-op stub
would hide that parser symptom but would fail generated-output parity and the
role-failure contract tests (4 exit tests fail); removing the call leaves the
same parity/semantic failures. The intact generator output parses cleanly
with open_kaishek and `tools/validate_static.py` is GREEN, so this candidate
does not explain or repair the independent `database_init` timeout. No
production source or branch was changed. The next phase2 code change must be
an evidence-backed loader/readiness fix, not a compatibility stub for this
invalid delta.

## 2026-09-02 03:28 evidence-backed schema increment

`open_kaishek` mainline `1c320ad` adds only the two scalar triggers already
marked `[static-confirmed]` in the exact-build ledger:
`has_game_rule` and `has_character_modifier`. Its rebuilt JAR is
`F01C9D5FD0095960AC58E20031F22A3A28F0AFA5B0716C4D3DBECE49583C8A1A`.
The retained offline artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postschema-preflight-1c320ad.json`
with SHA-256
`A63212B2F5BFAE1FEFE280DEAC1D75D77720A13BD5A46430876094D86D294F22`.
Parser and fixture IR/runtime remain GREEN; the bounded validator is RED at
`233,115` diagnostics, 601 fewer UNKNOWN diagnostics than `d207707`. The
eight additional WRONG_DOMAIN diagnostics are existing SCRIPTED_VALUES
coverage boundaries, not a schema expansion. Focused profile/validator Maven
tests and the CLI preflight passed; CK3 was not started.

## 2026-09-02 04:06 projection bisect and loader diagnostic

Before another CK3 launch, the current `a89282d` tree was projected offline by
removing the three largest generated workload clusters one at a time. The
index and all manifests/reports are retained at
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\projection-bisect-20260902\index.json`
(SHA-256
`6582011DE1AB4E6826194036D243A656DF12C8454C582B35538A77F9F4FFE078`).
The intact projection parsed `76` files with zero diagnostics. Removing
`scoreboard_snapshots`, `workforce_endgame_runtime_effects`, or
`scoreboard_slots` individually also parsed with zero diagnostics, but each
removal is semantically incomplete and is not a release candidate. Their
validator diagnostic counts were respectively `202,210`, `174,861`, and
`231,691` (intact `233,115`).

One additional diagnostic projection kept every endgame effect name while
replacing only the generated endgame bodies with a symbol shell. This was a
loader experiment, not production source: the expected filename was restored
in a clean full tree, and the shell candidate was preflighted with
`open_kaishek` before CK3 launch. The clean source tree SHA was
`eb31cbb234fc0025984b11d8692a27401c0cf4f7ec1349504f66ca0a7ebd3bf9`; the
source ZIP SHA was
`BF7E969A0610957F8B3FD8FEACFF379AD89BF1B5B5AD76CB4D1850C8BD8A6F87`.
The preflight was structurally `GREEN` (archive equivalence, parser, fixture
IR/runtime, static checks, and exact-build dependency identity), while the
bounded profile validator remained the known schema-only `RED` boundary;
`ck3_started=false` for that offline step. It used `open_kaishek` `1c320ad`
and JAR SHA
`F01C9D5FD0095960AC58E20031F22A3A28F0AFA5B0716C4D3DBECE49583C8A1A`.
The retained preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-shell-gate-20260902\artifacts4-live\open_kaishek-preflight.json`
with SHA-256
`9484DD60C6B0A170F5394455D68199A77740FF4A4833DCC44DBFB7F4338EEA8D`.

The single live diagnostic then returned `RED/LoaderStageTimeout`:
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-shell-gate-20260902\artifacts4-live\runner-report.json`
(SHA-256
`3549502304DD58AB39AE553B546F6A5331CD1778F03027C71B03BA04C7D3A0C8`).
It stayed at `database_init` for `299.962s` (`quiet_seconds=195.089`), with
`fatal_error_count=0`, `event_wait_authorized=false`, and no Frontend, Load
Save, In Game, or native-ready frame. The debug log still ends at
`onaction >>> Total of : 881`; the symbol shell did not move the transition.
Therefore the shell is not a fix and was not merged. No second same-shape CK3
attempt is planned.

The runner's post-run source immutability check was `false` only because six
Python bytecode files were emitted during the run; the retained report records
that fact and the clean source content itself was not changed. The six files
are environmental artifacts, not a production-tree mutation.

The combined evidence narrows the next implementation step to a real,
generated-source effect-cluster decomposition or equivalent loader/readiness
repair that preserves all generated symbols and contracts. A no-op shell,
blind file deletion, timeout extension, or bridge-scope expansion is not an
acceptable substitute. All diagnostic artifacts and the failed attempt are
retained for comparison; no production tree was changed by this gate.

## 2026-09-02 04:31 `open_kaishek` performance/current preflight

`open_kaishek` mainline is now `19ff306cd902978dac43a56377720be874c51cb8`
(`main == origin/main`). The six static `Pattern` replacements are semantics
preserving and cut the bounded corpus warm-parser time from about `1066ms` to
`421ms`, parse+validate from about `1240--1300ms` to `574--610ms`, and a fresh
CLI preflight process from about `2.65--3.10s` to `1.43--1.49s`; its focused and
full Maven/parser/fuzz tests are GREEN. The new JAR SHA-256 is
`3DF2B4463EDC1D732DE1FAA85CE2803F8995DEAE1640D5F2D93001FEE53174C2`.

Before any further CK3 launch, a fresh copy of the `a89282d` source was
preflighted with that JAR. The parent artifact
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postschema-preflight-19ff306-clean\preflight.json`
(SHA-256 `004AD71FD182590FAB7A8EE932BFE58536E42B98A32D476734293E6B614F248F`)
is `GREEN/preflight-ready`: parser `76/23,831,410/0`, IR/runtime and static
dependency checks GREEN, `ck3_launch_attempted=false`. The profile validator is
still the known schema-only `RED/233,115`, with
`seed_contract_status=blocked_seed_generation_required`; this is not a CK3
capability result. A prior stale-`pyc` RED attempt is retained as environment
provenance. The live loader RED at `database_init` is unchanged; no new CK3 run
is justified until the generated-source decomposition candidate is reviewed.

## 2026-09-02 04:52 generated effect-cluster gate

The evidence-backed decomposition candidate from `a1177f1` was integrated as
`041fd68` and preflighted before launch. It split the workforce/endgame
effects into 14 ordinary CK3 files while retaining a byte-identical offline
aggregate (`4,636,271` bytes; candidate aggregate SHA-256
`926453fe4b3621b5381743d61f5d03ac29c1d498181702e05a9532739d334d8a`). The
fresh preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\cluster-split-041fd68\artifacts2\preflight.json`
(SHA-256 `3DBA85267D901DEF2DF9ACDBF1518F17DA6FE8EC972ECDB75E1BA65F4FDC95D5`).
Its archive/tree equivalence, parser (`89` files, zero diagnostics), IR/runtime,
static checks, and local/release checks were GREEN; the profile validator
remained the explicit schema-only `RED/233,115`, and no CK3 launch occurred in
that preflight.

The one permitted exact-build gate for that changed layout is retained at
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\cluster-split-041fd68\artifacts3\runner-report.json`
(SHA-256 `FDF3A172C6BED99221B48446577F47535F7B036111826F9B2A8D79D7C7D7D115`).
It returned `RED/LoaderStageTimeout`: `database_init` was observed, then
timed out at `299.915s` with `quiet_seconds=207.595`, zero fatal errors, an
empty `error.log`, and no Frontend/Load Save/In Game/native-ready frame.
Source and external dependencies remained unchanged. Since the file-layout
change did not move the loader transition, it was reverted immediately by
`e4a964a`; the candidate and failed run remain retained as diagnostic evidence.
No same-shape retry, timeout extension, or deletion/no-op workaround is planned.

## 2026-09-02 04:58 loader dependency observability

The loader harness now records two read-only fields in each progress snapshot:
`database_node_count` and `last_database_node` (`7413346`). Stage classification,
event authorization, timeout budgets, and bridge behavior are unchanged; the
offline fixture test remains GREEN. Applying the parser to retained logs gives
the first concrete phase boundary: the older successful run reached `303`
`database_dependencies.cpp:433` nodes and ended at
`CJominiInGameMusicDatabase`/`in_game`, while the current `a89282d`, shell, and
reverted-cluster runs each reached only `2` nodes and ended at
`CJominiLoadScreenDatabase`/`database_init`.

The extracted comparison is retained outside the repository at
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-node-inventory-20260902.json`
(SHA-256 `808328DCFA319ED3CC327F8AE201A5D6F0C269343768EA342688CF34EBE6D185`).
This is a new observation boundary, not a root-cause claim; it supplies the
acceptance criterion for any future generated-source repair. No additional CK3
launch was made.

## 2026-09-02 05:01 dependency inventory and schema preflight

The retained dependency inventory now covers the `24` changed production
script/event/gui files. Its report is outside the repository at
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\dependency-inventory-20260902\report.json`
(SHA-256
`8E2C811BC95DE60ED37700DF6692979B677E909064B36C73688A6655E6CF697A`). The
focused graph has `1,656` definitions and `2,764` edges, zero duplicate
business definitions, and no actionable newly unresolved call-like symbol;
the only corpus duplicate is the generic GUI `window` container. The largest
size deltas are the B2 resolver and scoreboard/workforce endgame snapshots.
This does not justify another loader gate or a speculative resolver rewrite;
the baseline remains frozen until a concrete dependency node/file/symbol
change is observable.

The current `open_kaishek` mainline is
`450b559c892228b6ab650c6fa68bece6defdfec7`, with CLI JAR SHA-256
`06E71C403924412A32EE307149AF6DB5E4A40886064263CF1FFDDE5615538C4D`.
Its direct preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-government-flag-preflight-20260902.json`
(SHA-256
`6C4BEAC7FF87CA29B9481FB247CC4AD1E02350D279D9AA644C9A5D6661E28FDA`):
parser `76/23,831,410/0` is GREEN, while validator/root scan remain the
bounded schema-only `RED/233,014`; CK3 was not launched. The temporary schema
branch was merged and removed promptly, leaving the open_kaishek mainline
with only its pre-existing user branches.

## 2026-09-02 05:20 open_kaishek `has_perk` schema slice

`open_kaishek` was fast-forwarded to
`a6705894bb41d87aa5e53530d77910369c6eb209`; the temporary schema branch was
merged and removed immediately. The exact-build-backed scalar character
trigger `has_perk` now has profile and validator regression coverage. Its CLI
JAR SHA-256 is
`392B130B7F6DCB516627EAE284CF673C7F109D6857A5C6388AE56F02EC0BF1AD`.

The retained preflight artifact
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-has-perk-preflight-20260902.json`
(SHA-256
`F37560B6C0B3113C3B6F0EDE04368E9C5B57BE55F473938DCE7A2D355787E8E9`)
reports parser `76/23,831,410/0` GREEN and validator/root scan
`RED/233,014`; CK3 was not launched. The phase2 corpus contains no
`has_perk` use, so this slice does not reduce the current validator boundary
or change the frozen loader diagnosis. No new CK3 gate is scheduled.

## 2026-09-02 05:24 node-to-source localization closure

The read-only localization pass confirms that the existing loader parser can
reliably expose only `database_node_count` and `last_database_node`. CK3 debug
node lines contain the native database node name and timing, but no production
script filename or callback, so an offline parser cannot map the stall to a
changed file. The retained current log has `2` nodes ending at
`CJominiLoadScreenDatabase`; the older successful log has `303` ending at
`CJominiInGameMusicDatabase`. The loader-node inventory SHA remains
`808328DCFA319ED3CC327F8AE201A5D6F0C269343768EA342688CF34EBE6D185`, and the
dependency inventory remains `1,656` definitions/`2,764` edges with zero
actionable unresolved delta (SHA
`8E2C811BC95DE60ED37700DF6692979B677E909064B36C73688A6655E6CF697A`).

No new instrumentation or same-shape CK3 gate is justified. The next phase2
施工入口 is a loader-side callback/node observation that supplies a concrete
file or symbol; until then the `a89282d` baseline stays frozen.

## 2026-09-02 09:40 offline candidate closure and accelerator refresh

The frozen `a89282d` mod corpus was preflighted once with the current
`open_kaishek` mainline `757fb1b0d0b92fd234961f32e853f9cdef7069d1` (CLI JAR
SHA-256
`D4BA0FF5E6A9C85ED0853FD78D44940E98445F2867E9D6CA5902AF0E19B29476`).
The retained artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\static-candidate-mod-preflight-20260902.json`
(SHA-256
`1EC2D07D2ADD278C61BDE98F3536364C77282DA4D6BD7CE6D005EF2A98EB21A1`).
Parser/root scan stayed GREEN (`76` files, `23,831,410` bytes, zero
diagnostics), fixture IR/runtime stayed GREEN, and the bounded validator
remained the known schema-only RED (`233,014`; `zg361_jingcha.txt` unknown
opcodes). The run was offline and did not mutate a save or start CK3.

The same pass re-used the retained 24-file dependency inventory
(`1,656` definitions / `2,764` edges, zero duplicate business definitions;
report SHA-256
`8E2C811BC95DE60ED37700DF6692979B677E909064B36C73688A6655E6CF697A`).
The generator/phase2 wiring suites (`577 + 43` tests) were GREEN. There is no
evidence-backed source/effect change that explains the `database_init` stop,
so no speculative generated split or same-shape CK3 gate was added. The
baseline remains frozen; the next actionable entry is still loader-side
callback/source-context observation.

The `has_dynasty_perk` schema slice in `open_kaishek` is syntax/profile-only
and has zero occurrences in the frozen phase-two root, so it does not reduce
the loader RED or change native readiness.

## 2026-09-02 09:46 typed loader-node context

Parent commit `a5c079e` extends `tools/zg361_phase2_loader_stage.py` with a
read-only `database_nodes` list and `last_database_node_detail`. Each entry
preserves the timestamp, native source line, node name, initialization time,
and inclusive dependency time while retaining the existing count/last-node
scalars. The focused loader fixture test is GREEN. This is an observation
join key for a future loader-side callback probe; it changes no stage,
timeout, event authorization, or CK3 launch behavior. Re-parsing the retained
logs still yields `2` nodes for the current run versus `303` for the older
successful run, so the `a89282d` production baseline and native-readiness RED
remain unchanged.

## 2026-09-02 09:55 accelerator schema follow-up

`open_kaishek` subsequently advanced to
`7da444d6afbeb98ec6c9d91da49535a43d55d0ce` with the exact-build-backed scalar
`has_dlc_feature` trigger descriptor (`certified=false`). Focused profile and
validator tests (`12` and `22`) plus offline packaging passed; the new CLI JAR
SHA-256 is
`78AFD52B147874070813B5E77FA710B082065C6BB14EB3C9071A833BB0FEF2A9`.
The full phase-two preflight kept parser/IR/runtime GREEN and the bounded
validator RED (`39,360` diagnostics) without starting CK3. This schema-only
increment has no `has_dlc_feature` occurrence in the frozen phase-two tree and
does not change the loader diagnosis or native readiness.

## 2026-09-02 10:07 callback-location static closure

The exact CK3 1.19.0.6 binary scan now supplies a stable loader-side callback
anchor. Function RVA `0x3B9AB00` (pdata range
`[0x3B9AB00,0x3B9ACED)`) is the database-node initialization loop:
`0x3B9AB50` obtains the current node, `0x3B9AB53` checks `node+0x88`, and
`0x3B9AB90` calls `[rax+0x10]`, the per-node initialization virtual callback.
After the call, the loop reads `node+0x98` and the dependency chain at
`node+0xB8` to aggregate timing; the nearby format strings are
`Database Node Init Time...` (RVA `0x4558670`) and `PostInit - %s` (RVA
`0x4558648`).

This is a static exact-build observation point, not yet a bridge detour or a
production source-file attribution. It can expose native node name/timing in
a future read-only probe once the vtable slot semantics are closed. The
repeated `onaction.cpp:429 Total of : 881` remains non-discriminating, so no
`onaction_total` field is justified. No CK3 launch, ABI widening, or new gate
was added; `a89282d` remains the frozen phase-two production baseline.

## 2026-09-02 10:19 loader callback contract

The static callback anchor is now captured in machine-readable contracts on
parent mainline `56e786c` (source branch commit `7758b9b`, merged and retired):

- `ck3_autonomous_player/native_bridge/research/phase2_loader_callback_v1_abi.json`
- `ck3_autonomous_player/native_bridge/research/fixtures/phase2_loader_callback_v1_source_contract.json`
- `ck3_autonomous_player/tests/unit/test_phase2_loader_callback_contract.py`

The focused contract suite is `4/4` GREEN. It binds the exact executable,
loop range, callback vcall, node offsets, dependency timing, and format-string
RVAs while explicitly leaving callback return semantics, vtable slot meaning,
production script-file attribution, and production readiness as `unknown`.
This is a reusable static/fixture observation boundary only: it adds no bridge
detour, ABI field, timeout, event authorization, or CK3 launch.

## 2026-09-02 10:30 phase-two error-cluster closure

The retained frozen `a89282d` phase-two artifact has `error.log=0` and no
debug `[E]`/`[W]` entries; its loader reaches only two database nodes before
the bounded timeout. The large error sets in older attempts are stale
corpora, not a new current fatal: their unset-variable, unknown-trigger,
unknown-effect, `TICKET_STATE`, list-target, and persistent-key cases already
map to the historical fixes in `641e862`, `c79057c`, `e1d8ebf`, `bd5c795`,
`88095ba`, `32848a5`, and `dab001c`. The current source retains the B1 list
anchors, and the open_kaishek offline parser/fixture remains GREEN with only
the known bounded validator schema boundary.

There is therefore no evidence-backed script/generated-file edit to make in
this pass. The G2 fresh debug log (which completes the database-node list and
reaches paused state) further points to loader/native callback context rather
than current event/value/effect registration. Keep `a89282d` frozen and use
the new callback contract as the next observation entry; do not repeat the
same CK3 timeout or broaden the gate without a new file/symbol artifact.

## 2026-09-02 10:44 callback-stall telemetry and retained-log replay

Parent mainline `f20a88d` adds only read-only loader telemetry. Completed
`Database Node Init Time` rows are now exposed as callback completions,
`PostInit - %s` rows are retained as opaque records, and a callback-specific
quiet clock distinguishes loader progress from unrelated event/on-action log
traffic. Terminal RED evidence receives an additive `reason_code`; stage,
timeout, event authorization, and CK3 behavior are unchanged. The focused
loader test, optimized-mode test, seed-capture contract, and four callback
contract tests are GREEN.

The new parser was replayed once against the frozen `a89282d` logs without
starting CK3. The report is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-callback-replay-f20a88d\loader-stage-replay.json`
(SHA-256
`56233A3CAF9062B347C1661132E3D16A419CF0698C69CB4C775214B47311E56D`);
its append-only progress SHA-256 is
`50F47B22B2BD373CC641B6CDC88ED576A95B4A658E9F3E186319255634C50631`.
It classifies the retained boundary as `RED/database_callback_stall`: two
completed callbacks, last node `CJominiLoadScreenDatabase`, zero fatal errors,
and `event_wait_authorized=false`. No retained `PostInit` record exists. This
narrows the observable stall category but does not identify a source file,
repair the loader, or upgrade phase-two readiness.

Before this replay, the planned next-entry corpus was run through the current
`open_kaishek` adapter once (offline only). The retained preflight is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\next-entry-open-kaishek-preflight-20260902.json`
(SHA-256
`4C7370C9E0F9E83FB2A6080C8A4AEB467F5F56A4AAD9AFEB46F7009C82FB8F9A`). It
reported parser `55/2,223,707/0` and fixture IR/runtime GREEN, with the
declared bounded validator RED (`39,360` unsupported diagnostics),
`ck3_started=false`, and no save mutation. This preflight was consumed as
offline evidence only and did not justify another same-shape CK3 launch.

## 2026-09-02 10:52 loader detour feasibility boundary

A short static bridge review found no safe reusable pre-loader callback detour
for the current exact-build anchor. The existing installers require proven
prologue bytes, calling convention, quiescence, trampoline/rollback, and a
process-lifetime observation sink; the loader callback currently has none of
those proofs, and the bridge has no safe post-loader uninstall lifecycle.
Existing private journals use preallocated atomics/rings rather than callback-
side file I/O. Therefore no detour, public ABI field, or CK3 rerun was added.
The next legitimate entry is offline closure of callback prologue/parameter/
thread evidence, followed by a separately opt-in private recorder only if
those prerequisites become concrete.

## 2026-09-02 11:17 telemetry live recheck

After the required current `open_kaishek` offline preflight, one new exact-build
read-only phase-two entry was run against frozen source `a89282d` with the
`f20a88d` loader telemetry. The retained report is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\phase2-live-recheck-20260902\artifacts-a89282d-f20-loader\runner-report.json`
(SHA-256
`187E1A438F0DCDE838BAC1AF02AAB878393BBAF999D704E3C9F2D843627FBBA9`). The
matching offline preflight is retained in the same attempt directory
(`open-kaishek-preflight.json`, SHA-256
`E18ECD37F2EC8AAA56BCE5CE271F968CB58CEF8ACACEB710E14D5001A272B8DC`).

The run reached the same loader boundary but now has native callback evidence:
`RED/loader_stage_timeout`, `reason_code=database_callback_stall`,
`elapsed_seconds=299.748`, two completed callbacks/nodes
(`CGameConceptTypeDatabase` 441 ms and `CJominiLoadScreenDatabase` 9 ms),
zero fatal errors, zero `PostInit` rows, and
`database_callback_quiet_seconds=286.430`. `event_wait_authorized=false`;
native readiness and all seed/event work were not entered. Managed cleanup,
tree removal, and driver close are GREEN, with no action or save write.

The report's `clean_source_unchanged=false` is isolated to six runner-created
`__pycache__` files in the clean export; product/runtime dependency hashes are
unchanged and the logs contain only four path-length warnings, not script
fatalities. This immutability defect is tracked for the next runner patch and
does not alter the loader diagnosis or upgrade phase-two readiness.

## 2026-09-02 11:00 open_kaishek `has_innovation` follow-up

Before any subsequent phase-two entry, the current accelerator was advanced
to `dad0ea2a864cbb4b9ea4a4e9dd388f606485830a` and its rebuilt JAR was pinned
to SHA-256
`478D2F4040316C5223470BB350AF286256D78ECA3EB7B413B0383EEF88B86911`.
The new `has_innovation` slice is exact-build syntax/profile evidence
(`TRIGGER/CULTURE/STRING`, `certified=false`) with no runtime evaluator.
Its current-adapter fixture-only artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-has-innovation-adapter-fixture-only-20260902.json`
(SHA-256
`A8F852B8586F0AEC3975B75E7A118105286C79E9E64D2C7E8D26EFAADAEA317B`).
The fixture parser/validator are GREEN with IR/runtime explicitly SKIPPED;
the companion full-root run retains the known bounded schema-only RED
(`232,973`). Both are offline (`ck3_started=false`, no save mutation). This
is an offline dependency check only and leaves the loader callback-stall
diagnosis and phase-two readiness unchanged.
