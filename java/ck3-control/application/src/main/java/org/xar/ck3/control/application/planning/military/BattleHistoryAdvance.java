package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.battleadvance.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** DRAFT/PARTIAL: strategy envelope reconciliation; not compiled, tested, or adopted by a policy. */
public final class BattleHistoryAdvance {
    private BattleHistoryAdvance() { }
    public record Validation(String step, boolean valid, List<String> errors, long elapsedDays,
            boolean terminalObserved, boolean sentinel, Obj evidence) {
        public Validation { errors = List.copyOf(errors); }
    }
    public static Optional<Validation> validate(Obj original) {
        if (original == null) return Optional.empty();
        String step = optionalText(original.get("step"));
        Optional<BattleAdvanceStep> parsed = BattleAdvanceStep.parse(step);
        if (parsed.isEmpty()) return Optional.empty();
        List<String> errors = new ArrayList<>();
        try {
            var profile = original.get("schema") == null ? BattleAdvanceResultCodec.Profile.LEGACY_NATIVE_V1
                    : BattleAdvanceResultCodec.Profile.JAVA_V1;
            var decoded = BattleAdvanceResultCodec.decode(new RawJson(OpportunityJson.encode(original)), profile);
            var request = parsed.orElseThrow();
            Obj envelope = decoded.envelope();
            int start = integer(envelope.get("starting_date_raw"), "start").intValueExact();
            int target = integer(envelope.get("target_date_raw"), "target").intValueExact();
            int end = integer(envelope.get("ending_date_raw"), "end").intValueExact();
            long elapsed = integer(envelope.get("elapsed_days"), "elapsed").longValueExact();
            List<Integer> watch = array(envelope.get("watch_army_ids"), "watch").stream()
                    .map(value -> integer(value, "public CUnit").intValueExact()).toList();
            require(!watch.isEmpty() && watch.size() <= 64 && watch.stream().allMatch(id -> id >= 0)
                    && watch.stream().distinct().count() == watch.size(), "watch_set_invalid");
            int maximum = request.scope() == BattleAdvanceStep.Scope.STATIONARY_OBJECTIVE_HOLD ? 7
                    : request.scope() == BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW ? 3 : 45;
            long horizon = (long) target - start;
            require(horizon >= 24 && horizon <= maximum * 24L && horizon % 24 == 0
                    && elapsed >= 0 && start + elapsed * 24 == end && end <= target, "date_tick_reconciliation_failed");
            if (request.requestedTarget().isPresent())
                require(request.requestedTarget().orElseThrow().equals(BigInteger.valueOf(target)), "typed step target differs");
            else if (decoded.plan().isPresent()) {
                var plan = decoded.plan().orElseThrow();
                require(plan.step().equals(step) && plan.startingDateRaw() == start && plan.targetDateRaw() == target
                        && plan.speed() == request.speed() && plan.scope() == request.scope()
                        && plan.watchArmyIds().equals(watch), "actual normalized durable plan differs");
                require(target == start + 45 * 24 || plan.campaignDeadline().isPresent(),
                        "generic capped target lacks actual campaign Cap");
            } else require(target == start + 45 * 24, "legacy generic horizon differs");
            var arm = decoded.armed().orElseThrow(() -> new IllegalArgumentException("sentinel_arm_missing"));
            var stop = decoded.sentinel().orElseThrow(() -> new IllegalArgumentException("sentinel_stop_missing"));
            var mode = request instanceof BattleAdvanceStep.Battle battle && battle.terminal()
                    ? LateOutcome.Mode.TERMINAL_OR_SENTINEL : LateOutcome.Mode.DECISION_EPOCH;
            BattleSentinelValidation.arm(arm, start, target, request.speed(), mode, watch, request.scope());
            var boundary = BattleAdvanceResultCodec.decodeBoundary(decoded);
            boolean canceled = false;
            if (boundary.isPresent()) {
                Obj rawBoundary = object(original.get("player_decision_boundary"), "player_decision_boundary");
                for (String key : List.of("snapshot_id", "revision", "native_revision", "bridge_pid", "connection_generation",
                        "episode_character_id", "episode_run_id", "played_character_id"))
                    require(rawBoundary.get(key) != null && rawBoundary.get(key).equals(original.get(key)), "decision owner/frame differs: " + key);
                require(boundary.orElseThrow().validIdentity(), "player_decision_boundary_identity_invalid");
                switch (boundary.orElseThrow().kind()) {
                    case ACTIVE_EVENT -> require(instance(original.get("active_event")).equals(boundary.orElseThrow().instanceId()), "active event identity differs");
                    case PENDING_CHARACTER_INTERACTION -> require(instance(original.get("pending_character_interaction")).equals(boundary.orElseThrow().instanceId()), "pending interaction identity differs");
                    case ONE_LIFE_TERMINAL -> require(truth(original.get("one_life_terminal"))
                            && boundary.orElseThrow().terminalReason().equals(Optional.of(text(original.get("one_life_terminal_reason"), "terminal reason")))
                            && boundary.orElseThrow().playedCharacterAlive().equals(Optional.of(bool(original.get("played_character_alive"), "alive"))),
                            "terminal boundary differs");
                    case ACTIVE_WAR_SET_CHANGED -> require(warIds(original.get("war_progress_before")).equals(boundary.orElseThrow().beforeWarIds())
                            && warIds(original.get("war_progress_after")).equals(boundary.orElseThrow().afterWarIds())
                            && absent(original.get("active_event")) && absent(original.get("pending_character_interaction")), "war set boundary differs");
                }
                if (!absent(original.get("player_decision_boundary_cancel"))) {
                    Obj cancel = object(original.get("player_decision_boundary_cancel"), "cancel");
                    require(cancel.members().keySet().equals(java.util.Set.of("step", "status", "generation"))
                            && ("research-cancel-tactical-daily-sentinel-v1-generation-" + arm.generation().decimal()).equals(text(cancel.get("step"), "cancel step"))
                            && "canceled".equals(text(cancel.get("status"), "cancel status"))
                            && generation(cancel.get("generation"), profile).equals(arm.generation().decimal()), "cancel evidence differs");
                    canceled = true;
                }
                BattleSentinelValidation.decision(stop, arm, start, target, end, request.speed(), mode, watch, boundary.orElseThrow(), canceled);
                require("player_decision".equals(text(envelope.get("stop_kind"), "stop_kind")), "decision stop kind differs");
                long pause = integer(envelope.get("player_decision_boundary_pause_count"), "boundary pause").longValueExact();
                require(pause >= 0 && pause <= 1 && pause == integer(envelope.get("external_pause_count"), "external pause").longValueExact()
                        && (stop.state() != LateOutcome.State.TRIGGERED || pause == 0), "decision pause ownership differs");
            } else {
                BattleSentinelValidation.stop(stop, arm, start, target, end, request.speed(), mode, watch);
                require(elapsed > 0 && (stop.terminalObserved() ? "terminal" : "decision_epoch").equals(optionalText(envelope.get("stop_kind"))),
                        "terminal stop kind differs");
                require(integer(envelope.get("external_pause_count"), "external_pause").signum() == 0, "external_pause_count differs");
            }
            boolean idle = stop.state() == LateOutcome.State.IDLE;
            require(integer(envelope.get("completed_daily_ticks"), "ticks").longValueExact() == stop.completedDailyTicks()
                    && (idle ? stop.completedDailyTicks() <= elapsed : stop.completedDailyTicks() == elapsed), "completed ticks differ");
            require(stop.generation().decimal().equals(generation(envelope.get("sentinel_generation"), profile)), "generation differs");
            String modeWire = mode.name().toLowerCase(Locale.ROOT), scopeWire = request.scope().name().toLowerCase(Locale.ROOT);
            require(integer(envelope.get("timeline_speed"), "speed").intValueExact() == request.speed()
                    && modeWire.equals(optionalText(envelope.get("timeline_policy")))
                    && modeWire.equals(optionalText(envelope.get("sentinel_mode")))
                    && scopeWire.equals(optionalText(envelope.get("sentinel_scope")))
                    && "postcondition".equals(optionalText(envelope.get("progress_status")))
                    && integer(envelope.get("requested_horizon_days"), "horizon").longValueExact() == horizon / 24
                    && bool(envelope.get("paused"), "paused"), "composite completion metadata differs");
            require(integer(envelope.get("intermediate_pause_count"), "intermediate pauses").longValueExact() == stop.intermediatePauseCount()
                    && integer(envelope.get("overshoot_days"), "overshoot").longValueExact() == stop.overshootDays()
                    && bool(envelope.get("zero_intermediate_pause"), "zero pause") == (stop.intermediatePauseCount() == 0)
                    && bool(envelope.get("terminal_reached"), "terminal reached") == stop.terminalObserved()
                    && array(envelope.get("trigger_reasons"), "reasons").stream().map(value -> text(value, "reason")).toList().equals(stop.triggerReasons())
                    && integer(envelope.get("external_rich_query_count"), "external queries").signum() == 0, "public completion differs from actual sentinel");
            require(stop.terminalObserved() == stop.triggerReasons().contains("combat_terminal"), "terminal_flag_disagrees");
            Obj cleanup = object(envelope.get("managed_failure_cleanup"), "cleanup");
            require(new Bool(false).equals(cleanup.get("attempted")) && cleanup.get("error") == Nil.INSTANCE, "cleanup cannot prove natural completion");
            if (request instanceof BattleAdvanceStep.Hold hold) holdBinding(envelope, hold, watch, boundary);
            return Optional.of(new Validation(step, true, List.of(), elapsed,
                    boundary.isEmpty() && stop.terminalObserved(), true, envelope));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            errors.add(invalid.getMessage() == null ? invalid.getClass().getSimpleName() : invalid.getMessage());
            return Optional.of(new Validation(step, false, errors, -1, false, true, original));
        }
    }
    private static void holdBinding(Obj envelope, BattleAdvanceStep.Hold hold, List<Integer> watch,
            Optional<BattleAdvanceFrame.Boundary> boundary) {
        Obj request = object(envelope.get("war_objective_hold_request"), "hold request");
        require(request.members().keySet().equals(java.util.Set.of("sentinel_scope", "war_id", "subject_army_id", "objective_province_id", "target_date_raw")),
                "hold request fields differ");
        bind(request, hold, null);
        require(integer(request.get("target_date_raw"), "hold target").equals(hold.targetDateRaw()), "hold target differs");
        Obj admission = object(envelope.get("war_objective_hold_admission"), "hold admission");
        Obj stop = object(envelope.get("war_objective_hold_post_stop"), "hold post stop");
        bind(admission, hold, watch); bind(stop, hold, watch);
        require("matched".equals(optionalText(admission.get("status"))), "hold admission differs");
        String state = text(stop.get("status"), "hold post stop status");
        require(state.equals("matched") || state.equals("invalidated"), "hold unavailable is not invalidated");
        if (boundary.isPresent() && boundary.orElseThrow().kind() != BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED)
            require(state.equals("invalidated") && "pending_player_decision".equals(optionalText(stop.get("reason"))), "hold decision boundary differs");
        require(new Bool(false).equals(envelope.get("exact_war_terminal_watch"))
                && new Bool(false).equals(envelope.get("exact_active_war_set_watch"))
                && integer(envelope.get("maximum_omitted_state_detection_lag_days"), "omitted lag").equals(BigInteger.valueOf(7)),
                "hold omitted-watch boundary differs");
        if (boundary.isEmpty()) require(new Bool(false).equals(stop.get("exact_war_terminal_watch"))
                && new Bool(false).equals(stop.get("exact_active_war_set_watch")), "post-stop watch boundary differs");
    }
    private static void bind(Obj row, BattleAdvanceStep.Hold hold, List<Integer> watch) {
        require("stationary_objective_hold".equals(optionalText(row.get("sentinel_scope")))
                && integer(row.get("war_id"), "war").intValueExact() == hold.warId()
                && integer(row.get("subject_army_id"), "subject").intValueExact() == hold.armyId()
                && integer(row.get("objective_province_id"), "objective").intValueExact() == hold.objectiveProvinceId(), "hold binding differs");
        if (watch != null) require(array(row.get("watch_army_ids"), "hold watch").stream()
                .map(value -> integer(value, "watch").intValueExact()).toList().equals(watch), "hold watch differs");
    }
    private static String generation(Value value, BattleAdvanceResultCodec.Profile profile) {
        if (profile == BattleAdvanceResultCodec.Profile.JAVA_V1)
            return new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(text(value, "generation")).decimal();
        BigInteger number = integer(value, "legacy generation");
        require(number.signum() >= 0 && number.bitLength() <= 64, "legacy uint64 generation required"); return number.toString();
    }
    private static Optional<Value> instance(Value raw) {
        if (!(raw instanceof Obj value) || absent(value.get("instance_id"))) return Optional.empty();
        return Optional.of(value.get("instance_id"));
    }
    private static List<Integer> warIds(Value raw) {
        Obj summary = object(raw, "war summary");
        List<Integer> ids = array(summary.get("wars"), "wars").stream()
                .map(value -> integer(object(value, "war").get("war_id"), "war_id").intValueExact()).sorted().toList();
        require(ids.stream().allMatch(id -> id > 0) && ids.stream().distinct().count() == ids.size(), "war summary identities differ");
        return ids;
    }
    private static String optionalText(Value value) { return value instanceof Text text ? text.value() : null; }
    private static boolean truth(Value value) { return new Bool(true).equals(value); }
    private static boolean absent(Value value) { return value == null || value == Nil.INSTANCE; }
}

