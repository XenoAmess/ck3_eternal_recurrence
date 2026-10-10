# Native71 current Army position helper at 2C09360

This helper's actual 1.20.0.4 body is closed at `2C09360..2C09410`: 176 bytes,
54 instructions, held Steam build 25734779 and executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The reached parent is the separately owned actual `2C09280` 220-byte predicate.
The finite capture used the parent's literal `2C092AA -> 2C09360` CALL and the
held actual runtime owner. It read 176 new bytes once through the existing
shared cache and O_EXCL claim. No old executable or broad image scan ran.

`SOURCE-PROOF.json` was frozen before this leaf's code. The new leaf is
`army_position_helper_2c09360_12004.hpp/.cpp` and exports
`ReadArmyPosition2C0936012004(access, holder, actor, optional_war_identity)`.
Its arguments preserve the native stack pair and actor separately: in the
parent, original RDX becomes pair[0], original R8 becomes pair[8], and original
RCX becomes helper RDX. At the current position caller `2C097F0`, the two
literal parent calls receive R8=0 and reverse the actor/holder direction.

The native order is retained:

1. Read holder full Character ID at +18, then actor full ID at +18. Equal IDs
   return true immediately, without reading any delegated predicate or War.
2. Call the separately closed `2C090D0` with holder, actor, original optional
   War pointer. A true result returns true immediately. The readonly leaf
   reuses 15b's guarded projection and preserves missing inputs.
3. Reload actor ID and holder ID in that order. Equality now returns false.
4. Obtain `28BC250(holder, actor)`'s returned relation +20 full War ID through
   24c's readonly raw reader. Full ID -1 returns false.
5. Resolve the War through actual manager slot `5D1DE58`, low24 index, count
   +2C, table +20, 16-byte slots with pointer +8, and full ID +8. Invalid
   resolution uses actual fallback slot `5D1DE40`.
6. The resolved War's byte +358 must equal zero. Then a null original optional
   War pointer returns true; a non-null pointer must equal the resolved War.

The last two steps reuse 16b's `ReadArmyPositionWarGate12004`, whose literal
resolution/end/filter operands agree with this helper. All readers use 34b's
`ArmyRegularCoreReadonlyAccess12004`; its callback owns the shared frame read
budget. The helper does not call native code or assign a guessed ABI.

R8=null removes only the final identity constraint. A reached missing prefix,
relation, database, fallback, or War field remains unavailable. The projections
cannot reproduce unclosed native dependency side effects or claim the original
selected actor changed; the parent preserves the actual raw carrier and owns
replacement selection. Entry and return frames remain separate. This source
and the new synthetic compound case provide no natural runtime, Game,
complete Army position transfer, or old final Side planner validation.

The source packet is external under continuation-28b/actual-helper-source01.
Dependencies remain uniquely owned by continuation-15b (2C090D0),
continuation-24c (28BC250), and continuation-16b (parent and shared War gate).
Central 33/10 executes only the new phase compound case. Source protection is
reviewed on 2026-10-17; small records are reviewed after 180 days, without
automatic renewal, under the shared storage policy and current Root admission.
