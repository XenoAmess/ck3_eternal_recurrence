# M6 manual native witness 203

This Windows x64 fixture runs the 351-byte upper, its 126-byte range caller and the 194-byte reverse leaf together in one private image and the same data RAM. Seven new whole profiles cover empty input, middle insertion, append, a front AVX path, exact capacity, source aliasing and growth. The sources are a standalone capture tool, with no game bridge or default CI wiring.

No original executable, body bytes, assembly or built binary is distributed here. Verify the four private inputs before invoking the CLI. It loads each input and checks exact size; its caller must verify file size and SHA-256 independently.

| CLI input | Bytes | SHA-256 |
| --- | --- | --- |
| Upper `[ADD0D0,ADD22F)` | 351 | `640d693377bdb24ad17d176109b437481cc7546458a4797b9d89cba52f30d75e` |
| Caller `[9D0950,9D09CE)` | 126 | `7cf624784877e13a583ba7675383f324e7e7d7786522046f0cfdfd064377a0d0` |
| Reverse `[4220AA4,4220B66)` | 194 | `84d1fd764c92185dab2ad410375479acb4e657d1847674e98ce0cf5615fe68b3` |
| Float material `0000c03f` (1.5) | 4 | `c0e336a5f371ef22cd534e094269f2c1a9635cd080b71ffa671086832d3b60b7` |

Build from this directory in an x64 MSVC developer command prompt:

```bat
cl /nologo /c /std:c++20 /EHsc /W4 /WX /O2 /utf-8 Native203Execute.cpp Native203Io.cpp Native203Main.cpp
link /NOLOGO /MACHINE:X64 /INCREMENTAL:NO /OUT:Native203Witness.exe Native203Execute.obj Native203Io.obj Native203Main.obj kernel32.lib
Native203Witness.exe <verified351-body-path> <verified126-body-path> <verified194-body-path> <verified4-literal-path>
```

The image reserves `0x5430000` bytes and commits six pages: four RX code pages, one RO literal page and a controlled feature page that becomes RO or inaccessible. Each case has a fresh 4 KiB data allocation. The three supplied bodies and float material remain unchanged. A COPY trampoline uses an explicit snapshot effect bounded to 80 bytes; allocator virtual slots 8 and 16 use controlled callbacks. Those effects do not establish the natural COPY or allocator implementations. Callback captures are bounded, pointer roles are explicit, and the active callback context and MXCSR rounding mode are restored by scope guards.

Host CPUID, OSXSAVE, XCR0 and AVX2 eligibility gate the front AVX profile. An unsupported host reports that profile as skipped instead of altering the feature input. The feature word is controlled fixture RAM, with no claim about its natural value.

Exit zero reports successful capture and invariant checks, not an expected-row comparison. The first private validation executed all seven profiles with zero skips and AVX2 eligibility true. Final header, RAM and typed callback outputs matched independently frozen owner rows and already captured Java rows: 21 pairwise comparisons, zero differences. [VALIDATION.json](VALIDATION.json) preserves source hashes, first stage intervals, measured guards and model grades. Publication does not recompile or repeat the runs.

The five checks are `rawUnchanged`, `protectionsFinal`, `mappingReleased`, `callbackGuard` and `memoryGuard`. Native memory access order and vzeroupper counts are not instrumented; the Java event-trace checks remain separate. The executor is owner-led after rejected model attempts. IO is partially adopted and Main preserves the original model source. Rejected model oracle attempts receive no independent-oracle credit. These results do not establish arbitrary invalid or concurrent RAM, complete ABI/EH/DF behavior, natural Game behavior, M6/G2 completion or seconds per saved game day.
