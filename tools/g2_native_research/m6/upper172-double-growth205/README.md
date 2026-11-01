# M6 manual native witness 205

This Windows x64 fixture runs a 172-byte parent and its 424-byte and 351-byte sibling callees in one private image and the same data RAM. Two new profiles give both children positive element counts, so both growth branches execute in the same parent invocation. The tool is standalone, with no Game bridge or default CI wiring.

No original executable, body bytes, assembly or built binary is distributed here. Verify each private input's exact size and SHA-256 before invoking the CLI. The readers reject short and long inputs; the caller must independently verify hashes.

| CLI input | Bytes | SHA-256 |
| --- | --- | --- |
| Parent `[37297F0,372989C)` | 172 | `6f271e3119ea92d8306865b46ced578ebfa70a8cd4c19f61a9253a4d66386213` |
| First sibling `[8C70B0,8C7258)` | 424 | `0a99a8546db4677b53fd0abd5bde3266ad8c48f38acaaf5ffb380552585c0a69` |
| Second sibling `[ADD0D0,ADD22F)` | 351 | `640d693377bdb24ad17d176109b437481cc7546458a4797b9d89cba52f30d75e` |
| Float material `0000c03f` (1.5) | 4 | `c0e336a5f371ef22cd534e094269f2c1a9635cd080b71ffa671086832d3b60b7` |

Build from this directory in an x64 MSVC developer command prompt:

```bat
cl /nologo /c /std:c++20 /EHsc /W4 /WX /O2 /utf-8 Native205Execute.cpp Native205Io.cpp Native205Main.cpp
link /NOLOGO /MACHINE:X64 /INCREMENTAL:NO /OUT:Native205Witness.exe Native205Execute.obj Native205Io.obj Native205Main.obj kernel32.lib
Native205Witness.exe <verified172-body-path> <verified424-body-path> <verified351-body-path> <verified4-literal-path>
```

The image reserves `0x54df000` bytes and commits six pages: four RX code pages and two RO literal/allocator-pool pages. Each profile uses fresh 4 KiB scratch RAM. All three bodies and the float material remain unchanged. A COPY trampoline records its three arguments without changing RAM, including zero-byte/null calls. Allocator16 and allocator4 virtual slots8/16 use separate controlled callbacks. Their natural implementations are not established. Fixed captures are bounded to twelve records, and scope guards restore active callback context and MXCSR rounding mode. Both profiles captured seven callbacks.

The parent objects D and S are distinct in both cases. The first profile uses two 16-byte and two 4-byte elements with separate source payloads. The second uses one of each and makes the source16 vector begin at `D+0x10`, an ordinary destination-header RAM alias. The parent clears that header before the first sibling's actual MOVUPS read. The resulting first16 bytes of N16 are zero, and its remaining16-byte observation window stays `A5`. This is not a side-effecting Memory implementation or same-parent-object alias. The 424-byte body copies its elements inline; the 351-byte COPY port records metadata only, leaving the N4 window `A5`.

Outputs include equality of the full returned RAX with the destination address, fixed parent fields, both final headers, actual old headers captured before release-time stores, the32-byte N16 and16-byte N4 windows, and ordered typed callback arguments. Allocation16 alignment8 and allocation4 alignment4 are checked. The free16 port captures four registers and free4 captures three.

The first original-code run executed both profiles. A new owner Java manual witness called the unchanged mature parent/children implementation and passed two profiles with346 checks. Read-only comparisons joined those already captured rows with the owner expectations frozen before any model, Java or Native output: six pairwise comparisons, zero differences. No old eight-case suite, previous Native case or production algorithm was recompiled or rerun. CLI exit zero checks captures and invariants; the separate comparisons establish row equality.

Six measured guards passed: `rawUnchanged`, `protectionsFinal`, `mappingReleased`, `callbackGuard`, `memoryGuard` and `forbiddenTargetsUnmapped`. The last checks MEM_RESERVE at `8F8550` and `9D0950`; it is not a Native access trace or branch counter. No AVX feature RAM is used by these profiles. [VALIDATION.json](VALIDATION.json) records exact source hashes, first stage intervals, comparisons and model contribution grades. Publication reuses those results without recompiling or repeating them.

IO and Main preserve original R1 model source. The executor partially adopts R2 with significant owner corrections to physical pointers, case byte counts and ends, free-R9 capture, arrays, logical roles and RAM guards. Both model Java attempts were rejected; the final Java witness is owner-written. Both independent model-oracle attempts were rejected, so the expected rows receive owner-derived credit. These finite results do not establish other inputs, richer COPY Entry/RSP/register/DF/budget wiring, full ABI/EH/DF, arbitrary or concurrent RAM, natural Game behavior, M6/G2 completion or seconds per saved game day.
