# Sway pending ACK checkpoint pairing (2026-09-29)

The R0339 H3924 action returned a native `submitted_verification_pending` ACK for
actor 29829 and target 32716. Its receipt remained RED. R0340 cold read did not
resolve the material postcondition. The saved game has a new matching Sway row,
but the formal ledger must remain `receipt_pending` until the independent
receipt/recovery contract can prove the outcome. Neither ACK nor the saved row
alone permits changing the ledger to `resolved` or submitting Sway again.

The current paired source is
`Z:\m6swayh3922pr545formal-live-20260929\state`:

| Asset | SHA-256 |
| --- | --- |
| `profile\save games\xar_checkpoint.ck3` | `4BBB0615DEC505E9759E936950754EAA40D634E8A75D63C3C615FDF97C71ECB0` |
| `native-session\driver-state.json` | `1E71F7184B6BBA00CCD47D00B99E395BD2F8664F03470CF20EF11AD5A690D9FB` |
| `active-scheme-sway-formal-private-v1.json` | `63539B6D63FE54B1217AF41D2A0182AF11137C3F3909D579E993928AD4CEE9FC` |

The driver `last_checkpoint` names actor 29829, episode
`native-29829-2bc2d599f7f9`, date raw 53219928, history index 3924 and the
same save hash and size. The ledger preserves action ID
`sway-9e297c964fd243839fedb26bf6c7ed1a`, target 32716, pending ACK and
`resolved=null`.

`tools/g2_preview_operator.py prepare-state` accepts the optional
`--sway-formal-sidecar` path, or finds the fixed filename in the flat
`--sample-dir`. Before preparing a state, it binds the pending ACK's
actor/target/action/date to the source save and driver's last checkpoint.
After the ordinary seed rebind it checks the copied save/driver again, then
copies the ledger byte for byte and records its SHA-256 in the preparation
receipt. It does not infer action success or alter the ledger.

The source `operator-manifest.json` still contains its earlier preparation
hashes. Build a **new** exact candidate and stage the three current source
files under a flat `sample-dir`; use that candidate's manifest for
`prepare-state`. Preserve the existing resolved family sidecar and Emma child
pending sidecar through their established flags and proof reports. Complete
the official no-launch preflight before using the unique CK3 instance. This
source change has no new CK3 live action or cold recovery evidence.
