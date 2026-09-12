# R524/R525 scoreboard post-action projection RED (2026-09-12)

## Verdict

R525 closes the preceding scoreboard-root blocker. The exact-build provider
resolved all 15 fixed widget identities and published a valid closed-state
observation. Native `open` dispatch was accepted and returned an exact ACK, but
the immediately following independent query returned
`unavailable/state_projection_unavailable`. R525 alone could not distinguish a
show/hide transition frame from another semantic-projection mismatch. The
failed take contains no clean span; P2 remains `0/8`.

This is a capability RED with loader, harness, and lifecycle GREEN. It is not a
product scoreboard-content failure and it does not justify loosening the native
semantic invariants.

## Rounds and lifecycle

- R524/PID `11456` completed the authenticated Frontend warm-up and was fully
  terminated before R525.
- R525/PID `107576` was the only gameplay instance. It loaded the isolated
  `autosave` under CK3 `1.19.0.6`, with bridge DLL
  `B25CF9A7814CE5C95702B86C79BBAAE2E5F9647888BA7DCD44BB3658A5FA1F52`.
- Cleanup is GREEN. R524 and R525 are terminated, and the final CK3/FFmpeg
  inventory is empty.
- No desktop click or keyboard input was used. The action used the typed native
  dispatcher, so the desktop coordinate-map contract was not involved.

## Observed transition

The source query was `available` on paused native revision `4`, public revision
`5`, date `53147016`, player `29037`, provider session
`161B0FB6A2D828BAAB2336D2F10DAE31`. It found all 15 widgets and published
observation/revision `2/1`, tree fingerprint
`1B584B44C40CD0739123F6613F2ACD030C8A2A2705A3E00B35D77B6C30A1EF96`,
and semantic fingerprint
`E02FB23FDA0C63BB1328A00C08A74492970A76AB05E95473D6F7DAC66D62FECD`.
The closed surface had the received entry effectively visible and the modal,
panel, tabs, and pages effectively hidden.

The `open` request targeted `zg361_scoreboard_entry_received` at
`0x1C084C4A2C0` under window `0x1C03BCC04E0`. The bridge returned
`accepted=true`, `native_handled=true`, and
`acknowledged_verification_pending`. The next query was issued immediately and
failed native semantic projection before a new observation could be published.

The product GUI applies `Animation_ShowHide_Quick` to both the entry container
and modal. Exact-build source defines its fade-in and fade-out duration as
`0.15` seconds. Sampling immediately after the synchronous callback can see a
transition frame that satisfies neither the closed-state nor open-state
mutual-exclusion invariant. This was the bounded hypothesis carried into R527,
not a completed root-cause claim. The recorder stopped at the RED almost
immediately; the 2.90-second frame still shows the pre-render surface and cannot
disprove the ACK.

## Minimal correction and validation

`zhongguo_scoreboard_action_cell.py` now waits `0.25` seconds after an accepted
native action before its existing single independent later query. This covers
the exact 0.15-second animation with a small render margin. Rejected actions do
not wait. The change adds no retry loop, changes no MCP/schema/evidence fields,
and does not relax native provider or postcondition checks.

Focused validation:

- `py_compile` on the changed action cell: GREEN.
- `test_zhongguo_scoreboard_action_v1_bridge.py`: `7 passed` in `2.72s`.
- The initial system Python pytest command failed because that interpreter does
  not contain pytest; the repository virtual environment then ran the intended
  focused test successfully.

Because this is only internal verifier timing, it does not trigger an
open_kaishek compatibility change. The next and only proportionate live check is
a fresh R526 Frontend warm-up followed by R527 gameplay using the same native
DLL and the committed Python correction.

R527 performed that check and returned the same RED after the 0.25-second wait.
The fixed-delay hypothesis is therefore insufficient. See
`r526-r527-scoreboard-surface-diagnostic-red-2026-09-12.md` for the replacement
diagnostic plan; no longer wait or retry loop is proposed.

## Evidence

- plan: `capture-plan.json`, SHA-256
  `E528D590BD6DBF93C8DF8C19A7D710DE8A78851A4E16DD270299CF475822B863`
- outer report: SHA-256
  `5B022DF5D2DC53AA0ED0DD9E27209F72295A07DCF4BCC2F95CADF9BA8CC11892`
- inner report: SHA-256
  `E909311D0059E018FDA567A4022D233062BEBFADBB21727703ABE204E39C49C1`
- visual action cell: SHA-256
  `2B8C437BAB05DCD3D4028C2A3C99D5782A6DE9B57EDDBA2C7AF39262130D9CD4`
- driver state: SHA-256
  `6C621FBD7ECD411E5D44D4B70D1F2711B60D22EF67F960038A52139576D3A282`
- cleanup: SHA-256
  `F4DC0BF55A47717E8EA1387BF12CD5129BC9FE999D2695E6495B981A7E9F2D7E`
- timeline: SHA-256
  `124A3203BDC85CE35029F84057EA835E30EFBECF695B2309AB5B6DDED68CEEAA`
- failed MKV: SHA-256
  `727F3CB58F5D827A5744A26A6897D6CD57D355410C345295B3FE1251DF358DC1`
- 2.90-second diagnostic frame: SHA-256
  `7CA43D546CA6387110114FE62293A6232D3B9BB26D4C6F9A35EF34D42738FEA4`
