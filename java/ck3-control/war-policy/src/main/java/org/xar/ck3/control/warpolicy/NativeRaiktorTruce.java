package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.warpolicy.NativeTerminationTerms.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;

/** A real evaluator observation; evaluated days never imply a persisted expiry. */
public final class NativeRaiktorTruce {
    public static final String BACKEND = "ck3-1.19.0.6-native-raiktor-surrender-truce-v1";
    private NativeRaiktorTruce() { }
    public static ObjectNode normalize(JsonNode raw, NativeRaiktorAggregate.Frame frame) {
        ObjectNode value = exact(raw, Set.of("schema_version", "backend_id", "status", "failure", "snapshot_revision",
                "native_revision", "date_raw", "paused", "war_id", "active_casus_belli_database_index", "active_casus_belli_key",
                "owner_character_id", "toward_character_id", "evaluated_days", "pointer_shape_verified",
                "evaluator_double_read_stable", "same_frame_stable", "expiry_observable", "expiry_date_raw"), "native Raiktor surrender truce");
        require(number(value.get("schema_version"), 1, 1) == 1 && text(value.get("backend_id")).equals(BACKEND)
                && text(value.get("status")).equals("available") && value.get("failure").isNull(), "native Raiktor surrender truce is unavailable");
        require(positive32(value.get("war_id")) == frame.warId()
                && positiveU64(value.get("snapshot_revision")).equals(frame.snapshotRevision())
                && positiveU64(value.get("native_revision")).equals(frame.nativeRevision())
                && signed32(value.get("date_raw")) == frame.dateRaw()
                && positive32(value.get("owner_character_id")) == frame.attacker()
                && positive32(value.get("toward_character_id")) == frame.defender()
                && nonnegative32(value.get("active_casus_belli_database_index")) == frame.casusBelliIndex()
                && text(value.get("active_casus_belli_key")).equals("raiktor_claim_cb"),
                "native Raiktor surrender truce binding disagrees");
        nonnegative32(value.get("evaluated_days"));
        require(bool(value.get("paused")) && bool(value.get("pointer_shape_verified"))
                && bool(value.get("evaluator_double_read_stable")) && bool(value.get("same_frame_stable")),
                "Raiktor surrender truce stability gate failed");
        require(!bool(value.get("expiry_observable")) && value.get("expiry_date_raw").isNull(), "Raiktor surrender truce invented an expiry date");
        return value.deepCopy();
    }
}
