# R576-R579 static scoreboard drain RED and scope correction

## Result

R579 reconfirmed the real promotion route and the corrected `.148` option-1
close. The take then repeated the post-close scoreboard RED despite the bounded
retry added after R575.

The retained native command history contains 20 scoreboard queries over five
wall-clock seconds. Every response remained at native snapshot revision `11`
and returned `status=unavailable`, `unavailable_reason=acl_inconsistent`, with
all widget fields `snapshot_unavailable`. A paused CK3 session does not publish
a new GUI snapshot merely because the read-only query is repeated. The retry
therefore has no useful recovery mechanism and is removed.

The scoreboard query is also outside the necessary product-event drain scope.
For a product-event span, the clean end frame is recorded before the event is
closed, the bound native option receipt proves that its instance advanced, and
the next span restores an independent source through a new CK3 round. A
scoreboard surface that was never opened in that round cannot affect the
accepted span and is discarded with the round. Requiring its unavailable GUI
snapshot only adds a false gate after the required evidence is complete.

P2 remains **`0/8` accepted clean spans** because this file contains only four
closed spans. The final promotional-video lock remains in force.

## Live evidence

Attempt directory:
`Z:\ck3_mod_rewrite\_runtime\p2-capture-r576-r583-e4ff677-20260913`

- R576 was the managed warm-up and terminated before gameplay capture.
- R577 closed spans 1 and 2.
- R578 restored Stage 10, reached real `zg361mg.120`, and closed span 3.
- R579 restored the promotion source, traversed real
  `zg361pp.147 -> zg361pp.148`, and closed span 4.
- The `.148` bound-option close remained GREEN.
- Native command-history entries `101..120` are the 20 identical unavailable
  scoreboard queries at snapshot revision `11`.
- R576-R579, FFmpeg and the injector all terminated. Canonical cleanup is
  GREEN; gameplay PID lineage was `95768, 190652, 133220`, and the current
  process inventory is empty.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| capture plan | 13,417 | `53F52B1601E0F8246BEE61EFA0C96B6EEFAC07568ABC62BCF6B0F619C5F7019F` |
| capture-cell report | 4,332,313 | `B9FB27B15206AB2C7E2B9A7267DEEF71935626383173F65FF97A1C6492A27B41` |
| `.148` bound-option GREEN gate | 2,326 | `943D08B79137106A603858F9BA87D7CE3276AF64C48061209A8E9A1A9A563C55` |
| retained native driver state | 1,533,481 | `439FA0E77B43DF4E1AB3562AD864A25684362E27312C0473BACB7B9FBEEE70D2` |
| cleanup | 36,652 | `D7A1220357EB072382859298C23D0DD2150BA3F15A7053282E1F4CD7D3C369E6` |
| capture timeline | 34,412 | `2D9A978EA87261374A69A599963C6A3D00F7AE77B06E1FD55E033A38D7BB744C` |
| raw failed MKV | 275,240,901 | `C9EAEE69BC256982B3AAEDC96EB475887C6D8E163F03D7EB1D531698121E5C3D` |

## Minimum correction

`drain_after_span` now applies evidence by surface kind:

- `product_event`: require the active event to be absent after its bound close;
  the next cross-span restore disposes of the round;
- `named_widget`: retain the existing scoreboard provider check, including the
  explicit close receipt and hidden-modal observation;
- any surviving event remains typed `span_drain_not_empty` RED.

Focused event-choreography tests are **21/21 GREEN**; Python compilation and
`git diff --check` are GREEN. No mod script, DLL source, public MCP interface,
open_kaishek API or dependency changed. One new continuous live take is needed
to pass this corrected drain boundary and continue to spans 5-8.
