package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual Java children and original Win32 Job only; all observations are SOFTWARE. */
final class WindowsJobOwnedStdioTest {
    @TempDir Path temp;
    private Path javaExe() { return Path.of(System.getProperty("java.home"), "bin", "java.exe"); }
    private Path classes() throws Exception {
        return Path.of(OwnedStdioSoftwarePeer.class.getProtectionDomain().getCodeSource().getLocation().toURI());
    }
    private WindowsJobProcess.OwnedStdioSpec spec(String mode, int frame, long sent, long received,
            List<ControlBuild.FileRef> extra, WindowsJobProcess.StdioGuard guard) throws Exception {
        Path run = Files.createDirectory(temp.resolve("run-" + java.util.UUID.randomUUID()));
        List<ControlBuild.FileRef> refs = new ArrayList<>();
        refs.add(ControlBuild.FileRef.measure(classes().resolve("org/xar/ck3/control/build/OwnedStdioSoftwarePeer.class")));
        refs.addAll(extra);
        List<String> args = List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=24m", "-XX:ReservedCodeCacheSize=16m", "-XX:MaxDirectMemorySize=8m", "-Xss256k",
                "-Dfile.encoding=UTF-8", "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"),
                "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                "-cp", classes().toString(), OwnedStdioSoftwarePeer.class.getName(), mode);
        // The software fixture declares its own bounded JVM and retains the admitted temporary paths.
        var environment = new java.util.TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv()); environment.remove("JAVA_TOOL_OPTIONS");
        var command = new WindowsJobProcess.CommandSpec(javaExe(), args, run, environment,
                run.resolve("stdout.raw"), run.resolve("stderr.raw"), 128L << 20);
        return new WindowsJobProcess.OwnedStdioSpec(command, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                ControlBuild.FileRef.measure(javaExe()), refs, Instant.now().plusSeconds(12), frame, sent, received, guard);
    }
    private WindowsJobProcess.OwnedStdioSpec spec(String mode) throws Exception {
        return spec(mode, 4096, 1 << 20, 1 << 20, List.of(), () -> { });
    }
    private static void successful(WindowsJobProcess.AwaitResult result) {
        assertTrue(result.commandResult().passed(), result.toString());
        assertEquals(0, result.commandResult().accounting().activeProcesses());
        assertNull(result.commandResult().stopReason());
    }
    private static void cleanup(WindowsJobProcess.AwaitResult result) {
        assertFalse(result.commandResult().passed()); assertNotNull(result.commandResult().stopReason());
        assertEquals(0, result.commandResult().accounting().activeProcesses());
    }
    @Test void actualEofImageDenialKeepsTheOriginalHeldRetirement() throws Exception {
        var spec = spec("echo");
        byte[] raw = "actual-eof-window\n".getBytes(StandardCharsets.UTF_8);
        try (var channel = WindowsJobProcess.startOwnedStdio(spec);
                var retained = WindowsJobProcess.retainReadOnlyProcess(channel.identity().pid())) {
            assertEquals(channel.identity(), retained.identity());
            assertNotEquals(0, retained.waitZero(), "echo peer must be waiting for actual stdin");
            channel.write(raw, Instant.now().plusSeconds(3));
            assertArrayEquals(raw, channel.readLine(Instant.now().plusSeconds(3)).rawBytes());
            // Read the actual owner's existing handles/API. No field is replaced and no
            // native reply is fabricated. Acquisition occurs while the peer waits for EOF.
            var ownerField = WindowsJobProcess.OwnedStdio.class.getDeclaredField("owner");
            ownerField.setAccessible(true);
            WindowsJobProcess owner = WindowsJobProcess.class.cast(ownerField.get(channel));
            var apiField = WindowsJobProcess.class.getDeclaredField("nativeApi");
            var processField = WindowsJobProcess.class.getDeclaredField("process");
            var jobField = WindowsJobProcess.class.getDeclaredField("job");
            apiField.setAccessible(true); processField.setAccessible(true); jobField.setAccessible(true);
            var api = WindowsJobProcess.JobKernel32.class.cast(apiField.get(owner));
            var process = com.sun.jna.platform.win32.WinBase.PROCESS_INFORMATION.class.cast(processField.get(owner));
            var job = com.sun.jna.platform.win32.WinNT.HANDLE.class.cast(jobField.get(owner));
            char[] image = new char[32768];
            var length = new com.sun.jna.ptr.IntByReference();
            var belongs = new com.sun.jna.ptr.IntByReference();
            var created = new com.sun.jna.platform.win32.WinBase.FILETIME();
            var exited = new com.sun.jna.platform.win32.WinBase.FILETIME();
            var kernel = new com.sun.jna.platform.win32.WinBase.FILETIME();
            var user = new com.sun.jna.platform.win32.WinBase.FILETIME();
            channel.closeInput();
            long end = System.nanoTime() + Duration.ofSeconds(5).toNanos();
            int checks = 0;
            String nativeFailure = null;
            IOException guardFailure = null;
            while (System.nanoTime() < end) {
                int before = api.WaitForSingleObject(process.hProcess, 0);
                if (before == 0) break;
                assertEquals(258, before, "original held process wait must be timeout or signalled");
                String call = null;
                int code = 0;
                if (!api.GetProcessTimes(process.hProcess, created, exited, kernel, user)) {
                    code = com.sun.jna.Native.getLastError(); call = "GetProcessTimes";
                }
                else {
                    length.setValue(image.length);
                    if (!api.QueryFullProcessImageName(process.hProcess, 0, image, length)) {
                        code = com.sun.jna.Native.getLastError(); call = "QueryFullProcessImageName";
                    } else if (!api.IsProcessInJob(process.hProcess, job, belongs)) {
                        code = com.sun.jna.Native.getLastError(); call = "IsProcessInJob";
                    } else if (belongs.getValue() == 0) call = "IsProcessInJob(result=0)";
                }
                if (call != null) {
                    int after = api.WaitForSingleObject(process.hProcess, 0);
                    nativeFailure = "call=" + call + "; win32=" + Integer.toUnsignedString(code)
                            + "; before=" + Integer.toUnsignedString(before) + "; after=" + Integer.toUnsignedString(after);
                    try { channel.verifyActualIdentityAndSources(); }
                    catch (IOException failure) { guardFailure = failure; }
                    break;
                }
                checks++;
            }
            var terminal = channel.awaitExit(null);
            System.out.println("OWNED_STDIO_ACTUAL_NATIVE_EOF probes=" + checks
                    + "; observation=" + nativeFailure + "; held_signal=" + retained.waitZero() + "; terminal=" + terminal);
            assertEquals(0, retained.waitZero(), "the original retained process must actually signal");
            assertEquals(0, terminal.commandResult().accounting().activeProcesses());
            if (guardFailure != null)
                throw new AssertionError("original guard failed during the actual EOF exit: " + terminal, guardFailure);
            successful(terminal);
            channel.verifyActualIdentityAndSources();
            assertEquals(channel.identity(), retained.identity());
            assertEquals(0, retained.exitCode());
            assertArrayEquals(raw, Files.readAllBytes(spec.command().stdout()));
            assertEquals("SOFTWARE_STDERR\n", Files.readString(spec.command().stderr()));
        }
    }

    @Test void rawEchoUsesOriginalJobAndIndependentStderr() throws Exception {
        var spec = spec("echo");
        byte[] raw = "{\"software\":\"\\u6c49\",\"n\":9007199254740993}\n".getBytes(StandardCharsets.UTF_8);
        try (var channel = WindowsJobProcess.startOwnedStdio(spec)) {
            channel.verifyLiveOwner();
            var write = channel.write(raw, Instant.now().plusSeconds(3));
            var arrival = channel.readLine(Instant.now().plusSeconds(3));
            assertEquals(raw.length, write.bytesWritten()); assertArrayEquals(raw, arrival.rawBytes());
            assertEquals(channel.identity(), arrival.identity()); assertEquals(write.identity(), arrival.identity());
            assertEquals(channel.sessionNonce(), arrival.sessionNonce()); assertEquals(write.sessionNonce(), arrival.sessionNonce());
            assertEquals(1, arrival.sequence()); assertEquals(64, arrival.sessionNonce().length());
            byte[] copy = arrival.rawBytes(); copy[0] = 0; assertArrayEquals(raw, arrival.rawBytes());
            channel.closeInput(); var terminal = channel.awaitExit(null); successful(terminal);
            assertSame(terminal, channel.awaitExit(null));
            assertThrows(IOException.class, channel::verifyLiveOwner);
            assertArrayEquals(raw, Files.readAllBytes(spec.command().stdout()));
            assertEquals("SOFTWARE_STDERR\n", Files.readString(spec.command().stderr()));
        }
        var ordinary = spec("echo");
        try (var owner = WindowsJobProcess.start(ordinary.command(), ordinary.consoleMode())) {
            var exit = owner.await(Duration.ofSeconds(3), ordinary.deadline(), () -> { });
            assertTrue(exit.passed(), exit.toString());
            assertEquals(0, Files.size(ordinary.command().stdout()));
            assertEquals("SOFTWARE_STDERR\n", Files.readString(ordinary.command().stderr()));
        }
    }
    @Test void splitUnicodeAndCoalescedLinesKeepSequenceAndExactBytes() throws Exception {
        try (var channel = WindowsJobProcess.startOwnedStdio(spec("split"))) {
            String[] expected = {"first\n", "\u6c49\u5b57-9007199254740993\n", "third\n"};
            for (int i = 0; i < expected.length; i++) {
                var arrival = channel.readLine(Instant.now().plusSeconds(3));
                assertEquals(i + 1, arrival.sequence());
                assertArrayEquals(expected[i].getBytes(StandardCharsets.UTF_8), arrival.rawBytes());
            }
            channel.closeInput(); successful(channel.awaitExit(null));
        }
    }
    @Test void finiteReadTimeoutLatchesUnknownAndCleanupCannotBecomeNaturalSuccess() throws Exception {
        try (var channel = WindowsJobProcess.startOwnedStdio(spec("silent"))) {
            long before = System.nanoTime();
            assertThrows(IOException.class, () -> channel.readLine(Instant.now().plusMillis(200)));
            assertTrue(System.nanoTime() - before < 5_000_000_000L);
            assertThrows(IOException.class, channel::verifyActualIdentityAndSources);
            assertThrows(IOException.class, () -> channel.write(new byte[]{10}, Instant.now().plusSeconds(1)));
            cleanup(channel.awaitExit(null));
        }
    }
    @Test void finiteWriteBackpressureIsCancelledAndJobDrained() throws Exception {
        var spec = spec("no-read", 4096, 2 << 20, 1 << 20, List.of(), () -> { });
        try (var channel = WindowsJobProcess.startOwnedStdio(spec)) {
            long before = System.nanoTime();
            assertThrows(IOException.class, () -> channel.write(new byte[1 << 20], Instant.now().plusMillis(250)));
            assertTrue(System.nanoTime() - before < 5_000_000_000L);
            cleanup(channel.awaitExit(null));
        }
    }
    @Test void eofInsideLineIsUnknownAndNonzeroExitNeverPasses() throws Exception {
        try (var channel = WindowsJobProcess.startOwnedStdio(spec("partial"))) {
            assertThrows(IOException.class, () -> channel.readLine(Instant.now().plusSeconds(3)));
            cleanup(channel.awaitExit(null));
        }
        try (var channel = WindowsJobProcess.startOwnedStdio(spec("exit7"))) {
            var terminal = channel.awaitExit(null);
            assertEquals(7, terminal.commandResult().exitCode()); assertFalse(terminal.commandResult().passed());
            assertNull(terminal.commandResult().stopReason());
            assertEquals(0, terminal.commandResult().accounting().activeProcesses());
        }
    }
    @Test void settledNaturalZeroExitCannotEraseThePreviouslyLatchedPartialEof() throws Exception {
        var spec = spec("partial");
        try (var channel = WindowsJobProcess.startOwnedStdio(spec);
                var retained = WindowsJobProcess.retainReadOnlyProcess(channel.identity().pid())) {
            // Observe the actual OS owner/accounting without a production hook
            // or fabricated terminal. This fixes the race ordering explicitly.
            var field = WindowsJobProcess.OwnedStdio.class.getDeclaredField("owner");
            field.setAccessible(true);
            WindowsJobProcess actualOwner = WindowsJobProcess.class.cast(field.get(channel));
            long end = System.nanoTime() + Duration.ofSeconds(5).toNanos();
            while ((retained.waitZero() != 0 || actualOwner.accounting().activeProcesses() != 0)
                    && System.nanoTime() < end) Thread.sleep(10);
            assertEquals(0, retained.waitZero()); assertEquals(0, retained.exitCode());
            assertEquals(0, actualOwner.accounting().activeProcesses());
            assertEquals(channel.identity(), retained.identity());
            IOException eof = assertThrows(IOException.class,
                    () -> channel.readLine(Instant.now().plusSeconds(3)));
            assertEquals("owned stdout EOF inside line", eof.getMessage());
            assertThrows(IOException.class, channel::verifyActualIdentityAndSources);
            assertThrows(IOException.class, () -> channel.write(new byte[] {10}, Instant.now().plusSeconds(1)));
            var terminal = channel.awaitExit(null);
            cleanup(terminal);
            assertEquals(0, terminal.commandResult().exitCode(), "the genuine natural exit must remain zero");
            assertEquals(retained.identity(), terminal.commandResult().identity());
            assertEquals("owned_stdio_unknown: IOException: owned stdout EOF inside line",
                    terminal.commandResult().stopReason());
            assertEquals(WindowsJobProcess.REQUIRED_FLAGS, terminal.commandResult().accounting().limitFlags());
            assertSame(terminal, channel.awaitExit(null));
            assertArrayEquals("unfinished".getBytes(StandardCharsets.UTF_8), Files.readAllBytes(spec.command().stdout()));
        }
    }
    @Test void contentAndSameBytesReplacementDriftAreRejectedBeforeNextWrite() throws Exception {
        for (boolean replacement : new boolean[]{false, true}) {
            Path source = temp.resolve("source-" + replacement + ".txt"); Files.writeString(source, "pinned");
            var spec = spec("echo", 4096, 1024, 4096, List.of(ControlBuild.FileRef.measure(source)), () -> { });
            try (var channel = WindowsJobProcess.startOwnedStdio(spec)) {
                if (replacement) {
                    Path next = temp.resolve("replacement.txt"); Files.writeString(next, "pinned");
                    Files.move(next, source, StandardCopyOption.REPLACE_EXISTING);
                } else Files.writeString(source, "drift!");
                assertThrows(IOException.class, channel::verifyActualIdentityAndSources);
                assertThrows(IOException.class, () -> channel.write(new byte[]{10}, Instant.now().plusSeconds(1)));
                cleanup(channel.awaitExit(null)); assertEquals(0, Files.size(spec.command().stdout()));
            }
        }
    }
    @Test void prelaunchDriftAndExpiredDeadlineDoNotCreateOutputs() throws Exception {
        Path source = temp.resolve("prelaunch.txt"); Files.writeString(source, "pinned");
        var spec = spec("echo", 4096, 1024, 4096, List.of(ControlBuild.FileRef.measure(source)), () -> { });
        Files.writeString(source, "broken");
        assertThrows(IOException.class, () -> WindowsJobProcess.startOwnedStdio(spec));
        assertFalse(Files.exists(spec.command().stdout())); assertFalse(Files.exists(spec.command().stderr()));
        var fresh = spec("echo");
        var expired = new WindowsJobProcess.OwnedStdioSpec(fresh.command(), fresh.consoleMode(), fresh.executableRef(),
                fresh.programSourceRefs(), Instant.now().minusSeconds(1), 4096, 4096, 4096, () -> { });
        assertThrows(IOException.class, () -> WindowsJobProcess.startOwnedStdio(expired));
        assertFalse(Files.exists(expired.command().stdout()));
    }
    @Test void lineAndAggregateLimitsRejectWholeArrivalAndDrain() throws Exception {
        var spec = spec("echo", 3, 1024, 4096, List.of(), () -> { });
        try (var channel = WindowsJobProcess.startOwnedStdio(spec)) {
            channel.write("long\n".getBytes(StandardCharsets.UTF_8), Instant.now().plusSeconds(3));
            assertThrows(IOException.class, () -> channel.readLine(Instant.now().plusSeconds(3)));
            cleanup(channel.awaitExit(null));
        }
        var sendLimit = spec("echo", 4096, 2, 4096, List.of(), () -> { });
        try (var channel = WindowsJobProcess.startOwnedStdio(sendLimit)) {
            assertThrows(IOException.class, () -> channel.write(new byte[]{1, 2, 10}, Instant.now().plusSeconds(3)));
            cleanup(channel.awaitExit(null)); assertEquals(0, Files.size(sendLimit.command().stdout()));
        }
    }
}
