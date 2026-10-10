# Retained incoming caller source binding

`conception_incoming_caller_sourcebinding_12004.py` consumes the already copied
19b `SerializeConceptionPairPassiveJournal12004` events. Construct
`CallerSourceResolver.from_held_metadata()` once. Then call
`bind_owned_journal(journal, image=ExactImage(version, executable_sha256,
module_base), resolver=resolver)` with the existing same-query journal. No second
query, listener, native call, executable read or live pointer dereference occurs.

The resolver pins the existing held `.4` PE metadata and runtime-function JSON.
It does not copy their 7 MB table into this packet. It normalizes the supplied
ReturnAddress against the admitted actual module base and checks an optional
retained RVA against it. It binary-searches the pdata row containing `RA-1`,
because the retained return PC names the instruction after a CALL.

The result separates metadata ownership, finite literal sourceproof and semantic
role. A pdata row names an extent and unwind RVA; it does not necessarily cover a
complete source function. For example, the entry `0x2929B40` begins the held
ordinal141383 row `[43162432,43162699)` although the existing reviewed physical
candidate source span covers664B. Neither extent supplies an incoming caller.

The current production proof registry is empty. Every valid metadata match
therefore returns `metadata-bound-source-unknown`, `literal_call_status=unknown`
and `monthly_or_stage_role=unknown`. Unreadable/absent source is unavailable;
metadata gaps are `unknown-source`. Fixture origin, process/thread/event keys,
original-once status and the journal owner's session guard are retained. This
consumer never verifies natural observation itself. Raw R8/R9 and native pair
orientation are left in the original record and do not become scheduling roles.

The future finite sourceproof factory requires a manually reviewed exact-build
contract, source SHA, the same pdata owner row and full bytes of that admitted
row (maximum8192B). It checks decoded instruction boundaries and an actual
five-byte `E8 rel32` ending at the retained RA and targeting `0x2929B40`. It does
not search the image for E8 byte patterns. Indirect calls and tailcall paths stay
unconfirmed by this direct-CALL factory. A sourceproof still leaves monthly or
stage semantics unknown until the actual upstream roles/date/scheduler source
is reviewed. Synthetic mechanical decoder cases cannot enter this registry.

Missing next source is concrete: Root's future unique authorized passive Game
window must retain a natural original `0x2929B40` event's caller_return_pc,
optional caller_return_rva, exact module base/SHA, process/thread and event key.
Only that observed address determines the next finite metadata row/source read.
After confirming its CALL, source its actual RCX/RDX/R8/R9 producers and loaded
date/clock/scheduler use. No natural caller address is held in this packet.

The standalone CLI accepts only a retained journal file plus explicit exact
version/SHA/module base and exclusively creates an external result file. It
cannot install or invoke a native observer. Root19/55 own runtime and query
integration; this packet supplies an immutable consumer.

Qualification is one central10 invocation of only the new sourcebinding fixture.
Old candidate/datehelper tests are not replayed. Plan hashes validate record
structure and held file identity; they do not establish native monthly behavior.
