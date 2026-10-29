package org.xar.ck3.control.build;

import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Mechanical qualification after complete integrated Own; never SDK or Game authority. */
public final class ToolsInputPostqualification {
    private ToolsInputPostqualification() { }
    public static final String POLICY = CiBootstrap.TOOLS_POSTQUALIFICATION_POLICY;
    public static final String INPUT_SCHEMA = "xar.control-ci-tools-postqualification-input/v1";
    public static final String ACTUAL_SCHEMA = "xar.control-ci-tools-postqualification-actual/v1";
    public static final String OWN_SCHEMA = "xar.integrated-tools-accepted-readback/v5";
    public static final String OWN_SCOPE = "INTEGRATED_TOOLS_RUNTIME_ONLY";
    public static final String OWN_CLASS = "org.xar.ck3.control.build.ToolsIntegratedAcceptedReadback24c";
    public static final long OWN_SOURCE_BYTES = 38867L;
    public static final String OWN_SOURCE_SHA256 = "d0551d847cfacb31b1181ea50b384950bb693497967f6d3f57429e33f5311cf3";
    public static final String TEST_CLASS = "org.xar.ck3.control.build.SharedOwnedCommandInputCountActualRegression";
    public static final String MARKER = "PASS_SHARED_OWNED_INPUTS_2048_ACTUAL_JUNIT_2";
    public enum Scope { MECHANICAL_LARGE_INPUTS_AFTER_COMPLETE_INTEGRATED_OWN_ONLY }

    /** Original seven-reference Own inputs; no substitute positive fixtures. */
    public record FullOwnInputs(FileRef producerSourceRef, FileRef materializedMapRef,
            FileRef historicalCompletedReceiptRef, FileRef genuineHistoricalCaptureRef,
            FileRef originalQuotaLeaseRef, FileRef originalQuotaRejectionRef,
            FileRef originalQuotaSourceMapRef, FileRef boundedInputManifestRef) {
        public FullOwnInputs {
            for (var ref : List.of(producerSourceRef, materializedMapRef, historicalCompletedReceiptRef,
                    genuineHistoricalCaptureRef, originalQuotaLeaseRef, originalQuotaRejectionRef,
                    originalQuotaSourceMapRef, boundedInputManifestRef)) positive(ref);
            if (producerSourceRef.bytes() != OWN_SOURCE_BYTES || !producerSourceRef.sha256().equals(OWN_SOURCE_SHA256)
                    || !producerSourceRef.path().endsWith("ToolsIntegratedAcceptedReadback24c.java"))
                throw new IllegalArgumentException("Only the exact complete selected Own producer is qualified");
        }
        public List<FileRef> arguments(FileRef tools) {
            return List.of(tools, materializedMapRef, historicalCompletedReceiptRef, genuineHistoricalCaptureRef,
                    originalQuotaLeaseRef, originalQuotaRejectionRef, originalQuotaSourceMapRef);
        }
    }
    public record Input(String schema, String machineId, String observedAtUtc, String reviewAtUtc,
            FileRef resourcePlanRef, FileRef capacityReleaseRef, FileRef toolsReceiptRef,
            FullOwnInputs fullOwn, List<FileRef> junitRuntime, List<FileRef> largeInputs) {
        public Input {
            if (!INPUT_SCHEMA.equals(schema) || machineId == null || machineId.isBlank())
                throw new IllegalArgumentException("Exact current mechanical postqualification input required");
            window(observedAtUtc, reviewAtUtc);
            positive(resourcePlanRef); positive(capacityReleaseRef); positive(toolsReceiptRef); Objects.requireNonNull(fullOwn);
            junitRuntime = List.copyOf(junitRuntime); largeInputs = List.copyOf(largeInputs);
            if (junitRuntime.isEmpty() || junitRuntime.size() > 32 || largeInputs.size() <= 512 || largeInputs.size() > 2048)
                throw new IllegalArgumentException("Original JUnit closure and513..2048 individual original inputs required");
            long bytes = 0; var jars = new HashSet<String>();
            for (var jar : junitRuntime) {
                positive(jar); bytes = Math.addExact(bytes, jar.bytes());
                if (!jar.path().endsWith(".jar") || jar.bytes() > (16L << 20) || !jars.add(jar.path()))
                    throw new IllegalArgumentException("Unique original JUnit JARs required");
            }
            if (bytes > (64L << 20)) throw new IllegalArgumentException("Bounded original JUnit runtime required");
            var paths = new HashSet<String>();
            for (var ref : largeInputs) {
                Objects.requireNonNull(ref);
                if (!paths.add(ref.path())) throw new IllegalArgumentException("Every original input must have its own unique path");
            }
        }
    }
    public record Execution(FileRef compileTerminal, FileRef javaTerminal, FileRef nativeEvidence,
            List<FileRef> carrier, List<String> physicalArguments, List<String> startupOptions,
            FileRef stdout, FileRef stderr, List<SharedSourceFiles.Witness> inputs) {
        public Execution {
            positive(compileTerminal); positive(javaTerminal); positive(nativeEvidence); positive(stdout); Objects.requireNonNull(stderr);
            carrier = List.copyOf(carrier); physicalArguments = List.copyOf(physicalArguments);
            startupOptions = List.copyOf(startupOptions); inputs = List.copyOf(inputs);
            if (carrier.size() != 1 || inputs.isEmpty() || inputs.size() > 256 || physicalArguments.isEmpty())
                throw new IllegalArgumentException("Exact original compiler, qualified carrier and native child required");
        }
    }
    public record Actual(String schema, Scope scope, String machineId, String startedAtUtc, String observedAtUtc,
            String reviewAtUtc, FileRef inputRef, SharedSourceFiles.Witness inputWitness, FileRef toolsReceiptRef, FileRef fullOwnActualRef,
            Execution fullOwnExecution, FileRef fullOwnInputGuardRef, FileRef bindingRef, FileRef specRef,
            Execution junitExecution, FileRef commandTerminalRef, int expectedTests) {
        public Actual {
            if (!ACTUAL_SCHEMA.equals(schema) || scope != Scope.MECHANICAL_LARGE_INPUTS_AFTER_COMPLETE_INTEGRATED_OWN_ONLY
                    || machineId == null || machineId.isBlank() || expectedTests != 2)
                throw new IllegalArgumentException("Strict mechanical-only two-JUnit proof required");
            window(startedAtUtc, reviewAtUtc);
            if (Instant.parse(observedAtUtc).isBefore(Instant.parse(startedAtUtc))
                    || Instant.parse(observedAtUtc).isAfter(Instant.parse(reviewAtUtc)))
                throw new IllegalArgumentException("Actual postqualification must complete in its original window");
            for (var ref : List.of(inputRef, toolsReceiptRef, fullOwnActualRef, fullOwnInputGuardRef, bindingRef, specRef, commandTerminalRef)) positive(ref);
            Objects.requireNonNull(fullOwnExecution); Objects.requireNonNull(junitExecution);
            if(inputWitness==null||!inputWitness.source().equals(inputRef))throw new IllegalArgumentException("Original typed input native identity required");
        }
    }
    public static List<CiBootstrap.JavaUtf8Invocation.Property> properties(FileRef binding, FileRef spec) {
        positive(binding); positive(spec);
        return List.of(new CiBootstrap.JavaUtf8Invocation.Property("xar.sharedOwned.largeInputs.binding.path", binding.path()),
                new CiBootstrap.JavaUtf8Invocation.Property("xar.sharedOwned.largeInputs.binding.bytes", Long.toString(binding.bytes())),
                new CiBootstrap.JavaUtf8Invocation.Property("xar.sharedOwned.largeInputs.binding.sha256", binding.sha256()),
                new CiBootstrap.JavaUtf8Invocation.Property("xar.sharedOwned.largeInputs.spec.path", spec.path()),
                new CiBootstrap.JavaUtf8Invocation.Property("xar.sharedOwned.largeInputs.spec.bytes", Long.toString(spec.bytes())),
                new CiBootstrap.JavaUtf8Invocation.Property("xar.sharedOwned.largeInputs.spec.sha256", spec.sha256()));
    }
    private static void positive(FileRef value) {
        if (value == null || value.bytes() < 1) throw new IllegalArgumentException("Actual positive original FileRef required");
    }
    private static void window(String observed, String review) {
        var start=Instant.parse(observed);var end=Instant.parse(review);
        if (!start.toString().equals(observed)||!end.toString().equals(review)||!start.isBefore(end))
            throw new IllegalArgumentException("Canonical finite original UTC window required");
    }
}
