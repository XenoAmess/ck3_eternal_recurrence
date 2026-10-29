package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyReinforcementCodec.*;

/** The original immutable conditional-arrival consumer. Current rosters are never augmented with an incoming candidate. */
public final class ArmyReinforcementAssessment {
    public static final String TEMPORAL="present_time_only_not_future_binding";
    public static final String CONDITION="observed_route_target_current_admission_gates_combat_and_relations_persist_until_native_eta";
    public enum Lifecycle { ALREADY_PARTICIPATING,ASSIGNED_EN_ROUTE,ORDINARY_EN_ROUTE,ASSIGNED_ETA_UNAVAILABLE,ARRIVED_NOT_YET_PARTICIPATING,NO_ARRIVAL_TARGET }
    public record Conditional(PublicUnitId selected,PositiveId target,TargetProvenance provenance,int eta,PositiveId currentlySelectedCombat,JoinSide side) {
        public Conditional {require(side==JoinSide.ATTACKER||side==JoinSide.DEFENDER,"conditional arrival requires an observed current joining side");}
        public boolean futureBinding(){return false;}public String condition(){return CONDITION;}public String temporalSemantics(){return TEMPORAL;}
    }
    public record Assessment(PublicUnitId selected,UInt64 snapshotRevision,long observedDateRaw,Availability status,Optional<String> unavailableReason,Optional<Lifecycle> lifecycle,
            Eligibility eligibility,Optional<PositiveId> target,TargetProvenance provenance,Optional<Integer> nativeEta,Optional<PositiveId> actualActiveCombat,
            boolean currentParticipationVerified,Optional<PositiveId> currentlySelectedCombat,JoinSide side,List<PublicUnitId> attackers,List<PublicUnitId> defenders,Optional<Conditional> conditional) {
        public Assessment {attackers=List.copyOf(attackers);defenders=List.copyOf(defenders);}
        public boolean futureBinding(){return false;}public String temporalSemantics(){return TEMPORAL;}
    }
    private ArmyReinforcementAssessment() { }
    public static Assessment derive(BattleResponses.Reinforcement frame) {
        var state=value(frame.state());Optional<Arrival> arrival=state.flatMap(s->value(s.contact().arrivalAdmission()));
        if(frame.status()!=Availability.AVAILABLE||arrival.isEmpty())return new Assessment(frame.selected(),frame.frame().nativeRevision(),frame.frame().dateRaw(),Availability.UNAVAILABLE,
                Optional.of(value(frame.unavailableReason()).filter(s->!s.isEmpty()).orElse("arrival_admission_not_published")),Optional.empty(),Eligibility.UNAVAILABLE,Optional.empty(),TargetProvenance.NONE,Optional.empty(),Optional.empty(),false,Optional.empty(),JoinSide.NONE,List.of(),List.of(),Optional.empty());
        var current=state.orElseThrow();var admission=arrival.orElseThrow();var target=value(admission.target().province());var provenance=admission.target().provenance();
        boolean available=admission.status()==ArrivalStatus.AVAILABLE||admission.status()==ArrivalStatus.NOT_APPLICABLE,verified=available&&admission.subjectParticipationVerified();
        Optional<Integer> eta=Optional.empty();
        if(provenance==TargetProvenance.NATIVE_HELP_OVERRIDE)eta=value(current.route().assignmentEta());
        else if(provenance==TargetProvenance.COMMITTED_ROUTE_FINAL&&!current.route().provinces().isEmpty()&&target.filter(current.route().provinces().getLast()::equals).isPresent())eta=value(current.route().arrivals()).map(List::getLast);
        Optional<Lifecycle> lifecycle=Optional.empty();
        if(verified)lifecycle=Optional.of(Lifecycle.ALREADY_PARTICIPATING);
        else if(value(current.assignment().activeCombat()).isPresent())lifecycle=Optional.empty();
        else if(target.isEmpty())lifecycle=Optional.of(Lifecycle.NO_ARRIVAL_TARGET);
        else if(current.route().currentProvince().equals(target.orElseThrow()))lifecycle=Optional.of(Lifecycle.ARRIVED_NOT_YET_PARTICIPATING);
        else if(provenance==TargetProvenance.NATIVE_HELP_OVERRIDE)lifecycle=Optional.of(current.route().alignment().equals("aligned_to_assignment")&&eta.isPresent()?Lifecycle.ASSIGNED_EN_ROUTE:Lifecycle.ASSIGNED_ETA_UNAVAILABLE);
        else if(provenance==TargetProvenance.COMMITTED_ROUTE_FINAL)lifecycle=Optional.of(Lifecycle.ORDINARY_EN_ROUTE);
        Optional<Conditional> conditional=Optional.empty();var selectedCombat=value(admission.selectedCombat());
        if(available&&lifecycle.filter(s->s==Lifecycle.ASSIGNED_EN_ROUTE||s==Lifecycle.ORDINARY_EN_ROUTE).isPresent()&&admission.eligibility()==Eligibility.ELIGIBLE&&eta.isPresent()&&selectedCombat.isPresent()&&admission.side()!=JoinSide.NONE)
            conditional=Optional.of(new Conditional(frame.selected(),target.orElseThrow(),provenance,eta.orElseThrow(),selectedCombat.orElseThrow(),admission.side()));
        return new Assessment(frame.selected(),frame.frame().nativeRevision(),frame.frame().dateRaw(),available?Availability.AVAILABLE:Availability.UNAVAILABLE,value(admission.unavailableReason()),lifecycle,admission.eligibility(),target,provenance,eta,value(admission.subject().activeCombat()),verified,available?selectedCombat:Optional.empty(),available?admission.side():JoinSide.NONE,available?admission.attackers():List.of(),available?admission.defenders():List.of(),conditional);
    }
    public static Obj json(Assessment value) {
        var n=ArmyJson.empty().put("selected_public_cunit_id",value.selected().value()).put("snapshot_revision",value.snapshotRevision().value()).put("observed_date_raw",value.observedDateRaw()).put("status",wire(value.status())).put("eligibility_now",wire(value.eligibility())).put("target_provenance",wire(value.provenance())).put("subject_current_participation_verified",value.currentParticipationVerified()).put("join_side_now",wire(value.side())).put("temporal_semantics",TEMPORAL).put("future_binding",false);
        text(n,"unavailable_reason",value.unavailableReason());text(n,"lifecycle",value.lifecycle().map(ArmyReinforcementAssessment::wire));id(n,"target_province_id",value.target());number(n,"native_eta_date_raw",value.nativeEta());id(n,"actual_active_combat_id",value.actualActiveCombat());id(n,"currently_selected_combat_id",value.currentlySelectedCombat());
        var attackers=n.putArray("current_attacker_public_cunit_ids_in_stored_order");value.attackers().forEach(v->attackers.add(v.value()));var defenders=n.putArray("current_defender_public_cunit_ids_in_stored_order");value.defenders().forEach(v->defenders.add(v.value()));
        if(value.conditional().isPresent()) {var c=value.conditional().orElseThrow();n.set("conditional_arrival",ArmyJson.empty().put("selected_public_cunit_id",c.selected().value()).put("target_province_id",c.target().value()).put("target_provenance",wire(c.provenance())).put("native_eta_date_raw",c.eta()).put("currently_selected_combat_id",c.currentlySelectedCombat().value()).put("join_side_if_observed_state_persists",wire(c.side())).put("condition",CONDITION).put("temporal_semantics",TEMPORAL).put("future_binding",false));}else n.putNull("conditional_arrival");
        return DriverJson.object(ArmyJson.bytes(n),DriverJson.MAX_NATIVE_BYTES);
    }
    private static String wire(Enum<?> value){return value.name().toLowerCase(java.util.Locale.ROOT);}
    private static <T> Optional<T> value(Field<T> value){return value instanceof Present<T> present?Optional.of(present.value()):Optional.empty();}
    private static void text(ObjectNode node,String field,Optional<String> value){if(value.isPresent())node.put(field,value.orElseThrow());else node.putNull(field);}
    private static void number(ObjectNode node,String field,Optional<Integer> value){if(value.isPresent())node.put(field,value.orElseThrow());else node.putNull(field);}
    private static void id(ObjectNode node,String field,Optional<PositiveId> value){if(value.isPresent())node.put(field,value.orElseThrow().value());else node.putNull(field);}
}
