# CK3 native-headless direct marriage contract

This is the first value-bearing outbound marriage slice for pinned CK3
1.19.0.6. It supports the played Character arranging their own marriage or
betrothal with one explicit candidate while CK3 remains minimized. Wider
courtier-to-courtier matchmaking is a later extension, not a prerequisite for
this path.

## Query and choice identity

`ReadArrangeMarriageChoices` is an explicit strategic query rather than a
250 ms heartbeat field. It scans the live Character component storage and,
for each non-dead candidate, builds the exact native interaction context:

- initial interaction actor and actor-side spouse: played CharacterID;
- initial interaction recipient and recipient-side spouse: candidate
  CharacterID;
- intermediary CharacterID: the constructor default (`-1`);
- default marriage option scopes unchanged.

Before construction, CK3 runs the interaction's redirect across all five role
IDs. A candidate courtier can therefore remain the secondary recipient while
their matchmaker becomes the primary recipient. The public choice still names
the selected played Character and candidate, not these derived routing roles.

Only contexts accepted by CK3's own complete interaction validator are
returned. An `ArrangeMarriageChoice` contains both full CharacterID handles:
`played_character_id` and `candidate_character_id`. Their high generation
bits are part of identity; a public opaque ID may encode the two decimal
handles as `<played_character_id>-<candidate_character_id>`, scoped to the
query generation. Low 24-bit component slots are never sufficient identity.

The query result also carries bounded native diagnostics: component-storage
capacity and scan counts, filtering counts, context construction counts,
validator true/false totals, and at most eight validator-false samples with
the five post-redirect role IDs. These fields explain a live empty result;
they do not weaken or replace CK3's validator.

## Exact submit

`SubmitArrangeMarriage` requires the cached choice's played CharacterID to
still equal the current played Character and resolves the candidate by the
complete handle. It then repeats the native construction and validation. A
dead/recycled candidate returns `candidate_not_found`; a changed relationship,
age, eligibility, or actor generation returns `choice_unavailable` without a
command submission.

On success it uses the common native character-interaction send chain:

1. call the exact-build getter at RVA `0x831890` and load
   `CCharacterInteractionDatabase +0xF48`;
2. initialize the five roles as `(played, candidate, played, candidate, -1)`
   and pass their addresses to redirect helper `0x2C3C4C0`;
3. pass the five redirected values plus a null extra context to all-role
   constructor `0x2C3F000`, producing the `0x338`-byte context with actor,
   recipient, secondary actor, secondary recipient, and intermediary at
   `+0x2D8/+0x2DC/+0x2E0/+0x2E4/+0x2E8`;
4. refresh (`0x2C40950`), finalize (`0x2C40B20`), and validate
   (`0x2C43F00`);
5. construct `CSendCharacterInteractionCommand` (`0x26B3220`), submit with
   flags `0x0E`, and destroy the copied and original contexts (`0x2C3F380`).

The engine derives marriage versus betrothal from the two characters' current
age/state. This slice intentionally leaves the default lineage option intact;
matrilineal configuration is a named interaction scope, not a proven raw
boolean payload.

## Relationship state and completion

When a played character exists, each state snapshot includes these fields
inside `played_character`:

- `betrothed_id`: a full generation-validated CharacterID, or null;
- `primary_spouse_id`: a full generation-validated CharacterID, or null;
- `spouse_ids`: every generation-valid CharacterID in the native spouse array.

Pinned 1.19.0.6 reads FamilyData from `CCharacter +0x1A0`, betrothed from
`FamilyData +0x10`, primary spouse from `+0x14`, and the native spouse-ID array
from `+0x20` (`data/capacity/count` at `+0x20/+0x28/+0x2C`). Every raw ID is
passed through the exact Character storage resolver, so a recycled slot with
the wrong generation is reported as absent. No primary-partner field is part
of the public contract.

The observable completion rule is deliberately direct:

- an adult marriage completes when the submitted candidate's full CharacterID
  appears in `played_character.spouse_ids`;
- a betrothal completes when `played_character.betrothed_id` equals that full
  candidate CharacterID.

Command acceptance alone is not completion, and `primary_spouse_id` is status
context rather than the adult-marriage success predicate.

## Named-pipe, MCP, and one-life policy

The DLL advertises `game.command.query-arrange-marriage-choices` and the
dynamic template `game.command.arrange-marriage-N`. The explicit query returns
`query_sequence` plus `arrange_marriage_choices`; each public `choice_id` is
`<played_character_id>-<candidate_character_id>`. Python only expands
`arrange-marriage-<choice_id>` from the latest query and clears that cache after
one submission attempt. A successful submit is persisted in the episode command
history as a proposal intent containing the exact played/candidate CharacterIDs
and `submitted_date_raw`; it is still not a completed marriage.

Typed MCP entry points are `ck3_query_arrange_marriage_choices` and
`ck3_arrange_marriage`. In pure `native-headless` mode both work while CK3 is
minimized and never invoke OCR, focus, keyboard, or mouse. In
`hybrid-fallback` they remain native-only strategic commands rather than
silently switching to visual UI automation.

The one-life planner runs this query after its baseline checkpoint and before
the first war only when the relationship snapshot shows no spouse or
betrothal. If CK3 returns choices, it submits the stable lowest candidate
CharacterID. An empty or failed query advances/retries at most three times; a
stale or rejected submit immediately forces a fresh query instead of
permanently disabling marriage. If a reconnect preserved the query history but
lost its process-local dynamic choice cache, the planner re-runs the query
immediately.

While a proposal intent remains unresolved, the planner chooses bounded
`life-advance` steps even if the old candidate still appears in a cached choice
list; it never re-submits the same pending proposal. Each new snapshot compares
the exact submitted candidate with `betrothed_id` and `spouse_ids`. A match
adds `marriage_result.status=accepted_betrothal` or `accepted_marriage` with
`source=native_relationship_snapshot` to the persisted proposal history. Only
that relationship-backed result counts as a cross-run marriage achievement.
After 30 game days or seven completed advances without a match, the intent
times out, a fresh query is issued, and another candidate is preferred when one
is available. Three empty retry queries release the planner to its other
one-life objectives rather than blocking the run forever.
Any later incoming marriage/betrothal notification is handled by the existing
pending-character-interaction accept command. Player death or a played-character
identity change still ends the episode; the agent never continues as an heir.

## Static and offline evidence

- canonical interaction registration: `0x2C3EA90`,
  `CCharacterInteractionDatabase +0xF48` (database getter RVA `0x831890`);
- all-five-role redirect: `0x2C3C4C0`;
- all-role context constructor: `0x2C3F000`;
- original redirect-then-constructor path: `0x18FA80E` through `0x18FA8A1`;
- original UI callbacks `0x126F923` and `0x126FAF3` also update secondary
  roles on an existing generic context before refresh/finalize; this path is
  not disproven by the all-role direct route;
- betrothed getter: `0x19D4BA0` (`FamilyData +0x10`);
- primary-spouse getter: `0x19D4C50` (`FamilyData +0x14`);
- generic UI validate/send wrapper: `0xFE5190`;
- Release fixture models a recipient-to-matchmaker redirect and covers query
  filtering, generation mismatch, relationship projection, native
  revalidation, all five roles, queue flags, and both context destructions.

Both the former generic-context build and the all-role direct build reached a
minimized live CK3 process and returned `available` with an empty choice array.
Bounded diagnostics showed native validation failures rather than traversal or
construction failures. Live memory resolved the explanation: played
CharacterID `29829` already had primary spouse `34730`, native spouse list
`[34730]`, and no betrothed. The empty result was correct for that state; it is
not evidence that one constructor route fixes the other. A minimized query in
an actually eligible state and a submit observed through the relationship
completion rules above remain the live acceptance boundary.
