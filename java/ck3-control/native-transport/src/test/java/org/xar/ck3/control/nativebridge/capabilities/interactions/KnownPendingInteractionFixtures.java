package org.xar.ck3.control.nativebridge.capabilities.interactions;

import org.xar.ck3.control.contracts.NativeCharacterId;

import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;

/** Synthetic full Native wire, preserving the real source-pin and strict producer/consumer contracts. */
final class KnownPendingInteractionFixtures {
    static final ExactRef SOURCE=new ExactRef("synthetic-known-pending-source",1,"a".repeat(64));
    static final Instant NOW=Instant.parse("2026-10-23T18:00:00Z");
    static final int PENDING=-2_130_706_399,PLAYER=707,SENDER=501,PRISONER=1001;
    private KnownPendingInteractionFixtures() { }
    static Context context() { return context(7,41); }
    static Context context(int revision,int nativeRevision) {
        var identity=new ObservationIdentity("synthetic-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(PLAYER),BigInteger.valueOf(nativeRevision),
                        BigInteger.valueOf(24000)),"frame-"+revision,BigInteger.valueOf(revision),"episode-1"),1);
        return new Context(identity,new G2Source(identity.machineId(),NOW.toString(),"1.20.0.4@sha256:"+Build.CROZIER4.sha256(),SOURCE),
                "held-session",BigInteger.ONE,Build.CROZIER4,NOW.plusSeconds(60),
                new ControlFrame(true,true,true,1,(long)PLAYER,PLAYER,"episode-1",false,
                        new PendingSummary(new PendingId(PENDING),NativeCharacterId.of(SENDER),false),null,List.of()));
    }
    static ObjectNode snapshot(Context c) {
        ObjectNode s=F.objectNode().put("snapshot_id",c.before().frame().snapshotId()).put("revision",c.before().frame().revision())
                .put("native_revision",c.revision()).put("date_raw",c.date()).put("episode_run_id",c.controls().episodeRunId())
                .put("paused",true).put("map_ready",true);
        s.putObject("played_character").put("character_id",c.actor()).put("alive",true);
        s.putObject("played_character_gold").put("raw",100000).put("scale",100000);
        s.putArray("active_wars");s.putArray("player_armies");s.putNull("active_event");s.putNull("current_event");
        s.putObject("pending_character_interaction").put("instance_id",c.controls().pending().instance().value()).put("sender_character_id",c.controls().pending().sender().value()).put("auto_accept_notification",c.controls().pending().autoAcceptNotification());
        s.putObject("diagnostics").put("connection_generation",1).put("bridge_pid",123);
        return s;
    }
    static ObjectNode wire(Context c,String key) {
        ObjectNode result=F.objectNode().put("step",PendingContextCodec.STEP).put("accepted",true).put("status","available")
                .put("query_sequence",1).put("snapshot_revision",c.revision())
                .put("queried_snapshot_id",c.before().frame().snapshotId()).put("queried_revision",c.before().frame().revision())
                .put("queried_native_revision",c.revision());
        ObjectNode n=result.putObject("pending_character_interaction_context").put("schema","pending-character-interaction-context-v1")
                .put("schema_version",1).put("status","available").put("snapshot_revision",c.revision()).put("date_raw",c.date())
                .put("pending_interaction_id",c.controls().pending().instance().value()).putNull("reason");
        n.putObject("build").put("version",c.build().version()).put("exe_sha256",c.build().sha256());
        long hash=key.equals("grant_vassal_interaction")?1_006_648_858L:key.equals("perk_alliance_interaction")?328_040_944L:1_298_930_137L;
        int ordinal=key.equals("grant_vassal_interaction")?277:key.equals("perk_alliance_interaction")?4:17;
        n.putObject("definition").put("canonical_key",key).put("deterministic_key_hash",hash).put("runtime_ordinal",ordinal);
        n.putObject("roles").put("actor_character_id",c.controls().pending().sender().value()).put("recipient_character_id",c.actor())
                .put("secondary_actor_character_id",key.equals("arrange_marriage_interaction")?901:key.equals("grant_vassal_interaction")?902:-1)
                .put("secondary_recipient_character_id",key.equals("arrange_marriage_interaction")?903:key.equals("pay_ransom_interaction")?PRISONER:-1)
                .put("intermediary_character_id",-1);
        n.putObject("target").put("present",false).put("raw_type_index",0).put("raw_16_bytes_hex","0".repeat(32))
                .put("type_key_status","absent").putNull("type_key").putNull("type_key_reason")
                .put("typed_identity_status","absent").putNull("typed_identity").putNull("typed_identity_reason");
        boolean marriage=key.equals("arrange_marriage_interaction"),ransom=key.equals("pay_ransom_interaction");
        int count=marriage?6:ransom?9:key.contains("alliance")?2:0;
        ObjectNode options=n.putObject("send_options").put("exclusive",count==0).put("definition_count",count).put("context_count",count);
        var rows=options.putArray("rows");
        List<String> ransomKeys=List.of("extortionate_gold","extortionate_current_gold","gold","current_gold","favor",
                "influence_send_option","herd_send_option","current_herd","hook");
        for(int i=0;i<count;i++) {
            ObjectNode row=rows.addObject().put("native_index",i).put("numeric_flag_identifier",100+i)
                    .put("selected",ransom&&i==2).put("is_shown",true).put("is_valid",true);
            if(ransom)row.put("canonical_flag_status","available").put("canonical_flag_key",ransomKeys.get(i)).putNull("canonical_flag_reason");
            else row.put("canonical_flag_status","unavailable").putNull("canonical_flag_key").put("canonical_flag_reason","numeric_flag_identifier_string_mapping_not_closed");
        }
        n.putObject("routing").put("kind",0).put("played_character_id",c.actor()).put("current_responder_role","recipient")
                .put("reply_execution_channel","recipient").put("local_route",true).put("auto_accept_notification",false);
        n.putObject("deadline").put("age_days",0).put("expiration_days",60).put("remaining_days",60).put("expiry_boundary_status","not_reached");
        n.putObject("auto_accept").put("status","available").put("value",false).putNull("reason");
        ObjectNode legality=n.putObject("legality");
        for(String action:List.of("accept","reject","block","acknowledge")) {
            boolean allowed=action.equals("accept")||action.equals("reject");
            ObjectNode value=legality.putObject(action).put("status","available").put("allowed",allowed);
            if(allowed)value.putNull("reason");else value.put("reason",action.equals("acknowledge")?"normal_reply_channel":"native_reply_not_allowed");
        }
        ObjectNode terms=n.putObject("terms").put("special_data_present",marriage);
        unknown(terms,"special_war_binding",marriage?"special_interaction_subtype_opaque":"special_war_binding_not_applicable");
        ObjectNode costs=terms.putObject("structured_costs").put("status","available").putNull("reason");
        var values=costs.putObject("value").put("raw_scale",100000).put("payer_role","actor").put("application_timing","on_send")
                .put("pending_payment_state","already_applied").putArray("entries");
        for(String resource:List.of("gold","prestige","piety","renown","influence","herd","treasury","treasury_or_gold","merit","barter_goods"))
            values.addObject().put("resource_key",resource).put("raw",0);
        for(String term:List.of("structured_exchanges","structured_effect_preview","recipient_ai_acceptance_score","recipient_ai_final_decision"))
            unknown(terms,term,term+"_unavailable");
        if(ransom)terms.putObject("ransom_quote").put("status","available").putNull("reason").putObject("value")
                .put("actor_character_id",SENDER).put("jailer_character_id",PLAYER).put("prisoner_character_id",PRISONER)
                .put("selected_option_index",2).put("selected_option_key","gold").put("gold_raw",1250000).put("raw_scale",100000)
                .put("amount_source_key","normal_ransom_cost_value").put("payer_scope","puppet_or_actor").put("receiver_scope","recipient")
                .put("application_timing","on_accept").put("payment_state","pending").put("amount_is_current_quote",true)
                .put("selected_option_shown",true).put("selected_option_valid",true).put("custody_matches_recipient",true)
                .put("hook_selected",false).put("decision_input_ready",true).put("ordinary_gold_decision_ready",true);
        ObjectNode readiness=n.putObject("readiness");
        for(String flag:List.of("stable_definition_ready","roles_ready","target_type_key_ready","target_typed_identity_ready",
                "send_options_ready","routing_ready","deadline_ready","auto_accept_ready","reply_legality_ready","generic_costs_ready","same_frame_ready"))readiness.put(flag,true);
        for(String flag:List.of("special_war_binding_ready","special_outcome_terms_ready","structured_terms_ready","interaction_semantic_decision_ready"))readiness.put(flag,false);
        readiness.putArray("not_ready_reasons").add(marriage?"special_interaction_subtype_opaque":"special_war_binding_not_applicable")
                .add("special_outcome_terms_unavailable").add("structured_exchanges_unavailable").add("structured_effect_preview_unavailable");
        List<String> pinKeys=List.of("backend_id","pending_storage_slot_rva","character_storage_slot_rva","expiration_days_rva",
                "local_routing_predicate_rva","reply_validator_rva","auto_accept_trigger_evaluator_rva","cost_evaluator_rva","common_war_relation_rva",
                "target_type_registry_getter_rva","target_type_registry_rva","script_identifier_name_rva","reply_primary_vtable_rva","reply_secondary_vtable_rva",
                "war_victory_special_vtable_rva","war_white_peace_special_vtable_rva","war_defeat_special_vtable_rva");
        List<String> pins=List.of("ck3-1.20.0.4-native-pending-character-interaction-context-v1","0x5D1EC80","0x5C67568","0x5C68CFC","0x136D190",
                "0x2968470","0x372DF10","0x310CEC0","0x28BC250","0x3795A60","0x54F2AF0","0x3F4F8E0","0x448BC28","0x448BBF8","0x46C3AB0","0x46C3B20","0x46C3B90");
        ObjectNode provenance=n.putObject("provenance");for(int i=0;i<pinKeys.size();i++)provenance.put(pinKeys.get(i),pins.get(i));
        return result;
    }
    private static void unknown(ObjectNode parent,String key,String reason) { parent.putObject(key).put("status","unavailable").putNull("value").put("reason",reason); }
    static Set<OperationKey> steps() { return Set.of(new OperationKey("accept-pending-character-interaction"),
            new OperationKey("reject-pending-character-interaction"),new OperationKey("save-checkpoint")); }
    static PlanningRequest request(Context c,ObjectNode snapshot,ObjectNode wire,Set<OperationKey> steps) {
        ObjectNode row=F.objectNode().put("index",1).put("command",PendingContextCodec.STEP).put("ok",true);row.set("result",wire);
        return new PlanningRequest(c.before(),c.source(),c.sessionId(),c.deadline(),new PlanningObservation(InteractionArguments.app(snapshot),
                List.of(InteractionArguments.app(row)),steps,Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    static KnownPendingInteractionRules.Input input(Context c,ObjectNode snapshot,ObjectNode wire,boolean prisoner) {
        PendingContext decoded=PendingContextCodec.decode(encode(wire),c,c.controls().pending().instance());
        return new KnownPendingInteractionRules.Input(decoded,c,WarExitEvidence.wars(snapshot),KnownPendingInteractionEvidence.warSignature(snapshot),
                prisoner?Optional.of(prisoners(true)):Optional.empty(),Optional.empty(),steps().stream().map(OperationKey::value).collect(java.util.stream.Collectors.toUnmodifiableSet()));
    }
    static ReleaseCollectionProjection12003.Observation prisoners(boolean present) {
        var row=new ReleaseCollectionProjection12003.Row(0,PRISONER,new ReleaseCollectionProjection12003.MeasuredLineage(null,null,false,false),
                new ReleaseCollectionProjection12003.MeasuredChildRelation(false),new ReleaseCollectionProjection12003.MeasuredTitleTier(null),
                new ReleasePreview12003.Unavailable("not_requested"),new NativeKinship12003.Missing());
        return new ReleaseCollectionProjection12003.Observation(ReleaseCollectionProjection12003.SupportedBuild.exact(Build.CROZIER4.version(),Build.CROZIER4.sha256()),
                6,BigInteger.ONE,BigInteger.ONE,0,present?List.of(row):List.of(),"a".repeat(64));
    }
    static PlanningReadPort noReads() { return new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) { throw new AssertionError("unexpected native read"); }
    }; }
}
