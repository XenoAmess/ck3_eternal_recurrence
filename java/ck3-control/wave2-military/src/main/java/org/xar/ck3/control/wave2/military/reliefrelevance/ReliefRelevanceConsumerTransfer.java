package org.xar.ck3.control.wave2.military.reliefrelevance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** The four real strategy call sites use the existing same-document realm-siege implementation. */
public final class ReliefRelevanceConsumerTransfer {
    public static final String INPUT_SCHEMA = "xar.relief-relevance-consumer-transfer-input.v1";
    public static final String OUTPUT_SCHEMA = "xar.relief-relevance-consumer-transfer-output.v1";
    public static final int INPUT_MAX_BYTES = 131_072;
    public static final int OUTPUT_MAX_BYTES = 16_384;
    public static final String SOURCE_PATH = "ck3_autonomous_player/src/xar_autoplayer/strategy.py";
    private ReliefRelevanceConsumerTransfer() { }
    public enum Consumer {
        TURN_CORE("turn_core", "_choose_one_life_turn_core"),
        RESERVE_RAISE("reserve_raise", "_defender_siege_reserve_raise_plan"),
        STATIONARY_WATCH("stationary_watch", "_defender_siege_observation_one_day_watch"),
        RELIEF_ASSESSMENT("relief_assessment", "_primary_defender_siege_relief_assessment");
        private final String wire;
        private final String function;
        Consumer(String wire, String function) { this.wire = wire; this.function = function; }
        public String wire() { return wire; }
        public String function() { return function; }
        public static Consumer fromWire(String value) {
            for (Consumer consumer : values()) { if (consumer.wire.equals(value)) { return consumer; } }
            throw new IllegalArgumentException("unknown original relief consumer");
        }
    }
    public record Request(Consumer consumer, ReliefRelevancePolicy.Request input) {
        public Request { Objects.requireNonNull(consumer); Objects.requireNonNull(input); }
    }
    public sealed interface Value permits Observed { }
    public record Observed(boolean relevant) implements Value { }
    public record Response(Consumer consumer, Value value) {
        public Response { Objects.requireNonNull(consumer); Objects.requireNonNull(value); }
    }
    public static Request decode(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw, INPUT_MAX_BYTES), Set.of("schema", "consumer", "input"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(node.get("schema"))), "unsupported relief transfer schema");
        return new Request(Consumer.fromWire(StrictJson.text(node.get("consumer"))), ReliefRelevanceCodec.decodeNode(node.get("input")));
    }
    public static Response apply(Request request) {
        Objects.requireNonNull(request);
        // Explicit null selectors are legal in the existing RealmSiege.Request.
        // Its factual predicate evaluates them as false; this adapter must not invent UNKNOWN.
        return new Response(request.consumer(), new Observed(
                ReliefRelevancePolicy.assess(request.input()).candidateSiegeReliefRelevant()));
    }
    public static byte[] evaluate(byte[] raw) { return encode(apply(decode(raw))); }
    public static byte[] encode(Response response) {
        ObjectNode node = StrictJson.object(); node.put("schema", OUTPUT_SCHEMA); node.put("consumer", response.consumer().wire());
        node.put("source_path", SOURCE_PATH); node.put("consumer_function", response.consumer().function()); node.put("native_action_authorized", false);
        node.put("observation_status", "available"); node.put("value", ((Observed) response.value()).relevant());
        node.putNull("required_observation");
        return StrictJson.canonical(node, OUTPUT_MAX_BYTES);
    }
}
