package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Shell32Util;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
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
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class WindowsJobProcessTest {
    @TempDir Path temporary;
    private enum DrainFailure { COMMAND_TIMEOUT, LEASE_EXPIRED, GUARD, INTERRUPTED }
    public record DetachedArgv(String mode, List<String> nativeArguments,
            List<String> launcherArguments, String nativeEncoding) {
        public DetachedArgv {
            if (!"detached-argv".equals(mode)) throw new IllegalArgumentException("Exact detached argv mode required");
            nativeArguments = List.copyOf(nativeArguments); launcherArguments = List.copyOf(launcherArguments);
            if (nativeEncoding == null || nativeEncoding.isBlank()) throw new IllegalArgumentException("Observed native encoding required");
        }
    }
    public interface CommandLineKernel32 extends StdCallLibrary { Pointer GetCommandLineW(); }

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
                assertActuallyExitedChild(retained, 125);
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
                assertActuallyExitedChild(retained, 125);
            }
        }
    }

    @Test void explicitDeadlineDrainObservesRealChildAliveBeyondFiveSecondsThenItsNaturalExit() throws Exception {
        Path output = temporary.resolve("root0-natural.stdout");
        Path gate = temporary.resolve("natural-child.start");
        Path sidecar = temporary.resolve("natural-child.job-members.json");
        try (WindowsJobProcess owner = WindowsJobProcess.start(spec("root0-natural-child", output, List.of(gate.toString())))) {
            long childPid = awaitLiveChildPid(output);
            try (WindowsJobProcess.ReadOnlyProcessHandle retained = WindowsJobProcess.retainReadOnlyProcess(childPid)) {
                assertEquals(258, retained.waitZero());
                awaitRootExit(owner);
                long rootExitObserved = System.nanoTime();
                Files.createFile(gate); // Only after the original root handle actually reports exit.
                AtomicBoolean liveBeyondFiveSeconds = new AtomicBoolean();
                WindowsJobProcess.AwaitResult awaited = owner.await(Duration.ofSeconds(20), Instant.now().plusSeconds(25),
                        () -> {
                            if (System.nanoTime() - rootExitObserved >= Duration.ofSeconds(5).toNanos()
                                    && retained.waitZero() == 258) liveBeyondFiveSeconds.set(true);
                        }, sidecar, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE);
                assertTrue(liveBeyondFiveSeconds.get(), "the same child handle must actually remain live beyond the default drain window");
                assertEquals(0, awaited.commandResult().exitCode()); assertNull(awaited.commandResult().stopReason());
                assertEquals(0, awaited.commandResult().accounting().activeProcesses()); assertTrue(awaited.commandResult().passed());
                assertEquals(WindowsJobProcess.DiagnosticWriteState.NOT_NEEDED, awaited.diagnostic().state());
                assertNull(awaited.diagnostic().sidecarRef()); assertFalse(Files.exists(sidecar));
                assertActuallyExitedChild(retained, 0); // Natural exit, never either owned-Job kill code.
            }
        }
    }

    @Test void explicitDeadlineDrainKeepsExpiredCommandLeaseGuardAndInterruptFailuresAfterActualRootExit() throws Exception {
        for (DrainFailure mode : DrainFailure.values()) {
            Path output = temporary.resolve("root0-policy-" + mode + ".stdout");
            try (WindowsJobProcess owner = WindowsJobProcess.start(spec("root0-live-child", output))) {
                long childPid = awaitLiveChildPid(output);
                try (WindowsJobProcess.ReadOnlyProcessHandle retained = WindowsJobProcess.retainReadOnlyProcess(childPid)) {
                    assertEquals(258, retained.waitZero()); awaitRootExit(owner);
                    Duration timeout = mode == DrainFailure.COMMAND_TIMEOUT ? Duration.ofNanos(1) : Duration.ofSeconds(8);
                    Instant lease = mode == DrainFailure.LEASE_EXPIRED ? Instant.now().minusNanos(1) : Instant.now().plusSeconds(12);
                    AtomicInteger guardCalls = new AtomicInteger();
                    try {
                        if (mode == DrainFailure.INTERRUPTED) Thread.currentThread().interrupt();
                        WindowsJobProcess.AwaitResult awaited = owner.await(timeout, lease, () -> {
                            guardCalls.incrementAndGet();
                            if (mode == DrainFailure.GUARD) throw new IllegalStateException("actual post-root drain guard rejected");
                        }, null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE);
                        String reason = switch (mode) {
                            case COMMAND_TIMEOUT, LEASE_EXPIRED -> "timeout_or_release_expired";
                            case GUARD -> "periodic_guard: actual post-root drain guard rejected";
                            case INTERRUPTED -> "interrupted";
                        };
                        assertEquals(0, awaited.commandResult().exitCode()); assertEquals(reason, awaited.commandResult().stopReason());
                        assertFalse(awaited.commandResult().passed()); assertEquals(0, awaited.commandResult().accounting().activeProcesses());
                        assertEquals(WindowsJobProcess.DiagnosticWriteState.NOT_REQUESTED, awaited.diagnostic().state());
                        if (mode == DrainFailure.COMMAND_TIMEOUT || mode == DrainFailure.LEASE_EXPIRED) assertEquals(0, guardCalls.get());
                        else assertTrue(guardCalls.get() > 0);
                        if (mode == DrainFailure.INTERRUPTED) assertTrue(Thread.currentThread().isInterrupted());
                        Thread.interrupted();
                        assertActuallyExitedChild(retained, 124);
                    } finally { Thread.interrupted(); }
                }
            }
        }
    }

    @Test void detachedJavaIsTheOnlyOwnedMemberAndPreservesCompleteOutputAndArguments() throws Exception {
        Path output = temporary.resolve("detached-argv.stdout");
        Path gate = temporary.resolve("detached-argv.release");
        List<String> expected = List.of("", "value with spaces", "中文 Ω", "\"quoted\"", "trailing\\", "slash\\\"mix");
        List<String> childArguments = new ArrayList<>(List.of(gate.toString())); childArguments.addAll(expected);
        WindowsJobProcess.CommandSpec command = spec("detached-argv", output, childArguments);
        try (WindowsJobProcess owner = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.DETACHED);
                WindowsJobProcess.ReadOnlyProcessHandle retained = WindowsJobProcess.retainReadOnlyProcess(owner.identity().pid())) {
            DetachedArgv actual = awaitDetachedArgv(output);
            assertEquals("detached-argv", actual.mode()); assertEquals(expected, actual.nativeArguments());
            assertEquals(expected.size(), actual.launcherArguments().size());
            for (int index = 0; index < expected.size(); index++) {
                if (expected.get(index).codePoints().allMatch(value -> value < 128))
                    assertEquals(expected.get(index), actual.launcherArguments().get(index));
            }
            assertEquals(owner.identity(), retained.identity()); assertEquals(258, retained.waitZero()); assertEquals(259, retained.exitCode());
            WindowsJobProcess.Accounting live = owner.accounting();
            assertEquals(1, live.activeProcesses(), "the live assigned Java root must be the one and only actual Job member");
            assertEquals(WindowsJobProcess.REQUIRED_FLAGS, live.limitFlags());
            assertEquals(command.memoryLimitBytes(), live.memoryLimitBytes());
            System.out.println("DETACHED_ONLY_MEMBER pid=" + owner.identity().pid() + " birth="
                    + owner.identity().creationFiletimeDecimal() + " active=" + live.activeProcesses());
            Files.createFile(gate);
            WindowsJobProcess.CommandResult terminal = owner.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            assertTrue(terminal.passed()); assertEquals(0, terminal.exitCode()); assertNull(terminal.stopReason());
            assertEquals(0, terminal.accounting().activeProcesses()); assertActuallyExitedChild(retained, 0);
            assertEquals(actual, ControlBuild.strictMapper().readValue(Files.readAllBytes(output), DetachedArgv.class));
            assertTrue(Files.readString(command.stderr()).contains("DETACHED_STDERR_OK"));
        }
    }

    @Test void detachedTimeoutLeaseGuardAndInterruptRetainActualTerminalAndJobZero() throws Exception {
        for (DrainFailure mode : DrainFailure.values()) {
            Path output = temporary.resolve("detached-failure-" + mode + ".stdout");
            Path sidecar = temporary.resolve("detached-failure-" + mode + ".job-members.json");
            try (WindowsJobProcess owner = WindowsJobProcess.start(spec("wait", output), WindowsJobProcess.ConsoleMode.DETACHED);
                    WindowsJobProcess.ReadOnlyProcessHandle retained = WindowsJobProcess.retainReadOnlyProcess(owner.identity().pid())) {
                assertEquals(258, retained.waitZero()); assertEquals(1, owner.accounting().activeProcesses());
                Duration timeout = mode == DrainFailure.COMMAND_TIMEOUT ? Duration.ofNanos(1) : Duration.ofSeconds(8);
                Instant lease = mode == DrainFailure.LEASE_EXPIRED ? Instant.now().minusNanos(1) : Instant.now().plusSeconds(12);
                AtomicInteger guards = new AtomicInteger();
                try {
                    if (mode == DrainFailure.INTERRUPTED) Thread.currentThread().interrupt();
                    WindowsJobProcess.AwaitResult awaited = owner.await(timeout, lease, () -> {
                        guards.incrementAndGet();
                        if (mode == DrainFailure.GUARD) throw new IllegalStateException("detached actual guard rejected");
                    }, sidecar);
                    String reason = switch (mode) {
                        case COMMAND_TIMEOUT, LEASE_EXPIRED -> "timeout_or_release_expired";
                        case GUARD -> "periodic_guard: detached actual guard rejected";
                        case INTERRUPTED -> "interrupted";
                    };
                    assertEquals(reason, awaited.commandResult().stopReason()); assertFalse(awaited.commandResult().passed());
                    assertEquals(0, awaited.commandResult().accounting().activeProcesses());
                    assertEquals(WindowsJobProcess.DiagnosticWriteState.WRITTEN, awaited.diagnostic().state());
                    awaited.diagnostic().sidecarRef().verify();
                    WindowsJobProcess.JobDiagnostic observed = ControlBuild.strictMapper().readValue(Files.readAllBytes(sidecar), WindowsJobProcess.JobDiagnostic.class);
                    assertEquals(WindowsJobProcess.JobListState.COMPLETE, observed.listState()); assertEquals(1, observed.members().size());
                    assertEquals(1, observed.accounting().activeProcesses()); assertEquals(owner.identity(), observed.members().getFirst().identity());
                    assertEquals(Boolean.TRUE, observed.members().getFirst().inOwnedJob());
                    if (mode == DrainFailure.COMMAND_TIMEOUT || mode == DrainFailure.LEASE_EXPIRED) assertEquals(0, guards.get());
                    else assertTrue(guards.get() > 0);
                    if (mode == DrainFailure.INTERRUPTED) assertTrue(Thread.currentThread().isInterrupted());
                    Thread.interrupted(); assertActuallyExitedChild(retained, 124);
                } finally { Thread.interrupted(); }
            }
        }
    }

    private static DetachedArgv awaitDetachedArgv(Path output) throws Exception {
        long deadline = System.nanoTime() + Duration.ofSeconds(10).toNanos();
        while (System.nanoTime() - deadline < 0) {
            if (Files.isRegularFile(output) && Files.readString(output).endsWith("\n"))
                return ControlBuild.strictMapper().readValue(Files.readAllBytes(output), DetachedArgv.class);
            Thread.sleep(10);
        }
        throw new AssertionError("actual detached child output was not fully observed");
    }

    private static void awaitRootExit(WindowsJobProcess owner) throws InterruptedException {
        long deadline = System.nanoTime() + Duration.ofSeconds(8).toNanos();
        while (owner.isRunning() && System.nanoTime() - deadline < 0) Thread.sleep(10);
        assertFalse(owner.isRunning(), "original owned root handle must actually report exit before the child gate opens");
    }

    /** Job accounting zero and each process object's signal are independent native observations. */
    private static void assertActuallyExitedChild(WindowsJobProcess.ReadOnlyProcessHandle retained, long expectedExit) throws InterruptedException {
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
        assertEquals(expectedExit, retained.exitCode());
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
                output.resolveSibling(output.getFileName() + ".stderr").toAbsolutePath(), 256L * 1024 * 1024);
    }

    public static final class Child {
        private Child() {}
        public static void main(String[] args) throws Exception {
            if (args[0].equals("detached-argv")) {
                if (args.length < 2) throw new IllegalArgumentException("One explicit detached release gate required");
                Path gate = Path.of(args[1]);
                // JDK-8337506: Java 21 projects Windows argv through the ANSI code page.
                // Observe CreateProcessW's UTF-16 arguments directly and retain that projection separately.
                var api = Native.load("kernel32", CommandLineKernel32.class, W32APIOptions.UNICODE_OPTIONS);
                List<String> nativeWords = List.of(Shell32Util.CommandLineToArgv(api.GetCommandLineW().getWideString(0)));
                int mainClass = nativeWords.indexOf(Child.class.getName());
                if (mainClass < 1 || nativeWords.lastIndexOf(Child.class.getName()) != mainClass)
                    throw new IllegalStateException("Unique actual Java main class argument required");
                List<String> nativeMain = nativeWords.subList(mainClass + 1, nativeWords.size());
                if (nativeMain.size() != args.length || !nativeMain.get(0).equals(args[0]) || !nativeMain.get(1).equals(args[1]))
                    throw new IllegalStateException("Native main arguments differ from the actual child invocation");
                var actual = new DetachedArgv("detached-argv", nativeMain.subList(2, nativeMain.size()),
                        List.of(args).subList(2, args.length), System.getProperty("native.encoding"));
                System.out.write(ControlBuild.strictMapper().writeValueAsBytes(actual));
                System.out.write('\n'); System.out.flush();
                System.err.write("DETACHED_STDERR_OK\n".getBytes(java.nio.charset.StandardCharsets.UTF_8)); System.err.flush();
                long deadline = System.nanoTime() + Duration.ofSeconds(20).toNanos();
                while (!Files.isRegularFile(gate)) {
                    if (System.nanoTime() - deadline >= 0) throw new IllegalStateException("Detached child release gate never opened");
                    Thread.sleep(10);
                }
                System.exit(0);
            }
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
            if (args[0].equals("natural-child")) {
                if (args.length != 2) throw new IllegalArgumentException("One actual natural-child start gate required");
                Path gate = Path.of(args[1]); long gateDeadline = System.nanoTime() + Duration.ofSeconds(20).toNanos();
                while (!Files.isRegularFile(gate)) {
                    if (System.nanoTime() - gateDeadline >= 0) throw new IllegalStateException("Natural-child gate never opened");
                    Thread.sleep(10);
                }
                long exitDeadline = System.nanoTime() + Duration.ofMillis(6_500).toNanos();
                while (System.nanoTime() - exitDeadline < 0) Thread.sleep(25);
                System.exit(0);
            }
            if (args[0].equals("tree") || args[0].equals("root0-live-child") || args[0].equals("root0-natural-child")) {
                boolean natural = args[0].equals("root0-natural-child");
                List<String> command = new ArrayList<>(List.of(Path.of(System.getProperty("java.home"), "bin/java.exe").toString(),
                        "-Xms16m", "-Xmx64m", "-cp", System.getProperty("java.class.path"), Child.class.getName(), natural ? "natural-child" : "wait"));
                if (natural) {
                    if (args.length != 2) throw new IllegalArgumentException("One exact child start gate required");
                    command.add(args[1]);
                }
                Process grandchild = new ProcessBuilder(command).inheritIO().start();
                System.out.println("GRANDCHILD:" + grandchild.pid()); System.out.flush();
                if (!args[0].equals("tree")) System.exit(0);
            }
            while (true) Thread.sleep(1000);
        }
    }
}
