package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.military.forecast.FixedContactForecast;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** The actual qualified/provisional consumers of one source-bound combat input; neither is a forecast producer substitute. */
public final class SiegeForecastAssessments {
    private SiegeForecastAssessments() { }
    public static final int PROVISIONAL_TRIALS=512, PROVISIONAL_HORIZON_DAYS=120;
    private static final String V2_EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String V3_EXE="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    public static boolean verifiedVanilla(Obj snapshot) {
        if(!(snapshot.get("diagnostics") instanceof Obj diagnostics)||!(diagnostics.get("hello") instanceof Obj hello)
                ||!yes(hello.get("ck3_build_match"))||!new Text("1.20.0.4").equals(hello.get("expected_ck3_version"))
                ||!(hello.get("expected_ck3_sha256") instanceof Text sha)||!sha.value().toUpperCase(Locale.ROOT).equals(V2_EXE))return false;
        try {return SuccessionLifecycleCodec.decode(OpportunityJson.encode(snapshot.get("succession_lifecycle"))).profile()
                ==SuccessionLifecycleBinding.Profile.ORDINARY_VERIFIED_MOD_ABSENCE;}
        catch(IllegalArgumentException invalid){return false;}
    }
    public static Obj provisional(Obj snapshot,CombatRequest encounter,BigInteger friendlyCurrent,
            CombatObservationCache.Observation observation) {
        Objects.requireNonNull(snapshot);Objects.requireNonNull(encounter);Objects.requireNonNull(friendlyCurrent);Objects.requireNonNull(observation);
        require(observation.request().equals(encounter),"provisional actual cache encounter differs");
        boolean v2=observation.version()==CombatObservationCache.Version.V2;
        Obj lifecycle=snapshot.get("succession_lifecycle") instanceof Obj row?row:empty();
        boolean legacy=new Text("ordinary_campaign_succession").equals(lifecycle.get("lifecycle"))&&new Text("xar_off").equals(lifecycle.get("xar_enabled"));
        boolean vanilla=verifiedVanilla(snapshot);
        Obj diagnostics=snapshot.get("diagnostics") instanceof Obj row?row:empty();
        Obj hello=diagnostics.get("hello") instanceof Obj row?row:empty();
        if(!yes(hello.get("ck3_build_match"))||!new Text(v2?V2_EXE:V3_EXE).equals(hello.get("expected_ck3_sha256"))||!(legacy||vanilla))return status("exact_build_or_profile_unavailable");
        Obj normalized=DriverJson.object(observation.normalizedJson().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);
        Obj base=v2?normalized:normalized.get("base_inputs") instanceof Obj row?row:null;
        Obj completeness=normalized.get("completeness") instanceof Obj row?row:null;
        Obj scenario=base!=null&&base.get("scenario") instanceof Obj row?row:null;
        Obj baseComplete=base!=null&&base.get("completeness") instanceof Obj row?row:null;
        boolean ready=completeness!=null&&(yes(completeness.get("input_observation_ready"))||!v2&&new Text("production_exact_132_refs").equals(normalized.get("contract_stage"))&&baseComplete!=null&&yes(baseComplete.get("input_observation_ready")));
        if(!ready||base==null||scenario==null||!number(encounter.targetProvinceId()).equals(base.get("target_province_id"))
                ||!Objects.equals(encounter.attackerEntryProvinceId()==null?Nil.INSTANCE:number(encounter.attackerEntryProvinceId()),scenario.get("attacker_entry_province_id"))
                ||!numbers(encounter.attackerArmyIds()).equals(scenario.get("attacker_army_ids"))||!numbers(encounter.defenderArmyIds()).equals(scenario.get("defender_army_ids"))
                ||!new Text("player_or_allied").equals(scenario.get("attacker_side"))||!new Text("enemy").equals(scenario.get("defender_side"))
                ||!no(scenario.get("actual_route_dependency"))||encounter.defenderArmyIds().isEmpty()||friendlyCurrent.signum()<=0)return status("same_frame_encounter_scope_mismatch");
        var forecast=observation.forecast(PROVISIONAL_TRIALS,PROVISIONAL_HORIZON_DAYS);
        Obj result=OpportunityJson.object(OpportunityJson.parse(forecast.toJson().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)),"actual forecast");
        if(!new Text("estimated").equals(result.get("status")))return obj(f("status",text("research_trial_unavailable")),f("model_status",nullable(result.get("status"))));
        var admission=FixedContactForecast.contactAdmission(forecast,true);
        Obj admitted=OpportunityJson.object(OpportunityJson.parse(admission.toJson().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)),"actual defensive contact admission");
        BigInteger budget=friendlyCurrent.multiply(BigInteger.valueOf(100_000)).multiply(BigInteger.valueOf(20)).divide(BigInteger.valueOf(100));
        BigInteger hard=optionalInteger(result.get("player_p90_hard_loss_raw"));
        boolean allowed=admission.admitted()&&hard!=null&&hard.compareTo(budget)<=0;
        boolean multi=encounter.defenderArmyIds().size()>1,research=vanilla&&!legacy;
        Obj output=obj(f("status",text(multi?"multi_defender_research_only":research?"vanilla_profile_research_only":allowed?"provisional_admissible":"model_risk_budget_exceeded")),
                f("model_fidelity",text("research_only_phase_events_disabled")),f("calibrated_win_probability_available",new Bool(false)));
        if(multi||research)output=put(output,"planner_usable",new Bool(false));
        for(String field:List.of("input_sha256","advantage_input","simulator_build","sample_count","player_wins","player_losses","no_resolution"))output=put(output,field,nullable(result.get(field)));
        Obj wilson=result.get("resolved_win_wilson95") instanceof Obj row?row:empty();
        Obj identity=empty();for(String key:List.of("episode_run_id","snapshot_id","revision","native_revision","date_raw"))identity=put(identity,key,nullable(snapshot.get(key)));
        return merge(output,obj(f("model_resolved_win_wilson_low",nullable(wilson.get("lower"))),f("model_p90_hard_loss_raw",hard==null?Nil.INSTANCE:number(hard)),
                f("hard_loss_budget_raw",number(budget)),f("model_stack_wipe_fraction",nullable(result.get("player_stack_wipe_probability"))),
                f("model_character_death_fraction",nullable(result.get("commander_or_knight_death_probability"))),f("unmodeled_domains",nullable(result.get("missing_required_domains"))),
                f("contact_admission",admitted),f("observation_identity",identity)));
    }
    public static Obj qualified(Obj snapshot,int warId,int armyId,int target,int entry,List<Integer> defenders,boolean contactSafe) {
        if(!(snapshot.get("combat_entry_eu_v1") instanceof Obj payload))return status("producer_unavailable");
        if(!(payload.get("identity") instanceof Obj identity))return status("identity_unavailable");
        Obj frame=empty();for(String key:List.of("episode_run_id","snapshot_id","revision","native_revision"))frame=put(frame,key,nullable(snapshot.get(key)));
        if(!frame.equals(identity.get("observation"))||!frame.equals(identity.get("forecast"))||!number(warId).equals(identity.get("war_id"))
                ||!number(target).equals(identity.get("target_province_id"))||!number(entry).equals(identity.get("entry_province_id"))
                ||!numbers(List.of(armyId)).equals(identity.get("player_ordered_army_ids"))||!numbers(defenders).equals(identity.get("opponent_ordered_army_ids")))return status("encounter_identity_mismatch");
        Obj assessment;
        try {assessment=CombatEntryEuContract.assess(payload,snapshot.get("combat_entry_action_components_v1"));}
        catch(IllegalArgumentException invalid){return status("contract_invalid");}
        Obj result=obj(f("status",text("contract_blocked")),f("assessment_sha256",nullable(assessment.get("assessment_sha256"))),f("contract_status",nullable(assessment.get("status"))),
                f("blockers",nullable(assessment.get("blockers"))),f("action_components_ready",assessment.members().containsKey("action_components_ready")?assessment.get("action_components_ready"):new Bool(false)),
                f("candidate_action",nullable(assessment.get("candidate_action"))));
        if(!CombatEntryEuContract.ACTIVATION_ENABLED||!contactSafe||!new Text(CombatEntryEuContract.CONTRACT_SHA256).equals(assessment.get("contract_sha256"))
                ||!yes(assessment.get("external_inputs_ready"))||!yes(assessment.get("automatic_attack_enabled"))||!new Text("selected").equals(assessment.get("decision_status"))
                ||!new Text("attack").equals(assessment.get("selected_action")))return result;
        if(!(payload.get("utility_policy") instanceof Obj policy)||!(payload.get("distribution") instanceof Obj distribution)||!(payload.get("character_tails") instanceof Obj tails)
                ||!(policy.get("risk_constraints") instanceof Obj risk)||!(distribution.get("resolved_win_wilson95") instanceof Obj wilson))return result;
        BigInteger low=optionalInteger(wilson.get("low_raw")),wipe=optionalInteger(distribution.get("player_stack_wipe_probability_raw")),catastrophe=optionalInteger(tails.get("player_one_life_catastrophic_probability_raw"));
        BigInteger attack=optionalInteger(assessment.get("eu_attack_raw")),avoid=optionalInteger(assessment.get("eu_avoid_raw")),wait=optionalInteger(assessment.get("eu_wait_reinforce_raw")),margin=optionalInteger(assessment.get("attack_margin_raw")),minimum=optionalInteger(policy.get("minimum_attack_margin_raw"));
        if(low==null||wipe==null||catastrophe==null||attack==null||avoid==null||wait==null||margin==null||minimum==null)return result;
        if(low.compareTo(OpportunityJson.integer(risk.get("min_resolved_win_wilson_low_raw"),"Wilson floor"))<0||wipe.compareTo(OpportunityJson.integer(risk.get("max_player_stack_wipe_probability_raw"),"wipe limit"))>0
                ||catastrophe.compareTo(OpportunityJson.integer(risk.get("max_player_one_life_catastrophic_probability_raw"),"catastrophe limit"))>0
                ||!margin.equals(attack.subtract(avoid.max(wait)))||margin.compareTo(minimum)<=0)return result;
        Obj experiment=OpportunityJson.object(payload.get("experiment"),"qualified experiment");
        return obj(f("status",text("ready")),f("assessment_sha256",assessment.get("assessment_sha256")),f("simulator_version",experiment.get("simulator_version")),f("simulator_sha256",experiment.get("simulator_sha256")),
                f("player_win_probability_raw",distribution.get("player_win_probability_raw")),f("resolved_win_wilson95_low_raw",number(low)),f("player_stack_wipe_probability_raw",number(wipe)),
                f("player_one_life_catastrophic_probability_raw",number(catastrophe)),f("eu_attack_raw",number(attack)),f("eu_avoid_raw",number(avoid)),f("eu_wait_reinforce_raw",number(wait)),f("attack_margin_raw",number(margin)));
    }
    private static Obj status(String value) {return obj(f("status",text(value)));}
}
