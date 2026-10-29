package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevanceCodec;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevancePolicy;

/** Actual strategy19590..19898 relief producer. Position/strength is never contact permission. */
public final class WarStrengthRelief {
    public record ReliefContext(ObservationIdentity before,Optional<Army> selectedArmy,
            Optional<Integer> selectedWar,Obj assessment) {
        public ReliefContext {
            Objects.requireNonNull(before);Objects.requireNonNull(selectedArmy);Objects.requireNonNull(selectedWar);
            Objects.requireNonNull(assessment);OpportunityJson.text(assessment.get("status"),"relief status");
        }
    }
    /** These are outputs of the real route-ingress collector, not caller classified safety booleans. */
    public record ContactFacts(ObservationIdentity before,List<Army> controlled,Optional<Army> pursuit,
            Optional<Integer> tacticalWar) {
        public ContactFacts {
            Objects.requireNonNull(before);controlled=List.copyOf(controlled);Objects.requireNonNull(pursuit);
            Objects.requireNonNull(tacticalWar);
            if(pursuit.isPresent())require(controlled.contains(pursuit.orElseThrow()),"selected Army not in exact controlled roster");
        }
    }
    public sealed interface ContactObservation permits KnownContact,MissingContact {}
    public record KnownContact(ContactFacts facts) implements ContactObservation {
        public KnownContact {Objects.requireNonNull(facts);}
    }
    public record MissingContact(List<String> missing) implements ContactObservation {
        public MissingContact {missing=List.copyOf(missing);require(!missing.isEmpty(),"exact contact supplier gap required");}
    }
    @FunctionalInterface public interface ContactPort {ContactObservation collect(PlanningRequest request);}
    public sealed interface EvidenceLookup permits EvidenceFound,EvidenceAbsent,EvidenceUnavailable {}
    public record EvidenceFound(ObservationIdentity before,Obj evidence) implements EvidenceLookup {
        public EvidenceFound {Objects.requireNonNull(before);Objects.requireNonNull(evidence);}
    }
    public record EvidenceAbsent() implements EvidenceLookup {}
    public record EvidenceUnavailable(List<String> missing) implements EvidenceLookup {
        public EvidenceUnavailable {missing=List.copyOf(missing);require(!missing.isEmpty(),"exact movement evidence gap required");}
    }
    /** Supplied by the one WarContactHistory implementation, including restore checkpoint identity. */
    public interface MovementEvidence {
        EvidenceLookup activeIntent(PlanningRequest request,int army,int target);
        EvidenceLookup acceptedArrival(PlanningRequest request,int army,int target);
        EvidenceLookup observedErrorArrival(PlanningRequest request,int army,int target);
    }
    /** Actual _battle_control_turn_state collector result, needed only for a currently fighting Army. */
    @FunctionalInterface public interface BattleControlPort {Optional<Obj> collect(PlanningRequest request);}
    private final ContactPort contact;
    private final MovementEvidence movement;
    private final BattleControlPort battle;
    public WarStrengthRelief(ContactPort contact,MovementEvidence movement,BattleControlPort battle) {
        this.contact=Objects.requireNonNull(contact);this.movement=Objects.requireNonNull(movement);this.battle=Objects.requireNonNull(battle);
    }
    public Optional<ReliefContext> collect(PlanningRequest request) {
        ContactObservation observation=contact.collect(request);
        if(!(observation instanceof KnownContact known))return Optional.empty();
        ContactFacts facts=known.facts();require(facts.before().equals(request.before()),"relief ingress crossed frame");
        Obj assessment=assess(request,facts,movement,battle);
        Optional<Integer> selected=facts.tacticalWar();
        // Original10665 checks only ready. Preserve it even though the current
        // helper's normal candidate status is forecast_required.
        if(new Text("ready").equals(assessment.get("status"))) {
            Integer war=optionalInt(assessment.get("war_id"));
            if(war!=null&&wars(request).stream().anyMatch(row->Integer.valueOf(war).equals(optionalInt(row.get("war_id")))))selected=Optional.of(war);
        }
        return Optional.of(new ReliefContext(request.before(),facts.pursuit(),selected,assessment));
    }
    private record Siege(int warIndex,int enemyIndex,Obj war,Army enemy) {}
    private record Candidate(int score,int war,int enemy,int target,Balance balance) {}
    public static Obj assess(PlanningRequest request,ContactFacts facts,MovementEvidence movement,BattleControlPort battle) {
        require(facts.before().equals(request.before()),"relief facts crossed frame");
        Obj snapshot=request.observations().snapshot();List<Obj> wars=wars(request);List<Siege> sieges=new ArrayList<>();
        for(int wi=0;wi<wars.size();wi++) {
            Obj war=wars.get(wi);Integer warId=optionalInt(war.get("war_id")),score=optionalInt(war.get("player_relative_war_score"));
            if(!new Text("defender").equals(war.get("player_side"))||warId==null||score==null||score<=-100||score>=100)continue;
            List<Obj> enemyRows=rows(war.get("enemy_armies"));
            for(int ei=0;ei<enemyRows.size();ei++) {
                Army enemy=army(enemyRows.get(ei));
                if(!"sieging".equals(enemy.tacticalState())||Boolean.TRUE.equals(enemy.retreating()))continue;
                var relevance=reliefRequest(snapshot,wi,ei);
                boolean realm=RealmSiegePolicy.warQualifies(relevance.realmFrame().snapshot(),relevance.realmFrame().candidateWar());
                if(!(yes(war.get("player_is_primary_war_leader"))||realm)
                        ||!ReliefRelevancePolicy.assess(relevance).candidateSiegeReliefRelevant())continue;
                boolean departed=yes(enemy.raw().get("move_target_observable"))&&enemy.target()!=null&&enemy.target()>0
                        &&enemy.current()!=null&&enemy.current()>0&&!enemy.target().equals(enemy.current())
                        &&"complete_nonempty".equals(enemy.routeReadStatus())&&completeRoute(enemy)
                        &&Boolean.FALSE.equals(enemy.inCombat())&&Boolean.FALSE.equals(enemy.retreating());
                if(!departed)sieges.add(new Siege(wi,ei,war,enemy));
            }
        }
        if(sieges.isEmpty()||facts.controlled().size()!=1||facts.pursuit().isEmpty()
                ||!facts.pursuit().orElseThrow().equals(facts.controlled().get(0)))return status("not_applicable");
        if(!yes(snapshot.get("paused"))||!yes(snapshot.get("map_ready"))
                ||!nullOrMissing(snapshot.get("active_event"))||!nullOrMissing(snapshot.get("pending_character_interaction")))
            return unavailable("single-idle-controllable-army-binding");
        Army army=facts.controlled().get(0);Optional<Obj> forced=forcedRetreat(request,facts.controlled());
        if(forced.isPresent())return obj(f("status",text("native_forced_retreat")),f("native_forced_retreat_observation_v1",forced.orElseThrow()));
        if("combat".equals(army.tacticalState())) {
            Optional<Obj> observed=battle.collect(request);
            if(observed.isPresent()&&new Text("ready").equals(observed.orElseThrow().get("status"))
                    &&observed.orElseThrow().get("full_frames") instanceof Arr frames&&frames.items().size()==1
                    &&frames.items().get(0) instanceof Obj frame
                    &&new Text("available").equals(frame.get("status"))&&yes(frame.get("battle_control_ready"))
                    &&Integer.valueOf(army.id()).equals(optionalInt(frame.get("subject_public_cunit_id")))
                    &&Objects.equals(army.current(),optionalInt(frame.get("province_id")))
                    &&Objects.equals(snapshot.get("date_raw"),frame.get("observed_date_raw"))
                    &&fullCombat(frame.get("combat_id"))&&Boolean.TRUE.equals(army.inCombat())&&Boolean.FALSE.equals(army.retreating()))
                return obj(f("status",text("active_combat")),f("army_id",number(army.id())),f("combat_id",frame.get("combat_id")));
            return unavailable("same-frame-active-combat-binding");
        }
        boolean complete=completeRoute(army);
        boolean moving="moving".equals(army.tacticalState())||"embarked".equals(army.tacticalState())
                ||Integer.valueOf(4).equals(army.stateCode())||Integer.valueOf(7).equals(army.stateCode())
                ||("sieging".equals(army.tacticalState())&&Boolean.FALSE.equals(army.inCombat())&&Boolean.FALSE.equals(army.retreating())&&complete);
        if(moving) {
            EvidenceLookup intent=complete?movement.activeIntent(request,army.id(),army.target()):new EvidenceAbsent();
            if(intent instanceof EvidenceFound found)require(found.before().equals(request.before()),"move intent crossed frame");
            return !(intent instanceof EvidenceFound found)?unavailable("complete-matching-active-native-move-intent-route"):
                    obj(f("status",text("active_move_intent")),f("army_id",number(army.id())),f("target_province_id",number(army.target())),
                            f("route_province_ids",numbers(army.route().orElseThrow())),f("move_intent",found.evidence()));
        }
        boolean idleShape=Boolean.FALSE.equals(army.inCombat())&&Boolean.FALSE.equals(army.retreating())
                &&army.moveTargetPresent()&&army.target()==null&&army.route().isPresent()&&army.route().orElseThrow().isEmpty()&&army.current()!=null;
        if("sieging".equals(army.tacticalState())&&idleShape) {
            EvidenceLookup arrival=movement.acceptedArrival(request,army.id(),army.current());
            if(arrival instanceof EvidenceAbsent)arrival=movement.observedErrorArrival(request,army.id(),army.current());
            if(arrival instanceof EvidenceFound found)require(found.before().equals(request.before()),"move arrival crossed frame");
            return !(arrival instanceof EvidenceFound found)?unavailable("accepted-native-move-arrival-for-current-siege"):
                    obj(f("status",text("arrived_sieging")),f("army_id",number(army.id())),f("target_province_id",number(army.current())),f("move_arrival",found.evidence()));
        }
        if(!"regular".equals(army.tacticalState())||!idleShape)return unavailable("single-idle-controllable-army-binding");
        List<Candidate> candidates=new ArrayList<>();Set<Integer> incomplete=new HashSet<>();
        for(Siege siege:sieges) {
            int war=id(siege.war().get("war_id"));Army enemy=siege.enemy();Optional<Balance> measured=balance(request,war);
            boolean stationary=enemy.current()!=null&&enemy.current()>0&&Boolean.FALSE.equals(enemy.inCombat())&&Boolean.FALSE.equals(enemy.retreating())
                    &&enemy.moveTargetPresent()&&enemy.target()==null&&enemy.route().isPresent()&&enemy.route().orElseThrow().isEmpty();
            if(!stationary||measured.isEmpty()){incomplete.add(war);continue;}
            Balance b=measured.orElseThrow();Set<Integer> published=new HashSet<>();
            for(Obj row:rows(siege.war().get("enemy_armies"))) {Army member=army(row);if(!"retreating".equals(member.tacticalState()))published.add(member.id());}
            if(!ids(b.original().get("friendly_army_ids")).contains(army.id())||!ids(b.original().get("enemy_army_ids")).contains(enemy.id())
                    ||!new HashSet<>(ids(b.original().get("enemy_army_ids"))).equals(published)
                    ||b.friendlyCurrent().signum()<=0||b.enemyCurrent().signum()<=0||b.friendlyPower().signum()<=0||b.enemyPower().signum()<=0) {
                incomplete.add(war);continue;
            }
            candidates.add(new Candidate(int32(siege.war().get("player_relative_war_score")),war,enemy.id(),enemy.current(),b));
        }
        if(!incomplete.isEmpty())return put(unavailable("complete-same-frame-siege-position-and-war-strength"),"war_ids",numbers(incomplete.stream().sorted().toList()));
        require(!candidates.isEmpty(),"complete siege candidates unexpectedly empty");
        Candidate best=candidates.stream().min(Comparator.comparingInt(Candidate::score).thenComparingInt(Candidate::war)
                .thenComparingInt(Candidate::enemy).thenComparingInt(Candidate::target)).orElseThrow();
        return obj(f("status",text("forecast_required")),f("selection_policy",text("lowest-score-then-war-enemy-province")),
                f("war_id",number(best.war())),f("player_relative_war_score",number(best.score())),f("army_id",number(army.id())),
                f("enemy_army_id",number(best.enemy())),f("target_province_id",number(best.target())),f("army_strength_balance",best.balance().original()),
                f("candidate_count",number(candidates.size())),f("reason",text("qualified_same_frame_combat_forecast_required_for_siege_contact")));
    }
    private static ReliefRelevancePolicy.Request reliefRequest(Obj snapshot,int war,int enemy) {
        Obj frame=obj(f("schema",text(RealmSiegePolicy.INPUT_SCHEMA)),f("snapshot",snapshot),f("detached_wars",new Arr(List.of())),
                f("detached_enemies",new Arr(List.of())),f("candidate_war_ref",obj(f("collection",text("active_wars")),f("index",number(war)))),
                f("candidate_enemy_ref",obj(f("collection",text("candidate_war_enemy_armies")),f("index",number(enemy)))));
        Obj input=obj(f("schema",text(ReliefRelevancePolicy.INPUT_SCHEMA)),f("frame",frame));
        return ReliefRelevanceCodec.decodeNode(OpportunityJson.toNode(input));
    }
    private static boolean completeRoute(Army army) {
        return army.target()!=null&&army.target()>0&&army.route().isPresent()&&!army.route().orElseThrow().isEmpty()
                &&army.route().orElseThrow().get(army.route().orElseThrow().size()-1).equals(army.target());
    }
    private static boolean nullOrMissing(Value value){return value==null||value==Nil.INSTANCE;}
    private static boolean positive(Value value){BigInteger number=optionalInteger(value);return number!=null&&number.signum()>0;}
    private static boolean fullCombat(Value value){Integer component=optionalInt(value);return component!=null&&component!=-1;}
    private static Obj status(String status){return obj(f("status",text(status)));}
    private static Obj unavailable(String required){return obj(f("status",text("observation_unavailable")),f("required_observation",text(required)));}

    /** war_forced_retreat_observation_v1.py: recognizes CK3's already active order only. */
    public static Optional<Obj> forcedRetreat(PlanningRequest request,List<Army> controlled) {
        if(controlled.isEmpty())return Optional.empty();Obj s=request.observations().snapshot();
        if(!new Text("native-headless").equals(s.get("backend_id"))||!new Text("injected-dll-named-pipe").equals(s.get("source"))
                ||!yes(s.get("paused"))||!yes(s.get("map_ready"))||!positive(s.get("native_revision"))||!positive(s.get("revision"))
                ||!new Text("native:"+OpportunityJson.integer(s.get("native_revision"),"native revision")).equals(s.get("snapshot_id"))
                ||optionalInteger(s.get("date_raw"))==null||!(s.get("episode_run_id") instanceof Text episode)||episode.value().isEmpty()
                ||!(s.get("played_character") instanceof Obj actor)||!yes(actor.get("alive"))||optionalInteger(actor.get("character_id"))==null
                ||s.get("active_event")!=Nil.INSTANCE||s.get("pending_character_interaction")!=Nil.INSTANCE
                ||s.get("top_exclusive_modal_choice_hint") instanceof Obj hint&&new Text("present").equals(hint.get("status")))return Optional.empty();
        Set<Integer> selected=new HashSet<>();
        for(Army army:controlled) {
            if(!selected.add(army.id())||!new Text("native").equals(army.raw().get("source"))
                    ||!Objects.equals(army.raw().get("owner_character_id"),actor.get("character_id"))||!army.controllable()
                    ||!"retreating".equals(army.state())||!Integer.valueOf(6).equals(army.stateCode())
                    ||!Boolean.TRUE.equals(army.retreating())||!Boolean.FALSE.equals(army.inCombat())||army.current()==null||army.current()<=0
                    ||!yes(army.raw().get("move_target_observable"))||!"complete_nonempty".equals(army.routeReadStatus())||!completeRoute(army))return Optional.empty();
        }
        Set<Integer> published=new HashSet<>();for(Obj row:rows(s.get("player_armies")))if(yes(row.get("controllable")))published.add(id(row.get("army_id")));
        if(!published.equals(selected))return Optional.empty();
        return Optional.of(obj(f("schema",text("xar.ck3.existing-native-forced-retreat/v1")),f("army_ids",numbers(selected.stream().sorted().toList())),
                f("source_snapshot_id",s.get("snapshot_id")),f("source_native_revision",s.get("native_revision")),f("source_date_raw",s.get("date_raw")),
                f("existing_native_retreat_only",new Bool(true)),f("new_retreat_order",new Bool(false)),f("contact_free_proven",new Bool(false)),
                f("attack_authorized",new Bool(false)),f("arrival_or_battle_success_inferred",new Bool(false))));
    }
}
