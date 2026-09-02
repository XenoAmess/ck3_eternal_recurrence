# G2 fresh semantic-ready run: offline preflight and gap sheet

**Recorded:** 2026-09-02 (Asia/Shanghai)  
**Scope:** one bounded, read-only preparation entry for the next G2
Raiktor-truce probe.  This document does not launch CK3, mutate a save, widen
the bridge ABI, or authorize a surrender/white-peace action.

## Current conclusion

The next G2 live entry is still blocked at the semantic-ready boundary.  The
Python action-step builder already emits the concrete WarID step when a
semantic snapshot contains the capability and the requested active war.  The
last reusable paused/map-ready evidence instead advertised only the adapter
template (`query-war-termination-terms-v1-N`), so it did not run an MCP terms
sequence.  The diagnostic-only change from `d1850b3` (merged as `de4c7be`)
now preserves that distinction in RED reports.  No additional code change is
justified by the current evidence.

## Frozen identity to bind before a fresh entry

| Item | Required value |
| --- | --- |
| CK3 version | `1.19.0.6` |
| CK3 executable SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| Adapter | `ck3-1.19.0.6-msvc-x64` |
| WarID | `50331699` |
| Expected player CharacterID | `29829` |
| Expected `date_raw` | `53223936` |
| Frozen checkpoint | `C:\Users\xenoa\AppData\Local\Temp\xar-g2-altseed-after-embarked-fix-20260831-0937\profile\save games\xar_checkpoint.ck3` |
| Checkpoint SHA-256 | `60108A5DA03DC3A8315A3E79897D9CF2F49763910A8AA15A462E7DD0B6AAF164` |
| Frozen driver state SHA-256 | `4FB901C77AF6D95A05EAB2B0E900AE2E07A652B4C14729835DECB69FC8CFF57E` |

The bridge DLL/injector pair must be recorded in the attempt report and must
be the already frozen exact-build pair; do not substitute a newly built pair
without a new provenance record.

## Required `open_kaishek` preflight (no CK3)

The offline accelerator is pinned independently of the parent repository:

| Item | Required value |
| --- | --- |
| Checkout | `Z:\workspace\open_kaishek` |
| Git | `main == origin/main == bd980e787e8e64b64104b43542ae2afefe3e8a06` |
| CLI JAR | `Z:\workspace\open_kaishek\kaishek-cli\target\kaishek-cli-0.1.0-SNAPSHOT.jar` |
| JAR SHA-256 | `DCCCF51A8B68EEC6CCF8D391D7B0E839361DECB9E37098C31BBB78EB296247A1` |

Run the following against a fresh, immutable copy of the intended phase-two
source tree before any native runner command (the root path is deliberately a
caller-supplied fixture, not a repository dependency):

```powershell
$kaishekRoot = 'Z:\workspace\open_kaishek'
$kaishekJar = Join-Path $kaishekRoot 'kaishek-cli\target\kaishek-cli-0.1.0-SNAPSHOT.jar'
$java = 'C:\jdk-21\bin\java.exe'

& $java -jar $kaishekJar preflight `
  --root '<fresh immutable phase2 source copy>' `
  --profile ck3-1.19.0.6-zg361 `
  --fixture synthetic-361-014
```

Archive the single JSON output together with the checkout commit and JAR
SHA.  The expected contract is `open_kaishek.preflight.v1`,
`provenance.mode=offline`, `ck3_started=false`, `save_mutated=false`, and
`network_used=false`.  A full phase-two tree may retain the known bounded
profile-validator `RED` (currently `233,014` diagnostics); this is an offline
schema boundary, not CK3 evidence.  Do not relabel it as native readiness.

The same JAR may be smoke-checked without a source root using
`--fixture synthetic-361-014`; the intentionally unsupported
`ck3-calculated-value-014` fixture remains useful only as a typed diagnostic
(`CK3_TRIGGER_CALCULATED_VALUE_UNSUPPORTED`).

## Offline checks before launch

Run once, from the exact parent commit that will be used for the attempt:

```powershell
$env:PYTHONPATH = 'ck3_autonomous_player/src'
py -3.13 -m unittest `
  ck3_autonomous_player.tests.unit.test_raiktor_truce_probe `
  ck3_autonomous_player.tests.unit.test_war_termination_terms_live_acceptance -v
```

The focused contract suite must remain green.  It verifies the pointer-only
`CAddTruce` shape, two equal non-negative `evaluated_days` reads, same paused
frame, exact provenance, template-versus-concrete action-step diagnostics,
and rejection of mutation commands.  These tests are synthetic and do not
promote readiness.

Before invoking the native harness, also verify the two immutable input hashes
above and retain the JSON output from the `open_kaishek` command.  If either
input hash, checkout/JAR binding, or parser contract differs, stop before
launch and keep the attempt `preflight RED`.

## Semantic-ready gate (the only permitted next native entry)

Use the existing
`ck3_autonomous_player/native_bridge/research/run_war_termination_terms_live_acceptance.py`
entry with the frozen checkpoint/driver pair and its current bounded
readiness timeout.  Do not extend the timeout or retry an identical failed
shape merely to obtain a green status.

The runner may proceed to the MCP sequence only when **all** of these are
observed in the exact-build proof:

1. game version, adapter ID/status, executable SHA, and bridge hello all match
   the frozen identity;
2. the public capability includes `query-war-termination-terms-v1` and the
   action-step list contains the concrete literal
   `query-war-termination-terms-v1-50331699` (the template ending in `-N` is
   insufficient);
3. a semantic-ready paused snapshot contains CharacterID `29829`,
   `date_raw=53223936`, and WarID `50331699` on the player attacker side with
   a distinct primary opponent.

If the proof stops before MCP, retain the report's
`exact_build_proof.observed_action_steps` and classify the result as
`semantic-ready RED`; do not infer a Python defect or enable a write.  If the
concrete step is present, perform only the existing read-only sequence:
capabilities → paused snapshot → terms query (same revision) → paused
snapshot → second terms query (same revision) → paused snapshot.

## Acceptance boundary after a successful read

The two terms payloads must have identical normalized content and sequence
successors, bind to the same paused `snapshot_id`/revision/native revision,
carry exact game provenance, and expose the pointer-only Raiktor defeat truce
with equal non-negative `evaluated_days`.  `actual_expiry_observable` must
remain `false` with `expiry_date_raw=null`; no surrender, white-peace, or
enforce-demands command may occur.  Only after this single artifact exists
should the corresponding typed read contract be extended.

## Evidence-backed gaps and stop rules

- The latest three G2 attempts are RED before a terms sequence (harness
  preflight or native semantic-readiness failure); no paused truce artifact is
  available.
- The older paused/map-ready report cannot be reused because it lacks the
  concrete WarID action step.
- `ReadWarTerminationExitTerms` remains disabled with the recorded reason
  `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668`; expiry must
  not be inferred from `evaluated_days`.
- `GEN-034` therefore remains `static/query-ready + paused/live=false +
  unresolved`.  This sheet adds no new gate and no production policy.

**Next action:** run exactly one fresh semantic-ready entry after the offline
preflight above.  Preserve its full RED artifact if the gate is unavailable;
otherwise bind the one paused double-read artifact and update the existing G2
readiness audit.  Until then, no further native code or speculative bridge
change is planned.

## 2026-09-02 09:40 protocol regression update

Parent `a84c53d` now has a focused `NativeProtocolState.capabilities()`
regression: only a paused frame with a positive full-generation WarID expands
the concrete `query-war-termination-terms-v1-50331699` action step. The
template `query-war-termination-terms-v1-N` remains non-executable. This
regression is offline/static evidence only; it does not bypass the semantic
snapshot gate or authorize any termination write. The next live attempt still
uses the updated `bd980e7`/JAR binding above and stops if the concrete literal
or paused semantic snapshot is absent.

## 2026-09-02 10:08 bounded entry result

The single fresh entry prescribed above has now been completed. Its retained
report is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\report.json`
(SHA-256
`4A7C66D34C851698572F4BBA2970ECAA00C005C2DC338ABCD75A7FD304F0B991`); the
offline preflight used for that entry is
`open-kaishek-preflight-mod-20260902.json` in the same directory (SHA-256
`5F7F67C439D8721E56C735E2DFA49E07A32630DD7019EB221C1C1215DD68AC90`).
The concrete action step and semantic paused identity were present, and the
two read-only terms queries were equal on one frame. Gold, prestige, prisoner,
and favor rows passed; truce duration did not (`evaluated_days_observable=false`,
`evaluated_days=null`). No mutation was issued and cleanup was proven.

This closes the action-step/startup uncertainty but not the G2 decision gate:
`truce_ready=false`, `decision_ready=false`, and `GEN-034` remains unresolved.
The next implementation package is a narrow native observation of the truce
duration field. Do not rerun this identical checkpoint/driver shape or infer
expiry from a date-plus-duration calculation. The later `open_kaishek` schema
descendants through `bd980e7` are orthogonal and do not require repeating this
native entry. The next native entry, after a real truce-reader change, should
bind the current `bd980e7` preflight.

## 2026-09-02 10:24 accelerator schema slice

`open_kaishek` main is now
`bd980e787e8e64b64104b43542ae2afefe3e8a06` with the exact-build-backed
`has_court_position=<court-position-key>` scalar descriptor
(`certified=false`). The synthetic preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-court-position-synthetic-preflight-20260902.json`
(SHA-256
`B2183C32C18D0F7A6F00A8C96C2D0DEEAD7EAF8BFC358606F92415368E6674B7`), GREEN.
Focused profile/validator tests are `13/13` and `23/23`; the rebuilt JAR SHA-
256 is
`DCCCF51A8B68EEC6CCF8D391D7B0E839361DECB9E37098C31BBB78EB296247A1`.
This is offline syntax/profile evidence only and does not change the G2 live
gate or authorize any action.

## 2026-09-02 current accelerator binding

For any future native entry after a real truce-reader change, bind the current
clean `open_kaishek` mainline
`36b4743d5da013ba1f85790ebcffad2629442ed1` and JAR SHA-256
`DFEA464B657D627BBB1AEF34C12CD91419830644D47F891782A3C9D718C44D61`.
The latest parent-adapter preflight using its dedicated `war_days` fixture is
retained at
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T1042-war-days\open-kaishek-preflight-war-days.json`
(SHA-256
`CDC7DCD22888208C7585A2932F266912CAE4C08A9D0836D7EF6580796FC8571F`).
It is offline only: product parser `76/23,831,335/0` and the dedicated
fixture parser/validator are GREEN, the bounded root validator is the known
schema-only RED (`232,973`), and `ck3_started=false`.

The static evaluator call-site review closed the proposed alternate offset:
CAddTruce uses `truce_effect+0x108` and `context+0x28` at both known call sites.
No public schema/ABI widening or termination write is authorized; stop at the
existing semantic-ready/truce gate if internal evidence is still unavailable.
