# G2 readiness and offline preflight audit (2026-09-02)

This is a non-authoritative handoff note.  The frozen ABI/source contracts and
the existing live-artifact indexes remain authoritative; this note does not
change a policy, hash chain, readiness bit, or action boundary.

## Frozen scope

- CK3 build: `1.19.0.6`, executable SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Integration candidate audited: `integration/promo-g2-20260901` at
  `0147d455ccb4c2f07d757b1e927d999cab350e05`.
- Readiness-report diagnostic patch: `fcb1b3f1bd10a5b7c89753976eabf3b3b7ed0923`
  (`Preserve native readiness timeout evidence`).  It preserves bounded
  transport/heartbeat evidence on a timeout and does not promote readiness.
- This audit launched no CK3 process, loaded no native bridge, and performed
  no MCP write or save mutation.

## What is currently deliverable

| Slice | Current status | Evidence and boundary |
| --- | --- | --- |
| Typed `call_ally_interaction` war target | `static/query-ready`; not paused-live and not action-ready | The exact `type_index=16`, `type_key=war` full-generation WarID resolver is covered by native source-contract, mailbox, and Python contract tests. It only observes a target; it does not select a reply, submit `call_ally`, resolve terms, or authorize an OODA action. |
| Raiktor truce leaf | `static/query-ready`; public `evaluated_days` wire is present; not production-live | `raiktor_surrender_truce_v1` is a pointer-only, same-frame, double-evaluation observer. `expiry_observable=false` and `expiry_date_raw=null` remain intentional. |
| Raiktor six-domain aggregate | `static/fixture-ready`; not public/live decision readiness | The aggregate can reject missing or cross-frame leaves and keeps claims base separate from the six dynamic domains. Synthetic completeness cannot authorize surrender. |
| Raiktor three-way policy | `static/fixture-ready`; `GEN-034` unresolved; action disabled | Campaign dominance, owner budget, and white-peace comparison providers are still unavailable. `recommended_outcome=null`, `production_recommendation_ready=false`, `full_exit_decision_ready=false`, `action_ready=false`, and `automatic_surrender_ready=false` remain the truthful values. |
| Native timeout evidence | Implemented in `fcb1b3f` | A persistent semantic-unavailable timeout now reports compact bridge diagnostics and a correctly classified `first_blocker`; it is a diagnostic improvement only. |

The clean MSVC/Ninja G2 regression covered the three pending-interaction
targets and the three Raiktor targets: 18/18 native build targets and 6/6
focused tests were green.  The generated CTest registry contained 71 tests.
The Cygwin `ctest.exe` found on `PATH` is not evidence: it prepends the
current directory to `Z:/...` Windows paths and reports `BAD_COMMAND`.  Use
the Visual Studio CMake `ctest.exe` or run the native executables directly.

## Existing readiness RED and its meaning

The retained phase-two attempt
`phase2_seed_20260901_042407_head_48fbe07_attempt07` is the current bounded
counterexample to “just wait longer”:

- `bootstrap-event-wait.jsonl` has 8,916 observations.  The first and last
  rows are `semantic_snapshot_temporarily_unavailable` with
  `BridgeUnavailableError`; the last elapsed value is `899.963` seconds.
- Final cleanup is GREEN and proven.  Transport and heartbeat were connected
  (`bridge_pid=70092`, heartbeat sequence `3601`), but
  `semantic_state_available=false`, `snapshot=false`, mailbox
  `installed=false`, `ready=false`, and `pump_epochs=0`.
- The result is a capability/harness RED at the semantic-readiness boundary,
  not evidence that a truce action is safe or that the native bridge should
  be admitted by a longer timeout.

## Smallest next readiness dependency

The next G2 gate is one MCP-first, read-only paused truce-shape artifact.  It
must be attempted only after a fresh exact-build session reaches semantic
native readiness; the attempt above must not be replayed merely with a larger
timeout.  The artifact should contain, in one paused frame and a second
identical read:

1. exact full-generation WarID, `raiktor_claim_cb`, attacker/defender/claimant
   roles, connection/episode/PID provenance, date, and native/public revision;
2. the pointer-only `CAddTruce` shape and two equal non-negative
   `evaluated_days` values; and
3. unchanged paused snapshot identity after the second read, plus an
   append-only report and SHA-256.

This closes only the truce observation leaf.  It does not close expiry,
dynamic terms, campaign/owner/white-peace providers, the six-domain aggregate,
or any surrender/white-peace write.  Until that artifact exists, retain
`static/query-ready` and `GEN-034=unresolved`.

### Probe contract prepared (static, not live)

The narrow gate is now executable as a report check through
`ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_truce_probe.py`.
`run_war_termination_terms_live_acceptance.py` records its result under
`mcp_sequence.truce_probe_checks` and binds the frozen
`raiktor_surrender_truce_v1_source_contract.json` pointer shape. The check
requires two queries on one paused revision, exact WarID and
attacker/defender/claimant roles, exact-build provenance, equal non-negative
`evaluated_days`, and an explicit no-write boundary. It rejects
`surrender-war-*`, `offer-white-peace-*`, and `enforce-demands-*` steps.

Static contract tests:

```powershell
$env:PYTHONPATH = 'ck3_autonomous_player/src'
py -3.13 -m unittest ck3_autonomous_player.tests.unit.test_raiktor_truce_probe -v
```

These tests use synthetic payloads and the frozen source contract only; they
do not create a CK3 process or promote the gate to `production-live`.

## Executable open_kaishek preflight entry

`open_kaishek` is an optional offline accelerator, not a CK3 readiness gate.
The canonical checkout is `Z:\workspace\open_kaishek` on `main` (also
`origin/main`), at commit
`1c320ad` (descendant of the preflight
contract commit `b306a95`).  Bind the checkout and jar explicitly, then run a
fixture-only smoke before any future parent acceptance command:

```powershell
$kaishekRoot = 'Z:\workspace\open_kaishek'
$kaishekJar = Join-Path $kaishekRoot 'kaishek-cli\target\kaishek-cli-0.1.0-SNAPSHOT.jar'
$java = 'C:\jdk-21\bin\java.exe'

# Build with a writable Maven repository when the default C:\.m2 is unavailable.
# The build is optional if the jar was already built from the bound commit.
mvn -o -ntp -Dmaven.repo.local='Z:\ck3_mod_rewrite\_g2-maven-repo' `
  -f (Join-Path $kaishekRoot 'pom.xml') -DskipTests package

& $java -jar $kaishekJar preflight `
  --profile ck3-1.19.0.6-zg361 `
  --fixture synthetic-361-014
```

The command emits one JSON object with schema
`open_kaishek.preflight.v1`; expected fixture status is `GREEN`, with
`provenance.mode=offline`, `ck3_started=false`, `save_mutated=false`, and
`network_used=false`.  The canonical rebuilt CLI jar SHA-256 is
`F01C9D5FD0095960AC58E20031F22A3A28F0AFA5B0716C4D3DBECE49583C8A1A`;
record that SHA together with the resolved checkout commit.  Older local
jars (`A14644331FBBA16E1DDA0B84DCB81F24D39F98CE25702E42ADED93D63FFA9398`,
`47E20B1B3814A5CFBC4CCF7347C0C5CF0128961991FD8436BE2C00701AA969E6`
and `6E8D9CECCAAA2CCF925B369501919C5B8F15AA73F1C9CB78ACEAF52540EE3E91`)
are superseded and must not be used as current provenance.

For the loader boundary, the intentionally RED diagnostic fixture is:

```powershell
& $java -jar $kaishekJar preflight `
  --profile ck3-1.19.0.6-zg361 `
  --fixture ck3-calculated-value-014
```

Its expected diagnostic is
`CK3_TRIGGER_CALCULATED_VALUE_UNSUPPORTED`; `RED` here is useful evidence of
an offline syntax boundary and must not be converted to a CK3/live failure or
success.  A full mod tree may also be RED because the profile is deliberately
bounded.  Archive the JSON and jar/checkout provenance, and keep the later
native/live result in a separate artifact.

## Handoff decision

No additional native code or policy change is justified by the current
evidence.  The next implementation entry is the semantic-readiness diagnosis
needed to obtain the single paused truce shape artifact; once that artifact is
available, extend only the corresponding typed read path and its evidence
contract.  Do not enable surrender writes, infer expiry from
`evaluated_days`, or use a fixture-only preflight result as live evidence.

## 2026-09-02 artifact inventory refresh

A read-only inventory found no new paused truce artifact. The latest three
`xar-g2-truce-paused-live-*` attempts remain RED (preflight/harness or native
readiness failures) and contain no MCP terms sequence. The reusable frozen
pair is checkpoint
`C:\Users\xenoa\AppData\Local\Temp\xar-g2-altseed-after-embarked-fix-20260831-0937\profile\save games\xar_checkpoint.ck3`
(SHA-256
`60108A5DA03DC3A8315A3E79897D9CF2F49763910A8AA15A462E7DD0B6AAF164`) and
driver state SHA
`4FB901C77AF6D95A05EAB2B0E900AE2E07A652B4C14729835DECB69FC8CFF57E`.
The known-good older launch reached paused/map-ready but did not advertise
`query-war-termination-terms-v1-50331699`, so it cannot be reused as truce
evidence. The next live command remains the existing
`run_war_termination_terms_live_acceptance.py` entry with WarID `50331699`,
character `29829`, and `date_raw=53223936`; it must run open_kaishek offline
preflight first and must stop at the existing capability/readiness boundary
if no semantic native-ready frame is available. No code or branch changed in
this inventory.

## 2026-09-02 current offline accelerator

The canonical `open_kaishek` checkout remains `main == origin/main` and is now
at `19ff306cd902978dac43a56377720be874c51cb8`. The rebuilt JAR is pinned by
SHA-256 `3DF2B4463EDC1D732DE1FAA85CE2803F8995DEAE1640D5F2D93001FEE53174C2`.
This is an evidence-backed parser performance-only slice (six precompiled
`Pattern`s); it preserves parser semantics and diagnostics and has passed the
Maven, parser self, phase-one syntax, and 760-case fuzz suites. On the frozen
parent source, a fresh-copy preflight artifact
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postschema-preflight-19ff306-clean\preflight.json`
(SHA-256 `004AD71FD182590FAB7A8EE932BFE58536E42B98A32D476734293E6B614F248F`)
is `GREEN/preflight-ready` with `ck3_started=false`; the profile validator's
`RED/233,115` schema-only boundary and the blocked seed-contract status remain
explicit. This accelerates the next G2 offline step but does not add a paused
truce artifact or change `GEN-034` readiness.

## 2026-09-02 bridge capability gap refresh

A read-only bridge review confirms that the exact-build bridge already exposes
the generic termination options, the pointer-only
`query-war-termination-terms-v1-N` shape, and mechanically implemented
`surrender-war-N`/`offer-white-peace-N` commands. The upper layer must still
keep those writes frozen until the claim-exit-terms contract and campaign
readiness are proven. `ReadWarTerminationExitTerms` is explicitly disabled
with reason `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668`;
there is no evidence-supported field to re-enable by inference.

The reusable paused/map-ready report's concrete gap is
`exact_build_proof.checks.action_step_family=false`: bridge/hello capabilities
are present, but the driver did not advertise the literal
`query-war-termination-terms-v1-50331699` action step, so no MCP sequence ran.
Current contract coverage passes `17` tests / `51` subtests for the double-read,
pointer-only `CAddTruce` shape, expiry-unobserved boundary, and write rejection.
No code or branch changed in this review. The next G2 entry remains one fresh
exact-build semantic-ready run using the frozen checkpoint/driver pair; if the
literal action family is still absent, fix only its bridge/driver advertisement
without widening the ABI, otherwise stop at the existing readiness gate.

The current Python action-step builder was also checked directly: when the
capability and `active_wars[{war_id:50331699}]` are present, it emits the exact
`query-war-termination-terms-v1-50331699` step. Therefore the historical
`action_step_family=false` is attributed to the older runner/DLL provenance,
not to a current Python generation defect; no speculative code change is made.

The diagnostic-only harness increment is now on the parent mainline as
`de4c7be` (`d1850b3` source). If exact-build proof stops before MCP, the report
retains the observed terms-query action-step literals, distinguishing the
template `query-war-termination-terms-v1-N` from the concrete WarID step.
The focused termination/exit-terms/live harness suite is `18 passed / 51
subtests`; CK3 was not started and no action authorization changed.

## 2026-09-02 current open_kaishek schema slice

The canonical `open_kaishek` mainline is now
`450b559c892228b6ab650c6fa68bece6defdfec7`. The short-lived
`feat/government-flag-schema-20260902` branch was fast-forwarded and deleted;
the remaining branches are pre-existing user work, so this slice does not add
branch debt. It adds the exact-build-backed scalar `government_has_flag`
descriptor and regression coverage without claiming runtime certification.
The rebuilt CLI JAR is pinned to SHA-256
`06E71C403924412A32EE307149AF6DB5E4A40886064263CF1FFDDE5615538C4D`.

The required offline preflight against the frozen phase2 source is retained at
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-government-flag-preflight-20260902.json`
(SHA-256
`6C4BEAC7FF87CA29B9481FB247CC4AD1E02350D279D9AA644C9A5D6661E28FDA`).
Parser is GREEN (`76` files, `23,831,410` bytes, zero diagnostics); the
validator is the known bounded schema-only `RED/233,014`, and no CK3 process
was started. This improves the next G2 preflight path only; it does not create
the missing paused semantic-ready truce artifact or change `GEN-034`.

## 2026-09-02 accelerator follow-up

`open_kaishek` is now on mainline
`a6705894bb41d87aa5e53530d77910369c6eb209` after the temporary
`has_perk` schema branch was merged and deleted. The rebuilt JAR SHA-256 is
`392B130B7F6DCB516627EAE284CF673C7F109D6857A5C6388AE56F02EC0BF1AD`.
The corresponding offline preflight artifact
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-has-perk-preflight-20260902.json`
(SHA-256
`F37560B6C0B3113C3B6F0EDE04368E9C5B57BE55F473938DCE7A2D355787E8E9`)
is parser GREEN (`76/23,831,410/0`) with the expected bounded validator
`RED/233,014`; CK3 was not started. This schema increment does not change the
G2 semantic-ready gate, action-step requirement, or `GEN-034` status.

## 2026-09-02 09:40 concrete termination action-step regression

Parent mainline now includes `a84c53d`, a focused regression at
`NativeProtocolState.capabilities()`. When the frame is paused and the active
war has a positive full-generation WarID, the hello advertises the concrete
`query-war-termination-terms-v1-50331699` action step; it must never advertise
the template `query-war-termination-terms-v1-N` as executable. The native
adapter/bridge focused suite passed `204` tests. This locks the
template-to-concrete boundary found in the old DLL provenance; it does not
authorize surrender/white-peace writes, widen the ABI, or create a paused
semantic-ready artifact. CK3 was not started and no repeated RED gate was run.

The offline accelerator is now `open_kaishek`
`757fb1b0d0b92fd234961f32e853f9cdef7069d1` with CLI JAR SHA-256
`D4BA0FF5E6A9C85ED0853FD78D44940E98445F2867E9D6CA5902AF0E19B29476`.
Its direct parent preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-dynasty-perk-preflight-20260902-adapter.json`
(SHA-256
`37A1B6788306FD7FF8C1DFBAEDE1BE44B5B26602CE7E85334FF6A8B042A14426`):
parser/root-scan is GREEN (`75/23,831,185/0`), fixture IR/runtime is GREEN,
and the bounded profile validator remains the expected RED (`233,014`). The
preflight is offline (`ck3_started=false`) and therefore leaves `GEN-034` at
`static/query-ready + paused/live=false`.

## 2026-09-02 09:55 open_kaishek DLC-feature schema slice

The accelerator mainline advanced to
`7da444d6afbeb98ec6c9d91da49535a43d55d0ce` with the exact-build-backed scalar
`has_dlc_feature` trigger descriptor. Its profile/validator coverage and
offline package are GREEN (12 profile tests and 22 validator tests); the JAR
SHA-256 is
`78AFD52B147874070813B5E77FA710B082065C6BB14EB3C9071A833BB0FEF2A9`.
The slice is syntax/profile-only (`certified=false`) and does not alter the
G2 action-step or semantic-ready gates. The full phase-two preflight reported
parser/IR/runtime GREEN and the expected bounded validator RED (`39,360`),
with no CK3 launch; its output was not persisted as a separate artifact.

## 2026-09-02 10:08 fresh semantic-ready terms probe

After the offline preflight, one fresh exact-build runner was executed with
the frozen checkpoint/driver pair. The retained report is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\report.json`
(copied from the managed temp attempt; SHA-256
`4A7C66D34C851698572F4BBA2970ECAA00C005C2DC338ABCD75A7FD304F0B991`). The
matching offline preflight is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\open-kaishek-preflight-mod-20260902.json`
(SHA-256
`5F7F67C439D8721E56C735E2DFA49E07A32630DD7019EB221C1C1215DD68AC90`).

All exact-build proof checks passed: the concrete action step
`query-war-termination-terms-v1-50331699` was advertised, and the paused
snapshot bound CharacterID `29829`, `date_raw=53223936`, WarID `50331699`, and
opponent `36769` at `native:3 / revision=4 / native_revision=3`. Both read-only
terms queries succeeded on the same frame, sequence `1 -> 2`, with normalized
payloads equal; gold, prestige, prisoner-release, and favor-hook domains were
ready. Cleanup was GREEN (`tree_gone=true`, `driver_closed=true`) and no write
action was sent.

The run remains RED only because the native truce row reports
`evaluated_days_observable=false` and `evaluated_days=null` (expiry is also
unobserved). Consequently `truce_ready=false`, `decision_ready=false`, and
`GEN-034` remains unresolved. This is the first live evidence for the narrow
truce-duration observation gap, not a surrender/action authorization.

## 2026-09-02 10:24 open_kaishek schema follow-up

The offline accelerator is now clean at `bd980e787e8e64b64104b43542ae2afefe3e8a06`
with JAR SHA-256
`DCCCF51A8B68EEC6CCF8D391D7B0E839361DECB9E37098C31BBB78EB296247A1`.
The exact-build-backed `has_court_position=<court-position-key>` descriptor
passed `13/13` profile and `23/23` validator tests; its synthetic preflight
artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-court-position-synthetic-preflight-20260902.json`
(SHA-256
`B2183C32C18D0F7A6F00A8C96C2D0DEEAD7EAF8BFC358606F92415368E6674B7`). This
is syntax/profile-only (`certified=false`) and leaves the fresh live G2
result and `GEN-034` boundary unchanged.
