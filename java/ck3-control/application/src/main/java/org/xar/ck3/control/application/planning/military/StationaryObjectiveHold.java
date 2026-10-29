package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.LateWarCoreInputs.is;
import static org.xar.ck3.control.application.planning.military.CapitalRegroupEligibility.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.military.LateWarCoreInputs.Context;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Execution-only substitution of the already selected ordinary life-advance, strategy19974..20183. */
public final class StationaryObjectiveHold {
    private StationaryObjectiveHold() {}
    public static Optional<MilitaryPlanningDecision> plan(Context c,Obj pursuit) {
        var p=c.published();
        if(!(p.sentinel().enabled()&&advertised(c.request(),"war-objective-hold-sentinel-advance")
                &&is(pursuit,"target_source","war_objective_province")&&is(pursuit,"objective_kind","siege")
                &&Objects.equals(optionalInt(pursuit.get("war_id")),p.tacticalWarId())
                &&Objects.equals(optionalInt(pursuit.get("army_id")),c.subject().id())&&yes(c.snapshot().get("paused"))
                &&yes(c.snapshot().get("map_ready"))&&none(c.snapshot().get("active_event"))&&none(c.snapshot().get("pending_character_interaction"))))return Optional.empty();
        Integer target=optionalInt(pursuit.get("target_province_id"));
        if(target==null||target<=0||!(c.war().get("war_objective_province_ids") instanceof Arr exact)||!ids(exact).contains(target))return Optional.empty();
        List<Obj> player=rows(c.snapshot().get("player_armies"));if(player.isEmpty())return Optional.empty();
        Set<Integer> allIds=new HashSet<>();List<Integer> watched=new ArrayList<>();Army subject=null;
        for(Obj row:player) {
            Army a=army(row);boolean regular=a.state()!=null?"regular".equals(a.state().toLowerCase(Locale.ROOT)):Objects.equals(a.stateCode(),1);
            if(!allIds.add(a.id())||!regular||a.current()==null||a.current()<=0||a.target()!=null||a.route().isEmpty()
                    ||!a.route().orElseThrow().isEmpty()||Boolean.TRUE.equals(a.inCombat())||Boolean.TRUE.equals(a.retreating()))return Optional.empty();
            if(a.controllable())watched.add(a.id());if(a.id()==c.subject().id())subject=a;
        }
        if(watched.isEmpty()||watched.size()>64||subject==null||!subject.controllable()||!Objects.equals(subject.current(),target)||subject.target()!=null)return Optional.empty();
        for(Obj war:wars(c.request())) {
            if(!(war.get("objective_province_states") instanceof Arr states))continue;
            for(Value value:states.items())if(value instanceof Obj state&&state.get("active_siege") instanceof Obj siege&&yes(siege.get("player_army_besieging")))return Optional.empty();
        }
        BigInteger start=c.request().before().frame().identity().dateRaw();Optional<BigInteger> deadline=targetDate(start,p.warSummaries());
        if(deadline.isEmpty())return Optional.empty();
        int speed=p.sentinel().speed();String suffix=speed==3?"":"-speed-"+speed;
        String step="war-objective-hold-sentinel-advance-war-"+p.tacticalWarId()+"-army-"+c.subject().id()+"-at-"+target+"-until-"+deadline.orElseThrow()+suffix;
        String reason="the ordinary planner already selected life-advance for this same WarID, subject and preferred objective; use its speed-"+speed+" native sentinel as a seven-day execution-only substitute without changing the war or target decision";
        Obj baseline=obj(f("phase",text("native_war_pursuit_progress")),f("selected_step",text("life-advance")),f("war_id",number(p.tacticalWarId())),
                f("subject_army_id",number(c.subject().id())),f("objective_province_id",number(target)));
        Obj detail=obj(f("policy",text("one-life-turn-v1")),f("phase",text("native_war_stationary_objective_hold_sentinel")),f("selected_step",text(step)),f("reason",text(reason)),
                f("timeline_policy",text("war_stationary_objective_hold_speed_"+speed)),f("timeline_speed",number(speed)),f("research_high_speed_ab",new Bool(speed>3&&p.sentinel().highSpeedAb())),
                f("sentinel_mode",text("decision_epoch")),f("sentinel_scope",text("stationary_objective_hold")),f("absolute_target_date_raw",number(deadline.orElseThrow())),
                f("watch_army_ids",numbers(watched.stream().sorted().toList())),f("war_id",number(p.tacticalWarId())),f("subject_army_id",number(c.subject().id())),f("objective_province_id",number(target)),
                f("baseline_decision",baseline),f("exact_war_terminal_watch",new Bool(false)),f("exact_active_war_set_watch",new Bool(false)),f("maximum_omitted_state_detection_lag_days",number(7)),
                f("omitted_native_watch_fields",strings(List.of("active_war_set","war_id","war_score","objective_membership","occupation","current_province","army_state"))),
                f("pursuit",pursuit),f("active_wars",objects(p.warSummaries())));
        // This original family advertises its canonical base operation; the exact payload is constructed only after all bindings above.
        return Optional.of(new MilitaryPlanningDecision.Select("one-life-turn-v1","native_war_stationary_objective_hold_sentinel",reason,
                new OperationKey(step),empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,detail));
    }
    public static Optional<BigInteger> targetDate(BigInteger start,List<Obj> summaries) {
        Objects.requireNonNull(start);BigInteger target=start.add(BigInteger.valueOf(7*24));
        for(Obj war:List.copyOf(summaries))for(String field:List.of("war_termination_negative_reuse","war_termination_query_policy_defer"))
            if(war.get(field) instanceof Obj lease) {
                BigInteger expires=optionalInteger(lease.get("expires_date_raw"));if(expires!=null)target=target.min(expires);
            }
        return target.compareTo(start)>0&&target.signum()>0&&target.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0?Optional.of(target):Optional.empty();
    }
}
