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
            case "reconciled_original_cycle" -> {
                StrictJson.object(details,Set.of("evidence_id","source","machine_id","session","batch_id",
                        "completed_cycles","cycle_record_ref","frame"));
                ObjectNode actual=frame(object(details.get("frame"))),retained=frame(object(state.get("latest_binding")));
                ObjectNode interruption=object(state.get("interruption"));
                ObjectNode boundary=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
                ObjectNode cycle=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_CYCLE_FIELD));
                StrictJson.require("repair_required".equals(StrictJson.text(state.get("status")))
                        &&"java-reconciled-original-cycle/v1".equals(StrictJson.text(source))
                        &&"java-ordinary-batch-interruption/v2".equals(StrictJson.text(interruption.get("source")))
                        &&"BATCH_INTERRUPTED".equals(StrictJson.text(boundary.get("boundary")))
                        &&ContinuityJson.same(boundary.get("session"),details.get("session"))
                        &&ContinuityJson.same(cycle.get("session"),details.get("session"))
                        &&StrictJson.text(boundary.get("batch_id")).equals(StrictJson.text(details.get("batch_id")))
                        &&StrictJson.text(boundary.get("evidence_id")).equals(StrictJson.text(interruption.get("evidence_id")))
                        &&number(state,"interrupted_window_id",1)==number(state,"window_id",1)
                        &&number(details,"completed_cycles",0)==number(state,"last_settled_cycles",0)
                        &&number(interruption,"completed_cycles",0)==number(state,"last_settled_cycles",0)
                        &&cycle.has("pending_receipt")&&cycle.get("pending_receipt").isNull()
                        &&cycle.hasNonNull("head")&&ContinuityJson.same(cycle.get("head"),details.get("cycle_record_ref"))
                        &&number(cycle,"completed_cycles",0)>=number(state,"last_settled_cycles",0)
                        &&number(actual,"date_raw",0)>=number(retained,"date_raw",0)
                        &&number(actual,"date_raw",0)>=number(state,"last_settled_date_raw",0)
                        &&number(actual,"actor_character_id",1)==number(retained,"actor_character_id",1)
                        &&StrictJson.text(actual.get("episode_run_id")).equals(StrictJson.text(retained.get("episode_run_id")))
                        &&StrictJson.integer(actual.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retained.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX))>=0,
                        "reconciled original requires its actual interrupted batch and completed same-subject cycle without saved credit");
                state.put("status","running");binding(state,actual);
            }
            case "reconciled_original_save" -> {
                StrictJson.object(details,Set.of("evidence_id","source","machine_id","date_raw","completed_cycles","frame","session","batch_id","cycle_record_ref"));
                ObjectNode actual=frame(object(details.get("frame"))),retained=frame(object(state.get("latest_binding")));
                ObjectNode interruption=object(state.get("interruption"));
                ObjectNode boundary=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
                ObjectNode cycle=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_CYCLE_FIELD));
                StrictJson.require("repair_required".equals(StrictJson.text(state.get("status")))
                        &&"java-reconciled-original-save/v1".equals(StrictJson.text(source))
                        &&"java-ordinary-batch-interruption/v2".equals(StrictJson.text(interruption.get("source")))
                        &&"BATCH_INTERRUPTED".equals(StrictJson.text(boundary.get("boundary")))
                        &&ContinuityJson.same(boundary.get("session"),details.get("session"))
                        &&ContinuityJson.same(cycle.get("session"),details.get("session"))
                        &&StrictJson.text(boundary.get("batch_id")).equals(StrictJson.text(details.get("batch_id")))
                        &&StrictJson.text(boundary.get("evidence_id")).equals(StrictJson.text(interruption.get("evidence_id")))
                        &&number(state,"interrupted_window_id",1)==number(state,"window_id",1)
                        &&number(interruption,"completed_cycles",0)==number(state,"last_settled_cycles",0)
                        &&cycle.has("pending_receipt")&&cycle.get("pending_receipt").isNull()
                        &&cycle.hasNonNull("head")&&ContinuityJson.same(cycle.get("head"),details.get("cycle_record_ref"))
                        &&number(cycle,"completed_cycles",0)==number(details,"completed_cycles",0)
                        &&number(details,"completed_cycles",0)>=number(state,"last_settled_cycles",0)
                        &&number(actual,"date_raw",0)==number(details,"date_raw",0)
                        &&number(actual,"date_raw",0)>=number(state,"last_settled_date_raw",0)
                        &&number(actual,"date_raw",0)>=number(retained,"date_raw",0)
                        &&number(actual,"actor_character_id",1)==number(retained,"actor_character_id",1)
                        &&StrictJson.text(actual.get("episode_run_id")).equals(StrictJson.text(retained.get("episode_run_id")))
                        &&StrictJson.integer(actual.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retained.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX))>=0,
                        "reconciled original save requires its actual interrupted batch and completed same-subject cycle without saved credit");
                long date = number(details, "date_raw", 0), cycles = number(details, "completed_cycles", 0);
                long oldDate = number(state, "last_settled_date_raw", 0), oldCycles = number(state, "last_settled_cycles", 0);
                if (date < oldDate || cycles < oldCycles) {
                    StrictJson.require(date <= oldDate && cycles <= oldCycles, "inconsistent settled date/cycle chain");
                    return state;
                }
                state.put("last_settled_date_raw", date); state.put("last_settled_cycles", cycles); state.set("last_settled_source", source.deepCopy());
                binding(state, actual);
                if (date >= number(state, "target_date_raw", 0)) state.put("status", "complete");
                else state.put("status", "running");
            }
            case "saved_read_only_recovery" -> {
                StrictJson.object(details,Set.of("evidence_id","source","machine_id","session","batch_id","completed_cycles","frame","driver_ref","predecessor_head_digest"));
                StrictJson.require("java-saved-read-only-recovery/v1".equals(StrictJson.text(source))
                        &&previous!=null&&ContinuityJson.digest(previous).equals(StrictJson.text(details.get("predecessor_head_digest"))),
                        "Saved read-only recovery changed its exact predecessor/source");
                ObjectNode marker=SavedContinuityBootstrap.request(object(state.get(SavedContinuityBootstrap.FIELD))).detailsObject();
                ObjectNode owner=object(details.get("session"));
                StrictJson.object(owner,Set.of("machine_id","game","session_id"));StrictJson.text(owner.get("session_id"));
                ObjectNode boundary=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
                ObjectNode interruption=object(state.get("interruption"));
                StrictJson.require("repair_required".equals(StrictJson.text(state.get("status")))
                        &&StrictJson.text(owner.get("machine_id")).equals(machine)
                        &&ContinuityJson.same(owner.get("game"),state.get("game_binding"))
                        &&ContinuityJson.same(owner,marker.get("session"))&&ContinuityJson.same(owner,boundary.get("session"))
                        &&"BATCH_INTERRUPTED".equals(StrictJson.text(boundary.get("boundary")))
                        &&"java-ordinary-batch-interruption/v2".equals(StrictJson.text(interruption.get("source")))
                        &&StrictJson.text(boundary.get("evidence_id")).equals(StrictJson.text(interruption.get("evidence_id")))
                        &&StrictJson.text(boundary.get("batch_id")).equals(StrictJson.text(details.get("batch_id")))
                        &&StrictJson.text(boundary.get("evidence_id")).equals(StrictJson.text(details.get("batch_id"))+":BATCH_INTERRUPTED")
                        &&number(state,"interrupted_window_id",1)==number(state,"window_id",1)
                        &&number(details,"completed_cycles",0)==number(state,"last_settled_cycles",0)
                        &&number(interruption,"completed_cycles",0)==number(state,"last_settled_cycles",0),
                        "Saved read-only recovery crossed its actual interrupted owner/batch/window/frontier");
                for(String field:Set.of("pending_cycle","pending_actions","unknown_actions","UNKNOWN","pending_receipt",
                        org.xar.ck3.control.continuity.writer.WriterContracts.ACTION_LIFECYCLE_FIELD)) {
                    JsonNode value=state.get(field);
                    StrictJson.require(value==null||value.isNull()||value.isContainerNode()&&value.isEmpty(),"Saved recovery cannot discard pending/action/UNKNOWN: "+field);
                }
                JsonNode cycle=state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_CYCLE_FIELD);
                StrictJson.require(cycle==null||cycle.isNull()||cycle.isObject()&&cycle.has("pending_receipt")&&cycle.get("pending_receipt").isNull(),
                        "Saved recovery has an ordinary pending receipt");
                var driver=org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("driver_ref"));
                JsonNode reads=state.get(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_READ_HISTORY_FIELD);
                var expectedDriver=org.xar.ck3.control.contracts.ExactRef.fromJson(reads==null||reads.isNull()?marker.get("full_driver"):reads.get("after_driver"));
                StrictJson.require(driver.equals(expectedDriver),"Saved recovery did not retain the actual final Driver");
                ObjectNode retained=frame(object(state.get("latest_binding"))),actual=frame(object(details.get("frame")));
                StrictJson.require(number(actual,"date_raw",0)==number(state,"last_settled_date_raw",0)
                        &&number(actual,"date_raw",0)==number(retained,"date_raw",0)
                        &&number(actual,"actor_character_id",1)==number(retained,"actor_character_id",1)
                        &&StrictJson.text(actual.get("episode_run_id")).equals(StrictJson.text(retained.get("episode_run_id")))
                        &&StrictJson.integer(actual.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retained.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX))>=0
                        &&StrictJson.integer(actual.get("revision"),java.math.BigInteger.ONE,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retained.get("revision"),java.math.BigInteger.ONE,StrictJson.UINT64_MAX))>=0,
                        "Saved read-only recovery cannot change its saved subject/date or regress actual revisions");
                state.put("status","running");binding(state,actual);
            }

            case "operator_life_interruption_recovery" -> {
                StrictJson.object(details,Set.of("evidence_id","source","machine_id","completed_cycles","frame","session","batch_id","next_sequence","operator_observation"));
                ObjectNode retained=frame(object(state.get("latest_binding"))),actual=frame(object(details.get("frame")));
                ObjectNode cycle=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_CYCLE_FIELD));
                ObjectNode boundary=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
                StrictJson.require("java-operator-life-interruption-recovery/v1".equals(StrictJson.text(source))
                        &&"repair_required".equals(StrictJson.text(state.get("status")))
                        &&number(cycle,"completed_cycles",1)==number(details,"completed_cycles",1)
                        &&cycle.hasNonNull("head")&&cycle.has("pending_receipt")&&cycle.get("pending_receipt").isNull()
                        &&state.hasNonNull(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)
                        &&ContinuityJson.same(cycle.get("session"),details.get("session"))
                        &&"BATCH_INTERRUPTED".equals(StrictJson.text(boundary.get("boundary")))
                        &&ContinuityJson.same(boundary.get("session"),details.get("session"))
                        &&StrictJson.text(boundary.get("batch_id")).equals(StrictJson.text(details.get("batch_id")))
                        &&number(details,"next_sequence",2)>=2
                        &&StrictJson.text(details.get("batch_id")).endsWith("-"+(number(details,"next_sequence",2)-1))
                        &&number(actual,"date_raw",0)>=number(retained,"date_raw",0)
                        &&NativeCharacterId.fromJson(actual.get("actor_character_id")).equals(NativeCharacterId.fromJson(retained.get("actor_character_id")))
                        &&StrictJson.text(actual.get("episode_run_id")).equals(StrictJson.text(retained.get("episode_run_id")))
                        &&StrictJson.integer(actual.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retained.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX))>=0,
                        "Life interruption must preserve its exact nonzero completed/saved frontier without awarding observed days");
                for(String field:java.util.List.of("pending_cycle","pending_checkpoint","current_cycle_pending")) {
                    JsonNode value=state.get(field);StrictJson.require(value==null||value.isNull(),"Life interruption cannot clear pending state: "+field);
                }
                org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("operator_observation"));
                state.put("status","running");binding(state,actual);if(state.has("last_error"))state.putNull("last_error");
                // Preserve current cycle 13, saved cycle 1, all original dates/credit/domain/Driver and the old interruption facts.
            }
            case "operator_quarantine_recovery" -> {
                StrictJson.object(details,Set.of("evidence_id","source","machine_id","completed_cycles","frame","session","batch_id","next_sequence","operator_observation"));
                ObjectNode retained=frame(object(state.get("latest_binding"))),actual=frame(object(details.get("frame")));
                ObjectNode boundary=object(state.get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
                StrictJson.require("java-operator-quarantine-recovery/v1".equals(StrictJson.text(source))
                        &&"repair_required".equals(StrictJson.text(state.get("status")))
                        &&number(state,"last_settled_cycles",0)==0&&number(details,"completed_cycles",0)==0
                        &&"BATCH_INTERRUPTED".equals(StrictJson.text(boundary.get("boundary")))
                        &&ContinuityJson.same(boundary.get("session"),details.get("session"))
                        &&StrictJson.text(boundary.get("batch_id")).equals(StrictJson.text(details.get("batch_id")))
                        &&number(details,"next_sequence",1)==1
                        &&number(actual,"date_raw",0)==number(state,"last_settled_date_raw",0)
                        &&number(actual,"date_raw",0)==number(state,"start_date_raw",0)
                        &&NativeCharacterId.fromJson(actual.get("actor_character_id")).equals(NativeCharacterId.fromJson(retained.get("actor_character_id")))
                        &&StrictJson.text(actual.get("episode_run_id")).equals(StrictJson.text(retained.get("episode_run_id")))
                        &&StrictJson.integer(actual.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX)
                            .compareTo(StrictJson.integer(retained.get("native_revision"),java.math.BigInteger.ZERO,StrictJson.UINT64_MAX))>=0,
                        "operator quarantine recovery changed its original interrupted owner/frontier or credit");
                for(String field:java.util.List.of(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_CYCLE_FIELD,
                        org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,"pending_cycle","pending_checkpoint","current_cycle_pending")) {
                    JsonNode value=state.get(field);StrictJson.require(value==null||value.isNull(),"operator recovery cannot clear existing pending/cycle/SAVE state: "+field);
                }
                org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("operator_observation"));
                state.put("status","running");binding(state,actual);
                if(state.has("last_error"))state.putNull("last_error");
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
