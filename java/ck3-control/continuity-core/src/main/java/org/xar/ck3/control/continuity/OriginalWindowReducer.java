package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.continuity.writer.WriterContracts.Request;

/** Original root_continuity_window.transition, independent from files, locks and attempts. */
public final class OriginalWindowReducer {
    public static final long TARGET_DAYS = 10_958;
    /** Host binds this policy to its exact reducer source; a head document cannot choose its own policy. */
    public record Policy(long targetDays) {
        public Policy { StrictJson.safe(targetDays, 1); }
    }
    private OriginalWindowReducer() { }
    public static ContinuityState reduce(ContinuityState before, Request request) {
        return ContinuityState.fromJson(reduce(before.toJson(), request.kind(), request.detailsObject()), before.machineId());
    }
    public static ContinuityState reduce(ContinuityState before, Request request, Policy policy) {
        return ContinuityState.fromJson(reduce(before.toJson(), request.kind(), request.detailsObject(), policy), before.machineId());
    }
    /** Null predecessor is the original initial repair path. Prepared state remains raw JSON until attached. */
    public static ObjectNode reduce(ObjectNode previous, String kind, ObjectNode details) {
        return reduce(previous, kind, details, new Policy(TARGET_DAYS));
    }
    public static ObjectNode reduce(ObjectNode previous, String kind, ObjectNode details, Policy policy) {
        java.util.Objects.requireNonNull(policy);
        StrictJson.text(kind); StrictJson.text(details.get("evidence_id"));
        JsonNode source = details.get("source");
        StrictJson.require(truthy(source), "exact source and evidence ID required");
        ObjectNode state = previous == null ? initial(kind, details, policy) : previous.deepCopy();
        StrictJson.require(!StrictJson.text(state.get("schema")).equals(FreshContinuityGenesis.STATE_SCHEMA),"ordinary continuity requires actual initial Game entry");
        boolean episodeVersion=StrictJson.text(state.get("schema")).equals(EpisodeWindow.STATE_SCHEMA);
        StrictJson.require((StrictJson.text(state.get("schema")).equals("root.ck3.continuity-window/v1")||episodeVersion)
                && number(state, "target_days", 1) == policy.targetDays(), "different continuity policy/schema");
        if(episodeVersion)StrictJson.require(EpisodeWindow.State.fromJson(state.get(EpisodeWindow.FIELD)).phase()==EpisodeWindow.Phase.ACTIVE,
                "ordinary continuity cannot advance an awaiting first SAVE window");
        String machine = StrictJson.text(state.get("machine_id"));
        StrictJson.require(!details.has("machine_id") || StrictJson.text(details.get("machine_id")).equals(machine), "continuity machine changed");
        if (details.has("game")) StrictJson.require(ContinuityJson.same(episodeVersion||state.has(FreshContinuityGenesis.FIELD)
                ? org.xar.ck3.control.contracts.GameGeneration.fromJson(details.get("game")).toJson()
                : game(object(details.get("game"))), state.get("game_binding")), "Game generation changed; explicit handoff required");
        switch (kind) {
            case "repair_required", "ordinary_batch_interrupted" -> {
                ObjectNode frame = frame(object(details.get("frame"))); long cycles = number(details, "completed_cycles", 0);
                long window = number(state, "window_id", 0);
                state.put("status", window == 0 ? "prepared" : "repair_required"); state.put("interrupted_window_id", window);
                ObjectNode interruption = StrictJson.object(); interruption.set("reason", required(details, "reason"));
                interruption.set("source", source.deepCopy()); interruption.set("evidence_id", details.get("evidence_id").deepCopy());
                interruption.set("last_settled_frame", frame); interruption.put("completed_cycles", cycles); state.set("interruption", interruption);
                if(kind.equals("repair_required")) {
                    state.put("last_settled_date_raw", number(frame, "date_raw", 0)); state.put("last_settled_cycles", cycles);
                }else StrictJson.require(cycles==number(state,"last_settled_cycles",0)
                        &&number(frame,"date_raw",0)>=number(state,"last_settled_date_raw",0),
                        "ordinary interruption cannot grant or rewind saved progress");
            }
            case "captured_no_dispatch_recovery" -> {
                ObjectNode retainedFrame=frame(object(state.get("latest_binding"))),actual=frame(object(details.get("frame")));
                StrictJson.require("repair_required".equals(StrictJson.text(state.get("status")))
                        &&number(details,"completed_cycles",0)==number(state,"last_settled_cycles",0)
                        &&number(actual,"date_raw",0)>=number(state,"last_settled_date_raw",0)
                        &&number(actual,"actor_character_id",1)==number(retainedFrame,"actor_character_id",1)
                        &&StrictJson.text(actual.get("episode_run_id")).equals(StrictJson.text(retainedFrame.get("episode_run_id")))
                        &&StrictJson.integer(actual.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retainedFrame.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX))>=0,
                        "captured zero-dispatch recovery changed its retained game frontier or saved credit");
                state.put("status","running");binding(state,actual);
            }
            case "initial_no_dispatch_recovery" -> {
                ObjectNode retainedFrame=frame(object(state.get("latest_binding"))),actual=frame(object(details.get("frame")));
                StrictJson.require("repair_required".equals(StrictJson.text(state.get("status")))
                        &&number(state,"last_settled_cycles",0)==0&&number(details,"completed_cycles",0)==0
                        &&number(actual,"date_raw",0)==number(state,"last_settled_date_raw",0)
                        &&number(actual,"date_raw",0)==number(state,"start_date_raw",0)
                        &&number(actual,"actor_character_id",1)==number(retainedFrame,"actor_character_id",1)
                        &&StrictJson.text(actual.get("episode_run_id")).equals(StrictJson.text(retainedFrame.get("episode_run_id")))
                        &&StrictJson.integer(actual.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retainedFrame.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX))>=0,
                        "initial read-only recovery cannot change its original game frontier");
                state.put("status","running");binding(state,actual);
            }
            case "attach_verified" -> {
                ObjectNode frame = frame(object(details.get("frame"))); long cycles = number(details, "completed_cycles", 0);
                StrictJson.text(frame.get("episode_run_id")); String status = StrictJson.text(state.get("status"));
                if (status.equals("prepared") || status.equals("repair_required")) {
                    state.put("window_id", Math.addExact(number(state, "window_id", 0), 1)); state.put("status", "running");
                    state.put("start_date_raw", number(frame, "date_raw", 0));
                    state.put("target_date_raw", Math.addExact(number(frame, "date_raw", 0), Math.multiplyExact(policy.targetDays(), 24)));
                    state.put("manual_repair_count", Math.addExact(number(state, "manual_repair_count", 0), 1));
                    state.set("window_start_source", source.deepCopy()); state.set("previous_interruption", nullable(state, "interruption"));
                } else {
                    StrictJson.require(Set.of("running", "complete").contains(status), "unsupported continuity status");
                    StrictJson.require(number(frame, "date_raw", 0) >= number(state, "last_settled_date_raw", 0)
                            && cycles >= number(state, "last_settled_cycles", 0), "verified handoff moved backwards without repair");
                }
                state.put("last_settled_date_raw", number(frame, "date_raw", 0)); state.put("last_settled_cycles", cycles);
                binding(state, frame);
            }
            case "settled_batch", "automatic_recovery" -> {
                StrictJson.require(Set.of("running", "complete").contains(StrictJson.text(state.get("status"))), "manual repair unresolved");
                long date = number(details, "date_raw", 0), cycles = number(details, "completed_cycles", 0);
                long oldDate = number(state, "last_settled_date_raw", 0), oldCycles = number(state, "last_settled_cycles", 0);
                if (date < oldDate || cycles < oldCycles) {
                    StrictJson.require(date <= oldDate && cycles <= oldCycles, "inconsistent settled date/cycle chain");
                    return state;
                }
                state.put("last_settled_date_raw", date); state.put("last_settled_cycles", cycles); state.set("last_settled_source", source.deepCopy());
                if (kind.equals("automatic_recovery")) state.put("automatic_recovery_count", Math.addExact(number(state, "automatic_recovery_count", 0), 1));
                if (details.get("frame") instanceof ObjectNode supplied) {
                    ObjectNode frame = frame(supplied); StrictJson.require(number(frame, "date_raw", 0) == date, "settled frame/date mismatch"); binding(state, frame);
                }
                if (date >= number(state, "target_date_raw", 0)) state.put("status", "complete");
            }
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("unsupported continuity transition");
        }
        return state;
    }
    private static ObjectNode initial(String kind, ObjectNode details, Policy policy) {
        StrictJson.require(kind.equals("repair_required"), "initialize from real blocking failure");
        ObjectNode state = StrictJson.object(); state.put("schema", "root.ck3.continuity-window/v1");
        state.put("machine_id", StrictJson.text(details.get("machine_id"))); state.put("window_id", 0); state.put("status", "prepared");
        state.putNull("start_date_raw"); state.putNull("target_date_raw"); state.put("target_days", policy.targetDays());
        state.put("target_years", 30); state.put("calendar_year_days", 365.25); state.put("manual_repair_count", 0);
        state.put("automatic_recovery_count", 0); state.put("binding_lineage_count", 0); state.putNull("latest_binding");
        state.set("game_binding", game(object(details.get("game")))); state.put("sequence", 0); return state;
    }
    private static ObjectNode game(ObjectNode value) {
        ObjectNode row = StrictJson.object(); row.put("pid", number(value, "pid", 1)); row.put("creation_date", StrictJson.text(value.get("creation_date"))); return row;
    }
    private static ObjectNode frame(ObjectNode value) {
        ObjectNode row = StrictJson.object(); row.put("date_raw", number(value, "date_raw", 0));
        row.put("actor_character_id", (long)NativeCharacterId.fromJson(value.get("actor_character_id")).value());
        JsonNode episode = value.get("episode_run_id");
        StrictJson.require(episode == null || episode.isNull() || episode.isTextual(), "episode string/null boundary");
        row.put("episode_run_id", episode == null || episode.isNull() ? "" : episode.textValue());
        for (String key : Set.of("snapshot_id", "revision", "native_revision")) row.set(key, nullable(value, key));
        return row;
    }
    private static void binding(ObjectNode state, ObjectNode frame) {
        JsonNode old = state.get("latest_binding");
        if (truthy(old) && (!NativeCharacterId.fromJson(old.get("actor_character_id")).equals(NativeCharacterId.fromJson(frame.get("actor_character_id")))
                || !java.util.Objects.equals(old.get("episode_run_id"), frame.get("episode_run_id"))))
            state.put("binding_lineage_count", Math.addExact(number(state, "binding_lineage_count", 0), 1));
        state.set("latest_binding", frame);
    }
    private static boolean truthy(JsonNode value) {
        return value != null && !value.isNull() && (!value.isContainerNode() || !value.isEmpty())
                && (!value.isTextual() || !value.textValue().isEmpty()) && (!value.isBoolean() || value.booleanValue())
                && (!value.isNumber() || value.doubleValue() != 0);
    }
    private static JsonNode required(ObjectNode row, String key) { StrictJson.require(row.has(key), "required " + key); return row.get(key).deepCopy(); }
    private static JsonNode nullable(ObjectNode row, String key) { return row.has(key) ? row.get(key).deepCopy() : NullNode.instance; }
    private static ObjectNode object(JsonNode value) { return ContinuityJson.object(value); }
    private static long number(ObjectNode row, String field, long minimum) { return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER); }
}
