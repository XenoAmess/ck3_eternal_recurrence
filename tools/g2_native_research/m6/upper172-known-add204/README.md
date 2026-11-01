# M6 manual native witness 204

This Windows x64 fixture runs a 172-byte parent and its 424-byte and 351-byte sibling callees in one private image and the same data RAM. The parent calls the 424-byte body first and the 351-byte body second. Two profiles reproduce the separate-source and self-alias upper inputs from the existing Java200 assertions. This is a standalone capture tool with no Game bridge or default CI wiring.

No original executable, body bytes, assembly or built binary is distributed here. Verify each private input's exact size and SHA-256 before invoking the CLI. The CLI checks exact input sizes; its caller must independently check hashes.

| CLI input | Bytes | SHA-256 |
| --- | --- | --- |
| Parent `[37297F0,372989C)` | 172 | `6f271e3119ea92d8306865b46ced578ebfa70a8cd4c19f61a9253a4d66386213` |
| First sibling `[8C70B0,8C7258)` | 424 | `0a99a8546db4677b53fd0abd5bde3266ad8c48f38acaaf5ffb380552585c0a69` |
| Second sibling `[ADD0D0,ADD22F)` | 351 | `640d693377bdb24ad17d176109b437481cc7546458a4797b9d89cba52f30d75e` |
| Float material `0000c03f` (1.5) | 4 | `c0e336a5f371ef22cd534e094269f2c1a9635cd080b71ffa671086832d3b60b7` |

Build from this directory in an x64 MSVC developer command prompt:

```bat
cl /nologo /c /std:c++20 /EHsc /W4 /WX /O2 /utf-8 Native204Execute.cpp Native204Io.cpp Native204Main.cpp
link /NOLOGO /MACHINE:X64 /INCREMENTAL:NO /OUT:Native204Witness.exe Native204Execute.obj Native204Io.obj Native204Main.obj kernel32.lib
Native204Witness.exe <verified172-body-path> <verified424-body-path> <verified351-body-path> <verified4-literal-path>
```

The private image reserves `0x54df000` bytes and commits six pages: four RX code pages, one RO literal page and one RO allocator-pool page. Each profile uses fresh 4 KiB scratch RAM. All three supplied bodies and the float material remain unchanged. The COPY trampoline records arguments without copying RAM, including zero-byte/null calls. Allocator virtual slot 8 returns one controlled buffer, and slot 16 records the actual old header before new fields are installed. These controlled ports do not establish the natural COPY or allocator implementations. Fixed callback captures and scope guards restore the active callback context and MXCSR rounding mode.

The separate-source profile has an empty 16-byte range with equal endpoints at `B000`, so the first sibling returns early. The two-entry 4-byte range then takes the second sibling's growth path, producing five callbacks: allocation, three COPY argument records and release. In the self-alias profile, the parent clears source header fields before its child calls, so both siblings return early with zero callbacks. The returned full RAX is checked against the actual destination address. Output also contains fixed fields, both headers, the release-time old header and ordered callback arguments.

The first private run executed both profiles. A separate comparison matched the two Native rows against a read-only transcription of the already-passed Java200 upper assertions: two comparisons, zero differences. The old Java DATA run emitted five core rows and did not emit these two upper rows. This comparison uses old assertion literals; it has no cached Java upper rows, three-way comparison, new Java JVM or old eight-case rerun. CLI exit zero produces observations and checks guards; the separate comparison establishes the expected-row result.

Six measured guards passed: `rawUnchanged`, `protectionsFinal`, `mappingReleased`, `callbackGuard`, `memoryGuard` and `forbiddenTargetsUnmapped`. The last checks MEM_RESERVE at `8F8550` and `9D0950`; it is not an instruction trace or branch counter. Native access traces are not measured. [VALIDATION.json](VALIDATION.json) records exact source hashes, first stage intervals, comparison roles and model contribution grades. Publication reuses those first results without recompiling or repeating them.

The executor is owner-written after rejected wrong-role and length model replies. IO is partially adopted, and Main preserves its original model source. Both input-audit replies were rejected, and visible old expected hints preclude independent-oracle credit. The earlier source conclusion that the specified parent path cannot reach the reverse leaf remains unchanged. These two profiles do not establish other branch behavior, richer COPY Entry/RSP/register/DF/budget wiring, full ABI/EH/DF behavior, invalid or concurrent RAM, natural Game behavior, M6/G2 completion or seconds per saved game day.
