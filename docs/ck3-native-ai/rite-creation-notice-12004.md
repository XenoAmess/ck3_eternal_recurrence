# Rite creation announcement: exact 1.20.0.4 knowledge

## Plan and ownership

This package registers only stock `faith_creation.1021` knowledge and its source
index row for CK3 1.20.0.4 / Steam 25734779 / EXE SHA256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
It preserves earlier-build queries and adds no native provider, runtime rebuild,
campaign utility, general religion agent, or blanket first-shown-option policy.

The bounded contract covers the observed founder presentation: root and founder
are the player, seven saved scopes include `differing_tenet`, four authored
options yield shown native indices 0/1, and the selected source-reviewed choice
is native 0. Observer options are source documentation, without live or action
qualification. Unknown scope variants and altered effective definitions need
their own review.

Validation exercises the public knowledge/source query, detached JSON,
player materialization, exact founder scope/option checks and negative variants,
and preservation of prior builds and inherited source-index rows. The existing
source-migration test is adjusted for the explicit additive .4 row and run
with the new focused case. `open_kaishek` prevalidation is not applicable: these
changes register knowledge metadata and exercise Python projection contracts;
they do not evaluate CK3 effects or add a parser/IR/finite-runtime scenario.

## Evidence and limits

Observed on machine `bf-202609141645-5434332d4d`, 2026-10-15. Product evidence
remains in `ck3_mod_more_tenant_slots`, including the report
`artifacts/bugfix-20261015/queued-event-diagnosis/r20-001/report.json`
(2026-10-15T10:22:36.300398+00:00, SHA256
`4c0657fefcc57554616e95c4e52bc41d1bc40c0055e9ffdf6b3770e07a79c152`).
That report pins all original source, private-save and UI evidence. No private
save, raw UI image or product source is copied into this framework package.
The product's R20 acceptance documentation owns product business conclusions.

Stock event, Simplified Chinese locale, on-action and founder-widget files each
match the cached Steam depot 1158311 manifest 5078208590259867811 individual
file sizes and SHA1s. This is bounded cached-manifest corroboration, not online
validation or a full installation audit.

The original R20 receipts prove founder native 0 selection and independent
advancement `3 -> 2 -> 1 -> null` at date_raw 53144352. Instance numbers are
identities, not queue lengths. Generic saved Rite/Faith/Tenet identities remain
opaque in the native context; the offline saved scopes are separate evidence.
The frozen 007 runtime predates this registry addition and remains unchanged.
Registering knowledge here does not mean 007 served it, nor grant new execution,
material reward or product acceptance credit.

## Distinguishing queued announcements and repeated update messages

`on_rite_created` dispatches `faith_creation.1020`; the dispatcher saves the
created Rite and schedules `.1021` one day later. A save can already contain
multiple announcements. Each displayed occurrence must be identified through
the current event context, selected against its actual shown/native mapping,
and checked for independent advancement. Clearing a batch and subsequent time
observation are separate facts; newly appearing unrelated events are not proof
that the old event returned.

The event body reads saved `new_rite.GetName`, while the stock founder widget
reads `founder.GetRite`, the founder's current Rite. An older announcement can
therefore show an old name in its body and a newer Rite in its widget. The widget
does not prove the event's opaque saved new-Rite identity.

`msg_rite_updated` is a separate interface-message chain in `on_rite_updated`.
Its changed-tenet/doctrine messages must be sampled separately. Finite modal
queue drainage does not establish that recurring update messages were fixed.

## Validation result

Two focused compound cases passed on the same machine at
2026-10-15T11:05:00Z: the new exact founder/source contract case (0.200 s unittest,
0.547 s outer), and the affected source-migration case (0.183 s unittest,
0.848 s outer). Actual command/output receipts are committed under
`artifacts/enrichment-20261015/faith-creation1021-001/`:

- `test_faith_creation1021_12004.py.actual.json`, SHA256
  `efa53bb35d81eaf632bf158e97d80e5fcc440c8024b919b8b06d59b5157798fd`;
- `test_vanilla_event_migration_12004.py.actual.json`, SHA256
  `657d2a2f4f87cde521da5da613d9d6c50a81c9755b9f9e6a0eee45b5c54c6a3e`.

The current .4 source index has 194 rows; all 193 inherited rows and their .3
dataset remain unchanged. Public knowledge and source queries now find `.1021`.
The generic selection policy still returns
`registered_contract_requires_extended_consumer` with
`direct_projection_support:character_scopes=false`; no policy allowmap was
expanded. This preserves the distinction between readable source-bound knowledge
and an enabled generic actor. `git diff --check` passed. No game operation or
native/runtime rebuild is part of this package.
