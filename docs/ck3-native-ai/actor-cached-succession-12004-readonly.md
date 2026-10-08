# Exact 1.20.0.4 actor cached-succession observation

This private observation was added after R27 B4 changed the actor's saved
`succession` array from 45 to 40 and changed five political titles' saved `heir`
arrays. The four saved realm-law fields were unchanged. The cause remains
unknown; this reader neither repairs the cache nor changes the 87 protection
checks or the factory's script order.

The reader accepts only CK3 1.20.0.4 executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`
(installed Steam build 25734779). Its field basis is the bounded actual-image
classifier at RVA `0x2C0B4B0..0x2C0B7D2`: actor `+0x1C0` leads to land state,
land state `+0x3A0` contains a DWORD full-character-ID array with data at `+0`
and signed count at `+0xC`. The classifier is not called. Capacity at `+8` is
not consumed by this evidence and is not inferred by the new reader.

The current played actor is resolved by its complete ID. The reader copies
every entry in original order, resolves every complete candidate ID, and checks
the character's own full ID at `+0x18`. A second complete pass and final
owner/header check reject changes to owner, land-state pointer, data pointer,
count, order or resolved identity. Duplicate, self and high-generation IDs
remain in the output. `0xFFFFFFFF` is unavailable. A genuinely empty collection
is distinct from an unavailable observation. No persistent ID or pointer cache
is introduced.

The existing application-main query mailbox owns the sample. The receipt binds
the paused, live played actor, date, published native revision and execution
pump epoch. The outer Python service additionally keeps public revision,
native revision, game PID and connection generation distinct and checks the
same frame before and after the query. Business and full-product credits are
always false.

## Opt-in interface

The existing native build flag
`XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1` also compiles this
small reader and its mailbox handler. The canonical 12 native ON flags are
unchanged. Its exact .4 native capability is
`game.command.query-actor-cached-succession-v1`; the wire step is
`query-actor-cached-succession-v1`.

The independent Python driver permission is
`allow_private_actor_cached_succession_queries=False`. The MCP server keyword is
`actor_cached_succession_tools=False`. CLI `--actor-cached-succession-tools`
adds only `ck3_query_profile_actor_cached_succession_v1(expected_revision)`.
The revision is a strict positive integer. Default inventories 21, 23, 24 and
28 stay unchanged without this flag; the existing grant-28 options plus this
flag produce inventory **29**. No old tools are renamed.

Native payload schema is `ck3-1.20.0.4-actor-cached-succession-v1`, nested under
`actor_cached_succession`. It includes the complete ordered full-ID array,
native count, original data pointer, land-state pointer and completeness.
Public schema is `ck3-actor-cached-succession-public-v1`.

## Factory execution boundary

`ck3_12004_adapter.cpp` routes the ordinary event option into
`ck3_12004_events.cpp::SubmitSelectEventOption`. That function constructs the
actual .4 event command with vtables `0x47733E0/0x4773540` and calls
`submit_command(..., 7)`. The shared command copier clones the command and
passes its ownership into the actual .4 command queue (RVA `0x37F06D0`, manager
`0x5CC1240`). A submitted receipt proves queue admission.

The five factory operations are CK3 script effects in
`mod_li_yu_dao/common/scripted_effects/lyd_c3_head_factory.txt`, entered by
`lyd_i3b_commit_effects.txt::lyd_i3b_commit_effect`. The project has no separate
C++ callbacks around create, holder change, resolve, SetHead or cleanup.
Sampling before/after queue submission would not be a five-stage trace.
Per-stage causal observation would require a separately established engine
effect-execution boundary; it is not added or claimed here. Native-to-saved
`succession` equality and the producer/eligibility cause require new actual
observations.

## Focused validation

`xar_ck3_12004_actor_cached_succession_v1_test` compiles the production reader
and an in-memory fixture, with no game, pipe or injection. It checks complete
ordered 45/40 arrays, same-epoch reads, legal empty, duplicate/self/high-generation
IDs, pointer/count/order/owner/land-state/generation changes and unresolved IDs.
Fourteen new Python tests check the strict DTO, bindings and independent opt-in
inventories without SDK or native runtime calls. Full DLL linking and live
field-to-save agreement remain ROOT's fresh-build and runtime work; whole-mod
acceptance remains NOT_GREEN.
