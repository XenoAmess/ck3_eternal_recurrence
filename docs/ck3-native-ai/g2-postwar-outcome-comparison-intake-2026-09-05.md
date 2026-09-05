# G2 postwar outcome comparison intake

Status: **static/no-launch consumer GREEN; source-specific comparison RED**.

This package consumes the retained R3 action-bound postwar receipt in the
existing `raiktor-three-way-exit-policy-v1` core. It does not treat that
receipt as a three-way result and does not issue or authorize any CK3 action.

## Why this package exists

R3 already proved one real private lifecycle:

- exact source candidate commit
  `e72f9fa302811a823479635648eb008a6f5d8418`;
- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-cleanup-formal-e72f9fa-r3-20260904\live-r3\report.json`;
- report size `214389654` bytes and SHA-256
  `44E1F7C0B470B2CF7B6549192865402F21F88C7CF073E896DE1B93632311D5D0`;
- one accepted `surrender-war-50331699` mutation;
- the same PID `17292`, connection generation `1`, and episode
  `native-29829-809d91e48a8d` across pre/action/post;
- eight persistent and eight current regiment generations in two CArmies;
- exact-store cleanup from measured `598` soldiers to `0`, with boundary loss
  `598`;
- a persisted, non-formula truce row from `29829` to `36769`, with
  `evaluated_days=1825` and expiry raw date `53267736`;
- immutable source checkpoint/driver-state and proven process cleanup.

The missing step was not another live capture. The existing three-way policy
had no intake for these measured postwar facts, so R3 could not participate in
the comparison workflow at all.

## Consumer wiring

`prepare_g2_postwar_comparison_intake.py` hash-checks the R3 report, rebuilds
the existing retention ticket, reuses its 20 receipt checks, verifies the
outer single-mutation/session/cleanup/source-invariant boundary, and projects
`raiktor-observed-surrender-outcome-v1`.

That projection is passed directly to
`assess_raiktor_three_way_exit(..., observed_surrender_outcome_value=...)`.
The old five-argument caller remains compatible. The policy returns the
normalized observation and its canonical SHA-256, so the path has a real
consumer rather than being a detached evidence summary.

The no-launch result is:

- artifact
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-postwar-comparison-intake-e72f9fa-20260905\intake-r1.json`;
- size `9800` bytes;
- SHA-256
  `01C0EBAAB1B5BF59EC077118C9DF9C23FC380668D4D10101874AF3DA98939C9E`;
- status `GREEN_STATIC_R3_COMPARISON_INTAKE`;
- normalized observation SHA-256
  `08132B217DDF647DF9602F00CF4F927096ED0146E53FF9AB56A87ACD92C81F97`;
- `observed_checkpoint_boundary_ready=true`;
- `source_specific_loss_comparison_ready=false`;
- `comparison_input_ready=false`;
- `recommended_outcome=null`.

The adapter reads only immutable JSON and repository inputs. It does not call
a CK3 launcher, process API, bridge pipe, or save writer, so it does not
require CK3 to be absent and can run alongside an independently owned live
session.

## Why `598 -> 0` is not a source-specific outcome

The eight frozen rows were selected by exact WarID and stable native object
generation. That proves those generic war-bound rows were destroyed after the
bound surrender. It does not prove that every row originated from the six
`bookmark.1071.a` Raiktor `spawn_army` executions. Bound WarID, `keep=false`,
army composition, and the authored `3000` are not source identity.

The policy therefore returns:

```text
observed_generic_boundary_source_attribution_required
source_specific_war_loss_attribution_unavailable
```

R3 can now be used as a measured checkpoint/cleanup/actual-expiry observation,
but its `598` loss is not allowed into campaign utility or a source-specific
surrender comparison. It cannot fill the campaign, owner-budget, or
white-peace providers either.

## Exact next construction seam

The remaining native provider is
`raiktor-source-specific-war-loss-attribution-provider-v1`. Its already frozen
exact-build observation window is the `spawn_army` execute
post-finalize/pre-cleanup range starting at RVA `0x2E7F951` and ending before
`0x2E7F9A6`.

The capture must bind each execution to the selected `bookmark.1071.a` loaded
option node and the exact `raiktor_claim_cb` WarID, then freeze every newly
created persistent CRegiment/current CArmyRegiment/CArmy generation and its
measured soldiers before gameplay advances. Exactly six source executions are
required. Evaluated name is supporting evidence only. A capture from the
already-post-bookmark R3 checkpoint cannot reconstruct this provenance.

The provider's offline portion is now implemented and preflight GREEN: its
typed normalizer consumes the existing default-OFF standalone capture shape,
and the exact ABI plus fresh standalone self-test are frozen in
[g2-source-specific-war-loss-provider-2026-09-05.md](g2-source-specific-war-loss-provider-2026-09-05.md).
No real six-execution capture exists yet, so source-specific comparison remains
RED and the R3 outcome status above is unchanged.

Even after that provider exists, the complete three-way decision still needs
the separately listed campaign-dominance certificate, an owner-authored budget
profile, and a same-frame white-peace comparison certificate. No observed
three-way winner exists today.

## Boundaries

- `r3_generic_boundary_used_as_source_specific_loss=false`
- `three_way_outcome_compared=false`
- `public_readiness_promoted=false`
- `action_readiness_promoted=false`
- `decision_ready=false`
- `automatic_surrender_ready=false`
- `gen034_closed=false`

This work changed no CK3 effect file and encountered no effect-file loading or
single-file-size performance RED. The effect sharding rule was therefore not
exercised by this native/Python package.
