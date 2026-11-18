# GUI-only Workshop cache preparation uses disk identity

More Tenets Slots v12 reached exact native download/file validation on CK3 1.21.0/build26757580/EXE `bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79`, but its common GUI-only cache preparation failed because `_engine` admitted only native-wire registry identities. The earlier 1.21.0/2F2B identity does not qualify this executable's native ABI. Source and independent cold-load GUI runs had already passed; those conclusions remain product-specific.

The explicit shared GUI-only cache context now selects a disk metadata reader. It compares the configured EXE SHA and launcher version/path with the pinned shared GUI manifest, then checks actual Steam app1158310, installed StateFlags4 and exact selected build ID through the existing VDF parser. The native path and native build registry remain unchanged and reject unqualified executables. This adds no DLL, native bridge, offsets, gameplay capability, or launch authority.

Validation: 33 focused GUI/cache/preparation/fixture tests pass. Counterexamples reject EXE tampering, wrong launcher version/path, wrong Steam app/build/state, absent manifest and missing selected metadata; the same synthetic unregistered EXE continues to fail native preparation. The new reader passes strict mypy. Actual cache process acceptance is still pending at this software commit.

Ownership: the reusable identity distinction and regression belong here; product sources, raw machine receipts and private saves stay in the [independent product](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/live-report-2026-11-19.md). This report does not infer that other products passed. Earlier completed runtime/tool identities and the failed cache-preparation attempt remain historical evidence.


## Actual product cache result

The independent More Tenets Slots v12 cache run R0003 subsequently passed on this exact CK3 1.21.0/build26757580/EXE bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79, using framework d5dfb281f. Steam downloaded the published item3182367229; all48 files matched the tagged formal tree. The common GUI-only preparation admitted the actual disk identity, and engine logs confirmed Enabled plus Mounted Data directly from the Steam Workshop cache. The main menu was reached and normal GUI exit returned0 from the original process at 2026-11-18T21:36:29.338882Z; keeper exited and the screen lease was released. No campaign or business cases were repeated for this cache check.

The [published product evidence](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/104b907/docs/workshop/publication-v12.md) and [cache evidence](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/104b907/docs/evidence/upgrade-20261119-cache-live.json) retain the first preparation RED and separate source/cold gameplay acceptance. Full public description, Change Notes and tags matched after publication; final Steam background probe was offline. These are this product's results. This disk-reader fix grants no native ABI or gameplay capability qualification and does not establish acceptance of other products.
