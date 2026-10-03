# Current player mercenary reinforcement context, exact 1.20.0.3

The new read-only `ck3_query_player_mercenary_context_v1(expected_revision)` copies the current player's world mercenary candidates, native final hire permission, all ten resource prices, native payment status, current soldiers, employer, company home and the actual native hire auto-raise selector. The immediate gameplay input is Robert 29829's defense of capital 2640. Root's latest saved ordinary-campaign baseline is calendar 4025 / raw date 53240928; this file-only work has advanced zero days and has observed no current mercenary market.

Exact build: CK3 **1.20.0.3**, Steam build **25652598**, executable SHA-256 **94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6**. Current player / original ordinary campaign / episode `native-29829-2bc2d599f7f9` remains the runtime entrance. The query has no actor or company parameter and submits no hire command.

## Reused native tree and new closed inputs

The existing [war finance and hire tree](ck3-1.20.0.3-war-finance-and-hire.md) is the research starting point. The three new exact-build topics preserve the evidence and callable boundaries:

- [Candidate manager and real current soldiers](ck3-1.20.0.3-mercenary-candidates-native-query.md).
- [Final permission, quote, payment and contract duration](mercenary-final-hire-terms-native-query-12003.md).
- [Company home, actual auto-raise selector and command chain](mercenary-hire-spawn-selection-12003.md).

The company manager is `0x5D1DF08`, fallback `0x5D1DEF8`; live slots are copied on application-main. Generation-bearing company IDs, including legal zero, remain company IDs. They are never army IDs. Null/fallback slots are omitted; hired or unhireable companies remain observable rows. Native current soldiers calls `0x2625720`; the result is a plain signed soldier count, not a Q100000 value or nominal maximum.

For every real candidate, native mode 1 is passed to `CanHire 0x26242D0` and `PaymentStatus 0x2625470`. The independent quote is `0x26253B0`, retaining all ten signed raw Q100000 slots. Generic `CanAfford 0x310E710` is published independently. Payment status 0 means unaffordable, 1 native permitted debt, and 2 fully funded. A native permitted-debt row can have `CanHire=true` and generic `CanAfford=false`; the query retains this actual distinction. It does not invent a cash policy or convert native false permission into a free candidate. Literal temporary native reasons are copied before native string destruction. Contract months use `0x2625580`.

Company home is company `+0x24` title through title-province getter `0x230F900`. The actual active-war hire path uses `0x26247D0 → 0x2625AC0 → 0x24A6AB0(actor)`, then validated province resolution and `0x262606D → 0x2A96EA0`. `0x24A6AB0` chooses an actual usable rally point and falls back to capital only when none exists. The existing default-raise query uses a different selector and cannot stand in for this field. Home and actual hire auto-raise province are separate fields. When actor wars are empty, this query records no auto-raise attempt; it does not call the selector or fabricate a spawn province. A predicted selector result does not prove hire execution or army creation.

```mermaid
flowchart TD
    A[Current played actor on application-main] --> B[Actual mercenary manager slots]
    B --> C[Copied company ID, employer and native current soldiers]
    B --> D[Native final CanHire, ten-slot quote, PaymentStatus, CanAfford, months]
    B --> E[Company home title and province]
    A --> W{Actor has active wars?}
    W -->|yes| F[Actual hire selector 0x24A6AB0 and province resolution]
    W -->|no| N[No auto-raise attempt; no spawn province]
    C --> Q[Same-frame read-only command result]
    D --> Q
    E --> Q
    F --> Q
    N --> Q
    Q --> M[Registered current-player MCP, exact actor/date/epoch binding]
    M -. current paused market pending Root .-> R[Current legal candidate and nearby reinforcement decision]
    B -. native AI hire cadence, ranking and tie-break unknown .-> U[Native AI chooser]
    R -. typed hire and independent army/payment after-state not implemented here .-> H[Actual reinforcement]
```

## Owner, lifecycle and failure meanings

The named executor `permitted_executor_player_mercenary_context12003` is registered at exact .3 startup and participates in the existing install, executor-presence admission, submit and uninstall lifecycle. It resolves the current played character in the existing query mailbox, builds the real title/province world bindings, copies leaves, and completes using the captured actor/date/epoch frame. No new feature flag or authorization gate is introduced.

Collection availability is independent from row leaf availability. An available empty manager is a real empty market. `current_soldiers=0` is a real observed zero. Native `can_hire=false` is a usable qualification outcome, not a transport failure. Failed home resolution preserves independently readable actual hire province and vice versa. A missing quote, payment or spawn input remains an explicit row failure and cannot be used to decide a concrete hire.

Protocol step: `query-player-mercenary-context-v1`; capability: `game.command.query-player-mercenary-context-v1`; inner schema: `ck3_12003_player_mercenary_context_v1`. The existing bridge revision remains required. Root performs one fresh paused query after the combined v46 build, using a same-frame public snapshot revision. The frozen query recipe is in external `war-mercenary-reinforcement-v45/delivery/MERCENARY-QUERY-CONFIG.json`.

## Evidence and readiness

External package root: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war-mercenary-reinforcement-v45`.

- Candidate focused attempt 02 is GREEN; the complete genuine 226-byte current-soldier getter ran with declared external dependency stubs. Attempt 01's fixture signed-literal warning is retained.
- Final terms focused-native-01 is GREEN with three scenarios, 45 explicit checks, native reasons freed, and permitted debt preserved.
- Position focused fixture is GREEN with four new cases distinguishing home, actual spawn, peace and partial reads.
- Integration `focused-native-01` executes the actual candidate/context/final-terms/position readers and production wire serializer: one new scenario, 31 explicit checks, `/O2 /DNDEBUG /W4 /WX`, GREEN. Its genuine 2684-byte wire SHA-256 is `b75c067aa914d3d4a802515e8fa57a1b8e99efd31e966c3b6b6e3183c73de4e1`.
- Python `focused-mcp-01` consumes those unchanged wire bytes through the actual registered MCP, service, driver and normalizer: one new case, 16 explicit checks, `-O -B`, GREEN. The endpoint/hello/frame fixture remains synthetic and is not Robert live evidence.
- Four changed executor translation units compile GREEN against frozen `Z:/g47` source `7a0bef46588292d26c74716a39fe02b348d3ee65`. The initial old-g46 bridge C1061 is retained; only bridge and subsequently changed adapter translation units were recompiled against the actual baseline.

Readiness is **static-ready**. There have been zero game/SDK/window calls, zero days, zero hires/payments and zero army-gain credit from this worker package. The actual current market, a production-live query and a complete hire/army after-state loop remain pending Root. Native AI ranking remains an explicit research branch; it does not prevent reading the closed final player qualification inputs. No hire executor or strategy change is included.

## Production-live primitive: v46 current ordinary campaign, consumed 2026-10-04

The sole fresh paused query is external `runtime-preparation/v46/actual-sway-retention-mercenary-gathering-01/013-ck3_query_player_mercenary_context_v1.json`. Mercenary query and checkpoint calls are GREEN. The multi-domain batch is RED because a separate sway query returned RED; this is not a mercenary capability failure. Root reports the actual SDK47704 session normally closed. No query or game action was repeated by the file consumer.

Actual frame: current Robert **29829**, original episode `native-29829-2bc2d599f7f9`, raw date **53240928** / calendar **4025**, native revision **3**, public revision **2**, query sequence **1**, capture epoch **23172**, native hire mode **1**. Collection is available with **559** real company rows; all 559 final terms and native current strength reads are available. There are **33** native `CanHire=true` candidates, all 33 with `CanAfford=true`, payment status **2**, employer **null**, and **36** contract months. Every observed hire auto-raise selector is **2618**, with actor war count **3**. This is a native predicted active-war spawn input, not proof that any company was hired or army created.

Current saved-batch initial/final resources are equal: gold raw **106634828**, prestige raw **279109860**, piety raw **37383750**, all scale **100000**; i.e. gold **1066.34828**, prestige **2791.09860**, piety **373.83750**. The maximum current aggregate force candidate is company **286** with **2531** soldiers, **811** gold (raw `[81100000,0,0,0,0,0,0,0,0,0]`), home **2560**, actual predicted spawn **2618**. Company **289** exposes **2511** soldiers / **735** gold / home **2501**; company **48**, **2491** / **729** / home **4582**. The cheapest and highest aggregate soldiers-per-gold candidate is **297**, **837** soldiers / **202** gold (4.14356 soldiers/gold); middle-sized **514** is **1647** / **420**, and **294** is **1674** / **428**. These are declared factual comparisons, not the native AI winner or battle quality estimates.

All 33 candidates and all ten signed resource slots are retained in external `war-mercenary-reinforcement-v45/actual-v46/ACTUAL-RECEIPT.json`; the concise 33-row table is `CANDIDATE-TABLE.md`. The current query publishes aggregate native soldiers, not per-type regiment composition, damage/toughness, knight or commander quality; no such data is inferred from price or company ID. A hired result and a capital arrival before the deadline have not been observed.

The current checkpoint is saved at history **5509**, raw date **53240928**, **91443885** bytes, SHA-256 **7ded957a3c703ceb5bd5bd3515444c5c04d01de0594da1812a2ba99440fabafb**. The raw query artifact is **1948654** bytes, SHA-256 **0e65416298a95479eb7b81ee7cb64f6eef25b046d6f3e46f4656bb0871c66529**. Source packets and copied production body remain immutable evidence; consumer receipts add no days, hires, payments or army credit.

Readiness has advanced from initial **static-ready** to **production-live primitive** for this current-player mercenary observation. The next concrete dependency is the normal typed hire action plus independent employer/contract, wealth and player-army after-state. Root authorized file-only parallel implementation against frozen `Z:/g49`; it does not credit submitted/queued commands as actual hires. Native AI chooser scoring remains a separate tree branch, and current manager enumeration order is not a winner.
