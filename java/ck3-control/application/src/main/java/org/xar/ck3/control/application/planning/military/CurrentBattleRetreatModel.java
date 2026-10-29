package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.wave2.military.forecast.CombatCore.DrawState;
import org.xar.ck3.control.wave2.military.forecast.CurrentBattleConditionCodec;
import org.xar.ck3.control.wave2.military.forecast.CurrentBattleConditionCodec.ObservedInputs;
import org.xar.ck3.control.wave2.military.forecast.FrozenCurrentBattleRunner;

/** Actual normalized current-control -> shared casualty runner -> ordinary retreat request. */
public final class CurrentBattleRetreatModel implements ActiveRetreatProposal.CurrentLossModel {
    @FunctionalInterface public interface AdditionalObservedOperands { ObservedInputs collect(Obj normalizedControl); }
    private final AdditionalObservedOperands operands;
    private final DrawState callerDrawState;
    /** Original native-control-only call: additional backing/resume/levy operands are explicitly unprovided. */
    public CurrentBattleRetreatModel() { this(new NativeControlOnly(), new DrawState(0, 0)); }
    public CurrentBattleRetreatModel(AdditionalObservedOperands operands, DrawState callerDrawState) { this.operands = Objects.requireNonNull(operands); this.callerDrawState = Objects.requireNonNull(callerDrawState); }
    private static final class NativeControlOnly implements AdditionalObservedOperands {
        @Override public ObservedInputs collect(Obj normalizedControl) { Objects.requireNonNull(normalizedControl); return ObservedInputs.empty(); }
    }
    @Override public BattleRetreatPolicy.Request inputs(Obj normalizedCurrentControl, BigInteger budget, Optional<Obj> normalizedPreview) {
        Objects.requireNonNull(normalizedCurrentControl); Objects.requireNonNull(normalizedPreview);
        var condition = CurrentBattleConditionCodec.adapt(OpportunityJson.toNode(normalizedCurrentControl), Objects.requireNonNull(operands.collect(normalizedCurrentControl)));
        var result = FrozenCurrentBattleRunner.run(condition, callerDrawState);
        return new BattleRetreatPolicy.Request(battleFrame(normalizedCurrentControl), budget, result.toRetreatTick(), normalizedPreview.map(CurrentBattleRetreatModel::preview).orElse(null));
    }
    private static BattleRetreatPolicy.BattleFrame battleFrame(Obj control) {
        Obj legal = object(control.get("legality"), "native legality");
        List<String> reasons = OpportunityJson.array(legal.get("reason_codes_in_native_order"), "native legal reasons").stream().map(v -> OpportunityJson.text(v, "native legal reason")).toList();
        Value earliest = legal.get("earliest_day_gate_date_raw"); Long earliestDate = nil(earliest) ? null : integer(earliest, "earliest native gate").longValueExact();
        return new BattleRetreatPolicy.BattleFrame(observed(control), OpportunityJson.bool(control.get("battle_control_ready"), "battle_control_ready"), int32(control.get("phase_raw"), "phase_raw"), int32(control.get("winner_raw"), "winner_raw"), int32(control.get("forced_winner_raw"), "forced_winner_raw"), OpportunityJson.bool(control.get("finalized"), "finalized"), new BattleRetreatPolicy.Legality(OpportunityJson.bool(legal.get("legal_now"), "legal_now"), reasons, earliestDate));
    }
    private static BattleRetreatPolicy.ObservedFrame observed(Obj control) {
        return new BattleRetreatPolicy.ObservedFrame(integer(control.get("snapshot_revision"), "snapshot_revision"), integer(control.get("observed_date_raw"), "observed_date_raw").longValueExact(), int32(control.get("combat_id"), "combat_id"), int32(control.get("combat_province_id"), "combat_province_id"), int32(control.get("side_index"), "side_index"), int32(control.get("selected_public_cunit_id"), "selected_public_cunit_id"), int32(control.get("selected_owner_character_id"), "selected_owner_character_id"), OpportunityJson.text(control.get("phase"), "phase"), int32(control.get("phase_day"), "phase_day"), scope(control.get("side_scope")));
    }
    private static BattleRetreatPolicy.RetreatPreview preview(Obj preview) {
        Obj control = object(preview.get("battle_control_snapshot"), "preview control"); Obj source = object(preview.get("source_binding"), "preview source");
        Value reason = preview.get("unavailable_reason"), target = preview.get("target_preview"); String token = null;
        if (!nil(target)) { Value raw = object(target, "preview route").get("candidate_token"); if (!nil(raw)) token = OpportunityJson.text(raw, "candidate_token"); }
        return new BattleRetreatPolicy.RetreatPreview(observed(control), OpportunityJson.bool(preview.get("action_ready"), "preview action_ready"), OpportunityJson.text(preview.get("status"), "preview status"), nil(reason) ? null : OpportunityJson.text(reason, "preview reason"), integer(source.get("revision"), "preview source revision"), int32(preview.get("target_province_id"), "preview target"), token);
    }
    private static BattleRetreatPolicy.Scope scope(Value raw) {
        return switch (OpportunityJson.text(raw, "side_scope")) { case "full_side" -> BattleRetreatPolicy.Scope.FULL_SIDE; case "owner_subset" -> BattleRetreatPolicy.Scope.OWNER_SUBSET; default -> throw new IllegalArgumentException("unknown native battle side scope"); };
    }
    private static Obj object(Value value, String name) { return OpportunityJson.object(value, name); }
    private static BigInteger integer(Value value, String name) { return OpportunityJson.integer(value, name); }
    private static int int32(Value value, String name) { return integer(value, name).intValueExact(); }
    private static boolean nil(Value value) { return value == null || value == Nil.INSTANCE; }
}
