# Integrated candidate revision 003 — frozen source review package

This fresh external successor preserves the repaired I3b70 candidate, C2/C3 display changes and both-direction locks. It replaces the shared validator with independently verified authored SHA `089a6004c48dd5ae8e207827cb130caa41044640c20b7b200100f308039d74a1`, adds actual negative product regressions, and applies the approved 30 text fields plus dated source-boundary correction. Root alone may import the exact delta into tracked source.

Baseline: supplied frozen `3d3305e75cf642a7a82bef5f9aee03dc76b3c10e`; parent states root HEAD `bfe0514650dbb446f6cab2a8543d3e4bf1582aff` leaves LYD unchanged. No Git command was issued here. `before/` has 139 exact files; `candidate/` has 154 files. `DELTA.json` binds all 53 differences from baseline; `REVISION-DELTA.json` binds 11 differences from frozen002, including exact before/after SHA and size. `SOURCE-INDEX.json` binds the complete source trees. `patches/` contains one reviewable text diff per baseline delta. The single workflow institution-test line is inherited from frozen002; its baseline delta is still present. Validator regressions execute through existing `test_build_release.py`, so there is no duplicate workflow command.

`checks-003/report.json` is the freeze-ready result: **161 tests / 13 actual commands GREEN** (155 product tests, 6 external integration proof tests). Five generator checks, static validation and deterministic double build all pass. Source inputs are stable before/after. `checks-001` retains the first 159-test run and `checks-002` the 161-test run before making boundary inputs self-contained. Original frozen002's report claimed 14 commands, but its actual report has 13; that old report was preserved unchanged and its validator remains unsuitable for admission.

| Actual L0 command | Exit code |
| --- | --- |
| tool-tests | 0 |
| runner-tests | 0 |
| school-consent-tests | 0 |
| content-leadership-tests | 0 |
| institution-tests | 0 |
| content-generated-check | 0 |
| runtime-generated-check | 0 |
| static | 0 |
| build-check | 0 |
| school-consent-generated-check | 0 |
| leadership-generated-check | 0 |
| institution-generated-check | 0 |
| integration-boundary-tests | 0 |

Production staging: **70 runtime / 889 bilingual keys / 68 events**; manifest SHA `b2e61e8faff036fa28ceea7c38d667ce5cc2d1f6555544ecf837618d7ea99c47`; deterministic ZIP SHA `c8749c5a2607cfa38dd3e6dac02ad9649d34304e077d4787b42521bea122b77e`. External harness uses the supplied frozen baseline revision rather than optional Git lookup; this is provenance input, not a claim of a committed release or native acceptance. `production-staging-003/` contains the actual formal projection.

Validator proof requires `=` for positive helpers and containers; OR branches retain their complete key/operator/scope; structural Block extraction requires `=`. Opaque wrappers, predicates, tooltip-only bodies and negative helper calls cannot invent a game operation. Operation proof uses a conservative vocabulary covering the current product and fixture. It is not a complete native registry or native scope checker. Independent variant001 and variant002 patches, indexes, actual 51-variant/9-fixture receipts and old false-GREEN results are preserved under `inputs/`. `pre-fix-probe-001` preserves local failures and explains two initial diagnostic-message assertion mistakes without treating them as source false-GREEN findings.

Content authority before/after SHA is exact. External boundary tests restore precisely the 30 reviewed text constants and prove the entire two author ASTs then equal frozen002; IDs, schema, options, resources and source URLs remain equal. Current `gen_content` reproduces the writer's four exact projections. Current `gen_runtime` additionally changes one English rite-name value in runtime localization and one in I3b localization. All 70 runtime script ASTs and all nontext bytes remain equal to frozen002; localization keys are identical. No old59 tree or generator replaced I3b70. The dated source note retains unverified historical citation boundaries.

I3b execution preserves actor/nonce/serial barriers, all alive human consent, every school's two-thirds approval, representative eligibility distinct from native HoR, title protection and cancellation ownership. C2/C3 display stripping retains original business AST; cross-flow locks and native factories are byte-preserved. I3b effect guards and mutations stay inside `hidden_effect`, and preview descriptions are read-only. Native gate remains **CLOSED / NOT_RUN**. No tracked source, Git, game, native bridge, CI, PowerShell or agent spawning occurred. Historical RED/partial/preparation attempts remain intact; `OLD-INPUTS-VERIFY.json` proves old002 and content package indexed bytes remain unchanged.

| Revision 002 → 003 path | Before SHA | After SHA |
| --- | --- | --- |
| `mod_li_yu_dao/common/religion/rite_types/lyd_rites.txt` | 929fb9f7cc6df5a7e8a1acfcc07b43ace9a397bb22246e6884884d5920762a20 | 1106d2e9b06bbddb6cc3ab663d19b2e4e7863325ec63d67c776c694eb513ca17 |
| `mod_li_yu_dao/common/religion/tenet_types/lyd_tenets.txt` | 410f0c593aa47bec13ae1d85fde9d956aae1a12bd6a2a4d6c1b4767cfc0c15de | 1a2b4a4f4729b2ac475c1c2a70a3734525ecd31ae50861b002adcf1003a2920e |
| `mod_li_yu_dao/docs/content-copyedit-2026-10-05.md` | NEW | 7f109836af799e4e5aa79572808e8a766fc85dcfe81b1bb12e6d9f35784619c5 |
| `mod_li_yu_dao/localization/english/lyd_content_l_english.yml` | 833fcdb277cfa8a736aa94077a5df1adc0c16dbe6834ef89cdc0a62180337c98 | 287498e26ddd657db91d1fded99ca671628ef2409f7f56aa86110cabd63d4a78 |
| `mod_li_yu_dao/localization/english/lyd_i3b_institution_l_english.yml` | e54154dfe0a0f26ea167e2c21c4d70634b105c97681d4d8bae63905b17178009 | 1a370a05c02c14204df309acb8c162ed9651e622ccd848c3181809f3fb1053ac |
| `mod_li_yu_dao/localization/english/lyd_runtime_l_english.yml` | d76b648c16a763266ca202c97a00a48e24c72b7b3be291d288d5e2e4134fab0a | f2959daa69931f05633bb5c2280b36a2789858b0977360301388efe0794e0199 |
| `mod_li_yu_dao/localization/simp_chinese/lyd_content_l_simp_chinese.yml` | a28e41c0d4d58116e9bb81882223fe73817cedd5ce9f808384d367180e577972 | 4e93e04d6c894eb549f807bbde9ea1f13a0d43cac202ca30efbcf18221db799f |
| `mod_li_yu_dao/tools/additional_practices.py` | 86354f2d9a116c82710e52201ccc51edcd4f1d9ff0156bbfb446adbac4172e42 | cbae8ccf96a33d893ab2c8084ab09046aa34c46596f41ac7241429d2ca56d583 |
| `mod_li_yu_dao/tools/content_data.py` | 67bc8bbd5f518f29de5de776505c05c16122ffaab3cdc933fedc4a90fbbd66de | cb368c771dc4b99a612e560b9bb4ce04992a403c7598f24d9ae3aaeae4bcda73 |
| `mod_li_yu_dao/tools/test_build_release.py` | f552e553823f6e1e3d09d0af4df894b2454e90aca62b091db2672f0a7e8b3f46 | 18eec05254e9a537b97089c237c4886775ed1f0d432ae38a1abbb83d07d75fe4 |
| `mod_li_yu_dao/tools/validate_static.py` | 985c04f081b011d170821ea69dd8139a9f90dd1637553fa55bfde5c95ae8a186 | 089a6004c48dd5ae8e207827cb130caa41044640c20b7b200100f308039d74a1 |

Independent review must bind this complete frozen INDEX before admission; this authored/L0 report does not replace native evidence. No native publication or runtime capability claim is made.
