# Florin 1.21.0.3 source candidate (2026-11-20)

This is the 1.0.1 source candidate for canonical Workshop item **3812510217**.
The upstream item 3600021457 is forbidden. The published 1.0.0 tag and old reports
remain historical; no new tag, upload, subscription verification or live pass is
granted by this source change.

Machine: `desktop-3fevhd2-1c74096080`. Reviewed installed launcher rawVersion:
`1.21.0.3 (Florin)`, public build `26785313`, EXE SHA-256
`859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`.
The build/EXE tuple comes from the Root installation receipt. PE FileVersion is
1.0.0.0; it is not the launcher version. No Native ABI is qualified here.

The five gameplay scripts, all nine localization files and thumbnail keep their
original exact bytes. Costs, AI prohibition, prestige levels 2/3/4, declaration
target-list ownership, war-local goal capture, defender joining and one title
transaction retain the existing contract. The source change updates descriptor
metadata, pins the actual dependency closure, hardens validator types/metadata
errors, enforces the canonical publishing item, and updates fixture metadata.

The current stock API supports the existing callbacks and target scopes:
`game/common/casus_belli_types/_casus_belli.info:50-86` documents declaration and
war-result callback scopes, target tiers, de-jure goal metadata and neighbors.
`game/common/on_action/war_on_actions.txt:309-312` explicitly gives on_war_started
the declaration scopes. Existing stress calls still have a stock caller in
`game/common/scripted_effects/00_war_effects.txt:3184-3195`, including the attacker
and defender character scopes and medium stress expression. It would be wrong to
rename this builtin merely because it moved out of the invasion CB file.
No new optional holy-war metadata field is needed to preserve this product.

`tools/validate_static.py` records 17 exact stock dependencies: the CB info, three
CB examples, war on-actions, six effect-definition files, four script-value
files, the war-opinion file and the Frankokratia story-cycle definition. Their
actual SHA values and concrete definition lines are in the external candidate
source-audit.json; the same file hashes are executable validator guards.
The old four 1.20.0.3 CB source texts are unavailable here. The retained 292-file
26622941 selection lacks those four and war_on_actions. It does retain
00_war_effects.txt, which is byte-identical to the current file. This review does
not invent missing old text or claim a complete old/new installation diff.

Fresh software checks: actual release static CLI over all 16 runtime files and
nine language formats, the original 13 shared-release tests plus six product
regressions, strict typing of the five affected product tools, typing of the
shared test file, real shared-builder double manifest/ZIP comparison and all
16 retained ZIP member bytes/CRC, and the real CLI manifest verifier. Installed
metadata/source negative cases reject wrong version, bool version, wrong JSON
root, malformed JSON and changed stock bytes. Eight non-Chinese languages only
have format/key checks; no new semantic translation qualification is claimed.

For an uncommitted external candidate, the shared API takes an explicitly labeled
40-hex candidate-content binding in its legacy git_sha field, with git_tag=null.
That binding is not a Git commit. The external candidate-source-binding.json and
manifest.json bind the actual reviewed sources and patches. This reproducible
NoGame artifact is not an exact-tag formal release. Integration must recheck the
per-file pins, commit normally and create a fresh formal artifact later.

Fresh installed-source check:

```text
python -B -X utf8 mod_de_jure_conquest/tools/validate_static.py --game "C:/SteamLibrary/steamapps/common/Crusader Kings III" --release-localization
python -B -X utf8 tools/test_independent_mod_release.py
python -B -X utf8 mod_de_jure_conquest/tools/gen_acceptance_fixture.py --output <fresh-external-directory>
```

The existing generator emits 72 distinct business PASS markers: three tiers,
three outcomes per tier and eight checks per cell. BEGIN/DONE are not additional
business assertions. DJC-01 through DJC-13 in test-plan.md are complete acceptance
obligations, not thirteen markers. The basic-load case has a zero-day bound and
explicitly excludes business coverage; it remains unchanged.

All new game, matrix, GUI, payment and Save/Load checks remain NOT_RUN. The
follow-up fixture source now implements two-day reset/actual readback, stress
zero, conditional restoration of originally independent Naples, known visible
completion/failure pause windows and bounded fresh tiers. Three separate fresh
tiers retain the original72 predicates as24 each, nominal16/max18 natural days;
the default all-tier contract remains72 but nominal46/max48 and can encounter
Robert's earliest day35 event. This is software preparation, not a fresh-game
pass. Follow [the exact tier recipe and unchanged acceptance gaps](fixture-florin-121003.md).

The fresh acceptance contract remains all DJC-01--13: exact mod/no-mod load and
diagnostics; prestige boundary availability; AI refusal; exact resources below/at
cost and actual native GUI declaration payment; exact participants and de-jure
county/title/liege transfers with outside titles protected; victory at all three
tiers; white peace, defeat and invalidation/truce consequences; attacker and
defender death plus real physical Save/Load continuation; concurrent-war
isolation; actual automatic-army stages; simplified-Chinese confirmation/result
GUI with zero raw localization keys; and coexistence with other maintained mods.
Scripted start_war/end_war preparation does not cover native GUI declaration or
peace legality/payment. Existing conditional CB previews and total payments must
be measured separately. Old 1.20 reports do not grant this engine qualification.
