package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;

/** Established opaque Python-only map v1 receipt; this lane never passes through JavaScript Number. */
public record CampaignMapAdmission(String machineId, GameGeneration game, String recordingSessionId,
                                   SavedFrame actualInitialFrame, String observedAtUtc) {
    public static final String SCHEMA = "xar.current-saved-root-map-review/v1";
    public CampaignMapAdmission {
        StrictJson.text(machineId); StrictJson.text(recordingSessionId); StrictJson.utc(observedAtUtc);
        StrictJson.require(game != null && actualInitialFrame != null, "typed actual launch and frame required");
    }
    public static CampaignMapAdmission fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "status", "reviewer", "game_pid",
                "game_creation_filetime", "Game_map_visible", "decision_text_visible", "recording_session_id",
                "actual_initial_frame", "schema", "observed_at_utc"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))
                && "GREEN".equals(StrictJson.text(row.get("status")))
                && "/root".equals(StrictJson.text(row.get("reviewer"))), "actual Root reviewed map contract");
        StrictJson.trueValue(row.get("Game_map_visible")); StrictJson.trueValue(row.get("decision_text_visible"));
        return new CampaignMapAdmission(StrictJson.text(row.get("machine_id")),
                new GameGeneration(StrictJson.integer(row.get("game_pid"), 1, 4_294_967_295L),
                        PythonOpaqueGameGenerationV1.filetime(row.get("game_creation_filetime"))),
                StrictJson.text(row.get("recording_session_id")), SavedFrame.fromJson(row.get("actual_initial_frame")),
                StrictJson.text(row.get("observed_at_utc")));
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object();
        row.put("machine_id", machineId); row.put("status", "GREEN"); row.put("reviewer", "/root");
        row.put("game_pid", game.pid()); row.put("game_creation_filetime", game.creationFiletime().value());
        row.put("Game_map_visible", true); row.put("decision_text_visible", true);
        row.put("recording_session_id", recordingSessionId); row.set("actual_initial_frame", actualInitialFrame.toJson());
        row.put("schema", SCHEMA); row.put("observed_at_utc", observedAtUtc);
        return row;
    }
    public byte[] toCanonicalBytes() { return StrictJson.canonical(toJson(), StrictJson.OUTPUT_MAX_BYTES); }
}
