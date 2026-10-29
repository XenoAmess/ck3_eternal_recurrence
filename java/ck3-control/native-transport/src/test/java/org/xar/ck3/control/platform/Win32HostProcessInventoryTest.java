package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;

/** Controlled Win32 boundary plus an actual read-only current-process observation. No Game owner is minted. */
final class Win32HostProcessInventoryTest {
    private static final String BIRTH = "133700000000000001";
    private static final long PID = 41;
    private static final class Boundary {
        final AtomicInteger waits = new AtomicInteger(), closes = new AtomicInteger(), images = new AtomicInteger();
        int before = 258, after = 258, code = 259;
        boolean imageAvailable = true, timesAvailable = true;
        final String executable = Path.of(System.getProperty("java.home"), "bin", "java.exe").toAbsolutePath().toString();
        final Win32Host.Api api = Win32Host.Api.class.cast(Proxy.newProxyInstance(
                Win32Host.Api.class.getClassLoader(), new Class<?>[]{Win32Host.Api.class}, (proxy, method, arguments) -> {
                    return switch (method.getName()) {
                        case "WaitForSingleObject" -> {
                            int value = waits.getAndIncrement() == 0 ? before : after;
                            if (value == -1) Native.setLastError(6);
                            yield value;
                        }
                        case "GetProcessTimes" -> {
                            if (!timesAvailable) { Native.setLastError(5); yield false; }
                            LongByReference.class.cast(arguments[1]).setValue(Long.parseUnsignedLong(BIRTH));
                            LongByReference.class.cast(arguments[2]).setValue(0);
                            yield true;
                        }
                        case "GetExitCodeProcess" -> {
                            IntByReference.class.cast(arguments[1]).setValue(code); yield true;
                        }
                        case "QueryFullProcessImageNameW" -> {
                            images.incrementAndGet();
                            if (!imageAvailable) { Native.setLastError(31); yield false; }
                            char[] output = char[].class.cast(arguments[2]);
                            executable.getChars(0, executable.length(), output, 0);
                            IntByReference.class.cast(arguments[3]).setValue(executable.length()); yield true;
                        }
                        case "CloseHandle" -> { closes.incrementAndGet(); yield true; }
                        default -> throw new AssertionError("Unexpected native operation " + method.getName());
                    };
                }));
        Win32Host.ReadProcess open() { return new Win32Host.ReadProcess(api, new HANDLE(Pointer.createConstant(7)), PID); }
    }
    private static Win32Host.ProcessInventory inventory(Win32Host.ProcessObservation row) {
        return new Win32Host.ProcessInventory("ck3.exe", "2026-10-24T19:00:00Z", List.of(row));
    }
    @Test void signalZeroAndExit259AreNotRunningEvenWhenImageQueryFailsAndExitTimeIsZero() throws Exception {
        Boundary boundary = new Boundary(); boundary.before = 0; boundary.after = 0; boundary.imageAvailable = false;
        try (var held = boundary.open()) {
            var observed = held.observe(23);
            assertEquals(Win32Host.ProcessState.SIGNALLED, observed.state());
            assertEquals(259L, observed.exitCode().longValue()); assertEquals("0", observed.times().exitFiletimeDecimal());
            assertEquals(BIRTH, observed.times().creationFiletimeDecimal());
            assertNull(observed.executable()); assertEquals(31, observed.failures().getFirst().win32Error().intValue());
            assertEquals(Win32Host.ProcessOperation.IMAGE, observed.failures().getFirst().operation());
            assertTrue(inventory(observed).qualifiedRunning().isEmpty());
            assertThrows(IOException.class, observed::running);
            byte[] json = ControlBuild.strictMapper().writeValueAsBytes(inventory(observed));
            var roundTrip = ControlBuild.strictMapper().readValue(json, Win32Host.ProcessInventory.class);
            assertEquals(inventory(observed), roundTrip);
            assertTrue(new String(json, java.nio.charset.StandardCharsets.UTF_8).contains("\"creation_filetime_decimal\":\"" + BIRTH + "\""));
        }
        assertEquals(2, boundary.waits.get()); assertEquals(1, boundary.closes.get());
    }
    @Test void timeoutWithFullBirthAndActualExecutableSuppliesOnlyReadOnlyRunningIdentity() throws Exception {
        Boundary boundary = new Boundary();
        try (var held = boundary.open()) {
            var observed = held.observe(23);
            assertEquals(Win32Host.ProcessState.RUNNING, observed.state());
            var rows = inventory(observed).qualifiedRunning(); assertEquals(1, rows.size());
            assertEquals(BIRTH, rows.getFirst().identity().creationFiletimeDecimal());
            assertEquals(Path.of(boundary.executable).toRealPath().toString(), rows.getFirst().identity().executable());
        }
    }
    @Test void timeout259WithUnavailableExecutableRemainsUnavailableAndBlocksInventory() throws Exception {
        Boundary boundary = new Boundary(); boundary.imageAvailable = false;
        try (var held = boundary.open()) {
            var observed = held.observe(23); assertEquals(Win32Host.ProcessState.UNAVAILABLE, observed.state());
            assertEquals(259L, observed.exitCode().longValue()); assertThrows(IOException.class, () -> inventory(observed).qualifiedRunning());
        }
    }
    @Test void failedWaitDoesNotUse259ToCreateRunningIdentity() throws Exception {
        Boundary boundary = new Boundary(); boundary.before = -1; boundary.after = -1;
        try (var held = boundary.open()) {
            var observed = held.observe(23); assertEquals(Win32Host.ProcessState.UNAVAILABLE, observed.state());
            assertEquals(0xffff_ffffL, observed.waitAfter().longValue()); assertEquals(259L, observed.exitCode().longValue());
            assertThrows(IOException.class, observed::running);
        }
    }
    @Test void contradictingTimeoutAndExitCodeCannotQualifyEitherTerminalOrRunning() throws Exception {
        Boundary boundary = new Boundary(); boundary.code = 42;
        try (var held = boundary.open()) {
            var observed = held.observe(23); assertEquals(Win32Host.ProcessState.UNAVAILABLE, observed.state());
            assertEquals(42L, observed.exitCode().longValue()); assertThrows(IOException.class, observed::running);
        }
    }
    @Test void exitDuringIdentityObservationIsRetainedAsSignalled() throws Exception {
        Boundary boundary = new Boundary(); boundary.after = 0;
        try (var held = boundary.open()) {
            var observed = held.observe(23); assertEquals(258L, observed.waitBefore().longValue());
            assertEquals(Win32Host.ProcessState.SIGNALLED, observed.state());
            assertTrue(inventory(observed).qualifiedRunning().isEmpty());
        }
    }
    @Test void absentTimesCannotQualifyTimeoutEvenWithAnExecutable() throws Exception {
        Boundary boundary = new Boundary(); boundary.timesAvailable = false;
        try (var held = boundary.open()) {
            var observed = held.observe(23); assertNull(observed.times());
            assertEquals(Win32Host.ProcessState.UNAVAILABLE, observed.state());
            assertThrows(IOException.class, () -> inventory(observed).qualifiedRunning());
        }
    }
    @Test void closedOriginalHandleCannotBeReobservedOrReopened() throws Exception {
        Boundary boundary = new Boundary(); var held = boundary.open(); held.close();
        assertThrows(IOException.class, () -> held.observe(23));
        assertEquals(0, boundary.waits.get()); assertEquals(1, boundary.closes.get());
    }
    @Test void actualCurrentProcessReadBackHasIndependentSignalAndExactImage() throws Exception {
        var current = Win32Host.inspectProcess(ProcessHandle.current().pid(), 0, Instant.now().plusSeconds(5));
        assertEquals(Win32Host.ProcessState.RUNNING, current.state());
        assertEquals(258L, current.waitBefore().longValue()); assertEquals(258L, current.waitAfter().longValue());
        assertEquals(259L, current.exitCode().longValue()); assertTrue(current.failures().isEmpty());
        assertEquals(ProcessHandle.current().pid(), current.running().identity().pid());
    }
}
