package org.xar.ck3.control.application.planning.warentry;

import static org.xar.ck3.control.application.planning.warentry.WarEntryJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;

/** Conservative historical canaries and the actual player-claim production selector. */
public final class WarEntryCandidates {
    public static final String CLAIM_RULE="feudal-adjacent-independent-county-player-claim-forecast-candidate-v1";
    public static final String DE_JURE_RULE="feudal-single-county-de-jure-forecast-candidate-v1";
    // These are the original strategy canary identities, not a claim about today's installed vanilla bytes.
    private static final String CLAIM_SHA="D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1";
    private static final String DE_JURE_SHA="D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE";
    private WarEntryCandidates() { }
    public static String typedStep(Obj declaration) {
        String id=text(get(declaration,"declaration_id"));if(id==null)return null;
        try{return DeclarationContract.buildStep(id).wire();}catch(IllegalArgumentException invalid){return null;}
    }
    public static String assessmentStep(BigInteger target) {return target!=null && target.signum()>0 && target.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0?"query-war-entry-assessments-v1-1-"+target:null;}
    private static boolean oneTitle(Obj row) {List<Value> titles=array(row.get("target_title_ids"));return row.get("target_title_ids") instanceof Arr && titles.size()==1 && positive(titles.getFirst());}
    public static List<Obj> playerClaims(List<Obj> declarations,BigInteger actor) {
        if(actor==null || actor.signum()<=0)return List.of();
        return declarations.stream().filter(row->is(row.get("source"),"native") && is(row.get("casus_belli_key"),"claim_cb") && actor.equals(number(row,"claimant_character_id")) && row.get("declaration_id") instanceof Text && number(row,"target_character_id")!=null && oneTitle(row))
                .sorted(Comparator.comparing((Obj row)->required(row,"target_character_id")).thenComparing(row->text(row.get("declaration_id")))).toList();
    }
    public static boolean claimScopeReady(Obj root) {Obj readiness=child(root,"readiness");return yes(get(readiness,"adjacent_external_province_holders_ready")) && yes(get(readiness,"related_character_contexts_ready"));}
    public static List<Obj> adjacentClaims(List<Obj> declarations,Obj root) {
        if(!claimScopeReady(root) || !(get(root,"adjacent_external_province_holder_character_ids") instanceof Arr) || !(get(root,"related_character_contexts") instanceof Arr))return List.of();
        Set<BigInteger> adjacent=array(root.get("adjacent_external_province_holder_character_ids")).stream().filter(WarEntryJson::positive).map(WarEntryJson::integer).collect(java.util.stream.Collectors.toSet());
        Map<BigInteger,BigInteger> countyTargets=new LinkedHashMap<>();
        for(Obj context:objects(root.get("related_character_contexts"))) {BigInteger target=number(context,"character_id");Obj title=child(context,"primary_title");if(target!=null && adjacent.contains(target) && is(context.get("relationship_role"),"adjacent_external_province_holder") && yes(context.get("independent")) && eq(get(title,"tier_raw"),2) && is(get(title,"tier_key"),"county") && positive(get(title,"title_id")))countyTargets.put(target,number(title,"title_id"));}
        return declarations.stream().filter(row->array(row.get("target_title_ids")).getFirst().equals(new IntegerValue(countyTargets.getOrDefault(required(row,"target_character_id"),BigInteger.valueOf(-1))))).toList();
    }
    static boolean feudal(Obj root,boolean requireFlag) {Obj government=child(root,"government");return is(get(government,"key"),"feudal_government") && (!requireFlag || array(get(government,"flags")).stream().anyMatch(value->is(value,"government_is_feudal")));}
    static boolean economic(Obj root,boolean noFactions) {BigInteger size=number(root,"player_domain_size"),limit=number(root,"player_domain_limit");Obj income=child(root,"player_monthly_gold_income");return (!noFactions || eq(get(root,"player_targeting_faction_count"),0)) && size!=null && limit!=null && size.compareTo(limit)<=0 && eq(get(income,"scale"),100000) && positive(get(income,"raw"));}
    public static Obj deJure(Obj declaration,Obj assessment,Obj root,Set<String> steps,boolean peace) {
        List<String> blockers=new ArrayList<>();if(!peace)blockers.add("active_war_blocks_conservative_entry");
        if(!(is(declaration.get("source"),"native") && is(declaration.get("casus_belli_key"),"individual_county_de_jure_cb") && eq(declaration.get("configuration_index"),-1) && eq(declaration.get("claimant_character_id"),-1) && oneTitle(declaration)))blockers.add("declaration_outside_single_county_de_jure_slice");
        if(!feudal(root,true))blockers.add("same_frame_standard_feudal_scope_unavailable");if(!economic(root,true))blockers.add("same_frame_peacetime_budget_scope_not_conservative");
        if(assessment==null)blockers.add("same_frame_native_power_assessment_unavailable");else {
            boolean valid=same(assessment.get("target_character_id"),declaration.get("target_character_id")) && same(assessment.get("effective_target_character_id"),declaration.get("target_character_id")) && positive(assessment.get("actor_power_base_raw")) && positive(assessment.get("target_power_total_raw")) && eq(assessment.get("actor_network_contribution_raw"),0) && same(assessment.get("actor_power_total_raw"),assessment.get("actor_power_base_raw")) && eq(assessment.get("target_network_contribution_raw"),0) && same(assessment.get("target_pre_adjustment_total_raw"),assessment.get("target_power_base_raw")) && eq(assessment.get("target_adjustment_delta_raw"),0) && same(assessment.get("target_power_total_raw"),assessment.get("target_pre_adjustment_total_raw")) && eq(assessment.get("distance_raw"),0) && positive(assessment.get("actual_power_ratio_raw"));
            if(!valid)blockers.add("native_de_jure_candidate_scope_not_met");
        }
        String step=typedStep(declaration);
        return obj().text("status",blockers.isEmpty()?"forecast_required":"blocked").text("rule_id",DE_JURE_RULE).value("selected_step",null).text("typed_declaration_step",step).bool("typed_declaration_available",step!=null && steps.contains(step)).value("blockers",strings(blockers)).text("source","common/casus_belli_types/00_dejure_war.txt").text("source_sha256",DE_JURE_SHA).value("native_actual_power_ratio_raw",get(assessment,"actual_power_ratio_raw")).build();
    }
    private record Claim(Obj declaration,Obj assessment,String step) { }
    public static Obj claim(List<Obj> declarations,Map<BigInteger,Obj> assessments,Obj root,Set<String> steps,boolean peace) {
        List<String> global=new ArrayList<>();if(!peace)global.add("active_war_blocks_player_claim_entry");
        if(!yes(get(root,"independent")) || !feudal(root,true))global.add("same_frame_independent_feudal_scope_unavailable");
        if(!economic(root,true))global.add("same_frame_peacetime_budget_scope_not_conservative");
        List<Obj> blocked=new ArrayList<>();List<Claim> admitted=new ArrayList<>();
        for(Obj declaration:declarations) {
            BigInteger target=required(declaration,"target_character_id");Obj assessment=assessments.get(target);List<String> blockers=new ArrayList<>(global);
            if(assessment==null)blockers.add("same_frame_native_power_assessment_unavailable");
            else if(!completeClaimPower(assessment,target))blockers.add("native_complete_power_assessment_invalid");
            String step=typedStep(declaration);if(step==null)step="";
            if(!blockers.isEmpty())blocked.add(obj().value("declaration_id",declaration.get("declaration_id")).number("target_character_id",target).value("blockers",strings(blockers)).build());else admitted.add(new Claim(declaration,assessment,step));
        }
        Builder result=obj().text("status",admitted.isEmpty()?"blocked":"forecast_required").text("rule_id",CLAIM_RULE).value("selected_step",null).value("candidate_blockers",rows(blocked)).text("source","common/casus_belli_types/00_claim.txt").text("source_sha256",CLAIM_SHA);
        if(admitted.isEmpty())return result.build();
        Claim selected=admitted.stream().min(Comparator.comparing((Claim c)->required(c.assessment(),"actual_power_ratio_raw")).thenComparing(c->required(c.assessment(),"target_power_total_raw")).thenComparing(c->required(c.assessment(),"distance_raw")).thenComparing(c->required(c.declaration(),"target_character_id")).thenComparing(c->text(c.declaration().get("declaration_id")))).orElseThrow();
        return result.text("typed_declaration_step",selected.step()).bool("typed_declaration_available",steps.contains(selected.step())).value("declaration",selected.declaration()).value("assessment",selected.assessment()).value("native_actual_power_ratio_raw",selected.assessment().get("actual_power_ratio_raw")).number("eligible_candidate_count",admitted.size()).build();
    }
    private static boolean completeClaimPower(Obj a,BigInteger target) {return target.equals(number(a,"target_character_id")) && target.equals(number(a,"effective_target_character_id")) && positive(a.get("actor_power_total_raw")) && required(a,"actor_power_total_raw").equals(required(a,"actor_power_base_raw").add(required(a,"actor_network_contribution_raw"))) && positive(a.get("target_power_total_raw")) && required(a,"target_pre_adjustment_total_raw").equals(required(a,"target_power_base_raw").add(required(a,"target_network_contribution_raw"))) && required(a,"target_power_total_raw").equals(required(a,"target_pre_adjustment_total_raw").add(required(a,"target_adjustment_delta_raw"))) && positive(a.get("actual_power_ratio_raw"));}
    public static Obj powerProjection(Obj a) {
        List<String> missing=new ArrayList<>(List.of("participant_arrival_bounds","combat_forecast","campaign_cost","exit_assessment","calibrated_utility_policy"));
        if(a==null) {missing.addFirst("native_power_assessment");return obj().text("status","power_assessment_required").bool("native_power_component_ready",false).value("eu_lower_raw",null).value("missing_components",strings(missing)).bool("automatic_declaration_enabled",false).build();}
        BigInteger actor=required(a,"actor_power_base_raw"),total=required(a,"actor_power_total_raw"),target=required(a,"target_power_total_raw"),an=required(a,"actor_network_contribution_raw").max(BigInteger.ZERO),tn=required(a,"target_network_contribution_raw").max(BigInteger.ZERO),margin=actor.subtract(target),ratio=required(a,"actual_power_ratio_raw"),distance=required(a,"distance_raw");
        Obj component=obj().number("scale",100000).number("actual_power_ratio_raw",ratio).number("actor_power_base_raw",actor).number("actor_power_total_raw",total).number("target_power_total_raw",target).number("native_total_power_margin_raw",total.subtract(target)).number("conservative_self_power_margin_raw",margin).number("actor_network_dependency_raw",an).number("target_network_support_raw",tn).number("distance_raw",distance).value("risk_order_key",numbers(List.of(margin.negate().max(BigInteger.ZERO),ratio,an,tn,target,distance))).build();
        return obj().text("status","native_power_component_ready").bool("native_power_component_ready",true).value("native_power_component",component).value("eu_lower_raw",null).value("missing_components",strings(missing)).bool("automatic_declaration_enabled",false).build();
    }
}
