# Guardian current-family relation projection, CK3 1.20.0.4

The existing Guardian family query gains an owned `current_family_relation_v1`
child in its private `guardian-two-factory-source.json` sidecar. It resolves the
same query's played character and current first heir with their complete DWORD
IDs, then evaluates the source-closed lower relation algorithm for the two
current factory keys. A known `false` is available and can make the pair ready.
An unreadable reached input, unsupported negative count, changed reached cell
or changed enclosing frame remains unavailable.

This is a software projection of actual source, with
`source_projection_only=true`, `native_trigger_invoked=false` and
`parsed_target_observed=false`. It does not create a scripted trigger receiver
or call the original C8 method, its expression evaluator, a factory, an
allocator or a native predicate. The legacy top-level
`guardian_membership_observed=false` and `source_discovery_only=true` continue
to describe the earlier factory/template observation. The new child's
`available`, `raw_value` and `ready` describe its separate consumable value;
those legacy flags do not suppress it.

## Source and direction

Actual `4217820` gates the target character tag `0x43686172` and the root and
target QWORD fields at `+1D0`, then reads root `+1B0`. Actual `2949A80` searches
that extension's `+8` data and signed DWORD `+14` count in 16-byte records,
using the full unsigned target ID. Its final check is `target < selected_key`;
the projection retains that literal comparison and does not add an equality
test. A zero count or source-null returned pointer yields known false.

Actual `2596930` reads the returned peer's QWORD `+20` data and signed DWORD
`+2C` count in 40-byte entries, selecting predicate `25942B0` with mode zero.
The predicate first compares the entry's full QWORD to the current factory
`+18` raw bits. If unequal, it reads the stored entry pointer's `+220` data and
signed DWORD `+22C` count in 16-byte rows. Every reached nonempty row list reads
fallback global `5D1EBF8`. BYTE `row+C == 2` selects QWORD `row`; other tags
select the fallback bits. Equality preserves zero, duplicates and full pointer
bits, without dereferencing the wanted factory value. These offsets and tags
are not assigned an inferred guardian/ward object or hierarchy meaning.

The explicit direction is `played_to_current_first_heir`: resolved current
played root, current first-heir full-ID lookup, returned peer, then each
current named factory's raw comparison input. It is not a claim that the
original parsed trigger selected that target or returned that result. Parent
selector `A03A30` and expression evaluator `3755500` are retained source
context; the latter's positive-count configured-expression output is not
needed or fabricated by this independent lower projection.

The parent root-storage RIP transcription was corrected from retained
instructions to actual `5C67568/5C67570`. The current software resolver uses
the existing storage slot, unsigned low-24-bit index and complete DWORD
generation match at character `+18`. Historical R93/R94 name IDs, addresses
and descriptors are evidence only; production uses the current same-query
values.

## Collection and wire

`ReadGuardianCurrentFamilyRelations12004V1` reads through the existing
`GuardianFactoryReadEnvironment12004V1::read_memory` provider. It preserves
every successful reached scalar cell and rereads those cells before accepting
the sample. Existing read-provider behavior and budget apply. No new count,
byte, probe or trace threshold is introduced. No latency has yet been measured
for this new observer.

For a positive relation count, each row binds current factory `+10` to its
own lookup `record_name_id` and current `+18` to the copied raw input. The
record ID need not equal the lookup name ID; map ID still binds the name ID.
An empty relation array returns false without demanding an unused descriptor,
vtable, RTTI or fallback read. Negative counts are outside the supported
projection domain and remain unknown rather than becoming empty.

The unchanged job boundaries require the exact executable, paused execution
stamp, matching before/after snapshot and matching worker completion snapshot.
The new owned value is collected inside those boundaries using the same
request, revision, date, played character and first-heir IDs. An unqualified
completion emits requested IDs as uint32 bit patterns, null raw pointers and
unavailable rows; it does not export stale values.

The child includes requested complete IDs, nullable resolved addresses, target
tag and state fields, `identity_round_trip`, `sample_stable`, `ready`, and two
fixed-key rows. Each row carries `available`, `raw_value`, its reached source
basis, unavailable reason, mode zero, descriptor reachability/raw bits and
nullable peer/count facts. Ready means qualified completion, stable identity
and both values available. Python validates the same-command bindings and
returns the owned child with `guardian_pair_ready=child.ready`. Legacy sidecars
without this child keep the previous behavior.

## Source receipts and qualification boundary

The source package references the immutable 373-byte parent and root-RIP
correction, 138-byte `2949A80` full-CFG contract, 159-byte `2596930` contract,
92-byte `25942B0` complete contract and 131-byte selector contract. The package
manifest records their exact paths and SHA-256 pins. Existing R93/R94 observed
factory inputs and the old 5-native/19-Python qualification are reused as
history and are not replayed.

The new native fixture authors nine cases: true, empty false with an unreadable
unused descriptor, changed complete IDs, generation mismatch, changed scalar
bookend, zero fallback match, unsupported negative peer count, changed query
after-snapshot and changed completion snapshot. The new Python fixture consumes
their production serializer wires; its first case follows the existing driver
and private transport once through a fake response.

The sole new joined qualification passed on 2026-10-10 UTC: one new scene TU
compiled and linked, nine native scenes passed once, and the new Python
consumer passed 21 checks once. The first compile failed because a scene
pointer constant reused a helper string's name; the original bytes and C2371
receipt were retained, and only that identifier was renamed before retry.
Production header pins stayed unchanged. Actual result
`guardian-readonly-stage01/first-joined01/repair02/RESULT.json` is 19162 bytes,
SHA-256 `19b9a84a6ddd28df8be726b94932e1c3a494054868bc752a2257021ebdaea80b`.
The package also pins all nine emitted production wires and the Python
`FOCUSED-VALIDATION.json`. No old 5/19/31 cases ran. This proves the owning
source projection and same-job wire consumption on synthetic memory; no new
live relation value is claimed until Root builds and performs a fresh same-MCP
capture. Exact-EXE Defender settings remain independently pending because the
manifest helper required actual CL producers for reused objects; no settings
operation was issued and no provenance was fabricated.

## Permanent repository entry

Native scene main:
`ck3_autonomous_player/native_bridge/tests/guardian_current_family_relation_12004_new_cases.cpp`.
Consumer entry:
`ck3_autonomous_player/tests/unit/guardian_current_family_relation_same_job_v1.py`.
These are the actual qualified sources, not the earlier factory-input fixture.

The repository-relative reproduction recipe is:

```json
{
  "native_main": "ck3_autonomous_player/native_bridge/tests/guardian_current_family_relation_12004_new_cases.cpp",
  "native_language": "C++20",
  "compiler_profile": "same configured actual .4 Bridge definitions; /MD /EHsc /W4 /WX /permissive- /utf-8 /O1 /Gy /Gw /UNDEBUG; NOMINMAX",
  "include_root": "ck3_autonomous_player/native_bridge/include",
  "production_object_sources": [
    "ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp",
    "ck3_autonomous_player/native_bridge/src/appointment_window_snapshot_v1.cpp",
    "ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp",
    "ck3_autonomous_player/native_bridge/src/appointment_character_level12004.cpp",
    "ck3_autonomous_player/native_bridge/src/zhongguo_case_snapshot_v1.cpp"
  ],
  "libraries": ["xar_ck3_12002_runtime", "xar_bridge_protocol", "bcrypt", "user32", "kernel32"],
  "link_options": ["/MACHINE:X64", "/INCREMENTAL:NO", "/OPT:REF", "/OPT:ICF"],
  "native_arguments": ["<fresh-output>/wire"],
  "consumer": "ck3_autonomous_player/tests/unit/guardian_current_family_relation_same_job_v1.py",
  "consumer_arguments": [
    "--source-root", "<repository>",
    "--candidate-src", "<repository>/ck3_autonomous_player/src",
    "--source-freeze", "<fresh-source-pin-receipt>",
    "--wire-root", "<fresh-output>/wire",
    "--output-directory", "<fresh-output>/python"
  ]
}
```

Resolve provider object and library paths from the current successful Bridge
build receipts. Preserve the actual configured definitions rather than
inventing a Runtime-only link. The exact qualified run reused those five
production objects and the two libraries in place and compiled only the new
main. Keep a fresh external source-pin receipt for the actual driver/private
transport imports used by the Python entry. The recipe introduces no CMake
target, macro, existing suite run or game dependency. Its current qualification
is the result above; another machine/build is a new execution with its own
storage admission and receipts.
