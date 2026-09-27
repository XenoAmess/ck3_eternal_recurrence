# R0259 pending family proposal: pair the latest checkpoint

R0259 submitted one typed first-heir proposal for heir 38822 and candidate
38718 at raw 53216640. The first saved pending checkpoint is h2443, SHA-256
`6604a41ede9cdefbdba5a033d56287a871b0e864c04b69ea05da784c4d8ea268`.
The proposal remained `receipt_pending` during later read-only result queries.
The latest qualified source checkpoint is h2513/raw 53216784, SHA-256
`96697f0b19280e20723eed05163a60a7a84befaab6da77a0d37e9097c5afde6c`.
Both belong to actor 29829 and episode `native-29829-2bc2d599f7f9`.

The prior `family_pending_sidecar_pair` compared the latest save SHA/date to
the proposal's original pending checkpoint. C190's official `prepare-state`
therefore stopped with `family pending identity disagrees with paired save`
before creating a derived state or launching CK3. The source pair, sidecar and
formal report are frozen under
`Z:\r0259-h2513-family-pending-freeze-20260927`; the C190 failure result is
`Z:\r190-family-h2513-pending-attempt\C190-PAIRING-RESULT.json`.

The corrected pairing separately requires one saved submission checkpoint
matching the sidecar's date, actor, episode and candidate; exactly one typed
submit result; and one later report checkpoint matching the actual paired
save/driver SHA, date and history index. History index, date and turn index
must advance monotonically. A later paired checkpoint additionally needs the
last subsequent result query to remain `pending` or `accepted_pending` for the
same heir and candidate; both retain the pending ledger in the formal consumer.
The previous
same-checkpoint case remains valid. This is a no-launch recovery check: it
does not establish acceptance, a betrothal or a cold-restored live action.

Deterministic h2443→h2513-shaped unit cases cover both valid paths, missing
pending queries, a later refusal, duplicate typed submits and a mismatched save. The actual
frozen R0259 JSON files also pass the corrected pairing function read-only.
