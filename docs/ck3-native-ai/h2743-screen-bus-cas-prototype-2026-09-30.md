# H2743 screen-bus CAS protocol prototype

This branch is stacked on the static-seal Draft #728 at `d4004005`. The live
runner still returns `LIVE_STOP_CAS_MIGRATION_PENDING` for the current-HEAD v5
candidate before reading the bus or launching a process. The new
`h2743_screen_cas_protocol.py` is an isolated protocol candidate, **not wired
into live preparation or `--run`**. It does not change or reinterpret the
attempt 17 static seal, which is bound to the unchanged d400 runner bytes.

The candidate pins both CLI source and installed bytes to reviewed #685
`e7c0727b7e851de803f79ce04806feccfa33149d`, SHA-256
`D6629F52EE098C709C5A85ADBC629F40E8B2724BE9CC1F29FAF48AF215E96121`.
Each command uses `--bus-dir` and `--expected-cli-sha256`. A fresh task claims
`ck3-screen:acquired` through `register`, then passes its last authoritative
sequence to `heartbeat` and `release-screen-cas`. Each response is compared
with the locked event stream, task snapshot, sequence tail and every screen
resource record, including stale and `done+screen` records. Command argv,
stdout, stderr, return code, readback and failure stop are written into a new
external evidence directory. Ambiguous operations forbid blind retries.
The constructor unconditionally rejects the authoritative bus path, even if
those reviewed bytes are later installed there; this branch only exercises an
isolated bus.

The focused integration tests explicitly inject the reviewed #685 CLI into a
**temporary bus** and copy its bytes into that bus's temporary installed path.
They exercise claim, heartbeat, cleanup-gated release, a stale unreleased
owner, wrong expected sequence, CLI SHA mismatch and event-stream corruption
under normal Python and `-O`. Without `H2743_REVIEWED_BUS_SOURCE`, they skip
instead of silently choosing an old local or installed CLI. The reviewed CLI
is not copied into this branch's committed source; it remains owned by #685.

## Required before any live use

1. Merge or otherwise adopt the reviewed CAS bus source, install the same
   exact bytes on the authoritative bus during a managed quiet period, and
   independently recheck source/installed SHA. The existing authoritative
   installation is old, and the historical XQOL screen record is unreleased.
2. Migrate all screen-capable callers to the same CAS fence and resolve that
   stale record through the separately audited recovery procedure. Do not
   clear it with old `status` or treat a stale flag as a released resource.
3. Wire the protocol into H2743's actual managed supervisor. Bind release to
   verified worker/CK3 process-tree cleanup evidence rather than a bare
   boolean, and save the exact evidence bytes and hashes.
4. Obtain a new static/preflight attempt for the then-current runner bytes,
   fresh Steam offline image review and independent live-gate review. Only
   after those gates may a new commit remove the v5 hard-stop.

The current result is `CODE_PROTOTYPE_ONLY / AUTHORITY_STOP / LIVE_STOP`.
There were no authoritative task-bus mutations, screen claims, CK3 launches,
native H2743 reads or gameplay actions in this work.
