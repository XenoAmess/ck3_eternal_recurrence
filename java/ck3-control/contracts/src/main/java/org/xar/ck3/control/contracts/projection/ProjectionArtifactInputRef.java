package org.xar.ck3.control.contracts.projection;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** References are claims only. Only the server-configured scope can admit their contents. */
public record ProjectionArtifactInputRef(ExactRef inputRef, ExactRef leaseRef) {
    public ProjectionArtifactInputRef {
        absolute(inputRef); absolute(leaseRef);
        StrictJson.require(inputRef.bytes() > 0 && leaseRef.bytes() > 0
                && leaseRef.bytes() <= StrictJson.INPUT_MAX_BYTES, "nonempty artifact and finite lease metadata required");
    }
    public static ProjectionArtifactInputRef fromJson(JsonNode value) {
        var object = StrictJson.object(value, Set.of("input_ref", "lease_ref"));
        return new ProjectionArtifactInputRef(ExactRef.fromJson(object.get("input_ref")), ExactRef.fromJson(object.get("lease_ref")));
    }
    private static void absolute(ExactRef ref) {
        Objects.requireNonNull(ref);
        Path path = Path.of(ref.path());
        StrictJson.require(path.isAbsolute() && path.normalize().equals(path), "normalized absolute artifact reference required");
    }
}
