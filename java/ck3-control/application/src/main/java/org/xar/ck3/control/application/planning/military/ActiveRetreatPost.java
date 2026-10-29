package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal.Order;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal.SourceFrame;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Scope;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Independent current Army+original Combat lifecycle consumer. ACK is deliberately absent. */
public final class ActiveRetreatPost {
    private ActiveRetreatPost() {}
    public sealed interface Result permits Pending,Observed {Obj json();}
    public record Pending(String reason,List<Obj> affected,boolean terminalQueryRequired) implements Result {
        public Pending {Objects.requireNonNull(reason);affected=List.copyOf(affected);}
        @Override public Obj json(){return merge(base(),obj(f("reason",text(reason)),f("affected",objects(affected)),f("terminal_query_required",new Bool(terminalQueryRequired))));}
    }
    public record Observed(Scope scope,SourceFrame after,List<Obj> affected,Value terminalEventSequence) implements Result {
        public Observed {Objects.requireNonNull(scope);Objects.requireNonNull(after);affected=List.copyOf(affected);Objects.requireNonNull(terminalEventSequence);}
        @Override public Obj json(){return merge(base(),obj(f("status",text("operational_retreat_observed")),f("operational_retreat_verified",new Bool(true)),
                f("scope",text(scope.wire())),f("affected",objects(affected)),f("post_public_revision",number(after.revision())),
                f("post_native_revision",number(after.nativeRevision())),f("terminal_event_sequence",terminalEventSequence)));}
    }
    private static Obj base(){return obj(f("status",text("independent_post_pending")),f("operational_retreat_verified",new Bool(false)),
            f("command_causation_verified",new Bool(false)),f("replay_allowed",new Bool(false)),f("war_outcome_verified",new Bool(false)));}
    /** Receives the shared full normalized DTO. Its native decoder and receipt guard remain mandatory upstream. */
    public static Result transition(Order intent,Obj snapshot,Obj normalizedTransition) {
        if(!current(intent,snapshot))return pending("independent_same_episode_current_post_required");
        SourceFrame frame=SourceFrame.read(snapshot);var args=intent.arguments();
        if(!number(args.expectedCombatId()).equals(normalizedTransition.get("combat_id"))
                ||!number(frame.nativeRevision()).equals(normalizedTransition.get("snapshot_revision"))
                ||!number(frame.dateRaw()).equals(normalizedTransition.get("observed_date_raw")))return pending("transition_full_CombatID_or_current_frame_differs");
        if(!new Text("available").equals(normalizedTransition.get("status")))
            return new Pending("original_combat_not_available_requires_existing_terminal_query",List.of(),true);
        List<Obj> affected=affected(intent,snapshot);
        if(affected.stream().anyMatch(row->!yes(row.get("retreat_target_route_observed")) ))return new Pending("affected_retreat_target_route_not_independently_complete",affected,false);
        boolean lifecycle;
        if(args.expectedScope()==Scope.OWNER_SUBSET) {
            String field=(args.expectedSideIndex()==0?"attacker":"defender")+"_public_cunit_ids_in_stored_order";
            List<Integer> members=ids(normalizedTransition.get(field));Set<Integer> unique=new HashSet<>(members);
            require(unique.size()==members.size(),"transition stored-order roster contains duplicate public CUnits");
            lifecycle=intent.affectedInStoredOrder().stream().noneMatch(unique::contains)&&unique.containsAll(intent.unaffectedInStoredOrder());
        }else lifecycle=number(1-args.expectedSideIndex()).equals(normalizedTransition.get("winner_raw"))
                &&Set.of("pursuit","done").contains(optionalText(normalizedTransition.get("phase")));
        if(!lifecycle)return new Pending("scope_lifecycle_or_real_reinforcement_reopen_requires_observation",affected,false);
        return new Observed(args.expectedScope(),frame,affected,Nil.INSTANCE);
    }
    public static Result terminal(Order intent,Obj snapshot,Obj normalizedTerminal) {
        if(!current(intent,snapshot))return pending("independent_same_episode_current_post_required");
        var args=intent.arguments();SourceFrame after=SourceFrame.read(snapshot);
        if(args.expectedScope()!=Scope.FULL_SIDE)return pending("removed_owner_subset_retains_existing_lifecycle_reader");
        if(!number(args.expectedCombatId()).equals(normalizedTerminal.get("prior_combat_id"))
                ||!number(args.selectedPublicCunitId()).equals(normalizedTerminal.get("subject_public_cunit_id"))
                ||!number(after.nativeRevision()).equals(normalizedTerminal.get("snapshot_revision"))
                ||!number(after.dateRaw()).equals(normalizedTerminal.get("observed_date_raw")))return pending("terminal_full_CombatID_subject_or_current_frame_differs");
        if(!new Text("available").equals(normalizedTerminal.get("status")))return pending("original_terminal_journal_unavailable");
        Obj journal=OpportunityJson.object(normalizedTerminal.get("terminal_journal"),"terminal journal"),
                prior=OpportunityJson.object(normalizedTerminal.get("prior"),"prior combat"),removal=OpportunityJson.object(normalizedTerminal.get("removal"),"removal"),
                subject=OpportunityJson.object(normalizedTerminal.get("subject"),"subject"),successor=OpportunityJson.object(normalizedTerminal.get("successor"),"successor");
        String side=(args.expectedSideIndex()==0?"attacker":"defender")+"_public_cunit_ids_in_stored_order";
        if(!(new Text("observed").equals(journal.get("event_status"))&&new Text("normal_result").equals(prior.get("terminal_kind"))
                &&number(1-args.expectedSideIndex()).equals(prior.get("winner_raw"))&&no(removal.get("prior_combat_strictly_resolves"))
                &&ids(prior.get(side)).equals(intent.affectedInStoredOrder())&&new Text("subject_retreating").equals(successor.get("state"))
                &&number(args.targetProvinceId()).equals(subject.get("move_target_province_id"))
                &&ids(subject.get("route_province_ids_in_stored_order")).equals(intent.routeProvinceIds())))return pending("terminal_kind_original_scope_or_retreat_state_incomplete");
        Value sequence=journal.get("event_sequence");require(sequence instanceof IntegerValue i&&i.value().signum()>0,"observed terminal event requires exact positive sequence");
        List<Obj> affected=affected(intent,snapshot);
        if(affected.stream().anyMatch(row->!yes(row.get("retreat_target_route_observed"))))return new Pending("affected_army_terminal_core_post_incomplete",affected,false);
        return new Observed(Scope.FULL_SIDE,after,affected,sequence);
    }
    private static boolean current(Order intent,Obj snapshot) {
        SourceFrame before=intent.source(),after=SourceFrame.read(snapshot);Obj actor=OpportunityJson.object(snapshot.get("played_character"),"actor");
        return after.episodeRunId().equals(before.episodeRunId())&&after.connectionGeneration().equals(before.connectionGeneration())
                &&after.revision().compareTo(before.revision())>0&&!after.snapshotId().equals(before.snapshotId())
                &&after.nativeRevision().compareTo(before.nativeRevision())>=0&&after.dateRaw().compareTo(before.dateRaw())>=0
                &&yes(snapshot.get("paused"))&&yes(snapshot.get("map_ready"))&&number(intent.selectedOwnerCharacterId()).equals(actor.get("character_id"));
    }
    private static List<Obj> affected(Order intent,Obj snapshot) {
        List<Obj> result=new ArrayList<>();
        for(int unit:intent.affectedInStoredOrder()) {
            List<Obj> matches=rows(snapshot.get("player_armies")).stream().filter(a->number(unit).equals(a.get("army_id"))).toList();
            boolean valid=matches.size()==1&&yes(matches.getFirst().get("retreating"))&&no(matches.getFirst().get("in_combat"))
                    &&number(intent.selectedOwnerCharacterId()).equals(matches.getFirst().get("owner_character_id"))
                    &&number(intent.arguments().targetProvinceId()).equals(matches.getFirst().get("move_target_province_id"))
                    &&new Arr(intent.routeProvinceIds().stream().<Value>map(MilitaryPlanInputs::number).toList()).equals(matches.getFirst().get("route_province_ids"));
            result.add(obj(f("public_cunit_id",number(unit)),f("retreat_target_route_observed",new Bool(valid))));
        }
        return List.copyOf(result);
    }
    private static Pending pending(String reason){return new Pending(reason,List.of(),false);}
}
