# G2 focused contract evidence (2026-09-03)

## Result

At 08:32 Asia/Shanghai, the G2 read-only contract slice passed its minimum
offline regression without starting CK3:

```
18 passed, 12 subtests passed in 14.44s
```

Command (from `_root-promo-split-20260902`):

```
$env:PYTHONPATH='ck3_autonomous_player/src';
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' -m pytest -q --disable-warnings \
  ck3_autonomous_player/tests/unit/test_raiktor_surrender_truce_contract.py \
  ck3_autonomous_player/tests/unit/test_g2_truce_preview_entry_observer_seam.py \
  ck3_autonomous_player/tests/unit/test_g2_truce_preview_entry_observer_v1_contract.py \
  ck3_autonomous_player/tests/unit/test_g2_truce_preview_entry_observer_integration.py
```

The slice covers:

- the exact `evaluated_days`/no-expiry root contract and its descriptive
  `open_kaishek` profile binding;
- the exact-build preview seam (PE/PData/unwind/anchor and vtable filter);
- source-level proof that the private observer does not call the duration
  evaluator, read `this+0x108`, mutate state, or advertise a public gameplay
  capability;
- default-off diagnostic-only wiring through the native driver/service path.

The test result is static/fixture evidence only. It does not certify a paused
native value, a CK3 runtime read, or the `evaluated_days` readiness gate. The
preview observer remains a private default-off seam and cannot be used to
derive expiry or submit a termination action. No guessed activity opcode or
schema allow-list was added.

## Frozen inputs

- CK3 build: `1.19.0.6`;
- executable SHA-256:
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`;
- preview seam SHA-256:
  `1178F46B21A307CCBB5497278951C7BB00F259B4C70B6FB2011D2D318E3CE7E9`;
- `open_kaishek` profile remains descriptive only, with native/runtime
  certification false.

## Next G2 item

The next value-bearing step is still a single, exclusive CK3 launch slot:
obtain an exact-build paused artifact that reaches the evaluator and proves
two same-frame reads. Until that external runtime evidence exists, the public
wire remains fail-closed and this offline regression is the deliverable for
the current cycle.
