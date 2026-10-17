# SDK43 recovered-map startup: historical repair

This directory preserves the complete narrow owner delta and the original
manual-review producer as research text. It is not a public launcher and must
not be applied to an active runtime. Runtime paths and session IDs describe
this historical input only.

Attempt01 used an automatic-continuity review that the existing Root-only
startup guard rejected before the SDK pair was admitted. Its stderr remains
unchanged. Attempt02 created distinct STARTED/log files, pinned Root's actual
map and overlay review (`f57d843c…`), and retained the old queue/source freezes.
No automatic review, expired-review bypass, or fabricated pixel approval was
introduced. CLI flags in the historical producer cannot replace actual review.

The preflight receipt records three rejected metadata mutations. Closed Driver
validation/hash and the current live guard were explicit test substitutes;
that offline result alone did not admit or launch a live SDK. Root separately
performed startup and the bounded health run. The proposed 120-second automatic
wrapper was withdrawn and was not the deployed repair.

See [source pins](SOURCE-PINS.json), [the full minimal owner delta](attempt01-to-root-reviewed-attempt02.patch),
[actual Root review](ROOT-P43-RECOVERED-MAP-ADMITTED01.json), and
[the preflight boundary](ATTEMPT02-FULL-PREFLIGHT-TESTS.json).
