package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.LobbyVerifyTestInputs;

final class ControlBuildLobbySoftwareLaneTest {
    @TempDir Path temporary;

    private Path selectedSnapshot() throws IOException {
        Path snapshot = Files.createDirectory(temporary.resolve("snapshot"));
        Path testDir = Files.createDirectories(snapshot.resolve("src/test/java/org/xar/ck3/control/build"));
        Files.writeString(testDir.resolve("FrontendLobbyCallbackObservationTest.java"), "// selected fixture marker");
        Files.writeString(snapshot.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion></project>");
        return snapshot;
    }

    private ControlBuild.Config toolsConfig(Path snapshot) throws IOException {
        Path work = Files.createDirectory(temporary.resolve("work"));
        Path release = temporary.resolve("release.json");
        Files.writeString(release, "{}");
        return new ControlBuild.Config(snapshot, work, release, "lane-test", "/root", null, temporary,
                "3.10.0", 900, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,
                ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
    }

    @Test void softwareLaneWithoutExternalKeysLeavesLobbyEmpty() throws Exception {
        Path snapshot = selectedSnapshot();
        ControlBuild.Config config = toolsConfig(snapshot);
        Path settings = temporary.resolve("settings.xml");
        Path build = temporary.resolve("build");
        Map<String, String> environment = Map.of(
                "XAR_ORACLE_PYTHON", temporary.resolve("python.exe").toString(),
                "XAR_FRONTEND_LOBBY_SOFTWARE_FRAMES", temporary.resolve("frames").toString());
        List<String> args = ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, environment);
        assertTrue(args.stream().noneMatch(arg -> arg.startsWith("-Dxar.g2.frontend.lobby.inputs.")));
        assertFalse(args.stream().anyMatch(arg -> arg.startsWith("-Dmaven.test.skip") && !arg.equals("-Dmaven.test.skip=false")));
        assertEquals("verify", args.getLast());
        assertFalse(args.contains("-DskipTests=true"));
    }

    @Test void partialExternalKeysAlongsideSoftwareStillThrow() throws Exception {
        Path snapshot = selectedSnapshot();
        ControlBuild.Config config = toolsConfig(snapshot);
        Path settings = temporary.resolve("settings.xml");
        Path build = temporary.resolve("build");
        for (String key : List.of(LobbyVerifyTestInputs.ENV, LobbyVerifyTestInputs.ENV + "_BYTES", LobbyVerifyTestInputs.ENV + "_SHA256")) {
            Map<String, String> environment = Map.of(
                    "XAR_ORACLE_PYTHON", temporary.resolve("python.exe").toString(),
                    "XAR_FRONTEND_LOBBY_SOFTWARE_FRAMES", temporary.resolve("frames").toString(),
                    key, "");
            assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, environment));
        }
    }

    @Test void absentSoftwareWithNoExternalKeysThrows() throws Exception {
        Path snapshot = selectedSnapshot();
        ControlBuild.Config config = toolsConfig(snapshot);
        Path settings = temporary.resolve("settings.xml");
        Path build = temporary.resolve("build");
        Map<String, String> environment = Map.of("XAR_ORACLE_PYTHON", temporary.resolve("python.exe").toString());
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, environment));
        Map<String, String> blank = Map.of("XAR_ORACLE_PYTHON", temporary.resolve("python.exe").toString(),
                "XAR_FRONTEND_LOBBY_SOFTWARE_FRAMES", "  ");
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, blank));
    }

    @Test void validExternalMetadataAlongsideSoftwareProducesPinnedFragment() throws Exception {
        Path snapshot = selectedSnapshot();
        ControlBuild.Config config = toolsConfig(snapshot);
        Path settings = temporary.resolve("settings.xml");
        Path build = temporary.resolve("build");
        Path directory = Files.createDirectory(temporary.resolve("external-lobby"));
        List<ControlBuild.FileRef> originals = new ArrayList<>();
        for (String name : SdkFixtureProductionInputs.LOBBY_NAMES) {
            Path copy = directory.resolve(name);
            Files.write(copy, new byte[]{1, 2, 3});
            originals.add(ControlBuild.FileRef.measure(copy));
        }
        var inputs = new LobbyVerifyTestInputs.Inputs(LobbyVerifyTestInputs.SCHEMA,
                WindowsJobProcess.currentMachineId(), Instant.now().plusSeconds(3600).toString(),
                new SdkFixtureProductionInputs.LobbyWireSet(directory.toString(), originals));
        Path metadata = temporary.resolve("external-lobby-inputs.json");
        Files.write(metadata, ControlBuild.strictMapper().writeValueAsBytes(inputs));
        ControlBuild.FileRef ref = ControlBuild.FileRef.measure(metadata);
        Map<String, String> environment = Map.of(
                "XAR_ORACLE_PYTHON", temporary.resolve("python.exe").toString(),
                "XAR_FRONTEND_LOBBY_SOFTWARE_FRAMES", temporary.resolve("frames").toString(),
                LobbyVerifyTestInputs.ENV, ref.path(),
                LobbyVerifyTestInputs.ENV + "_BYTES", Long.toString(ref.bytes()),
                LobbyVerifyTestInputs.ENV + "_SHA256", ref.sha256());
        List<String> args = ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, environment);
        assertTrue(args.stream().anyMatch(arg -> arg.startsWith("-Dxar.g2.frontend.lobby.inputs.path=")));
        assertTrue(args.stream().anyMatch(arg -> arg.startsWith("-Dxar.g2.frontend.lobby.inputs.bytes=")));
        assertTrue(args.stream().anyMatch(arg -> arg.startsWith("-Dxar.g2.frontend.lobby.inputs.sha256=")));
        var recorded = new LobbyVerifyTestInputs.Recorded(ref, directory.toString());
        assertTrue(args.containsAll(recorded.mavenArguments()));
        ref.verify();
        Files.writeString(Path.of(originals.getFirst().path()), "changed exact original");
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, environment));
    }
}
