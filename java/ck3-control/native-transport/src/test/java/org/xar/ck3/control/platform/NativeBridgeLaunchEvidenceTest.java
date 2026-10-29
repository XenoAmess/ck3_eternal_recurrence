package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;

/** Real fixed-reader rejection paths; no successful native stage or launch is fabricated. */
final class NativeBridgeLaunchEvidenceTest {
    @TempDir Path temporary;

    private ControlBuild.FileRef input(String name, String body) throws IOException {
        Path file = temporary.resolve(name); Files.writeString(file, body); return ControlBuild.FileRef.measure(file);
    }
    private NativeLaunchEvidence.Expected expected(String environmentBody) throws IOException {
        var environment = input("environment.json", environmentBody);
        var build = input("build.json", "{}");
        var registration = input("registration.json", "{}");
        Path source = temporary.resolve("source"); Files.createDirectory(source);
        Path cmake = source.resolve("CMakeLists.txt"); Files.writeString(cmake, "project(negative-native-evidence)\n");
        return new NativeLaunchEvidence.Expected("software-machine", source, List.of(ControlBuild.FileRef.measure(cmake)),
                input("xar_ck3_bridge.dll", "no executable image"), input("xar_ck3_bridge_injector.exe", "no executable image"),
                new NativeLaunchEvidence.Inputs(environment, build, registration));
    }

    @Test void actualPortRejectsResearchTwoTargetReceiptsWithoutTouchingSources() throws Exception {
        var value = expected("{\"schema\":\"xar.shared-native-stage-actual/v2\",\"status\":\"PASS\",\"stage_id\":\"two-target-build\"}");
        var sources = value.completeSources();
        assertThrows(IOException.class, () -> new NativeBridgeLaunchEvidence().verify(value));
        for (var source : sources) assertEquals(source, ControlBuild.FileRef.measure(Path.of(source.path())));
        assertFalse(Files.exists(temporary.resolve("ACTUAL.json")));
    }

    @Test void genericJavaSuccessAndLegacyNativeSchemaCannotGrantPhysicalLaunchProof() throws Exception {
        var value = expected("{\"schema\":\"xar.native-bridge-build-actual/v1\",\"status\":\"PASS\"}");
        assertThrows(IOException.class, () -> new NativeBridgeLaunchEvidence().verify(value));
        Files.writeString(Path.of(value.inputs().environmentActual().path()), "{\"schema\":\"xar.java-control.build-receipt/v1\",\"status\":\"PASS\"}");
        var changed = ControlBuild.FileRef.measure(Path.of(value.inputs().environmentActual().path()));
        var generic = new NativeLaunchEvidence.Expected(value.machineId(), value.sourceRoot(), value.completeSources(),
                value.bridgeDll(), value.injector(), new NativeLaunchEvidence.Inputs(changed, value.inputs().buildActual(), value.inputs().registrationActual()));
        assertThrows(IOException.class, () -> new NativeBridgeLaunchEvidence().verify(generic));
    }
}
