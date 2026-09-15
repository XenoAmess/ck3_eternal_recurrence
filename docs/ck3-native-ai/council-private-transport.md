# Council application-main controlled transport (1.19.0.6)

Status: **static-ready only**. This is the private Council26 acceptance route, not
an advertised gameplay capability or evidence that a councillor was appointed.
The exact CK3 EXE SHA-256 remains
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

Council23 already installed `ExecuteCouncilApplicationMainV1` in fixed mailbox
slot 41. Its worker never configured a source binding or submitted a request.
Council26 adds a build-time `XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1`
switch, default `OFF`. With it `ON`, the worker binds the exact candidate
reader/enrichment/projection to the currently published paused snapshot. The
private query is not placed in the adapter capability list or hello frame.
The action path still requires a separately admitted exact final-gate callback;
the query-only configuration returns `complete_native_action_gates_not_bound`
for assignment and receipt requests.

Council27 adds the independent build-time
`XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1` switch, also default
`OFF`. It is valid only together with the Council26 private route. With it
`ON`, the fixed transport context binds the exact Council25 four-gate callback
for a sealed controlled candidate. The default query-only candidate still has
no action callback. This private switch does not register a public query/action
or add either to the adapter capability/hello advertisement; live behavior for
already-councillor, guest, pending interaction and replacement fireability
must be accepted separately before any production advertisement.

The separate `XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1` switch
is also default `OFF` and requires the private route. It enables
`private-query-council-final-gates-v1` for a paused, same-revision read of the
provider's complete candidate rows on application-main. This gate-only build
keeps action admission false: private assign/receipt reject before a helper is
called. A queued gate query uses the same non-cancelling private status step and
60-second terminal window. If any exact native row is unavailable, the entire
gate vector is typed `unavailable` with no partial rows; guest/pending false and
incumbent fireability true must come from the native result, not from the
visible GUI. Query results are unadvertised and do not prove a councillor
change or next-turn consumption.

The controlled native pipe request is a protocol v1 `execute_step` frame. After
the host reports a paused native snapshot at revision `N`, submit:

```json
{"type":"execute_step","protocol_version":1,"request_id":"council-query-1","step":"private-query-council-composition-candidates-v1","expected_revision":N}
```

This returns typed `pending` once the mailbox accepts the request. The worker
does **not** synchronously wait or cancel; the CK3 application-main pump must
run before the result can appear. Poll with a fresh request ID:

```json
{"type":"execute_step","protocol_version":1,"request_id":"council-status-1","step":"private-council-application-main-status-v1","expected_revision":N}
```

An `idle` status means no request is in flight. A completed status returns the
Council23 typed envelope, including exact source revision, incumbent and
candidate rows. Treat `query_unavailable`, infrastructure failure, timeout and
unexecuted as separate outcomes. The bounded read-only acceptance window is
60 wall-clock seconds from query acceptance to a typed terminal status; it
must not modify the source save or advance the game date. A real action still
requires four separate paused-live final gates (already-councillor, guest,
pending interaction and replacement fireability), helper-only ACK, an
independent later paused frame and formal next-turn consumption.

### Naturally occurring final-gate scene queue (2026-09-15)

The frozen R695 and R700 gate-only readers are lawful controlled read-only
entries, but their runners pin the old R639/R696 owner, date, incumbent and
11-row scene. Do not reuse those sealed candidates as a newly encountered
campaign frame. R695's frozen terminal SHA-256
F053530B6164A32B2425E54B953531F631AC2A608754D968FF2E050482D03330
has 11/11 complete standard-feudal steward rows at paused native:3: three
already-councillor positive candidates, zero guest positives, zero candidate
pending positives, and all 11 incumbent-fireability results true. R700's
frozen terminal SHA-256
C0C31AC426ED82E7CCBF49572044DC69E5EAB8CCAB4DA81733ECB231DC0340E5
independently sees the new incumbent 33433 after a real new-process reload,
with the same three missing positive gate scenes. The read-only
inspect_council_final_gate_scene.py checks a SHA-pinned private terminal,
exact build, same paused native/public revision, complete typed gate rows,
zero helper invocations and unadvertised status; it reports positive native
IDs and candidates with just one blocking gate as scene classification only,
not action or final-gate acceptance. A row with both guest and pending
interaction does not isolate either rejection class.

The sole CK3 operator should wait for a real ordinary feudal paused frame,
freeze its exact checkpoint and runtime pair, then reseal a gate-only
candidate with the private route and final-gate query ON and private
assignment OFF. A guest-positive or candidate-pending-positive row must
come from the native gate result; a fireability denial additionally requires
an occupied steward seat with native incumbent_can_be_fired=false. For a
genuine positive row, a separate controlled private-action candidate may
check the matching typed rejection without helper invocation and unchanged
independent game state. The exact vanilla
is_blocked_from_being_fired_from_council_trigger reads
council_task.can_fire_position=no or a matching owner's
block_fire_councillor variable
(00_councillor_triggers.txt SHA-256
D7A10D08D2F73D770B56A375ECEBCBE02486038B4E9648B492BEE786A482C9C2);
the vanilla liege-petition effect can set that timed variable
(00_petition_liege_effects.txt SHA-256
9440F91322C32690BCC3091736EA888EA07F73A2AF69C4B7AF3963BEC6F6C9CC).
These are source-proven natural-scene leads, not permission to force a
petition, set the variable, edit the save, or infer a false gate from a
visible GUI. The public query/action stay unregistered and unadvertised until
all four distinct native gates, a real assignment result, independent later
paused incumbent and formal next-turn consumption are accepted.

The query-only Release candidate was built with Visual Studio 18 and the
exact-build source path. It passed the Council23 source verifier, the Council26
normal/optimized source contract and a Release `xar_ck3_bridge` build. The
bounded live query and four action gates remain to be run by the single CK3
instance owner.

Compatibility assessment for root master `c3af806c` and `open_kaishek`
main `c88206e5`: the new `private-query-council-final-gates-v1` step and
`xar.ck3.private.council-final-gates/v1` nested schema are default `OFF`,
private, and absent from hello/MCP registration. The passive `open_kaishek`
council profiles pin only the unchanged public
`query-council-composition-candidates-v1` /
`xar.ck3.council-composition-candidates/v1` contract and
`game.action.assign-councillor-v1` request/ACK/receipt; there is no private
step consumer in that profile. This version pair has no demonstrated public
interface break and needs no Java adapter change. This comparison is static;
paused-live gate evidence and public registration remain pending. Reassess if
the private step is promoted or a pinned public field changes.
