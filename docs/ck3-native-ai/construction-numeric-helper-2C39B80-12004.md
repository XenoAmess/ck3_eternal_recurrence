# Construction aggregate numeric helper2C39B80

This source tree is fixed before candidate code. Exact source is CK3
1.20.0.4 / Steam25734779, retained SHA256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The actual reached helper body is431B `[2C39B80,2C39D2F)`, exact retained
runtime-function row `[46373760,46374191,84973024]`. Source acquisition used
the unchanged finite mapper with canonical sharedD cache and existing
O_EXCL range claim: one new431B read, no old executable or new pdata read,
whole executable hashing, section scan, Game or SDK operation.

The actual parent is the already held2468DA0 aggregate. LiteralCALL246905F
passes RCX as the stack output qword address, and RDX as the qword reached
through the slots receiverF0 context and context848. The helper saves RCX
in RBX, moves RDX into RCX, and CALLs24CEF10 at2C39B8C. The incoming R8/R9
are not consumed: their first uses write source-defined values. This is an
actual two-argument output/receiver ABI; no null extra argument assumption
is needed. The original writes its final signed-qword bit pattern through
RBX and returns that same output pointer.

The child24CEF10 returnEAX is explicitly sign-extended at2C39B91. The
source-defined numeric input is therefore signed32, with no object type or
domain meaning inferred from the receiver848 chain. That168B child has
retained exact row `[38596368,38596536,84973024]` and is a separately owned
necessary source dependency assigned by coordinator02. Its raw reader must
be source-closed before its value can qualify this helper's computed output.
This lane does not acquire or expand the child tree itself.

The helper multiplies the signed32 child value by100000, then combines it
with the signedQ64 loaded by MOV2C39BA0 from RVA5C69450. The first arithmetic
stage is the exact100000-scaled fast/minmax wrapped64 path already held in
03c's `SignedScaleProduct100000V1`. It keeps that existing implementation
and multiplication order. The second stage scales by100000/divisor10000000,
using a source-defined fast bound53E2D6238DA3 or the exact decomposed slow
path. Finally it adds100000 with native64 bit semantics. The parent consumes
this first stack qword and subtracts100000 at2469069. Neither this helper
output nor its isolated scalar is an independently attributed building
yield, realized benefit, recipient transfer or NET value.

The new input reader reuses03c's `LoadedInputAccessV1` and `ReadOffsetV1`.
It qualifies the existing Province ownerID and slots620, copies the context
F0/receiver848 chain and exactQ64 scalar, and checks the identities and
scalar again after capture. These are read-only current-frame operands;
they are not a capture of the original MOV-consumed value. A separately
supplied child result must retain the same exact sourcepin, receiver,
Province/slots/context and source-frame coordinate. Missing or mismatched
child proof leaves computed output unavailable instead of synthesizing0.

The raw loaded operands and their independent failures are still useful
before child closure. The consumer invokes no original helper, getter,
context constructor, SDK or publisher. Unknown receiver type, authored
scalar key, child meaning and per-building attribution remain unresolved.

Candidate code and no-main owned cases are externalD-only.03c composes
these inputs with the other actual children;10 owns the first connected
verification batch. No old19 natural-conception compound or old gate is
replayed. Source closure and an owned arithmetic check do not qualify a
Game hit or runtime construction benefit.
