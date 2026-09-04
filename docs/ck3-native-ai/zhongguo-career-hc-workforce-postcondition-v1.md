# ZhongGuo career-HC / Workforce route-B postcondition v1

Status: **exact-build static-confirmed + offline fixture-ready; semantic
capability default-OFF; paused live pending**.

## Decision value and boundary

The provider closes the career/HC half of the real `zg361we.360` route-B cell.
It answers one narrow question: did the paused played character receive the
exact M360 state-4/choice-2 receipt from the requested owner while its fixed
six-field career-HC ledger remained conserved and the route-B manager cost was
zero?

The public request contains only `request_nonce`, `expected_revision`, and
`owner_character_id`. The subject is always the played character captured in
the same paused frame. The owner is an equality filter against the observed
receipt owner; it is never a selectable read scope. Variable names, alternate
subjects, receipt values, buckets and routes are not caller-controlled.

## Exact-build reader

The reader is pinned to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
It reuses the frozen subject-variable ABI:

- variable context: `0x3329A40`;
- identifier table / lookup / name: `0x3B971A0`, `0x3B97020`, `0x3B97090`;
- character storage / fallback slots: `0x570C130`, `0x570C138`;
- fixed-point numeric kind `1`, character kind `4`, scale `100000`.

It performs two complete reads of exactly 14 allowlisted subject-local rows,
with an equal paused frame before and after. It retains no engine pointer. The
allowlist is the six M360 receipt fields, `zg361_ch_hc_authorized`, the five
partition buckets, `zg361_ch_hc_conserved`, and
`zg361_we_al_external_collective_manager_cost_total`.

GREEN requires exact owner/played-subject/cycle/case identity, receipt
`state=4`, `choice=2`, six nonnegative HC values,
`available + reserved + occupied + frozen + reclaimed = authorized`, the
provider's conservation flag true, manager cost zero, and same-frame stability.
Absent or partial receipt, wrong route, identity drift, missing or mistyped HC,
nonconservation, nonzero cost, or a changing frame returns typed unavailable.

An action response with `accepted=true` is only transport ACK. The native reader
does not accept ACK fields, and the Python normalizer rejects ACK-shaped JSON;
therefore ACK cannot produce GREEN.

## Wiring and readiness

The application-main mailbox uses fixed slot 26,
`permitted_executor_sexvigintary`. Reader, serializer, strict schema, mailbox,
bridge dispatch, native driver, service facade and MCP surface are implemented.
The exact semantic capability
`game.command.query-zhongguo-career-hc-workforce-postcondition-v1` is
deliberately absent from `ck3_11906_adapter.cpp`, so normal capability checks
fail closed until live evidence exists. This is a default-off provider, not a
production-live primitive.

Machine-readable details are in
`ck3_autonomous_player/native_bridge/research/zhongguo_career_hc_workforce_postcondition_v1_abi.json`
and its source contract. Static verification is:

```powershell
py tools/preflight_zg361_phase2_hc_workforce_b6.py
```

## Required live checkpoint

Use the current cumulative projection with the workforce-transition fixture
active and the real `zg361we.360` event open before selecting route B. Freeze
date, event instance, owner/subject and snapshot/native revision. Submit native
option index 1 (option number 2) once, retain its ACK only as command evidence,
rebind to the exact subject without advancing date, then query this provider
while paused and map-ready. The resulting normalized provider frame must be
joined with B4's separate workforce-collective proof. Until that artifact is
captured, capability advertisement and live readiness remain false.
