# P0-SPLIT exact CK3 1.20.0.3 native source contract

2026-10-04. Research / exact static-confirmed for the new split chain. No new live sample, SDK, screen, native invocation, gameplay day, DLL, checkout mutation, test matrix, or Git ref. The installed EXE was read and matched Steam build25652598 SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`. Historical Z: merge evidence is absent on this machine; only its tracked conclusion is reused. Exact spans and disassembly remain here.

## Source and call chain

The existing typed action remains `ck3_execute_step(step="split-army-half-D", expected_revision=R)`, where D is the full public CUnit ID. Native bridge `ck3_12002_military.cpp:484–517` resolves fresh D, reads Unit+178 internal full CArmy ID and calls `296CF60(kind1, nativeArmyId, freshPlayedCharacterId, null)`. Packet layout and old ABI are reused, not revalidated by a new matrix. GUI `window_army.gui:1351–1362` uses `ArmyWindow.SplitHalfSelected`, current legality `CanSplitHalfSelected` and `BuildSplitHalfTooltip`. GUI native caller `13481A0` invokes the same validator at `13481BE` and enqueues the actual command.

Command secondary executor `296C310` resolves source CArmy using the complete ID from secondary-this+10, calls `296B6E0` at `296C384`, then partitions original regiment IDs between the retained source and newly returned sibling. `296B6E0` calls `2A96EA0` at `296B85B` to allocate a CArmy and corresponding CUnit at the original resolved province and owner context. The creator increments the allocation generation at `2A96FA2`, writes the CArmy full ID at `2A96FBD`, creates CUnit via `2AD67B0` at `2A970D8`, then stores CUnit ID at CArmy+124 (`2A970FA–FD`) and the CArmy ID at CUnit+178 (`2A97134–37`). This supports distinct same-session sibling identity, not a reusable global number after reload.

## Split supply and capacity

`296B956` reads source CArmy+180, and `296B95D` writes precisely the same signed64 raw value to new CArmy+180. Current source `ck3_12002_army.cpp:333` and the existing capacity topic identify this as current supply. The clone does not divide it by two and does not apply a capacity percentage. Original source is retained by execution. The same clone copies source+188 to new+188 (`296B948–94F`) and source+190 to new+190 (`296B964–96B`). Their timing meanings are the supply-clock owner's separate chain; this lane proves copying only. `2A96EA0` initially writes now at new+190 (`2A97062–72`), then this clone overwrites it with source+190: new allocation does not itself prove a fresh grace anchor.

Capacity is the existing `2C53C10(out,CArmy,null)` calculation from the current commander, not a copied "half capacity" field. The split executor after both composition refreshes calls existing commander selector `2C11A10(actor,false)` at `296CCC5`; valid returned Character is assigned to the sibling with `24DFA10` at `296CD34`. It is not necessarily the actor itself. Source commander remains separately observed; selector ranking is reused from commander topic and not closed anew here. Actual resulting commanders and capacities must be read after the action. Supply copied before commander selection is not proof of capacity equality or subsequent clamping time. No claim is made that final stored supply is always <= the new capacity before the normal update.

## Regiment assignment

`296B260` traverses the source `CArmy+38` array with count+44, resolves full ArmyRegiment IDs and constructs 16-byte sorting rows containing actual regiment pointer and signed weight. It has three groups:

1. A valid CMenAtArmsType at ArmyRegiment+18 (tag `4744624F` at definition+38) enters the MAA group. Weight is current soldiers ArmyRegiment+38, with a separate total per definition index+10.
2. A valid linked Character at ArmyRegiment+148 enters the character/knight group. Its sorting weight is Character+EC (prowess input); this is not the regiment's public soldier count.
3. Remaining records enter the other group with current soldiers ArmyRegiment+38. It includes the normal levy case, but the unqualified group must not be renamed "all and only levies" without record type evidence.

The MAA group is sorted by descending row weight (small-row insertion branch `296C730–7A4`, native sort for >32). It traverses descending records at `296C840`, uses same-type totals plus floor(1.5*current soldiers) in the transfer comparison, and otherwise balances total retained/sibling soldiers for a type not yet assigned to the sibling. Do not simplify this into every MAA type split exactly in half. The other group is ascending-sorted and traversed in reverse, moving a whole record when retained running soldier total is >= sibling total (`296CAD0–CB11`). These counters carry the earlier MAA totals. The character group is ascending-sorted then traversed in reverse, with independent prowess-weight balancing counters (`296CC60–CC9E`). This prevents "half" from implying exact equality of displayed soldiers or equal regiment counts.

Every actual transfer removes the same full ArmyRegiment ID from source through `24E0D30` and appends it to sibling through `24E0C70` (MAA `296C947/956`, other `296CAF2/CB05`, character `296CC7F/CC92`). The append helper writes CArmy ID back to ArmyRegiment+140 at `24E0D14` and appends the ID into the new army's vector. No new ArmyRegiment is constructed by these transfer blocks; individual records stay whole. Both compositions are refreshed using `24E8120` at `296CCA5/CCB4`. Formal proof of all current/max totals remaining unchanged still needs same-date live per-record rows: action completion alone cannot supply them.

## Existing merge formula reused

The tracked merge topic closes `296EEA0→2C54FD0→2C551A0`, keeps destination D and consumes source S. Supply is absolute supply-unit raw, not percentage. Destination weight is native `24E0160(D,out,0)+24E02A0(D,out)`; source weight is `2A95740(source_regiment_array,flags0)*100000`. It cannot be replaced with public current_soldiers for arbitrary records. Positive-weight result is the sum of per-army native fixed division then fixed multiplication of each original supply; clamp to the newly selected commander's native capacity, then write destination+180. Capacity and monthly supply changes are not summed. Two fixed truncation stages matter; even immediately recombining equal-supply split armies is not promised to restore identical raw supply.

## Available observation and remaining gap

Current strengths returns all `regiment_replenishment[]` ArmyRegiment full IDs when the optional collection is available (`ck3_12002_army.cpp:359–364`). Even unavailable first-record rows preserve their real `army_regiment_id`: use complete collections to prove source/sibling partition. Current/max per ArmyRegiment are already read at :289–290 but only aggregated to army totals; first-record chunks have partial coverage and cannot stand in for every full record. The current MCP exposes no native merge weight field. Numeric verification of all per-regiment values or a specific merge arithmetic example requires the smallest extension to the same strengths query or an independently bound save reader. Until then report actual aggregate changes, membership, supply, capacity and commanders separately.

## Exact evidence

| Logical span | Length | SHA-256 |
|---|---:|---|
| Executor 296C310..296CE13 | 2819 | 2e58b65cb25d14d7db2c466d8373f66bf84111660180f109eb699a50a3a1241d |
| Clone 296B6E0..296B9B0 | 720 | abcece0993c77c5e8eb0ae6c9c929ca50eb3103f00c8a8bcecd0992a118e6f13 |
| Classification 296B260..296B6E0 (includes trailing padding) | 1152 | 9633a7605a07a66521a24523f8ef94e4e717178d72e81a2feb0e11f0d041b212 |
| Army/Unit creation 2A96EA0..2A97194 | 756 | 1a597ddc81ef51fd181d30b2d3fad881a0091e4ccbfdd080c3a22d25b3204e12 |
| Remove 24E0D30..24E0EA9 | 377 | 42668b2c3d09878e1f4fad66e0e16e9084add1bb9d6debb8204ac3d506233be9 |
| Append 24E0C70..24E0D30 (complete fragmented function plus padding) | 192 | 2f9446d95b9e7b7a0fc87bc213fdfe2b32995cd22705841800915991737ee911 |
| New commander selector 2C11A10..2C11C0F | 511 | 88378335511265e6310f58513b033f742b7fab839eaf836d92f81f5280651a46 |

Single .pdata regions for classification, append and creator are only prefixes. Full contiguous spans were retained as additional evidence, without overwriting the prefixes. No prefix is claimed as the full function. All unknown selector/capacity-after-selection/live branches remain open.

2026-10-04 correction: the actual append backlink store is RVA `24E0D14` (full append disassembly), replacing the a01 mistyped `24E0CF7`. The mechanism and bytes are unchanged; a01 remains preserved.
