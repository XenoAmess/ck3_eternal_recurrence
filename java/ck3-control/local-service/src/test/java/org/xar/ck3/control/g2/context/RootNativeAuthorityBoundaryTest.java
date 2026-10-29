package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.lang.reflect.Modifier;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;

/** Pure rejection/API regressions. These tests never call launch or invent a Native completion. */
final class RootNativeAuthorityBoundaryTest {
    @Test void endpointLocatorRejectsCoercionAliasesAndUnsignedOverflow() {
        for (String value : List.of("", "0", "01", "+1", "-1", "1.0", "true", " 1", "18446744073709551616")) {
            assertThrows(IllegalArgumentException.class, () -> new RootNativePreloadAuthority.EndpointLocator(value));
        }
        assertEquals("18446744073709551615", new RootNativePreloadAuthority.EndpointLocator("18446744073709551615").serverHandleDecimal());
    }
    @Test void callerCannotConstructGameAdmissionOrPrecallWitness() {
        for (Class<?> type : List.of(RootNativeGameLaunch.OwnedGame.class,
                RootNativePreloadAuthority.NativeAdmission.class, RootNativePreloadAuthority.CallWitness.class,
                RootNativeRuntimeBinding.class, RootSteamOfflineGate.QualifiedOffline.class)) {
            for (var constructor : type.getDeclaredConstructors()) assertFalse(Modifier.isPublic(constructor.getModifiers()));
        }
    }
    @Test void newGameRequestRequiresExactInheritedNativePipeBeforeAnyCreation() {
        Path root = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        WindowsJobProcess.CommandSpec noPipe = new WindowsJobProcess.CommandSpec(root.resolve("ck3.exe"), List.of(), root,
                Map.of(), root.resolve("never-game.stdout"), root.resolve("never-game.stderr"), 64L << 20);
        assertThrows(IllegalArgumentException.class, () -> new RootNativeGameLaunch.Request(noPipe, "\\\\.\\pipe\\native-test",
                root.resolve("never-injector-evidence"), Map.of(), 64L << 20, Duration.ofSeconds(1), Instant.now().plusSeconds(10), null));
        ExactRef exe = new ExactRef(root.resolve("ck3.exe").toString(), 1, "0".repeat(64));
        ExactRef launcher = new ExactRef(root.resolve("launcher-settings.json").toString(), 1, "0".repeat(64));
        G2WindowsRootSources.Configuration supported = new G2WindowsRootSources.Configuration("fixture-machine", "fixture-session",
                new G2RetainedNativeSourceProvider.GameIdentity(1, "1"), "fixture-episode", "1", exe, launcher,
                List.of(), root, 1, 1, RootMcpEnvelope.OWNER_ROW_MAX_BYTES);
        assertEquals(32 * 1024 * 1024, supported.artifactBudget());
        assertEquals(RootMcpEnvelope.OWNER_ROW_MAX_BYTES, G2RetainedNativeSourceProvider.MAX_NATIVE_ARTIFACT_BYTES);
        assertThrows(IllegalArgumentException.class, () -> new G2RetainedNativeSourceProvider.Limits(RootMcpEnvelope.OWNER_ROW_MAX_BYTES + 1, 1024));
        assertThrows(IllegalArgumentException.class, () -> new G2RetainedNativeSourceProvider.Limits(1024, 1048577));
        assertThrows(IllegalArgumentException.class, () -> new G2WindowsRootSources.Configuration("fixture-machine", "fixture-session",
                new G2RetainedNativeSourceProvider.GameIdentity(1, "1"), "fixture-episode", "1", exe, launcher,
                List.of(), root, 1, 1, RootMcpEnvelope.OWNER_ROW_MAX_BYTES + 1));
    }
    @Test void sourceOnlyRuntimeRequestCannotSubstituteAnotherProcessForGame() {
        Path root = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        ControlBuild.FileRef pin = new ControlBuild.FileRef(root.resolve("never-read.json").toString(), 1, "0".repeat(64));
        ControlBuild.FileRef software = new ControlBuild.FileRef(root.resolve("python.exe").toString(), 1, "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> new RootNativeRuntimeBinding.Request("fixture-machine", Instant.now().plusSeconds(10),
                pin, pin, pin, pin, root, software,
                new ControlBuild.FileRef(root.resolve("launcher-settings.json").toString(), 1, "0".repeat(64)),
                new ControlBuild.FileRef(root.resolve("xar_ck3_bridge.dll").toString(), 1, "0".repeat(64)),
                new ControlBuild.FileRef(root.resolve("xar_ck3_bridge_injector.exe").toString(), 1, "0".repeat(64)),
                List.of(pin), List.of("never-run.py"), 1024));
    }
}
