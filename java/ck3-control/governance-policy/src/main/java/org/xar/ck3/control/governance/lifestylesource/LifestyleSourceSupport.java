package org.xar.ck3.control.governance.lifestylesource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestylesource.LifestyleSourceFacts.*;

/** One narrow JSON boundary. The copied raw packet remains diagnostic data when a lane is rejected. */
final class LifestyleSourceSupport {
    static final String EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    static final Set<String> TARGETS = Set.of("cutting_corners_perk", "professional_workforce_perk", "centralization_perk",
            "tax_man_perk", "thoughtful_perk", "serve_the_crown_perk");
    private static final ObjectMapper WRITER = new ObjectMapper();
    private static final Set<String> U64_FIELDS = java.util.concurrent.ConcurrentHashMap.newKeySet();
    private LifestyleSourceSupport() { }
    static final class Invalid extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        Invalid(String reason) { super(reason); }
    }
    static Map<String, String> spec(String declaration) {
        var fields = new LinkedHashMap<String, String>();
        for (String pair : declaration.split(" ")) {
            String[] parts = pair.split(":"); fields.put(parts[0], parts[1]);
            if (parts[1].equals("u64") || parts[1].equals("?u64")) U64_FIELDS.add(parts[0]);
        }
        return Map.copyOf(fields);
    }
    static void require(boolean condition, String reason) { if (!condition) throw new Invalid(reason); }
    static JsonNode object(JsonNode value, Map<String, String> fields, String path) {
        require(value != null && value.isObject(), path + ":object_required");
        var actual = new HashSet<String>(); value.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(fields.keySet()), path + ":fields_mismatch");
        fields.forEach((name, kind) -> require(typed(value.get(name), kind), path + "." + name + ":" + legacyKind(kind) + "_required"));
        return value;
    }
    private static String legacyKind(String kind) {
        String base = kind.startsWith("?") ? kind.substring(1) : kind;
        String translated = switch (base) { case "s" -> "string"; case "b" -> "bool"; case "o" -> "object"; default -> base; };
        return kind.startsWith("?") ? "nullable_" + translated : translated;
    }
    private static boolean typed(JsonNode value, String kind) {
        if (value == null) return false;
        if (kind.startsWith("?")) { if (value.isNull()) return true; kind = kind.substring(1); }
        return switch (kind) {
            case "s" -> value.isTextual();
            case "b" -> value.isBoolean();
            case "o" -> value.isObject();
            case "i32" -> value.isIntegralNumber() && value.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0
                    && value.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0;
            default -> kind.startsWith("u") && value.isIntegralNumber() && value.bigIntegerValue().signum() >= 0
                    && value.bigIntegerValue().bitLength() <= Integer.parseInt(kind.substring(1));
        };
    }
    static BigInteger integer(JsonNode value, String name) { return value.get(name).bigIntegerValue(); }
    static BigInteger nullableInteger(JsonNode value, String name) { JsonNode item = value.get(name); return item == null || item.isNull() ? null : item.bigIntegerValue(); }
    static String text(JsonNode value, String name) { return value.get(name).textValue(); }
    static boolean yes(JsonNode value, String name) { return Boolean.TRUE.equals(bool(value, name)); }
    static Boolean bool(JsonNode value, String name) { JsonNode item = value.get(name); return item == null || item.isNull() ? null : item.booleanValue(); }
    static boolean isNull(JsonNode value, String name) { return value.get(name).isNull(); }
    static boolean zero(BigInteger value) { return value != null && value.signum() == 0; }
    static boolean nonzero(BigInteger value) { return value != null && value.signum() != 0; }
    static boolean equal(Object left, Object right) { return java.util.Objects.equals(left, right); }
    static boolean same(JsonNode left, JsonNode right) { return Arrays.equals(bytes(left), bytes(right)); }
    static SourceFrame frame(JsonNode frame, BigInteger publicRevision, BigInteger player) {
        BigInteger date = nullableInteger(frame, "date_raw");
        return new SourceFrame(text(frame, "snapshot_identity"), integer(frame, "native_revision"),
                date == null ? Optional.empty() : Optional.of(date.intValueExact()), Optional.ofNullable(player),
                integer(frame, "module_base"), Optional.ofNullable(nullableInteger(frame, "frame_identity")),
                Optional.ofNullable(nullableInteger(frame, "query_sequence")), integer(frame, "proof_epoch"), publicRevision, yes(frame, "caller_snapshot_confirmed"));
    }
    static void bind(Binding binding, JsonNode frame, BigInteger player, String target, String prefix, boolean frontier) {
        binding.snapshotIdentity().ifPresent(expected -> require(expected.equals(text(frame, "snapshot_identity")), prefix + "snapshot_identity_binding_mismatch"));
        binding.nativeRevision().ifPresent(expected -> require(expected.equals(integer(frame, "native_revision")), prefix + "native_revision_binding_mismatch"));
        binding.dateRaw().ifPresent(expected -> require(equal(BigInteger.valueOf(expected), nullableInteger(frame, "date_raw")), prefix + "date_raw_binding_mismatch"));
        binding.playedCharacterId().ifPresent(expected -> require(expected.equals(player), prefix + (frontier ? "requested_full_character_id" : "played_character_id") + "_binding_mismatch"));
        binding.targetKey().ifPresent(expected -> require(expected.equals(target), frontier ? "inputs:target_key_binding_mismatch" : "packet:target_binding_mismatch"));
    }
    static CopiedPacket copy(JsonNode raw) { return new CopiedPacket(bytes(raw)); }
    static ObjectNode raw(CopiedPacket packet) { return (ObjectNode) StrictJson.parse(packet.canonicalNativeJson()); }
    static byte[] bytes(JsonNode value) {
        try {
            byte[] raw = WRITER.writeValueAsBytes(sorted(value));
            require(raw.length <= StrictJson.INPUT_MAX_BYTES, "packet:copied_source_packet_too_large"); return raw;
        } catch (IOException error) { throw new IllegalArgumentException("copied source JSON serialization failed", error); }
    }
    private static JsonNode sorted(JsonNode value) {
        if (value.isObject()) {
            var result = StrictJson.object(); var keys = new TreeSet<String>(); value.fieldNames().forEachRemaining(keys::add);
            for (String key : keys) result.set(key, sorted(value.get(key))); return result;
        }
        if (value.isArray()) { var result = WRITER.createArrayNode(); value.forEach(item -> result.add(sorted(item))); return result; }
        return value.deepCopy();
    }
    /** Facts use decimal-string u64 carriers; original copied native JSON retains integer tokens. */
    static ObjectNode decimalFacts(ObjectNode packet) { return (ObjectNode) decimalNode(packet, null); }
    private static JsonNode decimalNode(JsonNode value, String field) {
        if (value.isObject()) {
            var result = StrictJson.object(); value.properties().forEach(item -> result.set(item.getKey(), decimalNode(item.getValue(), item.getKey()))); return result;
        }
        if (value.isArray()) { var result = WRITER.createArrayNode(); value.forEach(item -> result.add(decimalNode(item, null))); return result; }
        if (field != null && U64_FIELDS.contains(field) && value.isIntegralNumber()
                && value.bigIntegerValue().signum() >= 0 && value.bigIntegerValue().bitLength() <= 64)
            return WRITER.getNodeFactory().textNode(value.bigIntegerValue().toString());
        return value.deepCopy();
    }
    static void putOutputs(ObjectNode node, Outputs outputs) {
        outputs.rawU8().ifPresentOrElse(value -> node.put("returned_raw_u8", value), () -> node.putNull("returned_raw_u8"));
        outputs.rawU16().ifPresentOrElse(value -> node.put("returned_raw_u16", value), () -> node.putNull("returned_raw_u16"));
        outputs.qword0().ifPresentOrElse(value -> node.put("returned_qword0", value.toString()), () -> node.putNull("returned_qword0"));
        outputs.qword1().ifPresentOrElse(value -> node.put("returned_qword1", value.toString()), () -> node.putNull("returned_qword1"));
    }
}
