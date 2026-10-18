# Existing preview: actual origin graph adjacency on 1.20.0.4

R205's complete War4 occupation query contained 27 holding rows: defender3
(`2635/2636/2644`) and attacker24. Excluding Army18's actual origin2635 left
only two defender candidates. The two real first edges were2636 and2645;
both had `county_objects_differ=false` and all three P stage counts0.
The snapshot listed only War4. This did not observe an internal P failure or
establish that no other native county condition can pass.

Those observations are from machine `desktop-3fevhd2-1c74096080`, R0205,
PID23676/generation1/episode `native-31254-7a037a02690d`, actor31254,
date53148192, source19024b4d79d818a88709c9932ca4eb364d81ef33/native a35.
The bounded scout RESULT was17052B/SHA
`9e180225e8f68f8a7e168e69c62b3f1897492b018392dfa33b79fabde8ad6e7f`.
These facts do not describe a future scene or qualify a county physical debit.

The existing CampaignRoot adjacency projection supplies the sorted distinct
holders along the whole player's subrealm boundary. It discards origin and
target ProvinceIDs. It cannot serve as Army18's current county-neighbor list.

## Actual source

Root performed one authorized704B file read on2026-10-18T02:30:25Z, reusing the
qualified actual4 executable identity and section map. There were zero new
metadata reads, zero whole-image hashes and no game/SDK action. The captured
span is RVA `[0x24AAD80,0x24AB040)`, file offset38445440, SHA
`ce60c96b74109f03453b2d077c8acd0e5d6a080aa3003b56179614960fabc090`.
The span decodes completely:689B native instruction body through RET at24AB030,
then15B INT3 padding. The function was already independently bound as the
[native prefix-duration reader](route-contact-horizon-12004-restoration.md).

[The source contract](evidence/episode04-origin-adjacency-source-12004/source-contract.json),
[raw bytes](evidence/episode04-origin-adjacency-source-12004/route-24AAD80.actual.bin),
[disassembly](evidence/episode04-origin-adjacency-source-12004/route-24AAD80.actual.asm)
and [Root read receipt](evidence/episode04-origin-adjacency-source-12004/root-read-receipt.json)
retain the exact local source. This is native field-use evidence; no callback
was called while researching it.

| Actual instruction | Proven field use |
| --- | --- |
|24AAD99,24AADE5,24AAE2A|Fourth argument is retained in RBP; Province+8 is the map-node receiver.|
|24AAE36,24AAE46|Signed32 count at node+5C; row data pointer at node+50.|
|24AAE50..24AAE5B|Native row address is data+index*0x30.|
|24AAE5E|Native target ProvinceID is the DWORD at row+4.|

The body does not read row+0 kind. The publisher therefore neither reads nor
publishes kind, and does not infer land/sea or route legality. The County+40
neighbor array used by the condition's Q loop is a different source and is not
published here. Province/tag/full actor/CArmy joins reuse the already bound
county preview inputs; no .3 RVA shift is used.

```mermaid
flowchart LR
  O[Actual preview origin Province] --> N[Province+8 map node]
  N --> S[node+50 rows / node+5C count]
  S --> R[index*30hex +4 target ProvinceID]
  R --> W[origin_adjacency_v1 A/B stable prefix]
  W --> P[Existing readonly preview of an observed target]
  R -. unknown .-> K[row kind / path legality]
  P -. separate native observation .-> C[Native county first-edge bool]
  C -. requires natural arrival writer evidence .-> D[Physical county debit]
```

## Publication and consumer

The existing `route_preview.county_entry_condition_v1` gains optional
`origin_adjacency_v1`. It samples only the current origin map-node rows before
and after the existing24E2230 call. There is no new native game function call,
hook, query, MCP tool, route mutation or movement order. The child's own A/B
comparison requires the existing CUnit/CArmy/actor/Province predicate sample to
remain equal. Its read failure does not erase the original native county bool.

The child publishes origin ProvinceID and opaque same-query Province/map-node/
data identities, the actual signed32 `native_count`, and ordered `rows` of
`occurrence_index` and `target_province_id`. Native duplicate occurrences are
preserved. Identities are process-local observations, not cross-query join keys
or county TitleIDs.

`status=available` means the complete native row extent was read twice and
matched; zero count is a complete empty list. `status=truncated` means a stable
first64 rows of a larger native count: `collection_complete=false`,
`truncated=true`. This limit is our bounded observation budget, not a native
map limit. An unreadable count remains null, and an unavailable child has
`rows=null` and an explicit reason. It never substitutes a failed read with0
or an empty collection. The independent strict consumer rejects wrong origins,
unstable readable rows and count/completeness contradictions. Historical leaf
absence remains absent.

## Root's next bounded use

After the source is adopted and a newly qualified DLL is actually deployed,
one ordinary existing preview to a known valid target can publish all current
origin neighbors, even if that preview's county bool is false. Use the actual
new scene identity/public revision; R205's PID and revision are not reusable.

1. Read `origin_adjacency_v1` from that existing preview. Keep the same current
   actor/Army/origin/date/episode and paused frame. Prefer a complete collection;
   a truncated prefix cannot prove absence of another exit.
2. Take observed positive target IDs in native occurrence order, deduplicate
   for requests, and preview at most three new candidates through the existing
   `preview-move-army-N-to-N` step. No raw graph row alone grants a Move.
3. Inspect the actual returned first hop and county child, including definition
   bytes, county-pointer difference, native bool and optional P/relation trace.
   Duplicate first hops add no new county test. Same-county edges do not reach P.
4. Only a fresh available native true with both definition bytes nonzero can
   supply a Root-reviewed unique Move candidate. Applied loss still requires
   the existing arrival/writer/DATA evidence, including exact source attribution;
   graph rows, a positive budget and Army net change do not supply that credit.

No new production CMake option is introduced. The leaf follows the existing
exact4 county-preview binding. One deliberate standalone fixture target,
`xar_test_origin_adjacency_preview_12004`, is excluded from default builds;
it emits six JSON rows and uses explicit runtime checks, including Release.
Root must use its standard build/producer/SYSTEM qualification before executing
that EXE. `consume_native_wire.py --source-root <adopted repo> --wire <stdout>`
then consumes the six lines through the actual production strict consumer.

Four new production Driver/consumer behavior groups passed offline. Three
MSVC `/Zs /W4 /WX` checks passed for the fixture, the actual serializer template
and the modified Army TU. Full DLL compilation, linked fixture execution and
actual new-leaf observation are NOT_RUN here. No R04 physical positive is added.
