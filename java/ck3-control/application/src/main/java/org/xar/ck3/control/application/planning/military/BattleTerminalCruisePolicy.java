package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure migration of battle_terminal_cruise_policy.py; observations never grant live qualification. */
public final class BattleTerminalCruisePolicy {
    private BattleTerminalCruisePolicy() { }
    public record Context(boolean paused,boolean mapReady,boolean activeEvent,boolean pendingInteraction,
            List<Integer> controlled,List<Integer> watched,Optional<BigInteger> targetDate,
            boolean speedFiveAvailable,boolean sentinelImplemented,boolean sentinelLiveReady,
            boolean overwhelmingMatrixLiveReady,int dominanceMultiplier) {
        public Context {
            controlled=List.copyOf(controlled);watched=List.copyOf(watched);Objects.requireNonNull(targetDate);
            require(dominanceMultiplier>=2,"integer dominance multiplier >= 2 required");
        }
    }
    public record Assessment(boolean candidateReady,boolean researchRunReady,boolean productionReady,Obj document) {
        public Assessment {Objects.requireNonNull(document);require(!productionReady||researchRunReady,"production requires research admission");}
    }
    public static Assessment assess(Obj frame,Context context) {
        Objects.requireNonNull(frame);Objects.requireNonNull(context);
        List<String> candidate=new ArrayList<>(),run=new ArrayList<>(),production=new ArrayList<>();
        BigInteger start=null;String kind=null,ownRole=null,enemyRole=null;BigInteger ownCurrent=null,enemyCurrent=null,ownStrength=null,enemyStrength=null;
        Boolean currentFloor=null,strengthFloor=null;
        if(!yes(frame.get("battle_control_ready")))candidate.add("battle_control_frame_not_ready");
        else if((start=optionalInteger(frame.get("observed_date_raw")))==null)candidate.add("battle_observed_date_unavailable");
        if(candidate.isEmpty()) {
            Integer side=optionalInt(frame.get("side_index"));
            if(Integer.valueOf(0).equals(side)){ownRole="attacker";enemyRole="defender";}
            else if(Integer.valueOf(1).equals(side)){ownRole="defender";enemyRole="attacker";}
            else candidate.add("player_battle_side_unavailable");
            String phase=optionalText(frame.get("phase")),winner=optionalText(frame.get("winner_side"));
            if(yes(frame.get("finalized"))||"done".equals(phase))candidate.add("battle_already_terminal");
            else if(!"maneuver".equals(phase)&&!"main".equals(phase)&&!"pursuit".equals(phase))candidate.add("battle_phase_not_cruise_eligible");
            if(("maneuver".equals(phase)||"main".equals(phase))&&!"none".equals(winner))candidate.add("preterminal_winner_state_changed");
            else if("pursuit".equals(phase)) {
                if(!"attacker".equals(winner)&&!"defender".equals(winner))candidate.add("pursuit_winner_unavailable");
                else if(ownRole!=null&&!winner.equals(ownRole))candidate.add("pursuit_player_not_winner");
            }
            if(ownRole!=null&&frame.get(ownRole) instanceof Obj own&&frame.get(enemyRole) instanceof Obj enemy) {
                ownCurrent=nonnegative(own.get("derived_current_fighting_raw"));enemyCurrent=nonnegative(enemy.get("derived_current_fighting_raw"));
                ownStrength=nonnegative(own.get("side_strength_raw"));enemyStrength=nonnegative(enemy.get("side_strength_raw"));
                if(ownCurrent==null||enemyCurrent==null||ownStrength==null||enemyStrength==null)candidate.add("battle_side_metrics_unavailable");
            }else if(ownRole!=null)candidate.add("battle_side_metrics_unavailable");
            if(candidate.isEmpty()) {
                if("pursuit".equals(phase))kind="pursuit_cleanup";
                else if(ownCurrent.signum()>0&&enemyCurrent.signum()==0)kind="opponent_fighting_pool_exhausted";
                else {
                    BigInteger multiplier=BigInteger.valueOf(context.dominanceMultiplier());
                    currentFloor=enemyCurrent.signum()>0&&ownCurrent.compareTo(enemyCurrent.multiply(multiplier))>=0;
                    strengthFloor=enemyStrength.signum()>0&&ownStrength.compareTo(enemyStrength.multiply(multiplier))>=0;
                    if(!currentFloor)candidate.add("current_fighting_dominance_not_met");
                    if(!strengthFloor)candidate.add("side_strength_dominance_not_met");
                    if(candidate.isEmpty())kind="double_dominance_hold";
                }
            }
        }
        boolean watch=validUnits(context.controlled())&&validUnits(context.watched())&&!context.controlled().isEmpty()
                &&new HashSet<>(context.controlled()).equals(new HashSet<>(context.watched()));
        if(!context.paused())run.add("paused_prearm_frame_required");if(!context.mapReady())run.add("map_ready_prearm_frame_required");
        if(context.activeEvent())run.add("active_event_requires_decision");if(context.pendingInteraction())run.add("pending_interaction_requires_decision");
        BigInteger target=context.targetDate().orElse(null),elapsed=null;
        if(start==null||target==null||target.compareTo(start)<=0||!target.subtract(start).mod(BigInteger.valueOf(24)).equals(BigInteger.ZERO))run.add("positive_whole_day_absolute_target_required");
        else elapsed=target.subtract(start).divide(BigInteger.valueOf(24));
        if(!watch)run.add("all_controllable_armies_must_be_watched");if(!context.speedFiveAvailable())run.add("speed_5_unavailable");
        if(!context.sentinelImplemented())run.add("terminal_sentinel_not_implemented");
        boolean overwhelming="double_dominance_hold".equals(kind)||"opponent_fighting_pool_exhausted".equals(kind);
        if(!context.sentinelLiveReady())production.add("terminal_sentinel_live_matrix_pending");
        if(overwhelming&&!context.overwhelmingMatrixLiveReady())production.add("overwhelming_checkpoint_matrix_pending");
        boolean candidateReady=candidate.isEmpty(),research=candidateReady&&run.isEmpty(),ready=research&&production.isEmpty();
        Obj doc=obj(f("policy_version",text("battle-terminal-cruise-research-v1")),f("candidate_ready",new Bool(candidateReady)),
                f("research_run_ready",new Bool(research)),f("production_ready",new Bool(ready)),f("candidate_kind",nullableText(kind)),
                f("overwhelming_matrix_required",new Bool(overwhelming)),f("selected_action",research?text("run_speed_5_until_terminal_or_sentinel"):Nil.INSTANCE),
                f("sentinel_mode",research?text("terminal"):Nil.INSTANCE),f("requested_speed",research?number(5):Nil.INSTANCE),
                f("dominance_multiplier",number(context.dominanceMultiplier())),f("player_role",nullableText(ownRole)),f("opponent_role",nullableText(enemyRole)),
                f("player_current_fighting_raw",nullableNumber(ownCurrent)),f("opponent_current_fighting_raw",nullableNumber(enemyCurrent)),
                f("current_fighting_ratio_floor_met",nullableBool(currentFloor)),f("player_side_strength_raw",nullableNumber(ownStrength)),
                f("opponent_side_strength_raw",nullableNumber(enemyStrength)),f("side_strength_ratio_floor_met",nullableBool(strengthFloor)),
                f("all_controllable_army_ids",numbers(context.controlled().stream().sorted().toList())),f("watched_army_ids",numbers(context.watched().stream().sorted().toList())),
                f("watch_set_complete",new Bool(watch)),f("start_date_raw",nullableNumber(start)),f("absolute_target_date_raw",nullableNumber(target)),
                f("absolute_target_elapsed_days",nullableNumber(elapsed)),f("candidate_blockers",strings(candidate)),f("run_blockers",strings(run)),f("production_blockers",strings(production)),
                f("expected_external_intermediate_pause_count",research?number(0):Nil.INSTANCE),f("post_stop_rule",research?text("terminal/removal -> terminal journal query; any other sentinel reason -> one paused rich query and replan"):Nil.INSTANCE));
        return new Assessment(candidateReady,research,ready,doc);
    }
    private static boolean validUnits(List<Integer> ids){return ids.stream().allMatch(id->id>=0)&&new HashSet<>(ids).size()==ids.size();}
    private static BigInteger nonnegative(Value value){BigInteger n=optionalInteger(value);return n!=null&&n.signum()>=0?n:null;}
    private static Value nullableText(String value){return value==null?Nil.INSTANCE:text(value);}
    private static Value nullableNumber(BigInteger value){return value==null?Nil.INSTANCE:number(value);}
    private static Value nullableBool(Boolean value){return value==null?Nil.INSTANCE:new Bool(value);}
}
