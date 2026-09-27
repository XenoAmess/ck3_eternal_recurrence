# R0256 construction progress: zero divisor on the cold paused frame

Status: bounded live observation and exact-build source interpretation. This
is a **derived** h223 Robert replay; it adds no days to the official Robert
high-water line. No construction completion or income change was observed.

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
enters its completion path. The manager's `0x21FDAC0` refresh path writes a
new divisor at `0x21FDD75`; its `0x21FDDB0` progress path calls `0x21F6D40`.
Thus `0` is an actual sampled raw value, **not** a missing-field encoding or
evidence that progress is blocked. The source alone does not establish when
the refresh path runs relative to a cold-loaded paused frame.

The stock start path writes `1095 * 100000 = 109500000` initial work for this
building. The observed `103500006` is lower by `5999994`, exactly
`54 * 111111`, where 54 is the elapsed game days from submit raw `53153760`
to the R0256 read and `111111` is integer `10000000000 / 90000`. This is
consistent with normal daily work having occurred before the cold read. It
does not prove a constant divisor, a completion date, or exclusive causation:
the stock start path also calls `0x21FBD10`, and no per-day paired progress
samples have been read.

## Next material read

Continue from the R0256 h252/raw `53155128` **paired save, driver and construction
sidecar** using a newly qualified candidate and new PID. On its first paused
frame, query the same barony/province/type/slot. If active, compare remaining
work with `103500006` and record the new divisor, date and native revision;
if no longer active, require the matching built-slot row. Read player and
province income separately. A second `0` paired with lower remaining work
would support a cold-frame/refresh-phase explanation; unchanged work or a
conflicting active/completed row needs its own investigation. Do not infer an
ETA from this zero, force date advances, re-submit construction, or count this
derived replay toward the official Robert high-water days.
