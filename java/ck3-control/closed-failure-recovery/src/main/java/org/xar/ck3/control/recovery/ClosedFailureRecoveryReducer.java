package org.xar.ck3.control.recovery;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.OriginalWindowReducer;

/** Pure original repair_required projection; no writer, process, file or native operation. */
public final class ClosedFailureRecoveryReducer {
    public static final long LEGACY_TARGET_DAYS = 10_950;
    private ClosedFailureRecoveryReducer() { }

    private static int actor(JsonNode value){try{return NativeCharacterId.fromJson(value).value();}catch(IllegalArgumentException malformed){throw new ContractViolationException(malformed.getMessage());}}

    public static RecoveryPreview preview(ClosedFailureRecoveryInput input) {
        return preview(input, RecoveryPrerequisiteVerifier.unavailable());
    }

    public static RecoveryPreview preview(ClosedFailureRecoveryInput input, RecoveryPrerequisiteVerifier verifier) {
        Objects.requireNonNull(input); Objects.requireNonNull(verifier);
        try {
            return project(input, verifier);
        } catch (ContractViolationException error) {
            return new RecoveryPreview.Rejected(error.getMessage());
        }
    }

    public static String inputDigest(ClosedFailureRecoveryInput input) {
        ObjectNode sources = StrictJson.object();
        sources.put("machine_id", input.machineId()); sources.put("observed_at_utc", input.observedAtUtc());
        ArrayNode refs = sources.putArray("metadata_sources");
        for (ExactRef ref : input.metadataSources()) { refs.add(ref.toJson()); }
        sources.set("current_driver", input.currentDriver().toJson());
        sources.set("current_driver_identity", input.currentDriverIdentity().toJson());
        sources.set("current_save", input.currentSave().toJson());
        sources.set("current_save_identity", input.currentSaveIdentity().toJson());
        return hash(sources);
    }

    private static RecoveryPreview project(ClosedFailureRecoveryInput in, RecoveryPrerequisiteVerifier verifier) {
        ObjectNode before = in.predecessor().object(), basis = in.savedBasis().object();
        boolean version2=text(before,"schema").equals(EpisodeWindow.STATE_SCHEMA);
        StrictJson.require(version2||text(before,"schema").equals("root.ck3.continuity-window/v1"),"exact legacy or versioned episode continuity schema required");
        if(version2){
            ContinuityState actual=ContinuityState.fromJson(before,in.machineId());
            EpisodeWindow.requireActive(actual);
        }else StrictJson.require(!before.has(EpisodeWindow.FIELD),"legacy schema cannot hide a versioned window");
        requireText(before, "machine_id", in.machineId()); requireText(basis, "machine_id", in.machineId());
        requireText(before, "status", "repair_required");
        StrictJson.require(number(before, "target_days", 1) == (version2?OriginalWindowReducer.TARGET_DAYS:LEGACY_TARGET_DAYS), "exact version-bound writer target policy");
        ObjectNode game;
        if(version2)game=org.xar.ck3.control.contracts.GameGeneration.fromJson(before.get("game_binding")).toJson();
        else{
            game=StrictJson.object(before.get("game_binding"), Set.of("pid", "creation_date"));
            StrictJson.integer(game.get("pid"), 1, 0xffff_ffffL);StrictJson.text(game.get("creation_date"));
        }
        long window = number(before, "window_id", 1), sequence = number(before, "sequence", 1);
        long historicalCycles = number(before, "last_settled_cycles", 0);
        long historicalDate = number(before, "last_settled_date_raw", 0);
        ObjectNode origin = object(basis.get("origin"));
        for (String key : Set.of("start_date_raw", "target_date_raw", "target_days")) {
            StrictJson.require(number(before, key, 0) == number(origin, key, 0), "original window/origin changed");
        }
        SavedFrame savedFrame;try{savedFrame=SavedFrame.fromJson(basis.get("frame"));}catch(IllegalArgumentException malformed){throw new ContractViolationException(malformed.getMessage());}
        long savedCycles = number(basis, "completed_cycles", 0);
        StrictJson.require(historicalCycles > savedCycles && historicalDate == savedFrame.dateRaw(),
                "closed zero-day partial prefix must lie above the saved cycle frontier");
        ObjectNode refs = object(basis.get("refs"));
        StrictJson.require(ExactRef.fromJson(refs.get("save")).equals(in.currentSave()), "exact prior SAVE reference");
        StrictJson.require(object(basis.get("save_identity")).equals(in.currentSaveIdentity().toJson()), "same current SAVE identity");
        ObjectNode oldQualification = in.priorQualification().object();
        requireText(oldQualification, "machine_id", in.machineId());
        StrictJson.require(ExactRef.fromJson(oldQualification.get("basis_ref")).equals(in.savedBasis().reference()),
                "prior qualification binds the actual saved basis");

        ObjectNode state = in.rawState().object(), governance = in.rawGovernance().object();
        ObjectNode checkpoint = object(basis.get("checkpoint"));
        ObjectNode rawCheckpoint = object(state.get("actual_saved_checkpoint"));
        StrictJson.require(number(checkpoint, "saved_date_raw", 0) == savedFrame.dateRaw()
                && number(rawCheckpoint, "date_raw", 0) == savedFrame.dateRaw()
                && actor(rawCheckpoint.get("episode_character_id")) == savedFrame.actorCharacterId()
                && text(rawCheckpoint, "episode_run_id").equals(savedFrame.episodeRunId()), "same saved frame in normalized SDK anchor and raw Native checkpoint");
        for (String key : Set.of("name", "path", "sha256")) {
            StrictJson.require(text(checkpoint, key).equals(text(rawCheckpoint, key)), "same actual saved checkpoint identity");
        }
        for (String key : Set.of("size", "history_index")) {
            StrictJson.require(number(checkpoint, key, 1) == number(rawCheckpoint, key, 1), "same exact Native/SDK checkpoint integer");
        }
        JsonNode rawLifecycle = rawCheckpoint.get("succession_lifecycle");
        StrictJson.require(java.util.Objects.equals(checkpoint.get("succession_lifecycle"),
            rawLifecycle == null ? com.fasterxml.jackson.databind.node.NullNode.instance : rawLifecycle), "same original SDK normalized checkpoint lifecycle");
        StrictJson.require(number(state, "completed_cycles", 0) == historicalCycles
                && number(governance, "completed_cycles", 0) == historicalCycles, "exact raw completed prefix");
        ObjectNode frame = object(state.get("before"));
        StrictJson.require(number(frame, "date_raw", 0) == historicalDate
                && actor(frame.get("actor_character_id")) == savedFrame.actorCharacterId()
                && text(frame, "episode_run_id").equals(savedFrame.episodeRunId()), "saved same-episode zero-day prefix");
        ObjectNode pending = object(state.get("pending_cycle"));
        StrictJson.require(pending.equals(governance.get("pending_cycle")), "raw pending retained in governance");
        StrictJson.require(number(pending, "global_turn", 1) == historicalCycles + 1
                && text(pending, "stage").equals("auto_unsettled")
                && object(pending.get("before")).equals(frame), "actual unsettled cycle identity");
        requireNull(state, "pending_checkpoint");
        long unknown = number(pending, "auto_sequence", 1);
        ObjectNode fullRequest = in.fullRequest().object(), failedFull = in.failedFull().object();
        ObjectNode autoRequest = in.autoRequest().object(), failedAuto = in.failedAuto().object();
        requireText(fullRequest, "command", "full_loop");
        long control = number(fullRequest, "sequence", 1);
        StrictJson.require(control < unknown && fullRequest.equals(failedFull.get("request"))
                && !failedFull.has("result") && text(failedFull, "client_error").length() > 0,
                "failed original FULL remains failed");
        requireFalse(failedFull, "replay_allowed");
        requireText(autoRequest, "tool", "ck3_auto_turn");
        StrictJson.require(number(autoRequest, "sequence", 1) == unknown
                && object(autoRequest.get("arguments")).isEmpty()
                && autoRequest.equals(failedAuto.get("request"))
                && text(failedFull, "original_response").equals(in.failedAuto().reference().path()), "exact parent/child binding");
        ObjectNode error = object(failedAuto.get("result"));
        requireTrue(error, "is_error"); requireText(error, "result_type", "complete");
        StrictJson.text(object(error.get("structured_content")).get("error_type"));
        StrictJson.require(number(in.actualNext().object(), "next_sequence", 1) == unknown + 1,
                "consumed failed AUTO remains unreplayed in NEXT");
        ObjectNode rows = object(failedFull.get("full_rpc_rows_v1"));
        StrictJson.require(number(rows, "control_sequence", 1) == control, "FULL RPC source control");
        StrictJson.require(number(rows, "row_count", 1) == 2 * (historicalCycles - savedCycles) + 1
                && number(rows, "duplicate_rows_ignored", 0) == 0
                && number(rows, "invalid_elapsed_rows", 0) == 0, "all original RPC rows counted without conflict");
        ObjectNode tools = object(rows.get("tools"));
        StrictJson.require(number(object(tools.get("AUTO")), "count", 1) == historicalCycles - savedCycles + 1
                && number(object(tools.get("MET")), "count", 0) == historicalCycles - savedCycles
                && number(object(tools.get("AUTO")), "error_count", 0) == 1
                && number(object(tools.get("SEM")), "count", 0) == 0
                && number(object(tools.get("SAVE")), "count", 0) == 0, "bounded failed partial FULL counts, no new SAVE");
        for (String kind : Set.of("AUTO", "MET", "SEM", "SAVE")) {
            ObjectNode summary = object(tools.get(kind));
            StrictJson.require(number(summary, "client_error_count", 0) == 0
                    && number(summary, "error_count", 0) == (kind.equals("AUTO") ? 1 : 0), "original tool error counts");
            if (kind.equals("SEM") || kind.equals("SAVE")) {
                JsonNode elapsed = summary.get("elapsed_seconds_sum");
                StrictJson.require(elapsed != null && elapsed.isNumber() && elapsed.decimalValue().signum() == 0,
                        "zero actual SEM/SAVE elapsed summary");
            }
        }

        String digest = inputDigest(in);
        RecoveryPrerequisiteVerifier.Check prerequisites = Objects.requireNonNull(verifier.verify(in, digest));
        if (prerequisites instanceof RecoveryPrerequisiteVerifier.Unavailable missing) {
            return new RecoveryPreview.Unavailable(missing.reason());
        }
        if (prerequisites instanceof RecoveryPrerequisiteVerifier.Rejected rejected) {
            return new RecoveryPreview.Rejected(rejected.reason());
        }
        if (!(prerequisites instanceof RecoveryPrerequisiteVerifier.Verified proof)) {
            throw new IllegalStateException("closed prerequisite branch");
        }
        StrictJson.require(proof.inputDigest().equals(digest) && proof.driver().equals(in.currentDriver())
                && proof.driverIdentity().equals(in.currentDriverIdentity()) && proof.save().equals(in.currentSave())
                && proof.saveIdentity().equals(in.currentSaveIdentity())
                && proof.validatorSource().equals(ExactRef.fromJson(refs.get("checkpoint_validator")))
                && proof.checkpointDigest().equals(hash(basis.get("checkpoint")))
                && proof.settledPrefixCycles() == historicalCycles - savedCycles
                && proof.unknownSequence() == unknown, "new actual original-SDK/closed-prefix source authority binding");

        String evidenceId = "closed-failed-partial-saved-reanchor:" + digest;
        String reason = "Closed failed partial FULL; original pending AUTO remains unknown; verified SAVE frontier reanchored with zero credit";
        ObjectNode details = StrictJson.object();
        details.put("machine_id", in.machineId()); details.put("evidence_id", evidenceId);
        details.put("source", proof.closedEpochProof().path()); details.put("reason", reason);
        details.set("frame", savedFrame.toJson()); details.put("completed_cycles", savedCycles);
        details.set("game", game.deepCopy());
        ObjectNode recovery = StrictJson.object();
        recovery.put("schema", "xar.closed-failed-partial-recovery-candidate/v1");
        recovery.put("input_digest", digest); recovery.put("original_full_sequence", control);
        recovery.put("unknown_auto_sequence", unknown); recovery.put("historical_cycles", historicalCycles);
        recovery.put("ordinary_cycle_credit", 0); recovery.put("game_day_credit", 0);
        recovery.put("original_actions_replayed", false); recovery.put("raw_pending_modified", false);
        recovery.put("ready", false); recovery.put("requires_new_cold_binding", true);
        recovery.set("raw_state", in.rawState().reference().toJson());
        recovery.set("raw_governance", in.rawGovernance().reference().toJson());
        recovery.set("failed_full", in.failedFull().reference().toJson());
        recovery.set("failed_auto", in.failedAuto().reference().toJson());
        recovery.set("closed_epoch_proof", proof.closedEpochProof().toJson());
        recovery.set("settled_prefix_proof", proof.settledPrefixProof().toJson());
        recovery.set("canonical_checkpoint_proof", proof.canonicalCheckpointProof().toJson());
        details.set("closed_failure_recovery", recovery);

        // Exactly the existing transition(previous, "repair_required", details).
        ObjectNode reduced = before.deepCopy();
        reduced.put("status", "repair_required"); reduced.put("interrupted_window_id", window);
        ObjectNode interruption = StrictJson.object();
        interruption.put("reason", reason); interruption.put("source", proof.closedEpochProof().path());
        interruption.put("evidence_id", evidenceId); interruption.set("last_settled_frame", savedFrame.toJson());
        interruption.put("completed_cycles", savedCycles); reduced.set("interruption", interruption);
        reduced.put("last_settled_date_raw", savedFrame.dateRaw()); reduced.put("last_settled_cycles", savedCycles);
        if(version2)ContinuityState.fromJson(reduced,in.machineId());
        ObjectNode identityValue = StrictJson.object(); identityValue.put("kind", "repair_required"); identityValue.set("details", details);
        String identity = hash(identityValue);
        ObjectNode sourceKey = StrictJson.object(); sourceKey.put("kind", "repair_required"); sourceKey.put("evidence_id", evidenceId);
        ObjectNode committed = reduced.deepCopy(); committed.put("sequence", sequence + 1); committed.put("last_event_identity", identity);
        return new RecoveryPreview.Candidate(digest, hash(before), identity, hash(sourceKey), sequence,
                StrictJson.canonical(details), StrictJson.canonical(reduced), StrictJson.canonical(committed));
    }

    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "required object; missing/null are distinct");
        return (ObjectNode) value;
    }
    private static long number(ObjectNode row, String field, long minimum) {
        return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER);
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static void requireText(ObjectNode row, String field, String expected) {
        StrictJson.require(text(row, field).equals(expected), "exact " + field);
    }
    private static void requireFalse(ObjectNode row, String field) {
        JsonNode value = row.get(field);
        StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(), "actual false " + field);
    }
    private static void requireTrue(ObjectNode row, String field) { StrictJson.trueValue(row.get(field)); }
    private static void requireNull(ObjectNode row, String field) {
        StrictJson.require(row.has(field) && row.get(field).isNull(), "explicit null " + field);
    }
    private static String hash(JsonNode value) { return RecoveryEvidence.sha256(StrictJson.canonical(value)); }
}
