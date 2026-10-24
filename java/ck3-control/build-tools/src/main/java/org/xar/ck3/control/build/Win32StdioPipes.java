package org.xar.ck3.control.build;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.time.Instant;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Private redirected stdio endpoints only. Does not own a process, Job, MCP or Game pipe. */
final class Win32StdioPipes implements AutoCloseable {
    interface Api extends WindowsJobProcess.JobKernel32 {
        boolean ReadFile(HANDLE file, Pointer buffer, int size, Pointer transferred, Pointer overlapped);
        boolean WriteFile(HANDLE file, Pointer buffer, int size, Pointer transferred, Pointer overlapped);
        boolean ConnectNamedPipe(HANDLE pipe, Pointer overlapped);
        boolean GetOverlappedResult(HANDLE file, Pointer overlapped, IntByReference transferred, boolean wait);
        boolean CancelIoEx(HANDLE file, Pointer overlapped);
        boolean GetNamedPipeClientProcessId(HANDLE pipe, IntByReference pid);
    }
    private static final int PENDING = 997, CONNECTED = 535, NOT_FOUND = 1168;
    private static final int BROKEN = 109, NO_DATA = 232, NOT_CONNECTED = 233;
    private static final int WAIT_TIMEOUT = 258, WAIT_FAILED = -1;
    private static final int CHUNK = 65_536;
    private record Budget(Instant deadline, long monotonicDeadline) {
        static Budget start(Instant deadline) throws IOException {
            Duration remaining = Duration.between(Instant.now(), deadline);
            if (remaining.isNegative() || remaining.isZero() || remaining.compareTo(Duration.ofDays(1)) > 0)
                throw new IOException("finite stdio deadline within one day required");
            return new Budget(deadline, System.nanoTime() + remaining.toNanos());
        }
        void verify(WindowsJobProcess.StdioGuard guard) throws IOException {
            if (System.nanoTime() - monotonicDeadline >= 0) throw new IOException("owned stdio monotonic timeout");
            check(deadline, guard);
            if (System.nanoTime() - monotonicDeadline >= 0) throw new IOException("owned stdio monotonic timeout during guard");
        }
    }
    /* Never free a native buffer while its OVERLAPPED may still be in use by Windows. */
    private static final List<PendingBuffer> UNSETTLED = new ArrayList<>();
    private record PendingBuffer(Api api, Memory memory, WinBase.OVERLAPPED overlapped, HANDLE event) { }
    private final Api api;
    private final Endpoint input;
    private final Endpoint output;
    private boolean closed;

    private static final class Endpoint {
        final HANDLE parent;
        HANDLE inherited;
        Endpoint(HANDLE parent, HANDLE inherited) { this.parent = parent; this.inherited = inherited; }
    }
    private Win32StdioPipes(Api api, Endpoint input, Endpoint output) {
        this.api = api; this.input = input; this.output = output;
    }
    Api api() { return api; }
    HANDLE childInput() { return input.inherited; }
    HANDLE childOutput() { return output.inherited; }

    static Win32StdioPipes create(Instant deadline, WindowsJobProcess.StdioGuard guard) throws IOException {
        reap();
        synchronized (UNSETTLED) {
            if (!UNSETTLED.isEmpty()) throw new IOException("previous stdio cancellation remains unobserved");
        }
        Api api = Native.load("kernel32", Api.class, W32APIOptions.UNICODE_OPTIONS);
        Endpoint input = null;
        try {
            input = endpoint(api, true, deadline, guard);
            Endpoint output = endpoint(api, false, deadline, guard);
            return new Win32StdioPipes(api, input, output);
        } catch (IOException | RuntimeException failure) {
            if (input != null) closeEndpoint(api, input);
            throw failure;
        }
    }

    private static Endpoint endpoint(Api api, boolean input, Instant deadline,
            WindowsJobProcess.StdioGuard guard) throws IOException {
        check(deadline, guard);
        String name = "\\\\.\\pipe\\xar-owned-stdio-" + UUID.randomUUID();
        // Overlapped parent, synchronous inheritable child. These are private stdio handles,
        // unrelated to the existing NativeNamedPipeServer/CK3 connection.
        HANDLE server = api.CreateNamedPipe(name, (input ? 2 : 1) | 0x40000000 | 0x00080000,
                0x8, 1, CHUNK, CHUNK, 0, null);
        valid(server, "create stdio pipe");
        HANDLE client = null;
        try {
            WinBase.SECURITY_ATTRIBUTES inherited = new WinBase.SECURITY_ATTRIBUTES();
            inherited.bInheritHandle = true;
            client = api.CreateFile(name, input ? WinNT.GENERIC_READ : WinNT.GENERIC_WRITE,
                    0, inherited, 3, 0x80, null);
            valid(client, "open own stdio client");
            HANDLE event = api.CreateEvent(null, true, false, null); valid(event, "stdio connect event");
            try {
                WinBase.OVERLAPPED overlap = new WinBase.OVERLAPPED(); overlap.hEvent = event; overlap.write();
                boolean connected = api.ConnectNamedPipe(server, overlap.getPointer());
                int error = connected ? 0 : Native.getLastError();
                if (!connected && error != CONNECTED) {
                    if (error != PENDING) throw failure("connect stdio pipe", error);
                    waitPending(api, server, overlap, event, deadline, guard);
                }
                IntByReference pid = new IntByReference();
                if (!api.GetNamedPipeClientProcessId(server, pid)) throw failure("stdio client identity", Native.getLastError());
                if (pid.getValue() != api.GetCurrentProcessId()) throw new IOException("stdio endpoint was not opened by this Root process");
            } finally { if (!retained(event)) api.CloseHandle(event); }
            check(deadline, guard);
            return new Endpoint(server, client);
        } catch (IOException | RuntimeException failure) {
            if (client != null && !WinBase.INVALID_HANDLE_VALUE.equals(client)) api.CloseHandle(client);
            api.CloseHandle(server); throw failure;
        }
    }

    void closeInheritedCopies() {
        closeInherited(input); closeInherited(output);
    }
    private void closeInherited(Endpoint endpoint) {
        if (endpoint.inherited != null) { api.CloseHandle(endpoint.inherited); endpoint.inherited = null; }
    }
    void closeInput() {
        if (!inputClosed) { api.CloseHandle(input.parent); inputClosed = true; }
    }
    private boolean inputClosed;

    int write(byte[] bytes, int offset, int length, Instant deadline, WindowsJobProcess.StdioGuard guard)
            throws IOException, InterruptedException {
        if (closed || inputClosed) throw new IOException("owned stdin is closed");
        return transfer(input.parent, bytes, offset, Math.min(length, CHUNK), false, deadline, guard);
    }
    byte[] read(Instant deadline, WindowsJobProcess.StdioGuard guard) throws IOException, InterruptedException {
        if (closed) throw new IOException("owned stdout is closed");
        byte[] bytes = new byte[CHUNK];
        int count = transfer(output.parent, bytes, 0, bytes.length, true, deadline, guard);
        return count < 0 ? null : java.util.Arrays.copyOf(bytes, count);
    }

    private int transfer(HANDLE handle, byte[] bytes, int offset, int length, boolean read,
            Instant deadline, WindowsJobProcess.StdioGuard guard) throws IOException, InterruptedException {
        Budget budget = Budget.start(deadline); budget.verify(guard);
        Memory memory = new Memory(length);
        HANDLE event = api.CreateEvent(null, true, false, null);
        try { valid(event, "stdio I/O event"); }
        catch (IOException failure) { memory.close(); throw failure; }
        WinBase.OVERLAPPED overlap = new WinBase.OVERLAPPED(); overlap.hEvent = event; overlap.write();
        boolean pending = false, settled = true;
        try {
            if (!read) memory.write(0, bytes, offset, length);
            boolean immediate = read
                    ? api.ReadFile(handle, memory, length, Pointer.NULL, overlap.getPointer())
                    : api.WriteFile(handle, memory, length, Pointer.NULL, overlap.getPointer());
            int error = immediate ? 0 : Native.getLastError();
            if (!immediate) {
                if (read && (error == BROKEN || error == NO_DATA || error == NOT_CONNECTED)) return -1;
                if (error != PENDING) throw failure(read ? "read owned stdout" : "write owned stdin", error);
                pending = true;
                while (true) {
                    budget.verify(guard);
                    if (Thread.interrupted()) throw new InterruptedException("owned stdio interrupted");
                    int wait = api.WaitForSingleObject(event, 20);
                    if (wait == 0) { pending = false; break; }
                    if (wait == WAIT_FAILED) throw failure("stdio event wait", Native.getLastError());
                    if (wait != WAIT_TIMEOUT) throw new IOException("unexpected stdio wait state: " + wait);
                }
            }
            IntByReference count = new IntByReference();
            if (!api.GetOverlappedResult(handle, overlap.getPointer(), count, false)) {
                error = Native.getLastError();
                if (read && (error == BROKEN || error == NO_DATA || error == NOT_CONNECTED)) return -1;
                throw failure("complete owned stdio", error);
            }
            if (count.getValue() < 0 || count.getValue() > length) throw new IOException("invalid native stdio byte count");
            if (read) memory.read(0, bytes, offset, count.getValue());
            budget.verify(guard);
            return count.getValue();
        } finally {
            if (pending) settled = cancel(api, handle, overlap, event);
            if (settled) { api.CloseHandle(event); memory.close(); }
            else synchronized (UNSETTLED) { UNSETTLED.add(new PendingBuffer(api, memory, overlap, event)); }
        }
    }

    private static void waitPending(Api api, HANDLE handle, WinBase.OVERLAPPED overlap, HANDLE event,
            Instant deadline, WindowsJobProcess.StdioGuard guard) throws IOException {
        boolean settled = false;
        Budget budget = Budget.start(deadline);
        try {
            while (true) {
                budget.verify(guard);
                int wait = api.WaitForSingleObject(event, 20);
                if (wait == 0) { settled = true; break; }
                if (wait == WAIT_FAILED) throw failure("stdio connect wait", Native.getLastError());
                if (wait != WAIT_TIMEOUT) throw new IOException("unexpected stdio connect state");
            }
            if (!api.GetOverlappedResult(handle, overlap.getPointer(), new IntByReference(), false))
                throw failure("complete stdio connection", Native.getLastError());
        } finally {
            // Connection is between two handles opened synchronously by this process; a
            // pending result must still be observed before its native structure can die.
            if (!settled && !cancel(api, handle, overlap, event)) {
                synchronized (UNSETTLED) {
                    UNSETTLED.add(new PendingBuffer(api, new Memory(1), overlap, event));
                }
                throw new IOException("stdio connection cancellation did not settle");
            }
        }
    }

    private static boolean cancel(Api api, HANDLE handle, WinBase.OVERLAPPED overlap, HANDLE event) {
        boolean called = api.CancelIoEx(handle, overlap.getPointer());
        int error = called ? 0 : Native.getLastError();
        if (!called && error != NOT_FOUND) return false;
        return api.WaitForSingleObject(event, 5000) == 0;
    }
    static void check(Instant deadline, WindowsJobProcess.StdioGuard guard) throws IOException {
        if (!Instant.now().isBefore(deadline)) throw new IOException("owned stdio deadline expired");
        guard.verify();
        if (!Instant.now().isBefore(deadline)) throw new IOException("owned stdio deadline expired during guard");
    }
    private static void valid(HANDLE handle, String operation) throws IOException {
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw failure(operation, Native.getLastError());
    }
    private static IOException failure(String operation, int error) { return new IOException(operation + " Win32=" + error); }
    private static void closeEndpoint(Api api, Endpoint endpoint) {
        if (endpoint.inherited != null) api.CloseHandle(endpoint.inherited);
        api.CloseHandle(endpoint.parent);
    }
    private static void reap() {
        synchronized (UNSETTLED) {
            UNSETTLED.removeIf(pending -> {
                if (pending.api().WaitForSingleObject(pending.event(), 0) != 0) return false;
                pending.api().CloseHandle(pending.event()); pending.memory().close(); return true;
            });
        }
    }
    private static boolean retained(HANDLE event) {
        synchronized (UNSETTLED) { return UNSETTLED.stream().anyMatch(pending -> pending.event().equals(event)); }
    }
    boolean settled() { reap(); synchronized (UNSETTLED) { return UNSETTLED.isEmpty(); } }
    @Override public void close() {
        if (closed) return;
        closeInput(); closeInheritedCopies(); api.CloseHandle(output.parent); closed = true; reap();
    }
}
