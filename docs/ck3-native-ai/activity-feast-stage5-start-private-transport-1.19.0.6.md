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
option, the hosted activity ID/type/host set, and the original planner's
selected guest join/arrival estimates. Its result schema is
`activity-feast-stage5-start-inputs-private-v1`. Treasury and barter-goods
balances are explicitly unavailable. Their native zero costs need no balance;
their positive costs block Start.

The guest capture reuses the normal slot-12 refresh sequence and reports
`guest_join_status`, `selected_nonhost_count`, `positive_join_count`,
`timely_positive_join_count`, and `arrival_time_observed`. Counts are `null`
when the native read does not observe the same frame. A source-level positive
arrival estimate is not yet a qualified live guest route.

The independent `query-activity-feast-hosted-post-v1-private` step does not
depend on the planner staying open. It returns a new paused-frame set of
generation-bearing hosted IDs/type/host and Gold/Piety balances under schema
`activity-feast-hosted-post-private-read-v1`. The consumer compares it with
the pre-submit set using the typed reconciliation core. A new exact feast ID
and same-date debit are separate findings; next turn and cold restore remain
separate requirements.

The `start-activity-feast-stage5-v1-private` route accepts the same frame
identity, positive policy decision, unresolved-submit indicator, and four
resource reserves. The native guest route is derived from the current
selected-member read: observed selected non-host IDs, original positive
join and timely arrival predictions must match the same cost frame and
normal refresh. It cannot be set by the request. A missing or nonpositive
selected-member read returns `native_guest_route_unqualified` with
`submitted=false`. The core repeats that read and binds the same members
before invoking the original Start branch. R0368
obtained a paused selected-row read with zero non-host selections, while a
separate later H3928 read found a positive native-filtered pre-invitation
candidate. Those different runs cannot form one Start decision. The new
[read-only guest route proof](activity-feast-stage5-guest-route-proof-1.19.0.6.md)
binds active rules, selected rows, candidate prediction and final CanStart
on one paused frame. That independent read-only proof leaves its action
qualification false; filtered candidates are not selected-member evidence.
Predictions do not prove acceptance or arrival, and H3928 final CanStart
remains false. The new selected-member Start branch is source-ready until
a matching positive paused frame and the complete action/post/recovery path
are independently verified.

If a future qualified Start invokes the original branch, the command result
stays `submitted_pending` until the independent post read. A callback or
mailbox failure after invocation reports `submission_outcome_unknown` and
retains the precondition/receipt; the consumer must not retry an unresolved
Start. This package adds no public MCP capability or advertisement.
