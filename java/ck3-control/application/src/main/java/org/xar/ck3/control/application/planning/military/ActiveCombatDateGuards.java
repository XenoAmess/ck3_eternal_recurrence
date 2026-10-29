package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Exact ordinary wrapper8009..8049, preserving the selected action unless its original hold applies. */
public final class ActiveCombatDateGuards implements OrdinaryPolicy {
    @FunctionalInterface public interface ResumeAnnotator {Obj annotate(PlanningRequest request,Obj originalPlan);}
    @FunctionalInterface public interface DefenderExitObserver {Optional<Obj> observe(PlanningRequest request);}
    private final ExactRef source;
    private final ResumeAnnotator resume;
    private final DefenderExitObserver defender;
    public ActiveCombatDateGuards(ExactRef source,ResumeAnnotator resume,DefenderExitObserver defender) {
        this.source=Objects.requireNonNull(source);this.resume=Objects.requireNonNull(resume);this.defender=Objects.requireNonNull(defender);
        require(source.bytes()>0,"actual active-combat/date guard implementation source required");
    }
    @Override public PlanningStage stage(){return PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS;}
    @Override public ExactRef implementationSource(){return source;}
    @Override public Decision evaluate(PlanningRequest request,Draft previous) {
        Obj detail=Objects.requireNonNull(resume.annotate(request,previous.detail()));
        String originalStep=optionalText(detail.get("selected_step"));
        if(previous.command().isPresent())require(previous.command().orElseThrow().operation().value().equals(originalStep),
                "active combat/date guard plan literal differs from its original selected command");
        boolean held=dateHoldActive(request.observations().snapshot())&&(dateControl(originalStep)||moveControl(originalStep));
        detail=holdControl(detail,request.observations().snapshot());
        // The source physical-inventory verifier has no authenticated native
        // producer and returns false. Do not consume a shaped snapshot flag.
        // Every well-formed route-horizon advance is already a date control
        // under the exact shared parser and was cleared by the preceding hold.
        Optional<Obj> observation=defender.observe(request);
        if(observation.isPresent()) {
            Obj value=observation.orElseThrow();
            if(new Text("native_legality_observed_material_comparison_open").equals(value.get("status"))) {
                String candidate=optionalText(detail.get("selected_step"));
                if(candidate!=null&&(candidate.startsWith("surrender-war-")||candidate.startsWith("offer-white-peace-")))candidate=null;
                value=put(value,"continuation_handoff",obj(f("status",text(candidate==null?"no_tactical_candidate":"existing_tactical_candidate_requires_revalidation")),
                        f("candidate_selected_step",candidate==null?Nil.INSTANCE:text(candidate)),f("current_frame_revalidation_required",new Bool(true)),
                        f("exit_action_authorized",new Bool(false))));
            }
            detail=put(detail,"formal_defender_exit_observation",value);
        }
        String phase=optionalText(detail.get("phase")),reason=optionalText(detail.get("reason"));
        Draft retained=new Draft(previous.policy(),phase==null?previous.phase():phase,reason==null?previous.reason():reason,
                previous.kind(),held?Optional.empty():previous.command(),held?Purpose.READ_ONLY:previous.purpose(),previous.domain(),detail);
        if(held)return new Replace(retained,"original H3937 control guard retained no world action");
        // Annotate is deliberately detail-only in the real pipeline reducer.
        // Source plan labels do not replace the canonical selected draft labels.
        Draft annotated=new Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),previous.purpose(),previous.domain(),detail);
        return new Annotate(annotated,"current combat and exit observations retained with original action");
    }
    public static boolean dateHoldActive(Obj snapshot) {
        if(!new Text("native-29829-2bc2d599f7f9").equals(snapshot.get("episode_run_id")))return false;
        boolean ordinary=snapshot.get("succession_lifecycle") instanceof Obj lifecycle
                &&new Text("ordinary_campaign_succession").equals(lifecycle.get("lifecycle"))
                &&snapshot.get("campaign_goal") instanceof Obj goal&&number(1).equals(goal.get("format_version"))
                &&new Text("dynasty_continuity").equals(goal.get("goal_key"))&&Objects.equals(goal.get("campaign_id"),snapshot.get("episode_run_id"))
                &&snapshot.get("played_character") instanceof Obj actor&&Objects.equals(goal.get("current_character_id"),actor.get("character_id"));
        return !ordinary;
    }
    public static boolean dateControl(String step) {
        return WarHistorySteps.isLifeAdvance(step)||"resume-map".equals(step)
                ||Set.of("committed-route-sentinel-advance","war-objective-hold-sentinel-advance",
                        "set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5").contains(step==null?"":step);
    }
    public static boolean moveControl(String step) {
        return step!=null&&("move-army".equals(step)||step.startsWith("move-army-")
                ||"order-active-combat-retreat-v1".equals(step)||step.startsWith("order-active-combat-retreat-v1-"));
    }
    public static Obj holdControl(Obj plan,Obj snapshot) {
        if(!dateHoldActive(snapshot))return plan;
        String step=optionalText(plan.get("selected_step"));String field,phase,reason;
        if(dateControl(step)) {
            field="date";phase="h3937_war_date_hold_pending_inventory_and_cash_policy";
            reason="the H3937 war episode has no authenticated complete physical hostile inventory or accepted joint war/cash risk policy";
        } else if(moveControl(step)) {
            field="move";phase="h3937_war_move_hold_pending_inventory_and_cash_policy";
            reason="the H3937 war episode has no authenticated complete physical hostile inventory or accepted joint war/cash move risk policy";
        } else return plan;
        return merge(plan,obj(f("phase",text(phase)),f("selected_step",Nil.INSTANCE),f("blocked_"+field+"_step",text(step)),
                f("blocked_"+field+"_phase",nullable(plan.get("phase"))),f("required_observation",text("authenticated-physical-hostile-inventory-and-formal-war-cash-policy")),
                f("reason",text(reason)),f("h3937_"+field+"_hold",dateHoldAudit(snapshot))));
    }
    public static Obj dateHoldAudit(Obj snapshot) {
        Value actor=snapshot.get("played_character") instanceof Obj played?played.get("character_id"):Nil.INSTANCE;
        boolean warPresent=false,armyPresent=false;
        if(snapshot.get("active_wars") instanceof Arr)for(Obj war:rows(snapshot.get("active_wars")))warPresent|=number(16777231).equals(war.get("war_id"));
        if(snapshot.get("player_armies") instanceof Arr)for(Obj army:rows(snapshot.get("player_armies")))armyPresent|=number(83886367).equals(army.get("army_id"));
        return obj(f("episode_run_id",text("native-29829-2bc2d599f7f9")),f("source_actor_character_id",number(29829)),
                f("source_war_id",number(16777231)),f("source_army_id",number(83886367)),f("source_date_raw",number(53219928)),
                f("observed_actor_character_id",nullable(actor)),f("observed_date_raw",nullable(snapshot.get("date_raw"))),
                f("source_actor_matches",new Bool(number(29829).equals(actor))),f("source_war_present",new Bool(warPresent)),
                f("source_army_present",new Bool(armyPresent)),f("source_date_matches",new Bool(number(53219928).equals(snapshot.get("date_raw")))));
    }
}
