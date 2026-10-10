# Loaded singleton D2BE00, CK3 1.20.0.4

The reached actual function `D2BE00..D2BE57` is source closed: 87 bytes and 18
instructions, Steam 25734779, held executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
One new 87-byte capture used the existing mapper, held actual runtime owner,
cache-first lookup and shared D O_EXCL claim. No old executable or broad scan
was read. `SOURCE-PROOF.json` was frozen before the new leaf.

The actual context predicate reaches `2C250AF CALL D2BE00` only after its late
context DWORD equals the original raw receiver's DWORD at +18. This call has
no additional argument setup. The complete getter consumes no incoming
RCX/RDX/R8/R9 values. `D2BE04` loads RAX from singleton slot `5D1FBF8`; a
nonzero value takes `D2BE0E JNE D2BE52` and returns that pointer immediately.
The parent then puts original retained RDI first pointer in RDX, returned RAX
in RCX, and calls `31C1D10` at `2C250BA`. That consumer is separately owned;
this source does not supply its Boolean result or singleton type.

The null branch forms a local span with pointer `448D018`, length 30, flag 0,
ECX=1, R8D=0 and R9D=100, then calls `3F8B640` and reloads the same singleton
slot. Existing exact-build default-source evidence already closes that literal
as `Instance has not been created!` and the shared call as a diagnostic path.
This is not a supplied typed constructor or initializer. The existing packet
is `commander-loaded-key-source30/native-tree/SOURCE-CLOSED.json`; its singleton
type/database identity is not transferred to this different slot. No diagnostic
body expansion, diagnostic invocation, initializer or native getter runs here.

`loaded_singleton_d2be00_12004.hpp/.cpp` exports
`ReadLoadedD2BE00Singleton12004(access, snapshot_revision)`. It reuses 06c's
exact-bound `RawReceiverAccessV1` and one guarded QWORD read of the current
singleton slot. It records the caller's supplied frame key and raw copied
pointer. A readable nonzero pointer makes only the loaded-branch conditional
return available. A readable zero stays zero in the raw field, while the
post-diagnostic native return stays unavailable. Read failure preserves missing
raw/branch fields. Neither a pointer nor the helper establishes a paused frame;
03/21 owns the admitted snapshot boundary and shared read budget.

`ReadLoadedD2BE00ContextChild12004` is the exact 21c memory-model callback
signature. It consumes `inputs.frame_key` and supplies the copied nonzero
conditional return, without interpreting stale incoming native argument values.
Unavailable input leaves its output unchanged and causes the parent predicate
to retain its missing-child result. This adapter is not a native calling ABI.

The no-main export `RunLoadedD2BE00SingletonNewCase12004` supplies one owned-slot
case for the sole fresh 03/10 compound. It distinguishes loaded, readable-zero,
unreadable and wrong-build inputs and checks that the callback leaves unavailable
output unchanged. It does not qualify a natural invocation, guardian workflow,
Army cleanup or an older fixture. Central compilation/execution remains pending.

The external source and candidate are under continuation-28d. The 4 MiB leaf
budget uses the existing Root storage admission; source protection is reviewed
on 2026-10-17 and small records after 180 days, without automatic renewal.
