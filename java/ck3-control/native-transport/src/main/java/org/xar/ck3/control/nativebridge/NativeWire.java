package org.xar.ck3.control.nativebridge;

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
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/** The existing C++ protocol v1, not JSON-RPC. Raw packets and tokens are never reserialized. */
public final class NativeWire {
    public static final int MAXIMUM_FRAME_BYTES = 64 * 1024 * 1024;
    // Existing bridge.cpp uses kTacticalDailySentinelMaximumArmStepBytesV1 for every parsed step.
    public static final int MAXIMUM_STEP_BYTES = 795;
    public static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    private static final Set<String> RESERVED = Set.of("type", "protocol_version", "request_id", "step", "expected_revision");
    private static final JsonFactory FACTORY = JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(MAXIMUM_FRAME_BYTES)
                    .maxNumberLength(4300).maxNestingDepth(1000).build()).build();
    private static final ObjectMapper JSON = new ObjectMapper(FACTORY)
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS,
                    DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private NativeWire() { }

    public record Bytes(byte[] value) {
        public Bytes { value = value.clone(); }
        @Override public byte[] value() { return value.clone(); }
    }
    public enum Presence { ABSENT, NULL, VALUE }
    public record Field(Presence presence, Optional<Bytes> token) {
        public Field {
            token = Optional.ofNullable(token).orElseThrow();
            if (presence == null || (presence == Presence.ABSENT) != token.isEmpty())
                throw new IllegalArgumentException("field presence/token mismatch");
        }
    }
    public sealed interface Frame permits Hello, Snapshot, CommandResult, Notice { Bytes packet(); }
    public record Hello(long pid, BigInteger connectionGeneration, String bridgeVersion, String gameSha256,
            String adapterId, String adapterStatus, boolean buildMatch, List<String> capabilities, Bytes packet) implements Frame {
        public Hello { capabilities = List.copyOf(capabilities); }
    }
    public record Snapshot(String snapshotId, BigInteger revision, Bytes state, Bytes packet) implements Frame { }
    public record CommandResult(String requestId, boolean nativeOk, Field result, Field error, Bytes payload, Bytes packet) implements Frame { }
    public enum NoticeKind { HEARTBEAT, PONG, ERROR, SNAPSHOT_PUBLISH_DIAGNOSTIC }
    public record Notice(NoticeKind kind, Bytes payload, Bytes packet) implements Frame { }
    /** Revisions are separated from normalized domain fields; originalPacket is the actual immutable evidence. */
    public record ExecuteRequest(String requestId, String step, Optional<BigInteger> expectedRevision,
            Optional<BigInteger> expectedSnapshotRevision, Bytes normalizedAdditionalFields, Bytes originalPacket) {
        public ExecuteRequest {
            java.util.Objects.requireNonNull(requestId); java.util.Objects.requireNonNull(step);
            java.util.Objects.requireNonNull(expectedRevision); java.util.Objects.requireNonNull(expectedSnapshotRevision);
            java.util.Objects.requireNonNull(normalizedAdditionalFields); java.util.Objects.requireNonNull(originalPacket);
        }
    }
    public static ExecuteRequest decodeExecuteRequest(byte[] packet) throws IOException {
        require(packet != null && packet.length >= 5 && packet.length <= MAXIMUM_FRAME_BYTES + 4, "bounded complete outgoing Native packet required");
        int length = ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        require(length > 0 && length <= MAXIMUM_FRAME_BYTES && packet.length == length + 4, "exact outgoing LE uint32 frame length required");
        ObjectNode row = object(parse(Arrays.copyOfRange(packet, 4, packet.length)));
        require(text(row.get("type")).equals("execute_step"), "outgoing execute_step type required");
        integer(row.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
        String id = control(text(row.get("request_id"))); String operation = text(row.get("step")); step(operation);
        Optional<BigInteger> revision = row.has("expected_revision")
                ? Optional.of(integer(row.get("expected_revision"), BigInteger.ZERO, UINT64_MAX)) : Optional.empty();
        Optional<BigInteger> snapshotRevision = row.has("expected_snapshot_revision")
                ? Optional.of(integer(row.get("expected_snapshot_revision"), BigInteger.ZERO, UINT64_MAX)) : Optional.empty();
        if (revision.isPresent() && snapshotRevision.isPresent())
            require(revision.equals(snapshotRevision), "outgoing native and snapshot revisions disagree");
        ObjectNode additional = row.deepCopy();
        additional.remove(List.of("type", "protocol_version", "request_id", "step", "expected_revision", "expected_snapshot_revision"));
        boolean councilStatus = operation.equals("private-council-application-main-status-v1");
        require(!councilStatus || revision.isEmpty() && snapshotRevision.isEmpty() && additional.isEmpty(), "council status is exactly revisionless and has no domain fields");
        require(revision.isPresent() || snapshotRevision.isPresent() || councilStatus, "outgoing primitive requires its actual revision profile");
        return new ExecuteRequest(id, operation, revision, snapshotRevision, new Bytes(JSON.writeValueAsBytes(additional)), new Bytes(packet));
    }

    public static Frame decode(byte[] packet) throws IOException {
        require(packet != null && packet.length >= 5 && packet.length <= MAXIMUM_FRAME_BYTES + 4, "bounded complete Native packet required");
        int length = ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        require(length > 0 && length <= MAXIMUM_FRAME_BYTES && packet.length == length + 4, "exact LE uint32 frame length required");
        byte[] raw = Arrays.copyOfRange(packet, 4, packet.length);
        ObjectNode row = object(parse(raw));
        require(integer(row.get("protocol_version"), BigInteger.ONE, BigInteger.ONE).equals(BigInteger.ONE), "Native protocol version 1 required");
        String type = text(row.get("type")); Bytes original = new Bytes(packet);
        return switch (type) {
            case "hello" -> {
                long pid = integer(row.get("pid"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact();
                BigInteger generation = integer(row.get("connection_generation"), BigInteger.ONE, UINT64_MAX);
                require(row.path("capabilities").isArray(), "hello capabilities array required");
                List<String> capabilities = new ArrayList<>(); Set<String> unique = new HashSet<>();
                for (JsonNode capability : row.get("capabilities")) {
                    String name = text(capability); require(unique.add(name), "duplicate Native capability"); capabilities.add(name);
                }
                yield new Hello(pid, generation, text(row.get("bridge_version")), text(row.get("expected_ck3_sha256")),
                        text(row.get("game_adapter_id")), text(row.get("game_adapter_status")), bool(row.get("ck3_build_match")), capabilities, original);
            }
            case "state_snapshot" -> {
                String id = text(row.get("snapshot_id"));
                // Original Python revision tokens are retained as arbitrary exact integers.
                // The outgoing DLL boundary separately requires uint64 expected_revision.
                BigInteger revision = integer(row.get("revision"), BigInteger.ZERO, null);
                object(row.get("state"));
                yield new Snapshot(id, revision, new Bytes(token(raw, "state")), original);
            }
            case "command_result" -> {
                String id = control(text(row.get("request_id")));
                boolean ok = bool(row.get("ok"));
                yield new CommandResult(id, ok, field(raw, row, "result"), field(raw, row, "error"), new Bytes(raw), original);
            }
            case "heartbeat" -> {
                integer(row.get("sequence"), BigInteger.ZERO, null);
                yield new Notice(NoticeKind.HEARTBEAT, new Bytes(raw), original);
            }
            case "pong" -> {
                control(text(row.get("request_id")));
                yield new Notice(NoticeKind.PONG, new Bytes(raw), original);
            }
            case "error" -> new Notice(NoticeKind.ERROR, new Bytes(raw), original);
            case "snapshot_publish_diagnostic" -> {
                control(text(row.get("request_id"))); String phase = text(row.get("phase"));
                require(phase.equals("begin") || phase.equals("end"), "diagnostic phase required"); text(row.get("status"));
                integer(row.get("revision"), BigInteger.ZERO, null); integer(row.get("payload_bytes"), BigInteger.ZERO, null);
                yield new Notice(NoticeKind.SNAPSHOT_PUBLISH_DIAGNOSTIC, new Bytes(raw), original);
            }
            default -> throw new IOException("unsupported Native frame type: " + type);
        };
    }

    /** Additional fields are a narrow validated JSON boundary emitted by typed domain encoders. */
    public static byte[] execute(String requestId, String step, BigInteger revision, byte[] additionalFields) throws IOException {
        control(requestId); step(step); require(revision != null && revision.signum() >= 0 && revision.compareTo(UINT64_MAX) <= 0, "DLL expected_revision must fit uint64");
        ObjectNode extra = object(parse(additionalFields));
        Set<String> names = new HashSet<>(); extra.fieldNames().forEachRemaining(names::add);
        require(names.stream().noneMatch(RESERVED::contains), "domain encoder cannot replace Native envelope fields");
        ObjectNode request = JSON.createObjectNode().put("type", "execute_step").put("protocol_version", 1)
                .put("request_id", requestId).put("step", step).put("expected_revision", revision);
        extra.properties().forEach(entry -> request.set(entry.getKey(), entry.getValue()));
        return packet(JSON.writeValueAsBytes(request));
    }
    /** Exact additional envelope used by the retained g2_private_query_transport producer. */
    public static byte[] executePrivateQuery(String requestId, String step, BigInteger revision, byte[] additionalFields) throws IOException {
        ObjectNode extra = object(parse(additionalFields));
        if (extra.has("expected_snapshot_revision")) {
            require(integer(extra.get("expected_snapshot_revision"), BigInteger.ZERO, UINT64_MAX).equals(revision), "private query snapshot revision differs from native frame");
        } else extra.put("expected_snapshot_revision", revision);
        return execute(requestId, step, revision, JSON.writeValueAsBytes(extra));
    }
    /** Retained confucian_readonly_private_v1 producer uses only expected_snapshot_revision. */
    public static byte[] executeSnapshotRevisionOnly(String requestId, String step, BigInteger revision, byte[] additionalFields) throws IOException {
        control(requestId); step(step);
        require(revision != null && revision.signum() >= 0 && revision.compareTo(UINT64_MAX) <= 0, "DLL snapshot revision must fit uint64");
        ObjectNode extra = object(parse(additionalFields));
        Set<String> fields = new HashSet<>(); extra.fieldNames().forEachRemaining(fields::add);
        require(fields.stream().noneMatch(RESERVED::contains), "domain encoder cannot replace Native envelope fields");
        if (extra.has("expected_snapshot_revision"))
            require(integer(extra.remove("expected_snapshot_revision"), BigInteger.ZERO, UINT64_MAX).equals(revision), "confucian snapshot revision differs from frame");
        ObjectNode request = JSON.createObjectNode().put("type", "execute_step").put("protocol_version", 1)
                .put("request_id", requestId).put("step", step).put("expected_snapshot_revision", revision);
        extra.properties().forEach(entry -> request.set(entry.getKey(), entry.getValue()));
        return packet(JSON.writeValueAsBytes(request));
    }
    /** Exact retained council status producer: four fields, no revision or caller additions. */
    public static byte[] executeCouncilMailboxStatus(String requestId, String step, byte[] additionalFields) throws IOException {
        control(requestId);
        require("private-council-application-main-status-v1".equals(step), "exact council status step required");
        require(object(parse(additionalFields)).isEmpty(), "council status has no additional fields, including revisions or tickets");
        return packet(JSON.writeValueAsBytes(JSON.createObjectNode().put("type", "execute_step")
                .put("protocol_version", 1).put("request_id", requestId).put("step", step)));
    }
    public static byte[] packet(byte[] raw) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= MAXIMUM_FRAME_BYTES, "bounded Native payload required");
        return ByteBuffer.allocate(raw.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
    }
    public static JsonNode parse(byte[] raw) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= MAXIMUM_FRAME_BYTES, "bounded UTF-8 JSON required");
        // Decode with REPORT before Jackson so malformed UTF-8 is never repaired.
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw));
        JsonNode node = JSON.readTree(raw); require(node != null, "JSON value required");
        validateUnicode(node); return node;
    }
    public static ObjectNode object(JsonNode node) throws IOException { require(node instanceof ObjectNode, "JSON object required"); return (ObjectNode) node; }
    public static BigInteger integer(JsonNode node, BigInteger minimum, BigInteger maximum) throws IOException {
        require(node != null && node.isIntegralNumber(), "exact JSON integer required, rejecting boolean/float/string");
        BigInteger value = node.bigIntegerValue();
        require(value.compareTo(minimum) >= 0 && (maximum == null || value.compareTo(maximum) <= 0), "integer outside Native field range"); return value;
    }
    public static String text(JsonNode node) throws IOException { require(node != null && node.isTextual() && !node.textValue().isEmpty(), "nonempty JSON string required"); return node.textValue(); }
    private static boolean bool(JsonNode node) throws IOException { require(node != null && node.isBoolean(), "exact JSON boolean required"); return node.booleanValue(); }
    private static Field field(byte[] raw, ObjectNode row, String name) throws IOException {
        if (!row.has(name)) return new Field(Presence.ABSENT, Optional.empty());
        return new Field(row.get(name).isNull() ? Presence.NULL : Presence.VALUE, Optional.of(new Bytes(token(raw, name))));
    }
    public static byte[] token(byte[] raw, String field) throws IOException {
        try (JsonParser parser = FACTORY.createParser(raw)) {
            require(parser.nextToken() == JsonToken.START_OBJECT, "source object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken();
                long start = parser.currentTokenLocation().getByteOffset(); parser.skipChildren(); parser.finishToken();
                long end = parser.currentLocation().getByteOffset();
                if (field.equals(name)) return Arrays.copyOfRange(raw, Math.toIntExact(start), Math.toIntExact(end));
            }
        }
        throw new IOException("required original JSON token absent: " + field);
    }
    private static String control(String value) throws IOException {
        require(value != null && !value.isEmpty() && value.getBytes(StandardCharsets.UTF_8).length <= 128
                && value.chars().allMatch(character -> character >= 0x20 && character != '"' && character != '\\'), "unescaped bounded Native request id required"); unicode(value); return value;
    }
    private static void step(String value) throws IOException {
        require(value != null && !value.isEmpty() && value.getBytes(StandardCharsets.UTF_8).length <= MAXIMUM_STEP_BYTES
                && value.chars().allMatch(character -> character >= 0x20 && character != '"' && character != '\\'), "compact unescaped Native step required");
        unicode(value);
    }
    private static void validateUnicode(JsonNode node) throws IOException {
        if (node.isTextual()) unicode(node.textValue());
        else if (node.isObject()) {
            for (var entry : node.properties()) { unicode(entry.getKey()); validateUnicode(entry.getValue()); }
        } else if (node.isArray()) { for (JsonNode value : node) validateUnicode(value); }
    }
    private static void unicode(String value) throws IOException {
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) { require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(++index)), "unpaired JSON surrogate"); }
            else require(!Character.isLowSurrogate(current), "unpaired JSON surrogate");
        }
    }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}
