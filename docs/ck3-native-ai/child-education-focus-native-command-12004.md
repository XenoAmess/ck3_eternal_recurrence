# Child education focus native command, 1.20.0.4

2026-10-11: Root authorized a functional successor to the earlier source-only
focus-gate review. The new adapter is source-authored and has not been compiled,
tested, invoked or observed in CK3 in this work package.

The host's query uses `ValidateResolvedChildEducationFocusNativeAdapter12004V1`.
It shares command construction and readiness with dispatch, invokes the original
validator once, and never submits. Its optional result preserves native AL false
and true; unavailable readiness or SEH returns unknown. Submission calls dispatch
directly and performs its own single validation before queueing.
Dispatch preserves an unknown validator result as `unavailable`; only a returned
native false becomes `command_validator_rejected`. Only native true can submit.

`DispatchResolvedChildEducationFocusNativeAdapter12004V1` accepts the existing
actual4 native environment and execution access, the child's complete 32-bit ID,
the played controller's complete 32-bit ID, and a qualified education focus
definition address. The native host must resolve these inputs in the same paused
application-main query. The definition comes from the general focus database
qualifier; this adapter does not use the fixed player focus keys or a
focus-to-lifestyle member assumption.

The command is 0x38 bytes. Its primary and secondary vtables are module-relative
0x4760B90 and 0x4760B60. Offset 0x20 holds the child ID, 0x28 holds the definition
pointer, and 0x30 holds the played controller ID. All generation bits are copied.
Common state and padding use the existing actual4 stack-command defaults. The
original validator at 0x288A870 decides legality. The adapter does not add an age
rule or require equality between the target and controller.

The existing environment readiness check retains exact-build, SHA, module,
vtable and original callback binding checks, including its offline fixture
contract. The existing application-main and paused probes remain required. The
adapter invokes the original focus validator once with a null error carrier and,
if accepted, invokes the existing submission callback once with channel flags
0x0E. It does not retry either callback after an exception.

The retained actual4 vtable packet identifies primary-vtable offset 0x40 as
0x2895BD0. That complete 131-byte clone allocates 0x38 bytes and copies the target,
definition and controller fields independently. The existing submission wrapper
owns this native heap clone and queues it through actual4 0x37F06D0. The stack
command remains local to the adapter.

`submitted_verification_pending` is a pending NATIVE_ACK. It supplies no applied,
success or legal-action observation credit. A separate receipt must inspect the
same child, preserve full generation identity and match the chosen focus. The
earlier 2919670/29194E0 source graph remains useful evidence; its unresolved
3836440 value is not replaced with a hand predicate. Future execution uses the
original native validator path.

The source freeze and exact proof references are in the external work package
`background-g2-source-round-20261011-1152/owner-43/child-focus-command`. Its source
patch contains this topic and the new header/CPP only. Shared native host, wire,
driver, service, receipt and CMake changes remain with their assigned owners.


Root source adoption: **SOURCE_ADOPTED_NOT_RUN**. The connected native query,
original command, independent receipt, exact executor registration, guarded
Runtime source list, strict Driver and ordinary family caller are adopted
together. No test, import, build, deployment or game operation followed.
