# Active-war strategic-power query

Status: `static-ready`; exact build: CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Problem and reuse decision

R459 proved the exact outcome of surrendering WarID `33554473`, including the
3000-to-zero event-army loss and the persisted 1825-day truce. It did not prove
that surrender was preferable because the campaign comparison still lacked a
same-frame strategic-power observation for the current opponent.

The existing production-live capability
`game.command.query-war-entry-assessments-v1-N` already calls CK3's exact
strategic evaluator and returns actor/target base power, relationship-network
contributions, totals, target adjustment, distance, and native power ratio.
The C++ reader accepts explicit full-generation CharacterIDs. The former
declarable-only restriction lived in the Python/MCP admission layer, so a new
DLL or a second strategic-power contract would duplicate the same evaluator.

## Additive target scope

The one-target query now accepts a CharacterID present in either current
snapshot source:

- `declarable_wars[*].target_character_id`;
- `active_wars[*].primary_opponent_character_id`.

Every result adds `target_scopes`, with stable source values
`declarable_war` and `active_war_primary_opponent`. A target present in both
sources reports both values in that order. Targets outside the union are
rejected before the named-pipe request. The source set is checked again on the
same paused snapshot after the native result returns; a source change rejects
the result.

The native schema-v1 payload retains its frozen
`readiness.targets_declarable_ready` key. For this capability version, that
legacy spelling means that the caller's target scope was resolved and approved
by Python. Consumers that need to distinguish declaration from active-war use
the outer `target_scopes` field.

## Policy boundary

This remains a read-only observation. It does not enable declaration,
surrender, white peace, or any recommendation. For GEN-034 it can fill the
current-opponent strategic-power input, while campaign dominance,
owner-authored budget, and same-frame white-peace comparison retain their own
readiness gates.

Focused contract, native-driver, service, strategy, and official MCP client
tests pass `23/23` in normal Python and `23/23` under `python -O`. No CK3
process was launched for this code package. The next live check is one bounded,
read-only query of R459's durable pre-surrender checkpoint; it is not a long
campaign run.
