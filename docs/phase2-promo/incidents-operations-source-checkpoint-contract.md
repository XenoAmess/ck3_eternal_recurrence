# Incidents/operations source checkpoint contract

Status: **static-ready-live-pending**. This contract does not claim a live
gameplay result.

## Authoritative binding

The `phase2_incidents_operations` span starts from `zg361.50`. Its scripted
event trigger requires the event root (`this`) to equal
`scope:zg361_notice_prompt_subject`, while
`var:zg361_result_case_owner` must equal
`scope:zg361_notice_prompt_owner`. The delivery effect saves its current
recipient as `zg361_notice_prompt_subject`, saves the case owner separately as
`zg361_notice_prompt_owner`, and then schedules `zg361.50`.

Therefore the canonical received-self checkpoint has this identity:

- `player_character_id` is the played recipient and the `zg361.50` event root.
- `owner_character_id` is the saved notice/case owner queried by the Incident
  provider.
- Both IDs are positive and `owner_character_id != player_character_id`.

An Incident checkpoint with `owner_character_id == player_character_id` is
rejected as `incident_checkpoint_owner_equals_player`. This is a source-route
binding check, not a relaxation of the provider ACL.

The executable semantics are in
`mod_zhongguo_style/events/zg361_events.txt` (`zg361.50`) and
`mod_zhongguo_style/common/scripted_effects/zg361_effects.txt`
(`zg361_grade_325_apply_effect`).

## Runner route and GREEN boundary

The canonical source-checkpoint provider restores the exact registered bytes
and identities without fixture, console, or generic character rebinding. The
Incident gameplay cell then:

1. queries the exact `zg361.50` event context and verifies player/root plus the
   saved distinct owner;
2. selects authored option 1 and observes the old event instance disappear;
3. queries the Incident provider for the X/Y/Z terminal and KPI matrix; and
4. queries a deliberately wrong owner and requires typed
   `owner_filter_mismatch` with no leaked owner tuple.

An input ACK or event disappearance alone is not GREEN. The action cell needs
the provider-observed postcondition and the explicit wrong-owner negative
control. The visible post-action choreography remains `zg361ip.190`,
`zg361ip.290`, then `zg361ip.390`.

## Required live checkpoint

The remaining live input is one real paused, map-ready `zg361.50` checkpoint
and bound receipt where:

- the event-context provider reports the exact event definition, live instance,
  shown/enabled option 1, root equal to the player, and saved notice owner equal
  to the distinct owner ID;
- checkpoint bytes, size, SHA-256, save lineage, date, player, and owner match
  the source registry and its provider/UI receipt; and
- the capture used neither fixture nor console staging.

The existing Incident-X full-entry artifact proves candidate loading through a
paused rendered map only. It does not prove this action or its X/Y/Z
provider-observed postcondition.
