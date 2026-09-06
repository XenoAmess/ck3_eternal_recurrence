# R174: third-party disease notice interrupt

R174 proved the native review-now action and its independent B1-active
postcondition on the new R172 manager seed. At `date_raw=53156832`, the healthy
retained PID 68028 then paused on vanilla `health.2201`; product diagnostics had
not become RED. The native event query bound root/player 32904, sick character
32797, `health_court_owner=32904`, a disease flag, a background province, and
the exact visible native option indices `(5, 6)` from seven authored options.

CK3 1.19.0.6 source in `game/events/health_events.txt` shows that native option
5 starts the sick character's own treatment choice, native option 6 begins a
court-physician search, and native option 7 is the no-action branch. In this
live projection only options 6 and 7 are visible because root may choose care
but no physician is available. The exact interrupt contract therefore selects
authored option 7/native index 6, avoiding an unrelated physician-search chain.
The disease had already been applied before this notification and is not used
as promotion evidence.

The contract and regression are isolated in purpose-specific health files. The
live PID is intentionally retained so the Python-only contract update can be
loaded by the reconnect client without restarting CK3 or changing mod bytes.
