# CK3 full exact / B7 evidence (2026-09-03)

Observer-only launches, no save/gameplay/store/payment actions. Steam CK3 1.19.0.6, matching EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

| Run | Source | Result |
| --- | --- | --- |
| `formal-phase2-full-exact-1800-20260903/report.json` | 264 files, 15,937,535 bytes; workforce source SHA `926453FE4B3621B5381743D61F5D03AC29C1D498181702E05A9532739D334D8A` | timeout at 1800 s after `Total of : 881`; no Frontend/history; error.log 0; WM_CLOSE, exit 1, `cleanup_proven=true`; report SHA `241254233107098CF5F385F1C4472D94CA3E1C8D93D6CFFF869A8C38C0F7A79A` |
| `formal-phase2-workforce-stub-B7-20260903/report.json` | New 264-file B7 tree SHA `b1f22c96cb1c35b85ec74511750b4c2d0fe380c00652a513579512a884ed457e`; no-op stubs for four largest m360 blocks, all 324 top-level symbols preserved | timeout at 300 s after `Total of : 881`; no Frontend/history; error.log 0; WM_CLOSE, exit 1, `cleanup_proven=true`; report SHA `79EFD09AD3C9D4C3AEB3A25157676B734517286D6D0AAAC9709ED2F46C857229` |

Both runs ended with CK3/injector/watchdog inventories empty. B7 was run only after the full exact parent cleanup; no 7200-second continuation was started after cancellation.
