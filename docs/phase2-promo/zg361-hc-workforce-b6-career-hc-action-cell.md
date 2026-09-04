# `hc-workforce` B6 career/HC action cell

Status: **static-ready / live-pending**. No CK3 process was started and no
production-live result is claimed by this package.

## Smallest closed claim

The cell selects the real `zg361we.360` route B (native option index `1`,
submitted option number `2`) through the existing M360 action executor. An
accepted option command is only an ACK. Completion additionally requires one
paused, received-self provider frame that observes all of the following:

- the exact M360 owner, subject, cycle and case;
- receipt state `4`, choice `2`, and `provider_observed=true`;
- all six current career-HC buckets and `zg361_ch_hc_conserved`;
- `available + reserved + occupied + frozen + reclaimed == authorized`;
- route-B aggregate manager cost `0`;
- every value above comes from the same paused native frame.

This is the career/HC half of the proof. B4 separately proves the workforce
collective lifecycle, all three cohorts, rolling history and M361 charter gate.

## Product-source finding

The purpose shard
`common/scripted_effects/zg361_workforce_endgame_059_al_m360_route_b_effects.txt`
contains the real M360 route-B implementation and its state-4/choice-2 receipt,
but contains no `zg361_ch_hc_*` read or write. Route B forces the three cohort
quotas with zero manager cost; it does not debit the career headcount ledger.
The B6 postcondition therefore observes a conserved career-HC partition rather
than inventing a headcount transition that the product does not perform.

This is static product-source evidence, not a live CK3 outcome. The exact-build
native provider, serializer, slot-26 mailbox transport, native driver, service
and MCP query are now wired and fixture-tested. Its semantic capability remains
absent from the default adapter advertisement until a paused live query proves
the reader, so the claim remains `live-pending`.

## Integration point

- Contract/normalizer:
  `xar_autoplayer.bridge.zhongguo_career_hc_workforce_postcondition_contract`
- Fixed, currently default-off capability:
  `game.command.query-zhongguo-career-hc-workforce-postcondition-v1`
- Service seam:
  `query_zhongguo_career_hc_workforce_postcondition_v1(request_nonce, expected_revision, owner_character_id)`
- Cell:
  `tools/zg361_phase2_hc_workforce_b6_action_cell.py`
- No-launch preflight:
  `py tools/preflight_zg361_phase2_hc_workforce_b6.py`

The focused formal runner entry is now
`--phase2-hc-workforce-route-b-live`. Its B6 gate remains default-off: without
`--phase2-hc-workforce-enable-career-provider`, the registry replay records a
typed `career_hc_live_gate_default_off` result and never calls the provider.
The explicit enable flag makes a provider-observed result mandatory on both
the first execution and the case-identical replay. An advertised capability or
option ACK alone cannot enable or satisfy that result.

## Required live checkpoint

Use the current cumulative product projection. Activate the workforce
transition fixture and stop with the real `zg361we.360` window open before any
route is selected. Freeze the save/checkpoint identity, date, event instance,
and saved-scope owner/subject. Then:

1. submit route B once from the exact owner;
2. retain the ACK as command evidence only;
3. rebind the managed MCP session to the exact subject without advancing date;
4. issue the fixed provider query from a paused map-ready snapshot;
5. retain the normalized provider frame and its snapshot/native revision;
6. join it to B4's independently observed workforce postcondition.

Any missing capability, changed date, owner/subject drift, wrong cycle/case,
unavailable bucket, non-conserved partition, nonzero manager cost, or ACK-only
record is RED.

## File-boundary evidence

The no-launch preflight also checks the user-mandated generated-effect boundary.
At this checkpoint the career/HC runtime is 267 effects in 41 purpose shards,
with 1–10 effects per file and a maximum of 10. This confirms deterministic
policy compliance only; it does not prove that historical CK3 startup failures
were caused by file size. The established direct historical cause remains the
same-effect recursion found during the earlier loader incident.
