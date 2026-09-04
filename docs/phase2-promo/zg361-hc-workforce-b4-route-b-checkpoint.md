# `hc-workforce` B4 route-B checkpoint plumbing

Status: **static-ready / live-pending**. The formal capture and replay entries
are wired, but this package did not start CK3, did not capture or restore a
save, and does not claim a provider result.

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
`tools/zg361_phase2_hc_workforce_route_b_checkpoint.py`. The focused formal
producer is
`run_zhongguo_acceptance.py --phase2-hc-workforce-route-b-capture-live`; the
separate `--phase2-hc-workforce-route-b-live` entry consumes a
`zg361_hc_workforce_route_b_checkpoint_registry` through
`tools/zg361_phase2_hc_workforce_route_b_checkpoint_registry.py`.

## Strict checkpoint producer

The producer starts only under the explicit
`--phase2-hc-workforce-route-b-capture-live` mode. From the canonical paused
seed it verifies the saved subject and date against the seed contract, binds
the seed SHA-256 lineage, dynamically installs and activates the existing
Workforce transition fixture, handles the canonical B2 prompt if present, and
uses the typed subject-to-owner transition to reach the real `zg361we.360`.
The freeze then queries the real event context and requires option B (native
index 1) to be shown and enabled, alongside the full three-option surface and
the exact distinct owner/subject scopes.

Freezing alone does not publish a registry. The producer executes Route B
once, requires the existing Workforce provider to prove all 13 postcondition
facts and seal cycle/case identity, restores the pre-B checkpoint, and only
then calls `write_route_b_checkpoint_registry`. The writer reuses the strict
replay consumer as its validator and refuses missing provider evidence,
ACK-only evidence, changed checkpoint bytes, or an existing output file. The
career-HC provider remains default-off in this B4 producer.

No-launch producer preflight:

```powershell
& .\tools\.venv\Scripts\python.exe tools/preflight_zg361_phase2_hc_workforce_route_b_capture.py
```

The future explicit live command is:

```powershell
& .\tools\.venv\Scripts\python.exe tools/run_zhongguo_acceptance.py `
  --phase2-hc-workforce-route-b-capture-live `
  --phase2-hc-workforce-route-b-checkpoint-output <NEW_PRE_B_CK3> `
  --phase2-hc-workforce-route-b-registry-output <NEW_REGISTRY_JSON> `
  --phase2-seed-contract <CANONICAL_SEED_CONTRACT_JSON> `
  --bridge-dll <EXACT_BUILD_DLL> `
  --bridge-injector <EXACT_BUILD_INJECTOR>
```

Both output paths are mandatory, must differ, and must not exist. Supplying
output paths without the explicit capture-live mode is rejected before bridge
resolution or CK3 launch.

## Strict registry and replay entry

The registry must already contain the complete GREEN freeze object and its
provider-sealed Route-B postcondition object. Before resolving the bridge or
crossing the CK3 launch boundary, the runner verifies:

- `evidence_class=real_ck3`, fixture provenance is explicit, and console use is
  false;
- the checkpoint archive still has the recorded absolute path, byte count and
  SHA-256;
- the freeze happened on `zg361we.360` before option 2 and the typed
  subject-to-owner transition retained the same date;
- the native save receipt matches the archive and exact owner;
- all 13 Workforce facts are provider-sealed to one owner/subject/cycle/case;
- the option response remains an ACK with
  `business_receipt_claimed=false`;
- registry seed lineage and source Git commit match the requested run.

After the product-only seed loads, the entry installs the existing transition
fixture and recomputes the current product/fixture projection. A mismatch is
RED before any registered save is restored. A match allows the dedicated
managed restore, one case-bound Route-B execution, a hash-identical checkpoint
restore, and a second Route-B execution that must reproduce the sealed
owner/subject/cycle/case tuple.

The B6 provider is deliberately default-off. Add
`--phase2-hc-workforce-enable-career-provider` only when the exact-build
capability has been deliberately advertised for the live attempt. Without the
flag, both passes write the typed reason
`career_hc_live_gate_default_off`; with it, both passes require a same-frame
provider-observed B6 result.

No-launch static preflight:

```powershell
& .\tools\.venv\Scripts\python.exe tools/preflight_zg361_phase2_hc_workforce_route_b_live.py
```

It reports the entry itself GREEN while the nested live gate remains RED if no
qualified registry was supplied. A real replay command is:

```powershell
& .\tools\.venv\Scripts\python.exe tools/run_zhongguo_acceptance.py `
  --phase2-hc-workforce-route-b-live `
  --phase2-hc-workforce-route-b-checkpoint-registry <REAL_REGISTRY_JSON> `
  --phase2-seed-contract <MATCHING_SEED_CONTRACT_JSON> `
  --bridge-dll <EXACT_BUILD_DLL> `
  --bridge-injector <EXACT_BUILD_INJECTOR>
```

Do not add the B6 enable flag to the first replay merely because its transport
exists. Transport wiring, capability ACKs, or an M360 option ACK are not the
provider postcondition.

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

The read-only artifact search performed for this entry found no qualified
`zg361_hc_workforce_route_b_pre_action_checkpoint` or paired Route-B
postcondition artifact under the current `zg361` process-assets tree. The next
CK3 run must therefore execute the strict producer above; an older B2 save,
static preflight JSON, or product effect file is not a substitute.

That run must use a hash-bound current cumulative product projection,
activate the existing Workforce fixture, and pause on the real
`zg361we.360` before Route B. It must retain the archive, freeze report,
Route-B ACK, Workforce provider sidecar, optional career-HC provider sidecar,
restore receipt and provider replay. Until those artifacts exist, readiness
remains `static-ready-live-pending`.

Offline verification:

```powershell
py tools/test_zg361_phase2_hc_workforce_route_b_checkpoint.py -q
py tools/test_zg361_phase2_hc_workforce_route_b_checkpoint_preflight.py -q
py tools/test_zg361_phase2_hc_workforce_route_b_checkpoint_registry.py -q
& .\tools\.venv\Scripts\python.exe tools/test_zg361_phase2_hc_workforce_route_b_live_entry.py -q
& .\tools\.venv\Scripts\python.exe tools/test_zg361_phase2_hc_workforce_route_b_capture_preflight.py -q
py tools/zg361_phase2_hc_workforce_route_b_checkpoint_preflight.py
& .\tools\.venv\Scripts\python.exe tools/preflight_zg361_phase2_hc_workforce_route_b_live.py
& .\tools\.venv\Scripts\python.exe tools/preflight_zg361_phase2_hc_workforce_route_b_capture.py
```
