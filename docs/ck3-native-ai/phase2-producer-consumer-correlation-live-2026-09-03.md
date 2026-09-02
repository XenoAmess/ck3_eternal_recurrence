# Phase 2 producer-to-consumer correlation live (2026-09-03)

## Result

The one authorized serialized live run ended at the bounded loader timeout.
The exact producer selected and published the loader task once, but the raw
counter at the completion consumer hook `0x3B9DEA7` remained zero. The typed
decision is therefore `no-consumer-hook-hit`, not an identity mismatch: this
run never crossed the consumer seam and could not test whether its `RBX`
matched the retained producer task.

The run used clean source commit
`09b7524cc34c15c227800af983db64452c2ff222`, CK3 `1.19.0.6`, executable
SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
and PID 64304 from `2026-09-02T17:40:24.090971Z` through
`2026-09-02T17:41:49.607630Z`. No second live was started.

## Observer evidence

Both private hooks installed without failure. The producer D2 and D7 counts
were both 414, with zero read failure or histogram overflow. The exact
`0x88B480` callback was selected once and published state 2:

- task/callback: `0x18E97E09D50`;
- owner: `0x18E8F7441B8`;
- callback vptr: `0x7FF7E33ADBF0`;
- slot2 target: `0x7FF7DFBAB480`;
- producer thread: 67196;
- producer QPC: 570883681074.

The completion correlation object reported `consumer_raw_hit_count=0`,
`consumer_match_count=0`, and `consumer_read_failure_count=0`. Its last
state/reference/callback/thread/QPC fields correctly remained zero. Because
the raw counter is incremented inline before the complete-state classifier,
this is evidence that `0x3B9DEA7` itself was not executed during this bounded
run. It does not prove that the selected task was absent from the consumer.

## Evidence and cleanup

- runner report SHA-256:
  `DC42BAA030E150F2D14A369C4485CA27D030D2932CDD9B2A04828602D2EE6B21`;
- typed correlation postprocess SHA-256:
  `529F41DF9265966A6AF60EE722B95792FAEFB71C90E69C6842B79519D7A8703F`;
- cleanup SHA-256:
  `085E5E2915EBE412928F0ABB895C5D480BA702C579F59ECC70A6EEF50FC89728`;
- terminal evidence index SHA-256:
  `0476483AAAA30BF22B7C5579DEAEE40F071DC3DD3E7F6E02ACBB9C3B1225A6AD`;
- frozen source ZIP SHA-256:
  `2CD15C166CFC74FF70AFBFB6E85F4E6A14A811BC223E385146E8137600C8B4A3`;
- observer manifest SHA-256:
  `18A4767C661D603B635330F354C7398E9AC05405AC5752C03DC3F3060EF8325C`.

Cleanup, clean-source immutability, runtime projection immutability, and
external dependency immutability were GREEN. The legal handler returned
GREEN with no modal and zero clicks; no commerce action occurred. CK3 and the
injector were absent after cleanup.

## Next distinct seam

The next bounded observation should keep the same dynamically retained D7
task identity but move outward to the already frozen completion-wrapper entry
at `0x3B9E030`, recording whether that wrapper runs after the producer publish
and which branch/call edge leads toward `0x3B9DEA7`. This distinguishes
"wrapper was not scheduled" from "wrapper ran but selected another branch"
without repeating the `0x3B9DEA7`-only live, scanning generic loader callers,
or changing public ABI/readiness.
