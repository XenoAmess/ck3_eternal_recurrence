These seven JSON envelopes are exact output from the real C++ production target
`xar_ck3_121003_26785313_personal_gold_v2_on_test` on 2026-11-20.
Producer executable SHA-256:
`87fe1cc4e580541473ba3398d9e12381c37f040f9ad1657f312da65a586b5573`.

The production target's seven outputs matched the earlier independent leaf
producer byte for byte. Each fixture's length and SHA-256 are asserted in the
Java tests. Source inputs were explicitly hand-authored NoGame DATA. In
particular, `application_main_observed=true` inside a fixture is not a live
application-main, physical owner, Game, Native SDK or MCP admission observation.

V2 retains a signed64 canonical decimal string in `personal_gold.raw`, with
scale 100000, and the exact CK3 1.21.0.3/build26785313/859F tuple. V1's separate
fixtures and shared numeric `NativePlayedResources` contract remain unchanged.
The dedicated Java MCP registration and catalog/admission source are not
implemented by this fixture or the native query consumer.
