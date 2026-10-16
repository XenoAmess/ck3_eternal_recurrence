# Publish observed date and pause transitions sooner

The Native worker previously waited for its 250 ms maintenance heartbeat to
publish a new semantic frame, even when the existing owner-thread observer had
already recorded a date or pause transition. A complete one-day clock operation
could therefore finish before the worker published any intermediate running
frame.

The .4 connection loop now checks the existing owner diagnostics before its
heartbeat work. When a valid observed date/pause differs from the previous
publication, it attempts the existing `PublishSnapshot` path immediately.
The full current-owner read, identity and source-frame checks still belong to
`PublishSnapshot` and `WorkerAdapter`; the diagnostics do not become a partial
semantic snapshot. This does not submit another native query, change clock
speed, resume/pause the game or synthesize a date.

`DatePausePublicationDueV1` requires a previous frame, valid positive dates,
successful owner observation, verified pump epochs, matching owner/current
thread, initialized main-thread TLS and nonzero TLS/Jomini/game-state pointers.
Stopped, unobserved or incomplete stamps do not request fast publication.
Unchanged date/pause also does not request it. The existing **250 ms maintenance
heartbeat and 10 ms worker wait are unchanged**. Scheduling and downstream read
costs remain, so this is not a 10 ms end-to-end guarantee.

## Validation and provenance

Machine `xenoamess-full-tower-eb9d2c1186`, 2026-10-16 UTC:

- Native19 compiled one translation unit with actual MSVC and linked the frozen
  production closure. DLL SHA-256:
  `87ac9b1c1f73629d7ffaef0b12d97523061e96d0e04685871e7253819044cf4a`.
  The original Native18-02 inputs were unchanged. Existing five exports and
  declaration policy, private Army, camera, sentinel and UI contracts were
  checked in the produced artifact.
- The actual native fixture passed 18 checks, covering changed day, both pause
  directions, a day ending paused before a running publication, unchanged state
  and each incomplete owner-stamp condition. External receipt:
  `continuation42-cold-prep/p23-fast-state-native19-01/FOCUSED-FIXTURE-RESULT.json`,
  SHA-256 `c89b733ddd2be5633055a8700878425fca62b9e591dde8434cf77ab23333905a5`.
- Public integration moves only the include and connection-loop insertion from
  `native19-bridge.patch`, SHA-256
  `4aeea6f2b38f39789624da0ce6e2d6446af0dab018ba1630d1b1300767e40908`.
  It preserves other public bridge code. The new header is byte-identical to the
  frozen candidate, SHA-256
  `f7b18d97e41fc1261e364a3fdac35fd1c8478017ed7ad8be21440160c0ac5581`.
- The same 18-check function is integrated into the existing
  `xar_ck3_main_thread_query_mailbox_v1_test` target. Its body matches the native
  fixture exactly; only its linkage/name changes. `--date-pause-only` runs this
  focused check without a new executable target. Public migration receipt:
  `continuation42-cold-prep/p23-fast-state-native19-01/PUBLIC-SOURCE-MIGRATION.json`.
- The extracted public test body and public header also compiled with actual
  MSVC `/W4 /WX` and returned 18 through a new DLL fixture. Receipt:
  `continuation42-cold-prep/p23-fast-state-native19-01/PUBLIC-TRANSPLANT-FIXTURE-RESULT.json`,
  SHA-256 `12fde2131f60614106fc8d333ffefd698985129c287dfda4c7e94bada8681811`.
  This verifies the migrated function/header; it does not claim execution of
  the complete public mailbox test executable or its command-line wiring.

The build and fixture made no Game, SDK, OBS or desktop calls. At source
delivery, the candidate had not been loaded. These results do not establish
real-game clock latency, 0.5 seconds/day or an uninterrupted 30-year run; those
require separate live receipts.
