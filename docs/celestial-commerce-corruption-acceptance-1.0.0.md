# Celestial Commerce & Corruption 1.0.0 acceptance

## Result

Release acceptance is **GREEN** on CK3 `1.19.0.6`. Version `1.0.0` is public as maintained Workshop item [`3804807463`](https://steamcommunity.com/sharedfiles/filedetails/?id=3804807463); upstream item `3596263413` was not modified. The repository owner attested on 2026-09-20 that the upstream author granted redistribution and maintained-release permission; the source artifact remains pending archival while the owner is away, and publication proceeded on that attestation as directed.

## Compatibility repairs

1. Removed the stale `feast.txt` override. Vanilla 1.19 already contains barter-aware feast costs, while the upstream copy deleted current house-aspiration, accolade, background, free-feast, and cost-routing behavior.
2. Removed the stale `window_county_view.gui` override. Its single display change did not justify replacing a county window missing current shortcuts and building templates.
3. Rebased `celestial_government` on the exact installed 1.19.0.6 block. The static gate proves that the only semantic delta is `barter = yes`.
4. Replaced removed `active_accolades` with current `accolades`, and restored `allow_as_base_for_baronies`, `allow_accolades`, house aspirations, and current government flags.
5. Migrated the decision from block-form `ai_check_interval` and a one-day test cooldown to integer `36` months and a three-year cooldown.
6. Namespaced all additive gameplay identities and repaired the localization key format, hard-coded Chinese option, and behavior/copy mismatch. The contract now states percentage-point tax-rate reductions rather than an immediate gold grant.

## Automated evidence

- Release builder unit tests: 8 passed.
- Formal deterministic staging: 22 runtime files. Manifest SHA-256 `0668F42F11DDFBB06672B2033C8E987120E9F9087992FBBA358B3FE22DC0B981`; ZIP SHA-256 `4EA81245BCB8713B5D3C6B1FA179554DA72745A2125D5A7AD37142B36DCB8FF9`.
- Static gate: GREEN, including exact installed-government comparison, no stale activity/GUI overrides, four tax tiers, event/trait wiring, UTF-8/BOM rules, DDS headers, and frozen upstream-derived asset hashes.
- Live run: `oxa_20260920_094648_f8ba6adb`; report SHA-256 `3EE80181291298D9894520F4AC3DBED35587CBE1B30D15DC514F653EFC99AE35`.
- Game executable SHA-256 before and after: `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Exact product runtime tree SHA-256 before and after: `32C3EE4549E809E51CF5E53CFD49F54F7C1015139479713948D54EBF5D65FA7E`.
- Product and fixture trees unchanged; real profile, Steam cloud, and registered Workshop storage unchanged after the quiet period.
- No product-attributed parser, GUI, or database-conflict diagnostics.
- Fresh Workshop cache run: `xcca_20260920_122939_5bfbb8df`; report SHA-256 `2340929D8DF9B583E31B8AED85203A7A63178D186539B3293AB544AB2DCC979D`.
- Fresh-cache product tree SHA-256 before and after: `1549D2B5CA9D00E29969D2960668F91345247E1F1AEF331DF84BF15B425DF049`; external fixture tree SHA-256 before and after: `AB0F4CEC4636117B44E9F666232BEEBC10F326F31CFBF06EB7E84763F1D8C4A0`.
- Fresh-cache product/fixture/source trees were unchanged, the disposable userdir was removed, protected storage remained unchanged through the five-second quiet period, and CK3 stopped.

The source runner used an isolated user directory and the exact then-current 15-file gameplay projection plus an external acceptance fixture. The seven files added afterward contain localization only. The final subscriber-cache runner loaded the public 22-file tree plus the same external fixture and repeated the complete Simplified-Chinese production path. Through the native UI it:

1. proved the Song celestial government returns `government_allows = barter`;
2. switched to a current-build landed celestial official;
3. opened and confirmed the production `定夺贪墨之策` decision;
4. selected the production fourth-tier option;
5. proved `xccc_corruption_4` was applied; and
6. evaluated the production constants from `0.75 - 0.25` to exactly `0.50`.

Open Kaishek parsed the six-file fixture without parser diagnostics but its unreleased validator reported the fixture directories/opcodes as unsupported with `fixture=none`; that advisory result is retained as not-applicable rather than represented as GREEN. CK3 itself loaded and executed the same bytes successfully.

Live gameplay/UI acceptance is intentionally limited to Simplified Chinese. English and the other seven release translations are covered by the static localization audit; they are not CK3 live-test targets, and this record makes no multi-language live-validation claim.

## RED lineage

The first isolated attempt, `oxa_20260920_093543_9600d3c1`, was preserved as RED. The reusable marker reader still filtered the previous fixture's `TEA:` prefix, and queued GUI state execution could invoke the player switch twice. The second attempt introduced an `XCA:` marker stream and idempotent pending-flag guards; it did not overwrite the RED evidence.

The first fresh-cache attempt, `xcca_20260920_121115_b07ef63a`, was also preserved as RED even though its product cell was GREEN. Steam briefly held `remotecache.vdf` without read sharing during protected-storage postflight, so unchanged storage could not be proved. Commit `d97842c5433903ea45d188572700bb4c7f2aafb2` added bounded `PermissionError` retries without accepting a missing, changed, or persistently unreadable file. The independent Chinese-only rerun then completed fully GREEN.

## Workshop publication

- Native Steamworks create and submit returned `EResult=1` for new item `3804807463`; no legal agreement remained outstanding. Receipt SHA-256: `3F58242C7E269FED3E1275491B0B89954FAB2EB2AC47390C59EC4A8CEC7D04D9`.
- Anonymous readback matched the exact public title and all 1,734 normalized main-description characters, including the explicit `1.0.0` changelog section. Description SHA-256: `4C17C2CB2A54811EF12EB33C9E2E37DEC01EDF0FB426813B99AF82F1D248CA43`.
- Public Change Notes entry `1789875616` matched all 366 characters and 11 lines. Normalized SHA-256: `31BFDD2617FB05CDCC39FB87DED0E6A80D05B9692F211B917B388F53A64D1BEA`.
- Steam recreated the previously absent cache and strict ID-bound verification passed 22/22 files. The cache evidence SHA-256 is `0638C58158F1B8572923F37FAF7A9902B76FCEB8505FB42F8B47783CEB418ED8`.
- Steam returned to Offline Mode. The native probe reports `BLoggedOn=false`, `WantsOfflineMode=1`, `RunningAppID=0`, and CK3 process count zero. Final attestation SHA-256: `4CB8D6F69599459C8FB9D2CE444CC12408F4A0A3F0CAD34336BA14FECA6018C9`.
