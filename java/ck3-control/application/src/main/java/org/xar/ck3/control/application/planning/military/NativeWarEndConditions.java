package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import org.xar.ck3.control.contracts.StrictJson;

/** Current native exit facts; this projection neither selects an exit nor manufactures a recipient answer. */
public final class NativeWarEndConditions {
    private NativeWarEndConditions() { }
    public static Obj assess(Obj war, Obj sameFrameOptions) {
        Integer score=optionalInt(war.get("player_relative_war_score")); boolean primary=yes(war.get("player_is_primary_war_leader"));
        Obj result=obj(f("schema_version",number(1)),f("war_id",nullable(war.get("war_id"))),f("player_side",nullable(war.get("player_side"))),
                f("player_relative_war_score",score==null?Nil.INSTANCE:number(score)),f("status",text("current_options_not_published")),
                f("native_options",Nil.INSTANCE),f("native_nonloss_exit_available",Nil.INSTANCE),f("ordinary_war_input",Nil.INSTANCE),
                f("existing_score_victory_candidate",new Bool(primary&&score!=null&&score>=100)),f("required_native_input",Nil.INSTANCE));
        if(sameFrameOptions==null||!(sameFrameOptions.get("options") instanceof Obj raw))return result;
        Map<String,Value> values=new LinkedHashMap<>();
        for(String name:List.of("surrender","white_peace","victory")) {
            if(!(raw.get(name) instanceof Obj option))return result;
            Obj response=option.get("recipient_response") instanceof Obj row?row:null;
            values.put(name,withRoles(obj(f("outcome",nullable(option.get("outcome"))),f("context_constructed",booleanOrNull(option.get("context_constructed"))),
                    f("native_validator_passed",booleanOrNull(option.get("native_validator_passed"))),f("available",booleanOrNull(option.get("available"))),
                    f("ai_acceptance",nullable(option.get("ai_acceptance"))),f("auto_accept",booleanOrNull(option.get("auto_accept"))),
                    f("recipient_response_status",response==null?Nil.INSTANCE:nullable(response.get("status"))),
                    f("recipient_would_accept_now",response!=null&&is(response,"status","available")?booleanOrNull(response.get("would_accept_now")):Nil.INSTANCE)),option));
        }
        Obj nativeOptions=new Obj(values);Obj victory=(Obj)nativeOptions.get("victory"),white=(Obj)nativeOptions.get("white_peace");
        Value nonloss=victory.get("available") instanceof Bool v&&white.get("available") instanceof Bool w?new Bool(v.value()||w.value()):Nil.INSTANCE;
        String input=primary&&score!=null&&score>=100?"existing_score_victory_policy":primary&&score!=null&&score<=-100?"existing_terminal_defeat_policy":
                yes(nonloss)?"review_existing_exit_policy":no(nonloss)?"continue_war":"native_option_legality_unavailable";
        return merge(result,obj(f("status",text("current_native_conditions_observed")),f("war_duration_days",nullable(sameFrameOptions.get("war_duration_days"))),
                f("active_casus_belli_identity",nullable(sameFrameOptions.get("active_casus_belli_identity"))),f("cb_allows_white_peace",nullable(sameFrameOptions.get("cb_allows_white_peace"))),
                f("native_options",nativeOptions),f("native_nonloss_exit_available",nonloss),f("ordinary_war_input",text(input)),
                f("required_native_input",yes(white.get("available"))&&white.get("recipient_would_accept_now")==Nil.INSTANCE?text("current_white_peace_recipient_response"):Nil.INSTANCE)));
    }
    public static boolean sameFrame(Obj snapshot,Obj row,int warId) {
        Obj diagnostics=snapshot.get("diagnostics") instanceof Obj value?value:empty();
        return Objects.equals(optionalInt(row.get("war_id")),warId)
                &&equalPresent(row,"queried_snapshot_id",snapshot,"snapshot_id")&&equalPresent(row,"queried_revision",snapshot,"revision")
                &&equalPresent(row,"queried_native_revision",snapshot,"native_revision")
                &&equalPresent(row,"queried_connection_generation",diagnostics,"connection_generation")
                &&equalPresent(row,"episode_run_id",snapshot,"episode_run_id");
    }
    /** Actual strategy9092..9126,9701..9838 summary; every row remains in the source active-war order. */
    public static List<Obj> summaries(PlanningRequest request) { return summaries(request.observations().snapshot(),wars(request)); }
    public static List<Obj> summaries(Obj snapshot,List<Obj> activeWars) {
        List<Obj> options=rows(snapshot.get("war_termination_options"));
        Map<Integer,Obj> latestOptions=byWar(options),terms=byWar(rows(snapshot.get("war_termination_terms")));
        Map<Integer,Obj> exit=byWar(rows(snapshot.get("war_termination_exit_terms")).stream().filter(row->is(row,"status","available")
                &&row.get("readiness") instanceof Obj ready&&yes(ready.get("exit_terms_ready"))).toList());
        List<Obj> result=new ArrayList<>();
        for(Obj war:List.copyOf(activeWars)) {
            Integer warId=optionalInt(war.get("war_id"));require(warId!=null&&warId>0,"actual full WarID required for summary");
            List<Field> fields=new ArrayList<>();for(String name:BASE)fields.add(f(name,nullable(war.get(name))));
            Obj current=options.stream().filter(row->sameFrame(snapshot,row,warId)).findFirst().orElse(null);
            Obj summary=put(obj(fields.toArray(Field[]::new)),"native_end_conditions",assess(war,current));
            Obj termination=latestOptions.get(warId),terminationTerms=terms.get(warId),exitTerms=exit.get(warId);
            if(termination!=null) {
                Obj raw=termination.get("options") instanceof Obj row?row:empty();
                Map<String,Value> legal=new LinkedHashMap<>(),evidence=new LinkedHashMap<>();List<Obj> constructed=new ArrayList<>();
                for(var entry:raw.members().entrySet())if(entry.getValue() instanceof Obj option) {
                    legal.put(entry.getKey(),nullable(option.get("available")));List<Field> projection=new ArrayList<>();
                    for(String name:EVIDENCE)projection.add(f(name,nullable(option.get(name))));
                    evidence.put(entry.getKey(),withRoles(obj(projection.toArray(Field[]::new)),option));
                    if(yes(option.get("context_constructed")))constructed.add(option);
                }
                boolean termsComplete=exitTerms!=null||!constructed.isEmpty()&&constructed.stream().allMatch(row->yes(row.get("terms_observable")));
                boolean acceptanceComplete=!constructed.isEmpty()&&constructed.stream().allMatch(row->yes(row.get("ai_acceptance_observable"))&&yes(row.get("auto_accept_observable")));
                List<String> missing=new ArrayList<>(List.of("campaign_outcome_forecast"));
                if(exitTerms==null||!(exitTerms.get("primary_resource_balances") instanceof Obj))missing.add("primary_resource_balances");
                if(!termsComplete)missing.add("termination_terms");if(!acceptanceComplete)missing.add("opponent_acceptance");
                List<Field> eu=new ArrayList<>();for(String key:List.of("war_duration_days","attacker_war_score","defender_war_score","war_score_breakdown","active_casus_belli_identity"))eu.add(f(key,nullable(termination.get(key))));
                eu.add(f("structured_exit_terms",exitTerms==null?Nil.INSTANCE:exitTerms));eu.add(f("legal_options",new Obj(legal)));eu.add(f("option_evidence",new Obj(evidence)));
                String reason=exitTerms!=null?"native legality, acceptance, and structured exit terms including current primary resource balances are complete; full campaign expected-utility comparison still lacks campaign outcomes while the existing minimal end rules remain independent":
                        "native termination legality, score, and per-option acceptance evidence are projected for expected-utility evaluation; full campaign comparison still lacks CB-specific terms and campaign outcomes while existing minimal end rules remain independent";
                summary=put(summary,"war_termination_options",termination);
                if(terminationTerms!=null)summary=put(summary,"war_termination_terms",terminationTerms);if(exitTerms!=null)summary=put(summary,"war_termination_exit_terms",exitTerms);
                summary=put(summary,"war_exit_assessment",obj(f("status",text("evidence_partial")),f("reason",text(reason)),f("eu_inputs",obj(eu.toArray(Field[]::new))),
                        f("unknown_fields",new Arr(missing.stream().<Value>map(Text::new).toList())),f("automatic_termination_enabled",new Bool(false)),
                        f("automatic_termination_scope",text("full_campaign_expected_utility"))));
            } else if(is(summary,"player_side","defender"))summary=put(summary,"war_exit_assessment",obj(f("status",text("unavailable")),
                    f("reason",text("the bridge does not yet publish complete termination terms, opponent acceptance, or a campaign outcome forecast; do not infer surrender value from war score")),
                    f("required_capabilities",new Arr(List.of(text("game.command.query-war-termination-options-N"),text("game.forecast.campaign-outcomes-v1"))))));
            result.add(summary);
        }
        return List.copyOf(result);
    }
    private static Obj withRoles(Obj target,Obj source) {
        NativeInteractionRoles roles=NativeInteractionRoles.fromOption(OpportunityJson.toNode(source));
        if(roles instanceof NativeInteractionRoles.LegacyWithoutRoles)return target;
        return put(target,NativeInteractionRoles.FIELD,OpportunityJson.parse(StrictJson.canonical(NativeInteractionRoles.toJson(roles))));
    }
    private static Map<Integer,Obj> byWar(List<Obj> rows) {
        Map<Integer,Obj> result=new LinkedHashMap<>();for(Obj row:rows){Integer id=optionalInt(row.get("war_id"));if(id!=null)result.put(id,row);}return result;
    }
    private static boolean equalPresent(Obj first,String a,Obj second,String b) {return first.get(a)!=null&&second.get(b)!=null&&first.get(a).equals(second.get(b));}
    private static Value booleanOrNull(Value value) {return value instanceof Bool?value:Nil.INSTANCE;}
    private static boolean is(Obj value,String field,String token) {return new Text(token).equals(value.get(field));}
    private static final List<String> BASE=List.of("war_id","player_side","primary_opponent_character_id","player_is_primary_war_leader","enemy_primary_default_raise_province_id","player_relative_war_score","war_termination_negative_reuse");
    private static final List<String> EVIDENCE=List.of("outcome","available","terms_observable","terms","ai_acceptance_observable","ai_acceptance","auto_accept_observable","auto_accept","recipient_response");
}
