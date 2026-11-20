package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.net.URI;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

/** Pure SOFTWARE_ONLY MCP calls: no actual Root/Game/COMPLETE role is manufactured by these tests. */
class PublicMcpFiniteOwnerDrainTest {
    private static RawJson json(String text) { return new RawJson(McpJson.utf8(text)); }
    private static PublicMcpHttpResource.Input call(String id) {
        String body = "{\"jsonrpc\":\"2.0\",\"id\":\"" + id + "\",\"method\":\"tools/call\",\"params\":{\"name\":\"held\",\"arguments\":{},\"_meta\":{\""
                + PublicMcpSession.VERSION_KEY + "\":\"" + PublicMcpSession.MODERN
                + "\",\"io.modelcontextprotocol/clientCapabilities\":{}}}}";
        return new PublicMcpHttpResource.Input("POST", URI.create("http://127.0.0.1:8089/mcp"),
                Map.of("content-type", List.of("application/json"), "accept", List.of("application/json, text/event-stream"),
                        "mcp-protocol-version", List.of(PublicMcpSession.MODERN), "mcp-method", List.of("tools/call"),
                        "mcp-name", List.of("held")), McpJson.utf8(body));
    }
    @Test void uninstalledOwnerDrainIsFiniteIdempotentAndCannotInstallAuthority() throws Exception {
        var resource = new PublicMcpHttpResource(); resource.host = new PublicMcpHost();
        assertThrows(IllegalArgumentException.class, () -> resource.closeAndDrain(Duration.ofSeconds(61)));
        assertThrows(IllegalArgumentException.class, () -> resource.closeAndDrain(Duration.ofNanos(-1)));
        assertTrue(resource.closeAndDrain(Duration.ZERO).complete());
        assertEquals(0, resource.closeAndDrain(Duration.ZERO).unresolvedCalls());
        assertEquals(503, resource.route(call("1")).get(2, TimeUnit.SECONDS).status());
        assertTrue(resource.host.current().isEmpty());
    }

    @Test void finiteDrainPreservesOriginalUnresolvedCallAndNeverReplaysIt() throws Exception {
        var entered = new CountDownLatch(1); var release = new CountDownLatch(1); var calls = new AtomicInteger();
        PublicMcpDirectory software = new PublicMcpDirectory() {
            @Override public Scope scope() { return Scope.SOFTWARE_ONLY; }
            @Override public List<ToolDescriptor> tools() { return List.of(new ToolDescriptor("held", json(
                    "{\"name\":\"held\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":false}}"))); }
            @Override public CallResult invoke(ToolCall call) throws ToolFailure {
                calls.incrementAndGet(); entered.countDown();
                try { if (!release.await(5, TimeUnit.SECONDS)) throw new ToolFailure("finite software latch expired"); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new ToolFailure("interrupted", interrupted); }
                return CallResult.fromBusinessJson(json("{\"observed\":true}"));
            }
            @Override public List<ResourceDescriptor> resources() { return List.of(); }
            @Override public ResourceResult read(ResourceCall call) throws RpcFailure {
                throw new RpcFailure(-32601, "no software resource", Optional.empty());
            }
        };
        var router = new PublicMcpHttpResource.Router(software);
        try {
            var original = router.handle(call("18446744073709551615"));
            assertTrue(entered.await(5, TimeUnit.SECONDS), () -> original.isDone() ? new String(original.getNow(null).body(), java.nio.charset.StandardCharsets.UTF_8) : "actual request remains pending without business invocation");
            var first = PublicMcpHttpResource.drainRouter(router, Duration.ZERO);
            assertFalse(first.complete()); assertEquals(1, first.unresolvedCalls());
            assertFalse(original.isDone()); assertEquals(1, calls.get());
            assertEquals(503, router.handle(call("18446744073709551616")).get(2, TimeUnit.SECONDS).status());
            assertEquals(1, calls.get());
            release.countDown();
            assertEquals(200, original.get(5, TimeUnit.SECONDS).status());
            var ended = PublicMcpHttpResource.drainRouter(router, Duration.ofSeconds(2));
            assertTrue(ended.complete()); assertEquals(0, ended.unresolvedCalls()); assertEquals(1, calls.get());
            assertThrows(IllegalArgumentException.class, () -> new PublicMcpHost().install(
                    org.xar.ck3.control.build.runtime.HostMode.COMPLETE_MIGRATION, software));
        } finally { release.countDown(); router.close(Duration.ofSeconds(2)); }
    }

    @Test void closedPeerSnapshotSharesTheActualPeerAdmissionMonitor() throws Exception {
        PublicMcpDirectory software = new PublicMcpDirectory() {
            @Override public Scope scope() { return Scope.SOFTWARE_ONLY; }
            @Override public List<ToolDescriptor> tools() { return List.of(); }
            @Override public CallResult invoke(ToolCall call) { throw new AssertionError("no business call"); }
            @Override public List<ResourceDescriptor> resources() { return List.of(); }
            @Override public ResourceResult read(ResourceCall call) { throw new AssertionError("no business read"); }
        };
        var router = new PublicMcpHttpResource.Router(software);
        var entered = new CountDownLatch(1);
        var result = new AtomicReference<PublicMcpHttpResource.Drain>();
        var failure = new AtomicReference<Throwable>();
        Thread closer = new Thread(() -> {
            entered.countDown();
            try { result.set(PublicMcpHttpResource.drainRouter(router, Duration.ZERO)); }
            catch (Throwable actual) { failure.set(actual); }
        }, "software-finite-drain-admission");
        try {
            synchronized (router) {
                closer.start(); assertTrue(entered.await(2, TimeUnit.SECONDS));
                long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
                while (closer.getState() != Thread.State.BLOCKED && closer.isAlive() && System.nanoTime() < until)
                    Thread.sleep(1);
                assertEquals(Thread.State.BLOCKED, closer.getState(), "closed+peer snapshot must share create's admission lock");
                assertNull(result.get());
            }
            closer.join(2000); assertFalse(closer.isAlive()); assertNull(failure.get());
            assertTrue(result.get().complete()); assertEquals(0, result.get().unresolvedCalls());
            assertEquals(503, router.handle(call("after-drain")).get(2, TimeUnit.SECONDS).status());
        } finally { router.close(Duration.ZERO); closer.join(2000); }
    }
}
