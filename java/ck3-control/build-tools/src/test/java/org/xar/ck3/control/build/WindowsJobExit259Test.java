package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Two real managed children; nonzero natural termination is never promoted to success. */
final class WindowsJobExit259Test {
    private enum Entry { REGULAR_JOB, OWNED_STDIO }
    private record SoftwareObservation(String schema, String machineId, Entry entry,
            WindowsJobProcess.CommandResult terminal) { }

    private static final byte[] LINE = "SOFTWARE_EXIT259\n".getBytes(StandardCharsets.US_ASCII);
    @TempDir Path temporary;

    private static Path location(Class<?> type) throws URISyntaxException {
        return Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
    }

    private static ControlBuild.FileRef classRef(Class<?> type) throws IOException, URISyntaxException {
        Path root = location(type);
        return ControlBuild.FileRef.measure(Files.isDirectory(root)
                ? root.resolve(type.getName().replace('.', '/') + ".class") : root);
    }

    private WindowsJobProcess.CommandSpec command(String name) throws IOException, URISyntaxException {
        Path directory = Files.createDirectory(temporary.resolve(name));
        Path executable = Path.of(System.getProperty("java.home"), "bin", "java.exe");
        String classpath = String.join(File.pathSeparator, location(Exit259SoftwarePeer.class).toString(),
                location(Native.class).toString(), location(Kernel32.class).toString());
        List<String> arguments = List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=24m", "-XX:ReservedCodeCacheSize=16m", "-XX:MaxDirectMemorySize=8m", "-Xss256k",
                "-Dfile.encoding=UTF-8", "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"),
                "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                "-cp", classpath, Exit259SoftwarePeer.class.getName());
        var environment = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        // The software child declares its own bounded JVM, as in the qualified09 fixture.
        environment.remove("JAVA_TOOL_OPTIONS");
        return new WindowsJobProcess.CommandSpec(executable, arguments, directory, environment,
                directory.resolve("stdout.raw"), directory.resolve("stderr.raw"), 128L << 20);
    }

    private static void natural259(Entry entry, WindowsJobProcess.CommandResult actual) throws IOException {
        var mapper = ControlBuild.strictMapper();
        System.out.println(mapper.writeValueAsString(new SoftwareObservation("xar.software-exit259-observation/v1",
                WindowsJobProcess.currentMachineId(), entry, actual)));
        assertEquals(259, actual.exitCode(), actual.toString());
        assertEquals(0, actual.accounting().activeProcesses(), actual.toString());
        assertNull(actual.stopReason(), actual.toString());
        assertFalse(actual.passed());
        var decoded = mapper.readValue(mapper.writeValueAsBytes(actual), WindowsJobProcess.CommandResult.class);
        assertEquals(actual, decoded);
        var assessment = NativeLifecycleTerminal.assess(decoded);
        assertEquals(NativeLifecycleTerminal.Settlement.NATURAL_SETTLED, assessment.settlement());
        assertTrue(assessment.jobSettled());
        assertFalse(assessment.rootSucceeded());
        assertFalse(assessment.successful());
    }

    @Test void regularJobPreservesSignalledExit259AsNaturalNonzeroFailure() throws Exception {
        var spec = command("regular");
        try (var process = WindowsJobProcess.start(spec, WindowsJobProcess.ConsoleMode.NO_WINDOW)) {
            var actual = process.await(Duration.ofSeconds(15), Instant.now().plusSeconds(20), () -> { });
            assertFalse(process.isRunning());
            assertArrayEquals(LINE, Files.readAllBytes(spec.stdout()));
            assertEquals(0, Files.size(spec.stderr()));
            natural259(Entry.REGULAR_JOB, actual);
        }
    }

    @Test void ownedStdioRetainsExit259AfterRawArrivalAndHeldIdentityPostcheck() throws Exception {
        var command = command("owned");
        var refs = List.of(classRef(Exit259SoftwarePeer.class), classRef(Native.class), classRef(Kernel32.class),
                classRef(WindowsJobProcess.class), classRef(ControlBuild.class));
        Instant deadline = Instant.now().plusSeconds(20);
        var spec = new WindowsJobProcess.OwnedStdioSpec(command, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                ControlBuild.FileRef.measure(command.executable()), refs, deadline, 128, 128, 1024, () -> { });
        try (var channel = WindowsJobProcess.startOwnedStdio(spec)) {
            var arrival = channel.readLine(deadline);
            assertArrayEquals(LINE, arrival.rawBytes());
            assertEquals(channel.identity(), arrival.identity());
            assertEquals(channel.sessionNonce(), arrival.sessionNonce());
            var actual = channel.awaitExit(null);
            channel.verifyActualIdentityAndSources();
            assertThrows(IOException.class, channel::verifyLiveOwner);
            assertSame(actual, channel.awaitExit(null));
            assertArrayEquals(LINE, Files.readAllBytes(command.stdout()));
            assertEquals(0, Files.size(command.stderr()));
            natural259(Entry.OWNED_STDIO, actual.commandResult());
        }
    }
}
