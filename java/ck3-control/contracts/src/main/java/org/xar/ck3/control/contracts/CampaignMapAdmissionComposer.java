package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;

/** Production Java map producer. All input validation precedes constructing typed state. */
public final class CampaignMapAdmissionComposer {
    public static final String REQUEST_SCHEMA = "xar.java-campaign-map-compose-request/v1";
    private CampaignMapAdmissionComposer() { }
    public static byte[] compose(byte[] requestBody) {
        ObjectNode row = StrictJson.object(StrictJson.parse(requestBody), Set.of("schema", "machine_id",
                "observed_at_utc", "native_launch", "recording_session_id", "actual_initial_frame",
                "game_map_visible", "decision_text_visible"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(row.get("schema"))), "map compose request schema");
        StrictJson.trueValue(row.get("game_map_visible")); StrictJson.trueValue(row.get("decision_text_visible"));
        CampaignMapAdmission admission = new CampaignMapAdmission(StrictJson.text(row.get("machine_id")),
                GameGeneration.fromJson(row.get("native_launch")), StrictJson.text(row.get("recording_session_id")),
                SavedFrame.fromJson(row.get("actual_initial_frame")), StrictJson.text(row.get("observed_at_utc")));
        // Validate the produced wire contract too; no Number/string field alias is accepted.
        return CampaignMapAdmission.fromJson(admission.toJson()).toCanonicalBytes();
    }
}
