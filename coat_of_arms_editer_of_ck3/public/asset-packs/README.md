# Web asset packs

The production browser reads `ck3-coa-web-asset-pack-v1` manifests from this directory.
The project owner confirmed on 2026-09-15 that the original DDS pack may be versioned and
published by this repository. The exact CK3 1.19.0.6 pack covers all 1,630 DDS files under
the base-game CoA tree. Its 42 patterns and 1,577 clipboard-safe designer-registered colored
emblems are searchable. One registered high-byte filename, eight unregistered colored files,
and two render-support files are preserved but not misrepresented as fit candidates. Other
generated build directories remain ignored.

Generate a local Alpha pack with Python:

```text
python -m pip install -r coat_of_arms_editer_of_ck3/tools/requirements-pack.txt
python coat_of_arms_editer_of_ck3/tools/build_web_asset_pack.py --game-root "<CK3 installation root>" --output coat_of_arms_editer_of_ck3/public/asset-packs/ck3-1.19.0.6
```

The builder also emits a SHA-bound 32x32 RGBA fit index, allowing the browser to search the
complete registered library before fetching selected full DDS files. The resulting static site
does not read or launch CK3. Vite copies this content-addressed pack into `dist` as ordinary
static files. Verify every pack before committing or deploying it.
