package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.annotation.PreDestroy;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.OPTIONS;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.HttpHeaders;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.core.UriInfo;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.container.PreMatching;
import jakarta.ws.rs.ext.Provider;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ConcurrentHashMap;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Streamable HTTP framing for the directory installed by this same Root lifetime.
 * It cannot install a directory, bootstrap Root, launch Game, or create an application route.
 * HTTP creates no application executor: only PublicMcpSession owns application dispatch.
 */
@Path("/mcp")
@ApplicationScoped
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class PublicMcpHttpResource {
    @Inject PublicMcpHost host;
    @ConfigProperty(name = "xar.mcp.http.response-timeout", defaultValue = "PT5M")
    Duration responseTimeout = Duration.ofMinutes(5);
    private Router router;
    private volatile boolean closing;

    @POST
    public CompletionStage<Response> post(byte[] body, @Context HttpHeaders headers, @Context UriInfo uri) {
        Input input = new Input("POST", uri.getBaseUri(), headers.getRequestHeaders(), body);
        Duration wait = responseTimeout;
        if (wait == null || wait.compareTo(Duration.ofSeconds(1)) < 0 || wait.compareTo(Duration.ofMinutes(10)) > 0)
            return CompletableFuture.completedFuture(response(error(503, null, -32603, "Invalid finite HTTP response window")));
        CompletableFuture<Reply> actual = route(input);
        // Timeout is delivery uncertainty. It does not cancel or replace the retained application future.
        CompletableFuture<Reply> delivery = boundedDelivery(actual, input, wait);
        return delivery.handle((value, failure) -> response(failure == null ? value
                : error(503, idOrNull(input.body()), -32603, "HTTP delivery failed; outcome unconfirmed; do not resend")));
    }

    /** DATA transport timer only; the original application future remains retained and uncancelled. */
    static CompletableFuture<Reply> boundedDelivery(CompletableFuture<Reply> actual, Input input, Duration wait) {
        McpJson.require(wait != null && !wait.isNegative() && !wait.isZero()
                && wait.compareTo(Duration.ofMinutes(10)) <= 0, "Finite HTTP delivery wait required");
        CompletableFuture<Reply> delivery = actual.thenApply(value -> value);
        delivery.completeOnTimeout(error(503, idOrNull(input.body()), -32603,
                "HTTP delivery deadline elapsed; application/world outcome unconfirmed; do not resend"),
                wait.toMillis(), java.util.concurrent.TimeUnit.MILLISECONDS);
        return delivery;
    }

    @GET
    public Response get(@Context HttpHeaders headers, @Context UriInfo uri) {
        return response(methodReply(new Input("GET", uri.getBaseUri(), headers.getRequestHeaders(), new byte[0])));
    }

    @OPTIONS
    public Response options(@Context HttpHeaders headers, @Context UriInfo uri) {
        return response(methodReply(new Input("OPTIONS", uri.getBaseUri(), headers.getRequestHeaders(), new byte[0])));
    }

    /** Every verb at this endpoint crosses the Origin boundary, including verbs rejected before resource selection. */
    @Provider
    @PreMatching
    public static final class OriginBoundary implements ContainerRequestFilter {
        @Override public void filter(ContainerRequestContext context) {
            if (!"mcp".equals(context.getUriInfo().getPath().replaceAll("/+$", ""))) return;
            try {
                origin(new Input(context.getMethod(), context.getUriInfo().getBaseUri(), context.getHeaders(), new byte[0]));
            } catch (IllegalArgumentException invalid) {
                context.abortWith(response(error(403, null, -32600, "Invalid Origin")));
            }
        }
    }

    @DELETE
    public Response delete(@Context HttpHeaders headers, @Context UriInfo uri) {
        return response(methodReply(new Input("DELETE", uri.getBaseUri(), headers.getRequestHeaders(), new byte[0])));
    }

    CompletableFuture<Reply> route(Input input) {
        Reply transport = transportGuard(input);
        if (transport != null) return CompletableFuture.completedFuture(transport);
        PublicMcpDirectory actual = host == null ? null : host.current().orElse(null);
        if (closing || actual == null || actual.scope() != PublicMcpDirectory.Scope.COMPLETE_MIGRATION)
            return CompletableFuture.completedFuture(error(503, idOrNull(input.body()), -32603,
                    "Root has not installed the actual complete public directory"));
        Router same;
        synchronized (this) {
            if (closing) return CompletableFuture.completedFuture(error(503, idOrNull(input.body()), -32603,
                    "Original Root public lifetime is closing; no new call accepted"));
            if (router == null) router = new Router(actual);
            same = router;
        }
        if (same.directory != actual)
            return CompletableFuture.completedFuture(error(503, idOrNull(input.body()), -32603, "Original public directory changed"));
        return same.handle(input);
    }

    /** Finite lifecycle observation; unresolved calls remain original outcomes, never cancellation success. */
    public record Drain(boolean complete, int unresolvedCalls) { }

    public Drain closeAndDrain(Duration maximum) throws InterruptedException {
        McpJson.require(maximum != null && !maximum.isNegative()
                && maximum.compareTo(Duration.ofSeconds(60)) <= 0, "Finite HTTP drain required");
        Router same;
        synchronized (this) { closing = true; same = router; }
        return drainRouter(same, maximum);
    }
    /** Same transport-only drain used by the lifecycle; SOFTWARE_ONLY tests cannot install a Root host. */
    static Drain drainRouter(Router same, Duration maximum) throws InterruptedException {
        McpJson.require(maximum != null && !maximum.isNegative()
                && maximum.compareTo(Duration.ofSeconds(60)) <= 0, "Finite HTTP drain required");
        if (same == null) return new Drain(true, 0);
        Closed result = same.close(maximum);
        return new Drain(result.complete(), result.unresolvedCalls());
    }

    @PreDestroy
    void close() {
        try {
            Drain result = closeAndDrain(Duration.ofSeconds(30));
            System.err.println("MCP_HTTP_DRAIN complete=" + result.complete() + " unresolved_calls=" + result.unresolvedCalls());
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            System.err.println("MCP_HTTP_DRAIN interrupted; original application outcomes remain unconfirmed; do not resend");
        }
    }

    static Response response(Reply reply) {
        Response.ResponseBuilder result = Response.status(reply.status());
        reply.headers().forEach(result::header);
        if (reply.body().length != 0) result.type(MediaType.APPLICATION_JSON_TYPE).entity(reply.body());
        return result.build();
    }

    record Input(String method, URI endpoint, Map<String, List<String>> headers, byte[] body) {
        Input {
            Map<String, List<String>> copy = new LinkedHashMap<>();
            headers.forEach((name, values) -> copy.computeIfAbsent(name.toLowerCase(Locale.ROOT), ignored -> new ArrayList<>()).addAll(values));
            copy.replaceAll((name, values) -> List.copyOf(values));
            headers = Map.copyOf(copy);
            body = body == null ? new byte[0] : body.clone();
        }
        @Override public byte[] body() { return body.clone(); }
        String one(String name) {
            List<String> values = headers.get(name.toLowerCase(Locale.ROOT));
            if (values == null) return null;
            if (values.size() != 1) throw new Boundary("One " + name + " header required");
            return values.getFirst();
        }
    }
    record Reply(int status, Map<String, String> headers, byte[] body) {
        Reply { headers = Map.copyOf(headers); body = body.clone(); }
        @Override public byte[] body() { return body.clone(); }
    }
    record Closed(boolean complete, int unresolvedCalls) { }
    private static final class Boundary extends IllegalArgumentException {
        Boundary(String message) { super(message); }
    }
    private static final class BadInput extends IllegalArgumentException {
        final int code;
        final byte[] id;
        BadInput(int code, byte[] id) { this.code = code; this.id = id; }
    }
    private record Parsed(byte[] original, ObjectNode row, ObjectNode params, String method, String idKey, byte[] id) { }

    static Reply methodReply(Input input) {
        try { origin(input); }
        catch (IllegalArgumentException invalid) { return error(403, null, -32600, "Invalid Origin"); }
        return new Reply(405, Map.of("Allow", "POST", "Cache-Control", "no-store"), new byte[0]);
    }
    static Reply transportGuard(Input input) {
        try { origin(input); }
        catch (IllegalArgumentException invalid) { return error(403, null, -32600, "Invalid Origin"); }
        if (!"POST".equals(input.method())) return methodReply(input);
        try {
            String content = input.one("content-type");
            MediaType type = content == null ? null : MediaType.valueOf(content);
            if (type == null || !type.getType().equalsIgnoreCase("application") || !type.getSubtype().equalsIgnoreCase("json")
                    || type.getParameters().containsKey("charset") && !type.getParameters().get("charset").equalsIgnoreCase("utf-8"))
                return error(415, null, -32600, "Content-Type application/json with UTF-8 required");
        } catch (IllegalArgumentException invalid) { return error(415, null, -32600, "Invalid Content-Type"); }
        try {
            boolean json = false, stream = false;
            List<String> accepts = input.headers().get("accept");
            if (accepts != null) for (String value : accepts) for (String part : value.split(",")) {
                MediaType type = MediaType.valueOf(part.strip());
                BigDecimal quality = new BigDecimal(type.getParameters().getOrDefault("q", "1"));
                if (quality.signum() < 0 || quality.compareTo(BigDecimal.ONE) > 0) throw new Boundary("Invalid Accept quality");
                if (quality.signum() == 0) continue;
                json |= type.getType().equalsIgnoreCase("application") && type.getSubtype().equalsIgnoreCase("json");
                stream |= type.getType().equalsIgnoreCase("text") && type.getSubtype().equalsIgnoreCase("event-stream");
            }
            if (!json || !stream) return error(406, null, -32600, "Accept must list application/json and text/event-stream");
        } catch (IllegalArgumentException invalid) { return error(406, null, -32600, "Invalid Accept"); }
        if (input.body().length == 0 || input.body().length > McpJson.INPUT_MAX)
            return error(400, null, -32700, "Bounded JSON-RPC body required");
        return null;
    }
    private static void origin(Input input) {
        String raw = input.one("origin");
        if (raw == null) return;
        URI value = URI.create(raw);
        String host = value.getHost();
        int expectedPort = port(input.endpoint()), actualPort = port(value);
        if (!Set.of("127.0.0.1", "localhost", "::1", "[::1]").contains(host == null ? "" : host.toLowerCase(Locale.ROOT))
                || value.getScheme() == null || !value.getScheme().equalsIgnoreCase(input.endpoint().getScheme())
                || expectedPort != actualPort || value.getRawUserInfo() != null || value.getRawQuery() != null
                || value.getRawFragment() != null || value.getRawPath() != null && !value.getRawPath().isEmpty())
            throw new Boundary("Origin must be the local endpoint origin");
    }
    private static int port(URI uri) {
        return uri.getPort() >= 0 ? uri.getPort() : "https".equalsIgnoreCase(uri.getScheme()) ? 443 : 80;
    }

    /** Software protocol tests may supply SOFTWARE_ONLY here; that cannot install into PublicMcpHost. */
    static final class Router {
        private static final int MAX_PEERS = 16;
        final PublicMcpDirectory directory;
        private final Set<Peer> peers = ConcurrentHashMap.newKeySet();
        private final Map<String, Peer> legacy = new ConcurrentHashMap<>();
        private volatile boolean closed;
        Router(PublicMcpDirectory directory) { this.directory = java.util.Objects.requireNonNull(directory); }

        CompletableFuture<Reply> handle(Input input) {
            Reply rejected = transportGuard(input);
            if (rejected != null) return CompletableFuture.completedFuture(rejected);
            Parsed request;
            try { request = parse(input.body()); }
            catch (BadInput invalid) { return CompletableFuture.completedFuture(error(400, invalid.id, invalid.code, "Invalid JSON-RPC request")); }
            if (closed) return CompletableFuture.completedFuture(error(503, request.id(), -32603, "HTTP owner scope closed"));
            try {
                String version = input.one("mcp-protocol-version");
                boolean modernMeta = request.params().hasNonNull("_meta")
                        && McpJson.object(request.params().get("_meta")).has(PublicMcpSession.VERSION_KEY);
                if (version != null && !version.equals(PublicMcpSession.MODERN) && !PublicMcpSession.LEGACY.contains(version))
                    return CompletableFuture.completedFuture(unsupported(request.id()));
                boolean modern = PublicMcpSession.MODERN.equals(version) || modernMeta;
                if (modern) {
                    if (request.id() != null) {
                        if (!PublicMcpSession.MODERN.equals(version)
                                || !PublicMcpSession.MODERN.equals(McpJson.text(McpJson.object(request.params().get("_meta")).get(PublicMcpSession.VERSION_KEY))))
                            throw new Boundary("Protocol version header/body mismatch");
                        standardHeaders(input, request, true);
                        if (request.method().equals("initialize"))
                            return CompletableFuture.completedFuture(error(404, request.id(), -32601, "Modern HTTP has no initialize method"));
                    } else {
                        if (!PublicMcpSession.MODERN.equals(version)) throw new Boundary("Notification protocol version required");
                        standardHeaders(input, request, false);
                        if (request.method().equals("notifications/cancelled"))
                            return CompletableFuture.completedFuture(error(400, null, -32600, "Modern HTTP cancellation is not a stdio notification"));
                    }
                    Peer peer = create(null);
                    return peer.accept(request, true);
                }
                standardHeaders(input, request, false);
                String session = input.one("mcp-session-id");
                Peer peer;
                if (session == null) {
                    if (!request.method().equals("initialize") || request.id() == null)
                        return CompletableFuture.completedFuture(error(400, request.id(), -32600, "Actual legacy initialization and session id required"));
                    peer = create(UUID.randomUUID().toString());
                } else {
                    peer = legacy.get(session);
                    if (peer == null) return CompletableFuture.completedFuture(error(404, request.id(), -32600, "Unknown legacy session"));
                    if (version != null && !version.equals(peer.version))
                        return CompletableFuture.completedFuture(error(400, request.id(), -32600, "Legacy version differs from actual initialization"));
                }
                return peer.accept(request, false);
            } catch (Boundary mismatch) {
                return CompletableFuture.completedFuture(error(400, request.id(), -32020, "Header mismatch"));
            } catch (IllegalArgumentException malformed) {
                return CompletableFuture.completedFuture(error(400, request.id(), -32020, "Malformed protocol header or metadata"));
            } catch (RuntimeException unavailable) {
                return CompletableFuture.completedFuture(error(503, request.id(), -32603, "Actual public directory unavailable; no automatic retry"));
            }
        }
        private synchronized Peer create(String sessionId) {
            if (closed || peers.size() >= MAX_PEERS) throw new IllegalStateException("Bounded HTTP peer capacity unavailable");
            Peer peer = new Peer(sessionId);
            peers.add(peer);
            return peer;
        }

        private final class Exchange {
            final Parsed request;
            final CompletableFuture<Reply> reply = new CompletableFuture<>();
            byte[] packet;
            Exchange(Parsed request) { this.request = request; }
        }
        private final class Peer {
            final String sessionId;
            final Map<String, Exchange> exchanges = new HashMap<>();
            final PublicMcpSession session;
            volatile String version;
            Peer(String sessionId) {
                this.sessionId = sessionId;
                session = new PublicMcpSession(directory, this::packet, new PublicMcpSession.HttpLifecycle() {
                    @Override public void callFinished(String key) { finish(key); }
                    @Override public void terminated() {
                        peers.remove(Peer.this);
                        if (Peer.this.sessionId != null) legacy.remove(Peer.this.sessionId, Peer.this);
                    }
                });
            }
            CompletableFuture<Reply> accept(Parsed request, boolean oneShot) {
                if (session.outputFailure().isPresent())
                    return CompletableFuture.completedFuture(error(503, request.id(), -32603,
                            "Original protocol output failed; retained outcomes unconfirmed; do not resend"));
                if (request.id() == null) {
                    try {
                        validateNotification(request);
                        session.receive(request.original());
                        return CompletableFuture.completedFuture(new Reply(202, Map.of("Cache-Control", "no-store"), new byte[0]));
                    } catch (IllegalArgumentException malformed) {
                        return CompletableFuture.completedFuture(error(400, null, -32602, "Invalid notification parameters"));
                    } finally { if (oneShot) session.finishHttpInput(); }
                }
                Exchange exchange;
                synchronized (this) {
                    if (exchanges.containsKey(request.idKey()))
                        return CompletableFuture.completedFuture(error(400, request.id(), -32600, "Duplicate in-flight id; original call retained"));
                    exchange = new Exchange(request);
                    exchanges.put(request.idKey(), exchange);
                }
                try {
                    // Never enter Session while holding Peer: Session publication calls Peer.packet.
                    session.receive(request.original());
                    if (!session.httpPending(request.idKey())) finish(request.idKey(), exchange);
                } catch (RuntimeException failure) {
                    synchronized (this) { exchanges.remove(request.idKey(), exchange); }
                    exchange.reply.complete(error(503, request.id(), -32603, "Protocol delivery failed; outcome unconfirmed; do not resend"));
                } finally { if (oneShot) session.finishHttpInput(); }
                return exchange.reply;
            }
            synchronized void packet(byte[] line) throws IOException {
                if (line.length == 0 || line[line.length - 1] != '\n') throw new IOException("Complete MCP frame required");
                byte[] body = Arrays.copyOf(line, line.length - 1);
                ObjectNode value;
                String key;
                try { value = McpJson.object(McpJson.parseResult(body)); key = idKey(value.get("id")); }
                catch (IllegalArgumentException malformed) { throw new IOException("Uncorrelated MCP response", malformed); }
                Exchange exchange = exchanges.get(key);
                if (exchange == null || exchange.packet != null) throw new IOException("Original HTTP exchange unavailable");
                exchange.packet = body;
            }
            void finish(String key) { finish(key, null); }
            private void finish(String key, Exchange expected) {
                Exchange exchange;
                synchronized (this) {
                    exchange = exchanges.get(key);
                    if (exchange == null || expected != null && exchange != expected) return;
                    exchanges.remove(key, exchange);
                }
                if (exchange.packet == null) {
                    exchange.reply.complete(error(503, exchange.request.id(), -32603, "Application reply unavailable; outcome unconfirmed; do not resend"));
                    return;
                }
                ObjectNode value = McpJson.object(McpJson.parseResult(exchange.packet));
                Map<String, String> headers = new HashMap<>();
                headers.put("Cache-Control", "no-store");
                if (sessionId != null && exchange.request.method().equals("initialize")) {
                    if (value.hasNonNull("result")) {
                        String selected = McpJson.text(value.get("result").get("protocolVersion"));
                        if (!PublicMcpSession.LEGACY.contains(selected)) {
                            exchange.reply.complete(error(503, exchange.request.id(), -32603, "Original legacy negotiation unavailable"));
                            session.finishHttpInput(); return;
                        }
                        version = selected;
                        legacy.put(sessionId, this);
                        headers.put("MCP-Session-Id", sessionId);
                    } else session.finishHttpInput();
                }
                int status = sessionId == null && value.path("error").path("code").asInt() == -32601 ? 404 : 200;
                exchange.reply.complete(new Reply(status, headers, exchange.packet));
            }
            private void validateNotification(Parsed request) {
                ObjectNode p = request.params();
                if (request.method().equals("notifications/initialized")) McpJson.fields(p, Set.of("_meta"), Set.of());
                if (request.method().equals("notifications/cancelled")) {
                    McpJson.fields(p, Set.of("requestId", "reason", "_meta"), Set.of());
                    if (!p.hasNonNull("requestId")) McpJson.require("2025-11-25".equals(version), "Cancellation request id required");
                    else idKey(p.get("requestId"));
                    if (p.hasNonNull("reason")) McpJson.text(p.get("reason"));
                }
                if (p.hasNonNull("_meta")) McpJson.object(p.get("_meta"));
            }
        }
        Closed close(Duration maximum) throws InterruptedException {
            McpJson.require(maximum != null && !maximum.isNegative() && maximum.compareTo(Duration.ofSeconds(60)) <= 0, "Finite HTTP drain required");
            List<Peer> admitted;
            synchronized (this) { closed = true; admitted = List.copyOf(peers); }
            long stop = System.nanoTime() + maximum.toNanos();
            boolean complete = true;
            int unresolved = 0;
            for (Peer peer : admitted) {
                Duration remaining = Duration.ofNanos(Math.max(0, stop - System.nanoTime()));
                PublicMcpSession.Drain actual = peer.session.closeAndDrain(remaining);
                complete &= actual.complete(); unresolved += actual.unresolvedCalls();
            }
            return new Closed(complete, unresolved);
        }
    }

    private static Parsed parse(byte[] original) {
        JsonNode parsed;
        try { parsed = McpJson.parse(original); }
        catch (IllegalArgumentException invalid) { throw new BadInput(-32700, null); }
        ObjectNode row;
        String method, key;
        byte[] id;
        try {
            row = McpJson.object(parsed);
            McpJson.fields(row, Set.of("jsonrpc", "id", "method", "params"), Set.of("jsonrpc", "method"));
            McpJson.require("2.0".equals(McpJson.text(row.get("jsonrpc"))), "JSON-RPC 2.0 required");
            method = McpJson.text(row.get("method"));
            McpJson.require(!method.isEmpty(), "Method required");
            id = row.has("id") ? McpJson.token(original, "id") : null;
            key = id == null ? null : idKey(row.get("id"));
        } catch (IllegalArgumentException invalid) { throw new BadInput(-32600, null); }
        ObjectNode params;
        try { params = row.hasNonNull("params") ? McpJson.object(row.get("params")) : McpJson.object(); }
        catch (IllegalArgumentException invalid) { throw new BadInput(-32602, id); }
        return new Parsed(original, row, params, method, key, id);
    }
    private static String idKey(JsonNode id) {
        if (id != null && id.isTextual()) return "s:" + id.textValue();
        McpJson.require(id != null && id.isIntegralNumber()
                && id.bigIntegerValue().abs().compareTo(BigInteger.valueOf(9_007_199_254_740_991L)) <= 0, "Exact JS-safe RPC id required");
        return "n:" + id.bigIntegerValue();
    }
    private static byte[] idOrNull(byte[] body) {
        try { return parse(body).id(); } catch (IllegalArgumentException invalid) { return null; }
    }
    private static void standardHeaders(Input input, Parsed request, boolean required) {
        String method = input.one("mcp-method");
        if ((required || method != null) && !request.method().equals(method)) throw new Boundary("Mcp-Method mismatch");
        String source = switch (request.method()) {
            case "tools/call", "prompts/get" -> "name";
            case "resources/read" -> "uri";
            default -> null;
        };
        String name = input.one("mcp-name");
        if (source == null) { if (name != null) throw new Boundary("Unexpected Mcp-Name"); }
        else if ((required || name != null) && (name == null || !McpJson.text(request.params().get(source)).equals(headerText(name))))
            throw new Boundary("Mcp-Name mismatch");
    }
    private static String headerText(String raw) {
        McpJson.require(raw != null && raw.chars().allMatch(c -> c == 9 || c >= 32 && c <= 126), "ASCII HTTP header required");
        if (raw.startsWith("=?base64?") && raw.endsWith("?=")) {
            try {
                byte[] bytes = Base64.getDecoder().decode(raw.substring(9, raw.length() - 2));
                return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            } catch (IllegalArgumentException | java.nio.charset.CharacterCodingException invalid) { throw new Boundary("Invalid UTF-8 Base64 sentinel"); }
        }
        if (!raw.equals(raw.strip())) throw new Boundary("Whitespace value requires Base64");
        return raw;
    }
    private static Reply unsupported(byte[] id) {
        byte[] data = McpJson.utf8("{\"supported\":[\"2026-07-28\",\"2024-11-05\",\"2025-03-26\",\"2025-06-18\",\"2025-11-25\"]}");
        return error(400, id, -32022, "Unsupported protocol version", data);
    }
    private static Reply error(int status, byte[] id, int code, String message) {
        return error(status, id, code, message, null);
    }
    private static Reply error(int status, byte[] id, int code, String message, byte[] data) {
        byte[] extra = data == null ? new byte[0] : McpJson.join(McpJson.utf8(",\"data\":"), data);
        byte[] body = McpJson.join(McpJson.utf8("{\"jsonrpc\":\"2.0\",\"id\":"), id == null ? McpJson.utf8("null") : id,
                McpJson.utf8(",\"error\":{\"code\":" + code + ",\"message\":"), McpJson.quote(message), extra, McpJson.utf8("}}"));
        return new Reply(status, Map.of("Cache-Control", "no-store"), body);
    }
}
