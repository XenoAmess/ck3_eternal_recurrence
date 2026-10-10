# Construction mode3 M4 raw-memory model, CK3 1.20.0.4

Actual `24697C2` sets `DL=1`, `24697C4` restores the saved actual
`2467660` receiver into RCX, and `24697C9` calls `28B9300`. The parent
reaches this call only through its context predicate and selected Title
`+130 == 0`, `+12C == FFFFFFFF` conditions. The source executable pin is
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.

The four-byte `.pdata` row is a prologue fragment. The actual body is 109
bytes through `RET28B936C`; a 128-byte bounded literal acquisition retains
its padding and the next function's beginning, which are excluded from the
109-byte semantic body. No global version delta or function length was
inferred from that row.

For DL1, `CALL28B9315` returns the 28B7450 count in EAX, then the caller
restores the original receiver and `CALL28B931F` obtains the 28B71E0 count.
The first subtraction wraps in 32 bits. The caller rereads receiver+1C0:
null supplies minimum1, otherwise DWORD[nested+3D8] is interpreted as
signed32 and the minimum is its signed maximum with1. The second
subtraction also wraps in32 bits, and the literal return is its signed
maximum with0. DL0 is outside this mode3 API. The parent alone owns the
positive-EAX Q64 scaling from loaded globals5C69470/5C69488 and R15.

The owned 28B7450 model follows all stored occurrences, including repeated
raw FullIDs. Its descriptor is nested+1E0, or the actual static descriptor
module+5459C88 when receiver+1C0 is null. It copies pointer+0 and signed
count+C. Each raw DWORD uses the actual title registry5D1DAF8, low24 index,
stride16 pointer+8 and full ID+10 comparison; failed lookup uses the actual
fallback5D1DAE0. A predicate's nonzero AL increments the count once for
that occurrence. Negative extents and counts above the configured4096
copy budget remain unavailable rather than becoming an empty list or a
native rejection claim.

28B7370 resolves the Character from Title+128 through registry5C67568 and
fallback5C67570 before evaluating its Title/province gates. Its signed
rank<=1 gate proves that the reached 230F8E0 takes the direct Title+338
branch; the generic rank2 parent traversal is unnecessary here. It checks
province magic50726F76, nonzero BYTE628, Title BYTE130zero and
DWORD12Callones. It reads the Province+620 QWORD separately from passing
the Province+620 subobject address to the 22d predicate. When that
predicate is true and the QWORD's BYTEBC is zero, the actual receiver of
28C2DF0 is the resolved Character. The held predicate2C39EE0 body does
not overwrite R10, so the literal `MOV RCX,R10` retains that Character.
The reused04c object-only resolver copies the returned object's +418;
unequal pointers produce known AL0. Other admitted paths return the
Province's raw BYTE728, preserving its actual byte as well as AL!=0.

The 23d owner supplies the independent 28B71E0 raw-EAX projection; the
22d owner supplies the independent 2C39EE0 raw-AL projection. Both receive
the same immutable uint64 request snapshot revision. The production
adapter matches `Mode3SignedEaxChildV1.read` and keeps its output unchanged
on unavailable inputs. Count0 and EAX0 are successful known results.
Every borrowed pointer stays within the caller's admitted paused main
thread/frame boundary. The API creates no new clock, native call,
initializer, getter, query, or later frame backfill.

The seven held logical bodies and their actual RET instructions are pinned
in external `continuation-13e/SOURCE-CONTRACT-FROZEN.json`. Four bounded
reads acquired633 actual bytes;338B28B71E0,118B230F8E0 and237B28C2DF0
were reused from existing exact caches. Root's shared claims prevent a
second acquisition;22d reuses the47B logical predicate from its128B seed.
The source plan/check and graph describe offline source evidence. They
do not grant or claim live observation.

Fourteen fresh exported cases cover the new memory model, including its
default22d/23d providers producing positive EAX2 with no supplied numeric
stub, raw duplicate/fullID preservation, conditional returned-object
equality, wrapping subtraction, independent missing operands and budget
partial state. The only authorized compile/run is the new03d/10 connected
compound. These cases have no main and have not been executed by13e.
Old13/13b/13c/34 fixtures and qualifications remain unchanged; no live CK3
or Game qualification is claimed by this delivery.
