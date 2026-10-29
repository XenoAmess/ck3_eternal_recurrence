package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.TreeSet;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleControlExtensionCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleResponseCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservationCodec;

/** Pure consumers of the original current PlanningRequest. No observe/query/resume/dispatch callback exists here. */
public final class ActiveCombatGuardProducers implements ActiveCombatDateGuards.ResumeAnnotator,ActiveCombatDateGuards.DefenderExitObserver {
    private final ActiveCombatObservedComparison comparison=new ActiveCombatObservedComparison();
    @Override public Obj annotate(PlanningRequest request,Obj originalPlan) {
        Obj snapshot=request.observations().snapshot();
        TreeSet<Integer> active=new TreeSet<>();
        for(Value value:OpportunityJson.array(snapshot.get("player_armies"),"player_armies")) {
            if(!(value instanceof Obj row) || !yes(row.get("controllable")))continue;
            try {Army army=army(row);if("combat".equals(army.tacticalState()))active.add(army.id());}
            catch(IllegalArgumentException|ArithmeticException invalidRow) { /* Invalid optional subject cannot become an observed combat. */ }
        }
        if(active.isEmpty())return originalPlan;
        Optional<Obj> provisional=comparison.observe(request);
        Value raw=snapshot.get("active_combat_resume_inputs_v1");boolean present=raw!=null&&raw!=Nil.INSTANCE;
        Integer subject=null;BigInteger sequence=null;Obj receipt=null,mapping=null;
        try {
            subject=optionalInt(snapshot.get("battle_control_snapshot_v1_subject_army_id"));
            sequence=optionalInteger(snapshot.get("battle_control_snapshot_v1_query_sequence"));
            if(present) {
                require(request.observations().paused() && new Text("available").equals(snapshot.get("battle_control_snapshot_v1_status"))
                        && subject!=null && active.contains(subject) && sequence!=null && sequence.signum()>0 && sequence.compareTo(StrictJson.UINT64_MAX)<=0
                        && java.util.Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_snapshot_id"),snapshot.get("snapshot_id"))
                        && java.util.Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_revision"),snapshot.get("revision"))
                        && java.util.Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_native_revision"),snapshot.get("native_revision")),
                        "resume annotation lacks its actual current query binding");
                Obj parent=BattleResponseCodec.normalizeControl(OpportunityJson.object(snapshot.get("battle_control_snapshot_v1"),"active control"),
                        subject,request.before().frame().identity().nativeRevision(),request.before().frame().identity().dateRaw().longValueExact());
                ObjectNode normalized=BattleControlExtensionCodec.normalizeResume(
                        (ObjectNode)StrictJson.parse(OpportunityJson.encode(OpportunityJson.object(raw,"active resume"))),
                        (ObjectNode)StrictJson.parse(OpportunityJson.encode(parent)));
                receipt=OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(normalized)),"normalized resume");
                Obj observed=OpportunityJson.object(receipt.get("observed"),"observed resume");
                mapping=observed.get("battle_side_mapping") instanceof Obj actual?mapping(actual):legacyMapping(parent);
            }
        } catch(IllegalArgumentException|ArithmeticException invalidReceipt) {receipt=null;mapping=null;}
        List<Obj> subjects=new ArrayList<>();
        for(int id:active) {
            boolean bound=receipt!=null && subject!=null && subject==id;
            subjects.add(obj(f("army_id",number(id)),f("status",text("unavailable")),
                    f("unavailable_reason",bound?receipt.get("unavailable_reason"):text(present&&subject!=null&&subject==id?"same_frame_resume_receipt_invalid":"same_frame_resume_receipt_unavailable")),
                    f("missing_required_domains",bound?receipt.get("missing_required_domains"):Nil.INSTANCE),
                    f("source",bound?receipt.get("source"):Nil.INSTANCE),f("battle_side_mapping",bound?nullable(mapping):Nil.INSTANCE),
                    // Native query sequence is an unsigned 64-bit identity. Public JSON retains canonical decimal text.
                    f("battle_control_query_sequence",bound?text(sequence.toString()):Nil.INSTANCE)));
        }
        Obj annotation=obj(f("status",text("unavailable")),f("input_observation_ready",new Bool(false)),f("used_for_decision",new Bool(false)),
                f("provisional_comparison_status",text(provisional.isPresent()?"provisional_observed_comparison":"unavailable")),
                f("provisional_comparison_used_for_decision",new Bool(provisional.isPresent()&&yes(originalPlan.get("provisional_combat_comparison_used_for_decision")))),
                f("provisional_comparison",provisional.<Value>map(value->value).orElse(Nil.INSTANCE)),f("subjects",objects(subjects)));
        return put(originalPlan,"active_combat_resume_input",annotation);
    }
    @Override public Optional<Obj> observe(PlanningRequest request) {
        Value actual=OpportunityJson.parse(DefenderExitObservationCodec.evaluate(DriverJson.encode(request.observations().snapshot())));
        return actual==Nil.INSTANCE?Optional.empty():Optional.of(OpportunityJson.object(actual,"defender exit observation"));
    }
    private static Obj mapping(Obj actual) {
        var fields=new java.util.LinkedHashMap<String,Value>();
        for(String key:List.of("subject_side_index","opposing_side_index","subject_owner_character_id","side_scope",
                "same_side_public_cunit_ids_in_stored_order","opposing_side_public_cunit_ids_in_stored_order",
                "affected_public_cunit_ids_in_stored_order","unaffected_same_side_public_cunit_ids_in_stored_order"))
            fields.put(key,java.util.Objects.requireNonNull(actual.get(key),"missing normalized side mapping "+key));
        return new Obj(fields);
    }
    private static Obj legacyMapping(Obj parent) {
        int side=int32(parent.get("side_index"));require(side==0||side==1,"actual original combat side required");
        Obj same=OpportunityJson.object(parent.get(side==0?"attacker":"defender"),"same side");
        Obj opposing=OpportunityJson.object(parent.get(side==0?"defender":"attacker"),"opposing side");
        return obj(f("subject_side_index",number(side)),f("opposing_side_index",number(1-side)),
                f("subject_owner_character_id",parent.get("selected_owner_character_id")),f("side_scope",parent.get("side_scope")),
                f("same_side_public_cunit_ids_in_stored_order",units(same)),f("opposing_side_public_cunit_ids_in_stored_order",units(opposing)),
                f("affected_public_cunit_ids_in_stored_order",parent.get("affected_public_cunit_ids_in_stored_order")),
                f("unaffected_same_side_public_cunit_ids_in_stored_order",parent.get("unaffected_same_side_public_cunit_ids_in_stored_order")));
    }
    private static Arr units(Obj side) {
        return new Arr(rows(side.get("ordered_armies")).stream().<Value>map(row->row.get("public_cunit_id")).toList());
    }
}
