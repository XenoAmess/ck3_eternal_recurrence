package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** The original fixed-key treatment observation. Duration remains explicitly unverified. */
public final class EpidemicTreatmentPresenceQueries {
    public static final String STEP="query-player-epidemic-treatment-presence-v1";
    public static final String CONTRACT_ID="family/epidemic-treatment-presence/v1";
    public static final String PERMISSION="allow_private_epidemic_treatment_presence_query";
    public static final String MODIFIER="ce1_unorthodox_epidemic_treatment";
    private static final OperationKey OPERATION=new OperationKey(STEP);
    private EpidemicTreatmentPresenceQueries() {}
    @FunctionalInterface public interface Admission {void verify(PlanningReadRequest actual);}
    public enum Status {AVAILABLE,UNAVAILABLE}
    public record Presence(Status status,Optional<Boolean> present,Optional<String> unavailableReason) {
        public Presence {
            Objects.requireNonNull(status);Objects.requireNonNull(present);Objects.requireNonNull(unavailableReason);
            StrictJson.require(status==Status.AVAILABLE?present.isPresent()&&unavailableReason.isEmpty():
                    present.isEmpty()&&unavailableReason.isPresent(),"treatment availability and observed value differ");
            unavailableReason.ifPresent(StrictJson::text);
        }
    }
    public record Observation(BigInteger querySequence,BigInteger observationRevision,Presence presence,RawJson originalResult) {
        public Observation {positive(querySequence);positive(observationRevision);Objects.requireNonNull(presence);Objects.requireNonNull(originalResult);}
    }
    public static ReadContract<Obj> contract(ExactRef actualNativeSource,Admission admission) {
        Objects.requireNonNull(actualNativeSource);Objects.requireNonNull(admission);
        return new ReadContract<>(CONTRACT_ID,OPERATION,Optional.empty(),PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,actualNativeSource,
                (request,id)->{arguments(request);admission.verify(request);
                    return new NativeRequest(STEP,Optional.empty(),new RawJson(StrictJson.canonical(StrictJson.object())));},
                EpidemicTreatmentPresenceQueries::project,EpidemicTreatmentPresenceQueries::project);
    }
    public static Obj arguments(BigInteger expectedRevision) {
        positive(expectedRevision);return object(StrictJson.object().put("expected_revision",expectedRevision));
    }
    private static void arguments(PlanningReadRequest request) {
        StrictJson.require(request.operation().equals(OPERATION),"wrong treatment operation");
        ObjectNode fields=StrictJson.object(OpportunityJson.toNode(request.arguments()),Set.of("expected_revision"));
        StrictJson.require(number(fields.get("expected_revision")).equals(request.before().frame().revision()),"treatment public expected revision is stale");
        StrictJson.require(request.source().exactBuild().equals(FamilyObligations.Build.CURRENT4.exactBuild()),"current exact .4 treatment source required");
    }
    public static Observation decode(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);arguments(receipt.request());
        StrictJson.require(receipt.contractId().equals(CONTRACT_ID)&&receipt.original().nativeOk()
                &&receipt.requestId().equals(receipt.original().requestId()),"original installed successful treatment read required");
        for(var guard:List.of(receipt.before(),receipt.after()))StrictJson.require(
                guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
                &&guard.binding().operation().equals(OPERATION)&&guard.binding().source().equals(receipt.request().source())
                &&guard.binding().sessionId().equals(receipt.request().sessionId())&&guard.binding().observed().equals(receipt.request().before()),
                "treatment original crossed its exact paused living player frame");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                &&receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()),
                "treatment original connection or binding changed");
        RawJson raw=receipt.original().originalResultToken().orElseThrow();
        ObjectNode packet=StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes(),1048576),Set.of("type","protocol_version","request_id","ok","result"));
        StrictJson.require("command_result".equals(StrictJson.text(packet.get("type")))
                &&StrictJson.integer(packet.get("protocol_version"),1,1)==1&&bool(packet.get("ok"))
                &&receipt.requestId().equals(StrictJson.text(packet.get("request_id")))
                &&packet.get("result").equals(StrictJson.parse(raw.bytes(),1048576)),"treatment original packet/result custody differs");
        var frame=receipt.request().before().frame().identity();
        ObjectNode envelope=StrictJson.object(StrictJson.parse(raw.bytes(),1048576),Set.of("step","accepted","status","query_sequence","observation_revision",
                "snapshot_revision","player_epidemic_treatment_presence","private_build","read_only","advertised","backend_id"));
        StrictJson.require(STEP.equals(StrictJson.text(envelope.get("step")))&&bool(envelope.get("accepted"))
                &&bool(envelope.get("private_build"))&&bool(envelope.get("read_only"))&&!bool(envelope.get("advertised"))
                &&"native-headless".equals(StrictJson.text(envelope.get("backend_id")))
                &&number(envelope.get("snapshot_revision")).equals(frame.nativeRevision()),"treatment native envelope differs");
        BigInteger sequence=number(envelope.get("query_sequence")),observed=number(envelope.get("observation_revision"));
        ObjectNode value=StrictJson.object(envelope.get("player_epidemic_treatment_presence"),Set.of("schema","schema_version","modifier_key",
                "snapshot_revision","date_raw","played_character_id","status","present","remaining_days","unavailable_reason"));
        StrictJson.require("player-epidemic-treatment-presence-v1".equals(StrictJson.text(value.get("schema")))
                &&StrictJson.integer(value.get("schema_version"),1,1)==1&&MODIFIER.equals(StrictJson.text(value.get("modifier_key")))
                &&number(value.get("snapshot_revision")).equals(frame.nativeRevision())
                &&BigInteger.valueOf(StrictJson.integer(value.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)).equals(frame.dateRaw())
                &&boundedPlayer(value.get("played_character_id")).equals(frame.player())
                &&value.get("status").equals(envelope.get("status")),"treatment native player/key/frame differs");
        ObjectNode duration=StrictJson.object(value.get("remaining_days"),Set.of("status","value","unavailable_reason"));
        StrictJson.require("unavailable".equals(StrictJson.text(duration.get("status")))&&duration.get("value").isNull()
                &&"duration_abi_not_verified".equals(StrictJson.text(duration.get("unavailable_reason"))),"unverified duration contract changed");
        String status=StrictJson.text(value.get("status"));Presence presence;
        if(status.equals("available")) {
            StrictJson.require(value.get("unavailable_reason").isNull(),"available treatment has an unavailable reason");
            presence=new Presence(Status.AVAILABLE,Optional.of(bool(value.get("present"))),Optional.empty());
        } else {
            StrictJson.require(status.equals("unavailable")&&value.get("present").isNull(),"treatment status/presence is malformed");
            presence=new Presence(Status.UNAVAILABLE,Optional.empty(),Optional.of(StrictJson.text(value.get("unavailable_reason"))));
        }
        return new Observation(sequence,observed,presence,raw);
    }
    public static Obj project(PlanningReadReceipt receipt) {
        Observation actual=decode(receipt);ObjectNode value=(ObjectNode)StrictJson.parse(actual.originalResult().bytes(),1048576);
        var before=receipt.request().before().frame();
        value.put("queried_snapshot_id",before.snapshotId()).put("queried_revision",before.revision())
                .put("queried_native_revision",before.identity().nativeRevision());
        return object(value);
    }
    private static boolean bool(JsonNode raw) {StrictJson.require(raw!=null&&raw.isBoolean(),"exact treatment JSON boolean required");return raw.booleanValue();}
    private static BigInteger number(JsonNode raw) {StrictJson.require(raw!=null&&raw.isIntegralNumber(),"exact treatment uint64 integer required");BigInteger n=raw.bigIntegerValue();positive(n);return n;}
    private static BigInteger boundedPlayer(JsonNode raw) {BigInteger n=number(raw);StrictJson.require(n.compareTo(BigInteger.valueOf(0xffff_ffffL))<=0,"treatment full uint32 player required");return n;}
    private static void positive(BigInteger n) {StrictJson.require(n!=null&&n.signum()>0&&n.compareTo(StrictJson.UINT64_MAX)<=0,"positive uint64 treatment revision required");}
    private static Obj object(JsonNode value) {return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"actual treatment observation");}
}

