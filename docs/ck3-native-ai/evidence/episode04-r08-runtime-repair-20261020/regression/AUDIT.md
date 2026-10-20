# R08 actual runtime versus CI boundary audit

Final scope, 2026-10-20 14:12Z: the author **withdrew the host-root injection**.
The accepted a02/a03 candidate changes both payment-library imports to the
already declared top-level `ck3_live_run_id`, preserving the original host and
runtime. This fixes both the server process and the public actor parent. The
host-candidate discussion below is retained as intermediate diagnosis only.
The final executable smoke overlays the author's complete payment module, not
patched functions; the negative control changes only those two imports back to
the published broken namespace. The deployed test uses production modules
without overlays. No new import-root requirement is imposed on runtime config.

Actual final evidence: `candidate-payment-a03/ORIGINAL-WAIT.actual.json`
Popen35992/wait0, **4 subprocess tests PASS**,21.139s, a02 source. It also starts
a separate script with src/tools only, invokes the real public actor and real
CommonPackets against recorded synthetic public rows, then executes the real
payment normalizer twice before a deliberate stop at collect_current_context.
No root is injected in that parent. Old D39 parent independently fails with
`No module named 'tools'` (`baseline-parent-d39`,Popen19540/wait1).
One earlier candidate test failed because an externally located actor looked
for its sibling controller beside the external candidate; the failed wait1 is
preserved. The final overlay uses the canonical installed __file__ for that
unchanged real sibling controller; it is not a controller replacement.

`helper-candidate-a02/ORIGINAL-WAIT.actual.json` Popen17620/wait0 proves
**6 helper tests PASS**, including retained typed idle0, claimed/mutated idle0
refusal, clock failure continuing both OFF paths while withholding Save,
unavailable payment rejecting OFFclear, and natural-phase once-enable/query,
missing authorization, busy and unknown-action handling. Real clock/sampling
normalizers execute. Queue/payment seams remain explicitly simulated.

Root then found a separate a02 Save/close gate defect. The a03 author added
`save_verified`; I read the exact a03 source, real cleanup/CloseGate test and
original Popen28804/wait0 log: two tests include Save exception and independent
after unknown, each Save once and Quit withheld. I did not repeat the same
tests. The earlier 4+6 are a02 boundary evidence, not a statement that every a03
byte was retested. No a03/live/global R08 acceptance is inferred.

machine_id: `desktop-3fevhd2-1c74096080`. Read-only audit on 2026-10-20;
exact source and observations are pinned in `SOURCE-INDEX.actual.json`.
D remains detached `39e59acce6624edbc30322e4797d2e421c0a44aa`; no D/W edits,
game, native executable, pipe connection, UI or external SDK request occurred.

The successful Official workflow contained **147 steps**, not 147 R08 behavioral
tests. Its new R08 step runs five deterministic tests in
`tools/test_r08_writer_one_day.py`. Those tests established the stated route and
refusal properties, but did not exercise the failed runtime boundaries:

| Gap | Existing test boundary | Actual source/runtime consequence |
|---|---|---|
| Runtime package root | `PublicHook.test_actual_r10_dispatch...` replaces `actor.run_case`; the test adds tools/src to its own sys.path. Author `focused_run.py` additionally adds W/tools and D/tools. Old connected-payment tests add repository root explicitly. None starts the long-lived server with the generated runtime import environment. | R0222 runtime has only src and tools. `war_payment_observations_v1.py:369` imports `tools.ck3_live_run_id` before G2 `endpoint.send`; tools directory alone does not make the `tools` package importable. Actual failed native request count is zero. |
| Pre-arm clock | `test_prepare_failure...` replaces `_normalize_tactical_daily_sentinel_status` with a dictionary saying idle. Its fake packet returns an empty sentinel object. | Real full pre-arm idle leaf has generation0/speed0. The unchanged strict normalizer at native_driver.py:29806 rejects speed0; cleanup stops before payment disable/Save. No prior observer/Arm existed. |
| Natural-phase prerequisite | The same test replaces `normalize_payment_extras`, and controller test replaces `RootRuntime.request`, `check_cash`, READY and Popen. Its simple synthetic responses establish no native gate prerequisites. | The actor's initial payment-enable path contains no natural-phase query/enable/query. Native `war_payment_window_12004.cpp:62-63` refuses enable unless natural sampling is available/enabled/not busy. R0222 failed earlier at import, so this is a source-proven latent defect, **not an observed R0222 native refusal**. |

The existing connected-payment test already checks a serialized control refusal
with reason `natural_phase_sampling_must_be_enabled`; that proves truthful
transport/refusal handling, not that the public actor arranges the prerequisite.
Cold fixtures validate native observer ownership/route contracts, not this
Python server bootstrap or public cleanup path.

## Minimal executable regression candidate

`test_r08_runtime_entry_smoke.py` is intended for `tools/` after review. It runs
real fresh Python subprocesses from an external temporary cwd, with no inherited
repository import convenience. Each child loads the **published host module**,
calls its actual `clean_imports(repo)`, registers the actual MCP server and invokes
the actual registered public cash tool. The original NativeHeadless method and
G2 transport execute unchanged. Only endpoint.send is substituted: it records the
native request and immediately stops. No driver constructor, pipe, host main,
native wait, CK3 or live SDK request executes.

The positive case requires query/enable/disable to reach the native send boundary
once each, with actual machine ID and native revision, and invalid control usage
to reach it zero times. Omitting host bootstrap with the published R0222 two-path
environment is a negative control and must fail before native send. A complete
environment positive control shows that an import failure cannot masquerade as
successful execution. The child neither adds sys.path nor patches request-field
or normalizer functions. `--host-path` permits the author's external candidate
host to be checked without editing D/W.

CI command, after integrating the candidate test:

```text
python -B -X utf8 tools/test_r08_runtime_entry_smoke.py
```

Before a new authorized scene, use the **new generated exact runtime** without
editing it, with its selected interpreter:

```text
<selected-python> -B -X utf8 tools/test_r08_runtime_entry_smoke.py --runtime <new-runtime.local.json>
```

Default CI uses the R0222 two-path environment and requires production bootstrap
to repair its own import root; it does not silently add repository root to the
fixture. The actual-runtime option also detects a later generated environment
or interpreter mismatch. This is an offline import/entry/transport qualification,
not native memory or R08 business acceptance.

## Minimal additional behavior checks for the author's actor fix

1. Feed the retained actual complete idle0 leaf through the real cleanup helper
   with observer_claimed=false. It must proceed to one payment disable plus
   independent OFF query, all-family disable plus independent OFF query, then
   Save once only after all predicates pass. Claimed observer, any nonzero field,
   booleans in integer fields or malformed idle leaf must not use the exception.
   A bad clock must still attempt the two independent OFF paths but never Save.
2. Use actual actor/native-control normalizers with a stateful queue/native-send
   double. Start natural sampling OFF; reject payment enable unless a real
   natural enable receipt and a separate ON/idle query have occurred. With
   explicit once-enable authorization, assert that this native boundary is
   reached in legal order; without authorization, with unavailable/busy data,
   or an unknown enable response, assert no payment enable/observer/day replay.
   Preserve the original unknown action and prove enable is submitted at most
   once. Do not replace payment/clock normalizers or whole actor/controller.

These extra behavior tests must use source-defined native control shapes,
not objects asserting success by fiat. They can be added to the focused suite;
there is no reason to rerun the whole 147-step matrix locally or launch a game.

## Actual offline baseline

`baseline-d39/ORIGINAL-WAIT.actual.json` is the original Popen/wait receipt:
three subprocess tests, **one expected old-source failure and two controls
passing**, original wait1. The failure is the complete frozen runtime through
the real host bootstrap, with `No module named 'tools'` and native send0.
This preserved RED is evidence the proposed test detects the published defect;
it is not a fix PASS. Earlier exploratory two controls passed after explicitly
adding root only to a positive-control child environment. No R0222 record was
modified or replayed. Actual observer/day/payment-enable remain unexecuted by
this audit; full R08 and all formal counters receive no credit.
