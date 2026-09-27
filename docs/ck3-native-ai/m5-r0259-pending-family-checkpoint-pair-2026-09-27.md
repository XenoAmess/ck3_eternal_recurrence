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

## R0260 matched live continuation and remaining observation gap

C196 paired the original R0259 h2513/raw 53216784 save, driver, pending sidecar
and formal proposal report using the corrected official `prepare-state`,
ordinary `xar_off` rebind and no-launch checks. The frozen candidate index is
`Z:\r196-family-h2513-cold16\C196-CANDIDATE-INDEX.json`, SHA-256
`0E31986ED8F1A830E151F6C98811CA4479C3F4B5CE98A8FA2346BD5A44162499`;
runtime source is `130a596672f8c20a841f1fc7bad25c0290964a56`, with native DLL
SHA-256 `78CD5317DAE08952FC9EF3FFE5C6EDCD2038F62F75C05E8250C1F30E9F8F1922`.
R0260 then completed 16/16 qualified turns under unique PID 162992. This is
the matching new-PID validation that C190 lacked: the initial pending ledger
survived the official pair, its original source PID 59384 remained recorded,
and no second typed proposal was sent. The formal report SHA-256 is
`EE8F77D74D6FFDB995F7ABE59004BC05CBEDB63CBEA9B90D55260DC51FDDE02D`.

The result reads at proposal days 6, 7, 8 and 9 all returned `pending` for
heir 38822 and candidate 38718. The last sidecar SHA-256
`DF1BE2ACA2986C7C31157944D1147FFEC1996EF914530E5DC066DF535398DB98`
still has `receipt_pending`, `resolved=null`, and
`cold_absent_relation_unresolved=true`. An absent bilateral relationship in
this cold path does not itself distinguish an interaction still waiting from
a refusal or invalidation. No acceptance, betrothal, marriage or alliance is
established by R0260. The latest formal checkpoint is h2543/raw 53216856,
save SHA-256 `544AA83BE26C82C1E735EFD57EBA6814A5C6FB9B71C8B680F2186A01F6DB1AC9`;
the next candidate needs an official pair for this exact later checkpoint
before any further live run. A read-only exact-build interaction outcome
observation is the next dependency for a definitive family result.
