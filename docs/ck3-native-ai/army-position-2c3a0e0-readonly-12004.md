# Current Army position condition 2C3A0E0, CK3 1.20.0.4

The real `2C097F0` position predicate reaches `2C3A0E0` at `2C09993`
after its earlier predicates return false. Its setup is `RCX=holder` and
`RDX=actor`, both resolved Character objects; the caller tests the returned AL
at `2C09998`. This final direction is holder toward actor. It cannot be
substituted with actor toward holder or an Army pointer.

Source identity is CK3 1.20.0.4, Steam build 25734779, held executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The complete main body is its actual pdata interval `[2C3A0E0,2C3A18C)`,
172 bytes. Its only callee is actual `28BFCD0`, called independently at
`2C3A0F8` and `2C3A11C`. That leaf has no exact pdata record: bounded reads
closed its 103-byte body through the RET at `28BFD36`. Total new finite source
acquisition was 300 bytes in three nonoverlapping named cache spans. No older
executable, whole image hash, section scan or old qualification was used.

The external package is
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-62b`.
`SOURCE-CLOSED.json` freezes both reviewed bodies and the actual caller packet
from `continuation-34b/readonly-dependency-source01/unit-position-predicate-2C097F0.json`.
`INPUT-FREEZE.json` pins this leaf and the shared guarded-read access header
owned by 34b. The earlier 62 actual-context copier qualification is separate
and is not repeated here.

## Exact conditional reads

`28BFCD0` first reads the current object's QWORD at `+1C0`. Null selects the
actual loaded fallback QWORD at image RVA `5C67570`. Nonnull reads
`state+1C8`, then that pointer's `+28` candidate. The candidate must have
DWORD `+1C` equal to `43686172` (`Char`) and DWORD `+18` different from
`FFFFFFFF`; otherwise the leaf returns its original input object.

A nonnull candidate `+1D0`, or a null candidate `+1C0`, also returns the
original input. Otherwise the candidate's `+1C0` state leads through another
QWORD `+1C0` and QWORD `+28` to a secondary object. A valid `Char` secondary
with ID different from `FFFFFFFF` returns the original input; a secondary
with the wrong tag or invalid ID returns the candidate. No registry lookup,
low-24-bit ID match, native getter or additional callee occurs here. Pointer
roles are described by their literal offsets without assigning unproved
game relationship names.

The main predicate obtains the first result, checks its `Char` tag and full
DWORD ID, and returns false if the result is invalid or is the current object
itself. If current and actor pointers differ, it calls the same leaf again
on current. This second result is independently read. When its valid full
DWORD `+18` equals actor DWORD `+18`, a nonzero DWORD in current's primary
`+1C0` state at `+1EC` grants true. Only a null primary state selects current
QWORD `+1D0` and its nonzero DWORD `+74`. A present primary with zero `+1EC`
does not fall through to the alternate state.

If the condition did not grant true, current becomes the first leaf result
and the loop repeats. Generation bits are retained in the complete 32-bit
comparison. Legal zero IDs and any nonzero activity DWORD are not narrowed
or interpreted as signed thresholds.

## Readonly implementation and integration

`ReadArmyPosition2C3A0E012004(access, holder, actor)` reuses 34b's
`ArmyRegularCoreReadonlyAccess12004` and returns its optional predicate plus
an unavailable reason. It reads only through the collector's guarded raw
callback. A failed read remains unknown and cannot select the native null
fallback. The configured occurrence bound terminates an incomplete chain
as unknown. The callback's shared frame read budget remains owned by 34b.

34b calls this leaf only at the source-required final branch of its current
B position frame. It supplies the current resolved Character holder and
actor; the result does not prove that the native predicate or a historical
callback ran. 59d owns Service wiring, 55 owns bridge installation, and 60
owns CMake. This package changes only its independent new files in D.

## Verification

The exported `RunArmyPosition2C3A0E012004Cases()` has no standalone main.
Its 12 finite modeled cases cover call direction, full generation IDs,
actual loaded fallback, demanded primary/alternate reads, invalid object
domains, independent repeated leaf reads, unknown failures and bounded
cycles. Central 10 executed these new cases for the first time through the
34b/33 connected phase fixture at
`continuation-33b/root-fixture-retry03/RESULT.json`. The final compile and run
exited zero; all current frozen source pins, including this header and both
translation units, remained unchanged. The receipt records two compiler
invocations and one fixture invocation for this affected retry. The earlier
fixture alias failure and its correction are retained by the compound owner;
the old 62 context-copy fixture was not replayed. No new Game or live-history
credit is claimed.

The compound EXE's Defender registration remains pending: its recorded
settings request rejected the MSVC source provenance. The offline GREEN
result does not assert that a permanent exclusion was installed.
