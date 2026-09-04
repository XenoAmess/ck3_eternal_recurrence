# `hc-workforce` B4 route-B checkpoint plumbing

Status: **static-ready / live-pending**. This package did not start CK3, did
not capture or restore a save, and does not claim a provider result.

## Exact integration point

Use the current cumulative product projection already materialized by
`bootstrap_userdir`. Install the existing isolated Workforce transition
fixture with `install_phase2_workforce_action_fixture`, restore that fixture
activation, and select its typed subject-to-owner transition. Once
`wait_for_phase2_exact_event` observes the real `zg361we.360` window with the
exact owner played, call the new functions in this order:

1. `bind_current_cumulative_projection(bootstrap, fixture_install, source_git_commit=...)`
2. `freeze_route_b_pre_action_checkpoint(...)`
3. `run_route_b_and_collect_postconditions(...)`
4. `restore_route_b_pre_action_checkpoint(...)`
5. replay step 3 with `expected_case_identity` from the first provider proof

The functions live in
`tools/zg361_phase2_hc_workforce_route_b_checkpoint.py`. They are deliberately
not registered in the formal `run_zhongguo_acceptance.py` scenario registry by
this no-launch package.

## What is bound before option B

The freeze step requires a paused, map-ready frame; the real
`zg361we.360` definition; three shown and enabled A/B/C options; root, played
character and `zg361_we_al_owner` all equal to the expected owner; and
`zg361_we_al_subject` equal to the distinct expected subject. It also binds:

- the current staged product-tree SHA-256;
- the acceptance-only transition-fixture tree SHA-256;
- event instance, native revision and frozen date;
- the native checkpoint's absolute path, byte count, SHA-256, date and owner;
- an archived byte-identical copy created before any route option is selected.

An existing archive target is rejected instead of overwritten.

## Honest cycle/case boundary

The generic event-window query proves that the `zg361_we_al_cycle` and
`zg361_we_al_case` saved scopes exist, but their generic scope payloads do not
publish numeric cycle/case identities. The freeze step therefore records both
values as `pending_post_action_workforce_provider`; it does not infer them
from source text, caller input or the option ACK.

After Route B, the existing received-self Workforce provider supplies the
owner/subject/cycle/case identity together with all 13 required facts. That
provider result seals the numeric identity onto the checkpoint evidence. A
restore proves the same bytes, date, owner, event definition and option
surface. Runtime event-instance IDs are retained in each frame but are not
assumed stable across a cold process restore. Because
the restored pre-action event still cannot expose numeric scalar scopes, a
case-identical restore is completed only after replaying Route B and matching
the new provider identity to the sealed owner/subject/cycle/case tuple.

## Provider join

`run_route_b_and_collect_postconditions` retains the option response only as
an ACK and invokes `prove_m360_postcondition` for the 13 Workforce facts. The
owner-to-subject transition must be the typed `zga_phase2_workforce.3` path and
must preserve the frozen date.

The separate career-HC query is exposed through the typed
`CareerHcHook`. The default hook checks for
`game.command.query-zhongguo-career-hc-workforce-postcondition-v1` before
calling it. When that capability is not advertised, the artifact records
`status=not_available`, `provider_observed=false`, and no synthetic partition.
If it is advertised, the hook requires the same paused revision, date and
owner/subject/cycle/case as the Workforce result plus the real state-4,
choice-2 receipt. The career provider's exact-build native wiring is complete,
but remains default-off and unadvertised until this paused live checkpoint is
proven.

## Remaining live checkpoint

The next CK3 run must use a hash-bound current cumulative product projection,
activate the existing Workforce fixture, and pause on the real
`zg361we.360` before Route B. It must retain the archive, freeze report,
Route-B ACK, Workforce provider sidecar, optional career-HC provider sidecar,
restore receipt and provider replay. Until those artifacts exist, readiness
remains `static-ready-live-pending`.

Offline verification:

```powershell
py tools/test_zg361_phase2_hc_workforce_route_b_checkpoint.py -q
py tools/test_zg361_phase2_hc_workforce_route_b_checkpoint_preflight.py -q
py tools/zg361_phase2_hc_workforce_route_b_checkpoint_preflight.py
```
