package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.sun.jna.Native;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import java.util.WeakHashMap;

/** Actual owned-stdout locator receipt only; no Native classification or authorization. */
public final class NativeServerLocator {
    private static final int MAX_BYTES = 4096;
    private static final WeakHashMap<WindowsJobProcess.OwnedStdio, Boolean> READS = new WeakHashMap<>();
    private NativeServerLocator() { }

    public static Received receive(WindowsJobProcess.OwnedStdio actualOwner, String exactPipeName,
            Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(actualOwner); Objects.requireNonNull(deadline);
        if (exactPipeName == null || exactPipeName.length() > 240
                || !exactPipeName.startsWith("\\\\.\\pipe\\")
                || !exactPipeName.substring(9).matches("[A-Za-z0-9_.-]{1,231}"))
            throw new IOException("exact local pipe name required");
        synchronized (READS) {
            if (READS.putIfAbsent(actualOwner, Boolean.TRUE) != null)
                throw new IOException("locator notification read already attempted; no replay");
        }
        if (!Instant.now().isBefore(deadline) || deadline.isAfter(actualOwner.deadline()))
            throw new IOException("finite locator deadline within original owner deadline required");
        actualOwner.verifyLiveOwner();
        var arrival = actualOwner.readLine(deadline);
        verifyArrival(actualOwner, arrival);
        byte[] raw = arrival.rawBytes();
        if (raw.length < 2 || raw.length > MAX_BYTES || raw[raw.length - 1] != '\n')
            throw new IOException("bounded newline JSON-RPC locator notification required");
        JsonNode root = ControlBuild.strictMapper().readTree(raw);
        fields(root, Set.of("jsonrpc", "method", "params"));
        equalText(root, "jsonrpc", "2.0");
        equalText(root, "method", "notifications/xar/native-server-locator");
        JsonNode params = root.get("params");
        fields(params, Set.of("schema", "pipe_name", "handle_decimal"));
        equalText(params, "schema", "xar.root-native-server-locator/v1");
        equalText(params, "pipe_name", exactPipeName);
        JsonNode handleNode = params.get("handle_decimal");
        if (!handleNode.isTextual()) throw new IOException("handle_decimal must be a canonical unsigned decimal string");
        String handle = handleNode.textValue();
        if (!handle.matches("[1-9][0-9]{0,19}"))
            throw new IOException("canonical nonzero ULONG_PTR decimal required");
        BigInteger value = new BigInteger(handle);
        BigInteger maximum = BigInteger.ONE.shiftLeft(Native.POINTER_SIZE * 8).subtract(BigInteger.ONE);
        if (value.compareTo(maximum) >= 0)
            throw new IOException("valid non-sentinel ULONG_PTR locator required");
        actualOwner.verifyLiveOwner(); verifyArrival(actualOwner, arrival);
        return new Received(actualOwner, arrival, exactPipeName, handle, deadline);
    }

    private static void fields(JsonNode node, Set<String> expected) throws IOException {
        if (node == null || !node.isObject()) throw new IOException("exact locator object required");
        var actual = new HashSet<String>(); node.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(expected)) throw new IOException("locator fields differ: " + actual);
    }
    private static void equalText(JsonNode node, String key, String expected) throws IOException {
        JsonNode value = node.get(key);
        if (value == null || !value.isTextual() || !expected.equals(value.textValue()))
            throw new IOException("locator " + key + " differs");
    }
    private static void verifyArrival(WindowsJobProcess.OwnedStdio owner,
            WindowsJobProcess.Arrival arrival) throws IOException {
        if (!owner.identity().equals(arrival.identity())
                || !owner.sessionNonce().equals(arrival.sessionNonce()) || arrival.sequence() <= 0
                || !owner.deadline().equals(arrival.deadline()))
            throw new IOException("actual locator arrival owner, nonce, sequence or deadline differs");
    }

    public static final class Received {
        private final WindowsJobProcess.OwnedStdio owner;
        private final WindowsJobProcess.Arrival arrival;
        private final String pipeName, handleDecimal;
        private final Instant deadline;
        private WindowsPreloadCustody.Lease boundLease;
        private WindowsPreloadCustody.Endpoint retained;
        private boolean unknown;
        private Received(WindowsJobProcess.OwnedStdio owner, WindowsJobProcess.Arrival arrival,
                String pipeName, String handleDecimal, Instant deadline) {
            this.owner = owner; this.arrival = arrival; this.pipeName = pipeName;
            this.handleDecimal = handleDecimal; this.deadline = deadline;
        }
        public WindowsJobProcess.Arrival arrival() { return arrival; }
        public WindowsJobProcess.ProcessIdentity ownerIdentity() { return arrival.identity(); }
        public String sessionNonce() { return arrival.sessionNonce(); }
        public long sequence() { return arrival.sequence(); }
        public String pipeName() { return pipeName; }
        public String handleDecimal() { return handleDecimal; }
        public byte[] rawBytes() { return arrival.rawBytes(); }
        private void verify() throws IOException {
            if (!Instant.now().isBefore(deadline)) throw new IOException("locator deadline expired");
            owner.verifyLiveOwner(); verifyArrival(owner, arrival);
        }
        public synchronized WindowsPreloadCustody.Endpoint retain(WindowsPreloadCustody.Lease lease)
                throws IOException {
            Objects.requireNonNull(lease);
            if (unknown) throw new IOException("locator retention UNKNOWN; no replay");
            if (boundLease != null && boundLease != lease) {
                unknown = true; throw new IOException("locator is bound to the original same lease");
            }
            boundLease = lease;
            WindowsPreloadCustody.Endpoint candidate = null;
            try {
                verify();
                if (retained != null) { retained.verify(); verify(); return retained; }
                candidate = lease.retainOwnerServer(owner, handleDecimal, pipeName);
                verify(); retained = candidate; return candidate;
            } catch (WindowsPreloadCustody.PipeNotConnected waiting) {
                if (retained != null) {
                    unknown = true; throw new IOException("previous retained endpoint lost its client", waiting);
                }
                try { verify(); }
                catch (IOException | RuntimeException failure) { unknown = true; throw failure; }
                throw waiting;
            } catch (IOException | RuntimeException failure) {
                unknown = true;
                if (candidate != null) try { candidate.close(); }
                catch (IOException cleanup) { failure.addSuppressed(cleanup); }
                throw failure;
            }
        }
    }
}
