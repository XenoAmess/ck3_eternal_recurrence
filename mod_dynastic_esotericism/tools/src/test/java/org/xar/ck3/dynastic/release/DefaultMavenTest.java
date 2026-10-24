package org.xar.ck3.dynastic.release;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Observes the command selected by PATH, including CI; no installation path is configured. */
final class DefaultMavenTest {
    @Test
    void defaultMavenIsAtLeast3100() throws IOException, InterruptedException {
        boolean windows = System.getProperty("os.name").toLowerCase(Locale.ROOT).contains("windows");
        ProcessBuilder command = windows
                ? new ProcessBuilder("cmd.exe", "/d", "/c", "mvn", "--version")
                : new ProcessBuilder("mvn", "--version");
        Process process = command.redirectErrorStream(true).start();
        boolean completed = process.waitFor(30, TimeUnit.SECONDS);
        if (!completed) {
            process.destroyForcibly();
            process.waitFor();
        }
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
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
