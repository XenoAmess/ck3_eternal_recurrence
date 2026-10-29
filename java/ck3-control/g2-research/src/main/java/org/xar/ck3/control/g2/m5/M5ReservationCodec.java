package org.xar.ck3.control.g2.m5;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Commitments;
import org.xar.ck3.control.g2.m5.M5FrameDispatcher.Dispatch;
import org.xar.ck3.control.g2.m5.M5FrameDispatcher.ObservedCost;
import org.xar.ck3.control.g2.m5.M5FrameDispatcher.Reservation;
import org.xar.ck3.control.g2.m5.M5FrameDispatcher.Status;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Domain;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Existing reservation wire contract. Reading it grants no owner, lock or formal action right. */
public final class M5ReservationCodec {
    private static final String POLICY = "g2-m5-single-frame-dispatch-v1";
    private static final String SCHEMA = "xar.ck3.m5-frame-reservation.v1";
    private M5ReservationCodec() { }

    public static byte[] encode(Dispatch value) {
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("policy", new Text(POLICY)); fields.put("status", new Text(value.status().name()));
        fields.put("frame", frame(value.frame())); fields.put("selected_candidate_id", value.selectedCandidateId().<Value>map(Text::new).orElse(Nil.INSTANCE));
        fields.put("reservation", value.reservation().<Value>map(M5ReservationCodec::reservation).orElse(Nil.INSTANCE));
        fields.put("analysis", value.analysis().<Value>map(item -> item).orElse(Nil.INSTANCE));
        fields.put("selected_step", Nil.INSTANCE); fields.put("formal_action_ready", new Bool(false));
        return OpportunityJson.encode(new Obj(fields));
    }

    public static Dispatch decode(byte[] raw) {
        Obj row = M5PayloadCodec.parseObject(raw, "saved M5 dispatch");
        exact(row, Set.of("policy", "status", "frame", "selected_candidate_id", "reservation", "analysis", "selected_step", "formal_action_ready"));
        require(new Text(POLICY).equals(row.get("policy")) && row.get("selected_step") == Nil.INSTANCE && new Bool(false).equals(row.get("formal_action_ready")), "saved analytic dispatch cannot grant a formal action");
        Frame frame = M5FrameDispatcher.frame(object(row.get("frame"), "dispatch frame"), true);
        Optional<String> selected = row.get("selected_candidate_id") == Nil.INSTANCE ? Optional.empty() : Optional.of(text(row.get("selected_candidate_id"), "selected candidate"));
        Optional<Reservation> reservation = row.get("reservation") == Nil.INSTANCE ? Optional.empty() : Optional.of(reservation(object(row.get("reservation"), "reservation"), frame));
        Optional<Obj> analysis = row.get("analysis") == Nil.INSTANCE ? Optional.empty() : Optional.of(object(row.get("analysis"), "analysis"));
        Dispatch result = new Dispatch(Status.valueOf(text(row.get("status"), "dispatch status")), frame, selected, reservation, analysis);
        analysis.ifPresent(value -> {
            require(new Text("g2-m5-observed-opportunity-selector-v1").equals(value.get("policy"))
                    && new Bool(false).equals(value.get("formal_action_ready")) && value.get("selected_step") == Nil.INSTANCE,
                    "saved reservation must retain the original analytic selector boundary");
            require(frame.equals(M5FrameDispatcher.frame(object(value.get("frame"), "analysis frame"), true)), "saved analysis crossed reservation frame");
            Value actualSelected = value.get("selected_candidate_id");
            require(selected.<Value>map(Text::new).orElse(Nil.INSTANCE).equals(actualSelected), "saved analysis selected identity differs");
            require(new Text(selected.isPresent() ? "selected" : "wait").equals(value.get("status")), "saved analysis status differs");
        });
        return result;
    }

    private static Obj reservation(Reservation value) {
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("schema", new Text(SCHEMA)); fields.put("frame", frame(value.frame())); fields.put("candidate_id", new Text(value.candidateId()));
        fields.put("domain", new Text(value.domain().name())); fields.put("source_policy", new Text(value.sourcePolicy()));
        fields.put("commitments_after", commitments(value.frame(), value.commitmentsAfter())); fields.put("status", new Text("analytic_only_pending_formal_action"));
        ObservedCost cost = value.observedCost();
        fields.put("observed_opportunity_cost", new Obj(Map.of("gold_cost_raw", new IntegerValue(cost.goldCostRaw()), "war_slot_claim", new IntegerValue(cost.warSlotClaim()),
                "projected_supply_margin_raw", cost.projectedSupplyMarginRaw().<Value>map(IntegerValue::new).orElse(Nil.INSTANCE))));
        return new Obj(fields);
    }
    private static Reservation reservation(Obj value, Frame frame) {
        exact(value, Set.of("schema", "frame", "candidate_id", "domain", "source_policy", "commitments_after", "status", "observed_opportunity_cost"));
        require(new Text(SCHEMA).equals(value.get("schema")) && new Text("analytic_only_pending_formal_action").equals(value.get("status")), "exact analytic reservation contract required");
        require(frame.equals(M5FrameDispatcher.frame(object(value.get("frame"), "reservation frame"), true)), "saved reservation frame differs");
        Obj cost = object(value.get("observed_opportunity_cost"), "observed cost"); exact(cost, Set.of("gold_cost_raw", "war_slot_claim", "projected_supply_margin_raw"));
        Value supply = cost.get("projected_supply_margin_raw");
        return new Reservation(frame, text(value.get("candidate_id"), "candidate ID"), Domain.valueOf(text(value.get("domain"), "domain")), text(value.get("source_policy"), "source policy"),
                M5FrameDispatcher.commitments(object(value.get("commitments_after"), "commitments after"), frame),
                new ObservedCost(nonnegative(cost.get("gold_cost_raw"), "gold cost"), nonnegative(cost.get("war_slot_claim"), "war slot"), supply == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(supply, "observed supply"))));
    }
    static Obj frame(Frame value) {
        return new Obj(Map.of("played_character_id", new IntegerValue(value.playedCharacterId()), "native_revision", new IntegerValue(value.nativeRevision()), "date_raw", new IntegerValue(value.dateRaw()),
                "snapshot_id", new Text(value.snapshotId()), "revision", new IntegerValue(value.revision()), "episode_run_id", new Text(value.episodeRunId())));
    }
    private static Obj commitments(Frame frame, Commitments value) {
        Claims claims = value.claims();
        return new Obj(Map.of("frame", frame(frame), "gold_raw", new IntegerValue(value.goldRaw()), "pending_war_slots", new IntegerValue(value.pendingWarSlots()),
                "army_ids", numbers(claims.armyIds()), "ally_character_ids", numbers(claims.allyCharacterIds()), "character_ids", numbers(claims.characterIds()),
                "commitment_keys", new Arr(claims.commitmentKeys().stream().sorted(JointBudgetSelector::comparePythonText).<Value>map(Text::new).toList())));
    }
    private static Arr numbers(Set<BigInteger> values) { return new Arr(values.stream().sorted().<Value>map(IntegerValue::new).toList()); }
    private static void exact(Obj value, Set<String> expected) { require(value.members().keySet().equals(expected), "exact saved reservation fields required"); }
}
