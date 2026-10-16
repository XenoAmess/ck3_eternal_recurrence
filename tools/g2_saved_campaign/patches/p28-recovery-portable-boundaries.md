# P28 portable recovery boundaries

`zero_rpc_optional_research.py` qualifies only the reviewed optional Army
compare-configuration preflight. It requires immutable source-mode bytes,
source hashes, no original dispatch/before-submit marker, an independent
completed paused SEM, and the retained Game birth/actor/date/lifecycle.
The caller supplies those observations; a dictionary from an untrusted
source is not independent evidence. Local settlement writes metadata through
host callbacks, leaves gameplay counters unchanged, and clears HALT last.
It neither invokes SDK tools nor retries the rejected request.

The external P28 control8 actually performed this zero-RPC recovery. The
portable fixture is synthetic and carries no new live or succession claim.
The historical `ordinary_campaign_succession` dispatcher alias did not
mean that a successor was installed.

`runner_preflight.py` checks a published first bounded FULL before continuity
attachment and derives interruption IDs from content pins, frame, counters
and reason. The adjacent `p28-commonrunner-preflight.patch` preserves the
complete small external-runner integration: already attached evidence is
not applied twice. It is a generation recipe requiring the reviewed host's
existing continuity verifier, not a replacement runner or automatic install.

`route_contact_exact_day_war_scope_v1.py` checks only the complete starting
war roster. The caller must still validate the original Game/actor/frame,
native horizon, exact +24 stop and paused readback. Only explicit native
`retreating is True` excludes a hostile army; unknown values remain in scope.
The adjacent runtime scope recipe retains all original non-scope guards.

Run the portable checks from the repository root:

```text
python -B -m pytest -q tools/g2_saved_campaign/test_route_contact_exact_day_war_scope_v1.py tests/test_zero_rpc_optional_research.py tests/test_runner_preflight.py
```

These APIs do not install into every runner. Actual runtime binding and the
publication/experiment boundary are in the
[publication audit](../../../docs/ck3-native-ai/p27-publication-audit-2026-10-17.md).
