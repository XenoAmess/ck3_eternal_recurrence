# R501/R502 `travel_completion_event.1000` RED and reusable contract

Date: 2026-09-12 (Asia/Shanghai)

## Live RED

Old round R501 completed frontend warmup and terminated before current round R502/PID `149584` started. R502 was the sole CK3 process and passed loader, native, exact-mount, and material-error gates. It first drained the already reviewed `stress_threshold.1011` and `trait_specific_interactions.0011` events, proving both earlier contracts in live execution. After 21 game days it preserved a new pre-selection RED on `travel_completion_event.1000`, instance `21`; B1 remained active and `zg361mg.120` was not evaluated.

The direct RED is `E797ABDD300239ADBC9A60F41E7623B6F58E5B7ABA8D6BB97828F21CD24A6A5A`. The frame binds root and `travel_owner` to player `27181`, a distinct `travel_leader_scope` character, two opaque travel-plan scopes, and three opaque province scopes. The event window rendered only native option `0`; no selection was attempted before the contract existed.

## Exact-build decision

CK3 `1.19.0.6` / EXE `2D00FF31...DB86` defines the event at `events/travel_events/travel_completion_events.txt:15-203`, SHA-256 `525D15E8...60AB`. `common/on_action/travel_on_actions.txt`, SHA-256 `7E433A0D...40C`, selects it as the generic `on_travel_plan_complete` fallback and also lists it for abort cleanup.

The authored options are mutually exclusive. Native option `0` is available only when root is already at the default location; it has no explicit action and can only apply a small trait-conditioned stress decrease. Native option `1` is available away from home and invokes `return_home`, with possible small stress gain. The R502 projection therefore selects the sole rendered authored1/native0 route. The common after block only removes `recently_completed_mandala_contract` when present. No faith mutation occurs.

## Reusable asset and focused verification

The campaign-neutral contract binds `$player`, exact scope types/names, the distinct travel leader, snapshot authored count `2`, and the single rendered native index `0`; it does not preserve allocator identities or the live date. Frozen production replay is `22/22` GREEN at `D00237A61767D8A4F5638A346B393568EA06381D83344BF37C6E8E82AC7B6F00`.

The shared catalog advances to 187 events. Source index has 187 definitions, 73 definition files, 527 caller candidates, and 82 caller files; dataset SHA-256 is `FE3A1D8472B14A6901117243A21E7A97E5AD60EE685D03057D5F17BC568F43DC`, file SHA-256 `4A8ECB5576FB5F140EC6FDE08CB8CB185E523CD833D5CE84B8EA34436C706D8D`. Portable evidence advances to 290 blobs and 1,105 references; manifest SHA-256 is `F2D15B19DCEB80BE6EFDE6FCA49DAD2AE6842A49AE37A7F94DB1F6DE00B039E1`.

Focused normal validation produced 114 passes before two stale inventory expectations were corrected; the corrected files then passed 13 tests and 86 subtests. Optimized core validation passed 51 tests and 172 subtests. Source-index byte parity and portable-evidence offline checks are GREEN. The two standalone collection attempts without `PYTHONPATH=src` did not collect tests; the corrected invocation passed and did not expose a code failure. No broad suite or extended CK3 run was added.

This package changes only Python contracts, read-only assets, focused tests, and documentation. It does not change DLLs, game files, launch configuration, load order, or video material. P1 remains `8/9`, and P2 remains `LOCKED` pending a later bounded live attempt that reaches `.120`.
