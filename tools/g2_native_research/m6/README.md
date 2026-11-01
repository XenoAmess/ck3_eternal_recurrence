# M6 manual native witnesses 200 and 201

These Windows x64 research fixtures execute an externally supplied, previously verified normal body in private memory. Each directory contains its API, execution harness, JSON row writer and CLI. They are standalone capture programs; they are not linked into the game bridge or default CI.

The original executable, body bytes, assembly, object files, DLLs and executables are not distributed here. Before running, verify the external body against the identity below. The CLI checks its exact length; the caller must verify its SHA-256 separately.

| Witness | External inputs | SHA-256 |
| --- | --- | --- |
| 200 | ADD0D0 normal body, 351 bytes | `640d693377bdb24ad17d176109b437481cc7546458a4797b9d89cba52f30d75e` |
| 200 | float material, 4 bytes `0000c03f` | `c0e336a5f371ef22cd534e094269f2c1a9635cd080b71ffa671086832d3b60b7` |
| 201 | 9D0950 normal body, 126 bytes | `7cf624784877e13a583ba7675383f324e7e7d7786522046f0cfdfd064377a0d0` |

In an x64 MSVC developer command prompt, build each group from its own directory:

```bat
cl /nologo /std:c++20 /EHsc /W4 /WX /O2 /utf-8 Native200Execute.cpp Native200Io.cpp Native200Main.cpp /Fe:Native200Witness.exe /link kernel32.lib
Native200Witness.exe <verified351-body-path> <verified4-literal-path>
```

```bat
cl /nologo /std:c++20 /EHsc /W4 /WX /O2 /utf-8 Native201Execute.cpp Native201Io.cpp Native201Main.cpp /Fe:Native201Witness.exe /link kernel32.lib
Native201Witness.exe <verified126-body-path>
```

Successful capture emits JSON rows and measured guards. Exit zero alone is not the row-comparison result. The first private validation compared each row with independently frozen owner expectations and previously captured Java output: witness 200 had 5 cases/15 pairwise comparisons, and witness 201 had 6 cases/18 comparisons, both with zero differences. The exact source hashes, first stage intervals and model contribution grades are in [VALIDATION-200-201.json](VALIDATION-200-201.json). Publication preserves those source bytes and does not repeat the checks. This is a bounded manual workflow, not a portable build or test runner.

Witness 200 uses controlled callbacks for COPY4226860, 9D0950 and allocator virtual slots 8/16. Its five raw cases do not include the earlier software-only large-float and upper172 cases. Witness 201 controls 4220AA4: its first call records four qualified registers and later calls record the two reloaded registers. Its negative, misaligned and wrap profiles exercise scalar arithmetic under that callback, not natural pointer-range validity. Neither harness establishes the natural implementations of these callbacks, full ABI/EH behavior or arbitrary concurrency.

The supplied normal bodies remain unchanged in the private mappings; page protections, callback bounds and checked release underpin the recorded guards. These results do not establish natural Game behavior, completion of M6/G2, or seconds per saved game day. Expected rows are owner-led; rejected model oracle attempts receive no independent-oracle credit. Executor/IO partial adoption and the unchanged model Main201 are recorded separately from software and original-body verification.
