# Feast Stage-5 private inputs, guarded Start and hosted post transport

This package wires the standalone [typed Start and balance core](activity-feast-stage5-start-core-1.19.0.6.md)
to an application-main paused mailbox executor. It is compiled only with
`XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1=ON`; the flag is
OFF by default and requires the existing four-resource Stage-5 cost and final
CanStart readers. It uses mailbox slot 64 without replacing the Stage-5 cost
or Stage-2 destination executors. No CK3 Start has been performed by this
source package.

The private inputs step is
`query-activity-feast-stage5-start-inputs-v1-private`. It binds the public
revision/date/actor, Stage 5, `activity_feast`, and `feast_type_generic` to
one paused frame. The same owner callback reads the normal slot-12 refreshed
four-name Q100000 costs, final native CanStart, Gold/Piety balances, selected
option, and the hosted activity ID/type/host set. Its result schema is
`activity-feast-stage5-start-inputs-private-v1`. Treasury and barter-goods
balances are explicitly unavailable. Their native zero costs need no balance;
their positive costs block Start.

The independent `query-activity-feast-hosted-post-v1-private` step does not
depend on the planner staying open. It returns a new paused-frame set of
generation-bearing hosted IDs/type/host and Gold/Piety balances under schema
`activity-feast-hosted-post-private-read-v1`. The consumer compares it with
the pre-submit set using the typed reconciliation core. A new exact feast ID
and same-date debit are separate findings; next turn and cold restore remain
separate requirements.

The `start-activity-feast-stage5-v1-private` route accepts the same frame
identity, positive policy decision, unresolved-submit indicator, and four
resource reserves. The native guest route is currently **unqualified**:
`guest_route_qualified` is false in the transport and cannot be set by the
request. Thus the route returns `native_guest_route_unqualified` with
`submitted=false`; it cannot invoke the original Start branch. The source
reader in [guest arrival research PR #629](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/629)
still needs a paused Stage-5 fixture before its planned timely positive join
count can support a value decision. Its count is a prediction, not accepted
guests or actual arrival. Only after that fixture, a matching same-frame
native guest capture and a positive consumer value policy may remove this
specific gate.

If a future qualified Start invokes the original branch, the command result
stays `submitted_pending` until the independent post read. A callback or
mailbox failure after invocation reports `submission_outcome_unknown` and
retains the precondition/receipt; the consumer must not retry an unresolved
Start. This package adds no public MCP capability or advertisement.
