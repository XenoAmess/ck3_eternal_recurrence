package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.time.Instant;
import java.util.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.service.mcp.LifecyclePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Three original tools share the sole optional/canonical revision codec. Public DATA grants no private pending capability. */
public final class RootDriverLifecyclePublicCodec {
    private RootDriverLifecyclePublicCodec(){ }
    public record Query(BigInteger expectedRevision){public Query{new PythonOnlyUInt64(expectedRevision);}}
    public record Resume(LifecyclePublicCodec.Request original){public Resume{Objects.requireNonNull(original);}}
    public record Close(BigInteger expectedRevision,BigInteger actor,String episodeRunId){public Close{new PythonOnlyUInt64(expectedRevision);require(actor.signum()>0&&actor.bitLength()<32,"private Close requires original positive signed32 played actor");StrictJson.text(episodeRunId);}}
    public static Query query(PublicBindings.Arguments input){var value=LifecyclePublicCodec.decodeRequest(input);require(value.expectedRevision() instanceof LifecyclePublicCodec.ExactRevision,"timeline requires expected_revision");return new Query(value.expected().orElseThrow());}
    public static Resume resume(PublicBindings.Arguments input){return new Resume(LifecyclePublicCodec.decodeRequest(input));}
    public static Close close(PublicBindings.Arguments input){
        require(input instanceof PublicBindings.Value,"Close requires its exact three arguments");var row=StrictJson.object(PublicDataJson.object(((PublicBindings.Value)input).original()),Set.of("expected_revision","expected_played_character_id","expected_episode_run_id"));
        var revision=StrictJson.object();revision.set("expected_revision",row.get("expected_revision"));var expected=query(new PublicBindings.Value(PublicDataJson.encode(revision)));
        return new Close(expected.expectedRevision(),StrictJson.integer(row.get("expected_played_character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)),StrictJson.text(row.get("expected_episode_run_id")));
    }
    public static PublicBindings.Arguments encode(Query input){return LifecyclePublicCodec.encodeRequest(new LifecyclePublicCodec.Request(LifecyclePublicCodec.ArgumentPresence.OBJECT,new LifecyclePublicCodec.ExactRevision(input.expectedRevision())));}
    public static PublicBindings.Arguments encode(Resume input){return LifecyclePublicCodec.encodeRequest(input.original());}
    public static PublicBindings.Arguments encode(Close input){var row=PublicDataJson.object(((PublicBindings.Value)encode(new Query(input.expectedRevision()))).original());row.put("expected_played_character_id",input.actor());row.put("expected_episode_run_id",input.episodeRunId());return new PublicBindings.Value(PublicDataJson.encode(row));}
    /** Exact original material DATA only. The actual Runtime retains its archive/source qualification. */
    public sealed interface CloseMaterial permits SubmittedClose,ReclaimClose { }
    public enum ClosePhase { SUBMITTED_UNCONFIRMED,POST_ADVANCE_UNCONFIRMED,MATERIALLY_VERIFIED }
    public record PostQueryAttempt(int attempt,Optional<RawJson> query,Optional<String> error,Optional<RawJson> binding) {
        public PostQueryAttempt {require(attempt>=1&&attempt<=8,"original bounded post-query ordinal required");Objects.requireNonNull(query);Objects.requireNonNull(error);Objects.requireNonNull(binding);query.ifPresent(RootDriverLifecyclePublicCodec::queryObject);error.ifPresent(StrictJson::text);binding.ifPresent(RootDriverLifecyclePublicCodec::bindingObject);}
    }
    /** Exact flat runtime post-query binding DATA; this is not a full Driver snapshot. */
    public record EndingBinding(RawJson original) {
        public EndingBinding {bindingObject(original);}
    }
    public record SubmittedClose(ClosePhase phase,RawJson submissionAck,RawJson initialQuery,List<PostQueryAttempt> postAttempts,
            int startingDateRaw,RawJson endingSnapshot,Optional<RawJson> lifeResult,Optional<String> failure) implements CloseMaterial {
        /** Explicitly adapts the runtime binding role to the original nested snapshot DATA contract. */
        public SubmittedClose(ClosePhase phase,RawJson submissionAck,RawJson initialQuery,List<PostQueryAttempt> postAttempts,
                int startingDateRaw,EndingBinding ending,Optional<RawJson> lifeResult,Optional<String> failure) {
            this(phase,submissionAck,initialQuery,postAttempts,startingDateRaw,RootDriverLifecyclePublicCodec.endingSnapshot(ending),lifeResult,failure);
        }
        public SubmittedClose {
            Objects.requireNonNull(phase);ackObject(submissionAck);queryObject(initialQuery);postAttempts=List.copyOf(postAttempts);require(postAttempts.size()<=8,"original bounded post-query history required");
            for(int index=0;index<postAttempts.size();index++)require(postAttempts.get(index).attempt()==index+1,"actual post-query ordinals must retain their original order");
            require(startingDateRaw>0&&signed(object(submissionAck),"date_raw")==startingDateRaw,"original ACK/start date differ");
            var snapshot=object(endingSnapshot);require(!snapshot.members().containsKey("played_character_id")&&!snapshot.members().containsKey("played_character_alive"),"SubmittedClose requires nested ending snapshot; use explicit EndingBinding for runtime binding DATA");nullableCounter(member(snapshot,"revision"));nullableCounter(member(snapshot,"native_revision"));nullableSigned(member(snapshot,"date_raw"));
            // Validate the nested snapshot's projected roles with the same exact scalar contract as flat bindings.
            bindingObject(json(postBinding(snapshot)));
            Objects.requireNonNull(lifeResult);lifeResult.ifPresent(RootDriverLifecyclePublicCodec::object);Objects.requireNonNull(failure);failure.ifPresent(StrictJson::text);
            require(phase==ClosePhase.SUBMITTED_UNCONFIRMED?lifeResult.isEmpty():lifeResult.isPresent(),"original phase changed its actual Life result presence");
            require(phase==ClosePhase.MATERIALLY_VERIFIED?failure.isEmpty():failure.isPresent(),"original phase changed its actual failure presence");
            if(phase==ClosePhase.MATERIALLY_VERIFIED)require(!postAttempts.isEmpty()&&postAttempts.getLast().query().isPresent()&&signed(snapshot,"date_raw")>startingDateRaw,"success needs actual post-query and independent later ending date");
        }
    }
    /** Outer RED/reclaim remains original UNKNOWN even if it retains a validated inner ACK. */
    public record ReclaimClose(RawJson originalRequest,RawJson originalCommandResult,RawJson preSubmissionSnapshot,
            RawJson initialQuery,Optional<RawJson> retainedSubmissionAck,Optional<String> retainedAckValidationError) implements CloseMaterial {
        public ReclaimClose {
            var request=object(originalRequest);var frame=object(originalCommandResult);object(preSubmissionSnapshot);queryObject(initialQuery);
            require(new Text("execute_step").equals(request.get("type"))&&new Text(NativeTimelineBlocker12004.CLOSE_STEP).equals(request.get("step"))
                    &&new Text("command_result").equals(frame.get("type"))&&new Bool(false).equals(frame.get("ok"))&&Objects.equals(request.get("request_id"),frame.get("request_id")),"actual original Close request and RED result required");
            require(new IntegerValue(BigInteger.ONE).equals(request.get("protocol_version"))&&new IntegerValue(BigInteger.ONE).equals(frame.get("protocol_version")),"original protocol1 required");
            if(frame.members().containsKey("death_succession_close_failure_v1"))OpportunityJson.object(member(frame,"death_succession_close_failure_v1"),"actual retained reclaim diagnostic");
            Objects.requireNonNull(retainedSubmissionAck);Objects.requireNonNull(retainedAckValidationError);
            require(!(retainedSubmissionAck.isPresent()&&retainedAckValidationError.isPresent()),"inner ACK and validation failure cannot both be present");
            require(frame.members().containsKey("death_succession_close_failure_v1")?(retainedSubmissionAck.isPresent()||retainedAckValidationError.isPresent()):retainedSubmissionAck.isEmpty()&&retainedAckValidationError.isEmpty(),"original reclaim diagnostic presence differs from retained validation");
            retainedSubmissionAck.ifPresent(ack->{ackObject(ack);var detail=OpportunityJson.object(frame.get("death_succession_close_failure_v1"),"reclaim diagnostic");
                var inner=DriverJson.object(text(detail.get("submitted_ack_frame_exact_json"),"retained ACK JSON").getBytes(java.nio.charset.StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);
                require(new Bool(true).equals(inner.get("ok"))&&Objects.equals(inner.get("request_id"),frame.get("request_id"))&&object(ack).equals(inner.get("result")),"retained ACK differs from actual native exact JSON");});
            retainedAckValidationError.ifPresent(StrictJson::text);
        }
    }
    public static View withCloseMaterial(View original,CloseMaterial material){
        Objects.requireNonNull(original);Objects.requireNonNull(material);require(original.close().isPresent(),"original public Close has no retained canonical action");
        if(material instanceof SubmittedClose submitted&&submitted.phase()==ClosePhase.MATERIALLY_VERIFIED)require(original.close().orElseThrow().materialClearance()&&original.close().orElseThrow().verifiedDateAdvance().isPresent()
                &&(original.close().orElseThrow().outcome()!=ActionReceipt.Outcome.UNRESOLVED||original.close().orElseThrow().reconciliation().isPresent()),"original complete report requires actual clearance and independent date proof without releasing original UNKNOWN");
        return new View(original.status(),original.pending(),original.playerDecisionPending(),original.actionSubmitted(),original.snapshot(),original.transition(),original.close(),original.machineId(),original.observedAtUtc(),original.eventDiagnosis(),Optional.of(material));
    }
    /** Original Python projection. It issues no query, action, qualification or new success evidence. */
    public static RawJson projectClose(CloseMaterial material){
        Objects.requireNonNull(material);if(material instanceof SubmittedClose submitted)return json(projectSubmitted(submitted));
        var reclaim=(ReclaimClose)material;var frame=object(reclaim.originalCommandResult());var request=object(reclaim.originalRequest());
        if(!frame.members().containsKey("death_succession_close_failure_v1"))throw publicFailure(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"death-succession Close returned RED; action state is unknown: "+(member(frame,"error") instanceof Text t&&!t.value().isEmpty()?t.value():"unknown"));
        var error=member(frame,"error");String failure=error instanceof Text t&&!t.value().isEmpty()?t.value():"native Close reclaim failed";
        Obj result;
        if(reclaim.retainedSubmissionAck().isPresent())result=projectSubmitted(new SubmittedClose(ClosePhase.SUBMITTED_UNCONFIRMED,reclaim.retainedSubmissionAck().orElseThrow(),reclaim.initialQuery(),List.of(),signed(request,"expected_date_raw"),reclaim.preSubmissionSnapshot(),Optional.empty(),Optional.of(failure)));
        else result=new Obj(Map.ofEntries(Map.entry("step",new Text(NativeTimelineBlocker12004.CLOSE_STEP)),Map.entry("accepted",Nil.INSTANCE),Map.entry("status",new Text("submission_unknown")),Map.entry("material_result_verified",new Bool(false)),Map.entry("initial_query",object(reclaim.initialQuery())),Map.entry("submission_ack",Nil.INSTANCE),Map.entry("post_query_attempts",new Arr(List.of())),Map.entry("postcondition_queries",new Arr(List.of())),Map.entry("postcondition_query",Nil.INSTANCE),Map.entry("life_advance_result",Nil.INSTANCE),Map.entry("post_failure",new Text(failure)),Map.entry("retained_ack_validation_error",new Text(reclaim.retainedAckValidationError().orElseThrow()))));
        return json(result.with("ok",new Bool(false)).with("business_material_verified",new Bool(false)).with("native_request_id",request.get("request_id"))
                .with("native_request_frame",request).with("native_command_result_frame",frame).with("actual_pre_submission_snapshot",object(reclaim.preSubmissionSnapshot()))
                .with("native_reclaim_failure",frame.get("death_succession_close_failure_v1")).with("wire_bytes_preserved",new Bool(false)).with("ending_frame_source",new Text("pre_submission_last_known_only")));
    }
    private static Obj projectSubmitted(SubmittedClose value){
        var queries=value.postAttempts().stream().flatMap(a->a.query().stream()).map(RootDriverLifecyclePublicCodec::object).toList();
        Value last=queries.isEmpty()?Nil.INSTANCE:queries.getLast();var snapshot=object(value.endingSnapshot());
        Obj result=object(value.submissionAck()).with("status",new Text(switch(value.phase()){case SUBMITTED_UNCONFIRMED->"submitted_unconfirmed";case POST_ADVANCE_UNCONFIRMED->"post_advance_unconfirmed";case MATERIALLY_VERIFIED->"materially_verified";}))
                .with("material_result_verified",new Bool(value.phase()==ClosePhase.MATERIALLY_VERIFIED)).with("submission_ack",object(value.submissionAck())).with("initial_query",object(value.initialQuery()))
                .with("postcondition_queries",new Arr(new ArrayList<Value>(queries))).with("postcondition_query",last)
                .with("post_observation_revision",last instanceof Obj row?member(row,"observation_revision"):Nil.INSTANCE)
                .with("post_query_attempts",new Arr(value.postAttempts().stream().<Value>map(a->new Obj(Map.of("attempt",number(a.attempt()),"query",a.query().<Value>map(RootDriverLifecyclePublicCodec::object).orElse(Nil.INSTANCE),"error",a.error().<Value>map(Text::new).orElse(Nil.INSTANCE),"binding",a.binding().<Value>map(RootDriverLifecyclePublicCodec::object).orElse(Nil.INSTANCE)))).toList()))
                .with("post_failure",value.failure().<Value>map(Text::new).orElse(Nil.INSTANCE)).with("life_advance_result",value.lifeResult().<Value>map(RootDriverLifecyclePublicCodec::object).orElse(Nil.INSTANCE))
                .with("starting_date_raw",number(value.startingDateRaw())).with("ending_date_raw",member(snapshot,"date_raw")).with("ending_revision",member(snapshot,"revision")).with("ending_native_revision",member(snapshot,"native_revision"));
        return value.phase()==ClosePhase.POST_ADVANCE_UNCONFIRMED?result.with("post_advance_snapshot",postBinding(snapshot)):result;
    }
    private static Obj postBinding(Obj snapshot){var played=member(snapshot,"played_character");var out=new LinkedHashMap<String,Value>();for(String key:List.of("snapshot_id","revision","native_revision","date_raw","paused","map_ready","episode_character_id","episode_run_id"))out.put(key,member(snapshot,key));out.put("played_character_id",played instanceof Obj row?member(row,"character_id"):Nil.INSTANCE);out.put("played_character_alive",played instanceof Obj row?member(row,"alive"):Nil.INSTANCE);return new Obj(out);}
    private static RawJson endingSnapshot(EndingBinding binding){
        var values=new LinkedHashMap<>(object(Objects.requireNonNull(binding).original()).members());
        Value actor=values.remove("played_character_id"),alive=values.remove("played_character_alive");
        values.put("played_character",new Obj(Map.of("character_id",actor,"alive",alive)));
        return json(new Obj(values));
    }
    private static Obj object(RawJson raw){Objects.requireNonNull(raw);return DriverJson.object(raw.bytes(),RawJson.MAXIMUM_BYTES);}
    private static Value member(Obj row,String key){return row.members().getOrDefault(key,Nil.INSTANCE);}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static RawJson json(Obj value){return new RawJson(DriverJson.encode(value));}
    private static int signed(Obj row,String key){return integer(member(row,key),key).intValueExact();}
    private static void nullableCounter(Value value){if(value!=Nil.INSTANCE)new PythonOnlyUInt64(integer(value,"original uint64"));}
    private static void nullableSigned(Value value){if(value!=Nil.INSTANCE)integer(value,"original signed32").intValueExact();}
    private static void ackObject(RawJson raw){
        var row=object(raw);require(row.members().keySet().equals(Set.of("step","accepted","status","snapshot_revision","date_raw","played_character_id","action_observation_revision","identity_verified","can_continue_verified","paused_by_succession_verified","has_open_succession_verified","controller_vtable_verified","controller_open_verified","close_invocations","material_result_verified","private_build","advertised","backend_id")),"original Close ACK exact fields required");
        require(new Text(NativeTimelineBlocker12004.CLOSE_STEP).equals(row.get("step"))&&new Text("submitted").equals(row.get("status"))&&new Text("native-headless").equals(row.get("backend_id")),"original Close ACK identity required");
        for(String key:List.of("accepted","identity_verified","can_continue_verified","paused_by_succession_verified","has_open_succession_verified","controller_vtable_verified","controller_open_verified","private_build"))require(new Bool(true).equals(row.get(key)),"original true ACK flag required: "+key);
        for(String key:List.of("material_result_verified","advertised"))require(new Bool(false).equals(row.get(key)),"original false ACK flag required: "+key);
        for(String key:List.of("snapshot_revision","action_observation_revision")){var value=integer(row.get(key),key);new PythonOnlyUInt64(value);require(value.signum()>0,"original positive ACK counter required");}
        require(signed(row,"date_raw")>0&&signed(row,"played_character_id")>0&&number(1).equals(row.get("close_invocations")),"original positive actor/date and exactly one Close required");
    }
    private static void queryObject(RawJson raw){
        var row=object(raw);require(row.members().keySet().equals(Set.of("step","accepted","status","query_sequence","observation_revision","snapshot_revision","current_timeline_blocker_context","private_build","read_only","advertised","backend_id")),"original timeline exact fields required");
        require(new Text(NativeTimelineBlocker12004.QUERY_STEP).equals(row.get("step"))&&new Bool(true).equals(row.get("accepted"))&&new Bool(true).equals(row.get("private_build"))&&new Bool(true).equals(row.get("read_only"))&&new Bool(false).equals(row.get("advertised"))&&new Text("native-headless").equals(row.get("backend_id")),"original timeline flags required");
        for(String key:List.of("query_sequence","observation_revision","snapshot_revision")){var value=integer(row.get(key),key);new PythonOnlyUInt64(value);require(value.signum()>0,"positive original timeline counter required");}
        var context=OpportunityJson.object(row.get("current_timeline_blocker_context"),"original timeline context");
        require(context.members().keySet().equals(Set.of("schema","schema_version","status","snapshot_revision","date_raw","identity","blocks_simulation","has_open_succession","can_continue","evidence_source","unavailable_reason")),"original timeline context fields required");
        require(new Text("current-timeline-blocker-context-v1").equals(context.get("schema"))&&number(1).equals(context.get("schema_version"))&&Objects.equals(context.get("snapshot_revision"),row.get("snapshot_revision"))&&Objects.equals(context.get("status"),row.get("status")),"original context schema/status/revision differs");signed(context,"date_raw");
        require(Set.of("available","unavailable").contains(text(context.get("status"),"timeline status")),"closed timeline status required");
        require(Set.of("none","death_succession_modal","game_over_modal","succession_select_destiny_modal").contains(text(context.get("identity"),"timeline identity")),"closed timeline identity required");
        for(String key:List.of("blocks_simulation","has_open_succession","can_continue")){var field=asObject(context.get(key));require(field.members().keySet().equals(Set.of("status","value","unavailable_reason")),"exact typed native predicate required");var status=text(field.get("status"),"predicate status");require(status.equals("available")?field.get("value") instanceof Bool&&field.get("unavailable_reason")==Nil.INSTANCE:status.equals("unavailable")&&field.get("value")==Nil.INSTANCE&&field.get("unavailable_reason") instanceof Text,"native predicate type/status differs");}
        var evidence=asObject(context.get("evidence_source"));require(evidence.members().keySet().equals(Set.of("kind","path","root_name","decisive_widget_name")),"original evidence-source fields required");evidence.members().values().forEach(value->text(value,"evidence source text"));optionalText(context.get("unavailable_reason"));
    }
    private static void bindingObject(RawJson raw){var row=object(raw);require(row.members().keySet().equals(Set.of("snapshot_id","revision","native_revision","date_raw","paused","map_ready","episode_character_id","episode_run_id","played_character_id","played_character_alive")),"original full post-query binding required");for(String key:List.of("revision","native_revision"))nullableCounter(member(row,key));for(String key:List.of("date_raw","episode_character_id","played_character_id"))nullableSigned(member(row,key));for(String key:List.of("paused","map_ready","played_character_alive"))require(member(row,key)==Nil.INSTANCE||member(row,key) instanceof Bool,"exact nullable original binding boolean required");for(String key:List.of("snapshot_id","episode_run_id"))optionalText(member(row,key));}
    public sealed interface Payload permits Timeline,View {String machineId();Instant observedAtUtc();}
    /** The Close tool returns the actual original report, not the diagnostic View's canonical receipt metadata. */
    public static RawJson encodeClose(Payload payload){
        require(payload instanceof View,"actual Close presentation View required");var view=(View)payload;
        if(view.close().isEmpty())throw publicFailure(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.VALUE_ERROR,"successor UI has no currently legal verified modal Close");
        var material=view.originalCloseMaterial().orElseThrow(()->publicFailure(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"original Close report material is unavailable"));
        return encodeCloseMaterial(material);
    }
    /** Pure response DATA only: reuse the sole original Close formatter without constructing a Root View. */
    public static RawJson encodeCloseMaterial(CloseMaterial material){return json(closeRoles(object(projectClose(material)),true));}
    /** Pure native query DATA only: retains the original result shape and grants no Query/source permission. */
    public static RawJson encodeTimelineOriginal(RawJson original){queryObject(original);return json(queryRoles(object(original),true));}
    public static RawJson decodeTimelineOriginal(RawJson original){Obj numeric=queryRoles(object(original),false);queryObject(json(numeric));return json(numeric);}
    private static org.xar.ck3.control.service.mcp.PublicServiceFailure publicFailure(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind kind,String message){return new org.xar.ck3.control.service.mcp.PublicServiceFailure(kind,message,Optional.empty());}
    /** Validated response DATA cannot recreate actual Root/source/current/action custody. */
    public static final class CloseData {
        private final RawJson original;private CloseData(RawJson original){this.original=original;}
        public RawJson original(){return original;}
    }
    public static RawJson encodeCloseData(CloseData actual){return Objects.requireNonNull(actual).original;}
    public static CloseData decodeCloseData(RawJson original){
        Obj publicRow=object(original),nativeRow=closeRoles(publicRow,false);CloseMaterial material;
        if(nativeRow.members().containsKey("native_command_result_frame")){
            material=new ReclaimClose(json(asObject(nativeRow.get("native_request_frame"))),json(asObject(nativeRow.get("native_command_result_frame"))),
                    json(asObject(nativeRow.get("actual_pre_submission_snapshot"))),json(asObject(nativeRow.get("initial_query"))),optionalObject(member(nativeRow,"submission_ack")),optionalText(member(nativeRow,"retained_ack_validation_error")));
        }else{
            ClosePhase phase=switch(text(nativeRow.get("status"),"original Close status")){case "submitted_unconfirmed"->ClosePhase.SUBMITTED_UNCONFIRMED;case "post_advance_unconfirmed"->ClosePhase.POST_ADVANCE_UNCONFIRMED;case "materially_verified"->ClosePhase.MATERIALLY_VERIFIED;default->throw new IllegalArgumentException("unsupported original Close result status");};
            var attempts=new ArrayList<PostQueryAttempt>();for(Value value:array(nativeRow.get("post_query_attempts"),"original attempts")){
                Obj row=asObject(value);require(row.members().keySet().equals(Set.of("attempt","query","error","binding")),"exact original attempt fields required");
                attempts.add(new PostQueryAttempt(integer(row.get("attempt"),"attempt").intValueExact(),optionalObject(row.get("query")),optionalText(row.get("error")),optionalObject(row.get("binding"))));
            }
            Obj ending=new Obj(Map.of("date_raw",member(nativeRow,"ending_date_raw"),"revision",member(nativeRow,"ending_revision"),"native_revision",member(nativeRow,"ending_native_revision")));
            if(phase==ClosePhase.POST_ADVANCE_UNCONFIRMED){Obj binding=asObject(nativeRow.get("post_advance_snapshot"));var values=new LinkedHashMap<>(binding.members());values.remove("played_character_id");values.remove("played_character_alive");values.put("played_character",new Obj(Map.of("character_id",member(binding,"played_character_id"),"alive",member(binding,"played_character_alive"))));ending=new Obj(values);}
            material=new SubmittedClose(phase,json(asObject(nativeRow.get("submission_ack"))),json(asObject(nativeRow.get("initial_query"))),attempts,
                    integer(nativeRow.get("starting_date_raw"),"starting date").intValueExact(),json(ending),optionalObject(nativeRow.get("life_advance_result")),optionalText(nativeRow.get("post_failure")));
        }
        require(object(projectClose(material)).equals(nativeRow),"complete original Close schema, ACK, attempts or terminal fields changed");
        require(closeRoles(nativeRow,true).equals(publicRow),"canonical public Close number representation changed");return new CloseData(original);
    }
    private static Obj closeRoles(Obj original,boolean encode){
        Obj row=original;
        for(String key:List.of("snapshot_revision","action_observation_revision","post_observation_revision","ending_revision","ending_native_revision"))row=counter(row,key,encode);
        if(member(row,"submission_ack") instanceof Obj ack)row=row.with("submission_ack",ackRoles(ack,encode));
        if(member(row,"initial_query") instanceof Obj query)row=row.with("initial_query",queryRoles(query,encode));
        if(member(row,"postcondition_query") instanceof Obj query)row=row.with("postcondition_query",queryRoles(query,encode));
        if(member(row,"postcondition_queries") instanceof Arr list)row=row.with("postcondition_queries",new Arr(list.items().stream().<Value>map(v->queryRoles(asObject(v),encode)).toList()));
        if(member(row,"post_query_attempts") instanceof Arr list){var attempts=new ArrayList<Value>();for(Value value:list.items()){
            Obj attempt=asObject(value);if(member(attempt,"query") instanceof Obj query)attempt=attempt.with("query",queryRoles(query,encode));
            if(member(attempt,"binding") instanceof Obj binding)attempt=attempt.with("binding",bindingRoles(binding,encode));attempts.add(attempt);
        }row=row.with("post_query_attempts",new Arr(attempts));}
        if(member(row,"post_advance_snapshot") instanceof Obj binding)row=row.with("post_advance_snapshot",bindingRoles(binding,encode));
        if(member(row,"native_request_frame") instanceof Obj request)row=row.with("native_request_frame",counter(request,"expected_revision",encode));
        if(member(row,"life_advance_result") instanceof Obj life)row=row.with("life_advance_result",object(encode?RootLifeAdvancePublicResult.encode(json(life)):RootLifeAdvancePublicResult.decode(json(life))));
        if(member(row,"actual_pre_submission_snapshot") instanceof Obj snapshot)row=row.with("actual_pre_submission_snapshot",object(encode?PublicSnapshotCodec.encodeSemanticData(json(snapshot)):PublicSnapshotCodec.decodeSemanticData(json(snapshot))));
        if(encode)PublicSnapshotCodec.publicNumbers(DriverJson.toNode(row),"");return row;
    }
    private static Obj ackRoles(Obj row,boolean encode){return counter(counter(row,"snapshot_revision",encode),"action_observation_revision",encode);}
    private static Obj queryRoles(Obj row,boolean encode){for(String key:List.of("query_sequence","observation_revision","snapshot_revision"))row=counter(row,key,encode);if(member(row,"current_timeline_blocker_context") instanceof Obj context)row=row.with("current_timeline_blocker_context",counter(context,"snapshot_revision",encode));return row;}
    private static Obj bindingRoles(Obj row,boolean encode){return counter(counter(row,"revision",encode),"native_revision",encode);}
    private static Obj counter(Obj row,String key,boolean encode){
        if(!row.members().containsKey(key)||row.get(key)==Nil.INSTANCE)return row;Value value=row.get(key);BigInteger exact;
        if(encode)exact=integer(value,"original native uint64 "+key);else{String text=text(value,"public uint64 "+key);require(text.matches("0|[1-9][0-9]*"),"canonical uint64 text required");exact=new BigInteger(text);}
        new PythonOnlyUInt64(exact);return row.with(key,encode?new Text(exact.toString()):new IntegerValue(exact));
    }
    private static Obj asObject(Value value){return OpportunityJson.object(value,"actual object");}
    private static Optional<RawJson> optionalObject(Value value){Objects.requireNonNull(value);return value==Nil.INSTANCE?Optional.empty():Optional.of(json(asObject(value)));}
    private static Optional<String> optionalText(Value value){Objects.requireNonNull(value);return value==Nil.INSTANCE?Optional.empty():Optional.of(text(value,"actual nullable text"));}
    /** Exact JSON text in this internal schema retains original bytes and decimal lexemes across archive serde. */
    public static RawJson encodeMaterial(CloseMaterial material){
        var row=StrictJson.object().put("schema","xar.java.original-close-material/v1");
        if(material instanceof SubmittedClose value){row.put("kind","SUBMITTED").put("phase",value.phase().name()).put("starting_date_raw",value.startingDateRaw());putRaw(row,"submission_ack",Optional.of(value.submissionAck()));putRaw(row,"initial_query",Optional.of(value.initialQuery()));putRaw(row,"ending_snapshot",Optional.of(value.endingSnapshot()));putRaw(row,"life_result",value.lifeResult());if(value.failure().isPresent())row.put("failure",value.failure().orElseThrow());else row.putNull("failure");
            var attempts=row.putArray("post_attempts");for(var actual:value.postAttempts()){var attempt=attempts.addObject().put("attempt",actual.attempt());putRaw(attempt,"query",actual.query());putRaw(attempt,"binding",actual.binding());if(actual.error().isPresent())attempt.put("error",actual.error().orElseThrow());else attempt.putNull("error");}
        }else{var value=(ReclaimClose)material;row.put("kind","RECLAIM");putRaw(row,"original_request",Optional.of(value.originalRequest()));putRaw(row,"original_command_result",Optional.of(value.originalCommandResult()));putRaw(row,"pre_submission_snapshot",Optional.of(value.preSubmissionSnapshot()));putRaw(row,"initial_query",Optional.of(value.initialQuery()));putRaw(row,"retained_submission_ack",value.retainedSubmissionAck());if(value.retainedAckValidationError().isPresent())row.put("retained_ack_validation_error",value.retainedAckValidationError().orElseThrow());else row.putNull("retained_ack_validation_error");}
        return PublicDataJson.encode(row);
    }
    public static CloseMaterial decodeMaterial(RawJson original){
        var raw=PublicDataJson.object(original);require("xar.java.original-close-material/v1".equals(StrictJson.text(raw.get("schema"))),"exact Close material schema required");
        if("SUBMITTED".equals(StrictJson.text(raw.get("kind")))){
            var row=StrictJson.object(raw,Set.of("schema","kind","phase","starting_date_raw","submission_ack","initial_query","ending_snapshot","life_result","failure","post_attempts"));var attempts=new ArrayList<PostQueryAttempt>();require(row.get("post_attempts").isArray(),"actual post-attempt array required");
            for(var value:row.get("post_attempts")){var attempt=StrictJson.object(value,Set.of("attempt","query","binding","error"));attempts.add(new PostQueryAttempt((int)StrictJson.integer(attempt.get("attempt"),1,8),rawText(attempt,"query"),attempt.get("error").isNull()?Optional.empty():Optional.of(StrictJson.text(attempt.get("error"))),rawText(attempt,"binding")));}
            return new SubmittedClose(ClosePhase.valueOf(StrictJson.text(row.get("phase"))),rawText(row,"submission_ack").orElseThrow(),rawText(row,"initial_query").orElseThrow(),attempts,(int)StrictJson.integer(row.get("starting_date_raw"),1,Integer.MAX_VALUE),rawText(row,"ending_snapshot").orElseThrow(),rawText(row,"life_result"),row.get("failure").isNull()?Optional.empty():Optional.of(StrictJson.text(row.get("failure"))));
        }
        var row=StrictJson.object(raw,Set.of("schema","kind","original_request","original_command_result","pre_submission_snapshot","initial_query","retained_submission_ack","retained_ack_validation_error"));require("RECLAIM".equals(StrictJson.text(row.get("kind"))),"closed Close material kind required");
        return new ReclaimClose(rawText(row,"original_request").orElseThrow(),rawText(row,"original_command_result").orElseThrow(),rawText(row,"pre_submission_snapshot").orElseThrow(),rawText(row,"initial_query").orElseThrow(),rawText(row,"retained_submission_ack"),row.get("retained_ack_validation_error").isNull()?Optional.empty():Optional.of(StrictJson.text(row.get("retained_ack_validation_error"))));
    }
    private static void putRaw(ObjectNode row,String key,Optional<RawJson> value){if(value.isPresent())row.put(key,new String(value.orElseThrow().bytes(),java.nio.charset.StandardCharsets.UTF_8));else row.putNull(key);}
    private static Optional<RawJson> rawText(ObjectNode row,String key){var value=row.get(key);require(value!=null,"required original material slot: "+key);return value.isNull()?Optional.empty():Optional.of(new RawJson(StrictJson.text(value).getBytes(java.nio.charset.StandardCharsets.UTF_8)));}
    public record Timeline(PlanningReadReceipt original,NativeTimelineBlocker12004.Query value,String machineId,Instant observedAtUtc) implements Payload {
        public Timeline{Objects.requireNonNull(original);Objects.requireNonNull(value);StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);require(original.requestId().equals(value.requestId()),"public timeline changed its actual original request");}
    }
    /** Public DATA transport only. The opaque native context cannot recreate the private Query/source binding. */
    public static final class TimelineData {
        private final BigInteger sequence,observationRevision,snapshotRevision;private final RawJson context,original;private final String machine;private final Instant observed;
        private TimelineData(BigInteger sequence,BigInteger observationRevision,BigInteger snapshotRevision,RawJson context,RawJson original,String machine,Instant observed){this.sequence=sequence;this.observationRevision=observationRevision;this.snapshotRevision=snapshotRevision;this.context=context;this.original=original;this.machine=machine;this.observed=observed;}
        public BigInteger querySequence(){return sequence;}public BigInteger observationRevision(){return observationRevision;}public BigInteger snapshotRevision(){return snapshotRevision;}public RawJson context(){return context;}public String machineId(){return machine;}public Instant observedAtUtc(){return observed;}
    }
    public static TimelineData decodeTimelineData(RawJson original){
        var row=StrictJson.object(PublicDataJson.object(original),Set.of("step","accepted","status","query_sequence","observation_revision","snapshot_revision","current_timeline_blocker_context","private_build","read_only","advertised","backend_id","machine_id","observed_at_utc"));
        require(StrictJson.text(row.get("step")).equals(NativeTimelineBlocker12004.QUERY_STEP)&&bool(row.get("accepted"))&&bool(row.get("private_build"))&&bool(row.get("read_only"))&&!bool(row.get("advertised"))&&StrictJson.text(row.get("backend_id")).equals("native-headless"),"public timeline changed its native read-only producer flags");
        var sequence=publicUnsigned(row.get("query_sequence"));var observation=publicUnsigned(row.get("observation_revision"));var revision=publicUnsigned(row.get("snapshot_revision"));require(sequence.signum()>0&&observation.signum()>0&&revision.signum()>0,"actual positive timeline counters required");
        var context=row.get("current_timeline_blocker_context");require(context!=null&&context.isObject(),"public timeline native context must remain an object");require(publicUnsigned(context.get("snapshot_revision")).equals(revision),"public timeline nested revision differs");
        String status=StrictJson.text(row.get("status"));require((status.equals("available")||status.equals("unavailable"))&&status.equals(StrictJson.text(context.get("status"))),"public timeline/context availability differs");
        var raw=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);return new TimelineData(sequence,observation,revision,new RawJson(DriverJson.encode(raw.get("current_timeline_blocker_context"))),original,StrictJson.text(row.get("machine_id")),Instant.parse(StrictJson.text(row.get("observed_at_utc"))));
    }
    public static RawJson encodeTimelineData(TimelineData actual){Objects.requireNonNull(actual);return actual.original;}
    private static BigInteger publicUnsigned(JsonNode actual){require(actual!=null&&actual.isTextual()&&actual.textValue().matches("0|[1-9][0-9]*"),"canonical uint64 string required");return new PythonOnlyUInt64(new BigInteger(actual.textValue())).value();}
    public record CloseResult(ActionReceipt.Outcome outcome,String actionId,ExactRef canonicalReceipt,boolean materialClearance,Optional<ExactRef> verifiedDateAdvance,
            Optional<SuccessorUiObligation.ReadOnlyReconciliation> reconciliation) {
        public CloseResult(ActionReceipt.Outcome outcome,String actionId,ExactRef canonicalReceipt,boolean materialClearance,Optional<ExactRef> verifiedDateAdvance){this(outcome,actionId,canonicalReceipt,materialClearance,verifiedDateAdvance,Optional.empty());}
        public CloseResult{Objects.requireNonNull(outcome);StrictJson.text(actionId);Objects.requireNonNull(canonicalReceipt);Objects.requireNonNull(verifiedDateAdvance);Objects.requireNonNull(reconciliation);require(canonicalReceipt.bytes()>0,"actual canonical Close result required");require(!verifiedDateAdvance.isPresent()||materialClearance,"date result requires real material clearance");
            reconciliation.ifPresent(value->require(outcome==ActionReceipt.Outcome.UNRESOLVED&&value.originalUnknownReceipt().equals(canonicalReceipt)&&value.materialClearance().isPresent()==materialClearance&&value.verifiedDateAdvance().equals(verifiedDateAdvance),"public reconciliation must retain the same original UNKNOWN and independent confirmed proofs"));}
    }
    public enum Status {CLEAR("clear"),CLOSE_REQUIRED("close_required"),DEFERRED_PLAYER_DECISION("deferred_player_decision"),UI_UNRESOLVED("ui_unresolved");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status decode(String actual){for(var value:values())if(value.wire.equals(actual))return value;throw new IllegalArgumentException("closed successor UI public status required");}}
    public record View(Status status,boolean pending,boolean playerDecisionPending,boolean actionSubmitted,RawJson snapshot,
            Optional<SuccessorUiObligation> transition,Optional<CloseResult> close,String machineId,Instant observedAtUtc,Optional<ExactRef> eventDiagnosis,Optional<CloseMaterial> originalCloseMaterial) implements Payload {
        public View(Status status,boolean pending,boolean playerDecisionPending,boolean actionSubmitted,RawJson snapshot,Optional<SuccessorUiObligation> transition,Optional<CloseResult> close,String machineId,Instant observedAtUtc,Optional<ExactRef> eventDiagnosis){this(status,pending,playerDecisionPending,actionSubmitted,snapshot,transition,close,machineId,observedAtUtc,eventDiagnosis,Optional.empty());}
        public View(Status status,boolean pending,boolean playerDecisionPending,boolean actionSubmitted,RawJson snapshot,Optional<SuccessorUiObligation> transition,Optional<CloseResult> close,String machineId,Instant observedAtUtc){this(status,pending,playerDecisionPending,actionSubmitted,snapshot,transition,close,machineId,observedAtUtc,Optional.empty());}
        public View{Objects.requireNonNull(status);Objects.requireNonNull(snapshot);PublicDataJson.object(snapshot);Objects.requireNonNull(transition);Objects.requireNonNull(close);Objects.requireNonNull(eventDiagnosis);Objects.requireNonNull(originalCloseMaterial);StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);}
    }
    public static RawJson encode(Payload input){
        if(input instanceof Timeline timeline){
            var original=timeline.original().original().originalResultToken().orElseThrow();var row=PublicDataJson.object(original);
            for(String key:List.of("query_sequence","observation_revision","snapshot_revision"))decimal(row,key);
            decimal((ObjectNode)row.get("current_timeline_blocker_context"),"snapshot_revision");row.put("machine_id",timeline.machineId());row.put("observed_at_utc",timeline.observedAtUtc().toString());
            PublicSnapshotCodec.publicNumbers(row,"");return PublicDataJson.encodePreservingDecimals(row,original);
        }
        var value=(View)input;var row=StrictJson.object().put("status",value.status().wire()).put("pending",value.pending()).put("player_decision_pending",value.playerDecisionPending()).put("action_submitted",value.actionSubmitted()).put("new_parent_submitted",false).put("date_advanced",value.close().flatMap(CloseResult::verifiedDateAdvance).isPresent()).put("machine_id",value.machineId()).put("observed_at_utc",value.observedAtUtc().toString());
        row.set("snapshot",PublicDataJson.object(value.snapshot()));if(value.transition().isEmpty())row.putNull("transition");else row.set("transition",SuccessorUiObligationCodec.toJson(value.transition().orElseThrow()));
        if(value.eventDiagnosis().isPresent())row.set("pending_ui_diagnosis",value.eventDiagnosis().orElseThrow().toJson());else row.putNull("pending_ui_diagnosis");
        if(value.close().isEmpty())row.putNull("close_result");else{var closed=value.close().orElseThrow();var result=row.putObject("close_result").put("action_id",closed.actionId()).put("outcome",closed.outcome().name()).put("material_result_verified",closed.materialClearance()).put("date_advance_verified",closed.verifiedDateAdvance().isPresent()).put("replay_authorized",false);result.set("canonical_receipt",closed.canonicalReceipt().toJson());if(closed.verifiedDateAdvance().isPresent())result.set("verified_date_advance",closed.verifiedDateAdvance().orElseThrow().toJson());else result.putNull("verified_date_advance");
            if(closed.reconciliation().isEmpty())result.putNull("read_only_reconciliation");else{var actual=closed.reconciliation().orElseThrow();var reconciled=result.putObject("read_only_reconciliation");reconciled.set("original_unknown_receipt",actual.originalUnknownReceipt().toJson());reconciled.set("confirmed_receipt",actual.confirmedReceipt().toJson());reconciled.set("same_original_action_proof",actual.sameOriginalActionProof().toJson());if(actual.materialClearance().isPresent())reconciled.set("material_clearance",actual.materialClearance().orElseThrow().toJson());else reconciled.putNull("material_clearance");if(actual.verifiedDateAdvance().isPresent())reconciled.set("verified_date_advance",actual.verifiedDateAdvance().orElseThrow().toJson());else reconciled.putNull("verified_date_advance");}}
        PublicSnapshotCodec.publicNumbers(row,"");return PublicDataJson.encodePreservingDecimals(row,new RawJson(org.xar.ck3.control.application.driver.DriverJson.encode(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of("snapshot",org.xar.ck3.control.application.driver.DriverJson.object(value.snapshot().bytes(),RawJson.MAXIMUM_BYTES))))));
    }
    private static boolean bool(JsonNode actual){require(actual!=null&&actual.isBoolean(),"exact public boolean required");return actual.booleanValue();}
    private static void decimal(ObjectNode row,String key){var value=StrictJson.integer(row.get(key),BigInteger.ZERO,BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE));row.put(key,new PythonOnlyUInt64(value).value().toString());}
    /** A decoded public view is DATA. It cannot recreate Current, M3 PendingCause or a canonical continuation token. */
    public static View decodeView(RawJson original){
        var row=StrictJson.object(PublicDataJson.object(original),Set.of("status","pending","player_decision_pending","action_submitted","new_parent_submitted","date_advanced","machine_id","observed_at_utc","snapshot","transition","close_result","pending_ui_diagnosis"));
        require(!bool(row.get("new_parent_submitted")),"successor UI tool cannot submit a new parent");
        var domain=org.xar.ck3.control.application.driver.DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        var snapshot=new RawJson(org.xar.ck3.control.application.driver.DriverJson.encode(domain.get("snapshot")));
        Optional<SuccessorUiObligation> transition=row.get("transition").isNull()?Optional.empty():Optional.of(SuccessorUiObligationCodec.fromJson(row.get("transition")));
        Optional<CloseResult> closed=Optional.empty();if(!row.get("close_result").isNull()){
            var value=StrictJson.object(row.get("close_result"),Set.of("action_id","outcome","material_result_verified","date_advance_verified","replay_authorized","canonical_receipt","verified_date_advance","read_only_reconciliation"));
            require(!bool(value.get("replay_authorized")),"original unknown Close never authorizes replay");var date=value.get("verified_date_advance").isNull()?Optional.<ExactRef>empty():Optional.of(ExactRef.fromJson(value.get("verified_date_advance")));
            require(bool(value.get("date_advance_verified"))==date.isPresent(),"actual date proof presence differs");
            Optional<SuccessorUiObligation.ReadOnlyReconciliation> reconciliation=Optional.empty();if(!value.get("read_only_reconciliation").isNull()){
                var actual=StrictJson.object(value.get("read_only_reconciliation"),Set.of("original_unknown_receipt","confirmed_receipt","same_original_action_proof","material_clearance","verified_date_advance"));
                reconciliation=Optional.of(new SuccessorUiObligation.ReadOnlyReconciliation(ExactRef.fromJson(actual.get("original_unknown_receipt")),ExactRef.fromJson(actual.get("confirmed_receipt")),ExactRef.fromJson(actual.get("same_original_action_proof")),actual.get("material_clearance").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(actual.get("material_clearance"))),actual.get("verified_date_advance").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(actual.get("verified_date_advance")))));
            }
            closed=Optional.of(new CloseResult(ActionReceipt.Outcome.valueOf(StrictJson.text(value.get("outcome"))),StrictJson.text(value.get("action_id")),ExactRef.fromJson(value.get("canonical_receipt")),bool(value.get("material_result_verified")),date,reconciliation));
        }
        require(bool(row.get("date_advanced"))==closed.flatMap(CloseResult::verifiedDateAdvance).isPresent(),"public date advancement cannot be claimed without actual proof");
        return new View(Status.decode(StrictJson.text(row.get("status"))),bool(row.get("pending")),bool(row.get("player_decision_pending")),bool(row.get("action_submitted")),snapshot,transition,closed,StrictJson.text(row.get("machine_id")),Instant.parse(StrictJson.text(row.get("observed_at_utc"))),row.get("pending_ui_diagnosis").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("pending_ui_diagnosis"))));
    }
}
