package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.Isolated;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Real configuration bytes and the existing complete argv producers; no Git/Maven child is launched. */
@Isolated
class FormalReleaseTestInputsTest {
    @TempDir Path temporary;

    private record Fixture(Path repository, Path parent, Path root, Path git,
            FileRef config, Map<String, String> environment) { }

    private Fixture fixture(boolean expired) throws Exception {
        Path repository = Files.createDirectory(temporary.resolve("source"));
        Path parent = Files.createDirectory(temporary.resolve("leased-tmp"));
        Path root = parent.resolve("formal");
        // Deliberate inert DATA named git.exe. These tests prove pins/argv; actual Git qualification is separate.
        Path git = Files.writeString(temporary.resolve("git.exe"), "inert configuration fixture");
        Instant observed = Instant.now().minusSeconds(120);
        Instant review = expired ? observed.plusSeconds(1) : observed.plusSeconds(3600);
        var inputs = new FormalReleaseTestInputs.Inputs(FormalReleaseTestInputs.SCHEMA,
                WindowsJobProcess.currentMachineId(), repository.toString(), root.toString(),
                FileRef.measure(git), observed.toString(), review.toString());
        Path body = temporary.resolve("formal-inputs.json");
        Files.write(body, ControlBuild.strictMapper().writeValueAsBytes(inputs));
        FileRef pin = FileRef.measure(body);
        return new Fixture(repository, parent, root, git, pin, Map.of(
                FormalReleaseTestInputs.PATH_ENV, pin.path(),
                FormalReleaseTestInputs.BYTES_ENV, Long.toString(pin.bytes()),
                FormalReleaseTestInputs.SHA_ENV, pin.sha256(), "XAR_ORACLE_PYTHON", git.toString()));
    }

    private ControlBuild.Config config(Fixture fixture) throws Exception {
        Path release = temporary.resolve("historical-release.json");
        Files.writeString(release, "{\"schema\":\"xar.java-phase1.manual-capacity-release/v1\"}");
        return new ControlBuild.Config(fixture.repository(), temporary, release, "formal-unit", "/root/formal_unit",
                null, temporary, "3.10.0", 120, ControlBuild.TargetKind.SERVICE_FAST_JAR,
                ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
    }

    @Test void actualEnvironmentRoundTripsFiveArgumentsAndKeepsOriginalInputPins() throws Exception {
        var f = fixture(false);
        var recorded = FormalReleaseTestInputs.fromEnvironment(f.environment(), WindowsJobProcess.currentMachineId(),
                f.repository().toString());
        assertEquals(Optional.of(recorded), FormalReleaseTestInputs.fromRecordedArguments(recorded.mavenArguments()));
        assertEquals(List.of(f.config(), FileRef.measure(f.git())), FormalReleaseTestInputs.inputRefs(recorded));
        assertEquals(5, recorded.mavenArguments().size());
        assertFalse(Files.exists(f.root()));
    }

    @Test void partialDuplicateUnknownWrongTypesAndChangedOriginalsAreRejected() throws Exception {
        var f = fixture(false);
        var recorded = FormalReleaseTestInputs.fromEnvironment(f.environment(), WindowsJobProcess.currentMachineId(),
                f.repository().toString());
        assertEquals(Optional.empty(), FormalReleaseTestInputs.fromRecordedArguments(List.of("verify")));
        assertThrows(IOException.class, () -> FormalReleaseTestInputs.fromRecordedArguments(List.of(
                "-Dxar.formalReleaseTestRoot=" + f.root())));
        var duplicate = new ArrayList<>(recorded.mavenArguments()); duplicate.add(duplicate.getFirst());
        assertThrows(IOException.class, () -> FormalReleaseTestInputs.fromRecordedArguments(duplicate));
        var unknown = new ArrayList<>(recorded.mavenArguments()); unknown.add("-Dxar.formalRelease.inputs.alias=x");
        assertThrows(IOException.class, () -> FormalReleaseTestInputs.fromRecordedArguments(unknown));
        var json = ControlBuild.strictMapper(); var raw = json.readTree(Files.readAllBytes(Path.of(f.config().path())));
        assertTrue(raw.isObject());
        ((com.fasterxml.jackson.databind.node.ObjectNode) raw).put("test_root", true);
        assertThrows(IOException.class, () -> json.treeToValue(raw, FormalReleaseTestInputs.Inputs.class));
        Files.writeString(f.git(), "changed original");
        assertThrows(IOException.class, () -> FormalReleaseTestInputs.requireRecordedInputs(recorded,
                WindowsJobProcess.currentMachineId(), f.repository().toString()));
    }

    @Test void selectedVerifyGetsFixedFragmentAndCaptureConsumesNoFormalRuntimeInputs() throws Exception {
        var f = fixture(false); var config = config(f);
        Path helper = f.repository().resolve("local-service/src/test/java/org/xar/ck3/control/service/root/FormalReleaseTestFixture.java");
        Files.createDirectories(helper.getParent()); Files.writeString(helper, "fixture source DATA");
        var settings = temporary.resolve("settings"); var build = temporary.resolve("build");
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config, settings,
                f.repository(), build, Map.of("XAR_ORACLE_PYTHON", f.git().toString())));
        var recorded = FormalReleaseTestInputs.fromEnvironment(f.environment(), WindowsJobProcess.currentMachineId(),
                f.repository().toString());
        var complete = ControlBuild.reactorVerifyArguments(config, settings, f.repository(), build, f.environment());
        assertTrue(complete.containsAll(recorded.mavenArguments())); assertEquals("verify", complete.getLast());
        var capture = ControlBuild.reactorCaptureArguments(config, settings, f.repository(), build,
                Map.of("XAR_ORACLE_PYTHON", f.git().toString()));
        assertEquals("package", capture.getLast()); assertTrue(capture.contains("-DskipTests=true"));
        assertEquals(Optional.empty(), FormalReleaseTestInputs.fromRecordedArguments(capture));
    }

    @Test void completedConsumerReplaysExpiredLeaseWithoutRecreatingOutputAndRechecksPins() throws Exception {
        var f = fixture(true); var config = config(f); var input = ControlBuild.strictMapper().readValue(
                Files.readAllBytes(Path.of(f.config().path())), FormalReleaseTestInputs.Inputs.class);
        var recorded = new FormalReleaseTestInputs.Recorded(f.config(), f.root().toString(), f.git().toString());
        assertThrows(IOException.class, () -> FormalReleaseTestInputs.fromEnvironment(f.environment(),
                WindowsJobProcess.currentMachineId(), f.repository().toString()));
        var args = ControlBuild.completedVerifyArguments(config, temporary.resolve("settings"), f.repository(),
                temporary.resolve("build"), f.git().toString(), null, FileRef.measure(config.capacityRelease()),
                Instant.parse(input.observedAtUtc()), FormalReleaseTestInputs.fromRecordedArguments(recorded.mavenArguments()));
        assertTrue(args.containsAll(recorded.mavenArguments())); assertFalse(Files.exists(f.root()));
        assertEquals(recorded.mavenArguments(), FormalReleaseTestInputs.fromRecordedArguments(args).orElseThrow().mavenArguments());
    }

    @Test void originalPrivateTmpCreatorAndSharedNativeGuardRejectSourceDrift() throws Exception {
        var f = fixture(false); var recorded = FormalReleaseTestInputs.fromEnvironment(f.environment(),
                WindowsJobProcess.currentMachineId(), f.repository().toString());
        String name = ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, previous = System.getProperty(name);
        System.setProperty(name, "true");
        try {
            FormalReleaseTestInputs.prepareRoot(recorded, f.parent(), () -> { });
            assertTrue(Files.isDirectory(f.root()));
            var guard = FormalReleaseTestInputs.guarded(recorded, WindowsJobProcess.currentMachineId(),
                    f.repository().toString(), () -> { });
            guard.check();
            assertThrows(IOException.class, () -> FormalReleaseTestInputs.prepareRoot(recorded, f.parent(), () -> { }));
            Files.writeString(f.git(), "changed during original guarded build");
            assertThrows(IOException.class, guard::check);
        } finally {
            if (previous == null) System.clearProperty(name); else System.setProperty(name, previous);
        }
    }
}
