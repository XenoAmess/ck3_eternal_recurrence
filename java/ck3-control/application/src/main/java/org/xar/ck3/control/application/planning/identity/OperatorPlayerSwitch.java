package org.xar.ck3.control.application.planning.identity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original explicit operator switch. DATA validation never supplies native or writer authority. */
public final class OperatorPlayerSwitch {
    private OperatorPlayerSwitch() { }
    /** Exact original error codes. Unknown/malformed native replies remain BridgeUnavailable at the actual Root boundary. */
    public enum RejectionCode {
        TARGET_NOT_FOUND("target_not_found"),TARGET_DEAD("target_dead"),TARGET_CONTROLLED("target_controlled"),
        REQUIRES_PAUSED("requires_paused"),MAP_NOT_READY("map_not_ready"),POSTCONDITION_FAILED("postcondition_failed"),
        STATE_CHANGED("state_changed"),SUBMISSION_FAILED("submission_failed"),UNAVAILABLE("unavailable"),INVALID_REQUEST("invalid_request");
        private final String wire;RejectionCode(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    /** DATA decoding only. The caller must first verify its actual original canonical dispatch and custody. */
    public static java.util.Optional<RejectionCode> knownRejection(NativeActionPort.AckReceived actual) {
        Objects.requireNonNull(actual);if(actual.nativeOk())return java.util.Optional.empty();
        try {
            var frame=DriverJson.object(actual.originalFrame().bytes(),RawJson.MAXIMUM_BYTES);
            if(!new OpportunityJson.Text("command_result").equals(frame.get("type"))
                    ||!actual.requestId().equals(OpportunityJson.text(frame.get("request_id"),"request_id"))
                    ||!BigInteger.ONE.equals(OpportunityJson.integer(frame.get("protocol_version"),"protocol_version"))
                    ||OpportunityJson.bool(frame.get("ok"),"ok"))return java.util.Optional.empty();
            // Original Python appends typed-query failure JSON to the error, so it is not one of the ten exact codes.
            if(frame.get("typed_query_failure_v1") instanceof OpportunityJson.Obj)return java.util.Optional.empty();
            String error=OpportunityJson.text(frame.get("error"),"error");
            for(var code:RejectionCode.values())if(code.wire().equals(error))return java.util.Optional.of(code);
            return java.util.Optional.empty();
        } catch(IllegalArgumentException|ArithmeticException malformed) {return java.util.Optional.empty();}
    }
    public static final String CAPABILITY="game.command.set-played-character-v1-N";
    public static final String GAME_VERSION="1.19.0.6";
    public static final String EXECUTABLE_SHA256="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    public static final String SCHEMA="operator-player-switch-completion/v1";
    public static final int MAX_COMPLETION_BYTES=32768;
    public record Request(long characterId,BigInteger expectedRevision) {
        public Request { StrictJson.require(characterId>0&&characterId<=Integer.MAX_VALUE,"specific operator target must be positive signed int32");u64(expectedRevision); }
        public String step(){return "set-played-character-v1-"+characterId;}
    }
    public static Request decode(RawJson input) {
        ObjectNode row=StrictJson.object(StrictJson.parse(input.bytes()),Set.of("character_id","expected_revision"));
        return new Request(StrictJson.integer(row.get("character_id"),1,Integer.MAX_VALUE),publicU64(row.get("expected_revision")));
    }
    public enum NativeStatus {
        SWITCHED("switched"), ALREADY_PLAYED("already_played");
        private final String wire;NativeStatus(String wire){this.wire=wire;}public String wire(){return wire;}
        public static NativeStatus parse(String value){for(var status:values())if(status.wire.equals(value))return status;throw new IllegalArgumentException("unknown operator native status");}
    }
    public static void requireSupported(String actualVersion,String actualSha256,Set<String> actualCapabilities) {
        StrictJson.require(GAME_VERSION.equals(actualVersion)&&EXECUTABLE_SHA256.equals(Objects.requireNonNull(actualSha256).toUpperCase(java.util.Locale.ROOT))
                &&actualCapabilities.contains(CAPABILITY),"actual exact supported operator build and capability required");
    }
    /** Internal FullSnapshot DATA has integer u64 revisions; public request parsing remains a separate boundary. */
    public static void requireBefore(Request request,JsonNode actualInternalSnapshot) {
        Objects.requireNonNull(request);Objects.requireNonNull(actualInternalSnapshot);
        StrictJson.require(bool(actualInternalSnapshot,"paused")&&bool(actualInternalSnapshot,"map_ready"),"operator before must be paused and map ready");
        StrictJson.require(internalRevisionNode(actualInternalSnapshot.get("revision")).equals(request.expectedRevision()),"operator public revision changed before submission");
    }
    /** Actual internal semantic/Service values use integers only; no public decimal-string coercion is permitted. */
    public static BigInteger internalRevision(OpportunityJson.Value original) {
        BigInteger value=OpportunityJson.integer(original,"internal operator revision");u64(value);return value;
    }
    public static void requireAfter(Request request,JsonNode independentlyObserved) {
        StrictJson.require(bool(independentlyObserved,"paused")&&bool(independentlyObserved,"map_ready"),"independent operator after must be paused and map ready");
        JsonNode played=independentlyObserved.get("played_character");
        StrictJson.require(played!=null&&played.isObject()&&NativeCharacterId.fromJson(played.get("character_id")).value()==request.characterId()
                &&bool(played,"alive"),"independent operator target must actually be alive and played");
    }
    public static void requireRebound(Request request,String originalRun,JsonNode actualReboundSnapshot) {
        StrictJson.require(NativeCharacterId.fromJson(actualReboundSnapshot.get("episode_character_id")).value()==request.characterId()
                &&originalRun.equals(StrictJson.text(actualReboundSnapshot.get("episode_run_id")))
                &&actualReboundSnapshot.has("one_life_terminal")&&!bool(actualReboundSnapshot,"one_life_terminal")
                &&actualReboundSnapshot.has("one_life_terminal_reason")&&actualReboundSnapshot.get("one_life_terminal_reason").isNull(),
                "persisted operator identity must retain the run and clear the actual one-life result");
    }
    public record Replacement(DriverStateSnapshot.Complete driver,OpportunityJson.Obj auxiliary,boolean rebindPerformed) {
        public Replacement {Objects.requireNonNull(driver);Objects.requireNonNull(auxiliary);}
    }
    /** Pure replacement proposal. The sole source-owned canonical reducer/CAS must qualify and publish it. */
    public static Replacement replacement(DriverStateSnapshot.Complete before,OpportunityJson.Obj auxiliary,Request request) {
        boolean changed=!before.session().actorId().equals(BigInteger.valueOf(request.characterId()));
        if(!changed)return new Replacement(before,auxiliary,false);
        var session=new DriverStateSnapshot.Session(before.session().pipeName(),before.session().bridgePid(),BigInteger.valueOf(request.characterId()),before.session().episodeRunId());
        var driver=new DriverStateSnapshot.Complete(session,before.commandHistory(),before.lastCheckpoint(),before.rollbackWarFailure(),before.managedRestoreTransaction(),
                new DriverStateSnapshot.NullValue(),before.successionLifecycle(),before.campaignGoal(),before.rollbackWarFailures());
        var next=auxiliary.with("episode_binding_state",new OpportunityJson.Text("active_operator_rebind"))
                .with("restore_kind",new OpportunityJson.Text("operator_played_character_rebind"));
        // These are the actual shared Java owner slots. Public presentation names are produced elsewhere.
        next=next.with("arrange_marriage_choices",new OpportunityJson.Arr(List.of()))
                .with("arrange_marriage_query_sequence",OpportunityJson.Nil.INSTANCE)
                .with("active_combat_retreat_token",OpportunityJson.Nil.INSTANCE)
                .with("succession_reconciliation",OpportunityJson.Nil.INSTANCE);
        // Retain original optional legacy cache material only where that actual owner stored it.
        // New Java semantic/capability source tables are invalidated by the sole publisher in the same CAS.
        for(String key:List.of("declarable_wars"))if(next.members().containsKey(key))next=next.with(key,new OpportunityJson.Arr(List.of()));
        for(String key:List.of("declaration_query_sequence","declaration_query_binding","army_strength_query","combat_simulation_inputs_query",
                "combat_simulation_inputs_v3_query","battle_control_snapshot_v1_query","war_entry_assessments_query"))
            if(next.members().containsKey(key))next=next.with(key,OpportunityJson.Nil.INSTANCE);
        for(String key:List.of("war_termination_options","war_termination_terms","war_termination_exit_terms"))
            if(next.members().containsKey(key))next=next.with(key,new OpportunityJson.Obj(java.util.Map.of()));
        return new Replacement(driver,next,true);
    }
    public record Artifacts(ExactRef hello,ExactRef beforeNative,ExactRef ack,ExactRef afterNative,ExactRef beforeDriver,ExactRef afterDriver,
            ExactRef beforeAuxiliary,ExactRef afterAuxiliary,ExactRef canonicalCommit,ExactRef privateProof,ExactRef reboundNative) {
        public Artifacts {for(ExactRef ref:List.of(hello,beforeNative,ack,afterNative,beforeDriver,afterDriver,beforeAuxiliary,afterAuxiliary,canonicalCommit,privateProof,reboundNative))StrictJson.require(ref.bytes()>0,"actual nonempty operator originals required");}
        public List<ExactRef> references(){return List.of(hello,beforeNative,ack,afterNative,beforeDriver,afterDriver,beforeAuxiliary,afterAuxiliary,canonicalCommit,privateProof,reboundNative);}
    }
    public record Completion(Request request,String actionId,String bodySha256,String requestId,G2Source source,NativeObservationPort.TransportSession transport,
            String episodeRunId,long episodeEpoch,long priorActor,long beforeDriverVersion,long afterDriverVersion,NativeStatus status,
            BigInteger afterRevision,BigInteger nativeRevision,long dateRaw,Artifacts originals) {
        public Completion {
            Objects.requireNonNull(request);StrictJson.text(actionId);StrictJson.text(requestId);Objects.requireNonNull(source);Objects.requireNonNull(transport);StrictJson.text(episodeRunId);
            StrictJson.require(bodySha256!=null&&bodySha256.matches("[0-9a-f]{64}"),"actual operator command digest required");
            StrictJson.safe(episodeEpoch,0);StrictJson.safe(beforeDriverVersion,0);StrictJson.safe(afterDriverVersion,0);NativeCharacterId.of(priorActor);
            Objects.requireNonNull(status);u64(afterRevision);u64(nativeRevision);Objects.requireNonNull(originals);
            StrictJson.require(dateRaw>=Integer.MIN_VALUE&&dateRaw<=Integer.MAX_VALUE,"original operator Snapshot.date_raw is signed int32");
            StrictJson.require(source.machineId().equals(transport.machineId()),"operator source machine differs");
            StrictJson.require(afterDriverVersion==(priorActor==request.characterId()?beforeDriverVersion:Math.addExact(beforeDriverVersion,1)),"operator rebind changes Driver version once, preserving episode epoch");
            // Content-addressed equality says nothing about independent receive occurrences.
            // Actual transport/ACK chronology and role readers are mandatory in the private installed source verifier.
        }
        public boolean rebindPerformed(){return priorActor!=request.characterId();}
        public List<ExactRef> references(){return originals.references();}
        public void validate(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
            StrictJson.require(command.actionId().equals(actionId)&&ActionCodec.bodySha256(command).equals(bodySha256)
                    &&command.operation().value().equals(request.step())&&command.source().equals(source)&&command.sessionId().equals(transport.sessionId())
                    &&command.origin().game().equals(transport.game())&&command.origin().machineId().equals(transport.machineId()),"operator completion crossed original command/source/Game");
            StrictJson.require(attempt.requestId().equals(requestId)&&dispatch.requestId().equals(requestId)&&attempt.preparedRequest().step().equals(request.step()),"operator completion crossed original attempt/request");
            StrictJson.require(attempt.preparedRequest().requiredCapability().filter(CAPABILITY::equals).isPresent()
                    &&attempt.preparedRequest().additionalFields().objectFieldNames().isEmpty(),"original operator native request has only its exact target step and capability");
            StrictJson.require(dispatch instanceof NativeActionPort.AckReceived,"operator completion needs the original native ACK");
            var ack=(NativeActionPort.AckReceived)dispatch;StrictJson.require(ack.nativeOk(),"operator native ACK rejected");
            ObjectNode raw=object(StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()));
            StrictJson.require(status==NativeStatus.parse(StrictJson.text(raw.get("status"))),"operator status differs from original ACK");
        }
        public byte[] encode(){return StrictJson.canonical(toJson(),MAX_COMPLETION_BYTES);}
        private ObjectNode toJson() {
            ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);row.put("character_id",request.characterId());row.put("expected_revision",request.expectedRevision().toString());
            row.put("action_id",actionId);row.put("body_sha256",bodySha256);row.put("request_id",requestId);
            ObjectNode src=row.putObject("source");src.put("machine_id",source.machineId());src.put("observed_at_utc",source.observedAtUtc());src.put("exact_build",source.exactBuild());src.set("source_ref",source.sourceRef().toJson());
            ObjectNode tr=row.putObject("transport");tr.put("machine_id",transport.machineId());tr.set("game",transport.game().toJson());tr.put("connection_generation",transport.connectionGeneration().toString());tr.put("session_id",transport.sessionId());
            row.put("episode_run_id",episodeRunId);row.put("episode_epoch",episodeEpoch);row.put("prior_actor",priorActor);row.put("before_driver_version",beforeDriverVersion);row.put("after_driver_version",afterDriverVersion);
            row.put("status",status.wire());row.put("after_revision",afterRevision.toString());row.put("native_revision",nativeRevision.toString());row.put("date_raw",Long.toString(dateRaw));
            ObjectNode refs=row.putObject("originals");List<String> names=artifactNames();for(int i=0;i<names.size();i++)refs.set(names.get(i),originals.references().get(i).toJson());return row;
        }
    }
    public static Completion decodeCompletion(byte[] raw) {
        ObjectNode row=StrictJson.object(StrictJson.parse(raw,MAX_COMPLETION_BYTES),Set.of("schema","character_id","expected_revision","action_id","body_sha256","request_id","source","transport","episode_run_id","episode_epoch","prior_actor","before_driver_version","after_driver_version","status","after_revision","native_revision","date_raw","originals"));
        StrictJson.require(SCHEMA.equals(text(row,"schema")),"exact operator completion schema required");
        ObjectNode src=StrictJson.object(row.get("source"),Set.of("machine_id","observed_at_utc","exact_build","source_ref"));
        ObjectNode tr=StrictJson.object(row.get("transport"),Set.of("machine_id","game","connection_generation","session_id"));
        ObjectNode refs=StrictJson.object(row.get("originals"),Set.copyOf(artifactNames()));List<ExactRef> r=artifactNames().stream().map(key->ExactRef.fromJson(refs.get(key))).toList();
        return new Completion(new Request(StrictJson.integer(row.get("character_id"),1,Integer.MAX_VALUE),decimal(row.get("expected_revision"))),text(row,"action_id"),text(row,"body_sha256"),text(row,"request_id"),
                new G2Source(text(src,"machine_id"),text(src,"observed_at_utc"),text(src,"exact_build"),ExactRef.fromJson(src.get("source_ref"))),
                new NativeObservationPort.TransportSession(text(tr,"machine_id"),GameGeneration.fromJson(tr.get("game")),decimal(tr.get("connection_generation")),text(tr,"session_id")),
                text(row,"episode_run_id"),number(row,"episode_epoch"),NativeCharacterId.fromJson(row.get("prior_actor")).value(),number(row,"before_driver_version"),number(row,"after_driver_version"),NativeStatus.parse(text(row,"status")),
                decimal(row.get("after_revision")),decimal(row.get("native_revision")),signedDecimal(row.get("date_raw")),new Artifacts(r.get(0),r.get(1),r.get(2),r.get(3),r.get(4),r.get(5),r.get(6),r.get(7),r.get(8),r.get(9),r.get(10)));
    }
    private static List<String> artifactNames(){return List.of("hello","before_native","ack","after_native","before_driver","after_driver","before_auxiliary","after_auxiliary","canonical_commit","private_proof","rebound_native");}
    public static RawJson publicResult(Completion verified,Long sourceCharacterId) {
        ObjectNode row=StrictJson.object();row.put("schema_version",1);row.put("step",verified.request().step());row.put("accepted",true);row.put("status",verified.status().wire());
        if(sourceCharacterId==null)row.putNull("from_character_id");else row.put("from_character_id",NativeCharacterId.of(sourceCharacterId).value());
        row.put("to_character_id",verified.request().characterId());row.put("before_revision",verified.request().expectedRevision().toString());row.put("after_revision",verified.afterRevision().toString());row.put("native_revision",verified.nativeRevision().toString());row.put("date_raw",verified.dateRaw());
        row.put("paused",true);row.put("map_ready",true);row.put("postcondition_verified",true);row.put("prior_episode_character_id",verified.priorActor());row.put("episode_character_id",verified.request().characterId());row.put("episode_run_id",verified.episodeRunId());row.put("episode_rebind_performed",verified.rebindPerformed());row.put("one_life_terminal_cleared",true);row.put("backend_id","native-headless");return new RawJson(StrictJson.canonical(row));
    }
    private static BigInteger publicU64(JsonNode node){if(node!=null&&node.isIntegralNumber())return StrictJson.integer(node,BigInteger.ZERO,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER));return decimal(node);}
    private static BigInteger internalRevisionNode(JsonNode original){
        StrictJson.require(original!=null&&original.isIntegralNumber(),"internal operator revision must be an integer JSON value");
        return internalRevision(new OpportunityJson.IntegerValue(original.bigIntegerValue()));
    }
    private static BigInteger decimal(JsonNode node){String value=StrictJson.text(node);StrictJson.require(value.matches("0|[1-9][0-9]*"),"canonical uint64 decimal required");BigInteger parsed=new BigInteger(value);u64(parsed);return parsed;}
    private static long signedDecimal(JsonNode node){String value=StrictJson.text(node);StrictJson.require(value.matches("0|-?[1-9][0-9]*"),"canonical signed64 decimal required");return new BigInteger(value).longValueExact();}
    private static void u64(BigInteger value){StrictJson.require(value!=null&&value.signum()>=0&&value.compareTo(StrictJson.UINT64_MAX)<=0,"uint64 revision required");}
    private static boolean bool(JsonNode row,String key){JsonNode value=row.get(key);StrictJson.require(value!=null&&value.isBoolean(),"actual boolean "+key+" required");return value.booleanValue();}
    private static String text(ObjectNode row,String key){return StrictJson.text(row.get(key));}
    private static long number(ObjectNode row,String key){return StrictJson.integer(row.get(key),0,StrictJson.MAX_SAFE_INTEGER);}
    private static ObjectNode object(JsonNode node){StrictJson.require(node instanceof ObjectNode,"actual native object required");return (ObjectNode)node;}
}
