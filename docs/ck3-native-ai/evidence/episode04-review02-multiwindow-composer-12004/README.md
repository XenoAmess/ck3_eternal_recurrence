# Multiwindow composer: historical planning evidence

machine_id: `desktop-3fevhd2-1c74096080`
Historical PASS observation: 2026-10-17T09:52:15.293652+00:00. Packaging/correction receipt: 2026-10-17T09:52:53.451401+00:00. Intake time and exact source mapping are in [source-index.json](source-index.json).

[history-verify-source.py](history-verify-source.py) is the exact, renamed original `verify_multiwindow_a01.py`. It is historical process source, **not a generic validator for current main**. It hardcodes the original C:/D: input roots, project config and output receipt. It also requires the old main composer baseline 6822 B / SHA-256 `a88f7601623d6a10acb36165d198dd52e8d1875938ee1dad2db00ed3c2ba1646`. Main now contains the adopted multiwindow implementation, so rerunning this script would not recreate its original control. Do not run it as a repository test.

The first check failed because it wrongly required explicit `-ss` for a zero-start window. The engine correctly omits redundant zero seek. [CHECK-ATTEMPT01.actual.json](CHECK-ATTEMPT01.actual.json) preserves that error; the corrected [PASS](BEHAVIOR-CHECK.actual-a01.json) validates two immutable engine plans with independent seeks and the existing geometry. The composer implementation was unchanged between those checks. No media bodies, render, probe, SDK or new run were used; intake did not repeat the check.

[ROUGH-INPUTS.candidate-a01.json](ROUGH-INPUTS.candidate-a01.json) remains a machine-local authored candidate, not frozen production input. Its external paths need explicit mapping and preserved artifact qualification on another machine. Candidate4 rough/20 cards/45 pending does not rewrite canonical3/20/46. C05-10 is post-merge context, not filmed rendezvous arrival.

[AUTHOR-NOTES.original.md](AUTHOR-NOTES.original.md), the original delivery and release receipt remain byte-exact. Release0.3.0/environment facts apply only to the source machine at the recorded time. No current cross-machine environment, render-ready, continuous-clean, event-PTS, human1x/signoff or new research/business/dynamic credit is granted.
