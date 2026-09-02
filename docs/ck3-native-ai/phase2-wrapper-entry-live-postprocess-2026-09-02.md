# Phase-two wrapper-entry live postprocessing (2026-09-02)

This checklist and parser classify the next bounded private wrapper-entry live
without starting CK3 or changing any public ABI/readiness state. The parser is
`ck3_autonomous_player/native_bridge/research/analyze_phase2_wrapper_entry_live.py`.

Run it against the frozen runner report and the exact caller extractor artifact:

```powershell
py -3.13 ck3_autonomous_player/native_bridge/research/analyze_phase2_wrapper_entry_live.py `
  --runner-report <live-artifacts\runner-report.json> `
  --caller-artifact Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\completion-wrapper-callers-static-extract.json `
  --output <live-artifacts\wrapper-entry-postprocess.json>
```

## Checklist

1. Verify the caller artifact still binds CK3 `1.19.0.6`, EXE SHA-256
   `2D00FF...DB86`, exactly 618 unique callsites, and canonical list SHA-256
   `32B88F...1A8C`.
2. Recursively collect heartbeat objects and collapse duplicate `(pid,
   sequence)` snapshots.
3. Require the private `phase2_wrapper_entry_observer_v1` object and all frozen
   fields: installed/failure, entry count, caller return/callsite, scheduler
   owner, producer-list carrier, thread and QPC.
4. Require nonnegative typed values, installed with failure zero, and a
   non-regressing entry count and positive-entry QPC within each PID.
5. For positive entry samples, require callsite membership in the frozen 618
   set and nonzero return address, owner, producer-list, thread and QPC.
6. Report sampled last-value distributions for caller, owner, carrier and
   thread. Report whether the producer-list carrier is stable or changed across
   those snapshots. These are heartbeat samples, not a lossless entry log.
7. Record input byte SHA-256 values in the output before interpreting it.

Frozen observer v1 has no return counter. The output therefore always records
`return_dimension.status=not_observed_by_v1` and does not attempt an
`entry-no-return` decision. This missing dimension is not RED.

## Typed decision matrix

| Evidence | Decision | Status |
|---|---|---|
| observer absent or malformed | `observer-schema-missing/invalid` | RED |
| not installed or failure nonzero | `observer-install-or-runtime-failure` | RED |
| entry counter regresses | `entry-counter-regressed` | RED |
| positive-entry QPC regresses | `entry-qpc-regressed` | RED |
| final entry count zero | `no-entry-observed` | NO-GO |
| sampled caller outside frozen set | `entry-caller-outside-frozen-set` | RED |
| positive entry with zero context | `entry-context-incomplete` | NO-GO |
| valid caller, owner and carrier | `entry-caller-owner-carrier-observed` | GREEN |
| return count absent in v1 | `not_observed_by_v1` | NOT-RED |

The retained old-raw runner is a negative control: it predates the wrapper
observer and correctly produces `observer-schema-missing`, artifact SHA-256
`9CB4BF4ACEF808FE190C51D7D4F751B1EF0C441E362F35341F3AB56586F41561`.
