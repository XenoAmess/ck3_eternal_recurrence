# Ordinary life-advance: eight-day war-result cap

On 2026-10-15 the requested war-result dismissal target changed to **within ten
game days, best effort**. The previous seven-day target produced a global
six-day life-advance request cap whenever the native war-results query capability
was present. In the N39 P01 immutable response sample, 188 of 190 life-advance
requests asked for six days; observed completion was usually seven days and
sometimes eight. The global cap, not the peaceful horizon selector, was the
reason ordinary peace often stopped after about one week.

This change raises only that capability-dependent cap from six to eight
requested days. Peace remains bounded by the original 30-day selector before
the cap. A route-free war retains its seven-day selector; tactical route,
combat, retreat, assault, and observed siege slices retain one day. The
six-day war-result clear lease is unchanged: it becomes due during an
eight-day request and the next ordinary policy turn queries the window.
Event, interaction, terminal, and changed active-war semantic frames can
still stop the slice before its date horizon. Crown-authority retry deadlines
still reduce the horizon where applicable.

This is a best-effort cadence, not a hard ten-day guarantee: published-frame
and pause lag can add days, and no new live callback is introduced. A
30-day cap was rejected because a result window alone and a declaration
cooldown expiry do not interrupt Native life-advance. Production admission
requires the usual cold source freeze and live observation of requested and
actual elapsed days; this document is an offline code/test receipt only.

Source overlay: `D:/codex-ck3-demos/2026-10-14-robert-30year/lifeadvance-eight-day-horizon-opt01/candidate/xar_autoplayer/bridge/native_driver.py`
uses the already-frozen P17 event/history Native candidate as its base.
