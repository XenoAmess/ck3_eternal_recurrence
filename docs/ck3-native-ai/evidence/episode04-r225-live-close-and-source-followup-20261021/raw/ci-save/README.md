The legacy unknown-Save test was rejected before its intended timeout injection: its fake client had no retained handle/PID and its snapshot contained only revision/date. The ordinary Save guard correctly withheld submission. This candidate changes only tools/test_r08_writer_save_gate.py.

Source baseline: Git 81ac4459a19451c8435d91f16f9d6ede7038a7ac, test blob dbdd83108cbc20fe7316580146c57fd7a9ff7a29, 3448 bytes / SHA256 4d766f76e72348ed95db6b67d09c1b78f3c7ff13d8e0b1b453a97637088e8156. Collector machine_id: desktop-3fevhd2-1c74096080. GitHub runner machine_id: unknown.

The candidate provides a synthetic retained-client handle/PID and a complete paused ordinary native campaign frame with player, diagnostics, pipe/generation, snapshot/native revision, and managed-run consistency fields. It creates no host, game process, profile, or Save file. Its state_dir is an explicitly unused synthetic string. Production writer/Save guards are unchanged. All original assertions are retained. Additional assertions require the intended TimeoutError, exactly one Save submission, zero/one independent-after request as appropriate, Save_result preservation only after a received response, and the original blocked normal-close behavior.

Official CI39520294147 job118962219139 step20 failed at test_r08_writer_save_gate.py:45 in both unknown-result subcases (0 Save calls rather than1). Step19 succeeded. CI-STEP20-FAILURE.actual-a01.json retains a bounded official-job HTTP206 excerpt. No full job log, log archive, artifact, or CI rerun was downloaded/executed.

Actual paired checks:
- BASELINE-a02: one method, two failing subcases, original PID20228/birth134370169860695234/wait1, reproducing the CI assertions.
- CANDIDATE-a02: the same method and two unknown-result subcases pass, original PID17048/birth134370169880844142/wait0.
- MYPY-a02: four explicit inputs (candidate, normal harness, source-check owner, unchanged ordinary Save helper), original PID34096/birth134370169901677447/wait0. Flags disallow untyped definitions, any generics and Any returns; imports of unchanged legacy modules are skipped. This is modified-scope typing, not repository-wide or full CI success.

Both focused checks use normal imports from frozen TOP/tools plus existing D modules; no production function is mocked. Actual sys.setprofile tracing records the executed repository functions. The writer, ordinary Save helper, r10 need guard and sampling normalizer files equal81ac Git bytes. D bridge/driver.py is imported but differs from81ac; no driver.py/native_driver.py function or real driver constructor executes in either scenario. This deliberately does not claim canonical equivalence for all imported dependencies. The first a01 harness overconstrained every import to81ac and rejected both variants before tests; its original waits/logs and static result remain unchanged.

Input before/after pins and real original Popen waits are retained in the receipts. No D/W edits, Git mutation, SDK/native/Game/UI/Steam action occurred. The test patch still needs independent review and separately admitted integration/CI. The current Game run is independent.

Root admission: ../ROOT-CI-SAVE-FIXTURE-SOURCE-AMENDMENT.actual-a01.json, source/check cap524288 bytes inside existing scene other/metadata caps, deadline2026-10-21T01:30:00Z.
