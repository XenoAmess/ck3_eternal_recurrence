package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** One stdio peer; application calls serialize while the read thread can still receive cancellation and ping. */
public final class PublicMcpSession {
    public static final String SERVER_NAME = "Xar CK3 Gameplay Bridge";
    public static final String SERVER_VERSION = "0.1.0";
    public static final String INSTRUCTIONS = "Control the current one-life CK3 episode through semantic steps. Use ck3_plan_turn unless a specific gameplay step is requested.";
    public static final String MODERN = "2026-07-28";
    public static final String VERSION_KEY = "io.modelcontextprotocol/protocolVersion";
    public static final String CLIENT_CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities";
    public static final String SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo";
    public static final List<String> LEGACY = List.of("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25");
    @FunctionalInterface public interface Sink { void write(byte[] completeLine) throws IOException; }
    public record Drain(boolean complete, long completedCalls, int unresolvedCalls) { }
    private enum Era { UNDECIDED, LEGACY, MODERN }
    private record Id(String key, byte[] original) {
        Id { original = original.clone(); }
        @Override public byte[] original() { return original.clone(); }
    }
    private record Pending(Id id, String tool, boolean modern, McpCancellation cancellation) { }
    private final PublicMcpDirectory directory;
    private final List<ToolDescriptor> tools;
    private final List<ResourceDescriptor> resources;
    private final Sink sink;
    private final ThreadPoolExecutor worker;
    private final ConcurrentHashMap<String,Pending> pending = new ConcurrentHashMap<>();
    private final AtomicLong completed = new AtomicLong();
    private volatile IOException outputFailure;
    private volatile boolean closed;
    private Era era = Era.UNDECIDED;
    private boolean initialized;
    private String version = "2025-03-26";

    public PublicMcpSession(PublicMcpDirectory directory, Sink sink) {
        this.directory = Objects.requireNonNull(directory); this.sink = Objects.requireNonNull(sink);
        tools = List.copyOf(directory.tools());
        resources = List.copyOf(directory.resources());
        McpJson.require(tools.stream().map(ToolDescriptor::name).distinct().count() == tools.size(), "duplicate admitted MCP descriptor");
        McpJson.require(resources.stream().map(ResourceDescriptor::uri).distinct().count() == resources.size(), "duplicate admitted resource");
        worker = new ThreadPoolExecutor(1, 1, 0, TimeUnit.MILLISECONDS, new ArrayBlockingQueue<>(16), task -> {
            Thread thread = new Thread(task, "xar-public-mcp-application"); thread.setDaemon(true); return thread;
        }, new ThreadPoolExecutor.AbortPolicy());
    }
    /** Input is one complete JSON value without the transport LF; no source of authority is accepted here. */
    public void receive(byte[] payload) {
        McpJson.require(!closed, "stdio session already closed");
        if (payload == null || payload.length == 0 || payload.length > McpJson.INPUT_MAX) { error(null, -32700, "Parse error", Optional.empty()); return; }
        JsonNode parsed;
        try { parsed = McpJson.parse(payload); }
        catch (IllegalArgumentException invalid) { error(null, -32700, "Parse error", Optional.empty()); return; }
        ObjectNode row; String method; Id id = null;
        try {
            row = McpJson.object(parsed);
            McpJson.fields(row, Set.of("jsonrpc", "id", "method", "params"), Set.of("jsonrpc", "method"));
            McpJson.require("2.0".equals(McpJson.text(row.get("jsonrpc"))), "JSON-RPC 2.0 required");
            method = McpJson.text(row.get("method")); McpJson.require(!method.isEmpty(), "method required");
            if (row.has("id")) id = id(row.get("id"), McpJson.token(payload, "id"));
        } catch (IllegalArgumentException invalid) { error(null, -32600, "Invalid Request", Optional.empty()); return; }
        if (id == null) {
            try { notification(method, params(row)); }
            catch (IllegalArgumentException malformed) { System.err.println("Dropped malformed MCP notification: " + method); }
            return;
        }
        try {
            ObjectNode params = params(row);
            boolean hasEnvelope = params.hasNonNull("_meta") && McpJson.object(params.get("_meta")).has(VERSION_KEY);
            if (era == Era.UNDECIDED) era = !method.equals("initialize") && hasEnvelope ? Era.MODERN : Era.LEGACY;
            if (era == Era.MODERN && method.equals("initialize")) {
                ObjectNode data = McpJson.object(); data.putArray("supported").add(MODERN);
                if (params.path("protocolVersion").isTextual()) data.put("requested", params.get("protocolVersion").textValue());
                throw rpc(-32022, "connection is serving the 2026-07-28 protocol; the initialize handshake is not accepted", data);
            }
            if (era == Era.LEGACY && !method.equals("initialize") && hasEnvelope)
                throw rpc(-32600, "this connection serves the handshake protocol era; requests carrying the 2026-07-28 envelope are not accepted on it");
            boolean modern = era == Era.MODERN;
            if (modern) modernEnvelope(params);
            switch (method) {
                case "initialize" -> initialize(id, params);
                case "ping" -> { noArguments(params, Set.of("_meta")); result(id, McpJson.utf8("{}"), modern); }
                case "tools/list" -> { admitted(); list(id, params, modern); }
                case "tools/call" -> { admitted(); call(id, params, row.hasNonNull("params") ? McpJson.token(payload, "params") : McpJson.utf8("{}"), modern); }
                case "resources/list" -> { admitted(); resourceList(id, params, modern); }
                case "resources/read" -> { admitted(); read(id, params, row.hasNonNull("params") ? McpJson.token(payload, "params") : McpJson.utf8("{}"), modern); }
                case "server/discover" -> {
                    if (!modern) throw rpc(-32601, "Method not found", McpJson.quote(method));
                    noArguments(params, Set.of("_meta"));
                    byte[] discovery = McpJson.join(McpJson.utf8("{\"supportedVersions\":[\"" + MODERN + "\"],\"capabilities\":"), capabilities(),
                            McpJson.utf8(",\"instructions\":"), McpJson.quote(INSTRUCTIONS), McpJson.utf8("}"));
                    result(id, listDefaults(discovery, true), true);
                }
                case "resources/templates/list", "prompts/list" -> {
                    admitted(); pagination(params);
                    String field = method.equals("resources/list") ? "resources" : method.equals("prompts/list") ? "prompts" : "resourceTemplates";
                    result(id, listDefaults(McpJson.utf8("{\"" + field + "\":[]}"), modern), modern);
                }
                default -> throw rpc(-32601, "Method not found", McpJson.quote(method));
            }
        } catch (RpcFailure failure) { error(id, failure.code(), failure.getMessage(), failure.data()); }
        catch (IllegalArgumentException malformed) { error(id, -32602, "Invalid request parameters", Optional.empty()); }
    }
    private static ObjectNode params(ObjectNode row) {
        return !row.has("params") || row.get("params").isNull() ? McpJson.object() : McpJson.object(row.get("params"));
    }
    private void initialize(Id id, ObjectNode params) {
        McpJson.fields(params, Set.of("protocolVersion", "capabilities", "clientInfo", "_meta"), Set.of("protocolVersion", "capabilities", "clientInfo"));
        String offered = McpJson.text(params.get("protocolVersion")); McpJson.object(params.get("capabilities"));
        ObjectNode info = McpJson.object(params.get("clientInfo")); McpJson.text(info.get("name")); McpJson.text(info.get("version"));
        String selected = LEGACY.contains(offered) ? offered : LEGACY.get(LEGACY.size() - 1);
        byte[] response = McpJson.join(McpJson.utf8("{\"protocolVersion\":"), McpJson.quote(selected), McpJson.utf8(",\"capabilities\":"), capabilities(),
                McpJson.utf8(",\"serverInfo\":"), serverInfo(), McpJson.utf8(",\"instructions\":"), McpJson.quote(INSTRUCTIONS), McpJson.utf8("}"));
        result(id, response, false); initialized = true; version = selected;
    }
    private void admitted() throws RpcFailure {
        if (era != Era.MODERN && !initialized) throw rpc(-32602, "Invalid request parameters", McpJson.quote(""));
    }
    private static void noArguments(ObjectNode params, Set<String> allowed) { McpJson.fields(params, allowed, Set.of()); }
    private static void pagination(ObjectNode params) {
        McpJson.fields(params, Set.of("_meta", "cursor"), Set.of());
        // The original MCPServer has one complete list and ignores its optional cursor.
        if (params.hasNonNull("cursor")) McpJson.text(params.get("cursor"));
    }
    private void list(Id id, ObjectNode params, boolean modern) throws RpcFailure {
        pagination(params); requireMetadata(tools,directory::tools);
        ByteArrayOutputStream out = new ByteArrayOutputStream(); out.writeBytes(McpJson.utf8("{\"tools\":["));
        boolean first = true;
        for (ToolDescriptor descriptor : tools) { if (!first) out.write(','); first = false; out.writeBytes(descriptor.original().bytes()); }
        out.writeBytes(McpJson.utf8("]}")); requireMetadata(tools,directory::tools);
        result(id, listDefaults(McpJson.bounded(out.toByteArray()), modern), modern);
    }
    private void resourceList(Id id, ObjectNode params, boolean modern) throws RpcFailure {
        pagination(params); requireMetadata(resources,directory::resources);
        ByteArrayOutputStream out = new ByteArrayOutputStream(); out.writeBytes(McpJson.utf8("{\"resources\":["));
        boolean first = true;
        for (ResourceDescriptor descriptor : resources) { if (!first) out.write(','); first = false; out.writeBytes(descriptor.original().bytes()); }
        out.writeBytes(McpJson.utf8("]}")); requireMetadata(resources,directory::resources);
        result(id, listDefaults(McpJson.bounded(out.toByteArray()), modern), modern);
    }
    /** Re-enter the real directory guard for each metadata request, including after response construction.
     * Protocol ping/cancellation remain available; source failure must not terminate the stdio receive loop. */
    private <T> void requireMetadata(List<T> retained,java.util.function.Supplier<List<T>> current) throws RpcFailure {
        try {
            if(!retained.equals(List.copyOf(current.get())))
                throw rpc(-32603,"admitted public metadata changed; no application invocation occurred");
        } catch(UncheckedIOException unavailable) {
            throw rpc(-32603,"admitted public metadata inputs unavailable; no application invocation occurred");
        }
    }
    private static byte[] listDefaults(byte[] body, boolean modern) {
        return modern ? McpJson.member(McpJson.member(body, "ttlMs", McpJson.utf8("0")), "cacheScope", McpJson.quote("private")) : body;
    }
    private void read(Id id, ObjectNode params, byte[] originalParams, boolean modern) throws RpcFailure {
        McpJson.fields(params, Set.of("uri", "_meta"), Set.of("uri")); String uri = McpJson.text(params.get("uri"));
        if (resources.stream().noneMatch(resource -> resource.uri().equals(uri))) throw rpc(-32602, "Unknown resource: " + uri);
        Optional<RawJson> meta = params.hasNonNull("_meta") ? Optional.of(new RawJson(McpJson.token(originalParams, "_meta"))) : Optional.empty();
        Pending attempt = new Pending(id, uri, modern, new McpCancellation());
        if (pending.putIfAbsent(id.key(), attempt) != null) throw rpc(-32600, "duplicate in-flight request id; original application call retained");
        try { worker.execute(() -> invokeResource(attempt, new ResourceCall(uri, meta, attempt.cancellation()))); }
        catch (RejectedExecutionException full) { pending.remove(id.key(), attempt); throw rpc(-32000, "bounded application call queue is full; no application invocation occurred"); }
    }
    private void invokeResource(Pending attempt, ResourceCall call) {
        try {
            if (call.cancellation().requested()) throw new ToolFailure("resource request cancelled before application read");
            result(attempt.id(), listDefaults(directory.read(call).bytes(), attempt.modern()), attempt.modern());
        } catch (RpcFailure failure) { error(attempt.id(), failure.code(), failure.getMessage(), failure.data()); }
        catch (ToolFailure failure) { error(attempt.id(), -32603, failure.getMessage(), Optional.empty()); }
        catch (RuntimeException failure) { error(attempt.id(), -32603, "Resource reader failed; result unconfirmed", Optional.empty()); }
        finally { completed.incrementAndGet(); pending.remove(attempt.id().key(), attempt); }
    }
    private void call(Id id, ObjectNode params, byte[] originalParams, boolean modern) throws RpcFailure {
        McpJson.fields(params, Set.of("name", "arguments", "_meta"), Set.of("name"));
        String name = McpJson.text(params.get("name"));
        try { McpJson.toolName(name); }
        catch (IllegalArgumentException retiredOrInvalid) { throw rpc(-32602, retiredOrInvalid.getMessage()); }
        Presence presence = !params.has("arguments") ? Presence.MISSING : params.get("arguments").isNull() ? Presence.NULL : Presence.VALUE;
        Optional<RawJson> raw = presence == Presence.MISSING ? Optional.empty() : Optional.of(new RawJson(McpJson.token(originalParams, "arguments")));
        Arguments arguments = new Arguments(presence, raw);
        Optional<RawJson> meta = params.hasNonNull("_meta") ? Optional.of(new RawJson(McpJson.token(originalParams, "_meta"))) : Optional.empty();
        Pending attempt = new Pending(id, name, modern, new McpCancellation());
        if (pending.putIfAbsent(id.key(), attempt) != null) throw rpc(-32600, "duplicate in-flight request id; original application call retained");
        try { worker.execute(() -> invoke(attempt, new ToolCall(name, arguments, meta, attempt.cancellation()))); }
        catch (RejectedExecutionException full) {
            pending.remove(id.key(), attempt); throw rpc(-32000, "bounded application call queue is full; no application invocation occurred");
        }
    }
    private void invoke(Pending attempt, ToolCall call) {
        try {
            if (call.cancellation().requested()) throw new ToolFailure("request cancelled before application dispatch; no application invocation occurred");
            CallResult actual = directory.invoke(call);
            result(attempt.id(), McpJson.withoutResult(actual.bytes(), Set.of("ttlMs", "cacheScope")), attempt.modern());
        } catch (ToolFailure failure) {
            String message = failure.getMessage().startsWith("Unknown tool:") ? failure.getMessage() : "Error executing tool " + attempt.tool() + ": " + failure.getMessage();
            result(attempt.id(), toolError(message), attempt.modern());
        } catch (RpcFailure failure) { error(attempt.id(), failure.code(), failure.getMessage(), failure.data()); }
        catch (RuntimeException failure) {
            // A Java failure after dispatch cannot prove rejection or cancellation. Preserve that distinction to the client.
            result(attempt.id(), toolError("Error executing tool " + attempt.tool() + ": " + failure.getClass().getSimpleName()
                    + "; application/world outcome unconfirmed; do not resend"), attempt.modern());
        } finally { completed.incrementAndGet(); pending.remove(attempt.id().key(), attempt); }
    }
    private void notification(String method, ObjectNode params) {
        if (method.equals("notifications/initialized")) { noArguments(params, Set.of("_meta")); return; }
        if (!method.equals("notifications/cancelled") || era == Era.LEGACY && !initialized) return;
        McpJson.fields(params, Set.of("requestId", "reason", "_meta"), Set.of());
        if (!params.hasNonNull("requestId")) {
            McpJson.require(era == Era.LEGACY && version.equals("2025-11-25"), "cancellation requestId required for this protocol"); return;
        }
        Id id = id(params.get("requestId"), McpJson.encode(params.get("requestId")));
        Optional<String> reason = params.hasNonNull("reason") ? Optional.of(McpJson.text(params.get("reason"))) : Optional.empty();
        Pending actual = pending.get(id.key()); if (actual != null) actual.cancellation().request(reason);
    }
    private static void modernEnvelope(ObjectNode params) throws RpcFailure {
        if (!params.hasNonNull("_meta")) throw rpc(-32602, "modern request requires _meta envelope");
        ObjectNode meta = McpJson.object(params.get("_meta"));
        if (!meta.has(VERSION_KEY) || !meta.has(CLIENT_CAPABILITIES_KEY)) throw rpc(-32602, "modern request requires protocolVersion and clientCapabilities metadata");
        String requested = McpJson.text(meta.get(VERSION_KEY)); McpJson.object(meta.get(CLIENT_CAPABILITIES_KEY));
        if (!MODERN.equals(requested)) {
            ObjectNode data = McpJson.object().put("requested", requested); data.putArray("supported").add(MODERN);
            throw rpc(-32022, "Unsupported protocol version", data);
        }
        if (meta.hasNonNull("io.modelcontextprotocol/clientInfo")) {
            ObjectNode info = McpJson.object(meta.get("io.modelcontextprotocol/clientInfo")); McpJson.text(info.get("name")); McpJson.text(info.get("version"));
        }
    }
    private static Id id(JsonNode node, byte[] raw) {
        if (node != null && node.isTextual()) return new Id("s:" + node.textValue(), raw);
        McpJson.require(node != null && node.isIntegralNumber(), "JSON-RPC id must be an exact integer or string");
        McpJson.require(node.bigIntegerValue().abs().compareTo(java.math.BigInteger.valueOf(9_007_199_254_740_991L)) <= 0,
                "numeric JSON-RPC id must be JS-safe; use a string for a full-width identifier");
        return new Id("n:" + node.bigIntegerValue().toString(), raw);
    }
    private static byte[] capabilities() { return McpJson.utf8("{\"experimental\":{},\"prompts\":{\"listChanged\":false},\"resources\":{\"subscribe\":false,\"listChanged\":false},\"tools\":{\"listChanged\":false},\"extensions\":{}}"); }
    private static byte[] serverInfo() { return McpJson.utf8("{\"name\":\"" + SERVER_NAME + "\",\"version\":\"" + SERVER_VERSION + "\"}"); }
    private static byte[] toolError(String message) {
        return McpJson.join(McpJson.utf8("{\"content\":[{\"type\":\"text\",\"text\":"), McpJson.quote(message), McpJson.utf8("}],\"isError\":true,\"resultType\":\"complete\"}"));
    }
    private void result(Id id, byte[] original, boolean modern) {
        // The original SDK sieves complete-result vocabulary out of every handshake-era response.
        byte[] actual = modern ? original : McpJson.withoutResult(original, Set.of("resultType", "ttlMs", "cacheScope"));
        if (modern) {
            ObjectNode row = McpJson.object(McpJson.parseResult(actual));
            if (!row.hasNonNull("resultType")) actual = McpJson.memberResult(actual, "resultType", McpJson.quote("complete"));
            byte[] meta = row.hasNonNull("_meta") ? McpJson.tokenResult(original, "_meta") : McpJson.utf8("{}");
            ObjectNode metadata = McpJson.object(McpJson.parse(meta));
            if (!metadata.hasNonNull(SERVER_INFO_KEY)) actual = McpJson.memberResult(actual, "_meta", McpJson.member(meta, SERVER_INFO_KEY, serverInfo()));
        }
        emit(McpJson.join(McpJson.utf8("{\"jsonrpc\":\"2.0\",\"id\":"), id.original(), McpJson.utf8(",\"result\":"), actual, McpJson.utf8("}\n")));
    }
    private void error(Id id, int code, String message, Optional<RawJson> data) {
        byte[] extra = data.isPresent() ? McpJson.join(McpJson.utf8(",\"data\":"), data.orElseThrow().bytes()) : new byte[0];
        emit(McpJson.join(McpJson.utf8("{\"jsonrpc\":\"2.0\",\"id\":"), id == null ? McpJson.utf8("null") : id.original(),
                McpJson.utf8(",\"error\":{\"code\":" + code + ",\"message\":"), McpJson.quote(message), extra, McpJson.utf8("}}\n")));
    }
    private synchronized void emit(byte[] line) {
        if (outputFailure != null) return;
        try { sink.write(line); }
        catch (IOException failure) { outputFailure = failure; }
    }
    public Optional<IOException> outputFailure() { return Optional.ofNullable(outputFailure); }
    public Drain closeAndDrain(Duration maximum) throws InterruptedException {
        McpJson.require(maximum != null && !maximum.isNegative() && maximum.compareTo(Duration.ofSeconds(60)) <= 0, "finite stdio drain limit required");
        closed = true;
        for (Pending attempt : pending.values()) attempt.cancellation().request(Optional.of("stdio input closed; stop requested, existing world outcome must still be collected"));
        worker.shutdown(); boolean drained = worker.awaitTermination(maximum.toNanos(), TimeUnit.NANOSECONDS);
        return new Drain(drained && pending.isEmpty(), completed.get(), pending.size());
    }
    private static RpcFailure rpc(int code, String message) { return new RpcFailure(code, message, Optional.empty()); }
    private static RpcFailure rpc(int code, String message, JsonNode data) { return rpc(code, message, McpJson.encode(data)); }
    private static RpcFailure rpc(int code, String message, byte[] data) { return new RpcFailure(code, message, Optional.of(new RawJson(data))); }
}
