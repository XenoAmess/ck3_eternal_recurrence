package org.xar.ck3.control.vanilla.schemesway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.planning.swayreuse.ReusedSwayOpportunity;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;

/** A strict compact projection boundary; no JSON paths are opened or interpreted as authority. */
public final class SwayScheduleWire {
    private static final BigInteger MAX = BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER);
    private static final BigInteger MIN = MAX.negate();
    private SwayScheduleWire() { }

    public static Request decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("source", "snapshot", "selected_step",
                "root", "ledger", "state", "active_observation_only"));
        return new Request(source(row.get("source")), optional(row.get("snapshot")).map(SwayScheduleWire::frame),
                "life-advance".equals(StrictJson.text(row.get("selected_step"))) ? Step.LIFE_ADVANCE : Step.OTHER,
                optional(row.get("root")).map(SwayScheduleWire::root), ledger(row.get("ledger")),
                optional(row.get("state")).map(SwayScheduleWire::state), flag(row.get("active_observation_only")));
    }

    public static byte[] encode(Decision decision) {
        ObjectNode row = StrictJson.object();
        if (decision.job().isPresent()) { row.put("job", name(decision.job().orElseThrow())); }
        else { row.putNull("job"); }
        row.put("reason", name(decision.reason()));
        row.set("state", decision.state().map(SwayScheduleWire::stateJson).orElseGet(StrictJson::object));
        if (decision.job().isPresent()) {
            row.put("submit_allowed", false);
            decision.targetCharacterId().ifPresent(value -> row.put("target_character_id", value));
            decision.actionId().ifPresent(value -> row.put("action_id", value));
            if (decision.job().orElseThrow() == Job.QUERY_SELECTED_TARGET) { row.put("native_ai_rank_claimed", false); }
        }
        return StrictJson.canonical(row);
    }

    public static State decodeState(byte[] raw) { return state(StrictJson.parse(raw)); }
    public static byte[] encodeState(State state) { return StrictJson.canonical(stateJson(state)); }

    private static G2Source source(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "observed_at_utc", "exact_build", "source_ref"));
        return new G2Source(StrictJson.text(row.get("machine_id")), StrictJson.text(row.get("observed_at_utc")),
                StrictJson.text(row.get("exact_build")), ExactRef.fromJson(row.get("source_ref")));
    }
    private static Frame frame(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("snapshot_id", "revision", "native_revision", "date_raw",
                "paused", "map_ready", "played_character", "active_context"));
        ObjectNode actor = StrictJson.object(row.get("played_character"), Set.of("character_id", "alive"));
        JsonNode context = row.get("active_context");
        Context kind = Context.UNAVAILABLE;
        if (!context.isNull()) {
            ObjectNode active = StrictJson.object(context, Set.of("active_event", "pending_character_interaction"));
            kind = active.get("active_event").isNull() && active.get("pending_character_interaction").isNull()
                    ? Context.CLEAR : Context.MANDATORY;
        }
        return new Frame(StrictJson.text(row.get("snapshot_id")), positive(row.get("revision")),
                positive(row.get("native_revision")), integer(row.get("date_raw")), character(actor.get("character_id")),
                flag(row.get("paused")), flag(row.get("map_ready")), flag(actor.get("alive")), kind);
    }
    private static Root root(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("status", "player_character_id", "player_character_alive",
                "snapshot_revision", "date_raw", "direct_landed_vassal_character_ids"));
        return new Root("available".equals(StrictJson.text(row.get("status"))), character(row.get("player_character_id")),
                flag(row.get("player_character_alive")), positive(row.get("snapshot_revision")), integer(row.get("date_raw")),
                optional(row.get("direct_landed_vassal_character_ids")).map(SwayScheduleWire::characters));
    }
    private static Ledger ledger(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("pending", "resolved"));
        Optional<Pending> pending = optional(row.get("pending")).map(node -> {
            ObjectNode item = StrictJson.object(node, Set.of("action_id", "actor_character_id", "target_character_id"));
            return new Pending(StrictJson.text(item.get("action_id")), character(item.get("actor_character_id")),
                    character(item.get("target_character_id")));
        });
        Optional<Resolved> resolved = optional(row.get("resolved")).map(node -> {
            ObjectNode item = StrictJson.object(node, Set.of("identity", "applied", "postcondition_verified", "terminal_observed", "reuse_gap"));
            ObjectNode identity = StrictJson.object(item.get("identity"), Set.of("action_id", "actor_character_id",
                    "target_character_id", "scheme_instance_id", "scheme_instance_generation"));
            Identity held = new Identity(StrictJson.text(identity.get("action_id")), character(identity.get("actor_character_id")),
                    character(identity.get("target_character_id")), StrictJson.integer(identity.get("scheme_instance_id"), 0, 0xffff_fffeL),
                    Math.toIntExact(StrictJson.integer(identity.get("scheme_instance_generation"), 0, 255)));
            if (!item.get("reuse_gap").isNull()) {
                positive(item.get("reuse_gap").get("source_native_revision"));
                integer(item.get("reuse_gap").get("source_date_raw"));
            }
            return new Resolved(held, flag(item.get("applied")), flag(item.get("postcondition_verified")),
                    flag(item.get("terminal_observed")), ReusedSwayOpportunity.decodeResult(StrictJson.canonical(item.get("reuse_gap"))));
        });
        return new Ledger(pending, resolved);
    }
    private static State state(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("actor_character_id", "last_target_character_id", "no_operation_count",
                "last_check_date_raw", "next_check_date_raw", "frontier_membership", "last_observation_attempt_action_id",
                "last_terminal_action_id", "last_job_kind"));
        return new State(character(row.get("actor_character_id")), optional(row.get("last_target_character_id")).map(SwayScheduleWire::character),
                Math.toIntExact(StrictJson.integer(row.get("no_operation_count"), 0, 2)),
                optional(row.get("last_check_date_raw")).map(SwayScheduleWire::integer),
                optional(row.get("next_check_date_raw")).map(SwayScheduleWire::integer),
                optional(row.get("frontier_membership")).map(SwayScheduleWire::characters),
                optional(row.get("last_observation_attempt_action_id")).map(StrictJson::text),
                optional(row.get("last_terminal_action_id")).map(StrictJson::text),
                optional(row.get("last_job_kind")).map(node -> Job.valueOf(StrictJson.text(node).toUpperCase(Locale.ROOT))));
    }
    private static ObjectNode stateJson(State state) {
        ObjectNode row = StrictJson.object(); row.put("actor_character_id", state.actorCharacterId());
        if (state.lastTargetCharacterId().isPresent()) { row.put("last_target_character_id", state.lastTargetCharacterId().orElseThrow()); }
        else { row.putNull("last_target_character_id"); }
        row.put("no_operation_count", state.noOperationCount());
        number(row, "last_check_date_raw", state.lastCheckDateRaw()); number(row, "next_check_date_raw", state.nextCheckDateRaw());
        if (state.frontierMembership().isPresent()) {
            ArrayNode members = row.putArray("frontier_membership"); state.frontierMembership().orElseThrow().forEach(members::add);
        } else { row.putNull("frontier_membership"); }
        text(row, "last_observation_attempt_action_id", state.lastObservationAttemptActionId());
        text(row, "last_terminal_action_id", state.lastTerminalActionId());
        text(row, "last_job_kind", state.lastJobKind().map(SwayScheduleWire::name));
        return row;
    }
    private static List<Long> characters(JsonNode value) {
        StrictJson.require(value.isArray(), "actual JSON array required");
        List<Long> result = new ArrayList<>(); value.forEach(item -> result.add(character(item))); return List.copyOf(result);
    }
    private static long character(JsonNode value) { return StrictJson.integer(value, 1, 0xffff_ffffL); }
    private static BigInteger integer(JsonNode value) { return StrictJson.integer(value, MIN, MAX); }
    private static BigInteger positive(JsonNode value) { return StrictJson.integer(value, BigInteger.ONE, MAX); }
    private static boolean flag(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue(); }
    private static Optional<JsonNode> optional(JsonNode value) { StrictJson.require(value != null, "missing required nullable field"); return value.isNull() ? Optional.empty() : Optional.of(value); }
    private static String name(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static void number(ObjectNode row, String key, Optional<BigInteger> value) {
        if (value.isPresent()) {
            BigInteger number = value.orElseThrow();
            StrictJson.require(number.compareTo(MIN) >= 0 && number.compareTo(MAX) <= 0, "numeric wire date must be a safe integer");
            row.put(key, number);
        } else { row.putNull(key); }
    }
    private static void text(ObjectNode row, String key, Optional<String> value) { if (value.isPresent()) { row.put(key, value.orElseThrow()); } else { row.putNull(key); } }
}
