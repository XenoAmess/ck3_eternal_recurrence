package org.xar.ck3.control.admission.closedpartial;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.EnumSet;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryReducer;
import org.xar.ck3.control.recovery.RecoveryPreview;

/** Pure producer of source-bound metadata. Neither output is a cold/admission authorization. */
public final class ClosedPartialEpochProducer {
    private ClosedPartialEpochProducer() { }
    public record Produced(ClosedPartialEpochCodec.Epoch epoch, byte[] epochBytes, byte[] prefixBytes) {
        public Produced { epochBytes = epochBytes.clone(); prefixBytes = prefixBytes.clone(); }
        @Override public byte[] epochBytes() { return epochBytes.clone(); }
        @Override public byte[] prefixBytes() { return prefixBytes.clone(); }
        public boolean ready() { return false; }
    }

    public static Produced compose(ClosedFailureRecoveryInput input, ClosedPartialSources sources) {
        RecoveryPreview preliminary = ClosedFailureRecoveryReducer.preview(input);
        StrictJson.require(preliminary instanceof RecoveryPreview.Unavailable,
                "original failed FULL/raw pending/source contract must precede pure epoch projection");
        ObjectNode basis = metadata(input.savedBasis());
        ObjectNode savedFrame = object(basis.get("frame"));
        long savedCycles = number(basis, "completed_cycles", 0), date = number(savedFrame, "date_raw", 0);
        long full = number(metadata(input.fullRequest()), "sequence", 1);
        long unknown = number(metadata(input.autoRequest()), "sequence", 1);
        StrictJson.require(number(metadata(input.rawState()), "completed_cycles", 0)
                == savedCycles + sources.settledCycles().size(), "actual raw prefix count, not a new credit");
        validateClosure(input, sources);
        ObjectNode prefix = StrictJson.object(); prefix.put("schema", ClosedPartialEpochCodec.PREFIX_SCHEMA);
        prefix.put("machine_id", input.machineId()); prefix.put("input_digest", ClosedFailureRecoveryReducer.inputDigest(input));
        prefix.put("full_sequence", full); prefix.put("unknown_sequence", unknown);
        prefix.put("saved_cycles", savedCycles); prefix.put("settled_cycles", sources.settledCycles().size());
        prefix.put("new_ordinary_cycle_credit", 0); prefix.put("new_game_day_credit", 0);
        prefix.put("original_unknown_replayed", false); prefix.put("raw_pending_modified", false);
        prefix.put("qualification_scope", "SOURCE_BOUND_ZERO_DAY_ROWS_ONLY_ORIGINAL_CLASSIFIER_STILL_REQUIRED");
        prefix.set("capture_closed", sources.captureClosed().reference().toJson());
        ArrayNode rows = prefix.putArray("rows"); long sequence = full + 1;
        for (ClosedPartialSources.Cycle cycle : sources.settledCycles()) {
            ObjectNode auto = successful(cycle.auto(), sequence++, "ck3_auto_turn");
            ObjectNode met = successful(cycle.metrics(), sequence++, "root_current_runtime_metrics");
            StrictJson.require(number(met, "date_raw", 0) == date
                    && number(met, "actor_character_id", 1) == number(savedFrame, "actor_character_id", 1)
                    && text(met, "episode_run_id").equals(text(savedFrame, "episode_run_id")), "actual zero-day same-episode MET");
            StrictJson.trueValue(met.get("paused")); StrictJson.trueValue(met.get("map_ready"));
            StrictJson.require(text(auto, "status").equals("executed"), "actual settled AUTO execution result");
            String step = text(auto, "selected_step");
            // A query-shaped name is retained as evidence only; it does not replace the original source classifier.
            StrictJson.require(step.startsWith("query-"), "material actions require a different saved frontier recovery");
            if (auto.has("planning_source_frame")) {
                ObjectNode frame = object(auto.get("planning_source_frame"));
                StrictJson.require(number(frame, "date_raw", 0) == date
                        && number(frame, "actor_character_id", 1) == number(savedFrame, "actor_character_id", 1)
                        && text(frame, "episode_run_id").equals(text(savedFrame, "episode_run_id")), "AUTO planning frame identity");
            }
            ObjectNode row = rows.addObject(); row.set("auto", cycle.auto().reference().toJson());
            row.set("metrics", cycle.metrics().reference().toJson()); row.put("selected_step", step);
            row.put("date_raw", date); row.put("actor_character_id", number(met, "actor_character_id", 1));
            row.put("episode_run_id", text(met, "episode_run_id"));
        }
        StrictJson.require(sequence == unknown, "prefix ends immediately before the preserved UNKNOWN AUTO");
        ArrayNode tasks = prefix.putArray("task_sources");
        for (ClosedPartialSources.Task task : sources.tasks()) {
            ObjectNode row = tasks.addObject(); row.put("role", task.role().name());
            row.set("spec", task.spec().reference().toJson()); row.set("closed", task.closed().reference().toJson());
            row.set("unregistered", task.unregistered().reference().toJson());
        }
        ClosedPartialEpochCodec.Epoch epoch = new ClosedPartialEpochCodec.Epoch(input.machineId(), input.observedAtUtc(),
                ClosedFailureRecoveryReducer.inputDigest(input), full, unknown, unknown + 1, savedCycles,
                sources.settledCycles().size(), date, sources.sdkClosed().reference(), sources.gameExit().reference(),
                sources.supervisorClosed().reference(), sources.recordingClosed().reference(), sources.screenReleased().reference());
        byte[] epochBytes = ClosedPartialEpochCodec.encode(epoch);
        StrictJson.require(ClosedPartialEpochCodec.decode(epochBytes).equals(epoch), "new typed epoch serialization round trip");
        return new Produced(epoch, epochBytes, StrictJson.canonical(prefix, StrictJson.OUTPUT_MAX_BYTES));
    }

    private static ObjectNode successful(ClosedPartialRpcEvidence evidence, long sequence, String tool) {
        ObjectNode outer = evidence.object(), request = object(outer.get("request")), result = object(outer.get("result"));
        StrictJson.require(number(request, "sequence", 1) == sequence && text(request, "tool").equals(tool)
                && object(request.get("arguments")).isEmpty(), "exact original ordered AUTO/MET request");
        ClosedPartialEpochCodec.falseValue(result.get("is_error"));
        StrictJson.require(text(result, "result_type").equals("complete"), "actual RPC complete, not scheduling ACK");
        return object(result.get("structured_content"));
    }

    private static void validateClosure(ClosedFailureRecoveryInput input, ClosedPartialSources sources) {
        ObjectNode sdk = metadata(sources.sdkClosed()), game = metadata(sources.gameExit());
        ObjectNode supervisor = metadata(sources.supervisorClosed());
        for (ObjectNode row : java.util.List.of(sdk, game, supervisor)) {
            StrictJson.require(text(row, "machine_id").equals(input.machineId()), "same actual execution machine");
        }
        StrictJson.require(text(sdk, "status").equals("ACTUAL_BOTH_SDK_EXITS_OBSERVED"), "actual both SDK exits required");
        JsonNode processes = sdk.get("processes"); StrictJson.require(processes != null && processes.isArray() && processes.size() == 2,
                "exact SDK process pair");
        Set<String> roles = new java.util.HashSet<>();
        for (JsonNode node : processes) {
            ObjectNode process = object(node); roles.add(text(process, "role")); number(process, "pid", 1);
            StrictJson.integer(process.get("creation_filetime"), java.math.BigInteger.ONE, StrictJson.UINT64_MAX);
            StrictJson.trueValue(process.get("kernel_exit_observed")); StrictJson.integer(process.get("wait_result"), 0, 0);
            StrictJson.integer(process.get("exit_code"), 0, 4_294_967_295L);
            StrictJson.require(process.has("observation_error") && process.get("observation_error").isNull(), "SDK exit observation error absent");
            text(process, "executable");
        }
        StrictJson.require(roles.equals(Set.of("sdk_queue", "sdk_application")), "unique SDK roles");
        ObjectNode sdkAgain = object(supervisor.get("sdk_actual_exit"));
        StrictJson.require(java.util.Objects.equals(sdkAgain.get("processes"), processes)
                && text(sdkAgain, "status").equals(text(sdk, "status")), "independent supervisor SDK pair binding");
        StrictJson.trueValue(game.get("kernel_signaled"));
        StrictJson.integer(game.get("creation_filetime"), java.math.BigInteger.ONE, StrictJson.UINT64_MAX);
        ObjectNode owned = object(supervisor.get("owned_cleanup"));
        StrictJson.trueValue(owned.get("cleanup_proven")); StrictJson.trueValue(owned.get("tree_gone"));
        StrictJson.integer(owned.get("job_active_processes_final"), 0, 0);
        StrictJson.require(number(game, "pid", 1) == number(owned, "ck3_pid", 1)
                && number(game, "exit_code", 0) == number(owned, "ck3_exit_code", 0), "actual owned Game exit binding");
        StrictJson.require(number(game, "pid", 1) == number(object(metadata(input.predecessor()).get("game_binding")), "pid", 1),
                "closed Game is the original canonical epoch Game");
        ObjectNode before = object(object(supervisor.get("known_preload_phase")).get("before"));
        StrictJson.require(java.util.Objects.equals(before.get("creation_filetime"), game.get("creation_filetime")), "exact unrounded Game birth");
        ObjectNode keeper = object(supervisor.get("keeper")); StrictJson.trueValue(keeper.get("thread_exited"));
        StrictJson.require(keeper.has("failure") && keeper.get("failure").isNull(), "keeper stopped without failure");
        ObjectNode bus = metadata(sources.screenReleased()), task = object(bus.get("task")), event = object(bus.get("event"));
        StrictJson.require(text(bus, "schema").equals("codex.task_bus.v1"), "actual direct bus receipt, no invented returncode");
        StrictJson.trueValue(bus.get("ok"));
        StrictJson.require(text(task, "task_id").equals(text(keeper, "task_id"))
                && text(event, "task_id").equals(text(task, "task_id"))
                && text(task, "state").equals("done") && text(event, "state").equals("done")
                && text(event, "kind").equals("completed")
                && number(task, "last_sequence", 1) == number(event, "sequence", 1)
                && number(event, "sequence", 1) > number(keeper, "last_sequence", 1)
                && emptyArray(task.get("resources")) && emptyArray(event.get("resources")), "screen lease actual terminal CAS, not ACK");
        ObjectNode recording = metadata(sources.recordingClosed());
        StrictJson.require(text(recording, "machine_id").equals(input.machineId()), "recording machine binding");
        StrictJson.require(text(recording, "status").equals("CLEANUP_OBSERVED"), "actual recording shutdown status");
        StrictJson.trueValue(recording.get("capture_closed_verified"));
        StrictJson.trueValue(recording.get("inputs_unbound"));
        StrictJson.trueValue(recording.get("normal_engine_exit_proven"));
        StrictJson.integer(recording.get("engine_exit_code"), 0, 0);
        ObjectNode captureRef = object(recording.get("capture_closed")), capture = metadata(sources.captureClosed());
        StrictJson.require(text(captureRef, "path").equals(sources.captureClosed().reference().path())
                && text(captureRef, "sha256").equals(sources.captureClosed().reference().sha256())
                && text(capture, "schema").equals("xar.ck3.capture-closed-before-media-hash/v1")
                && number(capture, "game_pid", 1) == number(game, "pid", 1)
                && java.util.Objects.equals(capture.get("game_creation_filetime"), game.get("creation_filetime")), "actual capture tied to exact Game");
        StrictJson.trueValue(capture.get("inputs_unbound"));
        ObjectNode engine = object(capture.get("engine_close")); StrictJson.trueValue(engine.get("normal_exit_proven"));
        StrictJson.integer(engine.get("actual_exit_code"), 0, 0); StrictJson.integer(engine.get("forced_process_calls"), 0, 0);
        EnumSet<ClosedPartialSources.TaskRole> taskRoles = EnumSet.noneOf(ClosedPartialSources.TaskRole.class);
        for (ClosedPartialSources.Task closure : sources.tasks()) {
            StrictJson.require(taskRoles.add(closure.role()), "unique actual task role");
            ObjectNode spec = metadata(closure.spec()), closed = metadata(closure.closed()), unregister = metadata(closure.unregistered());
            StrictJson.require(text(closed, "machine_id").equals(input.machineId())
                    && text(unregister, "machine_id").equals(input.machineId())
                    && text(closed, "spec_sha256").equals(closure.spec().reference().sha256())
                    && text(closed, "nonce").equals(text(spec, "nonce")), "exact task source and nonce");
            StrictJson.integer(closed.get("job_active_after_stage"), 0, 0);
            number(closed, "child_exit_code", 0); number(closed, "bootstrap_exit_code", 0);
            StrictJson.integer(unregister.get("returncode"), 0, 0);
            ObjectNode result = object(StrictJson.parse(text(unregister, "stdout").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            StrictJson.require(text(result, "operation").equals("unregister"), "actual unregister operation");
            ObjectNode actual = object(result.get("actual")); StrictJson.trueValue(actual.get("absent_after"));
            StrictJson.integer(actual.get("instances"), 0, 0);
            StrictJson.require(text(result, "task_name").equals(text(spec, "task_name"))
                    && text(result, "machine_id").equals(input.machineId()), "unregister exact task identity");
        }
    }
    private static ObjectNode object(JsonNode node) { return ClosedPartialEpochCodec.object(node); }
    private static boolean emptyArray(JsonNode node) { return node != null && node.isArray() && node.isEmpty(); }
    private static ObjectNode metadata(org.xar.ck3.control.recovery.RecoveryEvidence evidence) {
        return object(StrictJson.parse(evidence.bytes()));
    }
    private static long number(ObjectNode row, String key, long min) { return ClosedPartialEpochCodec.number(row, key, min); }
    private static String text(ObjectNode row, String key) { return StrictJson.text(row.get(key)); }
}
