package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual immutable two-string query DATA. Construction grants no lease or write permission. */
public record CurrentRiteTextSource(long sourceRiteId, int actorId, boolean isCreating,
        String name, String description, boolean windowVisible, boolean windowEnabled,
        boolean blockedByUnrelatedModal, boolean writeAdmissible) {
    public CurrentRiteTextSource {
        CurrentRiteText.requireRiteId(sourceRiteId);
        StrictJson.require(actorId != -1, "Actual packed actor except -1 required");
        CurrentRiteText.requireActualText(name); CurrentRiteText.requireActualText(description);
        if (writeAdmissible) StrictJson.require(isCreating && windowVisible && windowEnabled && !blockedByUnrelatedModal,
                "Admitted text source lacks actual native window prerequisites");
    }
    public static CurrentRiteTextSource decode(JsonNode value) throws IOException {
        try {
            var source = StrictJson.object(value, Set.of("schema", "source_rite_id", "actor_id", "is_creating", "name",
                    "description", "window_visible", "window_enabled", "blocked_by_unrelated_modal", "write_admissible"));
            CurrentRiteText.identity(source, "schema", CurrentRiteText.SOURCE_SCHEMA);
            return new CurrentRiteTextSource(CurrentRiteText.riteId(source.get("source_rite_id")), CurrentRiteText.i32(source.get("actor_id")),
                    CurrentRiteText.bool(source, "is_creating"), CurrentRiteText.actualText(source.get("name")),
                    CurrentRiteText.actualText(source.get("description")), CurrentRiteText.bool(source, "window_visible"),
                    CurrentRiteText.bool(source, "window_enabled"), CurrentRiteText.bool(source, "blocked_by_unrelated_modal"),
                    CurrentRiteText.bool(source, "write_admissible"));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact current Rite text source DATA", invalid);
        }
    }
    public ObjectNode encode() {
        return StrictJson.object().put("schema", CurrentRiteText.SOURCE_SCHEMA).put("source_rite_id", sourceRiteId)
                .put("actor_id", actorId).put("is_creating", isCreating).put("name", name).put("description", description)
                .put("window_visible", windowVisible).put("window_enabled", windowEnabled)
                .put("blocked_by_unrelated_modal", blockedByUnrelatedModal).put("write_admissible", writeAdmissible);
    }
}
