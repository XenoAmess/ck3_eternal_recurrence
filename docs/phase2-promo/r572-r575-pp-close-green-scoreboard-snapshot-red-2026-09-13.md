# R572-R575 PP close GREEN and transient scoreboard snapshot RED

## Result

The focused `zg361pp.148` close correction passed live. R575 submitted
authored option 1 against bound event instance `273`; the native postcondition
advanced that instance to `null` at the same game date while CK3 remained
paused. The new bound-option gate is **GREEN**.

The continuous take then retained a new RED in the immediately following drain
check. The first scoreboard-state query after the event window closed returned
`status=unavailable`, `unavailable_reason=acl_inconsistent`; all fixed widgets
reported `snapshot_unavailable`. The same provider had returned available for
the preceding three spans. No active event remained, and no game date, player,
PID or connection-generation drift occurred.

This is a one-frame GUI observation boundary after closing the event window,
not a mod business failure. The first four spans closed their clean begin/end
gates, but the file is still an incomplete take. P2 remains **`0/8` accepted
clean spans**, and the final promotional-video lock remains in force.

## Live evidence

Attempt directory:
`Z:\ck3_mod_rewrite\_runtime\p2-capture-r572-r579-6228a16-20260913`

- R572 was the managed warm-up and terminated before gameplay capture.
- R573 closed spans 1 and 2.
- R574 restored Stage 10, reached real `zg361mg.120`, and closed span 3.
- R575 restored the registered promotion source, traversed real
  `zg361pp.147 -> zg361pp.148`, and closed span 4.
- The bound-option receipt records native revisions `10 -> 11`, public
  revisions `77 -> 78`, date `53245536 -> 53245536`, and event instance
  `273 -> null`.
- The immediately following command-history entry `101` is the unavailable
  scoreboard drain query at the same native snapshot `11`.
- R572-R575, FFmpeg and the injector all terminated. Canonical cleanup is
  GREEN; gameplay PID lineage was `215244, 130104, 50692`, and the current
  process inventory is empty.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| capture plan | 13,417 | `60C254BD3579C229D687F978D868459B996B5FDD5316E43CD02656104F070C1F` |
| capture-cell report | 4,332,117 | `FC26ECEFF45CB9B0023EF064F470C4CD69D7DE6ADF825BADBEDF1517FFD2F22C` |
| `.148` bound-option GREEN gate | 2,325 | `8CB2993D5AF3EE12F002230A962E61E7DB7B32DE28341C930C6F5F793AE2163C` |
| retained native driver state | 1,013,507 | `F958A1352D7ED6D55F94D976B06EF28056C13EF8FC55A9D2CE59D9CD575523AF` |
| cleanup | 36,649 | `8A10C9541771CA8A6892A77F9CF3BD85B28A5D2D1FCF4E035FA4655E932C1977` |
| capture timeline | 34,405 | `AAF4D2F2C7ECFC13DD791DB5F113DC6D80C3262FE67E04EB0864F1FAD95E94D6` |
| raw failed MKV | 262,378,122 | `173FD81F67D0D640E68AD8F161D1173681EB6168B0B38B31D1116CCF1BED32C8` |

## Minimum correction

The drain check now retries only the existing typed
`scoreboard_visibility_provider_unavailable` result for at most five wall-clock
seconds. Every observation must remain paused and retain the same game date,
played character, bridge PID and connection generation. A real event, binding
drift, non-transient provider error or timeout remains RED. The retry count is
included in the GREEN drain receipt.

Focused event-choreography tests are **21/21 GREEN**; Python compilation and
`git diff --check` are GREEN. No mod script, DLL source, public MCP interface,
open_kaishek API or dependency changed. One new continuous live take is needed
to exercise the bounded retry and continue to spans 5-8.
