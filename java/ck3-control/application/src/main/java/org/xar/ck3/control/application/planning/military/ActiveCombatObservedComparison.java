package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.SCALE;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.fixedDiv;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.mul;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleControlExtensionCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleResponseCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.forecast.ActiveCurrentCounterProjector;
import org.xar.ck3.control.wave2.military.forecast.CombatCore;

/** Observed retention and conditional current-frame damage; never future win odds or a resume model. */
public final class ActiveCombatObservedComparison implements GeneralBattleForecastPolicy.ActiveCombatComparison {
    @Override public Optional<Obj> observe(PlanningRequest request) {
        try {
            Obj snapshot=request.observations().snapshot();Integer subject=optionalInt(snapshot.get("battle_control_snapshot_v1_subject_army_id"));
            BigInteger sequence=optionalInteger(snapshot.get("battle_control_snapshot_v1_query_sequence"));
            if(!request.observations().paused()||subject==null||subject<0||sequence==null||sequence.signum()<=0
                    ||!new Text("available").equals(snapshot.get("battle_control_snapshot_v1_status"))
                    ||!Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_snapshot_id"),snapshot.get("snapshot_id"))
                    ||!Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_revision"),snapshot.get("revision"))
                    ||!Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_native_revision"),snapshot.get("native_revision"))
                    ||armies(request).stream().noneMatch(a->a.id()==subject&&a.controllable()&&"combat".equals(a.tacticalState())))return Optional.empty();
            Obj frame=BattleResponseCodec.normalizeControl(OpportunityJson.object(snapshot.get("battle_control_snapshot_v1"),"active control"),
                    subject,request.before().frame().identity().nativeRevision(),request.before().frame().identity().dateRaw().longValueExact());
            Value rawResume=snapshot.get("active_combat_resume_inputs_v1");
            if(rawResume!=null&&rawResume!=Nil.INSTANCE)BattleControlExtensionCodec.normalizeResume(
                    (ObjectNode)StrictJson.parse(OpportunityJson.encode(OpportunityJson.object(rawResume,"active resume"))),
                    (ObjectNode)StrictJson.parse(OpportunityJson.encode(frame)));
            return compare(frame,rawResume instanceof Obj resume?Optional.of(resume):Optional.empty());
        }catch(IllegalArgumentException|ArithmeticException invalid){return Optional.empty();}
    }
    static Optional<Obj> compare(Obj frame,Optional<Obj> resume) {
        if(!new Text("main").equals(frame.get("phase"))||yes(frame.get("finalized"))||!new Text("none").equals(frame.get("winner_side")))return Optional.empty();
        int own=int32(frame.get("side_index"));require(own==0||own==1,"native side index");
        List<Obj> sides=List.of(OpportunityJson.object(frame.get("attacker"),"attacker"),OpportunityJson.object(frame.get("defender"),"defender"));
        List<BigInteger> starts=new ArrayList<>(),currents=new ArrayList<>(),attacks=new ArrayList<>();
        boolean basis=new Text("full_side").equals(frame.get("side_scope"));BigInteger width=optionalInteger(frame.get("final_combat_width"));basis&=width!=null&&width.signum()>0;
        for(Obj side:sides) {
            List<Obj> entries=new ArrayList<>();entries.addAll(rows(side.get("levy_entries")));entries.addAll(rows(side.get("men_at_arms_entries")));
            List<Obj> fighting=entries.stream().filter(e->yes(e.get("fights_in_main_phase"))).toList();
            BigInteger start=BigInteger.ZERO,current=BigInteger.ZERO,attack=BigInteger.ZERO;
            for(Obj entry:fighting) {
                BigInteger initial=optionalInteger(entry.get("starting_raw")),live=optionalInteger(entry.get("current_fighting_raw")),damage=optionalInteger(entry.get("effective_damage_raw"));
                require(initial!=null&&live!=null,"complete main-phase pool operands required");start=start.add(initial);current=current.add(live);
                if(damage==null||damage.signum()<0)basis=false;else attack=attack.add(mul(damage,live));
            }
            if(start.signum()<=0||start.bitLength()>63||current.signum()<=0||current.compareTo(start)>0)return Optional.empty();
            starts.add(start);currents.add(current);attacks.add(attack);
            int armies=rows(side.get("ordered_armies")).size();
            basis&=yes(side.get("stored_current_matches_derived"))&&armies>0&&armies<=64&&!entries.isEmpty()&&entries.size()<=512;
        }
        BigInteger ownCurrent=currents.get(own),enemyCurrent=currents.get(1-own),ownRetention=fixedDiv(ownCurrent,starts.get(own)),enemyRetention=fixedDiv(enemyCurrent,starts.get(1-own));
        boolean severe=ownCurrent.multiply(BigInteger.TWO).compareTo(enemyCurrent)<=0&&ownRetention.multiply(BigInteger.TWO).compareTo(enemyRetention)<=0;
        Obj neutral=null,counter=null;boolean severeBasis=false;String counterStatus=basis?"current_frame_counter_unavailable":"conditional_damage_basis_unavailable";
        if(basis) {
            List<BigInteger> damages=new ArrayList<>();for(int i=0;i<2;i++)damages.add(CombatCore.outgoingDamageRaw(attacks.get(i),SCALE,width,
                    optionalInteger(sides.get(i).get("stored_current_fighting_raw")),BigInteger.valueOf(3000)));
            BigInteger ownDamage=damages.get(own),enemyDamage=damages.get(1-own);
            neutral=obj(f("status",text("conditional_frozen_day")),f("assumptions",text("neutral_advantage_no_counter_no_participant_refresh")),f("own_outgoing_raw",number(ownDamage)),f("enemy_outgoing_raw",number(enemyDamage)));
            severeBasis=severe(ownDamage,enemyDamage,ownCurrent,enemyCurrent,ownRetention,enemyRetention);
            if(frame.get("active_counter_inputs_v1") instanceof Obj inputs&&new Text("available").equals(inputs.get("status"))) {
                try {
                    var projected=ActiveCurrentCounterProjector.project(StrictJson.parse(OpportunityJson.encode(frame)));List<BigInteger> adjusted=new ArrayList<>();
                    for(int i=0;i<2;i++)adjusted.add(CombatCore.outgoingDamageRaw(projected.attacks().get(i),SCALE,width,optionalInteger(sides.get(i).get("stored_current_fighting_raw")),BigInteger.valueOf(3000)));
                    ownDamage=adjusted.get(own);enemyDamage=adjusted.get(1-own);
                    counter=obj(f("status",text("conditional_frozen_current_frame")),f("assumptions",text("same_frame_counter_neutral_advantage_no_participant_refresh")),
                            f("own_outgoing_raw",number(ownDamage)),f("enemy_outgoing_raw",number(enemyDamage)),
                            f("retention_by_class_raw",new Arr(projected.retentions().stream().<Value>map(row->new Arr(row.stream().<Value>map(MilitaryPlanInputs::number).toList())).toList())),
                            f("next_tick_retention_validated",new Bool(false)));
                    counterStatus="current_frame_counter_projected";severeBasis=severe(ownDamage,enemyDamage,ownCurrent,enemyCurrent,ownRetention,enemyRetention);
                }catch(IllegalArgumentException|ArithmeticException invalid){counterStatus="current_frame_counter_projection_rejected";}
            }
        }
        Value missing=resume.map(r->r.get("missing_required_domains")).orElseGet(()->strings(List.of("selected_commander_next_roll_bounds","active_regiment_counter_class_stack_context","next_day_non_roll_advantage_sources","battle_knight_participation_and_dynamic_entry_transitions")));
        return Optional.of(obj(f("status",text("provisional_observed_comparison")),f("model_fidelity",text(counter!=null?"observed-current-starting-and-conditional-counter-damage-basis":neutral!=null?"observed-current-starting-and-conditional-neutral-damage-basis":"observed-current-and-starting-only")),
                f("whole_battle_win_probability",Nil.INSTANCE),f("combat_id",frame.get("combat_id")),f("province_id",frame.get("province_id")),f("subject_army_id",frame.get("subject_public_cunit_id")),
                f("subject_side_index",number(own)),f("side_scope",frame.get("side_scope")),f("scale",number(SCALE)),f("own_current_fighting_raw",number(ownCurrent)),f("enemy_current_fighting_raw",number(enemyCurrent)),
                f("own_retained_share_raw",number(ownRetention)),f("enemy_retained_share_raw",number(enemyRetention)),f("severe_observed_disadvantage",new Bool(severe)),
                f("neutral_uncountered_damage_basis",nullable(neutral)),f("current_frame_counter_conditioned_damage_basis",nullable(counter)),f("current_frame_counter_basis_status",text(counterStatus)),
                f("severe_conditional_damage_basis_disadvantage",new Bool(severeBasis)),f("severe_conditional_damage_basis_source",counter!=null?text("current_frame_counter"):neutral!=null?text("neutral_uncountered"):Nil.INSTANCE),f("missing_dynamic_domains",missing)));
    }
    private static boolean severe(BigInteger own,BigInteger enemy,BigInteger ownCurrent,BigInteger enemyCurrent,BigInteger ownRetention,BigInteger enemyRetention) {
        return enemy.signum()>0&&own.multiply(BigInteger.TWO).compareTo(enemy)<=0&&ownCurrent.compareTo(enemyCurrent)<=0&&ownRetention.compareTo(enemyRetention)<=0;
    }
}
