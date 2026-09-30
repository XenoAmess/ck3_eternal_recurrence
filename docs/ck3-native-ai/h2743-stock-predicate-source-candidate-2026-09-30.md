# H2743 stock predicate reader source candidate — 2026-09-30

## Scope and current status

This isolated candidate is based on master `793041bfb8fe28090576f50310c4dd91086608f5` in `C:/h2743p30`. It implements three independent read-only observations for the frozen CK3 1.19.0.6 stock truce conditions: `short`, `long`, and `border_raid_pair`. It adds no effect, fee, date operation, surrender, public capability or launch authorization. The native adapter and CMake option default OFF.

The evidence proves equivalence to the stock getters' data and the frozen script conditions. It does not claim an executed outer trigger differential. No game was launched and no new binary was built during this preparation. Runtime predicate remains **0/1**, formal exit **0/1**, and authorized action **null**. `material_complete` intentionally remains false; three predicate values cannot certify all war termination effects or costs.

## Files and ABI

| File in `ck3_autonomous_player/native_bridge/` | Responsibility |
| --- | --- |
| `include/xar_bridge/h2743_stock_predicate_reader_v1.hpp` | Private typed observations, native bindings and pinned stamp |
| `src/h2743_stock_predicate_reader_v1.cpp` | Bounded complete raw reads and two identical samples |
| `src/h2743_stock_native_source_adapter_v1.cpp` | Windows/MSVC x64 process reads, lookup-only/name roundtrip and stable hash |
| `src/h2743_stock_predicate_reader_v1_test.cpp` | Fake memory fixture calling the production core; source prepared, execution pending authorized build |
| `cmake/h2743_stock_predicate_reader_v1.cmake` | Default OFF build fragment; integration owner includes after bridge target creation |
| `research/h2743_stock_predicate_reader_v1_abi.json` | Exact executable/script hashes, 45 disk proofs and pointer layout |
| `research/test_h2743_stock_predicate_reader_v1_source_contract.py` | Fresh create-only disk/source binding fixture; no native calls or compiler |

The executable SHA-256 is `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

### Short and long

The stock helper at `common/scripted_triggers/00_generic_struggle_scripted_triggers.txt:314` expands to the phase parameter test followed by a saved full struggle scope and membership in the defender's struggle list. The script value at `common/script_values/00_war_values.txt:20` binds attacker and defender independently for short and long parameters.

`CCharacterStruggleListBuilder` at `0x19BA7F0`, default mode2 at `0x19BF124`, requires Character cache `+0x1B8` and a zero **uint64** dirty word at `+0x1C8`. It emits full uint32 Struggle IDs from the involved/interloper arrays at cache `+0x168/+0x180`. The equality leaf `0x334FE60` compares kind, subtype and the full qword payload. Thus complete full-ID intersection of the two mode2 lists is the stock membership relation. Store `0x570CC78` and Struggle `+8` retain generation checks.

The phase pointer is Struggle `+0x4C0`. Getter `0x2D05950` scans four blocks starting at phase `+0x78`, stride `0xB30`, with four sorted integer arrays per block at `+0xAB0/+0xAC8/+0xAE0/+0xAF8`. Each array's proven inputs are pointer `+0` and signed count `+0xC`; this candidate does not invent a phase capacity ABI. Both parameter names use actual lookup-only `0x3B588E0(View16*)`, reject negative/missing identifier12, and verify the full borrowed name through `0x3B58970(int32)` before use. Interner `0x3B58330` is never called.

The two names are:

- `truces_by_involved_or_interlopers_within_region_shorter`
- `truces_by_involved_or_interlopers_within_region_longer`

Missing either name makes only that observation unavailable. Incomplete caches, stale IDs, invalid phase data or changing samples never become false.

### Border raid

The stock condition at `00_war_values.txt:56` iterates attacker `any_character_war` and checks primary attacker, primary defender and `using_cb = fp2_border_raid`.

The actual list builder `0x19DCB60` reads attacker land state/cache `+0x1B8`, then array pointer `+0x318` and count `+0x324`; it emits kind16/full War IDs. The candidate resolves every listed War against storage `0x570C740` and War `+8`, then reads roles `+0x288/+0x28C`. Both named role Characters must resolve with their full generation ID. Defender cache/dirty availability does not gate this branch's role identity.

`using_cb` leaf `0x28481A0` compares War `+0x100` to the loaded CB definition pointer. The candidate reads the already existing owner at `0x570BE58`, without calling lazy getter `0x88E260` or lock-writing lookup `0x2024E40`. The raw Robin Hood table has owner pointer `+0x198`, signed mask `+0x1A4`, overflow byte `+0x1A8`, 24-byte rows, state/hash/definition at `+4/+8/+0x10`, and `mask+overflow+2` rows. The probe does not mask-wrap. It rejects fallback, incomplete extent and distance overflow.

The native stable hash call `0x3B8B000(nullptr, bytes, uint32_length)` must return `0x229B01D7` for `fp2_border_raid`. A candidate definition must have exact vptr `module+0x44197A0`, hash `+0x14`, and a full MSVC name roundtrip at `+0x18`. Hash equality alone is insufficient.

The raw table read admits only mode byte owner `+0xEF8 == 0` and uint32 lock word owner `+0xEB8 == 0`, before and after the table/name reads; both reads enter the byte journal. The native lookup proves bit0 is a writer gate and +2 is a reader count. A zero word is sampled quiescence, **not an acquired lock or an atomic snapshot**. Other modes or occupied metadata are unavailable. Execution therefore also requires the actual registered application-main callback and pinned paused/living stamp.

## Focused verification and corrections

The fresh disk/source fixture completed **61/61**, RC0:

`C:/Users/1/ck3-h2743-resume-20260930/stock-source-preparation-a01/source-binding-fixture.json`

SHA-256 `313B498353DB0AC968B3D6E6A5329B540AD402206925C2902B8E1FC92D784ED5`. This verifies exact disk bytes and source guard bindings. It explicitly records `cpp_behavior_fixture_executed=false`, `native_build=false`, and `runtime_predicate_observed=false`.

Short/long independent review found no definite defects. Border review identified two concrete issues: omitted CB owner lock/mode metadata and missing independent defender generation validation. Both were corrected before final review. Historical review snapshots are preserved.

- Short/long original review receipt: `stock-source-review-a01/review.json`, SHA `DD0EFADDEB8167D894E11934EAB58DF67297BF343A00F8566CA5002D4DAF74DA`.
- Final core rebind after the border fixes: `stock-source-review-a01/final-core-rebind.json`, SHA `03EAAB5363A4B2FC4AF409FD9BE460FE01EFB7523ADFC33E11A71CCA0CBDCD6C`.
- Border final review: `stock-source-border-review-a01/postfix-review.md` and `postfix-source-snapshot-receipt.json`.

These directories are under `C:/Users/1/ck3-h2743-resume-20260930/`. Final core SHA is `F5CA0C5212B8AED2F365EE63513789FF44FEF3DF4B13DC629D1FE0EF70457416`; adapter SHA is `54756E9F9991E377D202901191DF179D404D2E994D656F5F3DCCD4B660DDD430`. Reviews certify static source and getter data equivalence only.

## Minimal integration still required

**Master793's native C++ does not contain the #723 H2743 baseline producer.** Adding this fragment alone will not produce a query. Preserve current common/H3/native fixes when projecting the narrow original #723 H2743 native contract, producer and serializer from source `24c51a37d2facd2dcf24da2d54e5f0c4548833cb`. Do not copy the entire old bridge/runtime tree or overwrite frozen #723 assets.

The old producer is `src/ck3_11906.cpp:18911`, `ReadDefenderDeJureExitTermsV1`. Its serializer at old `src/bridge.cpp:4429` emits unconditional `stock_condition_reader_unavailable` for these three keys. That is the exact behavior to replace with the three typed observations. Keep the existing outer admission/completion stamps and full baseline checks, `material_complete=false`, `evaluated_days=null`, and `persisted_expiry_date_raw=null`.

The new reader must run synchronously on the real application-main mailbox executor. The integration owner must close all of these in the same source:

1. Exact private query parser, first admission guard and handler; no general action admission.
2. Mailbox submit/collect route with the actual pinned actor, war, date, source revision and native revision.
3. Executor callback registered in its permitted callback table and installed in the application-main observer; the old direct worker handler is insufficient for this new adapter.
4. `H2743StockNativeContextV1` built from the exact verified game module, observed application-main thread ID and a stamp observer that reads actual bridge/game state. A profile/sidecar cannot substitute for this observer.
5. `BindH2743StockNativeSourcesV1(context)` then `ReadH2743StockPredicatesV1(bindings, expected)` inside that one callback. The context must live until the synchronous call returns.
6. Translate each state independently: native true/false -> `observed` bool; unavailable -> `value:null` with a reason. Never infer a value from missing data, lack of callback or this static fixture.

Before a new DLL is admitted, build and execute the focused production C++ fake-memory fixture, obtain a fresh traceable source -> Release DLL/injector pair, and audit parser -> firstguard -> handler -> submitted callback -> permitted/installed executor -> serialized typed rows. Root controls build resources and all later screen/Steam/GO inputs. Reserved R0120 and its old #723 baseline history remain unchanged.
