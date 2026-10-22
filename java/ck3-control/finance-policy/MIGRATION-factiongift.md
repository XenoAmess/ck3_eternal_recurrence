# Faction gift: pure Java decision leaf

The package `org.xar.ck3.control.finance.factiongift` ports the complete pure
`choose_faction_gift_v1` decision from
`ck3_autonomous_player/src/xar_autoplayer/faction_gift_policy_v1.py`.
`FactionGiftPolicy.choose(byte[])` accepts a closed JSON envelope containing
`observations`, `complete_native_enumeration` and `minimum_gold_reserve_raw`.
It produces an immutable sealed `FactionGiftChoice`. This package has no game,
file, clock, network, pending-state or ledger access and does not authorize a
gift submission.

The existing native producer is
`native_bridge/src/ck3_12004_faction_gift_router.cpp::SerializeObservation`;
its observation is consumed by
`faction_gift_formal_candidate_v1.py::choose_private_faction_gift_candidate_v1`.
The latter's caller is
`bridge/faction_gift_private_transport_v1.py::query_faction_gift_private_candidate_v1`.
That caller and `bridge/faction_gift_formal_route_v1.py` keep all same-frame
public-root/private-envelope qualification, stock-threat, checkpoint, pending
verification, native recapture and submission duties. Those responsibilities
have not migrated, and no production consumer has switched to this Java leaf.

The future integration port is a typed in-process invocation from the single
Quarkus host's policy coordinator, after the original native observation has
been qualified. Its result returns to the existing formal-candidate consumer;
the host must never expose an independently submitting gift service. The
planner's pending-verification path remains before any new-spend policy.

Semantics retained:

- Complete enumeration is explicit. Missing/incomplete observations stay
  unavailable; a known empty enumeration remains distinct from unknown.
- Same frame includes snapshot/native revisions, observed date, player and
  wallet. Frame drift rejects the entire vector, including after an earlier
  eligible candidate. The known-denial preview branch does not require cost or
  opinion values for an action that cannot be sent.
- Wallet and reserve use the original `100000` raw gold scale. The caller
  continues to supply military/emergency reserves; this leaf cannot invent or
  weaken them. Exact subtraction accepts equality at the reserve boundary.
- Ratio sorting uses positive `BigInteger` cross multiplication, equivalent to
  Python `Fraction`, followed by leader/member, opinion, faction ID, recipient
  ID and stable first occurrence. No floating-point arithmetic or narrowing of
  the old Python integer domain occurs.
- Old field names and explicit null action fields are retained on output.
  This is a Python-only numeric JSON projection: any later JavaScript-facing
  route needs a separately versioned decimal-string identity contract and
  cannot pass these numbers through JavaScript `Number`.
- `date_raw` and `gift_opinion_modifier_value` are declared native metadata
  outside this leaf's decision inputs. If present, their declared integer and
  nullable-integer types are checked. They are accepted as source metadata;
  `date_raw` never substitutes for `observed_date_raw`. Other unknown fields,
  duplicate keys, missing envelope fields, malformed JSON and excessive input
  are contract errors. Consumed integer tokens reject booleans, floats,
  strings and nulls without coercion, returning the original unavailable
  reason at the corresponding decision stage.

`src/test/resources/factiongift/python-golden-v1.json` was captured by calling
the unchanged original Python producer for 63 cases; all five existing
`test_faction_gift_policy_v1.py` functions were executed during that one-time
capture. The file records exact source/test/projection SHA-256 values. The
0515 candidate is an existing narrow historical observation projection, not a
new native read or an original packet. Its historical machine identity is
unknown; the capture machine is separately recorded as
`xenoamess-full-tower-eb9d2c1186` with observation time. Capture used zero game
RPCs and zero ledger writes. The scratch sampler is not a runtime dependency.

Java JUnit reads the committed golden, checks every producer output, persisted
choice reconstruction and input JSON-domain round trip. Additional cases cover
closed field names, duplicate/trailing input, malformed UTF-8, byte/vector
limits, missing fields and invalid persisted choices. Default tests do not
import or execute Python. Maven compilation/JUnit must be run by the shared
build owner; source completion and golden capture alone grant no compiled,
hosted-CI, planner or live-game qualification and no performance credit.
