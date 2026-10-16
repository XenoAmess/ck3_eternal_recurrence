# Private ordinary AUTO Army scalar read

The ordinary AUTO planner consumes eleven scalar Army fields and optional
supply/attrition pairs. The existing rich Army query also collects data that
these consumers do not use. The new `private_auto_scalar_v1` wire reads the same
complete Army scope and existing scalar inputs, omitting rich attachments and
their serialization. Explicit Army queries retain their existing rich output.
The `GameAdapter` vtable and native bindings layout are unchanged.

The feature defaults to **off**. Only the exact .4 capability
`game.command.query-army-strengths-private-auto-scalar-v1` can enable it.
Process-local MCP controls permit switching without another SDK restart:

1. `ck3_set_army_private_auto_scalar_ab_v1(mode="compare", expected_revision=...)`.
2. `ck3_compare_army_private_auto_scalar_ab_v1(expected_revision=...)` performs
   the existing rich query and the private query on the same paused frame.
3. `ck3_set_army_private_auto_scalar_ab_v1(mode="use", expected_revision=...)`
   requires an equal comparison for the same Game PID, connection generation,
   living actor, episode, adapter and build.
4. `ck3_query_army_private_auto_scalar_ab_v1(expected_revision=...)` reads the
   current control. Setting `off` disables the private path.

Both transports retain existing source-frame and normalization checks. Compare
returns the rich reference result. A mismatch clears the private cache and
disables the experiment; reconnects, actor/episode changes and capability loss
also disable it. The default off path does not assemble public capabilities.
These controls submit no gameplay actions and grant no combat permission.

## Evidence and limits

Machine: `xenoamess-full-tower-eb9d2c1186`; observed 2026-10-16 UTC.

- Nine portable Python cases cover default/capability fallback, explicit-query
  preservation, use-before-comparison rejection, equality, mismatch cache
  removal, connection changes and MCP control/readback. The comparison test
  distinguishes rich sequence 1 from private sequence 91 and checks that the
  public result remains sequence 1.
- Actual MSVC compilation and focused fixture invocation passed using the new
  production Army object: external
  `cb-candidates-native18-02/ARMY-FOCUSED-FIXTURE-RESULT.json`, SHA-256
  `4d1bacc2a5e12cd7c570c76a6da7d8933168b956b02c950311998420e3b771b4`.
  The fixture covers complete scope/core equality, signed and zero
  supply/attrition, omitted rich work, private parser rejection and ABI ordinal
  assertions. It created no EXE and made no Game/OBS/desktop calls.
- The initial fixture failure correctly detected that the synthetic private
  scope omitted war 42, while the rich scope included it. The test fixture was
  corrected to supply identical war membership; production code was unchanged.
- External source manifest:
  `continuation42-cold-prep/p21-native-army-producer01/PRIVATE-AUTO-SCALAR-SOURCE-PINS.json`;
  final Native patch SHA-256
  `cd07131c70645f2b9a9f66e3a1a3b7c88b43f0ba1b0d5326c86a3929621dac77`.

These are source and fixture results. They do not demonstrate real-game
rich/private equality or a measured game-day speed improvement. Enable `use`
only after the live comparison succeeds; retain the original comparison
receipt for offline performance analysis.
