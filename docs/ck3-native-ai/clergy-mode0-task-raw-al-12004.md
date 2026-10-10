# Current base clergy mode0 raw AL projection

The independent `ck3_query_player_clergy_appointment_v1` query calls the existing
actual4 `ReadClergyAppointment12004` producer. When its current chaplain seat has
an incumbent, it calls native `CanFire(owner, incumbent, Task, 0U, nullptr)` and
keeps that aggregate Boolean in `native_can_fire`. The current positive-candidate
replacement `CanConfirm` path passes mode1 and skips the mode0-only call. The
earlier continuation-26b replacement ledger remains valid.

The actual CanFire call at RVA `0x2C4782F` passes Task in RCX and null tooltip in
RDX to `0x31B4A10`, then tests AL. The exact4 held `.pdata` interval is
`[0x31B4A10, 0x31B4AB5)`: 165 bytes. One cache-first finite read supplied the full
body; SHA-256 is
`661075c1730477f7adb914383716bfe1b2697542d4dde18ab6983e0bf41a84d1`.
The source packet is `continuation-26c/MODE0-BODY-SOURCE.json`; its current
consumer and source pins are in `BASE-QUERY-MODE0-HANDOFF.json`.

`ReadClergyMode0TaskRawAl12004` is a software reader for this body. It accepts the
existing guarded `ReadMemory` callback/context, the current actual Task, exact
module base and three software child readers. It does not create a query or call
native code. Those child readers must supply source-qualified raw bytes or report
unavailable. They are not native function pointers.

The source calls `0x31B4810` first. Any nonzero AL makes the parent return raw0
without reading later Task fields. When AL is zero, the source loads Task type,
owner raw32, Position, incumbent raw32 and the compared Task raw32 in that order.
It then calls `0x31BDE90` with owner raw32, Position+0x2377, Position+0x20A8 and
null tooltip. A zero AL returns raw0. A nonzero AL reaches `0x31BD1A0` with
Position, owner raw32, Task+0x28, the raw32 comparison result, exact
module_base+0x48C8710 and null tooltip; the final AL passes through unchanged.

Raw AL is a byte. In particular, the Position precheck may return 2–255; the
parent tests zero versus nonzero. A needed unavailable child remains unavailable.
An unreached child is not required. These availability rules do not assign a
frame, resolve an ID or establish appointment eligibility.

The same three child targets also appear in the existing CanReassign body at
`0x31B4960`, but its Position operands are +0x2376/+0x1FD8 and its static argument
differs. Reuse child source by exact build and RVA while retaining each caller's
literal inputs. Do not substitute CanReassign's result.

The existing query envelope and base producer continue to own application-main,
paused frame, full-ID, current seat and final consistency checks. Their
`native_can_fire` remains the aggregate CanFire result: an earlier CanFire gate
can reject before this helper runs. Missing seat, vacancy, native false and
unavailable stay distinct, and `action_eligibility_complete` remains false.

The three software child providers are owned by continuation-04f, 06e and 08e.
Their required shared condition, scope and dynamic predicate inputs are still
being closed by the unique owners assigned through 02. The parent source and
software control flow are frozen; this does not claim the full rule tree or a
live raw-AL observation complete. Seven new no-main compound cases cover exact
operand forwarding, full raw-byte preservation, generation bits, field demand
order and unavailable propagation. They have not been compiled or run here;
the sole new connected validation belongs to 10 after source integration.
