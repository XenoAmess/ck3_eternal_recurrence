# Cross-cycle endgame owner/subject seam

Status: `static-ready-live-pending` (2026-09-04). This package did not launch
CK3 and does not claim a paused live artifact.

## Why the seam exists

The visible product events `zg361we.356`, `zg361we.360`, and `zg361we.361`
are owned by the celestial-liege player. The existing
`query_zhongguo_workforce_collective_snapshot_v1` provider has a stricter,
received-self ACL: it reads the played character as the case subject and only
accepts the supplied owner CharacterID as an equality filter. Therefore an
owner-side event query and a subject-side Workforce query cannot honestly be
joined in one unchanged-player frame.

`tools/zg361_phase2_cross_cycle_endgame_live_seam.py` closes the orchestration
gap without adding a generic character switch or variable reader:

1. From the hash-bound owner-facing `zg361we.356`, select option 1.
2. Advance the real product timeline at speed 1 within a bounded date window.
   Any other visible event, owner drift, or date escape is typed RED. This is
   the real M357-M359 progression; the fixture does not synthesize its state.
3. Query the exact owner-facing `zg361we.360`, cross-check the saved owner and
   subject scopes, then select option 3 (route C).
4. Query the exact owner-facing `zg361we.361` and materialize a checkpoint.
   The on-disk bytes and SHA-256 are checked before it becomes the result
   binding.
5. The runner integration seam installs only
   `tools/fixtures/zg361_phase2_cross_cycle_endgame_rebind` and reloads that
   exact checkpoint. The seam re-queries `zg361we.361`; the lifecycle callback
   receipt alone is insufficient.
6. Select the real `zg361we.361` option 1. The queued one-option fixture card
   saves the exact owner and the subject derived from the product's
   `zg361_p2c_m360_source_subject`, then performs the fixed owner-to-subject
   transition.
7. A later paused native snapshot must expose the subject CharacterID at the
   same date. Only then does the existing Workforce provider prove the same
   owner/subject/cycle/case, M360 choice 3, carried debt due next cycle, and
   ready-or-consumed M361 charter.

ACK-only evidence and `zg361we.361` visibility are deliberately non-terminal.
GREEN requires the subject-side provider fields. A wrong owner, wrong subject,
checkpoint hash/lineage drift, exact-build drift, or any declaration that a
generic rebind was used produces typed RED.

## Exact-build and fixture boundary

The seam is frozen to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The acceptance fixture writes only its own one-shot character flags. It has no
decision, no product-state mutation, no arbitrary target parameter, and no
variable-query surface. Its scripted GUI can summon the card only when the
owner's consumed central source points to a live AL state-5 subject with the
route-C receipt/debt and a ready three-cycle M361 charter.

The fixture contains seven small purpose-specific files and one event. This
respects the project file-boundary rule; no product effect shard was changed.

## Formal runner integration point

The formal Phase2 runner now assigns `capture_cross_cycle_endgame` to
`_Phase2CrossCycleEndgameSpanDriver`; the generic visual event adapter no
longer owns that handler. The integration in
`_make_default_phase2_promo_span_driver` does the following:

- consumes only the already registered `zg361we.356` source restore cached by
  the source choreographer. The registry provider reads an absolute save,
  verifies its size/SHA-256, real-CK3 receipt, owner, date and seed lineage;
  this path cannot create or mutate a source checkpoint;
- calls `run_exact_build_cross_cycle_endgame_seam` rather than the old generic
  `advance_to_result`/event-visibility verifier;
- supply a lifecycle-only `activate_result_session(result_binding)` callback
  that installs the named fixture into the isolated userdir and restores the
  checkpoint named by the result binding;
- preserve the source checkpoint's `save_lineage_id` and return a restore
  receipt containing exact build, checkpoint SHA, owner, subject, date, and
  fixture identity;
- require the subject-side Workforce provider postcondition, then disable the
  fixture and restore the hash-identical owner-visible `zg361we.361` result so
  the recorder's clean hold remains a real product surface;
- admit exactly two managed restore generations inside this one span. The
  span-session contract checks the exact handler, result checkpoint hash,
  seed lineage, start/end PID generations, typed fixture and provider proof;
  a generic rebind, console use, business-state fixture or ACK-only result is
  still RED.

The runner writes `phase2_cross_cycle_endgame_runner_cell.json` beside the
other capture evidence. Its readiness label remains
`static-ready-live-pending`: formal wiring does not become live evidence until
the user-supplied source registry contains a qualifying real checkpoint and a
paused run captures the final provider artifact.

The live gate remains open until a real `zg361we.356` source checkpoint, a
real owner-visible `zg361we.361` result checkpoint/restore, and the same-lineage
subject Workforce provider artifact all pass this seam.

## Real `zg361we.356` source capture entry

The formal runner also exposes an explicit capture-only mode for the missing
fourth source entry. It mounts only the product, starts the managed session,
and waits without timeline input for the expected owner/date frame. Once
`zg361we.356` is visible, it requires the played character and root/saved owner
scope to equal the requested owner, a distinct saved subject, the saved
cycle/case scopes, and exactly three shown/enabled options in native order.
It then performs only `save-checkpoint`, re-queries the same event binding, and
checks the materialized bytes/SHA-256 before emitting any GREEN receipt.

The input is a schema-2 `LIVE_PENDING` manifest with exactly the first three
canonical source entries, including the Incident strict receipt. Its seed,
exact game/EXE, product tree, enabled-mod set, and product-only capture lineage
must match the running session. A successful capture writes:

- `endgame-source-receipt.json` with the owner/date/subject/event surface and
  native save receipt;
- `phase2-source-checkpoint-capture-manifest.json` with all four real entries;
- `phase2-source-checkpoint-registry.json` plus its content-addressed archived
  checkpoints, assembled by the existing schema-2 registry builder.

The capture result deliberately remains `readiness: live-pending` and never
claims Phase2/gameplay completion. It uses no console, fixture, arbitrary
rebind, option selection, or ACK as state evidence.

Read-only prefix preflight (does not launch CK3):

```powershell
py tools/preflight_zg361_phase2_cross_cycle_endgame_source_capture.py `
  --prefix <three-entry-live-pending-manifest.json> `
  --expected-seed-lineage-id <zg361-phase2-seed-sha>
```

Explicit live invocation (the owner and date must be known checkpoint
bindings, not values inferred after launch):

```powershell
py tools/run_zhongguo_acceptance.py `
  --phase2-endgame-source-capture-live `
  --phase2-endgame-source-capture-prefix <three-entry-manifest.json> `
  --phase2-endgame-source-owner-character-id <character-id> `
  --phase2-endgame-source-date-raw <date-raw> `
  --phase2-seed-contract <ready-seed-contract.json> `
  --artifacts-dir <new-artifact-directory>
```

Run the offline audit without launching CK3:

```powershell
py tools/preflight_zg361_phase2_cross_cycle_endgame_rebind.py
py -m unittest tools.test_zg361_phase2_cross_cycle_endgame_live_seam
py tools/test_zg361_phase2_cross_cycle_endgame_source_capture.py
```
