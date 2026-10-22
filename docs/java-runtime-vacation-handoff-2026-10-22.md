# Runtime Java migration vacation handoff

machine_id: `xenoamess-full-tower-eb9d2c1186`
Observed: `2026-10-22T15:06:00Z`
State: user requested a vacation handoff; all runtime owners were instructed to
save current work and stop. No new migration leaves, capture, SDK measurement,
Maven or Game calls may start automatically. The unsigned 15:30 read ticket is
not permission to execute or renew it.

## Actual verification boundary

The previous nine-module Java group passed actual java07: 458 tests, including
native-diagnostics 16 and pure late-outcome-reconciliation 27, exit 0 / Job 0.
Those tests do not cover wave2-runtime. Actual java10 exited 1 / Job 0 before
runtime compilation: an upstream deprecated API with Werror caused runtime to
be skipped. Wave2-runtime has therefore never been compiled or executed.
Java11 was not started and has been stopped. The full new cold/warm CI command
group, independent-process SDK continuation, and 27-file performance route group
were never started. CI's actual stopped-state receipt is
`D:/codex-ck3-demos/2026-10-22-java-phase1/logs/CI-VACATION-HANDOFF-20261022-1503.json`.
No new Driver or SAVE body has been measured; no new Game/native business credit
or throughput improvement exists.

## Clock reader preserved source

Latest source receipt:
`D:/codex-ck3-demos/2026-10-22-java-phase1/logs/CLOCKREADER-SOURCE-FREEZE02.json`.
It contains exact pins for 15 leaves, 102,988 bytes, source-tree digest
`82fe68da610bbb410b65e5898f69aa297bc83dfd00331e389185f7a18fb1941a`,
and six existing canonical Python files. Expected tests: 20 Java, seven added
canonical receiver tests, three added SDK route tests. None of these new tests
has executed. The earlier source manifests and actual failed builds are retained.

Code is under `java/ck3-control/wave2-runtime/.../runtime/clockreader`, with
`MIGRATION-clockreader.md`. It implements the real file adapter/application,
actual shared Win32 measurements and exact source measurements, bounded unique
read tickets and retained intent, complete historical row reconstruction, and
the shared pure STATUS → paused SEM → confirming STATUS assessment. It creates
no MCP/native client and cannot resume, cancel, arm, clear HALT or commit.
PROPOSED still needs the original writer lock, real reducer, recheck/CAS and
persisted readback. Original failed credit remains zero / never replay.

The original Queue mechanical route is in existing
`current_saved_campaign_preflight_v1.py` and the existing
`prepare_current_saved_campaign_cold_v1.py` emitter. It binds the actual original
Session, preserves HALT/FULL state, uses the original consume_sequence and
INFLIGHT/OUTBOX, and executes the original guard before and after each fixed
read. A final pre-submission deadline check retains intent without submitting
after the original guard has consumed the budget. The denied legacy recovery
methods stay denied. The SDK adds only a zero-argument fixed private STATUS
tool behind the existing private SEM opt-in.

The SDK edit window ended at `2026-10-22T14:42:41Z`; source pins remain:

| Existing source | Bytes | SHA-256 |
| --- | ---: | --- |
| `native_driver.py` | 1,658,411 | `40a625c6448f753ffa920d6a7780e5687dde7bca28e5b6ab07237ad588efd8cb` |
| `mcp_server.py` | 282,938 | `89f7d45266ef924279d88345408c49c98ff98d429f1dac921b673e1605bb8004` |

Only AST parse and an actual installed MCP model probe ran locally. MCP 2.0.0
at `Python313/Lib/site-packages/mcp_types/_types.py` actually serializes
`is_error` / `structured_content` / `result_type` through model_dump(mode=json).
The cross-process Java test now uses that real CallToolResult producer, with
explicitly synthetic native body/Game facts, and the shared qualified Win32 Job.
It has not executed. It uses `xar.repo` or `XAR_REPO_ROOT`, optionally `xar.python`,
so the D-volume Maven snapshot does not need a global user.dir change.

### Known remaining clock reader fix

At stop time, independent source review identified a further P2 boundary:
`ClockMcpRowDecoder` does not require `result_type == "complete"`. MCP 2 allows
`input_required` and extension strings, which must not become completed native
Read facts merely because selected body fields exist. No live misclassification
is claimed. This fix was deliberately not started after the stop instruction.
Next change must require the textual complete discriminator after the result
object boundary and before success/error native decoding; client_error handling
stays distinct. Update the synthetic row fixture to emit complete and add valid
native-body counterexamples for input_required/task/missing/null/bool/float.
Missing type defaults to complete in generic MCP wire, but this leaf consumes
the pinned model_dump producer, which always includes the field. Keep that
scope precise. Do not broaden global map JSON or normalize malformed float
tokens by tree serialization.

## Finite runtime cohort

Only these eight wave2-runtime leaves belong to the first pending build:
clockreader, stdioidentity, savedproof, closedadoption, creationtime,
deadlinetransport, performancewindows, providerchain. The module POM already
depends on admission-contracts, closed-failure-recovery,
late-outcome-reconciliation, build-tools, contracts, Jackson and JUnit. Runtime
must not depend back on finance or development; those consumers depend on it.

Latest supplied owner records:

* stdioidentity: `STDIOIDENTITY-SOURCE-FREEZE01.json`, 12 files / 71,296 bytes,
  actual 40-case legacy capture passed; expected Java 46 tests have not run.
* savedproof: `SAVEDPROOF-SOURCE-FREEZE02.json`, 15 files / 92,841 bytes,
  expected seven tests; zero actual Driver/SAVE body reads. Single-measure cache
  must be reused by the temporary original writer and consumer in one JVM.
* closedadoption: saved final WIP 23 files / 174,487 bytes, tree digest
  `2f133151f67db29f4d944b5f42998b114df4c27f25ae2114dba70c85e3b861e5`.
  Includes the qualified file-Job session, source loader, 256 KiB independent
  writer protocol cap, explicit repo configuration, and temporary transaction
  Main. It has not compiled. **Known WIP blocker:** Main.exact wraps every input
  as JSON RecoveryEvidence, including two .py source files, so it will reject
  before measurement. Separate raw source SHA validation from JSON evidence
  first; owner stopped without fixing it. CLI documentation is also unfinished.
* creationtime: `CREATIONTIME-SOURCE-FREEZE02.json`, six sources / 32,749 bytes.
  Actual producer capture passed at 14:58:31Z, exit 0 / Job 0, 47 reports and
  152 vectors. Output remains `D:/scratch/creationtime-oracle02/original-v1.jsonl.gz`
  (2,963 bytes, SHA `b7d510771b9d1ad9f469cfdec059e4a86806faa9b0bf20cdd740047767d880ca`).
  It has not been copied into source resources; Java/consumer comparison is pending.
* providerchain: `PROVIDERCHAIN-SOURCE-FREEZE01.json`, 12 files / 66,950 bytes,
  two actual producer captures passed; expected Java 16 tests have not run.
* performancewindows: final owner receipt
  `BATCHTIMING-PERFORMANCEWINDOWS-ARMYSUMMARY-VACATION-WIP01.json` supersedes the
  earlier pending description. Capture01 child exited 0 / Job 0, but the outer
  post-cap check was RED. Its 63,957-byte D-volume golden remains outside source
  resources. Code is 107,887 bytes; capture02 was never started and is withdrawn.
  Missing golden must produce a real failure, never a skipped pass.
* deadlinetransport: `DEADLINE-TIMELINE-VACATION-HANDOFF01.json` contains final
  freeze03 pins for nine files / 70,102 bytes and timelineowner freeze01 pins for
  seven files / 64,860 bytes. Neither capture nor Java validation ran; expected
  40/46 tests are not passes. Pending batch04 is cancelled.

Already-written wave3 work is kept separate and must not delay first-runtime
verification: processcustody (retained-handle shared API still missing, DRAFT),
timelineowner, childexports (final five files / 29,831 bytes; private numeric
profile/golden gap, DRAFT), and armysummary (five files / 48,466 bytes, no golden
or Java execution, expected 11 tests). Childexports final pins are in
`PROVIDERCHAIN-CHILDEXPORTS-VACATION-HANDOFF01.json`; the two latter owners have
withdrawn their pending capture requests. The independent wave3-runtime POM exists but is
not permission to register or execute it. Modalboundary and bootstrapvalues
had no written code when cancelled and must remain unopened.

## Resume order after explicit user resumption

1. Recheck current machine, storage/resource releases, all saved owner source
   pins and stopped state. Do not use or renew the old unsigned/expired read ticket.
2. Fix the two known local boundaries above. Finish only the existing finite
   cohort; keep source metadata, native payload and writer-line byte budgets distinct.
3. Run the full shared build with M7 as the single Maven writer. Supply actual
   repository/Python fixture paths without changing user.dir. Consume actual
   exit/timeout/terminal status; skipped or missing golden is not passed.
4. Execute the complete corresponding cold/warm CI command group, independent
   SDK continuation and full route group in the coordinated resource window.
   Do not substitute selected unit/static checks or source review.
5. Only after the compiled/qualified chain passes, obtain a fresh finite signed
   read ticket and exclusive Job allocation. Execute exactly one permitted
   original-SDK Driver read and original SAVE hash, reuse that measured cache in
   the same JVM for the temporary original locked writer → real readback →
   original cold consumer, then verify actual terminal/Job accounting.
6. Root alone decides any production canonical change/new Game pack. Original
   N46 error, frozen source/runtime and unqualified late visual clue remain
   preserved. No historical success/SAVE/day credit is rewritten.
