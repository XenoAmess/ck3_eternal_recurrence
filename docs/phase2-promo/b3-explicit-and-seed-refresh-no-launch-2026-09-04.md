# B3 explicit-AND seed refresh: formal no-launch freeze

## Verdict

`READY_TO_RUN / NO_LAUNCH` at canonical
`9cd921674e192a118ea27c376fd41dfbb4bab327`.  The only authorized next CK3
session regenerates the canonical paused seed against the complete B3
explicit-AND product tree.  CK3 process inventory was zero before and after
both preflights; the live attempt, artifact, relay-result, stdout and stderr
paths were all absent when this freeze was signed.

The earlier direct promotion-source capture is `HOLD / NO_LAUNCH`.  Its exact
preflight failed before launch with
`current_product_tree_matches_seed_source`: the current seed binds product
tree `cdbcf82e...a98bd`, while this product is `d94c2d5...a35d`.  The gate was
not weakened.  A GREEN refreshed seed/contract is therefore a prerequisite
for `--phase2-promotion-source-checkpoint-live`.

## Frozen identity

- Clean source: `Z:\p2s10s`, detached at
  `9cd921674e192a118ea27c376fd41dfbb4bab327`; 2,735 files; logical tree
  `c5b2708fcf6a12c9c8bac71f6f5998069d17c61931e64668d8eb3cd2018f3477`.
- Checkout-byte ZIP: `Z:\p2s10.zip`, 83,535,513 bytes, SHA-256
  `2F36812A335BF403F85FF98B37406CB890039DDDA0129B4BE6D2BA4E380AD6E3`.
  The formal preflight proves exact path/byte equivalence to the Windows
  checkout; `git archive` is deliberately not used because it would restore
  LF blob bytes instead of the checked-out CRLF/BOM bytes.
- Product source:
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source`.
  The named projection contains 565 files / 21,607,199 bytes and materializes
  tree `d94c2d5d23e9ad254f4b20988fbf3c8e08408baa61070bd85f42b2d2fcbea35d`.
  Projection SHA-256 is
  `241DB7B5E2DF451AADBFAEB4570B083C8563239BC0158530682B9A77DA2F4ACD`.
- Default-OFF current native bridge: DLL SHA-256
  `BB10E12E0A166B9E405FE6E712F352D178377909EF5B672D3108E68A4001F4D7`;
  injector SHA-256
  `FBCD994CDE7934AC9B34D08551397CDBBB0677C038B098EADD9E183E3B7AC1C5`.
  Its schema-4 native freeze is
  `zhongguo_promotion_source_product_native_no_launch_candidate_1c69658_20260904.json`,
  SHA-256
  `E2AF344F3E72FEF018DBE51ADB3DC2960A8828179CBF0A4B079D1B31FC122911`,
  with 94/94 native tests GREEN.  The promotion-compensation private switch
  remains OFF because seed generation does not exercise that provider.
- Runner SHA-256:
  `D90A81ECE47EA5F58B8B449E89169C0426CDD2A4B4A2018D390C10120D4F6CAD`.
  Default-desktop relay SHA-256:
  `680532081C7B8A975A26A0432F9CDED8EDD1BE438FC3DE7B45C74BE18E1B80C3`.
- Input r9 seed contract SHA-256:
  `19B3451514FA4ED87836D03B5DEEB2D4AEC569A4714325E5C2164415E96563CC`.
  It supplies the previous real paused checkpoint only; this run must emit a
  new candidate and contract bound to the explicit-AND product tree.
- Full settings template SHA-256:
  `E04DDDC053E2850407DA6C40D044E241F355E5BB079D4608331789494E45E887`;
  its required 4,960-file warm shader cache is present.

The seed generator necessarily mounts its acceptance-only bootstrap fixture
alongside the exact product while creating the seed.  The product itself is
the unmodified explicit-AND tree above.  The fixture is not a promotion/live
product provider and must not be loaded by the later product-only source
capture.

## Formal no-launch evidence

- Seed runner preflight:
  `Z:\p2s10e\preflight.json`, SHA-256
  `B9E555D0578381520F08D1FFF6FAC7DD70E730CA1438B0BDAFB5AA1E21F31CC2`.
  Result is `GREEN / preflight-ready`; config, zero-CK3 inventory,
  source/archive equivalence, dependencies, bridge, all ten static gates,
  product+fixture projection, immutability, and final zero-CK3 inventory are
  GREEN.  The projected fixture tree is
  `64b8c4b06a4be6f8832cf11bd4b59f5ef92db04d10fc6ae18fe53f42a3563d35`.
- Default-desktop relay preflight:
  `Z:\p2s10f\relay-no-launch.json`, SHA-256
  `A2709CBBCC58B1CB1D8D5712AA9BAEAAD100022CA063E403DD1AB397A5F25C59`;
  result `READY_TO_RUN`, `child_process_started=false`,
  `ck3_launch_attempted=false`.
- Live attempt: `Z:\p2s10`; live artifacts: `Z:\p2s10a`; both absent.
- Fresh pipe token: `e6d07a19c5b84f32a17906d3be428c51`.
- Longest prospective mounted product path is 154 characters, strictly below
  the 250-character boundary.
- Preserved promotion HOLD log:
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3k-ps1-freeze-20260904T111500Z\formal-no-launch-preflight.txt`,
  SHA-256
  `BC7CB5349FAFB0FF6D0B58626673798DDC9503C82F446D1921144D6C79052E5D`.

## Single authorized live command

Run this command only while the CK3 serial slot is exclusive:

```powershell
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'Z:\p2s10s\tools\run_zg361_phase2_seed_capture_default_desktop.py' --python 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' --source-root 'Z:\p2s10s' --result 'Z:\p2s10f\default-desktop-live.json' --stdout-log 'Z:\p2s10f\live.stdout.log' --stderr-log 'Z:\p2s10f\live.stderr.log' --execute -- --attempt-dir 'Z:\p2s10' --artifacts-dir 'Z:\p2s10a' --pipe '\\.\pipe\xar_ck3_bridge_zg361_e6d07a19c5b84f32a17906d3be428c51' --clean-source 'Z:\p2s10s' --source-zip 'Z:\p2s10.zip' --git-sha '9cd921674e192a118ea27c376fd41dfbb4bab327' --game-dir 'Z:\SteamLibrary\steamapps\common\Crusader Kings III' --bridge-dll 'Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-product-native-default-candidate-cac1e85-20260904T104203Z\xar_ck3_bridge.dll' --injector 'Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-product-native-default-candidate-cac1e85-20260904T104203Z\xar_ck3_bridge_injector.exe' --seed-contract 'Z:\p2s10s\tools\zg361_phase2_seed_contract.json' --product-source 'Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source' --product-projection 'b3-r5-exact-trigger-explicit-and-4d3c284' --product-projection-manifest 'Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\projection.json' --profile-settings-template 'Z:\ck3_mod_rewrite\_runtime\formal-ab-current-buildoff-20260903\profile\pdx_settings.txt' --frontend-first-load-save-name 'phase2_seed' --frontend-first-timeout-seconds 300 --binding-timeout-seconds 420 --loader-timeout-seconds 420 --native-readiness-timeout-seconds 180 --event-timeout-seconds 300 --keyboard-watchdog-interval-seconds 5
```

A GREEN seed capture proves only a refreshed paused seed/contract and its
typed selectors against the exact product tree.  It does not prove the first
promotion source checkpoint, B3 gameplay, the complete source registry, full
Phase2, T0, or footage completion.
