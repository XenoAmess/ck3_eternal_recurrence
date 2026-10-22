package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
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
            Path sidecar = temporary.resolve("exit42.job-members.json");
            WindowsJobProcess.AwaitResult awaited = owner.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {}, sidecar);
            WindowsJobProcess.CommandResult result = awaited.commandResult();
            assertEquals(WindowsJobProcess.DiagnosticWriteState.NOT_NEEDED, awaited.diagnostic().state());
            assertNull(awaited.diagnostic().sidecarRef()); assertFalse(Files.exists(sidecar));
            assertEquals(42, result.exitCode()); assertFalse(result.passed());
            assertEquals(0, result.accounting().activeProcesses());
            assertTrue(result.accounting().peakJobMemoryBytes() <= result.accounting().memoryLimitBytes());
            assertTrue(Files.readString(output).contains("EXIT42"));
        }
    }

    @Test void exitedRootZeroWithActualLiveChildWritesOwnedMembershipBeforeKillAndStillRejectsSuccess() throws Exception {
        Path output = temporary.resolve("root0-tree.stdout"); Path sidecar = temporary.resolve("root0.job-members.json");
        WindowsJobProcess owner = WindowsJobProcess.start(spec("root0-live-child", output));
        try (owner) {
            long childPid = awaitLiveChildPid(output);
            try (WindowsJobProcess.ReadOnlyProcessHandle retained = WindowsJobProcess.retainReadOnlyProcess(childPid)) {
                WindowsJobProcess.ProcessIdentity child = retained.identity(); assertEquals(258, retained.waitZero());
                WindowsJobProcess.AwaitResult awaited = owner.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {}, sidecar);
                WindowsJobProcess.CommandResult terminal = awaited.commandResult();
                assertEquals(0, terminal.exitCode()); assertEquals("root_exited_with_live_children", terminal.stopReason());
                assertFalse(terminal.passed()); assertEquals(0, terminal.accounting().activeProcesses());
                assertEquals(WindowsJobProcess.DiagnosticWriteState.WRITTEN, awaited.diagnostic().state());
                awaited.diagnostic().sidecarRef().verify(); assertNull(awaited.diagnostic().error());
                assertTrue(Files.size(sidecar) <= WindowsJobProcess.JOB_DIAGNOSTIC_MAX_BYTES);
                var mapper = ControlBuild.strictMapper();
                WindowsJobProcess.JobDiagnostic snapshot = mapper.readValue(Files.readAllBytes(sidecar), WindowsJobProcess.JobDiagnostic.class);
                assertEquals(snapshot, mapper.readValue(mapper.writeValueAsBytes(snapshot), WindowsJobProcess.JobDiagnostic.class));
                assertEquals(WindowsJobProcess.currentMachineId(), snapshot.machineId());
                assertEquals("OWNED_JOB_BEFORE_CLEANUP", snapshot.scope());
                assertEquals("root_exited_with_live_children", snapshot.trigger());
                assertEquals(terminal.identity(), snapshot.root().identity());
                assertEquals(0L, snapshot.root().waitZero()); assertEquals(0L, snapshot.root().exitCode());
                assertNull(snapshot.root().error()); assertTrue(snapshot.accounting().activeProcesses() > 0);
                assertEquals(WindowsJobProcess.JobListState.COMPLETE, snapshot.listState());
                WindowsJobProcess.JobMember row = snapshot.members().stream()
                        .filter(member -> member.pidDecimal().equals(Long.toString(childPid))).findFirst().orElseThrow();
                assertEquals(WindowsJobProcess.MemberState.OBSERVED, row.state()); assertEquals(child, row.identity());
                assertEquals(Boolean.TRUE, row.inOwnedJob()); assertEquals(258L, row.waitZero()); assertEquals(259L, row.exitCode());
                assertNull(row.error()); assertNull(row.win32Error());
                assertActuallyKilledChild(retained);
            }
        }
        assertThrows(IllegalStateException.class, owner::accounting);
    }

    @Test void existingDiagnosticSidecarCannotBeOverwrittenOrMaskTheActualLiveChildFailureAndCleanup() throws Exception {
        Path output = temporary.resolve("root0-existing.stdout"); Path sidecar = temporary.resolve("existing.job-members.json");
        Files.writeString(sidecar, "protected original diagnostic");
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("root0-live-child", output))) {
            long childPid = awaitLiveChildPid(output);
            try (WindowsJobProcess.ReadOnlyProcessHandle retained = WindowsJobProcess.retainReadOnlyProcess(childPid)) {
                assertEquals(258, retained.waitZero());
                WindowsJobProcess.AwaitResult awaited = owner.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {}, sidecar);
                assertEquals(0, awaited.commandResult().exitCode());
                assertEquals("root_exited_with_live_children", awaited.commandResult().stopReason());
                assertFalse(awaited.commandResult().passed()); assertEquals(0, awaited.commandResult().accounting().activeProcesses());
                assertEquals(WindowsJobProcess.DiagnosticWriteState.UNAVAILABLE, awaited.diagnostic().state());
                assertNull(awaited.diagnostic().sidecarRef()); assertTrue(awaited.diagnostic().error().contains("FileAlreadyExistsException"));
                assertEquals("protected original diagnostic", Files.readString(sidecar));
                assertActuallyKilledChild(retained);
            }
        }
    }

    /** Job accounting zero and each process object's signal are independent native observations. */
    private static void assertActuallyKilledChild(WindowsJobProcess.ReadOnlyProcessHandle retained) throws InterruptedException {
        long deadline = System.nanoTime() + Duration.ofSeconds(5).toNanos();
        long signal = 258; boolean observedInTime = false;
        while (System.nanoTime() - deadline < 0) {
            signal = retained.waitZero();
            if (signal != 258) {
                observedInTime = System.nanoTime() - deadline < 0;
                break;
            }
            Thread.sleep(10);
        }
        assertTrue(observedInTime, "actual child kernel signal must be observed within five monotonic seconds");
        assertEquals(0, signal, "Job accounting zero alone cannot stand in for the retained process object's signal");
        assertEquals(125, retained.exitCode());
    }

    private long awaitLiveChildPid(Path output) throws Exception {
        Instant deadline = Instant.now().plusSeconds(8);
        String ready = "";
        while (Instant.now().isBefore(deadline)) {
            if (Files.exists(output)) ready = Files.readString(output);
            if (ready.contains("GRANDCHILD:") && ready.endsWith("\n")) break;
            Thread.sleep(20);
        }
        assertTrue(ready.contains("GRANDCHILD:") && ready.endsWith("\n"), "actual child PID line must be complete");
        return ready.lines().filter(line -> line.startsWith("GRANDCHILD:"))
                .mapToLong(line -> Long.parseLong(line.substring(11))).findFirst().orElseThrow();
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

    @Test void retainedSelfHandleMeasuresIdentityAndIndependentNativeStateUntilOneClose() throws Exception {
        long pid = ProcessHandle.current().pid();
        WindowsJobProcess.ReadOnlyProcessHandle retained = WindowsJobProcess.retainReadOnlyProcess(pid);
        try (retained) {
            WindowsJobProcess.ProcessIdentity measured = retained.identity();
            assertEquals(WindowsJobProcess.exactProcess(pid), measured);
            assertTrue(new BigInteger(measured.creationFiletimeDecimal()).compareTo(BigInteger.ONE.shiftLeft(53)) > 0);
            assertEquals(258, retained.waitZero());
            assertEquals(259, retained.exitCode());
            assertEquals(measured, retained.identity());
        }
        retained.close();
        assertThrows(IllegalStateException.class, retained::identity);
        assertThrows(IllegalStateException.class, retained::waitZero);
        assertThrows(IllegalStateException.class, retained::exitCode);
        assertThrows(IllegalArgumentException.class, () -> WindowsJobProcess.retainReadOnlyProcess(0));
        assertThrows(IllegalArgumentException.class, () -> WindowsJobProcess.retainReadOnlyProcess(0x1_0000_0000L));
    }

    @Test void retainedHandlePreservesExitedJobGenerationAndUnsignedDwordAfterOriginalOwnerCloses() throws Exception {
        for (String mode : List.of("exit42", "exit259", "exit-1")) {
            Path releaseGate = temporary.resolve(mode + "-retained.release");
            WindowsJobProcess.ReadOnlyProcessHandle retained = null;
            WindowsJobProcess.ProcessIdentity generation;
            long actualExit;
            try {
                try (WindowsJobProcess owner = WindowsJobProcess.start(spec("retained-" + mode,
                        temporary.resolve(mode + "-retained.stdout"), List.of(releaseGate.toString())))) {
                    generation = owner.identity();
                    retained = WindowsJobProcess.retainReadOnlyProcess(generation.pid());
                    assertEquals(generation, retained.identity());
                    assertFalse(Files.exists(releaseGate));
                    assertEquals(258, retained.waitZero(), "child must be retained before its release gate opens");
                    assertEquals(259, retained.exitCode());
                    Files.createFile(releaseGate);
                    WindowsJobProcess.CommandResult terminal = owner.await(
                            Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
                    assertEquals(0, terminal.accounting().activeProcesses());
                    actualExit = Integer.toUnsignedLong(terminal.exitCode());
                    long expectedExit = mode.equals("exit42") ? 42 : mode.equals("exit259") ? 259 : 0xffff_ffffL;
                    assertEquals(expectedExit, actualExit);
                }
                // The independent query handle survives the original Job owner's cleanup.
                assertEquals(generation, retained.identity());
                assertEquals(0, retained.waitZero());
                assertEquals(actualExit, retained.exitCode());
                assertEquals(0, retained.waitZero());
            } finally {
                if (retained != null) retained.close();
            }
        }
    }

    private WindowsJobProcess.CommandSpec spec(String mode, Path output) {
        return spec(mode, output, List.of());
    }

    private WindowsJobProcess.CommandSpec spec(String mode, Path output, List<String> childArguments) {
        Path java = Path.of(System.getProperty("java.home"), "bin/java.exe");
        String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        String scratch = System.getProperty("java.io.tmpdir");
        environment.put("JAVA_TOOL_OPTIONS", "-Xms16m -Xmx64m -XX:MaxMetaspaceSize=64m -XX:ReservedCodeCacheSize=32m -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch);
        List<String> arguments = new ArrayList<>(List.of("-Xms16m", "-Xmx64m", "-cp", classpath,
                Child.class.getName(), mode));
        arguments.addAll(childArguments);
        return new WindowsJobProcess.CommandSpec(java, arguments, temporary.toAbsolutePath(), environment, output.toAbsolutePath(),
                temporary.resolve(mode + ".stderr").toAbsolutePath(), 256L * 1024 * 1024);
    }

    public static final class Child {
        private Child() {}
        public static void main(String[] args) throws Exception {
            if (args[0].equals("exit42")) { Thread.sleep(1000); System.out.println("EXIT42"); System.exit(42); }
            if (args[0].startsWith("retained-exit")) {
                if (args.length != 2) throw new IllegalArgumentException("One explicit release gate required");
                int exit = switch (args[0]) {
                    case "retained-exit42" -> 42;
                    case "retained-exit259" -> 259;
                    case "retained-exit-1" -> -1;
                    default -> throw new IllegalArgumentException("Unknown retained child exit mode");
                };
                Path releaseGate = Path.of(args[1]);
                long deadline = System.nanoTime() + Duration.ofSeconds(20).toNanos();
                while (!Files.isRegularFile(releaseGate)) {
                    if (System.nanoTime() - deadline >= 0) throw new IllegalStateException("Release gate never opened");
                    Thread.sleep(10);
                }
                System.exit(exit);
            }
            if (args[0].equals("tree") || args[0].equals("root0-live-child")) {
                Process grandchild = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin/java.exe").toString(),
                        "-Xms16m", "-Xmx64m", "-cp", System.getProperty("java.class.path"), Child.class.getName(), "wait").inheritIO().start();
                System.out.println("GRANDCHILD:" + grandchild.pid()); System.out.flush();
                if (args[0].equals("root0-live-child")) System.exit(0);
            }
            while (true) Thread.sleep(1000);
        }
    }
}
