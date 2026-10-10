# R54 actual day 48 failure

The failure is `case-natural-day-0050`, the 48th one-day advance. Its original report row ran from `2026-10-10T21:37:23.249661+00:00` to `21:37:27.810143+00:00`, returned `ok: false`, and recorded:

`RuntimeError: campaign pause readback lost the complete same-owner frame`

Both `result` and `after_snapshot` are absent in that failed row. There is no native pause-frame payload in this row. The precise failing predicate remains UNKNOWN until the shared advance implementation and its available native evidence establish it.

The command was published once with queue exit 0 in `IN_PROCESS_PINNED_QUEUE_LIBRARY` mode. This ACK does not prove a completed day. The public case stopped before writing `case-natural-day-0050.actual-results.json` or submitting observation 0048 model/tree/final queries. The new keyed-query `completion_diagnostics` does not apply to this observed failure; it is not evidence that R53's keyed-query completion refusal recurred.

ROOT supplied report byte offset 8483050. The reader consumed only a 128KiB window starting at 8482922 and extracted the exact failed row, retaining window and row byte offsets, sizes and SHA-256. An earlier 64KiB tail attempt could not locate the row and exited 1; it produced no substitute row. Neither attempt read or hashed the whole native report.

ROOT observed complete observations 0 through 47. `FACTS.actual.json` predates the located failure row: its `failed_native_row: null` and pending status are superseded by `FAILED-DAY-0050.actual.json`. Its empty `last_complete_query_rows` is a projection-container omission, not an assertion that original observation 0047 files are empty or failed; those originals remain externally pinned. No new query credit derives from that empty projection.

ROOT separately observed public run exit 2 at 21:43:21.350249Z and verify exit 2 at 21:44:29.893985Z. Closure remains ROOT-owned. This packet grants no normal-close, expiry, final SAVE, cold reload, or Phase I GREEN credit. The readonly-plan optimization source attempt remains a separate unapplied candidate; no MAIN, game, SDK, bus, build or test action occurred here.
