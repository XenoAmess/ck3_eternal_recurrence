# Prisoner current cost variant at 3755500

This leaf binds the current CK3 1.20.0.4 / Steam25734779 source with executable
SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The exact 842-byte body is `[03755500,0375584A)`, source SHA
`76665f652651c1163f17a684ff8ada07d2b037fa3ef25e1c88cdcbce91089115`.
One cache-first finite acquisition read these 842 bytes into the shared D cache;
no old executable, Game, SDK, broad scan or previous qualification was used.

The actual parent `9D7060` calls this child at `9D7252` only after the dynamic
mode is nonzero, the provider at `+B8` and named definition at `+A8` are null,
the actor/R9 path is null, and the lane's signed DWORD at `+14` is nonzero.
Negative count is included in that literal branch. RCX is `lane+8`, RDX points
to the parent's stack variant, R8 is the internal source alias shape, and R9
is the parent's descriptor. Actual stack arguments five and six are BYTE0
and DWORD0. The parent consumes the returned WORD tag at variant `+0`: tag1
selects the signed QWORD at `+8`; a known other tag selects lane `+98`.
An unknown child result cannot select that fallback.

The child reads list count at receiver `+C`. Count0 writes tag0 and payload0
without reading the scope. For a nonzero count it copies sixteen bytes from
the primary scope pointee. With the actual skip DWORD0, negative count returns
those copied sixteen bytes. The readonly API preserves the raw WORD tag and
signed payload, and exposes a numerical cost candidate only for tag1.

A positive count reaches sixteen-byte list rows. The receiver in each row's
first QWORD has a virtual `+30` type-mask method and `+20` value producer.
The type-mask uses the current variant's WORD tag; the producer receives the
copied internal aliases, the current row identity and a descriptor selected
from the inline receiver `+70` when its first QWORD is nonzero, otherwise the
actual R9 descriptor. The actual targets of these two virtual methods remain
unclosed. The API copies their current identities and bounded input witnesses
but invokes neither method. The positive path remains unknown, distinct from
a known tag0 or a known nonnumeric tag. Direct calls in the remaining body are
error/formatting/diagnostic paths, and provide no substitute numerical value.

`ReadPrisonerCostVariant3755500Readonly12004` requires the shared copied query
frame and preserves its exact image, revision, sequence, proof epoch, date,
full character IDs and context identities. It creates no clock or physical
internal alias address. A source-defined copied alias shape may have no
physical internal identity. Missing fields and failed guarded reads stay
unavailable. The list count is copied again to reject a changing conditional
input. Dynamic observations are bounded to the first reached row.

The new cases file has no main. Its twelve cases return a check count to 35's
single new connected quote fixture. Central10 owns compilation and execution;
this leaf does not run an independent fixture or replay the Army journal.
Until its fresh parent compound result arrives, validation is authored and
not run. This projection grants no native-entry, actual quote-completion or
selected-expression credit.
