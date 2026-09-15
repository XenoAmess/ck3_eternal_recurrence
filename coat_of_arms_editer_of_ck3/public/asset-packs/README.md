# Web asset packs

The production browser reads `ck3-coa-web-asset-pack-v1` manifests from this directory.
Generated CK3 packs are deliberately ignored by Git because they contain game assets and
require a separate distribution-rights decision.

Generate a local Alpha pack with Python:

```text
python coat_of_arms_editer_of_ck3/tools/build_web_asset_pack.py --game-root "<CK3 installation root>" --output coat_of_arms_editer_of_ck3/public/asset-packs/ck3-1.19.0.6
```

The resulting static site no longer reads or launches CK3. Vite copies this content-addressed
pack into `dist` as ordinary static files.

