package org.xar.ck3.control.wave2.planning.realmcompare;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.wave2.planning.scoreinputs.ScoreInputFrame;

/** Already-obtained current observation; does not qualify the original query. */
public record RealmObservation(ScoreInputFrame frame, ObjectNode sourceFrame, BigInteger querySequence,
        ObjectNode provenance, SubrealmCounties component) {
    public static final String SCHEMA = "xar.ck3.realm-membership-observation/v1";

    public RealmObservation {
        require(frame != null && sourceFrame != null && provenance != null && component != null,
                "complete supplied observation fields required");
        require(querySequence != null && querySequence.signum() > 0
                && querySequence.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 query sequence required");
        require(frame.actorCharacterId().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                "realm actor requires full positive int32 identity");
        require(frame.equals(frame(sourceFrame, "current_source_frame_incomplete")), "source metadata and typed frame must agree");
        require(component.complete() && component.actorCharacterId() == frame.actorCharacterId().intValueExact()
                && component.nativeRevision().equals(frame.nativeRevision()) && component.dateRaw() == frame.dateRaw(),
                "complete component must match original supplied frame");
        sourceFrame = sourceFrame.deepCopy(); provenance = provenance.deepCopy();
    }

    @Override public ObjectNode sourceFrame() { return sourceFrame.deepCopy(); }
    @Override public ObjectNode provenance() { return provenance.deepCopy(); }

    public static RealmObservation parse(JsonNode input) {
        if (!(input instanceof ObjectNode object) || !SubrealmCounties.text(object.get("schema"), SCHEMA)
                || !SubrealmCounties.text(object.get("status"), "available")
                || !SubrealmCounties.text(object.get("scope"), SubrealmCounties.SCOPE)
                || !(object.get("source_frame") instanceof ObjectNode source)
                || !(object.get("provenance") instanceof ObjectNode provenance)) {
            throw SubrealmCounties.refused("current_complete_observation_unavailable");
        }
        ScoreInputFrame frame = frame(source, "current_source_frame_incomplete");
        BigInteger sequence = SubrealmCounties.integer(object.get("query_sequence"), "current.query_sequence",
                BigInteger.ONE, StrictJson.UINT64_MAX);
        SubrealmCounties component = SubrealmCounties.parse(object.get("component"), frame.actorCharacterId().intValueExact(),
                frame.nativeRevision(), frame.dateRaw());
        if (!component.complete()) { throw SubrealmCounties.refused("current_complete_membership_unavailable"); }
        return new RealmObservation(frame, source, sequence, provenance, component);
    }

    static ScoreInputFrame frame(ObjectNode source, String reason) {
        if (!SubrealmCounties.text(source.get("schema"), "xar.ck3.planning-source-frame/v1")
                || !SubrealmCounties.text(source.get("status"), "complete")) { throw SubrealmCounties.refused(reason); }
        ObjectNode projection = StrictJson.object();
        for (String key : new String[] {"snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id",
                "actor_character_id", "bridge_pid", "connection_generation"}) {
            JsonNode value = source.get(key);
            if (value == null) { throw SubrealmCounties.refused(reason); }
            projection.set(key, value);
        }
        try {
            ScoreInputFrame frame = ScoreInputFrame.fromJson(projection);
            if (frame.nativeRevision().signum() < 1 || frame.actorCharacterId().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0) {
                throw SubrealmCounties.refused(reason);
            }
            return frame;
        } catch (ContractViolationException error) {
            throw SubrealmCounties.refused(reason);
        }
    }
}
