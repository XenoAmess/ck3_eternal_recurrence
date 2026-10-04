# Exact HEAD CI evidence

Commit: `3d3305e75cf642a7a82bef5f9aee03dc76b3c10e`. LYD product tree: `2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa`.

Both required push workflows and all their jobs completed successfully, attempt 1. This is static CI evidence; R6 native acceptance is pending.

- [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37200670917): run `37200670917`, job `111431527422`, `success`; {'success': 60, 'skipped': 20}.
- [Li Yu Dao static checks](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37200670823): run `37200670823`, job `111431526874`, `success`; {'success': 9}.

Official optional/manual/tagged release steps were skipped; their names remain in report.json. No retry, dispatch, cancellation or other CI mutation was performed.

See [report.json](report.json), [collection-receipts.json](collection-receipts.json), [INDEX.json](INDEX.json), `poll-001/`, `terminal-001/`, and exact workflow snapshots under `source/`.

Each `*.content.bin` preserves the exact UTF-8 encoding of the connector-returned structured content string without a trailing newline. The connector envelope and readable JSON are retained separately. Transport headers and HTTP wire bytes were unavailable.
