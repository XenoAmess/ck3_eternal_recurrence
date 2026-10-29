package org.xar.ck3.control.wave2.military.refuge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Typed boundary for the three existing imported consumers; it grants no native qualification. */
public final class DefenderRefugeConsumerTransfer {
    public static final String INPUT_SCHEMA = "xar.defender-refuge-consumer-transfer-input.v1";
    public static final String OUTPUT_SCHEMA = "xar.defender-refuge-consumer-transfer-output.v1";
    public static final int INPUT_MAX_BYTES = 131_072;
    public static final int OUTPUT_MAX_BYTES = 16_384;
    private DefenderRefugeConsumerTransfer() { }

    public enum Consumer {
        STRATEGY_CAPITALS("strategy_capitals", "ck3_autonomous_player/src/xar_autoplayer/strategy.py", "direct_vassal_capital_province_ids"),
        STRATEGY_LIFECYCLE("strategy_lifecycle", "ck3_autonomous_player/src/xar_autoplayer/strategy.py", "direct_vassal_refuge_lifecycle_scope"),
        NATIVE_CAPABILITIES("native_capabilities", "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", "same_frame_direct_vassal_refuge_scope");
        private final String wire;
        private final String sourcePath;
        private final String importedFunction;
        Consumer(String wire, String sourcePath, String importedFunction) {
            this.wire = wire; this.sourcePath = sourcePath; this.importedFunction = importedFunction;
        }
        public String wire() { return wire; }
        public String sourcePath() { return sourcePath; }
        public String importedFunction() { return importedFunction; }
        public static Consumer fromWire(String value) {
            for (Consumer consumer : values()) { if (consumer.wire.equals(value)) { return consumer; } }
            throw new IllegalArgumentException("unknown original refuge consumer");
        }
    }
    public record Request(Consumer consumer, DefenderRefugePolicy.Request input) {
        public Request { Objects.requireNonNull(consumer); Objects.requireNonNull(input); }
    }
    public sealed interface Value permits Capitals, Scope { boolean available(); }
    public record Capitals(List<Integer> provinceIds) implements Value {
        public Capitals { provinceIds = provinceIds == null ? null : List.copyOf(provinceIds); }
        @Override public boolean available() { return provinceIds != null; }
    }
    public record Scope(DefenderRefugePolicy.RefugeScope scope) implements Value {
        @Override public boolean available() { return scope != null; }
    }
    public record Response(Consumer consumer, Value value) {
        public Response {
            Objects.requireNonNull(consumer); Objects.requireNonNull(value);
            StrictJson.require((consumer == Consumer.STRATEGY_CAPITALS) == (value instanceof Capitals),
                    "consumer and typed result branch differ");
        }
    }
    public static Request decode(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw, INPUT_MAX_BYTES), Set.of("schema", "consumer", "input"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(node.get("schema"))), "unsupported refuge transfer schema");
        return new Request(Consumer.fromWire(StrictJson.text(node.get("consumer"))), DefenderRefugeCodec.decodeNode(node.get("input")));
    }
    public static Response apply(Request request) {
        Objects.requireNonNull(request);
        return new Response(request.consumer(), switch (request.consumer()) {
            case STRATEGY_CAPITALS -> new Capitals(DefenderRefugePolicy.directVassalCapitalProvinceIds(request.input().root()));
            case STRATEGY_LIFECYCLE -> new Scope(DefenderRefugePolicy.lifecycleScope(request.input().snapshot(), request.input().root()));
            case NATIVE_CAPABILITIES -> new Scope(DefenderRefugePolicy.sameFrameScope(request.input().snapshot(), request.input().cachedQuery()));
        });
    }
    public static byte[] evaluate(byte[] raw) { return encode(apply(decode(raw))); }
    public static byte[] encode(Response response) {
        ObjectNode node = StrictJson.object(); node.put("schema", OUTPUT_SCHEMA); node.put("consumer", response.consumer().wire());
        node.put("source_path", response.consumer().sourcePath()); node.put("imported_function", response.consumer().importedFunction());
        node.put("observation_status", response.value().available() ? "available" : "unavailable");
        node.put("native_action_authorized", false);
        // Encode the original consumed value through the single existing assessment serializer.
        DefenderRefugePolicy.Assessment assessment = response.value() instanceof Capitals capitals
                ? new DefenderRefugePolicy.Assessment(capitals.provinceIds(), null, null)
                : new DefenderRefugePolicy.Assessment(null, ((Scope) response.value()).scope(), null);
        JsonNode projection = StrictJson.parse(DefenderRefugeCodec.encodeAssessment(assessment));
        node.set("value", projection.get(response.value() instanceof Capitals ? "direct_vassal_capital_province_ids" : "lifecycle_scope"));
        return StrictJson.canonical(node, OUTPUT_MAX_BYTES);
    }
}
