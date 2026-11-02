# Fixed-version source basis

These references use Quarkus tag **3.40.1.1**. No framework source or vendor JAR is patched by this witness.

- [RuntimeUpdatesProcessor](https://github.com/quarkusio/quarkus/blob/3.40.1.1/core/deployment/src/main/java/io/quarkus/deployment/dev/RuntimeUpdatesProcessor.java):503-543 instrumentation eligibility/comparison/JDK call/fallback;556-605 restart versus completed no-restart branch;640-654 configured/explicit override;1476-1483 toggle.
- [ClassComparisonUtil](https://github.com/quarkusio/quarkus/blob/3.40.1.1/core/deployment/src/main/java/io/quarkus/deployment/dev/ClassComparisonUtil.java):24-25 dereferences the old ClassInfo; further methods compare structure rather than method bytecode bodies.
- [ApplicationArchiveBuildStep](https://github.com/quarkusio/quarkus/blob/3.40.1.1/core/deployment/src/main/java/io/quarkus/deployment/index/ApplicationArchiveBuildStep.java):64-107 official artifact-index configuration;200-254 runtime artifact-key selection and directory indexing.
- [CombinedIndexBuildStep](https://github.com/quarkusio/quarkus/blob/3.40.1.1/core/deployment/src/main/java/io/quarkus/deployment/steps/CombinedIndexBuildStep.java):30-56 combines startup archive indexes and installs lastStartIndex.
- [IsolatedDevModeMain](https://github.com/quarkusio/quarkus/blob/3.40.1.1/core/deployment/src/main/java/io/quarkus/deployment/dev/IsolatedDevModeMain.java):76-98 first runner reads instrumentation config;192-227 ordinary runtime restart omits that setter.
- [ClassChangeAgent](https://github.com/quarkusio/quarkus/blob/3.40.1.1/core/class-change-agent/src/main/java/io/quarkus/changeagent/ClassChangeAgent.java):the actual held source has premain; a disk manifest or a JVM argument alone is not a successful redefine witness. The private completed-instrumentation log plus observed unchanged identities/new values provides the positive result.

The JDK21 Instrumentation contract used in source review preserves active-frame bytecodes and existing state during redefinition. This witness exercises later calls from an unchanged live worker frame, not in-place rewriting of an already active run method.

The generated probe and runner are owner-written. Of four genuine ordinary three-message model requests, three ended length and were discarded whole. The completed actual-index diagnostic supplied a partial direction matching independent source review; its newly-added-class description, source line numbers and unproved POM-property-forwarding suggestion were rejected. No model code or complete model approval is adopted.
