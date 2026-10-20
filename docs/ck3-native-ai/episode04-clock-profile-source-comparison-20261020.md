# Clock source-comparison anchors after wait-progress instrumentation

machine_id: `desktop-3fevhd2-1c74096080`; source review and focused verification: 2026-10-20 15:23Z. Sources and original Popen waits are preserved in [the evidence directory](evidence/episode04-clock-profile-hook-anchors-20261020/README.md).

The clock behavior-comparison fixture used three contiguous text blocks to remove profiling hooks. Independent wait-progress instrumentation inserted between those statements, so current c1b03 CI failed at the unique-anchor check before comparing behavior. The historical c1b03 and4b9 CI failures remain failures.

The fixture now strips only four unique clock-profile hooks: import, start, finish and snapshot observation. Adjacent wait-progress code remains present on both sides. Every original assertion, extracted implementation and success/exception/action/CPU/phase comparison remains unchanged. The only product-tree change is this existing test file; runtime and native sources are unchanged.

The two existing comparison methods each passed once against exact c1b03 and frozen bc638 source bytes: four focused executions, both original child Popen waits0. Driver source blobs stayed in memory. This publication reuses those source-pinned results and does not rerun the222-test matrix. It does not claim whole-CI, live-clock, R08 or game qualification. New exact-head official workflow results are recorded separately by the publisher; no prior RED is rewritten as GREEN.
