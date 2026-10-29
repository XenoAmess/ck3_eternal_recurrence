package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.WindowsJobProcess;

final class NativeLaunchPolicyTest {
    @TempDir Path temporary;

    @Test void nativeEnvironmentRejectsAConflictingBackendPipeOrWindowsKeyAlias() {
        String pipe = "\\\\.\\pipe\\software-only";
        assertEquals(Map.of("XAR_CK3_BRIDGE_MODE", "native-headless"),
                NativeLaunchPolicy.requireEnvironment(Map.of("XAR_CK3_BRIDGE_MODE", "native-headless"), pipe));
        assertThrows(IllegalArgumentException.class, () -> NativeLaunchPolicy.requireEnvironment(
                Map.of("XAR_CK3_BRIDGE_MODE", "hybrid-fallback"), pipe));
        assertThrows(IllegalArgumentException.class, () -> NativeLaunchPolicy.requireEnvironment(
                Map.of("XAR_CK3_BRIDGE_PIPE", "\\\\.\\pipe\\different"), pipe));
        assertThrows(IllegalArgumentException.class, () -> NativeLaunchPolicy.requireEnvironment(
                Map.of("TMP", temporary.toString(), "tmp", temporary.toString()), pipe));
        assertThrows(IllegalArgumentException.class, () -> NativeLaunchPolicy.requireEnvironment(
                Map.of("BAD=KEY", "value"), pipe));
    }

    @Test void allActualOutputRootsAndBothExplicitTemporaryPathsReachTheSameGuard() throws IOException {
        List<Path> checked = new ArrayList<>();
        Path profile = temporary.resolve("profile"), state = temporary.resolve("state"),
                evidence = temporary.resolve("evidence"), production = profile.resolve("mod"),
                temp = temporary.resolve("temp"), tmp = temporary.resolve("tmp");
        NativeLaunchPolicy.requireOutputs(profile, state, evidence, production,
                Map.of("TEMP", temp.toString(), "tmp", tmp.toString()), true, checked::add);
        assertEquals(List.of(profile, state, evidence, production, temp, tmp), checked);
        for (Path path : checked) assertFalse(Files.exists(path));
    }

    @Test void enabledStoragePolicyRequiresBothTemporaryPathsWithoutInheritedFallback() {
        List<Path> checked = new ArrayList<>();
        IOException missing = assertThrows(IOException.class, () -> NativeLaunchPolicy.requireOutputs(
                temporary, temporary, temporary, temporary, Map.of(), true, checked::add));
        assertTrue(missing.getMessage().contains("TEMP"));
        IOException missingTmp = assertThrows(IOException.class, () -> NativeLaunchPolicy.requireOutputs(
                temporary, temporary, temporary, temporary,
                Map.of("TEMP", temporary.toString()), true, checked::add));
        assertTrue(missingTmp.getMessage().contains("TMP"));
        assertThrows(IOException.class, () -> NativeLaunchPolicy.requireOutputs(
                temporary, temporary, temporary, temporary, Map.of("TEMP", "relative"), false, checked::add));
    }

    @Test void aRejectedPhysicalOutputStopsBeforeLaterPathsAndCreatesNothing() {
        Path forbidden = temporary.resolve("forbidden"), later = temporary.resolve("later");
        List<Path> checked = new ArrayList<>();
        assertThrows(IOException.class, () -> NativeLaunchPolicy.requireOutputs(forbidden, later, later, later,
                Map.of("TEMP", later.toString(), "TMP", later.toString()), true, path -> {
                    checked.add(path);
                    if (path.equals(forbidden)) throw new IOException("actual volume rejected");
                }));
        assertEquals(List.of(forbidden), checked);
        assertFalse(Files.exists(forbidden));
        assertFalse(Files.exists(later));
    }

    @Test void actualSystemVolumeGuardRejectsTheLaunchProfileWithoutCreatingIt() {
        String systemRoot = System.getenv("SystemRoot");
        if (systemRoot == null || !System.getProperty("os.name", "").startsWith("Windows")) {
            throw new IllegalStateException("This actual physical-volume regression requires Windows SystemRoot");
        }
        String before = System.getProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        String beforeRoot = System.getProperty(ProjectStoragePolicy.PROJECT_STORAGE_ROOT);
        Path forbidden = Path.of(systemRoot).resolve("xar-launch-policy-regression-no-create");
        try {
            System.setProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true");
            System.setProperty(ProjectStoragePolicy.PROJECT_STORAGE_ROOT, temporary.toString());
            IOException error = assertThrows(IOException.class, () -> NativeLaunchPolicy.requireOutputs(
                    forbidden, temporary, temporary, temporary,
                    Map.of("TEMP", temporary.toString(), "TMP", temporary.toString()), true,
                    ProjectStoragePolicy::requireBulkOutput));
            assertTrue(error.getMessage().contains("system volume"));
            assertFalse(Files.exists(forbidden));
        } finally {
            restore(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, before);
            restore(ProjectStoragePolicy.PROJECT_STORAGE_ROOT, beforeRoot);
        }
    }

    @Test void retiredRendererFingerprintIncludesHiddenOwnersAndDoesNotDisableTheCurrentUi() throws IOException {
        for (String value : List.of("XARG2DecisionOverlay_1", "XARG2DecisionOverlay_000123")) {
            assertTrue(NativeLaunchPolicy.isRetiredDecisionPanel(value));
            assertThrows(IOException.class, () -> NativeLaunchPolicy.requireNoRetiredDecisionPanel(
                    Instant.now().plusSeconds(30), deadline -> List.of("CurrentDecisionUi", value)));
        }
        for (String value : List.of("XARG2DecisionOverlay_", "XARG2DecisionOverlay_0",
                "XARG2DecisionOverlay_-1", "XARG2DecisionOverlay_１２", "CurrentDecisionUi")) {
            assertFalse(NativeLaunchPolicy.isRetiredDecisionPanel(value));
        }
        NativeLaunchPolicy.requireNoRetiredDecisionPanel(Instant.now().plusSeconds(30),
                deadline -> List.of("CurrentDecisionUi", "OtherWindow"));
    }

    @Test void unavailableOrExpiredNativeWindowInventoryCannotBecomeAnEmptyPass() {
        IOException unavailable = assertThrows(IOException.class,
                () -> NativeLaunchPolicy.requireNoRetiredDecisionPanel(Instant.now().plusSeconds(30),
                        deadline -> { throw new IOException("native inventory unavailable"); }));
        assertEquals("native inventory unavailable", unavailable.getMessage());
        AtomicBoolean called = new AtomicBoolean();
        assertThrows(IOException.class, () -> NativeLaunchPolicy.requireNoRetiredDecisionPanel(Instant.EPOCH,
                deadline -> { called.set(true); return List.of(); }));
        assertFalse(called.get());
    }

    @Test void directCreatorUsesItsOneActualUserdirAndEveryExplicitOutput() throws IOException {
        String pipe = "\\\\.\\pipe\\software-only";
        Path profile = temporary.resolve("profile"), evidence = temporary.resolve("evidence");
        var command = gameCommand(List.of("-gdpr-compliant", "-userdir=" + profile), pipe);
        assertEquals(List.of(profile, command.stdout(), command.stderr(), evidence),
                NativeLaunchPolicy.gameOutputs(command, pipe, List.of(evidence)));
        assertFalse(Files.exists(profile));
        assertFalse(Files.exists(evidence));
    }

    @Test void missingDuplicateRelativeUserdirAndWrongPipeRejectBeforeAnyDirectCreator() {
        String pipe = "\\\\.\\pipe\\software-only";
        for (List<String> arguments : List.of(List.<String>of(), List.of("-userdir=relative"),
                List.of("-userdir=" + temporary, "-userdir=" + temporary.resolve("other")))) {
            var command = gameCommand(arguments, pipe);
            assertThrows(IOException.class, () -> NativeLaunchPolicy.gameOutputs(command, pipe, List.of()));
        }
        var command = gameCommand(List.of("-userdir=" + temporary), pipe);
        assertThrows(IOException.class, () -> NativeLaunchPolicy.gameOutputs(command, "\\\\.\\pipe\\other", List.of()));
    }

    private WindowsJobProcess.CommandSpec gameCommand(List<String> arguments, String pipe) {
        return new WindowsJobProcess.CommandSpec(temporary.resolve("ck3.exe"), arguments, temporary,
                Map.of("XAR_CK3_BRIDGE_MODE", "native-headless", "XAR_CK3_BRIDGE_PIPE", pipe,
                        "TEMP", temporary.toString(), "TMP", temporary.toString()),
                temporary.resolve("stdout"), temporary.resolve("stderr"), 128L << 20);
    }

    private static void restore(String property, String value) {
        if (value == null) System.clearProperty(property); else System.setProperty(property, value);
    }
}
