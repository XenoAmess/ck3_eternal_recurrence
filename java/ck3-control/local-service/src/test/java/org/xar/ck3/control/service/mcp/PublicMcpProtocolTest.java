package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Original facade/SDK producer -> actual Java schema/binding -> protocol consumer, with no Game. */
final class PublicMcpProtocolTest {
    record Request(Presence presence) { }
    record Response(RawJson business) { }
    static JsonNode resource(String name) throws IOException {
        try (InputStream input = Objects.requireNonNull(PublicMcpProtocolTest.class.getResourceAsStream("/mcp/" + name), "required producer fixture")) {
            return McpJson.parse(input.readAllBytes());
        }
    }
    static JsonNode oracle() throws IOException { return resource("original-protocol-golden.json"); }
    static McpCoverage.Catalog catalog() throws IOException {
        return McpCoverage.readCatalog(new RawJson(McpJson.encode(resource("original-tool-catalog.json"))));
    }
    static PublicRoutes.Target target() {
        // Synthetic software identity, never a deployed implementation. Software directories cannot install in Root.
        return new PublicRoutes.Target(PublicMcpProtocolTest.class.getName(), "fixture", new ExactRef("software-only/fixture.java", 1, "0".repeat(64)));
    }
    @FunctionalInterface interface Operation { Response read(Request request) throws InterruptedException; }
    static PublicMcpBindings bindings(Operation operation) throws IOException {
        var catalog = catalog(); var fixture = oracle();
        List<McpCoverage.Decision> decisions = new ArrayList<>();
        for (var declaration : catalog.declarations()) decisions.add(new McpCoverage.Decision(declaration.name(),
                declaration.name().equals("ck3_get_capabilities") || declaration.name().equals("ck3_query_core_frame_v1")
                        ? McpCoverage.Admission.ADMITTED : McpCoverage.Admission.UNMIGRATED,
                catalog.declarations().getFirst().source(), "explicit protocol software fixture; no actual Native or Root adoption"));
        var bindings = new PublicMcpBindings(catalog, decisions);
        for (JsonNode row : fixture.get("descriptors")) {
            String name = row.get("name").textValue(); if (name.equals("ck3_query_prewar_force_coalition_coverage_v2")) continue;
            bindings.registerDirect(new ToolDescriptor(name, new RawJson(McpJson.encode(row))), PublicMcpBindings.Kind.APPLICATION_COMPOSITE,
                    Request.class, Response.class, operation::read,
                    call -> new Request(call.arguments().presence()), response -> CallResult.fromBusinessJson(response.business()), target());
        }
        for (JsonNode row : fixture.get("resources")) {
            String uri = row.get("uri").textValue();
            bindings.registerResource(new ResourceDescriptor(uri, new RawJson(McpJson.encode(row))), Response.class,
                    call -> operation.read(new Request(Presence.MISSING)), response -> ResourceResult.fromBusinessJson(uri, response.business()), target());
        }
        return bindings;
    }
    static PublicMcpDirectory directory() throws IOException {
        RawJson business = new RawJson(McpJson.encode(oracle().get("business")));
        return bindings(request -> new Response(business)).freezeSoftwareScope();
    }
    static final class Peer implements AutoCloseable {
        final BlockingQueue<byte[]> lines = new LinkedBlockingQueue<>();
        final PublicMcpSession session;
        Peer(PublicMcpDirectory directory) { session = new PublicMcpSession(directory, line -> lines.add(line.clone())); }
        void send(String json) { session.receive(McpJson.utf8(json)); }
        JsonNode receive() throws InterruptedException {
            byte[] line = lines.poll(3, TimeUnit.SECONDS); assertNotNull(line, "actual protocol response required");
            assertEquals('\n', line[line.length - 1]); return McpJson.parse(line);
        }
        void initialize(String version) throws InterruptedException {
            send("{\"jsonrpc\":\"2.0\",\"id\":0,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"" + version
                    + "\",\"capabilities\":{},\"clientInfo\":{\"name\":\"software-test\",\"version\":\"1\"}}}");
            assertEquals(version, receive().path("result").path("protocolVersion").textValue());
        }
        @Override public void close() throws InterruptedException { assertTrue(session.closeAndDrain(Duration.ofSeconds(3)).complete()); }
    }
    static String request(String version, String id, String method, String extra) {
        String meta = version.equals(PublicMcpSession.MODERN)
                ? "\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientCapabilities\":{}}" : "";
        String parameters = meta + (meta.isEmpty() || extra.isEmpty() ? "" : ",") + extra;
        return "{\"jsonrpc\":\"2.0\",\"id\":" + id + ",\"method\":\"" + method + "\",\"params\":{" + parameters + "}}";
    }

    @Test void everyActualSdkVersionVectorTraversesTheJavaHost() throws Exception {
        JsonNode fixture = oracle();
        for (String version : List.of("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25", "2026-07-28")) {
            try (Peer peer = new Peer(directory())) {
                if (!version.equals(PublicMcpSession.MODERN)) peer.initialize(version);
                for (JsonNode vector : fixture.get("vectors")) {
                    if (!vector.get("version").textValue().equals(version)) continue;
                    String method = vector.get("method").textValue();
                    String arguments = method.equals("tools/call") ? "\"name\":\"ck3_get_capabilities\",\"arguments\":{}"
                            : method.equals("resources/read") ? "\"uri\":\"ck3://capabilities\"" : "";
                    peer.send(request(version, "\"18446744073709551615\"", method, arguments));
                    JsonNode envelope = peer.receive(); assertEquals("18446744073709551615", envelope.get("id").textValue());
                    var actual = McpJson.object(envelope.get("result")).deepCopy();
                    if (version.equals(PublicMcpSession.MODERN)) {
                        assertEquals(PublicMcpSession.SERVER_NAME, actual.path("_meta").path(PublicMcpSession.SERVER_INFO_KEY).path("name").textValue());
                        actual.remove("_meta");
                    }
                    assertEquals(vector.get("result"), actual, version + " " + method);
                }
            }
        }
    }

    @Test void exactProducerConversionPreservesDecimalIdentityNullAndEmptyArray() throws Exception {
        JsonNode fixture = oracle();
        var actual = CallResult.fromBusinessJson(new RawJson(McpJson.encode(fixture.get("business"))));
        assertEquals(fixture.get("call_result"), McpJson.parse(actual.bytes()));
        assertTrue(McpJson.parse(actual.bytes()).path("structuredContent").path("nullable").isNull());
        assertTrue(McpJson.parse(actual.bytes()).path("structuredContent").path("empty").isArray());
    }

    @Test void missingNullAndObjectArgumentsUseOriginalSdkEmptyObjectDefault() throws Exception {
        List<Presence> observed = new java.util.concurrent.CopyOnWriteArrayList<>();
        RawJson business = new RawJson(McpJson.encode(oracle().get("business")));
        try (Peer peer = new Peer(bindings(request -> { observed.add(request.presence()); return new Response(business); }).freezeSoftwareScope())) {
            peer.initialize("2025-11-25");
            for (String suffix : List.of("", ",\"arguments\":null", ",\"arguments\":{}")) {
                peer.send(request("2025-11-25", "1", "tools/call", "\"name\":\"ck3_get_capabilities\"" + suffix));
                assertFalse(peer.receive().path("result").path("isError").booleanValue());
            }
        }
        assertEquals(List.of(Presence.VALUE, Presence.VALUE, Presence.VALUE), observed);
    }

    @Test void malformedFieldTypeDuplicateUtf8AndVersionAreRejectedBeforeDispatch() throws Exception {
        AtomicInteger calls = new AtomicInteger(); RawJson business = new RawJson(McpJson.encode(oracle().get("business")));
        try (Peer peer = new Peer(bindings(request -> { calls.incrementAndGet(); return new Response(business); }).freezeSoftwareScope())) {
            peer.send("{\"jsonrpc\":\"2.0\",\"id\":1,\"id\":2,\"method\":\"ping\"}"); assertEquals(-32700, peer.receive().path("error").path("code").intValue());
            peer.session.receive(new byte[]{(byte)0xc3, (byte)0x28}); assertEquals(-32700, peer.receive().path("error").path("code").intValue());
            peer.send("{\"jsonrpc\":\"2.0\",\"id\":true,\"method\":\"ping\"}"); assertEquals(-32600, peer.receive().path("error").path("code").intValue());
            peer.initialize("2025-11-25");
            peer.send(request("2025-11-25", "1", "tools/call", "\"name\":\"ck3_query_core_frame_v1\",\"arguments\":{\"extra\":1}"));
            assertTrue(peer.receive().path("result").path("isError").booleanValue());
            peer.send(request("2025-11-25", "2", "tools/call", "\"name\":\"ck3_get_capabilities\",\"arguments\":[]"));
            assertEquals(-32602, peer.receive().path("error").path("code").intValue());
        }
        assertEquals(0, calls.get());
        try (Peer peer = new Peer(directory())) {
            peer.send("{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/list\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"unsupported\",\"io.modelcontextprotocol/clientCapabilities\":{}}}}");
            assertEquals(-32022, peer.receive().path("error").path("code").intValue());
        }
    }

    @Test void queuedCancellationDoesNotInterruptOrReplayTheActiveApplicationCall() throws Exception {
        CountDownLatch entered = new CountDownLatch(1), release = new CountDownLatch(1); AtomicInteger actualCalls = new AtomicInteger();
        RawJson business = new RawJson(McpJson.encode(oracle().get("business")));
        try (Peer peer = new Peer(bindings(request -> { actualCalls.incrementAndGet(); entered.countDown(); assertTrue(release.await(3, TimeUnit.SECONDS)); return new Response(business); }).freezeSoftwareScope())) {
            peer.initialize("2025-11-25");
            peer.send(request("2025-11-25", "10", "tools/call", "\"name\":\"ck3_get_capabilities\"")); assertTrue(entered.await(3, TimeUnit.SECONDS));
            peer.send(request("2025-11-25", "11", "tools/call", "\"name\":\"ck3_get_capabilities\""));
            peer.send("{\"jsonrpc\":\"2.0\",\"method\":\"notifications/cancelled\",\"params\":{\"requestId\":11,\"reason\":\"test\"}}");
            release.countDown();
            assertFalse(peer.receive().path("result").path("isError").booleanValue());
            assertTrue(peer.receive().path("result").path("isError").booleanValue());
            assertEquals(1, actualCalls.get());
        } finally { release.countDown(); }
    }

    @Test void fullMaterialFiniteDecimalSurvivesBothRpcErasWithoutChangingRequestLimits() throws Exception {
        String longDecimal = "1." + "0".repeat(5000);
        RawJson business = RawJson.fullMaterial(McpJson.utf8("{\"finite_decimal\":" + longDecimal + "}"));
        JsonNode expected = McpJson.parseResult(business.bytes());
        for (String version : List.of("2025-11-25", PublicMcpSession.MODERN)) {
            AtomicInteger calls = new AtomicInteger();
            try (Peer peer = new Peer(bindings(request -> {
                calls.incrementAndGet(); return new Response(business);
            }).freezeSoftwareScope())) {
                if (!version.equals(PublicMcpSession.MODERN)) peer.initialize(version);
                peer.send(request(version, "1", "tools/call", "\"name\":\"ck3_get_capabilities\""));
                byte[] wire = peer.lines.poll(3, TimeUnit.SECONDS);
                assertNotNull(wire, "actual full-material protocol response required");
                assertThrows(IllegalArgumentException.class, () -> McpJson.parse(wire));
                JsonNode envelope = McpJson.parseResult(wire);
                assertFalse(envelope.has("error"));
                JsonNode result = envelope.get("result");
                assertFalse(result.path("isError").booleanValue());
                byte[] structured = McpJson.tokenResult(McpJson.tokenResult(wire, "result"), "structuredContent");
                assertArrayEquals(business.bytes(), structured);
                assertEquals(expected, McpJson.parseResult(structured));
                byte[] text = result.path("content").get(0).path("text").textValue()
                        .getBytes(java.nio.charset.StandardCharsets.UTF_8);
                assertEquals(expected, McpJson.parseResult(text));
                assertEquals(longDecimal, new String(McpJson.tokenResult(text, "finite_decimal"),
                        java.nio.charset.StandardCharsets.UTF_8));
                assertEquals(1, calls.get());
                peer.send(request(version, "2", "tools/call",
                        "\"name\":\"ck3_get_capabilities\",\"arguments\":{\"finite_decimal\":" + longDecimal + "}"));
                assertEquals(-32700, peer.receive().path("error").path("code").intValue());
                assertEquals(1, calls.get());
            }
        }
    }

    @Test void postDispatchFailuresRemainUnconfirmedWithoutReplayingTheHandler() throws Exception {
        List<Operation> failures = List.of(
                request -> { throw new IllegalStateException("software handler failed after entry"); },
                request -> null,
                request -> new Response(new RawJson(McpJson.utf8("[]"))));
        for (String version : List.of("2025-11-25", PublicMcpSession.MODERN)) {
            for (Operation failure : failures) {
                AtomicInteger calls = new AtomicInteger();
                try (Peer peer = new Peer(bindings(request -> {
                    calls.incrementAndGet(); return failure.read(request);
                }).freezeSoftwareScope())) {
                    if (!version.equals(PublicMcpSession.MODERN)) peer.initialize(version);
                    peer.send(request(version, "\"failed-call\"", "tools/call", "\"name\":\"ck3_get_capabilities\""));
                    JsonNode envelope = peer.receive();
                    assertEquals("failed-call", envelope.path("id").textValue());
                    assertFalse(envelope.has("error"));
                    JsonNode result = envelope.get("result");
                    assertTrue(result.path("isError").booleanValue());
                    String text = result.path("content").get(0).path("text").textValue();
                    assertTrue(text.contains("application/world outcome unconfirmed; do not resend"), text);
                    assertEquals(1, calls.get());
                    peer.send(request(version, "2", "ping", ""));
                    JsonNode ping = peer.receive();
                    assertEquals(2, ping.path("id").intValue());
                    assertFalse(ping.has("error"));
                    assertTrue(ping.get("result").isObject());
                    var drain = peer.session.closeAndDrain(Duration.ofSeconds(3));
                    assertTrue(drain.complete());
                    assertEquals(1L, drain.completedCalls());
                    assertEquals(0, drain.unresolvedCalls());
                    assertEquals(1, calls.get());
                    assertTrue(peer.lines.isEmpty(), "one tool reply and one ping reply only");
                }
            }
        }
    }

    @Test void duplicateInFlightIdRetainsOriginalCall() throws Exception {
        RawJson business = new RawJson(McpJson.encode(oracle().get("business")));
        for (String version : List.of("2025-11-25", PublicMcpSession.MODERN)) {
            CountDownLatch entered = new CountDownLatch(1);
            CountDownLatch release = new CountDownLatch(1);
            AtomicInteger calls = new AtomicInteger();
            try (Peer peer = new Peer(bindings(request -> {
                calls.incrementAndGet();
                entered.countDown();
                assertTrue(release.await(3, TimeUnit.SECONDS));
                return new Response(business);
            }).freezeSoftwareScope())) {
                try {
                    if (!version.equals(PublicMcpSession.MODERN)) peer.initialize(version);
    
                    // 1. Start original call (held)
                    peer.send(request(version, "\"held-call\"", "tools/call", "\"name\":\"ck3_get_capabilities\""));
                    assertTrue(entered.await(3, TimeUnit.SECONDS), "handler must enter");
                    assertEquals(1, calls.get());
    
                    // 2. Duplicate same tool, same id -> RPC -32600
                    peer.send(request(version, "\"held-call\"", "tools/call", "\"name\":\"ck3_get_capabilities\""));
                    JsonNode dup1 = peer.receive();
                    assertEquals(-32600, dup1.path("error").path("code").intValue());
                    assertEquals("held-call", dup1.path("id").textValue());
                    assertEquals(1, calls.get(), "duplicate must not invoke handler");
    
                    // 3. Duplicate different tool, same id -> RPC -32600
                    peer.send(request(version, "\"held-call\"", "tools/call", "\"name\":\"ck3_query_core_frame_v1\""));
                    JsonNode dup2 = peer.receive();
                    assertEquals(-32600, dup2.path("error").path("code").intValue());
                    assertEquals("held-call", dup2.path("id").textValue());
                    assertEquals(1, calls.get(), "duplicate must not invoke handler");
    
                    // 4. Unrelated ping (numeric id) -> succeeds
                    peer.send(request(version, "2", "ping", ""));
                    JsonNode ping = peer.receive();
                    assertEquals(2, ping.path("id").intValue());
                    assertFalse(ping.has("error"));
                    assertTrue(ping.get("result").isObject());
                    assertEquals(1, calls.get());
    
                    // 5. Release original handler
                    release.countDown();
    
                    // 6. Consume original successful result
                    JsonNode original = peer.receive();
                    assertEquals("held-call", original.path("id").textValue());
                    assertFalse(original.has("error"));
                    assertFalse(original.path("result").path("isError").booleanValue());
                    assertEquals(McpJson.parse(business.bytes()), original.path("result").get("structuredContent"));
                    assertEquals(1, calls.get());
    
                    // 7. Drain
                    var drain = peer.session.closeAndDrain(Duration.ofSeconds(3));
                    assertTrue(drain.complete());
                    assertEquals(1L, drain.completedCalls());
                    assertEquals(0, drain.unresolvedCalls());
                    assertEquals(1, calls.get());
                    assertTrue(peer.lines.isEmpty(), "no extra output");
                } finally {
                    release.countDown();
                }
            }
        }
    }

    @Test void modernToolsCallPartialWriteFailureExits74WithoutRetry() throws Exception {
        RawJson business = new RawJson(McpJson.encode(oracle().get("business")));
        AtomicInteger calls = new AtomicInteger();
        CountDownLatch entered = new CountDownLatch(1);
        AtomicInteger attempts = new AtomicInteger();
        ByteArrayOutputStream accepted = new ByteArrayOutputStream();
        
        // Handler increments calls and returns fixture business
        var directory = bindings(request -> {
            calls.incrementAndGet();
            entered.countDown();
            return new Response(business);
        }).freezeSoftwareScope();

        // OutputStream accepts 12 bytes, throws on 13th, fails all later
        var output = new java.io.OutputStream() {
            @Override public void write(int value) throws IOException {
                int count = attempts.incrementAndGet();
                if (count <= 12) {
                    accepted.write(value);
                } else {
                    throw new IOException("write failure at byte " + count);
                }
            }
            @Override public void write(byte[] bytes, int offset, int length) throws IOException {
                for (int i = 0; i < length; i++) write(bytes[offset + i]);
            }
        };

        // Modern request for tools/call
        String requestJson = request(PublicMcpSession.MODERN, "1", "tools/call", "\"name\":\"ck3_get_capabilities\"");
        byte[] payload = McpJson.utf8(requestJson + "\n");

        var input = new ByteArrayInputStream(payload) {
            @Override public synchronized int read(byte[] target, int offset, int length) {
                int count = super.read(target, offset, length);
                if (count < 0) {
                    try { assertTrue(entered.await(3, TimeUnit.SECONDS), "handler must enter before stdin closes"); }
                    catch (InterruptedException interrupted) {
                        Thread.currentThread().interrupt();
                        throw new IllegalStateException("entry wait interrupted", interrupted);
                    }
                }
                return count;
            }
        };
        var exit = PublicMcpStdio.run(directory, input, output, Duration.ofSeconds(3));

        assertEquals(74, exit.code());
        assertEquals(1, exit.completedCalls());
        assertEquals(0, exit.unresolvedCalls());
        assertTrue(exit.reason().contains("client delivery unconfirmed"));
        assertTrue(exit.reason().contains("do not resend world actions"));
        assertEquals(1, calls.get());
        assertEquals(12, accepted.size());
        assertEquals(13, attempts.get()); // 12 successful + 1 failure. No retry means no 14th attempt.
    }

    @Test void ndjsonCrLfPartialFrameAndInputOutputFailuresHaveActualExitCodes() throws Exception {
        String ping = "{\"jsonrpc\":\"2.0\",\"id\":7,\"method\":\"ping\"}";
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        assertEquals(0, PublicMcpStdio.run(directory(), new ByteArrayInputStream(McpJson.utf8(ping + "\r\n")), output, Duration.ofSeconds(1)).code());
        assertEquals(7, McpJson.parse(output.toByteArray()).path("id").intValue());
        assertEquals(65, PublicMcpStdio.run(directory(), new ByteArrayInputStream(McpJson.utf8(ping)), new ByteArrayOutputStream(), Duration.ZERO).code());
        InputStream broken = new InputStream() { @Override public int read() throws IOException { throw new IOException("actual read failure"); } };
        assertEquals(74, PublicMcpStdio.run(directory(), broken, new ByteArrayOutputStream(), Duration.ZERO).code());
        java.io.OutputStream failed = new java.io.OutputStream() { @Override public void write(int value) throws IOException { throw new IOException("actual write failure"); } };
        assertEquals(74, PublicMcpStdio.run(directory(), new ByteArrayInputStream(McpJson.utf8(ping + "\n")), failed, Duration.ofSeconds(1)).code());
    }
}
