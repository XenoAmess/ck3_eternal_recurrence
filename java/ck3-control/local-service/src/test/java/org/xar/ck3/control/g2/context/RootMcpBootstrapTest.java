package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Software protocol boundaries only. No Native admission, Game tuple or pre-load resource capability is fabricated. */
final class RootMcpBootstrapTest {
    private static final RootMcpWire.Limits LIMITS = new RootMcpWire.Limits(RootMcpEnvelope.RPC_LINE_MAX_BYTES, 8);
    private static final RootMcpWire.Handshake HANDSHAKE = new RootMcpWire.Handshake("2025-11-25", Set.of("2025-11-25"),
            "java-root-bootstrap-test", "1", "software-peer", "1");
    private static final String INITIALIZED = "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"tools\":{}},\"serverInfo\":{\"name\":\"software-peer\",\"version\":\"1\"}}}\n";
    private static final String CAP = "{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"content\":[],\"structuredContent\":{\"software_only\":true}}}\n";
    private static final String SEM = CAP.replace("\"id\":2", "\"id\":3");

    @Test void fixedCapabilitiesBootstrapPrecedesSemanticWithoutInventingARootSequence() throws Exception {
        Port port = new Port(INITIALIZED, CAP, SEM); var exchange = exchange(port); exchange.initialize(deadline());
        var capabilities = exchange.capabilities(deadline()); exchange.finishCapabilities(); var semantic = exchange.semantic(71, deadline());
        assertArrayEquals(bytes(CAP), capabilities.originalRpcLine().bytes());
        assertEquals(4, port.writes.size());
        assertTrue(text(port.writes.get(2)).contains("\"name\":\"ck3_get_capabilities\""));
        assertTrue(text(port.writes.get(3)).contains("\"name\":\"ck3_take_semantic_snapshot_private_v1\""));
        assertTrue(text(port.writes.get(3)).contains("\"id\":3")); assertEquals(71, semantic.row().sequence());
        assertEquals(RootMcpExchange.State.READY, exchange.state());
    }

    @Test void completeCapabilitiesObservationsUseFreshIdsUntilSealedBeforeSemantic() throws Exception {
        String second = CAP.replace("\"id\":2", "\"id\":3");
        String semantic = CAP.replace("\"id\":2", "\"id\":4");
        Port port = new Port(INITIALIZED, CAP, second, semantic); var exchange = exchange(port); exchange.initialize(deadline());
        assertThrows(IllegalArgumentException.class, exchange::finishCapabilities);
        exchange.capabilities(deadline());
        assertThrows(IllegalArgumentException.class, () -> exchange.semantic(1, deadline())); assertEquals(3, port.writes.size());
        var observedAgain = exchange.capabilities(deadline()); assertArrayEquals(bytes(second), observedAgain.originalRpcLine().bytes());
        assertTrue(text(port.writes.get(3)).contains("\"id\":3"));
        exchange.finishCapabilities();
        assertThrows(IllegalArgumentException.class, exchange::finishCapabilities);
        assertThrows(IllegalArgumentException.class, () -> exchange.capabilities(deadline())); assertEquals(4, port.writes.size());
        assertEquals(1, exchange.semantic(1, deadline()).row().sequence());
        assertTrue(text(port.writes.get(4)).contains("\"id\":4"));
        assertThrows(IllegalArgumentException.class, () -> exchange.capabilities(deadline())); assertEquals(5, port.writes.size());
        Port afterSemantic = new Port(INITIALIZED, CAP); var other = exchange(afterSemantic); other.initialize(deadline()); other.semantic(1, deadline());
        assertThrows(IllegalArgumentException.class, () -> other.capabilities(deadline())); assertEquals(3, afterSemantic.writes.size());
    }

    @Test void knownErrorOrMissingCapabilitiesBodyCannotActivateTheProtocolBootstrap() throws Exception {
        for (String result : List.of("{\"content\":[],\"structuredContent\":{},\"isError\":true}",
                "{\"content\":[]}", "{\"content\":[],\"structuredContent\":null}")) {
            Port port = new Port(INITIALIZED, "{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":" + result + "}\n");
            var exchange = exchange(port); exchange.initialize(deadline());
            assertThrows(IllegalArgumentException.class, () -> exchange.capabilities(deadline()));
            assertEquals(RootMcpExchange.State.FAILED, exchange.state());
            assertThrows(IllegalArgumentException.class, () -> exchange.semantic(1, deadline())); assertEquals(3, port.writes.size());
        }
    }

    @Test void wrongCapabilityIdAndExpiredDeadlinePreserveTheFirstFailureWithoutReplay() throws Exception {
        String wrong = CAP.replace("\"id\":2", "\"id\":3"); Port port = new Port(INITIALIZED, wrong);
        var exchange = exchange(port); exchange.initialize(deadline());
        assertThrows(IllegalArgumentException.class, () -> exchange.capabilities(deadline()));
        assertArrayEquals(bytes(wrong), exchange.failure().lastFrame().bytes()); assertEquals("capabilities", exchange.failure().phase());
        assertThrows(IllegalArgumentException.class, () -> exchange.capabilities(deadline())); assertEquals(3, port.writes.size());
        Port expired = new Port(INITIALIZED); var other = exchange(expired); other.initialize(deadline());
        assertThrows(IOException.class, () -> other.capabilities(Instant.now().minusSeconds(1))); assertEquals(2, expired.writes.size());
    }

    @Test void missingAdmissionRefusesBeforeChannelAccessAndSoftwareCannotConstructNativeCompletion() {
        var unavailable = assertInstanceOf(RootMcpSemanticClient.Unavailable.class,
                RootMcpSemanticClient.openNative(null, Optional.empty(), HANDSHAKE, LIMITS, deadline()));
        assertEquals(RootMcpSemanticClient.Reason.ACCEPTED_NATIVE_RUNTIME_UNAVAILABLE, unavailable.reason());
        assertEquals(0, RootMcpSemanticClient.OwnedCapabilities.class.getConstructors().length);
        assertEquals(0, RootMcpSemanticClient.OwnedCompletion.class.getConstructors().length);
        assertFalse(RootMcpSemanticClient.OwnedCompletion.class.isAssignableFrom(RootMcpSemanticClient.OwnedSoftwareCompletion.class));
    }

    @Test void separateBodyAndWholeLineLimitsRejectRealOversizedOpaqueTokensBeforeNativeRetention() throws Exception {
        int payload = RootMcpEnvelope.SEMANTIC_BODY_MAX_BYTES + 1 - RootMcpEnvelopePeer.BODY_PREFIX.length() - RootMcpEnvelopePeer.BODY_SUFFIX.length();
        byte[] raw = bytes("{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"content\":[],\"structuredContent\":"
                + RootMcpEnvelopePeer.BODY_PREFIX + "A".repeat(payload) + RootMcpEnvelopePeer.BODY_SUFFIX + "}}\n");
        var response = assertInstanceOf(RootMcpWire.Response.class, RootMcpWire.message(raw, LIMITS));
        var result = RootMcpWire.toolResult(response);
        assertThrows(IllegalArgumentException.class, () -> RootMcpWire.semanticBody(result));
        byte[] wholeOverflow = new byte[RootMcpEnvelope.RPC_LINE_MAX_BYTES + 1]; wholeOverflow[wholeOverflow.length - 1] = '\n';
        assertThrows(IllegalArgumentException.class, () -> RootMcpWire.message(wholeOverflow, LIMITS));
    }

    private static RootMcpExchange exchange(Port port) { return new RootMcpExchange(port, LIMITS, HANDSHAKE); }
    private static Instant deadline() { return Instant.now().plusSeconds(30); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static String text(byte[] raw) { return new String(raw, StandardCharsets.UTF_8); }
    private static final class Port implements RootMcpExchange.Port {
        private final Deque<byte[]> replies = new ArrayDeque<>();
        private final List<byte[]> writes = new ArrayList<>();
        private Port(String... lines) { for (String line : lines) { replies.add(bytes(line)); } }
        @Override public void verify() { }
        @Override public void write(byte[] raw, Instant deadline) { writes.add(raw.clone()); }
        @Override public byte[] readLine(Instant deadline) throws IOException {
            if (replies.isEmpty()) { throw new IOException("finite software peer exhausted"); }
            return replies.removeFirst().clone();
        }
    }
}
