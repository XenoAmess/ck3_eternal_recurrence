# E2-04 a04 GUI scale cold-launch evidence (read-only audit)

This note audits the isolated a04 profile and the checked-in launch path. It does not certify a usable recording frame or identify the sole writer of `pdx_settings.txt`.

## Observed sequence

| Phase | Evidence | Result |
| --- | --- | --- |
| Before warmup | `episode02-e2-04-d05-live-20260928-a04/ck3-output/gui-settings-prelaunch.json` and `gui-settings-before-native-session.json` | The new isolated `pdx_settings.txt` was 420 bytes, SHA-256 `146ED5F330EB59BCBA8D4D5FE6F03D9A497DED37C72457ABA812121426958257`, with `GUI.scale` value `1.0` and `version=1`. The before-session readback passed its disk gate at 2026-09-28 16:14:25.212529 UTC. |
| Warmup exit | `ck3-output/session.jsonl` and `gui-settings-before-final-launch.json` | Warmup PID 16208 started at 16:14:27.605929 UTC. After it exited, the profile was 6,861 bytes, SHA-256 `2191EA423B3B1A94CB7E905B6096F3D07BBF0B7F1668C3E0ED412297AEF2C509`, with `GUI.scale=1.3`, at 16:16:28.690889 UTC. The file mtime was `1790612114971432000` ns, equivalent to 16:15:14.971432 UTC, within warmup lifetime. |
| Before final launch | `gui-settings-warmup-reseed.json` and `gui-settings-after-reseed-before-final-launch.json` | The warmup's complete 6,861-byte file was preserved. After a one-value, same-directory atomic replacement, the file was still 6,861 bytes, SHA-256 `A45FF273C54C4D1D0819FC756F6E8B336411AB71E147F24E5BC462057309E541`, with `GUI.scale=1.0` and `version=1`. The successful disk readback was at 16:16:28.802117 UTC; mtime `1790612188755938000` ns was 16:16:28.755938 UTC. This was a disk-only result. |
| Final cold process | `ck3-output/session.jsonl` | Final PID 23124 was launched at 16:16:30.717549 UTC, after the reseed. A subsequent read-only SHA check of the same profile returned the warmup's exact 6,861-byte SHA `2191EA423B3B1A94CB7E905B6096F3D07BBF0B7F1668C3E0ED412297AEF2C509` and `GUI.scale=1.3`. The exact post-final write mtime and process writer are not yet bound in this note. |

The post-final byte identity rules out a failure limited to the original 420-byte minimal formatting: the final launch path also returned a complete, naturally generated settings file whose only changed value was `GUI.scale` to its previous bytes. It does not distinguish a CK3 default/recommendation, an unobserved settings source, or behavior in the injected process.

## Launch-path boundary

In the Episode 2 branch, `promo/ck3_native_war_ai/integration/capture_session.py:29-30` puts this checkout's `ck3_autonomous_player/src` ahead of installed packages, and lines 894-909 pass `reseed_gui_scale_after_warmup` as the only before-final callback. `ck3_autonomous_player/src/xar_autoplayer/native_session.py:1139-1156` invokes that callback, records its success, then calls `launch` with the same profile and bound save. `ck3_autonomous_player/src/xar_autoplayer/runtime.py:2291-2300` forms a direct `ck3.exe -gdpr-compliant -userdir=<isolated profile> -loadsave=<checkpoint>` command. Its `launch` path at lines 2405-2473 and 2561-2620 clears selected runtime logs, creates the suspended process, binds the Job and resumes it; that reviewed path does not copy or regenerate `pdx_settings.txt` between callback and resume. The warmup had no native bridge or DLL injection and already rewrote the profile to 1.3. The final launch did inject the bridge, so the post-final byte identity cannot be attributed to unmodified CK3 alone.

The native 1.19.0.6 `game/settings_layout.txt:128-133` exposes category `GUI`, item `scale`. `game/gui/settings/setting_types.gui:142-146` calls `JominiSettingsWindow.SaveAndClose`; line 198 displays `RequireRestart` when the selected native setting requests it. These static files do not state whether `GUI.scale` requires a restart. Both the successful disk reseed and CK3's generated 1.3 block use `version=1`, so a version mismatch has not been observed.

## Other local sources checked

- The real Documents CK3 `pdx_settings.txt` is a separate 322-byte file, SHA-256 `3AFC0F3F9CA93B58F92C90FB14F4F54FFF473A3C4717ADF5FB60E0AD627F0BE6`, and contains no `GUI.scale` block.
- The sealed a03 isolated profile's `account/PDX/SDK/ck3` holds only account and telemetry consent JSON; `player` holds the game-rule preset. Searching those directories found no GUI scale value.
- Roaming Paradox launcher `launcher-v2/userSettings.json`, SHA-256 `1D3B93BDF4D0975794BE38F82611F887E104CC045A96ED52D38FCCF8F3DA4593`, contains launcher preferences, with no GUI scale field. The real CK3 `launcher-v2.sqlite` `key_value_pairs` table has only DLC/playset-related keys.
- Steam userdata for app 1158310 holds a 334-byte `remotecache.vdf` and an older remote save, with no `pdx_settings.txt` copy. This excludes the visible local Steam Cloud tree as an exact settings source; it does not prove there is no engine or remote account state.

## Next falsifiable check

In the paused a04 session, use the native pause menu's Settings → Interface → GUI scale control, inspect any restart marker, choose `1.0`, then invoke Save and Close. Preserve an immediate and delayed disk SHA/value readback plus an original desktop screenshot of the complete battle panel. If the UI requires restart, use a managed restart with the same isolated profile and exact checkpoint, recording pre-resume and postmap file identities. Compare the complete UI-saved settings bytes against the before-final reseed: a different companion field is a concrete candidate for the missing persistence contract; exact equality followed by a different cold-start outcome points to state outside that file. A positive postmap screenshot and file readback in the new process are required before any 600-second raw.
