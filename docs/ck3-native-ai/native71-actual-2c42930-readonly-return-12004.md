# Actual2C42930 read-only return resolver, CK3 1.20.0.4

Recorded 2026-10-10T12:28:30.429752+00:00. The actual95B function and its sole192B child are
source closed. The candidate implements the return pointer from copied raw
loads. Native compilation and the single new connected compound have not run
in this worker; central03/10 owns that qualification.

## Actual source

The held pdata row is [0x2C42930,0x2C4298F), with span SHA-256
`b6f45709084364156e00538b9fc69be9895627a493317c8ad754d0ba6ca39d11`. Existing Z named cache was reused read-only;
this worker acquired zero new binary bytes. Source is frozen in
[SOURCE-FREEZE.json](SOURCE-FREEZE.json), and exact instructions are in
[ACTUAL-2C42930-INSTRUCTIONS.txt](ACTUAL-2C42930-INSTRUCTIONS.txt).

Actual2467660 CALL24676B4 passes the selected Title in RCX. Actual2C42930
CALL2C4293F passes that Title in RDX and an out32 pointer in RCX to2C42820;
the parent consumes the written uint32 and ignores native RAX. Child22c source
is192B including4 padding bytes, span SHA-256 `01ea0535f38635ca1057aea31af076aad1c49762a60287310f01afe01dbfff17`,
and has no child CALL. Its read-only software adapter supplies all raw32
results, includingFFFFFFFF. A missing load is not a manufactured sentinel.

## Implemented branches

Only childoutFFFFFFFF replaces the requested ID with originalTitle+128.
Character registry global5C67568 uses the requested low24 index, unsigned
count at+2C, table at+20, stride16 pointer at+8, and full32 equality at
candidate+18. Null registry, out-of-range index, null candidate, or generation
mismatch selects lazy fallback global5C67570. A table pointer of zero has no
native fallback branch, so an unavailable candidate load remains unavailable.

The matched route does not read Title+128, fallback global, or candidate magic.
Fallback returns its raw pointer, including zero, without magic/identity
validation. Those guards belong to the actual caller06c/17c. No holder, tax or
yield semantics are inferred from the return pointer.

## API and one new qualification

New header `xar_bridge/construction_actual_2c42930_return_12004.hpp` exports
`RawTitleReturnAccessV1` and `ReadActual2C42930ReturnV1` in namespace
`xar::ck3_12004::construction_owner_mode3`. Caller22 binding uses
`ReadTitleSelectedFullIdAdapter12004` with child context pointing to a
`TitleSelectedFullIdAccess12004`; both readers share the caller's explicit
memory snapshot, module base and exact-build binding. Native getters are never
invoked. `observed` distinguishes an available returned pointer from unknown
input; per-field flags preserve genuine zero and all-ones source values.

No-main focus exposes `RunActual2C42930ReturnFocus12004`, failure label and
attempted case count. Fifteen cases cover high generation and zero/all-ones IDs,
sentinel-only substitution, lazy reads, four actual fallback branches, observed
null return, and missing input that must remain unknown. This narrow focus uses
an opaque counted child-output provider; the new03c compound must also bind
the real22 ->38 ->06 software path. Worker compile/run counts are zero.

Full new-file patch, exact candidates and pins are in [DELIVERY.json](DELIVERY.json).
38 adds no production TU;22 owns its existing new child TU and60 handles shared
CMake. Source/runtime evidence is not a current game or live-path acceptance.

## Storage

The worker leaf uses the common policy1.0.0 and a4MiB suballocation under
central10's Root-approved ledger. Current necessary candidates/source records
are protected for at most168h; protection does not renew automatically. Task
close records volume capacity and leaf size. No Z/Git/Game files were changed.
