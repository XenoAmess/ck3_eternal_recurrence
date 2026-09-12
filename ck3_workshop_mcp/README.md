# CK3 Workshop MCP

`ck3-workshop-mcp` provides direct Steamworks publication, Launcher UI Automation,
and a separate prototype publication workflow for CK3 Workshop items.

Version `0.1.0` contains three deliberately separate capability layers:

- the typed WAL state machine is fully executable against the in-memory fake
  provider, but no real publication provider is wired into that state machine;
- `pdx-uia` is a real Paradox Launcher UI Automation channel. It can inspect the
  accessible control tree, invoke a named semantic control, and set exact Edit
  text without OCR or screen coordinates. These direct UIA tools do not yet
  inherit the WAL plan, one-time token, ownership, EULA, or offline-compensation
  state machine;
- `steam-native` is a direct Steamworks flat-API channel for symbol inspection,
  active AppID/user probing, and receipt-backed create/update publication. It is
  exposed through MCP but is not wired into the typed WAL state machine above.

The current Launcher has exposed a complete 63-control UIA tree in live
inspection. That proves the semantic control transport, not an end-to-end
state-machine-backed upload provider. The direct Steamworks module loads an
operator-supplied `steam_api64.dll` only for explicit probe/publish calls and
does not accept or read passwords, tokens, cookies, or Steam Guard material.

The UIA attempt stopped at the Launcher's inconsistent `#/username` profile
state before creating any item. The subsequent **native MCP publication succeeded**
as item [3800124956](https://steamcommunity.com/sharedfiles/filedetails/?id=3800124956).
Its public title/description and newly downloaded 14-file cache were verified;
Steam was restored to Offline Mode without signing out. See the
[release evidence](../docs/release-changelogs/auto-upgrade-buildings/1.19.0.md).

## Why the provider boundary exists

Read-only reverse engineering of Paradox Launcher `2026.11.1` found this path:

```text
Launcher renderer
  @IPC_MODS_UPLOAD/UPLOAD_MOD
    -> Electron main PublishModHandler
    -> Greenworks 0.29.0 / STEAMUGC_INTERFACE_VERSION016
    -> Steam Client IPC
    -> ISteamUGC CreateItem / SubmitItemUpdate
```

There is no ordinary PDX HTTP upload endpoint to replay.  Launcher IPC is an
internal renderer-to-main channel, while authorization belongs to the active
Steam Client session.  The Launcher wrapper also does not expose a trustworthy
Workshop Legal Agreement query, visibility, update language, or change notes.
A CDP adapter and transport prototype exist, but the attempted debug-enabled
Launcher start was rejected by the execution environment's system policy. It
was not retried or bypassed, and `pdx-cdp` has **no live validation**. Do not cite
it as an operational publishing route. The supported current automation route
is normal Launcher startup followed by `pdx-uia` semantic controls.

The standalone direct provider now has a supported CK3 AppID launch context on
the verified workstation. It does not call `SteamAPI_RestartAppIfNecessary`,
start Steam, start CK3, or create/copy `steam_appid.txt`.

## Direct Steamworks flat-API channel

`steam_native.py` follows Valve's documented
[`ISteamUGC`](https://partner.steamgames.com/doc/api/ISteamUGC),
[`ISteamUtils`](https://partner.steamgames.com/doc/api/ISteamUtils), and
[`ISteamUser`](https://partner.steamgames.com/doc/api/ISteamUser) signatures.
It discovers versioned `SteamAPI_Steam*_vNNN` accessors from the exact PE export
table and uses `IsAPICallCompleted` plus `GetAPICallResult` for
`CreateItemResult_t` and `SubmitItemUpdateResult_t`.

The non-loading metadata command is safe to run offline:

```powershell
$env:PYTHONPATH = 'D:\workspace\ck3_eternal_recurrence\ck3_workshop_mcp\src'
& 'D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe' `
  -m ck3_workshop_mcp.steam_native symbols `
  --dll 'C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\steam_api64.dll'
```

On the verified DLL this reported SHA-256
`1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`,
1,065 exports, and accessors UGC `v016`, Utils `v010`, and User `v021`; all
required flat exports were present. The read-only `probe` then initialized the
existing Steam session and verified AppID `1158310`, logged-on state, and the
expected user. That is a real live probe, not a publication claim.

```powershell
& 'D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe' `
  -m ck3_workshop_mcp.steam_native probe `
  --dll 'C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\steam_api64.dll' `
  --app-id 1158310
```

`publish` is externally mutating and requires a reviewed JSON plan plus a
dedicated durable receipt path:

```powershell
& 'D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe' `
  -m ck3_workshop_mcp.steam_native publish `
  --dll 'C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\steam_api64.dll' `
  --plan-file D:\release\native_publish_plan.json `
  --receipt-file D:\release\native_publish_receipt.json
```

The plan fields are `operation_id`, `operation` (`create` or `update`), `app_id`,
`target_item_id`, `title`, either `description` or `description_path`,
`content_path`, optional `preview_path`, `visibility`, `tags`, `change_note`, and
`workshop_legal_agreement_accepted`. Content, description, preview, and metadata
are hash-bound to the receipt. For create, `CREATE_INTENT` is durable before the
call and the returned item ID is atomically persisted before content submission.
An unknown Create or Submit callback is never automatically retried. If Create
reports that the legal agreement is required, the item ID remains in the
receipt and a later acknowledged run continues with that item instead of
creating another one.

The first real MCP-backed create completed on 2026-09-12 as Workshop item
`3800124956`: `CreateItem` and `SubmitItemUpdate` both returned `EResult=1`, the
legal-agreement flag was false, and the durable receipt reached `complete` at
`2026-09-12T09:32:48.697643Z`. This validates the new-item path on that exact
machine/session. The same item then received two successful live native updates:
a metadata-only wording correction and the full 2.0.0 content update. The latter
returned `EResult=1` at `2026-09-12T14:32:37.174334Z`; anonymous public readback
matched the exact title and description, and a newly downloaded 15-file cache
matched the ID-bound release manifest byte for byte.

One live boundary was established during the 2026-09-13 changelog correction:
passing a different non-empty `pchChangeNote` while the Workshop content and
effective metadata were unchanged returned `EResult=1` but did not create or
replace a public Change Notes entry. Even a real description-only metadata
change did not replace that existing note. Therefore a native submit receipt is
not sufficient evidence for Change Notes publication: read back the public
changelog entry itself. Editing an already-created entry currently uses the
authenticated Workshop owner page; the native bridge does not expose that web
operation.

## Hard gates

Within the typed state-machine path, every plan binds the staging manifest, description, preview, metadata, target,
and operation kind into one deterministic SHA-256.  Preflight then requires:

- CK3 consumer AppID `1158310`;
- an exact staging tree matching every size and SHA-256 in the manifest;
- an inner `descriptor.mod` without `remote_file_id`;
- create with no outer/target ID, or update with identical outer and plan IDs;
- no target, outer, inner, or manifest reference to a configured forbidden
  upstream item such as `3596580780`;
- confirmed online mode and confirmed idle account (unknown and in-game both
  stop; no forced launch or session takeover);
- confirmed target ownership for updates;
- positively clear Workshop EULA status; owner action is never automated;
- provider support for every requested field.

The plaintext submit token is returned once, never stored, expires in 30–900
seconds, and is bound to the operation.  `workshop_submit` consumes it durably
before the first irreversible provider call.  The WAL records `CREATE_INTENT`
before `CreateItem`, records a returned new item ID before content submission,
and records `CONTENT_SUBMIT_INTENT` before `SubmitItemUpdate`.  If either result
is unknown, automatic retry is prohibited.  This prevents a lost callback from
silently creating duplicate items or submitting the same update again.

Every CK3 plan is required to set `offline_after=true`.  Any online window carries a durable compensation
obligation.  Success and failure paths both call the provider's offline restore
and verify the observed mode.  Failure to observe offline state is not reported
as completion.

## MCP surface

Resources:

```text
workshop://capabilities
workshop://operations/{operation_id}
workshop://operations/{operation_id}/events
```

Tools:

```text
workshop_capabilities
workshop_plan_create
workshop_begin_online_window
workshop_preflight
workshop_issue_submit_token
workshop_submit                 # state-machine irreversible call
workshop_operation_get
workshop_operation_events
workshop_restore_offline
workshop_recover_offline_obligations

# Registered only with --provider pdx-uia
workshop_ui_inspect
workshop_ui_invoke
workshop_ui_set_text
workshop_ui_keys
```

`workshop_ui_invoke` is a real UI action and may activate the selected button.
The bridge matches accessible `Name`, `ControlType`, and optional
`AutomationId`; it never falls back to pixel coordinates. `workshop_ui_set_text`
passes large text through a temporary UTF-8 file rather than a command-line
argument. The PowerShell bridge is included in installed wheels as package data.

The current Launcher controls have these observed semantics:

- invoking a `ComboBox` expands it;
- `ListItem` Select/Invoke can acknowledge without changing the selected item;
- focusing the exact ComboBox, sending `{DOWN}{END}{ENTER}`, and then reading
  the selected value back through UIA successfully selected the maintained mod;
- `workshop_ui_keys` accepts only `{HOME}`, `{END}`, `{UP}`, `{DOWN}`, `{TAB}`,
  `{ENTER}`, and `{ESC}`, including concatenated sequences. It is not an
  arbitrary keyboard-input endpoint;
- `workshop_ui_set_text` may use an empty `automation_id` only when the UIA tree
  yields exactly one matching anonymous Edit control. A 1024-character value
  has been set and read back successfully. The bridge tries clipboard paste
  first and falls back to `ValuePattern.SetValue` after a clipboard mismatch.

All success claims above are control-level readbacks. They do not prove a
Workshop item was created or remotely committed.

No tool accepts a password, Steam Guard code, cookie, Web API key, auth ticket,
or PDX token.  The server only returns the generic owner-action URL when EULA
handling is required:
`https://steamcommunity.com/sharedfiles/workshoplegalagreement`.

## Operation storage

Each operation is stored under:

```text
<state-dir>/<operation-id>/wal/00000001.json
<state-dir>/<operation-id>/wal/00000002.json
...
```

Every event is written to a temporary file, flushed and `fsync`'d, then atomically
renamed into the append-only sequence.  Current state is reconstructed from the
immutable records.  By default the state root is
`%LOCALAPPDATA%\XenoAmess\ck3-workshop-mcp\operations`; override it with
`CK3_WORKSHOP_MCP_STATE_DIR` or `--state-dir`.  No account name or machine path is
part of the protocol.

Providers with online-control support run durable offline compensation both at
server startup and in a `finally` block at orderly shutdown.  The explicit
recovery tool is available for operator-driven reconciliation as well.

## Install and run

Python 3.11 or newer is required.

```powershell
cd ck3_workshop_mcp
py -m venv .venv
& .venv\Scripts\python.exe -m pip install -e ".[mcp]"
& .venv\Scripts\ck3-workshop-mcp.exe --provider pdx-readonly
```

The default `pdx-readonly` provider is inert.  For an isolated protocol demo:

```powershell
& .venv\Scripts\ck3-workshop-mcp.exe `
  --provider fake `
  --state-dir "$env:TEMP\ck3-workshop-mcp-demo"
```

Do not point the fake-provider run at production operation evidence.  It is a
deterministic test double and does not publish anything.

### Call the real UIA channel through the official MCP client

Use the same Python environment that has `mcp==2.0.0` installed. For this
workspace the currently verified interpreter is:

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe
```

The arguments file must contain exactly one JSON object. For top-level-window
inspection, `inspect-arguments.json` is:

```json
{"hwnd": 0}
```

Call the tool through the official in-memory MCP client:

```powershell
& "D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe" `
  -m ck3_workshop_mcp.call_tool `
  --provider pdx-uia `
  --tool workshop_ui_inspect `
  --arguments-file inspect-arguments.json
```

Inspecting a selected Launcher window uses its real HWND:

```json
{"hwnd": 123456}
```

Invoke and text-setting argument shapes are:

```json
{"hwnd": 123456, "name": "Upload Mod", "control_type": "Button", "automation_id": ""}
```

```json
{"hwnd": 123456, "automation_id": "description-input"}
```

For large text, keep it out of JSON and supply its UTF-8 file separately:

```powershell
& "D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe" `
  -m ck3_workshop_mcp.call_tool `
  --provider pdx-uia `
  --tool workshop_ui_set_text `
  --arguments-file set-text-arguments.json `
  --text-file description.bbcode
```

An anonymous Edit is addressed explicitly with an empty ID; the bridge still
requires the resulting match to be unique:

```json
{"hwnd": 123456, "automation_id": ""}
```

Finite ComboBox navigation uses:

```json
{"hwnd": 123456, "automation_id": "mod-combobox", "sequence": "{DOWN}{END}{ENTER}"}
```

The CLI writes one JSON result envelope to stdout. UIA script diagnostics and
MCP failures are returned as errors; they are not converted into guessed UI
state. Because the UIA tools are not yet connected to `WorkshopService`, the
operator must independently enforce the publication plan, account-idle/EULA
checks, target identity, upload evidence, and final Steam-offline restoration.

## Plan example

All paths are operator-supplied and portable across machines via the MCP
bootstrap/configuration layer.  Hashes must describe the exact referenced
bytes.

```json
{
  "schema": "ck3.workshop.operation.v1",
  "operation_id": "auto-upgrade-buildings-1.19.0-create-01",
  "product_key": "auto-upgrade-buildings",
  "operation": "create",
  "consumer_app_id": 1158310,
  "staging_dir": "D:/release/mod_auto_upgrade_buildings",
  "staging_manifest": "D:/release/mod_auto_upgrade_buildings-v1.19.0.manifest.json",
  "staging_manifest_sha256": "<64 lowercase hex>",
  "outer_descriptor": "C:/userdir/mod/mod_auto_upgrade_buildings.mod",
  "title": "自动升级建筑（XenoAmess维护版）",
  "description_path": "D:/repo/workshop/auto_upgrade_buildings_description.bbcode",
  "description_sha256": "<64 lowercase hex>",
  "preview_path": "D:/release/mod_auto_upgrade_buildings/thumbnail.png",
  "preview_sha256": "<64 lowercase hex>",
  "tags": ["Balance"],
  "visibility": "public",
  "change_note": "Initial maintained release",
  "target_item_id": null,
  "forbidden_item_ids": ["3596580780"],
  "offline_after": true
}
```

For an update, set `operation` to `update`, provide the maintained item's ID as
`target_item_id`, and ensure the outer `.mod` contains that exact ID.  The
canonical inner descriptor must still have no ID.

## Tests

The test suite has no third-party dependency:

```powershell
$env:PYTHONPATH = "src"
py -m unittest discover -s tests -v
```

It covers package-data inclusion of `uia_bridge.ps1`, the finite UIA navigation-key contract, exact key parameter forwarding,
`--text-file` forwarding through the official MCP client, create callback loss without duplicate Create, unknown submit without
retry, EULA blocking, verified offline compensation, update ID mismatch,
forbidden upstream ID, in-game account refusal, exact staging validation,
restart recovery, and inert real-provider capabilities.

## Remaining work

Native create and update publication are both live-verified. Download callback
automation and Steam mode restoration are not native MCP features yet: the
verified releases used Steam's console for fresh downloading and its menu for
offline restoration. Direct tools remain separate from the prototype WAL workflow.

### Native MCP invocation used for publication

Set `SteamAppId=1158310` and `SteamGameId=1158310` only in the calling process,
or use the game's existing `binaries/steam_appid.txt` context. Never force-restart Steam.
With the package installed (or `PYTHONPATH` pointing to its `src`):

```powershell
& tools\.venv\Scripts\python.exe -m ck3_workshop_mcp.call_tool `
  --provider steam-native --tool workshop_native_publish `
  --arguments-file native-tool-arguments.json
```

```json
{"dll_path":"C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/steam_api64.dll","plan_file":"D:/release/native_publish_plan.json","receipt_file":"D:/release/native_publish_receipt.json"}
```

The integrated 2026-09-12 suite passed **23/23** tests using the verified MCP environment.
