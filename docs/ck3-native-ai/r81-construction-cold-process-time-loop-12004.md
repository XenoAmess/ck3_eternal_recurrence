# R81 repeated construction cold read: actual process-time encoding mismatch

Status: source-ready, NOTRUN. Root owns the sole registered consumer FIRST
and hotSDK/live continuation. This patch changes no construction tuple,
native code, schema, ACK, snapshot revision or game date.

After the release-ledger BOM repair's Root FIRST, R81 hot04 ordinary attempts
002 and 003 both selected `private-query-player-construction-receipt-v1` with
phase `construction_cold_applied_requery`. Both returned an independently
verified `applied`, `in_progress` receipt. Attempt002 took **91.090895 s**,
05:22:11.190451–05:23:42.281346 UTC; attempt003 took **38.429751 s**,
05:27:51.599912–05:28:30.029663 UTC. Neither advanced the game day or submitted
another action. Saved evidence is under
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/r81-sdk-bom-hot04/operator/gameplay-responses/`,
files `002-r81-bomfixed-normal-turn01.json` and
`003-r81-bomfixed-normal-turn02.json`.

One projection of these saved replies and the current small construction
ledger proved the actual discrepancy. PID is **175696**, episode is
`native-29829-2bc2d599f7f9`, date is **53288568**, and the query material frame
is native **5**, public **2**. Attempt002 records post creation
`20261009123752.997404+480`; attempt003 records
`20261009043752.997404+000`. These are the **same UTC creation instant**.
The actual WMI path preserves a local DMTF offset, while the existing fallback
can report UTC. The source compares these raw strings as part of a tuple in
construction priority/planning and material follow-up, so equivalent encodings
alternately look like a new process. The original start receipt remains
native3/public4 and its original creation string remains preserved.

At SDK source `af6c1f46bbee22b5efc48d49eb98c75de129f7ce`,
`construction_formal_consumer.priority_construction_receipt` and the main
applied-plan branch use literal tuple inequality. The same raw comparison
exists at the finite construction query/watch, previous-spend, Service
consumption and M5 proposal entries. The project already provides
`environment.same_process_creation_time`, which compares the supported
Windows encodings by UTC instant. No new time parser or identity protocol is
needed. The construction-scoped helper requires the same PID and accepts
either an identical raw timestamp or that existing semantic equality.

The minimal patch applies that same comparison consistently within this
construction pipeline. It leaves every raw timestamp in durable evidence;
it does not rewrite the ledger, manufacture a revision, erase a cold marker
or replace the original start receipt. A genuinely different PID, different
creation instant, earlier native frame or earlier date still takes the
existing independent cold material read.

Root's only new node is
`test_r81_construction_creation_time_registered.py::test_registered_r81_actual_creation_encodings_stop_repeated_cold_query`.
It consumes the two actual saved material receipts in private fixture state,
tests both encoding directions, and invokes registered `ck3_plan_turn` twice
per receipt. The real Service/ordinary construction consumer must choose its
following LIFE step, retain the material receipt and original start unchanged,
and issue no native query or submit. The same fixture also confirms that a
different actual creation instant/PID and an actual earlier frame retain the
existing cold read. Outer lookup, snapshot carrier and the baseline chooser
are explicit seams, and no Game/CIM/SDK process is queried. All worker
test/import/build/hash/Game calls and capability credit are zero. Root owns
FIRST and subsequent real ordinary continuation; the original loops remain
saved failure evidence.
