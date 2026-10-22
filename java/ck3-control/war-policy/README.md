# War outcome source knowledge

`war-policy` is an in-process Java module. Its integration state is `SOURCE_ONLY`:
there is no Service decision consumer, HTTP resource, game RPC, action writer or
runtime replacement. Root will integrate its Maven parent separately. Frozen
Native32 runs are not changed by this module.

`WarOutcomeStakesProjector.project(byte[])` accepts exact fields
`schema`, `war_id`, `snapshot`, `campaign_root`, `current_source_sha256`,
`observation_context`, with schema `g2.war-outcome-stakes-request/v1`.
The registry is SHA-bound bundled configuration supplied once at host setup.
The overload taking `ObservationContext` validates the SDK frame before
projection and supports a future shared host's batch or in-process invocation.
There is no per-war server.

The input is the existing SDK same-frame snapshot/cache and campaign-root
contract. The full termination-options payload is validated before a stale
binding can return unknown. Existing snapshot/root extensions are retained by
the wrapper, while cache/query/options fields are exact. Presence, explicit
null, empty lists, target order and duplicates remain distinct. Positive uint64
identities use exact `BigInteger` JSON numbers inside this Python/Java domain;
they are not JavaScript-safe IDs or decimal-string wire aliases. IDs reject
booleans, floating values and strings. AI fixed-point values use signed64 raw
integers and integer scale 100000. Dates and war scores are signed32 integers.

The two reviewed source profiles expose conditional title/vassal or political
risks. The result always leaves material terms, actual effects and actual war
result unverified, grants no surrender/action qualification and permits legal
war processing to continue. Unknown CBs do not grant a risk profile. This module
does not make the underlying missing material preview observable.

Input/output budgets are the existing contracts' 65536/16384 bytes. Duplicate
JSON fields, invalid UTF-8, trailing tokens and nonintegral integer fields fail
with `ContractViolationException`. The integer-only scale check deliberately
rejects legacy Python's incidental acceptance of `100000.0`; this is a stricter
new wire boundary, separate from equivalence on real native integer output.

## Regression provenance and execution

`WarOutcomeStakesGoldenTest` runs only committed classpath JSONL vectors and Java.
It never imports or executes local Python, reads game files or needs a fixture
environment variable. An absent golden is a failure, never a skipped pass.
Each captured call keeps its original JSON text so floating invalid IDs cannot
turn into integers during a test reserialization.

The one-time corpus originates from all 11 unchanged Python regression methods.
Their fixture invokes the real termination normalizer and production same-frame
cache method on synthetic in-memory owner state; no native connection is opened.
Its header records actual capture machine/time, source pins, original test count,
skips and each original-method lineage. Default Java reruns are frozen-vector
differential checks, not fresh Python producer or Service integration runs.

`PythonOracleGoldenExporter` is explicit local test support only. It pins the
unpublished oracle, tests and registry before execution, checks all producer pins
again afterward, refuses overwrite, times out at 120 seconds and caps stdout at
2 MiB/stderr at 128 KiB. It is not called by Maven or CI. A missing oracle or
failed original test aborts generation. The designated build writer may run:

```text
java --source 21 java/ck3-control/war-policy/src/test/java/org/xar/ck3/control/warpolicy/PythonOracleGoldenExporter.java Z:/ck3_mod_rewrite Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe xenoamess-full-tower-eb9d2c1186
```

After Root adds the module to the reactor, the Maven verification scope is
`-pl war-policy -am verify` with the existing external build-root configuration.
The actual writer must record command, source pins, exit/timeout and test results.
This document does not assert that either command has already run.

Before this result affects real choices, a separate integration must connect the
actual producer to Java and a real decision consumer, then validate its observed
business outcome. Passing these pure tests establishes no gameplay, 30-year or
seconds-per-day improvement.
