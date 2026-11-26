package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Facts about the single ordinary event observed within Full111's own paused read. */
public record NativeFull111OrdinaryEvent(int instanceId, int authoredOptionCount) {
    public static final String CAPABILITY = "game.state.full111-ordinary-event.v1";
    public static final String SCHEMA = "ck3_121003_full111_ordinary_event_v1";
    private static final int MAX_AUTHORED_OPTIONS = 64;
    private static final Set<String> FIELDS = Set.of("schema", "instance_id", "authored_option_count");

    public NativeFull111OrdinaryEvent {
        StrictJson.require(instanceId > 0 && authoredOptionCount >= 0 && authoredOptionCount <= MAX_AUTHORED_OPTIONS,
                "bounded Full111 ordinary event identity and authored count required");
    }

    /** The caller verifies the exact Full111 profile and, on live ingress, its original HELLO and source. */
    public static Optional<NativeFull111OrdinaryEvent> read(ObjectNode state) {
        var event = state.get("active_event");
        StrictJson.require(event != null, "Full111 requires an explicit active_event");
        if (event.isNull()) return Optional.empty();
        var summary = StrictJson.object(event, FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(summary.get("schema"))),
                "Full111 ordinary event summary schema differs");
        StrictJson.require(BooleanNode.TRUE.equals(state.get("paused"))
                        && BooleanNode.TRUE.equals(state.get("map_ready"))
                        && BooleanNode.TRUE.equals(state.path("played_character").get("alive")),
                "Full111 ordinary event summary requires a paused living map");
        return Optional.of(new NativeFull111OrdinaryEvent(
                Math.toIntExact(StrictJson.integer(summary.get("instance_id"), 1, Integer.MAX_VALUE)),
                Math.toIntExact(StrictJson.integer(summary.get("authored_option_count"), 0, MAX_AUTHORED_OPTIONS))));
    }

    ObjectNode semantic() {
        var event = StrictJson.object().put("source", "native").put("instance_id", instanceId)
                .put("authored_option_count", authoredOptionCount).putNull("option_count").putNull("title");
        // An authored list length does not establish a materialized option.
        event.putArray("options");
        return event;
    }
}
