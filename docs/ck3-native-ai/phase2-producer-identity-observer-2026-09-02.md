# Phase-two producer identity observer (2026-09-02)

The private producer identity observer is source-ready for one coordinated
live attempt. It is disabled by default and does not change the public bridge
ABI or readiness.

The exact logical seams are `0x3B9CFD2` before the state-2 publication and
`0x3B9CFD7` at the `xchg [RBX+0x60], EAX` publication. Because they are only
five bytes apart, installing two absolute detours would overlap. The observer
therefore uses one exact 16-byte physical transaction over
`[0x3B9CFD2,0x3B9CFE2)`, anchor
`B802000000874360E861702800488BF8`, SHA-256
`9A7AE24D86BC3453A89A92E6B948EE54A6DA043029CCF76E2B3D1443BD1BBE1E`.
Its stub records the logical pre edge, executes the original `mov eax,2` and
`xchg`, records the logical post edge, executes the original call at
`0x3E24040` and `mov rdi,rax`, then resumes at `0x3B9CFE2`.

The private heartbeat object `phase2_producer_identity_observer_v1` publishes:

- logical pre/post entry counts;
- `RBX` task, callback at `+0x38`, callback vptr and slot2;
- owner at `+0x58`, state at `+0x60` before and after publication;
- read-failure count, thread ID, and QPC timestamp.

Installation requires the exact build and suspended primary thread, verifies
the anchor, changes protection transactionally, flushes instruction caches,
and retains exact original bytes. The matching uninstall restores and verifies
those bytes before releasing the stub. The focused native fixture executes the
generated stub and verifies state `1 -> 2`, both logical observations, full
identity, one original call, exact uninstall, and recoverable failed-install
rollback.

Build option:
`XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=ON`. The private MSVC x64
Release DLL SHA-256 is
`736A8D168FA102C17BC64343CEF2680164606DEB8CA82A5177F0AAD846293FB6`;
the matching injector SHA-256 is
`1F949F28E09A42DDC378F2D0D9D439A8766BA3F85A86F8E53C1828E94A06E8AC`.
The default-OFF DLL SHA-256 is
`42AFF30F4862544821FBB5452D950BA9C317D2CB337E4700C25466E5F7B6BAEC`,
and contains no private heartbeat token.

`make_phase2_producer_identity_observer_manifest.py` creates the external
no-launch manifest after the exact source commit and binary hashes are frozen.
`zg361_phase2_acceptance_observer_gate.py` must validate that manifest against
the fresh clean source before the coordinator authorizes the only live attempt.
Source-ready status alone is not launch authorization. No CK3 process was
started in this package; readiness remains RED pending that bounded live.
