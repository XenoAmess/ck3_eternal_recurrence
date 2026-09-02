# Phase-two loader callback runtime vtable observation (2026-09-02)

One private, debugger-only exact-build run reached the previously frozen
callback instruction and produced the first paused runtime identity evidence.
It did not repeat the 300-second loader timeout, install a production detour,
or change the public bridge ABI.

## Preflight and exact build

- Parent source baseline: `09f21c8958d9f880d4993c69ce967abc88bdb175`.
  The coordinating mainline had subsequently advanced to `ea8164b`; this
  isolated branch does not claim to include that later promo pin.
- `open_kaishek`: `17caa288eb980aab0b652358e9e94a9901131619`;
  CLI JAR SHA-256
  `421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
- Offline preflight artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\open_kaishek-preflight-17caa288.json`,
  SHA-256
  `ED265EA237651B1DD4149792EE0427663D5BC932E4749B6F20A8600F377557D9`.
  Parser/IR/runtime were GREEN; the full-root validator retained the known
  schema-only RED (`232,973` diagnostics). `ck3_started=false`, and the
  preflight is not native/live evidence.
- CK3 `1.19.0.6` executable SHA-256:
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Paused observation

The private utility
`phase2_loader_callback_debug_capture.cpp` verified the exact executable hash
and `FF 50 10` bytes, launched CK3 with an isolated `-userdir` under
`DEBUG_ONLY_THIS_PROCESS`, and installed a one-shot breakpoint at RVA
`0x3B9AB90`. The breakpoint was hit after 18.101 seconds. While all debuggee
threads were stopped:

- OS thread ID: `48304`;
- node: `0x21A39F97B00`;
- callback receiver `RCX`: `0x21A39F97B50`;
- `[node+0x88]`: `0x21A39F97B50` (matches `RCX`);
- runtime vptr RVA: `0x408A450`;
- runtime vtable slot-2 target RVA: `0x947BD0`.

The retained capture is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\callback-debug-capture.json`,
SHA-256
`F78961E40F93C0D91E71EACFEFB65A6F5D0F6CCA9276B42F570D05F97834B816`.
The exact capture binary SHA-256 is
`5903F6D34D561908E951A5C1FE530DC653C9CCCED0C7017BBF0066479C390ADB`.
The original `0xFF` byte was restored before termination.

This observation confirms the existing `RCX=[node+0x88]` call shape and closes
one missing runtime vtable identity entry. It also disproves the assumption
that this invocation used either static construction candidate vtable RVA
`0x4558700`/`0x4558770` or their shared slot target RVA `0x3B9BA70`.
The observed values are retained without assigning an RTTI type, source file,
or business meaning.

## Cleanup and boundary

The first capture utility revision waited on the process handle before
draining `EXIT_PROCESS_DEBUG_EVENT`; its primary artifact therefore
conservatively says `cleanup-unproven`. Closing its kill-on-close Job removed
the process. A separate post-exit inventory at
`2026-09-02T08:41:33.2934971Z` found captured PID `46232` absent and zero
`ck3.exe` processes. That artifact is
`callback-debug-capture-cleanup.json`, SHA-256
`35087FA3CBD071AC2DF65666B5EF79BE6E951AEE0DC5BA36A725998A7562112B`.
The utility now drains the exit debug event before checking the handle; this
cleanup-only correction was compiled and self-tested but was not used to
repeat the runtime capture.

Phase two remains **native-readiness RED + not-live**. This note's immediate
RTTI/return-lifetime next entry was subsequently closed by
[the runtime-owner observation](phase2-loader-callback-runtime-owner-2026-09-02.md).
Concrete callback source attribution, later stalled-node identity, seed
readiness, and formal paused acceptance remain open. Do not repeat the
existing loader timeout or widen the public bridge.
