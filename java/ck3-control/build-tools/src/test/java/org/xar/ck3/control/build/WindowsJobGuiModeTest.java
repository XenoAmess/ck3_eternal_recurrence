package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Software process coverage only; a console child does not qualify GUI visibility or focus. */
final class WindowsJobGuiModeTest {
    @TempDir Path root;

    @Test void bothNoActivateModesRetainManagedChildIdentityOutputAndTerminalAccounting() throws Exception {
        for (WindowsJobProcess.ConsoleMode mode : List.of(
                WindowsJobProcess.ConsoleMode.GUI_MINIMIZED_NO_ACTIVATE,
                WindowsJobProcess.ConsoleMode.GUI_SHOWN_NO_ACTIVATE)) {
            Path stdout = root.resolve(mode.name() + ".stdout");
            Path stderr = root.resolve(mode.name() + ".stderr");
            Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
            environment.putAll(System.getenv());
            String scratch = System.getProperty("java.io.tmpdir");
            environment.put("JAVA_TOOL_OPTIONS", "-Xms16m -Xmx32m -XX:MaxMetaspaceSize=32m"
                    + " -XX:ReservedCodeCacheSize=16m -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch);
            String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
            var spec = new WindowsJobProcess.CommandSpec(
                    Path.of(System.getProperty("java.home"), "bin/java.exe"),
                    List.of("-Xms16m", "-Xmx32m", "-cp", classpath, Child.class.getName(), mode.name()),
                    root.toAbsolutePath(), environment, stdout.toAbsolutePath(), stderr.toAbsolutePath(), 256L << 20);
            try (WindowsJobProcess owner = WindowsJobProcess.start(spec, mode)) {
                var identity = owner.identity();
                var result = owner.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
                assertEquals(identity, result.identity());
                assertEquals(0, result.exitCode());
                assertNull(result.stopReason());
                assertEquals(0, result.accounting().activeProcesses());
                assertTrue(result.passed());
                assertEquals(mode.name(), Files.readString(stdout).strip());
            }
        }
    }

    public static final class Child {
        private Child() { }
        public static void main(String[] arguments) {
            if (arguments.length != 1) throw new IllegalArgumentException("One exact mode required");
            System.out.println(arguments[0]);
        }
    }
}
