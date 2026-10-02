# Ordinary campaign autoplay over an existing native MCP session

`tools/native_campaign_autoplay.py` exports `await run(client, config)`. The
caller supplies the existing official MCP client, or a queue transport returning
the real serialized official MCP result through `await client.call_tool(name,
arguments)`. The module does not attach/inject, own a pipe, load the SDK driver,
operate the desktop, change game rules, manufacture dates, select observer mode,
or alter character ages. The profile provider remains authoritative for the
frozen process/build, Steam offline state, task lease and crash guard. Any tool
error or identity change stops actions. Localization never participates in
option selection or completion.

```python
from pathlib import Path
from native_campaign_autoplay import CampaignConfig, run

result = await run(existing_client, CampaignConfig(
    start_date=frozen_start_save_date,
    target_date=requested_target_save_date,
    baseline_date_raw=frozen_start_native_clock,
    save_directory=Path(isolated_save_directory),
    evidence_directory=Path(new_policy_evidence_directory),
))
```

The frozen baseline is caller evidence from the original save/native clock. A
later policy start preserves that baseline and consumes the current campaign;
it never redefines the start date from its first observation. The initial
native checkpoint may already be later than the baseline. Every checkpoint is
archived by actual body date and full SHA-256, using exclusive creation and
independent archive-byte hashing. Source saves may subsequently be overwritten;
archived checkpoints and indexed request/response receipts are never rewritten.

## Ordinary control and decisions

The policy reads a guarded campaign snapshot, uses the provider-bound no-argument
pause, resolves bounded event chains while paused, checkpoints, sets an ordinary
speed (default 5), and resumes with the exact freshly observed public revision.
Every command is sent once. Subsequent confirmation performs only bounded
guarded snapshot reads, retaining the complete original MCP response. The only
legacy RED results recoverable through these reads are the two exact RuntimeError
messages for delayed pause/resume or current-pause postconditions. Event/save
RED, unknown RED, guard failures, timeouts and unresolved dispatches are never
blindly replayed.

An optional `pause_provider` passed to `run(client, config, pause_provider=...)`
uses the independent [qualified clock pause MCP](clock-pause-mcp.md). Default
native behavior is preserved. Controller target/build/session verification and
separate original receipts are mandatory; a successful independent pause still
requires the original native client's paused/date readback. Resume, event, save
and speed contracts stay with that existing native client. The controller path
never retries a failed native pause or fabricates its status.

Only context options with `shown=true` and `enabled=true` are candidates. Rank
noncritical options first, then options without observed stress increase, then
native index. Send `native_option_index + 1`; rendered order and synthetic
active-event slots are not the command payload. Indicators are explicitly
partial. The module claims neither complete effects nor optimal gameplay, and
does not use option text. After selection it verifies the previous full event
instance disappeared while the campaign remained paused, then observes/query
any next event independently.

Natural changes to the engine's living current player are recorded without a
one-life projection or an inferred heir identity. `pending_character_interaction`
is a pending mail observation; its presence alone does not prove a blocking UI.
While the campaign runs, the policy lets the engine advance and the mail expire
naturally. Indexed `pending-mail-observation` receipts record its presence,
absence, raw-clock progress and paused state. Absence is not reported as an
accepted, refused or otherwise resolved interaction. The policy sends no
interaction command and retains the existing no-progress timeout.

A pending mail alongside a confirmed scripted event does not prevent that
event's typed query/selection. Pending mail also does not invalidate paused
readback after the policy's own pause, event, save or simulation command. An
unexplained paused snapshot with mail and no scripted event returns `await_root`
before another command. Explicit blocking/unknown modal or game-over fields,
any unexpected pause, a dead/unavailable player, event chain bound, or no native
clock progress still stop the policy. There is no modal dismissal, player
switching or repeated resume shortcut.

### Clock progress across succession

`paused=false`, `map_ready=true`, and a new living current-player ID describe observed state; they do not establish that simulation ticks have resumed or a succession modal has closed. Require distinct actual raw-clock readings across the bounded progress window, and keep a `native_clock_no_progress` stop with its original evidence. An actual current-player transition does not permit inventing the next heir or dismissing an unknown modal.

An operator-owned exact 1.20.0.3/build25652598 regression with the frozen n2 DLL illustrates this limit: the new player was alive and unpaused/map-ready while raw date remained `77755008`. A complete immutable save had matching body/meta date `3876.2.22` and `played_character.has_open_succession=yes`. Its corpse-aware selected-record audit receipt SHA is `a0efe0634207585a84001b8f3a594b7243cbe6aba66de3ace834293a4f199256`; it explicitly did not prove window dismissal or later progress. The n2 private death/succession query/action flags are OFF, so the existence of legacy source declarations is no usable exact-patch3 modal capability.

The operator reviewed the normal current-heir continuation and dispatched one existing [semantic desktop action](reviewed-desktop-semantic-action-mcp.md). Its ACK needed independent readback. Frozen `0420-snapshot.json` SHA `30b0090c6ec805c99c52b789dcbb8305a9daa2d670c713b6060fb55ca374b7ff` then recorded raw date `77755032`, one normal day later, with the same process/DLL/session/generation and living current player. This establishes observed timeline progress after that reviewed action sequence, without a restart, reinjection or baseline reset. It does not qualify a generic native succession-continuation tool or an automatic modal policy.

Subsequent events still require actual canonical window-context options with genuine shown/enabled state and the ordinary selection postcondition. Likewise, an observed spouse relationship after ordinary UI proposal is relationship evidence; it does not qualify the SDK's separate native marriage submission path. Specific death, inheritance, event and marriage outcomes, source decisions and raw saves/screens remain in the independent project. Main retains these reusable observation boundaries.

## Save date and completion

Checkpoint scheduling uses the exact clock reader's 24 raw units per day and a
default interval of 365 elapsed days anchored to the frozen baseline. This is a
save trigger, not a calendar projection or completion proof. The module reads
all plaintext `SAV0100` checkpoint bytes, hashes them, checks file stability,
locates the unique top-level body `date` outside quoted/nested content, and
requires `meta_date` agreement when present. It compares the actual file's
path/size/SHA/native submission clock with the official checkpoint receipt.
Binary or ambiguous saves fail closed; no Rakaly dependency is imported.

`completed` requires an archived native checkpoint whose **body date** reaches
the requested target. Snapshots, raw-clock arithmetic, metadata dates alone,
command ACK, or the legacy succession-lifecycle report cannot establish it.
Annual checkpoints may overshoot a requested date; they prove reaching at least
the target without changing the engine calendar. The result returns the final
checkpoint proof and evidence directory. Every stopped result retains the last
checkpoint and the original reason.

## Thin caller errors after successful actions

Preserve the canonical `INSPECT` route, `ck3_query_native_profile_v1`, when supplying a queue/composite client. `CampaignPolicy.run()` reads its `observation` into the internal `native_observation` before binding the independent pause controller's target to the native campaign. A caller that omits this route/observation triggers the existing target-identity refusal; it must not fabricate an identity or bypass the guard. If a separate pause already succeeded before the caller error, retain its actual receipt and immediately take a fresh native snapshot before any further dispatch.

Reporting errors belong to a separate layer from submitted game actions. The policy object's retained save proof is `last_save_proof`; a stopped result dictionary uses `last_checkpoint`, while a completed result uses `final_checkpoint`. A caller must use the contract of the object/result it actually holds. An unsupported reporting attribute or exception serializer can fail after event selection or checkpoint success. Preserve those original action/save receipts, record the wrapper exception with `str(error)` when no richer documented shape exists, and repair only the caller's reporting. Do not replay an event, pause, proposal or save to fix report assembly.

These boundaries were exercised by transient caller omissions/reporting mistakes during the same operator-owned campaign. They were not defects in the authoritative profile tool or policy, and required no changes to SDK/native/policy/controller. This documentation update introduces no new test result or century-completion claim; it records how to keep successful business evidence intact while diagnosing a caller failure.

## Verification and evidence boundary

`python -m unittest discover -s tools -p test_native_campaign_autoplay.py` uses
an actual asynchronous FakeClient surface and temporary plaintext saves. It
tests elapsed simulation and immutable full-byte archives, native versus
rendered option indices, partial-indicator preference, delayed RED preservation
without command replay, exact RED rejection, offline/lease/crash tool errors,
no progress, unknown pause, player terminal state, process identity changes,
body/metadata disagreement and later entry with a frozen baseline.

These offline tests verify policy/transport and artifact contracts. They do not
claim any campaign length, CK3 behavior or live run passed. Live acceptance must
bind the caller's frozen source/build/profile and original baseline receipts to
the returned original MCP receipts and archived checkpoint bytes.

The 2026-10-02 pending-mail repair passed 21 tests, including running mail with
date progress and observed disappearance, mail at initial/later unexplained
pause, mail alongside a scripted event and periodic saves, mail without clock
progress, and explicit blocking state with mail. The trigger was R8 policy01's
`non_event_modal_requires_root` stop while native snapshots remained unpaused
and advancing. Later snapshots observed the mail disappear without interaction
input; the campaign continued to an archived body date `3853.7.9` (899 elapsed
days), then to 1,196 elapsed days under the root operator. These are bounded
reported milestones, not proof of the hundred-year target. The repair changes
only caller policy: the running DLL, frozen service and sole live client stay
unchanged. `open_kaishek` prevalidation is not applicable to this Python
transport/observation policy; the regression fixtures exercise its real async
client interface rather than CK3 script semantics.

The initial package passed all 15 tests. A separate read-only check of the R8
native checkpoint and its first-year milestone archive read all 41,961,544 bytes
from each file: body `date` and `meta_date` both equal `3852.2.8`, and both full
SHA-256 values equal
`8c35dd8ff296a49c578ef75ea2885880290b7e08741931f1440eb3a8b8ec71d4`.
That check dispatched no game command and proves only those existing artifact
bytes and dates, not the requested hundred-year campaign.
# Event presentation rendering wait (2026-10-02)

The policy bounds presentation-only read retries by `postcondition_timeout_seconds` (default 20 seconds, including calls). Only verified `event_window_not_materialized` and `event_splash_transition_in_progress` for the bound instance qualify. Each iteration reads a fresh guarded snapshot, requires paused state and binds the new revision; changed events return to the outer event loop for a new identity binding. Layout/scope/identity/unknown errors and guard failures stop immediately. No selection is dispatched until actual window options are ready; no input is replayed. Authored counts and synthetic `active_event.options[].enabled` do not qualify an option. See [the exact patch3 observation contract](fullscreen-event-context-1.20.0.3.md).
