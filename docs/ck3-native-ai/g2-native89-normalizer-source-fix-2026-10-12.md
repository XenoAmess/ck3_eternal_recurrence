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
execution receipt. The third invocation is pending at this record's creation.

The original source/build review deadline remains 2026-10-12 16:47:28.264315 UTC.
The current saved campaign and its full13 input keep their separate limited
protection. Copies and source fixes do not extend either deadline; reclamation
continues under the common storage policy.
