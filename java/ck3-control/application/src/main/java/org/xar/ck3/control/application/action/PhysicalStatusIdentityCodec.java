package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Independent versioned fact codec. Parsing cannot create a physical read scope or a native permit. */
public final class PhysicalStatusIdentityCodec {
    public static final String SCHEMA="xar.physical-status-identity/v1";
    private PhysicalStatusIdentityCodec(){}
    /** One digest of the complete typed identity; it is factual binding data and grants no scope. */
    public static String bindingSha256(PhysicalStatusIdentity actual) {
        return ActionCodec.sha256(StrictJson.canonical(encode(java.util.Objects.requireNonNull(actual))));
    }
    public static ObjectNode encode(PhysicalStatusIdentity value) {
        var row=StrictJson.object();row.put("schema",SCHEMA).put("machine_id",value.machineId()).put("session_id",value.sessionId());
        row.set("game",value.game().toJson());row.put("connection_generation",value.connectionGeneration().toString());
        row.put("snapshot_id",value.snapshotId()).put("native_revision",value.nativeRevision().toString());
        row.set("source",ProposalLifecycleCodec.source(value.source()));row.set("native_evidence",value.nativeEvidence().toJson());
        row.set("hello_evidence",value.helloEvidence().toJson());row.set("heartbeat_evidence",value.heartbeatEvidence().toJson());
        row.set("source_qualification",ExactRef.optionalToJson(value.sourceQualification()));row.set("epoch_manifest",ExactRef.optionalToJson(value.epochManifest()));
        row.put("observed_at",value.observedAt().toString());return row;
    }
    public static PhysicalStatusIdentity decode(JsonNode value) {
        var row=StrictJson.object(value,Set.of("schema","machine_id","session_id","game","connection_generation","snapshot_id","native_revision",
                "source","native_evidence","hello_evidence","heartbeat_evidence","observed_at"),Set.of("source_qualification","epoch_manifest"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact physical Status identity schema required");
        BigInteger generation=uint64(row.get("connection_generation"));
        StrictJson.require(generation.signum()>0,"actual positive native connection generation required");
        var transport=new NativeObservationPort.TransportSession(StrictJson.text(row.get("machine_id")),GameGeneration.fromJson(row.get("game")),
                generation,StrictJson.text(row.get("session_id")));
        return new PhysicalStatusIdentity(transport,StrictJson.text(row.get("snapshot_id")),uint64(row.get("native_revision")),
                G2Wire.source(row.get("source")),ExactRef.fromJson(row.get("native_evidence")),ExactRef.fromJson(row.get("hello_evidence")),
                ExactRef.fromJson(row.get("heartbeat_evidence")),ExactRef.optionalFromJson(row.get("source_qualification")),ExactRef.optionalFromJson(row.get("epoch_manifest")),
                Instant.parse(StrictJson.text(row.get("observed_at"))));
    }
    private static BigInteger uint64(JsonNode value){return new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(value)).decimal());}
}

