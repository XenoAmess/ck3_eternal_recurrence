package org.xar.ck3.control.nativebridge.capabilities.china_career;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Closed JSON boundary shared by the six original ZhongGuo native collectors. */
public final class CareerJson {
    public static final String VERSION = "1.19.0.6";
    public static final String EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    public static final String ADAPTER = "ck3-1.19.0.6-msvc-x64";
    public static final String BRIDGE = "0.1.0";
    public static final String DEPENDENCY = "zg361-bounded-ai-direct-manager-selection-v1";
    static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    static final BigInteger I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    public enum Availability { AVAILABLE, UNAVAILABLE }
    public record Datum<T>(Availability status, Optional<T> value, Optional<String> unavailable_reason) {
        public Datum {
            Objects.requireNonNull(status); Objects.requireNonNull(value); Objects.requireNonNull(unavailable_reason);
            require(status == Availability.AVAILABLE ? value.isPresent() && unavailable_reason.isEmpty()
                    : value.isEmpty() && unavailable_reason.isPresent(), "typed availability/value/reason mismatch");
        }
        public boolean available() { return status == Availability.AVAILABLE; }
        public T observed() { return value.orElseThrow(() -> new IllegalArgumentException("required native field unavailable: " + unavailable_reason.orElse(""))); }
    }
    public interface Group { List<Datum<?>> fields(); }
    public record FrameBinding(String request_nonce, String snapshot_id, BigInteger revision,
            BigInteger native_revision, BigInteger connection_generation, int date_raw,
            int player_character_id, int subject_character_id, int owner_character_id) {
        public FrameBinding {
            nonce(request_nonce); text(snapshot_id); unsigned(revision, false); unsigned(native_revision, true);
            unsigned(connection_generation, true); positive(player_character_id); positive(subject_character_id); positive(owner_character_id);
        }
    }
    public record Header(Availability status, String request_nonce, BigInteger snapshot_revision, int date_raw,
            boolean paused, int player_character_id, int subject_character_id, int requested_owner_character_id,
            Optional<String> unavailable_reason) { }
    private CareerJson() { }
    static JsonNode parse(RawJson raw) {
        try { return NativeWire.parse(raw.bytes()); }
        catch (IOException error) { throw new IllegalArgumentException("invalid original native JSON", error); }
    }
    static ObjectNode exact(JsonNode node, String... keys) {
        require(node instanceof ObjectNode, "closed native object required");
        Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(Set.of(keys)), "unexpected/missing fields: expected " + Set.of(keys) + ", actual " + actual);
        return (ObjectNode) node;
    }
    static ObjectNode without(JsonNode node, String... names) {
        require(node instanceof ObjectNode, "JSON object required");
        ObjectNode result = ((ObjectNode) node).deepCopy();
        for (String name : names) result.remove(name);
        return result;
    }
    static String text(JsonNode node) { require(node != null && node.isTextual(), "JSON text required"); return text(node.textValue()); }
    static String text(String value) { require(value != null && !value.isEmpty(), "nonempty text required"); return value; }
    static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "exact JSON boolean required"); return node.booleanValue(); }
    static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "exact JSON integer required; bool/float/string rejected"); return node.bigIntegerValue(); }
    static BigInteger i64(JsonNode node) { BigInteger value = integer(node); require(value.compareTo(I64_MIN) >= 0 && value.compareTo(I64_MAX) <= 0, "signed int64 required"); return value; }
    static int int32(JsonNode node) { try { return integer(node).intValueExact(); } catch (ArithmeticException error) { throw new IllegalArgumentException("int32 required", error); } }
    static int id(JsonNode node) { return positive(int32(node)); }
    static int positive(int value) { require(value > 0, "positive int32 identity required"); return value; }
    static BigInteger unsigned(BigInteger value, boolean positive) { require(value != null && value.signum() >= (positive ? 1 : 0) && value.compareTo(U64_MAX) <= 0, "uint64 required"); return value; }
    public static String nonce(String value) { require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"), "1..64 byte ASCII nonce required"); return value; }
    static Availability availability(JsonNode node) { return switch (text(node)) { case "available" -> Availability.AVAILABLE; case "unavailable" -> Availability.UNAVAILABLE; default -> throw new IllegalArgumentException("invalid availability"); }; }
    static Optional<String> reason(JsonNode node) { require(node != null, "reason must be present, including JSON null"); return node.isNull() ? Optional.empty() : Optional.of(node.isTextual() ? node.textValue() : text(node)); }
    static <T> Datum<T> datum(JsonNode node, Set<String> reasons, java.util.function.Function<JsonNode,T> decode) {
        exact(node, "status", "value", "unavailable_reason"); Availability status = availability(node.get("status"));
        Optional<String> reason = reason(node.get("unavailable_reason"));
        if (status == Availability.UNAVAILABLE) {
            require(node.get("value").isNull() && reason.isPresent() && (reasons == null || reasons.contains(reason.orElseThrow())), "invalid typed unavailability");
            return new Datum<>(status, Optional.empty(), reason);
        }
        require(reason.isEmpty() && !node.get("value").isNull(), "available field has reason/null");
        return new Datum<>(status, Optional.of(decode.apply(node.get("value"))), reason);
    }
    static Datum<BigInteger> number(JsonNode node, Set<String> reasons) { return datum(node, reasons, CareerJson::i64); }
    static Datum<BigInteger> unbounded(JsonNode node) { return datum(node, null, CareerJson::integer); }
    static Datum<Boolean> flag(JsonNode node, Set<String> reasons) { return datum(node, reasons, CareerJson::bool); }
    static Datum<String> string(JsonNode node, Set<String> reasons) { return datum(node, reasons, CareerJson::text); }
    static Datum<BigInteger> character(JsonNode node, Set<String> reasons) { return datum(node, reasons, value -> BigInteger.valueOf(id(value))); }
    static boolean all(Group group) { return group.fields().stream().allMatch(Datum::available); }
    static boolean none(Group group) { return group.fields().stream().noneMatch(Datum::available); }
    static boolean allReason(Group group, String reason) { return group.fields().stream().allMatch(field -> !field.available() && field.unavailable_reason().orElseThrow().equals(reason)); }
    static long n(Datum<BigInteger> value) { return value.observed().longValueExact(); }
    static boolean f(Datum<Boolean> value) { return value.observed(); }
    static boolean eq(Datum<BigInteger> value, long expected) { return value.available() && value.observed().equals(BigInteger.valueOf(expected)); }
    static boolean eq(Datum<Boolean> value, boolean expected) { return value.available() && value.observed() == expected; }
    static boolean eq(Datum<String> value, String expected) { return value.available() && value.observed().equals(expected); }
    static List<JsonNode> three(JsonNode node) { require(node != null && node.isArray() && node.size() == 3, "exactly three fixed native slots required"); return List.of(node.get(0), node.get(1), node.get(2)); }
    static Header header(JsonNode node, FrameBinding expected, boolean receivedSelf, boolean hasOwner) {
        require(integer(node.get("schema_version")).equals(BigInteger.ONE), "schema_version 1 required");
        require(text(node.get("request_nonce")).equals(expected.request_nonce()), "request nonce drift");
        BigInteger revision = unsigned(integer(node.get("snapshot_revision")), true); int date = int32(node.get("date_raw"));
        int player = id(node.get("player_character_id")); int subject = node.has("subject_character_id") ? id(node.get("subject_character_id")) : player;
        int owner = hasOwner ? id(node.get("requested_owner_character_id")) : expected.owner_character_id();
        require(revision.equals(expected.native_revision()) && date == expected.date_raw() && bool(node.get("paused"))
                && player == expected.player_character_id() && (!(receivedSelf || hasOwner) || subject == expected.subject_character_id())
                && owner == expected.owner_character_id(), "paused query identity drift");
        require(!receivedSelf || subject == player, "received-self subject must be the real played character");
        Availability status = availability(node.get("status")); Optional<String> reason = reason(node.get("unavailable_reason"));
        require((status == Availability.AVAILABLE) == reason.isEmpty(), "frame status/reason mismatch");
        return new Header(status, expected.request_nonce(), revision, date, true, player, subject, owner, reason);
    }
    static void require(boolean condition, String reason) { if (!condition) throw new IllegalArgumentException(reason); }
}
