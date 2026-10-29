package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Bounded pure JSON entry for the two independently closed producer functions. */
public final class ScoreInputCodec {
    private ScoreInputCodec() { }

    public static byte[] evaluate(byte[] input) { return StrictJson.canonical(evaluate(StrictJson.parse(input))); }

    public static JsonNode evaluate(JsonNode input) {
        require(input instanceof ObjectNode, "score input request object required");
        String operation = StrictJson.text(input.get("operation"));
        return switch (operation) {
            case "frame_reason" -> {
                ObjectNode object = StrictJson.object(input, Set.of("operation", "snapshot", "source"));
                require(object.get("snapshot") instanceof ObjectNode, "ordinary snapshot object required");
                ScoreInputFrameAssessment assessment = ScoreInputFrameAssessment.assess((ObjectNode) object.get("snapshot"), object.get("source"));
                yield switch (assessment) {
                    case ScoreInputFrameAssessment.Matched ignored -> JsonNodeFactory.instance.nullNode();
                    case ScoreInputFrameAssessment.Rejected rejected -> JsonNodeFactory.instance.textNode(rejected.reason());
                };
            }
            case "unknown_metric" -> {
                ObjectNode object = StrictJson.object(input, Set.of("operation", "metric", "reason"));
                JsonNode reason = object.get("reason");
                require(reason != null && reason.isTextual(), "explicit reason string required");
                yield new UnknownScoreMetric(UnknownScoreMetric.nameFromWire(StrictJson.text(object.get("metric"))), reason.textValue()).toJson();
            }
            default -> throw new IllegalArgumentException("unknown score input operation");
        };
    }
}
