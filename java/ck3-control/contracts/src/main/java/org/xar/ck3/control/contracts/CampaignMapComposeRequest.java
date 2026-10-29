package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;

/** Opaque Python-only map v1 request with the established exact numeric FILETIME ABI. */
public record CampaignMapComposeRequest(String machineId, GameGeneration nativeLaunch,
                                        String recordingSessionId, SavedFrame actualInitialFrame,
                                        String observedAtUtc) {
    public static final String SCHEMA = "xar.java-campaign-map-compose-request/v1";
    private static final Set<String> FIELDS = Set.of("schema", "machine_id", "observed_at_utc",
            "native_launch", "recording_session_id", "actual_initial_frame", "game_map_visible",
            "decision_text_visible");
    public CampaignMapComposeRequest {
        StrictJson.text(machineId); StrictJson.text(recordingSessionId); StrictJson.utc(observedAtUtc);
        StrictJson.require(nativeLaunch != null && actualInitialFrame != null, "typed actual launch and frame required");
    }
    public static CampaignMapComposeRequest fromBytes(byte[] body) { return fromJson(StrictJson.parse(body)); }
    public static CampaignMapComposeRequest fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "map compose request schema");
        StrictJson.trueValue(row.get("game_map_visible")); StrictJson.trueValue(row.get("decision_text_visible"));
        return new CampaignMapComposeRequest(StrictJson.text(row.get("machine_id")),
                PythonOpaqueGameGenerationV1.fromJson(row.get("native_launch")), StrictJson.text(row.get("recording_session_id")),
                SavedFrame.fromJson(row.get("actual_initial_frame")), StrictJson.text(row.get("observed_at_utc")));
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA); row.put("machine_id", machineId);
        row.put("observed_at_utc", observedAtUtc); row.set("native_launch", PythonOpaqueGameGenerationV1.toJson(nativeLaunch));
        row.put("recording_session_id", recordingSessionId); row.set("actual_initial_frame", actualInitialFrame.toJson());
        row.put("game_map_visible", true); row.put("decision_text_visible", true); return row;
    }
    public byte[] toCanonicalBytes() { return StrictJson.canonical(toJson(), StrictJson.INPUT_MAX_BYTES); }
}
