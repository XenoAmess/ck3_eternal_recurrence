# R390 Stage 11 RED, cleanup, and split P1 acceptance

Date: 2026-09-10 (Asia/Shanghai)

## Live result and preserved RED

- R390 was the only CK3 instance (`PID 190136`, connection generation `1`).
- B1 completed GREEN, but the later T0 continuation did not complete P1.
- At 20:46:55, the first Stage 11 Workforce entry evaluated five optional
  variables before portfolio initialization. The five reads produced 15 script
  errors (fetch, unset-scope, and invalid-comparison triplets):
  `zg361_we_portfolio_closed` at three sites,
  `zg361_we_portfolio_status`, and `zg361_we_portfolio_cycle`.
- The minimum generated-script fix is commit `a507d89ec1d236d0010ea2bf81d5ae35ea70676b`.
  It adds genuinely lazy `trigger_if(has_variable...) / trigger_else` guards.
  Static, dual-mode, release, and reproducible-build checks are GREEN. Because
  the change affects game scripts, it cannot be hot-applied to R390.
- The later vanilla `tgp_dynastic_cycle.0081` is not a new contract variant.
  Its irreversible chaos effect runs before its sole visible option, so the
  existing product overlay correctly marked the R390 scenario invalid and made
  no selection. This later invalidation does not erase the earlier product RED.

Immutable RED evidence:

- `_runtime/p2r390-t0-critical-continuation-live/r390-stage11-workforce-uninitialized-variable-product-red.json`
  SHA-256 `52BDB4228EFA463427EDA499E59C9EE88343A979FED59779336032E25E2D6FAC`
- R390 continuation state SHA-256
  `4EAEB19CC305796FE5D69A05623387A74C8B8D5E97FD7F69185A51FC47DA1289`
- R390 Stage 9 receipt SHA-256
  `1A26D75469752D01FF2F1AD137EE02AE1727BFC65167E6CC5CC2F83F06D5720B`

## Managed cleanup

The operator MCP accepted the idempotent `cleanup` control after the RED and
input checkpoint had been frozen. The canonical cleanup receipt is
`_runtime/p2r389-b1-final-survivor-live/09_phase2_native_session_cleanup.json`,
SHA-256 `E336CA9513A74073B7498BFB23E408953826FE923B9A209825DF08E0A46ECB04`.
All 29 checks are GREEN: the CK3 process tree and watchdog are gone, the owner
job exited with code 0, and the global `ck3.exe` inventory is empty. The cleanup
report still states `phase2_p1_result=PENDING`; B1/cleanup GREEN must not be
reported as P1 acceptance.

## Split acceptance plan

The narrowed P1 gate accepts independent, hash-bound live receipts for B1,
AF5, stages 9-11, cold restore, bounded log scanning, cleanup, and the exact
candidate L0. It does not require every receipt to share one campaign lineage.
Using separate real checkpoints therefore avoids repeatedly driving the known
R390 lineage into an unavoidable vanilla chaos transition.

1. Replay only the Stage 11 first-entry boundary from frozen R390
   `autosave_1.ck3`, SHA-256
   `93745B2FE52AD31D7878D22BD1AB7898D3D09AA97AFB2BEAC1C009FC17964527`.
   Stop at `zg361we.242`, scan the fresh log slice for zero occurrences of the
   old five-variable/15-error signature, and park before `.0081`. This receipt
   cannot serve as Stage 11 terminal or cold-restore evidence.
2. Verify AF5 independently from the exact-build `zg361pp.147` checkpoint,
   SHA-256
   `D4F625C84E900966E0B70CA8FD65CD33D63205B479A3CBC15BC0DF4B02B319F0`.
   The required route is source option 1, then `zg361comp.1` authored option 42
   / native index 41, followed by the native provider terminal postcondition.
3. Admit a different celestial lineage under CK3 1.19.0.6 and immediately
   re-save it through MCP before using it as evidence. The preferred candidate
   is the 1.18.3.1 save with SHA-256
   `8FDB1150F165638601A6EB0F54CC78069AFAE02BB340950D6651F759C47C5A42`.
   Admission must fail closed on migration, script, player, government, or
   product-state mismatch. If admitted, run the critical Stage 9, Stage 10, and
   Stage 11 terminal chain on that new exact-build checkpoint.
4. Start one further exclusive CK3 process from the terminal checkpoint and
   compare the B1, AF5, Central, and Workforce native readbacks before and after
   cold restore. Then run the bounded combined log scan and managed cleanup.

All new rounds use the current production projection (1,031 files, product-tree
SHA-256 `91129390431B851ED213D9551CED4D4AF8D34FC7B9143152045D5EE45FAE0195`)
and the fresh promotion-only bridge DLL (SHA-256
`F478B5AFFF054B4E8518BE8CC6CEAB3B1A7367103742F8E0C648D57D876D421B`).
CK3 starts remain exclusive and serialized; operator profiles and wrappers must
remain parameterized for other users and machines.

## Readiness boundary

- T0 P1: pending; Stage 11 fix is static-ready and still needs the live replay.
- T0 P2 final video: locked and untouched.
- T2 open_kaishek: no code change for the Stage 11 script fix or this split;
  no public MCP/API/schema/ABI changed.
