package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable DATA only. The original batch journal must admit it against its current canonical head. */
public record CleanBatchRestart(ExactRef controller, ExactRef driverFacts, ExactRef fullDriver,
        TransportSession previousTransport, BigInteger publicRevision, BigInteger nativeRevision,
        long observationVersion, long dateRaw, org.xar.ck3.control.g2.common.G2Source source) {
    public static final String SCHEMA="xar.java-clean-batch-restart/v1";
    private static final Set<String> FIELDS=Set.of("schema","controller","driver_facts","full_driver",
            "previous_transport","public_revision","native_revision","observation_version","date_raw","source");
    public CleanBatchRestart {
        for(ExactRef ref:java.util.List.of(controller,driverFacts,fullDriver))StrictJson.require(ref.bytes()>0,"complete restart original required");
        Objects.requireNonNull(previousTransport);Objects.requireNonNull(publicRevision);Objects.requireNonNull(nativeRevision);
        StrictJson.require(publicRevision.signum()>=0&&publicRevision.compareTo(StrictJson.UINT64_MAX)<=0
                &&nativeRevision.signum()>=0&&nativeRevision.compareTo(StrictJson.UINT64_MAX)<=0,"exact restart revisions required");
        StrictJson.require(observationVersion==3||observationVersion==4,"supported actual complete observation contract required");
        StrictJson.safe(dateRaw,0);
        Objects.requireNonNull(source);StrictJson.require(source.machineId().equals(previousTransport.machineId()),"restart logical source belongs to another machine");
    }
    public byte[] encode(){
        ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);row.set("controller",controller.toJson());
        row.set("driver_facts",driverFacts.toJson());row.set("full_driver",fullDriver.toJson());
        ObjectNode transport=OrdinaryCycleTransitions.sessionToJson(new SessionPorts.SessionIdentity(previousTransport.machineId(),previousTransport.game(),previousTransport.sessionId()));
        transport.put("connection_generation",previousTransport.connectionGeneration().toString());row.set("previous_transport",transport);
        row.put("public_revision",publicRevision.toString());row.put("native_revision",nativeRevision.toString());
        row.put("observation_version",observationVersion);row.put("date_raw",dateRaw);
        ObjectNode logical=StrictJson.object();logical.put("machine_id",source.machineId());logical.put("observed_at_utc",source.observedAtUtc());
        logical.put("exact_build",source.exactBuild());logical.set("source_ref",source.sourceRef().toJson());row.set("source",logical);return ContinuityJson.canonical(row);
    }
    public static CleanBatchRestart decode(byte[] bytes){
        ObjectNode row=StrictJson.object(ContinuityJson.parseObject(bytes,ContinuityJson.DOCUMENT_MAX_BYTES),FIELDS,FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"restart manifest schema differs");
        Set<String> fields=Set.of("machine_id","game","session_id","connection_generation");
        ObjectNode transport=StrictJson.object(row.get("previous_transport"),fields,fields);
        var session=new TransportSession(StrictJson.text(transport.get("machine_id")),org.xar.ck3.control.contracts.GameGeneration.fromJson(transport.get("game")),
                decimal(transport,"connection_generation"),StrictJson.text(transport.get("session_id")));
        Set<String> sourceFields=Set.of("machine_id","observed_at_utc","exact_build","source_ref");ObjectNode logical=StrictJson.object(row.get("source"),sourceFields,sourceFields);
        var source=new org.xar.ck3.control.g2.common.G2Source(StrictJson.text(logical.get("machine_id")),StrictJson.text(logical.get("observed_at_utc")),
                StrictJson.text(logical.get("exact_build")),ExactRef.fromJson(logical.get("source_ref")));
        return new CleanBatchRestart(ExactRef.fromJson(row.get("controller")),ExactRef.fromJson(row.get("driver_facts")),ExactRef.fromJson(row.get("full_driver")),
                session,decimal(row,"public_revision"),decimal(row,"native_revision"),StrictJson.integer(row.get("observation_version"),3,4),StrictJson.integer(row.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER),source);
    }
    private static BigInteger decimal(ObjectNode row,String name){
        String value=StrictJson.text(row.get(name));StrictJson.require(value.matches("0|[1-9][0-9]{0,19}"),"canonical decimal restart integer required");
        BigInteger result=new BigInteger(value);StrictJson.require(result.compareTo(StrictJson.UINT64_MAX)<=0,"restart integer exceeds uint64");return result;
    }
}
