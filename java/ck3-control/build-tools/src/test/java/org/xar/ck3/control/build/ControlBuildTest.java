package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ControlBuildTest {
    @TempDir Path temporary;

    @Test void measuredProducerRoundTripsThroughStrictConsumerAndDetectsSameSizeTampering() throws Exception {
        Path source = temporary.resolve("evidence.txt"); Files.writeString(source, "one");
        ControlBuild.FileRef produced = ControlBuild.FileRef.measure(source.toAbsolutePath());
        ObjectMapper json = ControlBuild.strictMapper();
        ControlBuild.FileRef consumed = json.readValue(json.writeValueAsBytes(produced), ControlBuild.FileRef.class);
        consumed.verify(); assertEquals(produced, consumed);
        Files.writeString(source, "two");
        assertThrows(IOException.class, consumed::verify);
    }

    @Test void actualRefParserRejectsTokenCoercionDuplicatesUnknownAndTrailingBodies() throws Exception {
        Path source = temporary.resolve("input.txt"); Files.writeString(source, "x");
        ObjectMapper json = ControlBuild.strictMapper();
        String valid = json.writeValueAsString(ControlBuild.FileRef.measure(source.toAbsolutePath()));
        for (String token : new String[]{"true", "1.0", "\"1\"", "null", "[]"}) {
            assertThrows(JsonProcessingException.class, () -> json.readValue(valid.replace("\"bytes\":1", "\"bytes\":" + token), ControlBuild.FileRef.class), token);
        }
        assertThrows(JsonProcessingException.class, () -> json.readValue(valid.substring(0, valid.length() - 1) + ",\"bytes\":1}", ControlBuild.FileRef.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue(valid.substring(0, valid.length() - 1) + ",\"unknown\":1}", ControlBuild.FileRef.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue(valid + " {}", ControlBuild.FileRef.class));
        String identity = "{\"pid\":1,\"creation_filetime_decimal\":18446744073709551615,\"executable\":\"C:/java.exe\"}";
        assertThrows(JsonProcessingException.class, () -> json.readValue(identity, WindowsJobProcess.ProcessIdentity.class));
    }

    @Test void commandReceiptCannotBecomeSuccessByDroppingExitOrCoercingTiming() throws Exception {
        ObjectMapper json = ControlBuild.strictMapper();
        WindowsJobProcess.CommandResult failed = new WindowsJobProcess.CommandResult(
                new WindowsJobProcess.ProcessIdentity(123, "18446744073709551615", "C:/java.exe"),
                42, 0.5, new WindowsJobProcess.Accounting(4096, 0, 8192, WindowsJobProcess.REQUIRED_FLAGS), null);
        String serialized = json.writeValueAsString(failed);
        assertFalse(json.readValue(serialized, WindowsJobProcess.CommandResult.class).passed());
        assertThrows(JsonProcessingException.class, () -> json.readValue(serialized.replace("\"exit_code\":42,", ""), WindowsJobProcess.CommandResult.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue(serialized.replace("\"stop_reason\":null", "\"unused\":null"), WindowsJobProcess.CommandResult.class));
        for (String wrong : new String[]{"\"0.5\"", "true", "null", "-0.5"}) {
            assertThrows(JsonProcessingException.class, () -> json.readValue(serialized.replace("\"elapsed_seconds\":0.5", "\"elapsed_seconds\":" + wrong), WindowsJobProcess.CommandResult.class));
        }
    }

    @Test void postcheckReadsActualSourceAfterFailureAndKeepsUnknownDistinctFromMismatch() throws Exception {
        Path root = temporary.resolve("module"); Files.createDirectories(root.resolve("src/main"));
        Path pom = root.resolve("pom.xml");
        Files.writeString(pom, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion></project>");
        Path source = root.resolve("src/main/input.txt"); Files.writeString(source, "one");
        List<ControlBuild.FileRef> original = List.of(ControlBuild.FileRef.measure(pom), ControlBuild.FileRef.measure(source));
        assertEquals(ControlBuild.SourceState.MATCH, ControlBuild.postcheckSource(root, original).state());
        Files.writeString(source, "two");
        assertEquals(ControlBuild.SourceState.MISMATCH, ControlBuild.postcheckSource(root, original).state());
        Files.delete(pom);
        ControlBuild.SourcePostcheck unavailable = ControlBuild.postcheckSource(root, original);
        assertEquals(ControlBuild.SourceState.UNKNOWN, unavailable.state()); assertNotNull(unavailable.error());
        ObjectMapper json = ControlBuild.strictMapper();
        assertEquals(unavailable, json.readValue(json.writeValueAsBytes(unavailable), ControlBuild.SourcePostcheck.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue("{\"state\":\"MATCH\",\"error\":\"not checked\"}", ControlBuild.SourcePostcheck.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue("{\"state\":true,\"error\":null}", ControlBuild.SourcePostcheck.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue("{\"state\":0,\"error\":null}", ControlBuild.SourcePostcheck.class));
    }

    @Test void defaultMvnUsesActualCmdPathAndPathextIgnoringExtensionlessWhereCandidate() throws Exception {
        Path home = temporary.resolve("maven-home"); Path bin = Files.createDirectories(home.resolve("bin"));
        Files.writeString(bin.resolve("mvn"), "EXTENSIONLESS_MUST_NOT_EXECUTE");
        Files.writeString(bin.resolve("mvn.bat"), "@echo WRONG_PATHEXT_ORDER\r\nexit /b 9\r\n");
        Files.writeString(bin.resolve("mvn.cmd"), "@echo off\r\necho Apache Maven 9.9.9 (fixture)\r\necho Maven home: " + home + "\r\necho SELECTED_CMD\r\nexit /b 0\r\n");
        Path working = Files.createDirectory(temporary.resolve("working")); Path batch = working.resolve("version.cmd");
        ControlBuild.writeMavenBatch(batch, null, List.of("-version"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.put("PATH", bin + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        environment.put("PATHEXT", ".CMD;.BAT;.EXE;.COM");
        Path output = working.resolve("version.stdout");
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(
                Path.of(System.getenv("SystemRoot"), "System32/cmd.exe"), List.of("/d", "/c", batch.toString()), working,
                environment, output, working.resolve("version.stderr"), 256L << 20))) {
            WindowsJobProcess.CommandResult actual = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            assertTrue(actual.passed()); assertEquals(0, actual.accounting().activeProcesses());
        }
        String actual = Files.readString(output); assertTrue(actual.contains("SELECTED_CMD")); assertFalse(actual.contains("WRONG_PATHEXT"));
        ControlBuild.MavenToolchain evidence = ControlBuild.measuredMavenToolchain(null, actual, "9.9.9");
        assertEquals(ControlBuild.MavenSelection.DEFAULT_COMMAND, evidence.selection());
        assertEquals("mvn", evidence.requestedCommand()); assertNull(evidence.explicitOverrideRef());
        assertEquals(ControlBuild.FileRef.measure(bin.resolve("mvn.cmd")), evidence.distributionLauncherRef());
    }

    @Test void minimumMavenVersionUsesNumericStableComponentsRatherThanStringEquality() {
        for (String accepted : new String[]{"3.10.0", "3.10.1", "3.11.0", "4.0.0", "3.100.0"}) {
            assertTrue(ControlBuild.mavenVersionAtLeast(accepted, "3.10.0"), accepted);
        }
        for (String rejected : new String[]{"3.9.16", "3.9.999", "2.99.99", "4.0.0-rc-1", "3.10", "true", "3.10.0.1"}) {
            assertFalse(ControlBuild.mavenVersionAtLeast(rejected, "3.10.0"), rejected);
        }
        Path root = temporary.toAbsolutePath();
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.Config(root.resolve("source"), root.resolve("work"),
                root.resolve("release.json"), "bad-minimum", "test", null, root.resolve("jdk"), "3.9.16", 60, ControlBuild.TargetKind.SERVICE_FAST_JAR));
    }
}
