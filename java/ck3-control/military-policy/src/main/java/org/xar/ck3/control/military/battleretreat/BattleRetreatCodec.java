package org.xar.ck3.control.military.battleretreat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.AdvanceDay;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Arguments;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Attack;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.BattleFrame;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Decision;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.FrozenMainTick;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Legality;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Losses;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.ObservedFrame;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.OwnerDelta;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Request;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.RetreatOrder;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.RetreatPreview;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Scope;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.SelectedArmy;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.SubjectArmy;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.TerminalQuery;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.TickFrame;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.TickSide;

/** Strict, bounded projection boundary; the existing native normalizers retain their qualification role. */
public final class BattleRetreatCodec {
    private static final Set<String> OBSERVED = Set.of("snapshot_revision", "observed_date_raw", "combat_id",
            "province_id", "side_index", "selected_public_cunit_id", "selected_owner_character_id",
            "phase", "phase_day", "side_scope");
    private static final Set<String> FRAME = Set.of("snapshot_revision", "observed_date_raw", "combat_id",
            "province_id", "side_index", "selected_public_cunit_id", "selected_owner_character_id",
            "phase", "phase_day", "side_scope", "battle_control_ready", "phase_raw", "winner_raw",
            "forced_winner_raw", "finalized", "legality");
    private static final Set<String> TICK_FRAME = Set.of("snapshot_revision", "observed_date_raw", "combat_id",
            "province_id", "subject_side_index", "phase", "phase_raw", "phase_day");

    private BattleRetreatCodec() { }

    public static Request decode(byte[] raw) { return decodeNode(StrictJson.parse(raw)); }

    public static Request decodeNode(JsonNode root) {
        ObjectNode request = StrictJson.object(root, Set.of("schema", "battle_frame",
                "maximum_next_tick_hard_loss_raw", "frozen_main_tick", "retreat_preview"));
        StrictJson.require(StrictJson.text(request.get("schema")).equals(BattleRetreatPolicy.INPUT_SCHEMA), "unsupported schema");
        return new Request(frame(request.get("battle_frame")), nonnegative(request.get("maximum_next_tick_hard_loss_raw")),
                request.get("frozen_main_tick").isNull() ? null : tick(request.get("frozen_main_tick")),
                request.get("retreat_preview").isNull() ? null : preview(request.get("retreat_preview")));
    }

    private static BattleFrame frame(JsonNode node) {
        ObjectNode object = StrictJson.object(node, FRAME);
        return new BattleFrame(observed(object), bool(object.get("battle_control_ready")), int32(object.get("phase_raw")),
                int32(object.get("winner_raw")), int32(object.get("forced_winner_raw")), bool(object.get("finalized")),
                legality(object.get("legality")));
    }

    private static ObservedFrame observed(JsonNode node) {
        return new ObservedFrame(uint64(node.get("snapshot_revision"), true), int64(node.get("observed_date_raw")),
                componentId(node.get("combat_id")), positiveInt32(node.get("province_id")), int32(node.get("side_index")),
                publicId(node.get("selected_public_cunit_id")), positiveInt32(node.get("selected_owner_character_id")),
                StrictJson.text(node.get("phase")), int32(node.get("phase_day")), scope(node.get("side_scope")));
    }

    private static Legality legality(JsonNode node) {
        ObjectNode object = StrictJson.object(node,
                Set.of("legal_now", "reason_codes_in_native_order", "earliest_day_gate_date_raw"));
        JsonNode earliest = object.get("earliest_day_gate_date_raw");
        return new Legality(bool(object.get("legal_now")), strings(object.get("reason_codes_in_native_order")),
                earliest.isNull() ? null : int64(earliest));
    }

    private static FrozenMainTick tick(JsonNode node) {
        ObjectNode object = StrictJson.object(node, Set.of("observed_frame", "sides", "adapter_missing_inputs"));
        ObjectNode frame = StrictJson.object(object.get("observed_frame"), TICK_FRAME);
        TickFrame observed = new TickFrame(uint64(frame.get("snapshot_revision"), true), int64(frame.get("observed_date_raw")),
                componentId(frame.get("combat_id")), positiveInt32(frame.get("province_id")), int32(frame.get("subject_side_index")),
                StrictJson.text(frame.get("phase")), int32(frame.get("phase_raw")), int32(frame.get("phase_day")));
        List<TickSide> sides = new ArrayList<>();
        for (JsonNode sideNode : array(object.get("sides"))) {
            ObjectNode side = StrictJson.object(sideNode, Set.of("attack", "losses"));
            ObjectNode attack = StrictJson.object(side.get("attack"),
                    Set.of("stored_levy_current_fighting_raw", "native_primary_levy_getter_observed_by_runner"));
            ObjectNode losses = StrictJson.object(side.get("losses"), Set.of("status", "owner_hard_ledger_deltas"));
            List<OwnerDelta> ledger = new ArrayList<>();
            for (JsonNode rowNode : array(losses.get("owner_hard_ledger_deltas"))) {
                ObjectNode row = StrictJson.object(rowNode, Set.of("owner_character_id", "hard_casualties_raw_delta"));
                JsonNode hard = row.get("hard_casualties_raw_delta");
                ledger.add(new OwnerDelta(positiveInt32(row.get("owner_character_id")), hard.isNull() ? null : integer(hard)));
            }
            sides.add(new TickSide(new Attack(integer(attack.get("stored_levy_current_fighting_raw")),
                    bool(attack.get("native_primary_levy_getter_observed_by_runner"))),
                    new Losses(StrictJson.text(losses.get("status")), ledger)));
        }
        return new FrozenMainTick(observed, sides, strings(object.get("adapter_missing_inputs")));
    }

    private static RetreatPreview preview(JsonNode node) {
        ObjectNode object = StrictJson.object(node, Set.of("battle_control_snapshot", "action_ready", "status",
                "unavailable_reason", "source_binding", "target_province_id", "target_preview"));
        ObjectNode source = StrictJson.object(object.get("source_binding"), Set.of("revision"));
        ObjectNode target = StrictJson.object(object.get("target_preview"), Set.of("candidate_token"));
        ObjectNode embedded = StrictJson.object(object.get("battle_control_snapshot"), OBSERVED);
        JsonNode reason = object.get("unavailable_reason");
        JsonNode token = target.get("candidate_token");
        return new RetreatPreview(observed(embedded), bool(object.get("action_ready")), StrictJson.text(object.get("status")),
                reason.isNull() ? null : StrictJson.text(reason), uint64(source.get("revision"), false),
                positiveInt32(object.get("target_province_id")), token.isNull() ? null : StrictJson.text(token));
    }

    public static byte[] encodeRequest(Request request) { return StrictJson.canonical(requestNode(request)); }

    public static ObjectNode requestNode(Request request) {
        ObjectNode result = StrictJson.object();
        result.put("schema", BattleRetreatPolicy.INPUT_SCHEMA);
        result.set("battle_frame", frameNode(request.battleFrame()));
        result.put("maximum_next_tick_hard_loss_raw", request.maximumNextTickHardLossRaw());
        if (request.frozenMainTick() == null) { result.putNull("frozen_main_tick"); }
        else { result.set("frozen_main_tick", tickNode(request.frozenMainTick())); }
        if (request.retreatPreview() == null) { result.putNull("retreat_preview"); }
        else { result.set("retreat_preview", previewNode(request.retreatPreview())); }
        return result;
    }

    private static ObjectNode frameNode(BattleFrame frame) {
        ObjectNode result = observedNode(frame.observed());
        result.put("battle_control_ready", frame.battleControlReady());
        result.put("phase_raw", frame.phaseRaw()); result.put("winner_raw", frame.winnerRaw());
        result.put("forced_winner_raw", frame.forcedWinnerRaw()); result.put("finalized", frame.finalized());
        ObjectNode legality = result.putObject("legality");
        legality.put("legal_now", frame.legality().legalNow());
        stringsNode(legality, "reason_codes_in_native_order", frame.legality().reasonCodesInNativeOrder());
        nullableLong(legality, "earliest_day_gate_date_raw", frame.legality().earliestDayGateDateRaw());
        return result;
    }

    private static ObjectNode observedNode(ObservedFrame frame) {
        ObjectNode result = StrictJson.object(); result.put("snapshot_revision", frame.snapshotRevision());
        result.put("observed_date_raw", frame.observedDateRaw()); result.put("combat_id", frame.combatId());
        result.put("province_id", frame.provinceId()); result.put("side_index", frame.sideIndex());
        result.put("selected_public_cunit_id", frame.selectedPublicCunitId());
        result.put("selected_owner_character_id", frame.selectedOwnerCharacterId()); result.put("phase", frame.phase());
        result.put("phase_day", frame.phaseDay()); result.put("side_scope", frame.sideScope().wire());
        return result;
    }

    private static ObjectNode tickNode(FrozenMainTick tick) {
        ObjectNode result = StrictJson.object(); TickFrame frame = tick.observedFrame();
        ObjectNode observed = result.putObject("observed_frame");
        observed.put("snapshot_revision", frame.snapshotRevision()); observed.put("observed_date_raw", frame.observedDateRaw());
        observed.put("combat_id", frame.combatId()); observed.put("province_id", frame.provinceId());
        observed.put("subject_side_index", frame.subjectSideIndex()); observed.put("phase", frame.phase());
        observed.put("phase_raw", frame.phaseRaw()); observed.put("phase_day", frame.phaseDay());
        ArrayNode sides = result.putArray("sides");
        for (TickSide side : tick.sides()) {
            ObjectNode sideNode = sides.addObject(); ObjectNode attack = sideNode.putObject("attack");
            attack.put("stored_levy_current_fighting_raw", side.attack().storedLevyCurrentFightingRaw());
            attack.put("native_primary_levy_getter_observed_by_runner", side.attack().nativePrimaryLevyGetterObservedByRunner());
            ObjectNode losses = sideNode.putObject("losses"); losses.put("status", side.losses().status());
            ArrayNode rows = losses.putArray("owner_hard_ledger_deltas");
            for (OwnerDelta row : side.losses().ownerHardLedgerDeltas()) {
                ObjectNode entry = rows.addObject(); entry.put("owner_character_id", row.ownerCharacterId());
                nullableInteger(entry, "hard_casualties_raw_delta", row.hardCasualtiesRawDelta());
            }
        }
        stringsNode(result, "adapter_missing_inputs", tick.adapterMissingInputs()); return result;
    }

    private static ObjectNode previewNode(RetreatPreview preview) {
        ObjectNode result = StrictJson.object(); result.set("battle_control_snapshot", observedNode(preview.battleControlSnapshot()));
        result.put("action_ready", preview.actionReady()); result.put("status", preview.status());
        if (preview.unavailableReason() == null) { result.putNull("unavailable_reason"); }
        else { result.put("unavailable_reason", preview.unavailableReason()); }
        result.putObject("source_binding").put("revision", preview.sourceRevision());
        result.put("target_province_id", preview.targetProvinceId());
        ObjectNode target = result.putObject("target_preview");
        if (preview.candidateToken() == null) { target.putNull("candidate_token"); }
        else { target.put("candidate_token", preview.candidateToken()); }
        return result;
    }

    public static byte[] encodeDecision(Decision decision) {
        ObjectNode result = StrictJson.object(); result.put("policy_version", BattleRetreatPolicy.POLICY_VERSION);
        result.put("scope_kind", "own_selected_owner_single_frozen_main_tick_budget");
        result.put("readiness", "static_ready_diagnostic_not_execution"); result.set("observed_frame", observedNode(decision.observedFrame()));
        result.put("maximum_next_tick_hard_loss_raw", decision.maximumNextTickHardLossRaw()); result.put("budget_source", "explicit_caller_own_policy");
        nullableInteger(result, "selected_owner_next_tick_hard_loss_raw", decision.selectedOwnerNextTickHardLossRaw());
        if (decision.budgetExceeded() == null) { result.putNull("budget_exceeded"); }
        else { result.put("budget_exceeded", decision.budgetExceeded()); }
        result.put("native_retreat_legal_now", decision.legality().legalNow());
        stringsNode(result, "native_retreat_reason_codes", decision.legality().reasonCodesInNativeOrder());
        nullableLong(result, "earliest_day_gate_date_raw", decision.legality().earliestDayGateDateRaw());
        stringsNode(result, "required_inputs", decision.requiredInputs());
        if (decision.retreatOrderArguments() == null) { result.putNull("retreat_order_arguments"); }
        else { result.set("retreat_order_arguments", argumentsNode(decision.retreatOrderArguments())); }
        result.putNull("win_probability"); result.putNull("retreat_loss_raw");
        result.put("retreat_destination_safety_observed", false); result.put("complete_transition", false);
        stringsNode(result, "quality_gaps", List.of("generic_native_ai_active_battle_intent_and_target_ranking",
                "future_reinforcement_roster_and_advantage_changes", "retreat_pursuit_losses_and_destination_hostile_routes"));
        result.put("recommendation", decision.recommendation().wire()); result.put("reason", decision.reason());
        result.put("proposed_tool", decision.proposedTool().wire()); result.set("proposed_tool_arguments", argumentsNode(decision.proposedToolArguments()));
        result.put("requires_fresh_public_revision", true);
        if (decision.observationDays() != null) { result.put("observation_days", decision.observationDays()); }
        if (decision.postActionRule() != null) { result.put("post_action_rule", decision.postActionRule()); }
        return StrictJson.canonical(result, StrictJson.OUTPUT_MAX_BYTES);
    }

    private static ObjectNode argumentsNode(Arguments arguments) {
        ObjectNode result = StrictJson.object();
        switch (arguments) {
            case SubjectArmy value -> result.put("subject_army_id", value.subjectArmyId());
            case TerminalQuery value -> { result.put("prior_combat_id", value.priorCombatId()); result.put("subject_public_cunit_id", value.subjectPublicCunitId()); }
            case AdvanceDay ignored -> result.put("step", "life-advance-one-day");
            case SelectedArmy value -> result.put("selected_public_cunit_id", value.selectedPublicCunitId());
            case RetreatOrder value -> {
                result.put("selected_public_cunit_id", value.selectedPublicCunitId()); result.put("expected_revision", value.expectedRevision());
                result.put("expected_combat_id", value.expectedCombatId()); result.put("expected_side_index", value.expectedSideIndex());
                result.put("expected_scope", value.expectedScope().wire()); result.put("target_province_id", value.targetProvinceId());
                result.put("candidate_token", value.candidateToken());
            }
        }
        return result;
    }

    private static Scope scope(JsonNode value) {
        String text = StrictJson.text(value);
        for (Scope scope : Scope.values()) { if (scope.wire().equals(text)) { return scope; } }
        throw new IllegalArgumentException("unknown side scope");
    }

    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact JSON integer required");
        return value.bigIntegerValue();
    }

    private static BigInteger nonnegative(JsonNode value) {
        BigInteger result = integer(value); StrictJson.require(result.signum() >= 0, "nonnegative integer required"); return result;
    }

    private static BigInteger uint64(JsonNode value, boolean positive) {
        return StrictJson.integer(value, positive ? BigInteger.ONE : BigInteger.ZERO, StrictJson.UINT64_MAX);
    }

    private static int int32(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static long int64(JsonNode value) { return StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static int positiveInt32(JsonNode value) { return (int) StrictJson.integer(value, 1, Integer.MAX_VALUE); }
    private static int publicId(JsonNode value) { return (int) StrictJson.integer(value, 0, Integer.MAX_VALUE); }
    private static int componentId(JsonNode value) {
        int result = int32(value); StrictJson.require(result != -1, "missing component ID sentinel forbidden"); return result;
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue();
    }
    private static JsonNode array(JsonNode value) {
        StrictJson.require(value != null && value.isArray(), "JSON array required"); return value;
    }
    private static List<String> strings(JsonNode value) {
        List<String> result = new ArrayList<>(); for (JsonNode entry : array(value)) { result.add(StrictJson.text(entry)); } return result;
    }
    private static void stringsNode(ObjectNode parent, String key, List<String> values) {
        ArrayNode array = parent.putArray(key); values.forEach(array::add);
    }
    private static void nullableInteger(ObjectNode parent, String key, BigInteger value) {
        if (value == null) { parent.putNull(key); } else { parent.put(key, value); }
    }
    private static void nullableLong(ObjectNode parent, String key, Long value) {
        if (value == null) { parent.putNull(key); } else { parent.put(key, value); }
    }
}
