package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete readonly actual samples, not a public mutation witness or rendered tooltip proof. */
public record CurrentRiteCreationBlockersSource(long sourceRiteId, int actorId, boolean isCreating,
        boolean nativeCanCreate, String blockersText, boolean windowVisible, boolean windowEnabled, boolean sampledTwice) {
    public CurrentRiteCreationBlockersSource {
        CurrentRiteCreationBlockers.requireRiteId(sourceRiteId);
        StrictJson.require(actorId != -1, "Actual packed actor except -1 required");
        CurrentRiteCreationBlockers.requireText(blockersText);
        StrictJson.require(sampledTwice, "Complete actual double-sampled blockers source required");
        // False Can/creating/visibility/enabled and empty reason text remain actual DATA.
    }
    public static CurrentRiteCreationBlockersSource decode(JsonNode value) throws IOException {
        try {
            var source = StrictJson.object(value, Set.of("schema", "source_rite_id", "actor_id", "is_creating", "native_can_create",
                    "blockers_text", "window_visible", "window_enabled", "sampled_twice"));
            CurrentRiteCreationBlockers.identity(source, "schema", CurrentRiteCreationBlockers.SOURCE_SCHEMA);
            return new CurrentRiteCreationBlockersSource(CurrentRiteCreationBlockers.riteId(source.get("source_rite_id")),
                    CurrentRiteCreationBlockers.i32(source.get("actor_id")), CurrentRiteCreationBlockers.bool(source, "is_creating"),
                    CurrentRiteCreationBlockers.bool(source, "native_can_create"), CurrentRiteCreationBlockers.text(source.get("blockers_text")),
                    CurrentRiteCreationBlockers.bool(source, "window_visible"), CurrentRiteCreationBlockers.bool(source, "window_enabled"),
                    CurrentRiteCreationBlockers.bool(source, "sampled_twice"));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact current Rite creation blockers source DATA", invalid);
        }
    }
    public ObjectNode encode() {
        return StrictJson.object().put("schema", CurrentRiteCreationBlockers.SOURCE_SCHEMA).put("source_rite_id", sourceRiteId)
                .put("actor_id", actorId).put("is_creating", isCreating).put("native_can_create", nativeCanCreate)
                .put("blockers_text", blockersText).put("window_visible", windowVisible).put("window_enabled", windowEnabled)
                .put("sampled_twice", sampledTwice);
    }
}
