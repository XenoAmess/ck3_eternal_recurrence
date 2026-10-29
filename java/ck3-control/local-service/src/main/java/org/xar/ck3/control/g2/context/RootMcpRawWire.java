package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection;

/** Decoded transport cache only. It neither binds an episode nor issues Native authority. */
public final class RootMcpRawWire {
    public static final String TOOL = "ck3_observe_native_transport_private_v1";
    public static final String SCHEMA = "xar.native.raw-transport-snapshot.v2";
    public static final int WRAPPER_MAX_BYTES = 16 * 1024 * 1024;
    public static final int NATIVE_PACKET_MAX_BYTES = 8 * 1024 * 1024;
    public static final int METADATA_MAX_BYTES = 1024 * 1024;
    private static final int METADATA_ENVELOPE_BYTES = "{\"diagnostics\":,\"owner_cold_adoption\":}".length();
    private static final JsonFactory FACTORY = JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(256)
                    .maxStringLength(RootMcpEnvelope.RPC_LINE_MAX_BYTES).build()).build();
    private static final ObjectMapper JSON = new ObjectMapper(FACTORY)
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS, DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private RootMcpRawWire() { }

    public record PlayedCharacter(long characterId) {
        public PlayedCharacter { require(characterId > 0 && characterId <= StrictJson.MAX_SAFE_INTEGER, "exact positive safe character ID required"); }
    }
    /** Original tokens are from the MCP decoded cache projection, never claimed to be original Native wire bytes. */
    public record Frame(RootMcpWire.JsonBytes wrapper, RootMcpWire.JsonBytes nativePacket,
            RootMcpWire.JsonBytes diagnostics, String snapshotId, long nativeRevision, long publicRevision,
            boolean mapReady, Optional<PlayedCharacter> playedCharacter, long dateRaw, boolean paused,
            NativeColdAdoptionProjection ownerColdAdoption) {
        public Frame {
            java.util.Objects.requireNonNull(wrapper); java.util.Objects.requireNonNull(nativePacket); java.util.Objects.requireNonNull(diagnostics);
            playedCharacter = java.util.Objects.requireNonNull(playedCharacter); java.util.Objects.requireNonNull(snapshotId);
            java.util.Objects.requireNonNull(ownerColdAdoption);
            bounded(wrapper.byteLength(), WRAPPER_MAX_BYTES, "raw wrapper"); bounded(nativePacket.byteLength(), NATIVE_PACKET_MAX_BYTES, "native packet");
            bounded(diagnostics.byteLength(), METADATA_MAX_BYTES, "raw metadata");
            bounded(Math.addExact(Math.addExact(diagnostics.byteLength(), ownerColdAdoption.original().bytes().length), METADATA_ENVELOPE_BYTES),
                    METADATA_MAX_BYTES, "combined diagnostics/adoption metadata");
            require(!snapshotId.isEmpty() && snapshotId.length() <= 1024 && nativeRevision >= 0 && nativeRevision <= StrictJson.MAX_SAFE_INTEGER
                    && publicRevision >= 0 && publicRevision <= StrictJson.MAX_SAFE_INTEGER && dateRaw >= 0 && dateRaw <= StrictJson.MAX_SAFE_INTEGER,
                    "validated finite raw frame identity required");
        }
    }

    public static byte[] request(long id) {
        new RootMcpWire.NumberId(id);
        ObjectNode params = StrictJson.object().put("name", TOOL); params.set("arguments", StrictJson.object());
        ObjectNode request = StrictJson.object().put("jsonrpc", "2.0").put("id", id).put("method", "tools/call");
        request.set("params", params); byte[] raw = StrictJson.canonical(request);
        byte[] line = Arrays.copyOf(raw, raw.length + 1); line[raw.length] = '\n'; return line;
    }

    public static Frame decode(RootMcpWire.ToolResult result) throws IOException {
        require(!result.isError(), "raw transport tool returned a known error; no preflight result exists");
        require(result.structuredPresence() == RootMcpWire.Presence.VALUE, "raw structuredContent object required");
        byte[] wrapper = token(result.originalResult().bytes(), "structuredContent");
        return decodeWrapper(new RootMcpWire.JsonBytes(wrapper));
    }

    /** Strict data parsing is public for software verification; only the private owned completion proves pipe custody. */
    public static Frame decodeWrapper(RootMcpWire.JsonBytes original) throws IOException {
        byte[] raw = original.bytes(); bounded(raw.length, WRAPPER_MAX_BYTES, "raw wrapper");
        ObjectNode row = object(parse(raw)); exactFields(row, Set.of("schema", "native_packet", "semantic_packet_accepted", "public_revision", "diagnostics", "owner_cold_adoption"));
        equalText(row.get("schema"), SCHEMA, "unsupported raw transport schema");
        require(bool(row.get("semantic_packet_accepted")), "latest native packet was rejected; it cannot be a cold preflight observation");
        long publicRevision = integer(row.get("public_revision"), 0, StrictJson.MAX_SAFE_INTEGER);
        byte[] packetRaw = token(raw, "native_packet"), metadata = token(raw, "diagnostics");
        byte[] adoption = token(raw, "owner_cold_adoption");
        bounded(packetRaw.length, NATIVE_PACKET_MAX_BYTES, "native packet"); bounded(metadata.length, METADATA_MAX_BYTES, "raw metadata");
        bounded(Math.addExact(Math.addExact(metadata.length, adoption.length), METADATA_ENVELOPE_BYTES), METADATA_MAX_BYTES, "combined diagnostics/adoption metadata");
        NativeColdAdoptionProjection projected = NativeColdAdoptionProjection.parse(adoption);
        ObjectNode packet = object(row.get("native_packet")); object(row.get("diagnostics"));
        equalText(packet.get("type"), "state_snapshot", "native state_snapshot packet required");
        require(integer(packet.get("protocol_version"), 1, 1) == 1, "native protocol version1 required");
        String snapshot = text(packet.get("snapshot_id")); require(snapshot.length() <= 1024, "bounded native snapshot ID required");
        long nativeRevision = integer(packet.get("revision"), 0, StrictJson.MAX_SAFE_INTEGER);
        ObjectNode state = object(packet.get("state"));
        boolean mapReady = bool(state.get("map_ready")), paused = bool(state.get("paused"));
        long dateRaw = integer(state.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER);
        require(state.has("played_character"), "raw played_character is required and may be null");
        JsonNode played = state.get("played_character");
        Optional<PlayedCharacter> character = played.isNull() ? Optional.empty()
                : Optional.of(new PlayedCharacter(integer(object(played).get("character_id"), 1, StrictJson.MAX_SAFE_INTEGER)));
        return new Frame(original, new RootMcpWire.JsonBytes(packetRaw), new RootMcpWire.JsonBytes(metadata), snapshot,
                nativeRevision, publicRevision, mapReady, character, dateRaw, paused, projected);
    }

    private static JsonNode parse(byte[] raw) throws IOException {
        require(raw.length > 0 && raw.length <= WRAPPER_MAX_BYTES, "bounded raw JSON required");
        require(!(raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf), "JSON BOM rejected");
        String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        JsonNode value = JSON.readTree(text); unicode(value); return value;
    }
    private static void unicode(JsonNode node) {
        if (node == null) { return; }
        if (node.isTextual()) { unicode(node.textValue()); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(RootMcpRawWire::unicode); }
        if (node.isContainerNode()) { for (JsonNode child : node) { unicode(child); } }
    }
    private static void unicode(String value) {
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (Character.isHighSurrogate(c)) {
                require(i + 1 < value.length() && Character.isLowSurrogate(value.charAt(i + 1)), "unpaired raw JSON surrogate rejected"); i++;
            } else { require(!Character.isLowSurrogate(c), "unpaired raw JSON surrogate rejected"); }
        }
    }
    private static byte[] token(byte[] raw, String field) throws IOException {
        try (JsonParser parser = FACTORY.createParser(raw)) {
            require(parser.nextToken() == JsonToken.START_OBJECT, "source object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken(); long start = parser.currentTokenLocation().getByteOffset();
                parser.skipChildren(); parser.finishToken(); long end = parser.currentLocation().getByteOffset();
                if (field.equals(name)) { return Arrays.copyOfRange(raw, Math.toIntExact(start), Math.toIntExact(end)); }
            }
        }
        throw new IOException("required original raw JSON token missing: " + field);
    }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "raw JSON object required"); return (ObjectNode) node; }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "exact raw JSON boolean required"); return node.booleanValue(); }
    private static String text(JsonNode node) { require(node != null && node.isTextual() && !node.textValue().isEmpty(), "nonempty raw string required"); return node.textValue(); }
    private static long integer(JsonNode node, long min, long max) {
        require(node != null && node.isIntegralNumber() && node.canConvertToLong(), "exact raw JSON integer required");
        long value = node.longValue(); require(value >= min && value <= max, "raw integer outside range"); return value;
    }
    private static void equalText(JsonNode node, String expected, String detail) { require(node != null && node.isTextual() && expected.equals(node.textValue()), detail); }
    private static void exactFields(ObjectNode row, Set<String> expected) {
        Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add); require(actual.equals(expected), "wrong/missing raw wrapper fields");
    }
    private static void bounded(int size, int maximum, String what) { require(size > 0 && size <= maximum, what + " exceeds its dedicated finite budget"); }
    private static void require(boolean condition, String detail) { if (!condition) { throw new IllegalArgumentException(detail); } }
}
