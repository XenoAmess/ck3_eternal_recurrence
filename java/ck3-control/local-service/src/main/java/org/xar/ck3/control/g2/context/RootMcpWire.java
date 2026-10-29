package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** MCP stdio boundary. Original result tokens remain bytes; JSON numbers never pass through double. */
public final class RootMcpWire {
    public static final String SEMANTIC_TOOL = "ck3_take_semantic_snapshot_private_v1";
    public static final String CAPABILITIES_TOOL = "ck3_get_capabilities";
    public static final int MAX_LINE_BYTES = RootMcpEnvelope.RPC_LINE_MAX_BYTES;
    public static final Set<String> LEGACY_VERSIONS = Set.of("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25");
    private static final JsonFactory FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(MAX_LINE_BYTES).build()).build();
    private static final ObjectMapper JSON = new ObjectMapper(FACTORY)
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS,
                    DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private RootMcpWire() { }

    public record Limits(int maximumLineBytes, int maximumNotifications) {
        public Limits {
            require(maximumLineBytes > 0 && maximumLineBytes <= MAX_LINE_BYTES && maximumNotifications >= 0 && maximumNotifications <= 128,
                    "finite MCP line/notification limits required");
        }
    }
    public record Handshake(String offeredVersion, Set<String> acceptedVersions, String clientName, String clientVersion,
            String expectedServerName, String expectedServerVersion) {
        public Handshake {
            acceptedVersions = Set.copyOf(acceptedVersions);
            require(LEGACY_VERSIONS.contains(offeredVersion) && !acceptedVersions.isEmpty()
                    && LEGACY_VERSIONS.containsAll(acceptedVersions) && acceptedVersions.contains(offeredVersion), "explicit supported initialize versions required");
            for (String value : List.of(clientName, clientVersion, expectedServerName, expectedServerVersion)) { StrictJson.text(value); }
        }
    }
    public sealed interface Id permits NumberId, TextId { }
    public record NumberId(long value) implements Id {
        public NumberId { require(value >= 1 && value <= StrictJson.MAX_SAFE_INTEGER, "positive safe JSON-RPC id required"); }
    }
    public record TextId(String value) implements Id {
        public TextId { StrictJson.text(value); require(value.length() <= 128, "bounded server request id required"); }
    }
    public enum Presence { MISSING, NULL, VALUE }
    public record JsonBytes(byte[] bytes) {
        public JsonBytes { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
        public int byteLength() { return bytes.length; }
    }
    public sealed interface Message permits Response, ErrorResponse, Notification, Ping { }
    public record Response(Id id, JsonBytes result, JsonBytes originalLine) implements Message { }
    public record ErrorResponse(Id id, int code, String message, JsonBytes originalLine) implements Message { }
    public record Notification(String method, JsonBytes originalLine) implements Message { }
    public record Ping(Id id, JsonBytes originalLine) implements Message { }
    public record Initialized(String version, String serverName, String serverVersion, JsonBytes originalResult) { }
    public record ToolResult(JsonBytes originalResult, JsonBytes ownerProjection, Presence metaPresence,
            Presence structuredPresence, boolean isError) { }
    public record OwnerRow(JsonBytes bytes, int resultProjectionBytes, long sequence, Instant startedAtUtc, Instant endedAtUtc) { }

    public static byte[] initialize(long id, Handshake handshake) {
        ObjectNode params = StrictJson.object(); params.put("protocolVersion", handshake.offeredVersion());
        params.set("capabilities", StrictJson.object());
        params.set("clientInfo", StrictJson.object().put("name", handshake.clientName()).put("version", handshake.clientVersion()));
        return request(id, "initialize", params);
    }
    public static byte[] initialized() { return line(StrictJson.object().put("jsonrpc", "2.0").put("method", "notifications/initialized")); }
    public static byte[] semantic(long id) {
        ObjectNode params = StrictJson.object().put("name", SEMANTIC_TOOL); params.set("arguments", StrictJson.object());
        return request(id, "tools/call", params);
    }
    public static byte[] capabilities(long id) {
        ObjectNode params = StrictJson.object().put("name", CAPABILITIES_TOOL); params.set("arguments", StrictJson.object());
        return request(id, "tools/call", params);
    }
    public static byte[] pong(Id id) {
        ObjectNode row = StrictJson.object().put("jsonrpc", "2.0"); putId(row, id); row.set("result", StrictJson.object()); return line(row);
    }
    public static Message message(byte[] originalLine, Limits limits) throws IOException {
        byte[] raw = payload(originalLine, limits.maximumLineBytes());
        ObjectNode row = object(parse(raw)); equalText(row.get("jsonrpc"), "2.0", "JSON-RPC2.0 required");
        JsonBytes retained = new JsonBytes(originalLine);
        if (row.has("method")) {
            requireFields(row, row.has("id") ? Set.of("jsonrpc", "id", "method", "params") : Set.of("jsonrpc", "method", "params"), Set.of("params"));
            String method = text(row.get("method"));
            if (row.has("params")) { object(row.get("params")); }
            if (row.has("id")) {
                require(method.equals("ping") && (!row.has("params") || row.get("params").isEmpty()), "unsupported server request; no sampling/roots capabilities offered");
                return new Ping(id(row.get("id")), retained);
            }
            require(method.startsWith("notifications/"), "server notification method required");
            return new Notification(method, retained);
        }
        require(row.has("id") && row.has("result") != row.has("error"), "one response result or error required");
        if (row.has("error")) {
            requireFields(row, Set.of("jsonrpc", "id", "error"), Set.of());
            ObjectNode error = object(row.get("error")); requireFields(error, Set.of("code", "message", "data"), Set.of("data"));
            long code = integer(error.get("code"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            return new ErrorResponse(id(row.get("id")), (int) code, text(error.get("message")), retained);
        }
        requireFields(row, Set.of("jsonrpc", "id", "result"), Set.of()); object(row.get("result"));
        return new Response(id(row.get("id")), new JsonBytes(token(raw, "result")), retained);
    }
    public static Initialized initializeResult(Response response, Handshake expected) throws IOException {
        ObjectNode row = object(parse(response.result().bytes));
        requireFields(row, Set.of("_meta", "protocolVersion", "capabilities", "serverInfo", "instructions"), Set.of("_meta", "instructions"));
        if (row.has("_meta")) { object(row.get("_meta")); }
        if (row.has("instructions")) { text(row.get("instructions")); }
        String version = text(row.get("protocolVersion")); require(expected.acceptedVersions().contains(version), "server negotiated an unsupported protocol version");
        ObjectNode capabilities = object(row.get("capabilities")); require(capabilities.has("tools"), "server has no tools capability"); object(capabilities.get("tools"));
        ObjectNode info = object(row.get("serverInfo"));
        String name = text(info.get("name")), revision = text(info.get("version"));
        require(name.equals(expected.expectedServerName()) && revision.equals(expected.expectedServerVersion()), "actual server identity differs from Root binding");
        return new Initialized(version, name, revision, response.result());
    }
    public static ToolResult toolResult(Response response) throws IOException {
        byte[] raw = response.result().bytes; ObjectNode row = object(parse(raw));
        requireFields(row, Set.of("_meta", "content", "structuredContent", "isError", "resultType"), Set.of("_meta", "structuredContent", "isError", "resultType"));
        require(row.get("content").isArray(), "complete MCP content array required");
        for (JsonNode block : row.get("content")) { object(block); }
        Presence meta = presence(row, "_meta"), structured = presence(row, "structuredContent");
        if (meta == Presence.VALUE) { object(row.get("_meta")); }
        if (structured == Presence.VALUE) { object(row.get("structuredContent")); }
        boolean error = false;
        if (row.has("isError")) { require(row.get("isError").isBoolean(), "MCP isError must be boolean when present"); error = row.get("isError").booleanValue(); }
        if (row.has("resultType")) { equalText(row.get("resultType"), "complete", "incomplete/deferred MCP result is not a complete Native observation"); }
        byte[] projection = join(ascii("{\"meta\":"), nullableToken(raw, row, "_meta"), ascii(",\"content\":"), token(raw, "content"),
                ascii(",\"structured_content\":"), nullableToken(raw, row, "structuredContent"),
                ascii(",\"is_error\":" + error + ",\"result_type\":\"complete\"}"));
        return new ToolResult(response.result(), new JsonBytes(projection), meta, structured, error);
    }
    /** Original structured token, separately bounded from its duplicated/escaped MCP envelope. No Native authority is inferred. */
    public static JsonBytes semanticBody(ToolResult result) throws IOException {
        JsonBytes original = structuredBody(result); RootMcpEnvelope.requireSemanticBody(original.byteLength()); return original;
    }
    public static JsonBytes capabilitiesBody(ToolResult result) throws IOException {
        JsonBytes original = structuredBody(result); RootMcpEnvelope.requireCapabilitiesBody(original.byteLength()); return original;
    }
    private static JsonBytes structuredBody(ToolResult result) throws IOException {
        require(result.structuredPresence() == Presence.VALUE, "semantic structured-content object required");
        byte[] original = token(result.originalResult().bytes, "structuredContent");
        return new JsonBytes(original);
    }
    public static OwnerRow ownerRow(long sequence, Instant started, Instant ended, long elapsedNanos, ToolResult result) throws IOException {
        require(sequence >= 1 && sequence <= StrictJson.MAX_SAFE_INTEGER && elapsedNanos >= 0 && !ended.isBefore(started), "actual finite owner request timing required");
        Objects.requireNonNull(result);
        ObjectNode prefix = StrictJson.object().put("started_at_utc", started.toString()).put("ended_at_utc", ended.toString());
        byte[] prefixBytes = StrictJson.canonical(prefix);
        ObjectNode request = StrictJson.object().put("sequence", sequence).put("tool", SEMANTIC_TOOL); request.set("arguments", StrictJson.object());
        byte[] projected = result.ownerProjection().bytes;
        byte[] raw = join(Arrays.copyOf(prefixBytes, prefixBytes.length - 1),
                ascii(",\"elapsed_seconds\":" + BigDecimal.valueOf(elapsedNanos, 9).toPlainString() + ",\"request\":"), StrictJson.canonical(request),
                ascii(",\"result\":"), projected, ascii(",\"mcp_result_projection_json_utf8_bytes\":" + projected.length + "}"));
        RootMcpEnvelope.requireOwnerRow(raw.length); object(parse(raw));
        return new OwnerRow(new JsonBytes(raw), projected.length, sequence, started, ended);
    }
    private static byte[] request(long id, String method, ObjectNode params) {
        new NumberId(id); ObjectNode row = StrictJson.object().put("jsonrpc", "2.0").put("id", id).put("method", method); row.set("params", params); return line(row);
    }
    private static byte[] line(ObjectNode row) { return join(StrictJson.canonical(row), new byte[] {'\n'}); }
    private static void putId(ObjectNode row, Id id) {
        if (id instanceof NumberId number) { row.put("id", number.value()); } else { row.put("id", ((TextId) id).value()); }
    }
    private static Id id(JsonNode value) { return value != null && value.isTextual() ? new TextId(text(value)) : new NumberId(integer(value, 1, StrictJson.MAX_SAFE_INTEGER)); }
    private static Presence presence(ObjectNode row, String field) { return !row.has(field) ? Presence.MISSING : row.get(field).isNull() ? Presence.NULL : Presence.VALUE; }
    private static byte[] nullableToken(byte[] raw, ObjectNode row, String field) throws IOException { return row.has(field) ? token(raw, field) : ascii("null"); }
    private static byte[] payload(byte[] line, int maximum) throws IOException {
        if (line != null) { RootMcpEnvelope.requireRpcLine(line.length); }
        require(line != null && line.length > 1 && line.length <= maximum && line[line.length - 1] == '\n', "bounded complete newline MCP frame required");
        int length = line.length - 1; if (length > 0 && line[length - 1] == '\r') { length--; }
        require(length > 0, "empty MCP line rejected");
        byte[] result = Arrays.copyOf(line, length);
        for (byte value : result) { require(value != '\r' && value != '\n', "MCP stdio frame has an embedded line break"); }
        return result;
    }
    private static JsonNode parse(byte[] raw) throws IOException {
        require(raw.length > 0 && raw.length <= MAX_LINE_BYTES, "bounded original JSON required");
        require(!(raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf), "JSON BOM rejected");
        for (byte value : raw) { require(value != 0, "raw JSON NUL rejected"); }
        String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        JsonNode parsed = JSON.readTree(text); validateUnicode(parsed); return parsed;
    }
    private static void validateUnicode(JsonNode node) {
        if (node == null) { return; }
        if (node.isTextual()) { validateUnicode(node.textValue()); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(RootMcpWire::validateUnicode); }
        if (node.isContainerNode()) { for (JsonNode child : node) { validateUnicode(child); } }
    }
    private static void validateUnicode(String text) {
        for (int index = 0; index < text.length(); index++) {
            char value = text.charAt(index);
            if (Character.isHighSurrogate(value)) {
                require(index + 1 < text.length() && Character.isLowSurrogate(text.charAt(index + 1)), "unpaired JSON Unicode surrogate rejected"); index++;
            } else { require(!Character.isLowSurrogate(value), "unpaired JSON Unicode surrogate rejected"); }
        }
    }
    private static byte[] token(byte[] raw, String field) throws IOException {
        try (JsonParser parser = FACTORY.createParser(raw)) {
            require(parser.nextToken() == JsonToken.START_OBJECT, "source object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken();
                long start = parser.currentTokenLocation().getByteOffset(); parser.skipChildren(); parser.finishToken();
                long end = parser.currentLocation().getByteOffset();
                if (field.equals(name)) { return Arrays.copyOfRange(raw, Math.toIntExact(start), Math.toIntExact(end)); }
            }
        }
        throw new IOException("required original JSON token absent: " + field);
    }
    private static ObjectNode object(JsonNode row) { require(row instanceof ObjectNode, "JSON object required"); return (ObjectNode) row; }
    private static String text(JsonNode value) { require(value != null && value.isTextual() && !value.textValue().isEmpty(), "nonempty JSON string required"); return value.textValue(); }
    private static long integer(JsonNode value, long minimum, long maximum) {
        require(value != null && value.isIntegralNumber() && value.canConvertToLong(), "exact JSON integer required");
        long result = value.longValue(); require(result >= minimum && result <= maximum, "JSON integer outside range"); return result;
    }
    private static void equalText(JsonNode value, String expected, String message) { require(value != null && value.isTextual() && expected.equals(value.textValue()), message); }
    private static void requireFields(ObjectNode row, Set<String> allowed, Set<String> optional) {
        Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add);
        require(allowed.containsAll(actual) && actual.containsAll(allowed.stream().filter(field -> !optional.contains(field)).toList()), "wrong/missing MCP fields");
    }
    private static byte[] ascii(String value) { return value.getBytes(StandardCharsets.US_ASCII); }
    private static byte[] join(byte[]... parts) {
        long length = 0; for (byte[] part : parts) { length = Math.addExact(length, part.length); }
        require(length > 0 && length <= MAX_LINE_BYTES, "joined MCP/owner container exceeds the finite whole-envelope budget");
        byte[] result = new byte[Math.toIntExact(length)]; int offset = 0;
        for (byte[] part : parts) { System.arraycopy(part, 0, result, offset, part.length); offset += part.length; }
        return result;
    }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
