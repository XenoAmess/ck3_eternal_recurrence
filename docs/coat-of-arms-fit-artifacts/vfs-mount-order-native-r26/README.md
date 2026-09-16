# CK3 CoA VFS mount-order native R26 (observer coverage RED)

This artifact preserves the first exact-build live run of the bounded VFS
mount-order diagnostic. It is a capability-coverage RED and must not be
rewritten as a successful mod-order observation.

## Scope

- CK3 exact build: `1.19.0.6`
- repository source: `ce65ad84cd90e9d95957e6faa18e67daacd1e4d6`
- interaction: managed typed MCP only; no OCR, keyboard, mouse, or fixed screen
  coordinates
- fixture source: `D:\ck3_coa_vfs_replace_path_r25_source`
- fixture order: `coa_vfs_replace_earlier`, then `coa_vfs_replace_later`
- private bridge: `C:\xb\coa-vfs-r26\xar_ck3_bridge.dll`
- bounded observer: `vfs_mount_lifecycle_observer_v1`, fixed 64-slot storage
- Steam: offline throughout the run

## Result

The bridge connected, advertised the exact build, and returned a stable
observer snapshot. The observer installed all four hooks with no failure flags,
and recorded four successful publisher calls:

1. `.../Crusader Kings III/clausewitz`
2. `.../Crusader Kings III/jomini`
3. `.../Crusader Kings III/game`
4. `D:/ck3_coa_vfs_mount_order_r26_live/profile`

It did **not** record any DLC or fixture-mod data roots. This absence is not a
claim that CK3 skipped those roots: the same session's CK3 debug log records 29
DLC mounts followed by both fixture directories at `virtualfilesystem_physfs.cpp:813`:

```text
[20:04:36][D][virtualfilesystem_physfs.cpp:813]: Mounted Data: D:/ck3_coa_vfs_replace_path_r25_source/coa_vfs_replace_earlier
[20:04:36][D][virtualfilesystem_physfs.cpp:813]: Mounted Data: D:/ck3_coa_vfs_replace_path_r25_source/coa_vfs_replace_later
```

Therefore the current lifecycle publisher hook covers the root publisher path,
not the PhysFS path which mounts DLC and directory mods. Its four rows cannot be
used to decide mod winner order or `replace_path` semantics.

The 300-second managed run ended before the cold database load reached the main
menu, so the route runner reported `main_menu route was not observed`. CK3 did
not crash. Cleanup proved the process tree gone, watchdog absent, control files
removed, and the shared slot released.

## Evidence boundary

This run proves that the existing observer is installed, readable through the
bridge diagnostics embedded in the official MCP capability response, and too
narrow for mod/DLC mount order. It does not yet prove a direct live call to
`ck3_get_bridge_diagnostics`, because the runner scheduled that explicit call
after reaching the CoA route and the cold load timed out first.

The successor work is consequently two separate changes:

1. collect the explicit diagnostic immediately after MCP capability readiness,
   so route timeouts retain direct-tool evidence;
2. add a default-off, private, read-only exact-build observer on the PhysFS
   mount path and expose it through the same bounded diagnostic contract.

Until the second capability passes a live fixture, browser asset-pack receipts
must not infer VFS winner order from this observer.

## Reproduction

```text
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile D:\ck3_coa_vfs_replace_path_r25_source --state-dir D:\ck3_coa_vfs_mount_order_r26_live --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar_ck3_coa_vfs_mount_order_r26 --bridge-dll C:\xb\coa-vfs-r26\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-vfs-r26\xar_ck3_bridge_injector.exe --timeout 300 --vfs-mount-order-diagnostics --output D:\ck3_coa_vfs_mount_order_r26_live_report.json
```

The checked-in [report.json](report.json) is the complete runner report:

- bytes: `181739`
- SHA-256: `6B00F44E704B997D795BACCCA5EC55D59197DAE891240FEB9662F29533EF29C7`

The full debug log remains on the evidence machine at
`D:\ck3_coa_vfs_mount_order_r26_live\profile\logs\debug.log`:

- bytes: `327083`
- SHA-256: `3824E9933E4E9968E2C9972003DC837C8EC804B8EC94895C7B0B183643ADE4F2`

The compact machine-readable conclusions are frozen in
[summary.json](summary.json).
