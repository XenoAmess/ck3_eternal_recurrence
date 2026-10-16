# Exact-day clock observations

Machine `xenoamess-full-tower-eb9d2c1186`, 2026-10-16 UTC.

Actual P26 AUTO46 advanced raw 53411184 to 53411208 at speed 5. Its MCP wrapper
took 7.5803153 seconds; resume-to-paused took 7.070033 seconds. Four existing
public-change waits were 0.095962, 5.433462, 1.304798 and 0.205667 seconds.
These nested timings must not be added again to the outer clock duration.
The original evidence does not include the observer/pump samples during that
wait, so 5.433 seconds cannot yet be assigned to Game CPU or a fixed polling
delay. Later SEM65's observer values cannot reconstruct AUTO46's stages.

The optional SDK profile reuses `XAR_CK3_ARMY_TIMING_JSONL`; it adds no new
startup flag or output root. During the existing exact-day primitive it writes
at most five `xar.ck3.exact-clock-observation.v1` phase rows: resume begin,
resume observed, first new date, paused observed and final. Rows contain
allowlisted cached heartbeat/owner/observer scalars and observed ages. Missing
Native timestamps remain null. The profile does not query Native or change
clock commands, speed, timeouts, waits, pause behavior or persistence.

A single limited-information process handle samples Game process CPU at the
phase boundaries, with current hello/bridge PID equality and creation FILETIME
checks. It closes in `finally`; no process enumeration or per-poll CPU sampling
is introduced. These are whole-process CPU counters, not a main-thread tick
measurement. Source identity changes, unavailable counters and counter
regressions do not become false zero deltas. Disabled profiling opens no
handle; profile I/O failure cannot replace the original gameplay result/error.

Public portable validation passed nine checks. It exercises the production
clock and two wait methods before/after removing only the three instrumentation
hunks, preserving Native command/action lists, results and failure cleanup.
Native/Win32 boundaries are mocked; SEM65's cached scalar projection and
AUTO46/47's raw dates identify the source facts, not a new live timing sample.
The small profile is diagnostic, with no demonstrated speed improvement yet.

External source/evidence root:
`continuation42-cold-prep/native20-cold-generation02/p24-elapsed-hotpath-audit01/`.
`CLOCK-PROFILE-FINAL.json` SHA-256
`cc156b65be22ad57fdb9016f2da2f341e3fe0766a7ceb6d4c5e7b9be885233e0`;
`ACTUAL-WINDOW-ATTRIBUTION.json` binds exact completed-response files and the
timing log prefix. New Native21/SDK27 measurements remain runtime work owned
by Root. This single day does not prove 0.5 seconds/day or uninterrupted 30 years.

## Actual Native21/SDK27 profile

Later R3 evidence binds Game6068/creation FILETIME134366412679616931 and SDK
application230732. Completed FULL3 RPC4–63 took 37.086448 seconds for five
game days (7.4173 seconds/day); FULL64 RPC65–124 took 79.307115 seconds for
17 days (4.6651 seconds/day). Combined processing is 116.393563 seconds/22
days, or 5.2906 seconds/day. The 47.783-second gap for Root idle/control setup
is separate; including it gives 7.4626 seconds/day. None is a whole-session rate.

Fifty phase rows cover ten exact-day clocks: 28.8056837 seconds of clock wall
time and 5.390625 seconds of whole-Game CPU. The other twelve gathering days
have no exact-clock CPU profile. The low CPU/wall ratio is observed evidence,
not proof of a particular wait or main-thread bottleneck. Twenty-one of the
22 days used speed1. Current actual stock `game/common/defines/00_defines.txt`
lines3–8 configure `GAME_SPEED_TICKS={2,1,0.5,0.2,0}`; speed1's two seconds/day
alone prevents the requested half-second/day rate on those paths.

`native21-cold-generation03/p27-clock-profile-audit01/ACTUAL-P27-CLOCK-ATTRIBUTION.json`
SHA-256 `a3d9035c025c29fe892e3da80f64509a0b61618c6fed0eb1176d9e1c19aa9051`
pins the 1,464,465-byte timing prefix and completed responses. Its analyzer
uses completed evidence, without reading the live Driver. A faster battle
observation candidate remains offline; this measurement is not that fix's
performance validation or a thirty-year success claim.
