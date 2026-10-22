# Campaign score: first closed arithmetic leaf

This module is a Java candidate for four unchanged pure functions in
`ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py`:
`Interval`, `aggregate_state`, `score_360`, and `interval_text`. It has no HTTP,
file/process/native adapter, policy decision, ledger writer, or gameplay side effect.
The parent reactor is owned by the integration/build agents; this work does not
edit its POM or an existing module. Default JUnit reads the committed JSONL and
does not need Python, a game installation, or an untracked fixture.

## Actual producer and consumers

- `campaign_development_score_v1.state_intervals` produces the six intervals.
  Its `build_report` consumes `aggregate_state` for current/baseline and shared
  confirmed contributions, and `interval_text` for display. The report's
  `Interval.export` is the exact decimal-string/null/Boolean ABI used here.
- `ck3_autonomous_player/tools/score_ck3_campaign.py:250` calls `build_report`.
  `campaign_score_save_reader.py` imports `D`, `UNITS`, and `fmt`;
  `campaign_score_existing_inputs_v1.py` and `campaign_score_cadence_v1.py`
  import `UNITS`. These adapters and callers remain Python and are not redirected.
- `tools/g2_saved_campaign/current_saved_campaign_replay_v1.py` binds the source
  identity; its preflight regression also pins the original module. Frozen
  source graphs and their limits are not modified.
- `ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py`
  exercises the pure functions. Repository search found `score_360` used by
  those pure regressions, rather than the current `FINAL_STATE_ONLY` report.
  A Java S30 result alone never qualifies an actual campaign's 360 fixed dates.

No production consumer has switched to Java. Integration can first shadow this
leaf with the six real Python-produced intervals, compare the exact exported
bytes, then explicitly replace the single arithmetic call. Do not create a
second source of weights or silently choose the better Python/Java score.

## Arithmetic and field contract

`DomainScores` fixes L/E/M/U/D/H and weights .25/.25/.15/.10/.15/.10.
`ScoreInterval` is an immutable shared record. Scale/add use precision 80,
HALF_EVEN. `score360(MonthlyHistory)` performs the original expression in the
same operation order, rounding **each** add/multiply/divide with precision 40,
HALF_EVEN. It keeps 360 monthly slots, last 12, bottom 36, and the original
endpoint/history weights. Game-over zeros and technically unknown [0,100] slots
remain different; neither shortens the denominator.

`ScoreDecimal` uses BigDecimal and an explicit negative-zero bit, retaining the
source exponent and original `fmt` spelling (including `-0`, `1E+2`, and fixed
fractional output). Numeric equality follows Decimal, independent of scale and
zero sign; lexical evidence still preserves the original representation.
There is no float/double arithmetic or intermediate rounding to display digits.
Display is HALF_EVEN for exact values, FLOOR/CEILING for interval bounds, with
the original precision-80 quantize failure preserved.

`CampaignScoreCodec` consumes original `Interval.export` objects with exactly
`lower`, `upper`, `known`, and `value`. Decimal bounds are strings; known/value
consistency is checked. Unknown requires explicit null value. A missing key,
null bound, empty array, or wrong token is rejected rather than replaced with
zero or UNKNOWN. The shared `contracts.StrictJson` enforces bounded strict UTF-8,
duplicate/trailing-token rejection and canonical output. The source's score
strings are preserved; this leaf does not port report weight JSON floats.

The deliberately bounded Java leaf admits decimal text/precision/absolute scale
up to 8192 and display places 0..80, inside the shared 64 KiB message limit.
These resource bounds are **narrower than arbitrary Python Decimal** and must be
checked before any future call-site switch; they are not a claim of unbounded
Decimal API parity or a new campaign startup requirement. Normal campaign
scores and all captured source cases fit. The caller still proves the actual
original T0, fixed monthly dates, endpoint identity, sources and availability.
Neither the records nor successful arithmetic provides that qualification.

## Actual oracle capture and proposed Java checks

`machine_id: xenoamess-full-tower-eb9d2c1186`; corpus observed
`2026-10-22T13:35:48.394516Z`. The unchanged producer SHA-256 is
`ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d`;
original test SHA-256 is
`0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2`.
The test-only Java `PythonScoreGoldenExporter` verifies both pins before/after,
runs five original pure regression methods with no skips, captures actual
`state_intervals`/`build_report` aggregate/display calls, and adds denominator,
40/80 precision, signed-zero, exponent and display boundary calls to the same
unchanged producer. It writes create-only JSONL, never Python production code.

Actual bounded capture receipt:
`D:/codex-ck3-demos/2026-10-22-java-phase1/logs/CAMPAIGN-SCORE-GOLDEN-CAPTURE02.json`.
It ran the shared qualified `WindowsJobProcess`: exit 0, 0.7740363 seconds,
183386112 B peak under the 536870912 B tree limit, final Job active 0, source
unchanged. The committed candidate corpus has **68 vectors / 283908 B**.
Capture01 remains RED: the five regressions passed, but an extra display at
80 places triggered the original Decimal80 InvalidOperation. Capture02 records
that rejection as a golden instead of suppressing it. These are oracle-capture
facts, not Java compilation/JUnit, runtime throughput, or game success.

`CampaignScoreGoldenTest` executes every captured vector against Java, checks
original pins/all five lineages, and adds strict bad-field/token/null/duplicate/
UTF-8, immutable-history, quantize, and fixed-denominator regression tests.
The designated Maven writer runs the integrated reactor `verify` with build,
temporary and m2 outputs on its authorized D: work package; no Maven was started
by this author. Missing corpus is a hard test failure, never a skipped test.

## Explicit remaining scope

Not ported: `metric`/`bounded_metric`, `R`/relative normalization,
`state_intervals` economic/military/domain formulas, `quality_power` sqrt/order,
report text/facts and availability/source adapters. Native/save observation,
date qualification, complete 360-sample collection and production switching
also remain unchanged. Their existing Python tests must continue to run when a
later migration actually changes their call sites. This first leaf makes no
G2, intelligence, 30-year completion, CPU improvement or 1-second/day claim.
