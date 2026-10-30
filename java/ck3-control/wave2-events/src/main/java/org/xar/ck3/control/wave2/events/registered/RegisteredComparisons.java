package org.xar.ck3.control.wave2.events.registered;

import org.xar.ck3.control.wave2.events.unhandledevent.EventOptionAvailability;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

/** The existing poet/current-stress and feast/directed-opinion source-reviewed comparators. */
final class RegisteredComparisons {
    private RegisteredComparisons() { }
    record Comparison(BigInteger nativeIndex, ObjectValue option, ObjectValue effect, ObjectValue utility, ObjectValue context) { }
    private static Map<BigInteger,ObjectValue> legal(ObjectValue context) {
        Map<BigInteger,ObjectValue> rows=new LinkedHashMap<>();
        for(Value row:seq(context.get("options"))) if(object(row)&&yes(get(row,"shown"))&&EventOptionAvailability.selectionAllowed(context,obj(row))&&integer(get(row,"native_option_index"))!=null) rows.put(integer(get(row,"native_option_index")),obj(row));
        return rows;
    }
    private static boolean relief(ObjectValue option) {
        Value indicators=option.get("effect_indicators"); List<Value> facets=RegisteredProfiles.stressRows(indicators,"1.20.0.4",true);
        return RegisteredProfiles.indicators(indicators,"1.20.0.4")&&facets.size()==1&&is(get(facets.getFirst(),"direction"),"decrease")&&no(get(facets.getFirst(),"critical"));
    }
    private static boolean journaller(ObjectValue option) {
        return seq(get(option.get("effect_indicators"),"rows")).stream().anyMatch(row->object(row)&&is(get(row,"kind"),"trait")&&is(get(row,"operation"),"add")&&is(get(get(row,"trait"),"status"),"available")&&is(get(get(row,"trait"),"key"),"journaller"));
    }
    static Comparison poet(ObjectValue event,ObjectValue knowledge,Value playedCharacter) {
        Value analysis=knowledge.get("analysis"),sources=get(analysis,"source_sha256");
        if(!(is(event.get("event_definition_key"),"trait_specific.9001")&&is(knowledge.get("ck3_build"),"1.20.0.4")&&is(get(sources,"events/trait_specific_events/trait_specific_events.txt"),"76A50F2B779E085419279801B1396A1C67C8785831E8859FCEC6D0F088853C3A"))) return null;
        Map<BigInteger,ObjectValue> options=legal(event); if(!options.keySet().equals(Set.of(BigInteger.ZERO,BigInteger.ONE,BigInteger.TWO))) return null;
        Value identity=get(event.get("root_scope"),"typed_identity"),stress=get(playedCharacter,"stress_points"); BigInteger amount=integer(stress);
        boolean stressAvailable=object(identity)&&eq(get(playedCharacter,"character_id"),get(identity,"character_id"))&&amount!=null&&amount.signum()>=0;
        Map<BigInteger,Boolean> relief=new LinkedHashMap<>(); options.forEach((index,row)->relief.put(index,relief(row)));
        int selected=0; String reason="retain_one_time_permanent_poet_benefit";
        if(stressAvailable&&amount.compareTo(BigInteger.valueOf(100))>=0&&!relief.get(BigInteger.ZERO)) {
            if(relief.get(BigInteger.ONE)&&journaller(options.get(BigInteger.ONE))) {selected=1;reason="permanent_journaller_and_observed_current_stress_relief";}
            else if(relief.get(BigInteger.TWO)) {selected=2;reason="observed_relief_at_first_break_threshold";}
        }
        String objective=selected==0?"acquire_long_term_poet_trait_from_one_time_event":selected==1?"acquire_long_term_journaller_while_reducing_current_stress":"reduce_current_break_threshold_stress";
        List<Value> alternatives=new ArrayList<>(); int rank=2;
        for(int index=0;index<3;index++) if(index!=selected) alternatives.add(b().set("native_option_index",index).set("rank",rank++).set("reason","lower_priority_under_current_source_and_stress_objective").build());
        ObjectValue utility=b().set("schema","xar.ck3.vanilla-event-campaign-utility").set("schema_version",1).set("selected_native_option_index",selected)
            .set("objective_id",objective).set("comparison_kind","source_reviewed_ordinal").set("selected_rank",1).set("rank_count",3)
            .set("selected_utility",b().set("material_direction","benefit").set("outcome_variance","deterministic_source_effect_with_current_stress_facet").set("persistent_state_risk","none_authored").set("resource_cost","none_authored").set("timeline_value",selected!=2?"permanent_positive_trait":"immediate_stress_relief").build())
            .set("alternatives",arr(alternatives)).set("cross_event_numeric_score",RetainedJson.NULL).set("calibration_status","not_calibrated").set("decision_scope","bounded_timeline_continuation").build();
        Map<String,Value> reliefFields=new LinkedHashMap<>();relief.forEach((index,value)->reliefFields.put(index.toString(),v(value)));
        ObjectValue context=b().set("schema","xar.ck3.poet-long-term-decision-context/v1").set("policy","permanent_trait_or_observed_break_threshold_relief_v1")
            .set("stress_input_available",stressAvailable).set("stress_points",stressAvailable?stress:RetainedJson.NULL)
            .set("at_or_above_first_break_threshold",stressAvailable?v(amount.compareTo(BigInteger.valueOf(100))>=0):RetainedJson.NULL)
            .set("stress_decrease_by_native_index",new ObjectValue(reliefFields)).set("selected_reason",reason).set("stress_magnitude_used",false).set("secondary_fulfillment_direction_used",false).set("generic_semantic_decision_ready",false).build();
        ObjectValue profile=obj(get(analysis,"selected_choice_effect_profile")).with("selected_native_option_index",v(selected));
        if(selected==1) profile=profile.with("selected_option_effects",json("[{\"domain\":\"trait\",\"subject\":\"root\",\"operation\":\"add_trait\",\"trait\":\"journaller\",\"permanent\":true,\"authored_resource_cost\":\"none\"},{\"domain\":\"stress\",\"subject\":\"root\",\"operation\":\"stress_and_fulfillment_impact\",\"loss_condition_trait\":\"content\",\"gain_condition_trait\":\"ambitious\",\"runtime_delta_exact\":false}]"));
        if(selected==2) profile=profile.with("selected_option_effects",json("[{\"domain\":\"stress\",\"subject\":\"root\",\"operation\":\"add_stress\",\"authored_value_key\":\"minor_stress_loss\",\"runtime_delta_exact\":false},{\"domain\":\"stress\",\"subject\":\"root\",\"operation\":\"stress_and_fulfillment_impact\",\"loss_condition_traits\":[\"lazy\",\"fickle\"],\"gain_condition_trait\":\"diligent\",\"runtime_delta_exact\":false}]"));
        if(selected!=0) { List<Value> anchors=new ArrayList<>(seq(profile.get("source_anchors"))); if(anchors.isEmpty()) throw new IllegalArgumentException("reviewed poet source anchors missing"); anchors.set(0,v("events/trait_specific_events/trait_specific_events.txt:1250-1413"));profile=profile.with("source_anchors",arr(anchors)); }
        String trait=selected==0?"lifestyle_poet":"journaller";
        profile=profile.with("observable_postcondition",b().set("metric",selected==2?"played_character.stress_points":"played_character.event_traits."+trait).set("expected_relation",selected==2?"strictly_decreasing":"false_to_true").set("material_change_required_for_evidence",true).build());
        return new Comparison(BigInteger.valueOf(selected),options.get(BigInteger.valueOf(selected)),profile,utility,context);
    }
    private record Opinions(Map<String,BigInteger> values,String reason) { }
    private static Opinions opinions(Value observations,ObjectValue event,ObjectValue knowledge,BigInteger actor,Map<String,BigInteger> fighters) {
        if(nil(observations)) return new Opinions(null,"current_guest_opinion_inputs_missing");
        if(!array(observations)||seq(observations).size()!=2) return new Opinions(null,"current_guest_opinion_pair_unavailable");
        Map<BigInteger,BigInteger> byGuest=new LinkedHashMap<>();
        for(Value row:seq(observations)) {
            if(!object(row)||!is(get(row,"status"),"observed")) return new Opinions(null,"current_guest_opinion_pair_unavailable");
            BigInteger guest=integer(get(row,"guest_character_id")),value=integer(get(row,"guest_opinion_of_actor")); String digest=text(get(row,"exe_sha256"));
            if(!(is(get(row,"schema"),"activity-feast-guest-opinion-private-read-v1")&&guest!=null&&fighters.containsValue(guest)&&!byGuest.containsKey(guest)&&eq(get(row,"actor_character_id"),v(actor))
                &&value!=null&&value.compareTo(BigInteger.valueOf(-100))>=0&&value.compareTo(BigInteger.valueOf(100))<=0&&yes(get(row,"read_only"))&&no(get(row,"raw_pointer_fields_persisted"))
                &&positive(get(row,"snapshot_revision"))&&eq(get(row,"queried_native_revision"),get(row,"snapshot_revision"))&&eq(get(row,"date_raw"),event.get("date_raw"))
                &&eq(get(row,"exact_ck3_build"),knowledge.get("ck3_build"))&&digest!=null&&is(knowledge.get("ck3_exe_sha256"),digest.toUpperCase(java.util.Locale.ROOT))
                &&text(get(row,"queried_snapshot_id"))!=null&&eq(get(row,"post_snapshot_id"),get(row,"queried_snapshot_id")))) return new Opinions(null,"current_guest_opinion_pair_does_not_match_event");
            byGuest.put(guest,value);
        }
        Map<String,BigInteger> result=new LinkedHashMap<>();fighters.forEach((name,id)->result.put(name,byGuest.get(id)));return new Opinions(result,null);
    }
    static Comparison feast(ObjectValue event,ObjectValue knowledge,Value observations) {
        Value analysis=knowledge.get("analysis"),sources=get(analysis,"source_sha256");
        if(!(is(event.get("event_definition_key"),"feast_default.6003")&&Set.of("1.20.0.3","1.20.0.4").contains(str(knowledge.get("ck3_build")))&&is(get(sources,"events/activities/feast_activity/main_events/feast_default_events.txt"),"D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1"))) return null;
        Map<BigInteger,ObjectValue> options=legal(event);if(!options.keySet().equals(Set.of(BigInteger.ZERO,BigInteger.ONE))) return null;
        BigInteger actor=character(event.get("root_scope")); Map<String,Value> scopes=scopes(event);Map<String,BigInteger> fighters=new LinkedHashMap<>();
        for(String name:List.of("fighter_1","fighter_2")) fighters.put(name,character(scopes.get(name)));
        if(actor==null||fighters.values().stream().anyMatch(Objects::isNull)||fighters.get("fighter_1").equals(fighters.get("fighter_2"))||fighters.containsValue(actor)) return null;
        BigInteger selected=integer(get(knowledge.get("contract"),"selected_native_option_index"));if(!options.containsKey(selected)) return null;
        Value effects=get(analysis,"authored_option_effect_profiles"),baseline=get(analysis,"selected_choice_campaign_utility_profile");
        if(!object(effects)||!object(get(effects,"0"))||!object(get(effects,"1"))||!object(baseline)) return null;
        Opinions pair=opinions(observations,event,knowledge,actor,fighters);String reason="retain_source_reviewed_bounded_route_without_current_opinion_pair";
        if(pair.values()!=null) {
            int comparison=pair.values().get("fighter_1").compareTo(pair.values().get("fighter_2"));
            if(comparison<0) {selected=BigInteger.ZERO;reason="support_fighter_1_with_lower_current_opinion_of_player";}
            else if(comparison>0) {selected=BigInteger.ONE;reason="support_fighter_2_with_lower_current_opinion_of_player";}
            else reason="equal_current_opinions_retain_source_reviewed_bounded_route";
        }
        BigInteger opposed=BigInteger.ONE.subtract(selected);
        ObjectValue utility=obj(baseline).with("selected_native_option_index",v(selected)).with("selected_rank",v(1)).with("rank_count",v(2))
            .with("alternatives",arr(b().set("native_option_index",opposed).set("rank",2).set("tradeoff","supports_the_other_fighter_and_opposes_this_side").build())).with("selection_basis",v(reason));
        utility=utility.with("selected_utility",obj(utility.get("selected_utility")).with("material_direction",v("support_fighter_"+selected.add(BigInteger.ONE)+"_and_oppose_fighter_"+opposed.add(BigInteger.ONE))));
        Map<String,Value> fighterRows=new LinkedHashMap<>(),revisionRows=new LinkedHashMap<>();
        for(var row:fighters.entrySet()) fighterRows.put(row.getKey(),b().set("character_id",row.getValue()).set("opinion_of_player",pair.values()==null?RetainedJson.NULL:v(pair.values().get(row.getKey()))).build());
        if(pair.values()!=null) for(Value row:seq(observations)) revisionRows.put(integer(get(row,"guest_character_id")).toString(),get(row,"queried_native_revision"));
        ObjectValue context=b().set("schema","xar.ck3.feast-brawl-current-opinion-context/v1").set("policy","support_lower_current_guest_opinion_v1").set("objective_id",utility.getOrNull("objective_id"))
            .set("comparison_status",pair.values()!=null?"current_inputs_compared":"bounded_fallback").set("current_opinion_inputs_used",pair.values()!=null).set("fallback_reason",pair.reason()).set("selected_reason",reason)
            .set("event_instance_id",event.getOrNull("current_event_instance_id")).set("snapshot_revision",event.getOrNull("snapshot_revision")).set("date_raw",event.getOrNull("date_raw")).set("actor_character_id",actor)
            .set("opinion_query_native_revisions",pair.values()==null?RetainedJson.NULL:new ObjectValue(revisionRows)).set("fighters",new ObjectValue(fighterRows)).set("relationship_identity_used",false).set("predicted_relationship_outcomes",RetainedJson.NULL).set("generic_semantic_decision_ready",false).build();
        return new Comparison(selected,options.get(selected),obj(get(effects,selected.toString())),utility,context);
    }
}
