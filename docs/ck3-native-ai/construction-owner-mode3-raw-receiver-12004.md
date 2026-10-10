# Construction mode3 raw receiver, actual1.20.0.4

The read-only leaf follows actual function `2467660`, used by `2468DA0` at
`2468DF3` and `2469343`. Its RCX is the Province owner plus `620`; the returned
pointer is subsequently passed to the modifier aggregator, piety rank,
government-object selector, raw-input getter and final factor. This source
closes the raw receiver selection; it does not establish holder transfer,
per-building yield, payable tax or a material terminal result.

The actual body is `[2467660,2467745)`, 229 bytes, held runtime row
`[38172256,38172485,84974928]`. The source is exact1.20.0.4 / Steam25734779,
held executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Its finite body SHA-256 is
`821c02b0bfba26a1a29aad69c7e8e5a4e42bf89189accd1705780e2f6abca69f`.
The existing 4118-byte parent instruction text was reused at
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/construction-benefit-owner-mode3-source/ACTUAL-PROVINCE718-PRODUCER-INSTRUCTIONS.txt`,
SHA-256 `70a939bdfc426af761b71772b8e44dbbaf6b3faa8caa4b64d1ad5a6e4188470f`.

## Actual selection

1. Load the Title storage pointer from module RVA `5D1DAF8` and its fallback
   from `5D1DAE0`. A null storage skips the slots/context read entirely.
   Otherwise read slots `+F0`, then context `+738` as a full uint32 ID.
2. Resolve that ID with index `ID & 00FFFFFF`, unsigned count at storage `+2C`,
   table at `+20`, stride16 pointer at entry `+8`, and full ID at Title `+10`.
   Out of range, null slot and generation mismatch select the loaded fallback.
3. `24676B4` calls actual `2C42930` with this selected Title. Its returned
   pointer is inspected at `+1C` for raw tag `43686172` and `+18` for an ID
   other than `FFFFFFFF`. If both match, `2467660` directly returns it.
4. Otherwise, when the Title storage is nonnull, read first Title `+E8` and
   resolve another Title through the same full-ID registry. A failed lookup
   retains the initial loaded fallback Title. It does not retain first Title.
5. Load Character storage from `5C67568`. With a nonnull storage, read the
   effective secondary Title `+128`, resolve with the same low24/stride16 rule
   and full Character ID at `+18`. Failure returns global `5C67570`.
   A null Character storage goes straight to that fallback without reading
   secondary Title `+128`.

No positive-ID or high-bit rejection appears in this body. The direct-child
tag/invalid-ID guard is source-defined. The final Character fallback has no
tag/full-ID guard here. The leaf records optional final identity metadata
without replacing the actual source return with a guessed object.

## Consumer and evidence

The API is `ReadAggregateRawReceiverV1(access, province, expected_id, child)`
in `xar::ck3_12004::construction_owner_mode3`; the lower API accepts the actual
slots pointer directly. `child` is `ReadActualTitleReturnV1`, whose typed
callback receives the same raw access and first selected Title, then returns
the actual read-only child result through an output pointer. Its ABI cannot
bind the native getter directly. The central consumer adapts
`ReadActual2C42930ReturnV1` from
`xar_bridge/construction_actual_2c42930_return_12004.hpp`; that leaf takes
`RawTitleReturnAccessV1` and the independently owned
`ReadTitleSelectedFullIdAdapter12004` from
`xar_bridge/title_selected_full_id_12004.hpp` as its `2C42820` dependency.
The child chain's actual192-byte `2C42820` body has no further CALL. It uses the
source byte at Title `+130`, the appropriate source registry, and raw member
IDs; none of these operations calls a native getter. The result of each
read-only child must be observed before its return can be used.
The leaf uses the existing admitted exact-build binding and
the central paused main-thread frame. `returned_receiver_pointer` is the raw
operand consumed by source-closed downstream leaves. There is no native getter
invocation, aggregate getter invocation, new global admission gate or separate
frame established by this leaf.

`continuation-06c/ACTUAL-2467660-SOURCE.json`, its instruction text and
`SOURCEPLAN.json` preserve finite capture details. The only necessary child is
the independently owned actual `2C42930` read-only resolver from
`continuation-38d`, with its selected-ID child in `continuation-22c`; the final
delivery records those precise dependencies. Eleven new no-main cases cover
this leaf's observed branch rules using a typed synthetic child-return packet.
They do not qualify the child leaf. They are supplied for the one connected
central compound only; the central owner adds the real child composition.
This packet is source evidence and an authored candidate, not a Game runtime
or economic acceptance result. No old qualification is rerun.

The packet is a bounded active input under storage policy1.0, scheduled for
review two days after creation. Once the adopted source/topic and central
result preserve its necessary pins, re-evaluate the derived D packet; retain
only evidence still referenced by an unresolved source question.
