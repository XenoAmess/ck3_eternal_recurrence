package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Full shared native enumeration diagnostics, including all retained false-role samples. */
public record MarriageDiagnostics(int storageCapacity, int slotsScanned, int emptySlots,
        int liveCandidates, int deadCandidates, int selfCandidates, int generationMismatches,
        int contextsConstructed, int contextConstructFailures, int nativeValidateTrue,
        int nativeValidateFalse, List<Sample> validationFalseSamples) {
    public record Sample(int slotIndex, int candidate, int actor, int recipient,
                         int secondaryActor, int secondaryRecipient, int intermediary) {
        public Sample { need(slotIndex>=0,"native sample slot cannot be absent"); }
    }
    public MarriageDiagnostics {
        validationFalseSamples=List.copyOf(validationFalseSamples);
        for(int counter:new int[]{storageCapacity,slotsScanned,emptySlots,liveCandidates,deadCandidates,selfCandidates,
                generationMismatches,contextsConstructed,contextConstructFailures,nativeValidateTrue,nativeValidateFalse})
            need(counter>=0,"negative native enumeration counter");
        need(slotsScanned<=storageCapacity,"native enumeration exceeded storage");
        for(Sample sample:validationFalseSamples) need(sample.slotIndex()<storageCapacity,"native sample outside scanned storage");
    }
    public boolean complete() { return slotsScanned==storageCapacity; }
    public static MarriageDiagnostics decode(JsonNode n) {
        closed(n,"storage_capacity","slots_scanned","empty_slots","live_candidates","dead_candidates","self_candidates",
                "generation_mismatch_candidates","contexts_constructed","context_construct_failures",
                "native_validate_true","native_validate_false","validation_false_samples");
        List<Sample> samples=list(n,"validation_false_samples",65536,row->{
            closed(row,"slot_index","candidate_character_id","actor_character_id","recipient_character_id",
                    "secondary_actor_character_id","secondary_recipient_character_id","intermediary_character_id");
            return new Sample(integer(row,"slot_index",0,Integer.MAX_VALUE),signed(row,"candidate_character_id"),
                    signed(row,"actor_character_id"),signed(row,"recipient_character_id"),signed(row,"secondary_actor_character_id"),
                    signed(row,"secondary_recipient_character_id"),signed(row,"intermediary_character_id"));
        });
        return new MarriageDiagnostics(count(n,"storage_capacity"),count(n,"slots_scanned"),count(n,"empty_slots"),
                count(n,"live_candidates"),count(n,"dead_candidates"),count(n,"self_candidates"),count(n,"generation_mismatch_candidates"),
                count(n,"contexts_constructed"),count(n,"context_construct_failures"),count(n,"native_validate_true"),
                count(n,"native_validate_false"),samples);
    }
    private static int count(JsonNode n,String name) { return integer(n,name,0,Integer.MAX_VALUE); }
    private static int signed(JsonNode n,String name) { return integer(n,name,Integer.MIN_VALUE,Integer.MAX_VALUE); }
}
