package org.xar.ck3.control.admission.cold;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure migration of the current Native32/67 offline receipt parser and comparison. */
public final class CurrentSavedPreflightCodec {
    public static final int RECEIPT_MAX_BYTES = 1_048_576;
    private static final List<String> REPLAY_REFS = List.of("receipt_ref", "helper_ref", "semantic_ref", "launch_ref",
            "original_cold_ref", "original_queue_ref", "score_ref", "anchor_ref");
    private static final Set<String> REPLAY_FIELDS = Set.of("receipt_ref", "helper_ref", "semantic_ref", "launch_ref",
            "original_cold_ref", "original_queue_ref", "score_ref", "anchor_ref", "historical_sequence",
            "check_after_ast_sha256", "historical_outer_context_reconstructed", "historical_row_modified",
            "actual_rpc_calls", "canonical_score_writes", "fresh_native_readiness_claimed");
    private static final Set<String> FIELDS = Set.of("schema", "machine_id", "observed_at_utc", "phase", "runtime_root",
            "attempt_nonce", "task_nonce", "plan_ref", "quote_ref", "basis_ref", "validation_ref", "core_source_ref",
            "runtime_source_refs", "historical_replay", "current_next_sequence", "files_verified", "canonical_entry_count",
            "closure_count", "startup_dispatch_replay_ref", "consumer_probe_ref", "read_only_game_start_permitted",
            "full_loop_permitted", "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed",
            "live_semantic_accepted", "live_warm_bound");

    private CurrentSavedPreflightCodec() { }

    public static CurrentSavedPreflightContract decode(byte[] raw, PathFlavor flavor) {
        return parse(StrictJson.parse(raw, RECEIPT_MAX_BYTES), flavor);
    }

    public static CurrentSavedPreflightContract parse(JsonNode value, PathFlavor flavor) {
        ObjectNode row = StrictJson.object(value, FIELDS);
        equalText(row.get("schema"), CurrentSavedPreflightContract.SCHEMA);
        equalText(row.get("phase"), CurrentSavedPreflightContract.Phase.OfflineColdContractQualified.name());
        StrictJson.trueValue(row.get("read_only_game_start_permitted"));
        for (String key : List.of("full_loop_permitted", "original_actions_replayed", "live_semantic_accepted", "live_warm_bound")) {
            falseValue(row.get(key));
        }
        zero(row.get("ordinary_cycle_credit")); zero(row.get("game_day_credit"));
        StrictJson.require(StrictJson.integer(row.get("canonical_entry_count"), 0, StrictJson.MAX_SAFE_INTEGER) == 8,
                "canonical eight retained");
        JsonNode sourceNodes = row.get("runtime_source_refs");
        StrictJson.require(sourceNodes != null && sourceNodes.isArray(), "JSON array required");
        StrictJson.require(sourceNodes.size() >= CurrentSavedPreflightContract.CANONICAL_ENTRY_COUNT
                        && sourceNodes.size() <= CurrentSavedPreflightContract.MAX_CLOSURE_COUNT,
                "finite unique receiver source pins");
        List<ExactRef> sources = new ArrayList<>();
        for (JsonNode item : sourceNodes) { sources.add(ExactRef.fromJson(item)); }
        return new CurrentSavedPreflightContract(StrictJson.text(row.get("machine_id")),
                StrictJson.text(row.get("observed_at_utc")), StrictJson.text(row.get("runtime_root")),
                StrictJson.text(row.get("attempt_nonce")), StrictJson.text(row.get("task_nonce")),
                ExactRef.fromJson(row.get("plan_ref")), ExactRef.fromJson(row.get("quote_ref")),
                ExactRef.fromJson(row.get("basis_ref")), ExactRef.fromJson(row.get("validation_ref")),
                ExactRef.fromJson(row.get("core_source_ref")), sources, parseHistorical(row.get("historical_replay")),
                ExactRef.fromJson(row.get("startup_dispatch_replay_ref")), ExactRef.fromJson(row.get("consumer_probe_ref")),
                StrictJson.integer(row.get("current_next_sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("files_verified"), 1, StrictJson.MAX_SAFE_INTEGER),
                (int) StrictJson.integer(row.get("closure_count"), 1, CurrentSavedPreflightContract.MAX_CLOSURE_COUNT), flavor);
    }

    public static HistoricalSemanticReplay parseHistorical(JsonNode value) {
        ObjectNode row = StrictJson.object(value, REPLAY_FIELDS);
        StrictJson.trueValue(row.get("historical_outer_context_reconstructed"));
        falseValue(row.get("historical_row_modified")); falseValue(row.get("fresh_native_readiness_claimed"));
        zero(row.get("actual_rpc_calls")); zero(row.get("canonical_score_writes"));
        return new HistoricalSemanticReplay(ExactRef.fromJson(row.get("receipt_ref")),
                ExactRef.fromJson(row.get("helper_ref")), ExactRef.fromJson(row.get("semantic_ref")),
                ExactRef.fromJson(row.get("launch_ref")), ExactRef.fromJson(row.get("original_cold_ref")),
                ExactRef.fromJson(row.get("original_queue_ref")), ExactRef.fromJson(row.get("score_ref")),
                ExactRef.fromJson(row.get("anchor_ref")),
                StrictJson.integer(row.get("historical_sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(row.get("check_after_ast_sha256")));
    }

    public static byte[] encode(CurrentSavedPreflightContract value) {
        return StrictJson.canonical(toJson(value), RECEIPT_MAX_BYTES);
    }

    public static ObjectNode toJson(CurrentSavedPreflightContract value) {
        StrictJson.require(value != null, "validated preflight contract required");
        ObjectNode row = StrictJson.object();
        row.put("schema", CurrentSavedPreflightContract.SCHEMA); row.put("machine_id", value.machineId());
        row.put("observed_at_utc", value.observedAtUtc()); row.put("phase", value.phase().name());
        row.put("runtime_root", value.runtimeRoot()); row.put("attempt_nonce", value.attemptNonce());
        row.put("task_nonce", value.taskNonce());
        row.set("plan_ref", value.planRef().toJson()); row.set("quote_ref", value.quoteRef().toJson());
        row.set("basis_ref", value.basisRef().toJson()); row.set("validation_ref", value.validationRef().toJson());
        row.set("core_source_ref", value.coreSourceRef().toJson());
        ArrayNode sources = row.putArray("runtime_source_refs");
        for (ExactRef ref : value.runtimeSourceRefs()) { sources.add(ref.toJson()); }
        row.set("historical_replay", historicalJson(value.historicalReplay()));
        row.set("startup_dispatch_replay_ref", value.startupDispatchReplayRef().toJson());
        row.set("consumer_probe_ref", value.consumerProbeRef().toJson());
        row.put("current_next_sequence", value.currentNextSequence()); row.put("files_verified", value.filesVerified());
        row.put("canonical_entry_count", CurrentSavedPreflightContract.CANONICAL_ENTRY_COUNT);
        row.put("closure_count", value.closureCount()); row.put("read_only_game_start_permitted", true);
        row.put("full_loop_permitted", false); row.put("ordinary_cycle_credit", 0); row.put("game_day_credit", 0);
        row.put("original_actions_replayed", false); row.put("live_semantic_accepted", false); row.put("live_warm_bound", false);
        return row;
    }

    public static ObjectNode historicalJson(HistoricalSemanticReplay value) {
        StrictJson.require(value != null, "validated historical semantic replay required");
        ObjectNode row = StrictJson.object();
        for (int i = 0; i < REPLAY_REFS.size(); i++) { row.set(REPLAY_REFS.get(i), value.references().get(i).toJson()); }
        row.put("historical_sequence", value.historicalSequence()); row.put("check_after_ast_sha256", value.checkAfterAstSha256());
        row.put("historical_outer_context_reconstructed", true); row.put("historical_row_modified", false);
        row.put("actual_rpc_calls", 0); row.put("canonical_score_writes", 0); row.put("fresh_native_readiness_claimed", false);
        return row;
    }

    /** Caller must independently perform the original reader revalidation before comparing. */
    public static boolean sameRevalidatedBinding(CurrentSavedPreflightContract sealed, CurrentSavedPreflightContract actual) {
        ObjectNode left = toJson(sealed), right = toJson(actual);
        left.remove("observed_at_utc"); right.remove("observed_at_utc");
        return left.equals(right);
    }

    private static void equalText(JsonNode value, String expected) {
        StrictJson.require(value != null && value.isTextual() && expected.equals(value.textValue()),
                "exact offline preflight contract");
    }

    private static void falseValue(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(), "offline scope requires actual false");
    }

    private static void zero(JsonNode value) {
        StrictJson.require(StrictJson.integer(value, 0, StrictJson.MAX_SAFE_INTEGER) == 0, "offline credit remains zero");
    }
}
