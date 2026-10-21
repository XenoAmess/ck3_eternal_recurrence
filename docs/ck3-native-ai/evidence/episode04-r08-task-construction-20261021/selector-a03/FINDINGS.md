# R08 selector production: a date predicate, with phase still open

Machine `desktop-3fevhd2-1c74096080`; observed 2026-10-21 UTC. Source is the exact retained 1.20.0.4 EXE identity recorded in SOURCE.actual.json, not a running-game qualification. The preceding a02 record remains unchanged; its then-unknown array producer is resolved further here.

The array consumed by the previously verified maintenance task is `owner+2630+bank*2640`. Its producer is now identified. `28F5140` selects the other bank, calls the complete leaf `28F3F80` to clear its descriptor counts, then calls `28F48C0` with the Character-pointer array at owner+20 and a date pointer. The latter function has three contiguous PE exception-table extents, all retained. It classifies each Character by the presence of components at +1C8, +1C0, +1B8, +1B0, then +1D0. The +1C8/+1C0 classes reach `28F42D0`.

In 28F42D0, the source date-derived ordinal and the raw DWORD Character ID at +18 are each reduced modulo 30. Only equality reaches `28F43D3`, which calls 880340 with the Character pointer and destination bankBase+25F8. Because bankBase=owner+38+bank*2640, this is exactly the maintenance-task descriptor above. This is a distinct, verified production predicate; it does not substitute the other task's modulo-30 bucket from a02.

`28F48C0` computes the ordinal by signed 32-bit subtraction of 43,800,000 (0x029C55C0), then signed division by 24 with truncation toward zero. `28F5370` constructs its local date from the low DWORD of [globalClock+8]+24 and passes that date to 28F5140. Its entry this-pointer is owner+8; 28F54AE explicitly subtracts eight. No claim about the global clock's live value is made here.

The same secondary CCharacterManager vtable (COL object offset eight) contains `28F5370` at +10 and `28F8770` at +18. Original image strings identify them as UpdatePreExecuteWithRandom and UpdateTurnTick. The latter calls 28F67A0, then calls the already-held maintenance dispatcher 28F6AA0 at 28F883B. Vtable adjacency and these names do not establish actual phase order, a bank-index handoff, or whether the clock advances before preparation. No runtime write to owner+4CB8 has been identified.

Consequently a snapshot ordinal remainder 22 and Character ID remainder 24 do not by themselves choose an observation day. Preparation might observe clock remainder 22 and build 23, or might run after the clock advances and build 24. Which prepared bank the subsequent tick consumes is still open. Do not guarantee a hit or prescribe a blind pre-step from this static arithmetic.

Still unproved: the actual parent caller's calendar occasions, bank handoff in a live instance, current Character membership, raw c/d writers or category, and the joins to a real wallet debit, payer and cadence. No Game, SDK, debugger, build or SYSTEM action was performed. Binary source spans are complete as specified; SELECTED.asm is an excerpt. Review retention on 2026-10-28; no indefinite protection is granted.
