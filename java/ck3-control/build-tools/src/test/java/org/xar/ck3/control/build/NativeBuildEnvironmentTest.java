package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Metadata/filesystem and command construction only; no vcvars, CMD or native process is started. */
final class NativeBuildEnvironmentTest {
    private static final String MACHINE = "software-fixture-machine";
    @TempDir Path temporary;

    @Test void sharedProducerWritesFreshScratchAndReaderRoundTripsAllowlistedValues() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("fresh-scratch"));
        Map<String, String> environment = values(scratch);
        environment.put("UNRELATED_SECRET", "must not serialize");
        environment.put("INCLUDE", "Unicode\u4e2d\u6587;space and = colon: backslash\\");
        NativeBuildEnvironment.Snapshot produced = NativeBuildEnvironment.capture(scratch, MACHINE, environment, Instant.parse("2026-10-23T04:00:00Z"));
        Path output = scratch.resolve(NativeBuildEnvironment.SNAPSHOT_NAME);
        NativeBuildEnvironment.write(scratch, output, produced);
        byte[] raw = Files.readAllBytes(output);
        NativeBuildEnvironment.Snapshot consumed = NativeBuildEnvironment.read(scratch, MACHINE, raw);
        assertEquals(produced, consumed);
        assertFalse(new String(raw, StandardCharsets.ISO_8859_1).contains("UNRELATED_SECRET"));
        assertFalse(new String(raw, StandardCharsets.ISO_8859_1).contains("must not serialize"));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.write(scratch, output, produced));
    }

    @Test void oldScratchBindingMissingFieldsAndPropertiesDriftFailOnTheActualWriterReader() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch05"));
        Path old = Files.createDirectory(temporary.resolve("scratch01"));
        NativeBuildEnvironment.Snapshot snapshot = NativeBuildEnvironment.capture(scratch, MACHINE, values(scratch), Instant.now());
        assertThrows(IOException.class, () -> NativeBuildEnvironment.write(scratch, old.resolve(NativeBuildEnvironment.SNAPSHOT_NAME), snapshot));
        Map<String, String> wrong = values(scratch); wrong.put("TMP", old.toString());
        assertThrows(IOException.class, () -> NativeBuildEnvironment.capture(scratch, MACHINE, wrong, Instant.now()));
        Map<String, String> missing = values(scratch); missing.remove("LIB");
        assertThrows(IOException.class, () -> NativeBuildEnvironment.capture(scratch, MACHINE, missing, Instant.now()));
        Path output = scratch.resolve(NativeBuildEnvironment.SNAPSHOT_NAME); NativeBuildEnvironment.write(scratch, output, snapshot);
        String original = Files.readString(output, StandardCharsets.ISO_8859_1);
        assertThrows(IOException.class, () -> NativeBuildEnvironment.read(scratch, MACHINE,
                (original + "\nLIB=duplicate\n").getBytes(StandardCharsets.ISO_8859_1)));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.read(scratch, MACHINE,
                (original + "\nUNRELATED=unexpected\n").getBytes(StandardCharsets.ISO_8859_1)));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.read(scratch, "wrong-machine",
                original.getBytes(StandardCharsets.ISO_8859_1)));
    }

    @Test void sharedBootstrapCallsPackagedProducerWithFreshPathsAndRejectsShellExpansion() throws Exception {
        Path scratch = temporary.resolve("fresh scratch");
        Path vcvars = temporary.resolve("Program Files/vendor/vcvars64.bat");
        Path java = temporary.resolve("jdk/bin/java.exe");
        Path runtime = temporary.resolve("tools runtime.jar");
        List<String> args = NativeBuildEnvironment.bootstrapArguments(vcvars, java, List.of(runtime), scratch, MACHINE);
        assertEquals(List.of("/d", "/v:off", "/s", "/c"), args.subList(0, 4));
        String command = args.get(4);
        assertTrue(command.contains("org.xar.ck3.control.build.NativeBuildEnvironment capture"));
        assertTrue(command.contains(scratch.resolve(NativeBuildEnvironment.SNAPSHOT_NAME).toString()));
        assertFalse(command.contains("native-prisoners-combat01-env.cmd"));
        assertFalse(command.contains("NativeEnvironmentSnapshot01.java"));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.bootstrapArguments(vcvars, java,
                List.of(temporary.resolve("%USERPROFILE%/tools.jar")), scratch, MACHINE));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.bootstrapArguments(vcvars, java,
                List.of(runtime), scratch, "machine&extra-command"));
    }

    @Test void exactConfigurationRoundTripRejectsLegacyAdapterAndWrongFreshOutput() throws Exception {
        Path scratch = temporary.resolve("scratch05");
        NativeBuildEnvironment.Configuration configuration = new NativeBuildEnvironment.Configuration(
                "xar.native-shared-vcvars-environment/v1", scratch.resolve(NativeBuildEnvironment.SNAPSHOT_NAME).toString());
        var mapper = ControlBuild.strictMapper();
        byte[] wire = mapper.writeValueAsBytes(configuration);
        assertEquals(configuration, NativeBuildEnvironment.readConfiguration(mapper.readTree(wire), scratch));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.readConfiguration(mapper.readTree(
                "{\"bootstrap_argv\":[\"old-env.cmd\"],\"actual_output\":\"old-scratch\"}"), scratch));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.readConfiguration(mapper.readTree(wire), temporary.resolve("old-scratch")));
        assertThrows(IOException.class, () -> NativeBuildEnvironment.readConfiguration(mapper.readTree(
                "{\"schema\":true,\"snapshot_output\":null}"), scratch));
    }

    private static Map<String, String> values(Path scratch) {
        Map<String, String> values = new HashMap<>();
        for (String name : List.of("PATH", "INCLUDE", "LIB", "VCToolsInstallDir", "WindowsSdkDir", "SystemRoot")) values.put(name, "fixture " + name);
        values.put("VSCMD_ARG_HOST_ARCH", "x64"); values.put("VSCMD_ARG_TGT_ARCH", "x64");
        for (String name : List.of("TEMP", "TMP", "TMPDIR")) values.put(name, scratch.toString());
        return values;
    }
}
