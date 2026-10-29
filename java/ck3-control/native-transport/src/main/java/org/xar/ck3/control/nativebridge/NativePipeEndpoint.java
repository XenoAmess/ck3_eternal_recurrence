package org.xar.ck3.control.nativebridge;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Duration;
import java.time.Instant;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Direct Java server for the unchanged C++ DLL client. No subprocess, Python, HTTP or reconnect. */
public final class NativePipeEndpoint implements AutoCloseable, NativePacketPort {
    interface Api extends StdCallLibrary {
        HANDLE CreateNamedPipeW(String name, int openMode, int pipeMode, int instances,
                int outputSize, int inputSize, int defaultTimeout, Pointer securityAttributes);
        boolean ConnectNamedPipe(HANDLE pipe, Pointer overlapped);
        boolean GetNamedPipeClientProcessId(HANDLE pipe, IntByReference clientPid);
        boolean PeekNamedPipe(HANDLE pipe, Pointer buffer, int bufferSize, Pointer bytesRead,
                IntByReference available, Pointer leftInMessage);
        boolean ReadFile(HANDLE file, Pointer buffer, int length, IntByReference read, Pointer overlapped);
        boolean WriteFile(HANDLE file, Pointer buffer, int length, IntByReference written, Pointer overlapped);
        boolean DisconnectNamedPipe(HANDLE pipe);
        boolean CloseHandle(HANDLE handle);
    }
    public record Config(String pipeName, String machineId, GameGeneration game, String sessionId,
            String expectedBridgeVersion, String expectedGameSha256, String expectedAdapterId) {
        public Config {
            Objects.requireNonNull(pipeName); Objects.requireNonNull(game);
            require(pipeName.startsWith("\\\\.\\pipe\\") && pipeName.length() > 9 && pipeName.length() <= 256, "explicit local pipe name required");
            require(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,63}") && !machineId.equals("unknown"), "explicit machine identity required");
            require(sessionId != null && !sessionId.isBlank() && sessionId.length() <= 128, "lifecycle-owned session id required");
            require(expectedBridgeVersion != null && !expectedBridgeVersion.isBlank(), "exact bridge version required");
            require(expectedGameSha256 != null && expectedGameSha256.matches("[a-fA-F0-9]{64}"), "exact Game EXE SHA256 required");
            require(expectedAdapterId != null && !expectedAdapterId.isBlank(), "exact Native adapter id required");
        }
    }
    /** Carries actual byte custody on partial read/write failures; never interpreted as a retry license. */
    public static final class TransferFailure extends IOException {
        private static final long serialVersionUID = 1L;
        private final byte[] retainedBytes;
        private final long writtenBytes;
        private final boolean writeAttempted;
        TransferFailure(String reason, byte[] retainedBytes, long writtenBytes, boolean writeAttempted, Throwable cause) {
            super(reason, cause); this.retainedBytes = retainedBytes.clone(); this.writtenBytes = writtenBytes; this.writeAttempted = writeAttempted;
        }
        public byte[] retainedBytes() { return retainedBytes.clone(); }
        public long writtenBytes() { return writtenBytes; }
        public boolean writeAttempted() { return writeAttempted; }
    }
    private record Budget(Instant deadline, long monotonicEnd) {
        static Budget start(Instant deadline) throws IOException {
            Objects.requireNonNull(deadline);Instant observed=Instant.now();Duration remaining = Duration.between(observed, deadline);
            if(remaining.isZero()||remaining.isNegative())throw new NativePacketPort.DeadlineExpired(
                    new org.xar.ck3.control.application.action.NativeActionPort.DeadlineObservation(deadline,observed,false));
            if (remaining.compareTo(Duration.ofDays(1)) > 0)
                throw new IOException("finite Native deadline within one day required");
            return new Budget(deadline, System.nanoTime() + remaining.toNanos());
        }
        void verify() throws IOException {
            boolean monotonicExpired=System.nanoTime()-monotonicEnd>=0;Instant observed=Instant.now();
            if(monotonicExpired||!observed.isBefore(deadline))throw new NativePacketPort.DeadlineExpired(
                    new org.xar.ck3.control.application.action.NativeActionPort.DeadlineObservation(deadline,observed,monotonicExpired));
        }
        boolean elapsed() { return System.nanoTime() - monotonicEnd >= 0 || !Instant.now().isBefore(deadline); }
        static Budget waitUntil(Instant deadline, Instant captureUntil) throws IOException {
            Objects.requireNonNull(deadline);
            Duration remaining = Duration.between(Instant.now(), deadline);
            if (!deadline.isBefore(captureUntil) || remaining.compareTo(Duration.ofDays(1)) > 0
                    || remaining.compareTo(Duration.ofDays(-1)) < 0)
                throw new IOException("bounded wait deadline strictly before the original capture deadline required");
            return new Budget(deadline, System.nanoTime() + Math.max(0, remaining.toNanos()));
        }
    }
    private static final int NO_DATA = 232, CONNECTED = 535, LISTENING = 536, CHUNK = 65_536;
    private final Config config;
    private final NativeProcessGuard guard;
    private final Api api;
    private final HANDLE pipe;
    private boolean connected;
    private boolean closed;
    private boolean poisoned;
    private NativePacketPort.Disconnection originalDisconnection;
    private byte[] retainedFailureBytes = new byte[0];

    NativePipeEndpoint(Config config, NativeProcessGuard guard, Api api, HANDLE pipe) {
        this.config = config; this.guard = guard; this.api = api; this.pipe = pipe;
    }
    /** Creates exactly one endpoint before injection. It never opens/launches/injects a Game. */
    public static NativePipeEndpoint create(Config config, NativeProcessGuard guard) throws IOException {
        Objects.requireNonNull(config); Objects.requireNonNull(guard); guard.verify(config.game());
        if (!System.getProperty("os.name", "").toLowerCase(Locale.ROOT).startsWith("windows")) throw new IOException("Native named pipes require Windows");
        if (!config.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("Native endpoint machine differs from the current execution machine");
        Api api = Native.load("kernel32", Api.class, W32APIOptions.UNICODE_OPTIONS);
        // DUPLEX | FIRST_PIPE_INSTANCE; BYTE | NOWAIT | REJECT_REMOTE_CLIENTS.
        // Nonblocking native calls plus chunked I/O enforce the caller deadline without orphan OVERLAPPED buffers.
        HANDLE pipe = api.CreateNamedPipeW(config.pipeName(), 0x0000_0003 | 0x0008_0000, 0x0000_0001 | 0x0000_0008,
                1, NativeWire.MAXIMUM_FRAME_BYTES + 4, NativeWire.MAXIMUM_FRAME_BYTES + 4, 0, Pointer.NULL);
        if (pipe == null || WinBase.INVALID_HANDLE_VALUE.equals(pipe)) throw new IOException("CreateNamedPipeW Win32="+Native.getLastError());
        try { guard.verify(config.game()); return new NativePipeEndpoint(config, guard, api, pipe); }
        catch (IOException | RuntimeException failure) { api.CloseHandle(pipe); throw failure; }
    }
    public Config config() { return config; }
    /** Last partial read or attempted write, available even when JSON decoding was impossible. */
    public synchronized byte[] retainedFailureBytes() { return retainedFailureBytes.clone(); }
    @Override public synchronized void verify() throws IOException {
        if (closed || poisoned) throw new IOException("Native endpoint is closed or terminal");
        try {guard.verify(config.game());}
        catch(IOException originalGuardFailure) {
            if(connected) {
                var available=new IntByReference();
                if(!api.PeekNamedPipe(pipe,Pointer.NULL,0,Pointer.NULL,available,Pointer.NULL)) {
                    int code=Native.getLastError();
                    if(pipeLost(code))originalGuardFailure.addSuppressed(nativeFailure("PeekNamedPipe",code));
                }
            }
            throw originalGuardFailure;
        }
        if (connected) {
            IntByReference client = new IntByReference();
            if (!api.GetNamedPipeClientProcessId(pipe, client)) throw win32("GetNamedPipeClientProcessId");
            if (Integer.toUnsignedLong(client.getValue()) != config.game().pid()) throw new IOException("actual Native pipe client PID differs from original Game");
        }
    }
    @Override public synchronized void awaitConnection(Instant deadline) throws IOException, InterruptedException {
        Budget budget = Budget.start(deadline);
        while (!connected) {
            check(budget); boolean result = api.ConnectNamedPipe(pipe, Pointer.NULL);
            int error = result ? 0 : Native.getLastError();
            if (result || error == CONNECTED) { connected = true; verify(); return; }
            if (error != NO_DATA && error != LISTENING) { poisoned = true; throw new IOException("ConnectNamedPipe Win32=" + error); }
            pause(budget);
        }
        check(budget);
    }
    @Override public synchronized byte[] readPacket(Instant deadline) throws IOException, InterruptedException {
        Budget budget = Budget.start(deadline); check(budget);
        if (!connected) throw new IOException("Native endpoint has no authenticated client");
        ByteArrayOutputStream retained = new ByteArrayOutputStream();
        try {
            byte[] header = readExact(4, budget, retained);
            int size = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN).getInt();
            if (size <= 0 || size > NativeWire.MAXIMUM_FRAME_BYTES) throw new IOException("invalid Native length header");
            readExact(size, budget, retained); check(budget); return retained.toByteArray();
        } catch (IOException | RuntimeException failure) {
            retainedFailureBytes = retained.toByteArray();
            if (retained.size() > 0) poisoned = true;
            throw new TransferFailure(failure.getMessage(), retained.toByteArray(), 0, false, failure);
        } catch (InterruptedException interrupted) {
            retainedFailureBytes = retained.toByteArray();
            if (retained.size() > 0) poisoned = true;
            throw new NativePacketPort.ReadInterrupted(retained.toByteArray(), interrupted);
        }
    }
    /** Only this explicit zero-prefix branch produces Elapsed. All actual I/O/identity/partial failures propagate. */
    @Override public synchronized NativePacketPort.WaitResult readPacketUntil(Instant waitUntil, Instant captureUntil)
            throws IOException, InterruptedException {
        Budget capture = Budget.start(captureUntil), wait = Budget.waitUntil(waitUntil, captureUntil);
        check(capture);
        if (!connected) throw new IOException("Native endpoint has no authenticated client");
        ByteArrayOutputStream retained = new ByteArrayOutputStream();
        try {
            // No packet prefix has been consumed here. Once one is available, its complete packet uses capture.
            while (true) {
                check(capture);
                if (wait.elapsed()) {
                    verify(); capture.verify();
                    return new NativePacketPort.Elapsed(waitUntil, Instant.now());
                }
                IntByReference available = new IntByReference();
                if (!api.PeekNamedPipe(pipe, Pointer.NULL, 0, Pointer.NULL, available, Pointer.NULL)) {
                    poisoned = true; throw win32("PeekNamedPipe");
                }
                if (available.getValue() < 0) { poisoned = true; throw new IOException("invalid Native available byte count"); }
                if (available.getValue() > 0) break;
                pause(capture);
            }
            byte[] header = readExact(4, capture, retained);
            int size = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN).getInt();
            if (size <= 0 || size > NativeWire.MAXIMUM_FRAME_BYTES) throw new IOException("invalid Native length header");
            readExact(size, capture, retained); check(capture);
            return new NativePacketPort.Packet(retained.toByteArray());
        } catch (IOException | RuntimeException failure) {
            retainedFailureBytes = retained.toByteArray();
            if (retained.size() > 0) poisoned = true;
            throw new TransferFailure(failure.getMessage(), retained.toByteArray(), 0, false, failure);
        } catch (InterruptedException interrupted) {
            retainedFailureBytes = retained.toByteArray();
            if (retained.size() > 0) poisoned = true;
            throw new NativePacketPort.ReadInterrupted(retained.toByteArray(), interrupted);
        }
    }
    private byte[] readExact(int length, Budget budget, ByteArrayOutputStream retained) throws IOException, InterruptedException {
        byte[] result = new byte[length]; int offset = 0;
        while (offset < length) {
            check(budget); IntByReference available = new IntByReference();
            if (!api.PeekNamedPipe(pipe, Pointer.NULL, 0, Pointer.NULL, available, Pointer.NULL)) { poisoned = true; throw win32("PeekNamedPipe"); }
            int count = Math.min(Math.min(length - offset, CHUNK), available.getValue());
            if (count <= 0) { pause(budget); continue; }
            try (Memory buffer = new Memory(count)) {
                IntByReference received = new IntByReference();
                if (!api.ReadFile(pipe, buffer, count, received, Pointer.NULL)) { poisoned = true; throw win32("ReadFile"); }
                int actual = received.getValue(); if (actual <= 0 || actual > count) { poisoned = true; throw new IOException("invalid Native read byte count"); }
                buffer.read(0, result, offset, actual); retained.write(result, offset, actual); offset += actual;
            }
        }
        return result;
    }
    @Override public synchronized void writePacket(byte[] packet, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(packet); Budget budget = Budget.start(deadline); int offset = 0; boolean attempted = false;
        try {
            check(budget); if (!connected) throw new IOException("Native endpoint has no authenticated client");
            if (packet.length < 5 || packet.length > NativeWire.MAXIMUM_FRAME_BYTES + 4) throw new IOException("bounded Native packet required");
            while (offset < packet.length) {
                check(budget); int length = Math.min(packet.length - offset, CHUNK);
                try (Memory buffer = new Memory(length)) {
                    buffer.write(0, packet, offset, length); IntByReference written = new IntByReference();
                    attempted = true;
                    if (!api.WriteFile(pipe, buffer, length, written, Pointer.NULL)) {
                        int error = Native.getLastError(); int actual = written.getValue();
                        if (actual >= 0 && actual <= length) offset += actual;
                        poisoned = true; throw nativeFailure("WriteFile",error);
                    }
                    int actual = written.getValue();
                    if (actual < 0 || actual > length) { poisoned = true; throw new IOException("invalid Native write byte count"); }
                    offset += actual;
                    if (actual == 0) pause(budget);
                }
            }
            check(budget);
        } catch (IOException | RuntimeException failure) {
            retainedFailureBytes = packet.clone();
            if (attempted && offset < packet.length) poisoned = true;
            throw new TransferFailure(failure.getMessage(), packet, offset, attempted, failure);
        } catch (InterruptedException interrupted) {
            retainedFailureBytes = packet.clone();
            if (attempted && offset < packet.length) poisoned = true;
            throw interrupted;
        }
    }
    private void check(Budget budget) throws IOException, InterruptedException {
        budget.verify(); if (Thread.interrupted()) throw new InterruptedException("Native operation interrupted"); verify(); budget.verify();
    }
    private static void pause(Budget budget) throws IOException, InterruptedException { budget.verify(); Thread.sleep(10); budget.verify(); }
    @Override public synchronized java.util.Optional<NativePacketPort.Disconnection> originalDisconnection(){
        return java.util.Optional.ofNullable(originalDisconnection);
    }
    private static boolean pipeLost(int code){return code==109||code==232||code==233;}
    private NativePacketPort.Disconnection observeDisconnection(String operation,int code,boolean succeeded) {
        if(originalDisconnection==null)originalDisconnection=new NativePacketPort.Disconnection(operation,code,succeeded);
        connected=false;return originalDisconnection;
    }
    private IOException nativeFailure(String operation,int code) {
        if(connected&&pipeLost(code))return new NativePacketPort.ConnectionLost(observeDisconnection(operation,code,false));
        return new IOException(operation+" Win32="+code);
    }
    private IOException win32(String operation) {return nativeFailure(operation,Native.getLastError());}
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
    @Override public synchronized void close() throws IOException {
        if (closed) return;
        boolean wasConnected=connected;
        boolean disconnected = !wasConnected || api.DisconnectNamedPipe(pipe); int disconnectError = disconnected ? 0 : Native.getLastError();
        if(wasConnected&&(disconnected||pipeLost(disconnectError)))
            observeDisconnection("DisconnectNamedPipe",disconnectError,disconnected);
        boolean released = api.CloseHandle(pipe); int closeError = released ? 0 : Native.getLastError();
        if (!released) { poisoned = true; throw new IOException("CloseHandle Native endpoint Win32=" + closeError); }
        closed = true;
        if (!disconnected && !pipeLost(disconnectError)) throw new IOException("DisconnectNamedPipe Win32=" + disconnectError);
    }
}
