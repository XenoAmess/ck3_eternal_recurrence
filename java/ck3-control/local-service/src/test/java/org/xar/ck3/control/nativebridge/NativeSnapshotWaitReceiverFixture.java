package org.xar.ck3.control.nativebridge;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** One test-only software Win32 byte producer shared by native and public consumer tests. */
public final class NativeSnapshotWaitReceiverFixture implements AutoCloseable {
    static final String SHA = "0".repeat(64);
    static final String HELLO = "{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":18446744073709551615,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\"" + SHA + "\",\"game_adapter_id\":\"fixture\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}";
    static final String STATE = "{\"date_raw\":1234,\"speed\":1,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":73,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_settlement\":null,\"played_character_gold\":0,\"played_character_prestige\":0,\"played_character_piety\":0,\"history\":[],\"active_wars\":[],\"player_armies\":[]}";

    private final Pipe api = new Pipe();
    private final NativeGameTransport actual;
    public NativeSnapshotWaitReceiverFixture() throws Exception { this(STATE.getBytes(StandardCharsets.UTF_8)); }
    public NativeSnapshotWaitReceiverFixture(byte[] actualInitialState) throws Exception {
        api.add(packet(HELLO)); api.add(originalSnapshot("first", 7, actualInitialState)); actual = transport(api, 16);
    }
    public NativeGameTransport transport() { return actual; }
    public NativePipeEndpoint.Config configuration() { return config(); }
    public byte[] publishSnapshot(String snapshotId, int revision) throws IOException {
        return publishSnapshot(snapshotId, revision, STATE.getBytes(StandardCharsets.UTF_8));
    }
    public byte[] publishSnapshot(String snapshotId, int revision, byte[] actualState) throws IOException {
        byte[] original = originalSnapshot(snapshotId, revision, actualState); api.add(original); return original.clone();
    }
    private static byte[] originalSnapshot(String snapshotId, int revision, byte[] actualState) throws IOException {
        if (snapshotId == null || !snapshotId.matches("[A-Za-z0-9_.:-]{1,128}") || revision < 0)
            throw new IOException("bounded exact fixture snapshot identity required");
        NativeWire.object(NativeWire.parse(actualState));
        return packet(snapshot(snapshotId, revision, new String(actualState, StandardCharsets.UTF_8)));
    }
    public int actualReadCalls() { return api.readCalls; }
    public int actualWriteCalls() { return api.writes; }
    public void failActualSource(String originalMessage) { api.guardFailure = new IOException(originalMessage); }
    @Override public void close() throws IOException { actual.close(); }

    static String snapshot(String id, int revision, String state) { return "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"" + id + "\",\"revision\":" + revision + ",\"state\":" + state + "}"; }
    static byte[] packet(String json) throws IOException { return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8)); }
    static Instant deadline() { return Instant.now().plusSeconds(5); }
    static NativePipeEndpoint.Config config() { return new NativePipeEndpoint.Config("\\\\.\\pipe\\typed-wait-fixture", "fixture-machine", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), "fixture-session", "fixture", SHA, "fixture"); }
    static NativePipeEndpoint endpoint(Pipe api) throws Exception {
        var endpoint = new NativePipeEndpoint(config(), game -> { if (api.guardFailure != null) throw api.guardFailure; api.guardChecks++; }, api, new HANDLE(Pointer.createConstant(7)));
        endpoint.awaitConnection(deadline()); return endpoint;
    }
    static NativeGameTransport transport(Pipe api, int maximumFrames) throws Exception { return new NativeGameTransport(endpoint(api), config(), maximumFrames, 16); }

    static final class Pipe implements NativePipeEndpoint.Api {
        final ArrayDeque<Byte> bytes = new ArrayDeque<>();
        int maximumChunk = 65_536, readBytes, pid = 42, interruptAfter = Integer.MAX_VALUE;
        volatile int readCalls, writes, guardChecks;
        boolean failPeek;
        boolean allowWrites;
        final ByteArrayOutputStream written = new ByteArrayOutputStream();
        volatile IOException guardFailure;
        Instant releaseAt;
        byte[] delayed;
        synchronized void add(byte[] original) { for (byte value : original) bytes.addLast(value); }
        public HANDLE CreateNamedPipeW(String name, int openMode, int pipeMode, int instances, int output, int input, int timeout, Pointer security) { throw new AssertionError("test never creates an actual native pipe"); }
        public boolean ConnectNamedPipe(HANDLE pipe, Pointer overlapped) { return true; }
        public boolean GetNamedPipeClientProcessId(HANDLE pipe, IntByReference client) { client.setValue(pid); return true; }
        public synchronized boolean PeekNamedPipe(HANDLE pipe, Pointer buffer, int size, Pointer read, IntByReference available, Pointer left) {
            if (failPeek) { Native.setLastError(109); return false; }
            if (delayed != null && !Instant.now().isBefore(releaseAt)) { add(delayed); delayed = null; }
            available.setValue(bytes.size()); return true;
        }
        public synchronized boolean ReadFile(HANDLE file, Pointer buffer, int length, IntByReference read, Pointer overlapped) {
            readCalls++; int size = Math.min(Math.min(length, maximumChunk), bytes.size()); byte[] actual = new byte[size];
            for (int i = 0; i < size; i++) actual[i] = bytes.removeFirst(); buffer.write(0, actual, 0, size); read.setValue(size); readBytes += size;
            if (readBytes >= interruptAfter) Thread.currentThread().interrupt(); return true;
        }
        public synchronized boolean WriteFile(HANDLE file, Pointer buffer, int length, IntByReference count, Pointer overlapped) {
            writes++; if (!allowWrites) throw new AssertionError("snapshot WAIT cannot write a native command");
            written.writeBytes(buffer.getByteArray(0, length)); count.setValue(length); return true;
        }
        public boolean DisconnectNamedPipe(HANDLE pipe) { return true; }
        public boolean CloseHandle(HANDLE pipe) { return true; }
    }
}
