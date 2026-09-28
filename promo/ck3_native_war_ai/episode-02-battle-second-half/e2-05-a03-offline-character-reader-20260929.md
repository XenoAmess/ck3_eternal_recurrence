# E2-05 a03 strict offline CharacterID reader candidate

Prepared 2026-09-29 CST. This is a no-screen research candidate for a **new,
separately pinned checkpoint**. It does not query a live character, validate a
combat event, identify a selector choice, or assert a day-27 outcome.

The entry point is [`e2_05_a03_character_status.py`](e2_05_a03_character_status.py).
The caller must independently supply the immutable save SHA-256, the native
save-checkpoint receipt SHA-256, its expected raw date, the corresponding
human-readable save date, the episode actor ID, target CharacterID, Rakaly
executable, and a fresh output directory. The reader requires:

- Rakaly CLI version `0.8.19`, executable SHA-256
  `E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D`;
- native receipt `CALL_COMPLETED`, accepted `save-checkpoint`, materialized
  `xar_checkpoint.ck3` bytes/size/date matching the caller's independent
  pins, actor ID, and CK3 exact-build SHA
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`;
- whole-file balanced Rakaly text, one top-level `date`, one top-level
  `living` database, one direct CharacterID child, and exactly one direct
  `alive_data` or `dead_data` block;
- for `dead_data`, one direct `date`, `reason` and positive `killer` scalar.
  Duplicates, nested shadows, missing fields, malformed syntax, changed
  source bytes or mismatched pins produce UNKNOWN/RED. Deaths without a killer
  remain UNKNOWN under this narrow contract.

The reader creates the output directory only if absent, retains the Rakaly
melted file, and writes an exclusive `report.json` on success or
`failure.json` after an attempted melt fails. `admission=false` and
`run_day27_admission=false` remain in successful reports: only
`status_proven_in_supplied_save=true` plus the explicit save date describe
the result. A new a03 d27 report requires its **own** fresh checkpoint,
receipt and independent SHA/date pins; d26 bytes must not be reused.

## Frozen d26 regression

The preserved a02 `last_save.ck3` is 52,882,306 bytes, SHA-256
`9D175355BC273EADCA630DF78FDE21F1E6AB0495518054E63A06B3F42952063C`.
Its native `e2-05-d26-before-save.json` receipt SHA-256 is
`AA56F56735C668D7B4E3A26A8C0E77FA679C9A9AC2FA75E5DC8223CCE5240049`;
receipt checkpoint SHA, size, actor `29829` and date_raw `53146848` match.
The final reader reran the pinned Rakaly against those raw bytes into fresh
external
`D:/ck3-research-artifacts/e2-05-a03-offline-reader-20260929-a06/`.
Its melted file is 81,787,801 bytes, SHA-256
`ADCF4A4ED9F784313D95C84CBE30F5026B7271C952C7E772B38211CE7D6D89D3`.
The report SHA-256 is
`B395C7F0ED0D61CBACEFEFA43BB1DECCAA95C812878E0CECD5ADF9E5C03D7CCF`.
It observes CharacterID `33437` **alive in the saved 1066.12.29 d26 state**.
This says nothing about d27 after the next combat fire.

A separate negative attempt using an earlier candidate handler pinned the same
d26 bytes and receipt but supplied `1066.12.30` as the required save date.
It exited `2`, reported
`admission=false` / `life_status=UNKNOWN`, and preserved the fresh external
`D:/ck3-research-artifacts/e2-05-a03-offline-reader-20260929-a04/failure.json`
(SHA-256
`9DD71BA89E4DE67353E4BE33EC6F3735B8FB0B4520AB3A28C0175AE5ABDDDFCA6`).
The failed attempt and melted text remain immutable.
Earlier successful a02/a03 reader development attempts are also retained
under their separate external directories; the a06 report is the final-code
reference.

[`test_e2_05_a03_character_status.py`](test_e2_05_a03_character_status.py)
contains eleven synthetic tests for valid alive/dead, duplicate life blocks,
both kinds, nested life/death-field shadows, missing/duplicate death fields,
duplicate target/database/date, malformed braces/quotes, unrelated same-ID
scopes, a fake receipt self-reporting its own SHA, and missing/wrongly typed
receipt fields. Normal Python and `-O` each passed 11/11.
