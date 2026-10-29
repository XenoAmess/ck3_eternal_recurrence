package org.xar.ck3.control.g2.client;

import java.io.IOException;
import java.net.Proxy;
import java.net.ProxySelector;
import java.net.SocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpHeaders;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.Duration;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.OptionalInt;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;

/**
 * The single Java client for the existing local read-only G2 evaluation route.
 * Caller provenance remains data: this client issues no source, action or writer authority.
 */
public final class G2JavaClient implements AutoCloseable {
    private final G2ClientConfig config;
    private final URI endpoint;
    private final HttpClient http;

    public G2JavaClient(G2ClientConfig config) {
        this.config = Objects.requireNonNull(config, "config");
        endpoint = config.baseUri().resolve(G2Wire.HTTP_PATH);
        http = HttpClient.newBuilder().connectTimeout(config.deadline())
                .followRedirects(HttpClient.Redirect.NEVER).version(HttpClient.Version.HTTP_1_1)
                .proxy(new DirectProxySelector()).build();
    }

    /** Fits existing pure consumer ports as client::evaluate. */
    public G2Response evaluate(G2Request request) { return evaluateWithEvidence(request).response(); }

    public G2Evaluation evaluateWithEvidence(G2Request request) {
        return evaluateWithEvidence(request, config.deadline());
    }

    /** Reuses this transport and clips one call to the remaining finite batch budget. */
    public G2Evaluation evaluateWithEvidence(G2Request request, Duration maximumCallTime) {
        Instant started = Instant.now();
        long tick = System.nanoTime();
        String id = request == null ? "unavailable" : request.requestId();
        byte[] encoded = new byte[0];
        BoundedG2BodySubscriber body = new BoundedG2BodySubscriber(config.maximumResponseBytes());
        AtomicReference<HttpResponse.ResponseInfo> info = new AtomicReference<>();
        boolean invoked = false;
        try {
            long budget;
            try {
                Objects.requireNonNull(maximumCallTime, "maximumCallTime");
                if (maximumCallTime.isNegative() || maximumCallTime.isZero()) {
                    throw new IllegalArgumentException("positive finite call budget required");
                }
                budget = Math.min(config.deadline().toNanos(), maximumCallTime.toNanos());
            } catch (RuntimeException error) {
                throw failure(G2ClientException.Reason.LOCAL_REQUEST_INVALID,
                        "G2 call budget rejected before HTTP invocation", id, started, tick, encoded, body, info, false, null, error);
            }
            try {
                Objects.requireNonNull(request, "request");
                encoded = G2Wire.encodeRequest(request);
                // The common parser is the sole runtime schema/token validator.
                G2Request decoded = G2Wire.decodeRequest(encoded);
                requireEcho(request, decoded.requestId(), decoded.milestone(), decoded.source());
            } catch (RuntimeException error) {
                throw failure(G2ClientException.Reason.LOCAL_REQUEST_INVALID,
                        "G2 request rejected before HTTP invocation", id, started, tick, encoded, body, info, false, null, error);
            }
            long remaining = budget - (System.nanoTime() - tick);
            if (remaining <= 0) {
                throw failure(G2ClientException.Reason.LOCAL_DEADLINE_EXPIRED,
                        "G2 call budget elapsed before HTTP invocation", id, started, tick, encoded, body, info, false, null, null);
            }
            HttpRequest wireRequest = HttpRequest.newBuilder(endpoint).timeout(Duration.ofNanos(remaining))
                    .header("Content-Type", "application/json; charset=utf-8")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofByteArray(encoded)).build();
            invoked = true;
            CompletableFuture<HttpResponse<byte[]>> exchange = http.sendAsync(wireRequest, metadata -> {
                info.set(metadata);
                return body;
            });
            HttpResponse<byte[]> response;
            try {
                response = exchange.get(Math.max(0, budget - (System.nanoTime() - tick)), TimeUnit.NANOSECONDS);
            } catch (TimeoutException error) {
                body.abort(error);
                exchange.cancel(true);
                throw failure(G2ClientException.Reason.TRANSPORT_UNKNOWN,
                        "G2 evaluation deadline elapsed; no automatic retry or action inference",
                        id, started, tick, encoded, body, info, true, null, error);
            } catch (InterruptedException error) {
                body.abort(error);
                exchange.cancel(true);
                Thread.currentThread().interrupt();
                throw failure(G2ClientException.Reason.TRANSPORT_UNKNOWN,
                        "G2 evaluation interrupted; no automatic retry or action inference",
                        id, started, tick, encoded, body, info, true, null, error);
            } catch (ExecutionException error) {
                Throwable cause = rootCause(error);
                G2ClientException.Reason reason = cause instanceof BoundedG2BodySubscriber.LimitExceeded
                        ? G2ClientException.Reason.RESPONSE_LIMIT_EXCEEDED : G2ClientException.Reason.TRANSPORT_UNKNOWN;
                throw failure(reason, "G2 HTTP exchange did not yield a complete verified response",
                        id, started, tick, encoded, body, info, true, null, cause);
            }
            byte[] raw = response.body();
            try {
                requireHeaders(response.headers());
                if (!body.complete()) throw new IllegalArgumentException("complete response body required");
                if (response.statusCode() == 200) {
                    G2Response result = G2Wire.decodeResponse(raw);
                    requireEcho(request, result.requestId(), result.milestone(), result.source());
                    org.xar.ck3.control.g2.m0.RaiktorRawClient.validateResponse(request, result);
                    return new G2Evaluation(result, evidence(id, started, tick, encoded, body, info, true), raw);
                }
                G2HttpError refusal = G2Wire.decodeError(raw);
                if (refusal.code().httpStatus() != response.statusCode()) {
                    throw new IllegalArgumentException("HTTP status and common typed error code differ");
                }
                throw failure(G2ClientException.Reason.HTTP_REJECTED, refusal.message(),
                        id, started, tick, encoded, body, info, true, refusal, null);
            } catch (G2ClientException error) {
                throw error;
            } catch (RuntimeException error) {
                throw failure(G2ClientException.Reason.RESPONSE_UNVERIFIED,
                        "G2 response headers/schema/request/provenance could not be verified",
                        id, started, tick, encoded, body, info, true, null, error);
            }
        } catch (G2ClientException error) {
            throw error;
        } catch (RuntimeException error) {
            body.abort(error);
            throw failure(invoked ? G2ClientException.Reason.TRANSPORT_UNKNOWN : G2ClientException.Reason.LOCAL_REQUEST_INVALID,
                    "G2 local transport unavailable; no response or action inference",
                    id, started, tick, encoded, body, info, invoked, null, error);
        }
    }

    private G2ClientException failure(G2ClientException.Reason reason, String message, String id,
            Instant started, long tick, byte[] request, BoundedG2BodySubscriber body,
            AtomicReference<HttpResponse.ResponseInfo> info, boolean invoked, G2HttpError refusal, Throwable cause) {
        return new G2ClientException(reason, message, evidence(id, started, tick, request, body, info, invoked),
                refusal, body.retainedBytes(), cause);
    }

    private G2CallEvidence evidence(String id, Instant started, long tick, byte[] request,
            BoundedG2BodySubscriber body, AtomicReference<HttpResponse.ResponseInfo> info, boolean invoked) {
        byte[] retained = body.retainedBytes();
        HttpResponse.ResponseInfo response = info.get();
        return new G2CallEvidence(endpoint, id, started, Instant.now(), Math.max(0, System.nanoTime() - tick),
                request.length, sha256(request), body.observedBytes(), retained.length, sha256(retained),
                response == null ? OptionalInt.empty() : OptionalInt.of(response.statusCode()), body.complete(), invoked);
    }

    private static void requireEcho(G2Request request, String id,
            org.xar.ck3.control.g2.common.Milestone milestone, org.xar.ck3.control.g2.common.G2Source source) {
        if (!request.requestId().equals(id) || request.milestone() != milestone || !request.source().equals(source)) {
            throw new IllegalArgumentException("response must echo the exact request ID, milestone and caller provenance");
        }
    }

    private static void requireHeaders(HttpHeaders headers) {
        String contentType = oneHeader(headers, "Content-Type");
        String[] parts = contentType.split(";", -1);
        if (!"application/json".equals(parts[0].strip().toLowerCase(Locale.ROOT))) {
            throw new IllegalArgumentException("JSON response content type required");
        }
        for (int index = 1; index < parts.length; index++) {
            String parameter = parts[index].strip().toLowerCase(Locale.ROOT);
            if (!"charset=utf-8".equals(parameter) && !"charset=\"utf-8\"".equals(parameter)) {
                throw new IllegalArgumentException("only explicit UTF-8 JSON charset is admitted");
            }
        }
        if (!G2Wire.PRODUCER.equals(oneHeader(headers, "X-Xar-Producer"))
                || !G2Wire.PRODUCER_VERSION.equals(oneHeader(headers, "X-Xar-Producer-Version"))
                || !G2Wire.REQUEST_SCHEMA.equals(oneHeader(headers, "X-Xar-Contract-Revision"))) {
            throw new IllegalArgumentException("exact G2 producer/version/contract headers required");
        }
    }

    private static String oneHeader(HttpHeaders headers, String name) {
        List<String> values = headers.allValues(name);
        if (values.size() != 1) throw new IllegalArgumentException("one original response header required: " + name);
        return values.getFirst();
    }

    private static String sha256(byte[] raw) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("required SHA-256 unavailable", error);
        }
    }

    private static Throwable rootCause(Throwable error) {
        Throwable current = error;
        while (current.getCause() != null && current.getCause() != current) current = current.getCause();
        return current;
    }

    /** Cancels this client's transport only; it never retries or cancels a Game action. */
    @Override public void close() { http.shutdownNow(); }

    private static final class DirectProxySelector extends ProxySelector {
        @Override public List<Proxy> select(URI uri) {
            Objects.requireNonNull(uri, "uri");
            return List.of(Proxy.NO_PROXY);
        }
        @Override public void connectFailed(URI uri, SocketAddress address, IOException error) {
            // The exchange reports its original failure; there is no alternate proxy or retry.
        }
    }
}
