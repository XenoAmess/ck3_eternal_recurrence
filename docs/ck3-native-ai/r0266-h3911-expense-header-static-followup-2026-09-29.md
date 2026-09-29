# R0266 H3911: expense cache header follow-up

Status: **static candidate and passive diagnostics only; five war-cash inputs remain `null`, `formal_cash_eligible=false`.** No CK3 session, desktop, native query, or game memory was used for this follow-up.

## Frozen attempt and exact build

H3911 attempt-05's immutable `formal-query-receipt/passive-topbar-raw.json` (SHA-256 `9D1A25DF8B33109B5F82917832951A6061956AA73A4A173BBAF5A7730AF1E5BE`) retained topbar block hashes but omitted the rejected vector/header and render-clock scalars. Its two bounded reads rejected the expense row address as unaligned and the render epoch as invalid. The formal termination query's successful native postcheck does not validate this independent GUI cache. No amount, including zero, is recoverable from the old hashes.

The local stock `ck3.exe` was read **offline** at `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`: 95,206,008 bytes, SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`. The existing exact-build topbar verifier passed in ordinary and `-O` Python and returned `exact_build_topbar_expense_cache_candidate_only`; the MilitaryView verifier also passed and returned `exact_build_gui_getter_candidate_only`. Both keep their formal/live claims false.

The verified instructions explain why the rejected pointer cannot be reinterpreted as a fee:

| RVA | Exact-build instruction consequence |
| --- | --- |
| `0xD4769B..0xD476B8` | Getter reads the render counter, compares it with `topbar+0xF88`, writes the new tick **before** calling the rebuild at `0xD476D0`. A matching tick alone cannot prove a completed refresh. |
| `0xD47867..0xD47871` | Expense refresh passes `topbar+0xAD8` to the row-vector clear routine. |
| `0x21C7687..0x21C768B`, `0x21C76FC..0x21C7729` | Vector count is DWORD `+0xC`, capacity is DWORD `+0x8`, data pointer is QWORD `+0x0`; existing rows advance in `0x90`-byte steps. A nonzero unaligned data pointer is not an amount or a valid row address. |
| `0xD478C8..0xD478CB`, `0xD47993..0xD4799A` | Rebuild negates the **whole** expense total into `topbar+0xB50` and writes the ValueBreakdown back-pointer at `+0xB68`. The total is not an independent military cost. |
| `0xBC3D70..0xBC3DFF` | ValueBreakdown construction initializes the vector header, Q100000 scale at object `+0x80`, and back-pointer at object `+0x90`. Constructor state does not establish that rows have been refreshed for this paused game frame. |

The render refresh interval global at RVA `0x570D8D0` lies 8,198,352 bytes into `.data`, beyond that section's 8,144,896 file-backed bytes. Thus the exact executable supplies the **address and read instruction**, not a valid runtime interval value from the on-disk bytes. In particular, `pefile.get_offset_from_rva` on that virtual tail yields unrelated file bytes; using those bytes as a refresh interval would be unsound. The next attempt must read the bounded live scalar and retain it even when its diagnostic validity check rejects it.

## Added bounded diagnostic

`war_cash_topbar_bounded_sample.py` now reports six additional fields from its **already-read** `0xF90` topbar block: expected expense object address, actual `+0xB68` back-pointer, whether they match, signed whole-expense total candidate at `+0xB50`, scale candidate at `+0xB58`, and whether the scale is Q100000. It performs no extra target read, does not follow a rejected pointer, does not call a getter, and cannot turn any candidate into a formal receipt. These scalars can reject an obviously wrong object interpretation or show a structurally initialized breakdown with unpopulated rows; they still cannot prove freshness or player/war attribution.

The negative tests independently force an unaligned row pointer, a wrong object back-pointer with an otherwise valid row vector, and a non-Q100000 total scale. All stay RED and `formal_cash_eligible=false`; none provides a usable amount. The bounded sampler tests pass 11/11 in ordinary and `-O` Python.

## Next live gate

Only in a **new**, managed, paused, exact-pair attempt, first record these passive scalars with native before/after identity, date, episode, WarID, gold, and revisions unchanged. If the object/header remains invalid, stop as diagnostic RED. A naturally rendered GUI tooltip can then be evaluated under the desktop contract; no bridge invocation of the mutating getter is authorized. Even a valid row vector requires completed natural refresh, current-player attribution, row-tree identity, a cross-check against the current MilitaryView amount, and payment cadence before it can support a war rate or future debit bound. The predicted all-raised MilitaryView monthly value is not a debit upper bound because fleet maintenance may exceed it. Pending spend, immediate fee, reserve policy, future cost, and risk budget remain `null` until their separate sources and assumptions are proved.
