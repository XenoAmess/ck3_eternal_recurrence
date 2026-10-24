package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.sun.jna.Native;
import com.sun.jna.platform.win32.BaseTSD.SIZE_T;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual kernel Job/root/descendant tests; no fabricated process/accounting or production test hook. */
final class WindowsJobDrainTerminalTest {
    @TempDir Path temporary;

    @Test void completedRootAndZeroMemberJobSkipOnlyTheLiveGuard() throws Exception {
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("zero", "settled", null))) {
            awaitRootExit(owner); awaitJobZero(owner);
            AtomicInteger calls = new AtomicInteger();
            var result = owner.await(Duration.ofSeconds(5), Instant.now().plusSeconds(10), () -> {
                calls.incrementAndGet(); throw new IllegalStateException("completed Job must not run a live-writer guard");
            }, null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
            assertEquals(0, calls.get()); assertTrue(result.passed());
            assertEquals(0, result.exitCode()); assertEquals(0, result.accounting().activeProcesses());
            assertNull(result.stopReason()); assertFalse(owner.isRunning());
        }
    }

    @Test void actualLiveDescendantStillRunsGuardBeforeNaturalCompletion() throws Exception {
        Path gate = temporary.resolve("natural.release");
        Path output = temporary.resolve("natural.stdout");
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("root-child", "natural", gate))) {
            long pid = awaitChildPid(output); awaitRootExit(owner);
            try (var child = WindowsJobProcess.retainReadOnlyProcess(pid)) {
                assertEquals(258, child.waitZero()); assertTrue(owner.accounting().activeProcesses() > 0);
                AtomicInteger calls = new AtomicInteger();
                var result = owner.await(Duration.ofSeconds(8), Instant.now().plusSeconds(12), () -> {
                    if (calls.incrementAndGet() == 1) {
                        assertEquals(258, child.waitZero());
                        try { Files.createFile(gate); } catch (IOException failure) { throw new IllegalStateException(failure); }
                    }
                }, null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
                assertTrue(calls.get() > 0); assertTrue(result.passed()); assertEquals(0, result.accounting().activeProcesses());
                assertExited(child, 0); assertFalse(owner.isRunning());
            }
        }
    }

    @Test void actualLiveDescendantGuardFailureStillKillsAndRetainsItsReason() throws Exception {
        Path gate = temporary.resolve("guard.release");
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("root-child", "guard", gate))) {
            long pid = awaitChildPid(temporary.resolve("guard.stdout")); awaitRootExit(owner);
            try (var child = WindowsJobProcess.retainReadOnlyProcess(pid)) {
                assertEquals(258, child.waitZero());
                AtomicInteger calls = new AtomicInteger();
                var result = owner.await(Duration.ofSeconds(8), Instant.now().plusSeconds(12), () -> {
                    calls.incrementAndGet(); throw new IllegalStateException("actual live descendant guard rejected");
                }, null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
                assertTrue(calls.get() > 0); assertFalse(result.passed());
                assertEquals("periodic_guard: actual live descendant guard rejected", result.stopReason());
                assertEquals(0, result.accounting().activeProcesses()); assertExited(child, 124);
            }
        }
    }

    @Test void completedJobCannotHideExpiredCommandOrLease() throws Exception {
        for (String mode : List.of("command", "lease")) {
            try (WindowsJobProcess owner = WindowsJobProcess.start(spec("zero", "expired-" + mode, null))) {
                awaitRootExit(owner); awaitJobZero(owner);
                AtomicInteger calls = new AtomicInteger();
                var result = owner.await(mode.equals("command") ? Duration.ofNanos(1) : Duration.ofSeconds(5),
                        mode.equals("lease") ? Instant.now().minusNanos(1) : Instant.now().plusSeconds(10),
                        calls::incrementAndGet, null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
                assertFalse(result.passed()); assertEquals("timeout_or_release_expired", result.stopReason());
                assertEquals(0, calls.get()); assertEquals(0, result.accounting().activeProcesses());
            }
        }
    }

    @Test void completedRealJobRetainsObservedPeakMemoryFailureBeforeSkippingGuard() throws Exception {
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("zero", "memory", null))) {
            awaitRootExit(owner); awaitJobZero(owner);
            WindowsJobProcess.Accounting before = owner.accounting();
            assertTrue(before.peakJobMemoryBytes() > (1L << 20));
            // Narrow the already-settled test Job in the OS. The retained historical
            // native peak must still make the actual accounting fail this new limit.
            Field field = WindowsJobProcess.class.getDeclaredField("job"); field.setAccessible(true);
            HANDLE actualJob = HANDLE.class.cast(field.get(owner));
            WindowsJobProcess.JobKernel32 api = Native.load("kernel32", WindowsJobProcess.JobKernel32.class,
                    W32APIOptions.UNICODE_OPTIONS);
            WindowsJobProcess.ExtendedLimits limits = new WindowsJobProcess.ExtendedLimits();
            assertTrue(api.QueryInformationJobObject(actualJob, 9, limits.getPointer(), limits.size(), null)); limits.read();
            limits.JobMemoryLimit = new SIZE_T(1L << 20); limits.write();
            assertTrue(api.SetInformationJobObject(actualJob, 9, limits.getPointer(), limits.size()));
            WindowsJobProcess.Accounting actual = owner.accounting();
            assertEquals(1L << 20, actual.memoryLimitBytes());
            assertTrue(actual.peakJobMemoryBytes() > actual.memoryLimitBytes());
            assertEquals(0, actual.activeProcesses());
            AtomicInteger calls = new AtomicInteger();
            var result = owner.await(Duration.ofSeconds(5), Instant.now().plusSeconds(10), calls::incrementAndGet,
                    null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
            assertFalse(result.passed()); assertEquals("observed_job_peak_exceeded_limit", result.stopReason());
            assertEquals(0, calls.get()); assertEquals(0, result.accounting().activeProcesses());
        }
    }

    private WindowsJobProcess.CommandSpec spec(String mode, String name, Path gate) {
        Path java = Path.of(System.getProperty("java.home"), "bin/java.exe");
        String cp = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        String scratch = System.getProperty("java.io.tmpdir");
        environment.put("JAVA_TOOL_OPTIONS", "-Xms16m -Xmx64m -XX:MaxMetaspaceSize=64m -XX:ReservedCodeCacheSize=32m"
                + " -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch);
        List<String> argv = new ArrayList<>(List.of("-Xms16m", "-Xmx64m", "-cp", cp, Child.class.getName(), mode));
        if (gate != null) argv.add(gate.toString());
        return new WindowsJobProcess.CommandSpec(java, argv, temporary.toAbsolutePath(), environment,
                temporary.resolve(name + ".stdout").toAbsolutePath(), temporary.resolve(name + ".stderr").toAbsolutePath(),
                256L << 20);
    }
    private static void awaitRootExit(WindowsJobProcess owner) throws InterruptedException {
        long end = System.nanoTime() + Duration.ofSeconds(8).toNanos();
        while (owner.isRunning() && System.nanoTime() < end) Thread.sleep(10);
        assertFalse(owner.isRunning(), "the original root handle must actually report exit");
    }
    private static void awaitJobZero(WindowsJobProcess owner) throws InterruptedException {
        long end = System.nanoTime() + Duration.ofSeconds(5).toNanos();
        while (owner.accounting().activeProcesses() != 0 && System.nanoTime() < end) Thread.sleep(10);
        assertEquals(0, owner.accounting().activeProcesses());
    }
    private static long awaitChildPid(Path output) throws Exception {
        long end = System.nanoTime() + Duration.ofSeconds(8).toNanos();
        while (System.nanoTime() < end) {
            if (Files.isRegularFile(output)) {
                String text = Files.readString(output);
                if (text.startsWith("CHILD:") && text.endsWith("\n")) return Long.parseLong(text.strip().substring(6));
            }
            Thread.sleep(10);
        }
        throw new IOException("Actual controlled descendant PID was not observed");
    }
    private static void assertExited(WindowsJobProcess.ReadOnlyProcessHandle child, long expected) throws InterruptedException {
        long end = System.nanoTime() + Duration.ofSeconds(5).toNanos();
        while (child.waitZero() == 258 && System.nanoTime() < end) Thread.sleep(10);
        assertEquals(0, child.waitZero()); assertEquals(expected, child.exitCode());
    }
    public static final class Child {
        private Child() { }
        public static void main(String[] args) throws Exception {
            if (args.length == 1 && args[0].equals("zero")) return;
            if (args.length != 2) throw new IllegalArgumentException("Exact controlled-process mode and gate required");
            if (args[0].equals("root-child")) {
                var command = List.of(Path.of(System.getProperty("java.home"), "bin/java.exe").toString(),
                        "-Xms16m", "-Xmx64m", "-cp", System.getProperty("java.class.path"), Child.class.getName(), "leaf", args[1]);
                Process child = new ProcessBuilder(command).inheritIO().start();
                System.out.println("CHILD:" + child.pid()); System.out.flush(); return;
            }
            if (!args[0].equals("leaf")) throw new IllegalArgumentException("Unknown controlled-process mode");
            Path gate = Path.of(args[1]); long end = System.nanoTime() + Duration.ofSeconds(15).toNanos();
            while (!Files.isRegularFile(gate)) {
                if (System.nanoTime() >= end) throw new IOException("Controlled descendant release deadline expired");
                Thread.sleep(10);
            }
        }
    }
}
