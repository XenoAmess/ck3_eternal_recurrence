# M5 assessed joint budget selector

This lane ports `ck3_autonomous_player/src/xar_autoplayer/m5_joint_budget_selector.py`
into `org.xar.ck3.control.finance.jointbudget`. It is an analytic comparison of
externally assessed alternatives: it selects at most one positive feasible row,
never emits a native step, never reserves funds, and never submits or persists.
It does not invent marriage payoff, war outcomes, supply measurements, or utility.

## Producer and all consumers

The existing producer is `select_m5_assessed_candidate`. Its only production
caller is `M5FrameDispatcher.choose` in `m5_joint_dispatch.py`. That dispatcher
adds the chosen amount, claims, and war-slot count to its one-frame reservation
under its existing lock. `compare_m5_joint_shortlist` in `m5_joint_shortlist.py`
builds the combined legal/domain-approved intake and calls that dispatcher.
`m5_observed_opportunity_selector._normalize_proposal` is the producer of the
observed proposal projection accepted through the shortlist.

The Java port is `JointBudgetSelector.select(Input)`. `JointBudgetCodec.decode`
accepts an exact six-field wrapper corresponding to the original function's
arguments; `select(byte[])` returns the original result JSON domain. Native
snapshot and proposal containers remain extensible projections, so unrelated
native fields are not falsely required to disappear. JSON nodes stop at the
codec; policy inputs, claims, frames, amounts and results are immutable records
and explicit status/reason branches.

The future consumer substitution belongs at the call in
`M5FrameDispatcher.choose`: supply its already checked six-part paused frame,
commitments and assessments to the in-process Java application port, consume
the original result fields, and keep the existing single reservation authority.
This lane does not change the Python caller, start an HTTP service, or assert
that the production consumer has switched. The leaf's historical identity is
player/native-revision/date; the dispatcher still validates snapshot/revision/
episode for the entire request. Observed proposals additionally bind all six
fields exactly, as in the original selector.

## Preserved rules

- Amounts, utilities, identities and slot counts use exact `BigInteger` integer
  tokens; booleans, floats, strings and explicit null cannot become integers.
  No safe-integer or signed-long truncation is introduced into the old Python
  integer ABI. Gold retains scale 100000, with stricter integer token validation
  required by the current field-contract rule.
- Existing gold plus the greater of policy/proposal reserves remains unavailable.
  Existing army, ally, character and commitment-key claims remain exclusive.
  Active and pending wars both consume slot capacity. Public army ID zero is
  valid; character and ally claims start at one.
- Rejection order remains net value, gold, supply, controllability, occupied
  claim, war slots. Evaluated rows remain in assessment order. Eligible ties use
  descending exact net then Python Unicode scalar ordering of candidate IDs.
  A typed candidate index preserves the original dictionary lookup instead of
  rescanning the entire legal intake for each assessment.
- Empty assessments return `missing_assessments` before requiring treasury or
  amount observations. Missing values never become measured zeros. Pending
  war slots alone retain the legacy missing-field default zero; explicit null
  is rejected. Unknown unobserved candidate domains remain rejected; an observed
  extension domain retains the original proposal-bound branch.
- One comparison can have several individually feasible alternatives while
  returning one choice. Resource reservation stays with the original dispatcher;
  increased commitments must be supplied to a later comparison. The Java leaf
  is not a second reservation writer.

## Evidence and validation status

`src/test/resources/jointbudget/legacy-producer-golden.json` is an actual capture
of the original production selector, with source SHA-256 pins and observation
time. It contains 18 scenarios: 13 accepted outcomes and five original rejected
inputs. One observed construction proposal is produced by the original
`_normalize_proposal` before selection. Inputs are synthetic assessments and
resource observations; historical R736 candidate IDs do not make the synthetic
utility or treasury a live observation.

Capture: machine `xenoamess-full-tower-eb9d2c1186`, 2026-10-22; 105674 bytes,
SHA-256 `9726d8a65e650068b2e02c8d0e971477f7f8759d2587c7a67593605806b10fd8`.
The capture used a one-off interpreter command invoking unchanged existing
production code; no new Python module or build entry point was created.

At 2026-10-22T13:36Z the existing Python unit files were actually executed:
`test_m5_joint_budget_selector.py`: six tests passed, zero skips;
`test_m5_public_army_zero_claims.py`: five passed, zero skips. These results
validate the original baseline only. The new Java test file has nine JUnit
methods, covering original-producer differential outcomes/rejections, double
spending alternatives, wrong/missing/unknown fields, duplicate keys, UTF-8,
identity and observed-claim drift, missing assessments, serialization round
trips, integer precision, immutable collections, and Unicode tie ordering.
Maven compilation/JUnit are pending the shared M7 build; they are not claimed
as passed here. Default JUnit uses the committed fixture, with no dependency
on an untracked Python file or a Python installation.

No Game, RPC, ledger, Task, service or frozen SDK/runtime changes occurred in
this lane. No performance improvement, actual campaign value or G2 completion
is inferred. All new lane source/test/golden/docs are bounded below 192 KiB;
build output and scratch belong to the Root-released D-drive work package.
