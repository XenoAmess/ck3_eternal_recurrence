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

/** Software protocol messages only. No Native frame/arrival or actual-source qualification is fabricated. */
final class RootMcpProtocolTest {
    private static final RootMcpWire.Limits LIMITS = new RootMcpWire.Limits(65536, 8);
    private static final RootMcpWire.Handshake HANDSHAKE = new RootMcpWire.Handshake("2025-11-25", Set.of("2025-11-25"), "java-root-software-test", "1", "software-mcp-peer", "1");
    private static final String INITIALIZED = "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"tools\":{}},\"serverInfo\":{\"name\":\"software-mcp-peer\",\"version\":\"1\"}}}\n";
    private static final String TOOL = "{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"content\":[],\"structuredContent\":{\"software_only\":true}}}\n";

    @Test void initializeNotificationAndSingleReadonlyToolUseTheRealWireContract() throws Exception {
        Port port = new Port(INITIALIZED, TOOL); var exchange = exchange(port);
        assertEquals("2025-11-25", exchange.initialize(deadline()).version());
        var call = exchange.semantic(11560, deadline());
        assertEquals(RootMcpExchange.State.READY, exchange.state()); assertEquals(3, port.writes.size());
        assertTrue(text(port.writes.get(0)).contains("\"method\":\"initialize\""));
        assertTrue(text(port.writes.get(1)).contains("\"method\":\"notifications/initialized\""));
        assertTrue(text(port.writes.get(2)).contains("\"name\":\"ck3_take_semantic_snapshot_private_v1\""));
        assertFalse(text(port.writes.get(2)).contains("ck3_auto_turn"));
        assertArrayEquals(bytes(TOOL), call.originalRpcLine().bytes());
        assertEquals(call.result().ownerProjection().bytes().length, call.row().resultProjectionBytes());
        assertTrue(text(call.row().bytes().bytes()).contains("\"sequence\":11560"));
        assertThrows(IllegalArgumentException.class, () -> exchange.semantic(11560, deadline()));
        assertEquals(3, port.writes.size());
    }

    @Test void projectionPreservesExactOpaqueIntegerFloatAndSignedZeroTokens() throws Exception {
        String result = "{\"_meta\":null,\"content\":[{\"type\":\"text\",\"text\":\"软件\",\"extra\":18446744073709551615}],\"structuredContent\":{\"u128\":340282366920938463463374607431768211455,\"decimal\":1.2300e-17,\"negative_zero\":-0.0},\"isError\":false,\"resultType\":\"complete\"}";
        var response = assertInstanceOf(RootMcpWire.Response.class, RootMcpWire.message(bytes("{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":" + result + "}\n"), LIMITS));
        var projected = RootMcpWire.toolResult(response);
        assertArrayEquals(bytes(result), projected.originalResult().bytes());
        String raw = text(projected.ownerProjection().bytes());
        assertTrue(raw.contains("340282366920938463463374607431768211455"));
        assertTrue(raw.contains("1.2300e-17")); assertTrue(raw.contains("-0.0")); assertTrue(raw.contains("18446744073709551615"));
        var row = RootMcpWire.ownerRow(7, Instant.parse("2026-10-23T00:00:00Z"), Instant.parse("2026-10-23T00:00:01Z"), 123456789, projected);
        assertTrue(text(row.bytes().bytes()).contains("\"elapsed_seconds\":0.123456789"));
        assertTrue(text(row.bytes().bytes()).contains("\"mcp_result_projection_json_utf8_bytes\":" + projected.ownerProjection().bytes().length));
    }

    @Test void missingNullAndTypedOptionalFieldsStayDistinctAtTheWireBoundary() throws Exception {
        var absent = projection("{\"content\":[]}"); var explicitNull = projection("{\"_meta\":null,\"content\":[],\"structuredContent\":null}");
        assertEquals(RootMcpWire.Presence.MISSING, absent.metaPresence());
        assertEquals(RootMcpWire.Presence.NULL, explicitNull.metaPresence());
        assertEquals(RootMcpWire.Presence.MISSING, absent.structuredPresence());
        assertEquals(RootMcpWire.Presence.NULL, explicitNull.structuredPresence());
        assertFalse(absent.isError()); assertTrue(text(absent.ownerProjection().bytes()).contains("\"structured_content\":null"));
        for (String value : List.of("null", "1", "1.0", "\"false\"")) {
            assertThrows(IllegalArgumentException.class, () -> projection("{\"content\":[],\"isError\":" + value + "}"));
        }
    }

    @Test void badIdsAliasesDuplicatesAndErrorResultMixNeverReachACompletedCall() {
        for (String id : List.of("true", "1.0", "null", "0", "9007199254740992")) {
            assertThrows(IllegalArgumentException.class, () -> RootMcpWire.message(bytes("{\"jsonrpc\":\"2.0\",\"id\":" + id + ",\"result\":{}}\n"), LIMITS));
        }
        for (String raw : List.of("{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{},\"error\":{}}\n",
                "{\"jsonrpc\":\"2.0\",\"id\":2,\"id\":2,\"result\":{}}\n",
                "{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{},\"alias\":true}\n")) {
            assertThrows(Exception.class, () -> RootMcpWire.message(bytes(raw), LIMITS));
        }
        assertThrows(IllegalArgumentException.class, () -> projection("{\"content\":[],\"structured_content\":{}}"));
        assertThrows(IllegalArgumentException.class, () -> projection("{\"content\":[],\"resultType\":\"deferred\"}"));
    }

    @Test void wrongServerIdentityOrVersionFailsBeforeInitializedOrToolWrites() {
        for (String invalid : List.of(INITIALIZED.replace("software-mcp-peer", "unbound-peer"), INITIALIZED.replace("2025-11-25", "2026-07-28"))) {
            Port port = new Port(invalid); var exchange = exchange(port);
            assertThrows(IllegalArgumentException.class, () -> exchange.initialize(deadline()));
            assertEquals(RootMcpExchange.State.FAILED, exchange.state()); assertEquals(1, port.writes.size());
            assertThrows(IllegalArgumentException.class, () -> exchange.initialize(deadline()));
        }
    }

    @Test void notificationsAndServerPingAreBoundedAndDoNotConsumeClientRequestIds() throws Exception {
        Port port = new Port(INITIALIZED,
                "{\"jsonrpc\":\"2.0\",\"method\":\"notifications/message\",\"params\":{\"data\":\"software log\"}}\n",
                "{\"jsonrpc\":\"2.0\",\"id\":\"peer-ping\",\"method\":\"ping\"}\n", TOOL);
        var exchange = exchange(port); exchange.initialize(deadline()); var call = exchange.semantic(8, deadline());
        assertEquals(2, call.notifications().size()); assertEquals(4, port.writes.size());
        assertTrue(text(port.writes.get(3)).contains("\"id\":\"peer-ping\""));
        assertTrue(text(port.writes.get(3)).contains("\"result\":{}"));
    }

    @Test void wrongResponseIdLatchesUnknownAndNeverResubmits() throws Exception {
        Port port = new Port(INITIALIZED, TOOL.replace("\"id\":2", "\"id\":3")); var exchange = exchange(port); exchange.initialize(deadline());
        assertThrows(IllegalArgumentException.class, () -> exchange.semantic(9, deadline()));
        assertEquals(RootMcpExchange.State.FAILED, exchange.state()); assertEquals(9, exchange.failure().attemptedRootSequence());
        assertArrayEquals(bytes(TOOL.replace("\"id\":2", "\"id\":3")), exchange.failure().lastFrame().bytes());
        assertThrows(IllegalArgumentException.class, () -> exchange.semantic(10, deadline())); assertEquals(3, port.writes.size());
    }

    @Test void actualPortTimeoutOrSourceDriftLatchesFailureWithoutRetry() throws Exception {
        Port timeout = new Port(INITIALIZED); var timed = exchange(timeout); timed.initialize(deadline());
        assertThrows(IOException.class, () -> timed.semantic(11, deadline()));
        assertEquals(RootMcpExchange.State.FAILED, timed.state()); assertThrows(IllegalArgumentException.class, () -> timed.semantic(12, deadline()));
        Port drift = new Port(INITIALIZED, TOOL); var changed = exchange(drift); changed.initialize(deadline()); drift.driftAfterRead = true;
        assertThrows(IOException.class, () -> changed.semantic(13, deadline()));
        assertEquals(RootMcpExchange.State.FAILED, changed.state()); assertEquals(3, drift.writes.size());
    }

    @Test void knownToolErrorKeepsOriginalCompleteReplyAndRequiresAFreshRootSequence() throws Exception {
        Port port = new Port(INITIALIZED, TOOL.replace("\"content\":[]", "\"content\":[],\"isError\":true"));
        var exchange = exchange(port); exchange.initialize(deadline()); var call = exchange.semantic(14, deadline());
        assertTrue(call.result().isError()); assertEquals(RootMcpExchange.State.READY, exchange.state());
        assertTrue(text(call.row().bytes().bytes()).contains("\"is_error\":true"));
        assertThrows(IllegalArgumentException.class, () -> exchange.semantic(14, deadline()));
    }

    @Test void notificationFloodAndUnsupportedServerRequestsFailClosed() throws Exception {
        String note = "{\"jsonrpc\":\"2.0\",\"method\":\"notifications/message\"}\n";
        Port port = new Port(INITIALIZED, note, note); var exchange = new RootMcpExchange(port, new RootMcpWire.Limits(65536, 1), HANDSHAKE);
        exchange.initialize(deadline()); assertThrows(IllegalArgumentException.class, () -> exchange.semantic(15, deadline()));
        assertEquals(RootMcpExchange.State.FAILED, exchange.state());
        assertThrows(IllegalArgumentException.class, () -> RootMcpWire.message(bytes("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"sampling/createMessage\",\"params\":{}}\n"), LIMITS));
    }

    @Test void malformedUtf8LineBoundariesAndExpiredDeadlineDoNotStartARequest() {
        for (byte[] raw : List.of(bytes("{}"), bytes("\n"), new byte[] {(byte) 0xc3, (byte) 0x28, '\n'},
                new byte[] {(byte) 0xef, (byte) 0xbb, (byte) 0xbf, '{', '}', '\n'}, new byte[] {'{', '}', 0, '\n'})) {
            assertThrows(Exception.class, () -> RootMcpWire.message(raw, LIMITS));
        }
        for (String invalid : List.of("uD800", "uDC00")) {
            String escaped = "\\" + invalid;
            assertThrows(IllegalArgumentException.class, () -> projection("{\"content\":[{\"type\":\"text\",\"text\":\"" + escaped + "\"}]}"));
            assertThrows(IllegalArgumentException.class, () -> projection("{\"content\":[],\"structuredContent\":{\"" + escaped + "\":1}}"));
        }
        Port port = new Port(INITIALIZED); var exchange = exchange(port);
        assertThrows(IOException.class, () -> exchange.initialize(Instant.now().minusSeconds(1)));
        assertEquals(0, port.writes.size()); assertEquals(RootMcpExchange.State.FAILED, exchange.state());
    }

    @Test void unboundActualSourcesAreUnavailableBeforeAnyOwnedChannelIsRequired() {
        assertFalse(RootMcpSemanticClient.hasSelectedSourceRefs(Optional.empty()));
        var unavailable = assertInstanceOf(RootMcpSemanticClient.Unavailable.class,
                RootMcpSemanticClient.open(null, Optional.empty(), HANDSHAKE, LIMITS, deadline()));
        assertEquals(RootMcpSemanticClient.Reason.SOURCE_UNBOUND, unavailable.reason());
        assertEquals(0, RootMcpSemanticClient.OwnedSoftwareCompletion.class.getConstructors().length);
    }

    private static RootMcpWire.ToolResult projection(String result) throws IOException {
        var response = assertInstanceOf(RootMcpWire.Response.class,
                RootMcpWire.message(bytes("{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":" + result + "}\n"), LIMITS));
        return RootMcpWire.toolResult(response);
    }
    private static RootMcpExchange exchange(Port port) { return new RootMcpExchange(port, LIMITS, HANDSHAKE); }
    private static Instant deadline() { return Instant.now().plusSeconds(30); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static String text(byte[] raw) { return new String(raw, StandardCharsets.UTF_8); }
    private static final class Port implements RootMcpExchange.Port {
        private final Deque<byte[]> replies = new ArrayDeque<>();
        private final List<byte[]> writes = new ArrayList<>();
        private boolean driftAfterRead;
        private boolean drift;
        private Port(String... lines) { for (String line : lines) { replies.add(bytes(line)); } }
        @Override public void verify() throws IOException { if (drift) { throw new IOException("software source drift"); } }
        @Override public void write(byte[] raw, Instant deadline) { writes.add(raw.clone()); }
        @Override public byte[] readLine(Instant deadline) throws IOException {
            if (replies.isEmpty()) { throw new IOException("software transport finite timeout"); }
            byte[] result = replies.remove(); if (driftAfterRead) { drift = true; } return result.clone();
        }
    }
}
