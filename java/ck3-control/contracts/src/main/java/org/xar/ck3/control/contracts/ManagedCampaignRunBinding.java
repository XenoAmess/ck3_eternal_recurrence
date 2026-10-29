package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

/** Allocator DATA only. This value does not prove physical custody, launch admission or a managed session. */
public record ManagedCampaignRunBinding(String runId, String stateDir, String bridgePipe, String hostPath,
        String frozenArgvSha256) {
    private static final Set<String> FIELDS = Set.of("run_id", "state_dir", "bridge_pipe", "host_path", "frozen_argv_sha256");
    public ManagedCampaignRunBinding {
        text(runId); text(stateDir); text(bridgePipe); text(hostPath);
        StrictJson.require(frozenArgvSha256 != null && frozenArgvSha256.matches("[a-f0-9]{64}"), "actual frozen argv lowercase SHA256 required");
    }
    /** Never infer this value from a nullable episode pair or normalize its original allocator paths. */
    public static ManagedCampaignRunBinding parse(JsonNode original) {
        StrictJson.require(original instanceof ObjectNode, "managed campaign run binding must be an object");
        Set<String> actual = new HashSet<>(); original.fieldNames().forEachRemaining(actual::add);
        StrictJson.require(actual.equals(FIELDS), "managed campaign run binding requires exactly its five original fields");
        return new ManagedCampaignRunBinding(text(original.get("run_id")), text(original.get("state_dir")), text(original.get("bridge_pipe")),
                text(original.get("host_path")), text(original.get("frozen_argv_sha256")));
    }
    public ObjectNode toJson() {
        return JsonNodeFactory.instance.objectNode().put("run_id", runId).put("state_dir", stateDir).put("bridge_pipe", bridgePipe)
                .put("host_path", hostPath).put("frozen_argv_sha256", frozenArgvSha256);
    }
    private static String text(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "managed campaign binding fields must be strings, never null/numbers/bools");
        return text(node.textValue());
    }
    private static String text(String value) {
        Objects.requireNonNull(value); StrictJson.require(!value.isEmpty(), "nonempty original managed campaign identity required"); return value;
    }
}
