# R54 campaign pause same-owner rejection diagnostic

R54's `case-natural-day-0050` failed on 2026-10-10 at 21:37:27.810143 UTC with
`RuntimeError: campaign pause readback lost the complete same-owner frame`.
The bounded retained row has `ok=false` and no `result` or `after_snapshot`.
It supplies no failed predicate or callsite. Those values and the underlying
cause remain UNKNOWN. Earlier successful days do not prove a race or a fix.
This is a shared-host rejection, separate from keyed-query completion diagnostics.

The source candidate preserves `campaign_pause_frame_binding`'s original complete
same-owner Boolean guard, `RuntimeError` type and exact message. At that existing
rejection, it attaches a bounded dictionary from the same in-memory frame. The
existing `execute` exception handler serializes it as
`steps[].campaign_pause_frame_diagnostic` and follows the original error route.
It adds no snapshot, RPC, pause, resume, retry, polling or game input.

The dictionary contains the original condition expressions, each condition's
true/false/unknown result, first failing index, and bounded original scalar values.
An absent or unavailable value remains null with its reason; no observation is
manufactured. `historical_callsite` and `underlying_cause` remain null. The existing
strict rejection is not readmitted and no day, live or business credit is added.

Six extracted pure-function checks already passed once: unchanged paused/running
results; continued rejection and identification of date, TID and semantic-state
failures; missing PID with first failure and unavailable later operand; and the
untouched earlier build guard. Their original result is retained below. The
repository test entry is a path-only projection: its six methods, fixture and
pure loader have equal ASTs to the already-run checks. It was not rerun when
packaged. CI will run that entry against the actual integrated repository host.

```text
python -B -X utf8 ck3_autonomous_player/tests/unit/test_campaign_pause_same_owner_diagnostic.py
```

The test extracts only pure functions through AST. Its frozen pre-diagnostic guard
is a regression fixture and never imported by production. No installed CK3, MCP,
external runtime directory, process or save is required. The sole CI increment
runs this command in the existing Official Runner shared-acceptance block and
retains the existing explicit failure check.

On a later authorized fresh run, inspect `first_failed_condition`, `conditions`
and `observations` if the exact rejection recurs. R54 must not be replayed or
relabelled. Any behavioral remedy needs the resulting actual evidence; this
diagnostic is not a behavioral fix or live qualification.

Raw retained evidence: [failed day row](evidence/2026-10-11-r54-campaign-pause-readback/FAILED-DAY-0050.actual.json),
[six original checks](evidence/2026-10-11-r54-campaign-pause-readback/FOCUSED.actual.json),
[original predicate map](evidence/2026-10-11-r54-campaign-pause-readback/PREDICATES.source.json),
[source candidate index](evidence/2026-10-11-r54-campaign-pause-readback/SOURCE-CANDIDATE.INDEX.json),
and [portable-entry AST proof](evidence/2026-10-11-r54-campaign-pause-readback/PORTABLE-ENTRY-AST-EQUIVALENCE.actual.json).
Original external paths in raw metadata are historical references, not new
qualification. Retention and later availability follow the repository's common
storage policy; copying does not renew the original expiry.
