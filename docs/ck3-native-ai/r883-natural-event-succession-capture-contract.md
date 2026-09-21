# R883 natural event and succession capture contract

Status: **production code ready; natural production evidence pending**.  This
contract is bound to the already launched R883/R0014 ordinary continuation.  It
does not authorize another CK3 process, a forced event, an artificial death, or
a dedicated permanent long run.

## Frozen entry and evidence boundary

R883 is using the R878 runnable-preview combination:

- agent/source commit `7d215435da2b616a228024ac8161ae493f5477ce`;
- native source commit `8adbf94091c80900a0efadcc6fdff7802dd7c732`;
- CK3 `1.19.0.6`, executable SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`;
- standard feudal, `xar_off`, `ordinary_campaign_succession`, no pact;
- only `mod/xar_autoplayer.mod` in the frozen load order.

The exact R883/R0014 launch is PID `133824`, production entry
`g2_preview_operator.py run -> native_auto_run`, output
`C:\b\g2-preview-ordinary-7d215435-r878-extracted\runs\r883-war-continuation`,
state root `C:\b\g2-preview-ordinary-7d215435-r878-state`, `200` formal turns,
`810` seconds operator timeout and `720` seconds readiness timeout.  Its stop
conditions remain formal terminal, RED, turn limit, or the existing operator
timeout.  Event and succession capture is opportunistic inside that frozen
window and must not change the launch arguments or keep the process alive.

R883 cold-starts from the R882 paired checkpoint:

| Item | Frozen value |
| --- | --- |
| Game checkpoint | `D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-7d215435-r878-qualification\final-pair-r882\xar_checkpoint.ck3` |
| Checkpoint SHA-256 | `C4E665F8086D135180F9BCF5420CA0513570C4609C2181586E0FD50F90F484CA` |
| Driver state | `D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-7d215435-r878-qualification\final-pair-r882\driver-state.json` |
| Driver SHA-256 | `845AD53680B165E636EF0F351C88C52AE7E628B13873EF1B1E2D647F5F7A3CC6` |
| Played character / episode | `31853` / `native-31853-af642d76cb41` |
| Health | `284502 / 100000` |
| Initial expected successor | `36403` |
| Initial title expectation | titles `524`, `525`, `530` all to `36403`; `single_successor` |
| Prior unconfirmed action | `null` |

The R882 expectation is an immediately usable prefix, not a promise that the
same heir will survive until the ruler dies.  If normal gameplay changes an
heir or title before death, acceptance uses the last complete expectation
persisted while the predecessor was alive and retains the transition from the
R882 starting value.  It must never substitute a later reconstructed guess.

No production implementation gap was found for the named events or ordinary
succession.  The exact event query, registry recommendation, typed option
action, stress material comparator, next-turn consumption, per-title
expectation, successor reconciliation, reflected succession-modal Close and
successor checkpoint owner are already wired into the formal path.  R883 is
therefore the current executable evidence task; adding another harness would
not remove a live wait.

## R883 standard-feudal capture assertions

### Natural `death_management.1007`

Only a modal reached through ordinary date progression and the vanilla
`on_death` chain qualifies.  Console, forced/simulated event, fixture, manual
click, OCR or coordinate input invalidates natural provenance.  On appearance,
the same R883 formal owner must retain all of the following:

1. one paused query with exact key and positive event instance, player root,
   `new_memory`, a distinct `dead_character`, `deceased_character_stress`, one
   shown/enabled native option `0`, played CharacterID and pre-selection player
   stress;
2. a registry decision with status `recommended`, authored option 1/native
   index `0`, and a ready stress material expectation;
3. exactly one typed selection bound to that event instance and revision;
4. a later independent native frame where the old instance is absent, the same
   played CharacterID is alive, and `post_stress > pre_stress`;
5. one later normal formal turn which consumes the cleared state and does not
   select the old instance again; and
6. the ensuing paired checkpoint and driver state with the action identity in
   history.

`post_stress == pre_stress` is lifecycle-only `verified_no_change` and does not
close the material gate.  A reversed delta, missing stress, CharacterID drift,
killer/known-killer projection, missing `new_memory`, malformed scopes or a
submitted-but-unconfirmed action is RED and must preserve the paused scene.
The owner must query actual state before any retry.

### Natural played-ruler death and inheritance

The formal owner must keep the last living-predecessor succession expectation
before CK3 changes the played character.  A qualifying transition requires:

1. a naturally observed `played_character_changed`, with no command, restart,
   manual selection or new seeded episode used to choose the successor;
2. distinct predecessor/successor CharacterIDs and episode runs, with actual
   successor and every predecessor title compared to that frozen expectation;
3. reconciliation `successor_match=true`, `title_distribution_match=true` and
   verdict `matched`;
4. either an independently clear timeline blocker, or exactly one typed
   reflected Close for `death_succession_modal` followed by an independent
   query showing identity `none`, both succession predicates false, and formal
   date increase;
5. at least one real successor gameplay turn after the modal is clear; and
6. a physical paired successor checkpoint retaining the high-level goal and
   all effective predecessor action receipts.

If the expected heir changes before death, a complete later living-frame
expectation is valid and the R882-to-final expectation history must be kept.  A
different successor without a matching persisted expectation, title mismatch,
game-over/select-destiny/unknown blocker, or unconfirmed Close is RED.  An
unrelated later episode or manually selected character cannot substitute for
same-campaign inheritance.

The later cold-restore proof is a distinct new-process round: restore this exact
successor pair, check the effective action receipts before choosing any retry,
continue the same high-level goal, and show no repeated predecessor action.
It must not be claimed from an in-process reload.

## `tgp_travel_events.0030` is not an R883 target

The exact event requires TGP plus `celestial_government`.  R883 is standard
feudal, so `.0030` cannot naturally occur in this run.  A forced feudal event
would be development evidence only and must not be used to close G2-M2.

Capture `.0030` only when an independently required, naturally eligible
celestial/TGP production campaign already exists.  Reuse its normal bounded
slice; do not start a permanent event-specific long run.  A nearby paired
checkpoint may use the existing six-turn/1200-second/readiness-300-second
slice; otherwise use at most the existing 40-turn/7200-second/readiness-300-
second campaign slice.  A bound reached without the event is
`evidence_not_observed`, not GREEN and not RED.

The qualifying chain is natural travel movement provenance; exact player root,
`travel_plan` and `poem_province` scopes; two shown/enabled options; positive
pre-stress; registry authored option 2/native index `1`; exactly one typed
selection; independent old-instance disappearance with the same CharacterID
and `post_stress < pre_stress`; one later formal turn without repetition; and a
paired checkpoint.  Equality is lifecycle-only evidence.  Do not change
government, force the event, or relabel R883.

## Result classes and durable locations

R883 writes its formal report to
`C:\b\g2-preview-ordinary-7d215435-r878-extracted\runs\r883-war-continuation\formal-report.txt`.
Its live pair is
`C:\b\g2-preview-ordinary-7d215435-r878-state\profile\save games\xar_checkpoint.ck3`
and
`C:\b\g2-preview-ordinary-7d215435-r878-state\native-session\driver-state.json`.
On process cleanup, copy any qualifying final pair and operator receipt into a
new immutable directory under `D:\ck3_mod_rewrite_process_assets\`; record
their SHA-256 values and the R883 report hash.  Do not overwrite the frozen R882
pair.

- Target natural loop complete: retain query -> recommendation -> typed action
  or transition -> independent result -> later formal consumption -> pair.
- Window completes without a target: record `evidence_not_observed`, retain the
  valid continuation checkpoint, and continue the already authorized campaign
  later.  This is neither capability GREEN nor RED.
- Contract/action/result drift: preserve RED, the last safe pair and the paused
  evidence; fix and short-retest before resuming from a compatible checkpoint.
- Readiness/timeout before execution: report readiness RED or timeout
  separately; do not infer an event or inheritance result.

This contract does not update the authoritative G2 file.  Until both named
natural event loops meet their material assertions, G2-M2 remains in progress;
until a natural ruler death, reconciliation, successor gameplay and cold
restore all complete, G2-M3 remains in progress.
