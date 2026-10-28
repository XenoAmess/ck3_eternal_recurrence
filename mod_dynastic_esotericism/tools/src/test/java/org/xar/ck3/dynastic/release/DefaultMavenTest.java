package org.xar.ck3.dynastic.release;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Observes the command selected by PATH, including CI; no installation path is configured. */
final class DefaultMavenTest {
    @Test
    void defaultMavenIsAtLeast3100(@TempDir Path temporary) throws IOException, InterruptedException {
        boolean windows = System.getProperty("os.name").toLowerCase(Locale.ROOT).contains("windows");
        ProcessBuilder command = windows
                ? new ProcessBuilder("cmd.exe", "/d", "/c", "mvn", "--version")
                : new ProcessBuilder("mvn", "--version");
        Path log = Files.createTempFile(temporary, "default-maven-version-", ".log");
        Process process = command.redirectErrorStream(true).redirectOutput(log.toFile()).start();
        boolean completed = false;
        try {
            completed = process.waitFor(30, TimeUnit.SECONDS);
        } finally {
            if (!completed) {
                List<ProcessHandle> descendants = process.descendants().toList();
                for (ProcessHandle descendant : descendants.reversed()) descendant.destroyForcibly();
                process.destroyForcibly();
                boolean terminal = process.waitFor(10, TimeUnit.SECONDS);
                for (ProcessHandle descendant : descendants) {
                    try {
                        descendant.onExit().get(10, TimeUnit.SECONDS);
                    } catch (ExecutionException | TimeoutException failure) {
                        throw new IOException("default Maven descendant terminal unavailable", failure);
                    }
                }
                assertTrue(terminal, "default Maven process terminal unavailable after termination");
            }
        }
        int maximumOutputBytes = 8 * 1024 * 1024;
        byte[] observed;
        try (var input = Files.newInputStream(log)) {
            observed = input.readNBytes(maximumOutputBytes + 1);
        }
        assertTrue(observed.length <= maximumOutputBytes, "default Maven version output exceeds bounded read: " + log);
        String output = new String(observed, StandardCharsets.UTF_8);
        System.out.println("Observed default command: mvn --version\n" + output);
        assertTrue(completed, "default mvn --version timed out");
        assertEquals(0, process.exitValue(), output);
        Matcher version = Pattern.compile("Apache Maven ([0-9]+)\\.([0-9]+)\\.([0-9]+)(?=\\s|$)").matcher(output);
        assertTrue(version.find(), "default Maven version is unavailable: " + output);
        int major = Integer.parseInt(version.group(1));
        int minor = Integer.parseInt(version.group(2));
        int patch = Integer.parseInt(version.group(3));
        assertTrue(major > 3 || (major == 3 && (minor > 10 || (minor == 10 && patch >= 0))),
                "default mvn must be >= 3.10.0: " + output);
        assertTrue(output.contains("Maven home:"), "Maven home was not observed: " + output);
    }
}
