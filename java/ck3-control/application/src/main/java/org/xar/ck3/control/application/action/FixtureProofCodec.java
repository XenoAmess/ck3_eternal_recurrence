package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Sole strict persisted fixture proof codec. Decoding DATA never grants a startup scope or adoption. */
public final class FixtureProofCodec {
    private FixtureProofCodec(){ }
    public static ObjectNode start(FixtureStartObservation value,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object().put("schema",FixtureStartObservation.SCHEMA);
        row.set("fixture",value.fixture().encode());row.set("before",CommandOriginCodec.frontend(value.before()));
        row.set("source",ProposalLifecycleCodec.source(value.source()));row.set("gameplay_session",OrdinaryCycleTransitions.sessionToJson(value.gameplaySession()));
        row.put("connection_generation",decimal(value.connectionGeneration()));row.set("first_map",OrdinaryCycleTransitions.semanticToJson(value.firstMap()));
        row.put("full_binding_sha256",value.fullBindingSha256());row.set("original_hello",value.originalHello().toJson());
        row.set("first_heartbeat",value.firstHeartbeat().toJson());row.set("last_heartbeat",value.lastHeartbeat().toJson());
        row.set("source_qualification",ExactRef.optionalToJson(value.sourceQualification()));row.set("independent_read",archive.referenceOf(value.independentRead()).toJson());
        row.set("snapshot_received",StrictJson.object().put("order",decimal(value.snapshotReceived().order())).put("observed_at",value.snapshotReceived().observedAt().toString()));return row;
    }
    public static FixtureStartObservation start(JsonNode input,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object(input,Set.of("schema","fixture","before","source","gameplay_session","connection_generation","first_map",
                "full_binding_sha256","original_hello","first_heartbeat","last_heartbeat","independent_read","snapshot_received"),Set.of("source_qualification"));
        StrictJson.require(FixtureStartObservation.SCHEMA.equals(text(row,"schema")),"exact first-map proof schema required");
        var dispatch=archive.load(ExactRef.fromJson(row.get("independent_read")));
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived,"fixture independent READ requires its actual ACK original");
        var received=StrictJson.object(row.get("snapshot_received"),Set.of("order","observed_at"));
        return new FixtureStartObservation(FixturePlan.decode(row.get("fixture")),CommandOriginCodec.frontend(row.get("before")),G2Wire.source(row.get("source")),
                OrdinaryCycleTransitions.sessionFromJson(row.get("gameplay_session")),integer(row,"connection_generation"),OrdinaryCycleTransitions.semanticFromJson(row.get("first_map")),
                text(row,"full_binding_sha256"),ExactRef.fromJson(row.get("original_hello")),ExactRef.fromJson(row.get("first_heartbeat")),ExactRef.fromJson(row.get("last_heartbeat")),
                ExactRef.optionalFromJson(row.get("source_qualification")),(NativeActionPort.AckReceived)dispatch,new NativeRequestChronology.Event(integer(received,"order"),Instant.parse(text(received,"observed_at"))));
    }
    public static ObjectNode businessEvidence(FixtureBusinessEvidence value,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object().put("schema",FixtureBusinessEvidence.SCHEMA).put("parent_action_id",value.parentActionId()).put("parent_body_sha256",value.parentBodySha256());
        row.set("fixture",value.fixture().encode());row.set("original_start",archive.receiptReferenceOf(value.originalStart()).toJson());
        row.set("final_semantic",OrdinaryCycleTransitions.semanticToJson(value.finalSemantic()));row.set("campaign_root_read",archive.readReferenceOf(value.campaignRootRead()).toJson());
        row.set("qualification",value.qualification().toJson());var refs=row.putArray("supporting_evidence");value.supportingEvidence().forEach(ref->refs.add(ref.toJson()));return row;
    }
    public static FixtureBusinessEvidence businessEvidence(JsonNode input,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object(input,Set.of("schema","parent_action_id","parent_body_sha256","fixture","original_start","final_semantic","campaign_root_read","qualification","supporting_evidence"));
        StrictJson.require(FixtureBusinessEvidence.SCHEMA.equals(text(row,"schema")),"exact fixture business evidence schema required");
        return new FixtureBusinessEvidence(text(row,"parent_action_id"),text(row,"parent_body_sha256"),FixturePlan.decode(row.get("fixture")),archive.loadReceipt(ExactRef.fromJson(row.get("original_start"))),
                OrdinaryCycleTransitions.semanticFromJson(row.get("final_semantic")),archive.loadRead(ExactRef.fromJson(row.get("campaign_root_read"))),ExactRef.fromJson(row.get("qualification")),references(row.get("supporting_evidence")));
    }
    public static ObjectNode business(FixtureBusinessObservation value,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object().put("schema",FixtureBusinessObservation.SCHEMA);row.set("evidence",businessEvidence(value.evidence(),archive));
        row.set("entry_prepared",value.entryPrepared().toJson());row.set("entry_receipt",value.entryReceipt().toJson());return row;
    }
    public static FixtureBusinessObservation business(JsonNode input,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object(input,Set.of("schema","evidence","entry_prepared","entry_receipt"));
        StrictJson.require(FixtureBusinessObservation.SCHEMA.equals(text(row,"schema")),"exact fixture business terminal schema required");
        return new FixtureBusinessObservation(businessEvidence(row.get("evidence"),archive),ExactRef.fromJson(row.get("entry_prepared")),ExactRef.fromJson(row.get("entry_receipt")));
    }
    private static List<ExactRef> references(JsonNode input){
        StrictJson.require(input!=null&&input.isArray()&&input.size()<=64,"finite explicit fixture support array required");
        var refs=new ArrayList<ExactRef>();input.forEach(value->refs.add(ExactRef.fromJson(value)));return List.copyOf(refs);
    }
    private static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    private static String decimal(BigInteger value){return new CrossJsDecimalUInt64(value.toString()).decimal();}
    private static BigInteger integer(ObjectNode row,String field){return new BigInteger(new CrossJsDecimalUInt64(text(row,field)).decimal());}
}
