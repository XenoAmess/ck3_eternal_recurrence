# Native71 M4 actual2C39EE0 subobject predicate

The actual CALL at `28B7401` uses `RCX=Province+620`. The parent separately
loads `RDI=[RCX]`; that object is not the callee receiver. The readonly child
model reproduces the47B function's raw memory predicate without invoking CK3.

| Native path | Copied operands |
| --- | --- |
| `u32[RCX+1C] !=0` | Load `data=ptr[RCX+10]`, then `selected=ptr[data]` |
| `u32[RCX+1C] ==0` | Load `selected=ptr[module+5D1E320]` |
| `u32[selected+38] !=4744624F` | Return observed AL0 before loading the flag data |
| Magic equals `4744624F` | Reload `data=ptr[RCX+10]`; byte `data+8 !=0` returns AL1, otherwise AL0 |

The source only defines AL. Its EAX upper bits are not a raw scalar result.
Every nonzero count bit pattern takes the first path; this is not a signed
positivity rule. Every nonzero flag byte produces AL1.

The reader distinguishes a complete AL0 observation from missing copied
fields. Missing input returns unavailable and preserves the caller output.
The optional source DTO retains only visited fields, the original subobject,
and the full64 unchanged snapshot revision supplied by13. It applies no new
revision gate. It retains the first data pointer and the later flag pointer
as separate operands, matching the native reload.

The exact13e seed is already captured at
`continuation-13e/source/ACTUAL-02C39EE0-128B.json` and remains the original
historical capture.22d acquired zero new binary bytes. Only
`[2C39EE0,2C39F0F)` belongs to this model; both RETs at `2C39F0B` and
`2C39F0E` are closed and the function contains no CALL. Padding and the
neighboring function beginning `2C39F10` are excluded, even though the128B
seed decode also contains their bytes.

The47B SHA256 is
`1b012e1eefd0b59e3d07e0ee1ea0d4a22a8dadc3d1c1594d9bcdfce222af8cdc`.
The frozen external source proof is
`native71-continuation-20261010/continuation-22d/SOURCE-PROOF.json`.
The leaf directly uses06c's `RawReceiverAccessV1` and copied-read helper;
its adapter exactly matches13e's `read_2c39ee0` callback. New cases have no
main and are handed to13→03d→10's sole fresh mode3 compound. No previous
Sway, Title or other qualification is replayed, and no piety or gameplay role
is inferred from the predicate.
