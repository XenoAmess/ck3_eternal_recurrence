# Campaign root paused-boundary rejection

The portable qualifier accepts only a completed AUTO error for the exact readonly
`query-campaign-root-context-v1` step. It does not replay the failed request.
The existing recovery control obtains one fresh semantic snapshot, validates the
retained Game identity and paused frame, then clears the failed pending cycle
without incrementing cycles, date credit or business credit.

Native22 final delivery is
`p34-zero-hop-native-repair01/final03/DELIVERY.json`, SHA-256
`3ad6b672ec8f35e3744bd8d2418b1ef19df3d9331cd35da71a7a7b7f444ce8a4`.
Its retained source freeze is SHA-256
`c877a07df4790288dfd87a0c4b2d51e35bd5af448354fd98e4686cbc875a4812`.
The exact compiled bridge source is
`p26-all-lifestyle-frontier01/jobs/47f64e761c49/bridge.cpp`, SHA-256
`55cc0bd664478f64496b219445a0b5ceeb902b386bb9e1ef076f1592f0b875e9`.

The bridge maps the exact campaign-root step to `QueryKind12002::campaign`
at lines 13236-13237. The actual .4 typed-early dispatch invokes
`RunTypedQuery12002` at lines 15384-15400. Its campaign executor binds the
campaign reader and calls `ReadCampaignRootContextV1` at lines 11499-11510.

At lines 13601-13608, `TrySubmitMainThreadQueryV1` returning
`paused_main_thread_not_observed` immediately produces the exact error
`paused application-main boundary is not ready`. This precedes the wait and
the campaign executor. The surrounding loop repeats only for nonterminal
title-map navigation (lines 13645-13659); campaign-root reads cannot reach this
admission rejection after an earlier campaign callback in the same request.
The successful campaign result is rendered only at lines 13705-13709.

The error string also occurs in other command dispatchers. The string alone is
therefore insufficient qualification: the exact diagnostic type, native step,
request identity, revision, completed error status and text are all checked.
Business commands, navigation, other queries, busy and timeout errors remain
outside this handler. No broad error catch or action replay was added.

Offline evidence: actual AUTO247 plus 21 negative cases; original seven registry
handlers do not match; the eighth handler matches after an atomic fixture-only
registry update. The actual P35 queue method supplies its production minimal
11-key environment to the unchanged known-pause dispatcher and readonly
recovery body. Only the birth reader and semantic reply are injected in that
test; the reply is actual SEM248 reused as a synthetic child250, not runtime
evidence. Portable tests separately exercise the formal AST function subset.

Runtime evidence is distinct: Root installed the eighth handler, then actual
control249 returned `readonly_planning_precondition_recovered`, one fresh
SEM250, cycles12550 unchanged, zero gameplay submissions and no original AUTO
replay. Actual SEM250 retained date53483928, Native117/public118, paused.
Root subsequently reported FULL251 had advanced 19 days. This last progress
report is parent-observed; it is not part of the offline test qualification.

No SDK source, canonical classifier, owner pin, Driver, SAVE, video or ledger
was changed by this package. The existing dynamic registry intentionally reloads
for each failure, so the handler applies to future matching transient failures
without a new SDK process. This does not prove every readonly query can use it.
