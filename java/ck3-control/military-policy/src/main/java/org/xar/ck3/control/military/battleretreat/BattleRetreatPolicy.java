package org.xar.ck3.control.military.battleretreat;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure translation of the current single frozen tick diagnostic. Never submits an action. */
public final class BattleRetreatPolicy {
    public static final String POLICY_VERSION = "current-battle-retreat-diagnostic-v1";
    public static final String INPUT_SCHEMA = "current-battle-retreat-inputs/v1";

    private BattleRetreatPolicy() { }

    public enum Recommendation {
        QUERY_CURRENT_BATTLE_INPUTS("query_current_battle_inputs"),
        CONTINUE_ONE_OBSERVED_DAY("continue_one_observed_day"),
        QUERY_BATTLE_TERMINAL("query_battle_terminal"),
        QUERY_RETREAT_PREVIEW("query_retreat_preview"),
        ORDER_ACTIVE_COMBAT_RETREAT("order_active_combat_retreat");
        private final String wire;
        Recommendation(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum Scope {
        FULL_SIDE("full_side"), OWNER_SUBSET("owner_subset");
        private final String wire;
        Scope(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum Tool {
        QUERY_CURRENT("ck3_query_battle_control_snapshot_v1"),
        ADVANCE("ck3_execute_step"), TERMINAL("ck3_query_battle_terminal_transition_v1"),
        PREVIEW("ck3_preview_active_combat_retreat_v1"), ORDER("ck3_order_active_combat_retreat_v1");
        private final String wire;
        Tool(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record ObservedFrame(BigInteger snapshotRevision, long observedDateRaw, int combatId,
            int provinceId, int sideIndex, int selectedPublicCunitId, int selectedOwnerCharacterId,
            String phase, int phaseDay, Scope sideScope) {
        public ObservedFrame {
            uint64(snapshotRevision, true);
            StrictJson.require(combatId != -1, "combat ID must not be the missing sentinel");
            StrictJson.require(provinceId > 0 && selectedPublicCunitId >= 0
                    && selectedOwnerCharacterId > 0, "invalid battle identities");
            StrictJson.text(phase);
            Objects.requireNonNull(sideScope, "side scope");
        }
    }

    public record Legality(boolean legalNow, List<String> reasonCodesInNativeOrder,
            Long earliestDayGateDateRaw) {
        public Legality { reasonCodesInNativeOrder = strings(reasonCodesInNativeOrder); }
    }

    public record BattleFrame(ObservedFrame observed, boolean battleControlReady, int phaseRaw,
            int winnerRaw, int forcedWinnerRaw, boolean finalized, Legality legality) {
        public BattleFrame { Objects.requireNonNull(observed); Objects.requireNonNull(legality); }
    }

    public record TickFrame(BigInteger snapshotRevision, long observedDateRaw, int combatId,
            int provinceId, int subjectSideIndex, String phase, int phaseRaw, int phaseDay) {
        public TickFrame {
            uint64(snapshotRevision, true);
            StrictJson.require(combatId != -1 && provinceId > 0, "invalid tick identity");
            StrictJson.text(phase);
        }
    }

    public record OwnerDelta(int ownerCharacterId, BigInteger hardCasualtiesRawDelta) {
        public OwnerDelta { StrictJson.require(ownerCharacterId > 0, "invalid owner ID"); }
    }

    public record Losses(String status, List<OwnerDelta> ownerHardLedgerDeltas) {
        public Losses { StrictJson.text(status); ownerHardLedgerDeltas = List.copyOf(ownerHardLedgerDeltas); }
    }

    public record Attack(BigInteger storedLevyCurrentFightingRaw,
            boolean nativePrimaryLevyGetterObservedByRunner) {
        public Attack { Objects.requireNonNull(storedLevyCurrentFightingRaw); }
    }

    public record TickSide(Attack attack, Losses losses) {
        public TickSide { Objects.requireNonNull(attack); Objects.requireNonNull(losses); }
    }

    public record FrozenMainTick(TickFrame observedFrame, List<TickSide> sides,
            List<String> adapterMissingInputs) {
        public FrozenMainTick {
            Objects.requireNonNull(observedFrame);
            sides = List.copyOf(sides);
            adapterMissingInputs = strings(adapterMissingInputs);
        }
    }

    public record RetreatPreview(ObservedFrame battleControlSnapshot, boolean actionReady,
            String status, String unavailableReason, BigInteger sourceRevision,
            int targetProvinceId, String candidateToken) {
        public RetreatPreview {
            Objects.requireNonNull(battleControlSnapshot);
            StrictJson.text(status);
            if (unavailableReason != null) { StrictJson.text(unavailableReason); }
            uint64(sourceRevision, false);
            StrictJson.require(targetProvinceId > 0, "positive target province required");
            if (candidateToken != null) { StrictJson.text(candidateToken); }
            StrictJson.require(!actionReady || !status.equals("available") || candidateToken != null,
                    "available ready preview requires candidate token");
        }
    }

    public record Request(BattleFrame battleFrame, BigInteger maximumNextTickHardLossRaw,
            FrozenMainTick frozenMainTick, RetreatPreview retreatPreview) {
        public Request {
            Objects.requireNonNull(battleFrame);
            nonnegative(maximumNextTickHardLossRaw, "maximum_next_tick_hard_loss_raw");
        }
    }

    public sealed interface Arguments permits SubjectArmy, TerminalQuery, AdvanceDay, SelectedArmy, RetreatOrder { }
    public record SubjectArmy(int subjectArmyId) implements Arguments {
        public SubjectArmy { StrictJson.require(subjectArmyId >= 0, "public CUnit ID must be nonnegative"); }
    }
    public record TerminalQuery(int priorCombatId, int subjectPublicCunitId) implements Arguments {
        public TerminalQuery {
            StrictJson.require(priorCombatId != -1 && subjectPublicCunitId >= 0, "invalid terminal query identities");
        }
    }
    public record AdvanceDay() implements Arguments { }
    public record SelectedArmy(int selectedPublicCunitId) implements Arguments {
        public SelectedArmy { StrictJson.require(selectedPublicCunitId >= 0, "public CUnit ID must be nonnegative"); }
    }
    public record RetreatOrder(int selectedPublicCunitId, BigInteger expectedRevision,
            int expectedCombatId, int expectedSideIndex, Scope expectedScope,
            int targetProvinceId, String candidateToken) implements Arguments {
        public RetreatOrder {
            StrictJson.require(selectedPublicCunitId >= 0 && expectedCombatId != -1
                    && (expectedSideIndex == 0 || expectedSideIndex == 1) && targetProvinceId > 0,
                    "invalid retreat order identities");
            uint64(expectedRevision, false);
            Objects.requireNonNull(expectedScope);
            StrictJson.text(candidateToken);
        }
    }

    public record Decision(ObservedFrame observedFrame, BigInteger maximumNextTickHardLossRaw,
            BigInteger selectedOwnerNextTickHardLossRaw, Boolean budgetExceeded, Legality legality,
            List<String> requiredInputs, Recommendation recommendation, String reason, Tool proposedTool,
            Arguments proposedToolArguments, RetreatOrder retreatOrderArguments,
            Integer observationDays, String postActionRule) {
        public Decision {
            Objects.requireNonNull(observedFrame); Objects.requireNonNull(legality);
            nonnegative(maximumNextTickHardLossRaw, "budget");
            if (selectedOwnerNextTickHardLossRaw != null) { nonnegative(selectedOwnerNextTickHardLossRaw, "hard loss"); }
            requiredInputs = strings(requiredInputs);
            Objects.requireNonNull(recommendation); StrictJson.text(reason);
            Objects.requireNonNull(proposedTool); Objects.requireNonNull(proposedToolArguments);
        }
    }

    public static Decision assess(Request request) {
        Objects.requireNonNull(request);
        BattleFrame frame = request.battleFrame();
        ObservedFrame observed = frame.observed();
        int side = observed.sideIndex();
        if (!frame.battleControlReady() || (side != 0 && side != 1)) {
            return query(request, "normalized_current_player_battle_control");
        }
        if (frame.finalized() || observed.phase().equals("done")) {
            return decision(request, null, null, List.of(), Recommendation.QUERY_BATTLE_TERMINAL,
                    "observed_battle_is_terminal", Tool.TERMINAL,
                    new TerminalQuery(observed.combatId(), observed.selectedPublicCunitId()), null, null, null);
        }
        if (observed.phase().equals("pursuit") || frame.winnerRaw() != -1 || frame.forcedWinnerRaw() != -1) {
            return observe(request, null, null, "native_result_or_pursuit_already_selected");
        }
        if (observed.phase().equals("maneuver")) {
            return observe(request, null, null, "maneuver_has_no_current_main_tick_loss_comparison");
        }
        if (!observed.phase().equals("main")) { return query(request, "current_combat_phase"); }
        FrozenMainTick tick = request.frozenMainTick();
        if (tick == null) { return query(request, "same_frame_frozen_main_tick"); }
        TickFrame expected = new TickFrame(observed.snapshotRevision(), observed.observedDateRaw(),
                observed.combatId(), observed.provinceId(), side, observed.phase(), frame.phaseRaw(), observed.phaseDay());
        if (!tick.observedFrame().equals(expected)) { return query(request, "frozen_main_tick_from_this_current_frame"); }
        if (tick.sides().size() != 2) { return query(request, "current_main_tick_side_loss_operands"); }
        Losses ownLosses = tick.sides().get(side).losses();
        Attack opposingAttack = tick.sides().get(1 - side).attack();
        if (!ownLosses.status().equals("available")) {
            return query(request, tick.adapterMissingInputs().isEmpty()
                    ? List.of("current_loss_or_active_counter_operands") : tick.adapterMissingInputs());
        }
        if (opposingAttack.storedLevyCurrentFightingRaw().signum() > 0
                && !opposingAttack.nativePrimaryLevyGetterObservedByRunner()) {
            return query(request, "current_loss_inputs_v1.sides[" + (1 - side) + "].levy_damage_raw");
        }
        List<OwnerDelta> ownRows = ownLosses.ownerHardLedgerDeltas().stream()
                .filter(row -> row.ownerCharacterId() == observed.selectedOwnerCharacterId()).toList();
        if (ownRows.size() != 1 || ownRows.getFirst().hardCasualtiesRawDelta() == null
                || ownRows.getFirst().hardCasualtiesRawDelta().signum() < 0) {
            return query(request, "selected_owner_current_entry_hard_loss_delta");
        }
        BigInteger hard = ownRows.getFirst().hardCasualtiesRawDelta();
        boolean exceeded = hard.compareTo(request.maximumNextTickHardLossRaw()) > 0;
        if (!exceeded) { return observe(request, hard, false, "frozen_selected_owner_hard_loss_within_caller_budget"); }
        if (!frame.legality().legalNow()) {
            return observe(request, hard, true, "caller_budget_exceeded_but_native_retreat_unavailable");
        }
        String reason = "caller_budget_exceeded_requires_current_native_route_preview";
        RetreatPreview preview = request.retreatPreview();
        if (preview != null) {
            if (!preview.battleControlSnapshot().equals(observed)) {
                reason = "recompute_frozen_tick_from_preview_current_battle_frame";
            } else if (!preview.actionReady() || !preview.status().equals("available")) {
                reason = preview.unavailableReason() == null ? "native_route_preview_unavailable" : preview.unavailableReason();
            } else {
                RetreatOrder order = new RetreatOrder(observed.selectedPublicCunitId(), preview.sourceRevision(),
                        observed.combatId(), side, observed.sideScope(), preview.targetProvinceId(), preview.candidateToken());
                return decision(request, hard, true, List.of(), Recommendation.ORDER_ACTIVE_COMBAT_RETREAT,
                        "caller_budget_exceeded_and_current_native_route_preview_available", Tool.ORDER,
                        order, order, null,
                        "independent affected armies retreat state/target/route and prior-combat transition, then normal SAVE");
            }
        }
        return decision(request, hard, true,
                List.of("caller_selected_current_target_province_id", "normalized_same_frame_retreat_preview"),
                Recommendation.QUERY_RETREAT_PREVIEW, reason, Tool.PREVIEW,
                new SelectedArmy(observed.selectedPublicCunitId()), null, null, null);
    }

    private static Decision query(Request request, String missing) { return query(request, List.of(missing)); }
    private static Decision query(Request request, List<String> missing) {
        return decision(request, null, null, missing, Recommendation.QUERY_CURRENT_BATTLE_INPUTS,
                "current_frozen_selected_owner_loss_unavailable", Tool.QUERY_CURRENT,
                new SubjectArmy(request.battleFrame().observed().selectedPublicCunitId()), null, null, null);
    }

    private static Decision observe(Request request, BigInteger hard, Boolean exceeded, String reason) {
        return decision(request, hard, exceeded, List.of(), Recommendation.CONTINUE_ONE_OBSERVED_DAY,
                reason, Tool.ADVANCE, new AdvanceDay(), null, 1,
                "fresh paused snapshot/control or prior-combat terminal query, then normal SAVE");
    }

    private static Decision decision(Request request, BigInteger hard, Boolean exceeded, List<String> missing,
            Recommendation recommendation, String reason, Tool tool, Arguments arguments,
            RetreatOrder order, Integer days, String postRule) {
        return new Decision(request.battleFrame().observed(), request.maximumNextTickHardLossRaw(), hard,
                exceeded, request.battleFrame().legality(), missing, recommendation, reason, tool,
                arguments, order, days, postRule);
    }

    private static void uint64(BigInteger value, boolean positive) {
        Objects.requireNonNull(value);
        StrictJson.require(value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0
                && value.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 outside range");
    }

    private static void nonnegative(BigInteger value, String field) {
        StrictJson.require(value != null && value.signum() >= 0, field + " must be a nonnegative integer");
    }

    private static List<String> strings(List<String> values) {
        List<String> result = List.copyOf(values);
        result.forEach(StrictJson::text);
        return result;
    }
}
