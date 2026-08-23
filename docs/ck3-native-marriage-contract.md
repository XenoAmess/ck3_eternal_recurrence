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

- interaction actor and actor-side spouse: played CharacterID;
- interaction recipient and recipient-side spouse: candidate CharacterID;
- optional third CharacterID: the constructor default (`-1`);
- default marriage option scopes unchanged.

Only contexts accepted by CK3's own complete interaction validator are
returned. An `ArrangeMarriageChoice` contains both full CharacterID handles:
`played_character_id` and `candidate_character_id`. Their high generation
bits are part of identity; a public opaque ID may encode the two decimal
handles as `<played_character_id>-<candidate_character_id>`, scoped to the
query generation. Low 24-bit component slots are never sufficient identity.

## Exact submit

`SubmitArrangeMarriage` requires the cached choice's played CharacterID to
still equal the current played Character and resolves the candidate by the
complete handle. It then repeats the native construction and validation. A
dead/recycled candidate returns `candidate_not_found`; a changed relationship,
age, eligibility, or actor generation returns `choice_unavailable` without a
command submission.

On success it uses the common native character-interaction send chain:

1. construct the `0x338`-byte context from `CK3GameData +0xF48`;
2. write secondary actor at `+0x2E0` and secondary recipient at `+0x2E4`;
3. refresh (`0x2C40950`) and finalize (`0x2C40B20`);
4. validate (`0x2C43F00`);
5. construct `CSendCharacterInteractionCommand` (`0x26B3220`), submit with
   flags `0x0E`, and destroy the copied and original contexts (`0x2C3F380`).

The engine derives marriage versus betrothal from the two characters' current
age/state. This slice intentionally leaves the default lineage option intact;
matrilineal configuration is a named interaction scope, not a proven raw
boolean payload.

## Named-pipe, MCP, and one-life policy

The DLL advertises `game.command.query-arrange-marriage-choices` and the
dynamic template `game.command.arrange-marriage-N`. The explicit query returns
`query_sequence` plus `arrange_marriage_choices`; each public `choice_id` is
`<played_character_id>-<candidate_character_id>`. Python only expands
`arrange-marriage-<choice_id>` from the latest query and clears that cache after
one submission attempt.

Typed MCP entry points are `ck3_query_arrange_marriage_choices` and
`ck3_arrange_marriage`. In pure `native-headless` mode both work while CK3 is
minimized and never invoke OCR, focus, keyboard, or mouse. In
`hybrid-fallback` they remain native-only strategic commands rather than
silently switching to visual UI automation.

The one-life planner runs this query after its baseline checkpoint and before
the first war. If CK3 returns choices, it submits the stable lowest candidate
CharacterID once; if the query is empty it proceeds to native war discovery.
Any later incoming marriage/betrothal notification is handled by the existing
pending-character-interaction accept command. Player death or a played-character
identity change still ends the episode; the agent never continues as an heir.

## Static and offline evidence

- canonical interaction registration: `0x2C3EA90`, GameData `+0xF48`;
- all-role context constructor: `0x2C3F000`;
- generic UI validate/send wrapper: `0xFE5190`;
- Release fixture covers query filtering, generation mismatch, native
  revalidation, all four direct-role IDs, queue flags, and both context
  destructions.

The C++ and Python contracts are covered by offline native, driver, planner,
service, and MCP fixtures. Live minimized acceptance remains required before
marking the route as game-proven.
