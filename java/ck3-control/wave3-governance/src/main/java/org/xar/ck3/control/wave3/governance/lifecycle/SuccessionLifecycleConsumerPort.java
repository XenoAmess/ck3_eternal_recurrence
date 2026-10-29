package org.xar.ck3.control.wave3.governance.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Set;
import static org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding.require;

/** Typed binding operations; the original consumers retain all file, save and writer checks. */
public final class SuccessionLifecycleConsumerPort {
    public static final String SCHEMA = "xar.java-succession-lifecycle-request/v1";
    public enum Constructor { LEGACY, UNKNOWN }
    public enum Consumer { CHECKPOINT, ORDINARY, ROGUE }
    public record BindingRequest(Consumer consumer, SuccessionLifecycleBinding binding) {
        public BindingRequest { require(consumer != null && consumer != Consumer.CHECKPOINT && binding != null, "explicit binding-only consumer required"); }
    }
    public record AnchorRequest(Consumer consumer, SuccessionLifecycleBinding driver, SuccessionLifecycleBinding checkpoint, SuccessionLifecycleBinding savedHistory) {
        public AnchorRequest { require(consumer != null && driver != null && checkpoint != null && savedHistory != null, "all original lifecycle anchors required"); }
    }
    private SuccessionLifecycleConsumerPort() { }
    public static SuccessionLifecycleBinding decodeNormalizeRequest(byte[] body) {
        JsonNode value = request(body, Set.of("schema", "operation", "binding"));
        require(operation(value).equals("normalize"), "normalizer operation differs from registered port");
        return SuccessionLifecycleCodec.decodeNode(SuccessionLifecycleCodec.field(value, "binding"));
    }
    public static Constructor decodeConstructorRequest(byte[] body) {
        JsonNode value = request(body, Set.of("schema", "operation"));
        return switch (operation(value)) { case "legacy" -> Constructor.LEGACY; case "unknown" -> Constructor.UNKNOWN; default -> throw new IllegalArgumentException("explicit lifecycle constructor required"); };
    }
    public static BindingRequest decodeConsumerRequest(byte[] body) {
        JsonNode value = request(body, Set.of("schema", "operation", "binding"));
        Consumer consumer = switch (operation(value)) { case "ordinary_seed" -> Consumer.ORDINARY; case "rogue_checkpoint" -> Consumer.ROGUE; default -> throw new IllegalArgumentException("explicit lifecycle binding consumer required"); };
        return new BindingRequest(consumer, SuccessionLifecycleCodec.decodeNode(SuccessionLifecycleCodec.field(value, "binding")));
    }
    public static AnchorRequest decodeAnchorRequest(byte[] body) {
        JsonNode value = request(body, Set.of("schema", "operation", "driver", "checkpoint", "saved_history"));
        Consumer consumer = switch (operation(value)) { case "checkpoint_anchors" -> Consumer.CHECKPOINT; case "ordinary_anchors" -> Consumer.ORDINARY; case "rogue_anchors" -> Consumer.ROGUE; default -> throw new IllegalArgumentException("explicit lifecycle anchor consumer required"); };
        return new AnchorRequest(consumer, SuccessionLifecycleCodec.decodeNode(SuccessionLifecycleCodec.field(value, "driver")),
                SuccessionLifecycleCodec.decodeNode(SuccessionLifecycleCodec.field(value, "checkpoint")), SuccessionLifecycleCodec.decodeNode(SuccessionLifecycleCodec.field(value, "saved_history")));
    }
    public static SuccessionLifecycleBinding construct(Constructor constructor) {
        require(constructor != null, "explicit lifecycle constructor required");
        return switch (constructor) { case LEGACY -> SuccessionLifecycleBinding.legacyRogue(); case UNKNOWN -> SuccessionLifecycleBinding.unknown(); };
    }
    public static SuccessionLifecycleBinding consume(BindingRequest request) { return gate(request.consumer(), request.binding()); }
    public static SuccessionLifecycleBinding consume(AnchorRequest request) {
        return SuccessionLifecycleConsumers.equalAnchors(gate(request.consumer(), request.driver()), gate(request.consumer(), request.checkpoint()), gate(request.consumer(), request.savedHistory()));
    }
    public static byte[] apply(byte[] body) {
        JsonNode value = SuccessionLifecycleCodec.parse(body);
        SuccessionLifecycleBinding result = switch (operation(value)) {
            case "normalize" -> decodeNormalizeRequest(body);
            case "legacy", "unknown" -> construct(decodeConstructorRequest(body));
            case "ordinary_seed", "rogue_checkpoint" -> consume(decodeConsumerRequest(body));
            case "checkpoint_anchors", "ordinary_anchors", "rogue_anchors" -> consume(decodeAnchorRequest(body));
            default -> throw new IllegalArgumentException("unknown lifecycle operation");
        };
        return SuccessionLifecycleCodec.encode(result);
    }
    private static SuccessionLifecycleBinding gate(Consumer consumer, SuccessionLifecycleBinding binding) {
        return switch (consumer) { case CHECKPOINT -> binding; case ORDINARY -> SuccessionLifecycleConsumers.ordinarySeed(binding); case ROGUE -> SuccessionLifecycleConsumers.rogueCheckpoint(binding); };
    }
    private static JsonNode request(byte[] body, Set<String> fields) {
        JsonNode value = SuccessionLifecycleCodec.parse(body); SuccessionLifecycleCodec.exact(value, fields);
        require(SCHEMA.equals(SuccessionLifecycleCodec.text(SuccessionLifecycleCodec.field(value, "schema"))), "lifecycle request schema changed"); return value;
    }
    private static String operation(JsonNode value) { return SuccessionLifecycleCodec.text(SuccessionLifecycleCodec.field(value, "operation")); }
}
