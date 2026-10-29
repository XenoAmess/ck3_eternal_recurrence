package org.xar.ck3.control.runtime.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Sole persisted field contract for the replayable original cause materials, never a Root token. */
public final class PendingNaturalCauseProof {
    public static final String SCHEMA="xar.java.pending-natural-cause/v2";
    public static final int MAX_BYTES=65_536;
    private static final Set<String> FIELDS=Set.of("schema","machine_id","observed_at_utc","parent_body_sha256",
            "writer_head_sha256","writer_head_sequence","predecessor_character_id","successor_character_id",
            "old_episode_run_id","episode_epoch","driver_version","ui_clearance_qualified","final_lifecycle_applied",
            "replay_authorized","estate_reconciliation_sha256","retained_death_original_sha256","predecessor_root",
            "engine_clock_proof","actual_precommit_snapshot","successor_root_read","successor_root_result",
            "successor_semantic","original_known");
    private PendingNaturalCauseProof() { }

    public record Document(String machineId,Instant observedAtUtc,String parentBodySha256,String writerHeadSha256,
            long writerHeadSequence,int predecessorCharacterId,int successorCharacterId,String oldEpisodeRunId,
            long episodeEpoch,long driverVersion,ExactRef predecessorRoot,ExactRef engineClockProof,
            ExactRef actualPrecommitSnapshot,ExactRef successorRootRead,ExactRef successorRootResult,
            ExactRef successorSemantic,ExactRef originalKnown,String estateReconciliationSha256,
            String retainedDeathOriginalSha256) {
        public Document {
            StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);StrictJson.utc(observedAtUtc.toString());
            digest(parentBodySha256);digest(writerHeadSha256);StrictJson.safe(writerHeadSequence,0);
            StrictJson.require(predecessorCharacterId>0&&successorCharacterId>0&&predecessorCharacterId!=successorCharacterId,
                    "private natural cause requires distinct positive predecessor and successor");
            StrictJson.text(oldEpisodeRunId);StrictJson.safe(episodeEpoch,0);StrictJson.safe(driverVersion,0);
            for(ExactRef ref:List.of(predecessorRoot,engineClockProof,actualPrecommitSnapshot,successorRootRead,
                    successorRootResult,successorSemantic,originalKnown))
                StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"complete retained cause original required");
            digest(estateReconciliationSha256);digest(retainedDeathOriginalSha256);
        }
    }
    public static byte[] encode(Document value) {
        Objects.requireNonNull(value);
        ObjectNode out=StrictJson.object().put("schema",SCHEMA).put("machine_id",value.machineId())
                .put("observed_at_utc",value.observedAtUtc().toString()).put("parent_body_sha256",value.parentBodySha256())
                .put("writer_head_sha256",value.writerHeadSha256()).put("writer_head_sequence",value.writerHeadSequence())
                .put("predecessor_character_id",value.predecessorCharacterId()).put("successor_character_id",value.successorCharacterId())
                .put("old_episode_run_id",value.oldEpisodeRunId()).put("episode_epoch",value.episodeEpoch())
                .put("driver_version",value.driverVersion()).put("ui_clearance_qualified",false)
                .put("final_lifecycle_applied",false).put("replay_authorized",false)
                .put("estate_reconciliation_sha256",value.estateReconciliationSha256())
                .put("retained_death_original_sha256",value.retainedDeathOriginalSha256());
        out.set("predecessor_root",value.predecessorRoot().toJson());out.set("engine_clock_proof",value.engineClockProof().toJson());
        out.set("actual_precommit_snapshot",value.actualPrecommitSnapshot().toJson());
        out.set("successor_root_read",value.successorRootRead().toJson());out.set("successor_root_result",value.successorRootResult().toJson());
        out.set("successor_semantic",value.successorSemantic().toJson());out.set("original_known",value.originalKnown().toJson());
        return StrictJson.canonical(out,MAX_BYTES);
    }
    /** v1 has no historical sequence or bound estate/Known originals and is deliberately not upgraded. */
    public static Document decode(byte[] original) {
        ObjectNode row=StrictJson.object(StrictJson.parse(original,MAX_BYTES),FIELDS);
        StrictJson.require(SCHEMA.equals(text(row,"schema")),"retained cause v2 originals required; legacy v1 is missing cold materials");
        for(String key:List.of("ui_clearance_qualified","final_lifecycle_applied","replay_authorized")) {
            JsonNode value=row.get(key);StrictJson.require(value.isBoolean()&&!value.booleanValue(),"cause DATA cannot carry final or submission authority: "+key);
        }
        return new Document(text(row,"machine_id"),Instant.parse(StrictJson.utc(text(row,"observed_at_utc"))),
                text(row,"parent_body_sha256"),text(row,"writer_head_sha256"),integer(row,"writer_head_sequence",0),
                (int)StrictJson.integer(row.get("predecessor_character_id"),1,Integer.MAX_VALUE),
                (int)StrictJson.integer(row.get("successor_character_id"),1,Integer.MAX_VALUE),text(row,"old_episode_run_id"),
                integer(row,"episode_epoch",0),integer(row,"driver_version",0),ref(row,"predecessor_root"),ref(row,"engine_clock_proof"),
                ref(row,"actual_precommit_snapshot"),ref(row,"successor_root_read"),ref(row,"successor_root_result"),
                ref(row,"successor_semantic"),ref(row,"original_known"),text(row,"estate_reconciliation_sha256"),text(row,"retained_death_original_sha256"));
    }
    private static String text(ObjectNode value,String field) {return StrictJson.text(value.get(field));}
    private static ExactRef ref(ObjectNode value,String field) {return ExactRef.fromJson(value.get(field));}
    private static long integer(ObjectNode value,String field,long minimum) {return StrictJson.integer(value.get(field),minimum,StrictJson.MAX_SAFE_INTEGER);}
    private static void digest(String value) {StrictJson.require(value!=null&&value.matches("[0-9a-f]{64}"),"original SHA256 required");}
}
