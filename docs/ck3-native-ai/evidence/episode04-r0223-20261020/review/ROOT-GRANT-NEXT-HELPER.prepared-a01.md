# Next Root grant helper: pre-write read-only refresh

This is an offline source proposal for a later integration. No D/W, signal,
observer or game was changed. The R0223 original grant and freshness gap remain.

Keep the existing three explicit Root declarations and create-only signal. The
current `make_root_admission.py::build` consumes exact awaiting/identity/input
pins and the static base-capacity GREEN record. It does not consume a fresh OS
and lease observation or a live combined measurement immediately before writing.

After the existing source/identity/date/scope checks and before opening the
signal, call the existing read-only facts path in the same helper process:

1. Reopen the declared PID with query/synchronize rights only, compare the exact
   GetProcessTimes creation FILETIME, require the original process active, and
   require CheckRemoteDebuggerPresent to succeed and explicitly report false.
   Enumerate the current visible window owned by this same process without
   focusing, capturing or input. Native controlled-window ID remains distinct
   from HWND; do not manufacture a new native owner observation.
2. Reuse `screen_bus_lease.checked_owner` against current canonical task rows,
   exact source/checkout and CAS ownership. Record non-atomic scan provenance.
3. Read the latest complete newline of the authoritative combined guard stream
   (including rotated parts), bind its exact base-capacity pin/machine/run, and
   require age<=30s, complete paired measurements, GREEN, no alarms/errors, exact
   component caps/unspent and nonnegative margins. Preserve path/offset/length/
   SHA of that original row; do not hash or copy the entire stream.
4. Re-evaluate the1090s remaining guard and measurement age immediately before
   the existing exclusive-create write. Unknown, stale, mismatched, partial or
   unavailable facts reject without a signal. Do not retry an existing signal.

Embed or pin the newly read facts in the grant so a later reviewer can distinguish
the explicit human declarations from the helper's current mechanical checks.
No automatic image judgment, SDK query, debugger attach, enable/day or new API is
needed. Root must still directly adopt the current owned-window metadata and
the single DR scope; mechanical refresh does not manufacture that declaration.

For later focused validation, cover one allowed source-bound write plus stale
guard, debugger-query unknown, PID reuse, foreign/expired lease and an already
existing signal. Each rejection must leave no new signal. This proposal adds no
new qualification or retroactive credit to R0223 and requires no old matrix run.
