package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.continuity.ContinuityJson;

/** Single checkpoint metadata contract. File IDs and nanoseconds remain decimal strings. */
public final class CheckpointPairCodec {
    public static final String SCHEMA = "xar.java-checkpoint-pair/v1";
    private CheckpointPairCodec() { }
    public static byte[] encode(CheckpointPair pair) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        row.set("save", fileWitnessToJson(pair.save())); row.set("driver", fileWitnessToJson(pair.driver()));
        row.set("frame", ProposalLifecycleCodec.observation(pair.frame()));
        row.put("lineage_id", pair.lineageId()); row.put("history_index", pair.historyIndex());
        row.put("save_action_id", pair.saveActionId()); row.set("native_ack_ref", pair.nativeAckRef().toJson());
        row.put("observed_at_utc", pair.observedAt().toString()); return ContinuityJson.canonical(row);
    }
    public static CheckpointPair decode(byte[] raw) {
        ObjectNode row = StrictJson.object(ContinuityJson.parseObject(raw, 65536), Set.of("schema", "save", "driver", "frame", "lineage_id", "history_index", "save_action_id", "native_ack_ref", "observed_at_utc"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "checkpoint schema");
        String at = StrictJson.text(row.get("observed_at_utc")); StrictJson.utc(at);
        return new CheckpointPair(fileWitnessFromJson(row.get("save")), fileWitnessFromJson(row.get("driver")), ProposalLifecycleCodec.decodeObservation(row.get("frame")),
                StrictJson.text(row.get("lineage_id")), StrictJson.integer(row.get("history_index"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(row.get("save_action_id")), ExactRef.fromJson(row.get("native_ack_ref")), Instant.parse(at));
    }
    public static ObjectNode fileWitnessToJson(CheckpointPair.FileWitness witness) {
        ObjectNode row = StrictJson.object(); row.set("ref", witness.reference().toJson());
        row.put("identity_schema", FileStatIdentity.SCHEMA); row.set("identity", witness.identity().toJson()); return row;
    }
    public static CheckpointPair.FileWitness fileWitnessFromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("ref", "identity_schema", "identity"));
        return new CheckpointPair.FileWitness(ExactRef.fromJson(row.get("ref")), FileStatIdentity.fromJson(row.get("identity"), StrictJson.text(row.get("identity_schema"))));
    }
}
