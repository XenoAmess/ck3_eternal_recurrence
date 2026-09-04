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

## Deterministic capture and execution seam

`tools/zg361_phase2_incident_checkpoint_seam.py` is the narrow integration
point. `capture_current_received_self_incident_checkpoint_v1` accepts only an
already visible paused/map-ready `zg361.50`; it performs the native event-window
query, proves option 1 and the received-self identities, invokes the native
checkpoint save, re-reads the same frame, and freezes the exact bytes under a
content-addressed filename. It never advances gameplay or creates the event.

The durable receipt contains the raw provider/UI query, all three same-frame
snapshot bindings, the native save materialization, player/subject/owner/date,
checkpoint bytes and SHA-256, and the exact seed/capture lineage. Loose legacy
receipts are rejected. A receipt-aware no-launch preflight must also receive
the expected seed lineage ID; self-declared lineage is insufficient.

`run_received_self_incident_checkpoint_action_cell` is the later live runner
seam. It restores only those exact bytes with fixture, console, and generic
rebind all disabled; re-observes the exact `zg361.50` provider/UI state after
the clean restart; then delegates to the existing Incident action cell. GREEN
requires that cell's X/Y/Z terminal/KPI matrix and its typed wrong-owner ACL
denial. Restore ACK or option ACK alone cannot satisfy the seam.

The formal Phase2 source-checkpoint registry now uses schema 2. Its Incident
entry must contain a `received_self_incident_checkpoint_receipt` locator. The
registry assembler first validates the complete strict receipt, requires its
checkpoint path/bytes/SHA-256, lineage, date, player/subject and distinct owner
to equal the Incident capture-manifest row, then copies the checkpoint and a
path-normalized receipt into the registry archive. The runner provider opens
and revalidates that archived receipt before recording. Its final preflight
also requires the receipt player to equal the paused runtime player and the
receipt owner to equal the seed's `incident_owner_character_id`. A loose
provider/UI GREEN receipt remains necessary for the common four-span registry
shape but is not sufficient for Incident.

This connects the strict capture seam to the production eight-span route
without changing the action semantics: `capture_incidents_operations` still
runs the existing Incident X/Y/Z gameplay cell, whose GREEN includes the
provider-observed terminal/KPI matrix and the explicit wrong-owner
`owner_filter_mismatch` negative control. Neither restore ACK nor action ACK is
accepted as result evidence.

No receipt or action artifact was produced while implementing this plumbing,
so readiness remains **static-ready-live-pending** until a real capture and
live action run are retained.
