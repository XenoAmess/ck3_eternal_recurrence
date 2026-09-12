# R503/R504 Stage 10 provider-readiness RED and fix

Date: 2026-09-12 (Asia/Shanghai)

## Live result

Old round R503 terminated before current round R504/PID `214796` became the
sole CK3 process. R504 passed the loader in 62.79 seconds with 303 database
callbacks and zero fatal signatures. It then advanced 36 game days, drained ten
known event windows, and paused on the target `zg361mg.120`, instance `28`.
No target option or acknowledgement was attempted.

The preserved direct RED is
`28EB9B11BA023A44839D7F6A6F0D4991F87196E06D22581AAFC4811ED3E35F0B`.
Its exact native provider frame binds player/subject `27181` and owner `36354`;
the F case is `state=5`, `active=false`, with matching owner and subject. This
matches the event trigger in `zg361_manager_governance_runtime_events.txt`,
which requires F state 5 and inactive before the player-visible event can open.

## Root cause and minimum correction

The Stage 10 action incorrectly required the manager-governance provider's
aggregate `readiness.ready`. That aggregate also waits for unrelated
distribution-settlement lifecycle fields. In the target frame those future
fields are correctly unavailable, so aggregate readiness is false even though
the F case and Stage 10 event are terminal. This is an acceptance-contract RED,
not a mod gameplay RED.

The provider gate now requires only the fields used by this acceptance claim:
subject binding, case identity, same-frame readiness, exact owner/subject, and
F `state=5 / active=false`. The hot-resume admission also accepts a preserved
target-event postcondition RED in addition to an unknown vanilla-event RED,
provided no input was attempted. It retains the original timeline origin,
absolute 120-day deadline, current PID, and bridge generation.

Focused normal and optimized tests both pass `14/14`; Python compilation and
diff checks pass. No broad test, new CK3 launch, mod change, DLL change, or
extended runtime was added. P1 remains `8/9` until the retained current round
R504 action completes and independently saves/acknowledges the terminal frame.
P2 remains `LOCKED`.
