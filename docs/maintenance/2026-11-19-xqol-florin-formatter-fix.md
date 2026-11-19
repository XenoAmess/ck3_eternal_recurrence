# XQOL1.1.3 Florin formatter source candidate

machine_id: desktop-3fevhd2-1c74096080
Observed source date: 2026-11-19. Target CK3 1.21.0 Florin/build26622941,
EXE SHA2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc.

This unpublished1.1.3 candidate adds only an independently owned118B Simplified
Chinese localization replacement plus packaging/validation/regression metadata.
Existing xqol-v1.1.2 is a frozen historical candidate, not a tag to move. No tag,
Git or Workshop operation is performed by this work package. Production core,
slider UI, interactions, predicates, payment values, source generators and all
existing live-case assertions remain unchanged.

The current stock localization/simp_chinese/house_relations_l_simp_chinese.yml:142
defines house_relation_latest_change_amount with #weak immediately followed by
the Chinese left parenthesis. Its19485B source SHA is
952a1b95e24720724a5bc794cf71efd74b9e88e640f5da11d7de8076f2c3dbc4.
English:156 has the separator after #weak. The XQOL replacement adds that single
ASCII U+0020, preserving Chinese parentheses and
[HOUSE_RELATION.GetLatestChangeAmount|=+%^] exactly. The new file is
localization/replace/xqol_florin_house_relation_l_simp_chinese.yml, UTF8BOM+
l_simp_chinese header, SHA41ba1efe9cc6c295a83522ab032edcc3bd71b3c3c7afddff88a9ae2f5fa5a982.
It has the same reviewed118bytes as AUB's independent replacement, with no AUB
runtime dependency. It is additive to the strict XQOL runtime allowlist27→28.

The builder and standalone release-localization gate require those exact bytes,
including BOM/header/one space/full expression/one key. Mutation regressions
reject missingBOM, wrongheader, removedspace, alterednumeric flags, missingclose,
extrakey and duplicatekey through actual source, localization and build guards.
Nine normal language keysets remain unchanged; the tenth localization file is
this one reviewed stock-key replacement, not a new language or business string.

R4 original profile:
D:/ck3-state/upgrade-20261118/gui-state/gui-ecd8f919b27d48f9a599a4b779eea575/profile.
Original error.log1530B/SHA
d50e1b904b6609d05a2549120ae2352f8a24ca87b2dba31de0c8512dc89503c2 contains17
formatter records with weak/backspace/control-negative_value,14 at18:58:34 and3
at19:01:44. Original debug.log SHA
930c204af81f8e62a298de65b9c0f1b6c49d19100633cd6252e2471cf5f497f0.
No record identifies a localization key or script stack. The source defect and
signature agree, but this is not proof that all17 records came from this key.
Original bounded core successes, raw diagnostics, product-release false and
uncompleted UI scope retain their original truth. No R4 raw-zero requalification.

Fresh work required: Root adopts this exact candidate in a new scene, preserving
all original core markers/assertions and60-day cap. Read an actual negative
house-relation latest-change value, render its stock news/tooltip through the
permitted current channel, retain the underlying relation/object and exact
display/log evidence, and evaluate the complete unfiltered error.log. A synthetic
localized-string sample, a build or AUB's separate zero-formatter result is not
XQOL runtime proof. Keep fresh core, complete remaining slider/defense/governor
UI, normal closure and product acceptance separate; all are NOT_RUN here.

The complete production payload before this new118B file is991149B, including
768568B thumbnail. A new complete staging plus this candidate exceeds the1MiB
work-package cap even before ZIP/manifest/TEMP. Therefore full real-product
builder/double-ZIP, Game, Native ABI, GUI, tag, upload and subscription cache are
NOT_RUN. Full static validation composes exact changed text with the pinned
read-only original source/stock and reads the original PNG; no large copies or
placeholder product artifacts receive production qualification. Unit builder
fixtures use tiny assets only and are reported as such.

All changed paths bind independent base/target SHA pins; Root may change other
files/HEAD concurrently. Adoption requires those exact path pins, not a claim
that the whole repository was frozen. Output/TEMP stays under the explicit1MiB
D-volume reservation. Policy1.0.0 record review is180days; reads do not renew the
historical profile or raw-log retention lifetime.
