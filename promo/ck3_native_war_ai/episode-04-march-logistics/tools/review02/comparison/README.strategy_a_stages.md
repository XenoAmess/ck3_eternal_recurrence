# A stages: finite Root relay source, not general campaign readiness

`strategy_a_stages.py` is the byte-identical phase adapter prepared for the
2026-10-16 Root operation. It preserves the historical upper deadline
`2026-10-16T07:45:01.597Z`; that deadline is neither a permanent public policy nor
a new runtime lease. This archived source is **PREPARED_NOT_LIVE**. After that
finite window it is not a ready executor for a new run: a newly authorized,
reviewed bounded operation must supply its own qualified binding/configuration.
No gameplay result or cross-machine deployment is conferred by this archive.

The reusable policy/knowledge lives separately in `strategy_a.py`,
`strategy_a_route_inputs.py` and the R10 comparison contract. They describe full
cohort/frame/arrival and current-vs-future supply semantics. This finite relay
source connects those consumers to Root's existing request mechanism; it is not
a new public MCP API, planner, game launcher, event policy or autonomous runner.

## Portable source layout

All source dependencies are now repository-relative. From this directory:

* phase entry: `strategy_a_stages.py`;
* existing consumers: `r10_compare.py`, `r10.schema.json`, `strategy_a.py`,
  `strategy_a_route_inputs.py` (pin their exact bytes in an external manifest);
* frozen relay source: `sources/locked_routes_root_1463.frozen.py`, SHA256
  `01b2370c9ce0da52b2d6cb75e6a5405e0889f05a4026328c08530a9aab15fbf6`;
* the frozen relay's `VERIFY_REL` points to the existing repository
  `promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/verify.py`.

The30KB source dependency is archived unchanged. Its original machine/Robert/
1463/asset-specific constructor is a historical implementation, not a promise
that it supports future machines. The A adapter overrides that constructor and
uses only the reviewed request/snapshot/claim/action/readback/process-time and
response-local complete-query methods. This change adds no new compatibility
claim and does not copy a machine launcher or request-helper tree.

`python -B strategy_a_stages.py --help` is offline. Tests are repository-relative
(`test_strategy_a_stages.py`) and import the archived relay without constructing
a live instance. The original five synthetic wiring checks are preserved, not
rerun by this packaging change. They are no new native/live qualification.

## Explicit finite invocation

Root passes `--relay-source` as this archive path, its SHA, `--consumer-root` as
this comparison directory, and an external `--consumer-manifest`. No C-drive
module or historical runtime is imported implicitly by the phase entry.

The remaining explicit inputs stay external: frozen PLAN/runtime JSON,
current-runtime loaded-features bound source, evidence root, allocated context,
reviewed new-run request helper plus SHA, loaded normal-save SHA, actual public
CUnit and native CArmy IDs, case/attempt, prior state and finite deadline.
`--repo` is the actual matching source checkout. Root's Steam/offline evidence,
process/create-time/DLL proof, SDK credentials, local request transport,
recording control and capacity admission are machine/run facts and stay outside
the repository. Each needs its own machine_id/time/evidence, not an inherited
historical path.

The phase order remains `baseline` (readonly), `Move-once`, `Move-post`,
`advance --days N` (1..30, original global T0+90 and stop on first arrival),
`post` (readonly; no automatic arrival continuation). Every phase is a separate
explicit invocation and unique attempt. Each output is under
`<new-assets>/r10-a-stages-a03/<case-id>/<attempt>/`; complete source files stay
referenced with exact bytes/SHA. An unknown Move/Arm/Resume retains its once
claim; a new attempt does not authorize action replay.

The clock stays speed5/date-only a-0, one actual tick, +24 and zero overshoot.
Fresh post-status snapshot avoids stale-public-revision reuse. Full cohort/DATA
is read from the response-local Driver reference, never summary/latest. Native
current aggregate usage remains current; target usage excludes future incoming
Army. Future terrain/loss/refill/maintenance/split-saving remain unknown.

The local1MiB preparation cap and old512MiB reservation are historical source
facts, not new live capacity approval. Root must qualify any new session's full
DATA/query/log peak separately. No source or binary algorithm changed here.

Packaging source machine_id: `desktop-3fevhd2-1c74096080`; exact UTC, source pins,
layout/apply checks and unchanged-program proof are in the external READY receipt.
