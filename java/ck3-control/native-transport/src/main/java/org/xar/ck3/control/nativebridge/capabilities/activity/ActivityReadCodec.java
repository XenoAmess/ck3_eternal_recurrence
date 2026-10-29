package org.xar.ck3.control.nativebridge.capabilities.activity;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.governance.activity.ActivityConfigurationCodec;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels.Frame;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.finance.feastterminal.CompletionCallJournal;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityPayload.*;

/** Strict migration of the actual Python producers; no quotation, membership or ACK grants Start. */
public final class ActivityReadCodec {
    private ActivityReadCodec() { }
    static final Set<String> CANDIDATE_FAILURES = Set.of("exact_build_rejected","frame_changed","planner_unavailable","no_normal_refresh","candidate_source_unavailable","native_evaluation_failed","arrival_unavailable","configuration_changed");
    static final Set<String> RULE_FAILURES = Set.of("exact_build_rejected","frame_changed","planner_unavailable","window_unbound","rule_unavailable","ambiguous_rule","native_read_failed","native_action_failed","postcondition_failed");
    static final Set<String> PROVENANCE_FAILURES = Set.of("exact_build_rejected","no_normal_refresh","frame_changed","planner_unavailable","rule_unavailable","ambiguous_rule","capture_overflow","native_read_failed");
    static final Set<String> SELECTED_FAILURES = Set.of("exact_build_rejected","frame_changed","planner_unavailable","planner_diagnostic_unavailable","planner_absent","not_stage_five","widget_detached","widget_hidden","host_view_type_mismatch","no_normal_refresh","configuration_changed","guest_source_unavailable","native_evaluation_failed","cache_disagreed","arrival_source_unavailable","arrival_evaluation_failed");
    static final Set<String> START_FAILURES = Set.of("exact_build_rejected","callback_missing","planner_unavailable","not_stage5","selected_type_mismatch","native_identity_mismatch","native_evaluation_failed","frame_changed");
    public static ActivityPayload decode(ActivityNativeContracts.Query query, byte[] payload, Frame frame, Obj arguments,
            String envelopeStatus, CompletionCallJournal.Source journalSource) {
        String message=publicPayloadMessage(query);
        return message==null?decodeBody(query,payload,frame,arguments,envelopeStatus,journalSource)
                :checked(message,()->decodeBody(query,payload,frame,arguments,envelopeStatus,journalSource));
    }
    /** The original public parser has one typed BridgeUnavailable error family. Its message is
     * selected at the actual validation branch, never inferred from a coordinator diagnosis. */
    public static final class MalformedPayload extends IllegalArgumentException {
        private static final long serialVersionUID=1L;
        public MalformedPayload(String originalMessage,Throwable cause){super(originalMessage,cause);}
    }
    private static <T> T checked(String originalMessage,java.util.function.Supplier<T> validation) {
        try{return validation.get();}
        catch(MalformedPayload original){throw original;}
        catch(IllegalArgumentException|NullPointerException invalid){throw new MalformedPayload(originalMessage,invalid);}
    }
    private static void check(String originalMessage,Runnable validation){checked(originalMessage,()->{validation.run();return null;});}
    private static String publicPayloadMessage(ActivityNativeContracts.Query query){return switch(query){
        case GUEST_CANDIDATE->"private feast guest candidate payload malformed";
        case GUEST_OPINION->"private feast guest opinion payload malformed";
        case GUEST_TARGET->"private feast target payload malformed";
        case GUEST_ROUTE_PROOF->"private feast guest route proof malformed";
        case GUEST_RULE_PROVENANCE->"private feast rule provenance payload malformed";
        case START_INPUTS,HOSTED->"private feast Start payload malformed";
        case FULL_COST->"private feast full-cost payload malformed";
        default->null;
    };}
    private static ActivityPayload decodeBody(ActivityNativeContracts.Query query, byte[] payload, Frame frame, Obj arguments,
            String envelopeStatus, CompletionCallJournal.Source journalSource) {
        JsonNode row = parse(payload); JsonNode args = argument(arguments); Obj original = app(row);
        return switch(query) {
            case DIAGNOSTIC -> { available(envelopeStatus); yield new Diagnostic(ActivityPlannerDiagnostic.decode(payload,new ActivityPlannerDiagnostic.Frame(frame.nativeRevision(),frame.dateRaw(),frame.actorId())),original); }
            case STAGE1_OPTION -> { available(envelopeStatus); yield new StageOne(ActivityConfigurationCodec.stageOne(payload,frame),original); }
            case STAGE2_OPTION -> { available(envelopeStatus); yield new StageTwo(ActivityConfigurationCodec.stageTwo(payload,frame),original); }
            case STAGE2_LOCATION -> { available(envelopeStatus); yield new Location(ActivityConfigurationCodec.location(payload,frame,ActivityNativeContracts.candidates(args)),original); }
            case STAGE2_GATE -> { available(envelopeStatus); yield new Gate(ActivityConfigurationCodec.gate(payload,frame),original); }
            case GOLD -> gold(row,frame,envelopeStatus);
            case FULL_COST -> fullCost(row,frame,envelopeStatus);
            case START_INPUTS -> inputs(row,frame,envelopeStatus);
            case HOSTED -> hosted(row,frame,envelopeStatus,journalSource);
            case GUEST_CANDIDATE -> candidate(row,frame,envelopeStatus);
            case GUEST_OPINION -> opinion(row,frame,args,envelopeStatus);
            case GUEST_TARGET -> target(row,frame,args,envelopeStatus);
            case GUEST_ROUTE_PROOF -> route(row,frame,envelopeStatus);
            case GUEST_RULE -> ruleRead(row,frame,text(args,"authored_rule_key"),envelopeStatus,false);
            case GUEST_RULE_PROVENANCE -> provenance(row,frame,args,envelopeStatus);
        };
    }
    public static byte[] encode(ActivityPayload payload) { return org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(payload.original()); }
    /** Public representation inverse feeds the identical existing business decoder. This expects
     * the payload object, without the public read/provenance envelope fields. */
    public static ActivityPayload decodePublicPayload(ActivityNativeContracts.Query query,byte[] payload,Frame frame,Obj arguments,
            String envelopeStatus,CompletionCallJournal.Source journalSource) {
        return decode(query,ActivityPublic64.decode(query,new org.xar.ck3.control.application.action.RawJson(payload)).bytes(),frame,arguments,envelopeStatus,journalSource);
    }
    private static void bind(JsonNode row,Frame frame,String schema) {
        eq(row,"schema",schema); need(positive(row,"snapshot_revision").equals(frame.nativeRevision()) && number(row,"date_raw",BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)).equals(frame.dateRaw()) && number(row,"actor_character_id",BigInteger.ONE,U32).equals(frame.actorId()),"activity payload crossed native frame");
    }
    private static void feast(JsonNode row,int stage) { eq(row,"activity_key","activity_feast"); need(integer(row,"planning_stage",stage,stage)==stage,"activity stage"); }
    private static void readonly(JsonNode row) { yes(row,"read_only"); no(row,"raw_pointer_fields_persisted"); }
    private static void available(String status) { need(status.equals("available"),"available activity envelope required"); }
    private static Gold gold(JsonNode row,Frame frame,String status) {
        exact(row,FRAME+" activity_key planning_stage normal_refresh_sequence configured_cost resource_value final_can_start raw_slot12_resource_mapping read_only raw_pointer_fields_persisted");
        bind(row,frame,"activity-stage5-gold-cost-private-read-v1"); feast(row,5); readonly(row); available(status); nil(row,"final_can_start"); nil(row,"raw_slot12_resource_mapping");
        return new Gold(positive(row,"normal_refresh_sequence"),goldValue(row.get("configured_cost"),"CostBreakdown.GetCost"),goldValue(row.get("resource_value"),"CCharacter.GetGold"),app(row));
    }
    private static BigInteger goldValue(JsonNode row,String source) { exact(row,"resource raw scale source"); eq(row,"resource","gold"); eq(row,"source",source); need(integer(row,"scale",100000,100000)==100000,"Gold scale"); return signed(row,"raw"); }
    private static FullCost fullCost(JsonNode row,Frame frame,String status) {
        exact(row,FRAME+" activity_key planning_stage normal_refresh_sequence scale actor_gold_raw resources final_can_start final_can_start_failure_display read_only raw_pointer_fields_persisted");
        check("private feast full-cost resources malformed",()->exact(row.get("resources"),"gold treasury piety barter_goods"));
        JsonNode display=row.get("final_can_start_failure_display");check("private feast CanStart failure display malformed",()->exact(display,"state value unknown_reason"));
        List<Cost> costs=costs(row.get("resources"),"private feast full-cost resources malformed","private feast full-cost resource malformed");
        bind(row,frame,"activity-stage5-feast-full-cost-private-read-v1");feast(row,5);readonly(row);available(status);integer(row,"scale",100000,100000);positive(row,"normal_refresh_sequence");signed(row,"actor_gold_raw");
        boolean start=bool(row,"final_can_start");
        FailureDisplay failure=checked("private feast CanStart failure display malformed",()->{
            if(start){eq(display,"state","not_applicable");nil(display,"value");nil(display,"unknown_reason");return new FailureDisplay(DisplayState.NOT_APPLICABLE,Optional.empty(),Optional.empty());}
            if(text(display,"state").equals("known")){String value=text(display,"value");need(!value.isEmpty()&&value.getBytes(StandardCharsets.UTF_8).length<512,"CanStart display bound");nil(display,"unknown_reason");return new FailureDisplay(DisplayState.KNOWN,Optional.of(value),Optional.empty());}
            eq(display,"state","unknown");nil(display,"value");eq(display,"unknown_reason","native_failure_display_empty");return new FailureDisplay(DisplayState.UNKNOWN,Optional.empty(),Optional.of("native_failure_display_empty"));
        });
        return new FullCost(positive(row,"normal_refresh_sequence"),signed(row,"actor_gold_raw"),costs,start,failure,app(row));
    }
    private static List<Cost> costs(JsonNode row,String shapeMessage,String rowMessage) {
        check(shapeMessage,()->exact(row,"gold treasury piety barter_goods"));List<Cost> result=new ArrayList<>();
        for(Resource resource:Resource.values())result.add(checked(rowMessage,()->{JsonNode item=row.get(resource.name().toLowerCase(java.util.Locale.ROOT));exact(item,"resource_index configured_cost_raw");return new Cost(resource,integer(item,"resource_index",0,9),signed(item,"configured_cost_raw"));}));
        return List.copyOf(result);
    }
    private static List<Balance> balances(JsonNode row) {
        check("private feast balances malformed",()->exact(row,"gold treasury piety barter_goods"));List<Balance> result=new ArrayList<>();
        for(Resource resource:Resource.values())result.add(checked("private feast balance row malformed",()->{JsonNode item=row.get(resource.name().toLowerCase(java.util.Locale.ROOT));exact(item,"available raw");Optional<BigInteger> value;if(bool(item,"available"))value=Optional.of(signed(item,"raw"));else{nil(item,"raw");value=Optional.empty();}return new Balance(resource,value);}));
        return List.copyOf(result);
    }
    private static List<HostedActivity> hostedIds(JsonNode rows) {
        check("private feast hosted identities malformed",()->need(rows!=null&&rows.isArray()&&rows.size()<=64,"hosted activity list"));List<HostedActivity> result=new ArrayList<>();Set<Long> seen=new HashSet<>();
        for(JsonNode row:rows) {check("private feast hosted identity malformed",()->{allowed(row,"activity_id host_character_id activity_type_key","terminal_flags_observed native_completed native_invalidated native_completion_stamp_observed native_completion_stamp_raw");long id=id(row,"activity_id");need(seen.add(id),"duplicate hosted full ActivityID");id(row,"host_character_id");String type=text(row,"activity_type_key");need(!type.isEmpty()&&type.length()<=63,"activity type bound");});long id=id(row,"activity_id");String type=text(row,"activity_type_key");Optional<Boolean> completed=Optional.empty(),invalidated=Optional.empty();
            if(row.has("terminal_flags_observed")||row.has("native_completed")||row.has("native_invalidated")){check("private feast hosted terminal flags malformed",()->{yes(row,"terminal_flags_observed");bool(row,"native_completed");bool(row,"native_invalidated");});completed=Optional.of(bool(row,"native_completed"));invalidated=Optional.of(bool(row,"native_invalidated"));}
            Optional<BigInteger> stamp=Optional.empty();if(row.has("native_completion_stamp_observed")||row.has("native_completion_stamp_raw"))stamp=checked("private feast native completion stamp malformed",()->{if(bool(row,"native_completion_stamp_observed"))return Optional.of(u64(row,"native_completion_stamp_raw"));nil(row,"native_completion_stamp_raw");return Optional.empty();});
            result.add(new HostedActivity(id,id(row,"host_character_id"),type,completed,invalidated,stamp));
        } return List.copyOf(result);
    }
    private static Optional<OutcomeValues> outcomes(JsonNode row) {
        if(!row.has("outcome_values"))return Optional.empty();JsonNode value=row.get("outcome_values");check("private feast outcome counters malformed",()->exact(value,"prestige_raw stress_points reveler_present reveler_xp_raw"));
        var prestige=checked("private feast fixed-point outcome counter malformed",()->optionalSigned(value,"prestige_raw"));var revelerXp=checked("private feast fixed-point outcome counter malformed",()->optionalSigned(value,"reveler_xp_raw"));
        var stress=checked("private feast integer stress counter malformed",()->optionalInt(value,"stress_points"));var reveler=checked("private feast reveler presence malformed",()->optionalBoolean(value,"reveler_present"));
        return Optional.of(new OutcomeValues(prestige,stress,reveler,revelerXp));
    }
    private static Optional<BigInteger> optionalSigned(JsonNode row,String key) { return row.get(key).isNull()?Optional.empty():Optional.of(signed(row,key)); }
    private static Optional<Integer> optionalInt(JsonNode row,String key) { return row.get(key).isNull()?Optional.empty():Optional.of(integer(row,key,Integer.MIN_VALUE,Integer.MAX_VALUE)); }
    private static Optional<Boolean> optionalBoolean(JsonNode row,String key) { return row.get(key).isNull()?Optional.empty():Optional.of(bool(row,key)); }
    private static Candidate candidate(JsonNode row,Frame frame,String envelope) {
        exact(row,FRAME+" activity_key planning_stage status normal_refresh_sequence source_fingerprint native_filtered_pre_invitation candidate read_only raw_pointer_fields_persisted"); bind(row,frame,"activity-feast-guest-candidate-private-read-v1"); feast(row,5); readonly(row); String status=text(row,"status");
        if(status.equals("observed") || status.equals("no_qualified_candidate")) { BigInteger refresh=checked("private feast guest candidate source malformed",()->{available(envelope);var value=positive(row,"normal_refresh_sequence");fingerprint(row,"source_fingerprint");return value;}); Optional<CandidateRow> candidate;
            if(status.equals("observed")) { CandidateRow found=checked("private feast guest candidate row malformed",()->{yes(row,"native_filtered_pre_invitation");CandidateRow value=candidateRow(row.get("candidate"),false);need(value.arrivalRaw()<=value.plannedStartRaw(),"candidate must arrive by start");return value;});candidate=Optional.of(found); }
            else { check("private feast guest empty result malformed",()->{no(row,"native_filtered_pre_invitation");nil(row,"candidate");});candidate=Optional.empty(); }
            return new Candidate(status.equals("observed")?CandidateStatus.OBSERVED:CandidateStatus.NO_QUALIFIED_CANDIDATE,Optional.empty(),Optional.of(refresh),Optional.of(text(row,"source_fingerprint")),candidate,app(row));
        }
        if(!CANDIDATE_FAILURES.contains(status))throw new MalformedPayload("private feast guest candidate status unknown",null);
        check("private feast guest unavailable result malformed",()->{need(envelope.equals("unavailable"),"candidate unavailable status");for(String key:List.of("normal_refresh_sequence","source_fingerprint","native_filtered_pre_invitation","candidate"))nil(row,key);});
        return new Candidate(CandidateStatus.UNAVAILABLE,Optional.of(status),Optional.empty(),Optional.empty(),Optional.empty(),app(row));
    }
    private static CandidateRow candidateRow(JsonNode row,boolean nonpositiveAllowed) { exact(row,"character_id planner_join_raw travel_days arrival_raw planned_start_raw"); BigInteger join=signed(row,"planner_join_raw"); need(nonpositiveAllowed || join.signum()>0,"positive candidate join required"); return new CandidateRow(id(row,"character_id"),join,integer(row,"travel_days",Integer.MIN_VALUE,Integer.MAX_VALUE),integer(row,"arrival_raw",Integer.MIN_VALUE,Integer.MAX_VALUE),integer(row,"planned_start_raw",Integer.MIN_VALUE,Integer.MAX_VALUE)); }
    private static Opinion opinion(JsonNode row,Frame frame,JsonNode args,String envelope) {
        boolean activity=args.has("activity_id"); allowed(row,FRAME+" guest_character_id status guest_opinion_of_actor read_only raw_pointer_fields_persisted"+(activity?" activity_target":""),"reward_opinion_modifiers"); bind(row,frame,"activity-feast-guest-opinion-private-read-v1"); readonly(row); long guest=id(row,"guest_character_id"); need(guest==id(args,"guest_character_id") && guest!=frame.actorId().longValueExact(),"guest opinion identity"); String status=text(row,"status"); Optional<Integer> value;
        if(status.equals("observed"))value=Optional.of(checked("private feast guest opinion value malformed",()->{available(envelope);return integer(row,"guest_opinion_of_actor",-100,100);}));
        else {if(!Set.of("invalid_request","frame_changed","opinion_unavailable").contains(status))throw new MalformedPayload("private feast guest opinion status unknown",null);check("private feast guest opinion unavailable malformed",()->{need(envelope.equals("unavailable"),"opinion failure envelope");nil(row,"guest_opinion_of_actor");});value=Optional.empty();}
        Optional<Obj> target=Optional.empty(); if(activity) { activityTarget(row.get("activity_target"),id(args,"activity_id"),frame.actorId().longValueExact(),guest); target=Optional.of(app(row.get("activity_target"))); }
        Optional<Obj> modifiers=Optional.empty();if(row.has("reward_opinion_modifiers")){JsonNode entries=row.get("reward_opinion_modifiers");check("private feast reward modifier keys malformed",()->exact(entries,"hosted_feast_opinion hosted_mediocre_feast_opinion impressed_opinion"));
            for(JsonNode item:entries){check("private feast reward modifier row malformed",()->exact(item,"status present value"));String modifierStatus=checked("private feast reward modifier status unknown",()->text(item,"status"));
                if(modifierStatus.equals("observed"))check("private feast reward modifier value malformed",()->{need(status.equals("observed"),"reward modifier needs observed opinion");if(bool(item,"present"))integer(item,"value",Integer.MIN_VALUE,Integer.MAX_VALUE);else nil(item,"value");});
                else if(modifierStatus.equals("read_failed"))check("private feast reward modifier failure malformed",()->{nil(item,"present");nil(item,"value");});
                else throw new MalformedPayload("private feast reward modifier status unknown",null);
            }modifiers=Optional.of(app(entries));}
        return new Opinion(guest,status,value,target,modifiers,app(row));
    }
    private static void activityTarget(JsonNode row,long activity,long actor,long guest) {
        check("private feast activity target malformed",()->{exact(row,"status activity_id guest_character_id host_character_id activity_type_key native_completed native_invalidated attending_list_observed attending_count target_in_attending_list character_record_observed character_activity_id character_activity_state_raw character_record_matches_activity native_active_attendee");need(id(row,"activity_id")==activity&&id(row,"guest_character_id")==guest,"activity target binding");});
        String status=checked("private feast activity target status unknown",()->text(row,"status"));if(!status.equals("observed")){
            if(!Set.of("exact_build_rejected","frame_rejected","manager_unavailable","actor_identity_unavailable","activity_identity_unavailable","target_identity_unavailable","attending_list_unavailable","character_record_unavailable","snapshot_changed").contains(status))throw new MalformedPayload("private feast activity target status unknown",null);
            check("private feast activity target unavailable malformed",()->row.fieldNames().forEachRemaining(key->{if(!Set.of("status","activity_id","guest_character_id").contains(key))nil(row,key);}));return;
        }
        check("private feast activity target observation malformed",()->{need(id(row,"host_character_id")==actor,"activity target host");eq(row,"activity_type_key","activity_feast");bool(row,"native_completed");bool(row,"native_invalidated");yes(row,"attending_list_observed");BigInteger count=number(row,"attending_count",BigInteger.ZERO,U64);boolean attending=bool(row,"target_in_attending_list");need(!attending||count.signum()>0,"attending empty set disagrees");bool(row,"character_record_observed");});
        boolean attending=bool(row,"target_in_attending_list");if(!bool(row,"character_record_observed")){check("private feast activity target empty record malformed",()->{for(String key:List.of("character_activity_id","character_activity_state_raw","character_record_matches_activity","native_active_attendee"))nil(row,key);});return;}
        long recordId=checked("private feast activity target record malformed",()->number(row,"character_activity_id",BigInteger.ZERO,U32).longValueExact());
        long state=checked("private feast activity target record malformed",()->{long value=number(row,"character_activity_state_raw",BigInteger.ZERO,U32).longValueExact();bool(row,"character_record_matches_activity");bool(row,"native_active_attendee");return value;});
        check("private feast activity target predicate malformed",()->need(bool(row,"character_record_matches_activity")==(recordId==activity)&&bool(row,"native_active_attendee")==(attending&&recordId==activity&&state==2),"activity target copied predicates"));
    }
    private static Target target(JsonNode row,Frame frame,JsonNode args,String envelope) {
        exact(row,FRAME+" activity_key planning_stage status target_status target_character_id selected_status start_gate_status normal_refresh_sequence source_fingerprint active_rule_count filtered_group_count selected_row_count native_filtered_member selected_member planner_join_raw travel_days arrival_raw planned_start_raw positive_join timely_arrival final_can_start authored_rule_membership native_guest_route_qualified read_only advertised"); bind(row,frame,"activity-feast-stage5-guest-target-private-v1"); feast(row,5); yes(row,"read_only"); no(row,"advertised"); nil(row,"authored_rule_membership"); no(row,"native_guest_route_qualified"); long target=id(row,"target_character_id"); need(target==id(args,"target_character_id"),"requested guest target differs");
        String status=row.path("status").asText();if(status.equals("unavailable")){check("private feast target unavailable data malformed",()->{String targetStatus=text(row,"target_status");need(envelope.equals("unavailable")&&(Set.of("observed","target_not_filtered").contains(targetStatus)||CANDIDATE_FAILURES.contains(targetStatus)),"target unavailable status");for(String key:List.of("normal_refresh_sequence","source_fingerprint","active_rule_count","filtered_group_count","selected_row_count","native_filtered_member","selected_member","planner_join_raw","travel_days","arrival_raw","planned_start_raw","positive_join","timely_arrival","final_can_start"))nil(row,key);});return new Target(target,false,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),app(row));}
        String targetStatus=checked("private feast target observed data malformed",()->{eq(row,"status","observed");available(envelope);String value=text(row,"target_status");need(Set.of("observed","target_not_filtered").contains(value),"target observed status");eq(row,"selected_status","observed");eq(row,"start_gate_status","observed");positive(row,"normal_refresh_sequence");fingerprint(row,"source_fingerprint");for(String key:List.of("active_rule_count","filtered_group_count","selected_row_count"))integer(row,key,0,4096);bool(row,"selected_member");bool(row,"final_can_start");return value;});
        boolean filtered=checked(targetStatus.equals("target_not_filtered")?"private feast target absence malformed":"private feast target native value malformed",()->bool(row,"native_filtered_member"));Optional<BigInteger> join=Optional.empty();Optional<Boolean> positiveJoin=Optional.empty(),timely=Optional.empty();
        if(targetStatus.equals("target_not_filtered"))check("private feast target absence malformed",()->{need(!filtered,"nonfiltered target predicate");for(String key:List.of("planner_join_raw","travel_days","arrival_raw","planned_start_raw","positive_join","timely_arrival"))nil(row,key);});
        else {BigInteger amount=checked("private feast target native value malformed",()->{need(filtered,"filtered target predicate");BigInteger value=signed(row,"planner_join_raw");int arrival=integer(row,"arrival_raw",Integer.MIN_VALUE,Integer.MAX_VALUE),start=integer(row,"planned_start_raw",Integer.MIN_VALUE,Integer.MAX_VALUE);integer(row,"travel_days",Integer.MIN_VALUE,Integer.MAX_VALUE);need(bool(row,"positive_join")==(value.signum()>0)&&bool(row,"timely_arrival")== (arrival<=start),"target predicates disagree");return value;});join=Optional.of(amount);positiveJoin=Optional.of(bool(row,"positive_join"));timely=Optional.of(bool(row,"timely_arrival"));}
        return new Target(target,true,Optional.of(bool(row,"selected_member")),Optional.of(filtered),join,positiveJoin,timely,Optional.of(bool(row,"final_can_start")),app(row));
    }
    private static RouteProof route(JsonNode row,Frame frame,String envelope) {
        exact(row,FRAME+" activity_key planning_stage status candidate_status selected_status start_gate_status normal_refresh_sequence source_fingerprint active_rule_count filtered_group_count selected_row_count selected_nonhost_count selected_nonhost_rows positive_join_count timely_positive_join_count final_can_start pre_invitation_candidate candidate_selected_membership authored_rule_membership native_guest_route_qualified read_only advertised"); bind(row,frame,"activity-feast-stage5-guest-route-proof-private-v1"); feast(row,5); yes(row,"read_only"); no(row,"advertised"); nil(row,"authored_rule_membership"); no(row,"native_guest_route_qualified"); String candidateStatus=text(row,"candidate_status"); need(Set.of("observed","no_qualified_candidate").contains(candidateStatus) || CANDIDATE_FAILURES.contains(candidateStatus),"route candidate status"); String selected=text(row,"selected_status"),start=text(row,"start_gate_status"); need(selected.equals("observed")||SELECTED_FAILURES.contains(selected),"route selected status"); need(start.equals("observed")||START_FAILURES.contains(start),"route start status");
        if(row.path("status").asText().equals("unavailable")){check("private feast guest route unavailable data malformed",()->{need(envelope.equals("unavailable"),"route unavailable envelope");for(String key:List.of("normal_refresh_sequence","source_fingerprint","active_rule_count","filtered_group_count","selected_row_count","selected_nonhost_count","positive_join_count","timely_positive_join_count","selected_nonhost_rows","final_can_start","pre_invitation_candidate","candidate_selected_membership"))nil(row,key);});return new RouteProof(false,List.of(),Optional.empty(),Optional.empty(),app(row));}
        check("private feast guest route status malformed",()->{eq(row,"status","observed");available(envelope);});
        check("private feast guest route observed data malformed",()->{need(Set.of("observed","no_qualified_candidate").contains(candidateStatus)&&selected.equals("observed")&&start.equals("observed"),"route observed sources");positive(row,"normal_refresh_sequence");fingerprint(row,"source_fingerprint");for(String key:List.of("active_rule_count","filtered_group_count","selected_row_count"))integer(row,key,0,4096);int count=integer(row,"selected_nonhost_count",0,128),positive=integer(row,"positive_join_count",0,4096),timely=integer(row,"timely_positive_join_count",0,4096);need(timely<=positive&&positive<=count,"route count ordering");JsonNode rows=row.get("selected_nonhost_rows");need(rows.isArray()&&rows.size()==count,"route selected rows count");bool(row,"final_can_start");});
        int positive=integer(row,"positive_join_count",0,4096);JsonNode rows=row.get("selected_nonhost_rows");List<SelectedGuest> result=new ArrayList<>();Set<Long> seen=new HashSet<>();int actualPositive=0;
        for(JsonNode item:rows){SelectedGuest value=checked("private feast guest route selected row malformed",()->{exact(item,"character_id planner_join_raw positive_join predicted_arrival_raw travel_days late");long id=id(item,"character_id");need(seen.add(id),"duplicate route guest");BigInteger join=signed(item,"planner_join_raw");need(bool(item,"positive_join")== (join.signum()>0),"selected join predicate");return new SelectedGuest(id,join,integer(item,"predicted_arrival_raw",Integer.MIN_VALUE,Integer.MAX_VALUE),integer(item,"travel_days",Integer.MIN_VALUE,Integer.MAX_VALUE),bool(item,"late"));});if(value.joinRaw().signum()>0)actualPositive++;result.add(value);}
        if(actualPositive!=positive)throw new MalformedPayload("private feast guest route positive count malformed",null);
        Optional<CandidateRow> candidate=Optional.empty();if(candidateStatus.equals("observed"))candidate=Optional.of(checked("private feast guest route candidate malformed",()->{CandidateRow value=candidateRow(row.get("pre_invitation_candidate"),false);need(!seen.contains(value.characterId()),"pre-invitation candidate already selected");no(row,"candidate_selected_membership");return value;}));
        else check("private feast guest route empty candidate malformed",()->{nil(row,"pre_invitation_candidate");nil(row,"candidate_selected_membership");});
        return new RouteProof(true,result,candidate,Optional.of(bool(row,"final_can_start")),app(row));
    }
    static Rule ruleRead(JsonNode row,Frame frame,String rule,String envelope,boolean activation) {
        allowed(row,FRAME+" activity_key planning_stage status invoked active native_key_hash ordered_rule_count active_rule_count filtered_group_count filtered_character_count","unavailable_reason"); bind(row,frame,"activity-feast-guest-rule-private-v1"); feast(row,5); ActivityJson.rule(rule); String status=text(row,"status"); boolean invoked=bool(row,"invoked"); if(row.has("unavailable_reason") && !row.get("unavailable_reason").isNull()) { String reason=text(row,"unavailable_reason"); need(!reason.isEmpty() && reason.length()<=96 && status.equals("rule_unavailable"),"rule unavailable reason"); }
        Optional<Boolean> active=Optional.empty(); if(Set.of("observed_inactive","observed_active","activated").contains(status)) { boolean value=bool(row,"active"); u64(row,"native_key_hash"); for(String key:List.of("ordered_rule_count","active_rule_count","filtered_group_count","filtered_character_count"))number(row,key,BigInteger.ZERO,U64); active=Optional.of(value);
            String expected=status.equals("observed_inactive")?"available":status.equals("activated")?"activated":"already_active"; need(envelope.equals(expected),"rule envelope status"); need(status.equals("activated") ? activation && invoked && value : !invoked && value==status.equals("observed_active"),"rule invocation/poststate"); }
        else { need(RULE_FAILURES.contains(status) && envelope.equals("unavailable"),"rule unknown status"); for(String key:List.of("active","native_key_hash","ordered_rule_count","active_rule_count","filtered_group_count","filtered_character_count"))nil(row,key); need(activation || !invoked,"read invoked native action"); }
        return new Rule(rule,status,invoked,active,app(row));
    }
    private static RuleProvenance provenance(JsonNode row,Frame frame,JsonNode args,String envelope) {
        exact(row,FRAME+" activity_key planning_stage authored_rule_key rule_status status candidate_character_id rule_active native_key_hash normal_refresh_sequence raw_rule_character_count filtered_rule_character_count candidate_membership filtered_rule_character_ids");bind(row,frame,"activity-feast-guest-rule-provenance-private-v1");feast(row,5);String rule=text(args,"authored_rule_key");ActivityJson.rule(rule);eq(row,"authored_rule_key",rule);long candidate=id(row,"candidate_character_id");need(candidate==id(args,"candidate_character_id"),"provenance candidate binding");String status=checked("private feast rule provenance status malformed",()->text(row,"status"));
        if(status.equals("observed"))return checked("private feast rule provenance observed data malformed",()->{available(envelope);eq(row,"rule_status","observed_active");yes(row,"rule_active");number(row,"native_key_hash",BigInteger.ZERO,U32);positive(row,"normal_refresh_sequence");int rawCount=integer(row,"raw_rule_character_count",0,4096),count=integer(row,"filtered_rule_character_count",0,4096);need(count<=rawCount,"filtered count exceeds source");JsonNode entries=row.get("filtered_rule_character_ids");need(entries.isArray()&&entries.size()==count,"provenance IDs coverage");List<Long> ids=new ArrayList<>();for(JsonNode item:entries)ids.add(org.xar.ck3.control.contracts.StrictJson.integer(item,BigInteger.ONE,U32).longValueExact());boolean membership=bool(row,"candidate_membership");need(membership==ids.contains(candidate),"provenance membership predicate");return new RuleProvenance(rule,candidate,status,Optional.of(membership),Optional.of(ids),app(row));});
        check("private feast rule provenance status malformed",()->need(PROVENANCE_FAILURES.contains(status)&&envelope.equals("unavailable"),"provenance unknown status"));
        check("private feast rule provenance unavailable data malformed",()->{String ruleStatus=text(row,"rule_status");need(Set.of("observed_active","observed_inactive").contains(ruleStatus)||RULE_FAILURES.contains(ruleStatus),"provenance rule status");optionalBoolean(row,"rule_active");for(String key:List.of("native_key_hash","normal_refresh_sequence","raw_rule_character_count","filtered_rule_character_count","candidate_membership","filtered_rule_character_ids"))nil(row,key);});return new RuleProvenance(rule,candidate,status,Optional.empty(),Optional.empty(),app(row));
    }
    private static Inputs inputs(JsonNode row,Frame frame,String envelope) {
        allowed(row,FRAME+" balances hosted_activities read_only advertised activity_key selected_option_key planning_stage scale normal_refresh_sequence final_can_start resources native_guest_route_qualified guest_join_status selected_nonhost_count positive_join_count timely_positive_join_count arrival_time_observed","outcome_values ordinary_guest_route");bind(row,frame,"activity-feast-stage5-start-inputs-private-v1");yes(row,"read_only");no(row,"advertised");available(envelope);
        List<Balance> balances=balances(row.get("balances"));List<HostedActivity> hosted=hostedIds(row.get("hosted_activities"));var outcomes=outcomes(row);
        List<Cost> costs=costs(row.get("resources"),"private feast Start costs malformed","private feast Start cost row malformed");
        String guestStatus=checked("private feast Start inputs malformed",()->{feast(row,5);eq(row,"selected_option_key","feast_type_generic");integer(row,"scale",100000,100000);positive(row,"normal_refresh_sequence");bool(row,"final_can_start");bool(row,"native_guest_route_qualified");bool(row,"arrival_time_observed");String value=text(row,"guest_join_status");need(value.equals("observed")||SELECTED_FAILURES.contains(value),"inputs guest source status");return value;});
        BigInteger refresh=positive(row,"normal_refresh_sequence");boolean selectedQualified=false;
        if(guestStatus.equals("observed"))selectedQualified=checked("private feast guest counts malformed",()->{int total=integer(row,"selected_nonhost_count",0,128),positive=integer(row,"positive_join_count",0,128),timely=integer(row,"timely_positive_join_count",0,128);need(timely<=positive&&positive<=total,"inputs count ordering");yes(row,"arrival_time_observed");return total>0&&timely>0;});
        else check("private feast unavailable guest must remain unknown",()->{for(String key:List.of("selected_nonhost_count","positive_join_count","timely_positive_join_count"))nil(row,key);no(row,"arrival_time_observed");});
        Optional<OrdinaryGuest> ordinary=row.has("ordinary_guest_route")?Optional.of(checked("private feast ordinary guest source malformed",()->ordinary(row.get("ordinary_guest_route"),frame,refresh))):Optional.empty();boolean qualified=bool(row,"native_guest_route_qualified");
        if(ordinary.isPresent()&&qualified!=(selectedQualified||ordinary.orElseThrow().qualified()))throw new MalformedPayload("private feast guest routes disagreed",null);
        return new Inputs(refresh,bool(row,"final_can_start"),qualified,costs,balances,hosted,ordinary,outcomes,app(row));
    }
    private static OrdinaryGuest ordinary(JsonNode row,Frame frame,BigInteger refresh) {
        exact(row,"status authored_rule_key candidate_status rule_status provenance_status rule_active native_key_hash provenance_key_hash provenance_refresh_sequence raw_rule_character_count filtered_rule_character_count candidate_membership candidate qualified"); eq(row,"authored_rule_key","activity_invite_rule_close_family"); String candidateStatus=text(row,"candidate_status"),ruleStatus=text(row,"rule_status"),provenance=text(row,"provenance_status"); need(Set.of("observed","no_qualified_candidate","target_not_filtered").contains(candidateStatus) || CANDIDATE_FAILURES.contains(candidateStatus),"ordinary candidate status"); need(Set.of("observed_active","observed_inactive").contains(ruleStatus) || RULE_FAILURES.contains(ruleStatus),"ordinary rule status"); need(provenance.equals("observed") || PROVENANCE_FAILURES.contains(provenance),"ordinary provenance status");
        need(Set.of("observed","unavailable").contains(text(row,"status")),"ordinary source status");bool(row,"qualified");
        boolean ruleObserved=Set.of("observed_active","observed_inactive").contains(ruleStatus);if(ruleObserved)check("private feast ordinary rule data malformed",()->{need(bool(row,"rule_active")==ruleStatus.equals("observed_active"),"ordinary rule active predicate");number(row,"native_key_hash",BigInteger.ZERO,U32);});else check("private feast ordinary rule unavailable data malformed",()->{nil(row,"rule_active");nil(row,"native_key_hash");});
        boolean membership=false;int filtered=0;if(provenance.equals("observed")){check("private feast ordinary provenance malformed",()->{boolean member=bool(row,"candidate_membership");number(row,"provenance_key_hash",BigInteger.ZERO,U32);positive(row,"provenance_refresh_sequence");int raw=integer(row,"raw_rule_character_count",0,4096),count=integer(row,"filtered_rule_character_count",0,4096);need(count<=raw&&(!member||count>0),"ordinary source counts");});membership=bool(row,"candidate_membership");filtered=integer(row,"filtered_rule_character_count",0,4096);}
        else check("private feast ordinary provenance unavailable data malformed",()->{for(String key:List.of("provenance_key_hash","provenance_refresh_sequence","raw_rule_character_count","filtered_rule_character_count","candidate_membership"))nil(row,key);});
        Optional<CandidateRow> candidate=Optional.empty(); boolean candidateFiltered=false,candidateFresh=false;
        if(candidateStatus.equals("observed")){JsonNode item=row.get("candidate");candidate=Optional.of(checked("private feast ordinary candidate malformed",()->{exact(item,"character_id planner_join_raw travel_days arrival_raw planned_start_raw snapshot_revision date_raw actor_character_id normal_refresh_sequence source_fingerprint native_filtered");need(id(item,"character_id")!=frame.actorId().longValueExact()&&positive(item,"snapshot_revision").equals(frame.nativeRevision())&&number(item,"date_raw",BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)).equals(frame.dateRaw())&&number(item,"actor_character_id",BigInteger.ONE,U32).equals(frame.actorId()),"ordinary candidate frame");fingerprint(item,"source_fingerprint");bool(item,"native_filtered");positive(item,"normal_refresh_sequence");return new CandidateRow(id(item,"character_id"),signed(item,"planner_join_raw"),integer(item,"travel_days",Integer.MIN_VALUE,Integer.MAX_VALUE),integer(item,"arrival_raw",Integer.MIN_VALUE,Integer.MAX_VALUE),integer(item,"planned_start_raw",Integer.MIN_VALUE,Integer.MAX_VALUE));}));candidateFiltered=bool(item,"native_filtered");candidateFresh=positive(item,"normal_refresh_sequence").equals(refresh);}
        else check("private feast ordinary candidate unavailable data malformed",()->nil(row,"candidate"));boolean observed=candidate.isPresent()&&candidateFiltered&&candidateFresh&&ruleStatus.equals("observed_active")&&provenance.equals("observed")&&row.get("native_key_hash").equals(row.get("provenance_key_hash"));boolean qualified=false;
        if(observed) { CandidateRow value=candidate.orElseThrow(); qualified=membership && filtered>0 && value.joinRaw().signum()>0 && value.travelDays()>=0 && value.arrivalRaw()<=value.plannedStartRaw(); }
        if(!text(row,"status").equals(observed?"observed":"unavailable")||bool(row,"qualified")!=qualified)throw new MalformedPayload("private feast ordinary qualification disagreed",null);return new OrdinaryGuest(qualified,candidate,app(row));
    }
    private static Hosted hosted(JsonNode row,Frame frame,String envelope,CompletionCallJournal.Source source) {
        allowed(row,FRAME+" balances hosted_activities read_only advertised","outcome_values native_terminal_observations native_completion_effect_counter_observations"); bind(row,frame,"activity-feast-hosted-post-private-read-v1"); yes(row,"read_only"); no(row,"advertised"); available(envelope);
        Optional<ActivityTerminalJournal.Observation> terminal=Optional.empty(); if(row.has("native_terminal_observations")) { JsonNode journal=row.get("native_terminal_observations"); if(journal.isNull())terminal=Optional.of(new ActivityTerminalJournal.ExplicitNull()); else { try { terminal=Optional.of(new ActivityTerminalJournal.Known(ActivityTerminalJournal.decode(raw(journal).bytes(),frame.actorId().longValueExact()))); } catch(IllegalArgumentException invalid) { terminal=Optional.of(new ActivityTerminalJournal.Rejected(invalid.getMessage(),raw(journal))); } } }
        Optional<JournalObservation> calls=Optional.empty(); if(row.has("native_completion_effect_counter_observations")) { JsonNode journal=row.get("native_completion_effect_counter_observations"); if(journal.isNull())calls=Optional.of(new JournalNull()); else { try { need(source!=null,"actual source needed for CALL journal"); calls=Optional.of(new JournalKnown(CompletionCallJournal.decode(raw(journal).bytes(),source))); } catch(IllegalArgumentException invalid) { calls=Optional.of(new JournalRejected(invalid.getMessage(),raw(journal))); } } }
        return new Hosted(balances(row.get("balances")),hostedIds(row.get("hosted_activities")),outcomes(row),terminal,calls,app(row));
    }
}
