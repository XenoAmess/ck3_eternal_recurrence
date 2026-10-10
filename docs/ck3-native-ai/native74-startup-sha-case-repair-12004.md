# Native74 startup digest comparison repair (1.20.0.4)

Actual source recording: 2026-10-10T16:05:28.098637+00:00. R0091 original job065b3269-5f7e-4a0a-b27b-8f24783bcd81 failed before native-session-ready with injector rc3, synthetic error1114, nonzero remote LoadLibrary DWORD2326724608 and prepare result0. Exact first failed startup initializer was not captured.

The production adapter copies uppercase `ck3_12004::kExecutableSha256` to the build descriptor. `BindActualArmyPreDatePrefixImage12004`, `BindActualArmyDailyAssaultPreparationImage12004` and `BindActualArmyAssaultPlacementImage12004` compared that digest case-sensitively with their lowercase constants. Each Bind deterministically returned disabled; its Install then rejected `exact_build`. This is a source-proven production startup defect compatible with the observed failure; it does not prove that no earlier initializer also failed. The earlier33 hypothesis was withdrawn: that constant was already uppercase.

Three implementation-local comparisons now accept the same hexadecimal digest with uppercase A–F. Digest identity, source/header constants, wire tags, target RVAs, hooks, ABI and quiescence checks remain unchanged. A different digest is still rejected. No general SHA helper or startup gate was added.

The permanent focused fixture `army_startup_canonical_sha_focus.cpp` calls the actual production Bind and Install paths with the adapter constant. It expects enabled bindings followed by the existing quiescence refusal, before any target read or patch, and verifies rejection of a changed digest. Central10 executes this new regression once; qualification and full Native75 build/live results are pending at this recording. Old observer fixture results are not replayed.

Source/patch/fixture pins and actual results: `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-55/native74-r0091-startup-case-compare-repair/`. Original R0091 evidence: `runtime-01/native74-r0091/launch-fault01/ROOT-ACTUAL-LOADLIBRARY-FAULT-PACKET.json` in the same continuation root.
