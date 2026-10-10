# CK3 1.20.0.4 natural per-Army assault preparation

This leaf observes a naturally entered `2A99B20` and its normal return. It never
requests preparation, placement, allocation, or a province getter. The original
RCX primary CArmyManager and RDX selected CArmy execute once; every returned RAX
bit is retained and forwarded. The return register has no semantic success value.

The build is Steam 25734779, executable SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The actual native pre-date caller executes `CALL 2A99B20` at `2A9A081`, with return
PC `2A9A086`. Full 637-byte producer and 1438-byte caller bodies are held in the
native source cache; no RVA delta, recapture, or new PE scan supplies these facts.

The first six producer instructions occupy 16 bytes: push RSI, push RDI, subtract
48h stack space, retain RCX in RDI, retain RDX in RSI, and move RDX to RCX. They
contain no relative or RIP operand. A 14-byte absolute jump can replace this
whole prefix; the trampoline retains its bytes and resumes at `2A99B30`.

The owned 20-byte entry thunk first executes `mov R8,R15; mov R9,R12` and then an
absolute jump to the typed observer. This preserves the real return address and
copies the caller's iterator/end before a C++ prologue can reuse nonvolatile
registers. The source caller obtains its start at `2A99E76`, computes one end,
and advances R15 by four bytes. A C++ context snapshot cannot replace these
literal entry registers.

The sole phase and monotonic clock owner is `army_natural_phase_scope_12004`.
Each preparation copies its active pre-date scope and obtains entry/return events
from that owner's adapter to the existing Person clock. Placement children copy
`CopyActiveActualArmyDailyAssaultPreparation12004()` while the original producer
is running. Their own sequences remain in this same clock domain. Local journal
ordinals are only retention indices.

Exact original occurrence binding requires the parent's complete
`pre_date_prefix_return` roster capture at `2A99E76`, the same clock/thread,
strict parent/capture/child ordering, matching native R12 end, a R15 iterator
inside the captured range at DWORD alignment, and matching captured/entry raw
FullID. Repeated IDs therefore retain their actual occurrence. Parent-entry
roster, current query roster, equal logical keys, and unrelated snapshots cannot
supply the missing boundary. Selected RDX and its full generation ID are separate
from the requested roster ID and are never re-resolved to replace the argument.

Entry/return snapshots reuse the source readers for gate, removal references,
resolved Siege flag 44Ch, pending table 130h exclusions, and ordered ArRg
occurrences. A direct-RDX adapter retains existing reader semantics. It refuses
unbounded vectors above 4096 copied references and caps each snapshot at 65536
readonly operations. The optional native province-classification getter is
disabled: dependent input remains partial while the native callback runs once.
Repeated accepted ArRg IDs keep their stored order.

When historical roster binding and the actual GameState identity match, the
entry snapshot exports the existing `DailyAssaultPreparationInput12004`: all
other roster rows remain raw reference skeletons; old35 selects the sole bound
occurrence. Its ordered request begins at that exact occurrence and never
replays earlier admissions. The compatibility `query_sequence` field contains
the observed entry event sequence, with an `actual-army:<clock>:<sequence>` frame.
Copied source inputs, normal return, placement observations, and complete daily
assault/monthly execution are distinct facts. No readiness flag is promoted by a
normal return.

The journal is a bounded 64-event ring. Queries join the complete before-entry
CArmy FullID including generation bits and return owned historical copies only.
They neither resolve pointers nor execute callbacks. An after-entry generation
change is explicit and never moves a past event to the new generation. Missing
entry identity increments unattributed failure count; failed owned publication
increments dropped-copy count. Missing scalar reads remain null.

Root installs this process-lifetime leaf at quiescent startup and owns Bridge,
CMake, query/serializer integration and live execution. Installation requires the
exact build, a closed prefix anchor and confirmed primary-thread suspension;
failed patch rollback retains forwarding storage and an unhealthy installation
status. The external candidate defines no unload or live reconfiguration API.

The new owned focus fragment is intended for the single central
`--army-natural-connected-phase` compound with 33b/44b/36b. It covers exact duplicate
occurrence, one-row old35 binding, original once/raw RAX, child scope, absence of
prefix capture, after-generation change, unmatched caller, failed read, bounded
journal retention, and the source-specific installed register thunk. Owned ABI
code proves observer mechanics only. It does not attest actual CK3 execution.
The earlier seven-case conditional old35 GREEN is retained and is not rerun.

59d's separate new whole-query fixture has a setup-only TU. It allocates one
owned 128-KiB fake image shared with 36b, installs the actual candidate observers,
and uses relative CALL instructions at the literal producer/placement call sites
to retain genuine return PCs. A fresh 33b parent invokes the owned callback graph
once. Unit/Province/Character pair/War raw fields select the positive readonly
gate branch without the disabled getter; Siege+8/44Ch and pending end FF provide
the exact key and the source-defined ArRg skip. Readers compute readiness from
these fields. No focus function, old argv, or native game callback body runs in
that whole-query fixture. Its installed guards apply to this owned fixture image
and do not attest installation or execution in CK3.

Source pins and per-file candidate hashes are in external
`continuation-35b/SOURCE-ABI-FREEZE.json` and `DELIVERY.json`. This publication has
no actual CK3 runtime acceptance. Central compound qualification is recorded
independently when the central runner returns its exact receipt.
