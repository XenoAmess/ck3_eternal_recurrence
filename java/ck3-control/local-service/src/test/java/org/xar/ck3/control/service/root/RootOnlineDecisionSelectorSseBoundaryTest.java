package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.Authenticator;
import java.net.CookieHandler;
import java.net.ProxySelector;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpHeaders;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicInteger;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSession;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

/**
 * Memory-only SSE boundary tests with no socket/server, Native, materials or action submission.
 * A fake HttpClient supplies finite InputStreams to the actual private call().
 * This fixture exercises observable parser outcomes; it does not copy the production byte scanner.
 */
class RootOnlineDecisionSelectorSseBoundaryTest {
    private static final int WIRE_LIMIT = 262144;
    private static final int LINE_LIMIT = 65536;
    private static final String STOP = "data:{\"choices\":[{\"delta\":{},\"finish_reason\":\"stop\"}]}\n";
    private static final String DONE = "data:[DONE]\n";

    @Test void splitUtf8AndCrLfAcrossReadsPreserveContentAndUsage() throws Exception {
        String expected = "火𐐨é";
        String text = ":nondata 火𐐨\r\n"
                + "data:{\"choices\":[{\"delta\":{\"role\":\"assistant\"}}]}\n"
                + event("") + event(expected) + STOP
                + "data:{\"choices\":[],\"usage\":{\"prompt_tokens\":19,\"completion_tokens\":3,"
                + "\"total_tokens\":22,\"prompt_tokens_details\":{\"cached_tokens\":0}}}\r\n" + DONE;
        byte[] wire = utf8(text);
        for (int chunk : new int[] {1, 2, 3, 7, 2048}) {
            Outcome result = run(new SegmentedBody(wire, chunk), 200);
            assertTrue(result.complete(), "split=" + chunk + ": " + result.failure());
            assertEquals(expected, result.content());
            assertArrayEquals(wire, result.raw());
            assertNotNull(result.ttftMs());
            assertEquals(19L, (Long) accessor(result.usage(), "promptTokens"));
            assertEquals(0L, (Long) accessor(result.usage(), "cachedPromptTokens"));
            assertEquals(1, result.calls());
        }
    }

    @Test void rolesUsageAndEmptyDeltasDoNotStartTtft() throws Exception {
        Outcome result = run(new SegmentedBody(utf8(":comment\n"
                + "data:{\"choices\":[{\"delta\":{\"role\":\"assistant\"}}]}\n" + event("")
                + "data:{\"choices\":[],\"usage\":{\"completion_tokens\":0}}\n" + STOP + DONE), 17), 200);
        assertFalse(result.complete());
        assertEquals("incomplete_model_stream", result.failure());
        assertNull(result.ttftMs());
        assertEquals("", result.content());
    }

    @Test void exactByteLineBudgetAcceptsAndOneExtraByteRejects() throws Exception {
        byte[] exact = utf8(":" + "x".repeat(LINE_LIMIT - 1) + "\n" + complete("ok"));
        Outcome accepted = run(new SegmentedBody(exact, 2048), 200);
        assertTrue(accepted.complete(), accepted.failure());
        assertEquals("ok", accepted.content());
        Outcome over = run(new SegmentedBody(utf8(":" + "x".repeat(LINE_LIMIT) + "\n" + complete("ok")), 2048), 200);
        assertFalse(over.complete());
        assertEquals("IllegalArgumentException:model SSE line limit exceeded", over.failure());
        assertFalse(over.transientFailure());
        assertNull(over.ttftMs());
    }

    @Test void crCountsTowardTheByteLineBudgetBeforeItIsStripped() throws Exception {
        Outcome exact = run(new SegmentedBody(utf8(":" + "x".repeat(LINE_LIMIT - 2) + "\r\n" + complete("ok")), 7), 200);
        assertTrue(exact.complete(), exact.failure());
        Outcome over = run(new SegmentedBody(utf8(":" + "x".repeat(LINE_LIMIT - 1) + "\r\n" + complete("ok")), 7), 200);
        assertEquals("IllegalArgumentException:model SSE line limit exceeded", over.failure());
        assertFalse(over.complete());
    }

    @Test void byteBudgetDoesNotBecomeAUtf16CharacterBudget() throws Exception {
        Outcome exact = run(new SegmentedBody(utf8(":" + "é".repeat((LINE_LIMIT - 2) / 2) + "x\n" + complete("ok")), 3), 200);
        assertTrue(exact.complete(), exact.failure());
        Outcome over = run(new SegmentedBody(utf8(":" + "é".repeat(LINE_LIMIT / 2) + "\n" + complete("ok")), 3), 200);
        assertFalse(over.complete());
        assertEquals("IllegalArgumentException:model SSE line limit exceeded", over.failure());
    }

    @Test void malformedUtf8InANonDataLineStillRejects() throws Exception {
        byte[] wire = concatenate(new byte[] {':', (byte) 0xc3, 0x28, '\n'}, utf8(complete("ok")));
        Outcome result = run(new SegmentedBody(wire, 1), 200);
        assertFalse(result.complete());
        assertTrue(result.failure().startsWith("MalformedInputException:"), result.failure());
        assertTrue(result.transientFailure());
        assertNull(result.ttftMs());
    }

    @Test void earlierMalformedEventWinsBeforeALaterOversizedLine() throws Exception {
        byte[] wire = utf8("data:{\"choices\":[]\n:" + "x".repeat(LINE_LIMIT) + "\n" + complete("ok"));
        Outcome result = run(new SegmentedBody(wire, 2048), 200);
        assertFalse(result.complete());
        assertEquals("IllegalArgumentException:invalid complete JSON material", result.failure());
        assertFalse(result.transientFailure());
    }

    @Test void exactNon200WireBudgetRetainsHttpFailureAndNextByteRejectsBeforeParsing() throws Exception {
        Outcome exact = run(new SegmentedBody(new byte[WIRE_LIMIT], 2048), 503);
        assertEquals("HTTP_503", exact.failure());
        assertTrue(exact.transientFailure());
        assertEquals(WIRE_LIMIT, exact.raw().length);
        byte[] tooLarge = new byte[WIRE_LIMIT + 1];
        tooLarge[WIRE_LIMIT] = (byte) 0xc3;
        Outcome over = run(new SegmentedBody(tooLarge, 2048), 503);
        assertEquals("IllegalArgumentException:model response wire limit exceeded", over.failure());
        assertFalse(over.transientFailure());
        assertEquals(WIRE_LIMIT, over.raw().length, "the rejected read must not be appended to raw evidence");
    }

    @Test void wholeReadWireCheckWinsOverMalformedUtf8InThatRead() throws Exception {
        byte[] commentBlock = utf8(":" + "x".repeat(2046) + "\n");
        ByteArrayOutputStream wire = new ByteArrayOutputStream();
        for (int index = 0; index < WIRE_LIMIT / 2048; index++) wire.writeBytes(commentBlock);
        wire.writeBytes(new byte[] {':', (byte) 0xc3, 0x28, '\n'});
        Outcome result = run(new SegmentedBody(wire.toByteArray(), 2048), 200);
        assertEquals("IllegalArgumentException:model response wire limit exceeded", result.failure());
        assertEquals(WIRE_LIMIT, result.raw().length);
        assertFalse(result.transientFailure());
    }

    @Test void doneStopsBeforeMalformedSuffixButRetainsTheAlreadyReadWire() throws Exception {
        byte[] wire = concatenate(utf8(complete("ok")), new byte[] {':', (byte) 0xc3, 0x28, '\n'});
        Outcome result = run(new SegmentedBody(wire, 2048), 200);
        assertTrue(result.complete(), result.failure());
        assertEquals("ok", result.content());
        assertArrayEquals(wire, result.raw());
    }

    @Test void unterminatedFinalLineCannotBeUsedAsDone() throws Exception {
        Outcome result = run(new SegmentedBody(utf8(event("ok") + STOP + "data:[DONE]"), 3), 200);
        assertFalse(result.complete());
        assertEquals("incomplete_model_stream", result.failure());
        assertTrue(result.transientFailure());
    }

    @Test void successiveAttemptsDoNotJoinAnIncompleteContentPrefix() throws Exception {
        RootOnlineDecisionSelector selector = selector();
        Outcome first = run(selector, new SegmentedBody(utf8(event("prefix-that-must-not-be-joined")), 2), 200, Duration.ofSeconds(3));
        Outcome second = run(selector, new SegmentedBody(utf8(complete("second-only")), 3), 200, Duration.ofSeconds(3));
        assertFalse(first.complete());
        assertTrue(first.transientFailure());
        assertTrue(second.complete(), second.failure());
        assertEquals("second-only", second.content());
        assertEquals(1, first.calls());
        assertEquals(1, second.calls());
    }

    @Test @Timeout(3) void bodyWatchdogStillClosesABlockedReadInsideTheOriginalBudget() throws Exception {
        BlockingBody body = new BlockingBody();
        Outcome result = run(body, 200, Duration.ofMillis(100));
        assertFalse(result.complete());
        assertEquals("model_stream_deadline", result.failure());
        assertTrue(result.transientFailure());
        assertTrue(body.closeCalls.get() >= 1);
        assertNull(result.ttftMs());
    }

    private record Outcome(byte[] raw, String content, Long ttftMs, String failure,
            boolean transientFailure, boolean complete, Object usage, int calls) { }

    private static Outcome run(InputStream body, int status) throws Exception {
        return run(body, status, Duration.ofSeconds(3));
    }

    private static Outcome run(InputStream body, int status, Duration budget) throws Exception {
        return run(selector(), body, status, budget);
    }

    private static RootOnlineDecisionSelector selector() {
        return new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                URI.create("http://offline.invalid/v1"), "offline-fixture", Duration.ofSeconds(3), 6, Duration.ZERO),
                Clock.systemUTC(), ignored -> { throw new AssertionError("call() must not archive or submit actions"); });
    }

    private static Outcome run(RootOnlineDecisionSelector selector, InputStream body, int status, Duration budget) throws Exception {
        MemoryClient client = new MemoryClient(status, body);
        Field field = RootOnlineDecisionSelector.class.getDeclaredField("http");
        field.setAccessible(true);
        ((HttpClient) field.get(selector)).close();
        field.set(selector, client);
        Method call = RootOnlineDecisionSelector.class.getDeclaredMethod("call", byte[].class, Instant.class, long.class);
        call.setAccessible(true);
        long nanoEnd = System.nanoTime() + budget.toNanos();
        Object result = call.invoke(selector, utf8("{}"), Instant.now().plus(budget), nanoEnd);
        return new Outcome((byte[]) accessor(result, "raw"), (String) accessor(result, "content"),
                (Long) accessor(result, "ttftMs"), (String) accessor(result, "failure"),
                (Boolean) accessor(result, "transientFailure"), (Boolean) accessor(result, "complete"),
                accessor(result, "usage"), client.calls.get());
    }

    private static Object accessor(Object target, String name) throws Exception {
        Method method = target.getClass().getDeclaredMethod(name);
        method.setAccessible(true);
        return method.invoke(target);
    }

    private static String event(String content) {
        var envelope = JsonNodeFactory.instance.objectNode();
        envelope.putArray("choices").addObject().putObject("delta").put("content", content);
        return "data: " + envelope + "\r\n";
    }

    private static String complete(String content) { return event(content) + STOP + DONE; }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    private static byte[] concatenate(byte[] first, byte[] second) {
        byte[] result = java.util.Arrays.copyOf(first, first.length + second.length);
        System.arraycopy(second, 0, result, first.length, second.length);
        return result;
    }

    private static final class SegmentedBody extends ByteArrayInputStream {
        private final int chunk;
        SegmentedBody(byte[] bytes, int chunk) { super(bytes); this.chunk = chunk; }
        @Override public synchronized int read(byte[] bytes, int offset, int length) {
            return super.read(bytes, offset, Math.min(length, chunk));
        }
        @Override public int read() { throw new AssertionError("expected buffered body read"); }
    }

    private static final class BlockingBody extends InputStream {
        private final CountDownLatch closed = new CountDownLatch(1);
        private final AtomicInteger closeCalls = new AtomicInteger();
        @Override public int read() { throw new AssertionError("expected buffered body read"); }
        @Override public int read(byte[] bytes, int offset, int length) throws IOException {
            try { closed.await(); return -1; }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
        }
        @Override public void close() { closeCalls.incrementAndGet(); closed.countDown(); }
    }

    private record MemoryResponse(int statusCode, InputStream body, HttpRequest request) implements HttpResponse<InputStream> {
        @Override public Optional<HttpResponse<InputStream>> previousResponse() { return Optional.empty(); }
        @Override public HttpHeaders headers() { return HttpHeaders.of(Map.of(), (name, value) -> true); }
        @Override public Optional<SSLSession> sslSession() { return Optional.empty(); }
        @Override public URI uri() { return request.uri(); }
        @Override public HttpClient.Version version() { return HttpClient.Version.HTTP_1_1; }
    }

    private static final class MemoryClient extends HttpClient {
        private final int status;
        private final InputStream body;
        private final AtomicInteger calls = new AtomicInteger();
        MemoryClient(int status, InputStream body) { this.status = status; this.body = body; }
        @Override public void close() { }
        @Override public Optional<CookieHandler> cookieHandler() { return Optional.empty(); }
        @Override public Optional<Duration> connectTimeout() { return Optional.empty(); }
        @Override public Redirect followRedirects() { return Redirect.NEVER; }
        @Override public Optional<ProxySelector> proxy() { return Optional.empty(); }
        @Override public SSLContext sslContext() { throw new AssertionError("no TLS or network"); }
        @Override public SSLParameters sslParameters() { return new SSLParameters(); }
        @Override public Optional<Authenticator> authenticator() { return Optional.empty(); }
        @Override public Version version() { return Version.HTTP_1_1; }
        @Override public Optional<Executor> executor() { return Optional.empty(); }
        @Override public <T> HttpResponse<T> send(HttpRequest request, HttpResponse.BodyHandler<T> handler) {
            throw new AssertionError("expected the actual asynchronous call path");
        }
        @Override @SuppressWarnings("unchecked")
        public <T> CompletableFuture<HttpResponse<T>> sendAsync(HttpRequest request, HttpResponse.BodyHandler<T> handler) {
            calls.incrementAndGet();
            return CompletableFuture.completedFuture((HttpResponse<T>) new MemoryResponse(status, body, request));
        }
        @Override public <T> CompletableFuture<HttpResponse<T>> sendAsync(HttpRequest request,
                HttpResponse.BodyHandler<T> handler, HttpResponse.PushPromiseHandler<T> pushHandler) {
            throw new AssertionError("no push or network");
        }
    }
}
