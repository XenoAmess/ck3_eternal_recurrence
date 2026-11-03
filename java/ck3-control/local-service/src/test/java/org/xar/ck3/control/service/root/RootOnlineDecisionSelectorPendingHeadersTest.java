package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

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
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSession;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

/** New in-memory pending-headers boundaries; actual private call(), no completed-future/parser fixture. */
class RootOnlineDecisionSelectorPendingHeadersTest {
    @Test @Timeout(10)
    void genuinelyPendingHeadersTimeOutAndCancelTheUnfinishedFuture() throws Exception {
        TrackingFuture pending = new TrackingFuture(true);
        PendingClient client = new PendingClient(pending);
        ProbeBody lateBody = new ProbeBody();
        ProbeResponse lateResponse = new ProbeResponse(lateBody);
        try {
            Outcome result = invoke(client);
            assertPendingTimeout(result, client, pending);
            assertTrue(pending.isCancelled());
            assertTrue(pending.isDone());
            assertTrue(pending.cancelResult);

            // An actual attempt to complete the cancelled future, with no isCancelled() guard.
            assertFalse(pending.complete(lateResponse));
            assertNotAdopted(lateResponse);
            assertEquals(1, pending.timedGetCalls, "late completion must not cause a second call");
        } finally {
            lateBody.close(); // The fixture still owns a response rejected by complete().
            pending.completeExceptionally(new CancellationException("fixture cleanup"));
        }
        assertEquals(1, lateBody.closeCalls);
    }

    @Test @Timeout(10)
    void declinedCancellationAllowsLateCompletionWithoutTransferringBodyToTheReturnedCall() throws Exception {
        TrackingFuture pending = new TrackingFuture(false);
        PendingClient client = new PendingClient(pending);
        ProbeBody lateBody = new ProbeBody();
        ProbeResponse lateResponse = new ProbeResponse(lateBody);
        try {
            Outcome result = invoke(client);
            assertPendingTimeout(result, client, pending);
            assertFalse(pending.cancelResult);
            assertFalse(pending.isCancelled());
            assertFalse(pending.isDone());

            // This late completion really succeeds after call() returned. No second call is made.
            assertTrue(pending.complete(lateResponse));
            assertTrue(pending.getNow(null) == lateResponse);
            assertNotAdopted(lateResponse);
            assertEquals(1, pending.timedGetCalls);
            assertEquals(1, pending.cancelCalls);
            assertEquals(List.of("sendAsync", "pendingTimedGet", "timedGetTimeout", "cancel:true"), pending.events);
        } finally {
            lateBody.close(); // call() did not receive this body; cleanup remains with this fixture.
            pending.completeExceptionally(new CancellationException("fixture cleanup"));
        }
        assertEquals(1, lateBody.closeCalls);
    }

    private static void assertPendingTimeout(Outcome result, PendingClient client, TrackingFuture pending) {
        assertEquals(1, client.calls);
        assertEquals(1, pending.timedGetCalls);
        assertTrue(pending.pendingAtTimedGetEntry, "must enter real timed get with an unfinished future");
        assertTrue(pending.requestedWaitNanos > 0);
        assertEquals(1, pending.timedGetTimeouts);
        assertEquals(1, pending.cancelCalls);
        assertTrue(pending.cancelMayInterrupt);
        assertEquals(List.of("sendAsync", "pendingTimedGet", "timedGetTimeout", "cancel:true"), pending.events);
        assertEquals(0, result.status());
        assertEquals(-1L, result.headersMs());
        assertFalse(result.complete());
        assertTrue(result.failure().startsWith("TimeoutException:"), result.failure());
        assertTrue(result.transientFailure());
        assertNull(result.ttftMs());
        assertEquals("", result.content());
        assertEquals(0, result.rawBytes());
    }

    private static void assertNotAdopted(ProbeResponse response) {
        assertEquals(0, response.statusCalls);
        assertEquals(0, response.bodyCalls);
        assertEquals(0, response.stream.readCalls);
        assertEquals(0, response.stream.closeCalls,
                "no late-response cleanup hook is registered by this call; fixture must dispose its own body");
    }

    private record Outcome(int status, int rawBytes, String content, long headersMs, Long ttftMs,
            String failure, boolean transientFailure, boolean complete) { }

    private static Outcome invoke(PendingClient client) throws Exception {
        var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                URI.create("http://offline.invalid/v1"), "pending-headers-fixture", Duration.ofSeconds(2), 1, Duration.ZERO),
                Clock.systemUTC(), ignored -> { throw new AssertionError("call() cannot archive or submit an action"); });
        Field field = RootOnlineDecisionSelector.class.getDeclaredField("http");
        field.setAccessible(true);
        ((HttpClient) field.get(selector)).close(); // Complete setup before starting the tested budget.
        field.set(selector, client);
        Method call = RootOnlineDecisionSelector.class.getDeclaredMethod("call", byte[].class, Instant.class, long.class);
        call.setAccessible(true);
        Duration budget = Duration.ofSeconds(1);
        long nanoEnd = System.nanoTime() + budget.toNanos();
        Object result = call.invoke(selector, "{}".getBytes(StandardCharsets.UTF_8), Instant.now().plus(budget), nanoEnd);
        return new Outcome((Integer) accessor(result, "status"), ((byte[]) accessor(result, "raw")).length,
                (String) accessor(result, "content"), (Long) accessor(result, "headersMs"),
                (Long) accessor(result, "ttftMs"), (String) accessor(result, "failure"),
                (Boolean) accessor(result, "transientFailure"), (Boolean) accessor(result, "complete"));
    }

    private static Object accessor(Object target, String name) throws Exception {
        Method method = target.getClass().getDeclaredMethod(name);
        method.setAccessible(true);
        return method.invoke(target);
    }

    private static final class TrackingFuture extends CompletableFuture<HttpResponse<InputStream>> {
        private final boolean acceptCancellation;
        private final List<String> events = new ArrayList<>();
        private int timedGetCalls;
        private int timedGetTimeouts;
        private int cancelCalls;
        private boolean pendingAtTimedGetEntry;
        private boolean cancelMayInterrupt;
        private boolean cancelResult;
        private long requestedWaitNanos;

        TrackingFuture(boolean acceptCancellation) { this.acceptCancellation = acceptCancellation; }

        @Override public HttpResponse<InputStream> get(long timeout, TimeUnit unit)
                throws InterruptedException, ExecutionException, TimeoutException {
            timedGetCalls++;
            pendingAtTimedGetEntry = !isDone();
            requestedWaitNanos = unit.toNanos(timeout);
            events.add("pendingTimedGet");
            try {
                return super.get(timeout, unit); // The real CompletableFuture timed wait, never a fabricated exception.
            } catch (TimeoutException timedOut) {
                timedGetTimeouts++;
                events.add("timedGetTimeout");
                throw timedOut;
            }
        }

        @Override public boolean cancel(boolean mayInterruptIfRunning) {
            cancelCalls++;
            cancelMayInterrupt = mayInterruptIfRunning;
            events.add("cancel:" + mayInterruptIfRunning);
            cancelResult = acceptCancellation && super.cancel(mayInterruptIfRunning);
            return cancelResult;
        }
    }

    private static final class ProbeBody extends InputStream {
        private int readCalls;
        private int closeCalls;
        @Override public int read() { readCalls++; return -1; }
        @Override public int read(byte[] bytes, int offset, int length) {
            java.util.Objects.checkFromIndexSize(offset, length, bytes.length);
            readCalls++;
            return length == 0 ? 0 : -1;
        }
        @Override public void close() { closeCalls++; }
    }

    private static final class ProbeResponse implements HttpResponse<InputStream> {
        private final ProbeBody stream;
        private int statusCalls;
        private int bodyCalls;
        ProbeResponse(ProbeBody stream) { this.stream = stream; }
        @Override public int statusCode() { statusCalls++; return 200; }
        @Override public HttpRequest request() { throw new AssertionError("late response must not be inspected"); }
        @Override public Optional<HttpResponse<InputStream>> previousResponse() { return Optional.empty(); }
        @Override public HttpHeaders headers() { return HttpHeaders.of(Map.of(), (name, value) -> true); }
        @Override public InputStream body() { bodyCalls++; return stream; }
        @Override public Optional<SSLSession> sslSession() { return Optional.empty(); }
        @Override public URI uri() { return URI.create("http://offline.invalid/v1"); }
        @Override public HttpClient.Version version() { return HttpClient.Version.HTTP_1_1; }
    }

    private static final class PendingClient extends HttpClient {
        private final TrackingFuture pending;
        private int calls;
        PendingClient(TrackingFuture pending) { this.pending = pending; }
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
            throw new AssertionError("expected actual asynchronous call path");
        }
        @Override @SuppressWarnings("unchecked")
        public <T> CompletableFuture<HttpResponse<T>> sendAsync(HttpRequest request, HttpResponse.BodyHandler<T> handler) {
            calls++;
            pending.events.add("sendAsync");
            return (CompletableFuture<HttpResponse<T>>) (CompletableFuture<?>) pending;
        }
        @Override public <T> CompletableFuture<HttpResponse<T>> sendAsync(HttpRequest request,
                HttpResponse.BodyHandler<T> handler, HttpResponse.PushPromiseHandler<T> pushHandler) {
            throw new AssertionError("no push or network");
        }
    }
}
