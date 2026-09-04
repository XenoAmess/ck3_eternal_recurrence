# ZhongGuo manager-governance snapshot v1

## Readiness

- Contract: `production_transport_integrated_static_and_fixture_ready_not_live`
- Fixed kind: `zhongguo.manager-governance`
- Capability: `game.command.query-zhongguo-manager-governance-snapshot-v1`
- OCR: not used and not accepted as truth
- CK3 live artifact: none

This provider is the narrow MCP observation surface for the implemented F032
and F035 manager-governance loop.  It does not expose arbitrary CK3 variables,
grandchild identities, raw result rows, or the AK345–354 policy case family.

## Product-shaped projection

The 77-name native allowlist is fixed in
`zhongguo_manager_governance_snapshot_v1.hpp`.  It is grouped as follows:

| Product object | Real persisted facts | Count |
|---|---|---:|
| F case | owner, subject, cycle, case, state, active, revision | 7 |
| Frozen team snapshot | status; composite owner/subject/cycle/case ID; producer revision and source cycle; `n`; targets, Jingcha, calibration, PIP success, appeal overturn, retention and HC efficiency | 15 |
| F035 distribution | typed receipt; real override/game-rule mode and source; top/middle/bottom/conserved slots; next-cycle token; effective and settled identity; current cohort and actual bottom slots | 33 |
| F032 manager result | typed receipt; exact score sum and score mode; official component-8 pending/settled token | 22 |

The snapshot does not invent a scalar team-snapshot ID.  Its durable identity is
the actual `(owner, subject, cycle, case)` tuple plus producer-owned revision.

F035 validates the implemented arithmetic rather than merely returning labels:

- top is `floor(n * 30%)`;
- strict bottom is `floor(n * 10%)`, with the real `n >= 5` minimum of one;
- relaxed bottom is `floor(n * 5%)`, with no fake minimum;
- off bottom is zero;
- middle is the remainder and all three slots must conserve `n`;
- a settled token must bind the effective mode, source cycle/case/input revision,
  settlement receipt, current `zg361_cohort_n` and actual
  `zg361_bottom_slots`.

F032 validates that the score sum and score mode agree with its receipt and
that the produced token is component `8`, has the same value, is due in the
next cycle, and moves from pending `1` to settled `2` without zero-filling the
settlement fields.  C routes expose typed `not_applicable`; retained variables
from an older A/B route are deliberately wiped from the projection.

## Bounded AI manager dependency

The request accepts only a subject ID, an owner filter and a nonce.  It cannot
contain `manager_is_ai`, government, rank, vassal relationship, case kind or a
variable name.

Two subject paths exist:

1. The subject is the paused played character.  The owner remains a required
   F-case equality filter.
2. The subject differs from the player.  The owner must be the paused player,
   and the application-main adapter must return the typed dependency
   `zg361-bounded-ai-direct-manager-selection-v1` proving all of:
   direct vassal of the player, AI-controlled, celestial government, landed,
   and duke rank or higher.

The provider-specific callback is
`AuthorizeZhongguoBoundedAiManagerV1`.  A missing selector returns
`bounded_ai_manager_dependency_unavailable`; a nonmatching candidate returns
`subject_not_bounded_ai_manager`.  Neither result permits the 77-row read.  A
caller assertion can never satisfy this dependency, so the scaffold does not
turn into an arbitrary third-party character reader.

## Atomic read

The reader reuses the frozen CK3 1.19.0.6 character-variable ABI.  On verified
paused application-main it captures:

```text
frame before
  -> all 77 allowlisted rows
  -> all 77 allowlisted rows again
  -> frame after
```

The two frames and two raw row arrays must be exactly equal.  No engine pointer
is retained.  Character-kind rows are independently resolved through the
frozen character store before they become typed IDs.

## Exact shared integration contract

The provider and its exact-build B3 manager/subordinate selector are now wired
through the shared mailbox, bridge, native driver, service, MCP server, and
formal Phase2 runner.  The completed static integration contains:

1. The reader, serializer and mailbox sources plus the native fixture are in
   `native_bridge/CMakeLists.txt`; compile and register the fixture as CTest.
2. The provider and selector share the already assigned fixed
   `permitted_executor_quinquevigintary` application-main mailbox slot; the
   operation tag prevents one request shape from being parsed as the other.
3. `bridge.cpp` publishes the two capabilities, binds the fixed slot, parses
   each closed request object, executes on application-main, serializes under
   key `zhongguo_manager_governance_snapshot`, and preserves completion-frame
   equality.
4. The bridge adapter implements the typed AI selector from native
   relationship/control/government/landed/rank observations.  Any structural
   read failure returns `dependency_unavailable`; caller data and zero-filled
   identities cannot authorize a manager.
5. `game_adapter.cpp` and its tests contain the fixed step/capability mapping.
6. Native-driver, service and MCP-server plumbing use
   `ZhongguoManagerGovernanceQueryV1` and
   `normalize_zhongguo_manager_governance_snapshot_v1_response`.  The public
   binding must mirror subject-binding kind and the dependency string returned
   by native code.
7. The response schema is registered as
   `schemas/zhongguo-manager-governance-snapshot-v1.schema.json` in repository
   contracts, again deriving list/count changes from then-current master.
8. The bridge/service test matrix covers player subject, authorized bounded AI
   manager, missing dependency, rejected candidate, pending F035/F032, settled
   F035/F032, C routes, same-frame drift and malformed/extra request fields.

Provider symbols already frozen for this integration:

- `kZhongguoManagerGovernanceSnapshotV1Capability`
- `kZhongguoManagerGovernanceSnapshotV1Step`
- `ParseZhongguoManagerGovernanceSnapshotRequestV1`
- `ExecuteZhongguoManagerGovernanceSnapshotMailboxQueryV1`
- `ReadZhongguoManagerGovernanceSnapshotV1`
- `SerializeZhongguoManagerGovernanceSnapshotV1`
- `ZHONGGUO_BOUNDED_AI_MANAGER_DEPENDENCY_V1`

## Live acceptance gate

Static and fixture evidence does not make this provider live.  The MCP-first
batch must eventually retain paused CK3 artifacts proving at least:

1. an authorized real AI celestial duke+ directly below the player is selected
   by the typed native dependency;
2. the F case and team snapshot composite identities agree;
3. F035 has a conserved pending token, followed in a later real cycle by an
   effective/settled token whose actual bottom slots match the active mode;
4. F032 publishes the actual seven-aggregate sum as official component 8 and a
   later real review settles the same source case exactly once;
5. a nonmanager or non-direct-vassal ID returns typed unavailable before any
   variable rows are read.

Until those artifacts exist, the honest readiness remains
`static_and_fixture_ready_not_integrated_not_live`.
