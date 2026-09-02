# Phase 2 producer-identity live terminal (2026-09-03)

## Frozen candidate

- Exact source commit: `f8500576823deb798dc756ad8469aa87cc732c77`.
- Clean source ZIP: `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260903\producer-freeze-f850057\source-f850057-clean.zip`, SHA-256 `1257F300528A5482AF7F71404829F134AB432563F6492CF8AC9922640D11840A`.
- Producer manifest SHA-256: `89919DEC9D4852BBD3143B36BCF43CB10A6903CFDA84213B441A8AF670BBA193`.
- Producer-only DLL SHA-256: `567B5C18DA5282539088273A23EDFB458529CF4B62C637BA5CD3F9E209C3DD3C`; injector SHA-256: `2FAE7AA325F448E26348CFC6C093D8C4349F09EC9F2F66937D99E551E6AC6CC4`.
- Native CMake, `src`, and `include` identities remained equal to `da43787`: `9f69130ed1d8c39255563ef16a4c2c04a6b0d3aa`, `51e60d72a4cd403ad804376b08b38e8fa6dd3ea7`, and `285d2d494382556b09c8e4637c018d70458efeba`.
- Action-aware legal tests (three focused cases), seed-capture normal and `-O` tests, and the no-launch acceptance gate were GREEN. The archive matched all 1,765 clean-source files.

## Unique live result

The only live used PID `67092` from `2026-09-02T16:32:32.376078+00:00` through `2026-09-02T16:37:55.817729+00:00`. It ended typed RED with reason `loader_terminal_missing_after_database_completion_publish`: the loader saw two database callbacks, ended on `CJominiLoadScreenDatabase`, observed the `0x3B9CFD7` publish edge, but saw no post-init entry and never reached Load Save/In Game/native readiness.

The private producer observer installed without failure and proved the D2/D7 seam is active:

| Field | Value |
|---|---:|
| `producer_0x3B9CFD2_entry_count` | 1,838 |
| `producer_0x3B9CFD7_entry_count` | 1,838 |
| `read_failure_count` | 0 |
| last task / callback | `0x1EC56F09410` / `0x1EC56F09410` |
| last callback slot2 RVA | `0x817C20` |
| last owner | `0x1EC50260E38` |
| last state transition | `1 -> 2` |
| last thread / QPC | `58188` / `531011198927` |

The last sample is the already identified `SPdxParallelForOverArray` range-worker callback, not loader callback `0x88B480`. Version 1 retains only the last sample, so it does not prove that all 1,838 publishes had that identity.

The v3 action-aware legal handler returned GREEN/no-modal with zero clicks and zero acceptances. It saved one preclassification screenshot, SHA-256 `2175453293A9975B456260AA369C63171ED08CCD7CAA4933C7624CC42477C6E6`. No click occurred, so there is no post-click screenshot or before/after acceptance marker pair. The screenshot captured content beyond a verified CK3 modal and remains local-only; only its hash is recorded here.

## Cleanup and evidence

Cleanup was GREEN: shutdown, cleanup proof, tree removal, empty job/global process inventory, driver close, runtime invariant, and source invariant all passed. CK3 and the injector were absent after the terminal.

Evidence root: `Z:\p2r-producer-f850057-artifacts`.

| Artifact | SHA-256 |
|---|---|
| `runner-report.json` | `06D8A4580A4056DC4F52C44F1B44AD05F426F223797A4ACC35AAB19B2B555CBD` |
| `00_phase2_native_session_start.json` | `0972BC784689662CADADC6CFA317309862BD7A007D055A451376DFEF59DA2B44` |
| `01_phase2_legal_consent.json` | `A501CC3515FBF57930BFA0EAA7E93AB94691824765158E3605A66A215BBCB417` |
| `09_phase2_native_session_cleanup.json` | `BADEC73BFB0050BD6D0ED6D5A2D019E85227ED82F003F194674461F63E864638` |
| `phase2-producer-identity-observer-v1-postprocess.json` | `7DDBB61DA34C05943224E7F3E98A9C678224C70E85618F0A12D82259426326B5` |
| `terminal-evidence-index.json` | `CFE6B15B72926E1D72F2D94C536904FF290AEEDB309C72D7CBC51FAF9C381459` |

No second live is allowed for this candidate. The next distinct seam is a capacity-bounded callback-slot2 RVA histogram at the same producer transaction, with an exact `0x88B480` selected counter and first/last selected task, callback, vptr, owner, state, thread, and QPC identity. That is sufficient to distinguish an absent loader task from a last-sample overwrite without repeating the version-1 observation.
