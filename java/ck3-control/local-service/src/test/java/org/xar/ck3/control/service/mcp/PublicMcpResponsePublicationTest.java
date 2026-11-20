package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.net.URI;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.LockSupport;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Deterministic protocol-only barriers. SOFTWARE_ONLY never installs a Root or buys a Native role. */
final class PublicMcpResponsePublicationTest {
    private static final String ID = "18446744073709551615";
    static final class Software implements PublicMcpDirectory {
        final List<ToolDescriptor> descriptors = List.of(new ToolDescriptor("software_echo",
                new RawJson(McpJson.utf8("{\"name\":\"software_echo\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":true}}"))));
        final AtomicInteger calls = new AtomicInteger();
        final CountDownLatch entered = new CountDownLatch(1), release = new CountDownLatch(1);
        final CountDownLatch metadataEntered = new CountDownLatch(1), metadataRelease = new CountDownLatch(1);
        final AtomicBoolean blockMetadata = new AtomicBoolean();
        final AtomicReference<PublicMcpSession> session = new AtomicReference<>();
        volatile boolean blockCall;
        @Override public Scope scope() { return Scope.SOFTWARE_ONLY; }
        @Override public List<ToolDescriptor> tools() {
            if (blockMetadata.compareAndSet(true,false)) {
                metadataEntered.countDown();
                await(metadataRelease,"metadata barrier");
            }
            return descriptors;
        }
        @Override public CallResult invoke(ToolCall call) {
            PublicMcpSession held = session.get();
            if (held != null) assertFalse(Thread.holdsLock(held),"application invocation must remain outside the publication boundary");
            int number = calls.incrementAndGet(); entered.countDown();
            if (blockCall) await(release,"application barrier");
            return CallResult.fromBusinessJson(new RawJson(McpJson.utf8("{\"call\":" + number + "}")));
        }
        @Override public List<ResourceDescriptor> resources() { return List.of(); }
        @Override public ResourceResult read(ResourceCall call) throws RpcFailure {
            throw new RpcFailure(-32602,"No software resources",Optional.empty());
        }
    }
    static void await(CountDownLatch gate,String name) {
        try { assertTrue(gate.await(3,TimeUnit.SECONDS),name); }
        catch (InterruptedException failure) { Thread.currentThread().interrupt(); throw new AssertionError(failure); }
    }
    static byte[] call(String id,boolean modern) {
        return McpJson.utf8("{\"jsonrpc\":\"2.0\",\"id\":\"" + id + "\",\"method\":\"tools/call\",\"params\":{"
                + (modern ? "\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientCapabilities\":{}}," : "")
                + "\"name\":\"software_echo\",\"arguments\":{}}}");
    }
    static JsonNode take(BlockingQueue<byte[]> sink) throws Exception {
        byte[] value = sink.poll(3,TimeUnit.SECONDS); assertNotNull(value,"actual terminal frame");
        return McpJson.parseResult(value);
    }
    static Thread daemon(String name,Runnable operation) {
        Thread t = new Thread(operation,name); t.setDaemon(true); return t;
    }
    static void blocked(Thread t) {
        long stop = System.nanoTime() + TimeUnit.SECONDS.toNanos(3);
        while (t.getState() != Thread.State.BLOCKED && t.isAlive() && System.nanoTime() < stop) LockSupport.parkNanos(100_000);
        assertEquals(Thread.State.BLOCKED,t.getState(),"the second request must reach the actual publication monitor");
    }

    @Test void modernVisibleResponseAllowsReuseButRunningCallRetainsOriginal() throws Exception {
        Software data = new Software();
        BlockingQueue<byte[]> frames = new LinkedBlockingQueue<>();
        CountDownLatch visible = new CountDownLatch(1), sinkReturn = new CountDownLatch(1);
        AtomicInteger emitted = new AtomicInteger();
        PublicMcpSession session = new PublicMcpSession(data,line -> {
            frames.add(line.clone());
            if (emitted.incrementAndGet()==1) { visible.countDown(); await(sinkReturn,"first frame already visible"); }
        });
        data.session.set(session);
        AtomicReference<Throwable> threadFailure = new AtomicReference<>();
        Thread reused = daemon("visible-response-id-reuse",() -> {
            try { session.receive(call(ID,true)); } catch (Throwable failure) { threadFailure.set(failure); }
        });
        try {
            session.receive(call(ID,true)); await(visible,"response visible before Sink returns");
            JsonNode first = take(frames); assertTrue(first.has("result"));
            reused.start(); blocked(reused); sinkReturn.countDown(); reused.join(3000);
            assertFalse(reused.isAlive()); assertNull(threadFailure.get());
            JsonNode second = take(frames);
            assertTrue(second.has("result"),second.toString());
            assertEquals(ID,second.path("id").textValue()); assertEquals(2,data.calls.get());
        } finally { sinkReturn.countDown(); assertTrue(session.closeAndDrain(Duration.ofSeconds(3)).complete()); }

        Software running = new Software(); running.blockCall=true;
        BlockingQueue<byte[]> replies = new LinkedBlockingQueue<>();
        PublicMcpSession busy = new PublicMcpSession(running,line -> replies.add(line.clone()));
        running.session.set(busy);
        try {
            busy.receive(call(ID,true)); await(running.entered,"original invocation entered");
            busy.receive(call(ID,true));
            JsonNode duplicate = take(replies); assertEquals(-32600,duplicate.path("error").path("code").intValue());
            assertEquals(1,running.calls.get()); running.release.countDown();
            assertTrue(take(replies).has("result")); assertEquals(1,running.calls.get());
        } finally { running.release.countDown(); assertTrue(busy.closeAndDrain(Duration.ofSeconds(3)).complete()); }
    }

    @Test void httpReplyCompletesWhileConcurrentMetadataIsStillBlocked() throws Exception {
        Software data = new Software(); data.blockCall=true;
        var router = new PublicMcpHttpResource.Router(data);
        Map<String,List<String>> headers = new java.util.HashMap<>();
        headers.put("Content-Type",List.of("application/json"));
        headers.put("Accept",List.of("application/json, text/event-stream"));
        URI endpoint = URI.create("http://127.0.0.1:8089/mcp");
        var initialized = router.handle(new PublicMcpHttpResource.Input("POST",endpoint,headers,McpJson.utf8(
                "{\"jsonrpc\":\"2.0\",\"id\":0,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-11-25\","
                        + "\"capabilities\":{},\"clientInfo\":{\"name\":\"software-concurrency\",\"version\":\"1\"}}}"))).get(3,TimeUnit.SECONDS);
        assertEquals(200,initialized.status());
        headers.put("MCP-Session-Id",List.of(initialized.headers().get("MCP-Session-Id")));
        headers.put("MCP-Protocol-Version",List.of("2025-11-25"));
        CompletableFuture<PublicMcpHttpResource.Reply> metadata = new CompletableFuture<>();
        Thread reader = daemon("blocked-http-metadata",() -> {
            try {
                router.handle(new PublicMcpHttpResource.Input("POST",endpoint,headers,McpJson.utf8(
                        "{\"jsonrpc\":\"2.0\",\"id\":\"metadata\",\"method\":\"tools/list\",\"params\":{}}")))
                        .whenComplete((value,failure) -> { if (failure==null) metadata.complete(value); else metadata.completeExceptionally(failure); });
            } catch (Throwable failure) { metadata.completeExceptionally(failure); }
        });
        try {
            var original = router.handle(new PublicMcpHttpResource.Input("POST",endpoint,headers,call(ID,false)));
            await(data.entered,"original HTTP application entered");
            data.blockMetadata.set(true); reader.start(); await(data.metadataEntered,"HTTP metadata is inside original Directory guard");
            data.release.countDown();
            var response = original.get(3,TimeUnit.SECONDS);
            assertEquals(200,response.status()); assertTrue(McpJson.parse(response.body()).has("result"));
            assertFalse(metadata.isDone(),"the metadata barrier remains held while the original response completes");
            assertEquals(1,data.calls.get());
            data.metadataRelease.countDown();
            assertEquals(200,metadata.get(3,TimeUnit.SECONDS).status());
        } finally {
            data.release.countDown(); data.metadataRelease.countDown(); reader.join(3000);
            assertTrue(router.close(Duration.ofSeconds(3)).complete()); assertFalse(reader.isAlive());
        }
    }
}
