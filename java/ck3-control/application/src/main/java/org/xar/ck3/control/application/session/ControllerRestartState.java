package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.LinkedHashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete Controller DATA. Decoding this document grants no restart or action admission. */
public record ControllerRestartState(SessionPorts.SessionIdentity owner, String batchPrefix, long nextBatchSequence,
        Set<String> usedBatches, Set<String> unsavedGameplayActions, Optional<CheckpointPair> savedPair,
        Optional<ExactRef> ledgerHead, int eligibleSinceSave, boolean dirty, boolean quarantined,
        boolean localUnresolved, long totalCommittedDays, Set<String> completedAnalysisIds, boolean stopRequested) {
    public static final String SCHEMA="xar.java-controller-restart-state/v1";
    private static final int MAX_ITEMS=100_000;
    private static final Set<String> FIELDS=Set.of("schema","owner","batch_prefix","next_batch_sequence",
            "used_batches","unsaved_gameplay_actions","saved_pair","ledger_head","eligible_since_save",
            "dirty","quarantined","local_unresolved","total_committed_days","completed_analysis_ids","stop_requested");
    public ControllerRestartState {
        Objects.requireNonNull(owner);text(batchPrefix);StrictJson.safe(nextBatchSequence,0);
        usedBatches=checked(usedBatches);unsavedGameplayActions=checked(unsavedGameplayActions);
        Objects.requireNonNull(savedPair);Objects.requireNonNull(ledgerHead);StrictJson.safe(eligibleSinceSave,0);
        StrictJson.safe(totalCommittedDays,0);completedAnalysisIds=checked(completedAnalysisIds);
    }
    public byte[] encode(){
        ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);
        row.set("owner",OrdinaryCycleTransitions.sessionToJson(owner));row.put("batch_prefix",batchPrefix);
        row.put("next_batch_sequence",nextBatchSequence);strings(row,"used_batches",usedBatches);
        strings(row,"unsaved_gameplay_actions",unsavedGameplayActions);
        if(savedPair.isPresent())row.set("saved_pair",ContinuityJson.parseObject(CheckpointPairCodec.encode(savedPair.orElseThrow()),ContinuityJson.DOCUMENT_MAX_BYTES));
        else row.putNull("saved_pair");
        if(ledgerHead.isPresent())row.set("ledger_head",ledgerHead.orElseThrow().toJson());else row.putNull("ledger_head");
        row.put("eligible_since_save",eligibleSinceSave);row.put("dirty",dirty);row.put("quarantined",quarantined);
        row.put("local_unresolved",localUnresolved);row.put("total_committed_days",totalCommittedDays);
        strings(row,"completed_analysis_ids",completedAnalysisIds);row.put("stop_requested",stopRequested);
        byte[] result=ContinuityJson.canonical(row);
        StrictJson.require(result.length<=ContinuityJson.DOCUMENT_MAX_BYTES,"Controller restart document exceeds its finite bound");return result;
    }
    public static ControllerRestartState decode(byte[] bytes){
        ObjectNode row=StrictJson.object(ContinuityJson.parseObject(bytes,ContinuityJson.DOCUMENT_MAX_BYTES),FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"Controller restart schema differs");
        for(String key:FIELDS)StrictJson.require(row.has(key),"Controller restart field missing: "+key);
        return new ControllerRestartState(OrdinaryCycleTransitions.sessionFromJson(row.get("owner")),StrictJson.text(row.get("batch_prefix")),
                StrictJson.integer(row.get("next_batch_sequence"),0,StrictJson.MAX_SAFE_INTEGER),strings(row.get("used_batches")),
                strings(row.get("unsaved_gameplay_actions")),row.get("saved_pair").isNull()?Optional.empty():Optional.of(CheckpointPairCodec.decode(ContinuityJson.canonical(row.get("saved_pair")))),
                row.get("ledger_head").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("ledger_head"))),
                (int)StrictJson.integer(row.get("eligible_since_save"),0,Integer.MAX_VALUE),bool(row,"dirty"),bool(row,"quarantined"),
                bool(row,"local_unresolved"),StrictJson.integer(row.get("total_committed_days"),0,StrictJson.MAX_SAFE_INTEGER),
                strings(row.get("completed_analysis_ids")),bool(row,"stop_requested"));
    }
    private static Set<String> checked(Set<String> values){
        Objects.requireNonNull(values);StrictJson.require(values.size()<=MAX_ITEMS,"Controller restart set exceeds its finite bound");
        values.forEach(ControllerRestartState::text);return Set.copyOf(values);
    }
    private static void text(String value){StrictJson.text(value);StrictJson.require(value.length()<=4096,"bounded Controller restart identifier required");}
    private static void strings(ObjectNode row,String key,Set<String> values){var list=row.putArray(key);values.stream().sorted().forEach(list::add);}
    private static Set<String> strings(JsonNode value){
        StrictJson.require(value!=null&&value.isArray()&&value.size()<=MAX_ITEMS,"bounded Controller restart string array required");
        Set<String> result=new LinkedHashSet<>();value.forEach(item->{String entry=StrictJson.text(item);text(entry);StrictJson.require(result.add(entry),"duplicate Controller restart identifier");});return Set.copyOf(result);
    }
    private static boolean bool(ObjectNode row,String key){JsonNode value=row.get(key);StrictJson.require(value!=null&&value.isBoolean(),"Controller restart boolean required: "+key);return value.booleanValue();}
}
