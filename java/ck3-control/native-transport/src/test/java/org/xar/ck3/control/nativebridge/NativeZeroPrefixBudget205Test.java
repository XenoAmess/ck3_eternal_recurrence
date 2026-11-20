package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Modifier;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** NoGame regression: actual budget code and byte reader; software pipe and synthetic budgets only. */
public final class NativeZeroPrefixBudget205Test {
    @Test void actualMonotonicExpiryKeepsTheEarlierUtcObservationWithoutInventingWallTime() throws Exception {
        Instant original = Instant.now().plusSeconds(60);
        Object budget = budget(original, System.nanoTime() - 1_000_000_000L);
        NativePipeEndpoint.WaitDeadlineElapsed actual = elapsed(budget);
        assertNotNull(actual);
        assertTrue(actual.monotonicExpired());
        assertTrue(actual.observedAt().isBefore(original));
        var result = new NativePacketPort.Elapsed(original, actual.observedAt(), actual);
        assertEquals(original, result.waitUntil());
        assertEquals(actual.observedAt(), result.observedAt());
        assertSame(actual, result.budgetObservation());
        assertThrows(IllegalArgumentException.class,
                () -> new NativePacketPort.Elapsed(original, actual.observedAt()));
    }

    @Test void noExpiryCannotMintEvidenceAndMismatchedOriginalsCannotReuseIt() throws Exception {
        Instant original = Instant.now().plusSeconds(60);
        assertNull(elapsed(budget(original, System.nanoTime() + 60_000_000_000L)));
        var actual = elapsed(budget(original, System.nanoTime() - 1_000_000_000L));
        assertNotNull(actual);
        assertThrows(IllegalArgumentException.class,
                () -> new NativePacketPort.Elapsed(original.plusSeconds(1), actual.observedAt(), actual));
        assertThrows(IllegalArgumentException.class,
                () -> new NativePacketPort.Elapsed(original, actual.observedAt().plusNanos(1), actual));
        assertThrows(IllegalArgumentException.class,
                () -> new NativePacketPort.Elapsed(original, actual.observedAt(), null));
        for (var constructor : NativePipeEndpoint.WaitDeadlineElapsed.class.getDeclaredConstructors())
            assertTrue(Modifier.isPrivate(constructor.getModifiers()), "no arbitrary expiration constructor");
        for (var method : NativePipeEndpoint.WaitDeadlineElapsed.class.getDeclaredMethods())
            assertFalse(Modifier.isPublic(method.getModifiers()), "no public expiration factory");
    }

    @Test void captureBudgetStillRejectsActualMonotonicExpiryWithItsOriginalDeadline() throws Exception {
        Instant original = Instant.now().plusSeconds(60);
        Object budget = budget(original, System.nanoTime() - 1_000_000_000L);
        var verify = budget.getClass().getDeclaredMethod("verify");
        verify.setAccessible(true);
        var thrown = assertThrows(InvocationTargetException.class, () -> verify.invoke(budget));
        var expired = assertInstanceOf(NativePacketPort.DeadlineExpired.class, thrown.getCause());
        assertEquals(original, expired.observation().suppliedDeadline());
        assertTrue(expired.observation().monotonicExpired());
        assertTrue(expired.observation().observedAt().isBefore(original));
    }

    @Test void actualZeroPrefixElapsedDoesNotPoisonOrConsumeAnAlreadyQueuedPrefix() throws Exception {
        Pipe api = new Pipe();
        try (var endpoint = endpoint(api)) {
            Instant wait = Instant.now().minusMillis(1);
            var elapsed = assertInstanceOf(NativePacketPort.Elapsed.class, endpoint.readPacketUntil(wait, deadline()));
            assertEquals(wait, elapsed.waitUntil());
            assertFalse(elapsed.observedAt().isBefore(wait));
            assertNotNull(elapsed.budgetObservation());
            assertEquals(0, api.readCalls);
            endpoint.verify();
            byte[] original = packet();
            api.add(original);
            assertInstanceOf(NativePacketPort.Elapsed.class,
                    endpoint.readPacketUntil(Instant.now().minusMillis(1), deadline()));
            assertEquals(0, api.readCalls);
            var received = assertInstanceOf(NativePacketPort.Packet.class,
                    endpoint.readPacketUntil(Instant.now().plusSeconds(1), deadline()));
            assertArrayEquals(original, received.originalPacket());
            assertEquals(0, api.writes);
            assertEquals(0, endpoint.retainedFailureBytes().length);
        }
    }

    @Test void startedPrefixUsesOriginalCaptureAndPartialCaptureFailureNeverBecomesElapsed() throws Exception {
        byte[] original = packet();
        for (int prefix : new int[] {2, 4}) {
            Pipe api = new Pipe();
            api.maximumChunk = 2;
            api.add(Arrays.copyOf(original, prefix));
            try (var endpoint = endpoint(api)) {
                Instant wait = Instant.now().plusMillis(250);
                api.releaseAt = wait.plusMillis(30);
                api.delayed = Arrays.copyOfRange(original, prefix, original.length);
                var received = assertInstanceOf(NativePacketPort.Packet.class,
                        endpoint.readPacketUntil(wait, wait.plusSeconds(3)));
                assertFalse(Instant.now().isBefore(wait));
                assertArrayEquals(original, received.originalPacket());
                assertEquals(0, api.writes);
                endpoint.verify();
            }
        }
        for (int prefix : new int[] {2, 5}) {
            Pipe api = new Pipe();
            byte[] partial = Arrays.copyOf(original, prefix);
            api.add(partial);
            try (var endpoint = endpoint(api)) {
                Instant wait = Instant.now().plusMillis(250);
                var failure = assertThrows(NativePipeEndpoint.TransferFailure.class,
                        () -> endpoint.readPacketUntil(wait, wait.plusMillis(250)));
                assertArrayEquals(partial, failure.retainedBytes());
                assertArrayEquals(partial, endpoint.retainedFailureBytes());
                assertFalse(failure.writeAttempted());
                assertEquals(0, failure.writtenBytes());
                assertThrows(IOException.class, endpoint::verify);
                assertEquals(0, api.writes);
            }
        }
    }

    @Test void actualIoIdentityAndPartialInterruptionRemainFailures() throws Exception {
        Pipe broken = new Pipe();
        broken.failPeek = true;
        try (var endpoint = endpoint(broken)) {
            var failure = assertThrows(NativePipeEndpoint.TransferFailure.class,
                    () -> endpoint.readPacketUntil(Instant.now().plusSeconds(1), deadline()));
            assertEquals(0, failure.retainedBytes().length);
            assertThrows(IOException.class, endpoint::verify);
        }
        Pipe source = new Pipe();
        try (var endpoint = endpoint(source)) {
            source.guardFailure = new IOException("Native transport deadline expired");
            assertThrows(IOException.class,
                    () -> endpoint.readPacketUntil(Instant.now().minusMillis(1), deadline()));
            assertEquals(0, source.readCalls);
        }
        Pipe foreign = new Pipe();
        try (var endpoint = endpoint(foreign)) {
            foreign.pid = 43;
            assertThrows(IOException.class,
                    () -> endpoint.readPacketUntil(Instant.now().minusMillis(1), deadline()));
            assertEquals(0, foreign.readCalls);
        }
        Pipe interrupted = new Pipe();
        interrupted.maximumChunk = 2;
        interrupted.interruptAfter = 2;
        byte[] partial = Arrays.copyOf(packet(), 2);
        interrupted.add(partial);
        try (var endpoint = endpoint(interrupted)) {
            try {
                var failure = assertThrows(NativePacketPort.ReadInterrupted.class,
                        () -> endpoint.readPacketUntil(Instant.now().plusSeconds(1), deadline()));
                assertArrayEquals(partial, failure.originalPartialPacket());
                assertArrayEquals(partial, endpoint.retainedFailureBytes());
                assertThrows(IOException.class, endpoint::verify);
            } finally { Thread.interrupted(); }
        }
    }

    private static Object budget(Instant original, long monotonicEnd) throws Exception {
        Class<?> type = Class.forName(NativePipeEndpoint.class.getName() + "$Budget");
        var constructor = type.getDeclaredConstructor(Instant.class, long.class);
        constructor.setAccessible(true);
        return constructor.newInstance(original, monotonicEnd);
    }
    private static NativePipeEndpoint.WaitDeadlineElapsed elapsed(Object budget) throws Exception {
        var method = budget.getClass().getDeclaredMethod("elapsed");
        method.setAccessible(true);
        return (NativePipeEndpoint.WaitDeadlineElapsed) method.invoke(budget);
    }
    private static Instant deadline() { return Instant.now().plusSeconds(5); }
    private static byte[] packet() {
        return ByteBuffer.allocate(6).order(ByteOrder.LITTLE_ENDIAN).putInt(2).put((byte)'{').put((byte)'}').array();
    }
    private static NativePipeEndpoint endpoint(Pipe api) throws Exception {
        var config = new NativePipeEndpoint.Config("\\\\.\\pipe\\zero-prefix205-fixture", "fixture-machine",
                new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), "fixture-session", "fixture",
                "0".repeat(64), "fixture");
        var endpoint = new NativePipeEndpoint(config, game -> {
            if (api.guardFailure != null) throw api.guardFailure;
        }, api, new HANDLE(Pointer.createConstant(7)));
        endpoint.awaitConnection(deadline());
        return endpoint;
    }
    private static final class Pipe implements NativePipeEndpoint.Api {
        final ArrayDeque<Byte> bytes = new ArrayDeque<>();
        int maximumChunk = 65_536, readBytes, pid = 42, interruptAfter = Integer.MAX_VALUE;
        int readCalls, writes;
        boolean failPeek;
        IOException guardFailure;
        Instant releaseAt;
        byte[] delayed;
        synchronized void add(byte[] original) { for (byte value : original) bytes.addLast(value); }
        public HANDLE CreateNamedPipeW(String n, int o, int m, int i, int out, int in, int t, Pointer s) {
            throw new AssertionError("fixture never creates a native pipe");
        }
        public boolean ConnectNamedPipe(HANDLE p, Pointer o) { return true; }
        public boolean GetNamedPipeClientProcessId(HANDLE p, IntByReference c) { c.setValue(pid); return true; }
        public synchronized boolean PeekNamedPipe(HANDLE p, Pointer b, int s, Pointer r, IntByReference a, Pointer l) {
            if (failPeek) { Native.setLastError(109); return false; }
            if (delayed != null && !Instant.now().isBefore(releaseAt)) { add(delayed); delayed = null; }
            a.setValue(bytes.size()); return true;
        }
        public synchronized boolean ReadFile(HANDLE f, Pointer b, int length, IntByReference r, Pointer o) {
            readCalls++;
            int size = Math.min(Math.min(length, maximumChunk), bytes.size());
            byte[] actual = new byte[size];
            for (int i = 0; i < size; i++) actual[i] = bytes.removeFirst();
            b.write(0, actual, 0, size); r.setValue(size); readBytes += size;
            if (readBytes >= interruptAfter) Thread.currentThread().interrupt();
            return true;
        }
        public boolean WriteFile(HANDLE f, Pointer b, int n, IntByReference w, Pointer o) {
            writes++; throw new AssertionError("snapshot WAIT cannot write");
        }
        public boolean DisconnectNamedPipe(HANDLE p) { return true; }
        public boolean CloseHandle(HANDLE p) { return true; }
    }
}
