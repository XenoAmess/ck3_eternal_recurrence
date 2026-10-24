package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Executes the retained real failure data through the current shared terminal consumer. */
public final class NativeLifecycleRegressionTest {
    private static final Path J = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1");
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final ControlBuild.FileRef CONFIGURE_RED = new ControlBuild.FileRef(
            J.resolve("scratch/native-prisoners-combat01/configure-drain05.actual.json").toString(), 5851,
            "3ce0351fe3756731798a3be5d846ab4b2869c2523df3f0821ebbc90a21537b9c");
    private static final ControlBuild.FileRef HELP = new ControlBuild.FileRef(
            J.resolve("build/resume56-20261023/native-vendor16/native_fixture09/help05/terminal.json").toString(), 6941,
            "ef2863c72d90d3b83acdeb5a52889fda4d4b08567fe6e5e7c4549eaf35ddc69d");
    private static final ControlBuild.FileRef REJECTED_ONE = new ControlBuild.FileRef(
            J.resolve("build/resume56-20261023/native-vendor16/native_fixture09/idle-one07/terminal.json").toString(), 5760,
            "a3cf511dbb84084dcee8d6deb797d94f0076d3392a4c29da506143db150b3340");

    @Test public void actualConfigureRootZeroAndCleanupJobZeroRemainsRed() throws IOException {
        JsonNode raw = read(CONFIGURE_RED);
        assertEquals(MACHINE, raw.path("machine_id").textValue());
        assertEquals("RED", raw.path("status").textValue());
        var result = JSON.treeToValue(raw.get("result"), WindowsJobProcess.CommandResult.class);
        var assessment = NativeLifecycleTerminal.assess(result);
        assertEquals(0, result.exitCode());
        assertEquals(0, result.accounting().activeProcesses());
        assertTrue(result.elapsedSeconds() >= 180);
        assertTrue(assessment.rootSucceeded());
        assertTrue(assessment.jobSettled());
        assertFalse(assessment.successful());
        assertEquals(NativeLifecycleTerminal.Settlement.CLEANUP_SETTLED, assessment.settlement());
        assertEquals("timeout_or_release_expired", assessment.stopReason());
        assertEquals(assessment, JSON.readValue(JSON.writeValueAsBytes(assessment), NativeLifecycleTerminal.Assessment.class));
    }

    @Test public void originalHelpExitOneIsOnlySyntheticUsageObservation() throws IOException {
        JsonNode raw = read(HELP);
        assertEquals("RED", raw.path("status").textValue());
        var result = JSON.treeToValue(raw.get("child"), WindowsJobProcess.CommandResult.class);
        ControlBuild.FileRef stdout = JSON.treeToValue(raw.get("stdout_ref"), ControlBuild.FileRef.class);
        ControlBuild.FileRef stderr = JSON.treeToValue(raw.get("stderr_ref"), ControlBuild.FileRef.class);
        var analysis = VctipProbeFacts.analyze(VctipProbeFacts.ProbeCase.HELP, result,
                resource(stdout), resource(stderr));
        assertEquals(1, result.exitCode());
        assertFalse(NativeLifecycleTerminal.assess(result).successful());
        assertEquals(VctipProbeFacts.Observation.HELP_OBSERVED, analysis.observation());
        assertEquals(VctipProbeFacts.Qualification.NONE, analysis.qualification());
        assertEquals(List.of("-timeout:1"), VctipProbeFacts.arguments(VctipProbeFacts.ProbeCase.IDLE_ONE));
        assertEquals(List.of("-timeout:2"), VctipProbeFacts.arguments(VctipProbeFacts.ProbeCase.IDLE_TWO));
    }

    @Test public void rejectedOriginalCaseOneHasNoInventedJobZero() throws IOException {
        JsonNode raw = read(REJECTED_ONE);
        assertEquals("REJECTED", raw.path("status").textValue());
        assertFalse(raw.path("child_started").booleanValue());
        assertTrue(raw.path("child").isNull());
        var absent = NativeLifecycleTerminal.assess(null);
        assertEquals(NativeLifecycleTerminal.Settlement.NOT_RETURNED, absent.settlement());
        assertFalse(absent.jobSettled());
        assertFalse(absent.successful());
    }

    @Test public void continuationReadsOriginalHistoryAndNeverReplaysHelpOrGrantsNative() throws IOException {
        List<NativeOperationAuthority09.OriginalEvidence> evidence = NativeOperationAuthority09.originalEvidenceRefs().stream()
                .map(ref -> {
                    try { return new NativeOperationAuthority09.OriginalEvidence(ref, resource(ref)); }
                    catch (IOException error) { throw new java.io.UncheckedIOException(error); }
                }).toList();
        var prepared = NativeOperationAuthority09.prepareOriginalUnexecutedCases(new NativeOperationAuthority09.OriginalHistory(
                evidence.get(0), evidence.get(1), evidence.get(2), evidence.get(3), evidence.get(4), evidence.get(5), evidence.get(6)));
        assertEquals(NativeOperationAuthority09.PreparationStatus.PREPARED_NOT_AUTHORIZED, prepared.status());
        assertEquals(NativeOperationAuthority09.UnavailableReason.ORDINARY09_HAS_NO_NATIVE_QUALIFICATION,
                prepared.executionUnavailableReason());
        assertEquals(List.of(1, 2), prepared.cases().stream().map(NativeOperationAuthority09.CaseRequest::originalIndex).toList());
        assertEquals(120, prepared.totalTimeoutSeconds());
        assertEquals(prepared, JSON.readValue(JSON.writeValueAsBytes(prepared), NativeOperationAuthority09.PreparedContinuation.class));
        assertThrows(IllegalArgumentException.class, () -> NativeOperationAuthority09.caseRequest(0));
        assertThrows(IllegalArgumentException.class, () -> NativeOperationAuthority09.caseRequest(3));
    }

    @Test public void currentProducerSerializesCausalAssessmentAndRejectsFalsePass() throws IOException {
        var result = terminal(0, 0, null);
        var actual = actual(result, NativeLifecycleTerminal.assess(result), NativeFixtureBuild.ActualStatus.PASS);
        byte[] wire = JSON.writeValueAsBytes(actual);
        assertEquals(actual, JSON.readValue(wire, NativeFixtureBuild.Actual.class));
        assertEquals(result, NativeProjectExeUac.qualifyBuildActual(JSON.readTree(wire)));
        String serialized = new String(wire, StandardCharsets.UTF_8);
        assertTrue(serialized.contains("\"lifecycle\""));
        var cleaned = terminal(0, 0, "timeout_or_release_expired");
        assertThrows(IllegalArgumentException.class, () -> actual(cleaned,
                NativeLifecycleTerminal.assess(cleaned), NativeFixtureBuild.ActualStatus.PASS));
        assertThrows(IllegalArgumentException.class, () -> actual(cleaned,
                NativeLifecycleTerminal.assess(result), NativeFixtureBuild.ActualStatus.RED));
    }

    @Test public void wireRejectsMissingWrongTypedAndDuplicateTerminalFields() throws IOException {
        JsonNode raw = JSON.valueToTree(terminal(0, 0, null));
        var wrong = raw.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) wrong).put("exit_code", true);
        assertThrows(IOException.class, () -> JSON.treeToValue(wrong, WindowsJobProcess.CommandResult.class));
        var missing = raw.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) missing).remove("stop_reason");
        assertThrows(IOException.class, () -> JSON.treeToValue(missing, WindowsJobProcess.CommandResult.class));
        String duplicate = new String(JSON.writeValueAsBytes(raw), StandardCharsets.UTF_8).replaceFirst("\\{", "{\"exit_code\":0,");
        assertThrows(IOException.class, () -> JSON.readValue(duplicate, WindowsJobProcess.CommandResult.class));
    }

    @Test public void naturalNonzeroAndLiveChildCannotBecomeSuccessfulSettlement() {
        assertEquals(NativeLifecycleTerminal.Settlement.NATURAL_SETTLED,
                NativeLifecycleTerminal.assess(terminal(1, 0, null)).settlement());
        assertFalse(NativeLifecycleTerminal.assess(terminal(1, 0, null)).successful());
        assertEquals(NativeLifecycleTerminal.Settlement.OWNED_PROCESSES_REMAIN,
                NativeLifecycleTerminal.assess(terminal(0, 1, null)).settlement());
        assertFalse(NativeLifecycleTerminal.assess(terminal(0, 1, null)).jobSettled());
    }

    @Test public void onlyExistingTwoNativeExecutableTargetsAreEligible() throws IOException {
        Path build = Path.of("D:/synthetic/native-build");
        for (String name : List.of("ck3_12003_prisoner_native_kinship_test",
                "xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test")) {
            Path expected = build.resolve("bin/" + name + ".exe");
            assertEquals(expected, NativeFixtureBuild.configuredPrimaryArtifact(build, name,
                    NativeFixtureBuild.TargetType.EXECUTABLE, List.of(expected.toString())));
        }
        assertThrows(IOException.class, () -> NativeFixtureBuild.configuredPrimaryArtifact(build,
                "newcontacttarget", NativeFixtureBuild.TargetType.EXECUTABLE,
                List.of(build.resolve("bin/newcontacttarget.exe").toString())));
    }

    private static JsonNode read(ControlBuild.FileRef ref) throws IOException {
        return JSON.readTree(resource(ref));
    }
    private static byte[] resource(ControlBuild.FileRef ref) throws IOException {
        String name = "/native-lifecycle/" + ref.sha256() + ".fixture";
        try (var input = NativeLifecycleRegressionTest.class.getResourceAsStream(name)) {
            if (input == null) throw new IOException("exact native lifecycle fixture missing: " + name);
            byte[] raw = input.readNBytes(65537);
            return new NativeOperationAuthority09.OriginalEvidence(ref, raw).rawBytes();
        }
    }
    private static WindowsJobProcess.CommandResult terminal(int exit, int active, String stop) {
        return new WindowsJobProcess.CommandResult(new WindowsJobProcess.ProcessIdentity(17, "134371745963270833",
                "D:/synthetic/root.exe"), exit, .1,
                new WindowsJobProcess.Accounting(1024, active, 268435456, WindowsJobProcess.REQUIRED_FLAGS), stop);
    }
    private static NativeFixtureBuild.Actual actual(WindowsJobProcess.CommandResult result,
            NativeLifecycleTerminal.Assessment assessment, NativeFixtureBuild.ActualStatus status) {
        return new NativeFixtureBuild.Actual("xar.shared-native-stage-actual/v2", MACHINE, "2026-10-22T23:00:00Z",
                status, "two-target-build", "2026-10-22T23:02:00Z", List.of("D:/synthetic/root.exe"), "D:/synthetic", null,
                null, null, null, null, List.of(), List.of(), result.identity(), result, assessment,
                true, null, null, List.of(), null);
    }
}
