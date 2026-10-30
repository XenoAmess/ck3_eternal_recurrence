# Pre-product seed completion repair

- machine_id: desktop-3fevhd2-1c74096080
- Observed: 2026-10-30T16:19:41.538265+00:00
- Qualification base: bae151d2c7de49fa946eb8e968cf49d34cf9e331.
  Target and loaded dependency blobs match qualified base 9ae14e43 exactly.
- Frozen game source: c3e46759b397f2f1950b6b46066a67c2df631dcb; that runtime was not modified.

R43 completed its zero-day pre-product seed Native Save and independent Java
readback, and Root accepted the four original phase assertions. The shared
adapter then raised FileNotFoundError while unconditionally pinning
profile/mod/product.mod. The case remained ERROR with business_pass=false.
Original evidence is retained in the R43 case-output/case-error-preserved.json
under resume-product-a20/runtime-a20/retest-source100-a01 on the named machine.
R43 subsequently completed its original normal-close lifecycle; SCREEN release
was 10055. These observations do not grant a repaired-runtime live pass.

The existing fixture-case completion now follows the declared product_loading.
For absent, it rechecks the original absent product paths and writes explicit
JSON null for product_outer and product_inner. For present, both actual descriptor
Pins remain required. No product placeholder, runtime patch or business-state
change is introduced. The generic verifier already accepts JsonValue null and
preserves both fields; the distinct Workshop cache route keeps its existing Pins.

The regression uses actual prepare_case, run_case, persisted JSON and verify_case
with authored offline transport. It exercises the zero-day seed requirements for
absent and present, checks explicit null versus real Pins, and keeps business and
release acceptance false. Against frozen Source100 the same new test reproduced
the original product.mod FileNotFoundError. No test double replaces the production
completion path.

Mainline qualification on the named machine:
- Complete tools/test_prebuilt_fixture_prepare.py: 12 tests, exit 0.
- Complete modified test: mypy --strict --strict-equality, exit 0.
- Complete adapter: existing CI mypy --follow-imports=skip, exit 0.
  Existing untyped function bodies retain their original checking boundary.

The small mainline candidate and original process waits are at
D:/workspace/ck3-des-seed-absence-mainline-a02. The earlier frozen-source candidate
and the expected RED reproduction are at
D:/workspace/ck3-des-seed-absence-candidate-a01. D's original worktree, HEAD and
index were preserved; submission used a separate temporary Git index.

Qualified code SHA-256:
- tools/ck3_mod_acceptance_cases/generic_product_adapter.py: 670c521a4ab1f81d73cf7351f1b87632431c7539e4a870741a9344b6251e205a
- tools/test_prebuilt_fixture_prepare.py: 58ff669cd51bed5c0d08a15437ff31ab5b4f1ac8d5e35695ec50d486d67749a2

Continuation observation: 2026-10-30T17:20:09.872132+00:00; machine_id unchanged.

The repair was published by ordinary fast-forward push as
3a422e35d694b1686f64c06eff1c7cac5ff74028. Subsequent official CI exposed existing
fixture defects: the strict recovery AST omitted new registry dependencies, and
Windows short TEMP names differed from the canonical paths in produced Pins.
91dcdb4037432f16c7e17a6cc9d619e37ef1d083 and
5253dc46f4b1c67d72bbc01539620535fea71919 repair the tests. The latter resolves the
recorder fixture root before producing any inputs. A real system short TEMP alias
reproduced the old rejection; the existing three-guard producer/consumer roundtrip
then returned 0. The production identity and invocation/wait guards remain intact.
The earlier official RED runs and original waits are retained.

Official qualification for exact code commit
5253dc46f4b1c67d72bbc01539620535fea71919:

- [Dynastic Esotericism Static](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/41096284777): success.
- [Religious Ritual Fusion Static](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/41096278292): success, including all 64 shared fixture/compatibility tests and strict types.
- [Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/41096125475): success.
- [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/41096125757): in_progress at this record's observation; no pass credit. This unrelated long suite continues automatically and was not cancelled or used to delay the required repair delivery.

CI terminal receipts and the short-TEMP regression waits are under
C:/ck3-dynastic-esotericism-20261024/resume-product-a20/core-a30-administration/mainline-ci-closure-a03.
An explicit small-output limit was exceeded when a filtered Git fetch unexpectedly
created a derived pack: the observed total was 5287404 bytes against 1048576.
The exact new pack/index were removed after preserving their Pins and the needed
small objects; recovery measured 765195 bytes before its receipt. The original
peak is not qualified. DERIVED-FETCH-OVERRUN-RECOVERY-a01.actual.json preserves the
failure and recovery. No D Git objects, worktree, HEAD or original index were
written during this continuation; later commits use C-owned indexless objects.

The separately authorized local Azur/RICE/POD cleanup removed 6098409520 bytes,
19263 files and 1130 directories, with individual original exits 0. Its exact
scope and receipts are in the [cleanup record](2026-10-30-workshop-unused-local-cache-cleanup-desktop-3fevhd2-1c74096080.md).
This cleanup and static qualification do not turn the original R43 ERROR into a
repaired-runtime live PASS. Further live acceptance remains outstanding.
