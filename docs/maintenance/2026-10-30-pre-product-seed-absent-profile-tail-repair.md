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
