package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialEpochProducer;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialSources;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Complete actual settled-query/capture qualification. Original SDK cache checks no longer own this policy. */
public final class ClosedPartialBusinessAuthority {
    private static final String CLASSIFIER_SHA = "0bff8fae24c072d5f05285ba62c503dfed408f8095690fb8dffec16fe72ec28b";
    private static final String QUEUE_SHA = "5493ce58688ffcbf4711de6e17041e2019424334752ea77785a8f2eefb330867";
    private ClosedPartialBusinessAuthority() { }
    public static String verify(ClosedFailureRecoveryInput input, ClosedPartialSources source,
            ClosedAdoptionSources business, ClosedAdoptionSources.SourceVerifier sourceVerifier) {
        ClosedPartialEpochProducer.compose(input, source);
        for (ExactRef reference : input.metadataSources()) { sourceVerifier.verify(reference); }
        for (RecoveryEvidence evidence : java.util.List.of(source.sdkClosed(), source.gameExit(), source.supervisorClosed(),
                source.recordingClosed(), source.captureClosed(), source.screenReleased())) { sourceVerifier.verify(evidence.reference()); }
        for (ClosedPartialSources.Task task : source.tasks()) {
            sourceVerifier.verify(task.spec().reference()); sourceVerifier.verify(task.closed().reference()); sourceVerifier.verify(task.unregistered().reference());
        }
        StrictJson.require(source.settledCycles().size() == business.cycles().size(), "one complete metadata set per settled cycle");
        for (RecoveryEvidence evidence : java.util.List.of(business.savedSeed(), business.savedGovernance(), business.coldBound(),
                business.openingSemantic(), business.openingCapabilities(), business.classifierPin(), business.captureProbe(), business.captureCleanup())) {
            sourceVerifier.verify(evidence.reference());
        }
        sourceVerifier.verify(business.classifierSource()); sourceVerifier.verify(business.queueSource());
        StrictJson.require(business.classifierSource().sha256().equals(CLASSIFIER_SHA)
                && business.queueSource().sha256().equals(QUEUE_SHA), "source version covered by this translated classifier, no guessed newer semantics");
        ObjectNode pin = object(business.classifierPin()); equal(pin, "machine_id", input.machineId());
        equal(pin, "source", business.classifierSource().path()); equal(pin, "sha256", business.classifierSource().sha256());
        ObjectNode basis = object(input.savedBasis()), refs = node(basis.get("refs"));
        StrictJson.require(ExactRef.fromJson(refs.get("seed")).equals(business.savedSeed().reference())
                && ExactRef.fromJson(refs.get("governance")).equals(business.savedGovernance().reference()), "original clean saved seed/governance sources");
        ObjectNode seed = object(business.savedSeed()), governance = object(business.savedGovernance());
        ObjectNode counts = node(seed.get("counts")).deepCopy();
        ObjectNode bound = object(business.coldBound()); equal(bound, "schema", "xar.c23.normal-checkpoint-cold-bound/v1");
        equal(bound, "machine_id", input.machineId());
        SavedFrame frame = SavedFrame.fromJson(bound.get("opening_frame")), saved = SavedFrame.fromJson(basis.get("frame"));
        sameBusinessFrame(frame, saved);
        StrictJson.require(bound.get("checkpoint").equals(seed.get("actual_saved_checkpoint")), "original actual checkpoint at new cold opening");
        equal(bound, "semantic_response", business.openingSemantic().reference().path());
        ObjectNode semantic = completed(object(business.openingSemantic()), "ck3_take_semantic_snapshot_private_v1"), cap = completed(object(business.openingCapabilities()), "ck3_get_capabilities");
        StrictJson.require(number(semantic, "episode_character_id", 1) == frame.actorCharacterId(), "opening original semantic actor");
        equal(semantic, "episode_run_id", frame.episodeRunId()); equal(semantic, "snapshot_id", frame.snapshotId());
        StrictJson.require(number(semantic, "date_raw", 0) == frame.dateRaw()
                && number(semantic, "revision", 1) == frame.revision() && number(semantic, "native_revision", 1) == frame.nativeRevision(), "original semantic opening frame");
        StrictJson.trueValue(semantic.get("paused")); StrictJson.trueValue(semantic.get("map_ready"));
        equal(cap, "episode_run_id", frame.episodeRunId());
        StrictJson.require(number(cap, "episode_character_id", 1) == frame.actorCharacterId(), "opening capability episode");
        long cycles = number(basis, "completed_cycles", 0), full = number(object(input.fullRequest()), "sequence", 1);
        StrictJson.require(number(node(object(business.openingSemantic()).get("request")), "sequence", 1) == full - 2
                && number(node(object(business.openingCapabilities()).get("request")), "sequence", 1) == full - 1, "actual SEM/CAP prefix ordering");
        long gamePid = number(object(source.gameExit()), "pid", 1);
        String lastMetrics = business.openingSemantic().reference().path();
        ObjectNode audit = StrictJson.object(); audit.put("classifier_contract", SettledQueryClassifier.CONTRACT);
        audit.set("classifier_source", business.classifierSource().toJson()); audit.set("queue_source", business.queueSource().toJson());
        var lineage = audit.putArray("cycles");
        for (int i = 0; i < business.cycles().size(); i++) {
            ClosedAdoptionSources.CycleSources metadata = business.cycles().get(i);
            for (RecoveryEvidence evidence : java.util.List.of(metadata.event(), metadata.ordinaryCredit(), metadata.autoAfter(), metadata.metricsAfter(), metadata.beforePlan())) {
                sourceVerifier.verify(evidence.reference());
            }
            ClosedPartialSources.Cycle rpc = source.settledCycles().get(i);
            sourceVerifier.verify(rpc.auto().reference()); sourceVerifier.verify(rpc.metrics().reference());
            ObjectNode auto = completed(rpc.auto().object(), "ck3_auto_turn");
            ObjectNode met = completed(rpc.metrics().object(), "root_current_runtime_metrics");
            ObjectNode event = object(metadata.event()), credit = object(metadata.ordinaryCredit());
            long sequence = full + 1 + i * 2L;
            SavedFrame after = frameFromMetrics(met); sameBusinessFrame(after, saved);
            StrictJson.trueValue(met.get("paused")); StrictJson.trueValue(met.get("map_ready")); StrictJson.trueValue(met.get("actor_alive"));
            StrictJson.require(number(met, "bridge_pid", 1) == gamePid, "actual same closed Game MET");
            ObjectNode observation = SettledQueryClassifier.classify(auto, frame);
            StrictJson.require(observation.equals(event.get("observation")) && observation.equals(credit.get("observation")),
                    "independent Java classification equals both original settled event and original ordinary credit");
            equal(event, "stage", "auto_verified"); equal(event, "auto_response", rpc.auto().reference().path());
            equal(event, "after_metrics_response", rpc.metrics().reference().path()); equal(event, "before_metrics_response", lastMetrics);
            equal(event, "selected_step", SettledQueryClassifier.text(auto, "selected_step"));
            StrictJson.require(SavedFrame.fromJson(event.get("before")).equals(frame) && SavedFrame.fromJson(event.get("after")).equals(after)
                    && number(event, "global_turn", 1) == cycles + i + 1 && number(event, "auto_sequence", 1) == sequence, "original complete settled cycle identity");
            StrictJson.integer(event.get("date_delta_raw"), 0, 0); SettledQueryClassifier.falseValue(event.get("business_success_inferred"));
            equal(credit, "source_response", rpc.auto().reference().path());
            ObjectNode plan = object(metadata.beforePlan()); equal(plan, "source", "actual GameplayBridgeService.before_submit callback");
            StrictJson.require(number(plan, "game_pid", 1) == gamePid && number(node(plan.get("request")), "parent_sequence", 1) == sequence, "original before-submit parent/source");
            ObjectNode planned = node(node(plan.get("result")).get("structured_content"));
            equal(planned, "selected_step", SettledQueryClassifier.text(auto, "selected_step"));
            marker(object(metadata.autoAfter()), rpc.auto().reference(), "ck3_auto_turn");
            marker(object(metadata.metricsAfter()), rpc.metrics().reference(), "root_current_runtime_metrics");
            observeCounts(counts, observation);
            StrictJson.require(counts.equals(event.get("cumulative_observation_counts")), "original exact cumulative observation counters");
            if (metadata.readonlySaveSkip().isPresent()) {
                RecoveryEvidence skipEvidence = metadata.readonlySaveSkip().orElseThrow(); sourceVerifier.verify(skipEvidence.reference());
                ObjectNode skip = object(skipEvidence); equal(skip, "status", "unchanged_readonly_evidence_chain");
                StrictJson.require(number(skip, "global_turn", 1) == cycles + i + 1 && SavedFrame.fromJson(skip.get("frame")).equals(after), "actual read-only SAVE skip source");
                SettledQueryClassifier.falseValue(skip.get("new_gameplay_mutations_observed")); StrictJson.trueValue(skip.get("last_actual_checkpoint_retained"));
                recordReadonlyCheckpointSkip(counts);
            }
            lineage.add(metadata.event().reference().toJson()); frame = after; lastMetrics = rpc.metrics().reference().path();
        }
        ObjectNode raw = object(input.rawState()), rawGov = object(input.rawGovernance());
        StrictJson.require(SavedFrame.fromJson(raw.get("before")).equals(frame) && counts.equals(raw.get("counts")), "actual raw partial prefix frontier/counters");
        equal(raw, "before_metrics_response", lastMetrics);
        ObjectNode pending = node(raw.get("pending_cycle")); equal(pending, "before_metrics_response", lastMetrics);
        StrictJson.require(java.util.Objects.equals(rawGov.get("state"), governance.get("governance_result_state"))
                && java.util.Objects.equals(rawGov.get("pending_focus"), governance.get("pending_focus")), "read-only prefix retains saved governance/focus without new material credit");
        capture(source, business);
        return RecoveryEvidence.sha256(StrictJson.canonical(audit));
    }
    private static void capture(ClosedPartialSources source, ClosedAdoptionSources business) {
        ObjectNode capture = object(source.captureClosed()), probe = object(business.captureProbe()), cleanup = object(business.captureCleanup());
        referenceWithoutSize(capture, "closed_file_probe", business.captureProbe().reference());
        referenceWithoutSize(capture, "cleanup", business.captureCleanup().reference());
        StrictJson.trueValue(cleanup.get("inputs_unbound")); StrictJson.trueValue(node(cleanup.get("engine_close")).get("normal_exit_proven"));
        StrictJson.integer(node(cleanup.get("engine_close")).get("actual_exit_code"), 0, 0);
        StrictJson.integer(node(cleanup.get("engine_close")).get("forced_process_calls"), 0, 0);
        StrictJson.integer(cleanup.get("unknown_or_global_stop_calls"), 0, 0);
        JsonNode streams = probe.get("streams"); StrictJson.require(streams != null && streams.isArray(), "actual closed capture probe");
        boolean video = false;
        for (JsonNode entry : streams) { if ("video".equals(node(entry).path("codec_type").asText())) { video = true; } }
        StrictJson.require(video, "actual recording video stream");
        String bytes = StrictJson.text(node(probe.get("format")).get("size"));
        StrictJson.require(bytes.matches("[1-9][0-9]*") && new java.math.BigInteger(bytes).equals(capture.get("output_bytes").bigIntegerValue()), "closed capture output size proof");
    }
    private static void referenceWithoutSize(ObjectNode row, String field, ExactRef ref) {
        ObjectNode value = node(row.get(field)); equal(value, "path", ref.path()); equal(value, "sha256", ref.sha256());
    }
    static void observeCounts(ObjectNode counts, ObjectNode observation) {
        increment(counts, observation, "typed_nonmaterial_observation", "typed_nonmaterial_observation_turns");
        increment(counts, observation, "existing_focus_verified", "existing_focus_verified_turns");
        increment(counts, observation, "primitive_accepted", "primitive_accepted_turns");
    }
    static void recordReadonlyCheckpointSkip(ObjectNode counts) { incrementCounter(counts, "checkpoint_readonly_skipped"); }
    private static void incrementCounter(ObjectNode counts, String counter) {
        long next = StrictJson.safe(Math.addExact(number(counts, counter, 0), 1), 0);
        // StrictJson parses original JSON integers as BigIntegerNode. Preserve that same
        // integer domain so the complete exact counter comparisons retain their meaning.
        counts.put(counter, java.math.BigInteger.valueOf(next));
    }
    private static void increment(ObjectNode counts, ObjectNode observation, String flag, String counter) {
        JsonNode value = observation.get(flag); if (value != null && value.isBoolean() && value.booleanValue()) {
            incrementCounter(counts, counter);
        }
    }
    private static void marker(ObjectNode marker, ExactRef response, String tool) { equal(marker, "response", response.path()); equal(marker, "tool", tool); }
    private static SavedFrame frameFromMetrics(ObjectNode value) {
        ObjectNode row = StrictJson.object(); for (String key : Set.of("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id", "episode_run_id")) { row.set(key, value.get(key)); }
        return SavedFrame.fromJson(row);
    }
    private static void sameBusinessFrame(SavedFrame actual, SavedFrame saved) {
        StrictJson.require(actual.dateRaw() == saved.dateRaw() && actual.actorCharacterId() == saved.actorCharacterId()
                && actual.episodeRunId().equals(saved.episodeRunId()), "same saved business actor/date/episode");
    }
    private static ObjectNode completed(ObjectNode outer, String tool) {
        equal(node(outer.get("request")), "tool", tool); ObjectNode result = node(outer.get("result"));
        SettledQueryClassifier.falseValue(result.get("is_error")); equal(result, "result_type", "complete"); return node(result.get("structured_content"));
    }
    private static ObjectNode object(RecoveryEvidence value) { return node(StrictJson.parse(value.bytes())); }
    private static ObjectNode node(JsonNode value) { return SettledQueryClassifier.object(value); }
    private static void equal(ObjectNode row, String key, String expected) { SettledQueryClassifier.equal(row, key, expected); }
    private static long number(ObjectNode row, String key, long min) { return SettledQueryClassifier.number(row, key, min); }
}
