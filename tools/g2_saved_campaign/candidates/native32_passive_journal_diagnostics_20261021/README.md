# Native32 passive journal diagnostic source candidate

This is an offline source candidate on machine `xenoamess-full-tower-eb9d2c1186`.
Creation time, immutable Native31 input pins and candidate file pins are recorded
in MANIFEST.json. No Native32 production DLL, ABI qualification, loaded-provider
pin or runtime admission exists. Native31 sources, historical evidence and current
deployment remain unchanged.

The candidate replaces only the small observer header/core leaves. It preserves
the Native31 namespace for source integration, but changes Event and Ticket
layout and Enter's signature. This is not binary compatible with existing Native31
objects. A later production qualification must recompile the core, installer,
bridge.cpp and ck3_12002_commands.cpp against the same new header, inspect all
remaining include/ABI consumers, and bind an exact DLL/source/EXE/provider identity.
The unchanged Native31 installer itself does not establish that qualification.

No hook slot is added. Lookup misses retain the observed primary and secondary
addresses, lookup outcome and sampled entry payload through the same invocation's
Return. An address in the last 64 observed retirements is labelled
`retired_same_address`; it does not recover an incarnation, parent, role, key or
request. Missing/retired observations cannot be identity qualified. Eviction,
misses and empty histories do not prove that an address was never seen or executed.
The retirement ring contains addresses and sequence numbers, never retired Tickets.

The original Clone/Delete/Execute/Append calls retain their original forwarding
and exception behavior. Execute's original is called exactly once. No wait,
retry, extra Game call or additional ReadScalar call is introduced. Return's
payload is explicitly an entry observation, not a fresh native return readback.

The Native32 JSON schema uses canonical decimal strings for uint64 identities,
QPC timestamps and pointer fields. Its renamed identity_qualified field has a
single consumer contract; the Native31 schema is rejected by this reader.
The pure Python reader has no endpoint or provider issuance path. Its runtime
qualification guard always rejects until a separately reviewed binding exists.

History selection is explicit:
`{"mode":"all-native-observed-history"}`.
`{"mode":"request-ids","request_ids":[]}` selects nothing.
Historical observer pairs are not current protocol attribution. All completion,
drain, recovery and absence proofs remain false, and credit remains zero.

From this directory, with the repository Python environment:

```text
python -B -m unittest discover -s cold -p test_observer_journal_v1.py
python -B verify.py
```

The C++ fixture is a single host TU including this candidate's actual core and
using deterministic host stubs. It exercises original forwarding, native throws,
active identity, missing/retired addresses, copied entry payload, address reuse,
payload drift, capacity and disabled behavior. It is not a Game, installer,
binary-layout or live timing qualification. Compilation requires a separate
bounded output/TMP/storage admission; no compile is performed by the Python
tests or verifier. A future admitted host build can invoke:

```text
python -B cold/qualify_host_fixture.py --executable <explicit-host-fixture-path>
```

This command validates three actual C++ producer frames with the actual Python
consumer. No executable is discovered automatically. Packaging performs zero
Game calls and does not alter the original failed request or HALT.

Actual results are in [QUALIFICATION.json](QUALIFICATION.json). The first /W4 /WX
host compile failed and remains in build-host/HOST-QUALIFICATION.json. Three
fixture globals were renamed: source to fixture_source, paused to fixture_paused,
and container to fixture_container. The recorded reverse recipe reproduces its
failed preimage exactly. The repaired host build and three C++ to Python frames
passed; Defender readback remains admin-required. This grants no runtime admission.
