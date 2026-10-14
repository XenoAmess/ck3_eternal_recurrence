# Wartime Python execution optimization (2026-10-15)

The continuous Robert campaign performs deterministic Python planning and typed
MCP/native commands; it does not invoke an LLM per game day. SDK03 advanced
10 game days using 301.92 seconds inside calls and 3.86 seconds between steady
calls. Initial bootstrap/manual gaps are excluded. This is an observed campaign
sample, not a controlled replay benchmark.

## Implementation

The Driver keeps the existing exact actor, episode, public/native revision,
connection and ordered army scope checks, then detaches only the 11 core fields
consumed by semantic snapshots. Complete manager input remains in the original
query cache and persisted history. Three immutable real 32 MB Army inputs
produced identical detached public fields: 0.418--0.555 s before versus
0.019--0.025 s after per cache read. Eight deliberate identity/frame/scope
mismatches retain the original invalidation behavior.

Automatic camera follow reuses a verified anchor only for the same complete
paused frame and landed-title target. New dates, revisions, episodes, process
or connection generations and hotspots use the original native path.
Explicit typed map navigation invalidates the automatic anchor. A reused
receipt states that no new native command was submitted; it does not invent
a fresh postcondition. War choices, required tactical reads and result credit
are unchanged.

Before adoption, SDK05 had 34 visible camera receipts, all already_centered.
Complete frame/title/province grouping gives 14 unique groups: 20 redundant
automatic navigation paths (58.8%). Army compact summaries omit camera
receipts and are not counted. None of the 34 calls performed a camera write.
This count is not a latency forecast.

Optional scalar timing now covers automatic camera work and route/preview
native pipe waits. The external SDK queue also retries the observed Windows
sharing-lock failure in local atomic replacement, never a gameplay command.

## Verification and live boundary

Camera and core-cache tests: 37 passed against the frozen performance source.
open_kaishek precheck is not applicable: changes concern Python object
projection and presentation scheduling, not Paradox script execution.

External evidence root: D:/codex-ck3-demos/2026-10-14-robert-30year/

- continuation37/ROOT-P01-SDK-FREEZE.json: exact candidate source manifest.
- route-python-hotpath-opt01/DELIVERY.json: real-input core equivalence.
- war71-query-dedupe01/REVIEW.json: actual query and camera grouping.
- performance-candidate01/BEFORE-LIVE.json: pre-adoption live timings.

## Same-Game adoption

P02 is live on retained CK3 PID 127268, with the same Desktop1 OBS segment.
The first completed 30-turn batch advanced 15 game days in 167.29 seconds
(11.15 s/game day), versus 30.58 s/day in the earlier steady sample: 2.74x
observed throughput. Inputs differ as this is the continuing campaign.
See performance-candidate01/AFTER-LIVE-FIRST-30.json.

Core/cache/camera and existing persistence/hot-restore checks passed: 40 tests
against the tracked implementation. The branch also includes the earlier
live core projection and byte-equivalent JSON encoding optimizations on which
this candidate depends; they had previously remained only in the frozen SDK.

Full camera confirmation measured about 5.2 s versus about 0.005 s for reuse.
A route-query native pipe wait measured about 0.02 s. Initial P02 route-query
and 3-day advance calls measured 0.081 s and 3.571 s respectively.

P01 first exposed an outer-harness coupling to the camera binding, after its
3-day advance had already succeeded. That original result was classified
once using its actual preceding same-frame camera receipt, without replay.
P02 carries the preserved original camera receipt with an explicit
previous_same_frame source, retaining existing consumer compatibility.

The continuous campaign and recording remain active. These timings do not
claim another war victory or the 30-year goal.

