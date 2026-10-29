package org.xar.ck3.control.wave2.events.registered;

import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

/** Exact reviewed effects and ordinal utilities; no probability or cross-event score is inferred. */
final class RegisteredProfiles {
    private RegisteredProfiles() { }
    static ObjectValue selectedEffect(ObjectValue knowledge,BigInteger nativeIndex) {
        Value profile=get(knowledge.get("analysis"),"selected_choice_effect_profile");
        return object(profile)&&is(get(profile,"schema"),"xar.ck3.vanilla-event-choice-effect")&&is(get(profile,"schema_version"),1)
            &&eq(get(profile,"selected_native_option_index"),v(nativeIndex))&&array(get(profile,"selected_option_effects"))&&array(get(profile,"common_after_effects")) ? obj(profile) : null;
    }
    static ObjectValue selectedUtility(ObjectValue knowledge,BigInteger nativeIndex) {
        Value profile=get(knowledge.get("analysis"),"selected_choice_campaign_utility_profile");
        BigInteger rank=integer(get(profile,"selected_rank")),count=integer(get(profile,"rank_count"));
        return object(profile)&&is(get(profile,"schema"),"xar.ck3.vanilla-event-campaign-utility")&&is(get(profile,"schema_version"),1)
            &&eq(get(profile,"selected_native_option_index"),v(nativeIndex))&&text(get(profile,"objective_id"))!=null
            &&Set.of("source_reviewed_ordinal","sole_legal_route").contains(str(get(profile,"comparison_kind")))
            &&rank!=null&&count!=null&&rank.signum()>0&&rank.compareTo(count)<=0&&object(get(profile,"selected_utility"))&&array(get(profile,"alternatives"))
            &&nil(get(profile,"cross_event_numeric_score"))&&is(get(profile,"calibration_status"),"not_calibrated") ? obj(profile) : null;
    }
    static boolean stressFacet(Value row,String build) { return object(row)&&(is(get(row,"kind"),"stress")||RegisteredEventKnowledge.migrated(build)&&is(get(row,"kind"),"stress_and_fulfillment")); }
    static List<Value> stressRows(Value indicators,String build,boolean filter) {
        List<Value> rows=seq(get(indicators,"rows")); return filter ? rows.stream().filter(row->stressFacet(row,build)).toList() : rows;
    }
    static boolean indicators(Value indicators,String build) {
        return object(indicators)&&is(get(indicators,"status"),"available")&&is(get(indicators,"coverage"),"played-character-event-icon-indicators-"+build+"-v1")&&no(get(indicators,"complete_effect_set"));
    }
    static ObjectValue epidemic(ObjectValue knowledge,ObjectValue selected,BigInteger index) {
        String build=str(knowledge.get("ck3_build")); Value analysis=knowledge.get("analysis"); boolean migrated=RegisteredEventKnowledge.migrated(build);
        Value review=get(get(analysis,"migration_1_20_0_2"),"definition_review");
        if(migrated&&!seq(get(review,"reviewed_profile_keys")).contains(v("dynamic_stress_indicator_profile"))) return null;
        Value hashes=RegisteredProjection.sourceHashes(analysis),indicators=selected.get("effect_indicators");
        List<Value> rows=stressRows(indicators,build,migrated);
        if(!(BigInteger.TWO.equals(index)&&is(get(hashes,"events/dlc/ce1/epidemic_events.txt"),"FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E")&&indicators(indicators,build)&&array(get(indicators,"rows"))&&rows.size()==1)) return null;
        Value stress=rows.getFirst();
        if(!(stressFacet(stress,build)&&is(get(stress,"direction"),"increase")&&eq(get(stress,"magnitude"),json("{\"status\":\"unavailable\"}"))&&yes(get(stress,"affected_by_trait"))&&get(stress,"critical") instanceof BooleanValue)) return null;
        ObjectValue effect=b().set("domain","player_stress").set("source",migrated?"stress_and_fulfillment_impact":"stress_impact").set("direction","increase").set("binding","selected_option_same_frame_native_indicator").build();
        ObjectValue profile=b().set("schema","xar.ck3.vanilla-event-choice-effect").set("schema_version",1).set("selected_native_option_index",2)
            .set("completeness",migrated?"selected-option-stress-facet-only":"selected-option-source-and-current-indicator-reviewed").set("selected_option_effects",arr(effect)).set("common_after_effects",arr())
            .set("observable_postcondition",json("{\"metric\":\"played_character.stress_points\",\"expected_relation\":\"strictly_increasing\",\"material_change_required_for_evidence\":true}"))
            .set("source_anchors",arr(v("events/dlc/ce1/epidemic_events.txt:"+(migrated?str(get(analysis,"definition_lines")):"6928-6962")))).build();
        return migrated ? profile.with("unobserved_effect_domains",json("[\"spiritual_fulfillment\",\"opinion\",\"relationship\"]")).with("complete_effect_set",v(false)) : profile;
    }
    static ObjectValue stressObservable(ObjectValue knowledge,ObjectValue selected,BigInteger nativeIndex,ObjectValue profile) {
        String build=str(knowledge.get("ck3_build")),key=str(knowledge.get("event_definition_key")); String direction,relation;
        if(key.equals("death_management.1007")&&BigInteger.ZERO.equals(nativeIndex)) { direction="increase";relation="non_decreasing"; }
        else if(key.equals("tgp_travel_events.0030")&&BigInteger.ONE.equals(nativeIndex)) { direction="decrease";relation="non_increasing"; }
        else return profile;
        if(!RegisteredEventKnowledge.migrated(build)||profile==null) return profile;
        Value indicators=selected.get("effect_indicators");List<Value> facets=stressRows(indicators,build,true);
        if(!indicators(indicators,build)||facets.size()!=1||!is(get(facets.getFirst(),"direction"),direction)) return profile;
        return profile.with("completeness",v("selected-option-stress-facet-only")).with("complete_effect_set",v(false))
            .with("observable_postcondition",b().set("metric","played_character.stress_points").set("expected_relation",relation).set("material_change_required_for_evidence",true).build())
            .with("observation_binding",b().set("source","selected_option_same_frame_native_indicator").set("indicator_kind",get(facets.getFirst(),"kind")).set("stress_direction",direction).set("secondary_fulfillment_direction_used",false).build());
    }
    static boolean japanIndicator(ObjectValue selected,String build) {
        Value indicators=get(selected,"effect_indicators"); List<Value> rows=stressRows(indicators,build,RegisteredEventKnowledge.migrated(build));
        if(!indicators(indicators,build)||rows.size()!=1) return false; Value stress=rows.getFirst();
        return stressFacet(stress,build)&&is(get(stress,"direction"),"decrease")&&eq(get(stress,"magnitude"),json("{\"status\":\"unavailable\"}"))&&yes(get(stress,"affected_by_trait"))&&no(get(stress,"critical"));
    }
}
