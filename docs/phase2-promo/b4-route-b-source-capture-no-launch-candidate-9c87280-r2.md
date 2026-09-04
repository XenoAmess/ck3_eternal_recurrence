# B4 WAIT360411 Route-B source-capture no-launch candidate (`9c87280`, r2)

Status: **RED_NO_LAUNCH / static-ready / live blocked by seed-product-tree binding**.
This pass created and verified a fresh frozen product candidate, but did not
start CK3, did not create a checkpoint or registry, and did not observe a
provider result. The machine-readable artifact index is
[`b4-route-b-source-capture-no-launch-candidate-9c87280-r2.json`](b4-route-b-source-capture-no-launch-candidate-9c87280-r2.json).

## Frozen candidate

The accepted r2 candidate lives at:

```text
Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2
```

It contains only the tracked checkout bytes from integrated base
`9c87280187250077afd99deb48e4126d5d19f87a`, a hash-bound broad product
projection, the existing seed contract, and an exact-build native bridge pair.
The product projection contains 735 files / 29,378,142 bytes and has tree
SHA-256 `aeaa96e2cf44c6154f8a61a5aa859b27cbe423e40d48703485cd0a301aea865d`.
The projection manifest SHA-256 is
`92e392c5ed98e899ee7662dcbdb1209d793eeeeb6a05ec2ae274644251e3cf54`.

The bridge DLL and injector retain the prior 92/92 GREEN native-test
provenance. A read-only Git diff found no native source change between that
build's source commit and `9c87280`, so the pair was copied rather than
rebuilt. The candidate binds CK3 1.19.0.6 executable SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`.

The discarded r1 used `git archive`. It was rejected because LF blob bytes do
not reproduce the Windows generator's checkout CRLF/BOM output; the central
generator `--check` correctly reported all generated files stale. r2 copies
only Git-tracked checkout bytes and passes the same generator check. This is a
byte-boundary failure, not CK3 loading or gameplay evidence.

## Static Route-B proof

The frozen r2 product and current strict capture tool prove this order:

1. Central stage 11 prepares the genuine M360 source after the current AL
   receipt boundary.
2. `zg361_p2c_schedule_m360_resume_effect` binds owner, distinct subject,
   P2C cycle/case, AL cycle/case and a monotonically increasing ticket serial.
3. The producer sets stage status `WAIT`, records wait reason `360411`, releases
   the UI lane, and schedules `zg361p2c.7` exactly one day later.
4. `.7` revalidates the complete ticket, current source, Central stage 11 and
   AL state 4, then invokes
   `zg361_we_resume_m360_from_central_source_effect` inside the frozen subject
   scope. The transition fixture cannot summon the owner-facing surface unless
   this production ticket already exists.
5. The source-capture path observes the real owner-facing `zg361we.360`,
   requires native option index 1 to be shown and enabled, and freezes before
   any option is selected.
6. After Route B, the Workforce provider—not the ACK and not fixture output—must
   seal these eight current-cycle facts before the registry writer runs:

   - `exact_owner_subject_cycle_case`
   - `m360_receipt_state_4_choice_2`
   - `route_b_collective_sealed_consumed_settled`
   - `three_distinct_cohorts`
   - `each_cohort_forced_equals_quota`
   - `each_cohort_exception_zero`
   - `each_cohort_manager_cost_zero`
   - `collective_totals_conserved`

The B4 capture deliberately calls the verifier with
`require_m361_charter=False`; it proves the current M360 cycle without
inventing three-cycle/M361 maturity. The generic later-cycle verifier remains
strict, and the career-HC provider remains default-off.

## Effect boundary

The audit was run against the frozen r2 product itself. All 427 B2-and-later
scripted-effect files satisfy the 1–10 target: 3,719 top-level effects,
`target_miss_count=0`, maximum 10 and `>20` violations 0. This pass did not run
CK3, so it produced no new loading-performance evidence and makes no new
file-size performance claim.

## No-launch verification and remaining RED

Focused results were GREEN: 11 capture-preflight checks, 34 Route-B unit tests,
the isolated Workforce fixture contract, 38 central generator tests, central
generator `--check`, effect-boundary audit, and `validate_static.py`.

The formal runner no-launch preflight first accepted the CK3/bridge identity,
then stopped with:

```text
phase-two seed install RED: current_product_tree_matches_seed_source
```

This is the correct strict outcome. The supplied real seed is bound to product
tree `cdbcf82e...`, while r2 is `aeaa96e2...`. A read-only search found four
distinct ready seed trees (`c2e3deec...`, `cdbcf82e...`, `de7533ad...`, and
`fc421846...`); none matches r2. Process count was zero before and after, and
the checkpoint, registry and live-artifact paths remain absent. An old
seed-matched projection is not a workaround because it does not contain the
integrated WAIT360411 production choreography.

The exact no-launch command that produced the RED is recorded as argv in the
JSON index. The corresponding future CK3 command is below, but it is **not
authorized yet**. Its reserved seed-contract path must first be populated by
a genuine managed seed producer for the exact r2 product tree, and the same
command with `--preflight` inserted must return exit 0 before removing that
flag:

```powershell
Set-Location -LiteralPath 'Z:\ck3_mod_rewrite\_hc-workforce-route-b-source-capture-candidate-20260904'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'tools\run_zhongguo_acceptance.py' `
  --phase2-hc-workforce-route-b-capture-live `
  --phase2-hc-workforce-route-b-checkpoint-output 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\future-live-output\hc-workforce-route-b-pre-option-b-9c87280-r2.ck3' `
  --phase2-hc-workforce-route-b-registry-output 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\future-live-output\hc-workforce-route-b-registry-9c87280-r2.json' `
  --bridge-dll 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\native\xar_ck3_bridge.dll' `
  --bridge-injector 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\native\xar_ck3_bridge_injector.exe' `
  --bridge-pipe '\\.\pipe\xar_ck3_bridge_zg361_9c87280187250077afd99deb48e4126d' `
  --phase2-seed-contract 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\future-live-output\zg361_phase2_seed_contract.current-product.json' `
  --phase2-product-source 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\product-source' `
  --phase2-product-projection 'b4-route-b-wait360411-9c87280-r2' `
  --phase2-product-projection-manifest 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\product-projection.json' `
  --artifacts-dir 'Z:\ck3_mod_rewrite_process_assets\zg361\b4-route-b-source-capture-9c87280-20260904-r2\live-artifacts-r2'
```

The remaining live checkpoint is therefore singular: create a real canonical
paused seed under the exact r2 projection, obtain a GREEN no-launch preflight,
then use CK3's exclusive launch gate once to observe
ticket -> WAIT360411 -> D+1 `.7` -> real `.360`, freeze before B, seal the
eight provider facts after B, restore the same checkpoint, and publish the
strict registry.
