# Unknown blocking choice: SDK contract and acceptance boundary

The SDK source includes a capability-gated path for unknown top modal windows.
The existing typed event and pending-interaction windows remain first-class
routes. This source integration does not establish live CK3 acceptance; the
Native producer, typed mailbox and exact DLL must be loaded and observed in
the current game before the generic route is considered available. The SDK
does not infer blocking from `active_event`, `paused`, `map_ready`, a modal-like
visual surface, or an enabled button alone.

The ordinary full state snapshot first supplies a candidate
`top_exclusive_modal_choice_hint`. Only `present` from the verified application
main-pump cache, with its top receiver identity and a 2,000 ms maximum age,
triggers the typed read. Expired or untrusted observations are `unknown`; an
`absent` value from an unverified worker is not evidence that no modal exists.
The independent `query-core-frame-v1` retains its existing strict contract.
Within the SDK semantic snapshot, a changed top root/status invalidates the
public revision even at the same date and Native revision. Pump/thread stamps
remain in diagnostics and cannot churn the public revision by themselves.

The generic path is eligible only when a typed Native query produces one
complete, same-frame window DTO with an authoritative `blocking_proof`:
`blocks_simulation`, or `exclusive_modal_blocks_input` with a native source
showing the receiver is exclusive and intercepts the actual game input.
The latter is UI blocking, not a claim that simulation is paused. A choice
must be a real, visible, enabled choice callback; close X and HUD controls
are excluded. The DTO must carry the full catalogue, stable `window_id` and
instance, source provenance, action token for each choice, and full actor,
episode, connection, process, snapshot, public/native revision and date
binding. A candidate with no authority or incomplete catalogue is
`mechanism_unavailable`, not an actionable fallback.
The parameterless public step is the read-only query; selection is an internal
typed Driver method requiring its fresh query ID, token, window instance and
full source frame. It is not advertised as a parameterless MCP action.

Known policies retain first priority. Existing event and interaction adapters
use their authorized typed presentation paths. When an event and top modal
coexist, a same-frame Native query may establish whether the top modal is an
independent GUI root. Generic selection is allowed only for the exact .4
event-controller/GUI-owner-tree relation, with the event instance and top
receiver both bound; a same-root or unknown relation yields to the typed
event adapter. Pending interactions still yield to their typed adapter because
no equivalent GUI-root relation has been qualified. For an unknown generic window, the
separate pure selector chooses the enabled option with the least top then
least left Native bounds. A sole enabled choice can be chosen without bounds;
multiple choices without bounds are unavailable. It never uses OCR or mouse.

The planned result carries the unmodified DTO, selector explanation and
selected token. The service writes an immutable `before` receipt before any
token dispatch and an `after` receipt containing the original native result.
The Native select ACK alone does not prove the old instance disappeared. A
fresh Native recensus may independently verify that old receiver is gone;
only then may Service record UI clearance, still with zero business credit.
Otherwise Service reports pending and an unresolved same-instance query
cannot submit a second token. Failures preserve original evidence and never
authorize replay. Completed pairs can be collected by a
separate offline worker; source review is not awaited on the ordinary turn.

Native `source_identity` identifies the runtime GUI receiver; its pointer is
specific to this one window. A reviewed empirical UI-recovery entry requires stable build/backend
and widget/callback identifiers, an independent old-instance-gone observation,
and later game-date progress in the same actor/episode. It only records that
this choice cleared the UI in that observed case; it does not claim business
effect or optimality. Each future action still needs a fresh Native query,
token and full frame binding. Until those facts exist the offline result is
`unresolved`. The external worker writes its `--output-dir` to
`<attempt>/state/evidence/unknown-mandatory-choice-reviews`. On a later
occurrence the SDK reads a reviewed entry only after a fresh query. It
rechecks the immutable before/after/response files, the source key, and the
launched DLL SHA and PID. It marks the source as previously observed UI
recovery, then still chooses from the new complete catalogue using the user's
current first-enabled rule and a new token. Old tokens are never loaded.

During life advance, a newly observed, owner-bound top modal interrupts the
progress wait even if CK3 has not yet advanced a day. The Driver requests
pause and returns the actual elapsed date; an armed exact-day sentinel must
be canceled with a verified receipt before returning early. No choice is
selected inside life advance. If pause or cancel cannot be verified, the
ordinary error remains an error. The queue classifier accepts the narrow
`modal_interrupted` composite as a zero-business observation, not a completed
day or permission to replay the clock. The next ordinary planner turn reads
the fresh Native catalogue.

The final02 Native hint could observe an unpaused modal while its typed
query/select owner gate still required a paused, map-ready frame. The
prospective final03 Native packet has a separately verified unpaused owner
path, but the Root queue must still account for a `pause-map` failure after
life advance before this can resolve a blocked modal end to end. Until that
queue path is verified, a failed pause remains an error, not a successful
choice. The hint alone is never a selection capability.

The source package needs Native query/select mailbox routing, actual capability
advertisement, a fresh owner-pump snapshot hint, and a typed Driver token
method. Those SDK components are present behind the capability gate. Live CK3
acceptance, the final Native DLL binding and Root queue admission remain
separate, Root-controlled checks. Offline C++ serializer fixtures and the
focused SDK regression tests are kept under
`ck3_autonomous_player/tests/fixtures/mandatory_choice_v1` and
`ck3_autonomous_player/tests/unit/test_mandatory_choice_sdk_integration.py`.
