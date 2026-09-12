# Primary-title succession v1

## Status and purpose

- **[static-ready, live pending]** `campaign-root-context-v1` now publishes
  `primary_title_succession_character_ids` in the native order stored on the
  played character's current primary landed title.
- The first element is the minimum observable primary-title heir candidate.
  An empty vector is a real native result: either the player is landless or the
  primary title currently has no successor in its ordered array.
- This component is sufficient to build a truthful minimum succession alert
  for the primary title. It does not predict partition across every held title,
  identify succession laws, or prove campaign continuation after death.
- Native AI decision-tree research is N/A for this read. The bridge publishes
  current world state and does not reproduce an AI choice.

The contract is bound to CK3 `1.19.0.6` and executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Exact-build layout

The existing native primary-title resolver at RVA `0x25F3350` returns the
current `CLandedTitle*`. That object exposes its ordered successor CharacterIDs
through the already frozen layout used by the war-exit prisoner-release reader:

| Field | Offset |
|---|---:|
| data pointer | `CLandedTitle+0x278` |
| capacity | `CLandedTitle+0x280` |
| signed count | `CLandedTitle+0x284` |

The generic campaign-root reader now consumes the complete span, capped at
4,096 entries. Every item must be a positive full CharacterID, distinct from
the current holder and all earlier entries, and must resolve through
`module+0x570C130` with `CCharacter+0x18` equal to the same full-generation ID.
The wire preserves native order; it must never sort the array because order is
the business value.

## Atomicity and failure behavior

The vector participates in both existing application-main observations and in
the before/after paused-frame equality gate. Any malformed span, generation
mismatch, duplicate, holder self-entry, read failure, or inter-sample change
makes the whole campaign-root frame typed unavailable with
`primary_title_succession_unavailable`. No partial prefix is published.

When `primary_title=null`, only `[]` is legal. When a primary title exists,
`[]` still means the native title currently exposes no successor; it must not
be replaced with `null`, OCR, a save-file guess, or an earlier snapshot.

## Readiness boundary

This package closes the static observation path for a **primary-title** heir
alert. These larger succession requirements remain open:

- succession law and elective state;
- eligible heirs with acceptance or disqualification reasons;
- predicted heir for every held title;
- partition distribution and claim consequences;
- game-over risk and post-death continuation proof.

One future bounded paused G2 session should read this vector alongside the
already required campaign-root/entity-directory live check. A dedicated long
run for this field is unnecessary.

## Focused verification

- Release DLL compile and link: GREEN.
- Direct native reader fixture: ordered two-successor span, landless empty
  vector, and generation-invalid successor rejection are GREEN.
- Native source-contract executable: GREEN.
- Python contract, driver, service, MCP and live-harness fixtures: normal and
  optimized `35/35` GREEN.

The built candidate DLL is a local ignored artifact; its exact hash is recorded
in the daily/weekly report for this package and does not constitute live CK3
evidence.
