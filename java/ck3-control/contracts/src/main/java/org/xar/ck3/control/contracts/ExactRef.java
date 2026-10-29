package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;

public record ExactRef(String path, long bytes, String sha256) {
    public ExactRef {
        StrictJson.text(path); StrictJson.safe(bytes, 0);
        StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "lowercase SHA-256 required");
    }
    public static ExactRef fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("path", "bytes", "sha256"));
        return new ExactRef(StrictJson.text(row.get("path")),
                StrictJson.integer(row.get("bytes"), 0, StrictJson.MAX_SAFE_INTEGER), StrictJson.text(row.get("sha256")));
    }
    /** Optional metadata only: a missing field and explicit null carry no reference. */
    public static java.util.Optional<ExactRef> optionalFromJson(JsonNode value) {
        return value==null||value.isNull()?java.util.Optional.empty():java.util.Optional.of(fromJson(value));
    }
    public static JsonNode optionalToJson(java.util.Optional<ExactRef> value) {
        java.util.Objects.requireNonNull(value);
        return value.isPresent()?value.orElseThrow().toJson():com.fasterxml.jackson.databind.node.NullNode.getInstance();
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object();
        row.put("path", path); row.put("bytes", bytes); row.put("sha256", sha256);
        return row;
    }
}
