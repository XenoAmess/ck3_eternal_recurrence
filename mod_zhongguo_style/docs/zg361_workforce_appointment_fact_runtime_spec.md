# GENERATED FILE -- edit tools/gen_zg361_workforce_appointment_fact.py
# Workforce #274 native appointment fact runtime contract

Status: **CK3 script static-ready; not loader-live or production-live.**

This independent package retires only the three legacy Native/Career
appointment aliases consumed by Workforce #274:

```text
zg361_we_ad_external_position_type_id
zg361_we_ad_external_position_receipt_id
zg361_we_ad_external_position_receipt_hash
```

## Truth source and business action

The public subject-scope ABI is:

```text
zg361_workforce_appointment_fact_m274_appoint_and_consume_effect = {
  TICKET_OWNER = <appointing owner>
  TICKET_SUBJECT = <subject>
  TICKET_CYCLE = <cycle>
  TICKET_CASE = <case>
}
```

It accepts no caller claim that an appointment succeeded and accepts no
caller-provided position type, receipt id, hash, title or HC source.  It first
joins the current AD state-4 case with the consumed #266 requisition, #272
offer and #273 candidate objects.  The subject must be the appointing owner's
living landed direct vassal, must still hold the frozen primary title, and the
same #266 formal-HC reservation must remain active.

The only write action is CK3's native `appoint_court_position` for
`zg361_workforce_appointment_fact_court_position`.  Exact-build 1.19.0.6 source documentation in
`game/common/court_positions/types/_court_positions.info` says this effect
requires the recipient's liege to be the employer and exposes
`on_court_position_received` with `scope:liege` and `scope:employee`.
`game/common/scripted_triggers/00_court_position_triggers.txt` requires
`can_appoint_char_to_court_position` before the effect.  This package follows
both contracts.

The position is a zero-salary native **probationary settlement office** with
exactly one slot per employer.  It is visible/eligible in the appointment
picker only during the exact request tick, is restricted to celestial
duke-or-higher employers, and has a negative AI vacancy score so vanilla AI
cannot independently fill it.  The project's authorized celestial-manager AI
path may call the same exact ABI.  After Workforce #274 consumes the matching
receipt, the package immediately uses native `revoke_court_position` and
requires the position to be absent before marking its receipt consumed.  A
next-day single-flight audit releases an acknowledged native position even when
the adapter/consumer remains blocked, then delegates a published exact tuple to
Workforce's resume seam.  Status 5 keeps exactly one daily reconciliation in
flight while the same state-4 case remains eligible; RED and complete outcomes
never requeue.  The package records that release only when
its own verified revoke command made the position absent; native invalidation,
vacation or death cannot be relabelled as package-owned release.  One slot plus
this bounded teardown prevents permanent occupation or stacking.

`is_shown` provides a static picker-visibility boundary, not live UI proof.
Until a CK3 artifact checks every character/court surface, this package does
**not** claim zero UI impact: while a request is pending or externally blocked,
the held probationary position may still appear on a character detail or other
engine-owned position surface.  Successful same-tick settlement releases it;
otherwise the next-day audit attempts the same native release and exact-tuple
resume.  This is a
static lifecycle contract, not live proof that every CK3 surface hides it or
that the delayed event always executes on the target build.

This proves one real, bounded probationary court-position appointment and an
immutable historical receipt that the appointment occurred; it deliberately
does not claim the subject still holds that temporary office after settlement.
An exact-tuple dispatch tombstone prevents a replay from appointing again even
when callback evidence was lost and the audit had to fail closed.  It
does not prove promotion to an unrelated vanilla title, ministry or council
seat; the frozen primary title is provenance and a holder postcondition, not a
claim that this package granted that title.

## Receipt boundary

The request tuple is intent only.  It cannot set the three external aliases.
A receipt may be sealed only after all of these facts exist together:

1. the custom position's engine-owned `on_court_position_received` callback;
2. the subject actually has `zg361_workforce_appointment_fact_court_position`;
3. `is_court_position_employer` names the frozen appointing owner;
4. owner, subject, cycle, case and state still match the live AD case;
5. primary-title holder and the exact #266 HC lineage still match.

The immutable receipt freezes owner, subject, cycle, case, state=4, result=1,
position type id `3612741`, source kind
`1`, primary-title scope/tier/holder, #266 HC case
and reserved amount, #272 offer object and #273 candidate object, native
employer, callback/holder postconditions, deterministic id/hash, bounded native
release provenance, publication state and one-time consumption.
The id/hash are derived inside the package after the callback; they are not
cryptographic signatures and are never accepted from a caller.

Only then does the package call the existing strict
`zg361_we_submit_ad_appointment_receipt_effect`.  The three legacy aliases are
written by that existing adapter, not by the request action.  The wrapper calls
`zg361_we_m274_route_a_effect` only from a sealed native receipt: either the
verified position is still held, or this package's own bounded revoke already
released it.  It marks its receipt consumed only after Workforce copies the
same type/id/hash, sets `ad_external_appointment_consumed=1`, and the temporary
position is absent with package-owned release provenance.
Duplicate delivery is status 2 and does not appoint again;
wrong tuple, source collision or missing native postcondition is typed RED.
Callback ordering may return status 5; the hidden single-flight audit retries
only while the immutable receipt remains unconsumed, and calls the Workforce
resume seam only after publication.

## Integration and readiness

The Workforce #274 player option and authorized AI path both call this
package's wrapper with the same four frozen arguments; neither calls
`zg361_we_m274_route_a_effect` directly.  Same-tick status 6 continues through
the existing path.  If the native callback is delayed, hidden event 9001 calls
`zg361_we_resume_m274_after_native_appointment_effect` with the sealed receipt
tuple.  That seam consumes #274 once, internally closes hired #275, then opens
#269 for a player owner or continues the authorized AI route in the background.
An exact continuation receipt makes duplicate hidden events idempotent.  No
central runtime, runner, native bridge or provider file is modified here.

Static generation/tests prove the command/callback/postcondition ordering,
five-field/source binding, absence of caller-supplied success, one-time receipt,
alias publication through the strict adapter, route-consumption join, BOM/key
parity and reproducibility.  There is no new CK3 loader log, paused snapshot,
save/load result, named MCP action/query or live employer/holder evidence.
Readiness therefore remains `ck3-script-static-ready-not-live`.

## External producer ledger replacement lines

The shared ledger records these three fields as static-closed, awaiting
loader/live proof:

```text
zg361_we_ad_external_position_type_id — real custom court-position callback producer; #274 callers wired, awaiting loader/live proof
zg361_we_ad_external_position_receipt_id — sealed once after callback + employer/holder/title/HC postconditions; #274 callers wired, awaiting loader/live proof
zg361_we_ad_external_position_receipt_hash — same immutable receipt tuple checksum, never caller-supplied; #274 callers wired, awaiting loader/live proof
```

## L0 commands

```powershell
py tools/gen_zg361_workforce_appointment_fact.py --check
py tools/test_zg361_workforce_appointment_fact.py -v
py -O tools/test_zg361_workforce_appointment_fact.py -v
py tools/validate_local.py
```
