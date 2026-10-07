# Exact-target native Workshop subscription

`workshop_native_subscribe` subscribes one explicit Workshop item through the existing authorized Steam session. This closes the new-item publication gap before a normal subscribed-cache download. Its implementation is reusable and contains no product ID, machine path or credentials.

This capability was added while preparing the original《超人强》product. Product plans and actual publication evidence belong in `mod_superman_qiang/docs/`; this document describes only the shared transport and verification boundary. At preparation time the new capability has static coverage and a non-loading local export audit; it has not performed a real subscription.

## Invocation and scope

```json
{
  "dll_path": "<installed CK3>/binaries/steam_api64.dll",
  "item_id": "<exact new or existing Workshop ID>",
  "app_id": 1158310,
  "timeout_seconds": 180
}
```

```text
<verified-python> -m ck3_workshop_mcp.call_tool --provider steam-native --tool workshop_native_subscribe --arguments-file <subscribe-arguments.json>
```

The operator supplies process-local `SteamAppId=1158310` and `SteamGameId=1158310` as for other native tools. The item is a nonzero uint64 ASCII decimal string; AppID is a nonzero uint32; timeout is finite, positive and at most 3600 seconds. The tool does not start Steam, CK3 or the Launcher, publish, change Steam mode, delete/move a cache, or automatically retry. Steam can schedule download and installation after subscribing; this is part of [Valve's SubscribeItem behavior](https://partner.steamgames.com/doc/api/ISteamUGC#SubscribeItem).

The caller independently enforces publication authorization, local account identity, online idle state and final Steam offline restoration. The direct tool remains outside the prototype WAL workflow.

## What completion proves

SubscribeItem returns a `SteamAPICall_t`. A nonzero handle is only initiation. The existing native wait requests the result for that exact handle and callback **1313**, using `RemoteStorageSubscribePublishedFileResult_t`. The Win64 result is 16 bytes: `EResult` at offset 0 and uint64 PublishedFileId at offset 8. The layout and callback constant come from Valve's pinned [Remote Storage header](https://github.com/ValveSoftware/source-sdk-2013/blob/0759e2e8e179d5352d81d0d4aaded72c1704b7a9/src/public/steam/isteamremotestorage.h); the documented ISteamUGC method returns this call result.

Business `complete` requires the exact callback item ID, `EResult=1`, and a subsequent GetItemState read for that same item with the Subscribed bit set. A foreign result or unobserved callback remains `unknown`; an invalid call or explicit failed result is `failed`; a successful callback without the observed bit is `partial`. The result binds AppID context, DLL SHA-256, call handle, callback, raw state and elapsed time. MCP transport `ok=true` alone is not business success.

Subscription completion does not establish installation or file contents: `installation_verified` and `content_verified` remain false. Continue with the independent [native download](workshop-native-download.md), first preserving any automatically created exact cache, proving the expected cache path absent, then validating the newly downloaded tree against the frozen release manifest. Public metadata, media and full Change Notes are independent gates.

Under the user's permanent **2026-10-07** policy for all future mods, published-cache acceptance only requires exact formal-file agreement and successful CK3 startup that actually enables and mounts/loads the target product from the real Steam-downloaded published-cache path. Actual initialization logs can prove the load; then quit normally through the GUI. No new game, character selection, map or native business query is required. Do not repeat gameplay/fixture/event/option/trait/cooldown/candidate tests for cache acceptance. Pre-publication source acceptance and historical results remain unchanged. Subscription and download callbacks do not establish CK3 loading; follow the [permanent Workshop cache acceptance policy](workshop-cache-acceptance.md).

## Static validation

The focused suite covers Win64 ABI, exact callback and state, unknown result without retry, foreign item, explicit failure, invalid API call, successful callback without Subscribed state, argument validation, missing exports before DLL load, and official MCP forwarding of a partial business result. Existing publication, preview and download tests remain applicable.

On 2026-10-04 the five-module focused suite passed **44/44** tests using `tools/.venv/Scripts/python.exe`, Python 3.14.7 and `mcp==2.0.0`. The raw stdio and exact source hashes are preserved in `D:/ck3-experience-drain-feasibility-20261004/publication-subscribe-static-01/`. The official non-loading MCP symbols call found both optional subscription exports in the installed CK3 DLL, SHA-256 `1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`. This validation did not load the DLL, change Steam mode or subscribe an item.

```text
<verified-python> -m unittest tests.test_native_subscribe tests.test_native_download tests.test_native_previews tests.test_steam_native tests.test_mcp_surface -v
```

Run from `ck3_workshop_mcp` with its `src` on `PYTHONPATH` and the official MCP SDK installed. The non-loading `workshop_native_symbols` now audits the two subscription exports as optional capability fields, leaving legacy publication requirements unchanged. The actual test result and any first live subscription must be recorded separately; a static pass cannot establish a public release.
