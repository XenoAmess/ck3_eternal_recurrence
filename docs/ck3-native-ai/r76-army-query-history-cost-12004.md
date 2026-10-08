# R76 army query history copying

R76 ordinary turns selected `query-army-strengths-v1` in responses 010 and 028.
Response 010 took 148 seconds; the response files are approximately 166 MB and
169 MB. These durations include planning, native queries, serialization and IPC;
they are not measurements of any single internal operation.

The persistent SDK loads Driver state once when adopting its session. Successful
read-only queries append complete history and defer durable encoding to the
existing barrier. The identified avoidable work is full history copying at
three semantic frame reads in the army query path.

These frame reads now omit the transcript while retaining current native
revision, date, player control and the independent after-frame check. Default
public snapshots still expose full history; persistence and resume retain every
history row. This changes Python frame handling only and introduces no native
observer or gameplay action.

The new `test_native_army_query_history_first0.py` exercises production dispatch,
ordinary public export, durable resume, and a changed after-frame. Its first
execution receipt belongs under
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261008/native-driver-r76-query-latency-first01/`.
Actual live timing remains to be measured after deploying the qualified SDK.
