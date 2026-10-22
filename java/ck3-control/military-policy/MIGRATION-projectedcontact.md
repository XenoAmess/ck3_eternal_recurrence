# Projected Contact Java leaf

This package migrates `normal_army_projected_contact_v1.select_normal_army_projected_contact_v1`
and its strict `bridge.projected_contact_contract` normalization into
`org.xar.ck3.control.military.projectedcontact`. It selects a successful current
native query against the target's **current** state. It does not calculate
distance, ETA, arrival probability, future army membership or combat odds; the
Python source contains no such arithmetic or rounding. `date_raw` remains an
opaque signed int32 native clock value, and native revision remains exact
positive uint64 via `BigInteger`. No conversion to days or floating point occurs.

`ProjectedContactPolicy` provides immutable records, sealed query/selection
states, canonical query tokens and the pure selector. `ProjectedContactCodec`
validates JSON token kinds before constructing these records. The input wrapper
has exactly `snapshot`, `query_rows`, and `request`. Snapshot, diagnostics,
history rows and query result envelopes are explicit projections from extensible
legacy containers; this leaf does not reject unrelated fields in those objects.
The native scope and new request wrapper have exact field sets. Required nullable
owner and selected Combat fields distinguish missing from explicit null. Integers
reject booleans, floating tokens and strings. Public CUnit slot zero is valid;
native CArmy, owner, Province and Combat identities remain positive int32.

Selection scans history newest first, skips failed, malformed, noncanonical,
stale or mismatched evidence, and may reuse an older same-frame valid query.
Binding includes snapshot ID, public and native revision, connection generation,
episode, native date, subject, target, incoming edge, current subject position
and optional owner. The scope preserves original array order, uniqueness and
disjoint sides. A `join_existing` projection binds the selected native Combat
identity and array index and requires the subject to be appended last on its
native side. A new incoming defender retains its actual incoming edge as contact
geometry; it does not invent the opposing attacker's entry.

Every available result preserves `actual_arrival_observed=false` and
`future_contact_authorized=false`. `incoming_attacker_geometry_ready` is true
only for `create_new` with subject side attacker. A complete `none` carries no
contact participants. No Game, RPC, ledger, file publication or HTTP owner is
introduced by the leaf.

The one-time Java capture utility invoked the unchanged actual Python producer
using the committed 1.20.0.4 source fixture helpers. Its checked-in
`src/test/resources/projectedcontact/producer-golden-v1.json` contains 30 inputs
and actual outputs, producer/source hashes, observation time and machine ID.
The capture machine was independently read with `tools/ck3_live_run_id.py machine`:
`xenoamess-full-tower-eb9d2c1186`. These are synthetic source inputs, not native
capture, actual movement or game qualification. Default JUnit reads this committed
golden and has no Python process or untracked oracle dependency. Ten JUnit methods
cover all golden cases, exact uint64 maximum, public slot zero, ordering,
immutability, wrong numeric tokens, missing/null, duplicate JSON keys, unknown
fields, malformed scope and serialization round trip. Initial execution belongs
to Root/M7's coordinated Maven reactor, not this source delivery.

The sole direct production consumer is `strategy.py::_general_battle_forecast_ingress`
at the existing endpoint branch, after the independent contact-free first-hop
branch. It projects effective commands after the latest restore and life advance,
then maps `query_required`, `none`, `join_existing`, new attacker and new defender
into its existing routing/model paths. The existing whole-consumer tests are
`test_normal_army_projected_contact_consumer_12004.py` and
`test_incoming_defender_service_compound_12004.py`; mercenary strategic reserve
also consumes the preserved native scope independently. Those consumers have
not yet been switched to Java by this source package. The outer host must preserve
history filtering, capability fallback, defender constructor raw0 and active
Combat resume boundaries during that switch. No silent Python fallback is added.

Status at source freeze: Java source and actual producer golden prepared;
coordinated Java compilation/JUnit, real consumer adoption and live testing
remain separate required results. Source fixture equality cannot grant native
or saved-day credit.

The first coordinated `java06` execution reported three failures in floating
negative cases. The test JSON tree had removed trailing BigDecimal zeros before
re-encoding, so `11.0` and `9.0` reached production as integer tokens. Source
freeze 02 changes the test mapper to preserve decimal scale and checks the exact
outgoing negative tokens, including a direct raw-byte regression. The original
producer golden and production integer guard remain unchanged. A fresh coordinated
execution is required; the preserved first failure is not reclassified as a pass.
