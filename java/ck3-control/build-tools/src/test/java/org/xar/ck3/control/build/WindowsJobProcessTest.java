package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
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

final class WindowsJobProcessTest {
    @TempDir Path temporary;

    @Test void actualChildExit42RetainsNativeBirthAndRejectsSuccess() throws Exception {
        Path output = temporary.resolve("exit42.stdout");
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("exit42", output))) {
            WindowsJobProcess.ProcessIdentity original = owner.identity();
            assertEquals(original, WindowsJobProcess.exactProcess(original.pid()));
            assertTrue(new BigInteger(original.creationFiletimeDecimal()).compareTo(BigInteger.ONE.shiftLeft(53)) > 0);
            WindowsJobProcess.CommandResult result = owner.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            assertEquals(42, result.exitCode()); assertFalse(result.passed());
            assertEquals(0, result.accounting().activeProcesses());
            assertTrue(result.accounting().peakJobMemoryBytes() <= result.accounting().memoryLimitBytes());
            assertTrue(Files.readString(output).contains("EXIT42"));
        }
    }

    @Test void timeoutKillsTheActualGrandchildAndLeavesNoJobMember() throws Exception {
        Path output = temporary.resolve("tree.stdout");
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("tree", output))) {
            Instant readyDeadline = Instant.now().plusSeconds(8);
            while ((!Files.exists(output) || !Files.readString(output).contains("GRANDCHILD:"))
                    && Instant.now().isBefore(readyDeadline) && owner.isRunning()) Thread.sleep(50);
            String ready = Files.readString(output);
            assertTrue(ready.contains("GRANDCHILD:"), ready);
            long grandchild = ready.lines().filter(line -> line.startsWith("GRANDCHILD:"))
                    .mapToLong(line -> Long.parseLong(line.substring(11))).findFirst().orElseThrow();
            WindowsJobProcess.ProcessIdentity generation = WindowsJobProcess.exactProcess(grandchild);
            WindowsJobProcess.CommandResult result = owner.await(Duration.ofMillis(500), Instant.now().plusSeconds(5), () -> {});
            assertFalse(result.passed()); assertEquals("timeout_or_release_expired", result.stopReason());
            assertEquals(0, result.accounting().activeProcesses());
            assertFalse(ProcessHandle.of(generation.pid()).map(ProcessHandle::isAlive).orElse(false));
        }
    }

    @Test void interruptedWaitStillReturnsActualTerminalAccountingAndPreservesInterrupt() throws Exception {
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("wait", temporary.resolve("interrupt.stdout")))) {
            Thread.currentThread().interrupt();
            try {
                WindowsJobProcess.CommandResult result = owner.await(Duration.ofSeconds(5), Instant.now().plusSeconds(8), () -> {});
                assertEquals("interrupted", result.stopReason()); assertFalse(result.passed());
                assertEquals(0, result.accounting().activeProcesses()); assertTrue(Thread.currentThread().isInterrupted());
                assertFalse(owner.isRunning());
            } finally { Thread.interrupted(); }
        }
    }

    @Test void failedCapacityGuardKillsActualChildAndRetainsReasonAndFinalAccounting() throws Exception {
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("wait", temporary.resolve("guard.stdout")))) {
            WindowsJobProcess.CommandResult result = owner.await(Duration.ofSeconds(5), Instant.now().plusSeconds(8),
                    () -> { throw new IllegalStateException("actual test capacity exhausted"); });
            assertEquals("periodic_guard: actual test capacity exhausted", result.stopReason());
            assertFalse(result.passed()); assertEquals(0, result.accounting().activeProcesses()); assertFalse(owner.isRunning());
        }
    }

    @Test void liveObservationBindsActualSelfIdentityAndUnsignedNativeUptime() throws Exception {
        long pid = ProcessHandle.current().pid();
        BigInteger before = new BigInteger(Long.toUnsignedString(com.sun.jna.platform.win32.Kernel32.INSTANCE.GetTickCount64()));
        WindowsJobProcess.LiveProcessObservation observed = WindowsJobProcess.observeLiveProcess(pid);
        BigInteger after = new BigInteger(Long.toUnsignedString(com.sun.jna.platform.win32.Kernel32.INSTANCE.GetTickCount64()));
        assertEquals(WindowsJobProcess.exactProcess(pid), observed.identity());
        BigInteger uptime = new BigInteger(observed.uptimeMillisDecimal()); assertTrue(uptime.compareTo(before) >= 0); assertTrue(uptime.compareTo(after) <= 0);
        var mapper = ControlBuild.strictMapper();
        assertEquals(observed, mapper.readValue(mapper.writeValueAsBytes(observed), WindowsJobProcess.LiveProcessObservation.class));
        var maximum = new WindowsJobProcess.LiveProcessObservation(observed.identity(), "18446744073709551615");
        assertEquals(maximum, mapper.readValue(mapper.writeValueAsBytes(maximum), WindowsJobProcess.LiveProcessObservation.class));
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsString(maximum).replace("\"uptime_millis_decimal\":\"18446744073709551615\"",
                "\"uptime_millis_decimal\":18446744073709551615"), WindowsJobProcess.LiveProcessObservation.class));
    }

    @Test void liveObservationRejectsActualExitedOwnedChildAndInvalidPid() throws Exception {
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("exit42", temporary.resolve("live-exit.stdout")))) {
            long pid = owner.identity().pid(); assertEquals(owner.identity(), WindowsJobProcess.observeLiveProcess(pid).identity());
            WindowsJobProcess.CommandResult terminal = owner.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            assertEquals(42, terminal.exitCode()); assertEquals(0, terminal.accounting().activeProcesses());
            assertThrows(RuntimeException.class, () -> WindowsJobProcess.observeLiveProcess(pid));
        }
        assertThrows(IllegalArgumentException.class, () -> WindowsJobProcess.observeLiveProcess(0));
        assertThrows(IllegalArgumentException.class, () -> WindowsJobProcess.observeLiveProcess(0x1_0000_0000L));
    }

    private WindowsJobProcess.CommandSpec spec(String mode, Path output) {
        Path java = Path.of(System.getProperty("java.home"), "bin/java.exe");
        String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        String scratch = System.getProperty("java.io.tmpdir");
        environment.put("JAVA_TOOL_OPTIONS", "-Xms16m -Xmx64m -XX:MaxMetaspaceSize=64m -XX:ReservedCodeCacheSize=32m -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch);
        return new WindowsJobProcess.CommandSpec(java, List.of("-Xms16m", "-Xmx64m", "-cp", classpath,
                Child.class.getName(), mode), temporary.toAbsolutePath(), environment, output.toAbsolutePath(),
                temporary.resolve(mode + ".stderr").toAbsolutePath(), 256L * 1024 * 1024);
    }

    public static final class Child {
        private Child() {}
        public static void main(String[] args) throws Exception {
            if (args[0].equals("exit42")) { Thread.sleep(1000); System.out.println("EXIT42"); System.exit(42); }
            if (args[0].equals("tree")) {
                Process grandchild = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin/java.exe").toString(),
                        "-Xms16m", "-Xmx64m", "-cp", System.getProperty("java.class.path"), Child.class.getName(), "wait").inheritIO().start();
                System.out.println("GRANDCHILD:" + grandchild.pid()); System.out.flush();
            }
            while (true) Thread.sleep(1000);
        }
    }
}
