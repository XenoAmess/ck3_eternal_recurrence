package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.LateWarCoreInputs.is;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.military.LateWarCoreInputs.Context;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Exact original admission predicates, strategy16318..16717. A positive result opens a native preview, never a move. */
public final class CapitalRegroupEligibility {
    private CapitalRegroupEligibility() {}
    static boolean none(Value value) {return value==null||value==Nil.INSTANCE;}
    static Obj object(Value value) {return value instanceof Obj o?o:empty();}
    static boolean quiet(Context c) {
        Obj s=c.snapshot();return yes(s.get("paused"))&&yes(s.get("map_ready"))&&none(s.get("active_event"))
                &&none(s.get("pending_character_interaction"))&&wars(c.request()).size()==1;
    }
    static boolean liveScore(Obj war) {
        Integer score=optionalInt(war.get("player_relative_war_score"));return score!=null&&score>-100&&score<100;
    }
    static boolean idle(Army army,boolean explicitFalse) {
        return "regular".equals(army.tacticalState())&&(explicitFalse?Boolean.FALSE.equals(army.inCombat()):!Boolean.TRUE.equals(army.inCombat()))
                &&(explicitFalse?Boolean.FALSE.equals(army.retreating()):!Boolean.TRUE.equals(army.retreating()))
                &&army.target()==null&&army.route().isPresent()&&army.route().orElseThrow().isEmpty();
    }
    private static boolean allObservedEnemies(Context c,boolean targetsRequired) {
        return !c.enemies().isEmpty()&&c.enemies().size()<=64&&c.enemies().stream().allMatch(a->a.current()!=null
                &&a.route().isPresent()&&(!targetsRequired||a.moveTargetPresent()));
    }
    public static boolean insufficientSiege(Context c) {
        var p=c.published();Obj s=c.snapshot();Army a=c.subject();
        if(!(quiet(c)&&is(c.war(),"player_side","attacker")&&yes(c.war().get("player_is_primary_war_leader"))
                &&c.controlled().size()==1&&p.rankedExactObjectives().equals(List.of(c.current()))
                &&p.exactSiegeRejection().filter(r->is(r,"status","insufficient_strength")).isPresent()
                &&List.of("war_objective_occupation_supported","war_objective_garrison_supported",
                    "war_objective_siege_progress_supported","war_objective_assault_supported").stream().allMatch(k->yes(s.get(k)))
                &&"sieging".equals(a.tacticalState())&&!Boolean.TRUE.equals(a.inCombat())&&!Boolean.TRUE.equals(a.retreating())
                &&a.moveTargetPresent()&&a.target()==null&&a.route().isPresent()&&a.route().orElseThrow().isEmpty()))return false;
        if(!(c.war().get("objective_province_states") instanceof Arr states)||states.items().size()!=1
                ||!(states.items().getFirst() instanceof Obj state))return false;
        if(!(Objects.equals(optionalInt(state.get("province_id")),c.current())&&yes(state.get("occupation_observable"))
                &&no(state.get("is_occupied"))&&yes(state.get("siege_observable"))&&state.get("active_siege") instanceof Obj siege))return false;
        return optionalInt(siege.get("siege_id"))!=null&&Objects.equals(optionalInt(siege.get("besieging_army_id")),a.id())
                &&yes(siege.get("player_army_besieging"))&&yes(siege.get("assault_observable"))&&no(siege.get("assault_in_progress"))
                &&Objects.equals(optionalInt(state.get("besieging_strength")),399)&&Objects.equals(optionalInt(state.get("garrison_size")),400)
                &&allObservedEnemies(c,true);
    }
    public static boolean defeatedAttackerAtCapital(Context c,List<Obj> rejected) {
        var exact=c.published().rankedExactObjectives();Integer score=optionalInt(c.war().get("player_relative_war_score"));
        if(!(quiet(c)&&is(c.war(),"player_side","attacker")&&yes(c.war().get("player_is_primary_war_leader"))
                &&score!=null&&score<0&&!exact.isEmpty()&&!exact.contains(c.current())&&!c.controlled().isEmpty()
                &&c.controlled().size()<=64&&c.controlled().stream().allMatch(a->Objects.equals(a.current(),c.current())&&idle(a,false))))return false;
        Set<Integer> rejectedIds=new HashSet<>();
        for(Obj r:rejected)if(is(r,"status","blocked")||is(r,"status","unavailable")&&is(r,"reason","route_does_not_reach_target"))
            rejectedIds.add(optionalInt(r.get("target_province_id")));
        return rejectedIds.containsAll(exact)&&!c.enemies().isEmpty()&&c.enemies().stream().allMatch(a->exact.contains(a.current())
                &&!Boolean.TRUE.equals(a.inCombat())&&!Boolean.TRUE.equals(a.retreating()));
    }
    public static boolean nonleaderAttacker(Context c,List<Integer> candidates,List<Obj> rejected) {
        Obj player=object(c.snapshot().get("played_character"));Army a=c.subject();
        if(!(quiet(c)&&c.contactSupported()&&is(c.war(),"player_side","attacker")&&no(c.war().get("player_is_primary_war_leader"))
                &&liveScore(c.war())&&optionalInt(player.get("character_id"))!=null&&yes(player.get("alive"))
                &&c.controlled().size()==1&&!candidates.isEmpty()&&rejected.size()==candidates.size()
                &&Objects.equals(optionalInt(player.get("character_id")),a.owner())&&a.controllable()&&idle(a,false)))return false;
        Set<Integer> ids=new HashSet<>();
        for(Obj r:rejected) {
            Integer target=optionalInt(r.get("target_province_id"));Obj h=object(r.get("contact_horizon"));
            if(!(is(r,"status","unsafe")&&is(r,"native_contact_veto","one_day_contact_not_free")&&is(h,"status","available")
                    &&no(h.get("one_day_contact_free"))&&target!=null&&Objects.equals(optionalInt(h.get("target_province_id")),target)))return false;
            ids.add(target);
        }
        return ids.equals(new HashSet<>(candidates));
    }
    public static boolean coalitionAttacker(Context c,List<Obj> rejected) {
        Obj w=c.war();Army a=c.subject();
        if(!(quiet(c)&&is(w,"player_side","attacker")&&w.get("player_is_primary_war_leader") instanceof Bool&&liveScore(w)
                &&!c.controlled().isEmpty()&&c.controlled().size()<=64&&!rejected.isEmpty()
                &&rejected.stream().anyMatch(r->is(r,"status","unsafe")||is(r,"status","blocked"))))return false;
        List<Army> subjects=c.controlled().stream().filter(x->Objects.equals(x.current(),c.current())&&x.id()==a.id()
                &&Set.of("regular","moving","sieging","embarked").contains(x.tacticalState()==null?"":x.tacticalState())
                &&!Boolean.TRUE.equals(x.inCombat())&&!Boolean.TRUE.equals(x.retreating())).toList();
        Obj player=object(c.snapshot().get("played_character"));
        boolean embarked=subjects.size()==1&&c.routeUnsafe()&&yes(player.get("alive"))&&Objects.equals(a.owner(),optionalInt(player.get("character_id")))
                &&a.controllable()&&"embarked".equals(a.tacticalState())&&"complete_nonempty".equals(a.routeReadStatus())
                &&a.route().isPresent()&&!a.route().orElseThrow().isEmpty()&&Objects.equals(a.route().orElseThrow().getLast(),a.target());
        return subjects.size()==1&&(embarked||c.balance().filter(Balance::hostileOvermatch).isPresent())
                &&c.controlled().stream().allMatch(x->!Boolean.TRUE.equals(x.inCombat())&&!Boolean.TRUE.equals(x.retreating()));
    }
    public static boolean outnumberedPrimaryDefender(Context c,List<Integer> candidates,List<Obj> rejected) {
        Army a=c.subject();
        if(!(quiet(c)&&is(c.war(),"player_side","defender")&&yes(c.war().get("player_is_primary_war_leader"))&&liveScore(c.war())
                &&c.controlled().size()==1&&c.balance().filter(Balance::hostileOvermatch).isPresent()&&c.routeUnsafe()&&!candidates.isEmpty()))return false;
        Set<Integer> ids=new HashSet<>();for(Obj r:rejected)if(is(r,"status","blocked")||is(r,"status","unsafe"))ids.add(optionalInt(r.get("target_province_id")));
        return ids.containsAll(candidates)&&ids.contains(a.target())&&"moving".equals(a.tacticalState())&&!Boolean.TRUE.equals(a.inCombat())
                &&!Boolean.TRUE.equals(a.retreating())&&a.route().isPresent()&&!a.route().orElseThrow().isEmpty()
                &&Objects.equals(a.route().orElseThrow().getLast(),a.target())&&allObservedEnemies(c,false);
    }
}
