# R532/R533 scoreboard close candidate-boundary RED (2026-09-12)

## Verdict

R533 is the first P2 attempt to pass the real scoreboard source, native `open`,
independent later-state and clean-frame gates. The visual wrapper returned
GREEN with `verified_pass=true`, and both begin/end screenshots show the real
received-scoreboard page. The run then stopped after the first span because the
post-recording scoreboard close was classified as
`scoreboard_close_not_green`.

This is a Python capture-choreography RED. The reusable action cell deliberately
returns `RED / production_capability_not_advertised` when the transition is
independently verified but the production capability is still withheld. The
promo open wrapper already treats that exact result as a capture-only candidate
boundary. The close path instead required the lower-level result itself to be
GREEN, so it rejected the same verified candidate boundary during cleanup.

The recorded first span is not counted independently: the eight-span report is
RED and the recorder stopped with seven spans missing. P1 remains `9/9 GREEN`;
P2 therefore remains `0/8` until a complete clean run produces an intake-ready
report, timeline and evidence index.

## Rounds and evidence

- R532/PID `199660` completed the isolated Frontend warm-up and terminated
  before gameplay.
- R533/PID `141800` was the sole gameplay instance on CK3 `1.19.0.6`, using
  `-loadsave=autosave`, the isolated userdir, bridge
  `3D41E88ABB0FD5CF812D67CB233D2BFD7A01A7661358E7D9375BCFD31E23CF48`
  and injector
  `6A4E7A045F54771BB027AC8E0B89B6BE131A62D99BCE239CC28BA0A9C1261E2C`.
- Loader, paused-seed and FFmpeg start gates passed. The scoreboard open wrapper
  is GREEN; its nested action cell records an accepted `open`, independent
  observation sequence `2 -> 3`, observed-state revision `1 -> 2`, and a visible
  received modal/page.
- Both clean gates for `phase2_fact_quota_calibration` are GREEN. The report is
  still RED because cleanup rejected the close candidate and the remaining seven
  spans were never recorded.
- Cleanup is GREEN. R532/R533 are terminated and CK3, FFmpeg and injector
  inventories are empty.

Artifact SHA-256 values:

- plan: `426C77504FE2E9B7768506BFC9228ABBB7D5ABE345AAE6A96FF71DD01CA86032`
- outer report: `54685B16CD802D17745B2841D3CDC932D3138358F5B5C37CCAEB54A7FA22A689`
- inner report: `E6469823BC85C98C480A8B761C3CD485F1F4DEE00FFD70E5E3B9C509B7CEB864`
- visual action cell: `30B480BE846860756834286D37073C989C0B6BB5A620BEC0441D656B0DDA6590`
- cleanup: `87105653CB2281B332E75705CDFE47C0AF40CDDBB2A857EC25A4DFFDDAA4F665`
- timeline: `6768CA74357D8BB733A65ED8B3A95FE64364B5D60A9C565EA06182F1D8F4C59C`
- evidence index: `7BC87D107DDA502752D235112A53CF5C6E0C46A4E35E471986D8B9DF6DC882AF`
- failed 23,298,471-byte MKV:
  `67A434E9D7679C326204E77B56DD7FF12FAED204B0DD4A9408A99A9EC66BF1AF`

## Minimal correction

The named-widget cleanup now requests `requested_action="close"` explicitly and
accepts only these two forms after requiring `verified_pass=true`:

1. the ordinary production-advertised GREEN result; or
2. the exact capture candidate boundary: result RED, production advertisement
   false, and failure reason `production_capability_not_advertised`.

It still requires the dispatched action to be `close` and the independent later
query to report `zg361_scoreboard_modal.effective_visible=false`. No public MCP
shape, action contract, provider semantics, mod content, DLL, game file, launch
configuration, load order, production capability flag, edit gate or publication
gate changed. This does not trigger an open_kaishek compatibility update.

Focused validation only:

- event choreography runner: `16/16` GREEN;
- promo runner plumbing: `20/20` GREEN;
- scoreboard bridge unit module: `7/7` GREEN;
- `git diff --check`: GREEN.

Two initial test commands selected interpreters without the repository's
`pyautogui` or `jsonschema` dependencies and failed before collecting tests.
Running the same targets with the shared repository promo environment produced
the GREEN results above. No broad suite or unchanged CK3 retry was run.

