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

Only context options with `shown=true` and `enabled=true` are candidates. Rank
noncritical options first, then options without observed stress increase, then
native index. Send `native_option_index + 1`; rendered order and synthetic
active-event slots are not the command payload. Indicators are explicitly
partial. The module claims neither complete effects nor optimal gameplay, and
does not use option text. After selection it verifies the previous full event
instance disappeared while the campaign remained paused, then observes/query
any next event independently.

Natural changes to the engine's living current player are recorded without a
one-life projection or an inferred heir identity. A dead/unavailable player,
pending non-event interaction, observed unknown modal, unexpected pause, event
chain bound, or no native-clock progress returns `await_root`. There is no modal
dismissal, player switching or repeated resume shortcut in this policy.

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

The initial package passed all 15 tests. A separate read-only check of the R8
native checkpoint and its first-year milestone archive read all 41,961,544 bytes
from each file: body `date` and `meta_date` both equal `3852.2.8`, and both full
SHA-256 values equal
`8c35dd8ff296a49c578ef75ea2885880290b7e08741931f1440eb3a8b8ec71d4`.
That check dispatched no game command and proves only those existing artifact
bytes and dates, not the requested hundred-year campaign.
