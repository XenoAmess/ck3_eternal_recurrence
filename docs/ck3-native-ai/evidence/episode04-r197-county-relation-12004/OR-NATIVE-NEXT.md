# R197 target-first P false: narrow next OR observation

machine_id: `desktop-3fevhd2-1c74096080`  
observed_at_utc: `2026-10-17T05:31:23Z`  
This task only read the retained function, small source indexes, current observer source and one existing response. No SDK, desktop, game, EXE scan, build, fixture execution or main-tree change occurred.

The R197 response is `D:/workspace/ck3_native_war_ai_promo_work/e04-r197-county-refill-a01/desktop-3fevhd2-1c74096080--vanilla--R0197/responses/r197-p-preview-once-a01.json`, 32,815 B, SHA-256 `522f42fccef31657eb07016d43d58259adbe93beda18ea0678af4e7421615263`. Its available child reports source receiver34960/actor31254, sampled pairWar4, raw+358=0, sampled direct gate true, actual relation ALtrue; target-first receiver34232/actor31254, sampled pairWar-1/directfalse, actual relation ALfalse. Both have stable complete IDs; the second target P was not called. Both children explicitly retain `unknown_or_inputs=true`. These are observations from this machine, not portable runtime qualification.

## Exact retained caller facts

The complete held function `2C09620..2C096DF` is191 B:

- `C:/ck3-e04-resume-20261015-a01/county-relation2C09620-source-a03/actual-function.bin`, SHA-256 `701c63b6a5f7ed78ce75d6a591fcc4dc0ae2464267a05a23f5b5feb3a3cd8edb`.
- Same directory `actual-function.asm`, 3,953 B, SHA-256 `e16e66f9028b9cd5a607f898a5deb6fcb36c5acbd7371c38cf6aa87c4e4164c9`.
- Same directory `RAW-READ-LEDGER.actual-a01.json`, 4,167 B, SHA-256 `bea6c5637e42f296aee72054d6ecea4591bd7cc992b42157fc0793864fcf1a3f`.
- Same directory `SOURCE-CONTRACT.actual-a01.json` gives the ordered branches and explicitly marks both OR callee bodies unread. Exact source EXE SHA is `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.

| OR leg | Actual CALL and caller return RVA | Source-proved inputs and return use |
| --- | --- | --- |
| First | CALL `2C096A3 -> 2C09580`; return `2C096A8` | `RCX=RSI=relation receiver`, `RDX=RDI=original actor`, `R8=RBX=original auxiliary identity`. The immediate `TEST AL,AL` branches true at `2C096AA` when AL is nonzero. |
| Second | CALL `2C096B2 -> 2C09780`; return `2C096B7` | Caller explicitly reloads only `RCX=receiver` and `RDX=actor`. The immediate `TEST AL,AL` at `2C096B7` branches false at `2C096B9` when AL is zero. **R8 is not reloaded after the first CALL**; do not carry the first leg's auxiliary contract into this leg. |

The first OR leg is reached after the native direct path fails; the second is reached only after the first returns ALzero. Same complete receiver/actor ID returns false before either leg. A direct-path true skips both. This is the retained CFG, not a claim that either OR return was observed in R197. Sampled pairWar-1 is an entry-time read, and actual outer ALfalse does not become two newly observed OR values. Their relationship names, internal logic and bodies remain unknown.

The retained metadata ledger already contains runtime rows `2C09580..2C09615` (149 B) and `2C09780..2C097EB` (107 B), both pointing at xdata `5109E4C`. Those are metadata only: no callee prefix/body was retained by this task. They do not authorize installation or establish a function's entry bytes.

## Smallest reusable observation proposal

Extend only the current P-stage/relation observation context with two optional **naturally called** OR entry/return records. Bind the first to actual native caller return `2C096A8`, the second to `2C096B7`, and retain current P stage, actual receiver/actor complete IDs, same thread and before/after identity stability. Capture first-leg actual R8 as an opaque auxiliary identity; the second leg has no source-proved R8 input meaning. Each record needs call count, actual native caller RVA, actual arguments and returned AL/bool. A skipped or unobserved call remains missing/unknown, never false; no synthetic predicate invocation is needed. The source P's naturally skipped OR path should remain skipped.

If acquisition must start with one named entry, `2C09580` is the first missing gate and the narrowest first source candidate. Capturing it alone will not close the second gate. Completing both natural entry/return observations can distinguish direct-path success, first-OR success and second-OR success/failure without inventing diplomatic relation labels. It does not by itself identify a normal target that yields R04 positive.

Inspected existing `ck3_12004_county_relation_inputs_{context,hook}` only observe the outer `2C09620` entry/return and pure sampled direct inputs. Their current relation callback depth is1 while the original native relation body runs, so it is an existing parent context for such children. Searches limited to county/relation/position headers and sources, central CMake, and the existing exact4 `world.json`/`army_world.json` indexes found no observer reference for either OR RVA. This is a bounded inspected-scope statement, not a repository-wide absence claim. The existing shared document `docs/ck3-native-ai/episode04-county-entry-relation-core-12004.md` lines32–33 and65 independently retains both legs as unexpanded.

No implementation is included. Any future entry hook still needs its exact retained prefix and applicable unwind source, normal source review, the existing default-off installation policy and focused owned-memory qualification. This proposal gives no new live, R04-positive, clean footage or approval credit.
