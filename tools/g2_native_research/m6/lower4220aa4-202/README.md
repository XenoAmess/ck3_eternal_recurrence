# M6 manual native witness 202

This Windows x64 fixture executes two externally supplied, previously verified normal bodies in private memory: 12 direct profiles for the 194-byte reverse leaf and two same-RAM profiles through its 126-byte caller. It is a standalone capture program, with no game bridge or default CI wiring.

The executable, original body bytes, assembly and built binaries are not distributed here. Verify both external inputs before running. The CLI checks exact lengths; its caller must check these SHA-256 values separately.

| Input | Bytes | SHA-256 |
| --- | --- | --- |
| Reverse leaf `[4220AA4,4220B66)` | 194 | `84d1fd764c92185dab2ad410375479acb4e657d1847674e98ce0cf5615fe68b3` |
| Caller `[9D0950,9D09CE)` | 126 | `7cf624784877e13a583ba7675383f324e7e7d7786522046f0cfdfd064377a0d0` |

Build from this directory in an x64 MSVC developer command prompt:

```bat
cl /nologo /c /std:c++20 /EHsc /W4 /WX /O2 /utf-8 Native202Execute.cpp Native202Io.cpp Native202Main.cpp
link /NOLOGO /MACHINE:X64 /INCREMENTAL:NO /OUT:Native202Witness.exe Native202Execute.obj Native202Io.obj Native202Main.obj kernel32.lib
Native202Witness.exe <verified194-body-path> <verified126-body-path>
```

The harness reserves an image of `0x5430000` bytes and commits three image pages: two code pages become RX, and the controlled feature page becomes RO or inaccessible. Each case uses a separate 4 KiB data allocation with boundary sentinels. The input code remains unchanged. CPUID, OSXSAVE, XCR0 and AVX2 eligibility gate the five bit-5-on profiles; unsupported profiles are listed as skipped. The feature word is controlled fixture input, not a claim about the natural program's feature state.

Successful capture emits JSON rows and measured guards. Exit zero alone is not an expected-row comparison. The first private validation executed all 14 profiles with zero skips and AVX2 eligibility true; comparison with independently frozen owner rows and already captured Java rows produced 42 pairwise comparisons with zero differences. The source hashes, first intervals and model grades are preserved in [VALIDATION.json](VALIDATION.json). Publication does not repeat those runs.

Native observations cover final RAM DWORDs, raw RAX, CPU eligibility and the `rawUnchanged`, `protectionsFinal`, `mappingReleased` and `memoryGuard` checks. Pointer-role normalization was fixed before execution. Native access order and vzeroupper counts are not instrumented; Java access-trace checks are separate evidence. Inputs are finite, aligned ranges of 0 to 96 bytes. These results do not establish arbitrary invalid or concurrent memory behavior, full ABI/EH support, natural Game behavior, M6/G2 completion or seconds per saved game day. Expected rows are owner-led; rejected model oracle attempts receive no independent-oracle credit.
