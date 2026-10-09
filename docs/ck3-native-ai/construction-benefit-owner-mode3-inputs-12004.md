# Construction benefit: reached owner mode3 input — CK3 1.20.0.4

Status: **research**, recorded 2026-10-09. This package identifies the smallest
remaining source entrance needed to investigate building-specific realized
income. It adds no policy, readiness gate, production field, M4 credit or test.

Exact native identity remains CK3 **1.20.0.4**, Steam **25734779**, retained
EXE SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The inspected producer source is
`Z:/gbs-runtime48-construction-latch-root-source` at
`dd302e80ed5eb6513a3bea1f9ea39c6abd305f5f`; this is an inspection locator,
not a replacement for Root's newer deployment pin. No EXE or binary payload
was read or hashed by this package.

## Existing inputs and the missing independent value

The current construction reader has these distinct sources:

| Source | Already observed meaning | Missing meaning |
| --- | --- | --- |
| `ck3_12004_construction.cpp:404` / `Province+0x718` | Current province income aggregate | One building's effective contribution and holder transfer |
| `ck3_12002_construction_authored_income.hpp` / 19 canonical keys | Authored unconditional province `monthly_income` | Conditional/contextual effects and realized player tax |
| `construction_economic_value_v1.py` | Target authored value minus known old-slot authored value | Guaranteed marginal yield or causal realized NET |
| `ck3_12004_construction_held.cpp:212` / `Title+0x128` | Actual player ownership match | Income distribution, holder tax or receipt |
| Existing cash-v2 sources | Actor gross, complete expenses and true NET | Per-building attribution |

The Python authored-value reader explicitly omits conditional extra effects.
Its five additional occupant entries describe old-slot authored comparisons;
they are not additional effective-income observations. Native final-cost
evaluation returns a ten-resource purchase cost, not a benefit value.

The existing economic outcome classifier correctly preserves aggregate
before/post observations while leaving `building_attribution_ready`,
`net_benefit_ready` and `m5_realized_value_ready` false. Neither a positive
aggregate NET difference nor a positive authored delta proves one building's
actual yield. The useful missing input is a context-qualified contribution
of the particular definition, including applicable modifiers, and its
actual transfer into the player's income. No current source field supplies
that value, so adding a Python formula or a placeholder native field would
not close it.

## Reused reached source and finite next body

The [construction economic source tree](construction-economic-consumers-12004.md)
already closes the completed-slot callback and its mode3 context through
actual `28662F0..286669E`. Its exact exit at `2866699` restores the stack and
tail-jumps to **`2479F50`**, with RCX equal to the owner from `P+0x5D0` and
EDX equal to the preserved mode **3** (`P = holdingF0+0x28`). The original
mode enters the closed callback edge `246CBEE -> 28662F0`.

No explicit building definition, numerical income output or Province+0x718
write has been established in that calling contract. The reached owner may
still carry relevant contextual inputs; its target body must be inspected
before assigning benefit or transfer semantics.

One exact lookup in the retained `OLD-RUNTIME-FUNCTIONS.json` and
`NEW-RUNTIME-FUNCTIONS.json` under the central `function-match-core` cache
finds these entry intervals:

| Image | Held runtime row | Range / bytes |
| --- | --- | --- |
| `.3` | `[38248304, 38248511, 85059696]` | `[2479F70,247A03F)` / **207** |
| `.4` | `[38248272, 38248479, 85059936]` | `[2479F50,247A01F)` / **207** |

The two concrete tail targets identify the proposed entries independently;
the identical length or ordinal alone is not semantic proof. A nonrecursive
named-range lookup in the five existing central cache directories found no
range covering either target. That lookup read filenames only, with zero
binary payload reads. No broader ownership or reverse-engineering census
was performed.

Root's single proposed next capture is therefore **414 bytes / two range
reads**, exactly one held runtime interval per frozen image. A complete
function return is not preasserted: chained code, callees and other intervals
remain outside this first capture. The goal is to record concrete reads,
writes, branch conditions and return/tail operands, then determine whether
they expose a useful independent benefit input. It is not an invitation to
expand a generic modifier or holder-tax tree.

```mermaid
flowchart TD
    C[Actual completed slot callback246CA40] --> P[Closed context28662F0 / P / mode3]
    P --> X[2866699 owner from P+5D0 / restore mode3]
    X --> T[Reached target2479F50 / one held207B interval]
    T -. body not yet captured .-> V[Province718 recomputation or other concrete output]
    V -. definition contribution and holder transfer unclosed .-> N[Attributed player NET]
    A[Existing province aggregate and cash-v2 NET] --> O[Observed aggregate change only]
```

Prepared Root-only artifacts are under
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/construction-benefit-owner-mode3-source/`:

- `OWNER-MODE3-REACHED-ENTRY-MANIFEST.json`: the exact old/current entries,
  held runtime rows and 207-byte bounds.
- `ROOT-READ-ARGV.json`: the existing central finite mapper invocation,
  output `owner-mode3-root-first01/`. It is **not executed by this package**.

Until Root supplies that actual generated source detail, the body and its
relation to Province+0x718/holder NET remain **unclosed**. Ordinary game
progress, natural completion observations and current cash decisions retain
their existing behavior; this research adds no new completion or income gate.
