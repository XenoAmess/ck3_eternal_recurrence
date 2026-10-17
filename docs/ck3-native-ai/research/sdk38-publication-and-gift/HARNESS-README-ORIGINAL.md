# Portable qualifier and campaign-ledger handoff

`portable/` contains four byte-identical reviewed pure qualifiers and a small
parameterized extraction of the clean feeder's ledger binding. There are no
runtime process calls, registry writes, SDK submissions, fixed runtime roots,
or ledger transitions in these modules. `COPYTARGETS.json` is a proposed public
tools mapping; the public writer owns the final import layout.

Run the focused suite in `portable/` with `python -B -m unittest discover -p test_*.py`.
It passes13 tests, including all seven first-heir PRE-read guards, exact negative
Native boundaries, and the ledger binding's first-FULL ordering and identity checks.
The retained small response projections preserve original rejection facts; their
test sequence numbers are variable. No SDK or Native is invoked by this suite.

The qualifications remain distinct:

* Construction: exact matched paused-frame rejection before the query executor.
* First heir: only the seven compiled PRE-read guards, with the complete scalar
  diagnostic grammar. During-read and unspecified errors remain rejected.
* Faction publication: a pure planning wait failed before querying a receipt;
  previously submitted faction business may still be pending and must be retained.
* Faction submit admission: the original operation was a business-submit attempt.
  The exact compiled Native error exits `ReadAction` before mailbox submission.
  It grants only fresh semantic observation and queue-failure reset, preserving
  the Python submission-started ledger. It neither replays the gift nor claims
  a successful gift or an independent receipt. The framework's historical
  `read_only_precondition` label does not turn the original submit into a query.

`campaign_continuity_binding.bind_campaign_continuity` validates an already
published FULL through an injected existing request prevalidator, verifies the
exact runtime/queue and official Game binding, then changes only the newly loaded
feeder module's ledger path. It does not attach, open, fail, reset, or write a
continuity window. Ordinary `WindowLedger` guards remain responsible for the
verified frame and monotonic counters. After an actual repair, the caller must
use the actual recovery/admission baseline rather than the initial zero frame.

The actual deployed source was the campaign-specific `launch_clean_feeder_v2.py`
SHA cf3115d2, not this newly extracted public API. `actual-launcher-v2.patch` is a
research recipe only, including its original source pins. The initial launch
mistakenly targeted the previous campaign's ledger. The ledger's original bad
metadata event was retained; correction4251 documents that error without rollback.
The new campaign's Game state and business credit were not inherited from it.

The future watchdog ledger patch08e9 was never deployed as the running capture
watchdog's full continuation. Its active attach-only mode does not execute that
feeder renderer. Correcting a future renderer's ledger path alone does not prove
its post-repair baseline or qualify a complete automatic continuation.

Package review: derived handoff material,48-hour review after public integration;
source input pins remain available from their original current task evidence.
No additional storage reservation or runtime deployment is performed here.
