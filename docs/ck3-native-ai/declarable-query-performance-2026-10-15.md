# Declarable-war query timing, 2026-10-15

Status: **static-ready diagnostic**, not a measured gameplay speedup. This package
does not start, connect to, inject into or restart CK3, and does not change war
policy, candidate scope, declaration ordinals, target order or public API output.

## Observed need and scope

Root's N41 P04 `ordinary-stage-timings.jsonl` measurements for Python PID 250464
showed 30 `driver.native_command_result_wait/query-declarable-wars` samples:
163.887 s total, median 5.45965 s, maximum 5.61976 s. Root semantic reads had a
0.4 ms median. The existing two queries without a declaration followed by a
30-day cooldown was already active; increasing that cooldown is not this fix.

`ReadDeclarableWars` evaluates every enabled CB against every living target.
Master already caches enabled definitions within a query and avoids a redundant
scratch clear. Further actor-only or unlanded-target shortcuts need actual native
source proof. The actual 1.20.0.4 evaluator prefix at RVA `0x31F4520` has a
CB-independent existing-war relation check, followed by compiled trigger scopes
that contain both actor and target. This bounded read did not establish a useful
peace-time shortcut.

It would be incorrect to discard `make_tributary_cb`,
`pam_investiture_conflict_cb` or other CB families as unsupported: current
`strategy.py`'s `general-native-war-entry-battle-prior-v1` can consider any legal
native declaration, and `prewar_selected_declaration12004.cpp` explicitly uses a
common wrapper without a CB-key branch. Such filtering could change declaration
choices and cannot be counted as policy-neutral performance work.

## Available diagnostic

Before the **next independently necessary native cold load**, set the CK3
process's launch environment variable `XAR_CK3_DECLARATIONS_PROFILE_JSONL` to a
JSONL filename inside an existing admitted output directory. The value is read
inside CK3, so changing only the SDK process environment after CK3 starts does
not enable it. Windows uses the wide environment/path API.

An unset or empty value disables clock reads, counter updates and file output.
When enabled, the existing full query writes one aggregate line containing:

- Schema `ck3-declarable-query-profile-v1`, timestamp, actor, game date, success,
  target count, returned row count and total elapsed nanoseconds.
- Every enabled CB's original database ordinal and canonical key, evaluation
  count, available count, materialized row count, native evaluator time, and
  materialization/scratch cleanup time, all accumulated across targets.

The evaluator call flags, target-major iteration, scratch destruction and
returned rows remain unchanged. A failed enumeration logs its observed partial
counts with `success=false` and returns the same failure as before. A file write
failure cannot become a query failure. There is one append after enumeration,
not one disk write per native evaluation. Enable sampling only for a bounded
diagnostic window; record launch/source/binary bindings alongside the JSONL and
compare query `total_ns` with the SDK wait before assigning the remaining delay
to native evaluation or transport. The per-evaluation clocks themselves add
diagnostic overhead, so enabled timings are not an uninstrumented throughput
benchmark.

## Focused verification and evidence

Source base: `0c801884de39443fb49aa22978f9ca1e28a591a3`. A direct MSVC C++20 build
compiled only `ck3_12002.cpp`, `ck3_12002_commands.cpp`,
`ck3_12002_declarations.cpp` and its existing test translation unit. Actual argv,
build log and fingerprints are under `D:/qperf15_artifacts/`; no whole native
build ran. The compiler retained its standard CRT `_wgetenv` deprecation warning.

The existing declaration/stale-choice/validation/native clone-ownership fixtures
passed. The added fixture compares complete rows, native call count, cleanup
count and target-major order with timing disabled and enabled. It also checks an
unwritable diagnostic sink. The output was independently parsed as JSON:

| Case | Evaluations | Returned rows | Query success |
| --- | ---: | ---: | --- |
| Two targets, two CBs with original ordinals 0 and 2 | 4 | 8 | true |
| Evaluator returns unavailable and still creates scratch | 4 | 0 | true |
| Malformed first available configuration | 1 | 0 | false |

The second CB's key includes quote, backslash and newline characters; JSON
round-trip preserved it. The three-line profile is 1,456 B, SHA-256
`63f51b92a14f2bf3b0af4fc62c1b8a7d070b1b1b66cf368577e31c30542b8493`.
`verification.json` records the one focused fixture run and equality results.
`open_kaishek` is not applicable to these C++ native call-order, scratch ownership
and timing checks; there is no newly interpreted CK3 script semantic subset.

The exact new fixture EXE was submitted through the existing project Defender
helper. Its receipt is `settings_failed`,
`admin_required_for_verified_readback=true`, with no Add or UAC attempted;
SHA-256 `c9b73f7a1bc14295169c36e2253cdc477de60ba3417e9d52a1d962881e51acd4`.
This is not administrator readback or proof of an effective exclusion.

The isolated source/output roots use Root's coordinated 150 MiB allocation from
the existing N41 reservation and policy 1.0.0. The small storage/availability
manifest is external; no assets were deleted. Review the build inputs and
evidence by 2026-10-22. Live CB timing capture, targeted native optimization and
an uninstrumented before/after gameplay throughput measurement remain pending.
