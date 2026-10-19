# Knight consumption JSON streaming candidate

The knight consumption serializer now writes retained preparation objects into
its existing parent stream. It avoids complete temporary JSON strings at four
source edges: consumption capture, callback entry inputs, callback preparation,
and each six-stage query capture. The two existing string-returning public
serializers remain available and delegate to the same writers. This candidate
changes allocation/copy work; it does not reduce the result's JSON fields or
encoded size.

This is a **source-only candidate** for a later Native deployment. The new
Robert v20261019 campaign can continue using its separately qualified Native25;
this change does not require waiting for a build. No Native/Game/MCP operation,
new EXE, build, or executable performance/equivalence test ran in this lane.

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

`git diff --check` also passed. No test/build success or runtime deployment is
claimed. The lane writes only small source and audit metadata under Root's
16 MiB allowance, performs no deletion, and leaves heavy-write admission and
full storage reservations with Root under policy 1.0.0. The record's retention
review is due 2027-04-17; the source and recipe remain normal tracked inputs.

## Next qualification and measurement

At the next authorized Native build, first run one bounded offline C++
comparison using fixed-baseline serializer bodies and these candidate writers
against the same owned DTOs. Compare the complete UTF-8 bytes, not parsed JSON
equality alone. Cover absent and present optional sidecars, partial captures,
false/zero/null, maximum full IDs and 64-bit raw values, control-character and
quote/backslash escaping, repeated ordered stages, and a large retained-PC
array. Measure baseline/candidate elapsed time and allocations separately; a
synthetic result is not campaign throughput.

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
