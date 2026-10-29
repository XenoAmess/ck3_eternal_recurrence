package org.xar.ck3.control.g2.context;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Protocol engine only. Package fixtures cannot produce a NativeArrival or an owned process capability. */
final class RootMcpExchange {
    interface Port {
        void verify() throws IOException;
        void write(byte[] completeLine, Instant deadline) throws IOException;
        byte[] readLine(Instant deadline) throws IOException;
    }
    enum State { NEW, INITIALIZING, READY, IN_FLIGHT, FAILED, CLOSED }
    record Call(RootMcpWire.ToolResult result, RootMcpWire.OwnerRow row,
            RootMcpWire.JsonBytes originalRpcLine, List<RootMcpWire.JsonBytes> notifications) {
        Call { notifications = List.copyOf(notifications); }
    }
    record Capabilities(RootMcpWire.ToolResult result, RootMcpWire.JsonBytes originalRpcLine,
            List<RootMcpWire.JsonBytes> notifications) {
        Capabilities { notifications = List.copyOf(notifications); }
    }
    record Raw(RootMcpWire.ToolResult result, RootMcpRawWire.Frame frame,
            RootMcpWire.JsonBytes originalRpcLine, List<RootMcpWire.JsonBytes> notifications) {
        Raw { notifications = List.copyOf(notifications); }
    }
    record Failure(String phase, String exceptionType, String message, RootMcpWire.JsonBytes lastFrame,
            long attemptedRequestId, long attemptedRootSequence) { }
    private record Received(RootMcpWire.Response response, List<RootMcpWire.JsonBytes> notifications) { }
    private final Port port;
    private final RootMcpWire.Limits limits;
    private final RootMcpWire.Handshake handshake;
    private State state = State.NEW;
    private long rpcId;
    private long rootSequence;
    private long capabilitiesReads;
    private boolean capabilitiesFinished;
    private boolean capabilitiesSubmittedOnce;
    private byte[] lastFrame = new byte[0];
    private Failure failure;

    RootMcpExchange(Port port, RootMcpWire.Limits limits, RootMcpWire.Handshake handshake) {
        this.port = Objects.requireNonNull(port); this.limits = Objects.requireNonNull(limits); this.handshake = Objects.requireNonNull(handshake);
    }
    synchronized State state() { return state; }
    synchronized Failure failure() { return failure; }
    synchronized RootMcpWire.Initialized initialize(Instant deadline) throws IOException {
        require(state == State.NEW, "MCP initialization is one-shot; unknown initialization cannot be retried");
        state = State.INITIALIZING; lastFrame = new byte[0];
        try {
            long id = nextId(); write(RootMcpWire.initialize(id, handshake), deadline);
            var result = RootMcpWire.initializeResult(receive(id, deadline).response(), handshake);
            write(RootMcpWire.initialized(), deadline); port.verify(); state = State.READY; return result;
        } catch (IOException | RuntimeException error) { fail("initialize", error); throw error; }
    }
    synchronized Call semantic(long sequence, Instant deadline) throws IOException {
        require(state == State.READY, "MCP session is not ready; failed/unknown requests are not replayable");
        require(capabilitiesReads == 0 || capabilitiesFinished, "capabilities observations must be sealed before the first semantic request");
        require(sequence >= 1 && sequence <= StrictJson.MAX_SAFE_INTEGER && sequence > rootSequence, "fresh increasing Root sequence required");
        rootSequence = sequence; state = State.IN_FLIGHT; lastFrame = new byte[0];
        Instant started = Instant.now(); long clock = System.nanoTime();
        try {
            long id = nextId(); write(RootMcpWire.semantic(id), deadline);
            Received received = receive(id, deadline);
            RootMcpWire.ToolResult result = RootMcpWire.toolResult(received.response());
            port.verify(); Instant ended = Instant.now();
            RootMcpWire.OwnerRow row = RootMcpWire.ownerRow(sequence, started, ended, System.nanoTime() - clock, result);
            state = State.READY;
            return new Call(result, row, received.response().originalLine(), received.notifications());
        } catch (IOException | RuntimeException error) { fail("semantic", error); throw error; }
    }
    synchronized Capabilities capabilities(Instant deadline) throws IOException {
        require(!capabilitiesSubmittedOnce, "single CAP submission consumed; no alternate polling entry");
        return readCapabilities(deadline);
    }
    /** CAP can persist Driver state. This latch is consumed before deadline/source checks or the first write. */
    synchronized Capabilities capabilitiesOnce(Instant deadline) throws IOException {
        require(!capabilitiesSubmittedOnce && capabilitiesReads == 0 && state == State.READY && rootSequence == 0 && !capabilitiesFinished,
                "one original CAP submission before semantic; unknown or not-ready CAP cannot be retried");
        capabilitiesSubmittedOnce = true;
        return readCapabilities(deadline);
    }
    private Capabilities readCapabilities(Instant deadline) throws IOException {
        require(state == State.READY && rootSequence == 0 && !capabilitiesFinished,
                "fixed capabilities observations are limited to the initialized bootstrap before any semantic request");
        state = State.IN_FLIGHT; lastFrame = new byte[0];
        try {
            long id = nextId(); write(RootMcpWire.capabilities(id), deadline); Received received = receive(id, deadline);
            RootMcpWire.ToolResult result = RootMcpWire.toolResult(received.response());
            require(!result.isError(), "capabilities bootstrap returned a known tool error; no Native session is admitted");
            RootMcpWire.capabilitiesBody(result); port.verify(); capabilitiesReads++; state = State.READY;
            return new Capabilities(result, received.response().originalLine(), received.notifications());
        } catch (IOException | RuntimeException error) { fail("capabilities", error); throw error; }
    }
    synchronized Raw raw(Instant deadline) throws IOException {
        require(state == State.READY && rootSequence == 0 && capabilitiesReads == 0 && !capabilitiesFinished && !capabilitiesSubmittedOnce,
                "fixed raw observations are limited to initialized pre-CAP preflight");
        state = State.IN_FLIGHT; lastFrame = new byte[0];
        try {
            long id = nextId(); write(RootMcpRawWire.request(id), deadline); Received received = receive(id, deadline);
            RootMcpWire.ToolResult result = RootMcpWire.toolResult(received.response());
            RootMcpRawWire.Frame frame = RootMcpRawWire.decode(result); port.verify(); state = State.READY;
            return new Raw(result, frame, received.response().originalLine(), received.notifications());
        } catch (IOException | RuntimeException error) { fail("raw-preflight", error); throw error; }
    }
    synchronized void finishCapabilities() {
        require(state == State.READY && rootSequence == 0 && capabilitiesReads > 0 && !capabilitiesFinished,
                "only a completed capabilities bootstrap can be sealed once before semantic requests");
        capabilitiesFinished = true;
    }
    synchronized void close() { state = State.CLOSED; }
    private Received receive(long expectedId, Instant deadline) throws IOException {
        List<RootMcpWire.JsonBytes> notifications = new ArrayList<>();
        while (true) {
            current(deadline); port.verify(); lastFrame = port.readLine(deadline).clone(); port.verify();
            RootMcpWire.Message message = RootMcpWire.message(lastFrame, limits);
            if (message instanceof RootMcpWire.Response response) {
                require(response.id().equals(new RootMcpWire.NumberId(expectedId)), "response id differs from the single in-flight request");
                return new Received(response, List.copyOf(notifications));
            }
            if (message instanceof RootMcpWire.ErrorResponse error) {
                require(error.id().equals(new RootMcpWire.NumberId(expectedId)), "error id differs from the single in-flight request");
                throw new IOException("MCP JSON-RPC error " + error.code() + ": " + error.message() + "; no automatic retry");
            }
            require(notifications.size() < limits.maximumNotifications(), "MCP notification/ping budget exhausted");
            if (message instanceof RootMcpWire.Notification notification) { notifications.add(notification.originalLine()); }
            else {
                RootMcpWire.Ping ping = (RootMcpWire.Ping) message; notifications.add(ping.originalLine());
                write(RootMcpWire.pong(ping.id()), deadline);
            }
        }
    }
    private void write(byte[] raw, Instant deadline) throws IOException {
        current(deadline); require(raw.length <= limits.maximumLineBytes(), "outgoing MCP line exceeds finite budget");
        port.verify(); port.write(raw, deadline); port.verify();
    }
    private long nextId() {
        require(rpcId < StrictJson.MAX_SAFE_INTEGER, "MCP request id exhausted"); return ++rpcId;
    }
    private void fail(String phase, Exception error) {
        state = State.FAILED;
        if (failure == null) {
            String message = error.getMessage() == null ? error.getClass().getName() : error.getMessage();
            failure = new Failure(phase, error.getClass().getName(), message,
                    new RootMcpWire.JsonBytes(lastFrame), rpcId, rootSequence);
        }
    }
    private static void current(Instant deadline) throws IOException {
        if (deadline == null || !Instant.now().isBefore(deadline)) { throw new IOException("finite MCP operation deadline expired"); }
    }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
