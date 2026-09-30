# H3937 route-contact queued dispatch

The fixed native source for R0125 is `0d06a372d502723fcbba35295d38a28ae3852a12`.
Its native tree is `d238a865b0aa714c1183770d31b4211cb492aa73`, also recorded by
the actual release pair consumer manifest SHA-256
`70281FD2B0AC82C1780633DBA00A318934B55091F05FEF6305BAD2A0B8DA3F79`.

That source's route-contact producer omits the existing wake trace argument
from `TrySubmitMainThreadQueryV1` and uses the three-argument queued wait.
The header defaults are `trace=nullptr` and `queued_wake_interval=0`.
`application-main route-contact query timed out before execution` maps only
to `timeout_cancelled_before_execution`: the wait elapsed and cancelled the
still-queued ticket before the executor acquired it. This source mapping does
not identify why the application pump did not acquire the R0125 ticket.

The scoped candidate connects the existing queued retry to the actual typed
route-contact producer with a 250 ms interval. Its queued budget stays 8,000 ms;
the executing wait slice stays 2,000 ms and retains caller storage until a
terminal state. The callback, paused/date/actor/hostile gates and physical
inventory completeness checks remain unchanged.

Negative route-contact `command_result` frames carry the sibling
`route_contact_dispatch_v1`. It contains the ticket, typed completion,
executor invocation count, queued wake trace, and passive mailbox snapshots
before submission and after waiting, before reclaim. It does not change
successful semantic results and does not authorize an additional query.
Initial, queued and total wake counts are separately labeled, and the captured
initial owner is included.

The two shared mailbox hunks are taken exclusively from the frozen ROLE
candidate `aef7ed46f5da8d734be05db9bcca5196e2d02bf2` (base `244005a`), patch
SHA-256 `94A89DB1C0B43D7B104C39EA8E5E10A2B6792B923E7483F4EA4CC3332A5DD291`.
They applied to the fixed H3 base without a context conflict. They retain the
captured nonzero owner, published ticket, queued state and stop gate for inert
wakes. No ROLE executor allocation is imported. The ROLE 5/5 callback fixture
and independent review bind those shared hunks; they do not constitute an H3
callback or route read test.

The focused fixture target is
`xar_ck3_h3937_route_contact_queued_retry_v1_test`; the exact CTest is
`xar_ck3_native_bridge_h3937_route_contact_queued_retry_v1`.
It must exercise the installed SDL return-site hook and actual H3 callback,
consume the first inert wake without pumping, then complete after the retry.
The second case retains an unpumped ticket for the actual 8,000 ms budget and
checks cancellation, reclaim and the diagnostic field binding.
Disabled world bindings intentionally return `query_unavailable`; this fixture
does not prove a route, physical inventory completeness or a live CK3 result.

At source authoring, the focused target has not been compiled or run. The old
queue suite and any native full build are outside this authoring step.


## ie canonical source-only integration — 2026-09-30

This ie change applies the frozen 12bb H3 delta and the aef7 ROLE bridge
delta to fixed ie 83aa. The shared mailbox changes are applied once.
The original authoring text above is retained as a historical snapshot.
The separately frozen focused H3 EC81 result and ROLE 30823 result/reviews
are reused; this adapted ie tree has not been built or run. Actual pairs
and preparation remain bound to their own frozen source trees. ROLE live
remains 0/1 and formal H3 remains 0/6. Steam stays offline for all tasks.
