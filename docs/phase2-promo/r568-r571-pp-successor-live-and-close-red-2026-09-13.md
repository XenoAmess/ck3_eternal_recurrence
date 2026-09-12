# R568-R571 PP successor live GREEN and capture-close RED

## Result

The corrected production edge from `zg361pp.147` to `zg361pp.148` is now
**production-live GREEN**. R571 selected option 1 on the bound real
`zg361pp.147`, advanced one game day, and independently queried real
`zg361pp.148` instance `273` on the same CK3 connection generation and played
owner. Both clean capture gates for the fourth span then completed.

The take still failed while closing `zg361pp.148`. The generic finalizer called
the single-option event helper, but the production definition has three enabled
options. The helper correctly retained RED and rejected the operation before
submitting any click:

```text
failure_reason = native interruption is not an exactly-one-option event
event_instance_id = 273
option_count = 3
selection_submission = null
```

This is a capture-orchestration defect. It is not a mod business defect and
does not invalidate the live `.147 -> .148` result. Because the failed MKV
contains only four closed spans, none of those spans are counted as accepted
P2 footage. P2 remains **`0/8` accepted clean spans**, and the final
promotional-video lock remains in force.

## Live evidence

Attempt directory:
`Z:\ck3_mod_rewrite\_runtime\p2-capture-r568-r575-b00e1c1-20260913`

- R568 was the managed warm-up and terminated cleanly.
- R569 passed loader, seed, exact-mount and material-error gates, then closed
  spans 1 and 2.
- R570 restored the qualified Stage 10 source, reached real `zg361mg.120`, and
  closed span 3.
- R571 restored the registered promotion source, proved the corrected real
  `.147 -> .148` transition, and closed the begin/end visual gates for span 4.
- The RED happened only when the finalizer attempted to close `.148`.
- R568-R571, FFmpeg and the injector all terminated. Canonical cleanup is
  GREEN; PID lineage was `38220, 100360, 208720`, and the current process
  inventory is empty.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| capture plan | 13,417 | `CBC6A6B7153AA97CEAB6995E5C4A9F49312D620E2E028C13828CFE7D8F8F9FCC` |
| capture-cell report | 4,332,208 | `B22BD4E04A421437CBCAE9211E24FFF2C5858D288B52B7DEFBEAD9F4524562FB` |
| `.148` close RED gate | 535 | `029A9830DB8201FD0A9A640D98E3676D68C1D068341AE64523866E9790795326` |
| cleanup | 36,797 | `54837EF36BF02E2BD48B07D0FB9A2B01CB8D0BE55AE814F6A290F8D2F94B9CDC` |
| capture timeline | 34,414 | `C6CE75E37286B8CEA77007E4CDBBEA6D1A942632CBC74373ECC73C4FB7FB3BDD` |
| raw failed MKV | 264,422,812 | `78A0CDE59B2B1AFA36B71F8085DFFCFE9CA2D55B816A7FB3EDEA0B7BA94490DF` |

## Minimum correction

Only the `zg361pp.148` close branch now uses an explicit bound-option helper:

1. require the same paused event instance, a valid public revision and an
   in-range option number;
2. submit authored option 1, which is the canonical route already used by the
   preceding promotion action;
3. require the event instance to advance without advancing the game date or
   unpausing CK3;
4. preserve a typed RED sidecar on any mismatch.

All existing exactly-one-option close paths remain unchanged. Focused event
choreography and runner-plumbing tests are **41/41 GREEN**; Python compilation
and `git diff --check` are GREEN.

No mod script, DLL source, public MCP interface, open_kaishek API or dependency
changed. One bounded live retry is required to exercise this corrected close
branch and continue toward the single continuous eight-span P2 take.
