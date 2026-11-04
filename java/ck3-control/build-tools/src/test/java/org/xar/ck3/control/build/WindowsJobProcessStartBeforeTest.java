package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Public startBefore boundary tests using an ordinary Java child; software history is recorded separately. */
final class WindowsJobProcessStartBeforeTest {
    @TempDir Path root;

    @Test void expiredOriginalDeadlineRejectsStartBeforeNoHook() throws Exception {
        String cp = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        List<String> argv = List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=32m", "-XX:ReservedCodeCacheSize=16m", "-Xss256k",
                "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"),
                "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                "-cp", cp, WindowsJobProcessStartBeforeTest.Child.class.getName(), "EXPIRED_MARKER");
        var env = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        env.putAll(System.getenv());
        for (String key : List.of("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS")) env.remove(key);

        Path stdout = root.resolve("expired.stdout");
        Path stderr = root.resolve("expired.stderr");
        var spec = new WindowsJobProcess.CommandSpec(
                Path.of(System.getProperty("java.home"), "bin/java.exe"),
                argv, root.toAbsolutePath(), env, stdout.toAbsolutePath(), stderr.toAbsolutePath(), 128L << 20);

        Instant expired = Instant.EPOCH;
        try (var owner = WindowsJobProcess.startBefore(spec, WindowsJobProcess.ConsoleMode.NO_WINDOW, expired)) {
            assertNotNull(owner);
            fail("startBefore must reject an expired original deadline");
        } catch (IOException failure) {
            assertNotNull(failure);
        }
    }

    @Test void futureOriginalDeadlineStartsAndAwaitsOrdinaryChild() throws Exception {
        String cp = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        List<String> argv = List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=32m", "-XX:ReservedCodeCacheSize=16m", "-Xss256k",
                "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"),
                "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                "-cp", cp, WindowsJobProcessStartBeforeTest.Child.class.getName(), "FUTURE_MARKER");
        var env = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        env.putAll(System.getenv());
        for (String key : List.of("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS")) env.remove(key);

        Path stdout = root.resolve("future.stdout");
        Path stderr = root.resolve("future.stderr");
        var spec = new WindowsJobProcess.CommandSpec(
                Path.of(System.getProperty("java.home"), "bin/java.exe"),
                argv, root.toAbsolutePath(), env, stdout.toAbsolutePath(), stderr.toAbsolutePath(), 128L << 20);

        Instant future = Instant.now().plusSeconds(30);
        try (var owner = WindowsJobProcess.startBefore(spec, WindowsJobProcess.ConsoleMode.NO_WINDOW, future)) {
            var identity = owner.identity();
            var result = owner.await(Duration.ofSeconds(10), future, () -> {});
            assertEquals(identity, result.identity());
            assertEquals(0, result.exitCode());
            assertNull(result.stopReason());
            assertEquals(0, result.accounting().activeProcesses());
            assertEquals(128L << 20, result.accounting().memoryLimitBytes());
            assertEquals(WindowsJobProcess.REQUIRED_FLAGS, result.accounting().limitFlags());
            assertTrue(result.passed());
            assertEquals("FUTURE_MARKER", Files.readString(stdout).strip());
        }
    }

    public static final class Child {
        private Child() { }
        public static void main(String[] arguments) {
            if (arguments.length != 1) throw new IllegalArgumentException("One exact marker required");
            System.out.println(arguments[0]);
        }
    }
}
