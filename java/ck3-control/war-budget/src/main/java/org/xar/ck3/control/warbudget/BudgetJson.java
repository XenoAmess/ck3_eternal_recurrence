package org.xar.ck3.control.warbudget;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;

/** Narrow SDK legacy boundary; callers preserve missing/default distinctions explicitly. */
final class BudgetJson {
    static final BigInteger ZERO = BigInteger.ZERO;
    private BudgetJson() { }
    static ObjectNode obj() { return StrictJson.object(); }
    static ObjectNode record(JsonNode value) { require(value instanceof ObjectNode, "budget JSON object required"); return (ObjectNode) value; }
    static void input(boolean condition, String reason) {
        require(condition, reason);
    }
    static ObjectNode inputRecord(JsonNode value) { input(value instanceof ObjectNode, "budget JSON object required"); return (ObjectNode) value; }
    static String inputText(JsonNode value) {
        return StrictJson.text(value);
    }
    static ObjectNode maybe(JsonNode value) { return value instanceof ObjectNode row ? row : obj(); }
    static JsonNode get(JsonNode value, String key) { return value != null && value.isObject() && value.has(key) ? value.get(key) : NullNode.instance; }
    static boolean missingOrNull(JsonNode value) { return value == null || value.isNull(); }
    static boolean text(JsonNode value, String expected) { return value != null && value.isTextual() && value.textValue().equals(expected); }
    static boolean yes(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    static boolean no(JsonNode value) { return value != null && value.isBoolean() && !value.booleanValue(); }
    static boolean exact(JsonNode value) { return value != null && value.isIntegralNumber(); }
    static boolean positive(JsonNode value) { return exact(value) && value.bigIntegerValue().signum() > 0; }
    static boolean nonnegative(JsonNode value) { return exact(value) && value.bigIntegerValue().signum() >= 0; }
    static BigInteger integer(JsonNode value) { input(exact(value), "exact budget integer required; boolean/float/string rejected"); return value.bigIntegerValue(); }
    static BigInteger number(JsonNode row, String key) { return integer(get(row, key)); }
    static int inputInt(BigInteger value) {
        input(value.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0
            && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "budget integer input outside signed32 range");
        return value.intValue();
    }
    static boolean equal(JsonNode left, JsonNode right) {
        if (missingOrNull(left) || missingOrNull(right)) { return missingOrNull(left) && missingOrNull(right); }
        if (left.isIntegralNumber() && right.isIntegralNumber()) { return left.bigIntegerValue().equals(right.bigIntegerValue()); }
        if (left.isObject() && right.isObject()) {
            if (left.size() != right.size()) { return false; }
            var keys = left.fieldNames();
            while (keys.hasNext()) { String key = keys.next(); if (!right.has(key) || !equal(left.get(key), right.get(key))) { return false; } }
            return true;
        }
        if (left.isArray() && right.isArray()) {
            if (left.size() != right.size()) { return false; }
            for (int i = 0; i < left.size(); i++) { if (!equal(left.get(i), right.get(i))) { return false; } }
            return true;
        }
        return left.equals(right);
    }
    static List<ObjectNode> rows(JsonNode value) {
        List<ObjectNode> rows = new ArrayList<>();
        if (value != null && value.isArray()) { for (JsonNode row : value) { if (row instanceof ObjectNode object) { rows.add(object); } } }
        return rows;
    }
    static boolean listPresent(JsonNode value) {
        if (missingOrNull(value)) { return false; }
        input(value.isArray(), "observed identity collection must be array/null/missing");
        for (JsonNode id : value) { input(positive(id), "observed collection ID must be a positive exact integer"); }
        return !value.isEmpty();
    }
    static BigInteger defaultInteger(ObjectNode row, String key, BigInteger fallback) {
        return row.has(key) ? integer(row.get(key)) : fallback;
    }
    static ObjectNode frame(JsonNode snapshot) {
        ObjectNode result = obj();
        JsonNode actor = get(snapshot, "played_character_id");
        if (actor.isNull()) { actor = get(get(snapshot, "played_character"), "character_id"); }
        input(positive(actor) && positive(get(snapshot, "native_revision")) && positive(get(snapshot, "revision"))
            && nonnegative(get(snapshot, "date_raw")), "M5 observed frame identity incomplete");
        result.set("played_character_id", actor);
        for (String key : List.of("native_revision", "date_raw", "revision")) { result.set(key, snapshot.get(key)); }
        result.put("snapshot_id", inputText(snapshot.get("snapshot_id")));
        result.put("episode_run_id", inputText(snapshot.get("episode_run_id")));
        return result;
    }
    static String fallbackEpoch(ObjectNode frame, List<BigInteger> warIds) {
        var value = obj().putArray("unused"); value.add(frame);
        var ids = value.addArray(); warIds.stream().sorted().forEach(ids::add);
        StringBuilder text = new StringBuilder(); pythonDefault(value, text);
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
            .digest(text.toString().getBytes(StandardCharsets.UTF_8))).substring(0, 24); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    /** Python json.dumps sort_keys=True defaults: spaces and ensure_ascii, not shared canonical JSON. */
    static void pythonDefault(JsonNode value, StringBuilder out) {
        if (value.isObject()) {
            out.append('{'); TreeSet<String> keys = new TreeSet<>(); value.fieldNames().forEachRemaining(keys::add);
            boolean first = true;
            for (String key : keys) { if (!first) { out.append(", "); } first = false; quoteAscii(key, out); out.append(": "); pythonDefault(value.get(key), out); }
            out.append('}');
        } else if (value.isArray()) {
            out.append('['); boolean first = true;
            for (JsonNode row : value) { if (!first) { out.append(", "); } first = false; pythonDefault(row, out); }
            out.append(']');
        } else if (value.isTextual()) { quoteAscii(value.textValue(), out); }
        else if (value.isIntegralNumber()) { out.append(value.bigIntegerValue()); }
        else if (value.isNull()) { out.append("null"); }
        else if (value.isBoolean()) { out.append(value.booleanValue()); }
        else { require(false, "epoch hash only uses integer frame identities"); }
    }
    private static void quoteAscii(String value, StringBuilder out) {
        out.append('"');
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\""); case '\\' -> out.append("\\\\");
                case '\b' -> out.append("\\b"); case '\f' -> out.append("\\f"); case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r"); case '\t' -> out.append("\\t");
                default -> { if (c < 32 || c > 126) { out.append(String.format(java.util.Locale.ROOT, "\\u%04x", (int) c)); } else { out.append(c); } }
            }
        }
        out.append('"');
    }
}
