# Sway read-only queries: omit unused transcript copies

2026-10-10 / ISO 2026-W41. Source candidate only, **AUTHORED_NOTRUN**.
This Python change follows the Person history candidate `e997280d`; it does
not change that candidate, native code, strategy, schemas or Sway ledgers.

Root's R0084 Native60 paused baseline completion query 003 took 54.961 seconds
and opinion query 004 took 54.890 seconds. These are observed end-to-end delays,
not a measurement assigning all elapsed time to Python history copying. Their
raw responses are retained under
`D:/codex-ck3-background-spill/g2-live-20261010-r85-retry02/managed-full-r85-native60restore01/operator/gameplay-responses/`.

Both production wrappers delegate to their existing private transports. Each
transport reads a snapshot to select the player, then calls the shared G2
reader, whose before and after snapshots validate the same paused frame.
Those three snapshots export and deep-copy the owned native command history
by default. No consumer at any of those positions reads command history:
the actor lookup uses `played_character`, and the shared reader uses the
existing semantic frame binding. The existing completion/opinion normalizers
use exact build, date, native revision and player/pair identity.

The scoped fix makes a shared snapshot helper prefer the existing finite
Driver reader only when explicitly requested. The shared G2 reader keeps
`include_native_command_history=True` by default. Only the completion and
opinion transports opt out for the actor and before/after snapshots. Drivers
which expose only the older `take_snapshot()` interface keep their existing
fallback behavior. Service wrappers, private permissions, native requests,
result bodies, frame validation, ledger updates and public snapshot defaults
remain the same. These private G2 reads do not append to Driver command
history before or after this change; no new history semantics are introduced.

The single new compound test is
`ck3_autonomous_player/tests/unit/test_sway_readonly_history_12004.py`.
It exercises both registered MCP tools through real Service and real
`NativeHeadlessGameplayDriver`, with synthetic endpoint/paused contexts and
two unchanged retained production native packets. Each packet retains its
own actor, target, date and native revision; they are not relabeled as one
native transaction. The opinion fixture's prior original-instance ledger is
explicitly synthetic. Request nonce correlation is the only native packet
alteration.

The compound checks native output preservation, existing durable completion
and named-material staging, stale and changed-frame rejection, zero full
history exports/copies during the two targeted reads, unchanged default G2
history export, detached explicit public export and normal close persistence
of the complete retained transcript. Native producer and prior test reruns
are zero. Root supplies `CK3_SWAY_READONLY_COMPLETION_PACKET` and
`CK3_SWAY_READONLY_OPINION_PACKET` and owns the first execution.

Retained native inputs:

- Completion: `C:/codex-ck3-background/migration4-entry-live-fix/terminal-first-r21-20261007T100447118106Z-6a52f7fc/native/terminated.json`.
  Its original native/consumer GREEN is documented in
  [retained-row qualification](sway-terminal-retained-row-12004.md).
- Opinion: `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/affected-domain-first03/sway/native/outcome_opinion.json`.
  Original producer was GREEN; registered directory-only retry04 completed
  qualification. Their failed attempts remain retained, as recorded in the
  [October 7 report](../autonomous-agent-progress/daily/2026-10-07.md).

No source import, test, build, SDK, game, process/window control or EXE read/hash
was performed by this source lane. Live improvement and its magnitude remain
unmeasured. G2 stays 5/8, NW2 2/4; this candidate grants no game days, save,
terminal cause, natural inheritance or new capability completion credit.
