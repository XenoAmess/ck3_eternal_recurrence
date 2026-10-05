# First-contact person preparation frontier, exact 1.20.0.3

2026-10-05 / ISO 2026-W41. This source package closes one missing native predicate before the existing A/B context sources and specifies the smallest additional current observation. It does not change the source freeze or claim a constructed Combat Entry.

The exact build is CK3 1.20.0.3 / Steam25652598, frozen EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`, image base `0x140000000`. The reused source file is `Z:/ck3_mod_rewrite/artifacts/migrations/2026-10-02/installed-build/binaries/ck3.exe`. The package is at `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/background-user-session-round02/battle-entry/`.

## Where the existing current prefix ends

The cached `291C0D0` caller sets `R13=model`, `R14=QWORD[model+8]` as the Character and `RSI=model+10` as the context. Existing current prior inputs observe the provider `+1530`, common `+1A48` and selected `+18F8/+19A0` contributions. The independently closed `291C204 -> 291D1D0` current contribution uses `context_branch_inputs`: actual `flag14`, selected index and seven group counts/property blocks. These are current prepared inputs; changed-stage receiver/held-title/qualifier reconstruction remains a separate dependency.

Between that prepared frontier and `291C282 -> 291E210`, the caller has an additional condition at `291C255`, followed by the unit contribution at `291C277`. Neither existing prior inputs nor A's four spans provide it. V86 closes the later A/B admission and prepared locale selection. R46's 21 observed empty current leaves are genuine observations of those leaves; they do not fill this missing caller contribution or construct a complete person/Entry.

## Exact predicate and contribution

`291C209` reads `Character+1B8`; a present carrier supplies its full DWORD Army key at `+F4`. The caller resolves it through Army storage slot `5D1DE48`, comparing the full DWORD object ID at `+10`. Readable native null/out-of-range/missing/generation-mismatch paths select `QWORD[5D1DE50]`. A null Character carrier also selects this fallback. It does not skip the predicate. Existing native binding metadata names `5D1DE48` as `army_internal_storage_slot`.

The actual call operand at `291C255` is VA `0x1424DFB70`, hence RVA **`24DFB70`**. The early FAST note dropped the leading `2`; this was corrected before any code read, and no bytes were sampled from RVA `4DFB70`.

`24DFB70` is a complete 88-byte frameless leaf. Adjacent `.pdata` records end at `24DFB70` and start at `24DFBD0`; the single captured 96-byte gap contains the leaf and eight bytes of INT3 padding. The leaf has no calls, writes or initialization:

1. Read DWORD `selectedArmy+120`. Exactly `FFFFFFFF` returns AL0 without reading `+124` or the second registry.
2. Otherwise read DWORD `selectedArmy+124` as the full requested key. Resolve it through storage slot `5D1E380`: low24 index, unsigned capacity `+2C`, slots `+20` with stride16/pointer `+8`, then exact full DWORD object `+10`. Native resolution failure selects `QWORD[5D1E378]`.
3. Return AL1 exactly when Army `+120` equals the selected second object's DWORD `+174`; otherwise return AL0. Upper EAX is not the boolean result. The second object's business type is not inferred.

An actual true result continues through `291C25E -> 8FD4E0`, reads `QWORD[provider+1640]+40`, and calls `2438850(model+10, property_block, 100000)` at `291C277`. False returns directly to the subsequent A call. The source therefore has an actual unit-weight merge in a precise place in the native construction order.

```mermaid
flowchart TD
  P["Existing current prior contribution inputs"] --> T["291C204 -> 291D1D0 prepared current group contributions"]
  T --> L["Character+1B8, carrier+F4 full Army key"]
  L -->|native resolved| A["Selected Army"]
  L -->|native null/miss| AF["Actual Army fallback5D1DE50"]
  A --> R["24DFB70: Army+120 DWORD"]
  AF --> R
  R -->|FFFFFFFF| N["AL0, no later predicate reads"]
  R -->|other raw value| S["Army+124 full key -> slot5D1E380 / fallback5D1E378"]
  S --> Q["Compare Army+120 with selected second+174 DWORD"]
  Q -->|equal| Y["AL1"]
  Q -->|different| N
  Y --> PC["provider1640 definition+40"]
  PC --> W["291C277 -> 2438850, weight100000"]
  W --> CA["291C282 A weighted sources"]
  N --> CA
  CA --> CB["291C298 B admitted source prefix"]
  CB --> POST["Task/Position then caller suffix contributions"]
  POST -.-> F["Remaining fullperson/source-bound stage construction"]
  F -.-> E["Entry effective-input identity and actual first-contact caller"]
  T -. "changed-stage receiver/census association" .-> U["unclosed new-stage binding"]
  classDef unknown stroke-dasharray: 5 5;
  class F,E,U unknown;
```

## Smallest current readonly construction

Add an optional `pre_291e210_1640` object under the existing `current_context_source_inputs` section, preserving its actor and outer frame provenance. No additional MCP query is required. The proposed fields and read order are specified in `OBSERVER-CONSTRUCTION-PACKAGE.json`.

| Required input | Current coverage | Minimal increment |
| --- | --- | --- |
| Validated current Character / source frame | Existing current-person observation | Reuse the actual actor/frame |
| Army storage `5D1DE48` and native fallback `5D1DE50` | Existing internal Army binding / native caller | Reuse the closed lookup and fallback |
| Character carrier `+1B8`, full Army key `+F4` | Existing source paths use this carrier; this contribution is not emitted | Sample the native selected Army for this branch |
| Army DWORDs `+120/+124` | Not emitted for this predicate | Emit raw32 operands; `+124` is not demanded when `+120==-1` |
| Second registry `5D1E380`, fallback `5D1E378`, selected DWORD `+174` | Not emitted for this predicate | Two binding slots and the consumed current operand |
| Exact AL admission | Missing | Project the closed read-only equality predicate |
| Provider `+1640` definition `+40` | Getter and paired-property reader already closed; this block absent | Read the property block only on actual true admission |
| Current A four spans / B admission/token prefix | Existing V85/V86 fields | Keep as later separate contributions |
| Current final stored context | Independently observed current final state | Preserve it as current final; it is not a before-A/B baseline |

The predicate can be implemented with ordinary readonly memory reads; calling the native predicate is unnecessary. Preserve full DWORD identities and signed raw32 wire bits. An actual zero operand can compare equal; positive IDs do not establish admission. A failed read must not be converted into a native lookup miss, fallback, null or false. False admission leaves the property block not demanded. True admission retains the existing paired-property observation's real counts, empty vectors and failure status.

A source-bound assembler adds this contribution after `291D1D0` and before A. It requires the explicit correct stage baseline. The current final stored context cannot be used as that baseline or receive the contribution a second time.

## Remaining complete-person/Entry distinction

The companion B ledger records the next unmapped current caller suffix at `291C2B3`: `Character+1B0`, actual fallback `5D1E308`, signed16 `Character+68`, signed32 threshold `5C6A19C`, and the conditionally merged property block `object+630` at `291C2FE`. The subsequent `291C32C` carrier contribution and `291C334 -> 28B6200` pointer-vector source are separate remaining inputs. Later fullperson auxiliary outputs also retain their exact callsite ledger.

Entry's `2C06D30` consumes Character EC and another context returned by `28BFC70`, passed to `2C06B00`. The existing sources do not prove that context is identical to `model+10` or establish the first-contact source-stage association. Current prefix contributions and current scalar values cannot establish a new Entry by themselves. These remaining branches are recorded with concrete xrefs in `branch-b-person/`, without a new broad audit or source capture.

## Work qualification

This round is native source research plus a concrete readonly construction contract. Two existing source lanes were reused. Only the single predicate leaf was captured from the frozen offline EXE, using bounded seek reads; `.pdata` absence is retained as a lookup diagnostic. No EXE scan or rehash, game/SDK/pipe/attach/window/profile activity, query-domain consumption, prepare/build/launch, compilation, test or game-day advance occurred. No implementation was installed and no current source-freeze bytes changed.

Oct5/W41 fields, exact source pins, byte/read logs, new Mermaid trees and the one-file documentation patch are in the parent `ROOT-DELIVERY.json`. No live, static implementation or complete Entry claim is made.

## Offline implementation increment, 2026-10-05

The vacation successor implemented the source-closed `pre_291e210_1640` leaf in the existing current-person query. The native DTO, exact-build bindings, readonly collector, serializer and strict Python normalizer now carry the same Character ID, native selections, signed32 raw operands, nullable AL admission and paired PropertyContainer. The two new registry bindings are `5D1E380/5D1E378`; Army `5D1DE48/5D1DE50` and the closed `8FD4E0` provider are reused. No query or command was added.

The actual demand order is retained. Null Character carrier selects the actual Army fallback. A readable null registry bypasses its requested-key read; bounds/null-slot/full-generation misses use its actual fallback. An unread registry/operand remains partial. `Army+120==-1` skips `+124`, the secondary registry and provider; other raw values, including zero and negative signed wire values, compare by exact DWORD bits. The provider and `1640` property block are demanded only on true admission. An empty key vector remains an available native observation without demanding unused value fields.

`emit_pre_291e210_1640_requests_from_current_source_inputs_12003` emits the admitted unit request, preserving the actual block and empty request. Its position is **current prior prefix → `291D1D0` → `pre_291e210_1640` → A `291E210` → B `291D7E0` → remaining suffix**. This increment emits a contribution; it neither selects a stage baseline nor writes or rebuilds a context. Observed current final storage remains current final storage.

Offline Python validation ran once: `py -m pytest -q ck3_autonomous_player/tests/unit/test_battle_pre_291e210_1640_12003.py`, with this checkout's `ck3_autonomous_player/src` on `PYTHONPATH`: **16 passed**. The new cases cover signed raw types, zero/negative equality, early false, fallback operands, partial read/PC status, actor join, older producer compatibility and unit-request block preservation. Receipt/log: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/background-implementation/battle-entry/python-tests.json` and `python-tests.log`. `open_kaishek` is not applicable: these are native-memory DTO/JSON observations and not Paradox script semantics.

The focused fake-memory native target is `xar_ck3_12003_pre_291e210_1640_test`, using the production collector and serializer. It additionally checks exact RVA binding, full-generation mismatch fallback and undemanded reads. This lane did **not** build or run it; the root integrator owns the one combined native build. Qualification at handoff is Python **static-ready**, native source implemented with compile/fixture execution pending; no new `fixture-live`, `production-live primitive`, `production-live loop`, game day, person or Entry credit. The user's current instruction forbids CK3 launch, attach, query, UI, Steam and stop activity; all implementation and testing here stayed offline.

The remaining exact breakpoints above are unchanged: post-A/B `291C2B3/C2FE`, `291C32C`, `291C334→28B6200`; changed-stage receiver/title/qualifier/count associations; scratch `430/438`; and `28BFC70→2C06B00` effectiveness-context identity plus the actual first-contact caller. The independently assigned suffix source research can add knowledge without turning this prefix into a complete Entry.


## Post-A/B person source suffix, exact 1.20.0.3

2026-10-05 / ISO 2026-W41. This bounded offline continuation closes the physical bindings of three native contribution families immediately after the current A/B stages. It extends the known pre-A `1640` frontier without replacing that contribution. Qualification remains **research**: no observer implementation, compiler, test, game query or live sampling occurred.

Reuse the existing exact CK3 1.20.0.3 / Steam25652598 pin, EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`, image base `0x140000000`. The frozen file is `Z:/ck3_mod_rewrite/artifacts/migrations/2026-10-02/installed-build/binaries/ck3.exe`. There was no full-file hash or scan. Source receipt and field contract are in `Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/entry-next-stage-research/`.

### Caller stage order and direct guards

The reused `caller-after-A-B.asm` window is `[291C2B3,291C370)`; its existing text pin is `fe0974406968f2d63bdd6750c514cb0ea8f5915d3e86e3570dd743e1ed255787`. The same caller binds `R14=Character`, `RSI=model+10`. All three families call `2438850` with weight **100000**, in the following order after `291C282->291E210` (A) and `291C298->291D7E0` (B).

1. **`291C2FE` direct guarded property.** Read `Character+1B0` as a pointer. If it is nonnull and its QWORD `+280` is nonnull, select `QWORD[carrier280+8]`; otherwise select the actual native `QWORD[5D1E308]` fallback. At `291C2D8`, demand DWORD `selected+38 == 0x4744624F`. Only when equal, read `Character+68` as signed16 and the loaded `DWORD[5C6A19C]` as signed32; `JL` skips when sign-extended Character operand is smaller. True admission merges the property block **`selected+630`** at `291C2FE`. Null Character carrier does not by itself imply false: the fallback participates in both guards. The body does not add a null guard for `carrier280+8`; the observer must distinguish failure to read this selected object from a native null carrier/fallback choice. No business name is inferred from the magic, the Character operand or the fallback.
2. **`291C32C` second carrier property.** After the first admitted writer, native code rereads `Character+1B0` at `291C303`; on its skipped path the earlier carrier remains in RCX. The next family requires this carrier and its QWORD `+288` both nonnull. It selects `QWORD[carrier288+18]`, then merges the property block **`selected+40`** at `291C32C`. A null carrier or null `+288` skips this family; there is no native fallback. No extra positive-ID or source-pointer guard is present in this caller. This is a separate contribution from `+280/+630`.
3. **`291C334->28B6200`, then `291C363` ordered list properties.** The caller passes the same Character. Newly captured exact `.pdata` extent **`[28B6200,28B6279)` is 121 bytes**. On the common selection path, the getter reads `QWORD[Character+1C0]`. Nonnull returns **`carrier+200`**; null returns **the address of the static list header RVA `54E7270`**, from `LEA` at `28B623D`. This is an inline header address, not `QWORD[54E7270]` as a header pointer. The caller reads `header+0` as the source-pointer array and `header+C` as signed32 count, computes the end using sign-extension and stride8, and consumes every QWORD source pointer in native stored order. Each occurrence merges its own **`source+D8`** block at `291C363`, weight100000. Preserve duplicate occurrences; do not deduplicate or reorder. An observed zero count is a valid empty list. No current header was sampled in this research.

`28B6200` has a TLS/guard path before its carrier selection: signed comparison of `DWORD[5D679F0]` with TLS-derived `DWORD+10`, then calls at `28B6251->4223AA4`, condition `DWORD[5D679F0]==-1`, `28B6266->4223F44` with address `436B370`, and `28B6272->4223A44`. This resembles C++ static initialization bookkeeping; the helper semantics were not independently closed and that label is an inference. Every recorded path rejoins `28B6225`, where the Character carrier or static fallback header is selected. A readonly observer reads the actual selected current header; it does not invoke these helpers or manufacture an empty fallback from initial file bytes.

### Minimal observation and composition contract

Add an optional `post_291d7e0_sources` under the existing `current_person_state.current_context_source_inputs`, preserving the existing actor/full ID and source-frame provenance. `OBSERVER-CONSTRUCTION-PACKAGE.json` specifies physical field names and demand order. Reuse the existing paired PropertyContainer reader for `+630`, `+40` and `+D8`; no new MCP query or native function invocation is needed. New address bindings are the direct object fallback slot `5D1E308`, loaded signed32 threshold slot `5C6A19C` and the inline static ordered-list header `54E7270`. The global TLS initialization guard is source provenance, not an additional observer operand requirement.

Distinguish a readable native null/skipped family, a native zero/empty property container, and an unread demanded operand. Wrong magic stops before the signed threshold reads; low signed Character operand stops before the property read. Direct `+288` guards stop before its selected property; zero list count demands no occurrence. Read failure cannot establish known false or native zero. Both independent container arrays retain their actual counts and row order through the existing reader. A requested list count outside the existing reader's representable limits remains unavailable rather than becoming an empty list; the source count itself is still signed32.

Composition order is `291D1D0 -> pre-A1640 -> A -> B -> +630 guard -> +40 carrier -> ordered+D8 occurrences -> later291C371 suffix`. An assembler requires the exact source-stage starting context and all intervening contributions. **Observed current final storage cannot supply a pre-A/post-B baseline or receive these contributions a second time.** Current source bindings do not derive changed-stage list generation, held-title/qualifier/receiver inputs or future caches.

```mermaid
flowchart TD
  P["291D1D0 then pre-A1640 then A then B"] --> G["Character+1B0 / +280 / selected+8 or slot5D1E308"]
  G --> M["selected+38 equals 4744624F"]
  M -->|false| S["Character carrier+288"]
  M -->|true| T["signed16 Character+68 >= signed32 slot5C6A19C"]
  T -->|false| S
  T -->|true| C["291C2FE: selected+630 unit100000"]
  C --> S
  S -->|present carrier and +288| D["291C32C: qword288+18 then +40 unit100000"]
  S -->|native null| L["28B6200 Character+1C0"]
  D --> L
  L -->|nonnull| H["Header carrier+200"]
  L -->|null| F["Inline static header54E7270"]
  H --> O["Stored pointer0 / signed32countC"]
  F --> O
  O --> I["Each occurrence:291C363 source+D8 unit100000"]
  I --> N["Later caller suffix starting291C371"]
  L -.-> U["Changed-stage list generation/cache invalidation unknown"]
  N -.-> E["Complete person / actual Entry context association unknown"]
  classDef unknown stroke-dasharray: 5 5;
  class U,E unknown;
```

### Remaining precise construction gaps and receipt

The highest-value physical source-list binding at `28B6200` is now closed. List allocation/writes, source-object type/lifetime and invalidation for changed stages are not closed; the known physical follow-on is **writers of Character+1C0 and its inline+200 list**. Later caller contributions beginning **`291C371`** remain separate. Full-person scratch430/438 producers `2948DF0`/`2948F00`, postcopy `2949010`, changed-stage receiver/held-title/qualifier/census binding, and the actual Entry context `28BFC70->2C06B00` plus first-contact caller identity retain their previous gaps. No current-final baseline, forecast, complete person, Entry readiness, win rate or new live evidence is claimed.

New frozen-file I/O was exactly **121 code bytes plus four 12-byte `.pdata` rows = 169 bytes**, captured by bounded seek/read and retained in separate metadata/body attempts. `.pdata` body bounds were found before code was read. The read log records every new offset and byte count; prior cached `.pdata` rows were reused. Small cached caller windows were reused without new EXE bytes. No unwind body, initializer helper, list-write xref scan or whole EXE scan was captured. The separate research-plan consistency check records only file/record structure and is not a semantic test. The draft plan is explicitly offline-only and not suitable for live observation. Initial command-transport failures are preserved in `ATTEMPT-NOTES.json`; none read an incorrect source RVA or touched the game. Shared source/doc files and the runtime freeze were untouched.

## 后台整合后的prestage资格（2026-10-05T19:48:26+08:00）

Root集中离线验收已于2026-10-05完成，整合源码 `4733655173e65be99c9ffaafbe2d9275940df4d6`。`xar_ck3_bridge` 与五个新增focused native目标在Release、`/WX`、jobs4、低优先级下编译GREEN；五项CTest一次5/5 GREEN。外置 [构建与测试冻结](Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/OFFLINE-FREEZE.json) 保留原始attempt/测试/producer pins。两次真实RED分别为occurrence缺少快照比较与geography fixture缺少phase-character链接，已最小修复；旧attempt不覆盖。

本次是默认配置的离线bridge/fixture资格，G2 capability flags未从v73运行配置采用，宗教private query仍OFF；不是可直接部署的v74，也未进行runtime prepare/stage/attach。未来实机须采用实际所需flags并另冻候选。用户独占CK3期间game/SDK/attach/query/pipe/UI/Steam/profile操作均0；没有新paused artifact、live资格或游戏日。

`xar_ck3_12003_pre_291e210_1640_test` 已真实编译并一次GREEN；lane新增Python16例一次GREEN（1.86秒），原日志/回执 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/background-implementation/battle-entry/python-tests.json`。prestage及两个registry bindings的生产读取/序列化/消费现为static-ready；current final不替代该baseline、-1/false/0与missing仍独立保留。上文post-A/B贡献族是新source研究输入，尚未observer施工；完整人物初始化、changed-stage census与actualEntry上下文仍partial，不授首次接战或完整战斗forecast。


## Post-A/B current observer implementation, 2026-10-05 second background batch

The three source-closed post-B contribution families are now implemented as optional current_person_state.current_context_source_inputs.post_291d7e0_sources. Exact .3 bindings are 5D1E308 (actual object fallback pointer slot), 5C6A19C (loaded signed32 threshold), and 54E7270 (**inline** static ordered-list header). This extends the existing native DTO, readonly collector, serializer and authoritative Python normalization reached by the existing current-person/MCP path; no new query, command, initialization helper or source writer is invoked.

The three leaves retain independent availability and the same current Character/full ID. guarded630 preserves the current 1B0/280 pointer guards, actual object selection, signed32 wire bits of DWORD +38, signed16 Character +68, loaded signed32 threshold and exact admission. Wrong magic stops before the signed operands; the native signed less-than result stops before the property read. Readable null carrier/280 chooses the actual fallback and still evaluates it. A failed selected-object read is partial, rather than a native null guard or false admission.

carrier40 independently observes current Character +1B0 and carrier+288. Native null skips the family; two present guards establish admission before the selected object's +18 pointer/+40 property can be read. A failed demanded pointer/property preserves the known true admission but leaves the leaf partial. There is no fallback for this family.

ordered_d8 selects the current inline carrier1C0+200 header or actual inline static 54E7270. It reads header pointer0 before signed32 countC, matching the caller, and emits every stored source occurrence with its index, snapshot-local source identity and actual paired property block source+D8. Duplicate occurrences remain separate and preserve their order. The additional nullable source_array_present records the readable pointer0 result: a known empty list with a readable null pointer is distinct from an unread header. Zero count is a valid empty list; negative count is retained as signed32 and unavailable, without manufacturing zero/empty storage. The native static header is observed directly, never reconstructed from frozen initial bytes.

The three families reuse the existing PropertyContainer reader, including legal zero keys, unused value-field short circuit and independently observed value counts. The optional field remains absent for older/unbound producers. The strict Python normalizer retains these current values/statuses and validates the existing actor join. emit_post_291d7e0_requests_from_current_source_inputs_12003 emits unit-weight requests in order **guarded630 → carrier40 → every orderedD8 occurrence**; empty blocks and duplicates remain requests. The complete native stage order remains 291D1D0 → pre-A1640 → A → B → guarded630 → carrier40 → orderedD8 → later291C371. No prestage baseline, current-final append, future context, full person or Entry is computed.

The new Python validation ran once against this package: **16 passed in 1.68 seconds**, covering the production current-person authority ingress, signed16-to-signed32 comparison, inline fallback, stored occurrence order/duplicates, independent paired counts, legal empty blocks, missing demanded PC, closed wire types and older producer compatibility. Receipt/log: Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/post-ab-observer/python-tests.json and python-tests.log. open_kaishek is not applicable: native-memory DTO/JSON and guards are outside Paradox finite runtime semantics.

The new native build target and CTest name are xar_ck3_12003_post_291d7e0_sources_test. Its one CTest invocation writes eight production collector/serializer snapshots to post_291d7e0_sources_wire.json in CMAKE_BINARY_DIR. The fake-memory fixture covers exact RVA binding, actual nonempty inline static fallback, native stored duplicates and signed paired values, empty-key unused-field reads, wrong-magic and signed-JL short circuits, null pointer guards, unread demanded selected pointer and negative/unread list counts. The lane has not compiled or run it; the root integrator owns the central offline jobs4 build with the adopted capability flags.

Qualification at lane delivery: the new Python path is **static-ready**; native source and focused fixture are implemented with compile/execution pending. No live/paused qualification, first-contact/Entry/forecast credit or new game day. No CK3 process/pipe, attach/query, runtime prepare/stage, UI, Steam, profile/save/cache or frozen-EXE read occurred.

Remaining source work is unchanged: changed-stage generation/lifetime/writers of Character 1C0+200, later caller sources beginning 291C371, receiver/held-title/qualifier/census association, full-person auxiliaries 2948DF0/2948F00 and postcopy 2949010, and 28BFC70→2C06B00 effectiveness context/actual first-contact caller. The independently assigned later-suffix and scratch/census lanes own these follow-ons.


## Later current-person direct contributions, exact 1.20.0.3

2026-10-05 / W41. This background lane continues the cached caller at `291C371`. It closes two direct contribution families after `291F0A0` and captures that helper's exact source extent. The prior post-A/B observer and actual Entry-context lane remain separate. Source tree and field contract were persisted before implementing any observer.

Reuse the CK3 1.20.0.3 / Steam25652598 EXE pin `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`. The cached entire `291C0D0` caller was reused; no EXE scan or rehash was performed. Exact `.pdata` closure of `291F0A0` is `[291F0A0,291F25D)`, 445 code bytes; binary-search metadata demanded four new 12-byte rows, total new frozen-file I/O **493 bytes**. All seeks, bytes and small file pins are retained in `Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/person-later-suffix/`.

### Closed direct inputs and demand order

At `291C377`, `291F0A0` receives `model` and the same Character; its recipient becomes `model+10`. The caller then executes:

1. **Ordered `+80` property occurrences, `291C3FB`.** Read `QWORD[Character+1B0]`. Nonnull selects the inline header at `carrier+98`; null selects the **address** of static header RVA `545A3E8`, rather than its first QWORD as another header pointer. Read signed32 count `header+C`, then the native stored DWORD full-key vector at `header+0`. Zero count is a real empty family, without demanding either registry slot. For each occurrence, resolve low24 index through `QWORD[5D1FC58]`, unsigned capacity `+2C`, stride16 pointer at slot `+8`, and full DWORD object ID `+10`. A readable native null/miss/mismatched generation selects `QWORD[5D1FC48]`; an unread operand remains unavailable. Native signed32 `selected+24C==0` skips its property. Every other signed value, including negative values, admits `selected+80`, weight100000 into `model+10`. Retain duplicate requested keys and duplicate selected objects, in stored order. `R12D` is zero from `291C1A6` and remains zero at this comparison.
2. **Guarded `+AA0` property, `291C44C`.** Read `QWORD[Character+1C0]`. Nonnull selects `QWORD[carrier+388]`; null selects the actual `QWORD[5D1DCB0]` fallback. Demand DWORD `selected+38`; exactly `4744624F` admits `selected+AA0`, unit100000, into the same context. Wrong magic skips the property; unread carrier/selection/magic does not establish false. No extra positive-ID or selected-pointer null guard occurs in this native body.

The direct contribution order is after post-A/B ordered `+D8` occurrences, **then helper291F0A0, then ordered+80, then guarded+AA0, then helper291F550 and helper291F940**, followed by caller `291C467`. Observing these direct leaves does not close or omit the helper between the earlier post-A/B leaves and them. Their property containers use the existing paired keys/values observation, retaining independent count provenance and genuine empty blocks. Current final storage cannot be supplied as a before-helper baseline or receive these leaves twice.

### Source-closed helper body and concrete remaining operands

The complete 445-byte `291F0A0` body contains four ordered families, each writing via `2438850` to `model+10` at weight100000:

- `291F11C`: Character full key `+B4` resolves through storage `5D1E2F8` and native fallback `5C67670`, comparing selected full DWORD ID at **+8**. A readable null registry skips the Character key read. The selected object's pointer `+20` / signed32 count `+2C` vector consists of direct PropertyContainer pointers; preserve occurrences.
- `291F1C1`: manager slot `5D1F6D0` can initialize via `3F8B660` when null. `3181BF0(manager, Character)` selects a object; `3181370(selected, recipient)` supplies a property block, admitted when signed32 `block+C !=0`. Recipient is `QWORD[Character1C8+A0]` or `2BFB4C0`'s output when the Character carrier is null. These selection/cache helper leaves are not closed or called by this observer.
- `291F1FC`: `28BD090(Character)` returns a pointer header (`+0` / signed32 `+C`). Each stored source pointer demands signed32 `source+A24`; nonzero admits `source+A18` (the count is the property container's own `+C`). The getter's physical header selection remains a concrete follow-on.
- `291F23C`: exact AL from `2BABEC0(Character)` gates selected object's pointer `+938` / signed32 `+944` list of direct PropertyContainer pointers. False demands no list. The predicate leaf remains a concrete follow-on.

```mermaid
flowchart TD
  P["Post A/B orderedD8 occurrences"] --> H["291C377 → 291F0A0"]
  H --> H1["CharacterB4 / registry5D1E2F8 / fallback5C67670; selected20/2C direct PC list"]
  H1 -.-> H2["3181BF0→3181370 selected cached PC; missing leaf selection"]
  H2 -.-> H3["28BD090 header, sourceA24!=0 → sourceA18"]
  H3 -.-> H4["2BABEC0 AL gate → selected938/944 direct PC list"]
  H4 --> L["Character1B0 → inline98 or static header545A3E8"]
  L --> C["Signed32 countC / ordered full DWORD keys0"]
  C -->|each occurrence| R["Registry5D1FC58 fullID10 or actual fallback5D1FC48"]
  R --> A["Selected signed32 24C!=0"]
  A -->|true| PC["291C3FB selected80 unit100000"]
  A -->|false| N["Next occurrence"]
  PC --> N
  N -->|list end or zero| G["Character1C0: selected388 or fallback5D1DCB0"]
  G --> M["Selected DWORD38 ==4744624F"]
  M -->|true| Q["291C44C selectedAA0 unit100000"]
  M -->|false| S["291F550 then291F940"]
  Q --> S
  S -.-> E["Later caller291C467 and complete-person inputs unknown"]
  classDef unknown stroke-dasharray: 5 5;
  class H2,H3,H4,S,E unknown;
```

The new optional current source section is `later_direct_291c3fb_44c`; its independent readiness qualifies exactly the two direct families. Missing helper inputs, later caller/helper branches, scratch430/438, changed-stage list generation/receiver/title/qualifier/census and actual Entry association retain their concrete seams. The observer provides current read-only inputs, without native initializer/counter/writer calls, prepared-cache mutation, new MCP query, forecast or game-result credit. No launch, attach, game/SDK/pipe query, UI, Steam, save/cache/profile or runtime preparation occurred; `open_kaishek` is not applicable to native ABI memory/DTO arithmetic.

### Implemented direct observer and focused validation

The two caller-direct families are now implemented under that optional field in the existing query: exact .3 binding, production readonly collector/DTO/serializer, shared strict Python current-source normalizer and pure unit-request emitter. Newer producers retain source actor29829, native full DWORD generation bits, selected snapshot-local identity, signed nonzero admission, actual fallback choices, ordered duplicates and genuine empty PropertyContainers. Older producers omitting the new field still load. A negative native list count is retained as unavailable/unrepresentable, never invented as an empty list. Header pointer0 and countC are demanded even for zero count; registry slots and occurrence bodies are not demanded on zero. Both registry slots are loaded before the first key, and reread after admitted native merge sites; the readonly observer performs these reads without merging.

The focused Python suite ran once: **11/11 GREEN**, 2.33s, receipt/log `python-tests.json` and `python-tests.log` in this external directory. It covers duplicate order/block reference preservation, negative nonzero admission, zero and false skipped body, failed reads instead of native fallback, admitted unavailable properties, negative source count, source actor join/legacy producer, native word types and undemanded branch properties. Source changes are ready for root's centralized native build. Target and CTest **`xar_ck3_12003_person_later_direct_test`** use the production collector and serializer and output seven genuine case wires under `BUILD_DIR/ck3_12003_person_later_direct_wire`; this lane did not compile or run it. Qualification remains Python static-ready/native implemented pending build, no complete-person/Entry/live/forecast credit.

### Additional exact helper leaf closures for the next implementation

After the direct implementation and its test, bounded source follow-on closed two of the previously unclosed helper operands. This does not silently extend the tested direct observer.

- **`28BD090`**: complete .pdata extent `[28BD090,28BD12A)`,154B. A nonnull `QWORD[Character+1C8]` returns the **address** `carrier+88`. Null carrier returns the **address** of inline static header **`5D67E40`**, not a QWORD header pointer. TLS guard paths can initialize the static header but rejoin that exact address; a readonly observer samples its current bytes without initializer calls or assuming static file zeroes. Combined with `291F1FC`, every stored occurrence has source+A24 nonzero admission and source+A18 PropertyContainer, unit100000.
- **`2BABEC0`**: complete161B frameless leaf, captured176B gap through next function start2BABF70 with15B INT3 padding; surrounding .pdata rows prove no covering body. Read signed/raw DWORD `Character+15C`; exactlyFFFFFFFF returns AL0 and demands no registry/key. Otherwise, select first object using registry **`5D1E2F8`**, full key Character+B4, exact full DWORD selected ID **+8**, actual fallback **`5C67670`**. A readable null registry does not demand the key. Second registry **`5D1E300`** selects using first object full key **+4B8**, again exact ID+8, with actual fallback **`5D1E2E0`**. AL1 iff the first Character15C DWORD equals selected second object's DWORD **+A0**. Legal zero and negative raw words compare by exact bits. Unread demanded fields cannot establish native false. This gates the previously captured selected first object's938/944 direct-PC list at291F23C.

`3181370` also now has a captured176B frameless gap, exact leaf `[3181370,3181417)` plus9B padding. It reads selected+64 signed32 count. Zero branches to3182420's current inline default PC (address **5D70FC0**, known116B getter, lazy guard not called). Nonzero compares the recipient signed64 with two loaded native QWORD threshold slots **5C68E00/5C68DF8**, selects the first or last stride218 row at selected+58 at the extreme bounds, otherwise scans rows in stored order. It consumes row signed64 lower1E0/upper1E8 and the exact sign-dependent inequalities, returns first matching row's base PC, or QWORD[selected+70] fallback. These source branches are captured but no new observer is installed; demanded threshold values and selected object remain missing inputs in the old query.

`3181BF0` is split into multiple .pdata regions. The captured39B head validates Character magic43686172 at+1C and ID18!=-1; captured5B/276B continuation closes three chained full-ID+8 lookups (first5D1E2F8/fallback5C67670 CharacterB4, second5D1E300/fallback5D1E2E0 first4B8, third5D1DE88/fallback5D1DE00 second8C). It then takes QWORD[third+20] and scans manager+50/signed count5C definition pointers using `A11CC0(definition+40, &third20)`. The captured continuation stops at3181D30: return/default tail3181D30/3E/50 and A11CC0 membership remain precise unclosed seams. An absent Character1C8 recipient still invokes `2BFB4C0`; its known551B .pdata extent was recorded but its body was not captured. Do not call native getters or assume an identity from these partial paths.

All subsequent captures retain separate raw receipts; total lane I/O including these follow-ons is frozen in `ROOT-DELIVERY.json`, while the earlier493B figure accurately records the source input available before the direct implementation. The follow-ons are research, distinct from the tested direct observer.

```mermaid
flowchart TD
  H["291F0A0 first selected object /20 directPC occurrences"] --> M["3181BF0 Character magic/fullID then three registry selections"]
  M -.-> ML["A11CC0 manager definition-membership + return/default tail unclosed"]
  ML --> R["Recipient: Character1C8+A0"]
  R --> K["3181370 current selected64/58 stride218 + signed recipient intervals"]
  R -. "null carrier" .-> RF["2BFB4C0 recipient construction unclosed"]
  K --> C["Current selected PC; countC!=0 then291F1C1"]
  C --> L["28BD090: Character1C8+88 or inline5D67E40"]
  L --> O["Stored pointers0/signedcountC:sourceA24!=0 → sourceA18"]
  O --> P["2BABEC0: Character15C==-1 earlyfalse; otherwise fullID8 two registries → secondA0 equality"]
  P -->|ALfalse| END["Return to caller ordered80 and guardedAA0"]
  P -->|ALtrue| X["Selected first938/944 directPC occurrences"]
  X --> END
  classDef unknown stroke-dasharray: 5 5;
  class ML,RF unknown;
```

### Manager tail closure after the implementation handoff

The next narrow reads close the previously named3181D30/3E/50 tail, without changing the validated observer code. Matching manager+50 stored definition occurrence returns the QWORD definition itself at3181D30. Exhausting the list selects QWORD**manager+EF0** at3181D3E (not a inferred small-offset default). An invalid Character magic43686172 or fullID18==-1 selects QWORD of **slot5D1FBD8** at3181D50. These are three separate native selections; null or unread current selected pointers do not manufacture an empty PC.

The326B A11CC0 body consumes header pointer0 / signed32 countC, compares its QWORD entries with the QWORD supplied at `&third20`, and returns AL whether a matching stored pointer was found. Its visible baseline paths compare complete64-bit values: SSE scans twoQWORDs at a time, followed by a scalar tail; duplicates do not change the predicate. A native global guard has lazy feature initialization. When the loaded upper32 feature word is >=4EE8, it delegates the same begin/end/key search to `3F90910`; that optimized leaf is not independently reversed here. Accordingly baseline bit-equal membership is source closed, while the optimized helper's return equivalence remains source inference. No static initializer, membership predicate or native selector was called.

The smallest next current observer is therefore manager slot5D1F6D0, Character identity/magic, the three resolved fullID8 objects and their selected third+20 pointer, manager50/5C ordered definition pointers plus each definition+40 membership header, managerEF0 and invalid-Character fallback5D1FBD8. The3181370 selectedPC range inputs and actual recipient still follow. Absent Character1C8 recipient2BFB4C0 and optimized search3F90910 are the precise remaining source leaves; once those are closed the whole291F0A0 helper can be implemented in this same query. The direct observer does not wait on or claim those future inputs.

```mermaid
flowchart TD
  C["Character magic1C=43686172 and ID18!=-1"] -->|false| F["Actual slot5D1FBD8 selected definition"]
  C -->|true| A["Three fullID8 registry selections: B4 → first4B8 → second8C"]
  A --> K["QWORD third20; manager50/5C stored definition occurrences"]
  K --> S["A11CC0(definition40,key): baseline fullQWORD equality"]
  S -->|first match| D["Return stored definition occurrence"]
  S -->|exhausted| N["Return QWORD managerEF0"]
  S -. "feature upper32>=4EE8" .-> O["3F90910 optimized find equivalence unclosed"]
  D --> G["3181370 current selected range PC"]
  N --> G
  F --> G
  G -. "recipient absent1C8" .-> R["2BFB4C0 actual recipient construction unclosed"]
  classDef unknown stroke-dasharray: 5 5;
  class O,R unknown;
```


## Auxiliary person scratch preparation, exact 1.20.0.3

2026-10-05 background round 2. This source increment closes the auxiliary `scratch+430/+438` producers independently from the already implemented six-skill cache. Frozen CK3 1.20.0.3 / Steam25652598 EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6` is reused. Only the frozen file was read; no whole-file scan/hash, CK3/process/SDK/pipe/UI/Steam action or game-day advance occurred.

### Exact inputs and native order

Reuse the v77 `28C3D80` caller windows. `RBP=Character`, `R15=QWORD[Character+1B0]` scratch and `R14=the actual context returned by 28C3AE0`. The caller first finishes six skill results, then calls `2948DF0(scratch, output, context)` at `28C3EB0`; the returned signed Q64 is copied to `scratch+430` at `28C3EBD`. The `.pdata`-bounded leaf is `[2948DF0,2948EFB)`,267 bytes.

The `430` leaf reads weighted key `0x38` through source-closed `24389A0` in mode1 then mode2, preserving stored weighted-row order and signed fixed-Q products. It also performs a lower-bound aggregate lookup for key `0x3D` in context's embedded `+68` PropertyContainer; actual absent key is zero. Let `P` be mode1 sum, `N` mode2 sum, `A` the aggregate key3D value and `B` signed QWORD[scratch+2D8]. Its native result is:

`negative_tail=wrap64(N+A); negative_tail=negative_tail<0 ? negative_tail : 0; total=wrap64(P+wrap64(negative_tail+B)); result=total<0 ? 0 : signed_min(total,100000)`.

Every ADD wraps before its subsequent signed test. The base is added after the negative-tail choice; moving it inside that choice produces a different result. No division occurs in this leaf.

For `438`, the caller reads `Character+1A1` byte and sign-extended signed16 `Character+68`. When the byte is zero it loads low/high signed32 slots `5C6A15C/5C69D18`; otherwise `5C69D10/5C69D14`. The caller selects key `0x3A` when the signed16 value is below the low slot. Otherwise it selects `0x3B` when below the high slot, else `0x3C`. The high slot is not demanded on the first branch. These operands have no inferred business names. It calls `2948F00(scratch,output,context,selected_u16_key)` at `28C3F1C` and copies the result to `scratch+438` at `28C3F24`, then sets scratch byte440 to1. The exact leaf is `[2948F00,2949008)`,264 bytes.

The `438` leaf first obtains key39 mode2 (`N`), reads aggregate key3E (`A`), wraps their sum, then obtains key39 mode1 (`P`) and aggregate selected3A/B/C (`S`). Signed QWORD[scratch+2E8] is `B`. Its native result is `wrap64(wrap64(wrap64(min(wrap64(N+A),0)+B)+S)+P)`. There is **no final zero clamp, upper cap, rounding or division**. A negative result is legitimate.

The source-closed mode getter and aggregate lookup are reused from v77; no native getter invocation is needed to consume the materialized current context. Missing context/keys/values/weighted rows remain partial; legal zero values and native absent keys remain zero. The current stored context is a current input only, not a changed-stage materialized baseline.

### Copy and following nine-byte cache

Reuse v64 `28C3F60` writer: it copies `scratch438→scratch2F0` at `28C3FED/3FF4`, rereads Character1B0 and copies `scratch430→scratch2E0` at `28C4002/4009`, then calls `2949010(scratch)` at `28C4017`, and clears440. Prepared430/438 and copied2E0/2F0 are separate observations; neither implies the copy has happened.

New bounded source `[2949010,2949578)`,1384 bytes, establishes that the next helper is a separate nine-byte producer. It reads `QWORD[scratch+258]` as model, searches aggregate U16 keys at model78/count84 with signed Q64 values at modelE0, then optionally adds definition-selected keys. The optional family requires scratch278 object DWORD28=`41495374`, selects object20+238 or actual fallback QWORD[5D1F7B8], then requires DWORD38=`4744624F`; its nine U16 definition operands at312..322 are grouped in three triples and `FFFF` means skip. Sums preserve wrap64. Each result is truncated by native /100000, narrowed to signed low32, clamped to[-100,100], and stored as a signed byte through QWORD[scratch+310]. The embedded jump table at2949550 selects the nine initial property IDs; the tenth entry is outside the actual0..8 loop. This entire helper does not consume scratch430/438 and does not establish Entry refresh or a cache's business name.

```mermaid
flowchart TD
  Six["Six skill cache scratch410..424"] --> S430["2948DF0: key38 +/-; aggregate3D; scratch2D8"]
  S430 --> P430["Clamp signed wrap64 total to0..100000 → scratch430"]
  P430 --> Sel["Character1A1 + signed16Character68 + loadedlow/high"]
  Sel --> K["Select3A,3B or3C"]
  K --> S438["2948F00: key39 +/-; aggregate3E/selected; scratch2E8"]
  S438 --> P438["Signed wrap64 result → scratch438; ready440=1"]
  P438 --> Copy["F60:438→2F0 then430→2E0"]
  Copy --> Nine["2949010: model aggregate + guarded ninekeys → nine signedbytes"]
  Nine --> Done["F60 clears440"]
  S430 -.-> Changed["Changed-stage exactcontext materialization/census unresolved"]
  Done -.-> Entry["Fullperson→actualEntry caller/context association unresolved"]
  classDef unknown stroke-dasharray:5 5;
  class Changed,Entry unknown;
```

### Minimal same-query increment

The useful bounded implementation is optional `raw_numeric_inputs.auxiliary_scratch_inputs`, under the existing explicit-Character current-person query and its actor/frame. It emits scratch2D8/2E8, source selector operands, prepared430/438, copied2E0/2F0 and ready440. The existing actual-selected `raw_numeric_inputs.context` is reused. A pure adapter reproduces the two source-closed leaves from this materialized context; it never writes, prepares, flushes, rebuilds a current-final baseline or updates Entry. Native-null scratch is a named no-op and demands none of these fields. The high threshold is demanded only when the low comparison passes. Older producers without the optional leaf remain compatible.

This increment releases the actual auxiliary calculation interface. Fullperson and Entry remain partial: changed-stage receiver/title/qualifier/census inputs, earlier source-stage baselines and actual first-contact association are still required. The newly closed nine-byte helper can be implemented in a subsequent independent package with its exact table, selected definition and actual model-bound properties; no forecast is inferred here.

### Receipt boundary

Source receipt, bounded binaries/assembly, previous caller/getter reuse pins and implementation qualification are under `Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/person-scratch-census/`. New frozen-file reads are1915 code bytes plus180 `.pdata` bytes=2095 bytes. The three function bodies and previously cached source were interpreted once. No unwind body, full-image xref scan, initializer or unneeded caller was followed. `open_kaishek` is not applicable to this ABI/DTO/native integer-arithmetic work; no Paradox script semantics are changed.

### Offline implementation qualification

Isolated source commit `73e8f3f1` implements this optional raw leaf, four exact loaded threshold bindings, current prepared/copied observations, strict optional normalizer and `compute_auxiliary_scratch_from_native_inputs_12003`. No new MCP or native getter invocation was added. One new production-normalizer→kernel Python case was run once: **1 passed in1.52s**; it covers low/middle/high signed selector boundaries, legal negative438, wrap64-before-clamp, empty/missing properties, legacy absent/explicit-null leaves and native-null scratch. Receipt/log: `PYTHON-VALIDATION.json/.log` in this packet. Python qualification is **static-ready**. Native target/CTest `xar_ck3_12003_person_auxiliary_scratch_test` has six production-reader/serializer fixture samples and is implemented but **not yet built or run by this lane**; Root owns the combined offline build. It emits `${CMAKE_BINARY_DIR}/person_auxiliary_scratch_12003.json` for one genuine wire-consumption follow-up. No new fixture-live or production-live qualification is claimed.


## Post-A/B genuine native fixture wire integration, 2026-10-05

After the root central offline /WX DLL/new-target build and one 5/5 GREEN CTest run, the eight genuine post_291d7e0_sources_wire.json snapshots were consumed once by the adopted production normalizer and post-B unit-request emitter from Z:/gb0, source 96e4c6a688d95dc326db4cd3b7cd25961e3c40c6. All eight cases passed. Exact request counts were [5,1,1,3,0,null,null,null]; the three partial demanded-source cases retained independent current facts and rejected complete post-B request emission.

This integration preserved guarded630→carrier40→stored orderedD8 order, duplicates, FFFF/zero and negative Q values, independent value counts, native wrong-magic/signed-JL short circuits, actual admitted fallback with a nonempty inline static list, and negative/unread list count distinctions. The adopted production module's optional later_direct extension remained compatible. Wire SHA-256: 6f0c05a9c5dd4f7783b0653f15af15aad387950e31520a76dc2d94fe8e6bf656.

Receipt: Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/post-ab-observer/native-wire-integration/WIRE-INTEGRATION-RECEIPT.json. Normalized actual native snapshots and unit requests are retained in NORMALIZED-AND-REQUESTS.json in the same directory. The root native build/CTest receipts are native-person-holy-01.json and native-person-holy-ctest-01.json in its round2 output. The old sixteen Python cases were not rerun; no source/native input changed during this integration.

The new post-A/B observer/consumer is now static-ready using the compiled production reader, serializer and adopted Python ingress. This is synthetic native-memory fixture evidence, not fixture-live or production-live. No paused artifact, full-person/Entry/forecast claim or game day was added. Game/process/pipe/runtime/desktop access remained zero.


### Root 整合 native/consumer 资格

实际验收收口时间：2026-10-05T21:12:06+08:00。整合 source `96e4c6a688d95dc326db4cd3b7cd25961e3c40c6` 在 adopted v73 capability flags 下 MSVC `/WX`、jobs4 below-normal 纯离线 bridge + 5新增targets构建 GREEN（152.98 秒、362增量步骤），`native-person-holy-01.json/.log` 保留。只运行5个新增 CTests，一次 **5/5 GREEN**（总0.73 秒）：post-A/B、knight effectiveness context、later direct、auxiliary scratch、holy-order current-war eligibility。旧C/D及旧Python cases未重跑。

真实生产reader/serializer输出随后各消费一次，合计28份：post-A/B8（ordered requests `[5,1,1,3,0,null,null,null]`）；knight4（缺诊断仍保留真实scalar/stats）；later-direct7（duplicates、fullgeneration fallback、negative count/missing/false分开）；auxiliary scratch6（真实准备/复制结果分列、native-noop、missing threshold）；holy-order3通过注册MCP consumer 48checks。无synthetic replacement，生产normalizer/module从Z:/gb0导入；十三份later/scratch在 `later-scratch-genuine-wire-integration.json`，其他各lane native-wire-integration/VALIDATION-RECEIPT保留wire、consumer与projection pins。新native+consumer资格均为 **static-ready**，不是live，也没有完整人物、changed-stage、Entry预测或release action信用。

qualified DLL已归档 `source96e4c6a6-person-holy-qualified-binaries/xar_ck3_bridge.dll`：9,691,648 bytes，SHA `ce030baa45956ffac50b43e3b1337b6b06c8407e9a38fe2ab110382d0c51ca41`，同档案保留5fixture EXE、实际JSON、CMakeCache与编译result。未注入或deploy。上一已推送loss milestone `02d187b2cf7df41393affe840992d26f2b715691` 官方CI `37313580089` SUCCESS；对应[CI日志](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37313580089)不能外推新commit已过CI。

下一后台工作仍在做：已交付九cachebyte child源待Root采用/独立native验证；291F0A0 helper四族观测、2633340 conditional raised refresh及retained selected Rules真实effect值正在 source-first施工。这些都针对当前功能输入缺口，不派生理论安全审计，不用无paused状态当停止理由。新CK3启动/连接/SDK/真实pipe、UI/Steam、profile/save/cache/runtimeprepare/stage/deploy与游戏日全部0；历史5035保存日与R0046停点不变。日/周保持rolling，不倒填早会，不把幕后源码测试记成production-live。


## Following nine-byte person cache, exact 1.20.0.3

2026-10-05 background round 2 continuation. Reuse the newly closed `2949010` body and table from `person-scratch-census`, frozen CK3 1.20.0.3 / Steam25652598 EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`. No new EXE bytes, full-file hash/scan, game/process/SDK/pipe/UI/Steam operation or native initialization is required.

### Current receiver, lists, demand and exact arithmetic

`28C4017` passes the current `QWORD[Character+1B0]` scratch to `2949010`. Unlike the earlier `28C3AE0` selection, this helper unconditionally selects `QWORD[scratch+258]` as its model; there is **no `model+8==Character` ownership branch or fallback-context selection** in this body. Its actual aggregate PropertyContainer is embedded at **model+78**: U16 key data+0, signed32 count+C (model84), signed Q64 value pointer+68 (modelE0). Reusing an earlier fallback-selected `raw_numeric_inputs.context` would therefore use the wrong model on an ownership mismatch. The minimal readonly observer copies this actual aggregate separately.

The actual loop has nine occurrences, in jump-table order at `2949550`: **[22A,228,22B,229,225,22D,22C,226,227]**. The tenth table branch is not consumed by this0..8 loop. Every base occurrence uses source lower-bound lookup; a legitimate native absent key contributes0. Actual count/keys/values are preserved, without reordering or synthesizing values.

The optional contribution family first reads `QWORD[scratch+278]` and its DWORD+28. Only magic **41495374** demands QWORD+20. If that pointer is nonnull, select QWORD[linked+238]; otherwise select the actual native **QWORD[5D1F7B8]** fallback. Demand DWORD[selected+38]; only magic **4744624F** admits definition keys. The caller's source has no null guard for scratch278 or the selected definition. An observer seeing a native null there reports an unavailable demanded operand; it does not manufacture a false family. Wrong first/second magic is a source-closed skipped family and demands no later fields.

An admitted family reads exactly nine U16 definition keys at **312,314,316,318,31A,31C,31E,320,322**, in three triples. Each corresponding cache position wrap64-adds the aggregate lookup for its own key. **FFFF skips** that contribution. Duplicates remain positional, and a selected key equal to its position's base key contributes that value again. No positivity rule is added.

Each final signed Q64 sum is truncated toward0 by **/100000**. The result is narrowed to **signed low32** before comparing against the actual instruction constants **-100 and100**; this is not a direct signed64 clamp. The clamped signed point is stored as its signed byte to `QWORD[scratch+310]+index`. Current cache bytes copied by an observer remain separate from these calculated results; stale or unprepared bytes are not treated as calculation evidence.

```mermaid
flowchart TD
  C["Current requested Character1B0 scratch"] -->|native null| N["F60 no-op; no model/cache operands demanded"]
  C -->|present| M["scratch258 actual model, no owner/fallback branch"]
  M --> A["Actual aggregate model78/count84/valuesE0"]
  A --> B["Nine base keys in native jump-table order"]
  B --> G["scratch278 DWORD28 ==41495374"]
  G -->|false| D["No definition-key additions"]
  G -->|true| L["linked20+238 or actual slot5D1F7B8"]
  L --> H["Selected definition DWORD38 ==4744624F"]
  H -->|false| D
  H -->|true| K["Nine positional U16 keys312..322; FFFF skip"]
  K --> W["Wrap64-add each aggregate value"]
  D --> Q["Each sum /100000 toward0 then signedlow32"]
  W --> Q
  Q --> P["Clamp to actual[-100,100] constants"]
  P --> S["Native destination scratch310 signedbyte[9]"]
  S -.-> F["Complete person / changed-stage source baselines remain unresolved"]
  F -.-> E["Actual Entry caller/context association remains unresolved"]
  classDef unknown stroke-dasharray:5 5;
  class F,E unknown;
```

### Same-query and calculation boundary

Add optional `raw_numeric_inputs.nine_cache_byte_inputs` to the existing explicitly requested current-person query. Reuse its actor/frame and emit the actual model aggregate, source gate operands and selected keys, and actual current nine signed bytes from scratch310. A null scratch is the existing F60 no-op; a missing demanded model/definition operand is partial. No native getters or helper2949010 run. Add a pure `compute_nine_cache_bytes_from_native_inputs_12003` adapter consuming these source operands; preserve distinct calculated sums, low32 points and clamped results. It does not write the cache or claim complete person, Entry, future forecast or callback execution.

Source body/table pins and Mermaid are published before code in this appendix. `open_kaishek` is not applicable to this native ABI/DTO/integer-arithmetic package. Root owns canonical append, daily/weekly records, central build, eventual runtime adoption and master push.

### Offline implementation qualification

Isolated child commit `2306c381` implements this same-query optional raw leaf, exact fallback binding, independent actual model aggregate, strict optional normalizer and `compute_nine_cache_bytes_from_native_inputs_12003`. Observation `ready` concerns formula source inputs; a missing current cache pointer remains separately observed and does not manufacture cache bytes or block calculation of otherwise known inputs. One new production-normalizer→kernel Python case ran once: **1 passed in1.10s**. It checks exact base order, both false native guard families, fallback selection, positional duplicates/FFFF, wrap64-before-division, signedlow32-before-clamp, missing demanded operands, legal empty containers, native-null scratch and old absent/explicit-null producer compatibility. Receipt/log: `PYTHON-VALIDATION.json/.log` in `person-nine-cache-byte`.

Native target/CTest `xar_ck3_12003_person_nine_cache_bytes_test` is implemented with eight production query/serializer samples and is **not yet compiled or run by this lane**. Its output is `${CMAKE_BINARY_DIR}/person_nine_cache_bytes_12003.json`; `replay_compiled_wire.py` consumes those genuine fixture bytes through the integrated normalizer and kernel, optionally also consuming the previous six auxiliary-scratch samples. Root owns the one central offline build. This is Python **static-ready**, native fixture execution pending, with no new live/game/Entry credit.


## Nine-byte cache offline native qualification, 2026-10-05

Root adopted child `2306c3813a6f31f61f3fab3d7f27ac29462ea8b1` as `da9aa3fa`. The new standalone target `xar_ck3_12003_person_nine_cache_bytes_test` compiled once with `/WX`: **GREEN9.66s**, integrated source `f16c12b7e50fb50da899655ef295993ecbe55cf5`. Its new CTest alone passed **1/1 GREEN0.13s**. These build/test facts are supplied by the Root integrator. This result does **not** qualify a newly linked complete bridge DLL; Root's combined DLL build remains a separate operation.

Its actual production-reader/serializer output is `Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/native-build/person_nine_cache_bytes_12003.json`,10572B,SHA256 `2033c0fd780383e1cfcdc086097388021d5f8dc9118a8887b68af3217ce5fe50`. On2026-10-05T21:20+08:00, the external replay script imported the integrated production normalizer and kernel from `Z:/gb0/ck3_autonomous_player/src` and consumed these **eight new samples once:30checks GREEN**, eight outcomes`computed,computed,computed,computed,partial,computed,partial,native_noop`. The earlier six auxiliary-scratch samples were not read or rerun. Replay receipt `compiled-wire-01/RESULT.json` is2983B,SHA256 `7691730f786587e50fb05531d60e5a921808ba478f3870f4252676e251035f50`.

The genuine fixture wire preserved the helper's actual model aggregate despite the earlier AE0 owner mismatch/fallback context, both source guard skips, positional keys/FFFF and fallback selection, current-cache absence independently from usable source inputs, partial demanded null carrier/model and the native null-scratch no-op. No fabricated replacement wire was used. These are offline fake-memory production-reader observations and mathematical consumption; helper2949010 itself was not executed and this is **static-ready**, not fixture-live or production-live. Game/process/SDK/pipe/attach/UI/Steam/save/cache activity, old-test reruns and new game days remain0.

The next concrete background construction entrances remain available. First, bind a **changed-stage selected Character/model** to the known `291C0D0` receiver `QWORD[model+8]` and the `291C204→291D1D0` group producer. The next source input adapter must specify the actual stage-starting context, receiver full ID, held-title/qualifier operands and seven group occurrences for that stage, rather than reusing the observed current-final aggregate. The existing native caller windows and `context_branch_inputs` reader provide the physical starting seam; source-close the changed-stage census producer before implementing its adapter.

For complete Entry, the independent source ledger now closes the occupied-knight wrapper and immediate `264E099→2657AC0` stat writer, but still names **general Entry `24E0EB0`'s Province and outer encounter admission** as the next specific source entrance. A background work package can reuse that caller/cache, capture only the demanded exact-build blocks, publish the native tree, then add the corresponding readonly/pure entry-source interface. Neither the nine bytes nor current six-stat/auxiliary results establish that admission or a changed-stage baseline. This delivery closes the new primitive; it does not claim background work is exhausted.


# Helper291F0A0 background delivery, 2026-10-05

The native tree in HELPER-SOURCE-TREE.md was written before observer/consumer construction. This delivery follows child2d567cd7 and retains the earlier direct80/guardedAA0 implementation977de946. Parent owns canonical topic and daily/weekly merge.

The missing current-person input is now an optional same-query helper_291f0a0 observer, using the existing PropertyContainer representation. It captures the native order primary_direct -> manager_range -> source_a18 -> conditional_direct, including stored duplicate occurrences, signed generation bits, current selector keys, exact predicate demands and actual signed recipient/range operands. All merge requests use model+10 / unit100000. Each available family can be emitted independently; the combined helper requires all four available. No observed final context is substituted for a missing stage baseline.

Manager source selection is source-closed for present Character1C8: current manager5D1F6D0, three fullID+8 registries or invalid-character slot5D1FBD8, first matching completeQWORD key definition or managerEF0, current signed1C8+A0 recipient and3181370 range/default choice. Scalar A11CC0 and captured frameless AVX2 3F90910 agree on completeQWORD membership and first-match semantics. Zero native key-count skips only manager admission. Direct pointer-list families retain real zero lists and original occurrence order.

The observer records actual lazy manager null, static pointer-list initializer guard5D67E38 and default PC guard5D70FBC/current stored zero count. Guards0/-1 remain partial with explicit reason. It never calls an initializer or a native helper. Character15C==-1 returns native false without demanding first938 or the later comparison operands.

Absent Character1C8 recipient still needs2BFAC30 contribution producer/current inputs inside source-closed551B2BFB4C0. The latter uses CharacterB4/28BD090/CharacterF8, effective modifier25D and actual collected map values before signed clamp. The explicit absent-recipient partial does not remove the other three useful families. Parent requested delivery of these source-closed paths now;291F550 and291F940 caller suffixes remain separate next source seams.

One new focused Python validation passed11 tests in1.07s. Receipt helper-python-tests.json/log pins the exact command, dirty source base2d567cd7 and log SHAed86b1a5659f51935e66925b55f2563997e527faa7d6e91064aa48bf2b1c985d. No old test reruns. open_kaishek is not applicable: native memory ABI/JSON and pure contribution emission, no Paradox script semantics.

The production collector, DTO/JSON, strict Python normalizer and pure ordered family/full emitters are implemented. New native target/CTest xar_ck3_12003_person_helper_291f0a0_test is ready for Root's central jobs4 build; seven wire cases cover all families/default, positive signed-range boundary, absent recipient with independent families, actual lazy manager, actual lazy default PC, early false predicate and first matching manager definition. Wire output is BUILD_DIR/ck3_12003_person_helper_291f0a0_wire. Native compilation/fixture execution is pending at this receipt; this lane did not compile.

Exact-build identity is reused: CK3 1.20.0.3 / Steam25652598 / EXE94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6. This follow-on reads775 new frozen EXE bytes:551B2BFB4C0 body,96B narrow .pdata rows and128B bounded3F90910 gap (115B body/13B padding). Lane cumulative new frozen EXE bytes3109. No whole EXE scan or rehash.

Readiness: Python static-ready; native implemented pending central build/fixture. Present1C8 can expose all four helper families when actual current dependencies are available. This is useful source observation; complete current-person stage, Entry/forecast, deployment and production-live readiness remain unclaimed. No game/SDK/pipe/UI/Steam/runtime/profile/save/cache activity, no game days advanced. Production baseline remains R0046/h9052/raw53265168/campaign5035/36524.


# Helper291F0A0 native/production-consumer qualification, 2026-10-05

Parent integrated childd30e01eb as12574a6b. The source tree and original construction receipt remain in HELPER-SOURCE-TREE.md / HELPER-DELIVERY.json; this additive receipt records later validation without rewriting their earlier pending status.

Root reports native-helper-rules-01 source52391be52ac520e077eb3131f9bb9e638651a978 GREEN156.12s under /WX, full bridge DLL including helper/current-state Rules, and the two new CTests2/2 GREEN .34s total (helper .11s). This lane did not compile or rerun prior tests.

After that GREEN message, consume_helper_native_wires.py consumed the actual seven outputs from Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/native-build/ck3_12003_person_helper_291f0a0_wire with the production normalizer and individual/full emitters loaded from Z:/gb0/ck3_autonomous_player/src. One attempt:7/7 GREEN in0.043s. Source module pins and unchanged exact raw wire copies are in helper-native-wire-integration/RECEIPT.json, SHAdea5b78aeeded9c49ab5e7662d3f5fa2fbdf3e4cfd9ccfe4ef995441a13e3873.

The wire/consumer boundary preserves all four-family order, stored duplicates, native row index, selected source identity, unit100000 weight and actual normalized PropertyContainer block references. Positive signedrange boundary selects the second PC with202. The absent-recipient, null-manager and uninitialized-default cases retain native partial reasons, independently emit their available families and reject full or unavailable-family requests. Early ALfalse emits no conditional rows. First completeQWORD manager-key match survives normalization.

This is static-ready offline fake-memory producer-to-production-DTO/emitter evidence. It does not establish paused/live observation or a complete person/Entry/forecast stage. No game days advanced; baseline remains R0046/h9052/raw53265168/campaign5035/36524. No CK3 launch/attach/query/SDK/pipe/UI/Steam/process/runtime/profile/save/cache operations.

Exact next source work remains absent1C8 recipient2BFB4C0 ->2BFAC30 current contribution inputs, then independent current-person caller291F550/291F940. These gaps do not erase the useful present1C8 four-family or independent three-family observer.


## Current raw title census and model-owner association, 2026-10-05

The exact source receiver/title/qualifier census now has a current read-only
implementation. Source tree and physical input plan were sealed before code in
`Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/person-changed-stage-census/`:
`SOURCE-TREE.md`, `SOURCE-RECEIPT.json`, `QUERY-PLAN.json`. Reused exact .3 sources
are291C0D0,291D1D0,28C2E10,28AC6B0 and the bounded28C3BC0 admission prefix.
New EXE/code/pdata/unwind reads are all0; no source bodies are copied.

Existing exact.3 `title_holder12003_abi.json` closes the prior unnamed record type
as Title: registry5D1DAF8/fallback5D1DAE0, FullID10, template48/tier64. The census
uses receiver Character1C0 landedData1E0, or actual static5439C88; it does not
substitute DeathData's held-title list. Highest held tier28AC6B0 separately prefers
landed1D4 unless7, then first held FullID/template tier, and only uses death68/74
when landed data is absent. Its source and government getter's different
precedence are documented; this package reuses both existing getter bindings.

The same current-person query optionally adds
`current_person_state.context_branch_inputs.census_inputs`. It publishes current
scratch/model presence, actual model8 owner's raw Character FullID and pointer
match, and local28C3BC0 model2F0 magic only after an owner match. It retains the
queried actor and never replaces that Character with the model owner. This
association is separate from the AE0 numeric-context fallback and current final
stored context. The census remains independently useful even when model is absent
or associated with another actual Character; those facts stay explicit.

Raw Title occurrences retain DWORD FullIDs in native order, duplicates, resolution
matched/fallback/unavailable and the actual resolved record FullID (including a
different fallback ID). Demand order is Title1D8 byte, then130 byte, then12C
signed32, fresh government bit14 on the same receiver Character, then signed32
template tier. Skipped fields are null. The implementation captures those values
inside the existing single traversal and government calls, preserving old counts,
property blocks, readiness and selected contribution. Raw census readiness is
independent of the older property contribution family's readiness. An observed
tier outside0..6 remains raw/source-ready while the seven-counter projection
stays partial. No category is clamped or discarded.

The strict optional-family normalizer retains native widths, occurrence positions,
actor join and demanded-source readiness, and accepts older producers with an
absent/null family. `compute_seven_group_census_from_native_inputs_12003` counts
the raw occurrences with source wrap32 math, independently of the old summary
fields. It returns row admission and model-association facts; missing required
row operands retain null seven-count output. No native writer or getter is called
by the pure kernel.

The one new production normalizer-to-kernel Python case is **1/1 GREEN**, 1.61s
(outer2.1966s), with receipt/log `PYTHON-VALIDATION.json/.log`. It covers ordered
duplicates/zero FullID, fallback identity, short circuit and fresh government
selection, absent/mismatched/wrong-magic model, static empty census, missing rows,
raw outside tier, native widths, actor join and old producer compatibility.
Existing auxiliary/nine-byte tests were not repeated. New native target/CTest
`xar_ck3_12003_person_title_census_test` uses the production query and serializer,
with10 fake-memory samples output at`BUILD_DIR/person_title_census_12003.json`.
This lane did not compile/run it; Root qualifies that necessary target centrally.

Readiness is Python **static-ready**, native implemented/pending build. It exposes
actual current raw source values and independently computes the current census.
It does not supply an actual changed-stage frame, explicit stage-start baseline,
current-final-as-prior assembly, complete person/Entry, forecast or live evidence.
The next specific changed-stage construction seam is the actual stage's
Character1C0 held-title1E0 membership and Title1D8/130/12C operands, tied to its
actual model8 receiver; current query and pure census now provide that physical
input interface. Source-stage context baseline and intervening contributions
remain separate. All game/SDK/pipe/UI/Steam/runtime/profile/save/cache operations
and advanced game days are0; remaining background work is not exhausted.

```mermaid
flowchart TD
  Q["Current queried Character"] --> S["Character1B0 -> scratch258 actual model"]
  S --> O["model8 receiver pointer/full ID; model2F0 magic; pointer match"]
  O --> A["28C3BC0 matched-model admission operands"]
  A --> C["291C0D0: model8 Character, context ADDRESS model10"]
  C --> H["291C204 ->291D1D0: landed1E0 / static5439C88 FullID occurrences"]
  H --> R["Title registry5D1DAF8 / actual fallback5D1DAE0"]
  R --> F["Title1D8 ->130 ->12C; exact short circuit"]
  F --> G["Fresh government bit14 on receiver Character per eligible occurrence"]
  G --> T["Title48 template64 signed tier"]
  T --> N["Seven wrap32 counters; positive group0..6 source blocks"]
  Q --> I["Current raw census, association and demand chain observer"]
  I --> P["Pure current census recomputation; preserves order and fallback"]
  N --> P
  P -. "actual changed-stage input capture still required" .-> U["Changed-stage receiver/title/qualifier adapter"]
  U -. "explicit stage-starting context absent" .-> B["Stage context assembly unknown"]
  B -. "general Entry24E0EB0 Province / encounter admission" .-> E["Complete first-contact Entry unknown"]
  classDef unknown stroke-dasharray:6 4,fill:#fff4e5,stroke:#b36b00;
  class U,B,E unknown;
```

### 当前七组 Title census 原生与消费者验收完成

实际收口时间：2026-10-05T22:06:41+08:00。Source-first当前raw Title census/model-owner关联源e46db613→Rootd2d2d341已接入既有只读查询；完整bridge和newtarget离线 `/WX`、jobs4 below-normal build GREEN148.40秒（native-census-02）。新夹具fix65415a63→Root12a9caf2仅改fake-memory test：query稳定性连续双采样，每帧Provider重置government序列，累计两次Provider/正常10次government；scratch扩到290补query已有custody288读取。生产代码与旧Python用例不改不重跑，整DLL无需因test-only变化重编。新target单独重建GREEN5.89秒；新CTest一次修复后1/1 GREEN0.07秒（总0.11）。

真实生产reader/serializer新JSON22497B，SHA25b7d129abbf535873f88ac935ee1cbf7c5a09c1d4af71982d54bc6951dfd13f；十份输出只消费一次，Z:/gb0 authoritative normalizer→pure seven-group kernel 45checks GREEN。compiled-wire-02/RESULT.json14563B，SHAd6174b5efc5544706f09979a072c24bb77e2fdd1e8a411abee491920244b3fc6。旧aux/nine/其他已通过样本0重跑。Raw census独立ready，outside-tier原值留存但七计数partial；头衔重复/顺序/fallback、实际actor/model-owner关联与短路source读取保留，不拿旧汇总或当前final代阶段baseline。

首次native-census-01因Root错误DLL target名无compile执行；native-census-ctest-01因夹具未模拟第二帧throw穿过noexcept而RED0xc0000409，输出0bytes。Root随后consumer也在byte0 JSONDecodeError，实际消费0份。原失败与empty wire均保留person-changed-stage-census/native-attempt-01-red/RESULT.json和owner ROOT-FIXTURE-FIX-DELIVERY.json；最小fixture修复后才首次实际消费十份GREEN，不能改写失败。新增路径共11项不同native CTests已通过、60份新真实fixture输出已消费通过，资格为static-ready，非game fixture-live。

整DLL归档source12a9caf2-census-qualified-binaries/xar_ck3_bridge.dll：9748992bytes，SHAce472bc34028dc675d9f5c47cf10f6ff65f082387bd93e0be8ebde115277f44a；编译production source为d2d2d341，fixture source为12a9caf2。同档案保留newEXE/wire/cache/result/consumer pins及source差异只有此test的证据，未stage/deploy/inject。前一已推送fc628dca官方CI37319699503 SUCCESS，归档tag archive/g2-background-20261005-round2-pre-rebase保全原编译源；新publication的实际SHA/CI另记，不借上一CI结果。

三条后台依赖继续source-first推进：291F550/291F940人物剩余helper，291C0D0 model10真实reset/显式起始状态，以及月度初始供给/围城/劫掠预算。阶段baseline、实际changed-stage receiver/operands、完整人物/Entry/fullmonthly/forecast仍未完成；无新paused/live或战争loop信用。CK3启动/连接/SDK/realpipe/UI/Steam/profile/save/cache/runtimeprepare/stage/deploy与新增游戏日0；历史5035/36524、G2 5/8、NW2 2/4、natural0保持。日/周rolling，后台工作未耗尽。



## Source closure for the remaining two helpers before observation

Adoption time: 2026-10-05T22:12:41+08:00. The source tree and QUERY-PLAN.json were sealed before production implementation. Both helpers are source-closed research; the same-query optional observer is now being implemented. There is no native/consumer qualification yet for these new fields.

2026-10-05 / ISO2026-W41. Research-only source closure before any observer/counter-policy construction. Parent owns canonical topic/report integration. Exact CK3 1.20.0.3 / Steam25652598 / frozen EXE94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6, image base140000000; existing freeze identity reused, no whole scan or rehash.

## Caller association and phase order

Cached291C0D0 sets R13=model, R14=QWORD[model+8]=Character, RSI=model+10. After291F0A0, caller ordered80 and guardedAA0, it calls291F550 at291C457, then291F940 at291C462. Both append to this same model+10 receiver. They are further current-person construction stages; these bodies do not create an Entry, establish a before-stage baseline, or imply a complete forecast. The later caller continues at291C467 into additional158/2922070/2922530/conference/291F260 branches: they remain separate, not covered by these two helpers.

Native .pdata splits291F550 into seven contiguous segments covering[291F550,291F940),1008B, and291F940 into three covering[291F940,291FB09),457B. All normal paths and their local initializer branches were captured; these are one logical function each. Parent/source evidence must not mistake the first short segment for a complete helper.

## 291F550: guarded three families, unit100000

First load actual Culture storage slot5D1E2F0. Nonnull storage demands full DWORD Character+B0, low24 capacity+2C/table+20/stride16 pointer+8, exact selected ID+10; native null/miss selects QWORDslot5D1E2E8. Null storage does not demand Character+B0. Selected DWORD+14 must equal43756C74 (Cult), then selected fullID+10 must not equalFFFFFFFF. Wrong magic or minusone skips the entire helper, before government or family reads. No extra positive-ID guard exists.

1. Government-indexed property at291F62C. Physical government getter28C2E10 is reused from the cached237B .3 body. It loads Character storage5C67568/fallback5C67570 once; validates current Character magic+1C=43686172 and fullID+18!=-1; prefers deathData1D0+88, then current1C0+3F8. If neither component exists, it follows full Character key1B8+C8 (orFFFFFFFF if1B8 null) through the same storage, fullID+18, and loops on that selected Character. Invalid Character, or a null selected government after diagnostic branch, returns actual QWORDgovernment fallback5D1E2A8. No observer call or diagnostic is needed.
   Government magic+38=4744624F selects signed32 governmentID+10; native PC pointer is QWORD[Culture+670]+sext32(governmentID)*1C0. There is no native length or nonnegative check in this helper. Wrong government magic uses inline current fallback PC5D65890. Guard5D6588C is the native lazy initializer marker; native initializers rejoin at291F620. Read actual current guard/PC and retain0/-1 partial without initializing. Both selections contribute directly (including initialized empty PC), weight100000, receiver=model+10.
2. Ordered direct property pointers at291F65C. Culture QWORD+90 / signedcount+9C describes stored stride8 pointers. Every occurrence is the PropertyContainer itself, without additional offset/gate; duplicates and order remain. Zero count is actual empty; no unused row reads.
3. Conditional mapped PC occurrences at291F829. Resolve selected first Rite via Character+B4 storage5D1E2F8/fullID+8 or fallback5C67670; second object via first+4B8 storage5D1E300/fullID+8 or fallback5D1E2E0; then selected Rite via second+98 and the first Rite storage/fullID+8, defaulting to the original Rite fallback5C67670 (rather than a failed previously resolved Rite).
   Culture QWORD+230 / signedcount+23C stores descriptor pointers. For each occurrence, key is QWORD[descriptor+20]. Admit exactly if selected Rite's QWORD+7A0 / signedcount+7AC contains this entire QWORD. Reused A11F60 baseline and already-captured3F90910 AVX2 compare complete64-bit entries and return first equal/end; no native finder call is necessary.
   For admitted rows native reads shared inline PC fallback5DC2380/guard5DC2370 initialization state before mapping. Key object magic+38=4744624F permits a scan of the *whole same Culture230 list*, choosing its first descriptor whose key object's fullID+10 equals admitted key object's fullID+10; selected PC is QWORD[first-matching-descriptor+28], including actual null. Wrong magic, or an actual null descriptor fetched from the chosen slot, takes inline fallback5DC2380. The native scanner at291F80F does not independently guard a zero scan-result before its dereference; no-match is not a demonstrated native fallback. Exact pointer membership plus the current row supplies its own candidate in ordinary source state. A readonly unread demanded mapping remains partial rather than emulating an invalid dereference.
   Stored outer duplicates can select the same first mapped PC repeatedly. Every admitted occurrence merges, even an initialized empty fallback PC, at100000. Membership false skips magic/mapper/guard/PC.

Lazy initialization branches only were captured, not invoked: first default291F8D1 rejoins291F620; mapped fallback291F860 rejoins291F7CE. Inline fallback addresses are not pointer slots.

## 291F940: outer-row interleaving and nested mapped unit requests

Resolve first Rite Character+B4 through5D1E2F8/fullID+8 and fallback5C67670; second via first4B8 through5D1E300/fullID+8 and fallback5D1E2E0; third via second98 through the first Rite store/fullID+8, defaulting to original5C67670. The selected third Rite+750 is a membership context, **not the model+10 recipient**. Its QWORD+50 / signedcount+5C selects accepted keys for nested helper4212920. A business name for the second+98 relationship is not established here.

Independently resolve Character+158 through actual storage5D1DAF0/fullID+10 or fallback5D1DAE8. Resolve its full key+2C through storage5D1DE78/fullID+10 or fallback5D1DE28. Selected object's QWORD+178 / signedcount+184 stores source pointers in stride8 order.

For every outer source occurrence, native does the following in order:

1. Read signed32 source+16C. Nonzero admits source+160 PropertyContainer at291FACD, weight100000 to model+10. Exactly zero skips this direct merge; source16C is the PC key countC. Keep negative nonzero admission even if a consumed PC read then remains partial.
2. Always pass source+450 list header, selected Rite+750 context and model+10 recipient to4212920 at291FAE0. Header0 / signedcountC stores inline stride30 descriptors. For each inner descriptor, key=QWORD[row+20]; admit exactly if selected Rite+750's50/5C QWORD list contains key. Zero inner count does not demand membership context fields or keys.
3. Admitted inner descriptor invokes4212800(key, whole source450 header). This cached274B mapper checks key magic38=4744624F; when true chooses the *first row in whole same30-stride list* whose row20 key object's fullID10 equals selected key object's fullID10, then returns QWORD[row28] (including actual null). Wrong magic/no ID match returns inline default PC5DC21B0. Its actual initializer marker is5DC21A4; native checks this marker before magic/scan even if mapping succeeds. Observer reads current marker and PC without initialization.
4. Each admitted inner row merges returned PC at42129AF, weight100000, model+10. No Q-derived, scalar or variable weight appears in either helper. Duplicate inner key identities still produce separate occurrences selecting the first mapped PC.

**Full contribution order is outer0.direct160 -> outer0.inner0/inner1/... -> outer1.direct160 -> outer1.inner...**, not all direct rows followed by all conditional rows. Pure separate direct-family observations are useful independently; full-stage emission needs this nested order.

4212920 is three contiguous segments[4212920,42129D5),181B. Its membership and mapper are now source-closed, including map default/guard. No script callback, trigger evaluator, heap producer or variable-weight path occurs in this helper.

## Native tree and remaining boundaries

```mermaid
flowchart TD
  P["291F0A0 -> direct80 -> guardedAA0"] --> C["291C457 ->291F550; receiver=model+10"]
  C --> CG["Culture B0 fullID10 / fallback; Cult magic14 and ID10!=-1"]
  CG -->|false| H["291C462 ->291F940"]
  CG -->|true| G["Readonly28C2E10 selected government; magic38"]
  G --> GI["Culture670+signedGovID10*1C0 / actual static5D65890 +guard"]
  GI --> CP["291F62C unit100000"]
  CP --> CD["Culture90/9C stored directPCs;291F65C unit100000"]
  CD --> CR["B4 ->first4B8 ->second98 selected Rite; fallback"]
  CR --> CM["Culture230 descriptor20 QWORD membership in Rite7A0/7AC"]
  CM --> CX["admitted: first keyFullID10 mapped descriptor28 /actual5DC2380+guard;291F829 unit"]
  CM -->|false| H
  CX --> H
  H --> RR["B4/4B8/98 selected Rite+750 membership context"]
  RR --> OO["Character158 registry ->selected2C registry ->outer178/184 list"]
  OO --> D["outer row:16C!=0 ->PC160 unit100000"]
  D --> I["same outer row:450 header0/countC; stride30 inner rows"]
  I --> M["inner20 fullQWORD membership in Rite750+50/5C"]
  M -->|true| K["4212800: first FullID10 mapped row28 /actual5DC21B0+guard"]
  K --> W["42129AF unit100000 ->model+10"]
  M -->|false| N["next inner, then next outer"]
  W --> N
  N --> B["return; caller291C467 onwards"]
  B -. unknown .-> U["Other current-person caller stages and actual Entry association"]
  A["Absent1C8 recipient of earlier291F0A0"] -. "separate2BFB4C0" .-> T["2BFAC30 current contribution inputs still unknown"]
  classDef unknown stroke-dasharray: 5 5;
  class U,T unknown;
```

Both later helpers have independently valuable direct current source observations and source-closed conditional selection. They do not consume2BFAC30 or require earlier absent1C8 recipient reconstruction. Existing .2 religion-conversion package proves2BFAC30 call placement but delegates to the native complete evaluator rather than publishes its current contribution collection. Its readonly current source reconstruction therefore remains a separate exact .3 leaf; no new reads were spent on it here.

New EXE I/O is2064B =1920 code +144 narrow.pdata, total lane5173B. One274B4212800 body was redundantly captured after a parallel cached-path search found the old body; this extra is counted and preserved, with no wrong RVA/game action. Future captures follow cached-search results before code read. Other cached caller/A11F60/28C2E10/3F90910 source reused. No unwinds, external initializer leaves, whole-file scan/hash, compilation, old tests, runtime or game actions.


## Explicit person preparation stage baseline source closure

Adoption time: 2026-10-05T22:18:13+08:00. Source ledger, Mermaid and PLAN.json were sealed before the bounded assembler implementation. The existing completed-empty-reset interface remains; the explicit retained-baseline connection is being implemented and has no new validation claim yet.

The useful interface is a **logical post-reset context explicitly labeled
`post_291C010_pre_prefix`**, followed by the existing provider prefix and then
the actual291D1D0 requests. It does not identify an old snapshot as that stage.
Frozen EXE SHA256:94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6.

```mermaid
flowchart TD
  E[291C0D0 incoming model; owner already model8] --> R[291C0F7 calls291C010]
  R --> W{DWORD model1C !=0}
  W -->|yes including signed negative| Z[Clear model1C /84 /EC]
  W -->|zero| K[Preserve independent aggregate counts and arrays]
  Z --> C[2922950 model248 owned pointer cleanup]
  K --> C
  C -. actual nonnull children unread .-> U[9F24F0 and allocator virtual10 physical lifecycle]
  C --> A[Allocator cursors reset; model2F4 pending byte0]
  A --> S[Explicit logical postreset baseline model10]
  S --> B[291C119 provider1530 block40 at Q100000]
  B --> M[291C150 provider1A48 ordered common blocks40 at Q]
  M --> T[291C1F0 actual selected18F8 or19A0 ordered blocks40 at Q]
  T --> P[Exact pre291C204 context]
  P --> D[291C204 calls291D1D0]
  D --> G[Selected branch then positive group0..6 with weight count*Q]
  G --> X[Exact bounded post291D1D0 context before291C209]
  X -. additional contributions .-> L[preA1640 /A /D460 /B /DED0 /DCE0 /later suffix]
  L -. complete changed context and first contact .-> F[Full Entry /forecast unknown]
  G --> N{2438850 source key count0?}
  N -->|yes| SK[No weighted row or aggregate fold]
  N -->|nonzero complete arrays| ROW[Append source block and signed Q64 weight]
  ROW --> V{Destination key count0?}
  V -->|yes| CP[11E1180 key copy; B73F50 value copy]
  CP --> Q{Weight Q100000?}
  Q -->|yes| RET[23034A3 direct return; copied FFFF kept]
  Q -->|no| SC[23033BC..34A3 scale every copied value with exact fixed multiply]
  V -->|nonempty| MER[2303120 signed fixed term; skip FFFF; U16 lower_bound and zero insert then wrap64 add]
```

## Ordered source ledger

| Stage | Exact source | Logical effect and required input |
|---|---|---|
| Incoming |291C0F0/F3|RCX model, owner QWORD[model+8]; current model identity alone gives no historical stage |
| Reset |291C0F7→291C010|model+1C !=0 clears weighted count, key count model+84, value count model+EC; otherwise the independent aggregate counts and active arrays survive direct reset |
| Owned cleanup |291C074→2922950|model+248 pointer array, allocator model+240; normal control zeros only owned count model+254 directly; nonnull cleanup/release children remain physical lifecycle unknown |
| Reset return |291C0B7/C0C8|pending byte zero after allocator cursor reset; no context values copied or initialized here |
| Baseline |before291C119|Explicit postreset logical weighted count0, aggregate paired arrays/count. Empty baseline is valid when explicitly supplied; weighted0 alone never implies empty aggregate |
| Base prefix |291C119|provider+1530 block+40, weight100000; empty source skips |
| Common prefix |291C150|provider+1A48, native 16B order; each first pointer block+40 at weight100000 |
| Selected prefix |291C1F0|Actual observed selector18F8 or19A0, native 16B order at weight100000; provider second qword is not a weight |
| Prebranch |291C204|Complete logical prefix result is the actual required input for291D1D0 |
| Selected branch |291D238|Initial flag14 true uses actual selected index/providerFA8 block+40 at100000 |
| Seven groups |291D407|Actual eligible record census; positive signed32 group count in0..6 source order supplies provider1000[group]+40 and signed64 count*100000 |
| Stop |return to291C209|Remaining preparation contributes additional requests. This packet does not call it complete context or full Entry |

291CF50 later swaps model owners, pending flags, context headers, allocator and
owned containers. Therefore a present address, pending0 or zero rows cannot
retroactively prove that present context was the historical baseline.

## Minimal logical input and implementation plan

Extend the existing materialized-prefix module with an explicit stage baseline
and a bounded prefix→291D1D0 assembler. Keep the existing completed-empty-reset
API. Reuse its source-defined copy/merge and the existing signed Q multiply;
factor the fold rather than duplicate the numeric model.

The explicit baseline carries a Character full ID, the exact stage label,
logical context and caller provenance. After reset the weighted count is zero.
The retained branch still requires its actual complete paired aggregate arrays;
negative or mismatched counts remain partial. Source contributions retain native
order, duplicates, signed zero/negative values and original property rows.

An explicitly requested **modeled new reset** may project the source's direct
count stores from supplied entering counts. Nonzero weighted count projects an
empty logical count state; weighted zero preserves the supplied aggregate.
This is a conditional new-stage numeric model, never proof that native cleanup
ran or that a historical current-final snapshot was preprefix. Physical allocator
state is not modeled. A caller can instead supply the explicit postcleanup
logical context. No automatic adapter turns current-final into historical prior.

Empty destination with nonunit weight is now source-closed at the necessary
23033BC continuation: copied key/value order is retained, every copied value
(including keyFFFF) is scaled by the already implemented signed fixed Q helper.
Constants3037000499 and0x29F16B11C6D1E109, fast and decomposed paths, truncation,
store order and normal exit match the existing arithmetic primitive. With
weight100000 the source returns without scaling; nonempty merge still skipsFFFF
after computing its term. First copy does not coalesce duplicate keys.

Scope is logical numeric postimages after supplied normal source requests,
without physical allocation readiness claims. The actual arrays determine the
numeric result; storage capacity remains diagnostic. Other trait/provider
changes, later helpers, full first-contact context, Entry/stat refresh and
calendar/RNG remain separate inputs and unknown branches.

## Read receipt

Reuse v79 caller/reset/writer, v83 insertion, v85 copy/materializer, v86 cleanup
and current state. New necessary scale reads total231codebytes (18B fragment plus
213B bounded continuation). No new metadata was needed. A29B cleanup-entry read
duplicated v86 before that cache was found; it is preserved as an avoidable
attempt, not new research credit. Total fresh EXE I/O260B. Whole EXE scans/hashes,
native builds, old tests, game/process/query/SDK/pipe/UI/Steam operations:zero.
CLI `check --plan` failed before source capture due to a wrong argument; the
correct positional plan check passed. This harness failure remains in receipt.


### 显式人物阶段基线与前缀连接交付

实际采用时间：2026-10-05T22:28:23+08:00。source e68ef8922a535ea188d80654e0f09a309755c295→Root497319d0已合入，source账本/Mermaid先封存并同步frontier。既有materialized prefix保留completed-empty-reset API，新增明确post_291C010_pre_prefix logical baseline；支持weighted0但aggregate非空的实际保留分支，依原生base/common/actual-selected→291D1D0 selected/groups顺序复用共享fold，返回pre291C204和post291D1D0/pre291C209两个有界context。必要23033BC空目标非unit-Q scale已闭合；firstcopy重复keys/FFFF与nonempty merge的FFFF skip分开。不自动将current-final当historical prior或声称cleanup实际执行。

唯一新增production normalizer→assembler→既有six-skill kernel integration一次1/1 GREEN，结果保留aggregate为[9,6,6,6,8,9]、显式新reset清空为[9,6,6,6,8,7]；首group2Q空目标、大数分解与prowess raw80006→cap120已覆盖，缺失baseline和错误current-final stage仍partial，原当前prowess8与输入不变。旧tests、native builds和游戏操作0。本包资格为有界logical stage static-ready，不是完整人物/Entry、native parity、physical allocator/storage、历史stage观测或live。

交付及日周fields保存在第二批actual-entry-context/person-stage-baseline/ROOT-DELIVERY.json、OCT5-W41-FIELDS.json；focused-attempt-01/RESULT.json保留实际测试。新必要EXE code231B、一次可避免的cleanup重复读取29B按实际历史保留计成本而不给新研究信用，总260B；wrong plan CLI和Windows wildcard harness失败已保留纠正，没有capability RED。完整专题：[explicit person stage baseline](battle-person-stage-baseline-12003.md)。下一实际连接是post291D1D0→preA1640/A/D460/B/DED0/DCE0和已闭后缀，各helper输出逐stage续fold，未知与合法空分开。

两条原生observer包继续施工：291F550/291F940 ordered source与monthly post-updater budget，source均已闭合并同步native专题，尚不抢记其native/consumer GREEN。前一census提交74f60838的官方CI37322176165/37322176711已SUCCESS，11个新增native tests和60份新真实fixture consumer资格仍保持，未重复运行。各包完成即普通commit/push；后台入口没有耗尽。CK3/SDK/realpipe/UI/Steam/profile/save/cache/runtime prepare/stage/deploy与新增游戏日0，游戏留给用户，历史5035/36524、G2 5/8、NW2 2/4、natural0保持；日报/周报rolling不倒填午夜收口。

