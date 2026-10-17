# R37 closed peace advance review (offline)

Input: immutable `p37-newgame-measurement-prep01/NEW-GAME-FIRST-WINDOWS.json`
and the 21 closed, small `CUMULATIVE-TURN-000062..000082.json` receipts under
`robert30-clean-campaign01/runtime/p37-queue`. The accompanying
`summarize_closed_slice.py` reproduces the latter projection without opening
Driver, SAVE, video, or large AUTO bodies.

The 62–82 settled slice took 16.191044 wall seconds for 33 game days
(0.490637697 s/day). Four ordinary `life-advance` turns contributed exactly
7, 9, 8, and 9 days. Turns 66 and 76 were still in
`native_war_entry_forecast_required`; turns 78 and 80 were in
`native_war_discovery_cooldown`. Four intervening war-results queries observed
`hidden`, and turn 82 submitted a Crown action. The slice contains 17 zero-day
turns, no SAVE, and ends before a later fault. It does not establish sustained
campaign speed or the cost of a SAVE-inclusive window.

SDK37 already has a guarded multi-day peace path:

- `bridge/native_driver.py:29438` bounds a route-free, war-free starting frame
  at 30 days; tactical routes, combat/retreat, and observed siege retain their
  shorter bounds.
- `bridge/native_driver.py:24414` calls `ordinary_peace_horizon`, which keeps
  the existing short bound (at most eight days) unless six optional checks,
  declaration and family cooldowns, construction completion, the next 90-day
  checkpoint, owner-bound absence of a top modal, and the current actor/episode
  all establish future deadlines. Unknown/due state stays short.
- `bridge/native_driver.py:29094` stops a running slice on a new event,
  interaction, terminal state, owner-bound top modal, new war or player army,
  changed war progress, or new stationary threat, in addition to its date
  horizon. The actual 9-day results show the short requested horizon is not
  an exact-day stop; only the separate exact-day Native sentinel validates
  `completed_daily_ticks` and zero overshoot.

Do not replace the short bound with 30 days on these receipts. They lack a
sealed same-frame snapshot of all deadline inputs at turns 66/76/78/80, and
the Crown opportunity appeared immediately after the fourth slice. Enlarging
the interval would risk passing a due review or declaration opportunity.
The generic modal hint is an owner-cache observation; `unknown` is not proof
of no blocker. Nothing here proves every new modal is published promptly while
the map runs. The existing short fallback preserves that uncertainty.

The smallest safe SDK-side follow-up is *read-only diagnostics*, default off:
at the `ordinary_peace_horizon` call, emit the already computed base/short/
selected horizons and the **first failed qualification** (scope, UI hint,
optional deadline, declaration/family, construction, checkpoint). Keep the
return value and all reads unchanged. A later closed run can then show whether
an actual 8-day fallback has a repairable missing deadline. Only if all guards
are proven on one paused frame should the existing <=30-day path be enabled;
it needs no new time-advance interface. This candidate is a design note, not
runtime code or a claim of qualification in R37.
