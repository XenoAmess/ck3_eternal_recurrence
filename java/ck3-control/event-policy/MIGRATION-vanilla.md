# Vanilla event option projection — Java migration leaf

This package migrates the executable pure closure at
`vanilla_events/policy.py::_option_projection_checks` (lines 880–950 at capture).
It is used by both `_resolve_option_variant_contract` and the final registered
event choice projection. The Java implementation is not a placeholder: it checks
the current rendered order, authored native indices, disabled subset, rendered
flags, snapshot count and native-index-to-option-number mapping, then returns
the selected immutable option and the complete named check set.

`VanillaProjectionCodec.decode` takes a versioned, bounded projection, not the
entire native event context. `VanillaOptionProjection.project` performs the pure
assessment; `VanillaProjectionCodec.encode` emits its typed result. The future
Quarkus host can call this in process; this leaf starts no service and performs
no file, registry loading, Game, RPC, ledger, OCR or action submission I/O.

The binding retains event key, exact build/EXE, registry state and original
registry/index source hashes. Equality is exact, including digest case. A
source-analyzed event with no occurrence contract remains `not_registered` and
retains `contract:null`; it never becomes an automatic selection. Input source
equality checks do not authenticate a registry loader, authorize an action or
replace the existing exact-source review. The adapter must obtain this binding
from the actual registry and source index, never from a player's free text.

The option ABI retains native indices and rendered order separately. Option
number is authored native index + 1; it is not rendered index + 1. Disabled
options stay in the rendered projection. Reversed rows, substituted cancel or
fallback flags, disabled selection and snapshot drift produce blocked results.
Selected rows can still be present on a blocked result, matching the original
helper; consumers must use status and all checks. Every result has
`action_authorized:false` and `semantic_decision_ready:false`, including
`projection_ready`.

The JSON projection explicitly materializes the old fallback rules:
`disabled_native_option_indices` defaults to `[]` before this wire boundary;
`snapshot_option_counts` becomes the legacy plural values, or the singleton
`snapshot_option_count`, or the singleton `option_count`, in that order. Both
arrays are required at this boundary. Missing, null and empty are distinct.
Integers reject booleans, floating tokens, strings and overflow; flags accept
only JSON booleans. Duplicate/unknown/missing keys, trailing JSON values, invalid
UTF-8 and oversized arrays/requests reject before internal records are built.

## Captured producer comparison

The committed `src/test/resources/vanilla/option-projection-golden-v1.json`
contains **15 actual old leaf invocations** using real registry-produced and
materialized contracts: `tgp_travel_events.0030` on 1.19.0.6 and 1.20.0.4, and
`head_of_faith.0100` on 1.20.0.4, each with an exact projection and four drift
variants. Current option rows are explicit synthetic inputs, not observations
from a running game. Golden provenance records original policy/registry/build/
source-index hashes, actual registry/index source anchors and capture time.

Capture machine ID was independently read with
`tools/.venv/Scripts/python.exe tools/ck3_live_run_id.py machine`:
`xenoamess-full-tower-eb9d2c1186`. The one-time operational capture was
`tools/.venv/Scripts/python.exe D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/capture-vanilla-projection01.py`.
It exited 0 and produced 15 cases, 36,723 bytes, SHA-256
`1a624e53a1ee15061e55a96d1c4d16ec7dbffd089549962aa12115cf1980a402`.
This capture is not a new Python production/build/CI module. Default JUnit reads
the committed golden and requires no untracked Python oracle, SDK, Game or
personal scratch path.

Eight JUnit methods compare every old named check and selected row, exercise
serialization round trips and strict types/required fields, order and snapshot
drift, source mismatches, no-occurrence analyzed state, duplicate keys, trailing
data, invalid UTF-8 and duplicate/disabled native indices. Root/M7 owns the
shared Maven verification; this leaf does not claim tests passed before that
actual centralized run.

## Unmigrated consumers and next cutover

Production consumers remain on Python until an explicit adapter and full
consumer verification switch them. The direct call sites of this private leaf
are `_resolve_option_variant_contract` and
`recommend_registered_vanilla_event_option_v1`; one unit-test module also
imports it directly. Public choice consumers include `strategy.py`,
`bridge/r05_supply_observation_case.py` and the registered-event live research
and checkpoint runners; all continue to require the complete old choice result.

Registry loading and materialization, source-index lookup, scope/character and
occurrence-history checks, variant resolution and ambiguity, effect and campaign
utility profiles, outcome verification, fallback selection of unknown events,
and the full registered recommendation are **not migrated by this leaf**.
In particular, the head-of-faith fixture's passing option projection cannot
override its full producer's `registered_contract_requires_extended_consumer`
block. A later cutover must replace the shared helper in both actual consumers,
run the full registered-policy suite and prove the complete producer-to-action-
verifier route. No current frozen runtime/SDK or legacy Python source was changed.
