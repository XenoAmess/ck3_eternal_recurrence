# Settled same-Game software fixture

This derived fixture keeps the event1–35/38/42 entry, READ, ACTION, RETAIN, SETTLE and batch topology of dirty same-Game recovery. It uses the neutral owner settled-recovery-fixture and needs no original state directory, game installation, process, network or local model.

The gzip template contains42 software event edges and81 small archive inputs needed by the historical reader, reducer and capability replay. The loader selects frontier35,38 or42. Unrelated domain bodies and ignored import details are removed; unused source/decoder/deployment references become bounded metadata. This is transformed software DATA, without physical Native custody or production admission authority.

PortableSettledFixture expands under JUnit @TempDir, rebuilding byte counts and SHA256 references. Configuration and session paths become absolute temporary paths preserving their relationships. Production Driver/action encoders reconstruct their representations, and Native-framed tokens retain their length prefix. Missing or malformed resources fail without skipping or fallback. The decoded875326-byte template stays below the existing1MiB resource bound; gzip is94608 bytes.

SettledSameGameRecoveryRegressionTest has11 methods covering the production reader, reducer, Controller, action validator and archive codecs: dirty/unsaved/batch preservation, READY reentry, action idempotence, native/date/public monotonicity, real READ topology, JSON rejection and private fresh/canonical-action bridges.

SettledCapabilityRecoveryRegressionTest adds3 methods for original capability state/capsule typed replay, unchanged speed3/flagsfalse configuration, content-tampering rejection and deferred-batch38 next2/dirty/unsaved preservation without SAVE credit.

SettledOpenBatchRecoveryRegressionTest adds2 methods. Actual42 is RUNNING with BATCH_STARTED3 and no subsequent terminal/action/SAVE. The explicit software recovery commits43 without rewriting the prior boundary or cycle. Controller consumed ids0..3 and next4 are restored, BATCH_STARTED4 commits44, and a new Journal's READY adoption makes no second recovery. Historical batch-id allocation remains Controller-owned; no extra reducer guard is claimed.

Fresh SEM is an explicit verifier test double. Hypothetical APPLIED and batch transitions are software DATA validated by real production reducers/codecs. They do not represent Native requests, real actions, dates, SAVE, physical Pins or freshness proofs. The private bridge remains scoped to its cycle digest.

The3 plain JUnit classes use existing local-service dependencies, resources and default Surefire discovery. No Quarkus service or Game starts. From java/ck3-control, a focused Maven command is:

```text
mvn -T2 -pl local-service -am -Dtest=SettledSameGameRecoveryRegressionTest,SettledCapabilityRecoveryRegressionTest,SettledOpenBatchRecoveryRegressionTest -Dsurefire.failIfNoSpecifiedTests=false test
```

Use existing approved build/temporary roots. ReactorTestClosure requires reports for selected default *Test sources; no workflow/allowlist edit is needed. The D-only handoff records which groups were executed on which input version; it does not claim a combined16/16 Maven or CI execution.
