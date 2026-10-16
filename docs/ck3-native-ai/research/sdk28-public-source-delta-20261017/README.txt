SDK28 Rev2 actual frozen source vs public source, 2026-10-17

Actual binding:
  ROOT-ACTUAL-DRIVER-MODE-P28.json SHA 5a4fee5b4069f09a061b196a260f31988c1abe9ae7ba0632b3a054efa2a4a4ac
  ROOT-FINAL-SDK-FREEZE-P28.json SHA 6da46c57f3844522fa7cec516098f75b7987c8f7ac4bc2845311e3078c405587
  source_root continuation42-cold-prep/sdk-p28-candidate/src
  SOURCE-MANIFEST-REV2 SHA 33f1fd1b1d5fb6b699ec7db4c2c05b791ff1e954f6449c8a9d40ec28574f4fc7
  Public commit 79055bb2fc2559f4fe270ec3971591c78b59e0c8; source clean at capture.
  SDK29, live Driver, SAVE, video, external queue/feeder and Native DLL source are outside this packet.

1317 actual frozen leaves have individually verified raw SHA/size. Joint inventory:
  1261 raw equal; 5 newline only; 45 code differences;
  6 actual-only source leaves; 41 public-only source leaves.
METADATA.json contains all 1358 paths, normalized/raw hashes, original EOL runs,
public sparse-checkout/Git-blob mapping, three-way ancestry and source classification.
The 16 Workshop package leaves were compared to committed public source, not
misclassified as missing merely because the W worktree uses sparse checkout.

W-TO-ACTUAL-SDK28-NORMALIZED.patch contains complete narrow text diffs and creates
all six missing code leaves. recipes/ holds 97 hash-guarded lossless edit records,
including newline-only changes. Together with the pinned public Git commit they
reconstruct all 1317 actual source leaves byte for byte, including BOM, mixed EOL,
EOF and unchanged binary evidence blobs. No complete SDK or binary export is copied.

Portable verification from any repository containing the public commit:
  python -B -X utf8 <packet>/source_delta_recipe.py verify --git-only --public-root <repo> --public-commit 79055bb2fc2559f4fe270ec3971591c78b59e0c8
This reads Git objects and packet recipes only, reconstructs in memory, and writes
neither the repository nor an SDK. It does not need the old D paths or retained
actual SDK tree. Default working-tree verify checks current normalized source;
git-only defaults to the recorded public commit. It never fetches automatically.
The producer's prepare command is for the original external audit location only.

Verification: all1317 from Git blobs PASS; all97 raw recipes PASS; wrong-base
hash refusal PASS; git apply --numstat parsed all92 substantive text diffs.

This is a reconstruction research recipe, not a production rollback. Relative to
runtime baseline 00a70009: 67 raw differences reflect later public advances,
13 actual overlays, 12 divergent changes, and 5 newline changes. Applying the
whole patch to master would discard later public work. Review/port a specific
runtime change separately. Source inclusion/import reachability never establishes
live qualification, gameplay success, G2 completion, 0.5s/day or stable30years.
