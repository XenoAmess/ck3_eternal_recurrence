package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Explicit synthetic file-bound fixtures; never starts a vendor, CMD, compiler, or Native stage. */
final class NativeVendorTimeoutTest {
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    @TempDir Path temporary;
    private record Fixture(Path cohort, Path first, Path second, Path firstStdout, ControlBuild.FileRef vendor,
            ObjectNode firstWire, ObjectNode cohortWire) { }

    @Test void twoTypedTerminalsAndRawAnalysisRoundTripWithoutGrantingConfigureAuthority() throws Exception {
        Fixture fixture = fixture();
        var value = NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor());
        assertEquals(NativeFixtureBuild.VendorTimeoutStatus.NATURAL_CASES_OBSERVED_NOT_CONFIGURE_QUALIFIED, value.status());
        assertEquals(VctipProbeFacts.Qualification.NONE, value.firstAnalysis().qualification());
        assertEquals(VctipProbeFacts.Qualification.NONE, value.secondAnalysis().qualification());
        var mapper = ControlBuild.strictMapper();
        assertEquals(value, mapper.readValue(mapper.writeValueAsBytes(value), NativeFixtureBuild.VendorTimeouts.class));
        var ref = value.vendorRef();
        var card = new NativeFixtureBuild.ResourceCard("xar.shared-native-stage-resource-card/v2", MACHINE,
                "2026-10-23T00:00:00Z", "2026-10-23T00:02:00Z", "/root/native_fixture09",
                NativeFixtureBuild.ResourceStatus.ADMITTED_SINGLE_STAGE, NativeFixtureBuild.Stage.VENDOR_TIMEOUTS,
                256L << 20, 4L << 20, 120, ref, ref, ref, ref, ref, ref, List.of(), List.of(temporary.toString()));
        ObjectNode lower = mapper.valueToTree(card); lower.put("memory_limit_bytes", 128L << 20);
        assertThrows(IOException.class, () -> mapper.treeToValue(lower, NativeFixtureBuild.ResourceCard.class));
        ObjectNode longer = mapper.valueToTree(card); longer.put("timeout_seconds", 121);
        assertThrows(IOException.class, () -> mapper.treeToValue(longer, NativeFixtureBuild.ResourceCard.class));
        assertEquals(256L << 20, NativeFixtureBuild.stageMemoryLimit(NativeFixtureBuild.Stage.VENDOR_TIMEOUTS));
        assertEquals(16L << 20, NativeFixtureBuild.stageScratchLimit(NativeFixtureBuild.Stage.VENDOR_TIMEOUTS));
    }

    @Test void expectedFilePinAndFixedProductionVendorCannotBeSubstituted() throws Exception {
        Fixture fixture = fixture();
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort()));
        var other = ControlBuild.FileRef.measure(marker("other-vendor-evidence.txt"));
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), other));
        Files.writeString(Path.of(fixture.vendor().path()), "changed synthetic file evidence");
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
    }

    @Test void helpWrongArgumentAndWrongStageCannotSubstituteForTheFirstIdleCase() throws Exception {
        Fixture fixture = fixture();
        for (String argument : List.of("-?", "-timeout:2")) {
            ObjectNode wire = fixture.firstWire().deepCopy();
            wire.putArray("command").add(fixture.firstWire().path("command").get(0).textValue()).add(argument);
            rewriteFirst(fixture, wire);
            assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
        }
        ObjectNode wrongStage = fixture.firstWire().deepCopy(); wrongStage.put("stage_id", "version-cl-help");
        rewriteFirst(fixture, wrongStage);
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
    }

    @Test void cleanupLiveJobLowMemoryEarlyExitAndMissingRawMarkerCannotBecomeObservedTimeout() throws Exception {
        Fixture fixture = fixture(); var mapper = ControlBuild.strictMapper();
        var identity = new WindowsJobProcess.ProcessIdentity(17, "1", fixture.vendor().path());
        for (var result : List.of(
                new WindowsJobProcess.CommandResult(identity, 0, 1.1, new WindowsJobProcess.Accounting(1024, 0, 256L << 20, 8704), "timeout_or_release_expired"),
                new WindowsJobProcess.CommandResult(identity, 0, 1.1, new WindowsJobProcess.Accounting(1024, 1, 256L << 20, 8704), null),
                new WindowsJobProcess.CommandResult(identity, 0, 1.1, new WindowsJobProcess.Accounting(1024, 0, 128L << 20, 8704), null),
                new WindowsJobProcess.CommandResult(identity, 0, 0.1, new WindowsJobProcess.Accounting(1024, 0, 256L << 20, 8704), null))) {
            ObjectNode wire = fixture.firstWire().deepCopy(); wire.set("result", mapper.valueToTree(result));
            var lifecycle = NativeLifecycleTerminal.assess(result); wire.set("lifecycle", mapper.valueToTree(lifecycle));
            if (!lifecycle.successful()) { wire.put("status", "RED"); wire.put("error", "opaque synthetic non-natural terminal"); }
            rewriteFirst(fixture, wire);
            assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
        }
        Files.writeString(fixture.firstStdout(), "opaque unit output without server timeout observation");
        ObjectNode missingMarker = fixture.firstWire().deepCopy();
        missingMarker.set("stdout_ref", mapper.valueToTree(ControlBuild.FileRef.measure(fixture.firstStdout())));
        rewriteFirst(fixture, missingMarker);
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
    }

    @Test void originalDeadlineSameEnvironmentDistinctProcessesAndBothOriginalReceiptsAreMandatory() throws Exception {
        Fixture fixture = fixture(); var mapper = ControlBuild.strictMapper();
        ObjectNode renewed = fixture.firstWire().deepCopy(); renewed.put("stage_deadline_at_utc", Instant.now().plusSeconds(120).toString());
        rewriteFirst(fixture, renewed);
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
        ObjectNode changedEnvironment = fixture.firstWire().deepCopy();
        Path other = marker("different-environment");
        changedEnvironment.set("environment_ref", mapper.valueToTree(ControlBuild.FileRef.measure(other)));
        rewriteFirst(fixture, changedEnvironment);
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
        ObjectNode sameProcess = fixture.firstWire().deepCopy();
        var identity = new WindowsJobProcess.ProcessIdentity(18, "2", fixture.vendor().path());
        sameProcess.set("owner_identity", mapper.valueToTree(identity));
        ((ObjectNode) sameProcess.path("result")).set("identity", mapper.valueToTree(identity));
        rewriteFirst(fixture, sameProcess);
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
        rewriteFirst(fixture, fixture.firstWire()); Files.delete(fixture.second());
        assertThrows(IOException.class, () -> NativeFixtureBuild.readVendorTimeouts(fixture.cohort(), fixture.vendor()));
    }

    private static void rewriteFirst(Fixture fixture, ObjectNode wire) throws IOException {
        var mapper = ControlBuild.strictMapper(); Files.write(fixture.first(), mapper.writeValueAsBytes(wire));
        ObjectNode cohort = fixture.cohortWire().deepCopy();
        cohort.set("first_actual_ref", mapper.valueToTree(ControlBuild.FileRef.measure(fixture.first())));
        Files.write(fixture.cohort(), mapper.writeValueAsBytes(cohort));
    }

    private Path marker(String name) throws IOException {
        Path path = temporary.resolve(name); Files.writeString(path, "opaque unit marker: " + name); return path;
    }

    private Fixture fixture() throws IOException {
        var mapper = ControlBuild.strictMapper();
        var vendor = ControlBuild.FileRef.measure(marker("vendor-evidence-marker.txt"));
        Path source = marker("source-marker"), runtime = marker("runtime-marker"), card = marker("resource-card-marker");
        Path tools = marker("tools-receipt-marker"), env = marker("environment-marker");
        Path manifest = temporary.resolve("source-manifest.json");
        Files.write(manifest, mapper.writeValueAsBytes(new NativeFixtureBuild.SourceManifest("xar.native-stage-source-manifest/v1", MACHINE,
                Instant.now().toString(), List.of(ControlBuild.FileRef.measure(source)), List.of(vendor), List.of(ControlBuild.FileRef.measure(runtime)))));
        String deadline = Instant.now().plusSeconds(60).toString();
        var first = actual(NativeFixtureBuild.ActualStage.VENDOR_TIMEOUT_ONE, VctipProbeFacts.ProbeCase.IDLE_ONE, 17, "1", 1.1,
                Instant.now().minusSeconds(1).toString(), deadline, vendor, manifest, card, tools, env);
        var second = actual(NativeFixtureBuild.ActualStage.VENDOR_TIMEOUT_TWO, VctipProbeFacts.ProbeCase.IDLE_TWO, 18, "2", 2.1,
                Instant.now().toString(), deadline, vendor, manifest, card, tools, env);
        Path firstPath = temporary.resolve("synthetic-first.json"), secondPath = temporary.resolve("synthetic-second.json");
        Files.write(firstPath, mapper.writeValueAsBytes(first)); Files.write(secondPath, mapper.writeValueAsBytes(second));
        var value = new NativeFixtureBuild.VendorTimeouts("xar.native-vendor-timeouts/v1", MACHINE, Instant.now().toString(),
                NativeFixtureBuild.VendorTimeoutStatus.NATURAL_CASES_OBSERVED_NOT_CONFIGURE_QUALIFIED, deadline, vendor,
                first.sourceManifestRef(), first.toolsReceiptRef(), first.environmentRef(), ControlBuild.FileRef.measure(firstPath),
                analysis(first, VctipProbeFacts.ProbeCase.IDLE_ONE, vendor), ControlBuild.FileRef.measure(secondPath), analysis(second, VctipProbeFacts.ProbeCase.IDLE_TWO, vendor));
        Path cohort = temporary.resolve("synthetic-vendor-observations.json"); Files.write(cohort, mapper.writeValueAsBytes(value));
        return new Fixture(cohort, firstPath, secondPath, Path.of(first.stdoutRef().path()), vendor, mapper.valueToTree(first), mapper.valueToTree(value));
    }

    private NativeFixtureBuild.Actual actual(NativeFixtureBuild.ActualStage stage, VctipProbeFacts.ProbeCase probe,
            long pid, String birth, double elapsed, String observed, String deadline, ControlBuild.FileRef vendor,
            Path manifest, Path card, Path tools, Path env) throws IOException {
        Path stdout = temporary.resolve(stage.wireId() + ".stdout"), stderr = marker(stage.wireId() + ".stderr");
        int seconds = probe == VctipProbeFacts.ProbeCase.IDLE_ONE ? 1 : 2;
        Files.writeString(stdout, "Telemetry service timeout: " + seconds + "s\nStarting telemetry reporting service...", StandardCharsets.US_ASCII);
        var identity = new WindowsJobProcess.ProcessIdentity(pid, birth, vendor.path());
        var result = new WindowsJobProcess.CommandResult(identity, 0, elapsed, new WindowsJobProcess.Accounting(1024, 0, 256L << 20, 8704), null);
        return new NativeFixtureBuild.Actual("xar.shared-native-stage-actual/v2", MACHINE, observed, NativeFixtureBuild.ActualStatus.PASS,
                stage.wireId(), deadline, List.of(vendor.path(), VctipProbeFacts.arguments(probe).getFirst()), temporary.toString(),
                ControlBuild.FileRef.measure(env), ControlBuild.FileRef.measure(card), ControlBuild.FileRef.measure(tools),
                ControlBuild.FileRef.measure(manifest), null, List.of(vendor), List.of(), identity, result, NativeLifecycleTerminal.assess(result),
                true, ControlBuild.FileRef.measure(stdout), ControlBuild.FileRef.measure(stderr), List.of(), null);
    }

    private static VctipProbeFacts.Analysis analysis(NativeFixtureBuild.Actual actual, VctipProbeFacts.ProbeCase probe,
            ControlBuild.FileRef vendor) throws IOException {
        return VctipProbeFacts.analyze(probe, actual.result(), Files.readAllBytes(Path.of(actual.stdoutRef().path())),
                Files.readAllBytes(Path.of(actual.stderrRef().path())), vendor);
    }
}
