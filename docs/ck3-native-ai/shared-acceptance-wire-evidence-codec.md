# Shared acceptance wire evidence codec

`wire_evidence_codec` is an explicit host feature with two values: `plain` and
`gzip-members`. The public runtime producer accepts `--wire-evidence-codec`;
Selection validates the manifest and forwards that choice to the selected host.
The default is `plain`. An absent legacy report field means `plain`; explicit
null, another spelling or a different type is invalid.

The choice applies to native-wire, MCP-wire and MCP-calls, including the child
server. Each compressed record is a complete gzip member. Decompressing members
preserves the original JSONL bytes, including Windows CRLF, and record order.
The main report remains plain JSON with its existing atomic publication timing.

Each compressed stream has one small atomic commit sidecar. The host publishes
the three available boundaries in its ordinary report. A boundary binds the
stream ID, held native file identity, completed physical offset, cumulative
logical bytes, record count and last-member hash. Identity and 64-bit coordinates
cross JSON as canonical decimal strings. Windows uses the existing FileIdInfo
provider with explicit empty-file support; it does not substitute an observed
zero `st_ino` for a real FileID.

The Army reader takes its path and codec from the selected report. A bookmark
checks only the last published member. Recovery reads the bounded interval
between published boundaries, verifies each member and its CRC, and checks the
original request ID, query sequence, revision, Army IDs and profile. Physical
compressed ranges and logical JSONL ranges have separate hashes. An unpublished
tail is excluded; malformed, replaced or truncated evidence fails without
resubmitting the query. The target-proof consumer and its CLI consume the same
range contract. Pre-v2 plain bookmarks and proofs retain an explicit legacy
branch; their historical identities do not acquire native-handle qualification.

## Validation and filming boundary

On `machine_id: 4-8e1c2f1861`, observed 2026-10-22 22:47 UTC, the tested worktree
based on `5f2d913c606129d16defd9c9aa0b44249d1df269` has passed:

- The complete public-case CI step: 153 tests, zero skips.
- The complete configured-successor CI step: 112 tests, zero skips.
- The complete 13-module provider step: 143 tests and 74 subtests, zero skips.
- The complete shared acceptance CI step: all 89 commands, 778 tests, zero skips.
- The target-proof CLI serialization group: 5 tests, plus the complete R08
  adapter script: 1 test, zero skips.

Shared acceptance completed in four explicit segments (1–21, 22–40, 41–69 and
70–89). Each adopted command's original process returned zero. Earlier failures
are retained separately. Existing AST fixtures required the real codec helper
or the explicit default `plain` closure; legacy notice fixtures also needed their
current report, startup policy and pump-frame contract. Before continuation,
source comparisons established that the preceding commands did not consume
the changed test leaves. This is a segmented result, not one uninterrupted run
against a byte-identical test tree. Production bytes remained fixed throughout
those fixture corrections.

Final runtime source binding and deployed consumers are still pending at this
observation.
These checks do not prove a newly filmed Hajj, a returned checkpoint or trait
coexistence.

Actual receipts are under
`C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/source-checks/`:

- `wire-codec-entry-a01/public-CHECKS.actual.json`
- `wire-codec-entry-a01/successor-a04-CHECKS.actual.json`
- `wire-codec-host-a01/FINAL.host-provider.actual.json`
- `wire-codec-consumer-a01/consumer-close.a02.actual.json`
- `wire-codec-shared-ci-a01/WHOLE-SHARED-STEP.a06.actual.json`
- `wire-codec-shared-ci-a01/CLOSURE.actual.json`

The complete types/Army-reader modules pass strict checking. Whole legacy host,
provider, client, target-proof and runtime-builder modules retain existing diagnostics; the
recorded comparisons show no additional diagnostics. They are not described as
whole-module green.

The runtime must bind the reviewed host and noncompiled research-consumer delta
to the original native build. Existing native qualification, compiler inputs,
object identities and original build receipts remain required. Compression does
not grant game, storage, recording or checkpoint-continuation qualification.
