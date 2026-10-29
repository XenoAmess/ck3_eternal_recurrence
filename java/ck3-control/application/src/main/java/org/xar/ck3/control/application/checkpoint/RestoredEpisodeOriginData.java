package org.xar.ck3.control.application.checkpoint;

import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;

/** Serializable original restoration DATA. Decoding this record never creates ReboundOrigin or current permission. */
public record RestoredEpisodeOriginData(String requestId,SessionIdentity savedOwner,SessionIdentity previousOwner,
        SessionIdentity restoredOwner,String restoredConnectionGeneration,G2Source source,CheckpointPair pair,
        CheckpointPair.FileWitness materialWitness,String originalSavedHeadDigest,long attachmentSequence,
        String attachmentHeadDigest,String attachmentEventIdentity,WriterContracts.Pin lifecycleEvidence,
        WriterContracts.Pin restoredNativeEvidence,SemanticEvidence originalRestoredSemantic,ExactRef originalHistoryBasis) {
    public static final String SCHEMA="xar.java-restored-episode-origin/v1";
    public static final int MAXIMUM_BYTES=1024*1024;
    private static final Set<String> FIELDS=Set.of("schema","request_id","saved_owner","previous_owner","restored_owner",
            "restored_connection_generation","source","pair","material_witness","original_saved_head_sha256",
            "attachment_sequence","attachment_head_sha256","attachment_event_identity","lifecycle_evidence",
            "restored_native_evidence","original_restored_semantic","original_history_basis");
    public RestoredEpisodeOriginData {
        StrictJson.text(requestId);Objects.requireNonNull(savedOwner);Objects.requireNonNull(previousOwner);Objects.requireNonNull(restoredOwner);
        Objects.requireNonNull(source);Objects.requireNonNull(pair);Objects.requireNonNull(materialWitness);
        Objects.requireNonNull(lifecycleEvidence);Objects.requireNonNull(restoredNativeEvidence);
        Objects.requireNonNull(originalRestoredSemantic);Objects.requireNonNull(originalHistoryBasis);
        StrictJson.require(restoredConnectionGeneration!=null&&restoredConnectionGeneration.matches("[1-9][0-9]*")
                &&restoredConnectionGeneration.length()<=20&&new java.math.BigInteger(restoredConnectionGeneration).bitLength()<=64,
                "canonical positive decimal replacement connection generation required");
        WriterContracts.requireDigest(originalSavedHeadDigest);WriterContracts.requireDigest(attachmentHeadDigest);
        WriterContracts.requireDigest(attachmentEventIdentity);StrictJson.safe(attachmentSequence,1);
        StrictJson.require(savedOwner.machineId().equals(previousOwner.machineId())&&previousOwner.machineId().equals(restoredOwner.machineId())
                &&restoredOwner.machineId().equals(pair.frame().machineId())&&restoredOwner.machineId().equals(source.machineId())
                &&savedOwner.game().equals(pair.frame().game())&&!previousOwner.game().equals(restoredOwner.game())
                &&!previousOwner.sessionId().equals(restoredOwner.sessionId())
                &&originalRestoredSemantic.frame().game().equals(restoredOwner.game())
                &&originalRestoredSemantic.frame().machineId().equals(restoredOwner.machineId())
                &&originalRestoredSemantic.frame().frame().episodeRunId().equals(pair.frame().frame().episodeRunId())
                &&originalRestoredSemantic.frame().frame().identity().player().equals(pair.frame().frame().identity().player())
                &&originalRestoredSemantic.frame().frame().identity().dateRaw().equals(pair.frame().frame().identity().dateRaw()),
                "restoration DATA must keep saved, previous and actually restored Game/session/actor/date roles distinct");
    }
    public byte[] encode() {
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("request_id",requestId);
        row.set("saved_owner",OrdinaryCycleTransitions.sessionToJson(savedOwner));
        row.set("previous_owner",OrdinaryCycleTransitions.sessionToJson(previousOwner));
        row.set("restored_owner",OrdinaryCycleTransitions.sessionToJson(restoredOwner));
        row.put("restored_connection_generation",restoredConnectionGeneration);
        row.set("source",StrictJson.parse(G2Wire.sourceBytes(source)));row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
        row.set("material_witness",CheckpointPairCodec.fileWitnessToJson(materialWitness));
        row.put("original_saved_head_sha256",originalSavedHeadDigest);row.put("attachment_sequence",attachmentSequence);
        row.put("attachment_head_sha256",attachmentHeadDigest);row.put("attachment_event_identity",attachmentEventIdentity);
        row.set("lifecycle_evidence",LifecycleProofCodec.encodePin(lifecycleEvidence));
        row.set("restored_native_evidence",LifecycleProofCodec.encodePin(restoredNativeEvidence));
        row.set("original_restored_semantic",OrdinaryCycleTransitions.semanticToJson(originalRestoredSemantic));
        row.set("original_history_basis",originalHistoryBasis.toJson());
        byte[] bytes=StrictJson.canonical(row,MAXIMUM_BYTES);StrictJson.require(bytes.length<=MAXIMUM_BYTES,"bounded restoration original DATA required");return bytes;
    }
    public static RestoredEpisodeOriginData decode(byte[] bytes) {
        StrictJson.require(bytes!=null&&bytes.length>0&&bytes.length<=MAXIMUM_BYTES,"bounded restoration original DATA required");
        var row=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_BYTES),FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"restoration original DATA schema required");
        return new RestoredEpisodeOriginData(StrictJson.text(row.get("request_id")),
                OrdinaryCycleTransitions.sessionFromJson(row.get("saved_owner")),OrdinaryCycleTransitions.sessionFromJson(row.get("previous_owner")),
                OrdinaryCycleTransitions.sessionFromJson(row.get("restored_owner")),StrictJson.text(row.get("restored_connection_generation")),
                G2Wire.source(row.get("source")),CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair"))),
                CheckpointPairCodec.fileWitnessFromJson(row.get("material_witness")),StrictJson.text(row.get("original_saved_head_sha256")),
                StrictJson.integer(row.get("attachment_sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("attachment_head_sha256")),
                StrictJson.text(row.get("attachment_event_identity")),LifecycleProofCodec.decodePin(row.get("lifecycle_evidence")),
                LifecycleProofCodec.decodePin(row.get("restored_native_evidence")),OrdinaryCycleTransitions.semanticFromJson(row.get("original_restored_semantic")),
                ExactRef.fromJson(row.get("original_history_basis")));
    }
}
