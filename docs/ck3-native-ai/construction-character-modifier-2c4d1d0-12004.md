# Actual 1.20.0.4 Character modifier scalar

`ReadCharacterModifier2C4D1D012004` supplies the reached NULL-detail branch of
actual `2C4D1D0`. Caller `2C82340` reaches it at `2C82664`: RCX is the temporary
output address, RDX is its selected Character, R8 is the zero-extended u16 key,
R9 is detail, and stack argument 5 is Q64 `100000`. The returned qword is added
to the caller's ordered unique full-DWORD accumulation. The caller owns that
selection, source order and real frame association.

The helper first calls `28C3AC0(Character)` at `2C4D200`. With detail NULL it
calls `2C4D530` at `2C4D229`, passing the returned collection, original key and
scale, NULL detail and selector 0. The qualified raw getter/default-storage
adapter comes from continuation 46c; the scaled key adapter comes from 14c.
Both are used through the parent's same guarded read access. The implementation
does not invoke native getters, formatters, initialization or destruction.

The input must carry the exact 1.20.0.4 binding and a guarded copy callback.
The raw physical Character DWORD at +18 is copied and rechecked to keep the
receiver stable. A high generation ID remains a full DWORD; no Char tag or
positive/signed ID admission is added. For physical FFFFFFFF, the wrapper
requires the actual caller's Character fallback slot `image+5C67570` to equal
the argument, and repeats that slot after the scalar copy. This is a software
bookend of the caller's source-selected fallback, not a native getter gate.

The getter selection is resolved before the scalar, even when factor is zero.
An uninitialized default context cannot be accepted by skipping that selection.
After the scalar copy, the wrapper repeats raw getter selection and identity;
the initialized default also retains guard and both container lifetime stamps.
The scalar's own key/value source checks remain in effect. Changed or unreadable
input yields an unavailable result while preserving the observed raw receipts.

`ready && value_raw_q64.has_value()` is the only usable numerical result. Known
zero, absent key and negative/scaled values are ordinary Q64 output. Unknown
child values remain unknown. NonNULL detail requires string/detail sideeffects
outside this readonly profile and returns explicit unavailable status.

The actual helper's full pdata interval `[2C4D1D0,2C4D525)` was captured once:
853 new bytes from the fixed .4 source. Source branch and dependency input
pins were frozen before code; getter/default/arithmetic bodies were reused,
with no recapture. The new no-main wrapper fragment contains eight scenario
groups for the sole 03/10 M4 combination. No local fixture or old qualification
was run. Source closure and modeled checks do not establish game acceptance.
