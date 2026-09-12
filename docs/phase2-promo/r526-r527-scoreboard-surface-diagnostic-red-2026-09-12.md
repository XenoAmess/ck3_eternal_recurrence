# R526/R527 scoreboard surface diagnostic RED (2026-09-12)

## Verdict

R527 repeated `unavailable/state_projection_unavailable` after the bounded
0.25-second post-action render settle. This disproves the fixed delay as a
sufficient correction. The live frame nevertheless shows the scoreboard dark
backdrop and panel outline, so the accepted native callback did change the GUI.
The remaining blocker is identifying which canonical open-surface relation
failed; another delay increase or unchanged run is not justified.

P1 remains `9/9 GREEN`. P2 remains `0/8`; the 5.87 MB failed take has no clean
span. Edit, export, and publication remain gated.

## Rounds and result

- R526/PID `56948` completed authenticated Frontend warm-up and was terminated
  before R527.
- R527/PID `192328` was the only gameplay process. It loaded the isolated
  `autosave` on CK3 `1.19.0.6` with the unchanged R525 bridge DLL and the
  committed Python render-settle correction at root `57ed1395...7226`.
- The closed-state query was available at provider observation/revision `2/1`.
  The `open` action was accepted with `native_handled=true`; the single later
  query after 0.25 seconds remained `state_projection_unavailable`.
- The 3.00-second extracted frame visibly contains the scoreboard dimmer and
  panel structure. It is diagnostic only because the typed provider did not
  publish an available postcondition.
- Both R526 and R527 cleanup proofs are GREEN. The managed job tree is gone and
  CK3/FFmpeg inventory is empty.

## Minimal diagnostic correction

The native provider previously discarded decoded widgets and ACL whenever
tree/semantic canonicalization failed. It now copies the already decoded
first- or second-read state into the unavailable response before calling
`SetTopUnavailable`. That call still clears every readiness bit, preserves the
typed RED reason, and prevents provider observation/revision publication.

The formerly combined second-read branch is split only enough to retain the
existing precise reason vocabulary:

- GUI lookup failure: `gui_root_unavailable`;
- widget decode failure: `widget_state_unavailable`;
- ACL decode failure: `acl_inconsistent`;
- missing fixed instance: `widget_not_instantiated`;
- tree/semantic failure: `state_projection_unavailable`.

No field, enum, action, allowlist, pointer gate, fingerprint rule, provider
version, or success behavior changes. A native fixture proves that an invalid
neither-open-nor-closed surface preserves modal/entry visibility while all
readiness remains false. The strict Python consumer proves the same typed
diagnostics normalize without treating the response as available.

Focused validation:

- native scoreboard state executable: exit `0`, SHA-256
  `A71A15DBF5EEF6ABDF45B6086A7E0CD2D7182D5C2084A036D9C51C7B655B5962`;
- Python scoreboard state contract: `9 passed, 7 subtests passed` in `0.33s`;
- `git diff --check`: GREEN.

This unavailable-response semantic expansion requires a documentation-only
open_kaishek compatibility sync after the root commit is pushed. The next live
attempt requires a fresh DLL and exists only to read the retained surface state;
it must not be widened into a long capture retry.

## Evidence

- no-launch plan: `169A9C0BB71202E366149200FA4F9AD8C37497F99C68402A4D4A8100519E53AC`
- outer report: `68E61E5874DB00DDAAF2DE870752F850449C70B0A8201DCB3363933329464B54`
- inner report: `BE4A900E9245CF576BCDFC70473998F237BD408FD10F7933D9819D97296A9739`
- visual action cell: `54719C766A7D399E278AD9CE30F652E2556FDFB2A890C55242AF30247CB70E69`
- driver state: `6DB204502FD7CB6EC611AABCFD25D6F86976A7700AC89C4DBBFD6FF1C484F7FE`
- cleanup: `325318F5FD85EA35EA1525A9CF989C02AE89CBAF19FFECCA4A9C64A9F6449187`
- timeline: `BB8197531EFBC28944A477D1CE4D9D6D4919AFA525FB4028CDC4A28E71E2BC98`
- failed MKV: `774A04F981A5C4F72F8E0C3B2F84C642A7C1863545932D178C60211C6D12E498`
- extracted 3.00-second frame: `DB5CC3A55CC0D64E89C5B01D0759C9E2BB823DC636141B6E87B6949D3B34CDDC`

