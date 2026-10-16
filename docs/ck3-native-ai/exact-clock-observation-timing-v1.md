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
