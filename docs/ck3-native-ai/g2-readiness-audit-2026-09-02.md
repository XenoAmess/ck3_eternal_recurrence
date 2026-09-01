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

## Executable open_kaishek preflight entry

`open_kaishek` is an optional offline accelerator, not a CK3 readiness gate.
The canonical checkout is `Z:\workspace\open_kaishek` on `main` (also
`origin/main`), at commit
`aecb14fbdfa462e4824e5283bbb3e750d09339f0` (descendant of the preflight
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
`47E20B1B3814A5CFBC4CCF7347C0C5CF0128961991FD8436BE2C00701AA969E6`;
record that SHA together with the resolved checkout commit.  An older local
jar (`6E8D9CECCAAA2CCF925B369501919C5B8F15AA73F1C9CB78ACEAF52540EE3E91`)
is superseded and must not be used as current provenance.

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
