---
name: steam-ck3-versions
description: Query Crusader Kings III versions offered in the Steam client's game-version/beta list, switch to an explicitly requested branch, and verify download completion and the installed version. Use for CK3 Steam version changes, not Workshop uploads or the Steam client beta.
---

# Steam CK3 versions

Use the bundled Python CLI for repeatable discovery, exact target selection, and download monitoring. Copy the entire skill folder to another machine. The read-only core uses Python's standard library; Windows UIA needs `pywinauto` and `psutil`, and the optional mapped fallback needs `pyautogui` and Pillow in the selected interpreter. Do not claim Linux/macOS GUI support or cross-machine live validation.

Before using the desktop, follow the current workspace's screen-owner, Steam offline/account-occupancy, storage, and input rules. An active game or another screen owner is not permission to interrupt it. This skill never authorizes purchases, account login/takeover, game startup, or changing unrelated settings.

## Workflow

1. Read `scripts/steam_ck3_versions.py --help` with the selected Python interpreter. `inspect` discovers Steam/libraries and reads installed CK3 identity without changing branches. Use explicit machine-local path overrides only when discovery is ambiguous; do not copy paths from another machine.
2. `list` opens only CK3's Properties → Game Versions & Betas (older clients: Betas / 测试). Read the actual offered labels and current selection. A fresh online list is evidence of current availability for this account; an offline list is only cached availability. Installed version, selected branch, and available branches are different facts. Do not substitute a historical list, SteamDB, or a version name guessed from a build ID.
3. Resolve the user's exact target against that list. `public` means the default branch; it is not a promise of a particular version. Do not automatically choose the newest/nearest branch when the requested version is absent or ambiguous. If no target was requested, stop after listing; building this skill does not authorize an arbitrary test downgrade.
4. Before `switch`, confirm the target, exclusive local custody, no running CK3, the account is not occupied elsewhere, download authorization, and capacity under the workspace policy. Downloads require Steam online; this program does not silently toggle mode. Obtain any missing authority and use the workspace's normal Steam-mode procedure. Do not edit `appmanifest`/VDF files to force a branch, force-restart Steam, or inject input into another application.
5. Switch once through the official Steam control and read back the actual selection. A UI action ACK or selected label proves neither download completion nor installed version. Use `wait` with the exact recorded target and expected build/version when available; preserve incomplete/timeout receipts so monitoring can resume without resubmitting the switch.
6. Accept completion only after Steam's pending/update state is clear and the installed branch/build/version readback matches the target. Record EXE identity when changed. No CK3 launch or native bridge injection is needed. A CK3 version change invalidates old exact-build native bindings; do not repin an incompatible DLL merely to bypass that check.
7. If Steam was temporarily brought online for this operation, restore it offline immediately after the download completes or the operation terminates, saving fresh visually reviewed evidence under the workspace's rules.

## UI fallback and evidence

Prefer semantic UI Automation controls. Current Steam also exposes a version Table with RadioButton rows; the helper reads those rows, including their descriptions, and verifies actual checked state. For example, Steam's `1.20.0` branch explicitly advertises game `1.20.0.4`; match that description and still verify installed rawVersion, never infer an arbitrary patch from a shortened branch.

Some Steam Chromium tabs acknowledge Select without navigating. Opt into the proven fallback with `--coordinate-mapper <workspace-canonical-mapper>`; outside this workspace, `scripts/desktop_coordinate_map.py` is a bundled equivalent snapshot of the shared mapper (UTF-8 BOM normalized). Keep that snapshot synchronized with its upstream shared tool, not a separately evolving implementation. The fallback captures current original pixels and dimensions, derives the point from the current app-bound UIA rectangle, and saves mapped-click receipts. A changed/unsupported UI remains incomplete, never a successful switch. Keyboard input follows the workspace's English-layout and focus/readback rules.

Use a new external receipt directory for every invocation. With mapped screenshots, explicitly size the receipt budget for the current desktop; `--receipt-budget-bytes 8388608` covered this machine's actual 1920×1080 attempt, not every machine. Example after obtaining the required local lease and online authority:

```text
python scripts/steam_ck3_versions.py switch --target 1.20.0.4 --expected-version 1.20.0.4 --receipt-dir <new-attempt> --receipt-budget-bytes 8388608 --coordinate-mapper <mapper.py> --task-bus <bus.py> --task-id <owned-task> --account-idle-confirmed --allow-download --network-state online --network-evidence <fresh-reviewed-image>
```

For a resumed wait, use the recorded `target.branch` and `target.expected_version`, e.g. `wait --target 1.20.0 --expected-version 1.20.0.4`; the branch name alone is not that patch identity. Temporarily bringing Steam online can also start CK3 Workshop updates: include the existing queue in capacity planning and restore offline promptly when this version operation ends. Do not mistake a separate Workshop transfer for an unfinished game-version download.

The [qualification record](references/qualification-2026-10-15.json) separates actual one-machine switching, offline tests, original failures, and the storage incident. It does not freeze the future available-version list.

Store receipts outside the checkout in a bounded task directory. Keep exact visible labels, selected-before/after, expected/actual build, installed version, download status, timestamp, and whether the catalog was online or cached. Reports must distinguish `selected`, `downloading`, `installed_verified`, and `blocked/unknown`; simulated tests are not live download proof.

Valve documents branch selection and resulting content downloads in [Branches (Betas)](https://partner.steamgames.com/doc/store/application/branches?l=english). Optional SDK APIs are documented in [ISteamApps](https://partner.steamgames.com/doc/api/ISteamApps); use only a verified local ABI, never guessed vtable offsets. The official GUI remains the portable fallback when those exports are unavailable.
