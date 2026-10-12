# Native89 whole-build normalization, 2026-10-12

Native89 actually compiled all 917 owners and captured their dependencies.
Its explicit archive continuation produced 597 ordered members; the following
link-only continuation succeeded after binding the installed resource-tool
directory. This remains build evidence, without Game or M7 credit.

The actual dependency-verification packet is 45,460,300 bytes. The normalizer's
old 32 MiB JSON bound could not admit it. Its JSON bound is now finite 64 MiB;
input and proof bounds remain 64 KiB, with an explicit artifact bound.

The first normalization invocation then exposed a separate source defect:
`deps()` saved its raw dependency JSON reference in `ref`, overwrote that local
for each header, and returned the last header reference. The whole-build join
correctly rejected it. The fix saves and returns the raw reference in `dr`;
the per-header checks, raw-reference hashes and strict dependency join remain.

The exact reviewed fixed source is 20,478 bytes, SHA-256
`b5a05d8f2082e364aa477c4f24289117955b37db7d5468e1b12e4e4c736e1a1b`.
Two reviewers reused the prior complete 389-line review and independently read
the bounded changes; Root also read them and checked exact byte differences.
No suite, fixture or verification import was run.

The first actual failure has exit 2 and preserves `deps o`. A subsequent actual
caller's 300-second wait expired, although its slower child later wrote the
whole-build proof. That second proof has no independently observed child exit
code and is not adopted for runtime. Root selected separate third input/proof/
execution paths and finite 900-second supervision, preserving all prior files.

Evidence remains external under `g2-native89-production01/closure03`:
`ROOT-WHOLE917-NORMALIZER-ACTUAL-STOP.json`,
`ROOT-WHOLE917-NORMALIZER-ACTUAL-STOP-02.json` and
`ROOT-WHOLE917-CLOSURE-PROOF-02.json`. A proof file alone is insufficient;
runtime adoption requires actual exit 0, proof readback and the independent
execution receipt. The third invocation was pending at this record's creation.

At 04:06:19 UTC, the third invocation actually exited 0 after 530.62 seconds.
Root read the complete proof and external execution receipt. The proof binds
all 917 fresh owners and dependency outputs, zero reused owners, 597 exact
ordered archive members and the actual link closure to SDK91
`50a1a5451227d1b30f42394dd02ddfbaea26a1ff`. The 17,807,360-byte DLL has SHA-256
`7d97c73e24a68db1cf6cc67b7cb684a551fd0130df5d5a13bf5e092ac0e2fc02`.

The independent proof is `ROOT-WHOLE917-CLOSURE-PROOF-03.json`, 10,475 bytes,
SHA-256 `e2077b1cbbc58b42ce09f2a0913c3670ad0c2aef3c651543e8de07872f94c00d`.
Its execution receipt is `ROOT-WHOLE917-NORMALIZER-EXECUTION-03.json`, 2,123
bytes, SHA-256 `b2d9b825714d3579d275dff4e92a15d882880ce592fde11a7031795089a38edd`.
The first failure and second timeout proof remain unchanged. No normalizer
process termination occurred in the unsuccessful timeout-cleanup attempts.

Root derived separate small loader metadata, preserving the exact three
original helper EXE rows and their original provenance, and adding the actual
new DLL row. No helper binary was rehashed or copied for this derivation.
An initial metadata summary used an absent `name` key after writing the three
metadata files; the corrected summary read and compared those files without
overwriting them. This compile closure does not grant Game, family or M7
qualification. R104 runtime adoption remains a separate actual operation.

The original source/build review deadline remains 2026-10-12 16:47:28.264315 UTC.
The current saved campaign and its full13 input keep their separate limited
protection. Copies and source fixes do not extend either deadline; reclamation
continues under the common storage policy.
