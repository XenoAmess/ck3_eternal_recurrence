# Knight consumption JSON streaming candidate

The knight consumption serializer now writes retained preparation objects into
its existing parent stream. It avoids complete temporary JSON strings at four
source edges: consumption capture, callback entry inputs, callback preparation,
and each six-stage query capture. The two existing string-returning public
serializers remain available and delegate to the same writers. This candidate
changes allocation/copy work; it does not reduce the result's JSON fields or
encoded size.

The candidate is now **offline C++ byte-equivalent**, with no runtime deployment.
The new Robert v20261019 campaign continues using its separately qualified
Native25. A small isolated fixture ran through an ordinary Python/DLL child;
no Native/Game/MCP operation or full bridge build occurred. The measured
synthetic timing difference is small and overlapping, so no reliable speedup
is claimed.

## Grounded scope

The existing [P67/P68 sealed summary](evidence/p67-p68-combat-query-archive-performance-2026-10-18.json)
records AUTO77's consumption contexts as the dominant retained object: 144
contexts, with about 12 MB of consumption preparation and about 12 MB of entry
inputs. This lane read that small summary only. It did not reopen, decode, copy,
or benchmark the historical 100 MB response or 26 MB archive. P67 did not split
Native CPU, transport, and Python cost, so those historical timings cannot
quantify this candidate's benefit.

The exact source opportunity was independent of archive policy. Each context
previously serialized its owned preparation into a child `ostringstream`,
copied that buffer into a returned string, then inserted that string into the
parent. Entry inputs repeated that operation for their own preparation. The
writer paths retain every capture occurrence, output literal, ordering loop,
raw integer representation, unavailable reason, and DTO access. They neither
deduplicate captures nor reuse another frame's data. Current-input/outcome
binding serialization and the outer complete result remain unchanged.

The enclosing streams use their existing default JSON formatting. Existing
pointer helpers restore decimal formatting; the callback string helper restores
fill after control-character escaping. The new writer APIs document this
default-format stream contract. No custom-stream formatting API is introduced.

## Completed source audit and boundary

[The small receipt](evidence/knight-json-streaming-source-conservation-2026-10-19.json)
binds the actual machine to `machine_id: xenoamess-full-tower-eb9d2c1186`, observed
at `2026-10-19T01:48:20.142589+00:00`. Its sources are the stable machine helper,
fixed Git commit `652e873ab164cfb78b654854c0dc2ca35ef816b3`, five current small
source leaves, and the project-volume capacity read. These are facts about that
machine and observation time only.

The runnable [source conservation audit](../../tools/g2_saved_campaign/audit_knight_json_streaming_12004.py)
passed all five full-file comparisons. It reconstructs only the declared
signature/call changes from fixed Git blobs and requires the entire remaining
source text to match, including helpers and all emitted fields. It reads Git
blobs in memory and emits a small JSON receipt. It does not prove executable
equivalence, allocation counts, or latency. Reproduce the check without writing
or overwriting the original receipt:

```text
python -B -X utf8 tools/g2_saved_campaign/audit_knight_json_streaming_12004.py
```

`git diff --check` also passed. That initial audit was source-only and did not
claim build or execution success. It remains unchanged as historical evidence.
The record's retention review is due 2027-04-17; source and recipes remain normal
tracked inputs.

## Actual isolated C++ qualification

Root subsequently authorized one bounded executable comparison inside the
existing code/profile budget. The [qualification seal](evidence/knight-json-streaming-cpp-qualification-2026-10-19.json)
records actual machine `xenoamess-full-tower-eb9d2c1186`, UTC observation, source,
compiler/header/DLL pins, original failure, successful retry and storage child.
The [producer](../../tools/run_knight_json_streaming_fixture_12004.py) extracts
unchanged pure serializer/helper spans from baseline `652e873a` and candidate
`d90d5e79`; namespace and preprocessor symbol isolation occur outside their
function bodies. The [fixture template](../../ck3_autonomous_player/native_bridge/tests/knight_json_streaming_12004_fixture_main.cpp.in)
supplies owned instances of the actual production DTO types, with their project
header closure frozen from the same candidate commit. It implements no replacement
serializer and links no hooks, Game readers or bridge runtime.

Nine complete UTF-8 comparisons pass: null/empty objects, empty arrays, false
and zero, signed/unsigned 64-bit extremes and full IDs, quotes/backslashes and
control characters including NUL, UTF-8 Chinese text, partial optional nested
PC properties, repeated ordered captures, direct writers inside a default-format
parent stream, and a **7,727,887-byte** nested knight result. Old/new wire SHA-256
pairs match in every case. No complete synthetic result was duplicated to disk.

MSVC 14.51.36231 used C++20, `/W4 /WX /O2 /MD`. The original attempt is retained
as RED because the fixture assigned an `int` zero to `optional<uint16_t>`;
that fixture zero was explicitly typed and UTF-8 Chinese text coverage was
added before the necessary fresh attempt02. Production serializer bodies did
not change. Both successful
EXE and fallback DLL compile/link stages returned zero.

The existing exact-source EXE registration helper returned
`settings_failed/admin_required_for_verified_readback`, with no setting calls,
no UAC, and no new system configuration. The EXE was never executed. As explicitly
authorized by Root, the same bounded fixture was compiled as a DLL with one C
export and loaded only by an independent ordinary Python `ctypes` child. That
child exited zero. No DLL exclusion or EXE registration success is claimed.

The five alternating old/new serializer samples exclude DTO construction,
comparison, hashing and result destruction. The old median is **109.2761 ms**;
the candidate median is **108.0227 ms**, about **1.15%** lower. Their ranges overlap.
This is useful byte-equivalence evidence and a small synthetic timing result;
it does not establish a reliable performance improvement. Per-field stream
formatting remains the next grounded profiling target. The benchmark was not
repeated to obtain a more favorable result.

At closure the isolated work root held 65 files and **2,914,443 logical bytes**,
including the original RED attempt, compiled outputs and receipts. Physical
allocation was not measured. This fits the approved 64 MiB estimate and
512 MiB maximum inside the existing code/profile subbudget, without new global
reservation or deletion. No compiler/fixture process or pending child write
remained; the external child review is due 2026-10-20T01:48:56.993837Z.

## Next qualification and measurement

The bounded C++ comparison above closes executable byte equivalence for the
covered DTOs and default-format stream contract. Do not rerun it merely for
deployment paperwork. A later source change, failure or new unresolved case can
justify additional focused validation. Allocation counts were not measured.

For the next necessary real combat-input query, retain its actual machine ID,
UTC observation, EXE/DLL/SDK source tuple, actor/episode/date/native revision,
query sequence and exact selected step. Use its complete original retained
DTOs for an offline A/B after capture. Natural observers may change between
two live queries even while the game is paused; unrelated live results are
not a same-input comparison.

The relevant production boundaries are `bridge.cpp`'s
`ReadCombatSimulationInputs` call, `CombatSimulationInputsResultFrame`, its
`AppendCombatSimulationInputs` / `SerializeKnightStatConsumptionQuery12004`
serialization, and the subsequent `write_frame`. Record serialization separately
from read/observer capture and pipe write. The current path has no dedicated
knight-serialization timer; whole AUTO or MCP elapsed time alone cannot isolate
the change. Any future timing hooks must be opt-in and must not alter emitted
business fields or perform a second query. Measure completed-window
seconds/game-day separately before claiming ordinary-play throughput improved.
