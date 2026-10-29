package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Sole original settlement wire normalizer. DATA validation grants no episode, persistence or Game authority. */
public final class NativeOneLifeSettlement {
    public static final String KEY = "one_life_settlement";
    public static final String CAPABILITY = "game.state.xar-one-life-settlement";
    private static final BigInteger TWO52 = BigInteger.ONE.shiftLeft(52), TWO53 = BigInteger.ONE.shiftLeft(53);
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final int MAXIMUM_WIRE_BYTES = 64 << 20;
    private static final Set<String> READY_FIELDS = Set.of("ready", "commit_serial", "source_character_id", "final_score", "score_before_reject",
            "record_candidate", "old_record", "record_delta", "blessing_count", "refusal_count", "contract_progress", "record_written");
    private NativeOneLifeSettlement() { }

    public sealed interface State permits NullSettlement, Pending, Ready { }
    public enum NullSettlement implements State { INSTANCE }
    public record Pending(Optional<BigInteger> commitSerial) implements State {
        public Pending { Objects.requireNonNull(commitSerial); commitSerial.ifPresent(value -> nonnegative(value, "commit_serial")); }
    }
    public sealed interface Score permits Integral, Fractional {
        BigDecimal decimal();
    }
    public record Integral(BigInteger value) implements Score {
        public Integral { Objects.requireNonNull(value); }
        @Override public BigDecimal decimal() { return new BigDecimal(value); }
    }
    /** A nonintegral raw/scale source can round to 1.0 or signed zero; retain its actual float JSON lane. */
    public record Fractional(double value) implements Score {
        public Fractional { StrictJson.require(Double.isFinite(value), "one_life_settlement score must be finite"); }
        @Override public BigDecimal decimal() { return BigDecimal.valueOf(value); }
    }
    public record Ready(BigInteger sourceCharacterId, Score finalScore, Score scoreBeforeReject, BigInteger recordCandidate,
            BigInteger oldRecord, BigInteger recordDelta, BigInteger blessingCount, BigInteger refusalCount,
            BigInteger contractProgress, boolean recordWritten) implements State {
        public Ready {
            nonnegative(sourceCharacterId, "source_character_id"); Objects.requireNonNull(finalScore); Objects.requireNonNull(scoreBeforeReject);
            nonnegative(recordCandidate, "record_candidate"); nonnegative(oldRecord, "old_record"); Objects.requireNonNull(recordDelta);
            nonnegative(blessingCount, "blessing_count"); nonnegative(refusalCount, "refusal_count"); nonnegative(contractProgress, "contract_progress");
            StrictJson.require(recordDelta.equals(recordCandidate.subtract(oldRecord)), "one_life_settlement record_delta does not match candidate-old_record");
            StrictJson.require(!recordWritten || recordCandidate.compareTo(oldRecord) > 0, "one_life_settlement record_written requires a new record");
        }
    }

    /** MissingNode and explicit null reproduce raw state.get(None); actual raw packet custody remains outside this codec. */
    public static JsonNode normalize(JsonNode original) { return encode(decodeNative(original)); }
    /** Original native contract accepts ignored outer fields and exact bool-or-integer 0/1 flags. */
    public static State decodeNative(JsonNode original) {
        Objects.requireNonNull(original, "explicit MissingNode or NullNode is required");
        if (original.isMissingNode() || original.isNull()) return NullSettlement.INSTANCE;
        StrictJson.require(original instanceof ObjectNode, "one_life_settlement must be an object or null");
        boolean ready = boolean01(original.get("ready"), "ready");
        BigInteger serial = optionalNonnegative(original.get("commit_serial"), "commit_serial");
        if (!ready) return new Pending(Optional.ofNullable(serial));
        StrictJson.require(BigInteger.ONE.equals(serial), "ready one_life_settlement must have commit_serial 1");
        return new Ready(nonnegativeInteger(original.get("source_character_id"), "source_character_id"),
                normalizeScore(original.get("final_score"), "final_score"), normalizeScore(original.get("score_before_reject"), "score_before_reject"),
                nonnegativeInteger(original.get("record_candidate"), "record_candidate"), nonnegativeInteger(original.get("old_record"), "old_record"),
                integer(original.get("record_delta"), "record_delta"), nonnegativeInteger(original.get("blessing_count"), "blessing_count"),
                nonnegativeInteger(original.get("refusal_count"), "refusal_count"), nonnegativeInteger(original.get("contract_progress"), "contract_progress"),
                boolean01(original.get("record_written"), "record_written"));
    }
    /** Strict persisted normalized wire roundtrip; do not re-normalize an already normalized float as a fresh scalar. */
    public static State decodeNormalized(JsonNode normalized) {
        Objects.requireNonNull(normalized);
        if (normalized.isNull()) return NullSettlement.INSTANCE;
        StrictJson.require(normalized instanceof ObjectNode, "normalized settlement must be an object or explicit null");
        JsonNode ready = normalized.get("ready"); StrictJson.require(ready != null && ready.isBoolean(), "normalized ready must be a boolean");
        exact((ObjectNode) normalized, ready.booleanValue() ? READY_FIELDS : Set.of("ready", "commit_serial"));
        BigInteger serial = optionalNonnegative(normalized.get("commit_serial"), "commit_serial");
        if (!ready.booleanValue()) return new Pending(Optional.ofNullable(serial));
        StrictJson.require(BigInteger.ONE.equals(serial), "normalized ready settlement commit serial must be one");
        JsonNode written = normalized.get("record_written"); StrictJson.require(written != null && written.isBoolean(), "normalized record_written must be a boolean");
        return new Ready(nonnegativeInteger(normalized.get("source_character_id"), "source_character_id"),
                normalizedScore(normalized.get("final_score")), normalizedScore(normalized.get("score_before_reject")),
                nonnegativeInteger(normalized.get("record_candidate"), "record_candidate"), nonnegativeInteger(normalized.get("old_record"), "old_record"),
                integer(normalized.get("record_delta"), "record_delta"), nonnegativeInteger(normalized.get("blessing_count"), "blessing_count"),
                nonnegativeInteger(normalized.get("refusal_count"), "refusal_count"), nonnegativeInteger(normalized.get("contract_progress"), "contract_progress"), written.booleanValue());
    }
    /** Persisted normalized JSON needs binary64 tokens to preserve signed zero and integral ratio floats. */
    public static State decodeNormalized(byte[] normalized, int maximumBytes) {
        StrictJson.require(normalized != null && normalized.length > 0 && maximumBytes > 0 && maximumBytes <= MAXIMUM_WIRE_BYTES
                && normalized.length <= maximumBytes, "bounded complete normalized settlement wire required");
        return decodeNormalized(FullJsonTree.parse(normalized, maximumBytes));
    }
    public static byte[] encode(State value, int maximumBytes) {
        StrictJson.require(maximumBytes > 0 && maximumBytes <= MAXIMUM_WIRE_BYTES, "finite normalized settlement output lease required");
        return FullJsonTree.encode(encode(value), maximumBytes);
    }
    public static JsonNode encode(State value) {
        Objects.requireNonNull(value);
        if (value instanceof NullSettlement) return NullNode.instance;
        ObjectNode row = JSON.objectNode(); row.put("ready", value instanceof Ready);
        if (value instanceof Pending pending) { pending.commitSerial().ifPresentOrElse(serial -> row.put("commit_serial", serial), () -> row.putNull("commit_serial")); return row; }
        Ready ready = (Ready) value;
        row.put("commit_serial", 1); row.put("source_character_id", ready.sourceCharacterId()); row.set("final_score", encodeScore(ready.finalScore()));
        row.set("score_before_reject", encodeScore(ready.scoreBeforeReject())); row.put("record_candidate", ready.recordCandidate()); row.put("old_record", ready.oldRecord());
        row.put("record_delta", ready.recordDelta()); row.put("blessing_count", ready.blessingCount()); row.put("refusal_count", ready.refusalCount());
        row.put("contract_progress", ready.contractProgress()); row.put("record_written", ready.recordWritten()); return row;
    }
    public static JsonNode encodeScore(Score value) {
        Objects.requireNonNull(value); return value instanceof Integral integer ? JSON.numberNode(integer.value()) : JSON.numberNode(((Fractional) value).value());
    }
    /** Python's explicit raw/scale rule never guesses a CK3 scale and distinguishes scalar and ratio float normalization. */
    public static Score normalizeScore(JsonNode original, String name) {
        Objects.requireNonNull(name);
        if (original instanceof ObjectNode fixed) {
            exact(fixed, Set.of("raw", "scale"));
            BigInteger raw = integer(fixed.get("raw"), name + ".raw"), scale = integer(fixed.get("scale"), name + ".scale");
            StrictJson.require(scale.signum() > 0, "one_life_settlement fixed scale must be positive");
            BigInteger[] division = raw.divideAndRemainder(scale);
            return division[1].signum() == 0 ? new Integral(division[0]) : new Fractional(divideToDouble(raw, scale));
        }
        StrictJson.require(original != null && original.isNumber() && Double.isFinite(original.doubleValue()), "one_life_settlement " + name + " must be a finite JSON number or fixed object");
        if (original.isIntegralNumber()) return new Integral(original.bigIntegerValue());
        double number = original.doubleValue();
        return number == Math.rint(number) ? new Integral(new BigDecimal(number).toBigIntegerExact()) : new Fractional(number);
    }
    private static Score normalizedScore(JsonNode value) {
        StrictJson.require(value != null && value.isNumber(), "normalized score must be numeric, not fixed/bool/string/null");
        return value.isIntegralNumber() ? new Integral(value.bigIntegerValue()) : new Fractional(value.doubleValue());
    }
    /** Correct nearest-even rational conversion, including subnormal ties, signed zero and overflow refusal. */
    private static double divideToDouble(BigInteger signed, BigInteger denominator) {
        boolean negative = signed.signum() < 0; BigInteger numerator = signed.abs();
        int exponent = numerator.bitLength() - denominator.bitLength();
        int comparison = exponent >= 0 ? numerator.compareTo(denominator.shiftLeft(exponent)) : numerator.shiftLeft(-exponent).compareTo(denominator);
        if (comparison < 0) exponent--;
        StrictJson.require(exponent <= 1023, "one_life_settlement fixed score division overflow");
        if (exponent < -1075) return negative ? -0.0 : 0.0;
        boolean subnormal = exponent < -1022; int shift = subnormal ? 1074 : 52 - exponent;
        BigInteger scaledNumerator = shift >= 0 ? numerator.shiftLeft(shift) : numerator;
        BigInteger scaledDenominator = shift >= 0 ? denominator : denominator.shiftLeft(-shift);
        BigInteger[] division = scaledNumerator.divideAndRemainder(scaledDenominator); BigInteger significand = division[0];
        int halfway = division[1].shiftLeft(1).compareTo(scaledDenominator);
        if (halfway > 0 || halfway == 0 && significand.testBit(0)) significand = significand.add(BigInteger.ONE);
        long bits;
        if (subnormal) bits = significand.longValueExact();
        else {
            if (significand.equals(TWO53)) { exponent++; significand = significand.shiftRight(1); }
            StrictJson.require(exponent <= 1023, "one_life_settlement fixed score rounded outside finite range");
            bits = ((long) exponent + 1023) << 52 | significand.subtract(TWO52).longValueExact();
        }
        if (negative) bits |= Long.MIN_VALUE; return Double.longBitsToDouble(bits);
    }
    private static boolean boolean01(JsonNode value, String name) {
        if (value != null && value.isBoolean()) return value.booleanValue();
        BigInteger number = integer(value, name); StrictJson.require(number.equals(BigInteger.ZERO) || number.equals(BigInteger.ONE), "one_life_settlement " + name + " must be boolean or 0/1");
        return number.equals(BigInteger.ONE);
    }
    private static BigInteger optionalNonnegative(JsonNode value, String name) { return value == null || value.isNull() ? null : nonnegativeInteger(value, name); }
    private static BigInteger nonnegativeInteger(JsonNode value, String name) { BigInteger number = integer(value, name); nonnegative(number, name); return number; }
    private static BigInteger integer(JsonNode value, String name) {
        StrictJson.require(value != null && value.isIntegralNumber(), "one_life_settlement " + name + " must be an integer, never bool/float/string/null"); return value.bigIntegerValue();
    }
    private static void nonnegative(BigInteger value, String name) { Objects.requireNonNull(value); StrictJson.require(value.signum() >= 0, "one_life_settlement " + name + " must be non-negative"); }
    private static void exact(ObjectNode value, Set<String> fields) {
        java.util.HashSet<String> actual = new java.util.HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        StrictJson.require(actual.equals(fields), "one_life_settlement missing or unknown fixed/normalized fields");
    }
}
