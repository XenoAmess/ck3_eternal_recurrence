# CK3 1.19.0.6 realm-law application-main registration v1

Status: `candidate-ready internal shared-DLL registration; paused live
submission and receipt pending`.

LAW8 compiles LAW2 through LAW7 into `xar_ck3_bridge` and registers
`ExecuteRealmLawApplicationMainV1` as the fixed 37th gameplay executor in the
existing application-main mailbox. Slots 34, 35 and 36 remain assigned to
Faction, Construction and Decision respectively. The
capability-advertised constant remains
`false`; there is no public protocol schema, command, MCP tool or planner
change.

## Ownership and thread boundary

The worker owns one durable `RealmLawApplicationMainStateV1` and one durable
context. Configuration copies the source-manifest digest and borrows only the
reviewed LAW7 callback contexts and image reader. It does not read CK3 or bind
LAW5 on the worker thread.

The first submitted mailbox transaction verifies the exact mailbox ticket,
fixed executor identity, module base, current Windows thread, initialized TLS
main-thread marker, paused Jomini/game state and the consecutive paused-owner
proof. Only inside that executor does it run LAW7's double source-proof and
double exact-mutation-ABI preparation, then bind LAW5. The request date must
equal the mailbox execution stamp before any native binding or source callback
runs.

## Submit and receipt transactions

The submit transaction calls LAW5 once with the caller's complete pointer-free
request. A successful LAW7 command queue handoff stores the original ACK,
mailbox sequence and LAW5 pending state. Its only successful completion is
`submitted_verification_pending`. A second submit while that state exists is a
typed `pending_ack` RED and cannot overwrite the retained ACK or queue another
command.

The worker must reclaim the submit ticket before it can prepare a receipt. The
receipt is published as a later mailbox transaction and must have a sequence
greater than the stored submit sequence. Inside that independent execution,
LAW5 performs a fresh LAW3 law snapshot and resource read. LAW4 accepts the
receipt only when at least one public/native/proof/date revision is newer, the
requested law is effective, every resource delta equals the frozen charge, and
the succession shape equals the original ACK. The fresh title-successor
baseline is retained in the receipt as evidence. The accepted post date must
also equal the current mailbox stamp.

Failed and stale receipts remain RED and preserve the pending ACK for a later
fresh observation. Only an enacted receipt clears both the application-main
pending marker and LAW5's pending state. Queue acceptance alone never clears
either marker and never becomes enactment success.

## Static acceptance and live gap

The focused fixture uses the exact CK3 executable as LAW6 input and runs under
MSVC C++20 `/W4 /WX` in normal and `/O2` modes. It covers deferred in-executor
binding, one pending submit plus an independent fresh receipt, duplicate submit,
stale receipt, action rejection, mutation-ABI drift, mailbox identity failure
and request/stamp mismatch. The shared Release DLL must also link with the LAW2
through LAW8 sources.

No CK3 instance was started for LAW8. Production readiness still requires a
fixed candidate whose real source operations and target resolver are configured,
followed by one paused live submit ACK and a later retained fresh
law/resource/succession receipt. The current status is not `fixture-live` or
`production-live primitive`.
