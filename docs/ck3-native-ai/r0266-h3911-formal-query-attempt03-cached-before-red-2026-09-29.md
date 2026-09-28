# R0266 H3911 receiver attempt 03: compact BEFORE cash RED

This is a historical H3911 diagnostic, not a current Robert or M5 cash frame. All five war cash amounts, horizon and assumptions remain null; neither zero-fee approval registry is populated.

The separate attempt-02 no-launch preparation stopped at rebind because its newly chosen pipe differed from the frozen source driver's pipe. It launched no CK3 process. Attempt-03 used the source-bound pipe, independently rechecked the six H3911 assets and exact EXE, then passed receiver prepare/rebind and official no-launch preflight under #449 commit `d2a9c63e0856e3a25b7dec983b151b46ddb2679b`. Its derived driver SHA is `2F0E6C29BD0F500EC34A5B1DB9FE918B63D947C3166D748B156B0FE225698EA4`; ready summary SHA is `0D4D02534CF15A19FE5C0550053669E333ED2FDF89415AA3B4B0F4C2A4B94AE7`.

Fresh task-bus screen lease `r0266-h3911-formal-cash-20260929-a03` began at sequence 2123. Two random-code original screenshots had different pixels and hashes; a separate `desktop_steam_offline_recovery recover` moved the Steam window. The original second challenge and moved-window image visibly showed Steam `离线模式`. The Steam main content remained black. The manual review is frozen in `attempt-03/steam-offline-visual-review.json`; no Steam mode change was attempted.

The guarded one-turn run reached paused `native:3`, public revision 4/native revision 3, `date_raw=53219928`, player 29829 and sole WarID 16777231. The formal planner selected `query-war-termination-options-16777231` as a typed read-only query. The parsed request and accepted/available native envelope share request ID `step-3-a00a9e07d2d2`; query sequence is 1. Gameplay submissions and date advances are zero. The run returned code 1 after `1380.0657465999975` seconds because formal cash postcheck remained `same_paused_treasury_unproven`. Its cleanup proved the CK3 tree gone; screen release sequence 2211 was followed by an inspect showing no CK3, recorder or screen owner.

The new append-only diagnostic identifies the missing value: the **outer receiver BEFORE** has the six-field frame but lacks `played_character_gold` and top-level `active_wars`; the **outer AFTER** has Q100000 gold raw `120644281` and the sole war. The parsed inner query wire's BEFORE and AFTER both show that same gold raw and frame. These are cached semantic projections, not independent direct CK3 gold reads; the inner values cannot backfill the missing outer pre-query observation. A fee of zero, a transient debit/credit, and any deferred charge remain unproved. The passive topbar observer was never reached.

The source cause is `native_auto_run._wait_for_readiness`: it returns the compact readiness observation, which intentionally omits gold and top-level wars. The formal cash gate had used this compact object as `before`, while `after` came from the full receiver cached semantic projection. A follow-up code change takes a formal-only full cached semantic BEFORE before `service.auto_turn`, requires its six fields/paused/map-ready/typed gold/unique WarID to match readiness, and uses it only for the cash receipt and diagnostic. This is a receiver cache consistency fix; it does not force a native refresh or approve zero cost. A future attempt needs its own root, pin, no-launch and fresh screen evidence.

| Frozen artifact | SHA-256 |
| --- | --- |
| `attempt-03/formal-query-receipt/formal-query-attempt-diagnostic.json` | `F0FECE0DAD1B370CE1BA36AD91CDA6EA2E9EA8127FA5AE42860FE628F7374EF9` |
| `attempt-03/formal-query-receipt/formal-selected-query-receipt.json` | `C7166D890FDFF00DDFE3EA44DCB2E118D3AFA571249C907ADB5AC198D4E5E47D` |
| `attempt-03/formal-run-stdout.txt` | `8490A2F48F8EC3B8CE2E2099BA942EA5AF86EF816B3D962526C784339452B997` |
| `attempt-03/state/native-session/driver-state.json` | `A4833E91637EA05047B878B5138832B5FA5750D9EFBB89B1621F2325C6383FAF` |
| `attempt-03-independent-audit-cash-gui-owner-v1.json` | `DC78A5D9B527563701C41FC5CAC6DEDC25BD2B12A530CB97968C7025745458AC` |
| `attempt-03/screen-lease-exit.json` | `329274D3EF22F1422A4033D79EDCF173BF9E891910505FC03BFAF022D97873E2` |

All relative artifact paths in the table are under `D:/ck3-research-artifacts/r0266-h3911-formal-cash-20260929/`. This frozen attempt is not modified or retried in place.
