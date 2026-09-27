# R0260 pending proposal across two formal runs

R0259 submitted one typed first-heir marriage proposal for heir 38822,
candidate 38718 and recipient 32897. Its last saved checkpoint was
h2513/raw 53216784, SHA-256
`96697f0b19280e20723eed05163a60a7a84befaab6da77a0d37e9097c5afde6c`.
R0260 resumed that exact checkpoint in a new PID, submitted no second
proposal, read `pending` four times, and saved h2543/raw 53216856, SHA-256
`544aa83be26c82c1e735efd57eba6814a5c6fb9b71c8b680f2186a01f6db1ac9`.
The actor 29829 and episode `native-29829-2bc2d599f7f9` match. The raw
source files and hashes are indexed in
`Z:\r0260-h2543-family-pending-freeze-20260927\PAIR-IDENTITY.json`.

The C191 single-report pairing gate correctly admitted h2513, but the
original R0259 report cannot reach h2543 and the R0260 report has no original
typed submission. An official C199 `prepare-state` attempt with the R0260
report stopped before rebind with `family pending identity disagrees with
paired save`. The failing command output is
`Z:\c199-family-h2543-pair\evidence\prepare-original.log`.

The corrected gate accepts ordered `--family-proof-report` arguments. The
first report must prove the saved typed submission. Each later report must
start from the previous report's saved SHA, history index and game date, use a
new bridge PID for the same actor and episode, submit no duplicate proposal,
and show an unresolved result query before its paired checkpoint. Its last
checkpoint must match the paired save and driver. A refusal, material result,
broken chain or older save remains inadmissible. The existing single-report
command remains supported.

The C199 patched official `prepare-state` completed the rebind and ordinary
no-launch preflight with `family_pending_sidecar.status=paired_no_launch` for
h2543; see `Z:\c199-family-h2543-pair\evidence\prepare-patched.log`.
This validates the recovery pair, not marriage acceptance or alliance. R0260
still returned `pending` at proposal day nine, and the current cold result
reader cannot distinguish an absent bilateral relation from a refusal that
was not captured before restart. No new CK3 run was made for C199.
