# Actual detachment date and pending inputs (1.20.0.3)

This source-only package continues [the later removal tree](army-later-removal-drain-stage-inputs-12003.md). The qualified [current candidate mapper](army-current-candidate-detachment-mapper-12003.md) supplies an initial current receiver/count preview. Its nine raw occurrences, seven physical mapper rows and actual signed counts are immutable current-seed evidence, not the state after `2633FF0` or a later queue iteration.

The held build is CK3 **1.20.0.3**, Steam **25652598**, EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`, reused without recomputation. Scope was sealed before cached-body reuse in `Z:/ck3_mod_rewrite_process_assets/g2-background-round29-20261006/detachment-date-pending-source/SCOPE-FIRST.json`. This package performs **zero new EXE reads, zero tests/wires/builds, zero model/observer/shared-file changes and zero local game/Steam/SDK/pipe/UI/process/user-data operations**.

## Actual caller inputs and execution order

Held `slice-02633FF0-240.txt` has the semantic caller `[2633FF0,26341A8)` (**440 B**) inside a 576 B cache window. The original metadata selects only the first 9 B `.pdata` fragment; it must not be represented as the complete function extent. The larger held disassembly reaches the caller's final return. Its next-function prefix is excluded from this package's semantics. Existing capture-window SHA `4fc90347668a4517994600bfc8d4d4fae1b8e0cfc4fd31c57356cfed90b0dc33` is reused, not recomputed.

The physical ABI is **`2633FF0(ArRg, Province, date_pointer, primary_receiver)`**: entry RCX is retained in R13, RDX in R14, R8 in RBP and R9 in R15. The previous shorthand `2658180(chunk,Province,date)` omitted its output-buffer argument. The actual four arguments and the caller's signed comparison are necessary numeric inputs.

The held parent-source summary identifies `2A971A0` as the ArRg resolver/magic admission: it uses that ArRg's actual `+140` Army, then `24E0EB0(Army)` or its actual fallback context to supply this Province argument. Consequently the queried subject's current Province is not automatically this passed Province. In a persistent cleanup the incoming ArRg references originate from the selected persistent object's seven association slots; the initial outer candidate roster is a separate source scope. This package reuses that summary without reopening its closed function body.

| Order / source address | Read or effect | Subsequent demand |
| --- | --- | --- |
| `2634007..263402B` | Capture ArRg signed DATA count `+2C`, data pointer `+20`, and end `data + (sign_extend(count)<<4)` once. Loop terminates on cursor equality, not a positive-count gate. | Preserve raw count, pointer, ordered stride-`10h` records and captured cursor/end. A negative count is not a ready empty sequence. |
| `2634040..263408F` | Each fresh record `+8` Regi FullID resolves through registry `5D1EB68`, fallback `5D1EB58`. Selected object must have magic `Regi` at `+14` and FullID `+10 != FFFFFFFF`. | Record-by-record actual generation/fallback selection; no reuse of a finally returned mapper fallback as if it were this selection. |
| `2634095..26340AB` | Signed record ordinal `+C` selects physical address `Regi + 18h + 24h*ordinal`; only the resulting pointer is checked for zero. | Keep raw ordinal separately from occurrence index and physical alias identity. This caller does not add a seven-index or ArRg backlink gate. |
| `26340AD..26340B7` | Signed current `+4 >= maximum +0` invokes closed `2657EA0(chunk,maximum)`. | Predicate and later aliases must see the setter's resulting pair. Its source-closed special clear uses actual raw association/flag/owner cleanup operands when selected; the associated writer's narrower domain cannot substitute for this one. |
| `26340BC..26340C6` | `2658050(chunk)` returns AL. False bypasses all date and pending operations. | Close this predicate first: its actual operands decide which subsequent inputs are used and whether it must be recomputed after an earlier alias write. |
| `26340C8..26340EF` | True stores `chunk+1C = FFFFFFFF029C77F8`, then calls **`2658180(chunk,&output_date,Province,date_pointer)`**. | Actual passed Province and low/high date words; raw predicate-relevant fields after the setter; complete helper output/effects. The output is not the pre-call date. |
| `26340F4..2634108` | Read output qword; compare **signed output low32 > signed caller date low32**. Only then store the full output qword to `chunk+1C` and call **`2A9BE60(primary_receiver,chunk)`**. | Retain both date halves and signed comparison; source-defined append/changed primary state and physical pointer alias. Do not assume raw Army-ID append. |
| `263410D..2634126` | For every valid selected chunk, store `chunk+10 = FFFFFFFF`, byte `chunk+14 = 0`, then advance cursor `+10h`. | Next physical alias reads these writes; association is cleared even when the predicate was false or output date did not exceed the caller date. |
| `2634136..263419C` | After the entire DATA loop, read ArRg Character FullID `+148`. FFFFFFFF returns; otherwise resolve Character registry `5C67568` / fallback `5C67570` using selected `+18` full ID, then tail-call **`28CBE70(Character,Province)`**. | Exact actual Character receiver, independent of pending or DATA loop emptiness. No Character magic/identity guard is introduced here. |

The Regi fallback pointer is loaded into R9 before the DATA loop and reloaded only after a valid chunk's processed path (`2634118`); an invalid record skips that reload. Registry slot/count/payload checks are fresh per record. A sequential model must preserve this held fallback register as well as evolving registry state rather than resolving every failure from an assumed unchanged initial fallback.

`2633FF0` directly reads registries and writes physical chunk fields. It does **not** directly compact Army `+38/+44`. The existing closed nesting remains `2A972B0 -> 2A971A0 -> 2633FF0 -> 24E0D30 -> 2A9E640`; thus a later stable erase can change the outer captured Army buffer payload without shortening its previously captured end. A current mapper count must be recomputed from evolved physical chunks before the next raw occurrence uses it. Subsequent raw queue IDs must be resolved against the changed registry only after the separately closed destruction/invalidation stage.

## Cached Character suffix: direct body exists, inner effects remain explicit

The previous four-helper summary called `28CBE70` uncaptured. Named cache inventory now locates **`slice-028CBE70-210.txt`**, held 528 B `[28CBE70,28CC080)`, with semantic return extent `[28CBE70,28CC079)` (**521 B**) and seven trailing padding bytes. Its existing window SHA is `d91fe10177afcaffb2f31a47d050a094c692f054ceba7b49642f692eb64458b6`. Initial `.pdata` metadata `[28CBE70,28CBE9C)` is only the 44 B prologue fragment; that short slice is not a complete body. No cached body was rehashed or recaptured.

The held continuation gives these actual direct effects, not a transitive lifecycle claim:

- Character `+1B8 == null` returns without these writes or calls.
- Otherwise resolve the `+1B8` object's ArRg ID `+F8`, then its ArRg `+140` Army ID, then Army `+124` Unit ID, each with actual generation/fallback selection. Store the originally loaded object's `+F8 = FFFFFFFF`; if reread Character `+1B8` is nonnull, store its `+100 = FFFFFFFF029C77F8`.
- Call `28B1840(Character)`. Its returned object must have `Prov` magic at `+85C` before calling `28B2730(Character,returned_Province,0,0)`.
- Resolve the selected Unit's `+174` Character owner; its `+1C0` pointer plus `318h`, or the actual static fallback, supplies a count at `+C`. If nonzero, call `2C54340(&output_date,Unit,passed_Province,returned_Province,&current_state_date)`.
- Only signed output low32 greater than signed current-state-date low32 stores the output qword to reread Character `+1B8` object's `+100`.

The `28B1840`, `28B2730` and `2C54340` footprints are not silently closed by those direct calls. This wrapper contains no direct physical DATA/current/Regi-registry/pending-vector write, but its actually selected callees still determine downstream Unit/Character context. That branch is unused when the caller Character ID is FFFFFFFF or the resolved Character's `+1B8` is null.

```mermaid
flowchart TD
    A[Current candidate whole raw roster seed] --> M[Current mapper receiver and count]
    M -.-> E[Unknown earlier detach writes before later occurrence]
    M --> D[Actual selected ArRg DATA cursor/end]
    D --> R{Fresh record Regi resolution and valid tag/ID}
    R -->|invalid| N[Advance raw cursor]
    R -->|valid| P[Physical chunk address from signed raw ordinal]
    P --> C{Current greater than or equal maximum}
    C -->|yes| S[Closed setter: exact pair or source-selected clear]
    C -->|no| B
    S --> B[2658050 actual predicate]
    B -.-> U[Unknown predicate operands: first finite source step]
    B -->|false| W[Clear association10 and byte14]
    B -->|true| I[Store raw date sentinel]
    I --> H[2658180 chunk/output/Province/date]
    H -.-> UH[Unknown actual date output and writes]
    H --> Q{Signed output low32 greater than caller date low32}
    Q -->|no| W
    Q -->|yes| O[Store entire output date]
    O --> V[2A9BE60 primary/chunk]
    V -.-> UV[Unknown source pending changes]
    V --> W
    W --> N
    N -->|more raw records| R
    N -->|captured end| K{ArRg Character148 equals FFFFFFFF}
    K -->|yes| T[Direct caller finished]
    K -->|no| F[Fresh actual Character/fallback receiver]
    F --> CH[Held 28CBE70 direct Character ID/date effects]
    CH -.-> UC[Unknown selected inner location/date effects]
    CH --> T
    T -.-> L[Later stable erase, registry invalidation and next raw queue resolution]
```

## Minimum source and input construction plan

The new external `INPUT-LEDGER.json` distinguishes reusable existing current observations from the complete raw DATA/physical/Character state still required for this caller. The validated associated-DATA writer fields are useful on their actual source-domain subset; they are not proof of the caller's whole raw ArRg DATA cursor, arbitrary raw ordinal, or final fallback role. There is no new full-seven/prepared gate.

The minimum next source step is **`2658050`**, whose body is presently unlocated after named cache filename and disassembly entry searches. Reuse held `PE-MAP.json`: `.pdata` RVA `5DC3000`, size 2933220 B / 244435 records, and section file mapping. Binary-search only that exact entry; maximum 18 selected 12 B records plus a 4 B unwind header (**220 B**) and, if selected, one 12 B CHAININFO record (**232 B**). Publish exact record/raw header/chain provenance before reading body. There is no whole `.pdata` scan.

Only if the selected start is exactly `2658050`, its verified extent is complete and ends at or below the known direct callee entry `2658180`, the proposed first code budget is **at most `130h` / 304 B**, exact verified extent rather than a 304 B window. A fragment, nonmatching start, out-of-bound extent or CHAININFO requiring another extent stops before body capture and produces an amended finite plan. New code requires Root's separate approval after this source package; none is read here.

Once the predicate is closed, the next branch-selected source priorities are `2658180` actual output/effects and `2A9BE60` exact primary/chunk pending update. Each needs its own verified exact `.pdata` extent and finite bound; this plan does not authorize their body reads. The already held Character body avoids duplicate `28CBE70` code I/O; expand only an actually selected inner callee needed to evolve the numerical/current context. No generic allocator/CRT/destructor internals are needed by this stage plan.

The independently useful implementation candidate, **after those required branches are source-defined**, is an ordered conditional DATA-detach prefix with physical alias map and changed date/pending requests. It must read evolving maximum/current/association/byte/date values for every alias, use the captured raw cursor/end and branch-correct mapper count, and preserve ready predicate-false records independently of a different pending/Character branch. No model or new observer is implemented here. Actual detach/post-stage, future drain/lifecycle/calendar/full monthly/live remain false/null.

## Authorized exact metadata attempt: no entry, code still unread

Root approved **metadata only**. On October 6 **18:37:03 CST**, binary search consumed exactly **18 records / 216 B / 18 seeks**, then stopped because there is no record beginning at `2658050`. No unwind header or code byte was read. `2658050-METADATA-ONLY-READ-RECEIPT.json` preserves every actual selected record and the raw provenance.

The already-read consecutive records are RVA `5F49708` / file `5DE0908`, raw `107f65025080650224951005`, describing **`[2657F10,2658050)`** / unwind `5109524`; and RVA `5F49714` / file `5DE0914`, raw `808165022b83650204342605`, describing **`[2658180,265832B)`** / unwind `5263404`. Neither contains the target. Thus the direct called entrance is in a **304 B gap without an independent runtime-function entry**; the gap is not a verified 304 B function body. The original exact-record body proposal cannot be executed as written.

The amended `2658050-UNWIND-LESS-LEAF-PLAN.json` proposes only **at most 32 distinct target code bytes / 32 seeks**, incrementally decoding one instruction from `2658050` without reading ahead beyond a terminal return. No header/neighbor/helper body is read. If a branch needs bytes outside that bounded prefix, a call supplies an unresolved result, an indirect transfer appears, or 32 B do not reach the complete predicate, preserve the actual partial instructions and publish the concrete continuation before further reads. No predicate semantics, frameless-body classification or code-read qualification is inferred from the `.pdata` gap. This requires Root's separate code authorization; code remains **0 B** at this source update.

## Authorized first target prefix: actual association lookup, predicate still partial

Root then approved the target-only 32 B decode. It read exactly **`[2658050,2658070)` / 32 B / 32 seeks** on October 6 **18:42:07 CST** and stopped at the planned bound without reading a return, neighbor, metadata or old code. The actual first instruction loads ArRg registry `5D1F340`. The remaining captured instructions read **physical chunk `+10` association FullID**, keep its low 24-bit index, compare registry `+2C`, and load its `+20` slot data. Failure branches at `265805A` and `265806A` both target **`2658082`**, outside the first approved prefix. `2658050-TARGET-LEAF-READ-RECEIPT.json` and `function-02658050.asm.txt` preserve all raw bytes and instructions.

This proves an evolving association input is used by the predicate: after a preceding alias's closed `chunk+10=-1` store, its next invocation reads that changed field. It does **not** yet define AL, identity/tag admission, the final fallback rule or all helper effects. The new `2658050-CONTINUATION-PLAN.json` proposes at most **64 additional distinct B / 64 seeks** in `[2658070,26580B0)`, starting only the unfinished fallthrough and the known `2658082` branch. Reuse all first-prefix bytes; stop at actual returns on all selected paths. A remaining outside target, indirect transfer or required callee becomes a concrete partial continuation, not a new inferred body. New code requires separate Root approval. Cumulative actual EXE cost so far is **216 metadata B + 32 code B / 50 seeks**; no model, observer, test, native build or local game operation is performed.
