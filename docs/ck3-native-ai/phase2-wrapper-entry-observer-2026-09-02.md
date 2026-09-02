# Phase-two wrapper-entry observer (2026-09-02)

The prior raw live proved that the `0x3B9DEA7` consumer hook executes but does
not contain the synchronously completed task. Exact-build CFG then bound that
task to descriptor `+0x18` in the completion wrapper's fifth-argument producer
list. This private observer records that distinct carrier at wrapper entry.

The default-off build option
`XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1` installs one read-only patch
at `0x3B9E030`. Its exact 15-byte anchor is
`48895C240848896C24184889742420`; the generated stub preserves volatile GPRs,
captures `[RSP]` return address, `RCX` scheduler owner, and `[RSP+0x28]`
producer-list pointer, replays all 15 original bytes, and continues at
`0x3B9E03F`. It publishes entry count, callsite RVA, thread ID and QPC timestamp
only in a private-option heartbeat object.

`last_callsite_rva` subtracts the module base and the five-byte direct-call
length from the captured return address. The result must be checked against the
separately frozen 618-callsite artifact; this observer does not expand or guess
caller CFG. A separate return hook is unnecessary for this bounded observation:
normal return `0x3B9E265` is already exact-build frozen, while this package's
question is which runtime caller and producer carrier delivered the synchronous
task.

Installation is admitted only for the exact build while the newly created
primary thread is suspended. Anchor verification, page protection, write,
identity, instruction-cache flush, rollback and standalone quiescent uninstall
follow the existing private observer lifecycle. Offline fixture execution covers
argument capture, callsite mapping, exact-anchor restore and recoverable install
rollback. No CK3 process was started; default heartbeat, public ABI and readiness
are unchanged.

MSVC x64 Release private-option DLL SHA-256 is
`B39624100F0119A87DAED1055F8F31EB4692AB1D5F4083E1C5518028678F14E6`.
The separately built default-OFF DLL SHA-256 is
`99DD731351ACBC41EE60C60D00B5BA0E4085285E7A51D45FB0702FB6BA84DAAD`;
the wrapper observer heartbeat object and field tokens are absent from it.
