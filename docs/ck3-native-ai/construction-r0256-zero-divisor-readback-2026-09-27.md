# R0256 construction progress: zero divisor on the cold paused frame

Status: two paired bounded live observations and exact-build source
interpretation. This is a **derived** Robert replay; it adds no days to the
official Robert high-water line. Progress was observed, but no construction
completion or income benefit was observed.

## Bound observation

The R0256 candidate used runtime source `8189122dcbcff2c58b83addfbf0193acfa90b561`
and frozen CK3 1.19.0.6 EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The candidate index SHA-256 is
`E32A7C84FF61E46D7FE77AF9E848BCB4F4D94D55B51FD9875D795475603666B7`.
The local live `formal-report.txt` SHA-256 is
`CDE6D1F5024BE52B4019B190FA63FE4B26E866F729D7F12E760CCD6DE53A2EE6`;
the resulting `construction-formal-pending-v1.json` SHA-256 is
`BD569A443A0AF16564C9104FEC4DEBCE547D100497D42D721F65366E6344F0C0`.
Both remain with the R0256 candidate assets at
`Z:\c169-h223-construction-watch-candidate` on the run machine.

On the first new-PID paused material read, at h223/raw `53155056`, the native
row matched barony `2174`, province `2629`, building type `628`, slot `1`,
`hill_farms_01`. The receipt was `in_progress`, with
`native_remaining_work_raw=103500006` and `native_progress_divisor_raw=0`.
The receipt status `observed` means both signed integers were read; a missing
field would have been `null`/`unavailable`. The next formal turn consumed the
receipt. R0256 then advanced one game day on each of three war-route turns,
ending at **driver history h252/raw `53155128`**, and saved a checkpoint.
The saved `xar_checkpoint.ck3` SHA-256 is
`7285A2D94C4F70DBB826384A8E591B0DBE790F40229CE9128B28BEF6A9EB2BF6`;
its paired `native-session/driver-state.json` SHA-256 is
`F7C01D7ECB33CB3E3A1D191FA3DB442081EB6DE5749CD0D8A1B0A2DA8E7D06C6`.
The driver's last checkpoint and last history entry both identify h252/raw
`53155128`. The three elapsed game days must not be added to h223 to derive
a driver history index. Those turns did **not**
submit another construction material query. Therefore the later date and
unchanged ledger status do not show whether the building progressed or
completed during those three days.

## Exact-build interpretation

The existing [active-progress source](construction-active-progress-source-2026-09-27.md)
and its byte verifier bind the active slot to `Province+0x620` and the raw
progress divisor to `+0xE8`. A targeted disassembly of the same frozen EXE
confirms that `0x21F6D40` reads this field at `0x21F6D57`. If it is positive,
the routine subtracts integer `10000000000 / divisor` from remaining work at
`+0x88`; if it is nonpositive, the routine sets remaining work to zero and
enters its completion path. This conditional concerns the value **when that
routine executes**, not an earlier or later paused-frame sample. The
manager's `0x21FDAC0` refresh path writes a new divisor at `0x21FDD75`; its
`0x21FDDB0` progress path calls `0x21F6D40`. Thus `0` is an actual sampled
raw value, **not** a missing-field encoding or evidence that progress is
blocked. The source alone does not establish when the refresh path runs
relative to a cold-loaded paused frame.

The stock start path writes `1095 * 100000 = 109500000` initial work for this
building. The observed `103500006` is lower by `5999994`, exactly
`54 * 111111`, where 54 is the elapsed game days from submit raw `53153760`
to the R0256 read and `111111` is integer `10000000000 / 90000`. This is
consistent with normal daily work having occurred before the cold read. It
does not prove a constant divisor, a completion date, or exclusive causation:
the stock start path also calls `0x21FBD10`, and no per-day paired progress
samples had been read at R0256.

## R0257 paired cold calibration

R0257 used a fresh PID `79596` and source commit
`fd662bacc2d2700eacf18262a1f00053cad8b663`. Its prepared input is
the R0256 **h252/raw `53155128`** save, driver and sidecars. The source
pair index SHA-256 is
`04EE0136EE60D740AB07C5618826551693D82237DCA5061AFB21B2919B67F5E7`.
The R0257 formal report SHA-256 is
`98356C0B01C76227F42BB5FD060386A7AB4A9046906C3D9C5DC5B9DDBAC08B7D`;
the resulting construction sidecar SHA-256 is
`A11F3807639C027F9E7BEB7D62320EE6351571BEEF07DA949AA67705819298D5`.
These live assets remain at
`Z:\c175-h223-construction-cold4-current-candidate` on the run machine.

The first paused material receipt matched the **same** barony `2174`,
province `2629`, type `628`, slot `1` and still reported `in_progress` at raw
`53155128`. It read remaining work `103166673` and divisor `0`; player
monthly gold income was still raw `603774`. Formal turns 3 and 4 consumed
the receipt without another construction submit. The four-turn bounded run
did not advance the date. Completion and income benefit remain unobserved.

The material work difference across the R0256 three-day advance is
`103500006 - 103166673 = 333333 = 3 * 111111`. This is **observed progress**
across paired new-PID paused reads, consistent with the stock positive-divisor
quotient `10000000000 / 90000` during those days. Both cold paused reads
sampled divisor `0`; their work decrease proves this sampled zero is not a
reliable indicator of a blocked build or of immediate completion on the next
date advance. It does not establish the actual per-tick divisor, the refresh
ordering or an ETA.

## Next material read

The latest derived checkpoint is **R0257 h263/raw `53155128`**: save SHA-256
`5F96F853354FAD01E2369B2E6BC21731D5A44C7F0DEBA3AFACCFDA2399AB6328`,
driver SHA-256
`1CCBC4BC17379B1689C66478DBCF081C5828B5E4FDCD411A9D79A61BE398746A`,
and the construction sidecar SHA-256 above. If the formal strategy later
advances date from a qualified paired continuation, compare the same tuple's
remaining work with `103166673`; if no longer active, require the matching
built-slot row. Read player and province income separately. The existing
30-day warm watch from the R0257 receipt is due at raw `53155848`, subject
to subsequent cold recheck dates. Do not infer an ETA from the paused zero,
force date advances, re-submit construction, or count this derived replay
toward the official Robert high-water days.
