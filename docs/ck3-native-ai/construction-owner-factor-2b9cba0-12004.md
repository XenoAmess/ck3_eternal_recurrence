# Actual 2B9CBA0 null-detail factor in the province 718 producer

This source topic owns only the actual `2B9CBA0` child reached by the `2468DA0` producer at `2469C13`. The current source is CK3 1.20.0.4 / Steam 25734779, held executable SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`. Its retained `.pdata` interval is `[2B9CBA0,2B9CDFC)`, 604 bytes. The complete body was reused from the canonical named cache without opening the executable. The exact span SHA-256 is `713273f7c0689a2daf897281ebe85563f0e4b56bddfe20ebefb34157ff5a0c7b`.

The caller supplies `RCX` as a stack signed-Q64 output, `RDX` as the actual `2467660(slots)` returned object, and `R8` as the fifth detail pointer. That pointer is NULL in the actual mode3 route. At `2469C18` the caller loads the first Q64 from the returned `RAX` pointer. The existing `MaaGetSelectorFactor = int64_t *(*)(int64_t *, void *, void *)` type has this same calling convention; the current .4 binding points to `2B9CBA0`. Existing names are an ABI reuse clue, rather than a proof of the meaning of the new economic use.

| Actual source | Operation on the null-detail route |
| --- | --- |
| `2B9CBC1..CBC7` | Retain detail pointer, receiver and output pointer. |
| `2B9CBD4..CBD7` | Call `28C2DF0` with the exact receiver. |
| `2B9CBDC..CBE3` | Compare the returned object's byte at `+4D6` with 5. |
| `2B9CBE5` | If unequal, store signed Q64 `100000` and return the output pointer. No context/modifier input is needed for this branch. |
| `2B9CBF1..CBF9` | If equal, pass the receiver to `B17C70`, constructing the local context at `rsp+70`. |
| `2B9CBFF..CC13` | Initialize a signed-zero stack Q64; call `C86670` with index `0x4E`, that local context and an output object at `rsp+40`. |
| `2B9CC1D..CC25` | Take the signed Q64 at the returned pointer if it is nonnegative; otherwise take the initialized signed zero. |
| `2B9CC28..CC2B` | With NULL detail pointer, skip the whole detail/UI branch to `2B9CD82`. |
| `2B9CD82` | Store the selected factor Q64 in the original output. |
| `2B9CDDD..CDFB` | Return the original output pointer. |

The source-backed pure value recipe is therefore `factor = 100000` for `byte_4d6 != 5`, otherwise `factor = max(modifier_4e_returned_q64, 0)`. Zero is an available native value. Missing source inputs are unavailable; they are not zero. The byte, numeric modifier index and factor have no new unit or economic label attached to them in this topic.

The actual caller applies the returned factor to its already assembled signed Q64 `r15`, then applies `rsi`, with division by 100000 after each multiplication. `2469C1B..CB9` contains a direct-product branch within signed bounds `[-0xB504F333,+0xB504F333]` and a quotient/remainder decomposition outside them. The reciprocal signed multiply, arithmetic shift and sign correction perform division toward zero. This caller arithmetic remains owned by 03; this child returns only its factor input. Neither the child nor its caller takes a building definition as an argument on this path, so this factor does not establish per-building net income.

The non-NULL detail path is not admitted by the planned null-detail API. Its calls include detail assembly and writes to `rdi+88` and `rdi+8E`, and it is unnecessary for the actual mode3 input. The readonly implementation will read held source bytes and copied scalar inputs only, with no invocation of `28C2DF0`, `B17C70`, `C86670` or other active native functions.

Receiver resolution (`28C2DF0`), scope construction (`B17C70`) and conditional modifier evaluation (`C86670`) require their own current source closure. They were referred to 02 for exclusive source owners. Their raw copied results must retain the same receiver and observation/context binding as this call. A .4 binding or a historical typed name alone cannot make those inputs ready.

Delivery review is due 2026-10-12. This small topic/source packet remains an active input for the 03/10 consumer integration until that review. The canonical shared binary input remains a separate retained cache asset.
