# Celestial Commerce & Corruption 1.0.0 acceptance

## Result

Local source acceptance is **GREEN** on CK3 `1.19.0.6`. The repository owner attested on 2026-09-20 that the upstream author granted redistribution and maintained-release permission; the source artifact remains pending archival while the owner is away, and publication proceeds on that attestation as directed.

## Compatibility repairs

1. Removed the stale `feast.txt` override. Vanilla 1.19 already contains barter-aware feast costs, while the upstream copy deleted current house-aspiration, accolade, background, free-feast, and cost-routing behavior.
2. Removed the stale `window_county_view.gui` override. Its single display change did not justify replacing a county window missing current shortcuts and building templates.
3. Rebased `celestial_government` on the exact installed 1.19.0.6 block. The static gate proves that the only semantic delta is `barter = yes`.
4. Replaced removed `active_accolades` with current `accolades`, and restored `allow_as_base_for_baronies`, `allow_accolades`, house aspirations, and current government flags.
5. Migrated the decision from block-form `ai_check_interval` and a one-day test cooldown to integer `36` months and a three-year cooldown.
6. Namespaced all additive gameplay identities and repaired the localization key format, hard-coded Chinese option, and behavior/copy mismatch. The contract now states percentage-point tax-rate reductions rather than an immediate gold grant.

## Automated evidence

- Release builder unit tests: 8 passed.
- Deterministic staging before the localization-only release expansion: 15 runtime files; two independent builds produced identical manifest and ZIP bytes. The final nine-language projection contains 22 files and is rechecked by the L0 release gate.
- Static gate: GREEN, including exact installed-government comparison, no stale activity/GUI overrides, four tax tiers, event/trait wiring, UTF-8/BOM rules, DDS headers, and frozen upstream-derived asset hashes.
- Live run: `oxa_20260920_094648_f8ba6adb`; report SHA-256 `3EE80181291298D9894520F4AC3DBED35587CBE1B30D15DC514F653EFC99AE35`.
- Game executable SHA-256 before and after: `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Exact product runtime tree SHA-256 before and after: `32C3EE4549E809E51CF5E53CFD49F54F7C1015139479713948D54EBF5D65FA7E`.
- Product and fixture trees unchanged; real profile, Steam cloud, and registered Workshop storage unchanged after the quiet period.
- No product-attributed parser, GUI, or database-conflict diagnostics.

The live runner used an isolated user directory and the exact then-current 15-file gameplay projection plus an external acceptance fixture. The seven files added afterward contain localization only; they do not alter the six gameplay scripts or Chinese UI bytes exercised below. Through the native UI it:

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

## Remaining publication gates

- Create a new Workshop item under the maintainer account; never upload to upstream item `3596263413`.
- Upload only the deterministic staging, verify the fresh subscriber cache, publish and anonymously re-read exact Change Notes, then write the final repository changelog with the new item ID and public evidence.
