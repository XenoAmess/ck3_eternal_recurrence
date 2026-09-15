# User picture corpus v8 native r8

This is an append-only RED run against repository commit
`9fe76a3342ab2363c1139d759e0c3139ed155e65`. It introduced the MCP v3
reference-independent native-UV calibration, but the acceptance runner still
checked the v2 begin-stage field `readyForComplete` instead of the v3 field
`nextPhase = surface_complete`.

The v3 calibration itself succeeded: all four red/green/black/nine-marker
stages completed, the nine markers were isolated, and the affine fit had a
maximum reprojection error of `0.463543 px` against a predeclared `2.5 px`
bound. The recovered canonical-to-framebuffer map was approximately a
`167.46 px` square at `(807.58, 310.92)`, independent of the circular native
frame selected in this session.

Because the stale begin-stage check made the aggregate calibration result RED,
all seven framebuffer comparisons correctly failed closed and produced no
native crops. The seven large sources still completed Apply/Copy. Pictures 01,
03, 04, and 06 passed strict semantic sequence comparison; pictures 02, 05,
and 07 retained the already-known native Copy fractional-rotation
normalization mismatch.

Steam remained offline. The managed CK3 process was stopped and its process
tree was proven gone before the shared slot was released. `summary.json`
contains the compact reviewable receipt. The raw report remains local and is
identified by its byte count and SHA-256 in that summary.

Reproduction command:

```text
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile C:\Users\1\Documents\PARADO~1\CRUSAD~1 --state-dir D:\ck3_coa_picture_corpus_native_r8 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar-coa-picture-corpus-native-r8 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 300 --picture-corpus docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-budget-1024 --picture-crop-dir docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r8 --output docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r8\raw-report.json
```

r9 supersedes this run for actual UV-registered framebuffer comparisons; r8 is
retained to prove that the acceptance gate failed closed on a contract-version
mismatch.
