# Native Workshop additional preview images

The native bridge now reads, appends, replaces and removes the additional image
strip of an existing item. This is separate from `SetItemPreview` (the main
thumbnail) and BBCode `[img]` links. This package is **static-ready**: its new
query and setters have not yet been called against a live Steam session.

## Source and ownership decision

The owner requested publication of More Tenets Slots(XA), item `3182367229`,
including new CK3 1.20.0.3 Rite GUI screenshots and a replacement thumbnail.
The existing native MCP handled content, metadata and thumbnail but could not
update the additional image strip. That capability also serves other mods, so
the generic code, contract and tests belong to this framework. Product media,
BBCode, image provenance and actual release facts stay in
[ck3_mod_more_tenant_slots](https://github.com/XenoAmess/ck3_mod_more_tenant_slots).
The product's `docs/workshop-publication-plan.md` and release evidence govern
that publication; this document does not claim the mod is published.

## Read and freeze the existing strip

`workshop_native_previews` is registered with `--provider steam-native`:

```json
{"dll_path":"<installed CK3>/binaries/steam_api64.dll","item_id":"3182367229","app_id":1158310}
```

```text
<configured-python> -m ck3_workshop_mcp.call_tool --provider steam-native --tool workshop_native_previews --arguments-file preview-read-arguments.json
<configured-python> -m ck3_workshop_mcp.steam_native previews --dll <installed-dll> --item-id 3182367229 --app-id 1158310
```

Supply the existing authorized Steam session and process-local AppID context
(`SteamAppId=1158310`, `SteamGameId=1158310`). No Steam, CK3 or Launcher startup,
credential access or `steam_appid.txt` creation is performed. Only `symbols`
inspects the PE without loading the DLL; `previews` initializes Steamworks.

The query requests exactly one PublishedFileId, enables additional previews,
disables disk-cache reuse with `SetAllowCachedResponse(..., 0)`, waits for
callback 3401 and releases its handle on success or failure. Failed results,
wrong handles, cached responses or a result count other than one are rejected.
The result excludes the main thumbnail:

```json
{
  "schema":"ck3_workshop_mcp.steam_native.previews.v1","ok":true,
  "item_id":"3182367229","app_id":1158310,
  "previews":[
    {"index":0,"type":0,"url":"https://.../old-image.jpg","original_filename":"old-image.jpg"}
  ]
}
```

Freeze this returned object. Enumeration is not proof of ownership or legal
agreement status; retain the existing independent account identity, ownership
and online idle-state checks.

## Backward-compatible update-plan fields

Add these optional fields to the existing native publish plan:

```json
{
  "operation":"update","target_item_id":"3182367229",
  "expected_additional_previews":{
    "item_id":"3182367229","app_id":1158310,
    "previews":[{"index":0,"type":0,"url":"https://.../old-image.jpg","original_filename":"old-image.jpg"}]
  },
  "update_preview_files":[{"index":0,"path":"<absolute>/new-image.jpg","size":123456,"sha256":"<64 hex>"}],
  "remove_preview_indices":[],
  "additional_preview_files":[{"path":"<absolute>/second-image.jpg","size":234567,"sha256":"<64 hex>"}]
}
```

The normal content, description, thumbnail, title, tags, visibility, AppID and
Change Notes contract remains. Media edits require `update`, a positive exact
target ID and a snapshot of that same item/AppID; they do not enable CreateItem.
The implementation has no hardcoded product or machine paths.

Every file must match its frozen manifest size/SHA-256, have an absolute path,
be at least 16 bytes and **strictly under 1 MiB (1,048,576 bytes)**, and have a
PNG, JPEG or GIF signature. This is a signature check, not full codec decoding;
product image inspection remains required. The native limit differs from the
web uploader's observed 2 MB limit.

The ordered snapshot and media identities enter the receipt payload hash.
Before creating an update handle, publish re-queries the exact target and
requires the complete index/type/URL/original-filename list to match. It first
replaces existing image previews, then removes requested indices in descending
order, then appends files in plan order. Indices must exist, be unique and
cannot be both replaced and removed. Replacements require an existing image
(`type=0`). File hashes are checked again before setters; any rejected setter
stops before `SubmitItemUpdate`.

Valve's header defines zero-based, sorted removal indices. It does not specify
whether repeated removals reindex immediately or on submission. Descending
removal keeps every lower captured index stable in either case; replacements
run first and additions last. This ordering is tested offline. Actual public
strip order still requires live readback and cannot be inferred from ACKs.

Unknown-submit handling is unchanged: `submit_intent` forbids automatic retry.
A completed receipt cannot be reused with changed bytes or reordered media.
Plans without these fields retain their legacy payload hash; optional empty
arrays alone also preserve that identity. This package does not manage Steam
mode, download fresh cache files, edit existing web Change Notes or accept EULAs.

## Acceptance and primary references

On 2026-10-03, non-loading PE inspection of the installed CK3 DLL found all ten
additional-preview exports. DLL SHA-256:
`1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`;
1,065 exports; UGC `v016`, Utils `v010`, User `v021`. `symbols` now reports
optional media exports/missing symbols and query ABI metadata. Optional missing
media exports do not reject legacy publication during symbol inspection;
media methods bind only when requested.

The focused offline acceptance passed **21 tests** across
`tests.test_native_previews`, `tests.test_steam_native` and
`tests.test_mcp_surface`: exact targets, drift before update creation, mutation
and size limits, order, setter rejection, unknown callback retry refusal,
query cleanup, legacy hashes and official MCP tool forwarding. Callback 3401
uses 280 bytes, including its 256-byte cursor at offset 21. No DLL load,
Steam-mode change, browser or game operation occurred in this implementation.

The first live release must retain the pre-update query, media manifest,
receipt and anonymously read image list. Download the public URLs and compare
decoded pixels and order with the chosen source images; filenames and
`EResult=1` are insufficient. Continue independent title, BBCode, full Change
Notes, fresh subscription-cache and offline-restoration acceptance.

- [Valve ISteamUGC documentation](https://partner.steamgames.com/doc/api/ISteamUGC)
  defines query, preview setters and native image limits.
- [Pinned Valve ISteamUGC header](https://github.com/ValveSoftware/source-sdk-2013/blob/0759e2e8e179d5352d81d0d4aaded72c1704b7a9/src/public/steam/isteamugc.h)
  supplies callback field order and sorted removal-index semantics.
- [Pinned Valve Remote Storage header](https://github.com/ValveSoftware/source-sdk-2013/blob/0759e2e8e179d5352d81d0d4aaded72c1704b7a9/src/public/steam/isteamremotestorage.h)
  supplies the 256-byte URL/cursor constant.
