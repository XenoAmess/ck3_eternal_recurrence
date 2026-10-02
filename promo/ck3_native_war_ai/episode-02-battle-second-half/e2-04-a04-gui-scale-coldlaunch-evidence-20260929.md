# E2-04 a04 GUI scale cold-launch evidence (read-only audit)

This note audits the isolated a04 profile and the checked-in launch path. It does not certify a usable recording frame or identify the sole writer of `pdx_settings.txt`.

## Observed sequence

| Phase | Evidence | Result |
| --- | --- | --- |
| Before warmup | `episode02-e2-04-d05-live-20260928-a04/ck3-output/gui-settings-prelaunch.json` and `gui-settings-before-native-session.json` | The new isolated `pdx_settings.txt` was 420 bytes, SHA-256 `146ED5F330EB59BCBA8D4D5FE6F03D9A497DED37C72457ABA812121426958257`, with `GUI.scale` value `1.0` and `version=1`. The before-session readback passed its disk gate at 2026-09-28 16:14:25.212529 UTC. |
| Warmup exit | `ck3-output/session.jsonl` and `gui-settings-before-final-launch.json` | Warmup PID 16208 started at 16:14:27.605929 UTC. After it exited, the profile was 6,861 bytes, SHA-256 `2191EA423B3B1A94CB7E905B6096F3D07BBF0B7F1668C3E0ED412297AEF2C509`, with `GUI.scale=1.3`, at 16:16:28.690889 UTC. The file mtime was `1790612114971432000` ns, equivalent to 16:15:14.971432 UTC, within warmup lifetime. |
| Before final launch | `gui-settings-warmup-reseed.json` and `gui-settings-after-reseed-before-final-launch.json` | The warmup's complete 6,861-byte file was preserved. After a one-value, same-directory atomic replacement, the file was still 6,861 bytes, SHA-256 `A45FF273C54C4D1D0819FC756F6E8B336411AB71E147F24E5BC462057309E541`, with `GUI.scale=1.0` and `version=1`. The successful disk readback was at 16:16:28.802117 UTC; mtime `1790612188755938000` ns was 16:16:28.755938 UTC. This was a disk-only result. |
| Final cold process | `ck3-output/session.jsonl` and `gui-settings-postmap.json` | Final PID 23124 was launched at 16:16:30.717549 UTC, after the reseed. The postmap receipt at 16:25:07.604443 UTC records the same profile as 6,861 bytes, `GUI.scale=1.3`, disk gate RED, and the warmup's exact SHA-256 `2191EA423B3B1A94CB7E905B6096F3D07BBF0B7F1668C3E0ED412297AEF2C509`. Its mtime `1790612216573873100` ns was 16:16:56.573873 UTC, 25.856324 seconds after final launch. The receipt does not identify the writing process. |

The post-final byte identity rules out a failure limited to the original 420-byte minimal formatting: the final launch path also returned a complete, naturally generated settings file whose only changed value was `GUI.scale` to its previous bytes. It does not distinguish a CK3 default/recommendation, an unobserved settings source, or behavior in the injected process.

## Launch-path boundary

In the Episode 2 branch, `promo/ck3_native_war_ai/integration/capture_session.py:29-30` puts this checkout's `ck3_autonomous_player/src` ahead of installed packages, and lines 894-909 pass `reseed_gui_scale_after_warmup` as the only before-final callback. `ck3_autonomous_player/src/xar_autoplayer/native_session.py:1139-1156` invokes that callback, records its success, then calls `launch` with the same profile and bound save. `ck3_autonomous_player/src/xar_autoplayer/runtime.py:2291-2300` forms a direct `ck3.exe -gdpr-compliant -userdir=<isolated profile> -loadsave=<checkpoint>` command. Its `launch` path at lines 2405-2473 and 2561-2620 clears selected runtime logs, creates the suspended process, binds the Job and resumes it; that reviewed path does not copy or regenerate `pdx_settings.txt` between callback and resume. The warmup had no native bridge or DLL injection and already rewrote the profile to 1.3. The final launch did inject the bridge, so the post-final byte identity cannot be attributed to unmodified CK3 alone.

The native 1.19.0.6 `game/settings_layout.txt:103-134` puts category `GUI`, item `scale`, in the **Graphics** top-level tab, after Screen and Styling. The Chinese localization labels that tab `图像` and the category `图形用户界面` (`jomini/localization/settings/settings_l_simp_chinese.yml:2,25`). `game/gui/settings/setting_types.gui:142-146` calls `JominiSettingsWindow.SaveAndClose`; line 198 displays `RequireRestart` when the selected native setting requests it. These static files do not state whether `GUI.scale` requires a restart. Both the successful disk reseed and CK3's generated 1.3 block use `version=1`, so a version mismatch has not been observed.

## Native UI Save and Close in the same process

The a04 operator used the original Graphics page in final PID 23124 and selected 100% from the `图形用户界面缩放比例` control. Preserved original screenshots `graphics-tab-click-a01.png` (SHA-256 `F02C92BFE223D3BCD24873F61588536B9D3EF055AFCA8AA4B5D74872F82E8363`) and `scale-100-select-a01.png` (SHA-256 `5BFDC23C7A598678768BDCADA550765DC468D1DA90337B29C8D0A7E0125C046F`) show the control changing from 130% to 100% and the settings panel shrinking immediately. `ui-after-save-a01.png` (SHA-256 `CE2620160563D24B0569FEDA0C0CA3E39DC7C85AB89D11474061FDE217CD596B`) shows the settings menu closed. These images do not prove a fresh cold process or the complete battle panel's geometry.

The complete UI-saved file was frozen as `episode02-e2-04-d05-screen-lease-20260928-a04/native-ui-saved-settings-a01.pdx.txt`, 6,891 bytes, SHA-256 `E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D`. Preservation receipt `native-ui-saved-settings-a01.json` at 2026-09-28 16:45:53.161516 UTC records source mtime `1790613698040308000` ns (16:41:38.040308 UTC), matching source before and after the copy, and the original screenshot hashes. The hot readback `ck3-output/recovery-requests-responses/gui-scale-after-ui-save-a01.json`, SHA-256 `D3F1837AB33FD5541CA2696FF51DD27A114FEACFD332431D2CAC48691D68D337`, saw that same 6,891-byte SHA at 16:44:04.407494 UTC. The native save wrote `GUI.scale="1"` for 100%; its previous warmup file had `"1.3"`. The diagnostic's `disk_gate_passed=false` compares the literal string with requested `"1.0"`, so it is a parser false negative for the disk value; its `runtime_scale_proven=false` and the capture's RED status remain unchanged.

The 6,861-byte frozen warmup file `ck3-output/gui-settings-warmup-before-reseed.pdx.txt` and the 6,891-byte UI-saved copy both have 466 lines. An exact byte reconstruction needs only four string-value changes, once each:

| Setting | Warmup value | UI-saved value | Byte delta |
| --- | --- | --- | ---: |
| `Graphics.hud_skin` | `"DEFAULT"` | `"hud_skin_auto"` | +6 |
| `Graphics.map_table_style` | `"DEFAULT"` | `"map_table_style_auto"` | +13 |
| `Graphics.paper_map_style` | `"DEFAULT"` | `"paper_map_style_auto"` | +13 |
| `GUI.scale` | `"1.3"` | `"1"` | -2 |

The sum is exactly +30 bytes; replacing these four blocks reproduces all 6,891 bytes and SHA-256 `E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D`. No separate persistence flag, version change, or extra field appears in this file. The three Graphics changes are UI normalization candidates; their causal role in later startup behavior is untested. The native save establishes a valid 100% value for the current process and file, not persistence across a new cold process.

## Other local sources checked

- The real Documents CK3 `pdx_settings.txt` is a separate 322-byte file, SHA-256 `3AFC0F3F9CA93B58F92C90FB14F4F54FFF473A3C4717ADF5FB60E0AD627F0BE6`, and contains no `GUI.scale` block.
- The sealed a03 isolated profile's `account/PDX/SDK/ck3` holds only account and telemetry consent JSON; `player` holds the game-rule preset. Searching those directories found no GUI scale value.
- Roaming Paradox launcher `launcher-v2/userSettings.json`, SHA-256 `1D3B93BDF4D0975794BE38F82611F887E104CC045A96ED52D38FCCF8F3DA4593`, contains launcher preferences, with no GUI scale field. The real CK3 `launcher-v2.sqlite` `key_value_pairs` table has only DLC/playset-related keys.
- Steam userdata for app 1158310 holds a 334-byte `remotecache.vdf` and an older remote save, with no `pdx_settings.txt` copy. This excludes the visible local Steam Cloud tree as an exact settings source; it does not prove there is no engine or remote account state.

## Next falsifiable check

In a separate managed cold attempt, seed the exact frozen 6,891-byte UI-saved file into a new isolated profile and verify its SHA-256 before process resume. Record the warmup and final PID/start times, settings SHA/value/mtime before resume and after map load, and original screenshots showing the complete battle panel. The parser must accept numeric spellings `1` and `1.0` as the same 100% scale while retaining an exact-byte record of which spelling CK3 wrote. If the cold process preserves 100%, this complete UI-saved file is a usable seed for that attempt; if it returns to 130%, the four observed differences alone are insufficient to explain persistence. Do not reclassify the a04 RED capture or start a 600-second raw until the new process meets its visual and disk gates.
