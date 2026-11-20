package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Actual HTTP framing with an explicit SOFTWARE_ONLY directory. No Root, Native or Game authority is minted. */
final class PublicMcpHttpResourceTest {
    private static final URI LOCAL = URI.create("http://127.0.0.1:8089/mcp");
    static final class Software implements PublicMcpDirectory {
        final AtomicInteger calls = new AtomicInteger();
        final CountDownLatch entered = new CountDownLatch(1), release = new CountDownLatch(1);
        final boolean block;
        Software(boolean block) { this.block = block; }
        @Override public Scope scope() { return Scope.SOFTWARE_ONLY; }
        @Override public List<ToolDescriptor> tools() {
            return List.of(new ToolDescriptor("software_echo", new RawJson(McpJson.utf8(
                    "{\"name\":\"software_echo\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":true}}"))));
        }
        @Override public CallResult invoke(ToolCall call) throws ToolFailure {
            tools().getFirst().validateArguments(call.arguments()); calls.incrementAndGet(); entered.countDown();
            if (block) try {
                if (!release.await(5, TimeUnit.SECONDS)) throw new ToolFailure("Software gate elapsed");
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new ToolFailure("Interrupted", interrupted); }
            return CallResult.fromBusinessJson(new RawJson(McpJson.utf8("{\"original\":-0.0,\"nothing\":null,\"items\":[]}")));
        }
        @Override public List<ResourceDescriptor> resources() { return List.of(); }
        @Override public ResourceResult read(ResourceCall call) throws RpcFailure {
            throw new RpcFailure(-32602, "No software resource", Optional.empty());
        }
    }
    static Map<String,List<String>> headers(String version) {
        Map<String,List<String>> h = new HashMap<>();
        h.put("Content-Type",List.of("application/json"));
        h.put("Accept",List.of("application/json, text/event-stream"));
        if (version != null) h.put("MCP-Protocol-Version",List.of(version));
        return h;
    }
    static String request(String id, String method, boolean modern, String extra) {
        String meta = modern ? "\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientCapabilities\":{}}" : "";
        return "{\"jsonrpc\":\"2.0\",\"id\":" + id + ",\"method\":\"" + method + "\",\"params\":{"
                + meta + (meta.isEmpty() || extra.isEmpty() ? "" : ",") + extra + "}}";
    }
    static String initialize(String version) {
        return request("0","initialize",false,"\"protocolVersion\":\"" + version
                + "\",\"capabilities\":{},\"clientInfo\":{\"name\":\"software-http\",\"version\":\"1\"}");
    }
    static PublicMcpHttpResource.Input input(String method, Map<String,List<String>> h, String body) {
        return new PublicMcpHttpResource.Input(method,LOCAL,h,McpJson.utf8(body));
    }
    static PublicMcpHttpResource.Reply reply(CompletableFuture<PublicMcpHttpResource.Reply> value) throws Exception {
        return value.get(3,TimeUnit.SECONDS);
    }
    static JsonNode json(PublicMcpHttpResource.Reply r) { return McpJson.parseResult(r.body()); }
    static final class HttpPeer implements AutoCloseable {
        final Software software = new Software(false);
        final PublicMcpHttpResource.Router router = new PublicMcpHttpResource.Router(software);
        final HttpServer server;
        final HttpClient client = HttpClient.newHttpClient();
        final URI endpoint;
        HttpPeer() throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
            endpoint = URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/mcp");
            server.createContext("/mcp", exchange -> {
                try {
                    var in = new PublicMcpHttpResource.Input(exchange.getRequestMethod(),endpoint,
                            exchange.getRequestHeaders(),exchange.getRequestBody().readAllBytes());
                    var r = router.handle(in).get(3,TimeUnit.SECONDS);
                    r.headers().forEach((k,v) -> exchange.getResponseHeaders().set(k,v));
                    if (r.body().length == 0) exchange.sendResponseHeaders(r.status(),-1);
                    else {
                        exchange.getResponseHeaders().set("Content-Type","application/json");
                        exchange.sendResponseHeaders(r.status(),r.body().length);
                        exchange.getResponseBody().write(r.body());
                    }
                } catch (Exception unavailable) { exchange.sendResponseHeaders(503,-1); }
                finally { exchange.close(); }
            });
            server.start();
        }
        HttpResponse<byte[]> post(String body, Map<String,List<String>> headers) throws Exception {
            var builder = HttpRequest.newBuilder(endpoint).timeout(Duration.ofSeconds(5)).POST(HttpRequest.BodyPublishers.ofString(body));
            headers.forEach((k,values) -> values.forEach(v -> builder.header(k,v)));
            return client.send(builder.build(),HttpResponse.BodyHandlers.ofByteArray());
        }
        @Override public void close() throws Exception {
            software.release.countDown(); assertTrue(router.close(Duration.ofSeconds(3)).complete());
            server.stop(0); client.close();
        }
    }

    @Test void modernHttpUsesPerRequestMetadataJsonAndNoProtocolSession() throws Exception {
        try (HttpPeer peer = new HttpPeer()) {
            var h = headers(PublicMcpSession.MODERN); h.put("Mcp-Method",List.of("tools/list"));
            h.put("Origin",List.of("http://127.0.0.1:" + peer.endpoint.getPort()));
            h.put("MCP-Session-Id",List.of("irrelevant-modern-value"));
            var r = peer.post(request("1","tools/list",true,""),h);
            assertEquals(200,r.statusCode()); assertTrue(r.headers().firstValue("Content-Type").orElseThrow().startsWith("application/json"));
            assertTrue(r.headers().firstValue("MCP-Session-Id").isEmpty());
            assertEquals("software_echo",McpJson.parse(r.body()).path("result").path("tools").get(0).path("name").textValue());
            h.put("Mcp-Method",List.of("software/notification"));
            var note = peer.post("{\"jsonrpc\":\"2.0\",\"method\":\"software/notification\"}",h);
            assertEquals(202,note.statusCode()); assertEquals(0,note.body().length);
            assertEquals(405,peer.client.send(HttpRequest.newBuilder(peer.endpoint).GET().build(),HttpResponse.BodyHandlers.discarding()).statusCode());
            h.put("Mcp-Method",List.of("tools/call")); h.put("Mcp-Name",List.of("software_echo"));
            var result = peer.post(request("\"exact-id\"","tools/call",true,"\"name\":\"software_echo\",\"arguments\":{}"),h);
            assertEquals(200,result.statusCode()); assertEquals("exact-id",McpJson.parse(result.body()).path("id").textValue());
            assertTrue(new String(result.body(),java.nio.charset.StandardCharsets.UTF_8).contains("-0.0"));
            assertEquals(1,peer.software.calls.get());
            h.put("Mcp-Method",List.of("initialize")); h.remove("Mcp-Name");
            var modernInitialize = peer.post(request("44","initialize",true,
                    "\"protocolVersion\":\"2026-07-28\",\"capabilities\":{},\"clientInfo\":{\"name\":\"software\",\"version\":\"1\"}"),h);
            assertEquals(404,modernInitialize.statusCode());
            assertEquals(-32601,McpJson.parse(modernInitialize.body()).path("error").path("code").intValue());
            assertTrue(modernInitialize.headers().firstValue("MCP-Session-Id").isEmpty());
            assertEquals(1,peer.software.calls.get());
        }
    }

    @Test void everyLegacyEraRequiresActualInitializationAcrossHttpPosts() throws Exception {
        try (HttpPeer peer = new HttpPeer()) {
            for (String version : PublicMcpSession.LEGACY) {
                var h = headers(null);
                assertEquals(400,peer.post(request("1","tools/list",false,""),h).statusCode());
                var initialized = peer.post(initialize(version),h);
                assertEquals(200,initialized.statusCode());
                assertEquals(version,McpJson.parse(initialized.body()).path("result").path("protocolVersion").textValue());
                String id = initialized.headers().firstValue("MCP-Session-Id").orElseThrow();
                h.put("MCP-Session-Id",List.of(id)); h.put("MCP-Protocol-Version",List.of(version));
                assertEquals(202,peer.post("{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\",\"params\":{}}",h).statusCode());
                var listed = peer.post(request("1","tools/list",false,""),h); assertEquals(200,listed.statusCode());
                assertEquals("software_echo",McpJson.parse(listed.body()).path("result").path("tools").get(0).path("name").textValue());
                h.put("MCP-Session-Id",List.of("not-the-actual-session"));
                assertEquals(404,peer.post(request("2","tools/list",false,""),h).statusCode());
            }
            assertEquals(0,peer.software.calls.get());
        }
    }

    @Test void transportAndModernHeaderFailuresHaveZeroApplicationDispatch() throws Exception {
        Software data = new Software(false);
        var router = new PublicMcpHttpResource.Router(data);
        try {
            String body = request("9","tools/call",true,"\"name\":\"software_echo\",\"arguments\":{}");
            Map<String,List<String>> good = headers(PublicMcpSession.MODERN);
            good.put("Mcp-Method",List.of("tools/call")); good.put("Mcp-Name",List.of("software_echo"));
            for (String origin : List.of("null","http://evil.example:8089","http://127.0.0.1:8088","http://user@127.0.0.1:8089")) {
                var h = new HashMap<>(good); h.put("Origin",List.of(origin));
                assertEquals(403,reply(router.handle(input("POST",h,body))).status());
            }
            var h = new HashMap<>(good); h.put("Accept",List.of("application/json"));
            assertEquals(406,reply(router.handle(input("POST",h,body))).status());
            h = new HashMap<>(good); h.put("Content-Type",List.of("text/plain"));
            assertEquals(415,reply(router.handle(input("POST",h,body))).status());
            for (String field : List.of("Mcp-Method","Mcp-Name","MCP-Protocol-Version")) {
                h = new HashMap<>(good); h.remove(field);
                var bad = reply(router.handle(input("POST",h,body)));
                assertEquals(400,bad.status()); assertEquals(-32020,json(bad).path("error").path("code").intValue());
            }
            h = new HashMap<>(good); h.put("Mcp-Name",List.of("other"));
            assertEquals(400,reply(router.handle(input("POST",h,body))).status());
            h = new HashMap<>(good); h.put("Mcp-Method",List.of("tools/list","tools/call"));
            assertEquals(400,reply(router.handle(input("POST",h,body))).status());
            h = new HashMap<>(good); h.put("MCP-Protocol-Version",List.of("2099-01-01"));
            var unsupported = reply(router.handle(input("POST",h,body)));
            assertEquals(400,unsupported.status()); assertEquals(-32022,json(unsupported).path("error").path("code").intValue());
            assertEquals(0,data.calls.get());
        } finally { assertTrue(router.close(Duration.ofSeconds(3)).complete()); }
    }

    @Test void httpCannotInstallSoftwareDirectoryOrBootstrapAnAbsentRootHost() throws Exception {
        var resource = new PublicMcpHttpResource(); resource.host = new PublicMcpHost();
        var h = headers(PublicMcpSession.MODERN); h.put("Mcp-Method",List.of("tools/list"));
        assertEquals(503,reply(resource.route(input("POST",h,request("1","tools/list",true,"")))).status());
        assertThrows(IllegalArgumentException.class,() -> resource.host.install(
                org.xar.ck3.control.build.runtime.HostMode.COMPLETE_MIGRATION,new Software(false)));
        assertTrue(resource.host.current().isEmpty()); resource.close();
    }

    @Test void duplicateInFlightAndOwnerDrainRetainOriginalCallWithoutClaimingCancellation() throws Exception {
        Software data = new Software(true);
        var router = new PublicMcpHttpResource.Router(data);
        try {
            var h = headers(null);
            var init = reply(router.handle(input("POST",h,initialize("2025-11-25"))));
            h.put("MCP-Session-Id",List.of(init.headers().get("MCP-Session-Id")));
            h.put("MCP-Protocol-Version",List.of("2025-11-25"));
            String original = request("\"same-id\"","tools/call",false,"\"name\":\"software_echo\",\"arguments\":{}");
            var pending = router.handle(input("POST",h,original));
            assertTrue(data.entered.await(3,TimeUnit.SECONDS));
            var duplicate = reply(router.handle(input("POST",h,original)));
            assertEquals(400,duplicate.status()); assertEquals(-32600,json(duplicate).path("error").path("code").intValue());
            assertFalse(pending.isDone()); assertEquals(1,data.calls.get());
            var delivered = reply(PublicMcpHttpResource.boundedDelivery(pending, input("POST",h,original), Duration.ofMillis(30)));
            assertEquals(503,delivered.status());
            assertFalse(pending.isDone(),"HTTP deadline must not complete or cancel the actual application future");
            assertEquals(1,data.calls.get());
            var closed = router.close(Duration.ZERO);
            assertFalse(closed.complete()); assertEquals(1,closed.unresolvedCalls());
            assertFalse(pending.isDone(),"drain is not evidence of cancellation or rejection");
            assertEquals(503,reply(router.handle(input("POST",h,original))).status());
            data.release.countDown();
            var result = reply(pending); assertEquals(200,result.status());
            assertEquals("same-id",json(result).path("id").textValue()); assertEquals(1,data.calls.get());
        } finally {
            data.release.countDown(); assertTrue(router.close(Duration.ofSeconds(3)).complete());
        }
    }
}
