package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original completed-tail source contract. Parsing this record grants no reducer or recovery qualification. */
public record OriginalRollbackProof(String machineId,Instant observedAt,Path runtimeRoot,Sources sources) {
    public static final String SCHEMA="xar.current-saved-completed-unsaved-tail/v1";
    public OriginalRollbackProof {
        StrictJson.text(machineId);Objects.requireNonNull(observedAt);Objects.requireNonNull(runtimeRoot);Objects.requireNonNull(sources);
        StrictJson.require(runtimeRoot.isAbsolute()&&runtimeRoot.normalize().equals(runtimeRoot),"actual normalized absolute closed runtime required");
    }
    public record Sources(ExactRef priorBasis,ExactRef priorValidation,List<ExactRef> successfulFullResponses,
            ExactRef rawState,ExactRef rawGovernance,ExactRef interruption,ExactRef inventory,ExactRef abnormalClosedEpoch,
            ExactRef currentDriverReview,ExactRef actualNext,ExactRef canonicalCheckpointQualification,ExactRef continuityFrontier) {
        public Sources {
            successfulFullResponses=List.copyOf(successfulFullResponses);
            StrictJson.require(!successfulFullResponses.isEmpty()&&successfulFullResponses.size()<=256
                    &&successfulFullResponses.stream().map(ExactRef::path).distinct().count()==successfulFullResponses.size(),"finite unique original FULL chain required");
            for(ExactRef ref:successfulFullResponses)requireMaterialSource(ref);
            for(ExactRef ref:List.of(priorBasis,priorValidation,rawState,rawGovernance,interruption,inventory,abnormalClosedEpoch,
                    currentDriverReview,actualNext,canonicalCheckpointQualification,continuityFrontier))
                requireMaterialSource(ref);
        }
    }
    public static OriginalRollbackProof decode(byte[] original,String machine) {
        var row=StrictJson.object(StrictJson.parse(original,32768),Set.of("schema","status","machine_id","observed_at_utc","runtime_root","sources",
                "new_ordinary_cycle_credit","new_game_day_credit","original_actions_replayed","Driver_history_truncated"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&"CLOSED_COMPLETED_UNSAVED_TAIL".equals(StrictJson.text(row.get("status")))
                &&machine.equals(StrictJson.text(row.get("machine_id"))),"original completed-tail schema/status/machine differs");
        StrictJson.integer(row.get("new_ordinary_cycle_credit"),0,0);StrictJson.integer(row.get("new_game_day_credit"),0,0);
        falseValue(row.get("original_actions_replayed"));falseValue(row.get("Driver_history_truncated"));
        var source=StrictJson.object(row.get("sources"),Set.of("prior_basis","prior_validation","successful_full_responses","raw_state","raw_governance",
                "interruption","inventory","abnormal_closed_epoch","current_driver_review","actual_next","canonical_checkpoint_qualification","continuity_frontier"));
        JsonNode full=source.get("successful_full_responses");StrictJson.require(full!=null&&full.isArray(),"complete original FULL source array required");
        var refs=new java.util.ArrayList<ExactRef>();full.forEach(value->refs.add(ExactRef.fromJson(value)));
        return new OriginalRollbackProof(machine,Instant.parse(StrictJson.utc(StrictJson.text(row.get("observed_at_utc")))),
                Path.of(StrictJson.text(row.get("runtime_root"))),new Sources(ref(source,"prior_basis"),ref(source,"prior_validation"),refs,
                ref(source,"raw_state"),ref(source,"raw_governance"),ref(source,"interruption"),ref(source,"inventory"),ref(source,"abnormal_closed_epoch"),
                ref(source,"current_driver_review"),ref(source,"actual_next"),ref(source,"canonical_checkpoint_qualification"),ref(source,"continuity_frontier")));
    }
    private static ExactRef ref(JsonNode row,String key){return ExactRef.fromJson(row.get(key));}
    private static void requireMaterialSource(ExactRef ref) {
        Objects.requireNonNull(ref);
        StrictJson.require(ref.bytes()>0&&Path.of(ref.path()).isAbsolute(),"actual nonempty absolute original material source required");
    }
    private static void falseValue(JsonNode value){StrictJson.require(value!=null&&value.isBoolean()&&!value.booleanValue(),"actual false value required");}
}
