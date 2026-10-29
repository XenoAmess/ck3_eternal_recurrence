package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialSources;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Parameter-only Root request. It contains no successful-proof flag and no executable command. */
public record ClosedAdoptionRequest(String machineId, String observedAtUtc, InputRefs inputs, ClosedRefs closed,
        List<TaskRefs> tasks, List<CycleRefs> cycles, BusinessRefs business, Path canonicalPath, Path metadataRoot, ExactRef writerSource) {
    public ClosedAdoptionRequest {
        StrictJson.text(machineId); StrictJson.utc(observedAtUtc); Objects.requireNonNull(inputs); Objects.requireNonNull(closed);
        tasks = List.copyOf(tasks); cycles = List.copyOf(cycles); Objects.requireNonNull(business);
        Objects.requireNonNull(canonicalPath); Objects.requireNonNull(metadataRoot); Objects.requireNonNull(writerSource);
        StrictJson.require(tasks.size() == 3 && !cycles.isEmpty() && cycles.size() <= 30, "complete bounded closed partial sources");
        StrictJson.require(canonicalPath.isAbsolute() && metadataRoot.isAbsolute(), "Root-selected absolute target paths");
    }
    public record InputRefs(ExactRef predecessor, ExactRef savedBasis, ExactRef priorQualification, ExactRef fullRequest,
            ExactRef failedFull, ExactRef autoRequest, ExactRef failedAuto, ExactRef rawState, ExactRef rawGovernance, ExactRef actualNext) {
        public InputRefs { List.of(predecessor,savedBasis,priorQualification,fullRequest,failedFull,autoRequest,failedAuto,rawState,rawGovernance,actualNext); }
    }
    public record ClosedRefs(ExactRef sdk, ExactRef gameExit, ExactRef supervisor, ExactRef recording, ExactRef capture, ExactRef screen) {
        public ClosedRefs { List.of(sdk,gameExit,supervisor,recording,capture,screen); }
    }
    public record TaskRefs(ClosedPartialSources.TaskRole role, ExactRef spec, ExactRef closed, ExactRef unregistered) {
        public TaskRefs { Objects.requireNonNull(role); List.of(spec,closed,unregistered); }
    }
    public record CycleRefs(ExactRef auto, ExactRef metrics, ExactRef event, ExactRef ordinaryCredit, ExactRef autoAfter,
            ExactRef metricsAfter, ExactRef beforePlan, Optional<ExactRef> readonlySaveSkip) {
        public CycleRefs { List.of(auto,metrics,event,ordinaryCredit,autoAfter,metricsAfter,beforePlan); Objects.requireNonNull(readonlySaveSkip); }
    }
    public record BusinessRefs(ExactRef savedSeed, ExactRef savedGovernance, ExactRef coldBound, ExactRef openingSemantic,
            ExactRef openingCapabilities, ExactRef classifierPin, ExactRef classifierSource, ExactRef queueSource, ExactRef captureProbe, ExactRef captureCleanup) {
        public BusinessRefs { List.of(savedSeed,savedGovernance,coldBound,openingSemantic,openingCapabilities,classifierPin,classifierSource,queueSource,captureProbe,captureCleanup); }
    }
    public static ClosedAdoptionRequest decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("schema","machine_id","observed_at_utc","inputs","closed","tasks","cycles","business","canonical_path","metadata_root","writer_source"));
        StrictJson.require("xar.java-closed-partial-adoption-request/v1".equals(StrictJson.text(root.get("schema"))), "closed adoption parameter schema");
        ObjectNode input = StrictJson.object(root.get("inputs"), Set.of("predecessor","saved_basis","prior_qualification","full_request","failed_full","auto_request","failed_auto","raw_state","raw_governance","actual_next"));
        InputRefs inputs = new InputRefs(ref(input,"predecessor"),ref(input,"saved_basis"),ref(input,"prior_qualification"),ref(input,"full_request"),
                ref(input,"failed_full"),ref(input,"auto_request"),ref(input,"failed_auto"),ref(input,"raw_state"),ref(input,"raw_governance"),ref(input,"actual_next"));
        ObjectNode closed = StrictJson.object(root.get("closed"), Set.of("sdk","game_exit","supervisor","recording","capture","screen"));
        ClosedRefs closures = new ClosedRefs(ref(closed,"sdk"),ref(closed,"game_exit"),ref(closed,"supervisor"),ref(closed,"recording"),ref(closed,"capture"),ref(closed,"screen"));
        List<TaskRefs> tasks = new ArrayList<>();
        for (JsonNode entry : array(root.get("tasks"))) {
            ObjectNode task = StrictJson.object(entry, Set.of("role","spec","closed","unregistered"));
            String role = StrictJson.text(task.get("role"));
            StrictJson.require(Set.of("SUPERVISOR","FEEDER","DISPLAY").contains(role), "fixed task role");
            tasks.add(new TaskRefs(ClosedPartialSources.TaskRole.valueOf(role),ref(task,"spec"),ref(task,"closed"),ref(task,"unregistered")));
        }
        List<CycleRefs> cycles = new ArrayList<>();
        for (JsonNode entry : array(root.get("cycles"))) {
            ObjectNode cycle = StrictJson.object(entry, Set.of("auto","metrics","event","ordinary_credit","auto_after","metrics_after","before_plan","readonly_save_skip"));
            cycles.add(new CycleRefs(ref(cycle,"auto"),ref(cycle,"metrics"),ref(cycle,"event"),ref(cycle,"ordinary_credit"),ref(cycle,"auto_after"),
                    ref(cycle,"metrics_after"),ref(cycle,"before_plan"),cycle.get("readonly_save_skip").isNull() ? Optional.empty() : Optional.of(ref(cycle,"readonly_save_skip"))));
        }
        ObjectNode business = StrictJson.object(root.get("business"), Set.of("saved_seed","saved_governance","cold_bound","opening_semantic","opening_capabilities","classifier_pin","classifier_source","queue_source","capture_probe","capture_cleanup"));
        BusinessRefs evidence = new BusinessRefs(ref(business,"saved_seed"),ref(business,"saved_governance"),ref(business,"cold_bound"),ref(business,"opening_semantic"),
                ref(business,"opening_capabilities"),ref(business,"classifier_pin"),ref(business,"classifier_source"),ref(business,"queue_source"),ref(business,"capture_probe"),ref(business,"capture_cleanup"));
        return new ClosedAdoptionRequest(StrictJson.text(root.get("machine_id")), StrictJson.text(root.get("observed_at_utc")), inputs, closures, tasks, cycles,
                evidence, Path.of(StrictJson.text(root.get("canonical_path"))), Path.of(StrictJson.text(root.get("metadata_root"))),ref(root,"writer_source"));
    }
    private static JsonNode array(JsonNode value) { StrictJson.require(value != null && value.isArray(), "explicit source array"); return value; }
    private static ExactRef ref(ObjectNode row, String field) { return ExactRef.fromJson(row.get(field)); }
}
