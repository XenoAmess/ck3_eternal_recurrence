# Isolated native Workshop download acceptance

The `steam-native` provider exposes `workshop_native_download` for one explicit
AppID and Workshop item. It starts an independent Python process so its manual
callback queue cannot share ownership with a publication or preview query.
The tool requires an existing authorized Steam session. It does not start Steam
or CK3, change online/offline mode, subscribe to an item, create an item, publish,
or move/delete any cache. The download uses normal priority. It now has a
**first independent live acceptance** for item 3182367229, documented below;
other targets and failure paths retain their existing static-test boundary.

## MCP parameters and CLI

```json
{
  "dll_path": "C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/steam_api64.dll",
  "item_id": "3182367229",
  "app_id": 1158310,
  "timeout_seconds": 300,
  "expected_cache_path": "C:/SteamLibrary/steamapps/workshop/content/1158310/3182367229"
}
```

`dll_path` and the optional cache path are supplied by the operator. `item_id`
is a nonzero uint64 decimal string, `app_id` a nonzero uint32, and timeout must
be finite, greater than zero and at most 3600 seconds. The cache path must be
absolute and end with the exact item ID. Defaults are AppID 1158310 and 300
seconds; omitting the cache path permits ordinary download without a freshness
claim. No product item ID is hardcoded in the implementation.

Set SteamAppId/SteamGameId only in the calling process environment, use an
installed package or configured PYTHONPATH, and invoke with the selected Python:

```text
<python> -m ck3_workshop_mcp.call_tool --provider steam-native --tool workshop_native_download --arguments-file <download-arguments.json>
<python> -m ck3_workshop_mcp.steam_native download --dll <steam_api64.dll> --item-id 3182367229 --app-id 1158310 --timeout-seconds 300 --expected-cache-path <exact-cache-directory>
```

The standalone CLI exits 0 only for business success and otherwise exits 2.
MCP envelopes can have transport `ok=true` while `result.ok=false`; inspect
the business result. Persist stdout as publication evidence. No hidden receipt
or cache mutation is performed by this tool beyond Steam's requested download.

## Evidence and completion gate

`DownloadItem` returns a bool initiation acknowledgement. The worker uses
ManualDispatch and waits for callback **3406** whose AppID and item ID both
match the request. Every callback buffer is freed, including foreign callbacks;
matching fields are copied before freeing. It never calls RunCallbacks in the
download loop, mixes in a SteamAPICall_t wait, or automatically retries.
These semantics follow [Valve's ISteamUGC documentation](https://partner.steamgames.com/doc/api/ISteamUGC#DownloadItem)
and the [manual dispatch declarations](https://github.com/ValveSoftware/source-sdk-2013/blob/0759e2e8e179d5352d81d0d4aaded72c1704b7a9/src/public/steam/steam_api.h).

Callback ABI is fixed to 64-bit Python/DLL: `DownloadItemResult_t` is 24 bytes
with AppID at offset 0, uint64 item at 8 and int32 EResult at 16. `CallbackMsg_t`
is 24 bytes with its pointer at 8 and payload size at 16. Layouts are grounded
in Valve's pinned [UGC header](https://github.com/ValveSoftware/source-sdk-2013/blob/0759e2e8e179d5352d81d0d4aaded72c1704b7a9/src/public/steam/isteamugc.h)
and [callback header](https://github.com/ValveSoftware/source-sdk-2013/blob/0759e2e8e179d5352d81d0d4aaded72c1704b7a9/src/public/steam/steam_api_internal.h).
`workshop_native_symbols` audits nine download/manual-dispatch exports without
loading the DLL; missing exports or another ABI block download.

Only after the exact callback returns EResult 1 does the worker call
GetItemInstallInfo. Success requires an existing directory reported by Steam,
the Installed flag, and no NeedsUpdate, Downloading or DownloadPending flags.
When an expected cache path is supplied, it must be absent just before
DownloadItem and match Steam's reported installation path afterward. The
operator must first preserve/move that precise old cache; the tool refuses an
existing directory or link and performs no cleanup. GetItemDownloadInfo is
progress telemetry and cannot prove content freshness. Unsubscribed items can
download into Steam's temporary cache; the tool never calls SubscribeItem.

The result schema is `ck3_workshop_mcp.steam_native.download.v1`, with exact
target, DLL hash, worker PID/exit code, start acknowledgement, matching callback,
raw/named state flags, progress, installation path/size/timestamp and elapsed
time. `complete` has `ok=true`; a false start or non-OK exact callback is
`failed`; no callback by timeout is `unknown`; a successful callback with
incomplete installation/flags is `partial`. A hung/crashed child or malformed
response remains `unknown`. The supervising process terminates only its own
worker after timeout plus 15 seconds. Steam may continue downloading; inspect
the recorded evidence before a new operation.

Download completion does not prove release file contents. Validate the returned
directory against the frozen manifest with `ck3_workshop_mcp.validation._validate_manifest_tree`:
exact inventory, file sizes and SHA-256, with explicit product/item/version/count
checks supplied by the publishing caller. Public description, notes, media and
Steam offline restoration remain separate publication gates.

## Source and validation boundary (2026-10-03)

This capability was requested by the More Tenets Slots(XA) migration publication
for item 3182367229, whose release acceptance needs a fresh **46-file** tree.
Product mechanism, material and publication receipts remain in
[`ck3_mod_more_tenant_slots`](https://github.com/XenoAmess/ck3_mod_more_tenant_slots).
Its specific migration evidence is
[`docs/migration-report.md`](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/migration-report.md);
the independent project's
[v10 publication report](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/workshop/publication-v10.md)
records the first live download and exact manifest result. The reusable download/callback contract,
implementation and synthetic fixtures belong in this framework.

Focused static validation covers exact/foreign/failed/malformed callbacks,
buffer lifetime, start acknowledgement versus completion, timeout without retry,
incomplete installation and flags, exact cache path, old-cache preservation,
isolated process invocation, unknown child result, invalid parameters and MCP
forwarding. Local DLL PE audit found all nine exports at SHA-256
`1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`.
No DLL was loaded and no live download or Steam mode change was performed by
this framework work package. Static results cannot claim public release success.

```text
<python> -m unittest tests.test_native_download tests.test_native_previews tests.test_steam_native tests.test_mcp_surface -v
```

Run from `ck3_workshop_mcp` with PYTHONPATH pointing to its `src` and the official
MCP SDK installed. The bounded suite passes 35 tests.

## First independent live acceptance (2026-10-03)

The coordinating publication root reported this tool's first real download
after the native existing-item update at `2026-10-02T22:00:32Z`. The caller
preserved/moved the exact old 13-file cache before invoking the isolated native
worker; the MCP itself did not move or delete it. Callback 3406 matched
AppID 1158310, item 3182367229 and EResult 1. Completion took 14.398 seconds;
GetItemInstallInfo returned the exact expected path, size-on-disk 1,008,047
bytes and timestamp `1790978434`. State flags were 5: Subscribed and Installed
true; NeedsUpdate, Downloading and DownloadPending false. The Subscribed flag
was observed existing state, not a SubscribeItem action.

The publishing caller then passed the returned installation tree and frozen
release manifest to `_validate_manifest_tree`: the exact inventory, sizes and
SHA-256 of all **46 files** passed. This closes the download plus content gate
for that product version. The raw MCP report, manifest, cache preservation and
publication evidence remain in
[publication-v10.md](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/workshop/publication-v10.md)
in the independent project. Only the root-provided method/results and source
link are enriched here; no machine path or product artifact is imported.

This live result covers the exact installed DLL hash above and this subscribed
item's successful fresh download. Unsubscribed temporary-cache behavior,
timeouts, failed callbacks and child failure remain statically tested only.
The implementation author performed no Steam/game/desktop action for this
documentation package. Public metadata/media/notes and final Steam offline
restoration are distinct gates, with their final status owned by the product
publication report.
