package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Platform;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real Windows msvcrt/Win32 contention. No skip is a passing compatibility qualification. */
class WindowsWriterInteropTest {
    @TempDir Path root;
    static String python() {
        String path = System.getProperty("xar.python");
        if (path == null || path.isBlank()) throw new IllegalStateException("explicit verified -Dxar.python required"); return path;
    }
    static Path repository() {
        String path = System.getProperty("xar.repository.root");
        if (path == null || path.isBlank()) throw new IllegalStateException("explicit -Dxar.repository.root required"); return Path.of(path);
    }
    @Test void originalPythonLockExcludesJavaAndReleasesNormally() throws Exception {
        assertTrue(Platform.isWindows(), "Windows compatibility test must actually execute on Windows");
        WriterFixture fixture = new WriterFixture(root);
        String script = "import sys\nsys.path.insert(0,sys.argv[1])\nfrom tools.g2_saved_campaign.root_continuity_window import WindowLedger\nwith WindowLedger(sys.argv[2]).locked():\n print('LOCKED',flush=True)\n sys.stdin.readline()\n";
        Process child = new ProcessBuilder(python(), "-B", "-X", "utf8", "-c", script, repository().toString(), fixture.layout.snapshot().toString())
                .redirectErrorStream(true).start();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(child.getInputStream(), StandardCharsets.UTF_8))) {
            assertTimeoutPreemptively(Duration.ofSeconds(15), () -> assertEquals("LOCKED", reader.readLine()));
            assertThrows(java.io.IOException.class, () -> fixture.writer.preview(WriterFixture.settled("one", 1024, 2)));
            child.getOutputStream().write('\n'); child.getOutputStream().flush();
            assertTrue(child.waitFor(15, TimeUnit.SECONDS)); assertEquals(0, child.exitValue());
            assertNotNull(fixture.writer.preview(WriterFixture.settled("one", 1024, 2)));
        } finally { child.destroyForcibly(); }
    }
    @Test void javaOriginalByteRangeExcludesPythonAndOwnsExactLockIdentity() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root);
        String script = "import sys,msvcrt\nf=open(sys.argv[1],'a+b');f.seek(0)\ntry:\n msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)\nexcept OSError:\n print('BUSY');sys.exit(0)\nelse:\n msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1);sys.exit(7)\n";
        try (WindowsLedgerLock ignored = WindowsLedgerLock.acquire(fixture.layout.lock())) {
            Process child = new ProcessBuilder(python(), "-B", "-X", "utf8", "-c", script, fixture.layout.lock().toString()).redirectErrorStream(true).start();
            try {
                assertTrue(child.waitFor(15, TimeUnit.SECONDS));
                assertEquals("BUSY", new String(child.getInputStream().readAllBytes(), StandardCharsets.UTF_8).strip()); assertEquals(0, child.exitValue());
                assertThrows(java.io.IOException.class, () -> Files.move(fixture.layout.lock(), root.resolve("moved.lock")));
            } finally { child.destroyForcibly(); }
        }
        try (WindowsLedgerLock ignored = WindowsLedgerLock.acquire(fixture.layout.lock())) { assertNotNull(ignored); }
    }
}
