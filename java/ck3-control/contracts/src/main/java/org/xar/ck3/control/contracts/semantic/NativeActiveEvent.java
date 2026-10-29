package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;

/** The original active_event semantic projection, independent of the stricter native event-window wire. */
public final class NativeActiveEvent {
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private NativeActiveEvent() { }

    /** MissingNode and JSON null both implement the original outer dict.get/null case.
     * Original Native bytes remain with their existing archive; this returns the shared semantic projection.
     */
    public static JsonNode normalize(JsonNode original, String defaultSource) {
        Objects.requireNonNull(original, "use MissingNode for a missing JSON field");
        if (original.isMissingNode() || original.isNull()) return NullNode.getInstance();
        require(original.isObject(), "active_event must be an object or null");
        return encode(decode((ObjectNode) original, defaultSource));
    }

    /** Original backend-neutral chooser. This does not normalize, infer display order or grant native legality.
     * Integer identity remains unbounded here; the actual native caller owns its narrower option bound.
     */
    public static Optional<BigInteger> chooseOptionNumber(JsonNode original) {
        Objects.requireNonNull(original, "use MissingNode for a missing JSON field");
        if (!original.isObject() || !original.path("options").isArray()) return Optional.empty();
        BigInteger best = null;
        double bestScore = 0.0;
        for (JsonNode option : original.get("options")) {
            if (!option.isObject() || !option.path("enabled").isBoolean() || !option.get("enabled").booleanValue()) continue;
            JsonNode number = option.get("option_number");
            if (number == null || !number.isIntegralNumber() || number.bigIntegerValue().signum() <= 0) continue;
            JsonNode rawScore = option.get("strategy_score");
            double score = rawScore != null && rawScore.isNumber() ? rawScore.doubleValue() : 0.0;
            if (rawScore != null && rawScore.isIntegralNumber() && !Double.isFinite(score))
                throw new ArithmeticException("int too large to convert to float");
            // Python tuple comparison treats signed zero as equal. Double.compare would alter it.
            if (best == null || score > bestScore || score == bestScore && number.bigIntegerValue().compareTo(best) < 0) {
                best = number.bigIntegerValue(); bestScore = score;
            }
        }
        return Optional.ofNullable(best);
    }

    private record Event(String source, Optional<BigInteger> instanceId, Optional<BigInteger> optionCount,
            Optional<String> title, List<Option> options) {
        private Event { options = List.copyOf(options); }
    }
    /** Score retains the existing JSON numeric union; no boolean/string coercion or double round trip. */
    private record NumericScore(JsonNode original) {
        private NumericScore {
            require(original.isIntegralNumber() || original.isFloatingPointNumber(),
                    "active_event option strategy_score must be numeric or null");
            original = original.deepCopy();
        }
    }
    private record Option(BigInteger number, Optional<String> label, boolean enabled,
            Optional<NumericScore> score, Optional<List<String>> reasons) {
        private Option { reasons = reasons.map(List::copyOf); }
    }

    private static Event decode(ObjectNode value, String defaultSource) {
        Optional<BigInteger> instance = nullableNonnegative(value.get("instance_id"), "active_event instance_id");
        JsonNode rawTitle = value.get("title");
        Optional<String> title = Optional.empty();
        if (!absentOrNull(rawTitle)) {
            require(rawTitle.isTextual() && hasPythonNonWhitespace(rawTitle.textValue()),
                    "active_event title must be a non-empty string or null");
            title = Optional.of(rawTitle.textValue());
        }
        String source;
        if (!value.has("source")) source = defaultSource;
        else {
            JsonNode rawSource = value.get("source");
            require(rawSource.isTextual(), "active_event source must be a non-empty string");
            source = rawSource.textValue();
        }
        require(source != null && !source.isEmpty(), "active_event source must be a non-empty string");
        JsonNode rawOptions = value.get("options");
        require(absentOrNull(rawOptions) || rawOptions.isArray(), "active_event options must be a list");
        TreeMap<BigInteger, Option> byNumber = new TreeMap<>();
        if (!absentOrNull(rawOptions)) {
            BigInteger fallback = BigInteger.ONE;
            for (JsonNode raw : rawOptions) {
                require(raw.isObject(), "active_event option must be an object");
                Option option = option((ObjectNode) raw, fallback, byNumber.keySet());
                byNumber.put(option.number(), option);
                fallback = fallback.add(BigInteger.ONE);
            }
        }
        JsonNode rawCount = value.get("option_count");
        Optional<BigInteger> count;
        if (absentOrNull(rawCount) && !absentOrNull(rawOptions)) count = Optional.of(BigInteger.valueOf(byNumber.size()));
        else count = nullableNonnegative(rawCount, "active_event option_count");
        if (count.isPresent()) {
            BigInteger total = count.orElseThrow();
            require(byNumber.isEmpty() || byNumber.lastKey().compareTo(total) <= 0, "active_event option exceeds option_count");
            for (BigInteger number = BigInteger.ONE; number.compareTo(total) <= 0; number = number.add(BigInteger.ONE)) {
                byNumber.putIfAbsent(number, new Option(number, Optional.empty(), true, Optional.empty(), Optional.empty()));
            }
        }
        return new Event(source, instance, count, title, new ArrayList<>(byNumber.values()));
    }

    private static Option option(ObjectNode raw, BigInteger fallback, Set<BigInteger> existingNumbers) {
        JsonNode rawNumber = raw.get("option_number");
        BigInteger number;
        if (absentOrNull(rawNumber)) {
            JsonNode rawIndex = raw.get("index");
            number = absentOrNull(rawIndex) ? fallback : nonnegative(rawIndex, "active_event option index").add(BigInteger.ONE);
        } else number = positive(rawNumber, "active_event option_number");
        // Unlike a missing index, an explicit null index must fail even when the number defaulted.
        BigInteger index = raw.has("index") ? nonnegative(raw.get("index"), "active_event option index") : number.subtract(BigInteger.ONE);
        require(index.equals(number.subtract(BigInteger.ONE)), "active_event option index and option_number disagree");
        require(!existingNumbers.contains(number), "active_event option numbers must be unique");
        JsonNode rawLabel = raw.has("label") ? raw.get("label") : raw.get("visible_text");
        Optional<String> label = Optional.empty();
        if (!absentOrNull(rawLabel)) {
            require(rawLabel.isTextual(), "active_event option label must be a string or null");
            label = Optional.of(rawLabel.textValue());
        }
        boolean enabled = true;
        if (raw.has("enabled")) {
            JsonNode rawEnabled = raw.get("enabled");
            require(rawEnabled.isBoolean(), "active_event option enabled must be boolean");
            enabled = rawEnabled.booleanValue();
        }
        JsonNode rawScore = raw.get("strategy_score");
        Optional<NumericScore> score = absentOrNull(rawScore) ? Optional.empty() : Optional.of(new NumericScore(rawScore));
        JsonNode rawReasons = raw.get("strategy_reasons");
        Optional<List<String>> reasons = Optional.empty();
        if (rawReasons != null && rawReasons.isArray()) {
            List<String> strings = new ArrayList<>();
            rawReasons.forEach(reason -> { if (reason.isTextual()) strings.add(reason.textValue()); });
            reasons = Optional.of(strings);
        }
        return new Option(number, label, enabled, score, reasons);
    }

    private static ObjectNode encode(Event event) {
        ObjectNode result = JSON.objectNode().put("source", event.source());
        event.instanceId().ifPresentOrElse(value -> result.put("instance_id", value), () -> result.putNull("instance_id"));
        event.optionCount().ifPresentOrElse(value -> result.put("option_count", value), () -> result.putNull("option_count"));
        event.title().ifPresentOrElse(value -> result.put("title", value), () -> result.putNull("title"));
        ArrayNode options = result.putArray("options");
        for (Option option : event.options()) {
            ObjectNode row = options.addObject().put("index", option.number().subtract(BigInteger.ONE))
                    .put("option_number", option.number());
            option.label().ifPresentOrElse(value -> row.put("label", value), () -> row.putNull("label"));
            row.put("enabled", option.enabled());
            option.score().ifPresent(score -> row.set("strategy_score", score.original().deepCopy()));
            option.reasons().ifPresent(reasons -> {
                ArrayNode list = row.putArray("strategy_reasons"); reasons.forEach(list::add);
            });
        }
        return result;
    }

    private static Optional<BigInteger> nullableNonnegative(JsonNode raw, String field) {
        return absentOrNull(raw) ? Optional.empty() : Optional.of(nonnegative(raw, field));
    }
    private static BigInteger nonnegative(JsonNode raw, String field) {
        require(raw != null && raw.isIntegralNumber() && raw.bigIntegerValue().signum() >= 0,
                field + " must be a non-negative integer");
        return raw.bigIntegerValue();
    }
    private static BigInteger positive(JsonNode raw, String field) {
        require(raw != null && raw.isIntegralNumber() && raw.bigIntegerValue().signum() > 0,
                field + " must be a positive integer");
        return raw.bigIntegerValue();
    }
    private static boolean absentOrNull(JsonNode value) { return value == null || value.isNull(); }
    private static boolean hasPythonNonWhitespace(String value) {
        return value.codePoints().anyMatch(point -> !(Character.isWhitespace(point) || Character.isSpaceChar(point) || point == 0x85));
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
