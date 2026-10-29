package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.battleretreat.BattleRetreatCodec;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Ordinary territorial-defence policy, separate from native legality and future battle prediction. */
public final class ActiveRetreatProposal {
    private ActiveRetreatProposal() {}
    public static final String BUDGET_POLICY="own-losing-territorial-defence-owner-hard-loss-5pct-v1";
    public record SourceFrame(String snapshotId,BigInteger revision,BigInteger nativeRevision,BigInteger dateRaw,
                              String episodeRunId,BigInteger connectionGeneration) {
        public SourceFrame {
            StrictJson.text(snapshotId);StrictJson.text(episodeRunId);
            for(BigInteger value:List.of(revision,nativeRevision,connectionGeneration))
                require(value.signum()>=0&&value.compareTo(StrictJson.UINT64_MAX)<=0,"retreat frame uint64 outside range");
            require(nativeRevision.signum()>0&&connectionGeneration.signum()>0,"native retreat source requires positive generation/revision");
            require(dateRaw!=null&&dateRaw.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&dateRaw.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"retreat date requires signed int64");
        }
        public static SourceFrame read(Obj snapshot) {
            Obj diagnostics=OpportunityJson.object(snapshot.get("diagnostics"),"retreat diagnostics");
            return new SourceFrame(OpportunityJson.text(snapshot.get("snapshot_id"),"snapshot_id"),
                    OpportunityJson.integer(snapshot.get("revision"),"revision"),
                    OpportunityJson.integer(snapshot.get("native_revision"),"native_revision"),
                    OpportunityJson.integer(snapshot.get("date_raw"),"date_raw"),
                    OpportunityJson.text(snapshot.get("episode_run_id"),"episode_run_id"),
                    OpportunityJson.integer(diagnostics.get("connection_generation"),"connection_generation"));
        }
        public Obj json() {return obj(f("snapshot_id",text(snapshotId)),f("revision",number(revision)),
                f("native_revision",number(nativeRevision)),f("date_raw",number(dateRaw)),f("episode_run_id",text(episodeRunId)),
                f("connection_generation",number(connectionGeneration)));}
    }
    public sealed interface Budget permits BudgetObserved,BudgetUnavailable {Obj json();}
    public record BudgetUnavailable(String reason) implements Budget {
        public BudgetUnavailable {StrictJson.text(reason);}
        @Override public Obj json(){return put(baseBudget(),"reason",text(reason));}
    }
    public record BudgetObserved(BigInteger maximumNextTickHardLossRaw,BigInteger ownerCurrentFightingRaw,
            BigInteger ownSideFightingRaw,BigInteger enemySideFightingRaw,List<Integer> opposingPublicCunitIds,
            List<Obj> losingDefensiveWars) implements Budget {
        public BudgetObserved {
            Objects.requireNonNull(maximumNextTickHardLossRaw);Objects.requireNonNull(ownerCurrentFightingRaw);
            require(ownerCurrentFightingRaw.signum()>0&&maximumNextTickHardLossRaw.equals(ownerCurrentFightingRaw.multiply(BigInteger.valueOf(5)).divide(BigInteger.valueOf(100))),"exact own five-percent budget required");
            require(ownSideFightingRaw.signum()>0&&ownSideFightingRaw.compareTo(enemySideFightingRaw)<=0,"current headcount disadvantage required");
            opposingPublicCunitIds=List.copyOf(opposingPublicCunitIds);losingDefensiveWars=List.copyOf(losingDefensiveWars);
            require(!opposingPublicCunitIds.isEmpty()&&!losingDefensiveWars.isEmpty(),"actual opposing territorial-war relation required");
        }
        @Override public Obj json(){return merge(baseBudget(),obj(f("status",text("observed")),f("reason",text("preserve_army_for_continued_defence")),
                f("maximum_next_tick_hard_loss_raw",number(maximumNextTickHardLossRaw)),f("maximum_next_tick_fraction_percent",number(5)),
                f("owner_current_fighting_raw",number(ownerCurrentFightingRaw)),f("current_own_side_fighting_raw",number(ownSideFightingRaw)),
                f("current_enemy_side_fighting_raw",number(enemySideFightingRaw)),f("observed_opposing_public_cunit_ids",numbers(opposingPublicCunitIds)),
                f("battle_warscore_attribution_verified",new Bool(false)),f("comparison_scope",text("current fighting headcount, not effective combat power or victory probability")),
                f("losing_defensive_wars",objects(losingDefensiveWars)),f("budget_source",text("explicit_ordinary_counter_policy_not_native_AI_threshold"))));}
    }
    private static Obj baseBudget(){return obj(f("status",text("unavailable")),f("maximum_next_tick_hard_loss_raw",Nil.INSTANCE),
            f("policy",text(BUDGET_POLICY)),f("battle_win_probability",Nil.INSTANCE),f("retreat_pursuit_losses_raw",Nil.INSTANCE),
            f("defeat_title_transfer_verified",new Bool(false)));}
    /** Consumes the actual normalized full battle frame, never a preclassified win/lose label. */
    public static Budget normalBudget(Obj snapshot,Obj control) {
        Obj actor=OpportunityJson.object(snapshot.get("played_character"),"played character");
        int actorId=id(actor.get("character_id"));
        Integer side=optionalInt(control.get("side_index"));
        List<Obj> wars=new ArrayList<>();
        for(Obj war:rows(snapshot.get("active_wars"))) {
            Integer score=optionalInt(war.get("player_relative_war_score"));
            if(!yes(war.get("player_is_primary_war_leader"))||!new Text("defender").equals(war.get("player_side"))||score==null||score>=0
                    ||!(war.get("targeted_title_ids") instanceof Arr titles)||titles.items().stream().noneMatch(v->v instanceof IntegerValue i&&i.value().signum()>=0))continue;
            wars.add(war);
        }
        if(wars.isEmpty()||side==null||(side!=0&&side!=1))return new BudgetUnavailable("no_current_losing_own_territorial_defence");
        if(!(control.get(side==0?"attacker":"defender") instanceof Obj own)||!(control.get(side==0?"defender":"attacker") instanceof Obj enemy))
            return new BudgetUnavailable("current_combat_entries_unavailable");
        Set<Integer> enemyIds=new HashSet<>();
        for(Obj army:rows(enemy.get("ordered_armies"))) {
            Integer candidate=optionalInt(army.get("public_cunit_id"));if(candidate!=null&&candidate>=0)enemyIds.add(candidate);
        }
        List<Obj> relevant=new ArrayList<>();
        for(Obj war:wars)if(war.get("enemy_armies") instanceof Arr&&rows(war.get("enemy_armies")).stream()
                .anyMatch(a->a.get("army_id") instanceof IntegerValue i&&i.value().bitLength()<32&&enemyIds.contains(i.value().intValue())))relevant.add(war);
        if(enemyIds.isEmpty()||relevant.isEmpty())return new BudgetUnavailable("current_opposing_cunits_not_related_to_losing_territorial_defence");
        BigInteger ownCurrent=optionalInteger(own.get("derived_current_fighting_raw")),enemyCurrent=optionalInteger(enemy.get("derived_current_fighting_raw"));
        if(ownCurrent==null||enemyCurrent==null||ownCurrent.signum()<=0||ownCurrent.compareTo(enemyCurrent)>0)
            return new BudgetUnavailable("current_combat_headcount_disadvantage_not_observed");
        List<Obj> entries=new ArrayList<>();entries.addAll(rows(own.get("levy_entries")));entries.addAll(rows(own.get("men_at_arms_entries")));
        List<Obj> owned=entries.stream().filter(row->number(actorId).equals(row.get("owner_character_id"))).toList();
        if(owned.isEmpty()||owned.stream().anyMatch(row->optionalInteger(row.get("current_fighting_raw"))==null||OpportunityJson.integer(row.get("current_fighting_raw"),"current fighting").signum()<0))
            return new BudgetUnavailable("selected_owner_current_entries_unavailable");
        BigInteger remaining=owned.stream().map(row->OpportunityJson.integer(row.get("current_fighting_raw"),"current fighting")).reduce(BigInteger.ZERO,BigInteger::add);
        if(remaining.signum()<=0)return new BudgetUnavailable("selected_owner_current_entries_empty");
        List<Obj> summary=relevant.stream().map(war->obj(f("war_id",nullable(war.get("war_id"))),f("player_relative_war_score",nullable(war.get("player_relative_war_score"))),f("targeted_title_ids",war.get("targeted_title_ids")))).toList();
        return new BudgetObserved(remaining.multiply(BigInteger.valueOf(5)).divide(BigInteger.valueOf(100)),remaining,ownCurrent,enemyCurrent,enemyIds.stream().sorted().toList(),summary);
    }
    /** First stored friendly rally only; all native hostile current orders must be complete. */
    public static List<Integer> rallies(Obj snapshot,int combatProvince) {
        if(!(snapshot.get("player_armies") instanceof Arr)||!(snapshot.get("active_wars") instanceof Arr)||rows(snapshot.get("active_wars")).isEmpty())return List.of();
        Set<Integer> threats=new HashSet<>();
        for(Obj war:rows(snapshot.get("active_wars"))) {
            if(!(war.get("enemy_armies") instanceof Arr))return List.of();
            for(Obj row:rows(war.get("enemy_armies"))) {
                var parsed=route(row.get("route_province_ids"));Integer target=optionalInt(row.get("move_target_province_id")),current=optionalInt(row.get("current_province_id"));
                String status=optionalText(row.get("route_read_status"));
                if(parsed.isEmpty()||current==null||current<=0)return List.of();
                List<Integer> path=parsed.orElseThrow();
                boolean empty="complete_empty".equals(status)&&path.isEmpty()&&row.get("move_target_province_id")==Nil.INSTANCE;
                boolean moving="complete_nonempty".equals(status)&&!path.isEmpty()&&target!=null&&target>0&&path.getLast().equals(target);
                if(!empty&&!moving)return List.of();
                threats.add(current);threats.addAll(path);if(target!=null&&target>0)threats.add(target);
            }
        }
        Obj actor=OpportunityJson.object(snapshot.get("played_character"),"actor");List<Integer> candidates=new ArrayList<>();
        for(Obj row:rows(snapshot.get("player_armies"))) {
            Integer current=optionalInt(row.get("current_province_id"));BigInteger soldiers=optionalInteger(row.get("soldiers"));String state=optionalText(row.get("army_state"));
            if(yes(row.get("controllable"))&&no(row.get("in_combat"))&&no(row.get("retreating"))&&Objects.equals(row.get("owner_character_id"),actor.get("character_id"))
                    &&row.get("route_province_ids") instanceof Arr path&&path.items().isEmpty()&&row.get("move_target_province_id")==Nil.INSTANCE
                    &&("idle".equals(state)||"regular".equals(state))&&current!=null&&current>0&&soldiers!=null&&soldiers.signum()>0
                    &&current!=combatProvince&&!threats.contains(current)&&!candidates.contains(current))candidates.add(current);
        }
        return List.copyOf(candidates);
    }
    public sealed interface Proposal permits Keep,Preview,Order {}
    public record Keep(String stage,String reason,Optional<Obj> assessment) implements Proposal {
        public Keep {StrictJson.text(stage);StrictJson.text(reason);Objects.requireNonNull(assessment);}
    }
    public record Preview(int subjectPublicCunitId,int targetProvinceId,Obj assessment) implements Proposal {
        public Preview {require(subjectPublicCunitId>=0&&targetProvinceId>0,"preview IDs");Objects.requireNonNull(assessment);}
    }
    public record Order(SourceFrame source,int selectedOwnerCharacterId,BattleRetreatPolicy.RetreatOrder arguments,
            List<Integer> affectedInStoredOrder,List<Integer> unaffectedInStoredOrder,List<Integer> routeProvinceIds,
            Obj assessment) implements Proposal {
        public Order {
            Objects.requireNonNull(source);Objects.requireNonNull(arguments);Objects.requireNonNull(assessment);
            affectedInStoredOrder=List.copyOf(affectedInStoredOrder);unaffectedInStoredOrder=List.copyOf(unaffectedInStoredOrder);routeProvinceIds=List.copyOf(routeProvinceIds);
            require(selectedOwnerCharacterId>=0&&!affectedInStoredOrder.isEmpty()&&affectedInStoredOrder.contains(arguments.selectedPublicCunitId()),"selected subject must belong to affected roster");
            require(affectedInStoredOrder.stream().allMatch(v->v>=0)&&affectedInStoredOrder.stream().distinct().count()==affectedInStoredOrder.size()
                    &&unaffectedInStoredOrder.stream().allMatch(v->v>=0)&&unaffectedInStoredOrder.stream().distinct().count()==unaffectedInStoredOrder.size()
                    &&affectedInStoredOrder.stream().noneMatch(unaffectedInStoredOrder::contains),"exact disjoint public roster required");
            require(!routeProvinceIds.isEmpty()&&routeProvinceIds.stream().allMatch(v->v>0)&&routeProvinceIds.getLast()==arguments.targetProvinceId(),"exact retreat route target required");
        }
    }
    /** Actual current-model adapter is mandatory; unavailable optional model leaves must not fabricate a tick. */
    @FunctionalInterface public interface CurrentLossModel {
        BattleRetreatPolicy.Request inputs(Obj normalizedCurrentControl,BigInteger budget,Optional<Obj> normalizedPreview);
    }
    public static Proposal propose(PlanningRequest request,Obj control,BudgetObserved budget,Optional<Obj> preview,CurrentLossModel model) {
        Objects.requireNonNull(model);Objects.requireNonNull(preview);Obj snapshot=request.observations().snapshot();
        if(!quiet(snapshot))return keep("retain_ordinary_battle_policy","ordinary_current_subject_or_modal_guard");
        SourceFrame frame=SourceFrame.read(snapshot);
        if(!frame.nativeRevision().equals(control.get("snapshot_revision") instanceof IntegerValue i?i.value():null)
                ||!frame.dateRaw().equals(control.get("observed_date_raw") instanceof IntegerValue i?i.value():null))
            return keep("query_current_control","current_control_binding_required");
        int subject=id(control.get("selected_public_cunit_id")),owner=id(control.get("selected_owner_character_id")),combatProvince=province(control.get("combat_province_id"));
        Obj actor=OpportunityJson.object(snapshot.get("played_character"),"actor");
        List<Obj> selected=rows(snapshot.get("player_armies")).stream().filter(a->number(subject).equals(a.get("army_id"))).toList();
        if(!number(owner).equals(actor.get("character_id"))||selected.size()!=1||!yes(selected.getFirst().get("controllable"))
                ||!yes(selected.getFirst().get("in_combat"))||!no(selected.getFirst().get("retreating"))||!number(combatProvince).equals(selected.getFirst().get("current_province_id")))
            return keep("retain_ordinary_battle_policy","ordinary_current_subject_or_modal_guard");
        var first=assess(model,control,budget,Optional.empty());
        if(first.recommendation()!=BattleRetreatPolicy.Recommendation.QUERY_RETREAT_PREVIEW)return new Keep("retain_ordinary_battle_policy",first.reason(),Optional.of(assessment(first)));
        List<Integer> targets=rallies(snapshot,combatProvince);
        if(targets.isEmpty())return new Keep("no_observed_rally","No alternative stationary controllable rally outside observed hostile positions/routes.",Optional.of(assessment(first)));
        if(preview.isEmpty())return new Preview(subject,targets.getFirst(),assessment(first));
        Obj observed=preview.orElseThrow();int target=province(observed.get("target_province_id"));
        Obj binding=OpportunityJson.object(observed.get("source_binding"),"preview source");
        List<Integer> path=route(OpportunityJson.object(observed.get("target_preview"),"target preview").get("route_province_ids")).orElseThrow();
        if(!targets.contains(target)||!(path.equals(List.of(target))||path.equals(List.of(combatProvince,target)))||!binding.equals(frame.json()))
            return keep("preview_rejected","one_hop_rally_or_source_changed");
        Obj current=OpportunityJson.object(observed.get("battle_control_snapshot"),"preview current control");
        var decision=assess(model,current,budget,preview);
        if(decision.recommendation()!=BattleRetreatPolicy.Recommendation.ORDER_ACTIVE_COMBAT_RETREAT)return new Keep("retain_ordinary_battle_policy",decision.reason(),Optional.of(assessment(decision)));
        var args=Objects.requireNonNull(decision.retreatOrderArguments());
        require(args.selectedPublicCunitId()==subject&&args.expectedRevision().equals(frame.revision())&&args.targetProvinceId()==target,"preview decision drifted from source/subject/target");
        return new Order(frame,owner,args,ids(observed.get("affected_public_cunit_ids_in_stored_order")),ids(observed.get("unaffected_same_side_public_cunit_ids_in_stored_order")),path,assessment(decision));
    }
    private static BattleRetreatPolicy.Decision assess(CurrentLossModel model,Obj control,BudgetObserved budget,Optional<Obj> preview) {
        var input=Objects.requireNonNull(model.inputs(control,budget.maximumNextTickHardLossRaw(),preview));var observed=input.battleFrame().observed();
        require(input.maximumNextTickHardLossRaw().equals(budget.maximumNextTickHardLossRaw())
                &&number(observed.snapshotRevision()).equals(control.get("snapshot_revision"))&&number(observed.observedDateRaw()).equals(control.get("observed_date_raw"))
                &&number(observed.combatId()).equals(control.get("combat_id"))&&number(observed.provinceId()).equals(control.get("combat_province_id"))
                &&number(observed.sideIndex()).equals(control.get("side_index"))&&number(observed.selectedPublicCunitId()).equals(control.get("selected_public_cunit_id"))
                &&number(observed.selectedOwnerCharacterId()).equals(control.get("selected_owner_character_id"))
                &&text(observed.phase()).equals(control.get("phase"))&&number(observed.phaseDay()).equals(control.get("phase_day"))
                &&text(observed.sideScope().wire()).equals(control.get("side_scope"))
                &&number(input.battleFrame().phaseRaw()).equals(control.get("phase_raw"))
                &&number(input.battleFrame().winnerRaw()).equals(control.get("winner_raw"))
                &&number(input.battleFrame().forcedWinnerRaw()).equals(control.get("forced_winner_raw"))
                &&new Bool(input.battleFrame().finalized()).equals(control.get("finalized"))
                &&new Bool(input.battleFrame().battleControlReady()).equals(control.get("battle_control_ready")),"current model input differs from actual normalized control");
        Obj legality=OpportunityJson.object(control.get("legality"),"current retreat legality");
        require(new Bool(input.battleFrame().legality().legalNow()).equals(legality.get("legal_now"))
                &&strings(input.battleFrame().legality().reasonCodesInNativeOrder()).equals(legality.get("reason_codes_in_native_order"))
                &&(input.battleFrame().legality().earliestDayGateDateRaw()==null?Nil.INSTANCE:number(input.battleFrame().legality().earliestDayGateDateRaw())).equals(legality.get("earliest_day_gate_date_raw")),"current model legality differs from actual normalized control");
        return BattleRetreatPolicy.assess(input);
    }
    public static boolean quiet(Obj snapshot) {
        return yes(snapshot.get("paused"))&&yes(snapshot.get("map_ready"))&&absent(snapshot.get("active_event"))
                &&absent(snapshot.get("pending_character_interaction"))&&absent(snapshot.get("one_life_settlement"))
                &&snapshot.get("played_character") instanceof Obj actor&&yes(actor.get("alive"));
    }
    private static boolean absent(Value value){return value==null||value==Nil.INSTANCE;}
    private static Keep keep(String stage,String reason){return new Keep(stage,reason,Optional.empty());}
    private static Obj assessment(BattleRetreatPolicy.Decision value){return OpportunityJson.object(OpportunityJson.parse(BattleRetreatCodec.encodeDecision(value)),"retreat assessment");}
}
